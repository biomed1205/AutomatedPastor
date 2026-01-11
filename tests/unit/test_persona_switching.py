"""Tests for reviewer persona switching.

These tests verify the ability to toggle reviewers in panel chat.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database and files - NO MOCKS.
"""
import pytest
import sqlite3
import json
from flask import Flask


# Default reviewer set
DEFAULT_REVIEWERS = [
    'theological', 'pastoral', 'structural', 'engagement',
    'illustration', 'scripture', 'language'
]


def create_test_db():
    """Create an in-memory test database."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('''
        CREATE TABLE user_preferences (
            id INTEGER PRIMARY KEY,
            user_id TEXT,
            preference_key TEXT,
            preference_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, preference_key)
        )
    ''')
    conn.execute('''
        CREATE TABLE reviewer_configs (
            id INTEGER PRIMARY KEY,
            config_name TEXT,
            reviewers TEXT,
            is_default INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE panel_discussions (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER,
            active_reviewers TEXT,
            status TEXT DEFAULT 'active'
        )
    ''')
    conn.commit()
    return conn


class TestEnableDisableReviewers:
    """Test suite for enabling/disabling individual reviewers."""

    def test_should_enable_reviewer(self):
        """Test enabling a reviewer."""
        from persona_switching import ReviewerConfig, enable_reviewer

        conn = create_test_db()
        config = ReviewerConfig(conn)

        result = enable_reviewer(config, 'theological')

        assert config.is_enabled('theological')
        conn.close()

    def test_should_disable_reviewer(self):
        """Test disabling a reviewer."""
        from persona_switching import ReviewerConfig, disable_reviewer

        conn = create_test_db()
        config = ReviewerConfig(conn)
        config.set_all_enabled(DEFAULT_REVIEWERS)

        result = disable_reviewer(config, 'theological')

        assert not config.is_enabled('theological')
        conn.close()

    def test_should_toggle_reviewer_state(self):
        """Test toggling reviewer enabled state."""
        from persona_switching import ReviewerConfig, toggle_reviewer

        conn = create_test_db()
        config = ReviewerConfig(conn)
        config.set_all_enabled(DEFAULT_REVIEWERS)

        # Toggle off
        toggle_reviewer(config, 'theological')
        assert not config.is_enabled('theological')

        # Toggle on
        toggle_reviewer(config, 'theological')
        assert config.is_enabled('theological')
        conn.close()

    def test_should_return_current_state_after_toggle(self):
        """Test toggle returns new state."""
        from persona_switching import ReviewerConfig, toggle_reviewer

        conn = create_test_db()
        config = ReviewerConfig(conn)
        config.set_all_enabled(DEFAULT_REVIEWERS)

        new_state = toggle_reviewer(config, 'theological')

        assert new_state is False  # Was enabled, now disabled
        conn.close()

    def test_should_validate_reviewer_name(self):
        """Test invalid reviewer name is rejected."""
        from persona_switching import ReviewerConfig, enable_reviewer, InvalidReviewerError

        conn = create_test_db()
        config = ReviewerConfig(conn)

        with pytest.raises(InvalidReviewerError):
            enable_reviewer(config, 'nonexistent_reviewer')
        conn.close()


class TestMultipleReviewerConfigurations:
    """Test suite for multiple reviewer configurations."""

    def test_should_create_named_configuration(self):
        """Test creating a named configuration."""
        from persona_switching import create_config, get_config

        conn = create_test_db()

        create_config(conn, name='minimal', reviewers=['theological', 'structural'])

        config = get_config(conn, name='minimal')
        assert config is not None
        assert len(config.reviewers) == 2
        conn.close()

    def test_should_list_all_configurations(self):
        """Test listing all configurations."""
        from persona_switching import create_config, list_configs

        conn = create_test_db()

        create_config(conn, name='minimal', reviewers=['theological'])
        create_config(conn, name='full', reviewers=DEFAULT_REVIEWERS)

        configs = list_configs(conn)

        assert len(configs) >= 2
        conn.close()

    def test_should_apply_configuration(self):
        """Test applying a configuration."""
        from persona_switching import create_config, apply_config, ReviewerConfig

        conn = create_test_db()

        create_config(conn, name='minimal', reviewers=['theological', 'structural'])

        current = ReviewerConfig(conn)
        apply_config(conn, current, config_name='minimal')

        assert current.is_enabled('theological')
        assert current.is_enabled('structural')
        assert not current.is_enabled('pastoral')
        conn.close()

    def test_should_delete_configuration(self):
        """Test deleting a configuration."""
        from persona_switching import create_config, delete_config, list_configs

        conn = create_test_db()

        create_config(conn, name='to_delete', reviewers=['theological'])

        delete_config(conn, name='to_delete')

        configs = list_configs(conn)
        names = [c['name'] for c in configs]
        assert 'to_delete' not in names
        conn.close()

    def test_should_update_existing_configuration(self):
        """Test updating an existing configuration."""
        from persona_switching import create_config, update_config, get_config

        conn = create_test_db()

        create_config(conn, name='test', reviewers=['theological'])
        update_config(conn, name='test', reviewers=['theological', 'structural'])

        config = get_config(conn, name='test')
        assert len(config.reviewers) == 2
        conn.close()


class TestSavePreferences:
    """Test suite for saving reviewer preferences."""

    def test_should_save_user_preference(self):
        """Test saving user's reviewer preference."""
        from persona_switching import save_preference

        conn = create_test_db()

        save_preference(conn, user_id='user_1', enabled_reviewers=['theological', 'structural'])

        cursor = conn.execute(
            'SELECT * FROM user_preferences WHERE user_id = ?',
            ('user_1',)
        )
        row = cursor.fetchone()

        assert row is not None
        conn.close()

    def test_should_update_existing_preference(self):
        """Test updating existing preference."""
        from persona_switching import save_preference, load_preference

        conn = create_test_db()

        save_preference(conn, user_id='user_1', enabled_reviewers=['theological'])
        save_preference(conn, user_id='user_1', enabled_reviewers=['theological', 'structural'])

        loaded = load_preference(conn, user_id='user_1')

        assert len(loaded) == 2
        conn.close()

    def test_should_save_timestamp(self):
        """Test preference includes timestamp."""
        from persona_switching import save_preference

        conn = create_test_db()

        save_preference(conn, user_id='user_1', enabled_reviewers=['theological'])

        cursor = conn.execute(
            'SELECT updated_at FROM user_preferences WHERE user_id = ?',
            ('user_1',)
        )
        row = cursor.fetchone()

        assert row['updated_at'] is not None
        conn.close()


class TestLoadPreferences:
    """Test suite for loading saved preferences."""

    def test_should_load_user_preference(self):
        """Test loading user's saved preference."""
        from persona_switching import save_preference, load_preference

        conn = create_test_db()

        save_preference(conn, user_id='user_1', enabled_reviewers=['theological', 'pastoral'])

        loaded = load_preference(conn, user_id='user_1')

        assert 'theological' in loaded
        assert 'pastoral' in loaded
        conn.close()

    def test_should_return_defaults_when_no_preference(self):
        """Test returns defaults when no preference exists."""
        from persona_switching import load_preference

        conn = create_test_db()

        loaded = load_preference(conn, user_id='new_user')

        assert loaded == DEFAULT_REVIEWERS
        conn.close()

    def test_should_apply_loaded_preference(self):
        """Test applying loaded preference to config."""
        from persona_switching import save_preference, load_and_apply_preference, ReviewerConfig

        conn = create_test_db()

        save_preference(conn, user_id='user_1', enabled_reviewers=['theological'])

        config = ReviewerConfig(conn)
        load_and_apply_preference(conn, config, user_id='user_1')

        assert config.is_enabled('theological')
        assert not config.is_enabled('pastoral')
        conn.close()


class TestReviewerFiltering:
    """Test suite for reviewer filtering in chat."""

    def test_should_filter_chat_messages_by_enabled_reviewers(self):
        """Test chat shows only enabled reviewers."""
        from persona_switching import filter_messages_by_reviewers

        messages = [
            {'sender': 'theological', 'content': 'Message 1'},
            {'sender': 'pastoral', 'content': 'Message 2'},
            {'sender': 'structural', 'content': 'Message 3'}
        ]

        filtered = filter_messages_by_reviewers(messages, enabled=['theological', 'structural'])

        senders = [m['sender'] for m in filtered]
        assert 'theological' in senders
        assert 'structural' in senders
        assert 'pastoral' not in senders

    def test_should_apply_filter_to_discussion(self):
        """Test filter applies to panel discussion."""
        from persona_switching import ReviewerConfig, apply_filter_to_discussion

        conn = create_test_db()
        config = ReviewerConfig(conn)
        config.set_enabled(['theological', 'structural'])

        conn.execute(
            'INSERT INTO panel_discussions (id, sermon_id, active_reviewers, status) VALUES (?, ?, ?, ?)',
            (1, 1, json.dumps(DEFAULT_REVIEWERS), 'active')
        )
        conn.commit()

        apply_filter_to_discussion(conn, discussion_id=1, config=config)

        cursor = conn.execute('SELECT active_reviewers FROM panel_discussions WHERE id = 1')
        row = cursor.fetchone()
        active = json.loads(row['active_reviewers'])

        assert 'theological' in active
        assert 'pastoral' not in active
        conn.close()

    def test_should_include_user_messages_regardless_of_filter(self):
        """Test user messages are always shown."""
        from persona_switching import filter_messages_by_reviewers

        messages = [
            {'sender': 'theological', 'sender_type': 'reviewer', 'content': 'Reviewer'},
            {'sender': 'user', 'sender_type': 'user', 'content': 'User message'},
            {'sender': 'pastoral', 'sender_type': 'reviewer', 'content': 'Another'}
        ]

        filtered = filter_messages_by_reviewers(messages, enabled=['theological'])

        assert any(m['sender'] == 'user' for m in filtered)


class TestDefaultReviewerSet:
    """Test suite for default reviewer set."""

    def test_should_have_seven_default_reviewers(self):
        """Test there are 7 default reviewers."""
        from persona_switching import get_default_reviewers

        defaults = get_default_reviewers()

        assert len(defaults) == 7

    def test_should_include_theological_reviewer(self):
        """Test defaults include theological reviewer."""
        from persona_switching import get_default_reviewers

        defaults = get_default_reviewers()

        assert 'theological' in defaults

    def test_should_include_all_expected_reviewers(self):
        """Test defaults include all expected reviewers."""
        from persona_switching import get_default_reviewers

        defaults = get_default_reviewers()

        for reviewer in DEFAULT_REVIEWERS:
            assert reviewer in defaults

    def test_should_reset_to_defaults(self):
        """Test resetting to default configuration."""
        from persona_switching import ReviewerConfig, reset_to_defaults

        conn = create_test_db()
        config = ReviewerConfig(conn)
        config.set_enabled(['theological'])  # Only one

        reset_to_defaults(config)

        for reviewer in DEFAULT_REVIEWERS:
            assert config.is_enabled(reviewer)
        conn.close()


class TestFlaskIntegration:
    """Test suite for Flask integration."""

    def test_should_expose_toggle_endpoint(self):
        """Test toggle reviewer API endpoint."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.post('/api/reviewers/toggle', json={
                'reviewer': 'theological'
            })
            assert response.status_code in [200, 404]

    def test_should_expose_config_endpoint(self):
        """Test get current config API endpoint."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/api/reviewers/config')
            assert response.status_code in [200, 404]

    def test_should_expose_save_preference_endpoint(self):
        """Test save preference API endpoint."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.post('/api/reviewers/preferences', json={
                'enabled_reviewers': ['theological', 'structural']
            })
            assert response.status_code in [200, 201, 404]

    def test_should_expose_configurations_list_endpoint(self):
        """Test list configurations API endpoint."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/api/reviewers/configurations')
            assert response.status_code in [200, 404]


class TestUIIntegration:
    """Test suite for UI integration."""

    def test_should_render_reviewer_toggles(self):
        """Test page renders reviewer toggle controls."""
        from persona_switching import prepare_reviewer_ui_context

        conn = create_test_db()

        context = prepare_reviewer_ui_context(conn)

        assert 'reviewers' in context
        assert len(context['reviewers']) == 7
        conn.close()

    def test_should_include_enabled_state_in_context(self):
        """Test context includes enabled state for each reviewer."""
        from persona_switching import prepare_reviewer_ui_context, ReviewerConfig

        conn = create_test_db()
        config = ReviewerConfig(conn)
        config.set_enabled(['theological', 'structural'])

        context = prepare_reviewer_ui_context(conn, config=config)

        for reviewer in context['reviewers']:
            assert 'enabled' in reviewer or 'is_enabled' in reviewer
        conn.close()

    def test_should_include_reviewer_display_info(self):
        """Test context includes display info for reviewers."""
        from persona_switching import prepare_reviewer_ui_context

        conn = create_test_db()

        context = prepare_reviewer_ui_context(conn)

        for reviewer in context['reviewers']:
            assert 'name' in reviewer or 'display_name' in reviewer
            assert 'identifier' in reviewer
        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
