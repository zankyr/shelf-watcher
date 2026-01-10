"""Unit tests for Receipt CRUD operations."""

import datetime as dt
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.connection import Base
from src.database.crud import create_receipt, get_receipt, get_receipts


@pytest.fixture
def db_session():
    """Create a fresh in-memory database for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()
    engine.dispose()


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
