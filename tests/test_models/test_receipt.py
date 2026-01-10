"""Unit tests for Receipt model."""

import datetime as dt
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from src.database.connection import Base
from src.database.models import Receipt


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


class TestReceiptCreation:
    """Tests for creating Receipt records."""

    def test_create_receipt_with_required_fields(self, db_session) -> None:
        """Test creating a receipt with only required fields."""
        receipt = Receipt(
            date=dt.date(2024, 1, 15),
            store="Lidl",
            total_amount=Decimal("45.99"),
        )
        db_session.add(receipt)
        db_session.commit()

        assert receipt.id is not None
        assert receipt.date == dt.date(2024, 1, 15)
        assert receipt.store == "Lidl"
        assert receipt.total_amount == Decimal("45.99")
        assert receipt.notes is None

    def test_create_receipt_with_all_fields(self, db_session) -> None:
        """Test creating a receipt with all fields including notes."""
        receipt = Receipt(
            date=dt.date(2024, 1, 15),
            store="Albert Heijn",
            total_amount=Decimal("32.50"),
            notes="Weekly groceries",
        )
        db_session.add(receipt)
        db_session.commit()

        assert receipt.id is not None
        assert receipt.notes == "Weekly groceries"

    def test_create_multiple_receipts(self, db_session) -> None:
        """Test creating multiple receipts."""
        receipt1 = Receipt(
            date=dt.date(2024, 1, 15),
            store="Lidl",
            total_amount=Decimal("45.99"),
        )
        receipt2 = Receipt(
            date=dt.date(2024, 1, 16),
            store="Albert Heijn",
            total_amount=Decimal("32.50"),
        )
        db_session.add_all([receipt1, receipt2])
        db_session.commit()

        assert receipt1.id != receipt2.id
        assert db_session.query(Receipt).count() == 2


class TestReceiptTimestamps:
    """Tests for Receipt timestamp fields."""

    def test_created_at_is_set_automatically(self, db_session) -> None:
        """Test that created_at is set when creating a receipt."""
        before = dt.datetime.now()
        receipt = Receipt(
            date=dt.date(2024, 1, 15),
            store="Lidl",
            total_amount=Decimal("10.00"),
        )
        db_session.add(receipt)
        db_session.commit()
        after = dt.datetime.now()

        assert receipt.created_at is not None
        assert before <= receipt.created_at <= after

    def test_updated_at_is_set_automatically(self, db_session) -> None:
        """Test that updated_at is set when creating a receipt."""
        receipt = Receipt(
            date=dt.date(2024, 1, 15),
            store="Lidl",
            total_amount=Decimal("10.00"),
        )
        db_session.add(receipt)
        db_session.commit()

        assert receipt.updated_at is not None
        assert receipt.created_at <= receipt.updated_at


class TestReceiptIndexes:
    """Tests for Receipt table indexes."""

    def test_date_index_exists(self, db_session) -> None:
        """Test that index on date column exists."""
        inspector = inspect(db_session.bind)
        indexes = inspector.get_indexes("receipts")
        index_names = [idx["name"] for idx in indexes]

        assert "idx_receipts_date" in index_names

    def test_store_index_exists(self, db_session) -> None:
        """Test that index on store column exists."""
        inspector = inspect(db_session.bind)
        indexes = inspector.get_indexes("receipts")
        index_names = [idx["name"] for idx in indexes]

        assert "idx_receipts_store" in index_names


class TestReceiptRepr:
    """Tests for Receipt string representation."""

    def test_repr_contains_id_date_store(self, db_session) -> None:
        """Test that __repr__ contains id, date, and store."""
        receipt = Receipt(
            date=dt.date(2024, 1, 15),
            store="Jumbo",
            total_amount=Decimal("25.00"),
        )
        db_session.add(receipt)
        db_session.commit()

        repr_str = repr(receipt)
        assert str(receipt.id) in repr_str
        assert "2024-01-15" in repr_str
        assert "Jumbo" in repr_str
