"""Unit tests for Store model."""

import datetime as dt

import pytest
from sqlalchemy.exc import IntegrityError

from src.database.models import Store


class TestStoreCreation:
    """Tests for creating Store records."""

    def test_create_store_with_required_fields(self, db_session) -> None:
        """Test creating a store with only required fields."""
        store = Store(name="Lidl")
        db_session.add(store)
        db_session.commit()

        assert store.id is not None
        assert store.name == "Lidl"
        assert store.location is None

    def test_create_store_with_all_fields(self, db_session) -> None:
        """Test creating a store with all fields including location."""
        store = Store(name="Albert Heijn", location="Amsterdam")
        db_session.add(store)
        db_session.commit()

        assert store.id is not None
        assert store.name == "Albert Heijn"
        assert store.location == "Amsterdam"

    def test_create_multiple_stores(self, db_session) -> None:
        """Test creating multiple stores."""
        store1 = Store(name="Lidl")
        store2 = Store(name="Albert Heijn")
        db_session.add_all([store1, store2])
        db_session.commit()

        assert store1.id != store2.id
        assert db_session.query(Store).count() == 2

    def test_store_name_must_be_unique(self, db_session) -> None:
        """Test that duplicate store names are rejected."""
        store1 = Store(name="Lidl")
        db_session.add(store1)
        db_session.commit()

        store2 = Store(name="Lidl")
        db_session.add(store2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestStoreTimestamps:
    """Tests for Store timestamp fields."""

    def test_created_at_is_set_automatically(self, db_session) -> None:
        """Test that created_at is set when creating a store."""
        before = dt.datetime.now()
        store = Store(name="Lidl")
        db_session.add(store)
        db_session.commit()
        after = dt.datetime.now()

        assert store.created_at is not None
        assert before <= store.created_at <= after


class TestStoreNameValidation:
    """Tests for store name validation."""

    def test_name_rejects_empty_string(self) -> None:
        """Test that empty string is rejected for store name."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Store(name="")

    def test_name_rejects_whitespace_only(self) -> None:
        """Test that whitespace-only string is rejected for store name."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Store(name="   ")

    def test_name_rejects_none(self) -> None:
        """Test that None is rejected for store name."""
        with pytest.raises(ValueError, match="cannot be None"):
            Store(name=None)

    def test_name_trims_whitespace(self) -> None:
        """Test that leading and trailing whitespace is trimmed."""
        store = Store(name="  Lidl  ")
        assert store.name == "Lidl"

    def test_name_accepts_valid_name(self) -> None:
        """Test that valid store names are accepted."""
        store = Store(name="Albert Heijn")
        assert store.name == "Albert Heijn"


class TestStoreRepr:
    """Tests for Store string representation."""

    def test_repr_contains_id_and_name(self, db_session) -> None:
        """Test that __repr__ contains id and name."""
        store = Store(name="Jumbo")
        db_session.add(store)
        db_session.commit()

        repr_str = repr(store)
        assert str(store.id) in repr_str
        assert "Jumbo" in repr_str
