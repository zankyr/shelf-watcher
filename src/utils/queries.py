"""Analytics query functions returning pandas DataFrames.

All functions accept a SQLAlchemy Session and return DataFrames.
No Streamlit dependencies — fully testable in isolation.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.database.models.category import Category
from src.database.models.item import Item
from src.database.models.receipt import Receipt


def get_receipt_list(
    db: Session,
    *,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    stores: list[str] | None = None,
    item_search: str | None = None,
    sort_by: str = "date",
    sort_desc: bool = True,
) -> pd.DataFrame:
    """Get a summary list of receipts with item counts.

    Args:
        db: Database session.
        date_from: Inclusive start date filter.
        date_to: Inclusive end date filter.
        stores: List of store names to include.
        item_search: Substring match on item names (case-insensitive).
        sort_by: Column to sort by — "date", "total", or "store".
        sort_desc: Sort descending if True.

    Returns:
        DataFrame with columns: receipt_id, date, store, total_amount, item_count, notes.
    """
    item_count = func.count(Item.id).label("item_count")
    stmt = (
        select(
            Receipt.id.label("receipt_id"),
            Receipt.date,
            Receipt.store,
            Receipt.currency,
            Receipt.total_amount,
            item_count,
            Receipt.notes,
        )
        .outerjoin(Item, Item.receipt_id == Receipt.id)
        .group_by(Receipt.id)
    )

    if date_from is not None:
        stmt = stmt.where(Receipt.date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Receipt.date <= date_to)
    if stores:
        stmt = stmt.where(Receipt.store.in_(stores))
    if item_search:
        # EXISTS subquery avoids affecting the item_count aggregation
        exists_sub = (
            select(Item.id)
            .where(Item.receipt_id == Receipt.id)
            .where(func.lower(Item.name).contains(item_search.lower()))
            .correlate(Receipt)
            .exists()
        )
        stmt = stmt.where(exists_sub)

    sort_map = {
        "date": Receipt.date,
        "total": Receipt.total_amount,
        "store": Receipt.store,
    }
    sort_col = sort_map.get(sort_by, Receipt.date)
    stmt = stmt.order_by(sort_col.desc() if sort_desc else sort_col.asc())

    return pd.read_sql(stmt, db.bind)


def get_receipt_items(db: Session, receipt_id: int) -> pd.DataFrame:
    """Get all items for a specific receipt.

    Returns:
        DataFrame with columns: item_id, name, brand, category, quantity, unit,
        price_per_unit, total_price, normalized_price, normalized_unit.
    """
    stmt = (
        select(
            Item.id.label("item_id"),
            Item.name,
            Item.brand,
            Category.name.label("category"),
            Item.quantity,
            Item.unit,
            Item.price_per_unit,
            Item.total_price,
            Item.normalized_price,
            Item.normalized_unit,
        )
        .outerjoin(Category, Item.category_id == Category.id)
        .where(Item.receipt_id == receipt_id)
    )
    return pd.read_sql(stmt, db.bind)


def get_filtered_items_export(
    db: Session,
    *,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    stores: list[str] | None = None,
    item_search: str | None = None,
) -> pd.DataFrame:
    """Get denormalized item data for CSV export.

    One row per item, with receipt fields repeated.

    Returns:
        DataFrame with columns: date, store, item_name, brand, category, quantity,
        unit, price_per_unit, total_price, normalized_price, normalized_unit, notes.
    """
    stmt = (
        select(
            Receipt.date,
            Receipt.store,
            Receipt.currency,
            Item.name.label("item_name"),
            Item.brand,
            Category.name.label("category"),
            Item.quantity,
            Item.unit,
            Item.price_per_unit,
            Item.total_price,
            Item.normalized_price,
            Item.normalized_unit,
            Receipt.notes,
        )
        .join(Item, Item.receipt_id == Receipt.id)
        .outerjoin(Category, Item.category_id == Category.id)
    )

    if date_from is not None:
        stmt = stmt.where(Receipt.date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Receipt.date <= date_to)
    if stores:
        stmt = stmt.where(Receipt.store.in_(stores))
    if item_search:
        stmt = stmt.where(func.lower(Item.name).contains(item_search.lower()))

    stmt = stmt.order_by(Receipt.date.desc(), Item.name)
    return pd.read_sql(stmt, db.bind)


def get_price_trends(
    db: Session,
    *,
    item_names: list[str] | None = None,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> pd.DataFrame:
    """Get price data over time for selected items.

    Returns:
        DataFrame with columns: date, item_name, store, normalized_price, normalized_unit.
    """
    stmt = (
        select(
            Receipt.date,
            Item.name.label("item_name"),
            Receipt.store,
            Item.normalized_price,
            Item.normalized_unit,
        )
        .join(Item, Item.receipt_id == Receipt.id)
        .where(Item.normalized_price.isnot(None))
    )

    if item_names:
        lower_names = [n.lower() for n in item_names]
        stmt = stmt.where(func.lower(Item.name).in_(lower_names))
    if date_from is not None:
        stmt = stmt.where(Receipt.date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Receipt.date <= date_to)

    stmt = stmt.order_by(Receipt.date)
    return pd.read_sql(stmt, db.bind)


def get_store_comparison(
    db: Session,
    *,
    item_names: list[str] | None = None,
    category_id: int | None = None,
) -> pd.DataFrame:
    """Get price statistics grouped by store.

    Returns:
        DataFrame with columns: store, avg_normalized_price, min_normalized_price,
        max_normalized_price, purchase_count.
    """
    stmt = (
        select(
            Receipt.store,
            func.round(func.avg(Item.normalized_price), 2).label("avg_normalized_price"),
            func.min(Item.normalized_price).label("min_normalized_price"),
            func.max(Item.normalized_price).label("max_normalized_price"),
            func.count(Item.id).label("purchase_count"),
        )
        .join(Item, Item.receipt_id == Receipt.id)
        .where(Item.normalized_price.isnot(None))
        .group_by(Receipt.store)
    )

    if item_names:
        lower_names = [n.lower() for n in item_names]
        stmt = stmt.where(func.lower(Item.name).in_(lower_names))
    if category_id is not None:
        stmt = stmt.where(Item.category_id == category_id)

    return pd.read_sql(stmt, db.bind)


def get_category_spending(
    db: Session,
    *,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> pd.DataFrame:
    """Get total spending grouped by category.

    Returns:
        DataFrame with columns: category, total_spent, item_count.
    """
    cat_label = func.coalesce(Category.name, "Uncategorized").label("category")
    stmt = (
        select(
            cat_label,
            func.round(func.sum(Item.total_price), 2).label("total_spent"),
            func.count(Item.id).label("item_count"),
        )
        .select_from(Receipt)
        .join(Item, Item.receipt_id == Receipt.id)
        .outerjoin(Category, Item.category_id == Category.id)
        .group_by(cat_label)
    )

    if date_from is not None:
        stmt = stmt.where(Receipt.date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Receipt.date <= date_to)

    return pd.read_sql(stmt, db.bind)


def get_monthly_spending(
    db: Session,
    *,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> pd.DataFrame:
    """Get spending by month and category.

    Returns:
        DataFrame with columns: month (YYYY-MM), category, total_spent.
    """
    month_label = func.strftime("%Y-%m", Receipt.date).label("month")
    cat_label = func.coalesce(Category.name, "Uncategorized").label("category")
    stmt = (
        select(
            month_label,
            cat_label,
            func.round(func.sum(Item.total_price), 2).label("total_spent"),
        )
        .join(Item, Item.receipt_id == Receipt.id)
        .outerjoin(Category, Item.category_id == Category.id)
        .group_by(month_label, cat_label)
    )

    if date_from is not None:
        stmt = stmt.where(Receipt.date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Receipt.date <= date_to)

    stmt = stmt.order_by(month_label)
    return pd.read_sql(stmt, db.bind)


def get_distinct_item_names(db: Session) -> list[str]:
    """Get all distinct item names for multiselect dropdowns."""
    stmt = select(func.distinct(Item.name)).order_by(Item.name)
    result = db.execute(stmt).scalars().all()
    return list(result)


def get_distinct_store_names(db: Session) -> list[str]:
    """Get all distinct store names from receipts (only stores with data)."""
    stmt = select(func.distinct(Receipt.store)).order_by(Receipt.store)
    result = db.execute(stmt).scalars().all()
    return list(result)


def parse_date_range(
    date_input: tuple[()] | tuple[dt.date] | tuple[dt.date, dt.date] | dt.date,
) -> tuple[dt.date | None, dt.date | None]:
    """Parse Streamlit's date_input return value into (date_from, date_to).

    Streamlit's date_input can return:
    - A single date (when not a range)
    - An empty tuple (no selection)
    - A single-element tuple (start date only)
    - A two-element tuple (start and end date)

    Returns:
        Tuple of (date_from, date_to), either or both may be None.
    """
    if isinstance(date_input, dt.date):
        return (date_input, date_input)
    if not date_input:
        return (None, None)
    if len(date_input) == 1:
        return (date_input[0], None)
    return (date_input[0], date_input[1])
