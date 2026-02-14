"""Receipt history page — browse past receipts with filters and export."""

import streamlit as st

from src.components.receipt_form import _EDIT_STATE_KEYS
from src.components.receipt_history import render_receipt_history

# Clear stale edit state when navigating to this page
for key in _EDIT_STATE_KEYS:
    st.session_state.pop(key, None)

st.header("\U0001f4cb Receipt History")
render_receipt_history()
