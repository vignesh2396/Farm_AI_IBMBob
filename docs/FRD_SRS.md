# Functional Requirements Document (FRD) & Software Requirements Specification (SRS)
## FarmAI – Agricultural Decision Intelligence System
**Version:** 1.0 | **Date:** 2026-11-04

---

## PART A — FUNCTIONAL REQUIREMENTS

### FR-01: Farm Profile Management
| ID | Requirement |
|---|---|
| FR-01.1 | System shall allow a user to enter farm details: location (district/state), farm size (acres), soil type, current crops, water source |
| FR-01.2 | System shall persist farm profile in session state across agent interactions |
| FR-01.3 | System shall allow the user to update their farm profile at any time |
| FR-01.4 | System shall display a summary of the stored farm profile to the user |

### FR-02: Soil Assessment
| ID | Requirement |
|---|---|
| FR-02.1 | System shall accept soil inputs: pH level, nitrogen (N), phosphorus (P), potassium (K), organic matter %, moisture level |
| FR-02.2 | Soil Assessment Agent shall classify soil type and fertility level |
| FR-02.3 | System shall recommend fertilizer type, quantity, and application schedule |
| FR-02.4 | System shall flag deficiencies (N/P/K) and suggest corrective amendments |
| FR-02.5 | System shall provide confidence score for soil assessment result |

### FR-03: Crop Suitability Analysis
| ID | Requirement |
|---|---|
| FR-03.1 | System shall evaluate minimum 5 candidate crops for the given farm and season |
| FR-03.2 | Crop Suitability Agent shall rank crops based on: soil compatibility, water availability, seasonal calendar, market demand |
| FR-03.3 | System shall display a ranked list with suitability score (0–100) for each crop |
| FR-03.4 | System shall allow the user to select a preferred crop and explain why it ranked as it did |
| FR-03.5 | System shall retrieve supporting evidence from the knowledge base using RAG |

### FR-04: Weather Intelligence
| ID | Requirement |
|---|---|
| FR-04.1 | System shall retrieve 7-day weather forecast for the farm's district |
| FR-04.2 | Weather Intelligence Agent shall identify risk periods (frost, heavy rain, drought) |
| FR-04.3 | System shall emit weather alerts that influence sowing and irrigation recommendations |
| FR-04.4 | System shall cache weather data with a 6-hour TTL to manage API rate limits |

### FR-05: Seasonal Farm Operations Plan
| ID | Requirement |
|---|---|
| FR-05.1 | Farm Operations Planning Agent shall generate a week-by-week seasonal plan covering: sowing, irrigation, fertilization, pest control, and harvest |
| FR-05.2 | System shall adapt the plan when a weather alert is active |
| FR-05.3 | System shall display the plan as a structured calendar/table |
| FR-05.4 | System shall allow the user to download the plan as a text/CSV file |

### FR-06: Agricultural Advisory (RAG)
| ID | Requirement |
|---|---|
| FR-06.1 | Agricultural Advisory Agent shall answer free-text questions about farming practices |
| FR-06.2 | Agent shall retrieve answers from the indexed knowledge base (PDF manuals, guidelines) |
| FR-06.3 | System shall cite the source document and page/section for every retrieved answer |
| FR-06.4 | System shall display a groundedness confidence score |

### FR-07: Multi-Agent Orchestration
| ID | Requirement |
|---|---|
| FR-07.1 | Supervisor Agent shall route user requests to the appropriate specialized agent |
| FR-07.2 | Supervisor Agent shall aggregate outputs from multiple agents into a unified response |
| FR-07.3 | System shall maintain a session conversation history visible to the user |
| FR-07.4 | Agent workflow steps shall be displayed to the user in a collapsible trace panel |

### FR-08: Human-in-the-Loop
| ID | Requirement |
|---|---|
| FR-08.1 | System shall flag recommendations requiring human review (e.g., resource allocation > 1 acre-ft water, pesticide usage) |
| FR-08.2 | System shall present a confirmation dialog before executing high-impact actions |
| FR-08.3 | Extension officer role shall be able to review and approve/reject flagged recommendations |

### FR-09: Explainability
| ID | Requirement |
|---|---|
| FR-09.1 | Every recommendation shall include: data inputs used, rules applied, sources retrieved, confidence score, and key risk factors |
| FR-09.2 | Explainability panel shall be collapsible and available for all agent outputs |
| FR-09.3 | System shall not expose internal LLM chain-of-thought prompts as "reasoning" |

---

## PART B — NON-FUNCTIONAL REQUIREMENTS

### NFR-01: Performance
| ID | Requirement | Target |
|---|---|---|
| NFR-01.1 | Farm profile save response time | < 500ms |
| NFR-01.2 | Single-agent response time (no RAG) | < 10 seconds |
| NFR-01.3 | Full multi-agent workflow (with RAG + weather API) | < 30 seconds |
| NFR-01.4 | UI page load time | < 3 seconds |

### NFR-02: Scalability
| ID | Requirement |
|---|---|
| NFR-02.1 | Application shall support horizontal scaling via container orchestration (future) |
| NFR-02.2 | Vector store shall support up to 10,000 document chunks without degradation |
| NFR-02.3 | Session state design shall not prevent concurrent multi-user access in deployed mode |

### NFR-03: Security
| ID | Requirement |
|---|---|
| NFR-03.1 | API keys shall be loaded from environment variables, never hardcoded |
| NFR-03.2 | No personally identifiable information (PII) shall be stored in the database without explicit consent |
| NFR-03.3 | Input validation shall prevent prompt injection attacks |
| NFR-03.4 | Application shall run with principle of least privilege |

### NFR-04: Availability
| ID | Requirement |
|---|---|
| NFR-04.1 | Application shall achieve ≥ 99.5% availability in production |
| NFR-04.2 | System shall degrade gracefully when external APIs are unavailable |

### NFR-05: Reliability
| ID | Requirement |
|---|---|
| NFR-05.1 | All agent tool calls shall include retry logic (3 attempts with exponential backoff) |
| NFR-05.2 | System shall log all errors with stack traces to a structured log file |
| NFR-05.3 | Agent validation layer shall catch hallucinated or out-of-range recommendations |

### NFR-06: Accessibility
| ID | Requirement |
|---|---|
| NFR-06.1 | UI shall meet WCAG 2.1 Level AA guidelines |
| NFR-06.2 | All interactive elements shall be keyboard navigable |
| NFR-06.3 | Color contrast ratio shall be ≥ 4.5:1 for all text |
| NFR-06.4 | Form inputs shall have descriptive labels and error messages |

### NFR-07: Compliance
| ID | Requirement |
|---|---|
| NFR-07.1 | System shall comply with OWASP Top 10 application security controls |
| NFR-07.2 | Responsible AI guidelines shall be embedded in every agent prompt |
| NFR-07.3 | System shall display AI limitation disclaimer prominently |
| NFR-07.4 | No third-party data sharing without farmer consent |

---

## PART C — USER PERSONAS

### Persona 1: Ravi Kumar — Smallholder Farmer
- **Age:** 42 | **Education:** 8th grade | **Location:** Vidarbha, Maharashtra
- **Farm Size:** 3 acres | **Crops:** Cotton, Soybean | **Water Source:** Borewell
- **Tech Comfort:** Basic smartphone, WhatsApp user
- **Goals:** Know the best crop for this season, reduce fertilizer cost, get irrigation schedule
- **Pain Points:** Can't access extension officer; conflicting advice from agri shops
- **Primary Use:** Mobile browser, voice-to-text input

### Persona 2: Priya Sharma — Agricultural Extension Officer
- **Age:** 31 | **Education:** B.Sc. Agriculture | **Location:** District HQ
- **Responsibility:** Advising 500+ farmers across 10 villages
- **Tech Comfort:** Laptop + smartphone, comfortable with apps
- **Goals:** Quickly generate and review plans for multiple farmers; flag unsafe recommendations
- **Pain Points:** Manual report writing; no tool to aggregate multi-farm data
- **Primary Use:** Desktop browser, review and approval workflows

### Persona 3: NGO Farm Program Manager
- **Age:** 38 | **Education:** M.Sc. Agricultural Economics
- **Goals:** Track aggregate adoption metrics, measure crop plan adherence, generate reports
- **Primary Use:** Admin dashboard (future scope), CSV data export

---

## PART D — USER STORIES & ACCEPTANCE CRITERIA

### Epic 1: Farm Profile & Onboarding

**US-01:** As a farmer, I want to enter my farm details so that the AI can give me relevant recommendations.
- **AC:** Farm profile form accepts location, size, soil type, water source; data persists in session; summary is shown after save.

**US-02:** As a farmer, I want to update my farm profile any time so that I can correct mistakes.
- **AC:** Edit form pre-filled with existing data; updates reflect immediately in all subsequent agent calls.

### Epic 2: Soil Assessment

**US-03:** As a farmer, I want to input my soil test results so that I get a fertilizer recommendation.
- **AC:** Form accepts N, P, K, pH, organic matter; agent returns classified soil type, deficiency list, and fertilizer schedule with confidence score.

**US-04:** As an extension officer, I want to see the reasoning behind the fertilizer recommendation so that I can verify it before advising the farmer.
- **AC:** Explainability panel shows: inputs used, classification rule applied, knowledge-base source cited.

### Epic 3: Crop Suitability

**US-05:** As a farmer, I want to see which crops are most suitable for my farm this season so that I can make an informed planting decision.
- **AC:** System returns ≥5 ranked crops with suitability scores; each crop has a brief justification; farmer can select preferred crop.

**US-06:** As a farmer, I want to understand why a specific crop was ranked #1 so that I trust the recommendation.
- **AC:** Clicking on a crop shows: soil match score, water requirement vs. availability, seasonal calendar fit, retrieved knowledge source.

### Epic 4: Weather Intelligence

**US-07:** As a farmer, I want to see the 7-day weather forecast for my area so that I plan sowing and irrigation accordingly.
- **AC:** Weather panel shows temperature, rainfall, humidity for 7 days; alerts flagged with color indicators (red/yellow/green).

**US-08:** As a farmer, I want the AI to warn me if bad weather is expected during my planned sowing window so I can adjust.
- **AC:** Advisor emits a warning message if forecast shows rainfall > 30mm or temperatures outside crop range on planned sowing date.

### Epic 5: Farm Operations Plan

**US-09:** As a farmer, I want a week-by-week seasonal plan so that I know exactly what to do on my farm each week.
- **AC:** Plan covers 12–16 weeks from sowing to harvest; includes irrigation schedule, fertilization dates, pest monitoring, harvest window.

**US-10:** As a farmer, I want to download my plan as a text file so that I can refer to it offline.
- **AC:** "Download Plan" button generates a downloadable .txt or .csv file.

### Epic 6: Agricultural Advisory

**US-11:** As a farmer, I want to ask questions about farming practices in plain language so that I get expert answers.
- **AC:** Free-text query returns an answer with cited source document; groundedness score is shown.

### Epic 7: Human-in-the-Loop

**US-12:** As an extension officer, I want to review high-impact recommendations before they are shown to the farmer so that I can prevent harmful advice.
- **AC:** System flags recommendations involving pesticides or heavy resource use; confirmation panel displayed before finalizing.

---

## PART E — PRODUCT BACKLOG

| Priority | Epic | Story ID | Story Title | Effort (SP) | Sprint |
|---|---|---|---|---|---|
| 1 | Farm Profile | US-01 | Enter farm details | 3 | 1 |
| 2 | Farm Profile | US-02 | Update farm profile | 2 | 1 |
| 3 | Soil Assessment | US-03 | Input soil data | 3 | 1 |
| 4 | Soil Assessment | US-04 | Review soil reasoning | 2 | 1 |
| 5 | Crop Suitability | US-05 | Get crop ranking | 5 | 1 |
| 6 | Crop Suitability | US-06 | Explain crop ranking | 3 | 2 |
| 7 | Weather | US-07 | View weather forecast | 3 | 2 |
| 8 | Weather | US-08 | Weather sowing alert | 2 | 2 |
| 9 | Operations Plan | US-09 | Generate seasonal plan | 8 | 2 |
| 10 | Operations Plan | US-10 | Download plan | 2 | 3 |
| 11 | Advisory | US-11 | Ask farming question | 5 | 3 |
| 12 | HITL | US-12 | Review high-impact | 3 | 3 |
