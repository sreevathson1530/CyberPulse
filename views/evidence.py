"""CyberPulse evidence: every raw event behind an incident, with filters
for person, IP address and device, and a CSV download."""

from html import escape

import pandas as pd
import streamlit as st

from core import ui
from core.schema import ACTIONS

state = st.session_state
LEVEL_ROW_STYLE = {level: f"background-color: {ui.STATUS[status][1]};" for level, status in ui.LEVEL_STATUS.items()}

ui.page_header("Evidence", "The raw events behind each incident. Pick an incident, then narrow it down by "
                           "person, IP address or device.")

events = ui.load_events(state.scenario)
whole_day = st.toggle("Show the whole day, not just up to the monitor's log time", value=False)
count = len(events) if whole_day else ui.shown_count()
incidents = ui.incidents_upto(state.scenario, count)
shown = events.iloc[:count]

labels = ["All events"] + [f"{i.id} · {i.level} ({i.score}) · {i.kind} · {', '.join(ui.short(u) for u in i.users) or ', '.join(i.ips)}"
                           for i in incidents]
incident_col, person_col, ip_col, device_col = st.columns([2.2, 1, 1, 1])
choice = incident_col.selectbox("Incident", range(len(labels)), format_func=labels.__getitem__,
                                index=1 if incidents else 0)
selected = incidents[choice - 1] if choice else None
rows = selected.evidence(shown) if selected else shown

people = person_col.multiselect("Person", sorted(rows["user"].unique()), placeholder="Everyone")
ips = ip_col.multiselect("IP address", sorted(rows["ip"].unique()), placeholder="Any IP address")
devices = device_col.multiselect("Device", sorted(rows["device"].unique()), placeholder="Any device")
if people:
    rows = rows[rows["user"].isin(people)]
if ips:
    rows = rows[rows["ip"].isin(ips)]
if devices:
    rows = rows[rows["device"].isin(devices)]

st.html(f"<div class='cp-footnote'>{escape(state.scenario)} · {count:,} of {len(events):,} events "
        f"{'(whole day)' if whole_day else f'up to {state.clock:%H:%M}'} · {len(incidents)} incidents</div>")

for column, (title, value) in zip(st.columns(4), [("Events", len(rows)), ("People", rows["user"].nunique()),
                                                  ("IP addresses", rows["ip"].nunique()), ("Devices", rows["device"].nunique())]):
    column.html(f"<div class='cp-card'><div class='cp-stat-label'>{title}</div>"
                f"<div class='cp-stat-value'>{value:,}</div></div>")

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

with st.container(key="card_events", gap="small"):
    title_col, download_col = st.columns([3, 1], vertical_alignment="center")
    title_col.html(f"<div class='cp-card-head'><h2 class='cp-card-title'>Events</h2>"
                   f"<span class='cp-card-meta'>Newest first · tinted rows belong to an incident</span></div>")
    with download_col:
        ui.download_csv(table, f"cyberpulse_{selected.id if selected else 'events'}.csv", "Download CSV")
    st.dataframe(
        table.style.apply(lambda row: [LEVEL_ROW_STYLE.get(row["Incident level"], "")] * len(row), axis=1),
        width="stretch", height=min(440, 38 + 35 * max(len(table), 1)), hide_index=True)
