"""CyberPulse score card: how well the backend did on Harish's simulated
company, measured against the answer key in his data."""

import plotly.graph_objects as go
import streamlit as st

from core import ui
from core.correlation import danger_over_time
from core.simulator import damage_start_time

st.set_page_config(page_title="CyberPulse · Score card", page_icon="📊", layout="wide")
ui.apply_theme()
ui.init_state()
ui.sidebar()

st.markdown("<div class='cp-title'>Score card</div>", unsafe_allow_html=True)
st.markdown("<div class='cp-subtitle'>Every number here is measured live: the backend runs over Harish's simulated "
            "company and is checked against the answer key in his data.</div>", unsafe_allow_html=True)

attack = ui.score_card("Account takeover")
normal = ui.score_card("Normal day")
events = ui.load_events("Account takeover")
damage_at = damage_start_time(events)


def kpi(column, title, value, description, accent):
    column.markdown(f"""
        <div class='cp-kpi' style='border-top: 4px solid {accent};'>
            <div class='cp-label'>{title}</div>
            <div class='cp-kpi-value' style='color:{accent};'>{value}</div>
            <div class='cp-kpi-desc'>{description}</div>
        </div>""", unsafe_allow_html=True)


caught, warning, red, quiet = st.columns(4)
kpi(caught, "Attacks caught", f"{attack['attacks_caught']}/{attack['attack_events_total']}",
    f"Attack events inside an alarm, in the account-takeover story ({attack['detection_rate']:.0%}).", "#38BDF8")
kpi(warning, "Warning before damage", f"{attack['minutes_of_warning']:.0f} min",
    f"First alarm at {attack['alarm_at']:%H:%M}; the mass download starts at {damage_at:%H:%M}.", "#FBBF24")
kpi(red, "Red before damage", f"{attack['minutes_red_before_damage']:.1f} min",
    f"The meter turned red (Likely attack) at {attack['red_at']:%H:%M}.", "#DC2626")
kpi(quiet, "False alarms", f"{attack['false_alarms'] + normal['false_alarms']}",
    f"Normal events wrongly raised to an alarm. The normal day peaked at {normal['top_score']} (Watch).", "#4ADE80")

st.caption("An alarm is an incident at Suspicious (40+) or Likely attack (75+). Watch-level incidents are notes, not "
           "alarms: the normal day has " + f"{normal['incidents']} of them, one for each harmless oddity in the data "
           "(travel, a new laptop, a planned admin change, a month-end rush, a late login).")

st.markdown("<div style='height:1rem'></div><span class='cp-label'>Danger score during the attack</span>",
            unsafe_allow_html=True)
history = danger_over_time(events, ui.load_profiles())
figure = go.Figure()
for low, high, level in [(0, 40, "Watch"), (40, 75, "Suspicious"), (75, 100, "Likely attack")]:
    figure.add_hrect(y0=low, y1=high, fillcolor=ui.LEVEL_COLORS[level][0], opacity=0.9, line_width=0, layer="below",
                     annotation_text=level, annotation_position="top left",
                     annotation_font_color=ui.LEVEL_COLORS[level][1])
figure.add_trace(go.Scatter(x=history["time"], y=history["score"], mode="lines+markers", line_shape="hv",
                            line=dict(color="#F1F5F9", width=3), marker=dict(size=8),
                            hovertemplate="%{x|%H:%M:%S}: %{y}<extra></extra>", showlegend=False))
figure.add_vline(x=damage_at, line=dict(color="#DC2626", dash="dash"))
figure.add_annotation(x=damage_at, y=12, text="Damage starts", showarrow=False, xanchor="left",
                      font=dict(color="#FCA5A5"))
figure.update_layout(paper_bgcolor="#0F172A", plot_bgcolor="#0F172A", height=320, margin=dict(l=50, r=30, t=20, b=40),
                     xaxis=dict(tickformat="%H:%M", tickfont=dict(color="#94A3B8"), gridcolor="#1E293B"),
                     yaxis=dict(range=[0, 100], tickfont=dict(color="#94A3B8"), gridcolor="#1E293B"))
st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})

st.markdown("<span class='cp-label'>Warning signs in the takeover</span>", unsafe_allow_html=True)
top = ui.incidents_upto("Account takeover", len(events))[0]
st.dataframe(top.timeline()[["time", "step", "severity", "detail"]].assign(time=lambda t: t["time"].dt.strftime("%H:%M:%S"))
             .rename(columns=str.title), hide_index=True, width="stretch")

st.caption("Measured on simulated data: 8 people, 2,071 normal events and one account-takeover story with "
           "163 attack events. Real companies are messier, so treat these as a demonstration, not a guarantee.")
