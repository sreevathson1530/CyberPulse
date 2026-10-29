"""Shared screen pieces: theme, colours, cached data and playback state.

Owner: Aswin Kumaran (frontend). Every page imports this, so the colours and
the playback position are the same everywhere.
"""

import base64
from datetime import datetime, time, timedelta
from html import escape

import streamlit as st
import streamlit.components.v1 as components

from core.correlation import analyze
from core.metrics import score_card as compute_score_card
from core.response import reset_response_states
from core.schema import to_frame
from core.simulator import DAY, build_scenario, employee_profiles

SCENARIOS = {"Normal day": "normal_day", "Account takeover": "account_takeover"}
DEMO_START = datetime.combine(DAY, time(13, 30))  # half the day played, just before the attack

# One colour per danger level, everywhere: (background, accent).
LEVEL_COLORS = {
    "Clear": ("#13261C", "#4E8B65"),
    "Watch": ("#1E2D24", "#4E8B65"),
    "Suspicious": ("#2D2318", "#D97706"),
    "Likely attack": ("#381A1A", "#DC2626"),
}
SEVERITY_COLORS = {"Low": "#4E8B65", "Medium": "#EAB308", "High": "#D97706", "Critical": "#DC2626"}
SEVERITY_RANK = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}

CSS = """
<style>
.stApp { background-color: #0B0F19; color: #F1F5F9; }
[data-testid="stMainBlockContainer"] { padding-top: 3rem; }
.cp-title {
    font-size: 2rem; font-weight: 800; letter-spacing: -0.03em; margin-bottom: 0.1rem;
    background: linear-gradient(135deg, #38BDF8 0%, #818CF8 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.cp-subtitle { color: #94A3B8; font-size: 0.95rem; margin-bottom: 1rem; }
.cp-label { font-size: 0.78rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; }
.cp-card {
    background-color: #0F172A; border: 1px solid #1E293B; border-radius: 10px;
    padding: 1rem 1.2rem; height: 100%;
}
.cp-meter { border: 1px solid; border-radius: 10px; padding: 1rem 1.2rem; height: 100%; }
.cp-score { font-size: 2.8rem; font-weight: 900; line-height: 1; margin: 0.4rem 0; }
.cp-pill {
    display: inline-block; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.06em;
    text-transform: uppercase; padding: 0.2rem 0.6rem; border-radius: 9999px; color: #FFFFFF;
}
.cp-chip {
    display: inline-block; padding: 0.15rem 0.5rem; background: #1E293B; border-radius: 4px;
    color: #38BDF8; font-weight: 600; font-size: 0.75rem;
}
.cp-progress { width: 100%; height: 8px; background-color: #1E293B; border-radius: 4px; overflow: hidden; }
.cp-story { background-color: #0F172A; border: 1px solid #1E293B; border-radius: 10px; padding: 1.2rem; }
.cp-story h4 { color: #94A3B8; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; margin: 0.9rem 0 0.25rem; }
.cp-story p { color: #E2E8F0; font-size: 0.95rem; line-height: 1.55; margin: 0; }
.cp-feed {
    background-color: #070B12; border: 1px solid #1E293B; border-radius: 10px; padding: 0.8rem;
    height: 420px; overflow-y: auto; font-family: Consolas, "SFMono-Regular", Menlo, monospace; font-size: 0.8rem;
}
.cp-row { padding: 0.4rem 0.6rem; margin-bottom: 0.35rem; border-radius: 4px; border-left: 4px solid #334155; color: #94A3B8; word-break: break-word; }
.cp-row.watch { border-left-color: #4E8B65; color: #BBF7D0; background-color: #10201A; }
.cp-row.suspicious { border-left-color: #D97706; color: #FDE68A; background-color: #2D2318; }
.cp-row.attack { border-left-color: #DC2626; color: #FCA5A5; background-color: #381A1A; }
.cp-kpi { background-color: #0F172A; border: 1px solid #1E293B; border-radius: 10px; padding: 1rem 1.2rem; height: 100%; }
.cp-kpi-value { font-size: clamp(1.5rem, 2.2vw, 2rem); font-weight: 900; line-height: 1.1; margin: 0.3rem 0; white-space: nowrap; }
.cp-kpi-desc { font-size: 0.83rem; color: #CBD5E1; line-height: 1.45; }
@media (max-width: 640px) {
    .cp-title { font-size: 1.6rem; }
    .cp-score { font-size: 2.2rem; }
    .cp-feed { height: 320px; }
}
</style>
"""


def apply_theme():
    st.markdown(CSS, unsafe_allow_html=True)


def sidebar():
    with st.sidebar:
        st.markdown("### CyberPulse")
        st.caption("Links suspicious log events into one incident, scores it and explains it in plain English.")
        st.page_link("app.py", label="Live dashboard", icon="🚨")
        st.page_link("pages/1_Incident_Details.py", label="Evidence", icon="🔍")
        st.page_link("pages/2_Scorecard.py", label="Score card", icon="📊")
        st.divider()
        st.caption("All data is simulated: a made-up company of 8 people, test-range IP addresses "
                   "(203.0.113.x) and .example emails. Response buttons are pretend.")


def download_csv(table, file_name, label):
    """A download button for a table, with the file inside the page.

    st.download_button fetches the file from the server's memory in a second
    request. On Vercel that request can reach a different server instance,
    which answers 404, so the file travels with the page instead."""
    data = base64.b64encode(table.to_csv(index=False).encode("utf-8")).decode()
    components.html(f"""
        <style>
          body {{ margin: 0; }}
          a {{ display: inline-block; padding: 0.4rem 0.8rem; border-radius: 0.5rem; text-decoration: none;
               border: 1px solid rgba(250, 250, 250, 0.2); background: #0F172A; color: #F1F5F9;
               font: 400 0.95rem "Source Sans Pro", "Source Sans", system-ui, sans-serif; }}
          a:hover {{ border-color: #38BDF8; color: #38BDF8; }}
        </style>
        <a download="{escape(file_name)}" href="data:text/csv;base64,{data}">{escape(label)}</a>""", height=44)


# Data

@st.cache_data(show_spinner=False)
def load_events(scenario):
    """All events of a scenario ("Normal day" or "Account takeover"), oldest first."""
    return to_frame(build_scenario(SCENARIOS[scenario]))


@st.cache_resource(show_spinner=False)
def load_profiles():
    return employee_profiles()


@st.cache_data(show_spinner=False, max_entries=600)
def incidents_upto(scenario, count):
    """Incidents found in the first `count` events, most dangerous first."""
    return analyze(load_events(scenario).iloc[:count], load_profiles())


@st.cache_data(show_spinner=False)
def score_card(scenario):
    return compute_score_card(load_events(scenario), load_profiles())


# Playback state, shared by every page

def init_state():
    if "scenario" not in st.session_state:
        set_scenario("Normal day", DEMO_START)
    st.session_state.setdefault("playing", False)
    st.session_state.setdefault("speed", "1x")


def set_scenario(scenario, clock=None):
    events = load_events(scenario)
    st.session_state.scenario = scenario
    st.session_state.clock = clock if clock is not None else events["time"].iloc[0] - timedelta(seconds=1)
    st.session_state.playing = False
    reset_response_states()


def shown_count():
    """How many events have been played so far."""
    events = load_events(st.session_state.scenario)
    return int(events["time"].searchsorted(st.session_state.clock, side="right"))


def advance(minutes):
    """Move the playback clock forward. Returns True at the end of the log."""
    last = load_events(st.session_state.scenario)["time"].iloc[-1]
    st.session_state.clock = min(st.session_state.clock + timedelta(minutes=minutes), last)
    if st.session_state.clock >= last:
        st.session_state.playing = False
        return True
    return False


# Button callbacks

def play():
    if shown_count() >= len(load_events(st.session_state.scenario)):
        set_scenario(st.session_state.scenario)  # at the end: start the day again
    st.session_state.playing = True


def pause():
    st.session_state.playing = False


def next_event():
    st.session_state.playing = False
    events = load_events(st.session_state.scenario)
    later = events["time"][events["time"] > st.session_state.clock]
    if not later.empty:
        st.session_state.clock = later.iloc[0]


def reset():
    set_scenario(st.session_state.scenario)


def launch_attack():
    """Switch to the takeover story just before it starts, and play it."""
    events = load_events("Account takeover")
    first_attack = events.loc[events["label"] == "attack", "time"].min()
    set_scenario("Account takeover", first_attack - timedelta(minutes=10))
    st.session_state.speed = "1x"
    st.session_state.playing = True


def change_scenario():
    set_scenario(st.session_state.scenario_choice, DEMO_START)
