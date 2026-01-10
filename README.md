# Grocery Receipt Tracker

Track grocery receipt history, analyze price trends over time, and visualize spending patterns.

## Setup

```bash
# Install all dependencies (including dev tools)
make dev

# Install pre-commit hooks (automatically run linters before commits)
uv run pre-commit install

# Run the app
make run
```

## Development

Quick commands using Makefile:

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

Or use uv commands directly:

```bash
uv run pytest
uv run black src/ tests/
uv run ruff check src/ tests/
uv run mypy src/
```

## Tech Stack

- Python 3.13+
- Streamlit (UI)
- SQLite (database)
- Pandas & Plotly (analytics)