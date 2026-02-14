"""Tests for form validation models."""

import datetime as dt
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.utils.validators import ItemFormData, ReceiptFormData


def _valid_item(**overrides: object) -> dict:
    """Return a valid item dict with optional overrides."""
    data: dict = {
        "name": "Milk",
        "quantity": Decimal("1"),
        "unit": "L",
        "total_price": Decimal("2.50"),
    }
    data.update(overrides)
    return data


def _valid_receipt(**overrides: object) -> dict:
    """Return a valid receipt dict with optional overrides."""
    data: dict = {
        "date": dt.date.today(),
        "store": "Lidl",
        "items": [_valid_item()],
    }
    data.update(overrides)
    return data


class TestItemFormData:
    """Tests for ItemFormData validation."""

    def test_valid_minimal(self) -> None:
        item = ItemFormData(**_valid_item())
        assert item.name == "Milk"
        assert item.brand == ""
        assert item.category_id is None
        assert item.new_category_name == ""

    def test_valid_full(self) -> None:
        item = ItemFormData(**_valid_item(brand="Arla", category_id=1, new_category_name="Dairy"))
        assert item.brand == "Arla"
        assert item.category_id == 1
        assert item.new_category_name == "Dairy"

    def test_name_stripped(self) -> None:
        item = ItemFormData(**_valid_item(name="  Bread  "))
        assert item.name == "Bread"

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            ItemFormData(**_valid_item(name=""))

    def test_whitespace_only_name_rejected(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            ItemFormData(**_valid_item(name="   "))

    def test_zero_quantity_rejected(self) -> None:
        with pytest.raises(ValidationError, match="quantity"):
            ItemFormData(**_valid_item(quantity=Decimal("0")))

    def test_negative_quantity_rejected(self) -> None:
        with pytest.raises(ValidationError, match="quantity"):
            ItemFormData(**_valid_item(quantity=Decimal("-1")))

    def test_negative_price_rejected(self) -> None:
        with pytest.raises(ValidationError, match="total_price"):
            ItemFormData(**_valid_item(total_price=Decimal("-0.01")))

    def test_zero_price_accepted(self) -> None:
        item = ItemFormData(**_valid_item(total_price=Decimal("0")))
        assert item.total_price == Decimal("0")

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValidationError, match="unit"):
            ItemFormData(**_valid_item(unit="lbs"))

    def test_all_valid_units_accepted(self) -> None:
        for unit in ("kg", "g", "L", "ml", "units"):
            item = ItemFormData(**_valid_item(unit=unit))
            assert item.unit == unit

    def test_brand_stripped(self) -> None:
        item = ItemFormData(**_valid_item(brand="  Arla  "))
        assert item.brand == "Arla"

    def test_new_category_name_stripped(self) -> None:
        item = ItemFormData(**_valid_item(new_category_name="  Dairy  "))
        assert item.new_category_name == "Dairy"

    def test_original_price_none_default(self) -> None:
        item = ItemFormData(**_valid_item())
        assert item.original_price is None

    def test_original_price_valid(self) -> None:
        item = ItemFormData(
            **_valid_item(total_price=Decimal("2.50"), original_price=Decimal("3.50"))
        )
        assert item.original_price == Decimal("3.50")

    def test_original_price_negative_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Original price"):
            ItemFormData(**_valid_item(original_price=Decimal("-1.00")))

    def test_original_price_less_than_total_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Original price"):
            ItemFormData(**_valid_item(total_price=Decimal("5.00"), original_price=Decimal("3.00")))


class TestReceiptFormData:
    """Tests for ReceiptFormData validation."""

    def test_valid_minimal(self) -> None:
        receipt = ReceiptFormData(**_valid_receipt())
        assert receipt.store == "Lidl"
        assert receipt.notes == ""
        assert len(receipt.items) == 1

    def test_total_amount_auto_calculated(self) -> None:
        receipt = ReceiptFormData(
            **_valid_receipt(
                items=[
                    _valid_item(total_price=Decimal("2.50")),
                    _valid_item(name="Bread", total_price=Decimal("1.30")),
                ]
            )
        )
        assert receipt.total_amount == Decimal("3.80")

    def test_total_amount_single_item(self) -> None:
        receipt = ReceiptFormData(**_valid_receipt())
        assert receipt.total_amount == Decimal("2.50")

    def test_store_stripped(self) -> None:
        receipt = ReceiptFormData(**_valid_receipt(store="  Lidl  "))
        assert receipt.store == "Lidl"

    def test_empty_store_rejected(self) -> None:
        with pytest.raises(ValidationError, match="store"):
            ReceiptFormData(**_valid_receipt(store=""))

    def test_whitespace_only_store_rejected(self) -> None:
        with pytest.raises(ValidationError, match="store"):
            ReceiptFormData(**_valid_receipt(store="   "))

    def test_empty_items_rejected(self) -> None:
        with pytest.raises(ValidationError, match="items"):
            ReceiptFormData(**_valid_receipt(items=[]))

    def test_future_date_rejected(self) -> None:
        future = dt.date.today() + dt.timedelta(days=1)
        with pytest.raises(ValidationError, match="future"):
            ReceiptFormData(**_valid_receipt(date=future))

    def test_today_accepted(self) -> None:
        receipt = ReceiptFormData(**_valid_receipt(date=dt.date.today()))
        assert receipt.date == dt.date.today()

    def test_past_date_accepted(self) -> None:
        past = dt.date.today() - dt.timedelta(days=30)
        receipt = ReceiptFormData(**_valid_receipt(date=past))
        assert receipt.date == past

    def test_notes_stripped(self) -> None:
        receipt = ReceiptFormData(**_valid_receipt(notes="  some notes  "))
        assert receipt.notes == "some notes"

    def test_notes_default_empty(self) -> None:
        receipt = ReceiptFormData(**_valid_receipt())
        assert receipt.notes == ""

    def test_multiple_items(self) -> None:
        items = [
            _valid_item(name="Milk"),
            _valid_item(name="Bread", unit="units"),
            _valid_item(name="Apples", unit="kg"),
        ]
        receipt = ReceiptFormData(**_valid_receipt(items=items))
        assert len(receipt.items) == 3

    def test_invalid_item_in_list_rejected(self) -> None:
        items = [_valid_item(), _valid_item(name="")]
        with pytest.raises(ValidationError):
            ReceiptFormData(**_valid_receipt(items=items))

    def test_currency_default_eur(self) -> None:
        receipt = ReceiptFormData(**_valid_receipt())
        assert receipt.currency == "EUR"

    def test_currency_chf_accepted(self) -> None:
        receipt = ReceiptFormData(**_valid_receipt(currency="CHF"))
        assert receipt.currency == "CHF"

    def test_invalid_currency_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Currency"):
            ReceiptFormData(**_valid_receipt(currency="USD"))
