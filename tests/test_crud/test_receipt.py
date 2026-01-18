"""Unit tests for Receipt CRUD operations."""

import datetime as dt
from decimal import Decimal

from src.database.crud import create_receipt, get_receipt, get_receipts


class TestCreateReceipt:
    """Tests for create_receipt function."""

    def test_create_receipt_with_required_fields(self, db_session) -> None:
        """Test creating a receipt with only required fields."""
        receipt = create_receipt(
            db=db_session,
            date=dt.date(2024, 1, 15),
            store="Lidl",
            total_amount=Decimal("45.99"),
        )

        assert receipt.id is not None
        assert receipt.date == dt.date(2024, 1, 15)
        assert receipt.store == "Lidl"
        assert receipt.total_amount == Decimal("45.99")
        assert receipt.notes is None

    def test_create_receipt_with_notes(self, db_session) -> None:
        """Test creating a receipt with notes."""
        receipt = create_receipt(
            db=db_session,
            date=dt.date(2024, 1, 15),
            store="Albert Heijn",
            total_amount=Decimal("32.50"),
            notes="Weekly groceries",
        )

        assert receipt.notes == "Weekly groceries"

    def test_create_receipt_is_persisted(self, db_session) -> None:
        """Test that created receipt is persisted to database."""
        receipt = create_receipt(
            db=db_session,
            date=dt.date(2024, 1, 15),
            store="Jumbo",
            total_amount=Decimal("25.00"),
        )

        # Fetch from database to verify persistence
        fetched = get_receipt(db_session, receipt.id)
        assert fetched is not None
        assert fetched.id == receipt.id
        assert fetched.store == "Jumbo"


class TestGetReceipt:
    """Tests for get_receipt function."""

    def test_get_receipt_returns_receipt(self, db_session) -> None:
        """Test getting an existing receipt by ID."""
        created = create_receipt(
            db=db_session,
            date=dt.date(2024, 1, 15),
            store="Lidl",
            total_amount=Decimal("45.99"),
        )

        fetched = get_receipt(db_session, created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.store == created.store

    def test_get_receipt_returns_none_for_nonexistent(self, db_session) -> None:
        """Test getting a non-existent receipt returns None."""
        result = get_receipt(db_session, 999)

        assert result is None


class TestGetReceipts:
    """Tests for get_receipts function."""

    def test_get_receipts_returns_empty_list(self, db_session) -> None:
        """Test getting receipts when none exist."""
        result = get_receipts(db_session)

        assert result == []

    def test_get_receipts_returns_all_receipts(self, db_session) -> None:
        """Test getting all receipts."""
        create_receipt(
            db=db_session,
            date=dt.date(2024, 1, 15),
            store="Lidl",
            total_amount=Decimal("45.99"),
        )
        create_receipt(
            db=db_session,
            date=dt.date(2024, 1, 16),
            store="Albert Heijn",
            total_amount=Decimal("32.50"),
        )

        result = get_receipts(db_session)

        assert len(result) == 2
        stores = [r.store for r in result]
        assert "Lidl" in stores
        assert "Albert Heijn" in stores

    def test_get_receipts_orders_by_date_descending_by_default(self, db_session) -> None:
        """Test that receipts are ordered by date descending by default."""
        create_receipt(
            db=db_session,
            date=dt.date(2024, 1, 10),
            store="Oldest",
            total_amount=Decimal("10.00"),
        )
        create_receipt(
            db=db_session,
            date=dt.date(2024, 1, 20),
            store="Newest",
            total_amount=Decimal("20.00"),
        )
        create_receipt(
            db=db_session,
            date=dt.date(2024, 1, 15),
            store="Middle",
            total_amount=Decimal("15.00"),
        )

        result = get_receipts(db_session)

        assert result[0].store == "Newest"
        assert result[1].store == "Middle"
        assert result[2].store == "Oldest"

    def test_get_receipts_orders_by_date_ascending(self, db_session) -> None:
        """Test ordering receipts by date ascending."""
        create_receipt(
            db=db_session,
            date=dt.date(2024, 1, 20),
            store="Newest",
            total_amount=Decimal("20.00"),
        )
        create_receipt(
            db=db_session,
            date=dt.date(2024, 1, 10),
            store="Oldest",
            total_amount=Decimal("10.00"),
        )

        result = get_receipts(db_session, order_by_date_desc=False)

        assert result[0].store == "Oldest"
        assert result[1].store == "Newest"

    def test_get_receipts_with_limit(self, db_session) -> None:
        """Test limiting the number of receipts returned."""
        for i in range(5):
            create_receipt(
                db=db_session,
                date=dt.date(2024, 1, i + 1),
                store=f"Store {i}",
                total_amount=Decimal("10.00"),
            )

        result = get_receipts(db_session, limit=3)

        assert len(result) == 3

    def test_get_receipts_with_offset(self, db_session) -> None:
        """Test skipping receipts with offset."""
        for i in range(5):
            create_receipt(
                db=db_session,
                date=dt.date(2024, 1, i + 1),
                store=f"Store {i}",
                total_amount=Decimal("10.00"),
            )

        result = get_receipts(db_session, offset=2)

        assert len(result) == 3

    def test_get_receipts_with_limit_and_offset(self, db_session) -> None:
        """Test pagination with both limit and offset."""
        for i in range(10):
            create_receipt(
                db=db_session,
                date=dt.date(2024, 1, i + 1),
                store=f"Store {i}",
                total_amount=Decimal("10.00"),
            )

        # Get second page (items 3-5) with date descending
        result = get_receipts(db_session, limit=3, offset=3)

        assert len(result) == 3
        # With descending order: dates are 10, 9, 8, 7, 6, 5, 4, 3, 2, 1
        # Offset 3 skips 10, 9, 8 -> returns 7, 6, 5
        assert result[0].date == dt.date(2024, 1, 7)
        assert result[1].date == dt.date(2024, 1, 6)
        assert result[2].date == dt.date(2024, 1, 5)
