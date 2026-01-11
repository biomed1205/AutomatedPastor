"""Moderation controls for panel discussions.

Provides user ability to guide panel discussions.
"""
from datetime import datetime


class DiscussionAlreadyEndedError(Exception):
    """Raised when trying to end an already ended discussion."""
    pass


class DiscussionEndedError(Exception):
    """Raised when trying to modify an ended discussion."""
    pass


class PermissionDeniedError(Exception):
    """Raised when user lacks permission for moderation action."""
    pass


def _check_permission(conn, user_id):
    """Check if user has moderation permission.

    Args:
        conn: Database connection.
        user_id: User ID to check.

    Raises:
        PermissionDeniedError: If user lacks permission.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        raise PermissionDeniedError("User not found")

    role = row[0] if isinstance(row, tuple) else row['role']

    if role not in ('owner', 'admin'):
        raise PermissionDeniedError(f"User role '{role}' cannot moderate")


def _get_discussion_status(conn, discussion_id):
    """Get discussion status.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.

    Returns:
        str: Discussion status.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM panel_discussions WHERE id = ?", (discussion_id,))
    row = cursor.fetchone()

    if not row:
        return None

    return row[0] if isinstance(row, tuple) else row['status']


def _log_action(conn, discussion_id, action_type, target=None, details=None):
    """Log a moderation action.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.
        action_type: Type of action (e.g., 'end_discussion', 'redirect', 'mute_reviewer').
        target: Target of the action (e.g., reviewer name).
        details: Additional details (e.g., new topic).
    """
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO moderation_actions (discussion_id, action_type, target, details)
           VALUES (?, ?, ?, ?)""",
        (discussion_id, action_type, target, details)
    )
    conn.commit()


def end_discussion(conn, discussion_id, user_id=None, check_permission=False):
    """End an active discussion.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion to end.
        user_id: ID of the user performing the action.
        check_permission: Whether to check user permission.

    Returns:
        dict: Result with status.

    Raises:
        DiscussionAlreadyEndedError: If discussion is already ended.
        PermissionDeniedError: If user lacks permission (when check_permission=True).
    """
    if check_permission and user_id is not None:
        _check_permission(conn, user_id)

    status = _get_discussion_status(conn, discussion_id)

    if status == 'ended':
        raise DiscussionAlreadyEndedError("Discussion is already ended")

    now = datetime.now().isoformat()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE panel_discussions SET status = ?, ended_at = ? WHERE id = ?",
        ('ended', now, discussion_id)
    )
    conn.commit()

    _log_action(conn, discussion_id, 'end_discussion')

    return {'status': 'ended', 'ended_at': now}


def redirect_discussion(conn, discussion_id, new_topic, user_id=None, check_permission=False):
    """Redirect discussion to a new topic.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.
        new_topic: New topic to redirect to.
        user_id: ID of the user performing the action.
        check_permission: Whether to check user permission.

    Returns:
        dict: Result with status.

    Raises:
        DiscussionEndedError: If discussion is ended.
        PermissionDeniedError: If user lacks permission (when check_permission=True).
    """
    if check_permission and user_id is not None:
        _check_permission(conn, user_id)

    status = _get_discussion_status(conn, discussion_id)

    if status == 'ended':
        raise DiscussionEndedError("Cannot redirect ended discussion")

    _log_action(conn, discussion_id, 'redirect', details=new_topic)

    return {'status': 'redirected', 'topic': new_topic}


def mute_reviewer(conn, discussion_id, reviewer, user_id=None, check_permission=False):
    """Mute a reviewer in a discussion.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.
        reviewer: Reviewer to mute.
        user_id: ID of the user performing the action.
        check_permission: Whether to check user permission.

    Returns:
        dict: Result with status.

    Raises:
        PermissionDeniedError: If user lacks permission (when check_permission=True).
    """
    if check_permission and user_id is not None:
        _check_permission(conn, user_id)

    cursor = conn.cursor()

    # Check if reviewer state exists
    cursor.execute(
        "SELECT id FROM reviewer_states WHERE discussion_id = ? AND reviewer = ?",
        (discussion_id, reviewer)
    )
    row = cursor.fetchone()

    if row:
        # Update existing
        cursor.execute(
            "UPDATE reviewer_states SET is_muted = 1, updated_at = ? WHERE discussion_id = ? AND reviewer = ?",
            (datetime.now().isoformat(), discussion_id, reviewer)
        )
    else:
        # Insert new
        cursor.execute(
            "INSERT INTO reviewer_states (discussion_id, reviewer, is_muted) VALUES (?, ?, 1)",
            (discussion_id, reviewer)
        )

    conn.commit()

    _log_action(conn, discussion_id, 'mute_reviewer', target=reviewer)

    return {'status': 'muted', 'reviewer': reviewer}


def unmute_reviewer(conn, discussion_id, reviewer, user_id=None, check_permission=False):
    """Unmute a reviewer in a discussion.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.
        reviewer: Reviewer to unmute.
        user_id: ID of the user performing the action.
        check_permission: Whether to check user permission.

    Returns:
        dict: Result with status.

    Raises:
        PermissionDeniedError: If user lacks permission (when check_permission=True).
    """
    if check_permission and user_id is not None:
        _check_permission(conn, user_id)

    cursor = conn.cursor()
    cursor.execute(
        "UPDATE reviewer_states SET is_muted = 0, updated_at = ? WHERE discussion_id = ? AND reviewer = ?",
        (datetime.now().isoformat(), discussion_id, reviewer)
    )
    conn.commit()

    _log_action(conn, discussion_id, 'unmute_reviewer', target=reviewer)

    return {'status': 'unmuted', 'reviewer': reviewer}


def is_reviewer_muted(conn, discussion_id, reviewer):
    """Check if a reviewer is muted.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.
        reviewer: Reviewer to check.

    Returns:
        bool: True if muted, False otherwise.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT is_muted FROM reviewer_states WHERE discussion_id = ? AND reviewer = ?",
        (discussion_id, reviewer)
    )
    row = cursor.fetchone()

    if not row:
        return False

    is_muted = row[0] if isinstance(row, tuple) else row['is_muted']
    return bool(is_muted)


def toggle_mute(conn, discussion_id, reviewer, user_id=None, check_permission=False):
    """Toggle mute state for a reviewer.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.
        reviewer: Reviewer to toggle.
        user_id: ID of the user performing the action.
        check_permission: Whether to check user permission.

    Returns:
        dict: Result with new mute state.
    """
    if check_permission and user_id is not None:
        _check_permission(conn, user_id)

    if is_reviewer_muted(conn, discussion_id, reviewer):
        unmute_reviewer(conn, discussion_id, reviewer)
        return {'muted': False}
    else:
        mute_reviewer(conn, discussion_id, reviewer)
        return {'muted': True}


def get_muted_reviewers(conn, discussion_id):
    """Get list of muted reviewers for a discussion.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.

    Returns:
        list: List of muted reviewer names.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT reviewer FROM reviewer_states WHERE discussion_id = ? AND is_muted = 1",
        (discussion_id,)
    )

    return [row[0] if isinstance(row, tuple) else row['reviewer'] for row in cursor.fetchall()]


def pause_discussion(conn, discussion_id, user_id=None, check_permission=False):
    """Pause a discussion.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.
        user_id: ID of the user performing the action.
        check_permission: Whether to check user permission.

    Returns:
        dict: Result with status.

    Raises:
        PermissionDeniedError: If user lacks permission (when check_permission=True).
    """
    if check_permission and user_id is not None:
        _check_permission(conn, user_id)

    cursor = conn.cursor()
    cursor.execute(
        "UPDATE panel_discussions SET status = ? WHERE id = ?",
        ('paused', discussion_id)
    )
    conn.commit()

    _log_action(conn, discussion_id, 'pause')

    return {'status': 'paused'}


def resume_discussion(conn, discussion_id, user_id=None, check_permission=False):
    """Resume a paused discussion.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.
        user_id: ID of the user performing the action.
        check_permission: Whether to check user permission.

    Returns:
        dict: Result with status.

    Raises:
        DiscussionEndedError: If discussion is ended.
        PermissionDeniedError: If user lacks permission (when check_permission=True).
    """
    if check_permission and user_id is not None:
        _check_permission(conn, user_id)

    status = _get_discussion_status(conn, discussion_id)

    if status == 'ended':
        raise DiscussionEndedError("Cannot resume ended discussion")

    cursor = conn.cursor()
    cursor.execute(
        "UPDATE panel_discussions SET status = ? WHERE id = ?",
        ('active', discussion_id)
    )
    conn.commit()

    _log_action(conn, discussion_id, 'resume')

    return {'status': 'active'}


def get_moderation_history(conn, discussion_id, action_type=None):
    """Get moderation action history for a discussion.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.
        action_type: Optional filter by action type.

    Returns:
        list: List of moderation action dicts.
    """
    cursor = conn.cursor()

    if action_type:
        cursor.execute(
            """SELECT id, discussion_id, action_type, target, details, created_at
               FROM moderation_actions
               WHERE discussion_id = ? AND action_type = ?
               ORDER BY created_at ASC""",
            (discussion_id, action_type)
        )
    else:
        cursor.execute(
            """SELECT id, discussion_id, action_type, target, details, created_at
               FROM moderation_actions
               WHERE discussion_id = ?
               ORDER BY created_at ASC""",
            (discussion_id,)
        )

    history = []
    for row in cursor.fetchall():
        if hasattr(row, 'keys'):
            history.append(dict(row))
        else:
            history.append({
                'id': row[0],
                'discussion_id': row[1],
                'action_type': row[2],
                'target': row[3],
                'details': row[4],
                'created_at': row[5]
            })

    return history
