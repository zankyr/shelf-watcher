"""CRUD operations for Category model."""

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.database.models import Category


def create_category(
    db: Session,
    name: str,
    parent_id: int | None = None,
    icon: str | None = None,
    color: str | None = None,
) -> Category:
    """Create a new category.

    Args:
        db: Database session
        name: Category name (must be unique)
        parent_id: Optional parent category ID for hierarchy
        icon: Optional emoji or icon identifier
        color: Optional hex color code (e.g., '#FF5733')

    Returns:
        The created Category

    Raises:
        SQLAlchemyError: If database operation fails (e.g., duplicate name)
    """
    category = Category(name=name, parent_id=parent_id, icon=icon, color=color)
    try:
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    except SQLAlchemyError:
        db.rollback()
        raise


def get_category(db: Session, category_id: int) -> Category | None:
    """Get a category by ID.

    Args:
        db: Database session
        category_id: Category ID

    Returns:
        Category if found, None otherwise
    """
    return db.query(Category).filter(Category.id == category_id).first()


def get_categories(
    db: Session,
    parent_id: int | None = None,
    top_level_only: bool = False,
    limit: int | None = None,
    offset: int | None = None,
) -> list[Category]:
    """Get categories with optional filtering and pagination.

    Args:
        db: Database session
        parent_id: Filter by parent category ID
        top_level_only: If True, only return categories with no parent
        limit: Maximum number of categories to return (None for all)
        offset: Number of categories to skip (None for no offset)

    Returns:
        List of categories ordered by name
    """
    query = db.query(Category)
    if top_level_only:
        query = query.filter(Category.parent_id.is_(None))
    elif parent_id is not None:
        query = query.filter(Category.parent_id == parent_id)
    query = query.order_by(Category.name.asc())
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    return query.all()
