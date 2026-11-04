"""
tests/test_crop_suitability.py
--------------------------------
Unit tests for crop suitability ranking.
Run with: pytest tests/test_crop_suitability.py -v
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.crop_db_tool import get_candidate_crops, _soil_compatibility, _water_compatibility, _seasonal_fit


class TestCropDBTool:
    """Unit tests for crop_db_tool.py"""

    def test_kharif_cotton_ranked_high_for_vertisol(self):
        """Cotton should rank high for Vertisol soil in Kharif season."""
        crops = get_candidate_crops(soil_type="Vertisol", season="Kharif", water_source="Borewell")
        top_crops = [c.crop_name for c in crops[:3]]
        assert "Cotton" in top_crops, f"Cotton not in top 3: {top_crops}"

    def test_rabi_wheat_ranked_high_for_alluvial(self):
        """Wheat should rank high for Alluvial Loam in Rabi season."""
        crops = get_candidate_crops(soil_type="Alluvial Loam", season="Rabi", water_source="Canal")
        top_crops = [c.crop_name for c in crops[:3]]
        assert "Wheat" in top_crops, f"Wheat not in top 3: {top_crops}"

    def test_top_n_respected(self):
        """top_n parameter should limit results."""
        crops = get_candidate_crops(soil_type="Vertisol", season="Kharif", water_source="Rainfall", top_n=3)
        assert len(crops) <= 3

    def test_scores_are_bounded(self):
        """All suitability scores should be 0–100."""
        crops = get_candidate_crops(soil_type="Inceptisol", season="Rabi", water_source="Canal")
        for crop in crops:
            assert 0 <= crop.suitability_score <= 100, f"Score out of range for {crop.crop_name}"

    def test_ranked_in_descending_order(self):
        """Crops should be ranked in descending score order."""
        crops = get_candidate_crops(soil_type="Vertisol", season="Kharif", water_source="Rainfall")
        scores = [c.suitability_score for c in crops]
        assert scores == sorted(scores, reverse=True)

    def test_rank_starts_at_1(self):
        """Rank should start at 1."""
        crops = get_candidate_crops(soil_type="Vertisol", season="Kharif", water_source="Borewell")
        assert crops[0].rank == 1

    def test_score_breakdown_keys_present(self):
        """Score breakdown should contain all four scoring dimensions."""
        crops = get_candidate_crops(soil_type="Vertisol", season="Kharif", water_source="Borewell")
        for crop in crops:
            assert "soil_match" in crop.score_breakdown
            assert "water_availability" in crop.score_breakdown
            assert "seasonal_fit" in crop.score_breakdown
            assert "market_demand" in crop.score_breakdown

    def test_mismatched_season_penalizes_score(self):
        """A Rabi crop ranked in Kharif should score lower on seasonal_fit."""
        from tools.crop_db_tool import _seasonal_fit
        kharif_fit = _seasonal_fit("Kharif", "Kharif")
        rabi_in_kharif = _seasonal_fit("Rabi", "Kharif")
        assert kharif_fit > rabi_in_kharif


class TestScoringFunctions:
    """Unit tests for individual scoring sub-functions."""

    def test_soil_exact_match_scores_100(self):
        score = _soil_compatibility("Vertisol", "Vertisol,Inceptisol")
        assert score == 100.0

    def test_soil_alias_match_near_100(self):
        score = _soil_compatibility("Black Cotton", "Vertisol,Alfisol")
        assert score >= 85

    def test_soil_no_match_low_score(self):
        score = _soil_compatibility("Sandy", "Vertisol,Inceptisol")
        assert score <= 40

    def test_water_sufficient_scores_100(self):
        score = _water_compatibility("Canal", 600)
        assert score == 100.0

    def test_water_insufficient_scores_below_100(self):
        score = _water_compatibility("Rainfall", 800)  # Rainfall = 400mm; need 800mm
        assert score < 100

    def test_seasonal_exact_match(self):
        score = _seasonal_fit("Kharif", "Kharif")
        assert score == 100.0

    def test_seasonal_mismatch_penalized(self):
        score = _seasonal_fit("Rabi", "Kharif")
        assert score <= 50
