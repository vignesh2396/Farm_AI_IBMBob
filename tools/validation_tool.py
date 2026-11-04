"""
tools/validation_tool.py
-------------------------
Tool: Output validation and high-impact flagging for FarmAI agents.
Validates agent outputs for safety, groundedness, and data integrity.
Flags recommendations that require human review.

Usage:
    from tools.validation_tool import validate_soil_result, flag_high_impact
"""
import re
from dataclasses import dataclass
from typing import Any

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    is_high_impact: bool
    issues: list[str]
    warnings: list[str]
    groundedness_score: float = 1.0  # 0–1; 1.0 means no grounding issues detected


# ── Input Validators ──────────────────────────────────────────────────────────

def validate_soil_inputs(
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    ph_level: float,
    organic_matter: float,
) -> ValidationResult:
    """
    Validate soil assessment input values.

    Returns:
        ValidationResult with any range or logic issues noted
    """
    issues = []
    warnings = []

    if not (0 <= nitrogen <= 100):
        issues.append(f"Nitrogen value {nitrogen} is outside valid range 0–100 kg/ha")
    if not (0 <= phosphorus <= 100):
        issues.append(f"Phosphorus value {phosphorus} is outside valid range 0–100 kg/ha")
    if not (0 <= potassium <= 100):
        issues.append(f"Potassium value {potassium} is outside valid range 0–100 kg/ha")
    if not (0 <= ph_level <= 14):
        issues.append(f"pH value {ph_level} is outside valid range 0–14")
    if not (0 <= organic_matter <= 20):
        issues.append(f"Organic matter {organic_matter}% is outside valid range 0–20%")

    if ph_level < 4.5 or ph_level > 9.5:
        warnings.append(
            f"Extreme pH ({ph_level}) detected. Laboratory verification recommended before taking corrective action."
        )
    if nitrogen == 0 and phosphorus == 0 and potassium == 0:
        warnings.append("All NPK values are zero. Please verify soil test results.")

    return ValidationResult(
        is_valid=len(issues) == 0,
        is_high_impact=False,
        issues=issues,
        warnings=warnings,
    )


def validate_crop_suitability_result(ranked_crops: list) -> ValidationResult:
    """
    Validate crop suitability output.

    Returns:
        ValidationResult with issues if no crops found or all scores are zero
    """
    issues = []
    warnings = []

    if not ranked_crops:
        issues.append("No crops found for the given soil/season combination")
    elif all(c.suitability_score < 40 for c in ranked_crops):
        warnings.append(
            "All crop suitability scores are below 40/100. "
            "Consider soil amendment or consult your extension officer."
        )

    return ValidationResult(
        is_valid=len(issues) == 0,
        is_high_impact=False,
        issues=issues,
        warnings=warnings,
    )


# ── Output Validators ─────────────────────────────────────────────────────────

_HIGH_IMPACT_KEYWORDS = [
    r"\borganophosphate\b",
    r"\bpesticide\b",
    r"\binsecticide\b",
    r"\bherbicide\b",
    r"\bfungicide\b",
    r"\bheavy metal\b",
    r"\bcyanide\b",
    r"\barsenic\b",
    r"\border of magnitude\b",
    r"\bextreme dosage\b",
    r"\bburn\b.*\bfield\b",
    r"\babandon\b.*\bcrop\b",
]

_SENSITIVE_CHEMICAL_KEYWORDS = [
    r"\bendosulfan\b",
    r"\bchlorophos\b",
    r"\bmonocrotophos\b",
    r"\bphorate\b",
    r"\bdicofol\b",
    r"\bDDT\b",
    r"\bBHC\b",
]


def flag_high_impact(recommendation_text: str) -> ValidationResult:
    """
    Check if a recommendation text contains high-impact or sensitive content.
    If detected, flags for human review (HITL).

    Args:
        recommendation_text: Full text of the recommendation or plan

    Returns:
        ValidationResult with is_high_impact=True if flagging is needed
    """
    text_lower = recommendation_text.lower()
    issues = []
    warnings = []
    is_high_impact = False

    for pattern in _HIGH_IMPACT_KEYWORDS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            is_high_impact = True
            warnings.append(
                f"Recommendation contains potentially high-impact term matching '{pattern}'. "
                f"Human review required before presenting to farmer."
            )
            break

    for pattern in _SENSITIVE_CHEMICAL_KEYWORDS:
        if re.search(pattern, recommendation_text, re.IGNORECASE):
            is_high_impact = True
            issues.append(
                f"Recommendation references a restricted/banned chemical. "
                f"This recommendation has been blocked. Consult extension officer."
            )

    if is_high_impact:
        logger.warning("HIGH IMPACT flag raised for recommendation text (first 100 chars): %s",
                       recommendation_text[:100])

    return ValidationResult(
        is_valid=len(issues) == 0,
        is_high_impact=is_high_impact,
        issues=issues,
        warnings=warnings,
    )


def check_groundedness(answer: str, retrieved_sources: list[dict]) -> float:
    """
    Heuristic groundedness check for RAG-generated answers.

    Checks if the answer text contains content similar to retrieved sources.
    Returns a groundedness score 0–1.

    Args:
        answer: LLM-generated answer text
        retrieved_sources: List of retrieved document chunks

    Returns:
        Float groundedness score (0 = no grounding, 1 = fully grounded)
    """
    if not retrieved_sources:
        logger.warning("Groundedness check: no sources provided — score set to 0.0")
        return 0.0

    answer_words = set(re.findall(r"\b\w{4,}\b", answer.lower()))
    if not answer_words:
        return 0.0

    total_overlap = 0
    for source in retrieved_sources:
        source_text = str(source.get("text", source.get("content", ""))).lower()
        source_words = set(re.findall(r"\b\w{4,}\b", source_text))
        overlap = len(answer_words & source_words)
        total_overlap += overlap / max(len(answer_words), 1)

    avg_score = total_overlap / len(retrieved_sources)
    # Normalize: typical overlap for grounded responses is 10–30%
    groundedness = min(1.0, avg_score * 4.0)

    logger.debug("Groundedness score: %.2f (overlap: %.3f over %d sources)",
                 groundedness, avg_score, len(retrieved_sources))
    return round(groundedness, 2)


def validate_llm_output_json(raw_output: str, required_keys: list[str]) -> ValidationResult:
    """
    Validate that an LLM JSON output is parseable and contains all required keys.

    Args:
        raw_output: Raw string from LLM
        required_keys: List of keys that must be present in the parsed JSON

    Returns:
        ValidationResult; is_valid=False if parsing fails or keys are missing
    """
    import json
    issues = []
    warnings = []

    # Extract JSON block if wrapped in markdown code fences
    json_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", raw_output)
    json_str = json_match.group(1) if json_match else raw_output.strip()

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        issues.append(f"LLM output is not valid JSON: {exc}")
        return ValidationResult(
            is_valid=False, is_high_impact=False, issues=issues, warnings=warnings
        )

    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        warnings.append(f"LLM output missing expected keys: {missing_keys}")

    return ValidationResult(
        is_valid=len(issues) == 0,
        is_high_impact=False,
        issues=issues,
        warnings=warnings,
    )
