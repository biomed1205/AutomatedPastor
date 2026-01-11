"""Chat message streaming module.

Provides real-time message streaming via WebSocket/SSE for panel chat.
"""
import threading
import uuid
from datetime import datetime
from flask_socketio import SocketIO, join_room, emit


def create_streaming_socketio(app, require_auth=False):
    """Create a SocketIO instance for streaming.

    Args:
        app: Flask application instance.
        require_auth: Whether to require authentication.

    Returns:
        SocketIO: Configured SocketIO instance.
    """
    socketio = SocketIO(app, cors_allowed_origins="*")

    @socketio.on('connect')
    def on_connect():
        """Handle client connection."""
        pass

    @socketio.on('authenticate')
    def on_authenticate(data):
        """Handle client authentication."""
        emit('authenticated', {'status': 'ok'})

    @socketio.on('join_stream')
    def on_join_stream(data):
        """Handle client joining a stream room."""
        discussion_id = data.get('discussion_id')
        if discussion_id:
            join_room(f'stream_{discussion_id}')

    return socketio


class StreamingMessage:
    """Represents a message being streamed."""

    def __init__(self, discussion_id, sender, full_content, sender_name=None):
        """Initialize streaming message.

        Args:
            discussion_id: ID of the discussion.
            sender: Sender identifier.
            full_content: Complete message content.
            sender_name: Optional display name.
        """
        self.discussion_id = discussion_id
        self.sender = sender
        self.sender_name = sender_name
        self.full_content = full_content


def stream_message_chunks(message, chunk_size=10):
    """Stream a message in chunks.

    Args:
        message: StreamingMessage to stream.
        chunk_size: Size of each chunk.

    Yields:
        dict: Chunk data with content and sender info.
    """
    content = message.full_content
    pos = 0

    while pos < len(content):
        chunk_content = content[pos:pos + chunk_size]
        is_final = (pos + chunk_size) >= len(content)

        yield {
            'sender': message.sender,
            'sender_name': message.sender_name,
            'content': chunk_content,
            'is_final': is_final,
            'position': pos
        }

        pos += chunk_size


def emit_message_chunk(socketio, discussion_id, chunk):
    """Emit a message chunk to clients.

    Args:
        socketio: SocketIO instance.
        discussion_id: ID of the discussion.
        chunk: Chunk data to emit.
    """
    socketio.emit('message_chunk', chunk, room=f'stream_{discussion_id}')


def stream_complete_message(socketio, discussion_id, message_id, content):
    """Mark a stream as complete.

    Args:
        socketio: SocketIO instance.
        discussion_id: ID of the discussion.
        message_id: ID of the message.
        content: Complete message content.
    """
    socketio.emit('stream_complete', {
        'message_id': message_id,
        'content': content,
        'is_final': True
    }, room=f'stream_{discussion_id}')


# =============================================================================
# Partial Message Storage
# =============================================================================

def save_partial_content(conn, discussion_id, message_id, content):
    """Save partial message content to database.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.
        message_id: ID of the message.
        content: Partial content to save.
    """
    cursor = conn.cursor()
    cursor.execute(
        """INSERT OR REPLACE INTO stream_state
           (discussion_id, message_id, partial_content, is_complete)
           VALUES (?, ?, ?, 0)""",
        (discussion_id, message_id, content)
    )
    conn.commit()


def append_partial_content(conn, message_id, content):
    """Append content to existing partial message.

    Args:
        conn: Database connection.
        message_id: ID of the message.
        content: Content to append.
    """
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE stream_state
           SET partial_content = partial_content || ?,
               updated_at = CURRENT_TIMESTAMP
           WHERE message_id = ?""",
        (content, message_id)
    )
    conn.commit()


def mark_stream_complete(conn, message_id):
    """Mark a stream as complete.

    Args:
        conn: Database connection.
        message_id: ID of the message.
    """
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE stream_state SET is_complete = 1 WHERE message_id = ?",
        (message_id,)
    )
    conn.commit()


def get_partial_content(conn, message_id):
    """Get current partial content for a message.

    Args:
        conn: Database connection.
        message_id: ID of the message.

    Returns:
        str: Partial content or None.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT partial_content FROM stream_state WHERE message_id = ?",
        (message_id,)
    )
    row = cursor.fetchone()

    if row:
        return row['partial_content'] if hasattr(row, 'keys') else row[0]
    return None


def get_resume_position(conn, discussion_id, message_id):
    """Get the position to resume streaming from.

    Args:
        conn: Database connection.
        discussion_id: ID of the discussion.
        message_id: ID of the message.

    Returns:
        int: Position to resume from.
    """
    content = get_partial_content(conn, message_id)
    return len(content) if content else 0


# =============================================================================
# Message Buffering
# =============================================================================

class MessageBuffer:
    """Buffer for messages during disconnection."""

    def __init__(self, discussion_id, max_size=100):
        """Initialize message buffer.

        Args:
            discussion_id: ID of the discussion.
            max_size: Maximum buffer size.
        """
        self.discussion_id = discussion_id
        self.max_size = max_size
        self._messages = []
        self._lock = threading.Lock()

    def add(self, message):
        """Add a message to the buffer.

        Args:
            message: Message dict to add.
        """
        with self._lock:
            self._messages.append(message)
            # Trim to max size (keep most recent)
            if len(self._messages) > self.max_size:
                self._messages = self._messages[-self.max_size:]

    def size(self):
        """Get number of messages in buffer.

        Returns:
            int: Number of messages.
        """
        with self._lock:
            return len(self._messages)

    def clear(self):
        """Clear all messages from buffer."""
        with self._lock:
            self._messages = []

    def get_all(self):
        """Get all messages in buffer.

        Returns:
            list: List of buffered messages.
        """
        with self._lock:
            return list(self._messages)

    def flush(self, socketio):
        """Flush buffer to clients via socketio.

        Args:
            socketio: SocketIO instance to emit to.
        """
        messages = self.get_all()
        for message in messages:
            socketio.emit('buffered_message', message,
                          room=f'stream_{self.discussion_id}')
        self.clear()


def add_to_buffer(buffer, message):
    """Add a message to a buffer.

    Args:
        buffer: MessageBuffer instance.
        message: Message to add.
    """
    buffer.add(message)


def get_buffered_messages(buffer):
    """Get all buffered messages.

    Args:
        buffer: MessageBuffer instance.

    Returns:
        list: List of messages.
    """
    return buffer.get_all()


# =============================================================================
# Stream Management
# =============================================================================

class Stream:
    """Represents an active message stream."""

    def __init__(self, stream_id, discussion_id, reviewer):
        """Initialize a stream.

        Args:
            stream_id: Unique stream ID.
            discussion_id: ID of the discussion.
            reviewer: Reviewer name.
        """
        self.id = stream_id
        self.discussion_id = discussion_id
        self.reviewer = reviewer
        self._content = ''
        self._lock = threading.Lock()

    def push_content(self, content):
        """Push content to the stream.

        Args:
            content: Content to push.
        """
        with self._lock:
            self._content += content

    def get_content(self):
        """Get stream content.

        Returns:
            str: Current content.
        """
        with self._lock:
            return self._content


class StreamManager:
    """Manages multiple concurrent streams."""

    def __init__(self):
        """Initialize stream manager."""
        self._streams = {}
        self._lock = threading.Lock()

    def add_stream(self, stream):
        """Add a stream to the manager.

        Args:
            stream: Stream to add.
        """
        with self._lock:
            self._streams[stream.id] = stream

    def remove_stream(self, stream_id):
        """Remove a stream from the manager.

        Args:
            stream_id: ID of stream to remove.
        """
        with self._lock:
            if stream_id in self._streams:
                del self._streams[stream_id]

    def get_stream(self, stream_id):
        """Get a stream by ID.

        Args:
            stream_id: ID of the stream.

        Returns:
            Stream or None.
        """
        with self._lock:
            return self._streams.get(stream_id)

    def active_stream_count(self):
        """Get count of active streams.

        Returns:
            int: Number of active streams.
        """
        with self._lock:
            return len(self._streams)

    def get_streams_by_discussion(self, discussion_id):
        """Get all streams for a discussion.

        Args:
            discussion_id: ID of the discussion.

        Returns:
            list: List of streams.
        """
        with self._lock:
            return [
                s for s in self._streams.values()
                if s.discussion_id == discussion_id
            ]


def create_stream(manager, discussion_id, reviewer):
    """Create a new stream.

    Args:
        manager: StreamManager instance.
        discussion_id: ID of the discussion.
        reviewer: Reviewer name.

    Returns:
        Stream: The created stream.
    """
    stream_id = str(uuid.uuid4())
    stream = Stream(stream_id, discussion_id, reviewer)
    manager.add_stream(stream)
    return stream


def get_streams_for_discussion(manager, discussion_id):
    """Get streams for a specific discussion.

    Args:
        manager: StreamManager instance.
        discussion_id: ID of the discussion.

    Returns:
        list: List of streams.
    """
    return manager.get_streams_by_discussion(discussion_id)


def push_to_stream(manager, stream_id, content):
    """Push content to a stream.

    Args:
        manager: StreamManager instance.
        stream_id: ID of the stream.
        content: Content to push.
    """
    stream = manager.get_stream(stream_id)
    if stream:
        stream.push_content(content)


def close_stream(manager, stream_id):
    """Close a stream.

    Args:
        manager: StreamManager instance.
        stream_id: ID of the stream to close.
    """
    manager.remove_stream(stream_id)
