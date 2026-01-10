"""Unit tests for database connection module."""

from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from src.database.connection import (
    DATABASE_PATH,
    DATABASE_URL,
    PROJECT_ROOT,
    Base,
    SessionLocal,
    _find_project_root,
    engine,
    get_db,
    init_db,
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

    def test_find_project_root_raises_when_pyproject_not_found(self) -> None:
        """Verify RuntimeError is raised when pyproject.toml cannot be found."""
        with patch("src.database.connection.Path") as mock_path:
            # Mock Path(__file__).resolve().parent to return a mock path
            mock_current = mock_path.return_value.resolve.return_value.parent
            # Make the path traversal reach root (parent equals self)
            mock_current.parent = mock_current
            # pyproject.toml never exists
            mock_current.__truediv__ = lambda path_obj, x: mock_path.return_value
            mock_path.return_value.exists.return_value = False

            with pytest.raises(RuntimeError, match="Could not find project root"):
                _find_project_root()


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
        """Verify the exported engine object can establish a connection.

        Note: This is an intentional integration test using the production engine
        to verify the actual configuration (path resolution, SQLite settings).
        The query is read-only and does not access application tables.
        """
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

    def test_exported_session_local_creates_session(self) -> None:
        """Verify the exported SessionLocal creates a valid session.

        Note: Integration test using production session factory to verify
        actual configuration. Query is read-only and does not access
        application tables.
        """
        session = SessionLocal()
        assert isinstance(session, Session)
        # Verify session is functional with read-only query
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1
        session.close()

    def test_session_factory_pattern(self) -> None:
        """Verify sessionmaker pattern works correctly in isolation."""
        test_engine = create_engine("sqlite:///:memory:")
        test_session_factory = sessionmaker(bind=test_engine)

        session = test_session_factory()
        assert isinstance(session, Session)
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

    def test_base_metadata_tables_is_mapping(self) -> None:
        """Verify Base.metadata.tables is a valid mapping."""
        assert hasattr(Base.metadata, "tables")
        # tables should be dict-like (works whether empty or with models)
        assert hasattr(Base.metadata.tables, "keys")


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
        """Verify get_db calls close() on session when generator exits."""
        with patch("src.database.connection.SessionLocal") as mock_session_local:
            mock_session = mock_session_local.return_value

            db_gen = get_db()
            next(db_gen)

            # close() should not be called yet
            mock_session.close.assert_not_called()

            # Exhaust the generator
            try:
                next(db_gen)
            except StopIteration:
                pass

            # Verify close() was called
            mock_session.close.assert_called_once()


class TestInitDb:
    """Tests for init_db function."""

    def test_init_db_calls_create_all_with_engine(self) -> None:
        """Verify init_db calls Base.metadata.create_all with the engine."""
        with patch.object(Base.metadata, "create_all") as mock_create_all:
            init_db()
            mock_create_all.assert_called_once_with(bind=engine)

    def test_create_all_runs_without_error(self) -> None:
        """Verify Base.metadata.create_all runs without error."""
        # Use isolated in-memory database for pattern testing
        test_engine = create_engine("sqlite:///:memory:")

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
