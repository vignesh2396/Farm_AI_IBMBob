"""
utils/db.py
-----------
SQLite database connection and schema initialization for FarmAI.
Uses parameterized queries throughout to prevent SQL injection.
"""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from utils.config import config
from utils.logger import get_logger

logger = get_logger(__name__)

_DB_PATH = Path(config.DB_PATH)

DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS farm_profile (
        profile_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id    TEXT    NOT NULL,
        district      TEXT    NOT NULL,
        state         TEXT    NOT NULL,
        farm_size     REAL    NOT NULL CHECK (farm_size > 0),
        soil_type     TEXT    NOT NULL,
        water_source  TEXT    NOT NULL,
        current_season TEXT   NOT NULL,
        prev_crop     TEXT,
        created_at    TEXT    DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS soil_assessment (
        assessment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id      INTEGER NOT NULL REFERENCES farm_profile(profile_id),
        nitrogen        REAL    NOT NULL,
        phosphorus      REAL    NOT NULL,
        potassium       REAL    NOT NULL,
        ph_level        REAL    NOT NULL,
        organic_matter  REAL,
        soil_class      TEXT,
        fertility_level TEXT,
        confidence      REAL,
        fertilizer_reco TEXT,
        deficiencies    TEXT,
        created_at      TEXT    DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS crop_plan (
        plan_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id     INTEGER NOT NULL REFERENCES farm_profile(profile_id),
        selected_crop  TEXT    NOT NULL,
        season         TEXT    NOT NULL,
        plan_json      TEXT    NOT NULL,
        status         TEXT    DEFAULT 'draft',
        reviewed_by    TEXT,
        review_notes   TEXT,
        created_at     TEXT    DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agent_trace (
        trace_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id        INTEGER,
        session_id     TEXT    NOT NULL,
        agent_name     TEXT    NOT NULL,
        step_number    INTEGER NOT NULL,
        input_summary  TEXT,
        output_summary TEXT,
        tool_called    TEXT,
        duration_ms    INTEGER,
        timestamp      TEXT    DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS weather_cache (
        cache_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        location      TEXT    NOT NULL UNIQUE,
        forecast_json TEXT    NOT NULL,
        cached_at     TEXT    DEFAULT (datetime('now')),
        expires_at    TEXT    NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS audit_log (
        log_id         INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id     TEXT    NOT NULL,
        event_type     TEXT    NOT NULL,
        agent_name     TEXT,
        action         TEXT,
        result_summary TEXT,
        timestamp      TEXT    DEFAULT (datetime('now'))
    )
    """,
    # Indexes
    "CREATE INDEX IF NOT EXISTS idx_fp_session ON farm_profile(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_sa_profile  ON soil_assessment(profile_id)",
    "CREATE INDEX IF NOT EXISTS idx_cp_profile  ON crop_plan(profile_id)",
    "CREATE INDEX IF NOT EXISTS idx_at_session  ON agent_trace(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_wc_loc      ON weather_cache(location)",
    "CREATE INDEX IF NOT EXISTS idx_al_session  ON audit_log(session_id)",
]


def init_db() -> None:
    """Initialize the database and create all tables if they don't exist."""
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        for stmt in DDL_STATEMENTS:
            conn.execute(stmt)
        conn.commit()
    logger.info("Database initialized at %s", _DB_PATH)


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager that yields a SQLite connection.
    Automatically commits on success and rolls back on exception.
    """
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def log_audit(
    session_id: str,
    event_type: str,
    agent_name: str = "",
    action: str = "",
    result_summary: str = "",
) -> None:
    """Record an audit log entry."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO audit_log (session_id, event_type, agent_name, action, result_summary)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, event_type, agent_name, action, result_summary),
        )
