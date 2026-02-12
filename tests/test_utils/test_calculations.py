"""Tests for price calculation utilities."""

from decimal import Decimal

import pytest

from src.utils.calculations import calculate_price_per_unit, normalize_price


class TestCalculatePricePerUnit:
    """Tests for calculate_price_per_unit()."""

    def test_simple_division(self) -> None:
        result = calculate_price_per_unit(Decimal("2"), Decimal("10.00"))
        assert result == Decimal("5.00")

    def test_rounds_to_two_decimal_places(self) -> None:
        result = calculate_price_per_unit(Decimal("3"), Decimal("10.00"))
        assert result == Decimal("3.33")

    def test_rounds_half_up(self) -> None:
        # 5.00 / 4 = 1.25 exactly — no rounding needed
        # 10.00 / 3 = 3.333... → 3.33
        # 10.00 / 6 = 1.666... → 1.67
        result = calculate_price_per_unit(Decimal("6"), Decimal("10.00"))
        assert result == Decimal("1.67")

    def test_fractional_quantity(self) -> None:
        result = calculate_price_per_unit(Decimal("0.500"), Decimal("3.50"))
        assert result == Decimal("7.00")

    def test_zero_price(self) -> None:
        result = calculate_price_per_unit(Decimal("1"), Decimal("0.00"))
        assert result == Decimal("0.00")

    def test_zero_quantity_raises(self) -> None:
        with pytest.raises(ValueError, match="Quantity must be positive"):
            calculate_price_per_unit(Decimal("0"), Decimal("10.00"))

    def test_negative_quantity_raises(self) -> None:
        with pytest.raises(ValueError, match="Quantity must be positive"):
            calculate_price_per_unit(Decimal("-1"), Decimal("10.00"))


class TestNormalizePrice:
    """Tests for normalize_price()."""

    # --- kg ---
    def test_kg_stays_kg(self) -> None:
        price, unit = normalize_price(Decimal("2"), "kg", Decimal("10.00"))
        assert unit == "kg"
        assert price == Decimal("5.00")

    def test_kg_fractional(self) -> None:
        price, unit = normalize_price(Decimal("0.500"), "kg", Decimal("2.50"))
        assert unit == "kg"
        assert price == Decimal("5.00")

    # --- g → kg ---
    def test_grams_converts_to_kg(self) -> None:
        price, unit = normalize_price(Decimal("500"), "g", Decimal("3.00"))
        assert unit == "kg"
        assert price == Decimal("6.00")

    def test_grams_1000_equals_1_kg(self) -> None:
        price, unit = normalize_price(Decimal("1000"), "g", Decimal("5.00"))
        assert unit == "kg"
        assert price == Decimal("5.00")

    def test_grams_small_quantity(self) -> None:
        price, unit = normalize_price(Decimal("100"), "g", Decimal("1.50"))
        assert unit == "kg"
        assert price == Decimal("15.00")

    # --- L ---
    def test_liters_stays_liters(self) -> None:
        price, unit = normalize_price(Decimal("1"), "L", Decimal("2.50"))
        assert unit == "L"
        assert price == Decimal("2.50")

    def test_liters_fractional(self) -> None:
        price, unit = normalize_price(Decimal("0.750"), "L", Decimal("3.00"))
        assert unit == "L"
        assert price == Decimal("4.00")

    # --- ml → L ---
    def test_ml_converts_to_liters(self) -> None:
        price, unit = normalize_price(Decimal("500"), "ml", Decimal("1.50"))
        assert unit == "L"
        assert price == Decimal("3.00")

    def test_ml_1000_equals_1_liter(self) -> None:
        price, unit = normalize_price(Decimal("1000"), "ml", Decimal("2.00"))
        assert unit == "L"
        assert price == Decimal("2.00")

    # --- units ---
    def test_units_returns_price_per_unit(self) -> None:
        price, unit = normalize_price(Decimal("3"), "units", Decimal("6.00"))
        assert unit == "units"
        assert price == Decimal("2.00")

    def test_units_single_item(self) -> None:
        price, unit = normalize_price(Decimal("1"), "units", Decimal("4.99"))
        assert unit == "units"
        assert price == Decimal("4.99")

    # --- error cases ---
    def test_zero_quantity_raises(self) -> None:
        with pytest.raises(ValueError, match="Quantity must be positive"):
            normalize_price(Decimal("0"), "kg", Decimal("10.00"))

    def test_negative_quantity_raises(self) -> None:
        with pytest.raises(ValueError, match="Quantity must be positive"):
            normalize_price(Decimal("-1"), "L", Decimal("10.00"))

    def test_unrecognized_unit_raises(self) -> None:
        with pytest.raises(ValueError, match="Unrecognized unit"):
            normalize_price(Decimal("1"), "lbs", Decimal("5.00"))
