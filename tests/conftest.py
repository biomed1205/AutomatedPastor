"""Shared test fixtures - NO MOCKS, real implementations only."""
import pytest
import tempfile
import sqlite3
import os


@pytest.fixture(autouse=True)
def reset_auth_between_tests():
    """Reset auth state before and after each test."""
    try:
        from auth import reset_auth_state
        reset_auth_state()
    except ImportError:
        pass  # auth module may not exist yet
    yield
    try:
        from auth import reset_auth_state
        reset_auth_state()
    except ImportError:
        pass


@pytest.fixture
def db_connection():
    """Real in-memory SQLite database for testing."""
    conn = sqlite3.connect(':memory:')
    yield conn
    conn.close()


@pytest.fixture
def temp_dir():
    """Real temporary directory for file operation tests."""
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def app_config(temp_dir):
    """Test configuration with real paths."""
    return {
        'DATABASE': ':memory:',
        'UPLOAD_FOLDER': os.path.join(temp_dir, 'uploads'),
        'EXPORT_FOLDER': os.path.join(temp_dir, 'exports'),
        'TESTING': True
    }
