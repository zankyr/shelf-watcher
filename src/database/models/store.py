"""Store model for the Grocery Receipt Tracker."""

import datetime as dt

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, validates

from src.database.connection import Base


class Store(Base):
    """Represents a store where groceries are purchased."""

    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(default=lambda: dt.datetime.now())

    def __repr__(self) -> str:
        return f"<Store(id={self.id}, name='{self.name}')>"

    @validates("name")
    def validate_name(self, key: str, value: str) -> str:
        """Validate and normalize the store name."""
        if value is None:
            raise ValueError("Store name cannot be None")
        stripped = value.strip()
        if not stripped:
            raise ValueError("Store name cannot be empty or whitespace-only")
        return stripped
