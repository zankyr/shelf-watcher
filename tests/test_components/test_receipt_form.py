"""Tests for save_receipt() atomic save function."""

import datetime as dt
from decimal import Decimal

import pytest

from src.components.receipt_form import save_receipt, update_receipt
from src.database.models.category import Category
from src.database.models.item import Item
from src.database.models.receipt import Receipt
from src.database.models.store import Store
from src.utils.validators import ItemFormData, ReceiptFormData


def _item(**overrides: object) -> ItemFormData:
    """Create a valid ItemFormData with optional overrides."""
    data: dict = {
        "name": "Milk",
        "quantity": Decimal("1"),
        "unit": "L",
        "total_price": Decimal("2.50"),
    }
    data.update(overrides)
    return ItemFormData(**data)


def _receipt(**overrides: object) -> ReceiptFormData:
    """Create a valid ReceiptFormData with optional overrides."""
    data: dict = {
        "date": dt.date.today(),
        "store": "Lidl",
        "items": [_item()],
    }
    data.update(overrides)
    return ReceiptFormData(**data)


class TestSaveReceipt:
    """Tests for the save_receipt() function."""

    def test_basic_save(self, db_session: object) -> None:
        """Save a receipt with one item and verify all fields."""
        receipt = save_receipt(_receipt(), db=db_session)

        assert receipt.id is not None
        assert receipt.date == dt.date.today()
        assert receipt.store == "Lidl"
        assert receipt.total_amount == Decimal("2.50")

        items = db_session.query(Item).filter(Item.receipt_id == receipt.id).all()
        assert len(items) == 1
        assert items[0].name == "Milk"
        assert items[0].unit == "L"
        assert items[0].total_price == Decimal("2.50")

    def test_multiple_items(self, db_session: object) -> None:
        """Save a receipt with multiple items."""
        items = [
            _item(name="Milk", total_price=Decimal("2.50")),
            _item(name="Bread", quantity=Decimal("1"), unit="units", total_price=Decimal("1.30")),
        ]
        receipt = save_receipt(_receipt(items=items), db=db_session)

        assert receipt.total_amount == Decimal("3.80")
        db_items = db_session.query(Item).filter(Item.receipt_id == receipt.id).all()
        assert len(db_items) == 2

    def test_new_store_auto_created(self, db_session: object) -> None:
        """A new store name should be auto-created in the stores table."""
        save_receipt(_receipt(store="NewMarket"), db=db_session)

        store = db_session.query(Store).filter(Store.name == "NewMarket").first()
        assert store is not None

    def test_existing_store_not_duplicated(self, db_session: object) -> None:
        """An existing store should not be duplicated."""
        db_session.add(Store(name="Lidl"))
        db_session.commit()

        save_receipt(_receipt(store="Lidl"), db=db_session)

        count = db_session.query(Store).filter(Store.name == "Lidl").count()
        assert count == 1

    def test_new_category_created(self, db_session: object) -> None:
        """A new category name should create a category record."""
        item = _item(new_category_name="Dairy")
        receipt = save_receipt(_receipt(items=[item]), db=db_session)

        cat = db_session.query(Category).filter(Category.name == "Dairy").first()
        assert cat is not None

        db_item = db_session.query(Item).filter(Item.receipt_id == receipt.id).first()
        assert db_item.category_id == cat.id

    def test_existing_category_reused(self, db_session: object) -> None:
        """If a category already exists, it should be reused, not duplicated."""
        db_session.add(Category(name="Dairy"))
        db_session.commit()

        item = _item(new_category_name="Dairy")
        save_receipt(_receipt(items=[item]), db=db_session)

        count = db_session.query(Category).filter(Category.name == "Dairy").count()
        assert count == 1

    def test_category_deduplication_within_receipt(self, db_session: object) -> None:
        """Two items requesting the same new category should create it only once."""
        items = [
            _item(name="Milk", new_category_name="Dairy"),
            _item(name="Cheese", new_category_name="Dairy"),
        ]
        save_receipt(_receipt(items=items), db=db_session)

        count = db_session.query(Category).filter(Category.name == "Dairy").count()
        assert count == 1

    def test_normalized_price_calculated(self, db_session: object) -> None:
        """Items should have normalized price and unit set."""
        item = _item(quantity=Decimal("500"), unit="g", total_price=Decimal("3.00"))
        receipt = save_receipt(_receipt(items=[item]), db=db_session)

        db_item = db_session.query(Item).filter(Item.receipt_id == receipt.id).first()
        assert db_item.normalized_unit == "kg"
        assert db_item.normalized_price == Decimal("6.00")

    def test_price_per_unit_calculated(self, db_session: object) -> None:
        """Items should have price_per_unit calculated."""
        item = _item(quantity=Decimal("2"), total_price=Decimal("5.00"))
        receipt = save_receipt(_receipt(items=[item]), db=db_session)

        db_item = db_session.query(Item).filter(Item.receipt_id == receipt.id).first()
        assert db_item.price_per_unit == Decimal("2.50")

    def test_rollback_on_error(self, db_session: object) -> None:
        """If an error occurs during save, the transaction should be rolled back."""
        from unittest.mock import patch

        save_receipt(_receipt(store="TestStore"), db=db_session)
        count_before = db_session.query(Receipt).count()

        # Patch normalize_price to raise an error mid-transaction (after receipt
        # is created but during item processing)
        with patch(
            "src.components.receipt_form.normalize_price",
            side_effect=RuntimeError("Forced error"),
        ):
            with pytest.raises(RuntimeError, match="Forced error"):
                save_receipt(_receipt(store="AnotherStore"), db=db_session)

        # Receipt count should be unchanged — the transaction was rolled back
        assert db_session.query(Receipt).count() == count_before

    def test_notes_saved(self, db_session: object) -> None:
        """Receipt notes should be persisted."""
        receipt = save_receipt(_receipt(notes="Weekly shopping"), db=db_session)
        assert receipt.notes == "Weekly shopping"

    def test_empty_notes_saved_as_none(self, db_session: object) -> None:
        """Empty notes should be stored as None."""
        receipt = save_receipt(_receipt(notes=""), db=db_session)
        assert receipt.notes is None


class TestUpdateReceipt:
    """Tests for the update_receipt() function."""

    def test_basic_update(self, db_session: object) -> None:
        """Updating a receipt changes its fields."""
        receipt = save_receipt(_receipt(store="Lidl", notes="old"), db=db_session)

        updated = update_receipt(
            receipt.id,
            _receipt(store="Albert Heijn", notes="new"),
            db=db_session,
        )

        assert updated.id == receipt.id
        assert updated.store == "Albert Heijn"
        assert updated.notes == "new"

    def test_update_replaces_items(self, db_session: object) -> None:
        """Updating a receipt replaces all old items with new ones."""
        receipt = save_receipt(
            _receipt(items=[_item(name="Milk")]),
            db=db_session,
        )

        update_receipt(
            receipt.id,
            _receipt(items=[_item(name="Bread"), _item(name="Cheese")]),
            db=db_session,
        )

        new_items = db_session.query(Item).filter(Item.receipt_id == receipt.id).all()
        assert len(new_items) == 2
        assert {i.name for i in new_items} == {"Bread", "Cheese"}

    def test_update_nonexistent_raises(self, db_session: object) -> None:
        """Updating a non-existent receipt raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            update_receipt(999, _receipt(), db=db_session)

    def test_update_new_category_created(self, db_session: object) -> None:
        """A new category referenced in the update should be created."""
        receipt = save_receipt(_receipt(), db=db_session)

        update_receipt(
            receipt.id,
            _receipt(items=[_item(new_category_name="Dairy")]),
            db=db_session,
        )

        cat = db_session.query(Category).filter(Category.name == "Dairy").first()
        assert cat is not None

    def test_update_new_store_auto_created(self, db_session: object) -> None:
        """A new store name in the update should be auto-created."""
        receipt = save_receipt(_receipt(store="Lidl"), db=db_session)

        update_receipt(receipt.id, _receipt(store="NewShop"), db=db_session)

        store = db_session.query(Store).filter(Store.name == "NewShop").first()
        assert store is not None

    def test_update_normalized_prices_recalculated(self, db_session: object) -> None:
        """Updated items should have normalized prices recalculated."""
        receipt = save_receipt(_receipt(), db=db_session)

        update_receipt(
            receipt.id,
            _receipt(items=[_item(quantity=Decimal("500"), unit="g", total_price=Decimal("3.00"))]),
            db=db_session,
        )

        item = db_session.query(Item).filter(Item.receipt_id == receipt.id).first()
        assert item.normalized_unit == "kg"
        assert item.normalized_price == Decimal("6.00")

    def test_update_rollback_on_error(self, db_session: object) -> None:
        """If an error occurs during update, the transaction should be rolled back."""
        from unittest.mock import patch

        receipt = save_receipt(_receipt(store="Lidl"), db=db_session)
        original_store = receipt.store

        with patch(
            "src.components.receipt_form.normalize_price",
            side_effect=RuntimeError("Forced error"),
        ):
            with pytest.raises(RuntimeError, match="Forced error"):
                update_receipt(receipt.id, _receipt(store="NewStore"), db=db_session)

        db_session.refresh(receipt)
        assert receipt.store == original_store

    def test_update_total_amount_recalculated(self, db_session: object) -> None:
        """The total_amount should reflect the new items after update."""
        receipt = save_receipt(_receipt(), db=db_session)

        items = [
            _item(name="A", total_price=Decimal("3.00")),
            _item(name="B", total_price=Decimal("7.00")),
        ]
        updated = update_receipt(receipt.id, _receipt(items=items), db=db_session)

        assert updated.total_amount == Decimal("10.00")

    def test_save_with_currency(self, db_session: object) -> None:
        """Save a CHF receipt and verify currency is stored."""
        receipt = save_receipt(_receipt(currency="CHF"), db=db_session)
        assert receipt.currency == "CHF"

    def test_save_default_currency(self, db_session: object) -> None:
        """Verify EUR is the default currency."""
        receipt = save_receipt(_receipt(), db=db_session)
        assert receipt.currency == "EUR"

    def test_update_currency(self, db_session: object) -> None:
        """Changing currency on update should persist."""
        receipt = save_receipt(_receipt(currency="EUR"), db=db_session)
        updated = update_receipt(receipt.id, _receipt(currency="CHF"), db=db_session)
        assert updated.currency == "CHF"

    def test_save_with_original_price(self, db_session: object) -> None:
        """Save an item with original_price and verify it persists."""
        item = _item(total_price=Decimal("2.50"), original_price=Decimal("3.50"))
        receipt = save_receipt(_receipt(items=[item]), db=db_session)

        db_item = db_session.query(Item).filter(Item.receipt_id == receipt.id).first()
        assert db_item.original_price == Decimal("3.50")

    def test_update_with_original_price(self, db_session: object) -> None:
        """Update a receipt and verify original_price on new items."""
        receipt = save_receipt(_receipt(), db=db_session)

        item = _item(total_price=Decimal("2.50"), original_price=Decimal("4.00"))
        update_receipt(receipt.id, _receipt(items=[item]), db=db_session)

        db_item = db_session.query(Item).filter(Item.receipt_id == receipt.id).first()
        assert db_item.original_price == Decimal("4.00")
