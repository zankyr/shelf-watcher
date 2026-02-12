"""Unit tests for Item CRUD operations."""

import datetime as dt
from decimal import Decimal

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.database.crud import create_item, get_item, get_items
from src.database.models import Category, Item, Receipt


def _create_receipt(db_session, store="Test Store", total=Decimal("25.00")):
    """Helper to create a receipt for item CRUD tests."""
    receipt = Receipt(date=dt.date(2024, 1, 15), store=store, total_amount=total)
    db_session.add(receipt)
    db_session.commit()
    return receipt


def _create_category(db_session, name="Dairy"):
    """Helper to create a category for item CRUD tests."""
    category = Category(name=name)
    db_session.add(category)
    db_session.commit()
    return category


class TestCreateItem:
    """Tests for create_item function."""

    def test_create_item_with_required_fields(self, db_session) -> None:
        """Test creating an item with only required fields."""
        receipt = _create_receipt(db_session)
        item = create_item(
            db=db_session,
            receipt_id=receipt.id,
            name="Whole Milk",
            quantity=Decimal("1.000"),
            unit="L",
            total_price=Decimal("2.50"),
        )

        assert item.id is not None
        assert item.receipt_id == receipt.id
        assert item.name == "Whole Milk"
        assert item.quantity == Decimal("1.000")
        assert item.unit == "L"
        assert item.total_price == Decimal("2.50")
        assert item.brand is None
        assert item.category_id is None

    def test_create_item_with_all_fields(self, db_session) -> None:
        """Test creating an item with all optional fields."""
        receipt = _create_receipt(db_session)
        category = _create_category(db_session)
        item = create_item(
            db=db_session,
            receipt_id=receipt.id,
            name="Organic Milk",
            quantity=Decimal("2.000"),
            unit="L",
            total_price=Decimal("3.50"),
            brand="Farm Fresh",
            category_id=category.id,
            price_per_unit=Decimal("1.75"),
            normalized_price=Decimal("1.75"),
            normalized_unit="L",
            notes="On sale",
        )

        assert item.brand == "Farm Fresh"
        assert item.category_id == category.id
        assert item.price_per_unit == Decimal("1.75")
        assert item.normalized_price == Decimal("1.75")
        assert item.normalized_unit == "L"
        assert item.notes == "On sale"

    def test_create_item_is_persisted(self, db_session) -> None:
        """Test that created item is persisted to database."""
        receipt = _create_receipt(db_session)
        item = create_item(
            db=db_session,
            receipt_id=receipt.id,
            name="Bread",
            quantity=Decimal("1.000"),
            unit="units",
            total_price=Decimal("3.00"),
        )

        fetched = get_item(db_session, item.id)
        assert fetched is not None
        assert fetched.id == item.id
        assert fetched.name == "Bread"

    def test_create_item_rolls_back_on_error(self, db_session) -> None:
        """Test that create_item rolls back and re-raises on DB error."""
        with pytest.raises(SQLAlchemyError):
            create_item(
                db=db_session,
                receipt_id=9999,
                name="Milk",
                quantity=Decimal("1.000"),
                unit="L",
                total_price=Decimal("2.50"),
            )

        # Verify rollback - session should be usable
        count = db_session.query(Item).count()
        assert count == 0


class TestGetItem:
    """Tests for get_item function."""

    def test_get_item_returns_item(self, db_session) -> None:
        """Test getting an existing item by ID."""
        receipt = _create_receipt(db_session)
        created = create_item(
            db=db_session,
            receipt_id=receipt.id,
            name="Milk",
            quantity=Decimal("1.000"),
            unit="L",
            total_price=Decimal("2.50"),
        )

        fetched = get_item(db_session, created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "Milk"

    def test_get_item_returns_none_for_nonexistent(self, db_session) -> None:
        """Test getting a non-existent item returns None."""
        result = get_item(db_session, 999)

        assert result is None


class TestGetItems:
    """Tests for get_items function."""

    def test_get_items_returns_empty_list(self, db_session) -> None:
        """Test getting items when none exist."""
        result = get_items(db_session)

        assert result == []

    def test_get_items_returns_all_items(self, db_session) -> None:
        """Test getting all items."""
        receipt = _create_receipt(db_session)
        create_item(
            db=db_session,
            receipt_id=receipt.id,
            name="Milk",
            quantity=Decimal("1.000"),
            unit="L",
            total_price=Decimal("2.50"),
        )
        create_item(
            db=db_session,
            receipt_id=receipt.id,
            name="Bread",
            quantity=Decimal("1.000"),
            unit="units",
            total_price=Decimal("3.00"),
        )

        result = get_items(db_session)

        assert len(result) == 2

    def test_get_items_orders_by_name(self, db_session) -> None:
        """Test that items are ordered by name ascending."""
        receipt = _create_receipt(db_session)
        create_item(
            db=db_session,
            receipt_id=receipt.id,
            name="Cheese",
            quantity=Decimal("0.500"),
            unit="kg",
            total_price=Decimal("5.00"),
        )
        create_item(
            db=db_session,
            receipt_id=receipt.id,
            name="Apples",
            quantity=Decimal("1.000"),
            unit="kg",
            total_price=Decimal("3.00"),
        )
        create_item(
            db=db_session,
            receipt_id=receipt.id,
            name="Bread",
            quantity=Decimal("1.000"),
            unit="units",
            total_price=Decimal("2.00"),
        )

        result = get_items(db_session)

        assert result[0].name == "Apples"
        assert result[1].name == "Bread"
        assert result[2].name == "Cheese"

    def test_get_items_filter_by_receipt_id(self, db_session) -> None:
        """Test filtering items by receipt ID."""
        receipt1 = _create_receipt(db_session)
        receipt2 = Receipt(
            date=dt.date(2024, 1, 16), store="Other Store", total_amount=Decimal("10.00")
        )
        db_session.add(receipt2)
        db_session.commit()

        create_item(
            db=db_session,
            receipt_id=receipt1.id,
            name="Milk",
            quantity=Decimal("1.000"),
            unit="L",
            total_price=Decimal("2.50"),
        )
        create_item(
            db=db_session,
            receipt_id=receipt2.id,
            name="Bread",
            quantity=Decimal("1.000"),
            unit="units",
            total_price=Decimal("3.00"),
        )

        result = get_items(db_session, receipt_id=receipt1.id)

        assert len(result) == 1
        assert result[0].name == "Milk"

    def test_get_items_filter_by_category_id(self, db_session) -> None:
        """Test filtering items by category ID."""
        receipt = _create_receipt(db_session)
        dairy = _create_category(db_session, name="Dairy")
        bakery = _create_category(db_session, name="Bakery")

        create_item(
            db=db_session,
            receipt_id=receipt.id,
            name="Milk",
            quantity=Decimal("1.000"),
            unit="L",
            total_price=Decimal("2.50"),
            category_id=dairy.id,
        )
        create_item(
            db=db_session,
            receipt_id=receipt.id,
            name="Bread",
            quantity=Decimal("1.000"),
            unit="units",
            total_price=Decimal("3.00"),
            category_id=bakery.id,
        )

        result = get_items(db_session, category_id=dairy.id)

        assert len(result) == 1
        assert result[0].name == "Milk"

    def test_get_items_filter_by_receipt_and_category(self, db_session) -> None:
        """Test filtering items by both receipt and category."""
        receipt1 = _create_receipt(db_session)
        receipt2 = Receipt(
            date=dt.date(2024, 1, 16), store="Other Store", total_amount=Decimal("10.00")
        )
        db_session.add(receipt2)
        db_session.commit()
        dairy = _create_category(db_session, name="Dairy")

        create_item(
            db=db_session,
            receipt_id=receipt1.id,
            name="Milk",
            quantity=Decimal("1.000"),
            unit="L",
            total_price=Decimal("2.50"),
            category_id=dairy.id,
        )
        create_item(
            db=db_session,
            receipt_id=receipt2.id,
            name="Yogurt",
            quantity=Decimal("0.500"),
            unit="kg",
            total_price=Decimal("4.00"),
            category_id=dairy.id,
        )
        create_item(
            db=db_session,
            receipt_id=receipt1.id,
            name="Bread",
            quantity=Decimal("1.000"),
            unit="units",
            total_price=Decimal("3.00"),
        )

        result = get_items(db_session, receipt_id=receipt1.id, category_id=dairy.id)

        assert len(result) == 1
        assert result[0].name == "Milk"

    def test_get_items_with_limit(self, db_session) -> None:
        """Test limiting the number of items returned."""
        receipt = _create_receipt(db_session)
        for name in ["Apples", "Bread", "Cheese", "Dates", "Eggs"]:
            create_item(
                db=db_session,
                receipt_id=receipt.id,
                name=name,
                quantity=Decimal("1.000"),
                unit="units",
                total_price=Decimal("1.00"),
            )

        result = get_items(db_session, limit=3)

        assert len(result) == 3

    def test_get_items_with_offset(self, db_session) -> None:
        """Test skipping items with offset."""
        receipt = _create_receipt(db_session)
        for name in ["Apples", "Bread", "Cheese", "Dates", "Eggs"]:
            create_item(
                db=db_session,
                receipt_id=receipt.id,
                name=name,
                quantity=Decimal("1.000"),
                unit="units",
                total_price=Decimal("1.00"),
            )

        result = get_items(db_session, offset=2)

        assert len(result) == 3

    def test_get_items_with_limit_and_offset(self, db_session) -> None:
        """Test pagination with both limit and offset."""
        receipt = _create_receipt(db_session)
        for name in ["Apples", "Bread", "Cheese", "Dates", "Eggs"]:
            create_item(
                db=db_session,
                receipt_id=receipt.id,
                name=name,
                quantity=Decimal("1.000"),
                unit="units",
                total_price=Decimal("1.00"),
            )

        # Alphabetical: Apples, Bread, Cheese, Dates, Eggs
        # Offset 1, limit 2 -> Bread, Cheese
        result = get_items(db_session, limit=2, offset=1)

        assert len(result) == 2
        assert result[0].name == "Bread"
        assert result[1].name == "Cheese"
