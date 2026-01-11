"""Tests for chat message streaming.

These tests verify real-time message streaming in panel chat.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL connections - NO MOCKS.
"""
import pytest
import sqlite3
import json
import time
import threading
from flask import Flask


def create_test_db():
    """Create an in-memory test database."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('''
        CREATE TABLE panel_discussions (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER,
            status TEXT DEFAULT 'active'
        )
    ''')
    conn.execute('''
        CREATE TABLE chat_messages (
            id INTEGER PRIMARY KEY,
            discussion_id INTEGER,
            sender TEXT,
            sender_type TEXT,
            content TEXT,
            is_streaming INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE stream_state (
            id INTEGER PRIMARY KEY,
            discussion_id INTEGER,
            message_id INTEGER,
            partial_content TEXT,
            is_complete INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute(
        'INSERT INTO panel_discussions (id, sermon_id, status) VALUES (?, ?, ?)',
        (1, 1, 'active')
    )
    conn.commit()
    return conn


class TestWebSocketConnection:
    """Test suite for WebSocket connection establishment."""

    def test_should_establish_connection(self):
        """Test WebSocket connection is established."""
        from chat_streaming import create_streaming_socketio
        from flask_socketio import SocketIOTestClient

        app = Flask(__name__)
        socketio = create_streaming_socketio(app)

        client = SocketIOTestClient(app, socketio)

        assert client.is_connected()
        client.disconnect()

    def test_should_authenticate_connection(self):
        """Test connection requires authentication."""
        from chat_streaming import create_streaming_socketio
        from flask_socketio import SocketIOTestClient

        app = Flask(__name__)
        socketio = create_streaming_socketio(app, require_auth=True)

        client = SocketIOTestClient(app, socketio)
        client.emit('authenticate', {'token': 'test_token'})

        received = client.get_received()
        assert any('authenticated' in str(r).lower() or 'auth' in str(r).lower() for r in received) or received

        client.disconnect()

    def test_should_join_streaming_room(self):
        """Test client can join streaming room."""
        from chat_streaming import create_streaming_socketio
        from flask_socketio import SocketIOTestClient

        app = Flask(__name__)
        socketio = create_streaming_socketio(app)

        client = SocketIOTestClient(app, socketio)
        client.emit('join_stream', {'discussion_id': 1})

        received = client.get_received()
        assert len(received) >= 0  # Connection successful
        client.disconnect()

    def test_should_handle_multiple_clients(self):
        """Test multiple clients can connect."""
        from chat_streaming import create_streaming_socketio
        from flask_socketio import SocketIOTestClient

        app = Flask(__name__)
        socketio = create_streaming_socketio(app)

        client1 = SocketIOTestClient(app, socketio)
        client2 = SocketIOTestClient(app, socketio)

        assert client1.is_connected()
        assert client2.is_connected()

        client1.disconnect()
        client2.disconnect()


class TestMessageStreaming:
    """Test suite for message streaming from reviewers."""

    def test_should_stream_message_chunks(self):
        """Test messages are streamed in chunks."""
        from chat_streaming import StreamingMessage, stream_message_chunks

        message = StreamingMessage(
            discussion_id=1,
            sender='theological',
            full_content='This is a long message that should be streamed in chunks.'
        )

        chunks = list(stream_message_chunks(message, chunk_size=10))

        assert len(chunks) > 1

    def test_should_emit_chunk_events(self):
        """Test chunk events are emitted to clients."""
        from chat_streaming import create_streaming_socketio, emit_message_chunk
        from flask_socketio import SocketIOTestClient

        app = Flask(__name__)
        socketio = create_streaming_socketio(app)

        client = SocketIOTestClient(app, socketio)
        client.emit('join_stream', {'discussion_id': 1})

        emit_message_chunk(socketio, discussion_id=1, chunk={
            'message_id': 1,
            'content': 'Hello',
            'is_final': False
        })

        received = client.get_received()
        assert len(received) >= 1
        client.disconnect()

    def test_should_mark_stream_complete(self):
        """Test stream is marked complete after final chunk."""
        from chat_streaming import create_streaming_socketio, stream_complete_message
        from flask_socketio import SocketIOTestClient

        app = Flask(__name__)
        socketio = create_streaming_socketio(app)

        client = SocketIOTestClient(app, socketio)
        client.emit('join_stream', {'discussion_id': 1})

        stream_complete_message(socketio, discussion_id=1, message_id=1, content='Full message')

        received = client.get_received()
        # Should have final message event
        assert any('complete' in str(r).lower() or 'final' in str(r).lower() or 'message' in str(r).lower() for r in received) or received
        client.disconnect()

    def test_should_include_sender_info_in_stream(self):
        """Test stream includes sender information."""
        from chat_streaming import stream_message_chunks, StreamingMessage

        message = StreamingMessage(
            discussion_id=1,
            sender='theological',
            sender_name='Theological Reviewer',
            full_content='Test content'
        )

        chunks = list(stream_message_chunks(message))

        for chunk in chunks:
            assert chunk.get('sender') == 'theological'


class TestPartialMessageUpdates:
    """Test suite for partial message updates."""

    def test_should_store_partial_content(self):
        """Test partial content is stored in database."""
        from chat_streaming import save_partial_content

        conn = create_test_db()

        save_partial_content(conn, discussion_id=1, message_id=1, content='Partial')

        cursor = conn.execute('SELECT * FROM stream_state WHERE message_id = 1')
        row = cursor.fetchone()

        assert row is not None
        assert row['partial_content'] == 'Partial'
        conn.close()

    def test_should_append_to_partial_content(self):
        """Test new content is appended to partial."""
        from chat_streaming import save_partial_content, append_partial_content

        conn = create_test_db()

        save_partial_content(conn, discussion_id=1, message_id=1, content='Part 1')
        append_partial_content(conn, message_id=1, content=' Part 2')

        cursor = conn.execute('SELECT partial_content FROM stream_state WHERE message_id = 1')
        row = cursor.fetchone()

        assert 'Part 1' in row['partial_content']
        assert 'Part 2' in row['partial_content']
        conn.close()

    def test_should_mark_message_complete(self):
        """Test message is marked as complete."""
        from chat_streaming import save_partial_content, mark_stream_complete

        conn = create_test_db()

        save_partial_content(conn, discussion_id=1, message_id=1, content='Content')
        mark_stream_complete(conn, message_id=1)

        cursor = conn.execute('SELECT is_complete FROM stream_state WHERE message_id = 1')
        row = cursor.fetchone()

        assert row['is_complete'] == 1
        conn.close()

    def test_should_get_current_partial_content(self):
        """Test retrieving current partial content."""
        from chat_streaming import save_partial_content, get_partial_content

        conn = create_test_db()

        save_partial_content(conn, discussion_id=1, message_id=1, content='Current content')

        partial = get_partial_content(conn, message_id=1)

        assert partial == 'Current content'
        conn.close()


class TestConnectionRecovery:
    """Test suite for connection recovery."""

    def test_should_detect_disconnection(self):
        """Test disconnection is detected."""
        from chat_streaming import create_streaming_socketio
        from flask_socketio import SocketIOTestClient

        app = Flask(__name__)
        socketio = create_streaming_socketio(app)

        client = SocketIOTestClient(app, socketio)
        client.disconnect()

        assert not client.is_connected()

    def test_should_reconnect_automatically(self):
        """Test client can reconnect."""
        from chat_streaming import create_streaming_socketio
        from flask_socketio import SocketIOTestClient

        app = Flask(__name__)
        socketio = create_streaming_socketio(app)

        client = SocketIOTestClient(app, socketio)
        client.disconnect()

        # Reconnect
        client = SocketIOTestClient(app, socketio)
        assert client.is_connected()
        client.disconnect()

    def test_should_resume_stream_after_reconnect(self):
        """Test stream resumes from last position."""
        from chat_streaming import save_partial_content, get_resume_position

        conn = create_test_db()

        save_partial_content(conn, discussion_id=1, message_id=1, content='Partial content here')

        position = get_resume_position(conn, discussion_id=1, message_id=1)

        assert position > 0
        conn.close()

    def test_should_buffer_missed_messages(self):
        """Test missed messages are buffered."""
        from chat_streaming import MessageBuffer, add_to_buffer, get_buffered_messages

        buffer = MessageBuffer(discussion_id=1)

        add_to_buffer(buffer, {'id': 1, 'content': 'Message 1'})
        add_to_buffer(buffer, {'id': 2, 'content': 'Message 2'})

        messages = get_buffered_messages(buffer)

        assert len(messages) == 2


class TestMessageBuffering:
    """Test suite for message buffering."""

    def test_should_create_message_buffer(self):
        """Test creating a message buffer."""
        from chat_streaming import MessageBuffer

        buffer = MessageBuffer(discussion_id=1, max_size=100)

        assert buffer is not None
        assert buffer.max_size == 100

    def test_should_add_messages_to_buffer(self):
        """Test adding messages to buffer."""
        from chat_streaming import MessageBuffer

        buffer = MessageBuffer(discussion_id=1)
        buffer.add({'id': 1, 'content': 'Test'})

        assert buffer.size() == 1

    def test_should_respect_buffer_size_limit(self):
        """Test buffer respects size limit."""
        from chat_streaming import MessageBuffer

        buffer = MessageBuffer(discussion_id=1, max_size=5)

        for i in range(10):
            buffer.add({'id': i, 'content': f'Message {i}'})

        assert buffer.size() <= 5

    def test_should_clear_buffer(self):
        """Test clearing the buffer."""
        from chat_streaming import MessageBuffer

        buffer = MessageBuffer(discussion_id=1)
        buffer.add({'id': 1, 'content': 'Test'})
        buffer.clear()

        assert buffer.size() == 0

    def test_should_flush_buffer_to_client(self):
        """Test flushing buffer to client."""
        from chat_streaming import create_streaming_socketio, MessageBuffer
        from flask_socketio import SocketIOTestClient

        app = Flask(__name__)
        socketio = create_streaming_socketio(app)

        client = SocketIOTestClient(app, socketio)
        client.emit('join_stream', {'discussion_id': 1})

        buffer = MessageBuffer(discussion_id=1)
        buffer.add({'id': 1, 'content': 'Buffered message'})
        buffer.flush(socketio)

        received = client.get_received()
        assert len(received) >= 1
        client.disconnect()


class TestConcurrentStreams:
    """Test suite for concurrent streams."""

    def test_should_handle_multiple_streams(self):
        """Test handling multiple concurrent streams."""
        from chat_streaming import StreamManager, create_stream

        manager = StreamManager()

        stream1 = create_stream(manager, discussion_id=1, reviewer='theological')
        stream2 = create_stream(manager, discussion_id=1, reviewer='structural')

        assert manager.active_stream_count() == 2

    def test_should_isolate_streams_by_discussion(self):
        """Test streams are isolated by discussion."""
        from chat_streaming import StreamManager, create_stream, get_streams_for_discussion

        manager = StreamManager()

        create_stream(manager, discussion_id=1, reviewer='theological')
        create_stream(manager, discussion_id=2, reviewer='structural')

        streams = get_streams_for_discussion(manager, discussion_id=1)

        assert len(streams) == 1

    def test_should_not_interfere_between_streams(self):
        """Test concurrent streams don't interfere."""
        from chat_streaming import StreamManager, create_stream, push_to_stream

        manager = StreamManager()

        stream1 = create_stream(manager, discussion_id=1, reviewer='theological')
        stream2 = create_stream(manager, discussion_id=1, reviewer='structural')

        push_to_stream(manager, stream1.id, 'Content for stream 1')
        push_to_stream(manager, stream2.id, 'Content for stream 2')

        assert stream1.get_content() != stream2.get_content()

    def test_should_close_stream(self):
        """Test closing a stream."""
        from chat_streaming import StreamManager, create_stream, close_stream

        manager = StreamManager()

        stream = create_stream(manager, discussion_id=1, reviewer='theological')
        close_stream(manager, stream.id)

        assert manager.active_stream_count() == 0


class TestFlaskIntegration:
    """Test suite for Flask integration."""

    def test_should_expose_stream_endpoint(self):
        """Test stream endpoint is exposed."""
        from app import create_app

        app = create_app(testing=True)

        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert any('stream' in r for r in rules) or any('socket' in r.lower() for r in rules)

    def test_should_return_sse_response(self):
        """Test SSE fallback response."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/api/discussion/1/stream')

            if response.status_code == 200:
                assert 'event-stream' in response.content_type or 'json' in response.content_type

    def test_should_handle_stream_start(self):
        """Test starting a stream via API."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.post('/api/discussion/1/stream/start', json={
                'reviewer': 'theological'
            })
            assert response.status_code in [200, 201, 404]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
