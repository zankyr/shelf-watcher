"""Database connection and session management for the Grocery Receipt Tracker.

Provides SQLAlchemy engine, session factory, and declarative base for ORM models.
The database file is stored in the project's data/ directory.
"""

import os
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


def _find_project_root() -> Path:
    """Find the project root by looking for pyproject.toml.

    Traverses up from the current file until pyproject.toml is found.

    Raises:
        RuntimeError: If pyproject.toml cannot be found in any parent directory.
    """
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find project root: no pyproject.toml in any parent directory")


# Project root and database file location
PROJECT_ROOT = _find_project_root()
DATABASE_PATH = PROJECT_ROOT / "data" / "receipts.db"
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# SQLAlchemy engine (set SQLALCHEMY_ECHO=1 for SQL query logging)
# check_same_thread=False is required for Streamlit's multi-threaded environment
_echo = os.getenv("SQLALCHEMY_ECHO", "").lower() in ("1", "true", "yes")
engine = create_engine(
    DATABASE_URL,
    echo=_echo,
    connect_args={"check_same_thread": False},
)

# Session factory
SessionLocal = sessionmaker(bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Iterator[Session]:
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables in the database.

    Raises:
        sqlalchemy.exc.OperationalError: If database file cannot be created
            (e.g., permission denied, disk full, invalid path).
        sqlalchemy.exc.SQLAlchemyError: For other database-related errors.
    """
    Base.metadata.create_all(bind=engine)
