"""CyberPulse live monitor.

Plays a day of company logs event by event, runs them through the backend
and shows the danger score, the linked incident on a timeline, its story in
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
    ("lock_account", "Lock account", "Account locked", ":material/lock:"),
    ("sign_out_sessions", "Sign out all sessions", "Sessions signed out", ":material/logout:"),
    ("remove_forwarding_rules", "Remove forwarding rule", "Forwarding rule removed", ":material/forward_to_inbox:"),
]

state = st.session_state

ui.page_header("Live monitor", "Watch a day of sign-ins, emails and file activity from a made-up company of "
                               "8 people. CyberPulse links the warning signs into one incident and explains it.")

# Toolbar. Buttons use callbacks, so the state is updated before the page redraws.
with st.container(horizontal=True, vertical_alignment="center", gap="small", key="toolbar"):
    state.scenario_choice = state.scenario
    st.segmented_control("Scenario", list(ui.SCENARIOS), key="scenario_choice", required=True,
                         on_change=ui.change_scenario, label_visibility="collapsed")
    if state.playing:
        st.button("Pause", icon=":material/pause:", on_click=ui.toggle_play, key="play_pause")
    else:
        st.button("Play", icon=":material/play_arrow:", on_click=ui.toggle_play, key="play_pause")
    st.button("Next event", icon=":material/skip_next:", on_click=ui.next_event, key="next_event")
    st.button("Reset", icon=":material/restart_alt:", on_click=ui.reset, key="reset")
    st.segmented_control("Speed", list(MINUTES_PER_TICK), key="speed", required=True,
                         format_func=lambda s: s.replace("x", "×"), label_visibility="collapsed")
    st.space("stretch")
    st.button("Run attack demo", icon=":material/bolt:", type="primary", on_click=ui.launch_attack, key="run_attack")


def render_score(score, level, top):
    status = ui.LEVEL_STATUS[level]
    about = f"{escape(top.kind)} · {escape(', '.join(ui.short(u) for u in top.users) or top.ips[0])}" if top else "No incidents yet"
    st.html(f"""
        <section class='cp-card cp-kpi cp-s-{status}' aria-label='Danger score'>
          <div class='cp-card-head'><h2 class='cp-card-title'>Danger score</h2>{ui.level_badge(level)}</div>
          <div class='cp-score'><b>{score}</b><span>/ 100</span></div>
          <div class='cp-gauge'><i style='width:{max(score, 1)}%'></i><u style='left:40%'></u><u style='left:75%'></u></div>
          <div class='cp-scale'><span style='left:0'>0</span><span style='left:40%'>40</span>
            <span style='left:75%'>75</span><span style='left:100%'>100</span></div>
          <p class='cp-note'>{METER_TEXT[level]}</p>
          <div class='cp-meta'>{about}</div>
        </section>""")


def render_clock(events, count, top):
    total = len(events)
    percent = round(100 * count / total) if total else 0
    latest = f"Latest sign: {escape(top.signs[-1].step)} at {top.signs[-1].time:%H:%M}" if top else "No warning signs yet"
    live = (f"<span class='cp-live on'><i class='cp-dot'></i>Playing · {state.speed.replace('x', '×')}</span>"
            if state.playing else "<span class='cp-live'><i class='cp-dot'></i>Paused</span>")
    st.html(f"""
        <section class='cp-card cp-kpi' aria-label='Log time'>
          <div class='cp-card-head'><h2 class='cp-card-title'>Log time</h2>{live}</div>
          <div class='cp-clock'>{state.clock:%H:%M}</div>
          <div class='cp-progress'><i style='width:{percent}%'></i></div>
          <p class='cp-note'>{latest}</p>
          <div class='cp-meta'>{count:,} of {total:,} events · {escape(state.scenario)} · {state.clock:%d %b %Y}</div>
        </section>""")


def render_responses(top):
    with st.container(key="card_response", gap="small"):
        alarm = top and top.level in ALARM_LEVELS
        meta = "Pretend actions" if alarm else ""
        st.html(f"<div class='cp-card-head'><h2 class='cp-card-title'>Response</h2>"
                f"<span class='cp-card-meta'>{meta}</span></div>")
        if not alarm:
            st.html("<p class='cp-note' style='color:var(--cp-ink-3)'>No action needed yet. The response buttons "
                    "appear when an incident reaches Suspicious (40+).</p>")
            return
        st.html(f"<div class='cp-meta' style='margin:-0.2rem 0 0.2rem'>For "
                f"{escape(', '.join(ui.short(u) for u in top.users) or 'the accounts involved')}. Nothing real changes.</div>")
        done = get_response_states()
        for action, label, done_label, icon in RESPONSES:
            if done[action]["executed"]:
                st.button(done_label, icon=":material/check:", key=f"done_{action}", disabled=True, width="stretch")
            else:
                st.button(label, icon=icon, key=action, on_click=trigger_action, args=(action,), width="stretch")


def render_timeline(top):
    with st.container(key="card_timeline", gap="small"):
        meta = f"{top.id} · {escape(top.kind)} · hover a dot for details" if top else ""
        st.html(f"<div class='cp-card-head'><h2 class='cp-card-title'>Incident timeline</h2>"
                f"<span class='cp-card-meta'>{meta}</span></div>")
        if not top:
            ui.empty_state("No warning signs yet", "Press Play or run the attack demo. Each warning sign "
                                                   "shows up here as a dot on the timeline.")
            return
        signs = top.signs
        # Pad the time axis so a lone sign gets a readable axis and the labels
        # at either end are not cut off.
        pad = max((top.end - top.start) * 0.12, pd.Timedelta(minutes=5))
        figure = go.Figure()
        figure.add_hline(y=0, line=dict(color=ui.BORDER, width=2))
        figure.add_trace(go.Scatter(
            x=[s.time for s in signs], y=[0] * len(signs), mode="markers", text=[s.step for s in signs],
            marker=dict(size=13, color=[ui.SEVERITY_COLORS[s.severity] for s in signs], line=dict(color=ui.SURFACE, width=2)),
            customdata=[[s.severity, s.detail] for s in signs],
            hovertemplate="<b>%{text}</b><br>%{x|%H:%M:%S} · %{customdata[0]}<br>%{customdata[1]}<extra></extra>",
            cliponaxis=False, showlegend=False))
        # Labels sit on stems, alternating above and below at three heights,
        # so signs that land close together do not print over each other.
        for i, sign in enumerate(signs):
            side = -1 if i % 2 == 0 else 1
            figure.add_annotation(
                x=sign.time, y=0, text=escape(sign.step), ax=0, ay=side * (34 + 30 * (i // 2 % 3)),
                showarrow=True, arrowhead=0, arrowwidth=1, arrowcolor=ui.SEVERITY_COLORS[sign.severity],
                font=dict(size=11, color=ui.INK), bgcolor=ui.SURFACE,
                bordercolor=ui.SEVERITY_COLORS[sign.severity], borderwidth=1, borderpad=3)
        # One legend entry per severity present, in order.
        for severity in [s for s in ui.SEVERITY_RANK if any(sign.severity == s for sign in signs)]:
            figure.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=severity,
                                        marker=dict(size=9, color=ui.SEVERITY_COLORS[severity])))
        ui.style_figure(figure, 300)
        figure.update_layout(
            margin=dict(l=24, r=24, t=36, b=30),
            xaxis=dict(range=[top.start - pad, top.end + pad], tickformat="%H:%M", showgrid=True),
            yaxis=dict(range=[-1, 1], visible=False, fixedrange=True),
            legend=dict(orientation="h", x=0, y=1.14, font=dict(size=12, color=ui.INK_2), title=dict(text="Severity  ", font=dict(size=12, color=ui.INK_3))),
        )
        ui.show_chart(figure)


def render_story(top):
    if not top:
        st.html("<section class='cp-card cp-story'><div class='cp-card-head'><h2 class='cp-card-title'>What happened"
                "</h2></div><div class='cp-empty'><strong>Nothing to explain yet</strong>"
                "<span>When warning signs link up, the story appears here in plain English.</span></div></section>")
        return
    story = explain(top)
    st.html(f"""
        <section class='cp-card cp-story'>
          <div class='cp-card-head'><h2 class='cp-card-title'>What happened</h2>{ui.level_badge(top.level)}</div>
          <h3>{escape(top.kind)}</h3>
          <dl>
            <dt>What happened</dt><dd>{escape(story['what_happened'])}</dd>
            <dt>Why it matters</dt><dd>{escape(story['why_it_matters'])}</dd>
            <dt>What to do now</dt><dd>{escape(story['what_to_do'])}</dd>
          </dl>
        </section>""")


def render_feed(shown, incidents):
    # Colour each event by the most serious incident it belongs to.
    rank = {"Watch": 1, "Suspicious": 2, "Likely attack": 3}
    level_of = {}
    for incident in reversed(incidents):  # least dangerous first, so the worst wins
        for event_id in incident.event_ids:
            if rank[incident.level] >= rank.get(level_of.get(event_id), 0):
                level_of[event_id] = incident.level
    rows = []
    for event in shown.tail(FEED_ROWS).iloc[::-1].itertuples(index=False):
        action = "Failed sign-in" if event.action == "login" and event.outcome == "failure" else ACTIONS[event.action]
        target = f": {escape(str(event.target))}" if event.target else ""
        level = level_of.get(event.event_id)
        css = f"cp-s-{ui.LEVEL_STATUS[level]}" if level else ""
        rows.append(
            f"<div class='cp-row {css}'><time>{event.time:%H:%M:%S}</time>"
            f"<div><b>{escape(ui.short(event.user))}</b> · {escape(action)}{target}"
            f"<small>{escape(event.device)} · {escape(event.ip)} · {escape(event.country)}</small></div></div>")
    body = "".join(rows) or "<div class='cp-empty'><span>Waiting for the first event…</span></div>"
    st.html(f"""
        <section class='cp-card'>
          <div class='cp-card-head'><h2 class='cp-card-title'>Live feed</h2>
            <span class='cp-card-meta'>Newest first · tinted rows belong to an incident</span></div>
          <div class='cp-feed' tabindex='0'>{body}</div>
        </section>""")


def render_incident_list(incidents):
    if len(incidents) < 2:
        return
    with st.container(key="card_incidents", gap="small"):
        st.html(f"<div class='cp-card-head'><h2 class='cp-card-title'>All incidents so far</h2>"
                f"<span class='cp-card-meta'>{len(incidents)} incidents, most dangerous first</span></div>")
        st.dataframe(
            [{"Level": i.level, "Score": i.score, "Kind": i.kind, "People": ", ".join(ui.short(u) for u in i.users),
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

    score_col, clock_col, response_col = st.columns([1.15, 1.15, 1.2])
    with score_col:
        render_score(score, danger_level(score), top)
    with clock_col:
        render_clock(events, count, top)
    with response_col:
        render_responses(top)

    render_timeline(top)

    story_col, feed_col = st.columns([1.1, 1])
    with story_col:
        render_story(top)
    with feed_col:
        render_feed(events.iloc[:count], incidents)

    render_incident_list(incidents)


live_dashboard()
