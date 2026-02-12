"""Unit tests for Receipt model."""

import datetime as dt
import time
from decimal import Decimal

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from src.database.models import Receipt


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

    def test_updated_at_changes_on_modification(self, db_session) -> None:
        """Test that updated_at is updated when modifying a receipt."""
        receipt = Receipt(
            date=dt.date(2024, 1, 15),
            store="Lidl",
            total_amount=Decimal("10.00"),
        )
        db_session.add(receipt)
        db_session.commit()
        original_updated_at = receipt.updated_at

        # Delay to ensure timestamp difference (100ms for reliability across systems)
        time.sleep(0.1)

        # Modify the receipt
        receipt.total_amount = Decimal("15.00")
        db_session.commit()

        assert receipt.updated_at > original_updated_at


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


class TestStoreValidation:
    """Tests for store field validation."""

    def test_store_rejects_empty_string(self) -> None:
        """Test that empty string is rejected for store name."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Receipt(
                date=dt.date(2024, 1, 15),
                store="",
                total_amount=Decimal("10.00"),
            )

    def test_store_rejects_whitespace_only(self) -> None:
        """Test that whitespace-only string is rejected for store name."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Receipt(
                date=dt.date(2024, 1, 15),
                store="   ",
                total_amount=Decimal("10.00"),
            )

    def test_store_rejects_none(self) -> None:
        """Test that None is rejected for store name."""
        with pytest.raises(ValueError, match="cannot be None"):
            Receipt(
                date=dt.date(2024, 1, 15),
                store=None,
                total_amount=Decimal("10.00"),
            )

    def test_store_trims_whitespace(self) -> None:
        """Test that leading and trailing whitespace is trimmed."""
        receipt = Receipt(
            date=dt.date(2024, 1, 15),
            store="  Lidl  ",
            total_amount=Decimal("10.00"),
        )
        assert receipt.store == "Lidl"

    def test_store_accepts_valid_name(self) -> None:
        """Test that valid store names are accepted."""
        receipt = Receipt(
            date=dt.date(2024, 1, 15),
            store="Albert Heijn",
            total_amount=Decimal("10.00"),
        )
        assert receipt.store == "Albert Heijn"


class TestTotalAmountConstraint:
    """Tests for total_amount check constraint."""

    def test_rejects_negative_amount(self, db_session) -> None:
        """Test that negative total_amount is rejected by the database."""
        receipt = Receipt(
            date=dt.date(2024, 1, 15),
            store="Lidl",
            total_amount=Decimal("-10.00"),
        )
        db_session.add(receipt)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_accepts_zero_amount(self, db_session) -> None:
        """Test that zero total_amount is accepted."""
        receipt = Receipt(
            date=dt.date(2024, 1, 15),
            store="Lidl",
            total_amount=Decimal("0.00"),
        )
        db_session.add(receipt)
        db_session.commit()

        assert receipt.id is not None
        assert receipt.total_amount == Decimal("0.00")

    def test_accepts_positive_amount(self, db_session) -> None:
        """Test that positive total_amount is accepted."""
        receipt = Receipt(
            date=dt.date(2024, 1, 15),
            store="Lidl",
            total_amount=Decimal("99.99"),
        )
        db_session.add(receipt)
        db_session.commit()

        assert receipt.id is not None
        assert receipt.total_amount == Decimal("99.99")
