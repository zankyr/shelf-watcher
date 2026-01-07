# Grocery Receipt Tracker

Track grocery receipt history, analyze price trends over time, and visualize spending patterns.

## Setup

```bash
# Install dependencies
uv sync --all-extras

# Run the app
uv run streamlit run src/app.py
```

## Development

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

## Tech Stack

- Python 3.13+
- Streamlit (UI)
- SQLite (database)
- Pandas & Plotly (analytics)