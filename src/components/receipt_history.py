"""Receipt history browser with filters, expanders, and CSV export."""

from __future__ import annotations

import streamlit as st
from sqlalchemy.orm import Session

from src.database.connection import SessionLocal
from src.utils.queries import (
    get_distinct_store_names,
    get_filtered_items_export,
    get_receipt_items,
    get_receipt_list,
    parse_date_range,
)


def render_receipt_history() -> None:
    """Render the receipt history page with filters and inline detail expanders."""
    db = SessionLocal()
    try:
        _render_filters_and_list(db)
    finally:
        db.close()


def _render_filters_and_list(db: Session) -> None:
    """Render filter controls and receipt list."""
    # --- Filter controls ---
    store_names = get_distinct_store_names(db)

    col_date, col_store, col_search = st.columns([2, 2, 2])
    with col_date:
        date_range = st.date_input(
            "Date range", value=[], help="Select start and end dates"  # type: ignore[arg-type]
        )
    with col_store:
        selected_stores = st.multiselect("Store", options=store_names)
    with col_search:
        item_search = st.text_input("Search items", placeholder="e.g. milk, bread...")

    col_sort, col_dir, _ = st.columns([2, 1, 3])
    with col_sort:
        sort_by = st.selectbox("Sort by", options=["date", "total", "store"], index=0)
    with col_dir:
        sort_desc = st.checkbox("Descending", value=True)

    # Parse filter values
    date_from, date_to = parse_date_range(date_range)

    # --- Query receipts ---
    df = get_receipt_list(
        db,
        date_from=date_from,
        date_to=date_to,
        stores=selected_stores or None,
        item_search=item_search or None,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    # --- Header row with count and export ---
    col_count, col_export = st.columns([3, 1])
    with col_count:
        st.markdown(f"**Showing {len(df)} receipt{'s' if len(df) != 1 else ''}**")
    with col_export:
        if len(df) > 0:
            export_df = get_filtered_items_export(
                db,
                date_from=date_from,
                date_to=date_to,
                stores=selected_stores or None,
                item_search=item_search or None,
            )
            st.download_button(
                "Download CSV",
                data=export_df.to_csv(index=False),
                file_name="receipt_items.csv",
                mime="text/csv",
            )

    # --- Receipt list ---
    if len(df) == 0:
        st.info("No receipts found. Try adjusting your filters or add a receipt first.")
        return

    for _, row in df.iterrows():
        receipt_id = int(row["receipt_id"])
        date_str = str(row["date"])
        store = row["store"]
        total = float(row["total_amount"])
        item_count = int(row["item_count"])
        notes = row["notes"]

        label = (
            f"{date_str} | {store} | "
            f"\u20ac{total:.2f} | "
            f"{item_count} item{'s' if item_count != 1 else ''}"
        )
        with st.expander(label):
            items_df = get_receipt_items(db, receipt_id)
            if len(items_df) > 0:
                display_df = items_df.drop(columns=["item_id"])
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.caption("No items recorded.")
            if notes:
                st.caption(f"Notes: {notes}")
