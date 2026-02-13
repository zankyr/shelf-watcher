"""Analytics page — price trends, store comparison, and spending charts."""

import streamlit as st

from src.components.analytics import render_analytics

st.header("\U0001f4ca Analytics")
render_analytics()
