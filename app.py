"""
app.py
------
FarmAI – Agricultural Decision Intelligence System
Main Streamlit Application

Entry point for the FarmAI web interface.
Run with: streamlit run app.py

Features:
- Farm Profile Setup
- Soil Assessment with LLM Analysis
- Weather Intelligence with 7-day Forecast
- Crop Suitability Ranking
- Seasonal Farm Operations Plan Generation
- RAG-powered Agricultural Advisory Chat
- Human-in-the-Loop Review Panel
- Agent Trace Transparency Panel
"""

import json
import os
import sys
import time as _time
from pathlib import Path

import streamlit as st

# ── Path Setup ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# ── Guardrails & Performance Dashboard ────────────────────────────────────────
from utils.guardrails import (
    run_all_input_guardrails,
    run_all_output_guardrails,
    record_token_usage,
)
from utils.performance_dashboard import render_performance_dashboard

# ── App Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FarmAI – Agricultural Decision Intelligence",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "FarmAI v1.0.0 — AI-Powered Farm Planning System | IBM Bob Capstone Project",
    },
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Global */
.main { background-color: #f8fdf4; }
section[data-testid="stSidebar"] { background-color: #1a3c2e; }
section[data-testid="stSidebar"] * { color: #e8f5e9 !important; }

/* Metric cards */
.metric-card {
    background: white;
    padding: 16px;
    border-radius: 10px;
    border-left: 4px solid #2e7d32;
    margin-bottom: 12px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
}

/* Score bar */
.score-bar-container { background: #e0e0e0; border-radius: 10px; height: 14px; }
.score-bar-fill { background: #2e7d32; height: 14px; border-radius: 10px; }

/* Alert badges */
.alert-high   { background: #ffebee; border-left: 4px solid #c62828; padding: 10px; border-radius: 6px; }
.alert-medium { background: #fff8e1; border-left: 4px solid #f9a825; padding: 10px; border-radius: 6px; }
.alert-low    { background: #e8f5e9; border-left: 4px solid #2e7d32; padding: 10px; border-radius: 6px; }

/* Section headers */
.section-header {
    font-size: 20px;
    font-weight: 700;
    color: #1b5e20;
    margin-bottom: 8px;
    padding-bottom: 4px;
    border-bottom: 2px solid #a5d6a7;
}

/* Disclaimer */
.disclaimer-box {
    background: #fff3e0;
    border: 1px solid #ffe0b2;
    border-radius: 8px;
    padding: 12px;
    font-size: 13px;
    color: #4e342e;
    margin-top: 20px;
}

/* Agent trace */
.trace-step {
    background: #f3f4f6;
    border-left: 3px solid #1565c0;
    padding: 8px 12px;
    margin: 4px 0;
    border-radius: 4px;
    font-family: monospace;
    font-size: 12px;
    color: #0d1b2a;
}
.trace-step strong {
    color: #1565c0;
}
</style>
""", unsafe_allow_html=True)


# ── Session State Init ────────────────────────────────────────────────────────
def _init_session():
    """Initialize Streamlit session state with defaults."""
    defaults = {
        "session_id": None,
        "farm_profile": {},
        "soil_result": {},
        "weather_data": {},
        "crop_ranking": [],
        "selected_crop": "",
        "farm_plan": {},
        "advisory_history": [],
        "agent_trace": [],
        "supervisor": None,
        "step": 1,  # Workflow step: 1=Profile, 2=Soil, 3=Weather, 4=Crops, 5=Plan, 6=Advisory
        "is_extension_officer": False,
        "config_valid": False,
        "rag_ready": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # Generate session_id if not set
    if not st.session_state["session_id"]:
        from utils.helpers import generate_session_id
        st.session_state["session_id"] = generate_session_id()


def _init_db_and_rag():
    """Initialize database and RAG pipeline (only once per session)."""
    if st.session_state.get("db_initialized"):
        return
    try:
        from utils.db import init_db
        init_db()
        st.session_state["db_initialized"] = True
    except Exception as e:
        st.warning(f"Database initialization warning: {e}")

    # Check RAG readiness
    try:
        from pathlib import Path
        from utils.config import config
        chroma_path = Path(config.CHROMA_PERSIST_DIR)
        if not chroma_path.exists() or not list(chroma_path.rglob("*.bin")):
            from rag.embeddings import build_vector_store
            with st.spinner("🔨 Building knowledge base (first run)..."):
                build_vector_store()
        st.session_state["rag_ready"] = True
    except Exception as e:
        st.session_state["rag_ready"] = False


def _get_supervisor():
    """Get or create the supervisor agent."""
    if st.session_state["supervisor"] is None:
        from agents.supervisor_agent import SupervisorAgent
        st.session_state["supervisor"] = SupervisorAgent(st.session_state["session_id"])
    return st.session_state["supervisor"]


# ── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar():
    """Render the navigation sidebar."""
    with st.sidebar:
        st.markdown("## 🌱 FarmAI")
        st.markdown("*Agricultural Decision Intelligence*")
        st.markdown("---")

        # Config status
        from utils.config import config
        missing = config.validate()
        if missing:
            st.error(f"⚠️ Missing config: {', '.join(missing)}")
            st.info("Add your GOOGLE_API_KEY to the .env file")
        else:
            st.success("✅ Configuration OK")

        st.markdown("---")

        # Navigation
        st.markdown("### 📋 Workflow Steps")
        steps = [
            ("1", "Farm Profile"),
            ("2", "Soil Assessment"),
            ("3", "Weather Intelligence"),
            ("4", "Crop Suitability"),
            ("5", "Farm Operations Plan"),
            ("6", "Agricultural Advisory"),
            ("7", "📊 Performance Dashboard"),
        ]
        current_step = st.session_state.get("step", 1)
        for num, name in steps:
            icon = "✅" if int(num) < current_step else ("🔵" if int(num) == current_step else "⬜")
            if st.button(f"{icon} {num}. {name}", key=f"nav_{num}", use_container_width=True):
                st.session_state["step"] = int(num)
                st.rerun()

        st.markdown("---")

        # Extension Officer Mode
        st.markdown("### 👨‍🌾 Role")
        is_officer = st.toggle(
            "Extension Officer Mode",
            value=st.session_state.get("is_extension_officer", False),
            key="officer_toggle",
        )
        st.session_state["is_extension_officer"] = is_officer
        if is_officer:
            st.info("🔍 Officer mode: You can review and approve recommendations.")

        st.markdown("---")

        # Clear data
        if st.button("🗑️ Clear My Data", use_container_width=True):
            _clear_session()
            st.success("Session data cleared.")
            st.rerun()

        st.markdown("---")
        st.caption(f"Session: `{st.session_state['session_id'][:8]}...`")
        st.caption("FarmAI v1.0.0 | IBM Bob Capstone")


def _clear_session():
    """Clear farm data from session and database."""
    session_id = st.session_state.get("session_id")
    if session_id:
        try:
            from agents.farm_profile_agent import delete_farm_profile
            delete_farm_profile(session_id)
        except Exception:
            pass
    keys_to_clear = [
        "farm_profile", "soil_result", "weather_data", "crop_ranking",
        "selected_crop", "farm_plan", "advisory_history", "agent_trace",
        "supervisor", "step",
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


# ── Page 1: Farm Profile ───────────────────────────────────────────────────────
def page_farm_profile():
    st.markdown('<div class="section-header">🏡 Step 1: Your Farm Profile</div>', unsafe_allow_html=True)
    st.markdown("Tell us about your farm. This information guides all AI recommendations.")

    col1, col2 = st.columns(2)
    existing = st.session_state.get("farm_profile", {})

    with col1:
        district = st.text_input("District *", value=existing.get("district", ""), placeholder="e.g., Akola")
        state = st.text_input("State *", value=existing.get("state", ""), placeholder="e.g., Maharashtra")
        farm_size = st.number_input(
            "Farm Size (acres) *", min_value=0.1, max_value=10000.0,
            value=float(existing.get("farm_size", 1.0)), step=0.5,
        )
        prev_crop = st.text_input("Previous Crop", value=existing.get("prev_crop", ""), placeholder="e.g., Soybean")

    with col2:
        soil_type = st.selectbox(
            "Soil Type *",
            options=["Black Cotton", "Vertisol", "Red Laterite", "Alfisol",
                     "Sandy", "Entisol", "Loam", "Inceptisol", "Alluvial Loam", "Clay", "Silt"],
            index=0 if not existing.get("soil_type") else
                  ["Black Cotton", "Vertisol", "Red Laterite", "Alfisol",
                   "Sandy", "Entisol", "Loam", "Inceptisol", "Alluvial Loam", "Clay", "Silt"].index(
                      existing.get("soil_type", "Black Cotton")
                  ) if existing.get("soil_type") in ["Black Cotton", "Vertisol", "Red Laterite", "Alfisol",
                   "Sandy", "Entisol", "Loam", "Inceptisol", "Alluvial Loam", "Clay", "Silt"] else 0,
        )
        water_source = st.selectbox(
            "Water Source *",
            options=["Rainfall", "Canal", "Borewell", "Tank", "River"],
            index=["Rainfall", "Canal", "Borewell", "Tank", "River"].index(
                existing.get("water_source", "Rainfall")
            ) if existing.get("water_source") in ["Rainfall", "Canal", "Borewell", "Tank", "River"] else 0,
        )
        current_season = st.selectbox(
            "Current Season *",
            options=["Kharif", "Rabi", "Zaid"],
            index=["Kharif", "Rabi", "Zaid"].index(
                existing.get("current_season", "Kharif")
            ) if existing.get("current_season") in ["Kharif", "Rabi", "Zaid"] else 0,
        )

    if st.button("💾 Save Farm Profile & Continue →", type="primary", use_container_width=True):
        if not district.strip() or not state.strip():
            st.error("Please fill in District and State fields.")
        else:
            from agents.farm_profile_agent import save_farm_profile
            with st.spinner("Saving farm profile..."):
                result = save_farm_profile(
                    session_id=st.session_state["session_id"],
                    district=district.strip(),
                    state=state.strip(),
                    farm_size=farm_size,
                    soil_type=soil_type,
                    water_source=water_source,
                    current_season=current_season,
                    prev_crop=prev_crop.strip(),
                )

            if result.get("status") == "success":
                st.session_state["farm_profile"] = {
                    "profile_id": result.get("profile_id"),
                    "district": district.strip(),
                    "state": state.strip(),
                    "farm_size": farm_size,
                    "soil_type": soil_type,
                    "water_source": water_source,
                    "current_season": current_season,
                    "prev_crop": prev_crop.strip(),
                }
                st.success(f"✅ Farm profile saved! Profile ID: {result.get('profile_id')}")
                st.session_state["step"] = 2
                # Reset supervisor to use new profile
                st.session_state["supervisor"] = None
                st.rerun()
            else:
                for err in result.get("errors", ["Save failed"]):
                    st.error(err)


# ── Page 2: Soil Assessment ───────────────────────────────────────────────────
def page_soil_assessment():
    st.markdown('<div class="section-header">🧪 Step 2: Soil Assessment</div>', unsafe_allow_html=True)

    profile = st.session_state.get("farm_profile", {})
    if not profile:
        st.warning("⚠️ Please complete your Farm Profile first (Step 1).")
        return

    st.info(f"Farm: {profile.get('district')}, {profile.get('state')} | {profile.get('soil_type')} | {profile.get('farm_size')} acres")

    col1, col2 = st.columns(2)
    with col1:
        nitrogen = st.slider("Nitrogen (kg/ha)", 0.0, 100.0, 42.0, 0.5)
        phosphorus = st.slider("Phosphorus (kg/ha)", 0.0, 100.0, 18.0, 0.5)
        potassium = st.slider("Potassium (kg/ha)", 0.0, 100.0, 65.0, 0.5)
    with col2:
        ph_level = st.slider("pH Level", 0.0, 14.0, 7.2, 0.1)
        organic_matter = st.slider("Organic Matter (%)", 0.0, 10.0, 1.8, 0.1)
        moisture_level = st.selectbox("Moisture Level", ["Dry", "Moderate", "Wet"], index=1)

    if st.button("🔬 Run Soil Assessment", type="primary", use_container_width=True):
        soil_data = {
            "nitrogen": nitrogen, "phosphorus": phosphorus, "potassium": potassium,
            "ph_level": ph_level, "organic_matter": organic_matter, "moisture_level": moisture_level,
        }

        supervisor = _get_supervisor()
        supervisor.state.farm_profile = profile

        with st.spinner("🌱 Soil Assessment Agent analyzing your soil..."):
            result = supervisor.run_soil_assessment(soil_data)

        st.session_state["soil_result"] = result
        st.session_state["agent_trace"] = supervisor.get_trace()

        if result.get("status") == "error":
            for err in result.get("errors", []):
                st.error(err)
        else:
            _render_soil_result(result)
            st.session_state["step"] = 3
            if st.button("Continue to Weather Intelligence →"):
                st.rerun()

    elif st.session_state.get("soil_result"):
        _render_soil_result(st.session_state["soil_result"])


def _render_soil_result(result: dict):
    """Render the soil assessment result card."""
    st.markdown("---")
    st.markdown("### 📊 Soil Assessment Results")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Soil Classification", result.get("soil_class", "N/A"))
    with col2:
        st.metric("Fertility Level", result.get("fertility_level", "N/A"))
    with col3:
        conf = result.get("confidence", 0)
        st.metric("Confidence", f"{conf:.0%}")
        st.progress(conf)

    # pH Status
    ph_status = result.get("ph_status", "")
    if "Acidic" in ph_status or "Alkaline" in ph_status:
        st.warning(f"⚠️ pH Status: {ph_status}")
    else:
        st.success(f"✅ pH Status: {ph_status}")

    # Deficiencies
    deficiencies = result.get("deficiencies", [])
    if deficiencies:
        st.error("🔴 Nutrient Deficiencies: " + " | ".join(deficiencies))

    # Fertilizer Plan
    fert_plan = result.get("fertilizer_plan", [])
    if fert_plan:
        st.markdown("#### 🌿 Fertilizer Recommendation")
        fert_data = [
            {"Input": r.get("input_name"), "Qty (kg/acre)": r.get("quantity_kg_per_acre"), "Timing": r.get("timing")}
            for r in fert_plan
        ]
        st.table(fert_data)

    # LLM Narrative
    narrative = result.get("narrative_explanation", "")
    if narrative:
        with st.expander("💡 AI Explanation (Plain Language)", expanded=True):
            st.write(narrative)

    # Explainability
    explainability = result.get("explainability", {})
    if explainability:
        with st.expander("🔍 Why this recommendation? (Explainability)"):
            st.write("**Data Inputs:**")
            st.json(explainability.get("data_inputs", {}))
            st.write("**Rules Applied:**")
            for rule in explainability.get("rules_applied", []):
                st.write(f"  • {rule}")
            st.write("**Sources:**")
            for source in explainability.get("sources", []):
                st.write(f"  📚 {source}")

    # Warnings
    for warning in result.get("warnings", []):
        st.warning(f"⚠️ {warning}")


# ── Page 3: Weather Intelligence ─────────────────────────────────────────────
def page_weather_intelligence():
    st.markdown('<div class="section-header">🌤️ Step 3: Weather Intelligence</div>', unsafe_allow_html=True)

    profile = st.session_state.get("farm_profile", {})
    if not profile:
        st.warning("⚠️ Please complete your Farm Profile first.")
        return

    location = f"{profile.get('district', '')}, {profile.get('state', '')}"
    st.info(f"Fetching weather for: **{location}**")

    col1, col2 = st.columns([3, 1])
    with col1:
        location_override = st.text_input("Override location (optional):", value=location)
    with col2:
        fetch_btn = st.button("🌍 Fetch Weather", type="primary", use_container_width=True)

    if fetch_btn or st.session_state.get("weather_data"):
        if fetch_btn:
            supervisor = _get_supervisor()
            supervisor.state.farm_profile = profile
            with st.spinner("🌦️ Weather Intelligence Agent fetching forecast..."):
                result = supervisor.run_weather_intelligence(location_override or location)
            st.session_state["weather_data"] = result
            st.session_state["agent_trace"] = supervisor.get_trace()
        else:
            result = st.session_state["weather_data"]

        _render_weather_result(result)
        if st.session_state.get("weather_data"):
            if st.button("Continue to Crop Suitability →", type="primary"):
                st.session_state["step"] = 4
                st.rerun()


def _render_weather_result(result: dict):
    """Render the weather forecast panel."""
    st.markdown("---")
    if result.get("cached"):
        st.caption(f"⏱️ Showing cached data from {result.get('timestamp', 'earlier')}")

    # Summary
    summary = result.get("summary", "")
    if summary:
        st.info(f"🌍 {summary}")

    # Sowing Window
    sowing = result.get("sowing_window", {})
    sowing_status = sowing.get("status", "Unknown")
    if sowing_status == "Good":
        st.success(f"🌱 Sowing Window: **{sowing_status}** — {sowing.get('reason', '')}")
    elif sowing_status == "Caution":
        st.warning(f"⚠️ Sowing Window: **{sowing_status}** — {sowing.get('reason', '')}")
    elif sowing_status == "Delay":
        st.error(f"🚫 Sowing Window: **{sowing_status}** — {sowing.get('reason', '')}")

    # Alerts
    alerts = result.get("alerts", [])
    if alerts:
        st.markdown("#### ⚠️ Weather Alerts")
        for alert in alerts:
            severity = alert.get("severity", "LOW")
            css_class = {"HIGH": "alert-high", "MEDIUM": "alert-medium"}.get(severity, "alert-low")
            st.markdown(
                f'<div class="{css_class}"><strong>{alert.get("type", "ALERT")}</strong> '
                f'({severity}): {alert.get("message", "")}</div>',
                unsafe_allow_html=True,
            )
    else:
        st.success("✅ No significant weather alerts this week.")

    # 7-Day Forecast Table
    forecast = result.get("forecast", [])
    if forecast:
        st.markdown("#### 📅 7-Day Forecast")
        table_data = []
        for day in forecast:
            table_data.append({
                "Date": day.get("date", ""),
                "Max °C": f"{day.get('max_temp_c', '—'):.1f}" if day.get("max_temp_c") else "—",
                "Min °C": f"{day.get('min_temp_c', '—'):.1f}" if day.get("min_temp_c") else "—",
                "Rain (mm)": f"{day.get('rainfall_mm', 0):.1f}",
                "Humidity %": f"{day.get('humidity_pct', '—')}",
                "Wind km/h": f"{day.get('wind_kmh', '—')}",
            })
        st.table(table_data)


# ── Page 4: Crop Suitability ──────────────────────────────────────────────────
def page_crop_suitability():
    st.markdown('<div class="section-header">🌾 Step 4: Crop Suitability Ranking</div>', unsafe_allow_html=True)

    profile = st.session_state.get("farm_profile", {})
    if not profile:
        st.warning("⚠️ Please complete your Farm Profile first.")
        return

    col1, col2 = st.columns([2, 1])
    with col1:
        st.info(
            f"Farm: **{profile.get('district')}, {profile.get('state')}** | "
            f"Soil: {profile.get('soil_type')} | "
            f"Season: {profile.get('current_season')} | "
            f"Water: {profile.get('water_source')}"
        )
    with col2:
        rank_btn = st.button("🌱 Rank Crops", type="primary", use_container_width=True)

    if rank_btn or st.session_state.get("crop_ranking"):
        if rank_btn:
            supervisor = _get_supervisor()
            supervisor.state.farm_profile = profile
            supervisor.state.soil_result = st.session_state.get("soil_result", {})
            supervisor.state.weather_data = st.session_state.get("weather_data", {})

            with st.spinner("🌾 Crop Suitability Agent evaluating crops..."):
                ranked = supervisor.run_crop_suitability()
            st.session_state["crop_ranking"] = ranked
            st.session_state["agent_trace"] = supervisor.get_trace()
        else:
            ranked = st.session_state["crop_ranking"]

        if ranked:
            st.markdown(f"### Top Crops for {profile.get('current_season')} Season")
            for crop in ranked[:5]:
                with st.container():
                    col_a, col_b, col_c = st.columns([3, 2, 1])
                    with col_a:
                        medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][min(crop["rank"] - 1, 4)]
                        st.markdown(f"{medal} **{crop['crop_name']}**")
                        score = crop["suitability_score"]
                        bar_filled = int(score / 5)  # out of 20 chars
                        bar = "█" * bar_filled + "░" * (20 - bar_filled)
                        st.markdown(f"`{bar}` **{score}/100**")
                    with col_b:
                        st.caption(f"Duration: {crop.get('duration_days', '—')} days")
                        st.caption(f"Avg Yield: {crop.get('avg_yield_qtl', '—')} qtl/acre")
                        st.caption(f"Market Demand: {crop.get('market_demand', '—')}")
                    with col_c:
                        if st.button(f"Select", key=f"select_{crop['crop_name']}"):
                            st.session_state["selected_crop"] = crop["crop_name"]
                            st.session_state["step"] = 5
                            st.rerun()

                # Justification and weather notes
                with st.expander(f"ℹ️ Why {crop['crop_name']}?"):
                    st.write(crop.get("justification", ""))
                    for note in crop.get("weather_notes", []):
                        st.warning(note)
                    rag = crop.get("rag_knowledge")
                    if rag:
                        st.markdown(f"**📚 From {rag['source']}** (relevance: {rag['relevance_score']:.0%}):")
                        st.write(rag["excerpt"])
                st.divider()


# ── Page 5: Farm Operations Plan ──────────────────────────────────────────────
def page_farm_plan():
    st.markdown('<div class="section-header">📅 Step 5: Seasonal Farm Operations Plan</div>', unsafe_allow_html=True)

    profile = st.session_state.get("farm_profile", {})
    if not profile:
        st.warning("⚠️ Please complete your Farm Profile first.")
        return

    selected_crop = st.session_state.get("selected_crop", "")

    # Crop selection override
    if not selected_crop:
        ranked = st.session_state.get("crop_ranking", [])
        crop_names = [c["crop_name"] for c in ranked] if ranked else ["Cotton", "Soybean", "Wheat"]
        selected_crop = st.selectbox("Select Crop:", options=crop_names)

    st.info(f"Generating plan for: **{selected_crop}** | Season: {profile.get('current_season')}")

    if st.button("📋 Generate Seasonal Plan", type="primary", use_container_width=True):
        supervisor = _get_supervisor()
        supervisor.state.farm_profile = profile
        supervisor.state.soil_result = st.session_state.get("soil_result", {})
        supervisor.state.weather_data = st.session_state.get("weather_data", {})

        with st.spinner(f"🌾 Farm Operations Planning Agent generating {selected_crop} plan..."):
            plan = supervisor.run_farm_plan(selected_crop)
        st.session_state["farm_plan"] = plan
        st.session_state["agent_trace"] = supervisor.get_trace()

    plan = st.session_state.get("farm_plan", {})
    if plan:
        _render_farm_plan(plan, selected_crop, profile)


def _render_farm_plan(plan: dict, crop: str, profile: dict):
    """Render the farm operations plan."""
    st.markdown("---")

    # High-impact flag
    if plan.get("high_impact_flag"):
        st.error(
            "🔴 **Human Review Required**: This plan contains recommendations that need extension officer approval.\n\n"
            + "\n".join(plan.get("high_impact_warnings", []))
        )
        is_officer = st.session_state.get("is_extension_officer", False)
        if is_officer:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve Plan", type="primary"):
                    st.session_state["farm_plan"]["status"] = "approved"
                    from utils.db import log_audit
                    log_audit(st.session_state["session_id"], "PLAN_APPROVED",
                              "Extension Officer", "approve()", "Officer approved flagged plan")
                    st.success("Plan approved by extension officer.")
                    st.rerun()
            with col2:
                if st.button("❌ Reject Plan"):
                    st.session_state["farm_plan"]["status"] = "rejected"
                    st.error("Plan rejected. Please adjust crop selection or input data.")
                    st.rerun()
        else:
            st.info("👨‍🌾 Enable **Extension Officer Mode** in the sidebar to review and approve this plan.")
        return

    # Plan header
    status = plan.get("status", "draft")
    status_emoji = {"draft": "📝", "approved": "✅", "rejected": "❌"}.get(status, "📝")
    st.markdown(f"**{status_emoji} Plan Status:** {status.upper()}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Crop", plan.get("crop", crop))
    with col2:
        st.metric("Total Weeks", plan.get("total_weeks", len(plan.get("weeks", []))))
    with col3:
        expected_yield = plan.get("expected_yield_qtl_per_acre", 0)
        st.metric("Expected Yield", f"{expected_yield} qtl/acre" if expected_yield else "See notes")

    # Weekly plan table
    weeks = plan.get("weeks", [])
    if weeks:
        st.markdown(f"#### 📆 Week-by-Week Operations Plan — {crop}")
        for week_data in weeks:
            phase = week_data.get("phase", "")
            week_num = week_data.get("week", 0)
            activities = week_data.get("activities", [])
            irrigation = week_data.get("irrigation", "")
            weather_note = week_data.get("weather_note")
            inputs_list = week_data.get("inputs", [])

            with st.expander(f"Week {week_num:02d} — {phase}", expanded=(week_num <= 2)):
                for act in activities:
                    st.write(f"• {act}")
                if irrigation:
                    st.caption(f"💧 Irrigation: {irrigation}")
                if inputs_list:
                    st.caption(f"🌿 Inputs: {', '.join(inputs_list)}")
                if weather_note:
                    st.warning(f"🌦️ Weather Note: {weather_note}")

    # Key risks
    key_risks = plan.get("key_risks", [])
    if key_risks:
        with st.expander("⚠️ Key Risks to Monitor"):
            for risk in key_risks:
                st.write(f"• {risk}")

    # Download plan
    plan_text = _plan_to_text(plan, crop, profile)
    st.download_button(
        label="📥 Download Plan as Text",
        data=plan_text,
        file_name=f"farmai_plan_{crop.lower().replace(' ', '_')}.txt",
        mime="text/plain",
    )

    # Explainability
    explainability = plan.get("explainability", {})
    if explainability:
        with st.expander("🔍 How was this plan generated?"):
            st.write("**Data Sources Used:**")
            for src in explainability.get("data_sources_used", []):
                st.write(f"  • {src}")
            if explainability.get("weather_adaptation"):
                st.success("✅ Plan adapted for current weather conditions")
            if explainability.get("fertilizer_integrated"):
                st.success("✅ Soil fertilizer recommendations integrated into plan")


def _plan_to_text(plan: dict, crop: str, profile: dict) -> str:
    """Convert plan dict to downloadable plain text."""
    lines = [
        f"FARMAI SEASONAL OPERATIONS PLAN",
        f"================================",
        f"Crop: {crop}",
        f"Farm: {profile.get('district')}, {profile.get('state')}",
        f"Season: {profile.get('current_season')}",
        f"Generated by: FarmAI v1.0.0",
        f"",
    ]
    for week_data in plan.get("weeks", []):
        lines.append(f"WEEK {week_data.get('week', 0):02d} — {week_data.get('phase', '')}")
        for act in week_data.get("activities", []):
            lines.append(f"  • {act}")
        if week_data.get("irrigation"):
            lines.append(f"  💧 {week_data['irrigation']}")
        if week_data.get("weather_note"):
            lines.append(f"  ⚠️  WEATHER: {week_data['weather_note']}")
        lines.append("")
    lines.append("DISCLAIMER: AI-generated plan. Verify with your extension officer.")
    return "\n".join(lines)


# ── Page 6: Agricultural Advisory ────────────────────────────────────────────
def page_advisory():
    st.markdown('<div class="section-header">💬 Step 6: Agricultural Advisory</div>', unsafe_allow_html=True)
    st.markdown("Ask any farming question. The AI will retrieve answers from agricultural knowledge bases.")

    profile = st.session_state.get("farm_profile", {})

    # Chat history
    for msg in st.session_state.get("advisory_history", []):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("sources"):
                with st.expander("📚 Sources cited"):
                    for src in msg["sources"]:
                        st.caption(
                            f"📄 {src.get('document', 'Unknown')} | "
                            f"Relevance: {src.get('relevance_score', 0):.0%}"
                        )
            if msg.get("groundedness") is not None:
                g = msg["groundedness"]
                label = "HIGH" if g >= 0.75 else "MEDIUM" if g >= 0.5 else "LOW"
                st.progress(g, text=f"Groundedness: {label} ({g:.0%})")

    # Input
    query = st.chat_input("Ask a farming question, e.g., 'What is the best spacing for cotton?'")
    if query:
        # ── Input Guardrails ────────────────────────────────────────────
        guard = run_all_input_guardrails(query, session_id=st.session_state.get("session_id", ""))
        if guard.blocked:
            st.session_state["advisory_history"].append({"role": "user", "content": query})
            st.session_state["advisory_history"].append({
                "role": "assistant",
                "content": (
                    "⚠️ **Your message was blocked by safety guardrails**: "
                    f"`{', '.join(guard.violations)}`\n\n"
                    "Please rephrase your question."
                ),
            })
            st.rerun()
            return

        safe_query = guard.sanitized_text or query
        st.session_state["advisory_history"].append({"role": "user", "content": query})

        supervisor = _get_supervisor()
        supervisor.state.farm_profile = profile

        _start = _time.time()
        with st.spinner("🔍 Searching knowledge base..."):
            result = supervisor.run_advisory(safe_query)
        _latency = (_time.time() - _start) * 1000

        answer = result.get("answer", "")
        sources = result.get("sources", [])
        groundedness = result.get("groundedness_score", 0.0)
        high_impact = result.get("high_impact", False)

        # ── Output Guardrails ───────────────────────────────────────────
        out_guard = run_all_output_guardrails(answer)
        if out_guard.blocked:
            answer = "⚠️ The AI response was filtered for safety. Please consult a certified agricultural advisor."
        else:
            answer = out_guard.sanitized_text or answer

        # High-impact advisory flag
        if high_impact:
            answer += "\n\n⚠️ **This advice may require expert review before implementation.**"

        # Record metrics
        record_token_usage(len(safe_query.split()) * 2, len(answer.split()) * 2, cost_usd=0.0002)
        if "session_metrics" not in st.session_state:
            st.session_state["session_metrics"] = {}
        st.session_state["session_metrics"]["avg_latency_ms"] = _latency

        st.session_state["advisory_history"].append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "groundedness": groundedness,
        })

        disclaimer = result.get("disclaimer", "")
        if disclaimer:
            st.session_state["advisory_history"].append({
                "role": "assistant",
                "content": f"*ℹ️ {disclaimer}*",
            })

        st.session_state["agent_trace"] = supervisor.get_trace()
        st.rerun()


# ── Agent Trace Panel ─────────────────────────────────────────────────────────
def render_agent_trace():
    """Render the agent workflow trace in an expander."""
    trace = st.session_state.get("agent_trace", [])
    if not trace:
        return

    with st.expander(f"🤖 Agent Workflow Trace ({len(trace)} steps)", expanded=False):
        for step in trace:
            st.markdown(
                f'<div class="trace-step">'
                f'[{step["step"]}] <strong>{step["agent"]}</strong> | '
                f'{step["action"]} → {step["result"][:120]} '
                f'({step["duration_ms"]}ms)'
                f'{"  ❌ " + step["error"] if step.get("error") else ""}'
                f"</div>",
                unsafe_allow_html=True,
            )


# ── Disclaimer Footer ─────────────────────────────────────────────────────────
def render_disclaimer():
    st.markdown(
        '<div class="disclaimer-box">'
        "⚠️ <strong>AI Disclaimer:</strong> FarmAI provides AI-generated recommendations "
        "for informational and planning purposes only. "
        "Do not implement high-impact changes without consulting a qualified agricultural "
        "extension officer or Krishi Vigyan Kendra. AI outputs may contain errors. "
        "All recommendations should be verified against local conditions before implementation."
        "</div>",
        unsafe_allow_html=True,
    )


# ── Main App ──────────────────────────────────────────────────────────────────
def main():
    _init_session()
    _init_db_and_rag()

    # Header
    st.markdown(
        "# 🌱 FarmAI\n"
        "### Agricultural Decision Intelligence System\n"
        "*Powered by Agentic AI | IBM Bob Capstone Project*"
    )
    st.divider()

    render_sidebar()

    # Check configuration
    from utils.config import config
    missing = config.validate()
    if missing:
        st.warning(
            f"⚠️ **Setup Required**: Add your `GOOGLE_API_KEY` to the `.env` file. "
            f"Missing: {', '.join(missing)}. "
            f"The app will run with limited functionality (rule-based only, no LLM)."
        )

    # Render current step
    step = st.session_state.get("step", 1)
    pages = {
        1: page_farm_profile,
        2: page_soil_assessment,
        3: page_weather_intelligence,
        4: page_crop_suitability,
        5: page_farm_plan,
        6: page_advisory,
        7: _render_performance_page,
    }
    pages.get(step, page_farm_profile)()

    # Agent trace panel
    if step != 7:
        render_agent_trace()

    # Disclaimer
    render_disclaimer()


def _render_performance_page():
    """Render the LLM & Agent Performance Dashboard page."""
    render_performance_dashboard(st.session_state.get("session_metrics", {}))


if __name__ == "__main__":
    main()
