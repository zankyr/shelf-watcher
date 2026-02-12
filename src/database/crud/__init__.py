"""CRUD operations package."""

from src.database.crud.receipt import create_receipt, get_receipt, get_receipts
from src.database.crud.store import create_store, get_store, get_stores

__all__ = [
    "create_receipt",
    "get_receipt",
    "get_receipts",
    "create_store",
    "get_store",
    "get_stores",
]
