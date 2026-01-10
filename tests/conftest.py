"""Shared pytest fixtures for all tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.connection import Base


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
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()
    engine.dispose()
