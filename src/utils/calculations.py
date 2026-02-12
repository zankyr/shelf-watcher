"""Price calculation utilities for normalizing and computing unit prices."""

from decimal import ROUND_HALF_UP, Decimal

_TWO_PLACES = Decimal("0.01")

# Conversion factors to base units (kg, L)
_UNIT_CONVERSIONS: dict[str, tuple[Decimal, str]] = {
    "kg": (Decimal("1"), "kg"),
    "g": (Decimal("0.001"), "kg"),
    "L": (Decimal("1"), "L"),
    "ml": (Decimal("0.001"), "L"),
}


def calculate_price_per_unit(quantity: Decimal, total_price: Decimal) -> Decimal:
    """Calculate price per unit from quantity and total price.

    Args:
        quantity: The quantity purchased (must be > 0).
        total_price: The total price paid (must be >= 0).

    Returns:
        Price per unit, rounded to 2 decimal places.

    Raises:
        ValueError: If quantity is zero or negative.
    """
    if quantity <= 0:
        raise ValueError(f"Quantity must be positive, got {quantity}")
    return (total_price / quantity).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


def normalize_price(quantity: Decimal, unit: str, total_price: Decimal) -> tuple[Decimal, str]:
    """Normalize price to per-kg or per-L for comparison.

    Converts g→kg, ml→L. For 'units', returns price per unit with 'units' as the
    normalized unit.

    Args:
        quantity: The quantity purchased (must be > 0).
        unit: One of 'kg', 'g', 'L', 'ml', 'units'.
        total_price: The total price paid (must be >= 0).

    Returns:
        Tuple of (normalized_price, normalized_unit).

    Raises:
        ValueError: If quantity is zero or negative, or unit is unrecognized.
    """
    if quantity <= 0:
        raise ValueError(f"Quantity must be positive, got {quantity}")

    if unit == "units":
        price = (total_price / quantity).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
        return price, "units"

    if unit not in _UNIT_CONVERSIONS:
        raise ValueError(f"Unrecognized unit '{unit}', expected one of kg, g, L, ml, units")

    factor, base_unit = _UNIT_CONVERSIONS[unit]
    base_quantity = quantity * factor
    price = (total_price / base_quantity).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
    return price, base_unit
