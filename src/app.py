"""Shelf Watcher — Grocery Receipt Tracker.

Streamlit entry point. Run with: streamlit run src/app.py
"""

import streamlit as st

from src.database.connection import init_db

st.set_page_config(page_title="Shelf Watcher", page_icon="\U0001f6d2", layout="wide")

init_db()

st.title("\U0001f6d2 Shelf Watcher")
st.markdown("Track your grocery receipts and analyze price trends.")
st.markdown(
    "Use the **sidebar** to navigate between pages: "
    "**Receipt Entry**, **Receipt History**, and **Analytics**."
)
