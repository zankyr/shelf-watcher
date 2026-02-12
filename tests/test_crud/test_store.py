"""Unit tests for Store CRUD operations."""

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.database.crud import create_store, get_store, get_stores
from src.database.models import Store


class TestCreateStore:
    """Tests for create_store function."""

    def test_create_store_with_required_fields(self, db_session) -> None:
        """Test creating a store with only required fields."""
        store = create_store(db=db_session, name="Lidl")

        assert store.id is not None
        assert store.name == "Lidl"
        assert store.location is None

    def test_create_store_with_location(self, db_session) -> None:
        """Test creating a store with location."""
        store = create_store(db=db_session, name="Albert Heijn", location="Amsterdam")

        assert store.name == "Albert Heijn"
        assert store.location == "Amsterdam"

    def test_create_store_is_persisted(self, db_session) -> None:
        """Test that created store is persisted to database."""
        store = create_store(db=db_session, name="Jumbo")

        fetched = get_store(db_session, store.id)
        assert fetched is not None
        assert fetched.id == store.id
        assert fetched.name == "Jumbo"

    def test_create_store_rolls_back_on_duplicate_name(self, db_session) -> None:
        """Test that create_store rolls back and re-raises on duplicate name."""
        create_store(db=db_session, name="Lidl")

        with pytest.raises(SQLAlchemyError):
            create_store(db=db_session, name="Lidl")

        # Verify rollback - session should be usable
        count = db_session.query(Store).count()
        assert count == 1


class TestGetStore:
    """Tests for get_store function."""

    def test_get_store_returns_store(self, db_session) -> None:
        """Test getting an existing store by ID."""
        created = create_store(db=db_session, name="Lidl")

        fetched = get_store(db_session, created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "Lidl"

    def test_get_store_returns_none_for_nonexistent(self, db_session) -> None:
        """Test getting a non-existent store returns None."""
        result = get_store(db_session, 999)

        assert result is None


class TestGetStores:
    """Tests for get_stores function."""

    def test_get_stores_returns_empty_list(self, db_session) -> None:
        """Test getting stores when none exist."""
        result = get_stores(db_session)

        assert result == []

    def test_get_stores_returns_all_stores(self, db_session) -> None:
        """Test getting all stores."""
        create_store(db=db_session, name="Lidl")
        create_store(db=db_session, name="Albert Heijn")

        result = get_stores(db_session)

        assert len(result) == 2

    def test_get_stores_orders_by_name(self, db_session) -> None:
        """Test that stores are ordered by name ascending."""
        create_store(db=db_session, name="Jumbo")
        create_store(db=db_session, name="Albert Heijn")
        create_store(db=db_session, name="Lidl")

        result = get_stores(db_session)

        assert result[0].name == "Albert Heijn"
        assert result[1].name == "Jumbo"
        assert result[2].name == "Lidl"

    def test_get_stores_with_limit(self, db_session) -> None:
        """Test limiting the number of stores returned."""
        for name in ["Aldi", "Albert Heijn", "Jumbo", "Lidl", "Plus"]:
            create_store(db=db_session, name=name)

        result = get_stores(db_session, limit=3)

        assert len(result) == 3

    def test_get_stores_with_offset(self, db_session) -> None:
        """Test skipping stores with offset."""
        for name in ["Aldi", "Albert Heijn", "Jumbo", "Lidl", "Plus"]:
            create_store(db=db_session, name=name)

        result = get_stores(db_session, offset=2)

        assert len(result) == 3

    def test_get_stores_with_limit_and_offset(self, db_session) -> None:
        """Test pagination with both limit and offset."""
        for name in ["Aldi", "Albert Heijn", "Jumbo", "Lidl", "Plus"]:
            create_store(db=db_session, name=name)

        # Alphabetical order: Albert Heijn, Aldi, Jumbo, Lidl, Plus
        # Offset 1, limit 2 -> Aldi, Jumbo
        result = get_stores(db_session, limit=2, offset=1)

        assert len(result) == 2
        assert result[0].name == "Aldi"
        assert result[1].name == "Jumbo"
