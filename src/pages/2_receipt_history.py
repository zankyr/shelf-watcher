"""Receipt history page — browse past receipts with filters and export."""

import streamlit as st

from src.components.receipt_history import render_receipt_history

st.header("\U0001f4cb Receipt History")
render_receipt_history()
