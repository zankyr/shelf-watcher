"""CRUD operations for Item model."""

from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.database.models import Item


def create_item(
    db: Session,
    receipt_id: int,
    name: str,
    quantity: Decimal,
    unit: str,
    total_price: Decimal,
    brand: str | None = None,
    category_id: int | None = None,
    price_per_unit: Decimal | None = None,
    normalized_price: Decimal | None = None,
    normalized_unit: str | None = None,
    notes: str | None = None,
) -> Item:
    """Create a new item on a receipt.

    Args:
        db: Database session
        receipt_id: ID of the parent receipt
        name: Item name
        quantity: Quantity purchased
        unit: Unit of measurement (kg, g, L, ml, units)
        total_price: Total price paid
        brand: Optional brand name
        category_id: Optional category ID
        price_per_unit: Optional price per unit
        normalized_price: Optional normalized price (per kg or L)
        normalized_unit: Optional normalized unit (kg or L)
        notes: Optional notes

    Returns:
        The created Item

    Raises:
        SQLAlchemyError: If database operation fails
    """
    item = Item(
        receipt_id=receipt_id,
        name=name,
        quantity=quantity,
        unit=unit,
        total_price=total_price,
        brand=brand,
        category_id=category_id,
        price_per_unit=price_per_unit,
        normalized_price=normalized_price,
        normalized_unit=normalized_unit,
        notes=notes,
    )
    try:
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    except SQLAlchemyError:
        db.rollback()
        raise


def get_item(db: Session, item_id: int) -> Item | None:
    """Get an item by ID.

    Args:
        db: Database session
        item_id: Item ID

    Returns:
        Item if found, None otherwise
    """
    return db.query(Item).filter(Item.id == item_id).first()


def get_items(
    db: Session,
    receipt_id: int | None = None,
    category_id: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[Item]:
    """Get items with optional filtering and pagination.

    Args:
        db: Database session
        receipt_id: Filter by receipt ID
        category_id: Filter by category ID
        limit: Maximum number of items to return (None for all)
        offset: Number of items to skip (None for no offset)

    Returns:
        List of items ordered by name ascending
    """
    query = db.query(Item)
    if receipt_id is not None:
        query = query.filter(Item.receipt_id == receipt_id)
    if category_id is not None:
        query = query.filter(Item.category_id == category_id)
    query = query.order_by(Item.name.asc())
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    return query.all()
