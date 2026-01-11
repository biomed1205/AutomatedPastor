"""Chat UI module for The Green Room panel chat interface.

Provides frontend support functions for panel chat UI.
"""
import html
from datetime import datetime
from flask_socketio import SocketIO, join_room, emit


# Message length limit
MAX_MESSAGE_LENGTH = 10000

# Reviewer display configuration
REVIEWER_DISPLAY = {
    'theological': {
        'name': 'Theological Scholar',
        'display_name': 'Theological Scholar',
        'color': '#4B0082',
        'icon': 'book',
        'avatar': 'T'
    },
    'pastoral': {
        'name': 'Pastoral Mentor',
        'display_name': 'Pastoral Mentor',
        'color': '#228B22',
        'icon': 'heart',
        'avatar': 'P'
    },
    'structural': {
        'name': 'Homiletics Professor',
        'display_name': 'Homiletics Professor',
        'color': '#B8860B',
        'icon': 'structure',
        'avatar': 'H'
    },
    'engagement': {
        'name': 'Congregation Member',
        'display_name': 'Congregation Member',
        'color': '#FF6347',
        'icon': 'people',
        'avatar': 'C'
    },
    'illustration': {
        'name': 'Visitor Perspective',
        'display_name': 'Visitor',
        'color': '#4682B4',
        'icon': 'eye',
        'avatar': 'V'
    },
    'scripture': {
        'name': 'Elder Voice',
        'display_name': 'Elder',
        'color': '#8B4513',
        'icon': 'bible',
        'avatar': 'E'
    },
    'language': {
        'name': 'Youth Leader',
        'display_name': 'Youth Leader',
        'color': '#9370DB',
        'icon': 'chat',
        'avatar': 'Y'
    }
}

# Error messages
ERROR_MESSAGES = {
    'connection_failed': 'Unable to connect to the discussion. Please refresh the page.',
    'send_failed': 'Failed to send message. Please try again.',
    'load_failed': 'Unable to load messages. Please refresh the page.',
    'discussion_ended': 'This discussion has ended.',
    'discussion_paused': 'This discussion is paused.'
}

# UI state messages
UI_STATES = {
    'loading': {'message': 'Loading messages...', 'type': 'loading'},
    'reconnecting': {'message': 'Reconnecting to discussion...', 'type': 'warning'},
    'connected': {'message': 'Connected', 'type': 'success'},
    'disconnected': {'message': 'Disconnected', 'type': 'error'},
    'error': {'message': 'An error occurred', 'type': 'error'}
}


def create_socketio_app(app):
    """Create SocketIO app for real-time chat.

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
            room = f'discussion_{discussion_id}'
            join_room(room)
            emit('joined', {'room': room, 'message': 'Joined discussion'})

    @socketio.on('leave')
    def on_leave(data):
        discussion_id = data.get('discussion_id')
        if discussion_id:
            from flask_socketio import leave_room
            room = f'discussion_{discussion_id}'
            leave_room(room)

    return socketio


def broadcast_message(socketio, discussion_id, message):
    """Broadcast a message to discussion participants.

    Args:
        socketio: SocketIO instance.
        discussion_id: ID of the discussion.
        message: Message dict to broadcast.
    """
    room = f'discussion_{discussion_id}'
    socketio.emit('new_message', message, room=room)


def get_message_history(conn, discussion_id, limit=None, offset=None):
    """Get message history for a discussion.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.
        limit: Optional limit for pagination.
        offset: Optional offset for pagination.

    Returns:
        list: List of message dicts.
    """
    cursor = conn.cursor()

    query = """
        SELECT id, discussion_id, sender, sender_type, content, created_at
        FROM chat_messages
        WHERE discussion_id = ?
        ORDER BY created_at ASC
    """
    params = [discussion_id]

    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    if offset is not None:
        query += " OFFSET ?"
        params.append(offset)

    cursor.execute(query, params)

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
                'created_at': row[5]
            })

    return messages


def prepare_chat_context(conn, discussion_id):
    """Prepare template context for chat UI.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.

    Returns:
        dict: Template context with messages and discussion info.
    """
    messages = get_message_history(conn, discussion_id)

    # Get discussion info
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM panel_discussions WHERE id = ?", (discussion_id,))
    row = cursor.fetchone()

    status = 'unknown'
    sermon_id = None
    if row:
        if hasattr(row, 'keys'):
            status = row['status']
            sermon_id = row['sermon_id']
        else:
            status = row[2] if len(row) > 2 else 'active'
            sermon_id = row[1] if len(row) > 1 else None

    # Format messages for display
    formatted_messages = [format_message_for_display(msg) for msg in messages]

    return {
        'messages': formatted_messages,
        'discussion_id': discussion_id,
        'sermon_id': sermon_id,
        'status': status,
        'is_ended': status == 'ended',
        'is_paused': status == 'paused',
        'message_count': len(messages)
    }


def format_message_for_display(message):
    """Format a message for display in the UI.

    Args:
        message: Message dict.

    Returns:
        dict: Formatted message with display fields.
    """
    result = dict(message)

    # Format timestamp
    created_at = message.get('created_at', '')
    if created_at:
        try:
            if isinstance(created_at, str):
                dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                result['display_time'] = dt.strftime('%I:%M %p')
                result['formatted_time'] = dt.strftime('%B %d, %Y at %I:%M %p')
        except ValueError:
            result['display_time'] = str(created_at)
            result['formatted_time'] = str(created_at)

    # Add sender display info
    sender = message.get('sender', '')
    sender_type = message.get('sender_type', 'reviewer')
    result['sender_info'] = get_sender_display_info(sender, sender_type)

    # Sanitize content for display
    content = message.get('content', '')
    result['content'] = sanitize_message(content)

    return result


def validate_message(message):
    """Validate message content.

    Args:
        message: Message dict with content.

    Returns:
        bool: True if valid, False otherwise.
    """
    content = message.get('content', '')

    if not content or not content.strip():
        return False

    if len(content) > MAX_MESSAGE_LENGTH:
        return False

    return True


def sanitize_message(message):
    """Sanitize message content for display.

    Args:
        message: Raw message string.

    Returns:
        str: Sanitized message.
    """
    if not message:
        return ''

    # Strip whitespace
    message = message.strip()

    # Escape HTML
    message = html.escape(message)

    return message


def get_reviewer_display_info(reviewer):
    """Get display information for a reviewer.

    Args:
        reviewer: Reviewer type string.

    Returns:
        dict: Display info with name, color, avatar, icon.
    """
    if reviewer in REVIEWER_DISPLAY:
        return dict(REVIEWER_DISPLAY[reviewer])

    # Default for unknown reviewers
    return {
        'name': reviewer.title(),
        'display_name': reviewer.title(),
        'color': '#666666',
        'icon': 'user',
        'avatar': reviewer[0].upper() if reviewer else '?'
    }


def get_sender_display_info(sender, sender_type):
    """Get display information for a message sender.

    Args:
        sender: Sender identifier.
        sender_type: Type of sender ('user' or 'reviewer').

    Returns:
        dict: Display info with is_user flag.
    """
    if sender_type == 'user':
        return {
            'name': 'You',
            'display_name': 'You',
            'color': '#007bff',
            'icon': 'user',
            'avatar': 'U',
            'is_user': True
        }

    info = get_reviewer_display_info(sender)
    info['is_user'] = False
    return info


def get_error_message(error_type):
    """Get error message for a given error type.

    Args:
        error_type: Type of error.

    Returns:
        str: Error message.
    """
    return ERROR_MESSAGES.get(error_type, 'An unexpected error occurred.')


def get_ui_state(state):
    """Get UI state information.

    Args:
        state: State identifier.

    Returns:
        dict: State info with message and type.
    """
    return UI_STATES.get(state, {'message': state, 'type': 'info'})
