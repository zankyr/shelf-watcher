"""Receipt entry form page."""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import datetime as dt
from decimal import Decimal, InvalidOperation

import streamlit as st
from sqlalchemy.orm import Session

from src.database.connection import SessionLocal
from src.database.crud import create_receipt

st.set_page_config(
    page_title="Add Receipt",
    page_icon="📝",
)

st.title("Add Receipt")


def get_session() -> Session:
    """Get a database session."""
    return SessionLocal()


with st.form("receipt_form"):
    date = st.date_input("Date", value=dt.date.today())
    store = st.text_input("Store", placeholder="e.g., Lidl, Albert Heijn")
    amount_str = st.text_input("Total Amount", placeholder="e.g., 45.99")
    notes = st.text_area("Notes (optional)", placeholder="Any additional notes...")

    submitted = st.form_submit_button("Save Receipt")

    if submitted:
        # Validation
        errors = []

        if not store or not store.strip():
            errors.append("Store name is required")

        total_amount = None
        if not amount_str:
            errors.append("Total amount is required")
        else:
            try:
                total_amount = Decimal(amount_str)
                if total_amount < 0:
                    errors.append("Total amount cannot be negative")
            except InvalidOperation:
                errors.append("Invalid amount format. Use numbers like 45.99")

        if errors:
            for error in errors:
                st.error(error)
        elif total_amount is not None:
            # Save to database
            session = get_session()
            try:
                receipt = create_receipt(
                    db=session,
                    date=date,
                    store=store.strip(),
                    total_amount=total_amount,
                    notes=notes.strip() if notes and notes.strip() else None,
                )
                st.success(f"Receipt saved! (ID: {receipt.id})")
            except Exception as e:
                st.error(f"Error saving receipt: {e}")
            finally:
                session.close()
