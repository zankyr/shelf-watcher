# Grocery Receipt Tracker - Project Context

## Project Overview

**Project Name:** Grocery Receipt Tracker
**Developer:** Riccardo (10+ years experience, Python/Java expert)
**Goal:** Desktop/web application to track grocery receipt history, analyze price trends over time, and visualize spending patterns.

### Core Problem
Track grocery prices over time to understand price trends, compare stores, and monitor household spending patterns across categories.

### Solution Approach
A local-first Python application with web UI that stores receipts in a structured database, provides easy data entry, and offers rich visualizations for price analysis.

---

## Tech Stack

### Core Technologies
- **Python 3.11+**: Primary language
- **uv**: Package and project management (faster alternative to Poetry/pip)
- **Streamlit**: Web-based UI framework for rapid development
- **SQLite**: Local database (zero-config, portable)
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive visualizations

### Supporting Libraries
- **SQLAlchemy** (optional): ORM for database operations
- **Pydantic**: Data validation and settings management
- **pytest**: Testing framework

### Future Additions (Phase 2)
- **Tesseract-OCR / EasyOCR / PaddleOCR**: Receipt image processing
- **OpenCV / Pillow**: Image preprocessing for OCR

### Rationale
- **uv**: Modern, fast, reliable dependency management
- **SQLite**: No server needed, perfect for local-first app, easy backup
- **Streamlit**: Rapid UI development, built-in data viz components, Python-native
- **Plotly**: Interactive charts, good Streamlit integration

---

## Project Architecture

### Directory Structure
```
grocery-tracker/
├── pyproject.toml              # uv project config
├── .python-version             # Python version pinning
├── README.md
├── PROJECT_CONTEXT.md          # This file
├── src/
│   ├── __init__.py
│   ├── app.py                  # Streamlit main entry point
│   ├── config.py               # App configuration
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py           # SQLAlchemy models / schema
│   │   ├── crud.py             # CRUD operations
│   │   ├── connection.py       # Database connection management
│   │   └── migrations/         # Schema migration scripts
│   │       └── init_schema.sql
│   ├── pages/                  # Streamlit pages
│   │   ├── 1_📝_entry.py      # Receipt entry form
│   │   ├── 2_📊_history.py    # Receipt history browser
│   │   └── 3_📈_analytics.py  # Price analytics & charts
│   ├── components/             # Reusable UI components
│   │   ├── __init__.py
│   │   ├── receipt_form.py
│   │   └── item_table.py
│   └── utils/
│       ├── __init__.py
│       ├── validators.py       # Data validation functions
│       ├── formatters.py       # Price/date formatting
│       └── calculations.py     # Price normalization, aggregations
├── data/
│   └── receipts.db             # SQLite database (gitignored)
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_crud.py
│   └── test_calculations.py
└── docs/
    └── schema.md               # Database schema documentation
```

---

## Database Schema

### Tables

#### `receipts`
Stores high-level receipt information.

```sql
CREATE TABLE receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    store TEXT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `items`
Stores individual items from receipts with normalized pricing.

```sql
CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    brand TEXT,
    category_id INTEGER,
    quantity DECIMAL(10, 3) NOT NULL,
    unit TEXT NOT NULL,  -- kg, L, units, g, ml, etc.
    price_per_unit DECIMAL(10, 2),
    total_price DECIMAL(10, 2) NOT NULL,
    normalized_price DECIMAL(10, 2),  -- price per kg or L
    normalized_unit TEXT,  -- kg or L
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (receipt_id) REFERENCES receipts(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);
```

#### `categories`
Hierarchical category system.

```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    parent_id INTEGER,
    icon TEXT,  -- emoji or icon identifier
    color TEXT,  -- hex color for charts
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES categories(id)
);
```

#### `stores`
Store master data for autocomplete and analysis.

```sql
CREATE TABLE stores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes
```sql
CREATE INDEX idx_items_receipt_id ON items(receipt_id);
CREATE INDEX idx_items_category_id ON items(category_id);
CREATE INDEX idx_items_name ON items(name);
CREATE INDEX idx_receipts_date ON receipts(date);
CREATE INDEX idx_receipts_store ON receipts(store);
```

### Key Schema Decisions

1. **Normalized Pricing**: Store both original price and normalized price (per kg/L) for consistent comparisons
2. **Flexible Units**: Support various units (kg, g, L, ml, units) with conversion logic
3. **Hierarchical Categories**: Parent-child relationships for category organization (e.g., Dairy > Milk)
4. **Soft Store References**: Store names as text in receipts, but maintain stores table for autocomplete
5. **Audit Trail**: created_at/updated_at timestamps on all tables

---

## Development Phases

### Phase 1: Core MVP (Current Focus)

**Sprint 1: Foundation (Week 1)**
- [x] Project setup with uv
  - [x] Python 3.13 configured
  - [x] Core dependencies added (streamlit, pandas, plotly, sqlalchemy, pydantic)
  - [x] Dev dependencies added (pytest, pytest-cov, black, ruff, mypy)
  - [x] All dependencies installed
  - [x] Basic README.md created
  - [x] Tool configurations in pyproject.toml (black, ruff, mypy, pytest)
  - [x] Directory structure created (src/, tests/, data/, docs/ with __init__.py files)
  - [x] Updated .gitignore for project-specific files
  - [x] Pre-commit hooks configured and installed
  - [x] Makefile created with common development commands
- [x] Database connection module (src/database/connection.py)
  - [x] SQLAlchemy engine, SessionLocal, Base
  - [x] get_db() dependency for session management
  - [x] init_db() for table creation
  - [x] Unit tests with 100% coverage
- [x] Database models (incremental)
  - [x] Store model
  - [x] Category model
  - [x] Receipt model
  - [x] Item model
- [x] CRUD operations
  - [x] Receipt CRUD (create_receipt, get_receipt, get_receipts)
  - [x] Store CRUD (create_store, get_store, get_stores)
  - [x] Category CRUD (create_category, get_category, get_categories)
  - [x] Item CRUD (create_item, get_item, get_items)

**Sprint 2: Data Entry (Week 2)**
- [x] Streamlit app structure
- [x] Receipt entry form with dynamic item rows
- [x] Category management (inline creation in receipt form)
- [x] Data validation (Pydantic models + price normalization utilities)

**Sprint 3: Visualization (Week 3)**
- [x] Receipt history browser with filters
- [x] Price trend charts (line charts over time)
- [x] Store comparison charts
- [x] Category spending breakdown (pie/bar charts)
- [x] Export functionality

**Sprint 4: Edit/Delete (Week 4)**
- [x] Delete receipt CRUD with cascade
- [x] Update receipt with shared helper extraction
- [x] Edit/Delete buttons in receipt history (two-step delete confirmation)
- [x] Receipt form edit mode (pre-fill, update dispatch, cancel)

### Phase 2: OCR Integration (Future)
- Receipt photo upload
- OCR processing pipeline
- Automatic item extraction
- Manual correction interface
- Template learning for different stores

### Phase 3: Advanced Features (Future)
- Price anomaly detection
- Shopping list generation from history
- Budget tracking and alerts
- Mobile companion app (if needed)

---

## Core Features Specification

### 1. Receipt Entry
**Requirements:**
- Date picker (default: today)
- Store selector (autocomplete from history)
- Dynamic item rows (add/remove)
- Per-item fields:
    - Name (text, required)
    - Brand (text, optional)
    - Category (dropdown with search, required)
    - Quantity (number, required)
    - Unit (dropdown: kg, g, L, ml, units)
    - Total price (decimal, required)
    - Price per unit (auto-calculated or manual)
- Total receipt amount (auto-calculated from items)
- Notes (optional)
- Save/Cancel buttons

**Validations:**
- All required fields must be filled
- Quantity > 0
- Prices must be valid decimals
- Date cannot be in future
- Total matches sum of items (with tolerance)

### 2. Receipt History
**Requirements:**
- List view with filters:
    - Date range selector
    - Store multi-select
    - Category filter
    - Text search (item names)
- Sort options: date, total amount, store
- Receipt detail view (modal or new page)
- Edit/Delete actions with confirmation
- Export selected receipts to CSV

### 3. Price Analytics
**Charts Required:**

1. **Price Trends Over Time**
    - Line chart: item price vs date
    - Filter by item name (fuzzy match)
    - Multiple items on same chart
    - Normalized to same unit

2. **Store Comparison**
    - Bar chart: average prices by store
    - Filter by category or item
    - Show price range (min/max)

3. **Category Spending**
    - Pie chart: total spending by category
    - Time period selector
    - Drill-down to subcategories

4. **Monthly Summary**
    - Stacked bar chart: spending by category per month
    - Total spending trend line

**Interactions:**
- Date range selector (last week, month, 3 months, year, custom)
- Category/store filters
- Click chart elements to drill down
- Export chart data to CSV

### 4. Price Normalization Logic
Convert all prices to standard units for comparison:
- Mass: g, kg → kg (1000g = 1kg)
- Volume: ml, L → L (1000ml = 1L)
- Units: keep as-is, cannot normalize

**Algorithm:**
```python
def normalize_price(quantity: float, unit: str, total_price: float) -> tuple[float, str]:
    """
    Returns: (normalized_price, normalized_unit)
    normalized_price is price per kg or L
    """
    if unit in ['g', 'kg']:
        kg = quantity if unit == 'kg' else quantity / 1000
        return (total_price / kg, 'kg')
    elif unit in ['ml', 'L']:
        liters = quantity if unit == 'L' else quantity / 1000
        return (total_price / liters, 'L')
    else:
        # Cannot normalize units/pieces
        return (total_price / quantity, unit)
```

---

## Coding Conventions

### Python Style
- **PEP 8** compliance
- **Type hints** for all function signatures
- **Docstrings** for all modules and public functions (Google style)
- **Max line length**: 100 characters
- **Use `pathlib`** for file paths
- **Use `dataclasses`** or Pydantic models for data structures
- **Use `Iterator[T]`** for simple generators (not `Generator[T, None, None]`)
- **Use library defaults** unless there's a documented reason to deviate
- **Fail loudly**: Raise exceptions on configuration errors, don't use silent fallbacks
- **Auto-create directories**: When writing files, ensure parent directories exist

### Naming Conventions
- Variables/functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

### Database
- Table names: plural, lowercase (e.g., `receipts`, `items`)
- Column names: `snake_case`
- Always use parameterized queries (prevent SQL injection)
- **SQLite for Streamlit**: Use `check_same_thread=False` and `timeout=30` for multi-threading
- **Environment config**: Make debug settings (like `echo`) configurable via environment variables
- **Timestamp defaults**: Use `default=lambda: dt.datetime.now()`, not `default=dt.datetime.now`
- **Shared fixtures**: Put common test fixtures (like `db_session`) in `tests/conftest.py`

### Testing
- Test file names: `test_*.py`
- Test functions: `test_<functionality>`
- Use fixtures for database setup
- Aim for >80% coverage on business logic
- **Test actual exports**: If testing `SessionLocal`, import and test the real object, not a recreated pattern
- **Use in-memory databases**: Use `sqlite:///:memory:` for test isolation, avoid production database
- **Verify behavior, not just existence**: Tests should assert actual behavior (e.g., mock to verify `close()` was called)

### Git Workflow
- **Direct to main**: Commit directly to `main` for solo development velocity
- **Commit messages**: Conventional Commits format
    - `feat: add price normalization`
    - `fix: correct date validation`
    - `docs: update schema documentation`
- **Atomic commits**: Each commit should be a logical, self-contained change with passing tests

---

## Key Technical Decisions

### 1. Why Streamlit over PyQt/Tkinter?
- **Faster development**: Built-in components for forms, charts, tables
- **Python-native**: No need to learn Qt/Tk APIs
- **Good enough UX**: Runs in browser but feels like an app
- **Easy deployment**: Can deploy to Streamlit Cloud later if needed
- **Trade-off**: Not native desktop, requires browser

### 2. Why SQLite over PostgreSQL/MySQL?
- **Local-first**: No server setup, portable database file
- **Zero config**: Works out of the box
- **Easy backup**: Copy single file
- **Sufficient**: Handles thousands of receipts easily
- **Trade-off**: Not suitable for multi-user (not a requirement)

### 3. Why not use pandas for storage?
- **SQL is better**: Query flexibility, relationships, indexes
- **Data integrity**: Foreign keys, constraints
- **Scalability**: Better for 1000+ receipts
- **pandas is still used**: For analysis/visualization layer

### 4. Price normalization approach
- **Store both**: Original and normalized prices
- **Why**: Allows both detailed receipts and easy comparisons
- **Calculation**: Done at insert time, cached in database

---

## Development Guidelines

### Starting a Coding Session
1. Load this context document into Claude Code
2. Reference specific sections as needed
3. Ask Claude to implement specific features from the roadmap
4. Follow test-driven development when appropriate

### When Adding Features
1. Update this document if architecture changes
2. Add tests for new functionality
3. Update schema.md if database changes
4. Consider backward compatibility with existing data

### Before Committing
- [ ] Code follows conventions
- [ ] Tests pass (`pytest`)
- [ ] Type hints are present
- [ ] Docstrings added for new functions
- [ ] No hardcoded paths or credentials

---

## Example Data Model (Python)

```python
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

@dataclass
class Receipt:
    id: Optional[int]
    date: date
    store: str
    total_amount: Decimal
    notes: Optional[str] = None

@dataclass
class Item:
    id: Optional[int]
    receipt_id: int
    name: str
    brand: Optional[str]
    category_id: int
    quantity: Decimal
    unit: str
    price_per_unit: Optional[Decimal]
    total_price: Decimal
    normalized_price: Optional[Decimal]
    normalized_unit: Optional[str]
    notes: Optional[str] = None

@dataclass
class Category:
    id: Optional[int]
    name: str
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None
```

---

## Questions to Resolve

### During Development (Resolved)
- [x] **Multiple currencies?** → Yes, EUR and CHF only. Add currency field to receipts.
- [x] **Item-level discounts?** → Yes. Add original_price + discount fields to items.
- [x] **Receipt photo storage?** → No, skip until OCR phase.
- [x] **Tags in addition to categories?** → No, categories are sufficient.
- [x] **Tax/VAT tracking?** → No, prices are stored as-paid (tax included).

### For Phase 2 (OCR)
- [ ] Which OCR library performs best on grocery receipts?
- [ ] How to handle store-specific receipt formats?
- [ ] Should we build a template learning system?
- [ ] How to handle OCR corrections/feedback loop?

---

## Running the Application

### Initial Setup
```bash
# Create project with uv
uv init grocery-tracker
cd grocery-tracker

# Install dependencies
uv add streamlit pandas plotly sqlalchemy pydantic
uv add --dev pytest pytest-cov black ruff

# Initialize database
uv run python -m src.database.migrations.init_schema

# Run application
uv run streamlit run src/app.py
```

### Development Commands
```bash
# Run tests
uv run pytest

# Format code
uv run black src/

# Lint code
uv run ruff check src/

# Type check
uv run mypy src/
```

---

## Success Metrics (Phase 1)

- [ ] Can add a receipt with 5+ items in <2 minutes
- [ ] Can view price history for any item over time
- [ ] Can compare prices across stores
- [ ] Can export data to CSV for external analysis
- [ ] Database handles 100+ receipts without performance issues
- [ ] App starts in <3 seconds
- [ ] All core features have >80% test coverage

---

## Resources

### Documentation Links
- [Streamlit Docs](https://docs.streamlit.io)
- [Plotly Python Docs](https://plotly.com/python/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org)
- [uv Documentation](https://docs.astral.sh/uv/)

### Useful Libraries
- `streamlit-aggrid`: Advanced data tables (if needed)
- `streamlit-option-menu`: Better navigation
- `plotly-express`: Simpler plotting API

---

## Notes for Claude Code

When helping with this project:

1. **Assume Python 3.11+**: Use modern Python features
2. **Prioritize simplicity**: This is a personal project, avoid over-engineering
3. **Test as you go**: Write tests for business logic
4. **Database first**: Schema changes should be deliberate and documented
5. **UI iteration**: Streamlit allows rapid iteration, don't overthink initial UI
6. **Type safety**: Use type hints and Pydantic for data validation
7. **Riccardo's expertise**: Can handle complex implementations, provide advanced options
8. **Future OCR**: Keep data structures flexible for OCR integration

### When I Ask You To:
- **"Implement X"**: Provide complete, working code with tests
- **"Show me how"**: Explain approach with code examples
- **"Review this"**: Give constructive feedback on code quality
- **"Debug this"**: Analyze and suggest fixes
- **"Refactor this"**: Improve code quality while maintaining functionality

---

**Document Version**: 1.7
**Last Updated**: 2026-02-14
**Status**: Phase 1, Sprint 4 - Complete (Edit/Delete Receipts)
