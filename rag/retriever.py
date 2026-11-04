"""
rag/retriever.py
-----------------
RAG Pipeline: Query interface for the FarmAI ChromaDB vector store.
Retrieves semantically relevant document chunks for advisory queries.

Usage:
    from rag.retriever import retrieve_knowledge
    results = retrieve_knowledge("best spacing for cotton in black soil")
"""
from pathlib import Path
from typing import Optional

from utils.config import config
from utils.logger import get_logger

logger = get_logger(__name__)

_collection_cache: dict = {}


def _get_collection():
    """
    Get or initialize the ChromaDB collection.
    Caches the client/collection to avoid repeated disk I/O.
    """
    if _collection_cache.get("collection"):
        return _collection_cache["collection"]

    try:
        import chromadb
        from chromadb.utils import embedding_functions
    except ImportError:
        logger.error("chromadb not installed. Run: pip install chromadb")
        return None

    persist_dir = Path(config.CHROMA_PERSIST_DIR)
    if not persist_dir.exists():
        logger.warning("Vector store not found at %s. Building now...", persist_dir)
        from rag.embeddings import build_vector_store
        success = build_vector_store()
        if not success:
            logger.error("Failed to build vector store")
            return None

    try:
        client = chromadb.PersistentClient(path=str(persist_dir))
        api_key = config.GOOGLE_API_KEY
        if api_key:
            try:
                ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(api_key=api_key)
            except Exception:
                ef = embedding_functions.DefaultEmbeddingFunction()
        else:
            ef = embedding_functions.DefaultEmbeddingFunction()

        collection = client.get_or_create_collection(
            name="farmai_knowledge",
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
        _collection_cache["collection"] = collection
        return collection
    except Exception as exc:
        logger.error("Failed to load ChromaDB collection: %s", exc)
        return None


def retrieve_knowledge(
    query: str,
    top_k: int = 3,
    min_relevance: float = 0.0,
) -> list[dict]:
    """
    Retrieve the most relevant document chunks for a given query.

    Args:
        query: Natural language query string
        top_k: Number of results to return (default 3)
        min_relevance: Minimum relevance threshold (0–1; not enforced in ChromaDB but used post-filter)

    Returns:
        List of result dicts with keys: text, source, chunk_id, relevance_score
    """
    if not query or not query.strip():
        logger.warning("Empty query passed to retrieve_knowledge")
        return []

    collection = _get_collection()
    if collection is None:
        logger.error("RAG retrieval unavailable: collection not loaded")
        return []

    try:
        results = collection.query(
            query_texts=[query.strip()],
            n_results=min(top_k, max(1, collection.count())),
        )
    except Exception as exc:
        logger.error("ChromaDB query failed: %s", exc)
        return []

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    retrieved = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        # ChromaDB cosine distance: 0 = identical, 2 = opposite
        # Convert to similarity score 0–1
        similarity = max(0.0, 1.0 - (dist / 2.0))
        if similarity < min_relevance:
            continue
        retrieved.append({
            "text": doc,
            "source": meta.get("source", "Unknown"),
            "chunk_id": meta.get("chunk_id", 0),
            "relevance_score": round(similarity, 3),
        })

    logger.info(
        "RAG retrieval: query='%s...' → %d results (top score: %.2f)",
        query[:50],
        len(retrieved),
        retrieved[0]["relevance_score"] if retrieved else 0.0,
    )
    return retrieved


def retrieve_crop_knowledge(crop_name: str, topic: str = "") -> list[dict]:
    """
    Convenience wrapper to retrieve crop-specific knowledge.

    Args:
        crop_name: Name of the crop (e.g., "Cotton")
        topic: Optional topic focus (e.g., "irrigation", "spacing", "fertilizer")

    Returns:
        List of retrieved document chunks
    """
    query = f"{crop_name} {topic}".strip() if topic else f"{crop_name} cultivation practices"
    return retrieve_knowledge(query, top_k=3)


def invalidate_cache() -> None:
    """Clear the collection cache (useful after re-indexing)."""
    _collection_cache.clear()
    logger.info("RAG collection cache cleared")
