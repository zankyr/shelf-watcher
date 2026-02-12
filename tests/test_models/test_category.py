"""Unit tests for Category model."""

import datetime as dt

import pytest
from sqlalchemy.exc import IntegrityError

from src.database.models import Category


class TestCategoryCreation:
    """Tests for creating Category records."""

    def test_create_category_with_required_fields(self, db_session) -> None:
        """Test creating a category with only required fields."""
        category = Category(name="Dairy")
        db_session.add(category)
        db_session.commit()

        assert category.id is not None
        assert category.name == "Dairy"
        assert category.parent_id is None
        assert category.icon is None
        assert category.color is None

    def test_create_category_with_all_fields(self, db_session) -> None:
        """Test creating a category with all fields."""
        parent = Category(name="Dairy")
        db_session.add(parent)
        db_session.commit()

        child = Category(
            name="Milk",
            parent_id=parent.id,
            icon="🥛",
            color="#FFFFFF",
        )
        db_session.add(child)
        db_session.commit()

        assert child.id is not None
        assert child.name == "Milk"
        assert child.parent_id == parent.id
        assert child.icon == "🥛"
        assert child.color == "#FFFFFF"

    def test_create_multiple_categories(self, db_session) -> None:
        """Test creating multiple categories."""
        cat1 = Category(name="Dairy")
        cat2 = Category(name="Produce")
        db_session.add_all([cat1, cat2])
        db_session.commit()

        assert cat1.id != cat2.id
        assert db_session.query(Category).count() == 2

    def test_category_name_must_be_unique(self, db_session) -> None:
        """Test that duplicate category names are rejected."""
        cat1 = Category(name="Dairy")
        db_session.add(cat1)
        db_session.commit()

        cat2 = Category(name="Dairy")
        db_session.add(cat2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestCategoryHierarchy:
    """Tests for Category parent-child relationships."""

    def test_parent_relationship(self, db_session) -> None:
        """Test that child category references its parent."""
        parent = Category(name="Dairy")
        db_session.add(parent)
        db_session.commit()

        child = Category(name="Milk", parent_id=parent.id)
        db_session.add(child)
        db_session.commit()

        assert child.parent is not None
        assert child.parent.id == parent.id
        assert child.parent.name == "Dairy"

    def test_children_relationship(self, db_session) -> None:
        """Test that parent category lists its children."""
        parent = Category(name="Dairy")
        db_session.add(parent)
        db_session.commit()

        child1 = Category(name="Milk", parent_id=parent.id)
        child2 = Category(name="Cheese", parent_id=parent.id)
        db_session.add_all([child1, child2])
        db_session.commit()

        db_session.refresh(parent)
        assert len(parent.children) == 2
        child_names = [c.name for c in parent.children]
        assert "Milk" in child_names
        assert "Cheese" in child_names

    def test_top_level_category_has_no_parent(self, db_session) -> None:
        """Test that top-level categories have no parent."""
        category = Category(name="Dairy")
        db_session.add(category)
        db_session.commit()

        assert category.parent is None
        assert category.parent_id is None


class TestCategoryTimestamps:
    """Tests for Category timestamp fields."""

    def test_created_at_is_set_automatically(self, db_session) -> None:
        """Test that created_at is set when creating a category."""
        before = dt.datetime.now()
        category = Category(name="Dairy")
        db_session.add(category)
        db_session.commit()
        after = dt.datetime.now()

        assert category.created_at is not None
        assert before <= category.created_at <= after


class TestCategoryNameValidation:
    """Tests for category name validation."""

    def test_name_rejects_empty_string(self) -> None:
        """Test that empty string is rejected for category name."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Category(name="")

    def test_name_rejects_whitespace_only(self) -> None:
        """Test that whitespace-only string is rejected for category name."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Category(name="   ")

    def test_name_rejects_none(self) -> None:
        """Test that None is rejected for category name."""
        with pytest.raises(ValueError, match="cannot be None"):
            Category(name=None)

    def test_name_trims_whitespace(self) -> None:
        """Test that leading and trailing whitespace is trimmed."""
        category = Category(name="  Dairy  ")
        assert category.name == "Dairy"

    def test_name_accepts_valid_name(self) -> None:
        """Test that valid category names are accepted."""
        category = Category(name="Fresh Produce")
        assert category.name == "Fresh Produce"


class TestCategoryColorValidation:
    """Tests for category color validation."""

    def test_color_accepts_valid_hex(self) -> None:
        """Test that valid hex color codes are accepted."""
        category = Category(name="Dairy", color="#FF5733")
        assert category.color == "#FF5733"

    def test_color_accepts_none(self) -> None:
        """Test that None is accepted for color."""
        category = Category(name="Dairy", color=None)
        assert category.color is None

    def test_color_rejects_invalid_format(self) -> None:
        """Test that invalid color formats are rejected."""
        with pytest.raises(ValueError, match="hex color code"):
            Category(name="Dairy", color="red")

    def test_color_rejects_short_hex(self) -> None:
        """Test that short hex codes are rejected."""
        with pytest.raises(ValueError, match="hex color code"):
            Category(name="Dairy", color="#FFF")

    def test_color_converts_empty_to_none(self) -> None:
        """Test that empty string is converted to None."""
        category = Category(name="Dairy", color="  ")
        assert category.color is None


class TestCategoryRepr:
    """Tests for Category string representation."""

    def test_repr_contains_id_and_name(self, db_session) -> None:
        """Test that __repr__ contains id and name."""
        category = Category(name="Dairy")
        db_session.add(category)
        db_session.commit()

        repr_str = repr(category)
        assert str(category.id) in repr_str
        assert "Dairy" in repr_str
