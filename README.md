# Grocery Receipt Tracker

A local-first web application to track grocery receipts, analyze price trends over time, compare store prices, and visualize spending patterns. Built with Python and Streamlit.

## Features

### Receipt Entry
- Date picker, store selector (with auto-create), and per-receipt currency (EUR / CHF)
- Dynamic item rows with name, brand, category, quantity, unit, price, and optional original price
- Inline category creation with deduplication
- Automatic price-per-unit and normalized price (per kg/L) calculation
- Discount indicator when original price is set ("Saved" caption)

### Receipt History
- Filterable list with date range, store multi-select, and item name search
- Sort by date, total amount, or store (ascending/descending)
- Expandable receipt details with item table
- Edit and delete with two-step confirmation
- CSV export of filtered items (includes currency and original price)

### Price Analytics
Four tabbed visualizations, each filtered by currency:

- **Price Trends** -- normalized price over time for selected items (line chart)
- **Store Comparison** -- average/min/max prices by store, filterable by items or category (bar chart)
- **Category Spending** -- spending breakdown by category for a date range (pie chart)
- **Monthly Summary** -- stacked spending by category per month with total trend line

### Multi-currency
- EUR and CHF supported per receipt (no cross-currency conversion)
- Dynamic currency symbols throughout the UI
- Analytics queries are scoped to a single currency

### Item Discounts
- Optional original (pre-discount) price per item
- Discount computed in the UI as `original_price - total_price`
- All calculations (normalized price, totals) remain based on the price actually paid

## Setup

```bash
# Install all dependencies (including dev tools)
make install

# Install pre-commit hooks
uv run pre-commit install

# Run the app
make run
```

The SQLite database is created automatically at `data/receipts.db` on first run. Existing databases are migrated automatically (idempotent column additions).

## Development

```bash
make test         # Run tests
make coverage     # Run tests with HTML coverage report
make format       # Format code with black and ruff
make lint         # Lint code with ruff
make type-check   # Type check with mypy
make pre-commit   # Run all pre-commit hooks manually
make clean        # Remove cache files
make help         # Show all available commands
```

## Tech Stack

- **Python 3.13+** with type hints throughout
- **Streamlit** -- web UI with multi-page layout
- **SQLite** via **SQLAlchemy** ORM -- local database, zero config
- **Pydantic** -- form data validation
- **Pandas** -- query results and data manipulation
- **Plotly** -- interactive charts
- **pytest** -- test suite with coverage

## Project Structure

```
src/
  app.py                    # Streamlit entry point
  components/
    receipt_form.py         # Receipt entry/edit form + save/update logic
    receipt_history.py      # History browser with filters and export
    analytics.py            # Four-tab analytics dashboard
  database/
    connection.py           # Engine, session, Base, migrations
    models/                 # SQLAlchemy ORM models (Receipt, Item, Category, Store)
    crud/                   # CRUD operations per model
  utils/
    validators.py           # Pydantic form models + currency/unit constants
    calculations.py         # Price normalization and per-unit calculation
    queries.py              # Analytics queries returning DataFrames
tests/
  conftest.py               # Shared fixtures (in-memory SQLite)
  test_crud/                # CRUD operation tests
  test_models/              # Model constraint and validation tests
  test_components/          # Form save/update tests
  test_utils/               # Validator, calculation, and query tests
```

## Built with Claude Code

This project was developed entirely using [Claude Code](https://docs.anthropic.com/en/docs/claude-code), Anthropic's agentic coding tool. Every feature -- from database schema design and SQLAlchemy models to Streamlit UI components, Plotly visualizations, Pydantic validators, and the full pytest suite -- was planned, implemented, and tested through Claude Code conversations.

The development followed an iterative sprint-based approach across 5 sprints, with Claude Code handling architecture decisions, code generation, test writing, and conventional commit workflows directly on `main`.
