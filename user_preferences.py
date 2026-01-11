"""User Preferences/Settings (Issue #226)

Phase 10: Polish - Item 2

Provides user preferences management:
- Preference storage (set, get, bulk set, get all)
- Sermon generation preferences (defaults, length, theology)
- UI preferences (theme, font size)
- Notification preferences (email, reminders)
- Import/export preferences
"""

import json
from datetime import datetime


def set_preference(conn, user_id, key, value):
    """Set a single preference value.

    Args:
        conn: Database connection.
        user_id: User ID.
        key: Preference key.
        value: Preference value.

    Returns:
        bool: True if set successfully.
    """
    if not key:
        return False

    cursor = conn.cursor()

    # Convert value to string for storage
    if isinstance(value, bool):
        str_value = 'true' if value else 'false'
    else:
        str_value = str(value)

    cursor.execute('SELECT id FROM user_preferences WHERE user_id = ? AND preference_key = ?',
                   (user_id, key))
    existing = cursor.fetchone()

    if existing:
        cursor.execute('''
            UPDATE user_preferences
            SET preference_value = ?, updated_at = ?
            WHERE user_id = ? AND preference_key = ?
        ''', (str_value, datetime.now().isoformat(), user_id, key))
    else:
        cursor.execute('''
            INSERT INTO user_preferences (user_id, preference_key, preference_value)
            VALUES (?, ?, ?)
        ''', (user_id, key, str_value))

    conn.commit()
    return True


def get_preference(conn, user_id, key, default=None):
    """Get a preference value.

    Args:
        conn: Database connection.
        user_id: User ID.
        key: Preference key.
        default: Default value if not found.

    Returns:
        Preference value or default.
    """
    cursor = conn.cursor()

    cursor.execute('''
        SELECT preference_value FROM user_preferences
        WHERE user_id = ? AND preference_key = ?
    ''', (user_id, key))
    row = cursor.fetchone()

    if not row:
        return default

    value = row['preference_value'] if hasattr(row, 'keys') else row[0]

    # Convert boolean strings
    if value == 'true':
        return True
    elif value == 'false':
        return False

    return value


def set_preferences(conn, user_id, prefs):
    """Set multiple preferences at once.

    Args:
        conn: Database connection.
        user_id: User ID.
        prefs: Dict of preference key-value pairs.

    Returns:
        bool: True if all set successfully.
    """
    if not prefs:
        return True

    for key, value in prefs.items():
        set_preference(conn, user_id, key, value)

    return True


def get_all_preferences(conn, user_id):
    """Get all preferences for a user.

    Args:
        conn: Database connection.
        user_id: User ID.

    Returns:
        dict: All preferences.
    """
    cursor = conn.cursor()

    cursor.execute('''
        SELECT preference_key, preference_value FROM user_preferences
        WHERE user_id = ?
    ''', (user_id,))
    rows = cursor.fetchall()

    result = {}
    for row in rows:
        key = row['preference_key'] if hasattr(row, 'keys') else row[0]
        value = row['preference_value'] if hasattr(row, 'keys') else row[1]

        # Convert boolean strings
        if value == 'true':
            result[key] = True
        elif value == 'false':
            result[key] = False
        else:
            result[key] = value

    return result


def get_sermon_preferences(conn, user_id):
    """Get sermon generation preferences.

    Args:
        conn: Database connection.
        user_id: User ID.

    Returns:
        dict: Sermon preferences.
    """
    all_prefs = get_all_preferences(conn, user_id)

    word_count = all_prefs.get('default_length')
    if word_count:
        word_count = int(word_count)
    else:
        word_count = 2200  # Default

    return {
        'word_count': word_count,
        'default_length': word_count,
        'theology': all_prefs.get('theology', 'wesleyan'),
        'tradition': all_prefs.get('theology', 'wesleyan'),
    }


def set_default_length(conn, user_id, word_count):
    """Set default sermon length.

    Args:
        conn: Database connection.
        user_id: User ID.
        word_count: Default word count.

    Returns:
        bool: True if set, False if invalid.
    """
    if word_count <= 0:
        return False

    return set_preference(conn, user_id, 'default_length', word_count)


def set_default_theology(conn, user_id, tradition):
    """Set default theological tradition.

    Args:
        conn: Database connection.
        user_id: User ID.
        tradition: Theological tradition.

    Returns:
        bool: True if set.
    """
    return set_preference(conn, user_id, 'theology', tradition)


def get_ui_preferences(conn, user_id):
    """Get UI preferences.

    Args:
        conn: Database connection.
        user_id: User ID.

    Returns:
        dict: UI preferences.
    """
    all_prefs = get_all_preferences(conn, user_id)

    theme = all_prefs.get('theme', 'light')
    font_size = all_prefs.get('font_size', '16')

    return {
        'theme': theme,
        'font_size': int(font_size) if font_size else 16,
        'fontSize': int(font_size) if font_size else 16,
    }


def set_theme(conn, user_id, theme):
    """Set UI theme.

    Args:
        conn: Database connection.
        user_id: User ID.
        theme: Theme name (light, dark, system).

    Returns:
        bool: True if set, False if invalid.
    """
    valid_themes = ['light', 'dark', 'system']
    if theme not in valid_themes:
        return False

    return set_preference(conn, user_id, 'theme', theme)


def set_font_size(conn, user_id, size):
    """Set font size preference.

    Args:
        conn: Database connection.
        user_id: User ID.
        size: Font size in pixels.

    Returns:
        bool: True if set, False if invalid.
    """
    if size < 10 or size > 48:
        return False

    return set_preference(conn, user_id, 'font_size', size)


def get_notification_preferences(conn, user_id):
    """Get notification preferences.

    Args:
        conn: Database connection.
        user_id: User ID.

    Returns:
        dict: Notification preferences.
    """
    all_prefs = get_all_preferences(conn, user_id)

    email_enabled = all_prefs.get('email_enabled', False)
    reminder_days = all_prefs.get('reminder_days', '3')

    return {
        'email_enabled': email_enabled,
        'email': email_enabled,
        'reminder_days': int(reminder_days) if reminder_days else 3,
        'reminderDays': int(reminder_days) if reminder_days else 3,
    }


def set_email_notifications(conn, user_id, enabled):
    """Enable or disable email notifications.

    Args:
        conn: Database connection.
        user_id: User ID.
        enabled: True to enable, False to disable.

    Returns:
        bool: True if set.
    """
    return set_preference(conn, user_id, 'email_enabled', enabled)


def set_reminder_days(conn, user_id, days):
    """Set sermon reminder days before Sunday.

    Args:
        conn: Database connection.
        user_id: User ID.
        days: Number of days before Sunday.

    Returns:
        bool: True if set, False if invalid.
    """
    if days <= 0:
        return False

    return set_preference(conn, user_id, 'reminder_days', days)


def export_preferences(conn, user_id):
    """Export preferences as JSON.

    Args:
        conn: Database connection.
        user_id: User ID.

    Returns:
        str: JSON string of preferences.
    """
    prefs = get_all_preferences(conn, user_id)
    return json.dumps(prefs, indent=2)


def import_preferences(conn, user_id, json_data):
    """Import preferences from JSON.

    Args:
        conn: Database connection.
        user_id: User ID.
        json_data: JSON string of preferences.

    Returns:
        bool: True if imported, False if invalid.
    """
    try:
        prefs = json.loads(json_data)
    except json.JSONDecodeError:
        return False

    if not isinstance(prefs, dict):
        return False

    return set_preferences(conn, user_id, prefs)


def reset_to_defaults(conn, user_id):
    """Reset all preferences to defaults.

    Args:
        conn: Database connection.
        user_id: User ID.

    Returns:
        bool: True if reset.
    """
    cursor = conn.cursor()

    cursor.execute('DELETE FROM user_preferences WHERE user_id = ?', (user_id,))
    conn.commit()

    return True
