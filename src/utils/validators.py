"""Pydantic validation models for form data."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

VALID_UNITS = ("kg", "g", "L", "ml", "units")
VALID_CURRENCIES = ("EUR", "CHF")
CURRENCY_SYMBOLS: dict[str, str] = {"EUR": "\u20ac", "CHF": "CHF"}


class ItemFormData(BaseModel):
    """Validated data for a single item on a receipt."""

    name: Annotated[str, Field(min_length=1)]
    brand: str = ""
    category_id: int | None = None
    new_category_name: str = ""
    quantity: Annotated[Decimal, Field(gt=0)]
    unit: str
    total_price: Annotated[Decimal, Field(ge=0)]

    @field_validator("name", "brand", "new_category_name", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        """Strip whitespace from string fields."""
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        """Ensure unit is one of the allowed values."""
        if v not in VALID_UNITS:
            raise ValueError(f"Unit must be one of {VALID_UNITS}, got '{v}'")
        return v


class ReceiptFormData(BaseModel):
    """Validated data for a full receipt submission."""

    date: dt.date
    store: Annotated[str, Field(min_length=1)]
    currency: str = "EUR"
    notes: str = ""
    items: Annotated[list[ItemFormData], Field(min_length=1)]

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Ensure currency is one of the allowed values."""
        if v not in VALID_CURRENCIES:
            raise ValueError(f"Currency must be one of {VALID_CURRENCIES}, got '{v}'")
        return v

    @field_validator("store", "notes", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        """Strip whitespace from string fields."""
        if isinstance(v, str):
            return v.strip()
        return v

    @model_validator(mode="after")
    def validate_date_not_future(self) -> ReceiptFormData:
        """Ensure receipt date is not in the future."""
        if self.date > dt.date.today():
            raise ValueError("Receipt date cannot be in the future")
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_amount(self) -> Decimal:
        """Auto-calculate total from items."""
        return sum((item.total_price for item in self.items), Decimal("0"))
