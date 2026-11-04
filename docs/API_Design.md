# API Design Document
## FarmAI – Agricultural Decision Intelligence System
**Version:** 1.0 | **Date:** 2026-11-04

---

## 1. API Architecture

FarmAI uses a **Python function-call API** (internal Streamlit-to-agent calls). For future external deployment, REST API endpoints are designed below as FastAPI specs.

---

## 2. REST API Specification

### Base URL: `http://localhost:8000/api/v1`

---

### 2.1 Farm Profile API

#### POST /farms/profile
**Purpose:** Create or update farm profile

**Request Body:**
```json
{
  "session_id": "string",
  "district": "string",
  "state": "string",
  "farm_size": "number (acres)",
  "soil_type": "string (enum: Clay|Loam|Sandy|Silt|Peaty|Black Cotton|Red Laterite)",
  "water_source": "string (enum: Rainfall|Canal|Borewell|Tank|River)",
  "current_season": "string (enum: Kharif|Rabi|Zaid)",
  "prev_crop": "string (optional)"
}
```

**Success Response (201):**
```json
{
  "status": "success",
  "profile_id": 42,
  "message": "Farm profile saved successfully",
  "timestamp": "2026-11-04T07:30:00Z"
}
```

**Error Response (422):**
```json
{
  "status": "error",
  "code": "VALIDATION_ERROR",
  "message": "farm_size must be a positive number",
  "field": "farm_size",
  "timestamp": "2026-11-04T07:30:00Z"
}
```

---

#### GET /farms/profile/{session_id}
**Purpose:** Retrieve existing farm profile

**Path Parameters:** `session_id` (string)

**Success Response (200):**
```json
{
  "status": "success",
  "data": {
    "profile_id": 42,
    "session_id": "abc-123",
    "district": "Akola",
    "state": "Maharashtra",
    "farm_size": 3.5,
    "soil_type": "Black Cotton",
    "water_source": "Borewell",
    "current_season": "Kharif",
    "prev_crop": "Soybean",
    "created_at": "2026-11-04T07:00:00Z"
  }
}
```

---

### 2.2 Soil Assessment API

#### POST /agents/soil-assessment
**Purpose:** Run soil assessment agent

**Request Body:**
```json
{
  "session_id": "string",
  "profile_id": "integer",
  "soil_data": {
    "nitrogen": "number (0-100 kg/ha)",
    "phosphorus": "number (0-100 kg/ha)",
    "potassium": "number (0-100 kg/ha)",
    "ph_level": "number (0-14)",
    "organic_matter": "number (0-20 %)",
    "moisture_level": "string (enum: Dry|Moderate|Wet)"
  }
}
```

**Success Response (200):**
```json
{
  "status": "success",
  "assessment_id": 15,
  "soil_classification": "Vertisol",
  "fertility_level": "Medium",
  "confidence": 0.82,
  "deficiencies": ["Nitrogen (Low)", "Zinc (Marginal)"],
  "fertilizer_plan": [
    {"input": "Urea", "quantity_kg_per_acre": 60, "timing": "At sowing"},
    {"input": "DAP", "quantity_kg_per_acre": 25, "timing": "At sowing"},
    {"input": "ZnSO4", "quantity_kg_per_acre": 10, "timing": "Basal dose"}
  ],
  "explainability": {
    "data_inputs": ["N=42.5", "P=18.3", "K=65.1", "pH=7.2"],
    "rules_applied": ["pH 6.5-8.5 → Vertisol suitable", "N<50 → Nitrogen deficient"],
    "sources_retrieved": ["ICAR Fertilizer Guide 2024, p.45"]
  }
}
```

---

### 2.3 Weather Intelligence API

#### GET /agents/weather/{location}
**Purpose:** Fetch weather forecast and alerts

**Path Parameters:** `location` (string: "district,state")

**Success Response (200):**
```json
{
  "status": "success",
  "location": "Akola, Maharashtra",
  "forecast": [
    {
      "date": "2026-11-05",
      "max_temp_c": 32.1,
      "min_temp_c": 18.4,
      "rainfall_mm": 0.0,
      "humidity_pct": 45,
      "wind_kmh": 12
    }
  ],
  "alerts": [
    {
      "type": "DROUGHT_RISK",
      "severity": "MEDIUM",
      "date_range": "2026-11-08 to 2026-11-12",
      "message": "No rainfall expected for 5 days. Plan irrigation accordingly."
    }
  ],
  "data_source": "Open-Meteo",
  "cached": false,
  "timestamp": "2026-11-04T07:30:00Z"
}
```

---

### 2.4 Crop Suitability API

#### POST /agents/crop-suitability
**Purpose:** Get ranked crop recommendations

**Request Body:**
```json
{
  "session_id": "string",
  "profile_id": "integer",
  "assessment_id": "integer",
  "season": "Kharif"
}
```

**Success Response (200):**
```json
{
  "status": "success",
  "ranked_crops": [
    {
      "rank": 1,
      "crop_name": "Cotton",
      "suitability_score": 87,
      "score_breakdown": {
        "soil_match": 92,
        "water_availability": 85,
        "seasonal_fit": 90,
        "market_demand": 82
      },
      "justification": "Black cotton soil is ideal for cotton; borewell water sufficient for Kharif.",
      "rag_source": "ICAR Cotton Cultivation Manual, Section 3.2"
    }
  ],
  "explainability": {
    "scoring_method": "Weighted average: soil(35%) + water(25%) + season(25%) + market(15%)",
    "total_crops_evaluated": 8
  }
}
```

---

### 2.5 Farm Operations Plan API

#### POST /agents/farm-plan
**Purpose:** Generate seasonal operations plan

**Request Body:**
```json
{
  "session_id": "string",
  "profile_id": "integer",
  "selected_crop": "Cotton",
  "assessment_id": "integer",
  "include_weather_adaptation": true
}
```

**Success Response (200):**
```json
{
  "status": "success",
  "plan_id": 7,
  "crop": "Cotton",
  "season": "Kharif",
  "weeks": [
    {
      "week": 1,
      "activities": [
        "Deep ploughing (30cm)",
        "Apply FYM 5 tonnes/acre",
        "Apply ZnSO4 basal dose"
      ],
      "irrigation": "Pre-sowing irrigation if soil is dry",
      "weather_note": null
    },
    {
      "week": 2,
      "activities": [
        "Sowing: Cotton at 90x60 cm spacing",
        "Seed rate: 1.5 kg/acre"
      ],
      "irrigation": "Post-sowing light irrigation",
      "weather_note": "⚠️ Forecast shows 45mm rainfall on Nov 6 – delay sowing by 2 days if confirmed."
    }
  ],
  "high_impact_flag": false,
  "status": "draft"
}
```

---

### 2.6 Agricultural Advisory API

#### POST /agents/advisory
**Purpose:** Answer free-text farming queries via RAG

**Request Body:**
```json
{
  "session_id": "string",
  "query": "What is the best spacing for cotton in black soil?",
  "context_profile_id": 42
}
```

**Success Response (200):**
```json
{
  "status": "success",
  "answer": "For cotton grown in black cotton soil (Vertisol), the recommended spacing is 90cm x 60cm (row x plant). This allows adequate airflow and root development...",
  "sources": [
    {
      "document": "ICAR Cotton Cultivation Guide",
      "section": "Chapter 3: Sowing Practices",
      "relevance_score": 0.91
    }
  ],
  "groundedness_score": 0.88,
  "confidence": "HIGH",
  "disclaimer": "This is an AI-generated recommendation based on retrieved agricultural guidelines. Consult your local extension officer for site-specific advice."
}
```

---

## 3. Error Model

```json
{
  "status": "error",
  "code": "ERROR_CODE",
  "message": "Human-readable description",
  "field": "affected_field_if_validation",
  "request_id": "uuid",
  "timestamp": "ISO8601"
}
```

| Error Code | HTTP Status | Description |
|---|---|---|
| VALIDATION_ERROR | 422 | Input validation failed |
| PROFILE_NOT_FOUND | 404 | Session profile doesn't exist |
| WEATHER_API_UNAVAILABLE | 503 | Open-Meteo API unreachable |
| LLM_TIMEOUT | 504 | Gemini API response timeout |
| RAG_NO_RESULTS | 200 | No relevant documents found (graceful) |
| HIGH_IMPACT_FLAGGED | 202 | Plan requires human review |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests to LLM API |
| INTERNAL_ERROR | 500 | Unexpected server error |

---

## 4. Validation Rules

| Field | Validation Rule |
|---|---|
| farm_size | Must be > 0 and ≤ 10000 (acres) |
| ph_level | Must be between 0.0 and 14.0 |
| nitrogen/phosphorus/potassium | Must be 0–100 kg/ha |
| session_id | UUID v4 format |
| query (advisory) | Max 500 characters; sanitize for prompt injection |
| location | Non-empty string, max 100 characters |

---

## 5. Authentication Strategy

| Layer | Strategy | Notes |
|---|---|---|
| MVP (Demo) | No authentication (session-based) | Streamlit session_state |
| Production | JWT Bearer Token | Issued on login; 1hr expiry |
| Extension Officer | Role-based JWT claim | `role: extension_officer` |
| Admin | API Key (Header: X-Admin-Key) | Stored in .env |

---

## 6. Authorization Strategy / RBAC

| Endpoint | Farmer | Extension Officer | Admin |
|---|---|---|---|
| POST /farms/profile | ✅ Own session | ✅ Any session | ✅ |
| GET /farms/profile | ✅ Own session | ✅ Any | ✅ |
| POST /agents/* | ✅ | ✅ | ✅ |
| POST /review/approve | ❌ | ✅ | ✅ |
| GET /admin/audit-logs | ❌ | ❌ | ✅ |
| DELETE /farms/* | ❌ | ❌ | ✅ |

---

## 7. OpenAPI / Swagger Specification (Summary)

```yaml
openapi: "3.0.3"
info:
  title: FarmAI Decision Intelligence API
  version: "1.0.0"
  description: Agentic AI system for smallholder farm planning

servers:
  - url: http://localhost:8000/api/v1
    description: Local Development

paths:
  /farms/profile:
    post:
      summary: Create farm profile
      operationId: createFarmProfile
      tags: [Farm Profile]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FarmProfileInput'
      responses:
        '201': { description: Profile created }
        '422': { description: Validation error }

  /agents/soil-assessment:
    post:
      summary: Run soil assessment agent
      operationId: runSoilAssessment
      tags: [Agents]

  /agents/weather/{location}:
    get:
      summary: Get weather forecast and alerts
      operationId: getWeatherForecast
      tags: [Agents]

  /agents/crop-suitability:
    post:
      summary: Get ranked crop recommendations
      operationId: getCropSuitability
      tags: [Agents]

  /agents/farm-plan:
    post:
      summary: Generate seasonal operations plan
      operationId: generateFarmPlan
      tags: [Agents]

  /agents/advisory:
    post:
      summary: Agricultural advisory RAG query
      operationId: getAdvisoryAnswer
      tags: [Agents]

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```
