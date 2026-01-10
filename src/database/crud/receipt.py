"""CRUD operations for Receipt model."""

import datetime as dt
from decimal import Decimal

from sqlalchemy.orm import Session

from src.database.models import Receipt


def create_receipt(
    db: Session,
    date: dt.date,
    store: str,
    total_amount: Decimal,
    notes: str | None = None,
) -> Receipt:
    """Create a new receipt.

    Args:
        db: Database session
        date: Receipt date
        store: Store name
        total_amount: Total amount
        notes: Optional notes

    Returns:
        The created Receipt
    """
    receipt = Receipt(
        date=date,
        store=store,
        total_amount=total_amount,
        notes=notes,
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt


def get_receipt(db: Session, receipt_id: int) -> Receipt | None:
    """Get a receipt by ID.

    Args:
        db: Database session
        receipt_id: Receipt ID

    Returns:
        Receipt if found, None otherwise
    """
    return db.query(Receipt).filter(Receipt.id == receipt_id).first()


def get_receipts(db: Session) -> list[Receipt]:
    """Get all receipts.

    Args:
        db: Database session

    Returns:
        List of all receipts
    """
    return db.query(Receipt).all()
