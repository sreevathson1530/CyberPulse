"""CyberPulse: the entry point.

Sets up the page, the top navigation and the product tour, then runs the
page the visitor picked. The pages themselves live in views/.
"""

import streamlit as st

from core import tour, ui

st.set_page_config(page_title="CyberPulse", page_icon=ui.svg_url(ui.LOGO_MARK), layout="wide")
ui.apply_theme()
ui.init_state()
st.logo(ui.svg_url(ui.LOGO_WORDMARK), size="large")

page = st.navigation([
    st.Page("views/monitor.py", title="Live monitor", icon=":material/monitor_heart:", default=True),
    st.Page("views/evidence.py", title="Evidence", icon=":material/manage_search:"),
    st.Page("views/scorecard.py", title="Score card", icon=":material/insights:"),
], position="top")

if tour.should_open():
    tour.show()

page.run()
tour.remember_seen()
