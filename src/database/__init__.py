"""Database package for the Grocery Receipt Tracker.

Provides SQLAlchemy database connection, session management, and model base class.
"""

from src.database.connection import (
    DATABASE_PATH,
    DATABASE_URL,
    PROJECT_ROOT,
    Base,
    SessionLocal,
    engine,
    get_db,
    init_db,
)
from src.database.crud import create_receipt, get_receipt, get_receipts
from src.database.models import Receipt

__all__ = [
    "DATABASE_PATH",
    "DATABASE_URL",
    "PROJECT_ROOT",
    "Base",
    "SessionLocal",
    "engine",
    "get_db",
    "init_db",
    "Receipt",
    "create_receipt",
    "get_receipt",
    "get_receipts",
]
