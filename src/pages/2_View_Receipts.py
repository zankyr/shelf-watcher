"""Receipt list view page."""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from sqlalchemy.orm import Session

from src.database.connection import SessionLocal
from src.database.crud import get_receipts

st.set_page_config(
    page_title="View Receipts",
    page_icon="📋",
)

st.title("View Receipts")


def get_session() -> Session:
    """Get a database session."""
    return SessionLocal()


session = get_session()
try:
    receipts = get_receipts(session)

    if not receipts:
        st.info("No receipts yet. Add your first receipt!")
    else:
        st.write(f"**Total receipts:** {len(receipts)}")

        # Convert to display format
        data = [
            {
                "Date": receipt.date.strftime("%Y-%m-%d"),
                "Store": receipt.store,
                "Amount": f"\u20ac{receipt.total_amount:.2f}",
                "Notes": receipt.notes or "",
            }
            for receipt in receipts
        ]

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True,
        )
finally:
    session.close()
