# Architecture Design Document — HLD & LLD
## FarmAI – Agricultural Decision Intelligence System
**Version:** 1.0 | **Date:** 2026-11-04

---

## PART A — HIGH-LEVEL DESIGN (HLD)

### 1. Architecture Overview

FarmAI follows a **Layered Agentic Architecture** with four horizontal layers:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                               │
│           Streamlit Web Application  (app.py)                           │
│   Farm Profile │ Soil Panel │ Weather Panel │ Crop Ranking │ Chat UI    │
└──────────────────────────────────────┬───────────────────────────────────┘
                                       │ HTTP / Function Calls
┌──────────────────────────────────────▼───────────────────────────────────┐
│                       ORCHESTRATION LAYER                               │
│              Supervisor Agent  (supervisor_agent.py)                    │
│    Intent Routing │ Workflow Coordination │ State Management             │
└──────┬──────────────────┬──────────────────┬───────────────┬────────────┘
       │                  │                  │               │
┌──────▼──────┐  ┌────────▼────────┐  ┌─────▼──────┐  ┌────▼──────────┐
│Farm Profile │  │Soil Assessment  │  │Crop        │  │Weather       │
│  Agent      │  │  Agent          │  │Suitability │  │Intelligence  │
│             │  │                 │  │  Agent     │  │  Agent       │
└──────┬──────┘  └────────┬────────┘  └─────┬──────┘  └────┬──────────┘
       │                  │                  │               │
       └──────────────────┴──────────────────┴───────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────────┐
│                        TOOL LAYER                                       │
│  Weather API Tool  │  Soil Analysis Tool  │  Crop DB Tool  │  RAG Tool  │
│  Farm Plan Tool    │  Validation Tool     │  Export Tool                │
└──────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────────┐
│                       DATA & KNOWLEDGE LAYER                            │
│   SQLite DB  │  ChromaDB Vector Store  │  CSV Datasets  │  PDF Docs    │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2. Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│  app.py  ──►  SupervisorAgent                                          │
│                     │                                                   │
│              ┌──────┼────────────────────────────────────────┐         │
│              │      │                 │                       │         │
│   FarmProfile  SoilAssessment   CropSuitability  WeatherIntel │         │
│     Agent       Agent              Agent          Agent       │         │
│              │      │                 │                       │         │
│              │  FarmOpsPlan      AgricAdvisory                │         │
│              │     Agent           Agent                      │         │
│              └──────┼────────────────────────────────────────┘         │
│                     │                                                   │
│        ┌────────────┼─────────────────────────────┐                    │
│        │            │              │               │                    │
│   weather_api   soil_tools    crop_db_tools    rag_retriever            │
│    (Open-Meteo) (rule-based)  (CSV lookup)  (ChromaDB/FAISS)           │
│        │            │              │               │                    │
│   [External]   [Local]         [Local CSV]   [Local Vector DB]         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3. Deployment Diagram

```
[Developer / User Machine]
       │
       ▼
┌─────────────────────────────────────────┐
│  Python 3.11 Virtual Environment        │
│  ┌────────────────────────────────────┐ │
│  │  Streamlit HTTP Server :8501       │ │
│  │  ┌──────────────────────────────┐  │ │
│  │  │  app.py  (Streamlit App)     │  │ │
│  │  │  agents/ (6 Agent Modules)   │  │ │
│  │  │  tools/  (5 Tool Modules)    │  │ │
│  │  │  rag/    (ChromaDB + FAISS)  │  │ │
│  │  └──────────────────────────────┘  │ │
│  │  SQLite: farmdata.db               │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
       │ HTTPS API Calls
       ▼
┌──────────────────────────────────────┐
│  External Services (Cloud)           │
│  ┌─────────────────┐  ┌───────────┐  │
│  │ Google Gemini   │  │Open-Meteo │  │
│  │ Generative AI   │  │Weather API│  │
│  │  (LLM)          │  │(Free Tier)│  │
│  └─────────────────┘  └───────────┘  │
└──────────────────────────────────────┘
```

### 4. Service Architecture

| Service | Technology | Responsibility |
|---|---|---|
| Web UI | Streamlit 1.35+ | User interface, session state management |
| Supervisor Agent | LangGraph / Custom | Route requests, coordinate agents, aggregate results |
| Farm Profile Agent | Python + SQLite | Store and retrieve farm profile data |
| Soil Assessment Agent | Gemini + Rules Engine | Classify soil, compute fertilizer recommendations |
| Crop Suitability Agent | Gemini + CSV lookup | Rank crops by multi-factor scoring |
| Weather Intelligence Agent | Open-Meteo API | Fetch forecast, detect risk periods, emit alerts |
| Farm Operations Planning Agent | Gemini | Generate week-by-week seasonal plan |
| Agricultural Advisory Agent | Gemini + RAG | Answer queries from knowledge base |
| RAG Pipeline | ChromaDB + langchain | Embed, index, retrieve document chunks |
| Data Store | SQLite + CSV | Persist farm profiles, crop database |
| Vector Store | ChromaDB | Store document embeddings for RAG |

---

## PART B — LOW-LEVEL DESIGN (LLD)

### 1. Class Diagram

```
┌─────────────────────────────────┐
│         SupervisorAgent         │
├─────────────────────────────────┤
│ - llm: ChatGoogleGenerativeAI   │
│ - graph: StateGraph             │
│ - state: AgentState             │
├─────────────────────────────────┤
│ + route(request) → AgentNode    │
│ + run(user_input) → Response    │
│ + get_trace() → List[StepTrace] │
└────────────┬────────────────────┘
             │ uses
    ┌─────────┼──────────────────────────────────────────────┐
    │         │               │                │             │
┌───▼──┐  ┌──▼──┐      ┌─────▼──┐       ┌─────▼──┐   ┌─────▼──┐
│Farm  │  │Soil │      │Crop    │       │Weather │   │FarmOps│
│Prof  │  │Asmt │      │Suit    │       │Intel   │   │Plan   │
│Agent │  │Agent│      │Agent   │       │Agent   │   │Agent  │
└───┬──┘  └──┬──┘      └─────┬──┘       └─────┬──┘   └─────┬──┘
    │        │               │                 │             │
    ▼        ▼               ▼                 ▼             ▼
 SQLite  SoilTool        CropDBTool      WeatherAPI      PlanTool
  CRUD   RuleEngine      CSVLookup       OpenMeteo       Calendar

┌────────────────────────────────┐
│       AgricAdvisoryAgent       │
├────────────────────────────────┤
│ - retriever: VectorRetriever   │
│ - llm: ChatGoogleGenerativeAI  │
├────────────────────────────────┤
│ + answer(query) → RAGResponse  │
│ + cite_sources() → List[Source]│
└────────────────────────────────┘

┌────────────────────────────────┐
│        ValidationLayer         │
├────────────────────────────────┤
│ + validate_soil(result)        │
│ + validate_crop_score(score)   │
│ + check_groundedness(resp)     │
│ + flag_high_impact(rec)        │
└────────────────────────────────┘
```

### 2. Sequence Diagram — Full Crop Planning Flow

```
User → Streamlit → SupervisorAgent → FarmProfileAgent → [SQLite]
          │                │               │
          │         profile_saved          │
          │                │               │
          │         → SoilAssessmentAgent → SoilTool
          │                │               │
          │         soil_result_with_conf  │
          │                │               │
          │         → WeatherIntelAgent → Open-Meteo API
          │                │               │
          │         weather_data+alerts    │
          │                │               │
          │         → CropSuitabilityAgent → CropDBTool + RAG
          │                │               │
          │         ranked_crops           │
          │                │               │
          │         → ValidationLayer      │
          │                │               │
          │         → FarmOpsPlanning → PlanGenerator
          │                │               │
          │         operations_plan        │
          │                │               │
          │     [if high-impact flagged] → HumanReviewPanel
          │                │               │
          │          final_plan            │
          │                │               │
          ◄───────────────────────────────
```

### 3. Activity Diagram — Crop Recommendation Decision

```
[Start]
   ↓
Input Farm Profile
   ↓
Input Soil Data
   ↓
Classify Soil ──── [Confidence < 60%] ──→ Request More Soil Data
   ↓ [≥60%]
Fetch Weather Forecast
   ↓
[Weather API Available?] ──[No]──→ Use Cached/Default Forecast
   ↓ [Yes]
Evaluate 5+ Crops Against: Soil Score + Water Score + Season Score
   ↓
[Any crop score > 50?] ──[No]──→ Notify: No suitable crops found; suggest alternatives
   ↓ [Yes]
Retrieve RAG Knowledge for Top 3 Crops
   ↓
Rank & Score Crops
   ↓
[User Selects Crop]
   ↓
Generate Operations Plan
   ↓
[Plan contains high-impact items?] ──[Yes]──→ Flag for Human Review
   ↓ [No]
Display Final Plan + Explainability
   ↓
[End]
```

### 4. State Diagram — Agent Session

```
[Idle] ──user_input──→ [Routing]
                           │
              ┌────────────┼──────────────┐
              │            │              │
          [Soil       [Weather       [Crop
         Assessment]  Intelligence]  Suitability]
              │            │              │
              └────────────┼──────────────┘
                           │
                    [Planning / RAG]
                           │
                   [Validation Check]
                           │
              [Flagged?] ──Yes──→ [Human Review]
                   │                    │
                  No              [Approved/Rejected]
                   │                    │
                   └────────────────────┘
                           │
                    [Response Delivered]
                           │
              [User continues?] ──Yes──→ [Routing]
                           │
                          No
                           │
                       [Session End]
```

---

## 5. Agent Responsibilities Summary

| Agent | Input | Output | Tools Used |
|---|---|---|---|
| SupervisorAgent | User query | Routed response | All agents |
| FarmProfileAgent | Form data | Stored profile | SQLite CRUD |
| SoilAssessmentAgent | N/P/K/pH values | Classification + fertilizer plan | Soil rules engine |
| WeatherIntelligenceAgent | Location | 7-day forecast + alerts | Open-Meteo API |
| CropSuitabilityAgent | Profile + Soil + Weather | Ranked crop list | Crop CSV DB + RAG |
| FarmOpsPlanningAgent | Profile + Crop + Weather | Week-by-week plan | Plan generator |
| AgriculturalAdvisoryAgent | Free-text query | RAG-grounded answer | ChromaDB retriever |
| ValidationLayer | Any agent output | Validated/flagged output | Rule checks |
