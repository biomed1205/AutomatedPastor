"""Panel chat module for The Green Room.

Provides interactive discussion between reviewer personas.
"""
from datetime import datetime
from flask_socketio import SocketIO, join_room, emit


class InsufficientParticipantsError(Exception):
    """Raised when discussion has fewer than 2 participants."""
    pass


class DiscussionEndedError(Exception):
    """Raised when trying to post to an ended discussion."""
    pass


class DiscussionNotFoundError(Exception):
    """Raised when discussion is not found."""
    pass


class Discussion:
    """Represents a panel discussion."""

    def __init__(self, id=None, sermon_id=None, mode='discussion',
                 status='active', sermon_context=None, started_at=None,
                 ended_at=None, participants=None):
        self.id = id
        self.sermon_id = sermon_id
        self.mode = mode
        self.status = status
        self.sermon_context = sermon_context
        self.started_at = started_at or datetime.now().isoformat()
        self.ended_at = ended_at
        self.participants = participants or []

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'sermon_id': self.sermon_id,
            'mode': self.mode,
            'status': self.status,
            'sermon_context': self.sermon_context,
            'started_at': self.started_at,
            'ended_at': self.ended_at,
            'participants': self.participants
        }


class Message:
    """Represents a chat message."""

    def __init__(self, id=None, discussion_id=None, sender=None,
                 sender_type=None, content=None, reply_to_id=None,
                 created_at=None):
        self.id = id
        self.discussion_id = discussion_id
        self.sender = sender
        self.sender_type = sender_type
        self.content = content
        self.reply_to_id = reply_to_id
        self.created_at = created_at or datetime.now().isoformat()

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'discussion_id': self.discussion_id,
            'sender': self.sender,
            'sender_type': self.sender_type,
            'content': self.content,
            'reply_to_id': self.reply_to_id,
            'created_at': self.created_at
        }


def _get_sermon_content(conn, sermon_id):
    """Get sermon content from database."""
    cursor = conn.cursor()
    # Try manuscript first (production), fall back to content (test)
    try:
        cursor.execute("SELECT manuscript FROM sermons WHERE id = ?", (sermon_id,))
        row = cursor.fetchone()
        if row:
            value = row[0] if isinstance(row, tuple) else row['manuscript']
            if value:
                return value
    except Exception:
        pass

    try:
        cursor.execute("SELECT content FROM sermons WHERE id = ?", (sermon_id,))
        row = cursor.fetchone()
        if row:
            return row[0] if isinstance(row, tuple) else row['content']
    except Exception:
        pass

    return None


def start_discussion(conn, bridge, sermon_id, participants, mode='discussion'):
    """Start a new panel discussion.

    Args:
        conn: Database connection.
        bridge: CLI bridge for reviewer interactions.
        sermon_id: ID of the sermon to discuss.
        participants: List of reviewer types.
        mode: 'discussion' or 'individual'.

    Returns:
        Discussion: The created discussion.

    Raises:
        InsufficientParticipantsError: If fewer than 2 participants.
    """
    if len(participants) < 2:
        raise InsufficientParticipantsError("At least 2 participants required")

    sermon_context = _get_sermon_content(conn, sermon_id)

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO panel_discussions (sermon_id, mode, status) VALUES (?, ?, ?)",
        (sermon_id, mode, 'active')
    )
    conn.commit()

    discussion_id = cursor.lastrowid

    return Discussion(
        id=discussion_id,
        sermon_id=sermon_id,
        mode=mode,
        status='active',
        sermon_context=sermon_context,
        participants=participants
    )


def _check_discussion_active(conn, discussion_id):
    """Check if discussion is active."""
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM panel_discussions WHERE id = ?", (discussion_id,))
    row = cursor.fetchone()
    if not row:
        raise DiscussionNotFoundError(f"Discussion not found: {discussion_id}")
    status = row[0] if isinstance(row, tuple) else row['status']
    if status == 'ended':
        raise DiscussionEndedError("Discussion has ended")
    return status


def post_reviewer_message(conn, bridge, discussion_id, reviewer, content):
    """Post a message from a reviewer.

    Args:
        conn: Database connection.
        bridge: CLI bridge.
        discussion_id: ID of the discussion.
        reviewer: Reviewer type.
        content: Message content.

    Returns:
        Message: The created message.
    """
    _check_discussion_active(conn, discussion_id)

    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO chat_messages (discussion_id, sender, sender_type, content)
           VALUES (?, ?, ?, ?)""",
        (discussion_id, reviewer, 'reviewer', content)
    )
    conn.commit()

    return Message(
        id=cursor.lastrowid,
        discussion_id=discussion_id,
        sender=reviewer,
        sender_type='reviewer',
        content=content
    )


def respond_to_message(conn, bridge, discussion_id, reviewer, reply_to_id, content):
    """Post a response to another message.

    Args:
        conn: Database connection.
        bridge: CLI bridge.
        discussion_id: ID of the discussion.
        reviewer: Reviewer type.
        reply_to_id: ID of message being replied to.
        content: Response content.

    Returns:
        Message: The created message.
    """
    _check_discussion_active(conn, discussion_id)

    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO chat_messages (discussion_id, sender, sender_type, content, reply_to_id)
           VALUES (?, ?, ?, ?, ?)""",
        (discussion_id, reviewer, 'reviewer', content, reply_to_id)
    )
    conn.commit()

    return Message(
        id=cursor.lastrowid,
        discussion_id=discussion_id,
        sender=reviewer,
        sender_type='reviewer',
        content=content,
        reply_to_id=reply_to_id
    )


def generate_reviewer_response(conn, bridge, discussion_id, reviewer):
    """Generate a contextual response from a reviewer.

    Args:
        conn: Database connection.
        bridge: CLI bridge.
        discussion_id: ID of the discussion.
        reviewer: Reviewer type.

    Returns:
        Message: The generated message.
    """
    history = get_message_history(conn, discussion_id)

    prompt = f"""You are a {reviewer} reviewer. Based on the discussion so far, provide a brief, relevant response.

Previous messages:
"""
    for msg in history[-5:]:
        prompt += f"- {msg['sender']}: {msg['content']}\n"

    prompt += f"\nRespond as {reviewer}:"

    result = bridge.run(prompt)
    output = result.output if hasattr(result, 'output') else str(result)

    return post_reviewer_message(conn, bridge, discussion_id, reviewer, output)


def get_message_history(conn, discussion_id):
    """Get message history for a discussion.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.

    Returns:
        list: List of message dicts.
    """
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, discussion_id, sender, sender_type, content, reply_to_id, created_at
           FROM chat_messages
           WHERE discussion_id = ?
           ORDER BY created_at ASC""",
        (discussion_id,)
    )

    messages = []
    for row in cursor.fetchall():
        if hasattr(row, 'keys'):
            messages.append(dict(row))
        else:
            messages.append({
                'id': row[0],
                'discussion_id': row[1],
                'sender': row[2],
                'sender_type': row[3],
                'content': row[4],
                'reply_to_id': row[5],
                'created_at': row[6]
            })

    return messages


def post_user_message(conn, discussion_id, content):
    """Post a message from the user.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.
        content: Message content.

    Returns:
        Message: The created message.
    """
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO chat_messages (discussion_id, sender, sender_type, content)
           VALUES (?, ?, ?, ?)""",
        (discussion_id, 'user', 'user', content)
    )
    conn.commit()

    return Message(
        id=cursor.lastrowid,
        discussion_id=discussion_id,
        sender='user',
        sender_type='user',
        content=content
    )


def get_reviewer_responses(conn, bridge, discussion_id, to_message_id):
    """Get reviewer responses to a message.

    Args:
        conn: Database connection.
        bridge: CLI bridge.
        discussion_id: ID of the discussion.
        to_message_id: ID of message to respond to.

    Returns:
        list: List of response messages.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM panel_discussions WHERE id = ?", (discussion_id,))
    row = cursor.fetchone()
    if not row:
        return []

    response = generate_reviewer_response(conn, bridge, discussion_id, 'theological')
    return [response]


def get_discussion_by_id(conn, discussion_id):
    """Get discussion by ID.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.

    Returns:
        Discussion: The discussion or None.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM panel_discussions WHERE id = ?", (discussion_id,))
    row = cursor.fetchone()

    if not row:
        return None

    if hasattr(row, 'keys'):
        return Discussion(**dict(row))
    return Discussion(
        id=row[0],
        sermon_id=row[1],
        mode=row[2],
        status=row[3],
        started_at=row[4],
        ended_at=row[5]
    )


def get_discussions_for_sermon(conn, sermon_id):
    """Get all discussions for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: List of discussions.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM panel_discussions WHERE sermon_id = ?", (sermon_id,))

    discussions = []
    for row in cursor.fetchall():
        if hasattr(row, 'keys'):
            discussions.append(Discussion(**dict(row)))
        else:
            discussions.append(Discussion(
                id=row[0],
                sermon_id=row[1],
                mode=row[2],
                status=row[3],
                started_at=row[4],
                ended_at=row[5]
            ))

    return discussions


def end_discussion(conn, discussion_id):
    """End a discussion.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.

    Returns:
        Discussion: The ended discussion.
    """
    now = datetime.now().isoformat()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE panel_discussions SET status = ?, ended_at = ? WHERE id = ?",
        ('ended', now, discussion_id)
    )
    conn.commit()

    return Discussion(id=discussion_id, status='ended', ended_at=now)


def pause_discussion(conn, discussion_id):
    """Pause a discussion.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.

    Returns:
        Discussion: The paused discussion.
    """
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE panel_discussions SET status = ? WHERE id = ?",
        ('paused', discussion_id)
    )
    conn.commit()

    return Discussion(id=discussion_id, status='paused')


def resume_discussion(conn, discussion_id):
    """Resume a paused discussion.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.

    Returns:
        Discussion: The resumed discussion.
    """
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE panel_discussions SET status = ? WHERE id = ?",
        ('active', discussion_id)
    )
    conn.commit()

    return Discussion(id=discussion_id, status='active')


def redirect_discussion(conn, bridge, discussion_id, new_topic):
    """Redirect discussion to a new topic.

    Args:
        conn: Database connection.
        bridge: CLI bridge.
        discussion_id: ID of the discussion.
        new_topic: New topic to discuss.

    Returns:
        Message: The redirect message.
    """
    return post_user_message(conn, discussion_id, f"[Moderator] {new_topic}")


def create_socketio_app(app):
    """Create SocketIO app for real-time updates.

    Args:
        app: Flask app.

    Returns:
        SocketIO: The SocketIO instance.
    """
    socketio = SocketIO(app, cors_allowed_origins="*")

    @socketio.on('join')
    def on_join(data):
        discussion_id = data.get('discussion_id')
        if discussion_id:
            join_room(f'discussion_{discussion_id}')

    return socketio


def emit_message(socketio, discussion_id, message):
    """Emit a message to discussion participants.

    Args:
        socketio: SocketIO instance.
        discussion_id: ID of the discussion.
        message: Message dict to broadcast.
    """
    socketio.emit('new_message', message, room=f'discussion_{discussion_id}')


class PanelChat:
    """Panel chat manager class."""

    def __init__(self, cli_bridge, db_conn=None):
        self.cli_bridge = cli_bridge
        self.db_conn = db_conn

    def start(self, sermon_id, participants, mode='discussion'):
        """Start a new discussion."""
        return start_discussion(
            self.db_conn, self.cli_bridge,
            sermon_id, participants, mode
        )

    def post_message(self, discussion_id, reviewer, content):
        """Post a reviewer message."""
        return post_reviewer_message(
            self.db_conn, self.cli_bridge,
            discussion_id, reviewer, content
        )

    def end(self, discussion_id):
        """End a discussion."""
        return end_discussion(self.db_conn, discussion_id)


# =============================================================================
# @ Mention Parsing Functions
# =============================================================================

import re


def extract_mention_patterns(message):
    """Extract all @mention patterns from a message.

    This extracts the raw patterns without validating against reviewer names.
    Handles edge cases like emails (text@domain) and lone @ symbols.

    Args:
        message: The message text to parse.

    Returns:
        list: List of extracted patterns (without @ symbol).
    """
    if not message or not message.strip():
        return []

    # Pattern to match @word where:
    # - Not preceded by alphanumeric (to avoid emails like user@domain)
    # - Followed by word characters
    # - Word must start with a letter (not number)
    pattern = r'(?<![a-zA-Z0-9])@([a-zA-Z][a-zA-Z0-9_]*)'

    matches = re.findall(pattern, message)
    return matches


def parse_mentions(message, valid_reviewers):
    """Parse @mentions from a message and return valid reviewer names.

    Args:
        message: The message text to parse.
        valid_reviewers: List of valid reviewer names to match against.

    Returns:
        list: List of valid, lowercase, unique reviewer names found.
    """
    if not message or not message.strip():
        return []

    if not valid_reviewers:
        return []

    # Extract all @patterns
    patterns = extract_mention_patterns(message)

    # Normalize valid reviewers to lowercase for matching
    valid_lower = {r.lower() for r in valid_reviewers}

    # Match patterns against valid reviewers (case-insensitive)
    found = set()
    for pattern in patterns:
        pattern_lower = pattern.lower()
        if pattern_lower in valid_lower:
            found.add(pattern_lower)

    return list(found)


def parse_mentions_with_db(conn, message, default_reviewers):
    """Parse @mentions including custom reviewers from database.

    Args:
        conn: Database connection with custom_reviewers table.
        message: The message text to parse.
        default_reviewers: List of default reviewer names.

    Returns:
        list: List of valid, lowercase, unique reviewer names found.
    """
    if not message or not message.strip():
        return []

    # Get active custom reviewers from database
    custom_reviewers = []
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM custom_reviewers WHERE active = 1"
        )
        rows = cursor.fetchall()
        custom_reviewers = [
            row[0] if isinstance(row, tuple) else row['name']
            for row in rows
        ]
    except Exception:
        # Table may not exist or be empty
        pass

    # Combine default and custom reviewers
    all_reviewers = list(default_reviewers) + custom_reviewers

    return parse_mentions(message, all_reviewers)


def get_mentioned_reviewers(conn, message, default_reviewers):
    """Get reviewers mentioned in a message for routing.

    This is a convenience function for routing messages to specific reviewers.

    Args:
        conn: Database connection with custom_reviewers table.
        message: The message text to parse.
        default_reviewers: List of default reviewer names.

    Returns:
        list: List of reviewer names to route the message to.
    """
    return parse_mentions_with_db(conn, message, default_reviewers)


# =============================================================================
# Group Mention Shortcuts (@women, @UMC, etc.)
# =============================================================================

import json


def expand_group_mention(group_name, definitions):
    """Expand a group name to list of member names.

    Args:
        group_name: Name of the group to expand (e.g., 'women', 'umc').
        definitions: Dictionary mapping group names to member lists.

    Returns:
        list: List of member names, or empty list if group not found.
    """
    if not group_name:
        return []

    # Case-insensitive lookup
    group_lower = group_name.lower()

    # Create lowercase key mapping
    defs_lower = {k.lower(): v for k, v in definitions.items()}

    if group_lower in defs_lower:
        return list(defs_lower[group_lower])

    return []


def expand_groups_in_message(message, definitions):
    """Find and expand all group mentions in a message.

    Args:
        message: The message text to parse.
        definitions: Dictionary mapping group names to member lists.

    Returns:
        list: List of unique member names from all mentioned groups.
    """
    if not message or not message.strip():
        return []

    # Extract all @patterns from the message
    patterns = extract_mention_patterns(message)

    # Collect all unique members from matching groups
    all_members = set()

    for pattern in patterns:
        members = expand_group_mention(pattern, definitions)
        all_members.update(members)

    return list(all_members)


def parse_all_mentions(message, definitions, default_reviewers):
    """Parse all mentions including both groups and individual reviewers.

    Args:
        message: The message text to parse.
        definitions: Dictionary mapping group names to member lists.
        default_reviewers: List of default individual reviewer names.

    Returns:
        list: List of unique reviewer names from groups and individual mentions.
    """
    if not message or not message.strip():
        return []

    # First expand all groups
    group_members = expand_groups_in_message(message, definitions)

    # Then get individual mentions
    individual_mentions = parse_mentions(message, default_reviewers)

    # Collect all group member names as valid reviewers for individual matching
    all_group_members = set()
    for members in definitions.values():
        all_group_members.update(members)

    # Also check for individual mentions of group members
    member_mentions = parse_mentions(message, list(all_group_members))

    # Combine all and remove duplicates
    all_reviewers = set(group_members)
    all_reviewers.update(individual_mentions)
    all_reviewers.update(member_mentions)

    return list(all_reviewers)


def expand_group_with_db(conn, group_name, definitions):
    """Expand a group name with database lookup.

    Database groups take precedence over default definitions.
    Inactive groups are ignored.

    Args:
        conn: Database connection with group_shortcuts table.
        group_name: Name of the group to expand.
        definitions: Default group definitions dictionary.

    Returns:
        list: List of member names from the group.
    """
    if not group_name:
        return []

    group_lower = group_name.lower()

    # Try database first
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT members FROM group_shortcuts WHERE LOWER(group_name) = ? AND active = 1",
            (group_lower,)
        )
        row = cursor.fetchone()

        if row:
            members_json = row[0] if isinstance(row, tuple) else row['members']
            return json.loads(members_json)
    except Exception:
        # Table may not exist or other error
        pass

    # Fall back to default definitions
    return expand_group_mention(group_name, definitions)


def get_available_groups(definitions):
    """Get list of all available group names.

    Args:
        definitions: Dictionary mapping group names to member lists.

    Returns:
        list: List of group names.
    """
    return list(definitions.keys())


def get_group_members(group_name, definitions):
    """Get list of members for a specific group.

    Args:
        group_name: Name of the group.
        definitions: Dictionary mapping group names to member lists.

    Returns:
        list: List of member names, or empty list if group not found.
    """
    return expand_group_mention(group_name, definitions)
