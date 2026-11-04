"""
agents/farm_ops_planning_agent.py
----------------------------------
Farm Operations Planning Agent: Generates a week-by-week seasonal farm operations plan
using Gemini LLM, incorporating soil, weather, and crop data.
"""
import json
import re

from tools.validation_tool import flag_high_impact
from utils.logger import get_logger

logger = get_logger(__name__)

_PLAN_PROMPT = """
You are an expert agricultural extension officer creating a seasonal farm operations plan.

Farm Details:
- Location: {district}, {state}
- Farm Size: {farm_size} acres
- Soil Type: {soil_class} ({fertility_level} fertility)
- Selected Crop: {selected_crop}
- Season: {season}
- Water Source: {water_source}
- Previous Crop: {prev_crop}

Soil Recommendations:
{fertilizer_summary}

Weather Conditions:
{weather_summary}

Instructions:
Create a realistic {duration_weeks}-week farm operations plan from sowing to harvest.
For each week, include:
1. Primary farming activities (land prep, sowing, irrigation, fertilization, pest scouting, harvest)
2. Irrigation guidance (frequency and method)
3. Any weather-related cautions or adjustments

Format your response as valid JSON:
{{
  "crop": "{selected_crop}",
  "season": "{season}",
  "total_weeks": {duration_weeks},
  "weeks": [
    {{
      "week": 1,
      "phase": "Land Preparation",
      "activities": ["Activity 1", "Activity 2"],
      "irrigation": "Pre-sowing irrigation if soil is dry",
      "weather_note": null,
      "inputs": ["FYM 5 tonnes/acre"]
    }}
  ],
  "harvest_window": "Week 14–16",
  "expected_yield_qtl_per_acre": 8.0,
  "key_risks": ["Bollworm during boll development", "Drought if borewell fails"]
}}

Use only safe, standard agricultural practices. Do not recommend restricted pesticides.
Respond ONLY with the JSON object. No extra text.
"""


class FarmOpsPlanningAgent:
    """
    Farm Operations Planning Agent for FarmAI.

    Responsibilities:
    - Build a contextual prompt from farm profile, soil, and weather data
    - Generate a week-by-week seasonal operations plan via Gemini LLM
    - Validate the plan for high-impact content
    - Return structured plan with explainability metadata
    """

    CROP_DURATIONS = {
        "Cotton": 22, "Soybean": 16, "Pigeonpea": 24, "Groundnut": 18,
        "Green Gram": 10, "Wheat": 20, "Chickpea": 16, "Mustard": 16,
        "Sorghum (Jowar)": 16, "Pearl Millet (Bajra)": 14,
    }

    def __init__(self, llm, session_id: str):
        self.llm = llm
        self.session_id = session_id

    def generate_plan(
        self,
        farm_profile: dict,
        soil_result: dict,
        weather_data: dict,
        selected_crop: str,
    ) -> dict:
        """
        Generate a seasonal farm operations plan.

        Args:
            farm_profile: Farm profile dict
            soil_result: Soil assessment result dict
            weather_data: Weather intelligence result dict
            selected_crop: The crop selected by the farmer

        Returns:
            Farm operations plan dict with high_impact_flag and explainability
        """
        duration_weeks = self.CROP_DURATIONS.get(selected_crop, 16)

        # Build fertilizer summary
        fert_plan = soil_result.get("fertilizer_plan", [])
        fert_summary = "\n".join(
            f"- {r.get('input_name', 'Input')}: {r.get('quantity_kg_per_acre', 0)} kg/acre — {r.get('timing', '')}"
            for r in fert_plan
        ) if fert_plan else "Follow standard recommendations for your crop and soil."

        # Build weather summary
        weather_summary_parts = [weather_data.get("summary", "No weather data available.")]
        for alert in weather_data.get("alerts", [])[:3]:
            weather_summary_parts.append(f"Alert ({alert.get('type', '')}): {alert.get('message', '')}")
        weather_summary = "\n".join(weather_summary_parts)

        # Build prompt
        prompt = _PLAN_PROMPT.format(
            district=farm_profile.get("district", "Your Region"),
            state=farm_profile.get("state", "India"),
            farm_size=farm_profile.get("farm_size", "N/A"),
            soil_class=soil_result.get("soil_class", farm_profile.get("soil_type", "Inceptisol")),
            fertility_level=soil_result.get("fertility_level", "Medium"),
            selected_crop=selected_crop,
            season=farm_profile.get("current_season", "Kharif"),
            water_source=farm_profile.get("water_source", "Rainfall"),
            prev_crop=farm_profile.get("prev_crop", "None"),
            fertilizer_summary=fert_summary,
            weather_summary=weather_summary,
            duration_weeks=duration_weeks,
        )

        plan_data = self._call_llm_with_retry(prompt, selected_crop, duration_weeks)

        # Validate for high-impact content
        plan_text = json.dumps(plan_data)
        validation = flag_high_impact(plan_text)

        plan_data["high_impact_flag"] = validation.is_high_impact
        plan_data["high_impact_warnings"] = validation.warnings
        plan_data["status"] = "flagged" if validation.is_high_impact else "draft"
        plan_data["explainability"] = {
            "data_sources_used": [
                "Farm profile", "Soil assessment result",
                "Weather intelligence data", "Gemini LLM generation",
            ],
            "weather_adaptation": len(weather_data.get("alerts", [])) > 0,
            "fertilizer_integrated": len(fert_plan) > 0,
        }

        logger.info(
            "Farm plan generated: crop=%s, weeks=%d, high_impact=%s",
            selected_crop, len(plan_data.get("weeks", [])), plan_data["high_impact_flag"]
        )
        return plan_data

    def _call_llm_with_retry(
        self, prompt: str, crop_name: str, duration_weeks: int, max_retries: int = 3
    ) -> dict:
        """Call LLM with retry logic. Returns fallback plan on failure."""
        if self.llm is None:
            return self._fallback_plan(crop_name, duration_weeks)

        for attempt in range(1, max_retries + 1):
            try:
                response = self.llm.generate_content(prompt)
                text = response.text.strip()

                # Extract JSON if wrapped in markdown code blocks
                json_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
                json_str = json_match.group(1) if json_match else text

                plan = json.loads(json_str)
                if "weeks" in plan and len(plan["weeks"]) > 0:
                    return plan
                logger.warning("LLM plan missing weeks (attempt %d), retrying...", attempt)
            except json.JSONDecodeError as exc:
                logger.warning("LLM JSON parse error (attempt %d): %s", attempt, exc)
            except Exception as exc:
                logger.error("LLM call error (attempt %d): %s", attempt, exc)
                import time
                time.sleep(2 ** attempt)

        logger.error("All LLM retries exhausted for farm plan. Using fallback.")
        return self._fallback_plan(crop_name, duration_weeks)

    def _fallback_plan(self, crop_name: str, duration_weeks: int) -> dict:
        """Generate a minimal fallback plan when LLM is unavailable."""
        weeks = []
        phases = [
            "Land Preparation", "Sowing", "Early Vegetative", "Vegetative Growth",
            "Flowering / Reproductive", "Maturity / Harvest",
        ]
        weeks_per_phase = max(1, duration_weeks // len(phases))
        week_num = 1
        for i, phase in enumerate(phases):
            for _ in range(weeks_per_phase):
                if week_num > duration_weeks:
                    break
                weeks.append({
                    "week": week_num,
                    "phase": phase,
                    "activities": [
                        f"Carry out standard {phase.lower()} activities for {crop_name}"
                    ],
                    "irrigation": "As required based on soil moisture",
                    "weather_note": None,
                    "inputs": [],
                })
                week_num += 1

        return {
            "crop": crop_name,
            "season": "Current Season",
            "total_weeks": duration_weeks,
            "weeks": weeks,
            "harvest_window": f"Week {duration_weeks - 2}–{duration_weeks}",
            "expected_yield_qtl_per_acre": 0.0,
            "key_risks": ["Consult local extension officer for specific risk assessment"],
            "note": "This is a basic fallback plan. LLM service was unavailable.",
        }
