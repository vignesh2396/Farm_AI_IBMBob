# 🌱 FarmAI — Agricultural Decision Intelligence System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red?logo=streamlit)
![Google Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-orange?logo=google)
![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-green)
![License](https://img.shields.io/badge/License-MIT-purple)
![Status](https://img.shields.io/badge/Status-MVP%20Ready-brightgreen)

**AI-Powered Smallholder Farm Planning & Agricultural Decision Intelligence**

*IBM SkillsBuild Agentic AI Capstone Project | 2026*

</div>

---

## 📋 Project Overview

**FarmAI** is an Agentic AI-powered farm planning platform designed for smallholder farmers. It consolidates fragmented agricultural data — soil conditions, weather forecasts, crop databases, and expert knowledge — into a single intelligent planning workflow. Six specialized AI agents collaborate under a Supervisor Agent to deliver explainable, data-driven recommendations for seasonal crop planning, irrigation scheduling, fertilizer management, and agricultural advisory.

---

## 🌍 Domain & Problem Statement

| | |
|---|---|
| **Domain** | Agriculture / AgriTech |
| **Target Users** | Smallholder farmers, Agricultural extension officers, NGOs |
| **Industry Challenge** | Fragmented agricultural information forces farmers to make complex decisions without integrated data or timely expert advice |
| **AI-Assisted Decision** | Crop selection, fertilizer planning, irrigation scheduling, seasonal operations planning |

### The Challenge
Smallholder farmers (70%+ of food producers in developing economies) must make interconnected decisions about crops, soil, weather, irrigation, and budgets. Access to personalized agricultural advisory is limited by the farmer-to-extension-officer ratio (often 3,000:1).

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🏡 Farm Profile Management | Capture and persist farm location, size, soil type, water source, and season |
| 🧪 Soil Assessment | AI-powered soil classification with fertilizer recommendations and deficiency detection |
| 🌤️ Weather Intelligence | 7-day weather forecast with risk alerts (drought, heat, heavy rain) |
| 🌾 Crop Suitability Ranking | Multi-factor crop scoring (soil + water + season + market) with RAG enrichment |
| 📅 Farm Operations Plan | Week-by-week seasonal plan adapted to weather and soil conditions |
| 💬 Agricultural Advisory | RAG-grounded Q&A backed by agricultural knowledge base documents |
| 🔍 Explainability | Every recommendation includes data inputs, rules applied, and sources cited |
| 👥 Human-in-the-Loop | High-impact recommendations require extension officer review and approval |
| 📥 Plan Download | Export seasonal plan as a plain-text file for offline use |

---

## 🤖 AI Agent Architecture

```
User → Supervisor Agent
           │
    ┌──────┼──────────────────────────────────────────────┐
    │      │              │               │                │
    ▼      ▼              ▼               ▼                ▼
FarmProfile  SoilAssessment  Weather    CropSuitability  Advisory
  Agent        Agent        Intelligence   Agent          Agent
                              Agent                         │
    │      │              │               │                 │
    ▼      ▼              ▼               ▼                 ▼
  SQLite  Rules Engine  Open-Meteo    Crop CSV DB     ChromaDB RAG
  CRUD    + Gemini LLM  Weather API   + Gemini LLM   + Gemini LLM
                                      
                         FarmOps Planning Agent
                              │
                              ▼
                         Gemini LLM + Validation Layer
                              │
                              ▼ (if high-impact)
                         Human Review Panel (HITL)
```

### Agent Responsibilities

| Agent | Responsibility | Tools Used |
|---|---|---|
| **SupervisorAgent** | Route requests, coordinate agents, maintain state | All agents |
| **FarmProfileAgent** | Store and retrieve farm profile data | SQLite CRUD |
| **SoilAssessmentAgent** | Classify soil, compute fertilizer plan | Rule engine + Gemini LLM |
| **WeatherIntelligenceAgent** | Fetch forecast, detect risk periods | Open-Meteo API |
| **CropSuitabilityAgent** | Multi-factor crop ranking | Crop CSV DB + RAG |
| **FarmOpsPlanningAgent** | Generate week-by-week seasonal plan | Gemini LLM |
| **AgriculturalAdvisoryAgent** | Answer RAG-backed farming questions | ChromaDB + Gemini LLM |

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **LLM** | Google Gemini 1.5 Flash (`gemini-1.5-flash`) |
| **Agent Framework** | Custom Python Agentic Architecture |
| **UI** | Streamlit 1.35+ |
| **Vector Store** | ChromaDB (local persistent) |
| **Database** | SQLite 3 |
| **Weather API** | Open-Meteo (free, no API key required) |
| **Language** | Python 3.11 |
| **Embeddings** | Google Generative AI Embeddings (or default sentence-transformers) |

---

## 📁 Repository Structure

```
farmai_ibmbob/
├── app.py                              # Main Streamlit application
├── agents/
│   ├── supervisor_agent.py             # Orchestration + state management
│   ├── farm_profile_agent.py           # Farm profile CRUD
│   ├── soil_assessment_agent.py        # Soil classification + LLM analysis
│   ├── weather_intelligence_agent.py   # Weather forecast + alerts
│   ├── crop_suitability_agent.py       # Multi-factor crop ranking
│   ├── farm_ops_planning_agent.py      # Seasonal plan generation
│   └── agricultural_advisory_agent.py  # RAG-powered Q&A
├── tools/
│   ├── weather_api_tool.py             # Open-Meteo API + cache
│   ├── soil_analysis_tool.py           # Rule-based soil engine
│   ├── crop_db_tool.py                 # CSV crop database lookup
│   ├── rag_tool.py                     # ChromaDB retriever interface
│   └── validation_tool.py             # Output validation + HITL flagging
├── rag/
│   ├── documents/                      # Agricultural knowledge base (PDFs/text)
│   ├── embeddings.py                   # Document ingestion + embedding pipeline
│   └── retriever.py                    # Vector store query interface
├── data/
│   ├── farmdata.db                     # SQLite database
│   ├── crop_reference.csv              # Crop suitability reference data
│   └── soil_fertility_rules.json       # Soil classification rules
├── utils/
│   ├── config.py                       # Configuration management
│   ├── logger.py                       # Structured logging
│   ├── db.py                           # SQLite connection + schema init
│   └── helpers.py                      # Common utilities
├── tests/
│   ├── test_cases.md                   # 9 realistic test scenarios
│   ├── test_soil_agent.py              # Soil assessment unit tests
│   ├── test_crop_suitability.py        # Crop ranking unit tests
│   └── test_validation.py             # Validation + HITL tests
├── docs/
│   ├── BRD.md                         # Business Requirements Document
│   ├── FRD_SRS.md                     # Functional + Software Requirements
│   ├── UX_UI_Design.md                # UX/UI Design + Wireframes
│   ├── Architecture_HLD_LLD.md        # HLD + LLD Architecture Diagrams
│   ├── Database_Design.md             # ER Diagram + DDL + Data Dictionary
│   ├── API_Design.md                  # REST API + OpenAPI Spec
│   ├── Security_Architecture.md       # OWASP + Auth + RBAC
│   ├── Development_Plan.md            # Sprint Plan + CI/CD
│   └── Testing_Strategy.md           # Test Strategy + LLM Evaluation
├── assets/                            # Architecture diagrams, screenshots
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment variable template
├── .gitignore                         # Git exclusion rules
└── README.md                          # This file
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.11 or higher
- pip
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/vignesh2396/farmai_IBMBob.git
cd farmai_IBMBob
```

### Step 2: Create and Activate Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
GOOGLE_API_KEY=your_actual_gemini_api_key_here
```

> **Note:** Weather API (Open-Meteo) is free and requires no API key.

### Step 5: Initialize the Knowledge Base

```bash
python -m rag.embeddings
```

This creates the ChromaDB vector store from agricultural knowledge documents.

---

## 🚀 Running the Application

```bash
streamlit run app.py
```

Open your browser to: `http://localhost:8501`

---

## 🧪 Testing Instructions

### Run All Unit Tests
```bash
pytest tests/ -v
```

### Run Specific Test Modules
```bash
pytest tests/test_soil_agent.py -v
pytest tests/test_crop_suitability.py -v
pytest tests/test_validation.py -v
```

### View Test Scenarios
See [`tests/test_cases.md`](tests/test_cases.md) for 9 documented test scenarios.

---

## 🔑 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GOOGLE_API_KEY` | ✅ Yes | — | Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-1.5-flash` | Gemini model name |
| `LLM_TEMPERATURE` | No | `0.2` | LLM response temperature |
| `DB_PATH` | No | `data/farmdata.db` | SQLite database path |
| `CHROMA_PERSIST_DIR` | No | `data/chroma_db` | ChromaDB storage directory |
| `DOCUMENTS_DIR` | No | `rag/documents` | Knowledge base documents folder |
| `WEATHER_CACHE_TTL_HOURS` | No | `6` | Weather data cache duration |
| `DEBUG_MODE` | No | `false` | Enable debug logging |
| `LOG_LEVEL` | No | `INFO` | Logging level |

---

## 🌐 Deployment Instructions

### Local Development
```bash
streamlit run app.py --server.port 8501
```

### Streamlit Community Cloud
1. Push repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect GitHub repository
4. Set `GOOGLE_API_KEY` in Streamlit Cloud secrets
5. Deploy — auto-deploys from `main` branch

### Docker (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```

---

## 📸 Screenshots

| Screen | Description |
|---|---|
| `assets/screenshots/01_landing.png` | Landing page with feature overview |
| `assets/screenshots/02_farm_profile.png` | Farm profile setup form |
| `assets/screenshots/03_soil_assessment.png` | Soil assessment results with fertilizer plan |
| `assets/screenshots/04_weather_panel.png` | 7-day forecast with alerts |
| `assets/screenshots/05_crop_ranking.png` | Crop suitability ranking cards |
| `assets/screenshots/06_operations_plan.png` | Week-by-week seasonal plan |
| `assets/screenshots/07_advisory_chat.png` | Agricultural advisory RAG chat |
| `assets/screenshots/08_agent_trace.png` | Agent workflow trace panel |

---

## 🔮 Future Enhancements

| Enhancement | Priority |
|---|---|
| Multi-language support (Hindi, Telugu, Kannada) | High |
| Mobile app (Flutter/React Native) | High |
| Satellite imagery integration (NDVI analysis) | Medium |
| Real-time IoT sensor integration | Medium |
| Market price prediction via commodity APIs | Medium |
| Offline mode with local LLM (Llama/Mistral) | Medium |
| Multi-farm management for extension officers | High |
| Financial planning module (input cost calculator) | Low |
| WhatsApp/SMS bot interface | High |

---

## 🔒 Responsible AI Disclaimer

> FarmAI provides AI-generated recommendations for informational and decision-support purposes only. 
> All recommendations should be verified by a qualified agricultural extension officer before implementation.
> The system does not replace professional agricultural advice. High-impact decisions involving 
> pesticides, large resource allocations, or significant financial commitments require human review.

---

## 👨‍💻 Contributors

- **Developer:** Vignesh (IBM SkillsBuild Agentic AI Capstone, 2026)
- **Guided by:** IBM Bob AI Assistant

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with ❤️ using IBM Bob | Agentic AI Capstone Project 2026*
