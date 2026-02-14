"""Tests for analytics query functions."""

import datetime as dt
from decimal import Decimal

from src.database.models.category import Category
from src.database.models.item import Item
from src.database.models.receipt import Receipt
from src.utils.queries import (
    get_category_spending,
    get_distinct_item_names,
    get_distinct_store_names,
    get_filtered_items_export,
    get_monthly_spending,
    get_price_trends,
    get_receipt_items,
    get_receipt_list,
    get_store_comparison,
    parse_date_range,
)

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_category(db, name: str, **kwargs) -> Category:
    cat = Category(name=name, **kwargs)
    db.add(cat)
    db.flush()
    return cat


def _make_receipt(db, **kwargs) -> Receipt:
    defaults = {
        "date": dt.date(2026, 2, 10),
        "store": "Lidl",
        "total_amount": Decimal("10.00"),
    }
    defaults.update(kwargs)
    receipt = Receipt(**defaults)
    db.add(receipt)
    db.flush()
    return receipt


def _make_item(db, receipt: Receipt, **kwargs) -> Item:
    defaults = {
        "receipt_id": receipt.id,
        "name": "Milk",
        "quantity": Decimal("1"),
        "unit": "L",
        "total_price": Decimal("2.50"),
        "price_per_unit": Decimal("2.50"),
        "normalized_price": Decimal("2.50"),
        "normalized_unit": "L",
    }
    defaults.update(kwargs)
    item = Item(**defaults)
    db.add(item)
    db.flush()
    return item


# ---------------------------------------------------------------------------
# get_receipt_list
# ---------------------------------------------------------------------------


class TestGetReceiptList:
    def test_returns_correct_columns(self, db_session):
        _make_receipt(db_session)
        db_session.commit()

        df = get_receipt_list(db_session)
        assert list(df.columns) == [
            "receipt_id",
            "date",
            "store",
            "currency",
            "total_amount",
            "item_count",
            "notes",
        ]

    def test_item_count(self, db_session):
        r = _make_receipt(db_session)
        _make_item(db_session, r, name="Milk")
        _make_item(db_session, r, name="Bread")
        db_session.commit()

        df = get_receipt_list(db_session)
        assert df.iloc[0]["item_count"] == 2

    def test_empty_database(self, db_session):
        df = get_receipt_list(db_session)
        assert len(df) == 0

    def test_filter_date_from(self, db_session):
        _make_receipt(db_session, date=dt.date(2026, 1, 1))
        _make_receipt(db_session, date=dt.date(2026, 2, 1))
        db_session.commit()

        df = get_receipt_list(db_session, date_from=dt.date(2026, 1, 15))
        assert len(df) == 1
        assert str(df.iloc[0]["date"]) == "2026-02-01"

    def test_filter_date_to(self, db_session):
        _make_receipt(db_session, date=dt.date(2026, 1, 1))
        _make_receipt(db_session, date=dt.date(2026, 2, 1))
        db_session.commit()

        df = get_receipt_list(db_session, date_to=dt.date(2026, 1, 15))
        assert len(df) == 1
        assert str(df.iloc[0]["date"]) == "2026-01-01"

    def test_filter_date_range(self, db_session):
        _make_receipt(db_session, date=dt.date(2026, 1, 1))
        _make_receipt(db_session, date=dt.date(2026, 1, 15))
        _make_receipt(db_session, date=dt.date(2026, 2, 1))
        db_session.commit()

        df = get_receipt_list(
            db_session,
            date_from=dt.date(2026, 1, 10),
            date_to=dt.date(2026, 1, 20),
        )
        assert len(df) == 1

    def test_filter_stores(self, db_session):
        _make_receipt(db_session, store="Lidl")
        _make_receipt(db_session, store="Albert Heijn")
        _make_receipt(db_session, store="Jumbo")
        db_session.commit()

        df = get_receipt_list(db_session, stores=["Lidl", "Jumbo"])
        assert len(df) == 2
        assert set(df["store"]) == {"Lidl", "Jumbo"}

    def test_filter_item_search(self, db_session):
        r1 = _make_receipt(db_session, store="Lidl")
        _make_item(db_session, r1, name="Whole Milk")
        r2 = _make_receipt(db_session, store="Jumbo")
        _make_item(db_session, r2, name="Bread")
        db_session.commit()

        df = get_receipt_list(db_session, item_search="milk")
        assert len(df) == 1
        assert df.iloc[0]["store"] == "Lidl"

    def test_item_search_case_insensitive(self, db_session):
        r = _make_receipt(db_session)
        _make_item(db_session, r, name="Organic MILK")
        db_session.commit()

        df = get_receipt_list(db_session, item_search="milk")
        assert len(df) == 1

    def test_item_search_preserves_item_count(self, db_session):
        """Item search should not affect the item_count aggregation."""
        r = _make_receipt(db_session)
        _make_item(db_session, r, name="Milk")
        _make_item(db_session, r, name="Bread")
        _make_item(db_session, r, name="Cheese")
        db_session.commit()

        df = get_receipt_list(db_session, item_search="milk")
        assert len(df) == 1
        assert df.iloc[0]["item_count"] == 3  # all items, not just matching

    def test_sort_by_date_desc(self, db_session):
        _make_receipt(db_session, date=dt.date(2026, 1, 1))
        _make_receipt(db_session, date=dt.date(2026, 2, 1))
        db_session.commit()

        df = get_receipt_list(db_session, sort_by="date", sort_desc=True)
        assert str(df.iloc[0]["date"]) == "2026-02-01"

    def test_sort_by_date_asc(self, db_session):
        _make_receipt(db_session, date=dt.date(2026, 1, 1))
        _make_receipt(db_session, date=dt.date(2026, 2, 1))
        db_session.commit()

        df = get_receipt_list(db_session, sort_by="date", sort_desc=False)
        assert str(df.iloc[0]["date"]) == "2026-01-01"

    def test_sort_by_total(self, db_session):
        _make_receipt(db_session, total_amount=Decimal("50.00"))
        _make_receipt(db_session, total_amount=Decimal("10.00"))
        db_session.commit()

        df = get_receipt_list(db_session, sort_by="total", sort_desc=True)
        assert float(df.iloc[0]["total_amount"]) == 50.00

    def test_sort_by_store(self, db_session):
        _make_receipt(db_session, store="Jumbo")
        _make_receipt(db_session, store="Albert Heijn")
        db_session.commit()

        df = get_receipt_list(db_session, sort_by="store", sort_desc=False)
        assert df.iloc[0]["store"] == "Albert Heijn"

    def test_receipt_without_items(self, db_session):
        """A receipt with no items should show item_count=0."""
        _make_receipt(db_session)
        db_session.commit()

        df = get_receipt_list(db_session)
        assert df.iloc[0]["item_count"] == 0


# ---------------------------------------------------------------------------
# get_receipt_items
# ---------------------------------------------------------------------------


class TestGetReceiptItems:
    def test_returns_correct_columns(self, db_session):
        r = _make_receipt(db_session)
        _make_item(db_session, r)
        db_session.commit()

        df = get_receipt_items(db_session, r.id)
        assert list(df.columns) == [
            "item_id",
            "name",
            "brand",
            "category",
            "quantity",
            "unit",
            "price_per_unit",
            "total_price",
            "normalized_price",
            "normalized_unit",
        ]

    def test_resolves_category_name(self, db_session):
        cat = _make_category(db_session, "Dairy")
        r = _make_receipt(db_session)
        _make_item(db_session, r, category_id=cat.id)
        db_session.commit()

        df = get_receipt_items(db_session, r.id)
        assert df.iloc[0]["category"] == "Dairy"

    def test_null_category(self, db_session):
        r = _make_receipt(db_session)
        _make_item(db_session, r, category_id=None)
        db_session.commit()

        df = get_receipt_items(db_session, r.id)
        assert df.iloc[0]["category"] is None

    def test_nonexistent_receipt(self, db_session):
        df = get_receipt_items(db_session, 9999)
        assert len(df) == 0

    def test_multiple_items(self, db_session):
        r = _make_receipt(db_session)
        _make_item(db_session, r, name="Milk")
        _make_item(db_session, r, name="Bread", unit="units", normalized_unit="units")
        db_session.commit()

        df = get_receipt_items(db_session, r.id)
        assert len(df) == 2


# ---------------------------------------------------------------------------
# get_filtered_items_export
# ---------------------------------------------------------------------------


class TestGetFilteredItemsExport:
    def test_returns_correct_columns(self, db_session):
        r = _make_receipt(db_session)
        _make_item(db_session, r)
        db_session.commit()

        df = get_filtered_items_export(db_session)
        assert list(df.columns) == [
            "date",
            "store",
            "currency",
            "item_name",
            "brand",
            "category",
            "quantity",
            "unit",
            "price_per_unit",
            "total_price",
            "normalized_price",
            "normalized_unit",
            "notes",
        ]

    def test_denormalized_rows(self, db_session):
        r = _make_receipt(db_session, notes="Weekly shop")
        _make_item(db_session, r, name="Milk")
        _make_item(db_session, r, name="Bread", unit="units", normalized_unit="units")
        db_session.commit()

        df = get_filtered_items_export(db_session)
        assert len(df) == 2
        assert all(df["store"] == "Lidl")

    def test_filters_applied(self, db_session):
        r1 = _make_receipt(db_session, store="Lidl", date=dt.date(2026, 1, 1))
        _make_item(db_session, r1, name="Milk")
        r2 = _make_receipt(db_session, store="Jumbo", date=dt.date(2026, 2, 1))
        _make_item(db_session, r2, name="Bread", unit="units", normalized_unit="units")
        db_session.commit()

        df = get_filtered_items_export(db_session, stores=["Lidl"])
        assert len(df) == 1
        assert df.iloc[0]["item_name"] == "Milk"

    def test_item_search_filter(self, db_session):
        r = _make_receipt(db_session)
        _make_item(db_session, r, name="Whole Milk")
        _make_item(db_session, r, name="Bread", unit="units", normalized_unit="units")
        db_session.commit()

        df = get_filtered_items_export(db_session, item_search="milk")
        assert len(df) == 1

    def test_empty_database(self, db_session):
        df = get_filtered_items_export(db_session)
        assert len(df) == 0


# ---------------------------------------------------------------------------
# get_price_trends
# ---------------------------------------------------------------------------


class TestGetPriceTrends:
    def test_returns_correct_columns(self, db_session):
        r = _make_receipt(db_session)
        _make_item(db_session, r)
        db_session.commit()

        df = get_price_trends(db_session, item_names=["Milk"])
        assert list(df.columns) == [
            "date",
            "item_name",
            "store",
            "normalized_price",
            "normalized_unit",
        ]

    def test_case_insensitive_item_match(self, db_session):
        r = _make_receipt(db_session)
        _make_item(db_session, r, name="Whole Milk")
        db_session.commit()

        df = get_price_trends(db_session, item_names=["whole milk"])
        assert len(df) == 1

    def test_excludes_items_without_normalized_price(self, db_session):
        r = _make_receipt(db_session)
        _make_item(db_session, r, normalized_price=None, normalized_unit=None)
        db_session.commit()

        df = get_price_trends(db_session)
        assert len(df) == 0

    def test_date_range_filter(self, db_session):
        r1 = _make_receipt(db_session, date=dt.date(2026, 1, 1))
        _make_item(db_session, r1, name="Milk")
        r2 = _make_receipt(db_session, date=dt.date(2026, 3, 1))
        _make_item(db_session, r2, name="Milk")
        db_session.commit()

        df = get_price_trends(
            db_session,
            item_names=["Milk"],
            date_from=dt.date(2026, 2, 1),
        )
        assert len(df) == 1

    def test_no_filter_returns_all(self, db_session):
        r = _make_receipt(db_session)
        _make_item(db_session, r, name="Milk")
        _make_item(db_session, r, name="Bread", unit="units", normalized_unit="units")
        db_session.commit()

        df = get_price_trends(db_session)
        assert len(df) == 2

    def test_ordered_by_date(self, db_session):
        r1 = _make_receipt(db_session, date=dt.date(2026, 2, 1))
        _make_item(db_session, r1, name="Milk")
        r2 = _make_receipt(db_session, date=dt.date(2026, 1, 1))
        _make_item(db_session, r2, name="Milk")
        db_session.commit()

        df = get_price_trends(db_session, item_names=["Milk"])
        assert str(df.iloc[0]["date"]) == "2026-01-01"


# ---------------------------------------------------------------------------
# get_store_comparison
# ---------------------------------------------------------------------------


class TestGetStoreComparison:
    def test_returns_correct_columns(self, db_session):
        r = _make_receipt(db_session, store="Lidl")
        _make_item(db_session, r)
        db_session.commit()

        df = get_store_comparison(db_session, item_names=["Milk"])
        assert list(df.columns) == [
            "store",
            "avg_normalized_price",
            "min_normalized_price",
            "max_normalized_price",
            "purchase_count",
        ]

    def test_groups_by_store(self, db_session):
        r1 = _make_receipt(db_session, store="Lidl")
        _make_item(db_session, r1, name="Milk", normalized_price=Decimal("2.00"))
        r2 = _make_receipt(db_session, store="Jumbo")
        _make_item(db_session, r2, name="Milk", normalized_price=Decimal("3.00"))
        db_session.commit()

        df = get_store_comparison(db_session, item_names=["Milk"])
        assert len(df) == 2

    def test_calculates_stats(self, db_session):
        r1 = _make_receipt(db_session, store="Lidl", date=dt.date(2026, 1, 1))
        _make_item(db_session, r1, name="Milk", normalized_price=Decimal("2.00"))
        r2 = _make_receipt(db_session, store="Lidl", date=dt.date(2026, 1, 2))
        _make_item(db_session, r2, name="Milk", normalized_price=Decimal("4.00"))
        db_session.commit()

        df = get_store_comparison(db_session, item_names=["Milk"])
        row = df.iloc[0]
        assert float(row["avg_normalized_price"]) == 3.0
        assert float(row["min_normalized_price"]) == 2.0
        assert float(row["max_normalized_price"]) == 4.0
        assert row["purchase_count"] == 2

    def test_filter_by_category(self, db_session):
        cat = _make_category(db_session, "Dairy")
        r = _make_receipt(db_session, store="Lidl")
        _make_item(db_session, r, name="Milk", category_id=cat.id)
        _make_item(
            db_session, r, name="Bread", category_id=None, unit="units", normalized_unit="units"
        )
        db_session.commit()

        df = get_store_comparison(db_session, category_id=cat.id)
        assert len(df) == 1
        assert df.iloc[0]["purchase_count"] == 1

    def test_excludes_items_without_normalized_price(self, db_session):
        r = _make_receipt(db_session)
        _make_item(db_session, r, normalized_price=None, normalized_unit=None)
        db_session.commit()

        df = get_store_comparison(db_session)
        assert len(df) == 0

    def test_case_insensitive_item_names(self, db_session):
        r = _make_receipt(db_session, store="Lidl")
        _make_item(db_session, r, name="Whole Milk")
        db_session.commit()

        df = get_store_comparison(db_session, item_names=["whole milk"])
        assert len(df) == 1


# ---------------------------------------------------------------------------
# get_category_spending
# ---------------------------------------------------------------------------


class TestGetCategorySpending:
    def test_returns_correct_columns(self, db_session):
        r = _make_receipt(db_session)
        _make_item(db_session, r)
        db_session.commit()

        df = get_category_spending(db_session)
        assert list(df.columns) == ["category", "total_spent", "item_count"]

    def test_groups_by_category(self, db_session):
        cat = _make_category(db_session, "Dairy")
        r = _make_receipt(db_session)
        _make_item(db_session, r, name="Milk", category_id=cat.id, total_price=Decimal("2.50"))
        _make_item(
            db_session,
            r,
            name="Bread",
            category_id=None,
            total_price=Decimal("1.50"),
            unit="units",
            normalized_unit="units",
        )
        db_session.commit()

        df = get_category_spending(db_session)
        assert len(df) == 2

    def test_uncategorized_label(self, db_session):
        r = _make_receipt(db_session)
        _make_item(db_session, r, category_id=None)
        db_session.commit()

        df = get_category_spending(db_session)
        assert df.iloc[0]["category"] == "Uncategorized"

    def test_date_range_filter(self, db_session):
        r1 = _make_receipt(db_session, date=dt.date(2026, 1, 1))
        _make_item(db_session, r1, total_price=Decimal("10.00"))
        r2 = _make_receipt(db_session, date=dt.date(2026, 3, 1))
        _make_item(db_session, r2, total_price=Decimal("20.00"))
        db_session.commit()

        df = get_category_spending(
            db_session,
            date_from=dt.date(2026, 2, 1),
        )
        assert len(df) == 1
        assert float(df.iloc[0]["total_spent"]) == 20.0

    def test_sums_totals(self, db_session):
        cat = _make_category(db_session, "Dairy")
        r = _make_receipt(db_session)
        _make_item(db_session, r, name="Milk", category_id=cat.id, total_price=Decimal("2.50"))
        _make_item(db_session, r, name="Cheese", category_id=cat.id, total_price=Decimal("3.50"))
        db_session.commit()

        df = get_category_spending(db_session)
        assert float(df.iloc[0]["total_spent"]) == 6.0
        assert df.iloc[0]["item_count"] == 2

    def test_empty_database(self, db_session):
        df = get_category_spending(db_session)
        assert len(df) == 0


# ---------------------------------------------------------------------------
# get_monthly_spending
# ---------------------------------------------------------------------------


class TestGetMonthlySpending:
    def test_returns_correct_columns(self, db_session):
        r = _make_receipt(db_session)
        _make_item(db_session, r)
        db_session.commit()

        df = get_monthly_spending(db_session)
        assert list(df.columns) == ["month", "category", "total_spent"]

    def test_groups_by_month(self, db_session):
        r1 = _make_receipt(db_session, date=dt.date(2026, 1, 15))
        _make_item(db_session, r1, total_price=Decimal("10.00"))
        r2 = _make_receipt(db_session, date=dt.date(2026, 2, 15))
        _make_item(db_session, r2, total_price=Decimal("20.00"))
        db_session.commit()

        df = get_monthly_spending(db_session)
        assert len(df) == 2
        months = list(df["month"])
        assert "2026-01" in months
        assert "2026-02" in months

    def test_date_range_filter(self, db_session):
        r1 = _make_receipt(db_session, date=dt.date(2026, 1, 1))
        _make_item(db_session, r1)
        r2 = _make_receipt(db_session, date=dt.date(2026, 3, 1))
        _make_item(db_session, r2)
        db_session.commit()

        df = get_monthly_spending(db_session, date_from=dt.date(2026, 2, 1))
        assert len(df) == 1
        assert df.iloc[0]["month"] == "2026-03"

    def test_ordered_by_month(self, db_session):
        r1 = _make_receipt(db_session, date=dt.date(2026, 3, 1))
        _make_item(db_session, r1)
        r2 = _make_receipt(db_session, date=dt.date(2026, 1, 1))
        _make_item(db_session, r2)
        db_session.commit()

        df = get_monthly_spending(db_session)
        assert df.iloc[0]["month"] == "2026-01"
        assert df.iloc[1]["month"] == "2026-03"

    def test_uncategorized_label(self, db_session):
        r = _make_receipt(db_session)
        _make_item(db_session, r, category_id=None)
        db_session.commit()

        df = get_monthly_spending(db_session)
        assert df.iloc[0]["category"] == "Uncategorized"

    def test_empty_database(self, db_session):
        df = get_monthly_spending(db_session)
        assert len(df) == 0


# ---------------------------------------------------------------------------
# get_distinct_item_names / get_distinct_store_names
# ---------------------------------------------------------------------------


class TestDistinctHelpers:
    def test_distinct_item_names(self, db_session):
        r = _make_receipt(db_session)
        _make_item(db_session, r, name="Milk")
        _make_item(db_session, r, name="Bread", unit="units", normalized_unit="units")
        _make_item(db_session, r, name="Milk")  # duplicate
        db_session.commit()

        names = get_distinct_item_names(db_session)
        assert names == ["Bread", "Milk"]

    def test_distinct_item_names_empty(self, db_session):
        assert get_distinct_item_names(db_session) == []

    def test_distinct_store_names(self, db_session):
        _make_receipt(db_session, store="Lidl")
        _make_receipt(db_session, store="Jumbo")
        _make_receipt(db_session, store="Lidl")  # duplicate
        db_session.commit()

        names = get_distinct_store_names(db_session)
        assert names == ["Jumbo", "Lidl"]

    def test_distinct_store_names_empty(self, db_session):
        assert get_distinct_store_names(db_session) == []


# ---------------------------------------------------------------------------
# parse_date_range
# ---------------------------------------------------------------------------


class TestParseDateRange:
    def test_single_date(self):
        d = dt.date(2026, 1, 15)
        assert parse_date_range(d) == (d, d)

    def test_empty_tuple(self):
        assert parse_date_range(()) == (None, None)

    def test_single_element_tuple(self):
        d = dt.date(2026, 1, 15)
        assert parse_date_range((d,)) == (d, None)

    def test_two_element_tuple(self):
        d1 = dt.date(2026, 1, 1)
        d2 = dt.date(2026, 1, 31)
        assert parse_date_range((d1, d2)) == (d1, d2)
