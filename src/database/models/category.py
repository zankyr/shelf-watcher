"""Category model for the Grocery Receipt Tracker."""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.database.connection import Base

if TYPE_CHECKING:
    from src.database.models.item import Item


class Category(Base):
    """Represents a product category with optional parent for hierarchy.

    Categories support a parent-child hierarchy (e.g., Dairy > Milk).
    """

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(default=lambda: dt.datetime.now())

    parent: Mapped[Category | None] = relationship(
        "Category", remote_side=[id], back_populates="children"
    )
    children: Mapped[list[Category]] = relationship("Category", back_populates="parent")
    items: Mapped[list[Item]] = relationship("Item", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"

    @validates("name")
    def validate_name(self, key: str, value: str) -> str:
        """Validate and normalize the category name."""
        if value is None:
            raise ValueError("Category name cannot be None")
        stripped = value.strip()
        if not stripped:
            raise ValueError("Category name cannot be empty or whitespace-only")
        return stripped

    @validates("color")
    def validate_color(self, key: str, value: str | None) -> str | None:
        """Validate hex color format."""
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            return None
        if not stripped.startswith("#") or len(stripped) != 7:
            raise ValueError("Color must be a hex color code (e.g., '#FF5733')")
        return stripped
