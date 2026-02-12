"""Unit tests for Item model."""

import datetime as dt
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from src.database.models import Category, Item, Receipt


def _create_receipt(db_session):
    """Helper to create a receipt for item tests."""
    receipt = Receipt(date=dt.date(2024, 1, 15), store="Test Store", total_amount=Decimal("25.00"))
    db_session.add(receipt)
    db_session.commit()
    return receipt


def _create_category(db_session):
    """Helper to create a category for item tests."""
    category = Category(name="Dairy")
    db_session.add(category)
    db_session.commit()
    return category


class TestItemCreation:
    """Tests for creating Item records."""

    def test_create_item_with_required_fields(self, db_session) -> None:
        """Test creating an item with only required fields."""
        receipt = _create_receipt(db_session)
        item = Item(
            receipt_id=receipt.id,
            name="Whole Milk",
            quantity=Decimal("1.000"),
            unit="L",
            total_price=Decimal("2.50"),
        )
        db_session.add(item)
        db_session.commit()

        assert item.id is not None
        assert item.receipt_id == receipt.id
        assert item.name == "Whole Milk"
        assert item.quantity == Decimal("1.000")
        assert item.unit == "L"
        assert item.total_price == Decimal("2.50")
        assert item.brand is None
        assert item.category_id is None
        assert item.price_per_unit is None
        assert item.normalized_price is None
        assert item.normalized_unit is None
        assert item.notes is None

    def test_create_item_with_all_fields(self, db_session) -> None:
        """Test creating an item with all fields."""
        receipt = _create_receipt(db_session)
        category = _create_category(db_session)
        item = Item(
            receipt_id=receipt.id,
            name="Organic Milk",
            brand="Farm Fresh",
            category_id=category.id,
            quantity=Decimal("2.000"),
            unit="L",
            price_per_unit=Decimal("1.75"),
            total_price=Decimal("3.50"),
            normalized_price=Decimal("1.75"),
            normalized_unit="L",
            notes="On sale",
        )
        db_session.add(item)
        db_session.commit()

        assert item.id is not None
        assert item.brand == "Farm Fresh"
        assert item.category_id == category.id
        assert item.price_per_unit == Decimal("1.75")
        assert item.normalized_price == Decimal("1.75")
        assert item.normalized_unit == "L"
        assert item.notes == "On sale"

    def test_create_multiple_items(self, db_session) -> None:
        """Test creating multiple items on a receipt."""
        receipt = _create_receipt(db_session)
        item1 = Item(
            receipt_id=receipt.id,
            name="Milk",
            quantity=Decimal("1.000"),
            unit="L",
            total_price=Decimal("2.50"),
        )
        item2 = Item(
            receipt_id=receipt.id,
            name="Bread",
            quantity=Decimal("1.000"),
            unit="units",
            total_price=Decimal("3.00"),
        )
        db_session.add_all([item1, item2])
        db_session.commit()

        assert item1.id != item2.id
        assert db_session.query(Item).count() == 2


class TestItemRelationships:
    """Tests for Item foreign key relationships."""

    def test_item_receipt_relationship(self, db_session) -> None:
        """Test that item references its receipt."""
        receipt = _create_receipt(db_session)
        item = Item(
            receipt_id=receipt.id,
            name="Milk",
            quantity=Decimal("1.000"),
            unit="L",
            total_price=Decimal("2.50"),
        )
        db_session.add(item)
        db_session.commit()

        assert item.receipt is not None
        assert item.receipt.id == receipt.id
        assert item.receipt.store == "Test Store"

    def test_receipt_items_relationship(self, db_session) -> None:
        """Test that receipt lists its items."""
        receipt = _create_receipt(db_session)
        item1 = Item(
            receipt_id=receipt.id,
            name="Milk",
            quantity=Decimal("1.000"),
            unit="L",
            total_price=Decimal("2.50"),
        )
        item2 = Item(
            receipt_id=receipt.id,
            name="Bread",
            quantity=Decimal("1.000"),
            unit="units",
            total_price=Decimal("3.00"),
        )
        db_session.add_all([item1, item2])
        db_session.commit()

        db_session.refresh(receipt)
        assert len(receipt.items) == 2
        item_names = [i.name for i in receipt.items]
        assert "Milk" in item_names
        assert "Bread" in item_names

    def test_item_category_relationship(self, db_session) -> None:
        """Test that item references its category."""
        receipt = _create_receipt(db_session)
        category = _create_category(db_session)
        item = Item(
            receipt_id=receipt.id,
            name="Milk",
            category_id=category.id,
            quantity=Decimal("1.000"),
            unit="L",
            total_price=Decimal("2.50"),
        )
        db_session.add(item)
        db_session.commit()

        assert item.category is not None
        assert item.category.id == category.id
        assert item.category.name == "Dairy"

    def test_category_items_relationship(self, db_session) -> None:
        """Test that category lists its items."""
        receipt = _create_receipt(db_session)
        category = _create_category(db_session)
        item = Item(
            receipt_id=receipt.id,
            name="Milk",
            category_id=category.id,
            quantity=Decimal("1.000"),
            unit="L",
            total_price=Decimal("2.50"),
        )
        db_session.add(item)
        db_session.commit()

        db_session.refresh(category)
        assert len(category.items) == 1
        assert category.items[0].name == "Milk"

    def test_item_category_nullable(self, db_session) -> None:
        """Test that item can exist without a category."""
        receipt = _create_receipt(db_session)
        item = Item(
            receipt_id=receipt.id,
            name="Misc Item",
            quantity=Decimal("1.000"),
            unit="units",
            total_price=Decimal("1.00"),
        )
        db_session.add(item)
        db_session.commit()

        assert item.category_id is None
        assert item.category is None

    def test_cascade_delete_receipt_deletes_items(self, db_session) -> None:
        """Test that deleting a receipt cascades to its items."""
        receipt = _create_receipt(db_session)
        item = Item(
            receipt_id=receipt.id,
            name="Milk",
            quantity=Decimal("1.000"),
            unit="L",
            total_price=Decimal("2.50"),
        )
        db_session.add(item)
        db_session.commit()

        assert db_session.query(Item).count() == 1
        db_session.delete(receipt)
        db_session.commit()
        assert db_session.query(Item).count() == 0

    def test_item_requires_valid_receipt(self, db_session) -> None:
        """Test that item requires a valid receipt_id."""
        item = Item(
            receipt_id=9999,
            name="Milk",
            quantity=Decimal("1.000"),
            unit="L",
            total_price=Decimal("2.50"),
        )
        db_session.add(item)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestItemTimestamps:
    """Tests for Item timestamp fields."""

    def test_created_at_is_set_automatically(self, db_session) -> None:
        """Test that created_at is set when creating an item."""
        receipt = _create_receipt(db_session)
        before = dt.datetime.now()
        item = Item(
            receipt_id=receipt.id,
            name="Milk",
            quantity=Decimal("1.000"),
            unit="L",
            total_price=Decimal("2.50"),
        )
        db_session.add(item)
        db_session.commit()
        after = dt.datetime.now()

        assert item.created_at is not None
        assert before <= item.created_at <= after


class TestItemNameValidation:
    """Tests for item name validation."""

    def test_name_rejects_empty_string(self) -> None:
        """Test that empty string is rejected for item name."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Item(
                receipt_id=1,
                name="",
                quantity=Decimal("1.000"),
                unit="units",
                total_price=Decimal("1.00"),
            )

    def test_name_rejects_whitespace_only(self) -> None:
        """Test that whitespace-only string is rejected for item name."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Item(
                receipt_id=1,
                name="   ",
                quantity=Decimal("1.000"),
                unit="units",
                total_price=Decimal("1.00"),
            )

    def test_name_rejects_none(self) -> None:
        """Test that None is rejected for item name."""
        with pytest.raises(ValueError, match="cannot be None"):
            Item(
                receipt_id=1,
                name=None,
                quantity=Decimal("1.000"),
                unit="units",
                total_price=Decimal("1.00"),
            )

    def test_name_trims_whitespace(self) -> None:
        """Test that leading and trailing whitespace is trimmed."""
        item = Item(
            receipt_id=1,
            name="  Whole Milk  ",
            quantity=Decimal("1.000"),
            unit="L",
            total_price=Decimal("2.50"),
        )
        assert item.name == "Whole Milk"

    def test_name_accepts_valid_name(self) -> None:
        """Test that valid item names are accepted."""
        item = Item(
            receipt_id=1,
            name="Organic Whole Milk 2L",
            quantity=Decimal("1.000"),
            unit="L",
            total_price=Decimal("2.50"),
        )
        assert item.name == "Organic Whole Milk 2L"


class TestItemUnitValidation:
    """Tests for item unit validation."""

    @pytest.mark.parametrize("unit", ["kg", "g", "L", "ml", "units"])
    def test_valid_units_accepted(self, unit: str) -> None:
        """Test that all valid units are accepted."""
        item = Item(
            receipt_id=1,
            name="Test Item",
            quantity=Decimal("1.000"),
            unit=unit,
            total_price=Decimal("1.00"),
        )
        assert item.unit == unit

    def test_invalid_unit_rejected(self) -> None:
        """Test that invalid units are rejected."""
        with pytest.raises(ValueError, match="Unit must be one of"):
            Item(
                receipt_id=1,
                name="Test Item",
                quantity=Decimal("1.000"),
                unit="lbs",
                total_price=Decimal("1.00"),
            )

    def test_unit_none_rejected(self) -> None:
        """Test that None unit is rejected."""
        with pytest.raises(ValueError, match="Unit cannot be None"):
            Item(
                receipt_id=1,
                name="Test Item",
                quantity=Decimal("1.000"),
                unit=None,
                total_price=Decimal("1.00"),
            )


class TestItemConstraints:
    """Tests for Item check constraints."""

    def test_quantity_must_be_positive(self, db_session) -> None:
        """Test that quantity must be > 0."""
        receipt = _create_receipt(db_session)
        item = Item(
            receipt_id=receipt.id,
            name="Milk",
            quantity=Decimal("0"),
            unit="L",
            total_price=Decimal("2.50"),
        )
        db_session.add(item)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_total_price_non_negative(self, db_session) -> None:
        """Test that total_price must be >= 0."""
        receipt = _create_receipt(db_session)
        item = Item(
            receipt_id=receipt.id,
            name="Milk",
            quantity=Decimal("1.000"),
            unit="L",
            total_price=Decimal("-1.00"),
        )
        db_session.add(item)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_total_price_zero_allowed(self, db_session) -> None:
        """Test that total_price of 0 is allowed."""
        receipt = _create_receipt(db_session)
        item = Item(
            receipt_id=receipt.id,
            name="Free Sample",
            quantity=Decimal("1.000"),
            unit="units",
            total_price=Decimal("0.00"),
        )
        db_session.add(item)
        db_session.commit()

        assert item.total_price == Decimal("0.00")


class TestItemRepr:
    """Tests for Item string representation."""

    def test_repr_contains_id_name_and_price(self, db_session) -> None:
        """Test that __repr__ contains id, name, and total_price."""
        receipt = _create_receipt(db_session)
        item = Item(
            receipt_id=receipt.id,
            name="Milk",
            quantity=Decimal("1.000"),
            unit="L",
            total_price=Decimal("2.50"),
        )
        db_session.add(item)
        db_session.commit()

        repr_str = repr(item)
        assert str(item.id) in repr_str
        assert "Milk" in repr_str
        assert "2.50" in repr_str
