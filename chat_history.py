"""Chat history saving and export module.

Provides persistence and export functionality for panel chat sessions.
"""
import json
from datetime import datetime


def save_chat_session(conn, messages, sermon_id=None, session_name=None):
    """Save a chat session to the database.

    Args:
        conn: Database connection.
        messages: List of message dictionaries.
        sermon_id: Optional sermon ID to link session to.
        session_name: Optional name for the session.

    Returns:
        int: The session ID of the created session.
    """
    cursor = conn.cursor()

    # Create the session record
    cursor.execute(
        """INSERT INTO chat_sessions (sermon_id, session_name, message_count)
           VALUES (?, ?, ?)""",
        (sermon_id, session_name, len(messages))
    )
    session_id = cursor.lastrowid

    # Insert all messages
    for msg in messages:
        cursor.execute(
            """INSERT INTO chat_messages
               (session_id, sender, sender_type, content, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                session_id,
                msg.get('sender'),
                msg.get('sender_type'),
                msg.get('content'),
                msg.get('created_at', datetime.now().isoformat())
            )
        )

    conn.commit()
    return session_id


def load_chat_session(conn, session_id):
    """Load a chat session from the database.

    Args:
        conn: Database connection.
        session_id: ID of the session to load.

    Returns:
        list: List of message dictionaries, or None if session doesn't exist.
    """
    cursor = conn.cursor()

    # Check if session exists
    cursor.execute('SELECT id FROM chat_sessions WHERE id = ?', (session_id,))
    if cursor.fetchone() is None:
        return None

    # Load messages ordered by creation time
    cursor.execute(
        """SELECT sender, sender_type, content, created_at
           FROM chat_messages
           WHERE session_id = ?
           ORDER BY id""",
        (session_id,)
    )
    rows = cursor.fetchall()

    messages = []
    for row in rows:
        msg = {
            'sender': row['sender'] if hasattr(row, 'keys') else row[0],
            'sender_type': row['sender_type'] if hasattr(row, 'keys') else row[1],
            'content': row['content'] if hasattr(row, 'keys') else row[2],
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[3]
        }
        messages.append(msg)

    return messages


def export_chat_to_text(conn, session_id):
    """Export a chat session to plain text format.

    Args:
        conn: Database connection.
        session_id: ID of the session to export.

    Returns:
        str: Plain text representation of the chat.
    """
    messages = load_chat_session(conn, session_id)
    if not messages:
        return ""

    lines = []
    for msg in messages:
        sender = msg['sender']
        content = msg['content']
        timestamp = msg.get('created_at', '')
        lines.append(f"[{timestamp}] {sender}: {content}")

    return '\n'.join(lines)


def export_chat_to_markdown(conn, session_id):
    """Export a chat session to markdown format.

    Args:
        conn: Database connection.
        session_id: ID of the session to export.

    Returns:
        str: Markdown representation of the chat.
    """
    messages = load_chat_session(conn, session_id)
    if not messages:
        return ""

    lines = ["# Chat Session Export\n"]

    for msg in messages:
        sender = msg['sender']
        sender_type = msg.get('sender_type', 'unknown')
        content = msg['content']
        timestamp = msg.get('created_at', '')

        # Format based on sender type
        if sender_type == 'reviewer':
            lines.append(f"**{sender}** *({timestamp})*")
        elif sender_type == 'user':
            lines.append(f"**{sender}** *({timestamp})*")
        else:
            lines.append(f"**{sender}** *({timestamp})*")

        lines.append(f"> {content}\n")

    return '\n'.join(lines)


def export_chat_to_json(conn, session_id):
    """Export a chat session to JSON format.

    Args:
        conn: Database connection.
        session_id: ID of the session to export.

    Returns:
        str: JSON string representation of the chat.
    """
    messages = load_chat_session(conn, session_id)

    # Get session metadata
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, sermon_id, session_name, started_at, message_count
           FROM chat_sessions WHERE id = ?""",
        (session_id,)
    )
    row = cursor.fetchone()

    if row:
        session_data = {
            'session_id': row['id'] if hasattr(row, 'keys') else row[0],
            'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
            'session_name': row['session_name'] if hasattr(row, 'keys') else row[2],
            'started_at': row['started_at'] if hasattr(row, 'keys') else row[3],
            'message_count': row['message_count'] if hasattr(row, 'keys') else row[4],
            'messages': messages or []
        }
    else:
        session_data = {'messages': messages or []}

    return json.dumps(session_data, indent=2, default=str)


def delete_chat_session(conn, session_id):
    """Delete a chat session and its messages.

    Args:
        conn: Database connection.
        session_id: ID of the session to delete.

    Returns:
        bool: True if session was deleted, False if it didn't exist.
    """
    cursor = conn.cursor()

    # Check if session exists
    cursor.execute('SELECT id FROM chat_sessions WHERE id = ?', (session_id,))
    if cursor.fetchone() is None:
        return False

    # Delete messages first (in case no cascade)
    cursor.execute('DELETE FROM chat_messages WHERE session_id = ?', (session_id,))

    # Delete session
    cursor.execute('DELETE FROM chat_sessions WHERE id = ?', (session_id,))
    conn.commit()

    return True


def list_chat_sessions(conn, sermon_id=None):
    """List all chat sessions, optionally filtered by sermon.

    Args:
        conn: Database connection.
        sermon_id: Optional sermon ID to filter by.

    Returns:
        list: List of session dictionaries with metadata.
    """
    cursor = conn.cursor()

    if sermon_id is not None:
        cursor.execute(
            """SELECT id, sermon_id, session_name, started_at, message_count
               FROM chat_sessions WHERE sermon_id = ?
               ORDER BY started_at DESC""",
            (sermon_id,)
        )
    else:
        cursor.execute(
            """SELECT id, sermon_id, session_name, started_at, message_count
               FROM chat_sessions
               ORDER BY started_at DESC"""
        )

    rows = cursor.fetchall()
    sessions = []

    for row in rows:
        session = {
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
            'session_name': row['session_name'] if hasattr(row, 'keys') else row[2],
            'started_at': row['started_at'] if hasattr(row, 'keys') else row[3],
            'message_count': row['message_count'] if hasattr(row, 'keys') else row[4]
        }
        sessions.append(session)

    return sessions


def get_session_summary(conn, session_id):
    """Get summary metadata for a chat session.

    Args:
        conn: Database connection.
        session_id: ID of the session.

    Returns:
        dict: Summary metadata, or None if session doesn't exist.
    """
    cursor = conn.cursor()

    # Get session info
    cursor.execute(
        """SELECT id, sermon_id, session_name, started_at, message_count
           FROM chat_sessions WHERE id = ?""",
        (session_id,)
    )
    row = cursor.fetchone()

    if row is None:
        return None

    session_name = row['session_name'] if hasattr(row, 'keys') else row[2]
    started_at = row['started_at'] if hasattr(row, 'keys') else row[3]
    message_count = row['message_count'] if hasattr(row, 'keys') else row[4]

    # Get participants
    cursor.execute(
        """SELECT DISTINCT sender FROM chat_messages WHERE session_id = ?""",
        (session_id,)
    )
    participant_rows = cursor.fetchall()
    participants = [
        r['sender'] if hasattr(r, 'keys') else r[0]
        for r in participant_rows
    ]

    return {
        'session_name': session_name,
        'started_at': started_at,
        'message_count': message_count,
        'participants': participants
    }
