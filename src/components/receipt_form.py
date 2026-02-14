"""Receipt entry form component with atomic save."""

from __future__ import annotations

import uuid
from decimal import Decimal, InvalidOperation
from typing import Any

import streamlit as st
from sqlalchemy.orm import Session

from src.database.connection import SessionLocal
from src.database.models.category import Category
from src.database.models.item import Item
from src.database.models.receipt import Receipt
from src.database.models.store import Store
from src.utils.calculations import calculate_price_per_unit, normalize_price
from src.utils.validators import ItemFormData, ReceiptFormData

_NEW_STORE_SENTINEL = "-- Enter new store --"
_NO_CATEGORY = "(none)"
_NEW_CATEGORY_SENTINEL = "-- Create new --"


def _get_store_names() -> list[str]:
    """Fetch existing store names from the database."""
    db = SessionLocal()
    try:
        stores = db.query(Store.name).order_by(Store.name).all()
        return [row[0] for row in stores]
    finally:
        db.close()


def _get_category_options() -> list[dict[str, Any]]:
    """Fetch existing categories as list of dicts (id, name)."""
    db = SessionLocal()
    try:
        categories = db.query(Category.id, Category.name).order_by(Category.name).all()
        return [{"id": row[0], "name": row[1]} for row in categories]
    finally:
        db.close()


def _new_item_dict() -> dict[str, Any]:
    """Create a new empty item dict with a stable UUID key."""
    return {
        "id": str(uuid.uuid4()),
        "name": "",
        "brand": "",
        "category_selection": _NO_CATEGORY,
        "new_category_name": "",
        "quantity": 1.0,
        "unit": "units",
        "total_price": 0.0,
    }


def _resolve_categories_and_store(db: Session, receipt_data: ReceiptFormData) -> None:
    """Resolve new categories (dedup by name) and auto-create the store if needed.

    Mutates ``item_data.category_id`` for items that specify ``new_category_name``.
    """
    category_cache: dict[str, int] = {}
    for item_data in receipt_data.items:
        if item_data.new_category_name:
            name = item_data.new_category_name
            if name not in category_cache:
                existing = db.query(Category).filter(Category.name == name).first()
                if existing:
                    category_cache[name] = existing.id
                else:
                    cat = Category(name=name)
                    db.add(cat)
                    db.flush()
                    category_cache[name] = cat.id
            item_data.category_id = category_cache[name]

    store_name = receipt_data.store
    existing_store = db.query(Store).filter(Store.name == store_name).first()
    if not existing_store:
        db.add(Store(name=store_name))
        db.flush()


def _create_items_for_receipt(db: Session, receipt_id: int, items: list[ItemFormData]) -> None:
    """Create Item rows with price calculation for a receipt."""
    for item_data in items:
        price_per_unit = calculate_price_per_unit(item_data.quantity, item_data.total_price)
        norm_price, norm_unit = normalize_price(
            item_data.quantity, item_data.unit, item_data.total_price
        )

        item = Item(
            receipt_id=receipt_id,
            name=item_data.name,
            brand=item_data.brand or None,
            category_id=item_data.category_id,
            quantity=item_data.quantity,
            unit=item_data.unit,
            price_per_unit=price_per_unit,
            total_price=item_data.total_price,
            normalized_price=norm_price,
            normalized_unit=norm_unit,
        )
        db.add(item)


def save_receipt(receipt_data: ReceiptFormData, db: Session | None = None) -> Receipt:
    """Atomically save a validated receipt with all its items.

    Handles new category creation, new store auto-creation, price normalization,
    and price-per-unit calculation. Uses a single commit for atomicity.

    Args:
        receipt_data: Validated receipt form data.
        db: Optional database session (for testing). Creates one if not provided.

    Returns:
        The created Receipt object.

    Raises:
        Exception: Re-raises any exception after rolling back the transaction.
    """
    owns_session = db is None
    if owns_session:
        db = SessionLocal()
    assert db is not None  # guaranteed after conditional above

    try:
        _resolve_categories_and_store(db, receipt_data)

        receipt = Receipt(
            date=receipt_data.date,
            store=receipt_data.store,
            total_amount=receipt_data.total_amount,
            notes=receipt_data.notes or None,
        )
        db.add(receipt)
        db.flush()

        _create_items_for_receipt(db, receipt.id, receipt_data.items)

        db.commit()
        db.refresh(receipt)
        return receipt

    except Exception:
        db.rollback()
        raise
    finally:
        if owns_session:
            db.close()


def update_receipt(
    receipt_id: int, receipt_data: ReceiptFormData, db: Session | None = None
) -> Receipt:
    """Atomically update an existing receipt and replace all its items.

    Args:
        receipt_id: ID of the receipt to update.
        receipt_data: Validated receipt form data with new values.
        db: Optional database session (for testing). Creates one if not provided.

    Returns:
        The updated Receipt object.

    Raises:
        ValueError: If the receipt does not exist.
        Exception: Re-raises any exception after rolling back the transaction.
    """
    owns_session = db is None
    if owns_session:
        db = SessionLocal()
    assert db is not None

    try:
        receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
        if receipt is None:
            raise ValueError(f"Receipt with id {receipt_id} not found")

        _resolve_categories_and_store(db, receipt_data)

        # Update receipt fields
        receipt.date = receipt_data.date
        receipt.store = receipt_data.store
        receipt.total_amount = receipt_data.total_amount
        receipt.notes = receipt_data.notes or None

        # Delete all old items, then recreate
        db.query(Item).filter(Item.receipt_id == receipt_id).delete()
        db.flush()

        _create_items_for_receipt(db, receipt_id, receipt_data.items)

        db.commit()
        db.refresh(receipt)
        return receipt

    except Exception:
        db.rollback()
        raise
    finally:
        if owns_session:
            db.close()


_EDIT_STATE_KEYS = (
    "editing_receipt_id",
    "_edit_loaded",
    "edit_receipt_date",
    "edit_receipt_store",
    "edit_receipt_notes",
)


def _clear_edit_state() -> None:
    """Remove all edit-mode keys from session state."""
    for key in _EDIT_STATE_KEYS:
        st.session_state.pop(key, None)


def _load_receipt_into_session_state(receipt_id: int) -> None:
    """Fetch a receipt from the DB and populate session state for edit mode."""
    db = SessionLocal()
    try:
        receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
        if receipt is None:
            _clear_edit_state()
            st.session_state["error_message"] = f"Receipt #{receipt_id} not found."
            return

        st.session_state["edit_receipt_date"] = receipt.date
        st.session_state["edit_receipt_store"] = receipt.store
        st.session_state["edit_receipt_notes"] = receipt.notes or ""

        item_dicts: list[dict[str, Any]] = []
        for item in receipt.items:
            cat_name = _NO_CATEGORY
            if item.category is not None:
                cat_name = item.category.name
            item_dicts.append(
                {
                    "id": str(uuid.uuid4()),
                    "name": item.name,
                    "brand": item.brand or "",
                    "category_selection": cat_name,
                    "new_category_name": "",
                    "quantity": float(item.quantity),
                    "unit": item.unit,
                    "total_price": float(item.total_price),
                }
            )

        st.session_state["items"] = item_dicts if item_dicts else [_new_item_dict()]
        st.session_state["_edit_loaded"] = True
    finally:
        db.close()


def render_receipt_form() -> None:
    """Render the receipt entry form in Streamlit."""
    # Detect edit mode
    editing_id: int | None = st.session_state.get("editing_receipt_id")
    is_edit = editing_id is not None

    # Load receipt data once when entering edit mode
    if is_edit and not st.session_state.get("_edit_loaded"):
        assert editing_id is not None
        _load_receipt_into_session_state(editing_id)
        # Re-check — _load may have cleared edit state on error
        if not st.session_state.get("editing_receipt_id"):
            is_edit = False

    # Initialize session state (Streamlit's session_state uses dynamic attributes)
    if "items" not in st.session_state:
        st.session_state["items"] = [_new_item_dict()]
    if "success_message" not in st.session_state:
        st.session_state["success_message"] = None
    if "error_message" not in st.session_state:
        st.session_state["error_message"] = None

    # Cancel edit button
    if is_edit:
        if st.button("Cancel edit"):
            _clear_edit_state()
            st.session_state["items"] = [_new_item_dict()]
            st.rerun()

    # Show feedback messages
    if st.session_state["success_message"]:
        st.success(st.session_state["success_message"])
        st.session_state["success_message"] = None
    if st.session_state["error_message"]:
        st.error(st.session_state["error_message"])
        st.session_state["error_message"] = None

    # Load options
    store_names = _get_store_names()
    category_options = _get_category_options()
    category_names = [_NO_CATEGORY, _NEW_CATEGORY_SENTINEL] + [c["name"] for c in category_options]
    category_name_to_id = {c["name"]: c["id"] for c in category_options}

    # --- Receipt header ---
    # Pre-fill defaults for edit mode
    default_date = st.session_state.get("edit_receipt_date", "today") if is_edit else "today"
    edit_store = st.session_state.get("edit_receipt_store", "") if is_edit else ""
    default_notes = st.session_state.get("edit_receipt_notes", "") if is_edit else ""

    col_date, col_store = st.columns(2)
    with col_date:
        receipt_date = st.date_input("Date", value=default_date)
    with col_store:
        store_options = store_names + [_NEW_STORE_SENTINEL]
        # In edit mode, pre-select the store if it exists in the list
        store_index = None
        if is_edit and edit_store in store_options:
            store_index = store_options.index(edit_store)
        store_selection = st.selectbox(
            "Store", options=store_options, index=store_index, placeholder="Select a store..."
        )
        new_store_name = ""
        if store_selection == _NEW_STORE_SENTINEL:
            new_store_name = st.text_input("New store name")

    # --- Items section ---
    st.subheader("Items")

    items_to_remove: list[int] = []
    for idx, item_state in enumerate(st.session_state["items"]):
        item_id = item_state["id"]
        cols = st.columns([3, 2, 2, 1.5, 1.5, 1.5, 0.5])

        with cols[0]:
            item_state["name"] = st.text_input(
                "Name", value=item_state["name"], key=f"name_{item_id}"
            )
        with cols[1]:
            item_state["brand"] = st.text_input(
                "Brand", value=item_state["brand"], key=f"brand_{item_id}"
            )
        with cols[2]:
            cat_idx = 0
            if item_state["category_selection"] in category_names:
                cat_idx = category_names.index(item_state["category_selection"])
            item_state["category_selection"] = st.selectbox(
                "Category", options=category_names, index=cat_idx, key=f"cat_{item_id}"
            )
            if item_state["category_selection"] == _NEW_CATEGORY_SENTINEL:
                item_state["new_category_name"] = st.text_input(
                    "New category",
                    value=item_state.get("new_category_name", ""),
                    key=f"newcat_{item_id}",
                )
        with cols[3]:
            item_state["quantity"] = st.number_input(
                "Qty",
                value=item_state["quantity"],
                min_value=0.001,
                step=0.1,
                format="%.3f",
                key=f"qty_{item_id}",
            )
        with cols[4]:
            unit_options = ["kg", "g", "L", "ml", "units"]
            unit_idx = (
                unit_options.index(item_state["unit"]) if item_state["unit"] in unit_options else 4
            )
            item_state["unit"] = st.selectbox(
                "Unit", options=unit_options, index=unit_idx, key=f"unit_{item_id}"
            )
        with cols[5]:
            item_state["total_price"] = st.number_input(
                "Price",
                value=item_state["total_price"],
                min_value=0.0,
                step=0.01,
                format="%.2f",
                key=f"price_{item_id}",
            )
        with cols[6]:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("\U0001f5d1", key=f"del_{item_id}", help="Remove item"):
                items_to_remove.append(idx)

    # Remove items (in reverse order to preserve indices)
    for idx in sorted(items_to_remove, reverse=True):
        if len(st.session_state["items"]) > 1:
            st.session_state["items"].pop(idx)
            st.rerun()

    if st.button("+ Add Item"):
        st.session_state["items"].append(_new_item_dict())
        st.rerun()

    # --- Total and notes ---
    col_total, col_notes = st.columns(2)
    with col_total:
        total = sum(item["total_price"] for item in st.session_state["items"])
        st.metric("Total", f"\u20ac{total:.2f}")
    with col_notes:
        receipt_notes = st.text_area("Notes", value=default_notes, height=80)

    # --- Save / Update ---
    button_label = "Update Receipt" if is_edit else "Save Receipt"
    if st.button(button_label, type="primary"):
        # Determine store name
        store = new_store_name if store_selection == _NEW_STORE_SENTINEL else store_selection
        if not store:
            st.session_state["error_message"] = "Please select or enter a store name."
            st.rerun()
            return

        # Build item data
        try:
            item_form_data = []
            for item_state in st.session_state["items"]:
                cat_selection = item_state["category_selection"]
                category_id = None
                new_cat_name = ""
                if cat_selection not in (_NO_CATEGORY, _NEW_CATEGORY_SENTINEL):
                    category_id = category_name_to_id.get(cat_selection)
                elif cat_selection == _NEW_CATEGORY_SENTINEL:
                    new_cat_name = item_state.get("new_category_name", "")

                item_form_data.append(
                    ItemFormData(
                        name=item_state["name"],
                        brand=item_state["brand"],
                        category_id=category_id,
                        new_category_name=new_cat_name,
                        quantity=Decimal(str(item_state["quantity"])),
                        unit=item_state["unit"],
                        total_price=Decimal(str(item_state["total_price"])),
                    )
                )

            receipt_form = ReceiptFormData(
                date=receipt_date,
                store=store,
                notes=receipt_notes,
                items=item_form_data,
            )
        except (ValueError, InvalidOperation) as e:
            st.session_state["error_message"] = f"Validation error: {e}"
            st.rerun()
            return

        try:
            if is_edit:
                assert editing_id is not None
                receipt = update_receipt(editing_id, receipt_form)
                _clear_edit_state()
                st.session_state["items"] = [_new_item_dict()]
                st.session_state["success_message"] = (
                    f"Receipt updated! (ID: {receipt.id}, "
                    f"Total: \u20ac{receipt.total_amount:.2f})"
                )
            else:
                receipt = save_receipt(receipt_form)
                st.session_state["items"] = [_new_item_dict()]
                st.session_state["success_message"] = (
                    f"Receipt saved! (ID: {receipt.id}, "
                    f"Total: \u20ac{receipt.total_amount:.2f})"
                )
            st.rerun()
        except Exception as e:
            action = "updating" if is_edit else "saving"
            st.session_state["error_message"] = f"Error {action} receipt: {e}"
            st.rerun()
