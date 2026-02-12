"""Item model for storing individual line items from receipts."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.database.connection import Base

if TYPE_CHECKING:
    from src.database.models.category import Category
    from src.database.models.receipt import Receipt

VALID_UNITS = ("kg", "g", "L", "ml", "units")


class Item(Base):
    """Represents an individual line item on a receipt."""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    receipt_id: Mapped[int] = mapped_column(
        ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    price_per_unit: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    normalized_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    normalized_unit: Mapped[str | None] = mapped_column(String(10), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(default=lambda: dt.datetime.now())

    receipt: Mapped[Receipt] = relationship("Receipt", back_populates="items")
    category: Mapped[Category | None] = relationship("Category", back_populates="items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_items_quantity_positive"),
        CheckConstraint("total_price >= 0", name="ck_items_total_price_non_negative"),
        Index("idx_items_receipt_id", "receipt_id"),
        Index("idx_items_category_id", "category_id"),
        Index("idx_items_name", "name"),
    )

    def __repr__(self) -> str:
        return f"<Item(id={self.id}, name='{self.name}', total_price={self.total_price})>"

    @validates("name")
    def validate_name(self, key: str, value: str | None) -> str:
        """Validate and normalize the item name."""
        if value is None:
            raise ValueError("Item name cannot be None")
        stripped = value.strip()
        if not stripped:
            raise ValueError("Item name cannot be empty or whitespace-only")
        return stripped

    @validates("unit")
    def validate_unit(self, key: str, value: str | None) -> str:
        """Validate that unit is one of the allowed values."""
        if value is None:
            raise ValueError("Unit cannot be None")
        if value not in VALID_UNITS:
            raise ValueError(f"Unit must be one of {VALID_UNITS}, got '{value}'")
        return value
