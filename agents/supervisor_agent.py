"""
agents/supervisor_agent.py
---------------------------
Supervisor Agent: Orchestrates all specialized agents in FarmAI.
Routes user requests to appropriate agents and aggregates results.

This is the entry point for all agentic workflows.
"""
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import google.generativeai as genai

from utils.config import config
from utils.db import get_connection, log_audit
from utils.helpers import sanitize_input
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AgentStep:
    """A single step in the agent trace."""
    step_number: int
    agent_name: str
    action: str
    result_summary: str
    tool_called: str = ""
    duration_ms: int = 0
    error: str = ""


@dataclass
class AgentState:
    """Session-wide shared state passed between agents."""
    session_id: str
    farm_profile: dict = field(default_factory=dict)
    soil_result: dict = field(default_factory=dict)
    weather_data: dict = field(default_factory=dict)
    crop_ranking: list = field(default_factory=list)
    selected_crop: str = ""
    farm_plan: dict = field(default_factory=dict)
    trace: list[AgentStep] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    high_impact_flagged: bool = False
    human_review_required: bool = False


class SupervisorAgent:
    """
    Supervisor Agent for FarmAI.

    Responsibilities:
    - Receive user intent and route to appropriate specialized agents
    - Maintain AgentState across the full planning workflow
    - Aggregate results from all agents into a unified response
    - Log agent traces for transparency and debugging
    """

    INTENT_KEYWORDS = {
        "soil": ["soil", "nitrogen", "phosphorus", "potassium", "ph", "fertilizer", "nutrient"],
        "weather": ["weather", "rain", "forecast", "temperature", "drought", "monsoon"],
        "crop": ["crop", "sow", "plant", "cultivate", "seed", "variety"],
        "plan": ["plan", "schedule", "calendar", "season", "timeline", "operations"],
        "advisory": ["how", "why", "what", "when", "recommend", "advise", "guide", "tell me"],
    }

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state = AgentState(session_id=session_id)

        # Configure Gemini LLM
        if config.GOOGLE_API_KEY:
            genai.configure(api_key=config.GOOGLE_API_KEY)
            self.llm = genai.GenerativeModel(
                model_name=config.GEMINI_MODEL,
                generation_config=genai.GenerationConfig(
                    temperature=config.LLM_TEMPERATURE,
                    max_output_tokens=config.LLM_MAX_TOKENS,
                ),
            )
        else:
            self.llm = None
            logger.warning("GOOGLE_API_KEY not set — LLM features will be unavailable")

    def _detect_intent(self, user_input: str) -> str:
        """
        Detect the primary intent from user input using keyword matching.

        Returns one of: 'soil', 'weather', 'crop', 'plan', 'advisory', 'general'
        """
        text = user_input.lower()
        for intent, keywords in self.INTENT_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return intent
        return "advisory"

    def _add_trace(
        self,
        agent_name: str,
        action: str,
        result_summary: str,
        tool_called: str = "",
        duration_ms: int = 0,
        error: str = "",
    ) -> None:
        """Append a step to the agent trace."""
        step = AgentStep(
            step_number=len(self.state.trace) + 1,
            agent_name=agent_name,
            action=action,
            result_summary=result_summary,
            tool_called=tool_called,
            duration_ms=duration_ms,
            error=error,
        )
        self.state.trace.append(step)
        logger.debug(
            "TRACE [%d] %s | %s → %s", step.step_number, agent_name, action, result_summary[:100]
        )

    def run_soil_assessment(self, soil_data: dict) -> dict:
        """
        Run the Soil Assessment Agent.

        Args:
            soil_data: Dict with keys: nitrogen, phosphorus, potassium, ph_level, organic_matter

        Returns:
            Soil assessment result dict
        """
        from agents.soil_assessment_agent import SoilAssessmentAgent
        start = time.time()
        agent = SoilAssessmentAgent(self.llm, self.session_id)
        result = agent.assess(soil_data, self.state.farm_profile)
        duration = int((time.time() - start) * 1000)

        self.state.soil_result = result
        self._add_trace(
            "SoilAssessmentAgent", "assess_soil",
            f"soil_class={result.get('soil_class')}; fertility={result.get('fertility_level')}; "
            f"confidence={result.get('confidence', 0):.2f}",
            tool_called="soil_analysis_tool",
            duration_ms=duration,
        )
        log_audit(self.session_id, "SOIL_ASSESSMENT_RUN", "SoilAssessmentAgent",
                  f"N={soil_data.get('nitrogen')}, P={soil_data.get('phosphorus')}, pH={soil_data.get('ph_level')}",
                  f"class={result.get('soil_class')}, confidence={result.get('confidence', 0):.2f}")
        return result

    def run_weather_intelligence(self, location: str) -> dict:
        """
        Run the Weather Intelligence Agent.

        Args:
            location: Location string (e.g., "Akola, Maharashtra")

        Returns:
            Weather forecast and alerts dict
        """
        from agents.weather_intelligence_agent import WeatherIntelligenceAgent
        start = time.time()
        agent = WeatherIntelligenceAgent(self.session_id)
        result = agent.get_forecast_and_alerts(location)
        duration = int((time.time() - start) * 1000)

        self.state.weather_data = result
        alerts = result.get("alerts", [])
        self._add_trace(
            "WeatherIntelligenceAgent", f"get_forecast({location})",
            f"{len(result.get('forecast', []))} days forecast; {len(alerts)} alerts",
            tool_called="weather_api_tool",
            duration_ms=duration,
        )
        return result

    def run_crop_suitability(self) -> list:
        """
        Run the Crop Suitability Agent using current state (soil + weather + profile).

        Returns:
            List of ranked crop dicts
        """
        from agents.crop_suitability_agent import CropSuitabilityAgent
        start = time.time()
        agent = CropSuitabilityAgent(self.llm, self.session_id)
        ranked_crops = agent.rank_crops(
            farm_profile=self.state.farm_profile,
            soil_result=self.state.soil_result,
            weather_data=self.state.weather_data,
        )
        duration = int((time.time() - start) * 1000)

        self.state.crop_ranking = ranked_crops
        top = ranked_crops[0] if ranked_crops else {}
        self._add_trace(
            "CropSuitabilityAgent", "rank_crops",
            f"top_crop={top.get('crop_name', 'N/A')} ({top.get('suitability_score', 0)}/100); "
            f"{len(ranked_crops)} crops ranked",
            tool_called="crop_db_tool + rag_tool",
            duration_ms=duration,
        )
        log_audit(self.session_id, "CROP_RANKING_GENERATED", "CropSuitabilityAgent",
                  f"season={self.state.farm_profile.get('current_season')}",
                  f"top_crop={top.get('crop_name', 'N/A')}, score={top.get('suitability_score', 0)}")
        return ranked_crops

    def run_farm_plan(self, selected_crop: str) -> dict:
        """
        Run the Farm Operations Planning Agent.

        Args:
            selected_crop: The crop selected by the farmer

        Returns:
            Farm operations plan dict
        """
        from agents.farm_ops_planning_agent import FarmOpsPlanningAgent
        self.state.selected_crop = selected_crop
        start = time.time()
        agent = FarmOpsPlanningAgent(self.llm, self.session_id)
        plan = agent.generate_plan(
            farm_profile=self.state.farm_profile,
            soil_result=self.state.soil_result,
            weather_data=self.state.weather_data,
            selected_crop=selected_crop,
        )
        duration = int((time.time() - start) * 1000)

        self.state.farm_plan = plan
        if plan.get("high_impact_flag"):
            self.state.high_impact_flagged = True
            self.state.human_review_required = True

        self._add_trace(
            "FarmOpsPlanningAgent", f"generate_plan({selected_crop})",
            f"{len(plan.get('weeks', []))} week plan; high_impact={plan.get('high_impact_flag', False)}",
            tool_called="plan_generator",
            duration_ms=duration,
        )
        log_audit(self.session_id, "PLAN_GENERATED", "FarmOpsPlanningAgent",
                  f"crop={selected_crop}",
                  f"weeks={len(plan.get('weeks', []))}, flagged={plan.get('high_impact_flag', False)}")
        return plan

    def run_advisory(self, query: str) -> dict:
        """
        Run the Agricultural Advisory Agent (RAG-backed Q&A).

        Args:
            query: Free-text farming question

        Returns:
            Advisory response dict with answer, sources, groundedness score
        """
        from agents.agricultural_advisory_agent import AgriculturalAdvisoryAgent
        start = time.time()
        agent = AgriculturalAdvisoryAgent(self.llm, self.session_id)
        result = agent.answer(query, context=self.state.farm_profile)
        duration = int((time.time() - start) * 1000)

        self._add_trace(
            "AgriculturalAdvisoryAgent", f"answer_query",
            f"groundedness={result.get('groundedness_score', 0):.2f}; "
            f"{len(result.get('sources', []))} sources cited",
            tool_called="rag_retriever",
            duration_ms=duration,
        )
        return result

    def get_trace(self) -> list[dict]:
        """Return the full agent trace as a list of dicts."""
        return [
            {
                "step": s.step_number,
                "agent": s.agent_name,
                "action": s.action,
                "result": s.result_summary,
                "tool": s.tool_called,
                "duration_ms": s.duration_ms,
                "error": s.error,
            }
            for s in self.state.trace
        ]
