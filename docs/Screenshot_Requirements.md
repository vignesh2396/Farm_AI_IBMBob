# Screenshot Requirements
## FarmAI – Agricultural Decision Intelligence System
**Version:** 1.0 | **Date:** 2026-11-04

All screenshots should be captured at 100% browser zoom, in a 1280×800 or wider window.
Save all files to: `assets/screenshots/`

---

## SCR-01: Landing Page / Home
**Filename:** `01_landing.png`
**Purpose:** Show product overview and entry point
**Expected Display:**
- FarmAI logo and title visible at top
- Feature cards: Soil Assessment, Weather Intelligence, Crop Suitability, Seasonal Plan
- "Start Planning" button prominently visible
- AI Disclaimer footer visible
- Navigation sidebar with all 6 steps listed
**Capture:** Full page including sidebar

---

## SCR-02: Farm Profile Setup
**Filename:** `02_farm_profile.png`
**Purpose:** Show data input form for farm context
**Expected Display:**
- Form with District = "Akola", State = "Maharashtra"
- Farm Size = 3 acres
- Soil Type = "Black Cotton" selected
- Water Source = "Borewell" selected
- Season = "Kharif" selected
- "Save Farm Profile & Continue" button visible
**Capture:** Full form filled out before submitting

---

## SCR-03: Soil Assessment Results
**Filename:** `03_soil_assessment.png`
**Purpose:** Show AI-generated soil classification and fertilizer recommendation
**Expected Display:**
- Three metric boxes: "Vertisol", "Medium", "82%"
- Progress bar at 82% confidence
- Green pH status: "✅ pH Status: Neutral (Optimal)"
- Red deficiency alert: "🔴 Nutrient Deficiencies: Nitrogen (Low)"
- Fertilizer table with 3 rows (Urea, DAP, ZnSO₄)
- "AI Explanation" expander open showing narrative text
- "Why this recommendation?" expander visible
**Capture:** Full panel including expanded expanders

---

## SCR-04: Weather Intelligence Panel
**Filename:** `04_weather_panel.png`
**Purpose:** Show 7-day forecast with weather alerts
**Expected Display:**
- Location badge: "Akola, Maharashtra"
- Summary text showing average temperature and rainfall
- At least one alert badge (yellow DROUGHT_RISK or red HEAVY_RAIN)
- 7-day forecast table with dates, temperatures, rainfall, humidity
- Sowing window assessment: "Caution" or "Good" badge
**Capture:** Full panel showing both alerts and forecast table

---

## SCR-05: Crop Suitability Ranking
**Filename:** `05_crop_ranking.png`
**Purpose:** Show ranked crops with suitability scores and score bars
**Expected Display:**
- Header: "Top Crops for Kharif Season"
- 🥇 Cotton with score bar and "87/100"
- 🥈 Soybean "79/100"
- 🥉 Pigeonpea "73/100"
- 4th, 5th crops visible
- Duration and Avg Yield metadata on each
- One crop's "Why?" expander open showing justification
**Capture:** Full ranking list showing at least top 5 crops

---

## SCR-06: Farm Operations Plan
**Filename:** `06_operations_plan.png`
**Purpose:** Show week-by-week seasonal calendar
**Expected Display:**
- Header: "Seasonal Operations Plan — Cotton, Kharif 2026"
- Metric boxes: "Cotton", "22 weeks", "8.0 qtl/acre"
- Week 01 — Land Preparation: expanded, showing activities
- Week 02 — Sowing: showing weather note in yellow
- At least 3 weeks visible (expanded or collapsed)
- "Download Plan as Text" button visible
**Capture:** Plan header + first 3 weeks + download button

---

## SCR-07: Agricultural Advisory Chat
**Filename:** `07_advisory_chat.png`
**Purpose:** Show RAG-grounded Q&A interaction
**Expected Display:**
- User message: "What is the best spacing for cotton in black soil?"
- AI response with answer mentioning "90cm x 60cm spacing"
- "Sources cited" expander showing: "ICAR Cotton Guide, relevance 89%"
- Groundedness progress bar visible: "MEDIUM (89%)"
- Disclaimer text visible below response
**Capture:** Full chat area showing question + answer + sources

---

## SCR-08: Agent Trace Panel
**Filename:** `08_agent_trace.png`
**Purpose:** Show multi-agent workflow transparency
**Expected Display:**
- "Agent Workflow Trace (5 steps)" expander header
- Step 1: FarmProfileAgent — save_profile → success
- Step 2: SoilAssessmentAgent — assess_soil → Vertisol, Medium
- Step 3: WeatherIntelligenceAgent — get_forecast → 7 days, 1 alert
- Step 4: CropSuitabilityAgent — rank_crops → Cotton (87/100)
- Step 5: FarmOpsPlanningAgent — generate_plan → 22 week plan
- Duration in milliseconds shown for each step
**Capture:** Expanded trace panel showing all steps

---

## SCR-09: Human-in-the-Loop Review Panel
**Filename:** `09_hitl_review.png`
**Purpose:** Show extension officer review workflow for flagged recommendations
**Expected Display:**
- Red alert box: "Human Review Required"
- Warning message about high-impact content
- Extension Officer Mode toggle ON in sidebar
- "✅ Approve Plan" and "❌ Reject Plan" buttons visible
**Capture:** Plan screen with HITL panel visible (requires extension officer mode)

---

## SCR-10: Error State / Graceful Degradation
**Filename:** `10_error_handling.png`
**Purpose:** Show how the application handles API failures gracefully
**Expected Display:**
- Warning message: "Weather service is temporarily unavailable"
- OR: Input validation error for invalid pH value
- Friendly error message (not raw stack trace)
- Application continuing to function
**Capture:** Error or warning message displayed in context

---

## Screenshot Workflow

```
1. streamlit run app.py
2. Open http://localhost:8501
3. Use test data:
   - Location: Akola, Maharashtra
   - Farm size: 3 acres
   - Soil: Black Cotton
   - Water: Borewell
   - Season: Kharif
   - N=42, P=18, K=65, pH=7.2, OM=1.8%
4. Capture each screen at the specified step
5. Save to assets/screenshots/ with exact filenames
6. Verify all files present before running video_generator.py
```
