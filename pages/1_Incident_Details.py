"""CyberPulse evidence: every raw event behind an incident, with filters
for person, IP address and device, and a CSV download."""

from html import escape

import pandas as pd
import streamlit as st

from core import ui
from core.schema import ACTIONS

st.set_page_config(page_title="CyberPulse · Evidence", page_icon="🔍", layout="wide")
ui.apply_theme()
ui.init_state()
ui.sidebar()

state = st.session_state
LEVEL_ROW_STYLE = {
    "Likely attack": "background-color: #381A1A; color: #FCA5A5;",
    "Suspicious": "background-color: #2D2318; color: #FDE68A;",
    "Watch": "background-color: #10201A; color: #BBF7D0;",
}

st.markdown("<div class='cp-title'>Evidence</div>", unsafe_allow_html=True)
st.markdown("<div class='cp-subtitle'>The raw events behind each incident. Pick an incident, then narrow it "
            "down by person, IP address or device.</div>", unsafe_allow_html=True)

events = ui.load_events(state.scenario)
whole_day = st.toggle("Show the whole day, not just up to the dashboard's log time", value=False)
count = len(events) if whole_day else ui.shown_count()
incidents = ui.incidents_upto(state.scenario, count)
shown = events.iloc[:count]
st.caption(f"{escape(state.scenario)} · {count:,} of {len(events):,} events "
           f"{'(whole day)' if whole_day else f'up to {state.clock:%H:%M}'} · {len(incidents)} incidents")

labels = ["All events"] + [f"{i.id} · {i.level} ({i.score}) · {i.kind} · {', '.join(u.split('@')[0] for u in i.users) or ', '.join(i.ips)}"
                           for i in incidents]
choice = st.selectbox("Incident", range(len(labels)), format_func=labels.__getitem__, index=1 if incidents else 0)
selected = incidents[choice - 1] if choice else None
rows = selected.evidence(shown) if selected else shown

person_col, ip_col, device_col = st.columns(3)
people = person_col.multiselect("Person", sorted(rows["user"].unique()), placeholder="Everyone")
ips = ip_col.multiselect("IP address", sorted(rows["ip"].unique()), placeholder="Every IP address")
devices = device_col.multiselect("Device", sorted(rows["device"].unique()), placeholder="Every device")
if people:
    rows = rows[rows["user"].isin(people)]
if ips:
    rows = rows[rows["ip"].isin(ips)]
if devices:
    rows = rows[rows["device"].isin(devices)]

for column, (title, value) in zip(st.columns(4), [("Events", len(rows)), ("People", rows["user"].nunique()),
                                                  ("IP addresses", rows["ip"].nunique()), ("Devices", rows["device"].nunique())]):
    column.markdown(f"<div class='cp-kpi'><div class='cp-label'>{title}</div>"
                    f"<div class='cp-kpi-value'>{value:,}</div></div>", unsafe_allow_html=True)

# The most serious incident each event belongs to, for the row colours.
rank = {"Watch": 1, "Suspicious": 2, "Likely attack": 3}
level_of = {}
for incident in incidents:
    for event_id in incident.event_ids:
        if rank[incident.level] > rank.get(level_of.get(event_id), 0):
            level_of[event_id] = incident.level

table = pd.DataFrame({
    "Time": rows["time"].dt.strftime("%H:%M:%S"),
    "Person": rows["user"],
    "Action": [("Failed sign-in" if a == "login" and o == "failure" else ACTIONS[a]) for a, o in zip(rows["action"], rows["outcome"])],
    "Target": rows["target"],
    "IP address": rows["ip"],
    "Device": rows["device"],
    "Country": rows["country"],
    "Incident level": [level_of.get(event_id, "") for event_id in rows["event_id"]],
    "Event": rows["event_id"],
}).iloc[::-1].reset_index(drop=True)

st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
st.dataframe(
    table.style.apply(lambda row: [LEVEL_ROW_STYLE.get(row["Incident level"], "")] * len(row), axis=1),
    width="stretch", height=min(420, 38 + 35 * max(len(table), 1)), hide_index=True)

ui.download_csv(table, f"cyberpulse_{selected.id if selected else 'events'}.csv", "Download these events as CSV")
