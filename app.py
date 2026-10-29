"""CyberPulse - Early-Warning Cyber Incident Linker.

Primary SOC Dashboard providing real-time multi-stage attack visualization,
plain-English threat intelligence, automated response mitigations, and forensic timeline tracking.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Import core modules with fallbacks
from core.mock_data import (
    COLOR_ATTACK_ACCENT,
    COLOR_ATTACK_BG,
    COLOR_SUSPICIOUS_ACCENT,
    COLOR_SUSPICIOUS_BG,
    COLOR_WATCH_ACCENT,
    COLOR_WATCH_BG,
    SCENARIO_ATTACK,
    SCENARIO_NORMAL,
    SCENARIOS,
    SEVERITY_COLOR_MAP,
    SEVERITY_LEVEL_MAP,
    get_scenario_data,
)
from core.response import get_response_states, trigger_action, reset_response_states

# Optional detection backend integration if present
try:
    import core.detection as detection
    HAS_DETECTION_BACKEND = True
except ImportError:
    detection = None  # type: ignore
    HAS_DETECTION_BACKEND = False

# Configure Streamlit page layout
st.set_page_config(
    page_title="CyberPulse | SOC Incident Linker",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-Contrast Dark Styling (Slate Blue, Sage Green, Amber, Crimson)
st.markdown(
    """
    <style>
    /* Main Dark Theme Container */
    .stApp {
        background-color: #0B0F19;
        color: #F1F5F9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Global Card Base */
    .cyber-card {
        background-color: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -2px rgba(0, 0, 0, 0.3);
    }
    
    /* Header Branding */
    .cyber-header-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #38BDF8 0%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.15rem;
    }
    .cyber-header-subtitle {
        color: #94A3B8;
        font-size: 0.95rem;
        font-weight: 400;
        margin-bottom: 1.2rem;
    }

    /* Danger Meter Custom Box */
    .danger-container {
        border-radius: 10px;
        padding: 1.2rem;
        border-width: 1px;
        border-style: solid;
        transition: all 0.3s ease-in-out;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .danger-score-text {
        font-size: 2.8rem;
        font-weight: 900;
        line-height: 1;
        margin: 0.4rem 0;
    }
    .danger-badge-pill {
        display: inline-block;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        width: fit-content;
    }

    /* Stage Tracker Box */
    .stage-container {
        background-color: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 1.2rem;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    /* Response Panel Box */
    .response-container {
        background-color: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 1.2rem;
        height: 100%;
    }

    /* Story Box */
    .story-card {
        background-color: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 1.4rem;
        height: 480px;
        overflow-y: auto;
    }

    /* Live Log Feed Container */
    .log-terminal {
        background-color: #070B12;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 1.2rem;
        height: 480px;
        overflow-y: auto;
        font-family: "JetBrains Mono", "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
        font-size: 0.83rem;
        line-height: 1.6;
    }
    .log-entry {
        padding: 0.55rem 0.8rem;
        margin-bottom: 0.5rem;
        border-radius: 4px;
        word-break: break-all;
    }
    .log-info {
        background-color: #0F172A;
        border-left: 4px solid #64748B;
        color: #94A3B8;
    }
    .log-suspicious {
        background-color: #2D2318;
        border-left: 4px solid #D97706;
        color: #FDE68A;
    }
    .log-critical {
        background-color: #381A1A;
        border-left: 4px solid #DC2626;
        color: #FCA5A5;
    }

    /* Metric pill */
    .cyber-chip {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        background: #1E293B;
        border-radius: 4px;
        color: #38BDF8;
        font-weight: 600;
        font-size: 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _init_session() -> None:
    """Initialize app state keys safely."""
    if "scenario" not in st.session_state:
        st.session_state["scenario"] = SCENARIO_ATTACK
    if "step_index" not in st.session_state:
        st.session_state["step_index"] = 3  # Start at Stage 3 for rich initial impression
    if "is_playing" not in st.session_state:
        st.session_state["is_playing"] = False
    if "playback_speed" not in st.session_state:
        st.session_state["playback_speed"] = "1x"


_init_session()


# Sidebar Navigation & System Telemetry
with st.sidebar:
    st.markdown("### 🛡️ **CyberPulse SOC**")
    st.markdown(
        "<div style='font-size: 0.85rem; color: #94A3B8; margin-bottom: 1rem;'>"
        "Autonomous early-warning detection and rapid containment suite for small business workloads."
        "</div>",
        unsafe_allow_html=True,
    )
    
    st.markdown("---")
    st.markdown("#### 📡 **Engine Status**")
    st.markdown(
        f"""
        - **Detection Engine:** <span class='cyber-chip'>{'Active Backend' if HAS_DETECTION_BACKEND else 'Embedded Mock Engine'}</span>
        - **Correlation Engine:** <span class='cyber-chip'>Graph Linker v2.4</span>
        - **Monitored Workspaces:** <span class='cyber-chip'>M365 / Entra ID / AWS</span>
        - **Active Analyst:** <span style='color: #38BDF8;'>Keerthana (Lead IR)</span>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("---")
    st.markdown("#### ⚡ **Quick Navigation**")
    st.page_link("app.py", label="Incident Overview (SOC)", icon="🚨")
    st.page_link("pages/1_Incident_Details.py", label="Forensic Evidence Workspace", icon="🔍")
    st.page_link("pages/2_Scorecard.py", label="Executive Scorecard & KPIs", icon="📊")

    st.markdown("---")
    if st.button("🧹 Clear State & Reset System", use_container_width=True):
        st.session_state["step_index"] = 1
        st.session_state["is_playing"] = False
        reset_response_states()
        st.rerun()


# ==============================================================================
# SECTION 1: HEADER & CONTROL BAR (@st.fragment)
# ==============================================================================

st.markdown("<div class='cyber-header-title'>CyberPulse</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='cyber-header-subtitle'>Early-Warning Cyber Incident Linker • Live SOC Monitoring & Mitigation Console</div>",
    unsafe_allow_html=True,
)


@st.fragment
def render_control_bar() -> None:
    """Render interactive simulation playback and scenario controls without full-page re-renders."""
    with st.container():
        st.markdown(
            "<div style='background-color: #0F172A; border: 1px solid #1E293B; border-radius: 10px; padding: 0.9rem 1.2rem; margin-bottom: 1.2rem;'>",
            unsafe_allow_html=True,
        )
        ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([2.5, 3.2, 1.8, 2.5])

        with ctrl_col1:
            # Scenario Dropdown
            selected_scenario = st.selectbox(
                "Simulation Scenario",
                options=SCENARIOS,
                index=0 if st.session_state["scenario"] == SCENARIO_ATTACK else 1,
                label_visibility="collapsed",
                key="scenario_select_box",
            )
            if selected_scenario != st.session_state["scenario"]:
                st.session_state["scenario"] = selected_scenario
                st.session_state["step_index"] = 1
                st.session_state["is_playing"] = False
                reset_response_states()
                st.rerun()

        with ctrl_col2:
            # Playback Controls: Play, Pause, Next Step, Reset
            b1, b2, b3, b4 = st.columns(4)
            with b1:
                if st.button("▶ Play", use_container_width=True, help="Start automated playback"):
                    st.session_state["is_playing"] = True
                    st.rerun()
            with b2:
                if st.button("⏸ Pause", use_container_width=True, help="Pause current playback"):
                    st.session_state["is_playing"] = False
                    st.rerun()
            with b3:
                if st.button("⏭ Next", use_container_width=True, help="Advance simulation one step"):
                    st.session_state["is_playing"] = False
                    if st.session_state["step_index"] < 5:
                        st.session_state["step_index"] += 1
                    else:
                        st.session_state["step_index"] = 1
                    st.rerun()
            with b4:
                if st.button("🔄 Reset", use_container_width=True, help="Reset scenario to Step 1"):
                    st.session_state["step_index"] = 1
                    st.session_state["is_playing"] = False
                    reset_response_states()
                    st.rerun()

        with ctrl_col3:
            # Playback Speed radio pills
            speed_choice = st.radio(
                "Playback Speed",
                options=["1x", "2x", "4x"],
                index=["1x", "2x", "4x"].index(st.session_state.get("playback_speed", "1x")),
                horizontal=True,
                label_visibility="collapsed",
            )
            st.session_state["playback_speed"] = speed_choice

        with ctrl_col4:
            # Big prominent Action Button
            if st.button("🚨 Launch Simulated Attack", type="primary", use_container_width=True):
                st.session_state["scenario"] = SCENARIO_ATTACK
                st.session_state["step_index"] = 1
                st.session_state["is_playing"] = True
                reset_response_states()
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


render_control_bar()

# Retrieve current snapshot data
current_scenario = st.session_state["scenario"]
current_step = st.session_state["step_index"]
scenario_data = get_scenario_data(current_scenario, current_step)


# ==============================================================================
# SECTION 2: TOP ROW METRICS GRID (3 COLUMNS)
# ==============================================================================

metric_col1, metric_col2, metric_col3 = st.columns([1.2, 1.3, 1.5])

# --- Col 1: Danger Meter (0–100) Dynamic Container ---
with metric_col1:
    danger_score = scenario_data["danger_score"]
    status_label = scenario_data["danger_status"]
    bg_color = scenario_data["danger_bg_color"]
    accent_color = scenario_data["danger_accent_color"]

    st.markdown(
        f"""
        <div class='danger-container' style='background-color: {bg_color}; border-color: {accent_color};'>
            <div>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-size: 0.85rem; font-weight: 700; color: #E2E8F0; text-transform: uppercase; letter-spacing: 0.05em;'>
                        THREAT DANGER METER
                    </span>
                    <span class='danger-badge-pill' style='background-color: {accent_color}; color: #FFFFFF;'>
                        {status_label}
                    </span>
                </div>
                <div class='danger-score-text' style='color: {accent_color};'>
                    {danger_score}<span style='font-size: 1.2rem; color: #94A3B8; font-weight: 500;'>/100</span>
                </div>
            </div>
            <div style='font-size: 0.82rem; color: #CBD5E1; margin-top: 0.5rem;'>
                {
                    "Immediate containment recommended. Anomalous persistent behavior detected."
                    if danger_score >= 75
                    else "Heightened telemetry scrutiny. Possible credential compromise or token theft."
                    if danger_score >= 40
                    else "Normal baseline activity observed. No automated triggers tripped."
                }
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- Col 2: Active Scenario Stage ---
with metric_col2:
    stage_title = scenario_data["stage_title"]
    max_steps = scenario_data["max_steps"]
    step_percent = int((current_step / max_steps) * 100)

    st.markdown(
        f"""
        <div class='stage-container'>
            <div>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                    <span style='font-size: 0.85rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em;'>
                        ACTIVE SCENARIO STAGE
                    </span>
                    <span class='cyber-chip'>Step {current_step} of {max_steps}</span>
                </div>
                <div style='font-size: 1.25rem; font-weight: 700; color: #F8FAFC; margin: 0.3rem 0;'>
                    {stage_title}
                </div>
            </div>
            <div>
                <div style='margin-bottom: 0.35rem; display: flex; justify-content: space-between; font-size: 0.78rem; color: #94A3B8;'>
                    <span>Simulation Progress</span>
                    <span>{step_percent}% Complete</span>
                </div>
                <div style='width: 100%; height: 8px; background-color: #1E293B; border-radius: 4px; overflow: hidden;'>
                    <div style='width: {step_percent}%; height: 100%; background: linear-gradient(90deg, #38BDF8 0%, {accent_color} 100%); transition: width 0.4s ease;'></div>
                </div>
                <div style='font-size: 0.78rem; color: #64748B; margin-top: 0.5rem;'>
                    Scenario: <strong>{current_scenario}</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- Col 3: Response Actions Quick Panel (@st.fragment) ---
with metric_col3:
    @st.fragment
    def render_quick_response_panel() -> None:
        """Render response mitigation action buttons with isolated instant-feedback state."""
        response_states = get_response_states()

        st.markdown(
            """
            <div class='response-container'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;'>
                    <span style='font-size: 0.85rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em;'>
                        RESPONSE ACTIONS QUICK PANEL
                    </span>
                    <span style='font-size: 0.75rem; color: #4E8B65; font-weight: 600;'>Auto-Mitigation SOAR</span>
                </div>
            """,
            unsafe_allow_html=True,
        )

        # 3 Quick Action Buttons
        actions_to_render = [
            ("lock_account", "🔒 Lock Account"),
            ("sign_out_sessions", "🚪 Sign Out All Sessions"),
            ("remove_forwarding_rules", "📧 Remove Forwarding Rule"),
        ]

        for action_id, button_label in actions_to_render:
            act_data = response_states.get(action_id, {})
            is_done = act_data.get("executed", False)
            btn_col, status_col = st.columns([2.2, 1.8])

            with btn_col:
                if is_done:
                    st.button(
                        f"✓ Done: {button_label}",
                        key=f"btn_{action_id}",
                        disabled=True,
                        use_container_width=True,
                    )
                else:
                    if st.button(button_label, key=f"btn_{action_id}", use_container_width=True):
                        trigger_action(action_id)
                        st.rerun()

            with status_col:
                if is_done:
                    st.markdown(
                        f"<div style='color: #4E8B65; font-weight: 600; font-size: 0.82rem; padding-top: 0.45rem;'>"
                        f"✓ Executed <span style='font-size: 0.7rem; color: #94A3B8;'>({act_data.get('executed_at', '')[-8:]})</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        "<div style='color: #94A3B8; font-size: 0.82rem; padding-top: 0.45rem;'>Ready to trigger</div>",
                        unsafe_allow_html=True,
                    )

        st.markdown("</div>", unsafe_allow_html=True)

    render_quick_response_panel()

st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)


# ==============================================================================
# SECTION 3: ATTACK INCIDENT TIMELINE (PLOTLY CHART)
# ==============================================================================

st.markdown(
    """
    <div style='display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 0.5rem;'>
        <div>
            <span style='font-size: 1.15rem; font-weight: 700; color: #F1F5F9;'>
                🔗 Correlated Attack Incident Timeline
            </span>
            <span style='font-size: 0.85rem; color: #94A3B8; margin-left: 0.5rem;'>
                Chronological entity linkage and severity progression
            </span>
        </div>
        <div style='font-size: 0.78rem; color: #64748B;'>
            Hover node for forensic payload & GeoIP
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

timeline_events = scenario_data["timeline_events"]

if timeline_events:
    # Build Plotly Figure
    times = [e["time_seq"] for e in timeline_events]
    severities = [e["Flagged Severity"] for e in timeline_events]
    severity_scores = [e["severity_score"] for e in timeline_events]
    labels = [e["Action"] for e in timeline_events]
    colors = [e["severity_color"] for e in timeline_events]
    users = [e["User"] for e in timeline_events]
    ips = [e["IP Address"] for e in timeline_events]
    countries = [e["Country"] for e in timeline_events]

    fig = go.Figure()

    # Base connector line across linked steps
    fig.add_trace(
        go.Scatter(
            x=times,
            y=severity_scores,
            mode="lines",
            line=dict(color="#334155", width=3, dash="dot"),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Foreground highlighted scatter markers with step labels
    fig.add_trace(
        go.Scatter(
            x=times,
            y=severity_scores,
            mode="markers+text",
            marker=dict(
                size=[18 if s >= 4 else 14 for s in severity_scores],
                color=colors,
                line=dict(color="#FFFFFF", width=1.5),
                symbol="circle",
            ),
            text=labels,
            textposition="top center",
            textfont=dict(size=11, color="#E2E8F0", family="sans serif"),
            customdata=list(zip(severities, users, ips, countries)),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Time: %{x}<br>"
                "Severity: %{customdata[0]}<br>"
                "Target: %{customdata[1]}<br>"
                "IP: %{customdata[2]} (%{customdata[3]})"
                "<extra></extra>"
            ),
            showlegend=False,
        )
    )

    fig.update_layout(
        paper_bgcolor="#0F172A",
        plot_bgcolor="#0F172A",
        height=270,
        margin=dict(l=60, r=40, t=30, b=40),
        xaxis=dict(
            title=dict(text="Time Sequence (UTC)", font=dict(color="#94A3B8", size=12)),
            tickfont=dict(color="#94A3B8", size=11),
            gridcolor="#1E293B",
            showline=True,
            linecolor="#334155",
            zeroline=False,
        ),
        yaxis=dict(
            title=dict(text="Event Severity Category", font=dict(color="#94A3B8", size=12)),
            tickmode="array",
            tickvals=[1, 2, 3, 4, 5],
            ticktext=["Info", "Low", "Medium", "High", "Critical"],
            tickfont=dict(color="#94A3B8", size=11),
            gridcolor="#1E293B",
            range=[0.5, 5.8],
            showline=True,
            linecolor="#334155",
            zeroline=False,
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
else:
    st.info("No timeline events registered yet. Select a scenario or start playback.")

st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)


# ==============================================================================
# SECTION 4: BOTTOM ROW SPLIT LAYOUT (2 COLUMNS)
# ==============================================================================

bot_col1, bot_col2 = st.columns([1.3, 1.2])

# --- Left Column: What Happened - Plain English Story by Keerthana ---
with bot_col1:
    story = scenario_data["story"]
    st.markdown(
        """
        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
            <span style='font-size: 1.1rem; font-weight: 700; color: #F1F5F9;'>
                📖 What Happened? — Plain-English Brief
            </span>
            <span style='font-size: 0.78rem; color: #38BDF8; font-weight: 600;'>
                By Keerthana (Lead IR Analyst)
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    impact_items_html = "".join([f"<li style='margin-bottom: 0.3rem;'>{item}</li>" for item in story["impact"]])
    recomms_html = "".join([f"<li style='margin-bottom: 0.3rem;'>{item}</li>" for item in story["recommendations"]])

    st.markdown(
        f"""
        <div class='story-card'>
            <div style='font-size: 1.15rem; font-weight: 700; color: #38BDF8; margin-bottom: 0.75rem;'>
                {story['title']}
            </div>
            
            <div style='color: #E2E8F0; font-size: 0.92rem; line-height: 1.6; margin-bottom: 1.2rem; background: #1E293B; padding: 0.85rem; border-radius: 6px; border-left: 3px solid #38BDF8;'>
                {story['narrative']}
            </div>

            <div style='margin-bottom: 1.1rem;'>
                <div style='font-size: 0.85rem; font-weight: 700; color: #F87171; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.4rem;'>
                    💥 Impact Breakdown
                </div>
                <ul style='color: #CBD5E1; font-size: 0.88rem; padding-left: 1.2rem; line-height: 1.5;'>
                    {impact_items_html}
                </ul>
            </div>

            <div>
                <div style='font-size: 0.85rem; font-weight: 700; color: #4ADE80; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.4rem;'>
                    🛡️ Clear Recommended Next Steps
                </div>
                <ul style='color: #CBD5E1; font-size: 0.88rem; padding-left: 1.2rem; line-height: 1.5;'>
                    {recomms_html}
                </ul>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- Right Column: Live Log Streamer ---
with bot_col2:
    st.markdown(
        """
        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
            <span style='font-size: 1.1rem; font-weight: 700; color: #F1F5F9;'>
                💻 Live Security Event Stream
            </span>
            <span style='font-size: 0.78rem; color: #94A3B8;'>
                Raw Ingress Telemetry (Syslog / CloudTrail)
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    logs = scenario_data["logs"]
    log_entries_html = []

    for log in logs:
        if "CRIT" in log or "ALERT" in log or "Exfiltrated" in log or "Russia" in log:
            cls = "log-critical"
        elif "WARN" in log or "Tor" in log or "Failed" in log:
            cls = "log-suspicious"
        else:
            cls = "log-info"

        log_entries_html.append(f"<div class='log-entry {cls}'>{log}</div>")

    # Add extra background baseline noise logs for stream realism
    stream_content = "".join(reversed(log_entries_html)) if log_entries_html else "<div class='log-entry log-info'>Listening for incoming syslog telemetry...</div>"

    st.markdown(
        f"""
        <div class='log-terminal'>
            {stream_content}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# SECTION 5: PLAYBACK LOOP CONTROLLER
# ==============================================================================

if st.session_state.get("is_playing", False):
    speed_factor = {"1x": 2.0, "2x": 1.0, "4x": 0.5}.get(st.session_state.get("playback_speed", "1x"), 2.0)
    time.sleep(speed_factor)
    if st.session_state["step_index"] < scenario_data["max_steps"]:
        st.session_state["step_index"] += 1
        st.rerun()
    else:
        # End of scenario reached
        st.session_state["is_playing"] = False
        st.rerun()
