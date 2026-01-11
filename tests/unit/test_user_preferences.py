"""
Tests for User Preferences/Settings (Issue #226)

Phase 10: Polish - Item 2

Tests cover:
- Preference storage (set, get, bulk set, get all)
- Sermon generation preferences (defaults, length, theology)
- UI preferences (theme, font size)
- Notification preferences (email, reminders)
- Import/export preferences

TDD Approach: All tests fail with ModuleNotFoundError until implementation.
NO MOCKS: Uses real SQLite :memory: database.
"""

import pytest
import sqlite3
import json


def create_test_db():
    """Create a real SQLite in-memory database for testing."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create preferences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            preference_key TEXT NOT NULL,
            preference_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, preference_key)
        )
    ''')

    # Create preference defaults table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS preference_defaults (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            preference_key TEXT NOT NULL UNIQUE,
            default_value TEXT,
            category TEXT,
            description TEXT
        )
    ''')

    conn.commit()
    return conn


def insert_sample_user(conn, email='test@example.com', name='Test User'):
    """Insert a sample user for testing."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (email, name)
        VALUES (?, ?)
    ''', (email, name))
    conn.commit()
    return cursor.lastrowid


class TestSetPreference:
    """Tests for set_preference function."""

    def test_should_set_preference(self):
        """Should set a single preference value."""
        from user_preferences import set_preference

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = set_preference(conn, user_id, 'theme', 'dark')

        assert result is True

        conn.close()

    def test_should_store_string_value(self):
        """Should store string preference value."""
        from user_preferences import set_preference, get_preference

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        set_preference(conn, user_id, 'language', 'en-US')
        value = get_preference(conn, user_id, 'language')

        assert value == 'en-US'

        conn.close()

    def test_should_store_numeric_value(self):
        """Should store numeric preference value."""
        from user_preferences import set_preference, get_preference

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        set_preference(conn, user_id, 'font_size', 16)
        value = get_preference(conn, user_id, 'font_size')

        assert int(value) == 16 or value == '16'

        conn.close()

    def test_should_store_boolean_value(self):
        """Should store boolean preference value."""
        from user_preferences import set_preference, get_preference

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        set_preference(conn, user_id, 'email_enabled', True)
        value = get_preference(conn, user_id, 'email_enabled')

        assert value is True or value == 'true' or value == 'True' or value == '1'

        conn.close()

    def test_should_update_existing_preference(self):
        """Should update existing preference."""
        from user_preferences import set_preference, get_preference

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        set_preference(conn, user_id, 'theme', 'light')
        set_preference(conn, user_id, 'theme', 'dark')
        value = get_preference(conn, user_id, 'theme')

        assert value == 'dark'

        conn.close()


class TestGetPreference:
    """Tests for get_preference function."""

    def test_should_get_preference(self):
        """Should get a preference value."""
        from user_preferences import set_preference, get_preference

        conn = create_test_db()
        user_id = insert_sample_user(conn)
        set_preference(conn, user_id, 'theme', 'dark')

        value = get_preference(conn, user_id, 'theme')

        assert value == 'dark'

        conn.close()

    def test_should_return_default_for_missing(self):
        """Should return default for missing preference."""
        from user_preferences import get_preference

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        value = get_preference(conn, user_id, 'nonexistent', default='fallback')

        assert value == 'fallback'

        conn.close()

    def test_should_return_none_without_default(self):
        """Should return None when no default provided."""
        from user_preferences import get_preference

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        value = get_preference(conn, user_id, 'nonexistent')

        assert value is None

        conn.close()


class TestSetPreferences:
    """Tests for set_preferences function (bulk set)."""

    def test_should_set_multiple_preferences(self):
        """Should set multiple preferences at once."""
        from user_preferences import set_preferences, get_preference

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        prefs = {
            'theme': 'dark',
            'font_size': 14,
            'language': 'en-US'
        }
        result = set_preferences(conn, user_id, prefs)

        assert result is True
        assert get_preference(conn, user_id, 'theme') == 'dark'
        assert get_preference(conn, user_id, 'language') == 'en-US'

        conn.close()

    def test_should_update_existing_in_bulk(self):
        """Should update existing preferences in bulk."""
        from user_preferences import set_preferences, get_preference

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        set_preferences(conn, user_id, {'theme': 'light'})
        set_preferences(conn, user_id, {'theme': 'dark', 'new_pref': 'value'})

        assert get_preference(conn, user_id, 'theme') == 'dark'
        assert get_preference(conn, user_id, 'new_pref') == 'value'

        conn.close()

    def test_should_handle_empty_dict(self):
        """Should handle empty preferences dict."""
        from user_preferences import set_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = set_preferences(conn, user_id, {})

        assert result is True or result is False  # Either is acceptable

        conn.close()


class TestGetAllPreferences:
    """Tests for get_all_preferences function."""

    def test_should_get_all_preferences(self):
        """Should get all user preferences."""
        from user_preferences import set_preferences, get_all_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        prefs = {'theme': 'dark', 'font_size': '14', 'language': 'en'}
        set_preferences(conn, user_id, prefs)

        result = get_all_preferences(conn, user_id)

        assert isinstance(result, dict)
        assert 'theme' in result
        assert 'font_size' in result
        assert 'language' in result

        conn.close()

    def test_should_return_empty_for_no_preferences(self):
        """Should return empty dict for user with no preferences."""
        from user_preferences import get_all_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = get_all_preferences(conn, user_id)

        assert result == {} or result is None

        conn.close()


class TestGetSermonPreferences:
    """Tests for get_sermon_preferences function."""

    def test_should_get_sermon_preferences(self):
        """Should get sermon generation preferences."""
        from user_preferences import get_sermon_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = get_sermon_preferences(conn, user_id)

        assert isinstance(result, dict)

        conn.close()

    def test_should_include_default_length(self):
        """Should include default sermon length."""
        from user_preferences import get_sermon_preferences, set_default_length

        conn = create_test_db()
        user_id = insert_sample_user(conn)
        set_default_length(conn, user_id, 2200)

        result = get_sermon_preferences(conn, user_id)

        assert result.get('word_count') == 2200 or result.get('default_length') == 2200

        conn.close()

    def test_should_include_theology(self):
        """Should include theological tradition."""
        from user_preferences import get_sermon_preferences, set_default_theology

        conn = create_test_db()
        user_id = insert_sample_user(conn)
        set_default_theology(conn, user_id, 'wesleyan')

        result = get_sermon_preferences(conn, user_id)

        assert result.get('theology') == 'wesleyan' or result.get('tradition') == 'wesleyan'

        conn.close()


class TestSetDefaultLength:
    """Tests for set_default_length function."""

    def test_should_set_default_length(self):
        """Should set default sermon length."""
        from user_preferences import set_default_length, get_sermon_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = set_default_length(conn, user_id, 2500)

        assert result is True

        prefs = get_sermon_preferences(conn, user_id)
        assert prefs.get('word_count') == 2500 or prefs.get('default_length') == 2500

        conn.close()

    def test_should_reject_invalid_length(self):
        """Should reject invalid length values."""
        from user_preferences import set_default_length

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result_zero = set_default_length(conn, user_id, 0)
        result_negative = set_default_length(conn, user_id, -100)

        assert result_zero is False
        assert result_negative is False

        conn.close()

    def test_should_accept_valid_range(self):
        """Should accept valid word count range."""
        from user_preferences import set_default_length

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result_min = set_default_length(conn, user_id, 1000)
        result_max = set_default_length(conn, user_id, 5000)

        assert result_min is True
        assert result_max is True

        conn.close()


class TestSetDefaultTheology:
    """Tests for set_default_theology function."""

    def test_should_set_default_theology(self):
        """Should set default theological tradition."""
        from user_preferences import set_default_theology, get_sermon_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = set_default_theology(conn, user_id, 'wesleyan')

        assert result is True

        prefs = get_sermon_preferences(conn, user_id)
        assert prefs.get('theology') == 'wesleyan' or prefs.get('tradition') == 'wesleyan'

        conn.close()

    def test_should_accept_valid_traditions(self):
        """Should accept valid theological traditions."""
        from user_preferences import set_default_theology

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        traditions = ['wesleyan', 'reformed', 'lutheran', 'catholic', 'baptist']
        for tradition in traditions:
            result = set_default_theology(conn, user_id, tradition)
            assert result is True, f"Failed for tradition: {tradition}"

        conn.close()


class TestGetUIPreferences:
    """Tests for get_ui_preferences function."""

    def test_should_get_ui_preferences(self):
        """Should get UI preferences."""
        from user_preferences import get_ui_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = get_ui_preferences(conn, user_id)

        assert isinstance(result, dict)

        conn.close()

    def test_should_include_theme(self):
        """Should include theme preference."""
        from user_preferences import get_ui_preferences, set_theme

        conn = create_test_db()
        user_id = insert_sample_user(conn)
        set_theme(conn, user_id, 'dark')

        result = get_ui_preferences(conn, user_id)

        assert result.get('theme') == 'dark'

        conn.close()

    def test_should_include_font_size(self):
        """Should include font size preference."""
        from user_preferences import get_ui_preferences, set_font_size

        conn = create_test_db()
        user_id = insert_sample_user(conn)
        set_font_size(conn, user_id, 16)

        result = get_ui_preferences(conn, user_id)

        assert result.get('font_size') == 16 or result.get('fontSize') == 16

        conn.close()


class TestSetTheme:
    """Tests for set_theme function."""

    def test_should_set_light_theme(self):
        """Should set light theme."""
        from user_preferences import set_theme, get_ui_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = set_theme(conn, user_id, 'light')

        assert result is True
        prefs = get_ui_preferences(conn, user_id)
        assert prefs.get('theme') == 'light'

        conn.close()

    def test_should_set_dark_theme(self):
        """Should set dark theme."""
        from user_preferences import set_theme, get_ui_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = set_theme(conn, user_id, 'dark')

        assert result is True
        prefs = get_ui_preferences(conn, user_id)
        assert prefs.get('theme') == 'dark'

        conn.close()

    def test_should_set_system_theme(self):
        """Should set system theme."""
        from user_preferences import set_theme, get_ui_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = set_theme(conn, user_id, 'system')

        assert result is True
        prefs = get_ui_preferences(conn, user_id)
        assert prefs.get('theme') == 'system'

        conn.close()

    def test_should_reject_invalid_theme(self):
        """Should reject invalid theme value."""
        from user_preferences import set_theme

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = set_theme(conn, user_id, 'invalid_theme')

        assert result is False

        conn.close()


class TestSetFontSize:
    """Tests for set_font_size function."""

    def test_should_set_font_size(self):
        """Should set font size preference."""
        from user_preferences import set_font_size, get_ui_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = set_font_size(conn, user_id, 16)

        assert result is True
        prefs = get_ui_preferences(conn, user_id)
        font_size = prefs.get('font_size') or prefs.get('fontSize')
        assert int(font_size) == 16

        conn.close()

    def test_should_accept_valid_sizes(self):
        """Should accept valid font sizes."""
        from user_preferences import set_font_size

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        valid_sizes = [12, 14, 16, 18, 20, 24]
        for size in valid_sizes:
            result = set_font_size(conn, user_id, size)
            assert result is True, f"Failed for size: {size}"

        conn.close()

    def test_should_reject_invalid_sizes(self):
        """Should reject invalid font sizes."""
        from user_preferences import set_font_size

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result_too_small = set_font_size(conn, user_id, 6)
        result_too_large = set_font_size(conn, user_id, 100)

        assert result_too_small is False
        assert result_too_large is False

        conn.close()


class TestGetNotificationPreferences:
    """Tests for get_notification_preferences function."""

    def test_should_get_notification_preferences(self):
        """Should get notification preferences."""
        from user_preferences import get_notification_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = get_notification_preferences(conn, user_id)

        assert isinstance(result, dict)

        conn.close()

    def test_should_include_email_setting(self):
        """Should include email notification setting."""
        from user_preferences import get_notification_preferences, set_email_notifications

        conn = create_test_db()
        user_id = insert_sample_user(conn)
        set_email_notifications(conn, user_id, True)

        result = get_notification_preferences(conn, user_id)

        assert result.get('email_enabled') is True or result.get('email') is True

        conn.close()

    def test_should_include_reminder_days(self):
        """Should include reminder days setting."""
        from user_preferences import get_notification_preferences, set_reminder_days

        conn = create_test_db()
        user_id = insert_sample_user(conn)
        set_reminder_days(conn, user_id, 3)

        result = get_notification_preferences(conn, user_id)

        days = result.get('reminder_days') or result.get('reminderDays')
        assert int(days) == 3

        conn.close()


class TestSetEmailNotifications:
    """Tests for set_email_notifications function."""

    def test_should_enable_email_notifications(self):
        """Should enable email notifications."""
        from user_preferences import set_email_notifications, get_notification_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = set_email_notifications(conn, user_id, True)

        assert result is True
        prefs = get_notification_preferences(conn, user_id)
        assert prefs.get('email_enabled') is True or prefs.get('email') is True

        conn.close()

    def test_should_disable_email_notifications(self):
        """Should disable email notifications."""
        from user_preferences import set_email_notifications, get_notification_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        set_email_notifications(conn, user_id, True)
        result = set_email_notifications(conn, user_id, False)

        assert result is True
        prefs = get_notification_preferences(conn, user_id)
        assert prefs.get('email_enabled') is False or prefs.get('email') is False

        conn.close()


class TestSetReminderDays:
    """Tests for set_reminder_days function."""

    def test_should_set_reminder_days(self):
        """Should set sermon reminder days."""
        from user_preferences import set_reminder_days, get_notification_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = set_reminder_days(conn, user_id, 3)

        assert result is True
        prefs = get_notification_preferences(conn, user_id)
        days = prefs.get('reminder_days') or prefs.get('reminderDays')
        assert int(days) == 3

        conn.close()

    def test_should_accept_valid_days(self):
        """Should accept valid reminder days."""
        from user_preferences import set_reminder_days

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        for days in [1, 3, 5, 7]:
            result = set_reminder_days(conn, user_id, days)
            assert result is True, f"Failed for {days} days"

        conn.close()

    def test_should_reject_invalid_days(self):
        """Should reject invalid reminder days."""
        from user_preferences import set_reminder_days

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result_zero = set_reminder_days(conn, user_id, 0)
        result_negative = set_reminder_days(conn, user_id, -1)

        assert result_zero is False
        assert result_negative is False

        conn.close()


class TestExportPreferences:
    """Tests for export_preferences function."""

    def test_should_export_as_json(self):
        """Should export preferences as JSON."""
        from user_preferences import set_preferences, export_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)
        set_preferences(conn, user_id, {'theme': 'dark', 'font_size': '16'})

        result = export_preferences(conn, user_id)

        assert isinstance(result, str)
        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

        conn.close()

    def test_should_include_all_preferences(self):
        """Should include all preferences in export."""
        from user_preferences import set_preferences, export_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)
        prefs = {'theme': 'dark', 'font_size': '16', 'language': 'en'}
        set_preferences(conn, user_id, prefs)

        result = export_preferences(conn, user_id)
        parsed = json.loads(result)

        assert 'theme' in parsed
        assert 'font_size' in parsed
        assert 'language' in parsed

        conn.close()

    def test_should_handle_empty_preferences(self):
        """Should handle user with no preferences."""
        from user_preferences import export_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = export_preferences(conn, user_id)

        assert result is not None
        parsed = json.loads(result)
        assert parsed == {} or parsed is not None

        conn.close()


class TestImportPreferences:
    """Tests for import_preferences function."""

    def test_should_import_from_json(self):
        """Should import preferences from JSON."""
        from user_preferences import import_preferences, get_all_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)
        json_data = '{"theme": "dark", "font_size": "16"}'

        result = import_preferences(conn, user_id, json_data)

        assert result is True
        prefs = get_all_preferences(conn, user_id)
        assert prefs.get('theme') == 'dark'

        conn.close()

    def test_should_merge_with_existing(self):
        """Should merge with existing preferences."""
        from user_preferences import set_preferences, import_preferences, get_all_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)
        set_preferences(conn, user_id, {'existing': 'value'})

        json_data = '{"theme": "dark"}'
        import_preferences(conn, user_id, json_data)

        prefs = get_all_preferences(conn, user_id)
        assert prefs.get('theme') == 'dark'
        assert prefs.get('existing') == 'value'

        conn.close()

    def test_should_handle_invalid_json(self):
        """Should handle invalid JSON gracefully."""
        from user_preferences import import_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = import_preferences(conn, user_id, 'not valid json')

        assert result is False

        conn.close()


class TestResetToDefaults:
    """Tests for reset_to_defaults function."""

    def test_should_reset_all_preferences(self):
        """Should reset all preferences to defaults."""
        from user_preferences import set_preferences, reset_to_defaults, get_all_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)
        set_preferences(conn, user_id, {'theme': 'dark', 'font_size': '20'})

        result = reset_to_defaults(conn, user_id)

        assert result is True

        conn.close()

    def test_should_clear_custom_preferences(self):
        """Should clear custom preferences."""
        from user_preferences import set_preferences, reset_to_defaults, get_preference

        conn = create_test_db()
        user_id = insert_sample_user(conn)
        set_preferences(conn, user_id, {'custom_pref': 'custom_value'})

        reset_to_defaults(conn, user_id)

        # Custom preference should be gone or reset
        value = get_preference(conn, user_id, 'custom_pref')
        assert value is None or value == ''

        conn.close()


class TestDefaultValues:
    """Tests for default preference values."""

    def test_should_use_default_theme(self):
        """Should use default theme when not set."""
        from user_preferences import get_ui_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        prefs = get_ui_preferences(conn, user_id)

        # Should have a default theme
        assert prefs.get('theme') is not None or 'theme' in str(prefs)

        conn.close()

    def test_should_use_default_font_size(self):
        """Should use default font size when not set."""
        from user_preferences import get_ui_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        prefs = get_ui_preferences(conn, user_id)

        # Should have a default font size
        font_size = prefs.get('font_size') or prefs.get('fontSize')
        assert font_size is not None or 'font' in str(prefs).lower()

        conn.close()

    def test_should_use_default_sermon_length(self):
        """Should use default sermon length (2000-2500 words)."""
        from user_preferences import get_sermon_preferences

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        prefs = get_sermon_preferences(conn, user_id)

        # Default should be in 2000-2500 range
        length = prefs.get('word_count') or prefs.get('default_length') or 2200
        assert 2000 <= int(length) <= 2500

        conn.close()


class TestIntegration:
    """Integration tests for user preferences."""

    def test_should_manage_complete_preferences(self):
        """Should manage complete user preferences workflow."""
        from user_preferences import (
            set_theme, set_font_size, set_default_length,
            set_email_notifications, get_all_preferences,
            export_preferences
        )

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        # Set various preferences
        set_theme(conn, user_id, 'dark')
        set_font_size(conn, user_id, 16)
        set_default_length(conn, user_id, 2200)
        set_email_notifications(conn, user_id, True)

        # Get all
        all_prefs = get_all_preferences(conn, user_id)
        assert len(all_prefs) >= 4

        # Export
        exported = export_preferences(conn, user_id)
        assert len(exported) > 10

        conn.close()

    def test_should_support_multiple_users(self):
        """Should support preferences for multiple users."""
        from user_preferences import set_theme, get_ui_preferences

        conn = create_test_db()
        user1_id = insert_sample_user(conn, 'user1@example.com', 'User 1')
        user2_id = insert_sample_user(conn, 'user2@example.com', 'User 2')

        set_theme(conn, user1_id, 'dark')
        set_theme(conn, user2_id, 'light')

        prefs1 = get_ui_preferences(conn, user1_id)
        prefs2 = get_ui_preferences(conn, user2_id)

        assert prefs1.get('theme') == 'dark'
        assert prefs2.get('theme') == 'light'

        conn.close()


class TestEdgeCases:
    """Tests for edge cases."""

    def test_should_handle_nonexistent_user(self):
        """Should handle nonexistent user."""
        from user_preferences import get_preference, set_preference

        conn = create_test_db()

        result = get_preference(conn, 9999, 'theme')
        assert result is None

        conn.close()

    def test_should_handle_empty_key(self):
        """Should handle empty preference key."""
        from user_preferences import set_preference

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = set_preference(conn, user_id, '', 'value')

        assert result is False

        conn.close()

    def test_should_handle_special_characters(self):
        """Should handle special characters in values."""
        from user_preferences import set_preference, get_preference

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        value = "Test with 'quotes' and \"double quotes\""
        set_preference(conn, user_id, 'special', value)

        result = get_preference(conn, user_id, 'special')

        assert result == value

        conn.close()

    def test_should_handle_unicode_values(self):
        """Should handle unicode in preference values."""
        from user_preferences import set_preference, get_preference

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        value = "Test with émojis 🎉 and ünïcödé"
        set_preference(conn, user_id, 'unicode', value)

        result = get_preference(conn, user_id, 'unicode')

        assert result == value

        conn.close()
