# Database Design Document
## FarmAI – Agricultural Decision Intelligence System
**Version:** 1.0 | **Date:** 2026-11-04

---

## 1. ER Diagram

```
┌──────────────────────┐         ┌───────────────────────────┐
│     farm_profile     │         │      soil_assessment      │
├──────────────────────┤         ├───────────────────────────┤
│ PK: profile_id (INT) │◄────────│ FK: profile_id (INT)      │
│    session_id (TEXT) │   1:N   │ PK: assessment_id (INT)   │
│    district (TEXT)   │         │    nitrogen (REAL)        │
│    state (TEXT)      │         │    phosphorus (REAL)      │
│    farm_size (REAL)  │         │    potassium (REAL)       │
│    soil_type (TEXT)  │         │    ph_level (REAL)        │
│    water_source(TEXT)│         │    organic_matter (REAL)  │
│    current_season(TX)│         │    soil_class (TEXT)      │
│    prev_crop (TEXT)  │         │    fertility_level (TEXT) │
│    created_at (TEXT) │         │    confidence (REAL)      │
└──────────────────────┘         │    fertilizer_reco (TEXT) │
          │                      │    deficiencies (TEXT)    │
          │ 1:N                  │    created_at (TEXT)      │
          ▼                      └───────────────────────────┘
┌──────────────────────┐         
│    crop_plan         │         ┌───────────────────────────┐
├──────────────────────┤         │     weather_cache         │
│ PK: plan_id (INT)    │         ├───────────────────────────┤
│ FK: profile_id (INT) │         │ PK: cache_id (INT)        │
│    selected_crop(TX) │         │    location (TEXT)        │
│    season (TEXT)     │         │    forecast_json (TEXT)   │
│    plan_json (TEXT)  │         │    cached_at (TEXT)       │
│    status (TEXT)     │         │    expires_at (TEXT)      │
│    reviewed_by (TEXT)│         └───────────────────────────┘
│    created_at (TEXT) │         
└──────────────────────┘         ┌───────────────────────────┐
          │                      │     audit_log             │
          │ 1:N                  ├───────────────────────────┤
          ▼                      │ PK: log_id (INT)          │
┌──────────────────────┐         │    session_id (TEXT)      │
│    agent_trace       │         │    event_type (TEXT)      │
├──────────────────────┤         │    agent_name (TEXT)      │
│ PK: trace_id (INT)   │         │    action (TEXT)          │
│ FK: plan_id (INT)    │         │    result_summary (TEXT)  │
│    agent_name (TEXT) │         │    timestamp (TEXT)       │
│    step_number (INT) │         └───────────────────────────┘
│    input_summary(TX) │
│    output_summary(TX)│         ┌───────────────────────────┐
│    tool_called (TEXT)│         │   crop_reference (CSV)    │
│    duration_ms (INT) │         ├───────────────────────────┤
│    timestamp (TEXT)  │         │ crop_id (INT) PK          │
└──────────────────────┘         │ crop_name (TEXT)          │
                                  │ season (TEXT)             │
                                  │ soil_types (TEXT)         │
                                  │ min_rainfall_mm (REAL)    │
                                  │ max_temp_c (REAL)         │
                                  │ min_temp_c (REAL)         │
                                  │ water_req_mm (REAL)       │
                                  │ avg_yield_qtl (REAL)      │
                                  │ market_demand (TEXT)      │
                                  └───────────────────────────┘
```

---

## 2. Relational Schema (SQL DDL)

```sql
-- SQLite Database: farmdata.db

CREATE TABLE farm_profile (
    profile_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   TEXT    NOT NULL,
    district     TEXT    NOT NULL,
    state        TEXT    NOT NULL,
    farm_size    REAL    NOT NULL CHECK (farm_size > 0),
    soil_type    TEXT    NOT NULL,
    water_source TEXT    NOT NULL,
    current_season TEXT  NOT NULL,
    prev_crop    TEXT,
    created_at   TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE soil_assessment (
    assessment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id      INTEGER NOT NULL REFERENCES farm_profile(profile_id),
    nitrogen        REAL    NOT NULL CHECK (nitrogen BETWEEN 0 AND 100),
    phosphorus      REAL    NOT NULL CHECK (phosphorus BETWEEN 0 AND 100),
    potassium       REAL    NOT NULL CHECK (potassium BETWEEN 0 AND 100),
    ph_level        REAL    NOT NULL CHECK (ph_level BETWEEN 0 AND 14),
    organic_matter  REAL    CHECK (organic_matter BETWEEN 0 AND 20),
    soil_class      TEXT,
    fertility_level TEXT,
    confidence      REAL    CHECK (confidence BETWEEN 0 AND 1),
    fertilizer_reco TEXT,
    deficiencies    TEXT,
    created_at      TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE crop_plan (
    plan_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id     INTEGER NOT NULL REFERENCES farm_profile(profile_id),
    selected_crop  TEXT    NOT NULL,
    season         TEXT    NOT NULL,
    plan_json      TEXT    NOT NULL,
    status         TEXT    DEFAULT 'draft' CHECK (status IN ('draft','flagged','approved','rejected')),
    reviewed_by    TEXT,
    review_notes   TEXT,
    created_at     TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE agent_trace (
    trace_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id        INTEGER REFERENCES crop_plan(plan_id),
    session_id     TEXT    NOT NULL,
    agent_name     TEXT    NOT NULL,
    step_number    INTEGER NOT NULL,
    input_summary  TEXT,
    output_summary TEXT,
    tool_called    TEXT,
    duration_ms    INTEGER,
    timestamp      TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE weather_cache (
    cache_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    location      TEXT    NOT NULL,
    forecast_json TEXT    NOT NULL,
    cached_at     TEXT    DEFAULT (datetime('now')),
    expires_at    TEXT    NOT NULL
);

CREATE TABLE audit_log (
    log_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id     TEXT    NOT NULL,
    event_type     TEXT    NOT NULL,
    agent_name     TEXT,
    action         TEXT,
    result_summary TEXT,
    timestamp      TEXT    DEFAULT (datetime('now'))
);

-- Indexes
CREATE INDEX idx_farm_profile_session ON farm_profile(session_id);
CREATE INDEX idx_soil_profile         ON soil_assessment(profile_id);
CREATE INDEX idx_crop_plan_profile    ON crop_plan(profile_id);
CREATE INDEX idx_agent_trace_session  ON agent_trace(session_id);
CREATE INDEX idx_weather_cache_loc    ON weather_cache(location);
CREATE INDEX idx_audit_session        ON audit_log(session_id);
```

---

## 3. Data Dictionary

| Table | Column | Type | Description | Example |
|---|---|---|---|---|
| farm_profile | profile_id | INT | PK auto-increment | 1 |
| farm_profile | session_id | TEXT | Browser session UUID | "abc-123" |
| farm_profile | district | TEXT | Farm district | "Akola" |
| farm_profile | farm_size | REAL | Farm area in acres | 3.5 |
| farm_profile | soil_type | TEXT | Farmer-selected soil type | "Black Cotton" |
| farm_profile | water_source | TEXT | Irrigation source | "Borewell" |
| soil_assessment | nitrogen | REAL | N kg/ha (0–100) | 42.5 |
| soil_assessment | ph_level | REAL | Soil pH (0–14) | 7.2 |
| soil_assessment | confidence | REAL | Classification confidence (0–1) | 0.82 |
| soil_assessment | soil_class | TEXT | FAO classification | "Vertisol" |
| soil_assessment | fertility_level | TEXT | Low/Medium/High | "Medium" |
| crop_plan | plan_json | TEXT | JSON blob of weekly plan | {"week1":{...}} |
| crop_plan | status | TEXT | Workflow status | "approved" |
| agent_trace | agent_name | TEXT | Originating agent | "SoilAssessmentAgent" |
| agent_trace | duration_ms | INT | Execution time ms | 1240 |
| weather_cache | forecast_json | TEXT | JSON from Open-Meteo | {"daily":{...}} |
| weather_cache | expires_at | TEXT | Cache expiry ISO datetime | "2026-11-04T14:00:00" |

---

## 4. Normalization Analysis

| Table | Normal Form | Justification |
|---|---|---|
| farm_profile | 3NF | All attributes depend only on PK profile_id |
| soil_assessment | 3NF | All attributes depend only on PK assessment_id + FK |
| crop_plan | 3NF | plan_json is a blob (denormalized for MVP flexibility) |
| agent_trace | 2NF | All attributes functionally depend on trace_id |
| weather_cache | 1NF | forecast_json blob acceptable for caching use case |
| audit_log | 2NF | All attributes depend on log_id |

---

## 5. Indexing Strategy

| Index | Table | Column(s) | Purpose |
|---|---|---|---|
| idx_farm_profile_session | farm_profile | session_id | Fast profile lookup per session |
| idx_soil_profile | soil_assessment | profile_id | Join performance |
| idx_crop_plan_profile | crop_plan | profile_id | Retrieve plans for a farm |
| idx_agent_trace_session | agent_trace | session_id | Audit/debug trace retrieval |
| idx_weather_cache_loc | weather_cache | location | Cache hit check |
| idx_audit_session | audit_log | session_id | Compliance audit trail |

---

## 6. Backup Strategy

| Tier | Method | Frequency | Retention |
|---|---|---|---|
| Dev/Local | SQLite file copy to /backups/ | Daily (manual) | 7 days |
| Production (future) | pg_dump or automated snapshot | Daily at 02:00 | 30 days |
| Vector Store | ChromaDB persist_directory zip | Weekly | 4 weeks |
| Config/Env | Vault secrets backup | On change | 6 months |

---

## 7. Data Retention Strategy

| Data Type | Retention Period | Disposal Method |
|---|---|---|
| Farm profiles | 12 months after last activity | SQLite DELETE + secure overwrite |
| Soil assessments | 24 months (crop cycle reference) | Archive to CSV then DELETE |
| Agent traces | 90 days (debug/audit) | Auto-purge via scheduled job |
| Weather cache | 6 hours (auto-expiry) | TTL-based DELETE |
| Audit logs | 36 months (compliance) | Archive to cold storage |
