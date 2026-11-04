"""
tools/soil_analysis_tool.py
----------------------------
Tool: Rule-based soil classification and fertilizer recommendation engine.
Uses soil_fertility_rules.json to classify soil type and nutrient status.

Usage:
    from tools.soil_analysis_tool import analyze_soil
    result = analyze_soil(nitrogen=42, phosphorus=18, potassium=65, ph_level=7.2, organic_matter=1.8)
"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from utils.config import config
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SoilInput:
    """Input data model for soil assessment."""
    nitrogen: float        # kg/ha, range 0–100
    phosphorus: float      # kg/ha, range 0–100
    potassium: float       # kg/ha, range 0–100
    ph_level: float        # 0–14
    organic_matter: float = 0.0  # %, range 0–20
    moisture_level: str = "Moderate"  # Dry | Moderate | Wet


@dataclass
class FertilizerRecommendation:
    """Single fertilizer input recommendation."""
    input_name: str
    quantity_kg_per_acre: float
    timing: str
    notes: str = ""


@dataclass
class SoilAssessmentResult:
    """Output data model for soil assessment."""
    soil_class: str
    fertility_level: str
    confidence: float
    deficiencies: list[str] = field(default_factory=list)
    excesses: list[str] = field(default_factory=list)
    fertilizer_plan: list[FertilizerRecommendation] = field(default_factory=list)
    ph_status: str = ""
    recommendations_summary: str = ""
    suitable_for: list[str] = field(default_factory=list)


# Default rules embedded as fallback when JSON file is unavailable
_DEFAULT_RULES = {
    "soil_classification": {
        "Vertisol": {
            "description": "Black Cotton Soil — heavy clay, high shrink-swell",
            "ph_range": [6.0, 9.0],
            "indicators": ["high K", "moderate P", "heavy texture"],
        },
        "Inceptisol": {
            "description": "Alluvial / Loam — moderate fertility, well-drained",
            "ph_range": [6.5, 8.0],
            "indicators": ["balanced NPK", "light to medium texture"],
        },
        "Alfisol": {
            "description": "Red Laterite Soil — moderate to low fertility",
            "ph_range": [5.5, 7.5],
            "indicators": ["low P", "moderate N"],
        },
        "Entisol": {
            "description": "Sandy Soil — low water retention, low organic matter",
            "ph_range": [6.0, 8.5],
            "indicators": ["low N", "low P", "low OM"],
        },
    }
}


def _load_rules() -> dict:
    """Load soil classification rules from JSON file or use defaults."""
    rules_path = Path(config.SOIL_RULES_JSON)
    if rules_path.exists():
        try:
            with open(rules_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not load soil rules JSON: %s. Using defaults.", exc)
    return _DEFAULT_RULES


def _classify_soil(nitrogen: float, phosphorus: float, potassium: float,
                   ph_level: float, organic_matter: float) -> tuple[str, float]:
    """
    Classify soil type based on nutrient levels and pH.

    Returns:
        Tuple of (soil_class_name, confidence_score 0–1)
    """
    # Heuristic classification rules
    if ph_level >= 6.5 and potassium >= 55 and organic_matter < 2.5:
        return "Vertisol", 0.82
    elif ph_level >= 6.5 and nitrogen >= 50 and phosphorus >= 30 and organic_matter >= 1.5:
        return "Inceptisol", 0.79
    elif ph_level < 6.5 and phosphorus < 25:
        return "Alfisol", 0.75
    elif nitrogen < 30 and phosphorus < 20 and organic_matter < 1.0:
        return "Entisol", 0.72
    else:
        return "Inceptisol", 0.55  # Default to most common


def _assess_ph(ph: float) -> str:
    """Classify pH status."""
    if ph < 5.5:
        return "Very Acidic"
    elif ph < 6.5:
        return "Acidic"
    elif ph <= 7.5:
        return "Neutral (Optimal)"
    elif ph <= 8.5:
        return "Alkaline"
    return "Very Alkaline"


def _identify_deficiencies_and_excesses(
    nitrogen: float, phosphorus: float, potassium: float, ph: float, om: float
) -> tuple[list[str], list[str]]:
    """Identify nutrient deficiencies and excesses."""
    deficiencies = []
    excesses = []

    # Nitrogen
    if nitrogen < 35:
        deficiencies.append("Nitrogen (Low)")
    elif nitrogen > 85:
        excesses.append("Nitrogen (Excess — risk of leaching)")

    # Phosphorus
    if phosphorus < 20:
        deficiencies.append("Phosphorus (Low)")
    elif phosphorus > 80:
        excesses.append("Phosphorus (Excess)")

    # Potassium
    if potassium < 40:
        deficiencies.append("Potassium (Low)")

    # Micronutrient proxies
    if ph > 7.8:
        deficiencies.append("Zinc (likely immobilized at alkaline pH)")
    if ph < 6.0:
        deficiencies.append("Calcium/Magnesium (acidic soil)")

    # Organic matter
    if om < 0.5:
        deficiencies.append("Organic Matter (Critical — impairs soil structure)")
    elif om < 1.5:
        deficiencies.append("Organic Matter (Low)")

    return deficiencies, excesses


def _build_fertilizer_plan(
    soil_class: str,
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    ph: float,
    deficiencies: list[str],
) -> list[FertilizerRecommendation]:
    """Generate fertilizer recommendations based on soil classification and deficiencies."""
    plan = []

    # Nitrogen management
    n_urea_kg = max(0, min(80, 60 - (nitrogen - 35) * 0.5))
    if n_urea_kg > 5:
        plan.append(FertilizerRecommendation(
            input_name="Urea (46% N)",
            quantity_kg_per_acre=round(n_urea_kg, 1),
            timing="Split: 50% at sowing + 50% at 30 days",
        ))

    # Phosphorus
    p_dap_kg = max(0, min(50, 25 - (phosphorus - 20) * 0.3))
    if p_dap_kg > 3:
        plan.append(FertilizerRecommendation(
            input_name="DAP (18N:46P)",
            quantity_kg_per_acre=round(p_dap_kg, 1),
            timing="Basal dose at sowing",
        ))

    # Potassium
    if potassium < 40:
        plan.append(FertilizerRecommendation(
            input_name="MOP (60% K2O)",
            quantity_kg_per_acre=20,
            timing="Basal dose at sowing",
        ))

    # Zinc correction for alkaline soils
    if any("Zinc" in d for d in deficiencies):
        plan.append(FertilizerRecommendation(
            input_name="Zinc Sulphate (ZnSO₄)",
            quantity_kg_per_acre=10,
            timing="Basal dose once per 3 seasons",
            notes="Apply before sowing and mix into topsoil",
        ))

    # Organic matter correction
    if any("Organic Matter" in d for d in deficiencies):
        plan.append(FertilizerRecommendation(
            input_name="Farm Yard Manure (FYM)",
            quantity_kg_per_acre=500,
            timing="2–3 weeks before sowing",
            notes="Improves soil structure and moisture retention",
        ))

    # Lime for acid soils
    if ph < 6.0:
        plan.append(FertilizerRecommendation(
            input_name="Agricultural Lime (CaCO₃)",
            quantity_kg_per_acre=100,
            timing="6–8 weeks before sowing",
            notes="Raises pH to 6.5–7.0 range",
        ))

    return plan


def _fertility_level(nitrogen: float, phosphorus: float, potassium: float) -> str:
    """Compute overall fertility level."""
    avg_score = (
        min(nitrogen / 60, 1.0) * 40
        + min(phosphorus / 40, 1.0) * 30
        + min(potassium / 70, 1.0) * 30
    )
    if avg_score >= 70:
        return "High"
    elif avg_score >= 45:
        return "Medium"
    return "Low"


def analyze_soil(
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    ph_level: float,
    organic_matter: float = 0.0,
    moisture_level: str = "Moderate",
) -> SoilAssessmentResult:
    """
    Analyze soil conditions and generate classification + fertilizer plan.

    Args:
        nitrogen: N content in kg/ha (0–100)
        phosphorus: P content in kg/ha (0–100)
        potassium: K content in kg/ha (0–100)
        ph_level: Soil pH (0–14)
        organic_matter: Organic matter percentage (0–20)
        moisture_level: Categorical moisture (Dry/Moderate/Wet)

    Returns:
        SoilAssessmentResult with full classification and recommendations
    """
    # Input range clipping (safe guards against malformed data)
    nitrogen = max(0.0, min(100.0, nitrogen))
    phosphorus = max(0.0, min(100.0, phosphorus))
    potassium = max(0.0, min(100.0, potassium))
    ph_level = max(0.0, min(14.0, ph_level))
    organic_matter = max(0.0, min(20.0, organic_matter))

    soil_class, confidence = _classify_soil(nitrogen, phosphorus, potassium, ph_level, organic_matter)
    ph_status = _assess_ph(ph_level)
    deficiencies, excesses = _identify_deficiencies_and_excesses(
        nitrogen, phosphorus, potassium, ph_level, organic_matter
    )
    fertilizer_plan = _build_fertilizer_plan(
        soil_class, nitrogen, phosphorus, potassium, ph_level, deficiencies
    )
    fertility = _fertility_level(nitrogen, phosphorus, potassium)

    # Suitable crop hints based on soil class
    suitable_crops = {
        "Vertisol": ["Cotton", "Soybean", "Sorghum", "Chickpea"],
        "Inceptisol": ["Wheat", "Rice", "Maize", "Sugarcane"],
        "Alfisol": ["Groundnut", "Ragi", "Sorghum", "Sunflower"],
        "Entisol": ["Pearl Millet", "Sorghum", "Cowpea", "Sesame"],
    }.get(soil_class, ["Sorghum", "Pearl Millet"])

    summary_lines = [
        f"Soil classified as {soil_class} ({_load_rules().get('soil_classification', {}).get(soil_class, {}).get('description', soil_class)})",
        f"pH {ph_level:.1f} — {ph_status}",
        f"Fertility level: {fertility}",
    ]
    if deficiencies:
        summary_lines.append("Deficiencies detected: " + "; ".join(deficiencies))
    if excesses:
        summary_lines.append("Excesses noted: " + "; ".join(excesses))
    summary_lines.append(f"Recommended crops for this soil: {', '.join(suitable_crops)}")

    logger.info(
        "Soil analysis complete: class=%s, fertility=%s, confidence=%.2f",
        soil_class, fertility, confidence
    )

    return SoilAssessmentResult(
        soil_class=soil_class,
        fertility_level=fertility,
        confidence=confidence,
        deficiencies=deficiencies,
        excesses=excesses,
        fertilizer_plan=fertilizer_plan,
        ph_status=ph_status,
        recommendations_summary="\n".join(summary_lines),
        suitable_for=suitable_crops,
    )
