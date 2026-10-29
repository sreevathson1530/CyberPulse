"""Entry point for hosting (Vercel): the Streamlit app as an ASGI app.

Locally, run it the usual way:  streamlit run app.py
"""

import os
from pathlib import Path

# Vercel's file system is read-only outside /tmp. With usage statistics on,
# Streamlit saves an id in ~/.streamlit and every session fails to start.
os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

import streamlit as st  # noqa: E402

app = st.App(Path(__file__).with_name("app.py"))
