"""
utils/config.py
---------------
Configuration management for FarmAI.
Loads all settings from environment variables via python-dotenv.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / ".env")


class Config:
    """Central configuration object. All values sourced from environment."""

    # LLM
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))

    # Database
    DB_PATH: str = os.getenv("DB_PATH", str(_root / "data" / "farmdata.db"))

    # Vector Store
    CHROMA_PERSIST_DIR: str = os.getenv(
        "CHROMA_PERSIST_DIR", str(_root / "data" / "chroma_db")
    )
    DOCUMENTS_DIR: str = os.getenv(
        "DOCUMENTS_DIR", str(_root / "rag" / "documents")
    )
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "models/embedding-001"
    )

    # Weather API
    WEATHER_API_BASE_URL: str = os.getenv(
        "WEATHER_API_BASE_URL",
        "https://api.open-meteo.com/v1/forecast",
    )
    WEATHER_CACHE_TTL_HOURS: int = int(os.getenv("WEATHER_CACHE_TTL_HOURS", "6"))

    # Geocoding (for location → lat/lon)
    GEOCODING_API_BASE_URL: str = os.getenv(
        "GEOCODING_API_BASE_URL",
        "https://geocoding-api.open-meteo.com/v1/search",
    )

    # Application
    APP_TITLE: str = "FarmAI – Agricultural Decision Intelligence"
    APP_VERSION: str = "1.0.0"
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", str(_root / "data" / "farmai.log"))

    # Data Files
    CROP_REFERENCE_CSV: str = os.getenv(
        "CROP_REFERENCE_CSV", str(_root / "data" / "crop_reference.csv")
    )
    SOIL_RULES_JSON: str = os.getenv(
        "SOIL_RULES_JSON", str(_root / "data" / "soil_fertility_rules.json")
    )

    @classmethod
    def validate(cls) -> list[str]:
        """Return list of missing required configuration keys."""
        missing = []
        if not cls.GOOGLE_API_KEY:
            missing.append("GOOGLE_API_KEY")
        return missing


config = Config()
