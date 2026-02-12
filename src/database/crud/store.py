"""CRUD operations for Store model."""

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.database.models import Store


def create_store(
    db: Session,
    name: str,
    location: str | None = None,
) -> Store:
    """Create a new store.

    Args:
        db: Database session
        name: Store name (must be unique)
        location: Optional store location

    Returns:
        The created Store

    Raises:
        SQLAlchemyError: If database operation fails (e.g., duplicate name)
    """
    store = Store(name=name, location=location)
    try:
        db.add(store)
        db.commit()
        db.refresh(store)
        return store
    except SQLAlchemyError:
        db.rollback()
        raise


def get_store(db: Session, store_id: int) -> Store | None:
    """Get a store by ID.

    Args:
        db: Database session
        store_id: Store ID

    Returns:
        Store if found, None otherwise
    """
    return db.query(Store).filter(Store.id == store_id).first()


def get_stores(
    db: Session,
    limit: int | None = None,
    offset: int | None = None,
) -> list[Store]:
    """Get stores with optional pagination.

    Args:
        db: Database session
        limit: Maximum number of stores to return (None for all)
        offset: Number of stores to skip (None for no offset)

    Returns:
        List of stores ordered by name
    """
    query = db.query(Store).order_by(Store.name.asc())
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    return query.all()
