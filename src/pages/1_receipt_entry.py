"""Receipt entry page — Streamlit auto-discovers this for sidebar navigation."""

import streamlit as st

from src.components.receipt_form import render_receipt_form

if st.session_state.get("editing_receipt_id"):
    st.header("\u270f\ufe0f Edit Receipt")
else:
    st.header("\U0001f4dd Receipt Entry")

render_receipt_form()
