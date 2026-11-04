"""
tests/test_validation.py
-------------------------
Tests for the validation tool and high-impact flagging.
Run with: pytest tests/test_validation.py -v
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.validation_tool import (
    validate_soil_inputs,
    validate_crop_suitability_result,
    flag_high_impact,
    check_groundedness,
    validate_llm_output_json,
)


class TestHighImpactFlagging:
    """Tests for high-impact recommendation detection."""

    def test_pesticide_mention_flagged(self):
        result = flag_high_impact("Apply pesticide at high dosage")
        assert result.is_high_impact is True

    def test_banned_chemical_flagged_and_invalid(self):
        result = flag_high_impact("Use endosulfan for bollworm control")
        assert result.is_high_impact is True
        assert result.is_valid is False  # Banned chemical = invalid, not just flagged

    def test_safe_recommendation_not_flagged(self):
        result = flag_high_impact("Apply urea at 60 kg/acre during sowing and irrigate after")
        assert result.is_high_impact is False

    def test_ipm_recommendation_not_flagged(self):
        result = flag_high_impact("Use Trichogramma cards for bollworm biological control at 50,000/acre")
        assert result.is_high_impact is False

    def test_fym_recommendation_not_flagged(self):
        result = flag_high_impact("Apply FYM 5 tonnes per acre as basal dose two weeks before sowing")
        assert result.is_high_impact is False


class TestGroundednessCheck:
    """Tests for RAG groundedness scoring."""

    def test_empty_sources_returns_zero(self):
        score = check_groundedness("Cotton should be sown at 90x60 cm spacing", [])
        assert score == 0.0

    def test_matching_content_scores_higher(self):
        sources = [{"text": "Cotton spacing should be 90cm x 60cm for black cotton soil cultivation"}]
        answer = "Cotton should be sown at 90cm x 60cm spacing in black cotton soil"
        score = check_groundedness(answer, sources)
        assert score > 0.3  # Should have meaningful overlap

    def test_unrelated_answer_scores_lower(self):
        sources = [{"text": "Cotton spacing should be 90cm x 60cm for black cotton soil"}]
        answer = "The weather in Mumbai is generally humid with good rainfall"
        score = check_groundedness(answer, sources)
        # Less related → lower score
        matching = check_groundedness("Cotton spacing 90cm row plant", sources)
        assert score <= matching

    def test_score_bounded_0_to_1(self):
        sources = [{"text": "test content with multiple words"}]
        answer = "test content with multiple words and more content"
        score = check_groundedness(answer, sources)
        assert 0.0 <= score <= 1.0


class TestLLMOutputValidation:
    """Tests for LLM JSON output validation."""

    def test_valid_json_passes(self):
        result = validate_llm_output_json('{"crop": "Cotton", "weeks": []}', ["crop", "weeks"])
        assert result.is_valid is True

    def test_json_in_markdown_fence_extracted(self):
        raw = '```json\n{"crop": "Cotton", "weeks": []}\n```'
        result = validate_llm_output_json(raw, ["crop"])
        assert result.is_valid is True

    def test_invalid_json_fails(self):
        result = validate_llm_output_json("this is not json at all", ["crop"])
        assert result.is_valid is False

    def test_missing_keys_produce_warnings(self):
        result = validate_llm_output_json('{"crop": "Cotton"}', ["crop", "weeks", "season"])
        assert len(result.warnings) > 0
        assert result.is_valid is True  # Missing keys = warning, not error
