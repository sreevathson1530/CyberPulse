"""Entry point for hosting (Vercel): the Streamlit app as an ASGI app.

Locally, run it the usual way:  streamlit run app.py
"""

from pathlib import Path

import streamlit as st

app = st.App(Path(__file__).with_name("app.py"))
