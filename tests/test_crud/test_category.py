"""Unit tests for Category CRUD operations."""

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.database.crud import create_category, get_categories, get_category
from src.database.models import Category


class TestCreateCategory:
    """Tests for create_category function."""

    def test_create_category_with_required_fields(self, db_session) -> None:
        """Test creating a category with only required fields."""
        category = create_category(db=db_session, name="Dairy")

        assert category.id is not None
        assert category.name == "Dairy"
        assert category.parent_id is None

    def test_create_category_with_all_fields(self, db_session) -> None:
        """Test creating a category with all fields."""
        parent = create_category(db=db_session, name="Dairy")
        child = create_category(
            db=db_session,
            name="Milk",
            parent_id=parent.id,
            icon="🥛",
            color="#FFFFFF",
        )

        assert child.name == "Milk"
        assert child.parent_id == parent.id
        assert child.icon == "🥛"
        assert child.color == "#FFFFFF"

    def test_create_category_is_persisted(self, db_session) -> None:
        """Test that created category is persisted to database."""
        category = create_category(db=db_session, name="Produce")

        fetched = get_category(db_session, category.id)
        assert fetched is not None
        assert fetched.id == category.id
        assert fetched.name == "Produce"

    def test_create_category_rolls_back_on_duplicate_name(self, db_session) -> None:
        """Test that create_category rolls back and re-raises on duplicate name."""
        create_category(db=db_session, name="Dairy")

        with pytest.raises(SQLAlchemyError):
            create_category(db=db_session, name="Dairy")

        # Verify rollback - session should be usable
        count = db_session.query(Category).count()
        assert count == 1


class TestGetCategory:
    """Tests for get_category function."""

    def test_get_category_returns_category(self, db_session) -> None:
        """Test getting an existing category by ID."""
        created = create_category(db=db_session, name="Dairy")

        fetched = get_category(db_session, created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "Dairy"

    def test_get_category_returns_none_for_nonexistent(self, db_session) -> None:
        """Test getting a non-existent category returns None."""
        result = get_category(db_session, 999)

        assert result is None


class TestGetCategories:
    """Tests for get_categories function."""

    def test_get_categories_returns_empty_list(self, db_session) -> None:
        """Test getting categories when none exist."""
        result = get_categories(db_session)

        assert result == []

    def test_get_categories_returns_all_categories(self, db_session) -> None:
        """Test getting all categories."""
        create_category(db=db_session, name="Dairy")
        create_category(db=db_session, name="Produce")

        result = get_categories(db_session)

        assert len(result) == 2

    def test_get_categories_orders_by_name(self, db_session) -> None:
        """Test that categories are ordered by name ascending."""
        create_category(db=db_session, name="Produce")
        create_category(db=db_session, name="Bakery")
        create_category(db=db_session, name="Dairy")

        result = get_categories(db_session)

        assert result[0].name == "Bakery"
        assert result[1].name == "Dairy"
        assert result[2].name == "Produce"

    def test_get_categories_top_level_only(self, db_session) -> None:
        """Test filtering to only top-level categories."""
        dairy = create_category(db=db_session, name="Dairy")
        create_category(db=db_session, name="Produce")
        create_category(db=db_session, name="Milk", parent_id=dairy.id)

        result = get_categories(db_session, top_level_only=True)

        assert len(result) == 2
        names = [c.name for c in result]
        assert "Dairy" in names
        assert "Produce" in names
        assert "Milk" not in names

    def test_get_categories_by_parent_id(self, db_session) -> None:
        """Test filtering categories by parent ID."""
        dairy = create_category(db=db_session, name="Dairy")
        create_category(db=db_session, name="Milk", parent_id=dairy.id)
        create_category(db=db_session, name="Cheese", parent_id=dairy.id)
        create_category(db=db_session, name="Produce")

        result = get_categories(db_session, parent_id=dairy.id)

        assert len(result) == 2
        names = [c.name for c in result]
        assert "Milk" in names
        assert "Cheese" in names

    def test_get_categories_with_limit(self, db_session) -> None:
        """Test limiting the number of categories returned."""
        for name in ["Bakery", "Dairy", "Meat", "Produce", "Snacks"]:
            create_category(db=db_session, name=name)

        result = get_categories(db_session, limit=3)

        assert len(result) == 3

    def test_get_categories_with_offset(self, db_session) -> None:
        """Test skipping categories with offset."""
        for name in ["Bakery", "Dairy", "Meat", "Produce", "Snacks"]:
            create_category(db=db_session, name=name)

        result = get_categories(db_session, offset=2)

        assert len(result) == 3

    def test_get_categories_with_limit_and_offset(self, db_session) -> None:
        """Test pagination with both limit and offset."""
        for name in ["Bakery", "Dairy", "Meat", "Produce", "Snacks"]:
            create_category(db=db_session, name=name)

        # Alphabetical: Bakery, Dairy, Meat, Produce, Snacks
        # Offset 1, limit 2 -> Dairy, Meat
        result = get_categories(db_session, limit=2, offset=1)

        assert len(result) == 2
        assert result[0].name == "Dairy"
        assert result[1].name == "Meat"
