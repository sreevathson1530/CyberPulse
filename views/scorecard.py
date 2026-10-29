"""CyberPulse score card: how well the backend did on Harish's simulated
company, measured against the answer key in his data."""

import plotly.graph_objects as go
import streamlit as st

from core import ui
from core.correlation import danger_over_time
from core.simulator import damage_start_time

ui.page_header("Score card", "Every number here is measured live: the backend runs over the simulated company "
                             "and is checked against the answer key in the data.")

attack = ui.score_card("Account takeover")
normal = ui.score_card("Normal day")
events = ui.load_events("Account takeover")
damage_at = damage_start_time(events)


def stat(column, title, value, description, status):
    column.html(f"""
        <div class='cp-card cp-kpi' style='min-height:0; height:100%'>
          <div class='cp-card-head'><span class='cp-stat-label'>{title}</span>
            <span class='cp-s-{status}' style='color:var(--s-text)'>{ui.icon(status)}</span></div>
          <div class='cp-stat-value'>{value}</div>
          <div class='cp-stat-desc'>{description}</div>
        </div>""")


caught, warning, red, quiet = st.columns(4)
stat(caught, "Attacks caught", f"{attack['attacks_caught']}/{attack['attack_events_total']}",
     f"Attack events inside an alarm in the account-takeover story ({attack['detection_rate']:.0%}).", "good")
stat(warning, "Warning before damage", f"{attack['minutes_of_warning']:.0f} min",
     f"First alarm at {attack['alarm_at']:%H:%M}. The mass download starts at {damage_at:%H:%M}.", "good")
stat(red, "Red before damage", f"{attack['minutes_red_before_damage']:.1f} min",
     f"The score reached Likely attack at {attack['red_at']:%H:%M}.", "good")
stat(quiet, "False alarms", f"{attack['false_alarms'] + normal['false_alarms']}",
     f"Normal events wrongly raised to an alarm. The normal day peaked at {normal['top_score']} (Watch).", "good")

st.html("<div class='cp-footnote'>An alarm is an incident at Suspicious (40+) or Likely attack (75+). Watch-level "
        f"incidents are notes, not alarms: the normal day has {normal['incidents']} of them, one for each harmless "
        "oddity in the data (travel, a new laptop, a planned admin change, a month-end rush, a late login).</div>")

with st.container(key="card_history", gap="small"):
    st.html("<div class='cp-card-head'><h2 class='cp-card-title'>Danger score during the attack</h2>"
            "<span class='cp-card-meta'>Step line: the score after each event · hover for times</span></div>")
    history = danger_over_time(events, ui.load_profiles())
    figure = go.Figure()
    for low, high, level in [(0, 40, "Watch"), (40, 75, "Suspicious"), (75, 100, "Likely attack")]:
        status = ui.LEVEL_STATUS[level]
        figure.add_hrect(y0=low, y1=high, fillcolor=ui.STATUS[status][1], opacity=1, line_width=0, layer="below",
                         annotation_text=level, annotation_position="top left",
                         annotation_font=dict(color=ui.STATUS[status][2], size=11))
    figure.add_trace(go.Scatter(x=history["time"], y=history["score"], mode="lines+markers", line_shape="hv",
                                line=dict(color=ui.INK, width=2), marker=dict(size=7, color=ui.INK,
                                                                               line=dict(color=ui.SURFACE, width=1.5)),
                                hovertemplate="%{x|%H:%M:%S} · score %{y}<extra></extra>", showlegend=False))
    figure.add_vline(x=damage_at, line=dict(color=ui.STATUS["critical"][0], dash="dash", width=1.5))
    figure.add_annotation(x=damage_at, y=10, text="Damage starts", showarrow=False, xanchor="left", xshift=6,
                          font=dict(color=ui.STATUS["critical"][2], size=11))
    ui.style_figure(figure, 320)
    figure.update_layout(margin=dict(l=40, r=20, t=10, b=30), xaxis=dict(tickformat="%H:%M"),
                         yaxis=dict(range=[0, 100], tickvals=[0, 40, 75, 100], fixedrange=True))
    ui.show_chart(figure)

with st.container(key="card_signs", gap="small"):
    top = ui.incidents_upto("Account takeover", len(events))[0]
    st.html(f"<div class='cp-card-head'><h2 class='cp-card-title'>Warning signs in the takeover</h2>"
            f"<span class='cp-card-meta'>{len(top.signs)} signs linked into {top.id}</span></div>")
    st.dataframe(top.timeline()[["time", "step", "severity", "detail"]].assign(time=lambda t: t["time"].dt.strftime("%H:%M:%S"))
                 .rename(columns=str.title), hide_index=True, width="stretch")

st.html("<div class='cp-footnote'>Measured on simulated data: 8 people, 2,071 normal events and one account-takeover "
        "story with 163 attack events. Real companies are messier, so treat these as a demonstration, not a "
        "guarantee.</div>")
