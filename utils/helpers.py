"""
utils/helpers.py
----------------
Common utility functions for FarmAI.
"""
import re
import uuid
from datetime import datetime, timezone
from typing import Any


def generate_session_id() -> str:
    """Generate a new UUID v4 session identifier."""
    return str(uuid.uuid4())


def sanitize_input(text: str, max_length: int = 500) -> str:
    """
    Sanitize user text input before use in prompts or SQL.
    - Strips leading/trailing whitespace
    - Removes characters that could cause prompt injection
    - Truncates to max_length

    Args:
        text: Raw user input string
        max_length: Maximum allowed length (default 500)

    Returns:
        Sanitized string safe for use in LLM prompts
    """
    if not isinstance(text, str):
        return ""
    # Remove characters used in prompt injection attempts
    cleaned = re.sub(r"[<>{}\\|`]", "", text)
    # Collapse multiple whitespace characters
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:max_length]


def format_date(dt: datetime | None = None) -> str:
    """Return ISO 8601 UTC timestamp string."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def confidence_label(score: float) -> str:
    """Convert a 0–1 confidence float to a human-readable label."""
    if score >= 0.85:
        return "HIGH"
    elif score >= 0.65:
        return "MEDIUM"
    elif score >= 0.45:
        return "LOW"
    return "VERY LOW"


def format_score_bar(score: int, max_score: int = 100, bar_width: int = 20) -> str:
    """
    Create a text-based progress bar for suitability scores.

    Args:
        score: Current score value
        max_score: Maximum possible score
        bar_width: Width of the bar in characters

    Returns:
        String like "████████████░░░░░░░░ 72/100"
    """
    filled = int((score / max_score) * bar_width)
    bar = "█" * filled + "░" * (bar_width - filled)
    return f"{bar} {score}/{max_score}"


def truncate_text(text: str, max_chars: int = 200, suffix: str = "...") -> str:
    """Truncate text to max_chars, adding suffix if truncated."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - len(suffix)] + suffix


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float, returning default on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def week_label(week_number: int, sowing_date: str = "Week 1") -> str:
    """Format a week label for the operations plan calendar."""
    return f"Week {week_number:02d}"
