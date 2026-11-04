"""
agents/soil_assessment_agent.py
--------------------------------
Soil Assessment Agent: Combines rule-based soil classification with LLM explanation.
Uses soil_analysis_tool for classification and Gemini for enhanced narrative recommendations.
"""
import json
import re
import time
from typing import Any, Optional

from tools.soil_analysis_tool import analyze_soil
from tools.validation_tool import validate_soil_inputs
from utils.helpers import sanitize_input
from utils.logger import get_logger

logger = get_logger(__name__)

_ASSESSMENT_PROMPT_TEMPLATE = """
You are an expert agricultural soil scientist. You have received the following soil analysis results for a farmer's field.

Farm Context:
- Location: {district}, {state}
- Farm Size: {farm_size} acres
- Soil Type (Farmer-reported): {soil_type}
- Season: {current_season}

Soil Analysis Results:
- Soil Classification: {soil_class}
- Fertility Level: {fertility_level}
- pH Level: {ph_level} ({ph_status})
- Nitrogen: {nitrogen} kg/ha
- Phosphorus: {phosphorus} kg/ha
- Potassium: {potassium} kg/ha
- Organic Matter: {organic_matter}%
- Deficiencies: {deficiencies}
- Confidence Score: {confidence:.0%}

Fertilizer Plan Recommended:
{fertilizer_plan_text}

Instructions:
1. Provide a brief (3–4 sentence) plain-language explanation suitable for a smallholder farmer.
2. Highlight the most critical nutrient issue and what it means for crop growth.
3. Give ONE practical tip for improving soil health.
4. Do NOT include any chemical trade names or restricted substances.
5. End with a responsible AI disclaimer: "These are AI-generated recommendations. Please verify with your local Krishi Vigyan Kendra."

Respond only with the plain-language summary. No JSON, no bullet headers.
"""


class SoilAssessmentAgent:
    """
    Soil Assessment Agent for FarmAI.

    Responsibilities:
    - Validate soil input data
    - Run rule-based soil classification (soil_analysis_tool)
    - Enrich result with LLM-generated narrative explanation
    - Return structured assessment with explainability info
    """

    def __init__(self, llm, session_id: str):
        self.llm = llm
        self.session_id = session_id

    def assess(self, soil_data: dict, farm_profile: dict = None) -> dict:
        """
        Run soil assessment workflow.

        Args:
            soil_data: Dict with nitrogen, phosphorus, potassium, ph_level, organic_matter
            farm_profile: Optional farm profile for contextual recommendations

        Returns:
            Structured soil assessment result dict
        """
        farm_profile = farm_profile or {}

        # Extract and validate inputs
        n = float(soil_data.get("nitrogen", 0))
        p = float(soil_data.get("phosphorus", 0))
        k = float(soil_data.get("potassium", 0))
        ph = float(soil_data.get("ph_level", 7.0))
        om = float(soil_data.get("organic_matter", 0))
        moisture = str(soil_data.get("moisture_level", "Moderate"))

        validation = validate_soil_inputs(n, p, k, ph, om)
        if not validation.is_valid:
            return {
                "status": "error",
                "errors": validation.issues,
                "warnings": validation.warnings,
            }

        # Run rule-based classification
        result = analyze_soil(
            nitrogen=n, phosphorus=p, potassium=k,
            ph_level=ph, organic_matter=om, moisture_level=moisture
        )

        # Build fertilizer plan text for prompt
        fert_lines = []
        for rec in result.fertilizer_plan:
            fert_lines.append(
                f"- {rec.input_name}: {rec.quantity_kg_per_acre} kg/acre | {rec.timing}"
                + (f" | Note: {rec.notes}" if rec.notes else "")
            )
        fertilizer_plan_text = "\n".join(fert_lines) if fert_lines else "No specific fertilizer needed."

        # Generate LLM narrative explanation
        narrative = self._generate_narrative(
            result, farm_profile, n, p, k, ph, om, fertilizer_plan_text
        )

        # Serialize fertilizer plan
        fert_plan_dict = [
            {
                "input_name": r.input_name,
                "quantity_kg_per_acre": r.quantity_kg_per_acre,
                "timing": r.timing,
                "notes": r.notes,
            }
            for r in result.fertilizer_plan
        ]

        assessment_output = {
            "status": "success",
            "soil_class": result.soil_class,
            "fertility_level": result.fertility_level,
            "confidence": result.confidence,
            "ph_status": result.ph_status,
            "deficiencies": result.deficiencies,
            "excesses": result.excesses,
            "fertilizer_plan": fert_plan_dict,
            "suitable_crops": result.suitable_for,
            "narrative_explanation": narrative,
            "warnings": validation.warnings,
            "explainability": {
                "data_inputs": {
                    "nitrogen_kg_ha": n,
                    "phosphorus_kg_ha": p,
                    "potassium_kg_ha": k,
                    "ph_level": ph,
                    "organic_matter_pct": om,
                },
                "rules_applied": [
                    f"pH {ph:.1f} → {result.ph_status}",
                    f"N={n} → {'Deficient' if n < 35 else 'Adequate'}",
                    f"Soil class determined by NPK + pH heuristics",
                ],
                "sources": ["ICAR Fertilizer Guide 2024", "Soil Health Card Scheme Guidelines"],
                "confidence_label": self._confidence_label(result.confidence),
            },
        }

        logger.info(
            "Soil assessment complete: class=%s, fertility=%s, confidence=%.0f%%",
            result.soil_class, result.fertility_level, result.confidence * 100
        )
        return assessment_output

    def _generate_narrative(
        self,
        result,
        farm_profile: dict,
        n: float, p: float, k: float, ph: float, om: float,
        fertilizer_plan_text: str,
    ) -> str:
        """Generate LLM narrative for the soil assessment result."""
        if self.llm is None:
            return (
                f"Your soil is classified as {result.soil_class} with {result.fertility_level} fertility. "
                f"pH is {ph:.1f} ({result.ph_status}). "
                + (f"Key deficiencies: {', '.join(result.deficiencies)}. " if result.deficiencies else "")
                + "Please consult your local agricultural extension officer for site-specific advice."
            )

        prompt = _ASSESSMENT_PROMPT_TEMPLATE.format(
            district=farm_profile.get("district", "your region"),
            state=farm_profile.get("state", "India"),
            farm_size=farm_profile.get("farm_size", "N/A"),
            soil_type=farm_profile.get("soil_type", result.soil_class),
            current_season=farm_profile.get("current_season", "Kharif"),
            soil_class=result.soil_class,
            fertility_level=result.fertility_level,
            ph_level=ph,
            ph_status=result.ph_status,
            nitrogen=n, phosphorus=p, potassium=k,
            organic_matter=om,
            deficiencies=", ".join(result.deficiencies) if result.deficiencies else "None detected",
            confidence=result.confidence,
            fertilizer_plan_text=fertilizer_plan_text,
        )

        try:
            response = self.llm.generate_content(prompt)
            narrative = response.text.strip()
            logger.debug("LLM narrative generated (%d chars)", len(narrative))
            return narrative
        except Exception as exc:
            logger.error("LLM narrative generation failed: %s", exc)
            return result.recommendations_summary

    @staticmethod
    def _confidence_label(score: float) -> str:
        if score >= 0.85:
            return "HIGH"
        elif score >= 0.65:
            return "MEDIUM"
        elif score >= 0.45:
            return "LOW"
        return "VERY LOW"
