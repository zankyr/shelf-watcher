"""Database connection and session management for the Grocery Receipt Tracker.

Provides SQLAlchemy engine, session factory, and declarative base for ORM models.
The database file is stored in the project's data/ directory.
"""

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


def _find_project_root() -> Path:
    """Find the project root by looking for pyproject.toml.

    Traverses up from the current file until pyproject.toml is found.
    This is more robust than using relative parent paths.
    """
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    # Fallback: if not found, use the file's grandparent (original behavior)
    return Path(__file__).resolve().parent.parent.parent


# Project root and database file location
PROJECT_ROOT = _find_project_root()
DATABASE_PATH = PROJECT_ROOT / "data" / "receipts.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=False)

# Session factory
SessionLocal = sessionmaker(autoflush=False, bind=engine)

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
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)
