"""
rag/embeddings.py
------------------
RAG Pipeline: Document ingestion, chunking, and embedding for FarmAI.
Builds a ChromaDB vector store from agricultural knowledge documents.

Usage (one-time setup):
    python -m rag.embeddings
    
Or from code:
    from rag.embeddings import build_vector_store
    build_vector_store()
"""
import os
import re
from pathlib import Path
from typing import Optional

from utils.config import config
from utils.logger import get_logger

logger = get_logger(__name__)

_CHUNK_SIZE = 500   # characters per chunk
_CHUNK_OVERLAP = 80  # overlap between chunks


def _read_text_file(file_path: Path) -> str:
    """Read a text file, stripping excessive whitespace."""
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
    except OSError as exc:
        logger.error("Failed to read %s: %s", file_path, exc)
        return ""


def _chunk_text(text: str, source_name: str) -> list[dict]:
    """
    Split text into overlapping chunks for embedding.

    Args:
        text: Full document text
        source_name: Document filename for metadata

    Returns:
        List of chunk dicts with 'text' and 'metadata'
    """
    chunks = []
    start = 0
    chunk_id = 0
    while start < len(text):
        end = min(start + _CHUNK_SIZE, len(text))
        # Try to break at sentence boundary
        if end < len(text):
            for sep in (". ", ".\n", "\n", " "):
                idx = text.rfind(sep, start, end)
                if idx > start + _CHUNK_SIZE // 2:
                    end = idx + len(sep)
                    break

        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "source": source_name,
                    "chunk_id": chunk_id,
                    "char_start": start,
                    "char_end": end,
                },
            })
            chunk_id += 1
        start = end - _CHUNK_OVERLAP

    logger.debug("Chunked '%s' into %d chunks", source_name, len(chunks))
    return chunks


def build_vector_store(force_rebuild: bool = False) -> bool:
    """
    Build ChromaDB vector store from documents in the documents directory.

    Args:
        force_rebuild: If True, delete existing store and rebuild from scratch

    Returns:
        True if successful, False otherwise
    """
    try:
        import chromadb
        from chromadb.utils import embedding_functions
    except ImportError:
        logger.error("chromadb not installed. Run: pip install chromadb")
        return False

    docs_dir = Path(config.DOCUMENTS_DIR)
    persist_dir = Path(config.CHROMA_PERSIST_DIR)

    if not docs_dir.exists():
        logger.warning("Documents directory not found: %s", docs_dir)
        docs_dir.mkdir(parents=True, exist_ok=True)
        _create_sample_documents(docs_dir)

    if force_rebuild and persist_dir.exists():
        import shutil
        shutil.rmtree(persist_dir)
        logger.info("Deleted existing vector store for rebuild")

    persist_dir.mkdir(parents=True, exist_ok=True)

    # Initialize ChromaDB
    client = chromadb.PersistentClient(path=str(persist_dir))

    # Use Google embedding function if API key available, else default
    api_key = config.GOOGLE_API_KEY
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(api_key=api_key)
            logger.info("Using Google Generative AI embeddings")
        except Exception as exc:
            logger.warning("Google embedding setup failed: %s. Using default embeddings.", exc)
            ef = embedding_functions.DefaultEmbeddingFunction()
    else:
        ef = embedding_functions.DefaultEmbeddingFunction()
        logger.info("Using default (sentence-transformers) embeddings")

    collection = client.get_or_create_collection(
        name="farmai_knowledge",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    # Process all text files in documents directory
    doc_files = list(docs_dir.glob("*.txt")) + list(docs_dir.glob("*.md"))
    if not doc_files:
        logger.warning("No document files found in %s", docs_dir)
        return False

    all_chunks = []
    for doc_file in doc_files:
        text = _read_text_file(doc_file)
        if text:
            chunks = _chunk_text(text, doc_file.name)
            all_chunks.extend(chunks)

    if not all_chunks:
        logger.warning("No chunks generated from documents")
        return False

    # Add to ChromaDB (in batches of 100)
    batch_size = 100
    existing_ids = set(collection.get()["ids"])

    added = 0
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i: i + batch_size]
        ids = [f"{c['metadata']['source']}_chunk_{c['metadata']['chunk_id']}" for c in batch]
        texts = [c["text"] for c in batch]
        metadatas = [c["metadata"] for c in batch]

        # Skip already indexed chunks
        new_batch = [(id_, t, m) for id_, t, m in zip(ids, texts, metadatas) if id_ not in existing_ids]
        if new_batch:
            new_ids, new_texts, new_metas = zip(*new_batch)
            collection.add(ids=list(new_ids), documents=list(new_texts), metadatas=list(new_metas))
            added += len(new_batch)

    logger.info("Vector store built: %d new chunks added. Total: %d chunks", added, len(all_chunks))
    return True


def _create_sample_documents(docs_dir: Path) -> None:
    """Create sample knowledge base documents for demo purposes."""
    docs = {
        "icar_cotton_guide.txt": """
ICAR Cotton Cultivation Guide — Maharashtra
===========================================
Chapter 1: Introduction
Cotton (Gossypium hirsutum) is the most important fiber crop of India. Maharashtra is the
largest cotton-growing state, contributing about 30% of India's total cotton production.

Chapter 2: Soil Requirements
Cotton grows best in deep, well-drained black cotton soil (Vertisol) with pH 6.0–8.0.
It can tolerate slight alkalinity but not waterlogging. Minimum soil depth: 45 cm.
Organic matter content should be >1.5% for optimal growth.

Chapter 3: Sowing Practices
Recommended sowing time: Kharif season, June 15 to July 15 after receipt of good pre-monsoon rains.
Seed rate: 1.5–2.0 kg/acre for hybrid cotton.
Spacing: 90 cm x 60 cm (row x plant) or 120 cm x 45 cm for high-density planting.
Depth: 3–5 cm. Germination: 5–7 days.

Chapter 4: Fertilizer Management
General recommendation for hybrid cotton on black soil:
- Nitrogen: 120 kg/ha (60 kg basal + 60 kg in two splits at 30 and 60 days)
- Phosphorus: 60 kg P2O5/ha (basal)
- Potassium: 60 kg K2O/ha (basal)
- Zinc Sulphate: 25 kg/ha (basal, once in 3 years on zinc-deficient soils)

Chapter 5: Irrigation
Cotton is a moderately drought-resistant crop but requires timely irrigation at critical stages.
Critical irrigation stages: Germination, squaring (45–50 DAS), flowering (65–70 DAS), boll development.
Total water requirement: 600–800 mm per season.
Irrigation interval: 10–15 days during dry spells.

Chapter 6: Integrated Pest Management
Key pests: Bollworm, Aphid, Whitefly, Jassid, Thrips.
IPM approach: Use certified seeds, monitor regularly, use yellow sticky traps for whitefly.
Biological control: Trichogramma cards for bollworm (release at 50,000 per acre at egg stage).
Chemical control only when pest population exceeds economic threshold level (ETL).
""",
        "soil_health_card_guide.txt": """
Soil Health Card Scheme — Government of India
==============================================
Introduction
The Soil Health Card (SHC) scheme provides farmers with soil nutrient status
and recommendations for appropriate dosage of nutrients for improving soil health.

Soil Nutrient Status Ranges:
Nitrogen:
- Low: <280 kg/ha (available N)
- Medium: 280–560 kg/ha
- High: >560 kg/ha

Phosphorus (Available P2O5):
- Low: <10 kg/ha
- Medium: 10–25 kg/ha
- High: >25 kg/ha

Potassium (Available K2O):
- Low: <108 kg/ha
- Medium: 108–280 kg/ha
- High: >280 kg/ha

pH Ranges:
- Strongly acid: <5.5
- Moderately acid: 5.5–6.5
- Neutral: 6.5–7.5
- Moderately alkaline: 7.5–8.5
- Strongly alkaline: >8.5

Organic Carbon (%):
- Low: <0.5
- Medium: 0.5–0.75
- High: >0.75

Secondary and Micronutrients:
Important micronutrients: Zinc, Boron, Iron, Manganese.
Zinc deficiency: Common in alluvial soils and black soils of Maharashtra.
Symptom: Khairah disease in paddy, white bud in maize, little leaf in cotton.
Correction: Apply ZnSO4 @ 25 kg/ha (basal) or 0.5% foliar spray.
""",
        "kharif_crop_advisory.txt": """
Kharif Crop Season Advisory — 2026
====================================
Season Overview
Kharif season: June to November (sowing: June–July; harvest: October–November)
Key states: Maharashtra, MP, Rajasthan, Gujarat, Karnataka, Andhra Pradesh

Soybean:
Best suited for: Vertisol, Inceptisol (pH 6.0–7.5)
Seed rate: 30–35 kg/acre
Spacing: 45 cm x 10 cm
Fertilizer: 20:60:40 kg/ha NPK (only basal; soybean is self-nitrogen fixing)
Irrigation: 3–4 irrigations needed in drought conditions
Harvest: 90–100 DAS when 50% pods turn yellow

Pigeonpea (Arhar):
Best suited for: Well-drained Vertisol and Alfisol (pH 6.5–8.0)
Seed rate: 4–5 kg/acre
Duration: 150–180 days (short duration varieties 120–130 days available)
Fertilizer: 10:40:20 kg/ha NPK (basal only)
Important: Do not apply nitrogen top dressing (N2-fixing legume)
Water stress tolerance: Moderate to high

Groundnut:
Best suited for: Sandy loam, Alfisol, red soil (pH 6.0–7.0)
Seed rate: 40–50 kg/acre (bold varieties)
Spacing: 30 cm x 10 cm
Fertilizer: 25:50:30 kg/ha NPK
Gypsum application: 100 kg/acre at pegging stage (calcium for pod development)
Irrigation: 8–10 irrigations needed; critical at pegging and pod-fill stages

Integrated Crop Management Principles:
1. Use certified, high-yielding disease-resistant varieties
2. Treat seeds before sowing (thiram + carbendazim mixture)
3. Follow crop rotation to reduce pest and disease buildup
4. Practice inter-cropping for risk management (e.g., soybean + pigeonpea)
5. Monitor soil moisture and irrigate at critical growth stages
6. Use IPM over calendar-based pesticide spraying
"""
    }

    for filename, content in docs.items():
        (docs_dir / filename).write_text(content.strip(), encoding="utf-8")
        logger.info("Created sample document: %s", filename)


if __name__ == "__main__":
    logger.info("Building FarmAI knowledge base vector store...")
    success = build_vector_store(force_rebuild=True)
    if success:
        logger.info("Vector store built successfully.")
    else:
        logger.error("Vector store build failed.")
