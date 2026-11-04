"""
agents/crop_suitability_agent.py
---------------------------------
Crop Suitability Agent: Multi-factor crop ranking combining CSV database,
weather data, soil results, and RAG knowledge retrieval.
"""
from tools.crop_db_tool import get_candidate_crops
from tools.validation_tool import validate_crop_suitability_result
from rag.retriever import retrieve_crop_knowledge
from utils.logger import get_logger

logger = get_logger(__name__)

_CROP_EXPLAIN_PROMPT = """
You are an agricultural advisory expert. Explain in 2 sentences why {crop_name} is the 
top recommended crop for this farmer's conditions:
- Location: {district}, {state}
- Soil: {soil_class} ({fertility_level} fertility)
- Season: {season}
- Water Source: {water_source}
- Suitability Score: {score}/100

Keep the explanation simple and practical, suitable for a smallholder farmer.
Do not mention the scoring formula. Focus on practical farming benefits.
"""


class CropSuitabilityAgent:
    """
    Crop Suitability Agent for FarmAI.

    Responsibilities:
    - Query crop reference database for candidate crops
    - Score crops using multi-factor weighted algorithm
    - Enrich top crops with RAG-retrieved knowledge
    - Generate LLM-enhanced justifications for top recommendations
    - Validate output and return ranked list
    """

    def __init__(self, llm, session_id: str):
        self.llm = llm
        self.session_id = session_id

    def rank_crops(
        self,
        farm_profile: dict,
        soil_result: dict,
        weather_data: dict,
    ) -> list[dict]:
        """
        Rank crops for suitability based on farm conditions.

        Args:
            farm_profile: Farm profile dict (from FarmProfileAgent)
            soil_result: Soil assessment result (from SoilAssessmentAgent)
            weather_data: Weather forecast and alerts (from WeatherIntelligenceAgent)

        Returns:
            List of ranked crop dicts, sorted by suitability_score descending
        """
        soil_type = soil_result.get("soil_class") or farm_profile.get("soil_type", "Inceptisol")
        season = farm_profile.get("current_season", "Kharif")
        water_source = farm_profile.get("water_source", "Rainfall")

        # Get base rankings from crop database
        ranked = get_candidate_crops(
            soil_type=soil_type,
            season=season,
            water_source=water_source,
            top_n=8,
        )

        # Apply weather adjustment: penalize high-water crops in drought conditions
        alerts = weather_data.get("alerts", [])
        drought_active = any(a.get("type") == "DROUGHT_RISK" for a in alerts)
        heavy_rain_active = any(a.get("type") == "HEAVY_RAIN" for a in alerts)

        adjusted = []
        for crop in ranked:
            score = crop.suitability_score
            notes = []

            if drought_active and crop.avg_yield_qtl > 0:
                # Penalize high-water-requirement crops
                water_req = self._get_water_req(crop.crop_name)
                if water_req > 600:
                    penalty = min(15, int((water_req - 600) / 30))
                    score = max(0, score - penalty)
                    notes.append(f"⚠️ Drought risk: score reduced by {penalty} points")

            if heavy_rain_active:
                # Penalize crops sensitive to waterlogging
                waterlog_sensitive = ["Cotton", "Groundnut", "Chickpea", "Wheat"]
                if crop.crop_name in waterlog_sensitive:
                    score = max(0, score - 8)
                    notes.append("⚠️ Heavy rain risk: waterlogging-sensitive crop")

            adjusted.append({
                "rank": crop.rank,
                "crop_name": crop.crop_name,
                "suitability_score": score,
                "score_breakdown": crop.score_breakdown,
                "justification": crop.justification,
                "weather_notes": notes,
                "duration_days": crop.duration_days,
                "avg_yield_qtl": crop.avg_yield_qtl,
                "market_demand": crop.market_demand,
                "rag_knowledge": None,  # Filled for top 3 below
            })

        # Sort after weather adjustment
        adjusted.sort(key=lambda c: c["suitability_score"], reverse=True)
        for i, crop in enumerate(adjusted, start=1):
            crop["rank"] = i

        # Enrich top 3 with RAG knowledge
        for crop in adjusted[:3]:
            rag_results = retrieve_crop_knowledge(crop["crop_name"], "cultivation sowing irrigation")
            if rag_results:
                crop["rag_knowledge"] = {
                    "excerpt": rag_results[0]["text"][:300],
                    "source": rag_results[0]["source"],
                    "relevance_score": rag_results[0]["relevance_score"],
                }
                # Enrich justification with LLM for top crop
                if crop["rank"] == 1 and self.llm:
                    crop["justification"] = self._llm_justify(
                        crop["crop_name"], soil_type, season, water_source,
                        score=crop["suitability_score"],
                        district=farm_profile.get("district", "your region"),
                        state=farm_profile.get("state", "India"),
                        fertility_level=soil_result.get("fertility_level", "Medium"),
                    )

        # Validate output
        validation = validate_crop_suitability_result(
            [type("C", (), {"suitability_score": c["suitability_score"]})() for c in adjusted]
        )
        if not validation.is_valid:
            logger.warning("Crop validation issues: %s", validation.issues)

        logger.info(
            "Crop ranking complete: top=%s (%d/100), %d crops evaluated",
            adjusted[0]["crop_name"] if adjusted else "N/A",
            adjusted[0]["suitability_score"] if adjusted else 0,
            len(adjusted),
        )
        return adjusted

    def _get_water_req(self, crop_name: str) -> float:
        """Return approximate water requirement in mm for common crops."""
        water_req_map = {
            "Cotton": 700, "Soybean": 500, "Pigeonpea": 450, "Groundnut": 500,
            "Green Gram": 350, "Wheat": 400, "Chickpea": 300, "Mustard": 250,
            "Sorghum (Jowar)": 400, "Pearl Millet (Bajra)": 300,
        }
        return water_req_map.get(crop_name, 500)

    def _llm_justify(
        self,
        crop_name: str,
        soil_class: str,
        season: str,
        water_source: str,
        score: int,
        district: str,
        state: str,
        fertility_level: str,
    ) -> str:
        """Generate an LLM-enhanced justification for the top crop."""
        prompt = _CROP_EXPLAIN_PROMPT.format(
            crop_name=crop_name,
            district=district,
            state=state,
            soil_class=soil_class,
            fertility_level=fertility_level,
            season=season,
            water_source=water_source,
            score=score,
        )
        try:
            response = self.llm.generate_content(prompt)
            return response.text.strip()
        except Exception as exc:
            logger.warning("LLM crop justification failed: %s", exc)
            return f"{crop_name} is well-suited to {soil_class} soil in the {season} season with {water_source} irrigation."
