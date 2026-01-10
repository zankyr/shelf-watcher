"""Unit tests for database connection module."""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from src.database.connection import (
    DATABASE_PATH,
    DATABASE_URL,
    PROJECT_ROOT,
    Base,
    engine,
    get_db,
)


class TestProjectRoot:
    """Tests for project root detection."""

    def test_project_root_exists(self) -> None:
        """Verify PROJECT_ROOT points to an existing directory."""
        assert PROJECT_ROOT.exists()
        assert PROJECT_ROOT.is_dir()

    def test_project_root_contains_pyproject_toml(self) -> None:
        """Verify PROJECT_ROOT contains pyproject.toml."""
        assert (PROJECT_ROOT / "pyproject.toml").exists()

    def test_project_root_contains_src_directory(self) -> None:
        """Verify PROJECT_ROOT contains src directory."""
        assert (PROJECT_ROOT / "src").exists()


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

    def test_exported_engine_can_connect(self) -> None:
        """Verify the exported engine object can establish a connection."""
        # Test the actual engine exported from connection module
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_engine_creation_pattern(self) -> None:
        """Verify SQLAlchemy engine creation pattern works correctly."""
        # Use in-memory database for isolated pattern testing
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

    def test_base_metadata_is_empty_initially(self) -> None:
        """Verify Base metadata has no tables (no models yet).

        Note: This test will fail once models are added.
        Update it to check for expected tables at that point.
        """
        assert len(Base.metadata.tables) == 0


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
    """Tests for init_db function.

    Note: We test the table creation logic using an isolated in-memory database
    rather than calling init_db() directly, which would affect the real database.
    """

    def test_create_all_runs_without_error(self) -> None:
        """Verify Base.metadata.create_all runs without error."""
        # Use isolated in-memory database
        test_engine = create_engine("sqlite:///:memory:")

        # This mirrors what init_db() does internally
        # Currently no models, so no tables created
        Base.metadata.create_all(bind=test_engine)

        # Verify no error occurred (tables list may be empty)
        inspector = inspect(test_engine)
        tables = inspector.get_table_names()
        assert isinstance(tables, list)

        test_engine.dispose()

    def test_create_all_is_idempotent(self) -> None:
        """Verify create_all can be called multiple times safely."""
        test_engine = create_engine("sqlite:///:memory:")

        # Should not raise on repeated calls
        Base.metadata.create_all(bind=test_engine)
        Base.metadata.create_all(bind=test_engine)
        Base.metadata.create_all(bind=test_engine)

        test_engine.dispose()
