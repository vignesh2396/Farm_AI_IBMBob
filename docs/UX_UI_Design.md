# UX/UI Design Document
## FarmAI – Agricultural Decision Intelligence System
**Version:** 1.0 | **Date:** 2026-11-04

---

## 1. User Journey Maps

### Journey 1: First-Time Farmer — Seasonal Crop Planning

```
[Entry] User opens FarmAI URL in browser
   │
   ▼
[Step 1] Landing Page: View problem statement + "Start Planning" CTA
   │
   ▼
[Step 2] Farm Profile Form: Enter location, farm size, soil type, water source
   │  ← Validation error shown inline if fields empty
   ▼
[Step 3] Soil Assessment Panel: Enter N/P/K/pH values
   │  ← Soil Agent runs; spinner with agent step trace shown
   ▼
[Step 4] Soil Result Card: Classified soil type, fertilizer recommendation, confidence bar
   │  ← Explainability panel (expandable)
   ▼
[Step 5] Weather Intelligence Panel: Auto-loads 7-day forecast for entered location
   │  ← Alert badges shown if risk period detected
   ▼
[Step 6] Crop Suitability Panel: Shows ranked crop list with suitability bars
   │  ← User selects preferred crop
   ▼
[Step 7] Farm Operations Plan: Week-by-week seasonal calendar generated
   │  ← Human review flag shown if high-impact items detected
   ▼
[Step 8] Review & Confirm: Extension officer/farmer reviews and confirms
   │  ← Download plan button available
   ▼
[Exit] Plan downloaded; Advisory chat available for follow-up questions
```

### Journey 2: Extension Officer — Review Flagged Recommendation

```
[Entry] Officer receives notification of flagged recommendation
   ▼
[Step 1] Login (demo: no auth in MVP; extension officer mode toggle)
   ▼
[Step 2] Review panel shows flagged recommendation with full explainability trace
   ▼
[Step 3] Officer selects: Approve / Reject / Request More Information
   ▼
[Step 4] Approved plan updated; farmer view refreshes
   ▼
[Exit] Audit log entry created
```

---

## 2. Screen Inventory

| Screen ID | Screen Name | Primary User | Description |
|---|---|---|---|
| SCR-01 | Landing / Home | All | Product intro, feature overview, "Start Planning" CTA |
| SCR-02 | Farm Profile Setup | Farmer | Multi-field form: location, size, soil type, water source |
| SCR-03 | Soil Assessment Input | Farmer | N/P/K/pH input form |
| SCR-04 | Soil Assessment Result | Farmer / Officer | Result card: classification, fertilizer plan, confidence, explainability |
| SCR-05 | Weather Intelligence | Farmer | 7-day forecast table with alerts |
| SCR-06 | Crop Suitability Ranking | Farmer | Ranked crop cards with selection option |
| SCR-07 | Crop Detail / Explainability | Farmer | Detailed reasoning for selected crop |
| SCR-08 | Farm Operations Plan | Farmer | Week-by-week calendar table |
| SCR-09 | Human Review Panel | Extension Officer | Flagged recommendation review + approve/reject |
| SCR-10 | Agricultural Advisory Chat | Farmer | Free-text Q&A with RAG-backed responses |
| SCR-11 | Agent Trace / Debug Panel | All (collapsible) | Displays step-by-step agent workflow trace |
| SCR-12 | About / AI Disclaimer | All | Responsible AI disclaimer + limitations |

---

## 3. Navigation Flow

```
Home (SCR-01)
 ├── Start Planning
 │    ├── Farm Profile (SCR-02)
 │    │    └── Soil Assessment (SCR-03) → Result (SCR-04)
 │    │         └── Weather Panel (SCR-05)
 │    │              └── Crop Ranking (SCR-06) → Crop Detail (SCR-07)
 │    │                   └── Operations Plan (SCR-08)
 │    │                        └── Human Review (SCR-09) [if flagged]
 │    │                             └── Download Plan
 ├── Agricultural Advisory (SCR-10) [always accessible]
 ├── Agent Trace (SCR-11) [collapsible sidebar]
 └── About (SCR-12)
```

---

## 4. Wireframe Descriptions

### SCR-01: Landing Page
```
┌─────────────────────────────────────────────────────────┐
│  🌱 FarmAI                              [About] [Chat]  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  AI-Powered Farm Planning for Smallholder Farmers       │
│  ──────────────────────────────────────────────         │
│  [Icon: Soil] Soil Assessment                           │
│  [Icon: Sun]  Weather Intelligence                      │
│  [Icon: Crop] Crop Suitability                          │
│  [Icon: Cal]  Seasonal Operations Plan                  │
│                                                         │
│         [ 🚀 Start Planning → ]                         │
│                                                         │
│  ⚠️ AI Disclaimer: Recommendations are decision-support │
│  tools. Always consult an extension officer for final   │
│  approval on high-impact decisions.                     │
└─────────────────────────────────────────────────────────┘
```

### SCR-02: Farm Profile Setup
```
┌─────────────────────────────────────────────────────────┐
│  Step 1 of 5: Your Farm Profile                         │
├─────────────────────────────────────────────────────────┤
│  Location (District, State):  [___________________]     │
│  Farm Size (acres):           [___]                     │
│  Primary Soil Type:           [Dropdown: Clay/Loam/..] │
│  Water Source:                [Dropdown: Rain/Canal/..] │
│  Current Season:              [Dropdown: Kharif/Rabi]   │
│  Previous Crop:               [___________________]     │
│                                                         │
│            [ ← Back ]  [ Save & Continue → ]           │
└─────────────────────────────────────────────────────────┘
```

### SCR-04: Soil Assessment Result
```
┌─────────────────────────────────────────────────────────┐
│  Soil Assessment Result                                 │
├─────────────────────────────────────────────────────────┤
│  Soil Classification: Vertisol (Black Cotton Soil) ✅   │
│  Fertility Level:     Medium                            │
│  Confidence:          ████████░░ 82%                    │
│                                                         │
│  Deficiencies: Nitrogen (Low), Zinc (Marginal)          │
│                                                         │
│  Fertilizer Recommendation:                             │
│  ┌──────────────────────────────────┐                  │
│  │ Urea: 60 kg/acre at sowing       │                  │
│  │ DAP:  25 kg/acre at sowing       │                  │
│  │ ZnSO₄: 10 kg/acre basal dose    │                  │
│  └──────────────────────────────────┘                  │
│                                                         │
│  [ ▶ Why this recommendation? (Explainability) ]        │
└─────────────────────────────────────────────────────────┘
```

### SCR-06: Crop Suitability Ranking
```
┌─────────────────────────────────────────────────────────┐
│  Crop Suitability for Your Farm                         │
│  Season: Kharif | Location: Akola, Maharashtra          │
├─────────────────────────────────────────────────────────┤
│  #1  Cotton      [████████████████░░░░] 87/100  [Select]│
│  #2  Soybean     [██████████████░░░░░░] 79/100  [Select]│
│  #3  Pigeonpea   [████████████░░░░░░░░] 73/100  [Select]│
│  #4  Groundnut   [██████████░░░░░░░░░░] 67/100  [Select]│
│  #5  Green Gram  [████████░░░░░░░░░░░░] 58/100  [Select]│
│                                                         │
│  [ ⓘ How are scores calculated? ]                       │
└─────────────────────────────────────────────────────────┘
```

### SCR-08: Farm Operations Plan
```
┌─────────────────────────────────────────────────────────┐
│  Seasonal Operations Plan — Cotton, Kharif 2026         │
├──────────┬──────────────────────────────────────────────┤
│  Week 1  │  Soil preparation: deep ploughing            │
│          │  Apply ZnSO₄ basal dose                      │
├──────────┼──────────────────────────────────────────────┤
│  Week 2  │  Sowing: Cotton (spacing 90×60 cm)           │
│          │  ⚠️ Weather Alert: Delay if rainfall >30mm   │
├──────────┼──────────────────────────────────────────────┤
│  Week 4  │  First irrigation (if no rain)               │
│          │  Apply Urea: 30 kg/acre                      │
├──────────┼──────────────────────────────────────────────┤
│  ...     │  ...                                         │
├──────────┴──────────────────────────────────────────────┤
│  [ 📥 Download Plan ]  [ ✅ Confirm & Review ]          │
└─────────────────────────────────────────────────────────┘
```

---

## 5. UX Recommendations

1. **Progressive Disclosure**: Show complex soil/crop data in expandable panels; don't overwhelm first-time users.
2. **Plain Language**: Use farmer-friendly terminology; avoid jargon; use icons alongside text labels.
3. **Visual Confidence Indicators**: Progress bars for confidence scores; color-coded alerts (green/yellow/red).
4. **Mobile-First Layout**: Single-column layout; large touch targets (min 44×44px); minimal horizontal scrolling.
5. **Offline-Graceful Degradation**: Show cached weather data with timestamp when API is unavailable.
6. **Agent Trace Transparency**: Collapsible "How did the AI decide this?" panel on every result screen.
7. **Persistent AI Disclaimer**: Sticky footer disclaimer on all screens with recommendation outputs.
8. **Download & Share**: Every output panel has a copy/download option for low-connectivity environments.
9. **Error Recovery**: Friendly error messages with suggested next steps; never show raw stack traces to users.

---

## 6. Accessibility Guidelines

| Guideline | Implementation |
|---|---|
| Color Contrast | Background #FFFFFF, Text #1a1a1a; Alert red #C0392B on white |
| Font Size | Minimum 16px body text; 18px for critical alerts |
| Keyboard Navigation | All Streamlit inputs natively keyboard-accessible |
| Screen Reader | All images/icons have alt text; form inputs have labels |
| Focus Indicators | Visible focus ring on all interactive elements |
| Language | Plain English; Grade 8 reading level target |
| Responsive Layout | Tested at 375px (mobile), 768px (tablet), 1280px (desktop) |
| Error Messages | Inline validation errors; descriptive (not "Required field") |
