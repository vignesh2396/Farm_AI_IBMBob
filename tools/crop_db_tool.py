"""
tools/crop_db_tool.py
----------------------
Tool: CSV-based crop reference database lookup.
Filters and ranks crops based on soil type, season, water source, and climate.

Usage:
    from tools.crop_db_tool import get_candidate_crops
    crops = get_candidate_crops(soil_type="Vertisol", season="Kharif", water_source="Borewell")
"""
import csv
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from utils.config import config
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CropCandidate:
    """A candidate crop with its suitability profile."""
    crop_id: int
    crop_name: str
    season: str
    suitable_soils: list[str]
    min_rainfall_mm: float
    max_temp_c: float
    min_temp_c: float
    water_req_mm: float
    avg_yield_qtl: float
    market_demand: str  # High | Medium | Low
    duration_days: int
    notes: str = ""


@dataclass
class RankedCrop:
    """A crop with its computed suitability score."""
    rank: int
    crop_name: str
    suitability_score: int  # 0–100
    score_breakdown: dict = field(default_factory=dict)
    justification: str = ""
    duration_days: int = 0
    avg_yield_qtl: float = 0.0
    market_demand: str = "Medium"


# Embedded fallback crop dataset (used when CSV is missing)
_FALLBACK_CROPS = [
    {"crop_id": 1, "crop_name": "Cotton", "season": "Kharif",
     "suitable_soils": "Vertisol,Black Cotton,Alfisol",
     "min_rainfall_mm": 500, "max_temp_c": 43, "min_temp_c": 20,
     "water_req_mm": 700, "avg_yield_qtl": 8, "market_demand": "High", "duration_days": 180},
    {"crop_id": 2, "crop_name": "Soybean", "season": "Kharif",
     "suitable_soils": "Vertisol,Inceptisol,Alfisol",
     "min_rainfall_mm": 450, "max_temp_c": 38, "min_temp_c": 18,
     "water_req_mm": 500, "avg_yield_qtl": 12, "market_demand": "High", "duration_days": 100},
    {"crop_id": 3, "crop_name": "Pigeonpea", "season": "Kharif",
     "suitable_soils": "Vertisol,Alfisol,Entisol",
     "min_rainfall_mm": 400, "max_temp_c": 40, "min_temp_c": 18,
     "water_req_mm": 450, "avg_yield_qtl": 9, "market_demand": "Medium", "duration_days": 160},
    {"crop_id": 4, "crop_name": "Groundnut", "season": "Kharif",
     "suitable_soils": "Alfisol,Entisol,Inceptisol",
     "min_rainfall_mm": 500, "max_temp_c": 38, "min_temp_c": 22,
     "water_req_mm": 500, "avg_yield_qtl": 18, "market_demand": "High", "duration_days": 120},
    {"crop_id": 5, "crop_name": "Green Gram", "season": "Kharif",
     "suitable_soils": "Inceptisol,Alfisol,Entisol",
     "min_rainfall_mm": 350, "max_temp_c": 40, "min_temp_c": 20,
     "water_req_mm": 350, "avg_yield_qtl": 6, "market_demand": "Medium", "duration_days": 70},
    {"crop_id": 6, "crop_name": "Wheat", "season": "Rabi",
     "suitable_soils": "Inceptisol,Vertisol,Alfisol",
     "min_rainfall_mm": 250, "max_temp_c": 30, "min_temp_c": 5,
     "water_req_mm": 400, "avg_yield_qtl": 35, "market_demand": "High", "duration_days": 120},
    {"crop_id": 7, "crop_name": "Chickpea", "season": "Rabi",
     "suitable_soils": "Vertisol,Inceptisol,Alfisol",
     "min_rainfall_mm": 200, "max_temp_c": 30, "min_temp_c": 5,
     "water_req_mm": 300, "avg_yield_qtl": 12, "market_demand": "High", "duration_days": 110},
    {"crop_id": 8, "crop_name": "Mustard", "season": "Rabi",
     "suitable_soils": "Inceptisol,Alfisol,Entisol",
     "min_rainfall_mm": 200, "max_temp_c": 28, "min_temp_c": 5,
     "water_req_mm": 250, "avg_yield_qtl": 10, "market_demand": "Medium", "duration_days": 110},
    {"crop_id": 9, "crop_name": "Sorghum (Jowar)", "season": "Kharif",
     "suitable_soils": "Vertisol,Alfisol,Entisol,Inceptisol",
     "min_rainfall_mm": 350, "max_temp_c": 42, "min_temp_c": 18,
     "water_req_mm": 400, "avg_yield_qtl": 20, "market_demand": "Medium", "duration_days": 110},
    {"crop_id": 10, "crop_name": "Pearl Millet (Bajra)", "season": "Kharif",
     "suitable_soils": "Entisol,Alfisol,Inceptisol",
     "min_rainfall_mm": 300, "max_temp_c": 44, "min_temp_c": 22,
     "water_req_mm": 300, "avg_yield_qtl": 18, "market_demand": "Medium", "duration_days": 90},
]


def _load_crops() -> list[dict]:
    """Load crop reference from CSV or use fallback embedded data."""
    csv_path = Path(config.CROP_REFERENCE_CSV)
    if csv_path.exists():
        try:
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                crops = list(reader)
            logger.info("Loaded %d crops from %s", len(crops), csv_path)
            return crops
        except (OSError, csv.Error) as exc:
            logger.warning("Failed to load crop CSV: %s. Using fallback data.", exc)
    logger.info("Using embedded fallback crop database (%d crops)", len(_FALLBACK_CROPS))
    return _FALLBACK_CROPS


def _water_compatibility(water_source: str, water_req_mm: float) -> float:
    """
    Score water availability vs. crop requirement.
    Returns 0–100 score.
    """
    water_capacity_map = {
        "Canal": 900,
        "River": 800,
        "Borewell": 600,
        "Tank": 500,
        "Rainfall": 400,
    }
    available_mm = water_capacity_map.get(water_source, 500)
    if available_mm >= water_req_mm:
        return 100.0
    ratio = available_mm / max(water_req_mm, 1)
    return round(ratio * 100, 1)


def _soil_compatibility(soil_type: str, suitable_soils_str: str) -> float:
    """Return 100 if soil_type appears in suitable_soils list, else 40 (partial)."""
    suitable = [s.strip() for s in suitable_soils_str.split(",")]
    if soil_type in suitable:
        return 100.0
    # Partial match (e.g., "Black Cotton" matches "Vertisol" context)
    soil_aliases = {
        "Black Cotton": "Vertisol",
        "Red Laterite": "Alfisol",
        "Sandy": "Entisol",
        "Loam": "Inceptisol",
        "Alluvial Loam": "Inceptisol",
        "Clay": "Vertisol",
        "Silt": "Inceptisol",
    }
    canonical = soil_aliases.get(soil_type, soil_type)
    if canonical in suitable:
        return 90.0
    return 35.0


def _seasonal_fit(crop_season: str, farm_season: str) -> float:
    """Return 100 if seasons match, 40 if related (Kharif crops sometimes work in Zaid)."""
    if crop_season.lower() == farm_season.lower():
        return 100.0
    if {crop_season.lower(), farm_season.lower()} & {"zaid", "kharif"}:
        return 50.0
    return 20.0


def _market_score(demand: str) -> float:
    """Convert market demand label to a score."""
    return {"High": 100.0, "Medium": 65.0, "Low": 30.0}.get(demand, 50.0)


def _compute_suitability_score(
    crop: dict,
    soil_type: str,
    season: str,
    water_source: str,
) -> tuple[int, dict]:
    """
    Compute weighted suitability score for a crop.

    Weights: soil(35%) + water(25%) + season(25%) + market(15%)
    """
    try:
        water_req = float(crop.get("water_req_mm", 500))
        suitable_soils = str(crop.get("suitable_soils", ""))
        market = str(crop.get("market_demand", "Medium"))
        crop_season = str(crop.get("season", season))

        soil_s = _soil_compatibility(soil_type, suitable_soils)
        water_s = _water_compatibility(water_source, water_req)
        season_s = _seasonal_fit(crop_season, season)
        market_s = _market_score(market)

        total = (soil_s * 0.35) + (water_s * 0.25) + (season_s * 0.25) + (market_s * 0.15)
        breakdown = {
            "soil_match": round(soil_s),
            "water_availability": round(water_s),
            "seasonal_fit": round(season_s),
            "market_demand": round(market_s),
        }
        return round(total), breakdown
    except (TypeError, ValueError) as exc:
        logger.warning("Score computation error for %s: %s", crop.get("crop_name"), exc)
        return 0, {}


def get_candidate_crops(
    soil_type: str,
    season: str,
    water_source: str,
    top_n: int = 8,
    min_score: int = 0,
) -> list[RankedCrop]:
    """
    Filter and rank crops from the reference database.

    Args:
        soil_type: Classified soil type (e.g., "Vertisol", "Black Cotton")
        season: Current season (Kharif | Rabi | Zaid)
        water_source: Irrigation source (Canal | Borewell | Rainfall | Tank | River)
        top_n: Maximum number of crops to return
        min_score: Minimum suitability score to include (0–100)

    Returns:
        List of RankedCrop sorted by suitability_score descending
    """
    all_crops = _load_crops()
    scored = []

    for crop in all_crops:
        score, breakdown = _compute_suitability_score(crop, soil_type, season, water_source)
        if score < min_score:
            continue

        justification_parts = []
        if breakdown.get("soil_match", 0) >= 90:
            justification_parts.append(f"Excellent soil compatibility for {soil_type}")
        elif breakdown.get("soil_match", 0) >= 60:
            justification_parts.append(f"Moderate soil compatibility for {soil_type}")
        else:
            justification_parts.append(f"Limited soil compatibility — consider soil amendment")

        if breakdown.get("water_availability", 0) >= 80:
            justification_parts.append(f"{water_source} water source meets crop requirement")
        else:
            justification_parts.append(f"Water availability may be limiting — plan irrigation carefully")

        if breakdown.get("seasonal_fit", 0) == 100:
            justification_parts.append(f"Ideal {season} season crop")

        demand = str(crop.get("market_demand", "Medium"))
        if demand == "High":
            justification_parts.append("Strong market demand")

        scored.append(RankedCrop(
            rank=0,
            crop_name=str(crop.get("crop_name", "Unknown")),
            suitability_score=score,
            score_breakdown=breakdown,
            justification=" | ".join(justification_parts),
            duration_days=int(crop.get("duration_days", 120)),
            avg_yield_qtl=float(crop.get("avg_yield_qtl", 0)),
            market_demand=demand,
        ))

    scored.sort(key=lambda c: c.suitability_score, reverse=True)
    top = scored[:top_n]
    for i, crop in enumerate(top, start=1):
        crop.rank = i

    logger.info(
        "Crop ranking: top=%s (%d/%d), %d crops scored",
        top[0].crop_name if top else "N/A",
        top[0].suitability_score if top else 0,
        100,
        len(scored),
    )
    return top
