"""
agents/weather_intelligence_agent.py
--------------------------------------
Weather Intelligence Agent: Fetches weather forecasts and generates risk alerts.
Integrates with weather_api_tool and formats data for farm planning decisions.
"""
from tools.weather_api_tool import get_weather_forecast
from utils.logger import get_logger

logger = get_logger(__name__)


class WeatherIntelligenceAgent:
    """
    Weather Intelligence Agent for FarmAI.

    Responsibilities:
    - Fetch 7-day weather forecast for the farm's location
    - Identify weather risks: drought, heavy rain, extreme heat
    - Generate farmer-friendly alert messages
    - Provide caching-aware data retrieval
    """

    def __init__(self, session_id: str):
        self.session_id = session_id

    def get_forecast_and_alerts(self, location: str) -> dict:
        """
        Get weather forecast and process risk alerts for a farm location.

        Args:
            location: Location string (e.g., "Akola, Maharashtra")

        Returns:
            Structured dict with forecast, alerts, and sowing window assessment
        """
        raw = get_weather_forecast(location, session_id=self.session_id)
        forecast = raw.get("forecast", [])
        alerts = raw.get("alerts", [])

        # Add sowing window assessment
        sowing_assessment = self._assess_sowing_window(forecast)

        result = {
            "location": location,
            "forecast": forecast,
            "alerts": alerts,
            "sowing_window": sowing_assessment,
            "data_source": raw.get("data_source", "Unknown"),
            "cached": raw.get("cached", False),
            "timestamp": raw.get("timestamp", ""),
            "summary": self._generate_summary(forecast, alerts, location),
        }

        logger.info(
            "Weather intelligence ready for %s: %d days, %d alerts, sowing=%s",
            location, len(forecast), len(alerts), sowing_assessment.get("status")
        )
        return result

    def _assess_sowing_window(self, forecast: list) -> dict:
        """
        Assess whether the coming week is suitable for sowing.

        Returns dict with status (Good/Caution/Delay) and reason.
        """
        if not forecast:
            return {"status": "Unknown", "reason": "Weather data unavailable"}

        heavy_rain_days = sum(1 for d in forecast if (d.get("rainfall_mm") or 0) > 30)
        extreme_heat_days = sum(1 for d in forecast if (d.get("max_temp_c") or 0) > 42)
        dry_days = sum(1 for d in forecast if (d.get("rainfall_mm") or 0) < 2)

        if heavy_rain_days >= 2:
            return {
                "status": "Delay",
                "reason": f"Heavy rainfall expected on {heavy_rain_days} days this week. "
                          f"Delay sowing to avoid soil waterlogging and seed rot.",
                "severity": "HIGH",
            }
        elif extreme_heat_days >= 1:
            return {
                "status": "Caution",
                "reason": f"Extreme heat forecast ({extreme_heat_days} days >42°C). "
                          f"Sow early morning and ensure soil moisture before sowing.",
                "severity": "MEDIUM",
            }
        elif dry_days >= 6:
            return {
                "status": "Caution",
                "reason": f"Dry conditions expected ({dry_days}/7 days). "
                          f"Ensure pre-sowing irrigation if planting this week.",
                "severity": "LOW",
            }
        else:
            return {
                "status": "Good",
                "reason": "Weather conditions appear suitable for sowing this week.",
                "severity": "NONE",
            }

    def _generate_summary(self, forecast: list, alerts: list, location: str) -> str:
        """Generate a one-paragraph plain-language weather summary."""
        if not forecast:
            return f"Weather data for {location} is currently unavailable. Plan using historical seasonal averages."

        avg_max = sum(d.get("max_temp_c", 30) for d in forecast) / len(forecast)
        total_rain = sum(d.get("rainfall_mm", 0) or 0 for d in forecast)
        alert_summary = (
            " Key alerts: " + "; ".join(a.get("message", "") for a in alerts[:2])
            if alerts else " No major weather risks detected this week."
        )

        return (
            f"7-day forecast for {location}: Average max temperature {avg_max:.1f}°C, "
            f"total expected rainfall {total_rain:.1f}mm.{alert_summary}"
        )
