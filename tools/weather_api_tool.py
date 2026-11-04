"""
tools/weather_api_tool.py
--------------------------
Tool: Fetches 7-day weather forecast for a given location using Open-Meteo API.
Implements local caching with TTL to respect API rate limits.

Usage:
    from tools.weather_api_tool import get_weather_forecast
    result = get_weather_forecast("Akola, Maharashtra")
"""
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests

from utils.config import config
from utils.db import get_connection, log_audit
from utils.logger import get_logger

logger = get_logger(__name__)

_GEOCODING_URL = config.GEOCODING_API_BASE_URL
_WEATHER_URL = config.WEATHER_API_BASE_URL
_CACHE_TTL_HOURS = config.WEATHER_CACHE_TTL_HOURS
_REQUEST_TIMEOUT = 10  # seconds


def _geocode_location(location: str) -> Optional[tuple[float, float]]:
    """
    Convert a location name to latitude/longitude coordinates.

    Args:
        location: Human-readable location string (e.g., "Akola, Maharashtra")

    Returns:
        Tuple of (latitude, longitude) or None if not found
    """
    try:
        response = requests.get(
            _GEOCODING_URL,
            params={"name": location, "count": 1, "language": "en", "format": "json"},
            timeout=_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if results:
            return results[0]["latitude"], results[0]["longitude"]
        logger.warning("Geocoding returned no results for location: %s", location)
        return None
    except requests.RequestException as exc:
        logger.error("Geocoding API error for %s: %s", location, exc)
        return None


def _fetch_from_cache(location: str) -> Optional[dict]:
    """Check weather cache for a non-expired entry for the given location."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT forecast_json, expires_at FROM weather_cache WHERE location = ?",
                (location,),
            ).fetchone()
            if row and row["expires_at"] > now_str:
                logger.info("Weather cache HIT for %s (expires %s)", location, row["expires_at"])
                return json.loads(row["forecast_json"])
    except Exception as exc:
        logger.error("Cache read error: %s", exc)
    return None


def _save_to_cache(location: str, forecast_data: dict) -> None:
    """Persist weather forecast to SQLite cache with TTL."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=_CACHE_TTL_HOURS)
    expires_str = expires.strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO weather_cache (location, forecast_json, expires_at)
                VALUES (?, ?, ?)
                """,
                (location, json.dumps(forecast_data), expires_str),
            )
        logger.info("Weather data cached for %s until %s", location, expires_str)
    except Exception as exc:
        logger.error("Cache write error: %s", exc)


def _parse_forecast(raw: dict, location: str) -> dict:
    """
    Parse Open-Meteo daily forecast response into FarmAI-friendly structure.

    Returns structured forecast with daily entries and derived risk alerts.
    """
    daily = raw.get("daily", {})
    dates = daily.get("time", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    precipitation = daily.get("precipitation_sum", [])
    humidity = daily.get("relative_humidity_2m_max", [])
    wind = daily.get("wind_speed_10m_max", [])

    forecast_days = []
    alerts = []

    for i, date in enumerate(dates[:7]):
        rain = precipitation[i] if i < len(precipitation) else 0.0
        max_t = max_temps[i] if i < len(max_temps) else None
        min_t = min_temps[i] if i < len(min_temps) else None

        day_data = {
            "date": date,
            "max_temp_c": max_t,
            "min_temp_c": min_t,
            "rainfall_mm": rain,
            "humidity_pct": humidity[i] if i < len(humidity) else None,
            "wind_kmh": wind[i] if i < len(wind) else None,
        }
        forecast_days.append(day_data)

        # Generate alerts
        if rain and rain > 40:
            alerts.append({
                "type": "HEAVY_RAIN",
                "severity": "HIGH",
                "date": date,
                "message": f"Heavy rainfall expected ({rain:.1f}mm). Avoid sowing and field operations.",
            })
        elif max_t and max_t > 42:
            alerts.append({
                "type": "EXTREME_HEAT",
                "severity": "HIGH",
                "date": date,
                "message": f"Extreme heat expected ({max_t:.1f}°C). Irrigate early morning.",
            })

    # Drought check: 5+ consecutive days with <2mm rain
    dry_count = sum(1 for d in forecast_days if (d["rainfall_mm"] or 0) < 2)
    if dry_count >= 5:
        alerts.append({
            "type": "DROUGHT_RISK",
            "severity": "MEDIUM",
            "date_range": f"{dates[0]} to {dates[-1] if dates else 'N/A'}",
            "message": f"{dry_count} of 7 forecast days have <2mm rainfall. Plan irrigation proactively.",
        })

    return {
        "location": location,
        "forecast": forecast_days,
        "alerts": alerts,
        "data_source": "Open-Meteo",
        "cached": False,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def get_weather_forecast(location: str, session_id: str = "system") -> dict:
    """
    Get 7-day weather forecast for a given location.

    Checks local cache first (TTL = 6 hours). Falls back to Open-Meteo API.
    Returns a structured forecast dict with alerts.

    Args:
        location: Location string (e.g., "Akola, Maharashtra")
        session_id: Session ID for audit logging

    Returns:
        Dict with keys: location, forecast (list), alerts (list), data_source, cached, timestamp
    """
    # Check cache first
    cached = _fetch_from_cache(location)
    if cached:
        cached["cached"] = True
        return cached

    # Geocode location
    coords = _geocode_location(location)
    if coords is None:
        logger.warning("Could not geocode location '%s'. Using default forecast.", location)
        return {
            "location": location,
            "forecast": [],
            "alerts": [{"type": "DATA_UNAVAILABLE", "severity": "LOW",
                        "message": "Weather data unavailable for this location. Plan using historical averages."}],
            "data_source": "fallback",
            "cached": False,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    lat, lon = coords

    # Fetch from Open-Meteo
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join([
            "temperature_2m_max", "temperature_2m_min",
            "precipitation_sum", "relative_humidity_2m_max", "wind_speed_10m_max",
        ]),
        "timezone": "Asia/Kolkata",
        "forecast_days": 7,
    }

    try:
        start = time.time()
        response = requests.get(_WEATHER_URL, params=params, timeout=_REQUEST_TIMEOUT)
        response.raise_for_status()
        raw_data = response.json()
        elapsed = int((time.time() - start) * 1000)
        logger.info("Weather API response received in %dms for %s", elapsed, location)

        forecast = _parse_forecast(raw_data, location)
        _save_to_cache(location, forecast)

        log_audit(session_id, "WEATHER_FETCHED", "WeatherIntelligenceAgent",
                  f"fetch({location})", f"{len(forecast['forecast'])} days; {len(forecast['alerts'])} alerts")
        return forecast

    except requests.Timeout:
        logger.error("Weather API timeout for %s", location)
        return {
            "location": location,
            "forecast": [],
            "alerts": [{"type": "API_TIMEOUT", "severity": "MEDIUM",
                        "message": "Weather API timed out. Please try again later."}],
            "data_source": "error",
            "cached": False,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    except requests.RequestException as exc:
        logger.error("Weather API error for %s: %s", location, exc)
        return {
            "location": location,
            "forecast": [],
            "alerts": [{"type": "API_ERROR", "severity": "MEDIUM",
                        "message": "Weather service is temporarily unavailable. Plan using seasonal averages."}],
            "data_source": "error",
            "cached": False,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
