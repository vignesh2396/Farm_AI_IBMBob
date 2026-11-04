# Requirement Traceability Matrix (RTM)
## FarmAI – Agricultural Decision Intelligence System
**Version:** 1.0 | **Date:** 2026-11-04

---

## Purpose
Maps every Capstone Guideline requirement to a design decision, implementation component, and evidence of completion.

---

## Section 1: Mandatory Agentic AI Requirements (Guideline Section 4)

| Guideline Requirement | Design Decision | Implementation Component | Evidence |
|---|---|---|---|
| **4.1 — AI Agent**: At least one autonomous AI agent | 6 specialized agents + 1 supervisor | `agents/supervisor_agent.py`, all agent files | `agents/` directory with 7 agent files |
| **4.2 — Multiple Agent Roles**: At least 3 specialized roles | 6 specialized agents with distinct responsibilities | FarmProfile, Soil, Weather, CropSuitability, FarmOps, Advisory agents | `agents/` directory; Architecture HLD |
| **4.3 — Tool Calling**: Minimum 2 tools per project | 5 dedicated tools implemented | `tools/weather_api_tool.py`, `tools/soil_analysis_tool.py`, `tools/crop_db_tool.py`, `tools/rag_tool.py`, `tools/validation_tool.py` | `tools/` directory; 5 tool files |
| **4.4 — RAG**: Domain knowledge retrieval | ChromaDB vector store + agricultural PDFs | `rag/embeddings.py`, `rag/retriever.py`, `rag/documents/` | RAG pipeline; 3 knowledge base documents |
| **4.5 — Agent Memory / State**: Maintain information across steps | `AgentState` dataclass shared across all agents | `agents/supervisor_agent.py` → `AgentState` | State carries profile, soil, weather, crop data through all 6 workflow steps |
| **4.6 — Multi-Step Reasoning**: Multiple actions before final result | 6-step workflow: Profile→Soil→Weather→Crops→Plan→Advisory | Full workflow in `app.py` + supervisor coordination | Sequential agent execution; trace panel shows steps |
| **4.7 — Human-in-the-Loop**: High-impact recommendations reviewed | Flagging via `validation_tool.py`; HITL UI panel | `tools/validation_tool.py` flag_high_impact(); `app.py` HITL panel | TC-05 test case; HITL review panel in UI |
| **4.8 — Explainability**: Show why recommendation was made | Every agent output includes explainability dict | Explainability panels in all agent results + UI | `explainability` key in every agent response; `show_explainability` UI panels |

---

## Section 2: Minimum Project Features (Guideline Table)

| Feature | Min. Requirement | Implementation | Evidence |
|---|---|---|---|
| LLM | 1 | Google Gemini 1.5 Flash | `utils/config.py` GEMINI_MODEL; all agents use `llm` parameter |
| Specialized AI Agent Roles | 3 | **6 implemented**: FarmProfile, Soil, Weather, CropSuitability, FarmOps, Advisory | `agents/` directory |
| Tools / APIs / Functions | 2 | **5 implemented**: weather_api, soil_analysis, crop_db, rag_retriever, validation | `tools/` directory |
| Knowledge Source / Operational Data | At least 1 | **3 sources**: ICAR Cotton Guide, Soil Health Card Guide, Kharif Advisory + Crop Reference CSV | `rag/documents/` + `data/crop_reference.csv` |
| RAG | Recommended | ✅ Fully implemented with ChromaDB | `rag/` directory |
| Agent Memory / State | Required where relevant | ✅ `AgentState` dataclass in SupervisorAgent | `supervisor_agent.py` lines 37–49 |
| Multi-Step Agent Workflow | Required | ✅ 6-step workflow | `app.py` workflow + supervisor trace |
| User Interface | Required | ✅ Streamlit web app with 6 screens | `app.py` |
| Validation Layer | Required | ✅ `ValidationTool` with input + output validation + HITL flagging | `tools/validation_tool.py` |
| Human-in-the-Loop | Required for high-impact | ✅ Automatic flagging + officer review panel | `app.py` HITL section; TC-05 |
| Test Scenarios | Minimum 5 | ✅ **9 scenarios** documented | `tests/test_cases.md` |
| Architecture Diagram | Required | ✅ ASCII architecture diagrams in HLD doc | `docs/Architecture_HLD_LLD.md` |
| GitHub Repository | Required | ✅ Complete repository structure + README | All files; `README.md` |
| README | Required | ✅ Comprehensive GitHub-ready README | `README.md` |

---

## Section 3: Project Deliverables (Guideline Section 8)

| Deliverable | Requirement | File(s) | Status |
|---|---|---|---|
| Source Code | Complete, readable, logically structured | All `agents/`, `tools/`, `rag/`, `utils/` + `app.py` | ✅ Complete |
| GitHub Repository | Full repo with README, requirements.txt, .env.example, screenshots, architecture | Entire FarmAI directory | ✅ Ready |
| Project README | Project title, domain, agents, tech stack, installation, test scenarios | `README.md` | ✅ Complete |
| Architecture / Workflow Diagram | User→Supervisor→Agents→Tools→Output flow | `docs/Architecture_HLD_LLD.md` (ASCII + text diagrams) | ✅ Complete |
| Working Application | Functional prototype, web interface | `app.py` (Streamlit) | ✅ Complete |
| Test Cases | Minimum 5 realistic scenarios | `tests/test_cases.md` (9 scenarios) | ✅ Complete — 9/9 pass |

---

## Section 4: Industry-Level Expectations (Guideline Section 9)

| Expectation | Design Response | Evidence |
|---|---|---|
| **Target User** | Smallholder farmers + agricultural extension officers | Personas 1 & 2 in FRD; "Extension Officer Mode" in UI |
| **Industry Problem** | Fragmented information prevents optimal farm-management decisions | BRD Section 2: Problem Analysis |
| **AI-Assisted Decision** | Crop selection, fertilizer planning, irrigation scheduling, seasonal planning | All 6 agent outputs |
| **Agent Responsibilities** | Clearly defined per agent | Architecture HLD + README Agent table |
| **Tools** | Open-Meteo API, soil rules engine, crop CSV DB, ChromaDB RAG | `tools/` directory |
| **Human Oversight** | HITL for high-impact recs; explainability for all | HITL panel; explainability dicts in all agent outputs |
| **Business / Social Impact** | Decision time ↓, yield ↑, input costs ↓, advisory reach ↑ | BRD Section 5: Success Metrics; PPT Slide 3 |
| **Measurable Indicators** | Confidence scores, suitability scores, groundedness scores, response times | UI metric displays; performance test results |

---

## Section 5: Responsible AI Guidelines (Guideline Section 11)

| Principle | Implementation | File/Location |
|---|---|---|
| User privacy | No PII stored; session_id anonymization; consent banner | `utils/db.py`; `app.py` |
| Data security | Secrets in .env; parameterized SQL; no keys in code | `.env.example`; `utils/db.py` |
| Bias | Multi-factor scoring; transparent weights; no demographic assumptions | `tools/crop_db_tool.py` |
| Hallucination | RAG grounding; groundedness scoring; validation layer | `tools/validation_tool.py`; `rag/retriever.py` |
| Explainability | Explainability dict on every agent output; collapsible panels | All agent files; `app.py` |
| Consent | Consent notice on first load; "Clear My Data" button | `app.py` sidebar |
| Human oversight | HITL for high-impact; officer review workflow | `app.py` HITL section |
| Reliability | Retry logic; graceful fallbacks; error logging | All tool files with retry logic |
| Responsible use of personal info | Only farm data collected; no demographic/financial PII | BRD Section 9: Privacy Controls |

---

## Section 6: Complete SDLC Documentation Coverage

| Phase | Document | File | Status |
|---|---|---|---|
| Phase 1: Business Analysis | BRD | `docs/BRD.md` | ✅ |
| Phase 2: Requirements | FRD + SRS | `docs/FRD_SRS.md` | ✅ |
| Phase 3: UX/UI Design | UX/UI Document | `docs/UX_UI_Design.md` | ✅ |
| Phase 4: Architecture | HLD + LLD | `docs/Architecture_HLD_LLD.md` | ✅ |
| Phase 5: Database | DB Design | `docs/Database_Design.md` | ✅ |
| Phase 6: API Design | API Specification | `docs/API_Design.md` | ✅ |
| Phase 7: Security | Security Architecture | `docs/Security_Architecture.md` | ✅ |
| Phase 8: Development | Dev Plan + CI/CD | `docs/Development_Plan.md` | ✅ |
| Phase 9: Testing | Test Strategy + LLM Eval | `docs/Testing_Strategy.md` | ✅ |

---

## Section 7: Learning Outcomes Mapping

| Learning Outcome | Evidence |
|---|---|
| Build an Agentic AI system | 6 specialized agents + supervisor; multi-step workflow |
| Use tool calling | 5 tools: weather API, soil rules, crop DB, RAG, validation |
| Implement RAG | ChromaDB vector store + agricultural knowledge base |
| Maintain agent state | `AgentState` dataclass persisted across 6-step workflow |
| Implement Human-in-the-Loop | Automatic HITL flagging + officer review panel |
| Produce explainable AI | `explainability` key in all agent outputs; reasoning shown to user |
| Apply Responsible AI | Privacy controls, groundedness scoring, disclaimer, consent |
| Test AI agents | 9 test scenarios including LLM/agent evaluation framework |
| Deploy a working application | Streamlit app; GitHub repository; Streamlit Cloud deployable |
