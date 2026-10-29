"""CyberPulse: the live dashboard.

Plays a day of company logs event by event, runs them through the backend
and shows the danger meter, the linked incident on a timeline, its story in
plain English, the live feed and the response buttons.
"""

from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import ui
from core.correlation import danger_level
from core.explain import explain
from core.metrics import ALARM_LEVELS
from core.response import get_response_states, trigger_action
from core.schema import ACTIONS

st.set_page_config(page_title="CyberPulse", page_icon="🛡️", layout="wide")
ui.apply_theme()
ui.init_state()
ui.sidebar()

MINUTES_PER_TICK = {"1x": 2, "2x": 4, "4x": 8}  # log minutes played each second
TICK_SECONDS = 1.0
FEED_ROWS = 60
METER_TEXT = {
    "Clear": "Nothing unusual yet.",
    "Watch": "A few small oddities. Worth a look, no action needed.",
    "Suspicious": "Several warning signs link up. Check this now.",
    "Likely attack": "Act now: this looks like a real attack.",
}
RESPONSES = [
    ("lock_account", "Lock account", "Account locked"),
    ("sign_out_sessions", "Sign out all sessions", "Sessions signed out"),
    ("remove_forwarding_rules", "Remove forwarding rule", "Forwarding rule removed"),
]

state = st.session_state

# Header and control bar. Buttons use callbacks, so the state is updated
# before the page redraws.

st.markdown("<div class='cp-title'>CyberPulse</div>", unsafe_allow_html=True)
st.markdown("<div class='cp-subtitle'>Early warning for small businesses: suspicious log events, "
            "linked into one incident and explained in plain English.</div>", unsafe_allow_html=True)

# Two rows, so every label fits next to the sidebar on a laptop screen.
scenario_col, speed_col, launch_col = st.columns([3, 2, 2.4], vertical_alignment="center")
with scenario_col:
    state.scenario_choice = state.scenario
    st.selectbox("Scenario", list(ui.SCENARIOS), key="scenario_choice", on_change=ui.change_scenario,
                 label_visibility="collapsed")
with speed_col:
    st.radio("Speed", list(MINUTES_PER_TICK), key="speed", horizontal=True, label_visibility="collapsed")
with launch_col:
    st.button("🚨 Launch attack", type="primary", on_click=ui.launch_attack, width="stretch")
play_col, pause_col, next_col, reset_col = st.columns(4)
play_col.button("▶ Play", on_click=ui.play, width="stretch", disabled=state.playing)
pause_col.button("⏸ Pause", on_click=ui.pause, width="stretch", disabled=not state.playing)
next_col.button("⏭ Next event", on_click=ui.next_event, width="stretch")
reset_col.button("↺ Reset", on_click=ui.reset, width="stretch")


def render_meter(score, level, top):
    background, accent = ui.LEVEL_COLORS[level]
    about = f"{escape(top.kind)} · {escape(', '.join(_short(u) for u in top.users) or top.ips[0])}" if top else "No incidents"
    st.markdown(f"""
        <div class='cp-meter' style='background-color:{background}; border-color:{accent};'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <span class='cp-label'>Danger meter</span>
                <span class='cp-pill' style='background-color:{accent};'>{escape(level)}</span>
            </div>
            <div class='cp-score' style='color:{accent};'>{score}<span style='font-size:1.1rem; color:#94A3B8;'>/100</span></div>
            <div style='font-size:0.85rem; color:#E2E8F0;'>{METER_TEXT[level]}</div>
            <div style='font-size:0.78rem; color:#94A3B8; margin-top:0.4rem;'>{about}</div>
        </div>""", unsafe_allow_html=True)


def render_clock(events, count, top):
    total = len(events)
    percent = round(100 * count / total) if total else 0
    latest = f"Latest warning: {escape(top.signs[-1].step)} at {top.signs[-1].time:%H:%M}" if top else "No warnings yet"
    playing = "Playing" if state.playing else "Paused"
    st.markdown(f"""
        <div class='cp-card'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <span class='cp-label'>Log time</span>
                <span class='cp-chip'>{playing} · {state.speed}</span>
            </div>
            <div style='font-size:1.9rem; font-weight:800; color:#F8FAFC; margin:0.3rem 0;'>{state.clock:%H:%M}</div>
            <div style='font-size:0.85rem; color:#CBD5E1; margin-bottom:0.6rem;'>{latest}</div>
            <div class='cp-progress'><div style='width:{percent}%; height:100%; background:#38BDF8;'></div></div>
            <div style='font-size:0.78rem; color:#94A3B8; margin-top:0.4rem;'>
                {count:,} of {total:,} events · {escape(state.scenario)} · {state.clock:%d %b %Y}
            </div>
        </div>""", unsafe_allow_html=True)


def render_responses(top):
    with st.container(border=True):
        st.markdown("<span class='cp-label'>Response</span>", unsafe_allow_html=True)
        if not top or top.level not in ALARM_LEVELS:
            st.caption("No action needed yet. Buttons appear when an incident reaches Suspicious.")
            return
        st.caption(f"For {', '.join(_short(u) for u in top.users) or 'the accounts involved'}. "
                   "Pretend actions: nothing real changes.")
        done = get_response_states()
        for action, label, done_label in RESPONSES:
            if done[action]["executed"]:
                st.button(f"✓ {done_label}", key=f"done_{action}", disabled=True, width="stretch")
            else:
                st.button(label, key=action, on_click=trigger_action, args=(action,), width="stretch")


def render_timeline(top):
    if not top:
        st.info("No warning signs yet. They appear here as the log plays.")
        return
    signs = top.signs
    # Pad the time axis so a lone sign gets a readable axis and the labels at
    # either end are not cut off.
    pad = max((top.end - top.start) * 0.12, pd.Timedelta(minutes=5))
    figure = go.Figure()
    figure.add_hline(y=0, line=dict(color="#334155", width=2))
    figure.add_trace(go.Scatter(
        x=[s.time for s in signs], y=[0] * len(signs), mode="markers", text=[s.step for s in signs],
        marker=dict(size=15, color=[ui.SEVERITY_COLORS[s.severity] for s in signs], line=dict(color="#FFFFFF", width=1.5)),
        customdata=[[s.severity, s.detail] for s in signs],
        hovertemplate="<b>%{text}</b><br>%{x|%H:%M:%S} · %{customdata[0]}<br>%{customdata[1]}<extra></extra>",
        cliponaxis=False, showlegend=False))
    # Labels sit on stems, alternating above and below at three heights, so
    # signs that land close together do not print over each other.
    for i, sign in enumerate(signs):
        side = -1 if i % 2 == 0 else 1
        figure.add_annotation(
            x=sign.time, y=0, text=escape(sign.step), ax=0, ay=side * (34 + 30 * (i // 2 % 3)),
            showarrow=True, arrowhead=0, arrowwidth=1, arrowcolor=ui.SEVERITY_COLORS[sign.severity],
            font=dict(size=11, color="#E2E8F0"), bgcolor="#0F172A",
            bordercolor=ui.SEVERITY_COLORS[sign.severity], borderwidth=1, borderpad=3)
    # One legend entry per severity present, in order.
    for severity in [s for s in ui.SEVERITY_RANK if any(sign.severity == s for sign in signs)]:
        figure.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=severity,
                                    marker=dict(size=10, color=ui.SEVERITY_COLORS[severity])))
    figure.update_layout(
        paper_bgcolor="#0F172A", plot_bgcolor="#0F172A", height=320, margin=dict(l=30, r=30, t=40, b=40),
        xaxis=dict(range=[top.start - pad, top.end + pad], tickformat="%H:%M", tickfont=dict(color="#94A3B8"),
                   gridcolor="#1E293B"),
        yaxis=dict(range=[-1, 1], visible=False, fixedrange=True),
        legend=dict(orientation="h", x=0, y=1.12, font=dict(color="#94A3B8"), title_text="Severity: "),
    )
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


def render_story(top):
    if not top:
        st.markdown("<div class='cp-story'><p>Nothing to explain yet.</p></div>", unsafe_allow_html=True)
        return
    story = explain(top)
    _, accent = ui.LEVEL_COLORS[top.level]
    st.markdown(f"""
        <div class='cp-story' style='border-left: 4px solid {accent};'>
            <div style='font-size:1.1rem; font-weight:700; color:{accent};'>{escape(story['title'])}</div>
            <h4>What happened</h4><p>{escape(story['what_happened'])}</p>
            <h4>Why it matters</h4><p>{escape(story['why_it_matters'])}</p>
            <h4>What to do now</h4><p>{escape(story['what_to_do'])}</p>
        </div>""", unsafe_allow_html=True)


def render_feed(shown, incidents):
    # Colour each event by the most serious incident it belongs to.
    rank = {"Watch": 1, "Suspicious": 2, "Likely attack": 3}
    css = {"Watch": "watch", "Suspicious": "suspicious", "Likely attack": "attack"}
    level_of = {}
    for incident in reversed(incidents):  # least dangerous first, so the worst wins
        for event_id in incident.event_ids:
            if rank[incident.level] >= rank.get(level_of.get(event_id), 0):
                level_of[event_id] = incident.level
    rows = []
    for event in shown.tail(FEED_ROWS).iloc[::-1].itertuples(index=False):
        action = "Failed sign-in" if event.action == "login" and event.outcome == "failure" else ACTIONS[event.action]
        target = f": {escape(str(event.target))}" if event.target else ""
        rows.append(
            f"<div class='cp-row {css.get(level_of.get(event.event_id), '')}'>"
            f"{event.time:%H:%M:%S} · <b>{escape(_short(event.user))}</b> · {escape(action)}{target}<br>"
            f"<span style='opacity:0.75'>{escape(event.device)} · {escape(event.ip)} · {escape(event.country)}</span></div>")
    body = "".join(rows) or "<div class='cp-row'>Waiting for the first event…</div>"
    st.markdown(f"<div class='cp-feed'>{body}</div>", unsafe_allow_html=True)


def render_incident_list(incidents):
    if len(incidents) < 2:
        return
    st.markdown("<span class='cp-label'>All incidents so far</span>", unsafe_allow_html=True)
    st.dataframe(
        [{"Level": i.level, "Score": i.score, "Kind": i.kind, "People": ", ".join(_short(u) for u in i.users),
          "Steps": " → ".join(i.steps), "Started": f"{i.start:%H:%M}"} for i in incidents],
        hide_index=True, width="stretch")


@st.fragment(run_every=TICK_SECONDS if state.playing else None)
def live_dashboard():
    if state.playing and ui.advance(MINUTES_PER_TICK[state.speed]):
        st.rerun()  # reached the end: redraw the whole page so the controls update

    events = ui.load_events(state.scenario)
    count = ui.shown_count()
    incidents = ui.incidents_upto(state.scenario, count)
    top = incidents[0] if incidents else None
    score = top.score if top else 0

    meter_col, clock_col, response_col = st.columns([1.2, 1.3, 1.5])
    with meter_col:
        render_meter(score, danger_level(score), top)
    with clock_col:
        render_clock(events, count, top)
    with response_col:
        render_responses(top)

    st.markdown("<div style='height:0.8rem'></div><span class='cp-label'>Incident timeline</span>", unsafe_allow_html=True)
    if top:
        st.caption(f"{top.id} · {top.kind} · each dot is a warning sign; hover for details")
    render_timeline(top)

    story_col, feed_col = st.columns([1.2, 1.3])
    with story_col:
        st.markdown("<span class='cp-label'>What happened</span>", unsafe_allow_html=True)
        render_story(top)
    with feed_col:
        st.markdown("<span class='cp-label'>Live feed</span>", unsafe_allow_html=True)
        render_feed(events.iloc[:count], incidents)

    render_incident_list(incidents)


def _short(email):
    return email.split("@")[0]


live_dashboard()
