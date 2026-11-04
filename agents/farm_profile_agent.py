"""
agents/farm_profile_agent.py
-----------------------------
Farm Profile Agent: Manages farm profile CRUD operations in SQLite.
Stores and retrieves farm context used by all other agents.
"""
from utils.db import get_connection, log_audit
from utils.helpers import sanitize_input
from utils.logger import get_logger

logger = get_logger(__name__)

VALID_SOIL_TYPES = [
    "Black Cotton", "Vertisol", "Red Laterite", "Alfisol",
    "Sandy", "Entisol", "Loam", "Inceptisol", "Alluvial Loam",
    "Clay", "Silt", "Peaty",
]

VALID_WATER_SOURCES = ["Rainfall", "Canal", "Borewell", "Tank", "River"]
VALID_SEASONS = ["Kharif", "Rabi", "Zaid"]


def save_farm_profile(
    session_id: str,
    district: str,
    state: str,
    farm_size: float,
    soil_type: str,
    water_source: str,
    current_season: str,
    prev_crop: str = "",
) -> dict:
    """
    Save or update a farm profile for the given session.

    Args:
        session_id: Unique session identifier
        district: Farm district name
        state: Farm state name
        farm_size: Farm area in acres (must be > 0)
        soil_type: Soil type (must be in VALID_SOIL_TYPES)
        water_source: Water source (must be in VALID_WATER_SOURCES)
        current_season: Farming season (Kharif | Rabi | Zaid)
        prev_crop: Previously grown crop (optional)

    Returns:
        Dict with status, profile_id, and message
    """
    # Input validation
    errors = []
    if not district.strip():
        errors.append("District is required")
    if not state.strip():
        errors.append("State is required")
    if farm_size <= 0:
        errors.append("Farm size must be greater than 0 acres")
    if current_season not in VALID_SEASONS:
        errors.append(f"Season must be one of: {', '.join(VALID_SEASONS)}")
    if errors:
        return {"status": "error", "errors": errors}

    # Sanitize text inputs
    district = sanitize_input(district, 100)
    state = sanitize_input(state, 100)
    prev_crop = sanitize_input(prev_crop, 100)

    try:
        with get_connection() as conn:
            # Delete any existing profile for this session (one profile per session)
            conn.execute("DELETE FROM farm_profile WHERE session_id = ?", (session_id,))

            cursor = conn.execute(
                """
                INSERT INTO farm_profile
                    (session_id, district, state, farm_size, soil_type, water_source, current_season, prev_crop)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, district, state, farm_size, soil_type, water_source, current_season, prev_crop),
            )
            profile_id = cursor.lastrowid

        log_audit(session_id, "FARM_PROFILE_CREATED", "FarmProfileAgent",
                  f"save_profile(district={district}, size={farm_size}ac)",
                  f"profile_id={profile_id}")
        logger.info("Farm profile saved: session=%s, profile_id=%d", session_id, profile_id)

        return {
            "status": "success",
            "profile_id": profile_id,
            "message": f"Farm profile saved for {district}, {state}",
        }

    except Exception as exc:
        logger.error("Failed to save farm profile for session %s: %s", session_id, exc)
        return {"status": "error", "errors": [f"Database error: {str(exc)}"]}


def get_farm_profile(session_id: str) -> dict:
    """
    Retrieve the farm profile for the given session.

    Args:
        session_id: Session identifier

    Returns:
        Farm profile dict or empty dict if not found
    """
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM farm_profile WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
                (session_id,),
            ).fetchone()

        if row:
            profile = dict(row)
            logger.debug("Farm profile loaded for session %s", session_id)
            return profile
        logger.debug("No farm profile found for session %s", session_id)
        return {}

    except Exception as exc:
        logger.error("Failed to retrieve farm profile for session %s: %s", session_id, exc)
        return {}


def delete_farm_profile(session_id: str) -> bool:
    """
    Delete the farm profile for a session (user data deletion / privacy compliance).

    Args:
        session_id: Session identifier

    Returns:
        True if deleted, False if not found or error
    """
    try:
        with get_connection() as conn:
            result = conn.execute(
                "DELETE FROM farm_profile WHERE session_id = ?", (session_id,)
            )
        deleted = result.rowcount > 0
        if deleted:
            log_audit(session_id, "FARM_PROFILE_DELETED", "FarmProfileAgent",
                      "delete_profile()", "User-requested data deletion")
            logger.info("Farm profile deleted for session %s", session_id)
        return deleted
    except Exception as exc:
        logger.error("Failed to delete farm profile: %s", exc)
        return False
