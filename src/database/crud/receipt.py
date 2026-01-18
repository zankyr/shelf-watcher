"""CRUD operations for Receipt model."""

import datetime as dt
from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError
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

    Raises:
        SQLAlchemyError: If database operation fails
    """
    receipt = Receipt(
        date=date,
        store=store,
        total_amount=total_amount,
        notes=notes,
    )
    try:
        db.add(receipt)
        db.commit()
        db.refresh(receipt)
        return receipt
    except SQLAlchemyError:
        db.rollback()
        raise


def get_receipt(db: Session, receipt_id: int) -> Receipt | None:
    """Get a receipt by ID.

    Args:
        db: Database session
        receipt_id: Receipt ID

    Returns:
        Receipt if found, None otherwise
    """
    return db.query(Receipt).filter(Receipt.id == receipt_id).first()


def get_receipts(
    db: Session,
    limit: int | None = None,
    offset: int | None = None,
    order_by_date_desc: bool = True,
) -> list[Receipt]:
    """Get receipts with optional pagination and ordering.

    Args:
        db: Database session
        limit: Maximum number of receipts to return (None for all)
        offset: Number of receipts to skip (None for no offset)
        order_by_date_desc: Order by date descending if True (default), ascending if False

    Returns:
        List of receipts
    """
    query = db.query(Receipt)
    if order_by_date_desc:
        query = query.order_by(Receipt.date.desc())
    else:
        query = query.order_by(Receipt.date.asc())
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    return query.all()
