"""Receipt model for storing high-level receipt information."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.database.connection import Base

if TYPE_CHECKING:
    from src.database.models.item import Item


class Receipt(Base):
    """Stores high-level receipt information."""

    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[dt.date] = mapped_column(nullable=False)
    store: Mapped[str] = mapped_column(String(255), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(default=lambda: dt.datetime.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        default=lambda: dt.datetime.now(), onupdate=lambda: dt.datetime.now()
    )

    items: Mapped[list[Item]] = relationship(
        "Item", back_populates="receipt", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_receipts_date", "date"),
        Index("idx_receipts_store", "store"),
        CheckConstraint("total_amount >= 0", name="ck_receipts_total_amount_non_negative"),
        CheckConstraint("currency IN ('EUR', 'CHF')", name="ck_receipts_currency_valid"),
    )

    def __repr__(self) -> str:
        return f"<Receipt(id={self.id}, date={self.date}, store='{self.store}')>"

    @validates("currency")
    def validate_currency(self, key: str, value: str | None) -> str:
        """Validate that currency is one of the allowed values."""
        allowed = ("EUR", "CHF")
        if value is None:
            raise ValueError("Currency cannot be None")
        if value not in allowed:
            raise ValueError(f"Currency must be one of {allowed}, got '{value}'")
        return value

    @validates("store")
    def validate_store(self, key: str, value: str | None) -> str:
        """Validate and normalize the store name."""
        if value is None:
            raise ValueError("Store name cannot be None")
        stripped = value.strip()
        if not stripped:
            raise ValueError("Store name cannot be empty or whitespace-only")
        return stripped
