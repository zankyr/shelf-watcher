"""Main Streamlit application entry point."""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from src.database.connection import init_db

# Initialize database tables on startup
init_db()

st.set_page_config(
    page_title="Grocery Receipt Tracker",
    page_icon="🧾",
    layout="wide",
)

st.title("Grocery Receipt Tracker")

st.markdown("""
Welcome to the Grocery Receipt Tracker! Use the sidebar to navigate:

- **Add Receipt** - Enter a new receipt
- **View Receipts** - See all your receipts
""")
