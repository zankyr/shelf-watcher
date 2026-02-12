"""Shared pytest fixtures for all tests."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from src.database.connection import Base
from src.database.models import (
    Category,  # noqa: F401 - Ensure model is registered with Base
    Item,  # noqa: F401 - Ensure model is registered with Base
    Receipt,  # noqa: F401 - Ensure model is registered with Base
    Store,  # noqa: F401 - Ensure model is registered with Base
)


@pytest.fixture
def db_session():
    """Create a fresh in-memory database for each test.

    This fixture:
    - Creates an isolated in-memory SQLite database
    - Creates all tables defined in Base.metadata
    - Yields a session for test use
    - Cleans up session and engine after test
    """
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()
    engine.dispose()
