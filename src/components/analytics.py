"""Analytics dashboard with four tabbed Plotly charts."""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy.orm import Session

from src.database.connection import SessionLocal
from src.database.models.category import Category
from src.utils.queries import (
    get_category_spending,
    get_distinct_item_names,
    get_monthly_spending,
    get_price_trends,
    get_store_comparison,
    parse_date_range,
)
from src.utils.validators import VALID_CURRENCIES


def render_analytics() -> None:
    """Render the analytics dashboard with four tabs."""
    db = SessionLocal()
    try:
        _render_tabs(db)
    finally:
        db.close()


def _render_tabs(db: Session) -> None:
    """Render the four analytics tabs."""
    currency = st.selectbox("Currency", options=list(VALID_CURRENCIES), key="analytics_currency")

    tab_trends, tab_stores, tab_categories, tab_monthly = st.tabs(
        ["Price Trends", "Store Comparison", "Category Spending", "Monthly Summary"]
    )

    with tab_trends:
        _render_price_trends(db, currency)
    with tab_stores:
        _render_store_comparison(db, currency)
    with tab_categories:
        _render_category_spending(db, currency)
    with tab_monthly:
        _render_monthly_summary(db, currency)


def _render_price_trends(db: Session, currency: str) -> None:
    """Tab 1: Price trends over time."""
    item_names = get_distinct_item_names(db)
    if not item_names:
        st.info("No items in the database yet. Add some receipts first.")
        return

    col_items, col_dates = st.columns([3, 2])
    with col_items:
        selected_items = st.multiselect("Select items", options=item_names, key="trends_items")
    with col_dates:
        date_range = st.date_input(
            "Date range", value=[], key="trends_dates"  # type: ignore[arg-type]
        )

    if not selected_items:
        st.info("Select one or more items to see price trends.")
        return

    date_from, date_to = parse_date_range(date_range)
    df = get_price_trends(
        db, item_names=selected_items, date_from=date_from, date_to=date_to, currency=currency
    )

    if len(df) == 0:
        st.warning("No price data found for the selected items and date range.")
        return

    fig = px.line(
        df,
        x="date",
        y="normalized_price",
        color="item_name",
        markers=True,
        hover_data=["store", "normalized_unit"],
        labels={
            "date": "Date",
            "normalized_price": "Price",
            "item_name": "Item",
        },
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)


def _render_store_comparison(db: Session, currency: str) -> None:
    """Tab 2: Store price comparison."""
    item_names = get_distinct_item_names(db)
    categories = _get_categories(db)

    filter_mode = st.radio(
        "Filter by", options=["Items", "Category"], horizontal=True, key="store_filter_mode"
    )

    selected_items: list[str] | None = None
    category_id: int | None = None

    if filter_mode == "Items":
        if not item_names:
            st.info("No items in the database yet.")
            return
        selected_items = st.multiselect("Select items", options=item_names, key="store_items")
        if not selected_items:
            st.info("Select one or more items to compare store prices.")
            return
    else:
        if not categories:
            st.info("No categories in the database yet.")
            return
        cat_name = st.selectbox(
            "Select category",
            options=[c["name"] for c in categories],
            key="store_category",
        )
        if cat_name:
            category_id = int(next(c["id"] for c in categories if c["name"] == cat_name))

    df = get_store_comparison(
        db, item_names=selected_items, category_id=category_id, currency=currency
    )

    if len(df) == 0:
        st.warning("No price data found for the selected filters.")
        return

    fig = px.bar(
        df,
        x="store",
        y="avg_normalized_price",
        error_y=df["max_normalized_price"] - df["avg_normalized_price"],
        error_y_minus=df["avg_normalized_price"] - df["min_normalized_price"],
        text="purchase_count",
        labels={
            "store": "Store",
            "avg_normalized_price": "Avg Price",
            "purchase_count": "Purchases",
        },
    )
    fig.update_traces(texttemplate="%{text} purchases", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)


def _render_category_spending(db: Session, currency: str) -> None:
    """Tab 3: Category spending breakdown."""
    date_range = st.date_input("Date range", value=[], key="cat_dates")  # type: ignore[arg-type]
    date_from, date_to = parse_date_range(date_range)

    df = get_category_spending(db, date_from=date_from, date_to=date_to, currency=currency)

    if len(df) == 0:
        st.warning("No spending data found for the selected date range.")
        return

    fig = px.pie(
        df,
        names="category",
        values="total_spent",
        hole=0.3,
    )
    fig.update_traces(
        textinfo="label+percent+value", texttemplate="%{label}<br>%{percent}<br>%{value:.2f}"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_monthly_summary(db: Session, currency: str) -> None:
    """Tab 4: Monthly spending summary."""
    date_range = st.date_input(
        "Date range", value=[], key="monthly_dates"  # type: ignore[arg-type]
    )
    date_from, date_to = parse_date_range(date_range)

    df = get_monthly_spending(db, date_from=date_from, date_to=date_to, currency=currency)

    if len(df) == 0:
        st.warning("No spending data found for the selected date range.")
        return

    # Stacked bar chart by category
    fig = px.bar(
        df,
        x="month",
        y="total_spent",
        color="category",
        labels={
            "month": "Month",
            "total_spent": "Spending",
            "category": "Category",
        },
    )

    # Add total spending trend line
    monthly_totals = df.groupby("month")["total_spent"].sum().reset_index()
    fig.add_trace(
        go.Scatter(
            x=monthly_totals["month"],
            y=monthly_totals["total_spent"],
            mode="lines+markers",
            name="Total",
            line={"color": "black", "width": 2, "dash": "dot"},
        )
    )

    fig.update_layout(barmode="stack")
    st.plotly_chart(fig, use_container_width=True)


def _get_categories(db: Session) -> list[dict[str, int | str]]:
    """Fetch categories for filter dropdowns."""
    cats = db.query(Category.id, Category.name).order_by(Category.name).all()
    return [{"id": row[0], "name": row[1]} for row in cats]
