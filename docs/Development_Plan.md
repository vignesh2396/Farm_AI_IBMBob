# Development Plan
## FarmAI – Agricultural Decision Intelligence System
**Version:** 1.0 | **Date:** 2026-11-04

---

## 1. Repository Structure

```
farmai_ibmbob/
│
├── app.py                          # Main Streamlit application entry point
│
├── agents/
│   ├── __init__.py
│   ├── supervisor_agent.py         # Orchestrator: routes requests to specialized agents
│   ├── farm_profile_agent.py       # Farm profile CRUD operations
│   ├── soil_assessment_agent.py    # Soil classification + fertilizer recommendation
│   ├── weather_intelligence_agent.py # Weather forecast + alert generation
│   ├── crop_suitability_agent.py   # Multi-factor crop ranking
│   ├── farm_ops_planning_agent.py  # Seasonal week-by-week plan generator
│   └── agricultural_advisory_agent.py # RAG-backed Q&A agent
│
├── tools/
│   ├── __init__.py
│   ├── weather_api_tool.py         # Open-Meteo API integration
│   ├── soil_analysis_tool.py       # Rule-based soil classification engine
│   ├── crop_db_tool.py             # CSV crop database lookup
│   ├── rag_tool.py                 # ChromaDB retriever interface
│   └── validation_tool.py          # Output validation + high-impact flagging
│
├── rag/
│   ├── __init__.py
│   ├── documents/                  # Source PDFs and text files for knowledge base
│   │   ├── icar_cotton_guide.txt
│   │   ├── soil_health_card_guide.txt
│   │   └── kharif_crop_advisory.txt
│   ├── embeddings.py               # Document chunking + embedding pipeline
│   └── retriever.py                # Query interface for vector store
│
├── data/
│   ├── farmdata.db                 # SQLite database (gitignored in production)
│   ├── crop_reference.csv          # Crop suitability reference dataset
│   └── soil_fertility_rules.json   # Soil classification rule definitions
│
├── models/
│   └── .gitkeep                    # Placeholder for future ML models
│
├── utils/
│   ├── __init__.py
│   ├── helpers.py                  # Common utilities (date, text formatting)
│   ├── logger.py                   # Structured logging setup
│   ├── db.py                       # SQLite connection + schema initialization
│   └── config.py                   # Configuration loading from .env
│
├── tests/
│   ├── test_cases.md               # 5+ test scenario definitions
│   ├── test_soil_agent.py          # Unit tests for soil assessment
│   ├── test_weather_tool.py        # Unit tests for weather tool
│   ├── test_crop_suitability.py    # Unit tests for crop ranking
│   ├── test_farm_plan.py           # Integration test for full planning flow
│   └── test_validation.py          # Tests for validation + HITL flagging
│
├── assets/
│   ├── architecture.png            # Architecture diagram (exported from design doc)
│   ├── farmai_logo.png             # Application logo
│   └── screenshots/               # Application screenshots for README
│
├── docs/
│   ├── BRD.md
│   ├── FRD_SRS.md
│   ├── UX_UI_Design.md
│   ├── Architecture_HLD_LLD.md
│   ├── Database_Design.md
│   ├── API_Design.md
│   ├── Security_Architecture.md
│   ├── Development_Plan.md
│   ├── Testing_Strategy.md
│   └── RTM.md
│
├── requirements.txt                # Python dependencies with versions
├── .env.example                    # Environment variable template
├── .gitignore                      # Git exclusion rules
└── README.md                       # GitHub-ready project documentation
```

---

## 2. Coding Standards

### Python Style
- **PEP 8** compliant; enforced via `flake8`
- **Type hints** on all function signatures: `def assess_soil(data: SoilInput) -> SoilResult:`
- **Docstrings**: Google style on all classes and public methods
- **Line length**: Max 120 characters
- **Imports**: Grouped: stdlib → third-party → local; sorted alphabetically within groups

### Naming Conventions
| Element | Convention | Example |
|---|---|---|
| Classes | PascalCase | `SoilAssessmentAgent` |
| Functions/Methods | snake_case | `get_crop_ranking()` |
| Constants | UPPER_SNAKE_CASE | `MAX_CROPS_TO_RANK = 10` |
| Variables | snake_case | `soil_classification` |
| Files | snake_case | `soil_assessment_agent.py` |
| Database columns | snake_case | `ph_level` |

### Code Quality Rules
- No function longer than 50 lines; split into helpers if needed
- No global mutable state; use dataclasses or Pydantic models
- All agent responses wrapped in try/except with structured error logging
- All API calls include timeout and retry logic
- All user inputs sanitized before use in prompts or SQL

---

## 3. Git Workflow

### Branching Strategy (GitHub Flow)

```
main
  └─ feature/phase1-farm-profile
  └─ feature/phase1-soil-assessment
  └─ feature/phase2-weather-intelligence
  └─ feature/phase2-crop-suitability
  └─ feature/phase3-farm-plan
  └─ feature/phase3-advisory-rag
  └─ bugfix/weather-cache-ttl
  └─ release/v1.0.0
```

**Branch Rules:**
- `main` branch is always deployable
- All features developed in dedicated feature branches
- PRs require passing CI checks before merge
- Squash merge to keep `main` history clean
- Tags `v1.0.0`, `v1.1.0` follow semantic versioning

### Commit Message Convention (Conventional Commits)
```
feat: add soil assessment agent
fix: handle Open-Meteo API timeout gracefully
docs: add architecture diagram to README
test: add unit tests for crop suitability ranking
refactor: extract validation logic into ValidationLayer class
chore: update requirements.txt with pinned versions
```

---

## 4. Sprint Plan (4-Day Capstone)

### Day 1 — Foundation & Core Infrastructure
| Task | Owner | Hours |
|---|---|---|
| Project setup: repo, venv, requirements.txt | Dev | 0.5 |
| Database schema creation (db.py + SQLite) | Dev | 1.0 |
| Farm Profile Agent + SQLite CRUD | Dev | 1.5 |
| Soil data structures + rules engine (soil_fertility_rules.json) | Dev | 1.0 |

### Day 2 — Agent Development
| Task | Owner | Hours |
|---|---|---|
| Soil Assessment Agent (Gemini + rules) | Dev | 1.5 |
| Weather Intelligence Agent (Open-Meteo + caching) | Dev | 1.5 |
| Crop Suitability Agent (CSV lookup + scoring) | Dev | 1.0 |

### Day 3 — Advanced Agents & RAG
| Task | Owner | Hours |
|---|---|---|
| RAG pipeline (embeddings.py + ChromaDB + knowledge docs) | Dev | 2.0 |
| Agricultural Advisory Agent (RAG Q&A) | Dev | 1.0 |
| Farm Ops Planning Agent (full seasonal plan) | Dev | 1.0 |

### Day 4 — UI, Integration & Testing
| Task | Owner | Hours |
|---|---|---|
| Streamlit UI (all screens, agent trace panel) | Dev | 2.0 |
| Supervisor Agent + full workflow integration | Dev | 1.0 |
| 5 test scenarios execution + documentation | Dev | 0.5 |
| README, .gitignore, .env.example, screenshots | Dev | 0.5 |

---

## 5. CI/CD Pipeline Design

```yaml
# .github/workflows/ci.yml (design)

name: FarmAI CI Pipeline

on:
  push:
    branches: [main, feature/*, bugfix/*]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install flake8
      - run: flake8 . --max-line-length=120 --exclude=.venv

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install pip-audit
      - run: pip-audit -r requirements.txt

  test:
    runs-on: ubuntu-latest
    env:
      GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --tb=short

  deploy-staging:
    needs: [lint, security-scan, test]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Streamlit Cloud
        run: echo "Streamlit Cloud auto-deploys from main branch"
```

---

## 6. Release Strategy

| Release | Scope | Target Date |
|---|---|---|
| v0.1.0 | Farm Profile + Soil Assessment (Day 1–2) | Day 2 EOD |
| v0.2.0 | Weather + Crop Suitability + Partial UI | Day 3 EOD |
| v1.0.0 | Full MVP: All agents + RAG + UI + Tests | Day 4 EOD |
| v1.1.0 | Bug fixes post-demo | Post-capstone |

**Tagging Commands:**
```bash
git tag -a v1.0.0 -m "FarmAI MVP release — all agents operational"
git push origin v1.0.0
```
