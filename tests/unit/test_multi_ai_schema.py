"""Tests for multi-AI provider database schema.

TDD: These tests are written FIRST before implementation.
"""
import sqlite3
import pytest
from database import init_db, get_db


class TestMultiAIProviderSchema:
    """Test the new multi-AI provider database tables."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database for testing."""
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)
        return conn

    def test_should_create_ai_providers_table(self, db_conn):
        """Test ai_providers table exists with correct columns."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='ai_providers'"
        )
        assert cursor.fetchone() is not None, "ai_providers table should exist"

        # Check columns
        cursor = db_conn.execute("PRAGMA table_info(ai_providers)")
        columns = {row['name'] for row in cursor.fetchall()}
        expected = {'id', 'provider_name', 'display_name', 'api_key_encrypted',
                   'default_model', 'is_enabled', 'is_default', 'color_primary',
                   'color_bg', 'config_json', 'created_at', 'updated_at'}
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_should_create_content_sources_table(self, db_conn):
        """Test content_sources table exists with correct columns."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='content_sources'"
        )
        assert cursor.fetchone() is not None, "content_sources table should exist"

        cursor = db_conn.execute("PRAGMA table_info(content_sources)")
        columns = {row['name'] for row in cursor.fetchall()}
        expected = {'id', 'content_type', 'content_id', 'provider_id',
                   'model_id', 'generation_params', 'generated_at'}
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_should_create_research_items_table(self, db_conn):
        """Test research_items table exists with correct columns."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='research_items'"
        )
        assert cursor.fetchone() is not None, "research_items table should exist"

        cursor = db_conn.execute("PRAGMA table_info(research_items)")
        columns = {row['name'] for row in cursor.fetchall()}
        expected = {'id', 'sermon_id', 'item_type', 'title', 'content',
                   'source_citation', 'source_url', 'relevance_score',
                   'relevance_reasoning', 'provider_id', 'tags', 'created_at'}
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_should_create_content_versions_table(self, db_conn):
        """Test content_versions table exists with correct columns."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='content_versions'"
        )
        assert cursor.fetchone() is not None, "content_versions table should exist"

        cursor = db_conn.execute("PRAGMA table_info(content_versions)")
        columns = {row['name'] for row in cursor.fetchall()}
        expected = {'id', 'content_type', 'parent_id', 'version_number',
                   'content', 'author', 'change_summary', 'source_id', 'created_at'}
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_should_create_generation_outputs_table(self, db_conn):
        """Test generation_outputs table exists with correct columns."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='generation_outputs'"
        )
        assert cursor.fetchone() is not None, "generation_outputs table should exist"

        cursor = db_conn.execute("PRAGMA table_info(generation_outputs)")
        columns = {row['name'] for row in cursor.fetchall()}
        expected = {'id', 'sermon_id', 'output_type', 'output_index', 'content',
                   'word_count', 'source_id', 'is_selected', 'user_rating', 'created_at'}
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_should_create_content_comments_table(self, db_conn):
        """Test content_comments table exists with correct columns."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='content_comments'"
        )
        assert cursor.fetchone() is not None, "content_comments table should exist"

        cursor = db_conn.execute("PRAGMA table_info(content_comments)")
        columns = {row['name'] for row in cursor.fetchall()}
        expected = {'id', 'content_type', 'content_id', 'parent_comment_id',
                   'author', 'comment_text', 'highlight_start', 'highlight_end',
                   'status', 'created_at'}
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_should_create_revision_requests_table(self, db_conn):
        """Test revision_requests table exists with correct columns."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='revision_requests'"
        )
        assert cursor.fetchone() is not None, "revision_requests table should exist"

        cursor = db_conn.execute("PRAGMA table_info(revision_requests)")
        columns = {row['name'] for row in cursor.fetchall()}
        expected = {'id', 'content_type', 'content_id', 'comment_id',
                   'instructions', 'target_providers', 'status',
                   'created_at', 'completed_at'}
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_should_seed_default_providers(self, db_conn):
        """Test that default AI providers are seeded."""
        cursor = db_conn.execute("SELECT provider_name FROM ai_providers")
        providers = {row['provider_name'] for row in cursor.fetchall()}
        expected = {'claude_cli', 'claude_api', 'openai', 'gemini'}
        assert expected == providers, f"Expected providers: {expected}, got: {providers}"

    def test_should_set_claude_cli_as_default(self, db_conn):
        """Test that claude_cli is the default provider."""
        cursor = db_conn.execute(
            "SELECT provider_name FROM ai_providers WHERE is_default = 1"
        )
        row = cursor.fetchone()
        assert row is not None, "Should have a default provider"
        assert row['provider_name'] == 'claude_cli', "claude_cli should be default"

    def test_should_have_correct_provider_colors(self, db_conn):
        """Test that providers have correct color assignments."""
        cursor = db_conn.execute(
            "SELECT provider_name, color_primary, color_bg FROM ai_providers"
        )
        colors = {row['provider_name']: (row['color_primary'], row['color_bg'])
                  for row in cursor.fetchall()}

        assert colors['claude_cli'] == ('#D97706', '#FEF3C7'), "Claude CLI should be amber"
        assert colors['openai'] == ('#10B981', '#D1FAE5'), "OpenAI should be green"
        assert colors['gemini'] == ('#3B82F6', '#DBEAFE'), "Gemini should be blue"
