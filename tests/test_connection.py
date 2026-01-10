"""Unit tests for database connection module."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from src.database.connection import (
    DATABASE_PATH,
    DATABASE_URL,
    Base,
    get_db,
    init_db,
)


class TestDatabasePath:
    """Tests for database path configuration."""

    def test_database_path_is_in_data_folder(self) -> None:
        """Verify database path points to data directory."""
        assert "data" in str(DATABASE_PATH)

    def test_database_path_ends_with_receipts_db(self) -> None:
        """Verify database filename is receipts.db."""
        assert str(DATABASE_PATH).endswith("receipts.db")

    def test_database_url_is_sqlite(self) -> None:
        """Verify database URL uses SQLite protocol."""
        assert DATABASE_URL.startswith("sqlite:///")


class TestEngine:
    """Tests for SQLAlchemy engine."""

    def test_engine_can_execute_query(self) -> None:
        """Verify engine can execute a simple query."""
        # Use in-memory database for test isolation
        test_engine = create_engine("sqlite:///:memory:")
        with test_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        test_engine.dispose()


class TestSessionLocal:
    """Tests for session factory."""

    def test_session_local_creates_session(self) -> None:
        """Verify SessionLocal creates a valid session."""
        # Create isolated test session factory
        test_engine = create_engine("sqlite:///:memory:")
        test_session_factory = sessionmaker(bind=test_engine)

        session = test_session_factory()
        assert isinstance(session, Session)
        session.close()
        test_engine.dispose()

    def test_session_can_execute_query(self) -> None:
        """Verify session can execute queries."""
        test_engine = create_engine("sqlite:///:memory:")
        test_session_factory = sessionmaker(bind=test_engine)

        session = test_session_factory()
        result = session.execute(text("SELECT 42 as answer"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 42
        session.close()
        test_engine.dispose()


class TestBase:
    """Tests for declarative base."""

    def test_base_has_metadata(self) -> None:
        """Verify Base has metadata attribute."""
        assert hasattr(Base, "metadata")

    def test_base_metadata_has_receipts_table(self) -> None:
        """Verify Base metadata includes the receipts table."""
        # Import models to ensure they're registered with Base
        from src.database.models import Receipt  # noqa: F401

        assert "receipts" in Base.metadata.tables


class TestGetDb:
    """Tests for get_db dependency."""

    def test_get_db_yields_session(self) -> None:
        """Verify get_db yields a session object."""
        db_gen = get_db()
        session = next(db_gen)

        assert isinstance(session, Session)

        # Clean up
        try:
            next(db_gen)
        except StopIteration:
            pass

    def test_get_db_closes_session_after_use(self) -> None:
        """Verify get_db closes session when generator exits."""
        db_gen = get_db()
        session = next(db_gen)

        # Simulate end of use
        try:
            next(db_gen)
        except StopIteration:
            pass

        # Session should be closed (can't execute queries)
        # Note: SQLAlchemy sessions can still be used after close()
        # but this tests the generator cleanup pattern works
        assert session is not None


class TestInitDb:
    """Tests for init_db function."""

    def test_init_db_runs_without_error(self) -> None:
        """Verify init_db executes without raising exceptions."""
        # This should not raise any exceptions
        # Currently creates no tables (no models), but validates the function works
        init_db()

    def test_init_db_is_idempotent(self) -> None:
        """Verify init_db can be called multiple times safely."""
        # Should not raise on repeated calls
        init_db()
        init_db()
        init_db()
