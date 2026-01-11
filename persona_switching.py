"""Reviewer persona switching module.

Provides functionality to toggle reviewers in panel chat discussions.
"""
import json


# Default reviewer set
DEFAULT_REVIEWERS = [
    'theological', 'pastoral', 'structural', 'engagement',
    'illustration', 'scripture', 'language'
]

# Reviewer display info
REVIEWER_INFO = {
    'theological': {'name': 'Theological Reviewer', 'display_name': 'Theological'},
    'pastoral': {'name': 'Pastoral Reviewer', 'display_name': 'Pastoral'},
    'structural': {'name': 'Structural Reviewer', 'display_name': 'Structural'},
    'engagement': {'name': 'Engagement Reviewer', 'display_name': 'Engagement'},
    'illustration': {'name': 'Illustration Reviewer', 'display_name': 'Illustration'},
    'scripture': {'name': 'Scripture Reviewer', 'display_name': 'Scripture'},
    'language': {'name': 'Language Reviewer', 'display_name': 'Language'}
}


class InvalidReviewerError(Exception):
    """Raised when an invalid reviewer name is used."""
    pass


class ReviewerConfig:
    """Manages reviewer enabled/disabled state."""

    def __init__(self, conn):
        """Initialize reviewer configuration.

        Args:
            conn: Database connection.
        """
        self.conn = conn
        self._enabled = set()
        self.reviewers = []

    def is_enabled(self, reviewer):
        """Check if a reviewer is enabled.

        Args:
            reviewer: Reviewer identifier.

        Returns:
            bool: True if enabled, False otherwise.
        """
        return reviewer in self._enabled

    def set_all_enabled(self, reviewers):
        """Enable all specified reviewers.

        Args:
            reviewers: List of reviewer identifiers.
        """
        self._enabled = set(reviewers)
        self.reviewers = list(reviewers)

    def set_enabled(self, reviewers):
        """Set which reviewers are enabled.

        Args:
            reviewers: List of reviewer identifiers to enable.
        """
        self._enabled = set(reviewers)
        self.reviewers = list(reviewers)

    def get_enabled(self):
        """Get list of enabled reviewers.

        Returns:
            list: List of enabled reviewer identifiers.
        """
        return list(self._enabled)


def get_default_reviewers():
    """Get the default reviewer set.

    Returns:
        list: Default reviewer identifiers.
    """
    return DEFAULT_REVIEWERS.copy()


def _validate_reviewer(reviewer):
    """Validate a reviewer name.

    Args:
        reviewer: Reviewer identifier.

    Raises:
        InvalidReviewerError: If reviewer is not valid.
    """
    if reviewer not in DEFAULT_REVIEWERS:
        raise InvalidReviewerError(f"Invalid reviewer: {reviewer}")


def enable_reviewer(config, reviewer):
    """Enable a specific reviewer.

    Args:
        config: ReviewerConfig instance.
        reviewer: Reviewer identifier.

    Raises:
        InvalidReviewerError: If reviewer is not valid.
    """
    _validate_reviewer(reviewer)
    config._enabled.add(reviewer)
    if reviewer not in config.reviewers:
        config.reviewers.append(reviewer)


def disable_reviewer(config, reviewer):
    """Disable a specific reviewer.

    Args:
        config: ReviewerConfig instance.
        reviewer: Reviewer identifier.

    Raises:
        InvalidReviewerError: If reviewer is not valid.
    """
    _validate_reviewer(reviewer)
    config._enabled.discard(reviewer)
    if reviewer in config.reviewers:
        config.reviewers.remove(reviewer)


def toggle_reviewer(config, reviewer):
    """Toggle a reviewer's enabled state.

    Args:
        config: ReviewerConfig instance.
        reviewer: Reviewer identifier.

    Returns:
        bool: New enabled state.

    Raises:
        InvalidReviewerError: If reviewer is not valid.
    """
    _validate_reviewer(reviewer)
    if config.is_enabled(reviewer):
        disable_reviewer(config, reviewer)
        return False
    else:
        enable_reviewer(config, reviewer)
        return True


def reset_to_defaults(config):
    """Reset configuration to defaults.

    Args:
        config: ReviewerConfig instance.
    """
    config.set_all_enabled(DEFAULT_REVIEWERS)


# =============================================================================
# Configuration Management
# =============================================================================

class SavedConfig:
    """Represents a saved reviewer configuration."""

    def __init__(self, name, reviewers):
        """Initialize saved configuration.

        Args:
            name: Configuration name.
            reviewers: List of reviewer identifiers.
        """
        self.name = name
        self.reviewers = reviewers


def create_config(conn, name, reviewers):
    """Create a named reviewer configuration.

    Args:
        conn: Database connection.
        name: Configuration name.
        reviewers: List of reviewer identifiers.
    """
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO reviewer_configs (config_name, reviewers) VALUES (?, ?)',
        (name, json.dumps(reviewers))
    )
    conn.commit()


def get_config(conn, name):
    """Get a configuration by name.

    Args:
        conn: Database connection.
        name: Configuration name.

    Returns:
        SavedConfig or None: The configuration if found.
    """
    cursor = conn.cursor()
    cursor.execute(
        'SELECT config_name, reviewers FROM reviewer_configs WHERE config_name = ?',
        (name,)
    )
    row = cursor.fetchone()

    if row:
        reviewers = json.loads(row['reviewers'] if hasattr(row, 'keys') else row[1])
        return SavedConfig(name, reviewers)
    return None


def list_configs(conn):
    """List all configurations.

    Args:
        conn: Database connection.

    Returns:
        list: List of configuration dictionaries.
    """
    cursor = conn.cursor()
    cursor.execute('SELECT config_name, reviewers, created_at FROM reviewer_configs')
    rows = cursor.fetchall()

    configs = []
    for row in rows:
        configs.append({
            'name': row['config_name'] if hasattr(row, 'keys') else row[0],
            'reviewers': json.loads(row['reviewers'] if hasattr(row, 'keys') else row[1]),
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[2]
        })
    return configs


def apply_config(conn, config, config_name):
    """Apply a saved configuration.

    Args:
        conn: Database connection.
        config: ReviewerConfig instance to update.
        config_name: Name of configuration to apply.
    """
    saved = get_config(conn, config_name)
    if saved:
        config.set_enabled(saved.reviewers)


def delete_config(conn, name):
    """Delete a configuration.

    Args:
        conn: Database connection.
        name: Configuration name.
    """
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reviewer_configs WHERE config_name = ?', (name,))
    conn.commit()


def update_config(conn, name, reviewers):
    """Update an existing configuration.

    Args:
        conn: Database connection.
        name: Configuration name.
        reviewers: New list of reviewer identifiers.
    """
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE reviewer_configs SET reviewers = ? WHERE config_name = ?',
        (json.dumps(reviewers), name)
    )
    conn.commit()


# =============================================================================
# User Preferences
# =============================================================================

def save_preference(conn, user_id, enabled_reviewers):
    """Save user's reviewer preference.

    Args:
        conn: Database connection.
        user_id: User identifier.
        enabled_reviewers: List of enabled reviewer identifiers.
    """
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT OR REPLACE INTO user_preferences
           (user_id, preference_key, preference_value, updated_at)
           VALUES (?, 'enabled_reviewers', ?, CURRENT_TIMESTAMP)''',
        (user_id, json.dumps(enabled_reviewers))
    )
    conn.commit()


def load_preference(conn, user_id):
    """Load user's reviewer preference.

    Args:
        conn: Database connection.
        user_id: User identifier.

    Returns:
        list: Enabled reviewer identifiers, or defaults if none saved.
    """
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT preference_value FROM user_preferences
           WHERE user_id = ? AND preference_key = 'enabled_reviewers' ''',
        (user_id,)
    )
    row = cursor.fetchone()

    if row:
        return json.loads(row['preference_value'] if hasattr(row, 'keys') else row[0])
    return DEFAULT_REVIEWERS.copy()


def load_and_apply_preference(conn, config, user_id):
    """Load and apply user preference to config.

    Args:
        conn: Database connection.
        config: ReviewerConfig instance.
        user_id: User identifier.
    """
    enabled = load_preference(conn, user_id)
    config.set_enabled(enabled)


# =============================================================================
# Message Filtering
# =============================================================================

def filter_messages_by_reviewers(messages, enabled):
    """Filter messages to show only enabled reviewers.

    Args:
        messages: List of message dictionaries.
        enabled: List of enabled reviewer identifiers.

    Returns:
        list: Filtered messages.
    """
    enabled_set = set(enabled)
    filtered = []

    for msg in messages:
        sender = msg.get('sender', '')
        sender_type = msg.get('sender_type', 'reviewer')

        # Always include user and system messages
        if sender_type in ('user', 'system'):
            filtered.append(msg)
        elif sender in enabled_set:
            filtered.append(msg)

    return filtered


def apply_filter_to_discussion(conn, discussion_id, config):
    """Apply reviewer filter to a discussion.

    Args:
        conn: Database connection.
        discussion_id: Discussion identifier.
        config: ReviewerConfig instance.
    """
    enabled = config.get_enabled()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE panel_discussions SET active_reviewers = ? WHERE id = ?',
        (json.dumps(enabled), discussion_id)
    )
    conn.commit()


# =============================================================================
# UI Context
# =============================================================================

def prepare_reviewer_ui_context(conn, config=None):
    """Prepare UI context for reviewer toggles.

    Args:
        conn: Database connection.
        config: Optional ReviewerConfig instance.

    Returns:
        dict: Context dictionary for UI rendering.
    """
    reviewers = []

    for identifier in DEFAULT_REVIEWERS:
        info = REVIEWER_INFO.get(identifier, {})
        is_enabled = True

        if config:
            is_enabled = config.is_enabled(identifier)

        reviewers.append({
            'identifier': identifier,
            'name': info.get('name', identifier.title()),
            'display_name': info.get('display_name', identifier.title()),
            'enabled': is_enabled,
            'is_enabled': is_enabled
        })

    return {
        'reviewers': reviewers,
        'total_count': len(reviewers)
    }
