"""
tests/test_soil_agent.py
-------------------------
Unit tests for the Soil Assessment Tool and Agent.
Run with: pytest tests/test_soil_agent.py -v
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.soil_analysis_tool import analyze_soil, SoilInput, SoilAssessmentResult
from tools.validation_tool import validate_soil_inputs


class TestSoilAnalysisTool:
    """Unit tests for soil_analysis_tool.py"""

    def test_vertisol_classification(self):
        """Black cotton soil (Vertisol) should be correctly identified."""
        result = analyze_soil(nitrogen=42, phosphorus=18, potassium=65, ph_level=7.2, organic_matter=1.8)
        assert result.soil_class == "Vertisol"
        assert result.confidence >= 0.70

    def test_high_fertility_soil(self):
        """High NPK values should produce High fertility classification."""
        result = analyze_soil(nitrogen=80, phosphorus=70, potassium=80, ph_level=6.8, organic_matter=3.0)
        assert result.fertility_level == "High"

    def test_low_fertility_soil(self):
        """Low NPK values should produce Low fertility classification."""
        result = analyze_soil(nitrogen=10, phosphorus=5, potassium=15, ph_level=6.0, organic_matter=0.3)
        assert result.fertility_level == "Low"

    def test_nitrogen_deficiency_detected(self):
        """Low nitrogen should appear in deficiencies list."""
        result = analyze_soil(nitrogen=20, phosphorus=40, potassium=60, ph_level=7.0)
        assert any("Nitrogen" in d for d in result.deficiencies)

    def test_alkaline_ph_zinc_deficiency(self):
        """High pH should flag zinc deficiency (common in alkaline soils)."""
        result = analyze_soil(nitrogen=50, phosphorus=30, potassium=60, ph_level=8.5, organic_matter=1.5)
        assert any("Zinc" in d for d in result.deficiencies)

    def test_fertilizer_plan_generated(self):
        """Fertilizer plan should be non-empty for deficient soil."""
        result = analyze_soil(nitrogen=25, phosphorus=12, potassium=30, ph_level=7.0)
        assert len(result.fertilizer_plan) > 0

    def test_suitable_crops_returned(self):
        """Suitable crops list should be non-empty."""
        result = analyze_soil(nitrogen=42, phosphorus=18, potassium=65, ph_level=7.2)
        assert len(result.suitable_for) > 0

    def test_input_clipping_out_of_range(self):
        """Out-of-range values should be clipped, not crash."""
        result = analyze_soil(nitrogen=200, phosphorus=-5, potassium=65, ph_level=7.2)
        assert result.soil_class is not None  # Should not raise

    def test_ph_status_neutral(self):
        """pH 7.0 should produce Neutral pH status."""
        result = analyze_soil(nitrogen=50, phosphorus=30, potassium=60, ph_level=7.0)
        assert "Neutral" in result.ph_status

    def test_ph_status_very_acidic(self):
        """pH 4.5 should produce Very Acidic status."""
        result = analyze_soil(nitrogen=40, phosphorus=20, potassium=50, ph_level=4.5)
        assert "Acidic" in result.ph_status


class TestSoilInputValidation:
    """Tests for soil input validation."""

    def test_valid_inputs(self):
        result = validate_soil_inputs(40, 20, 60, 7.2, 1.8)
        assert result.is_valid is True
        assert len(result.issues) == 0

    def test_invalid_ph_too_high(self):
        result = validate_soil_inputs(40, 20, 60, 16.0, 1.5)  # pH > 14
        assert result.is_valid is False
        assert any("pH" in issue or "ph_level" in issue.lower() for issue in result.issues)

    def test_invalid_nitrogen_negative(self):
        result = validate_soil_inputs(-10, 20, 60, 7.0, 1.5)
        assert result.is_valid is False

    def test_extreme_ph_warning(self):
        result = validate_soil_inputs(40, 20, 60, 4.0, 1.5)  # Extreme but technically valid
        assert len(result.warnings) > 0

    def test_all_zero_npk_warning(self):
        result = validate_soil_inputs(0, 0, 0, 7.0, 1.5)
        assert result.is_valid is True  # Not an error — but should warn
        assert len(result.warnings) > 0
