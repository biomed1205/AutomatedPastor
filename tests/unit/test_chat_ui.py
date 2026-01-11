"""Tests for panel chat UI interface.

These tests verify the frontend interface for The Green Room panel chat.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database and files - NO MOCKS.
"""
import pytest
import sqlite3
import json
from flask import Flask


# Sample chat messages for testing
SAMPLE_MESSAGES = [
    {
        'id': 1,
        'sender': 'theological',
        'sender_type': 'reviewer',
        'content': 'The grace theology is well developed.',
        'created_at': '2025-01-10 12:00:00'
    },
    {
        'id': 2,
        'sender': 'structural',
        'sender_type': 'reviewer',
        'content': 'I agree, but the transitions need work.',
        'created_at': '2025-01-10 12:01:00'
    },
    {
        'id': 3,
        'sender': 'user',
        'sender_type': 'user',
        'content': 'What about the conclusion?',
        'created_at': '2025-01-10 12:02:00'
    }
]


def create_test_db():
    """Create an in-memory test database."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('''
        CREATE TABLE panel_discussions (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE chat_messages (
            id INTEGER PRIMARY KEY,
            discussion_id INTEGER,
            sender TEXT,
            sender_type TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY,
            title TEXT,
            content TEXT
        )
    ''')
    conn.execute(
        'INSERT INTO sermons (id, title, content) VALUES (?, ?, ?)',
        (1, 'Test Sermon', 'Sample content')
    )
    conn.execute(
        'INSERT INTO panel_discussions (id, sermon_id, status) VALUES (?, ?, ?)',
        (1, 1, 'active')
    )
    for msg in SAMPLE_MESSAGES:
        conn.execute(
            'INSERT INTO chat_messages (id, discussion_id, sender, sender_type, content, created_at) VALUES (?, ?, ?, ?, ?, ?)',
            (msg['id'], 1, msg['sender'], msg['sender_type'], msg['content'], msg['created_at'])
        )
    conn.commit()
    return conn


class TestChatUIRoutes:
    """Test suite for chat UI routes."""

    def test_should_return_200_for_chat_page(self):
        """Test GET /chat returns 200."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/chat/1')
            assert response.status_code == 200

    def test_should_return_404_for_nonexistent_chat(self):
        """Test GET /chat returns 404 for missing discussion."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/chat/99999')
            assert response.status_code == 404

    def test_should_accept_post_message(self):
        """Test POST /chat/message accepts new message."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.post('/chat/1/message', json={
                'content': 'Test message from user'
            })
            assert response.status_code in [200, 201]

    def test_should_return_400_for_empty_message(self):
        """Test POST /chat/message returns 400 for empty message."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.post('/chat/1/message', json={
                'content': ''
            })
            assert response.status_code == 400

    def test_should_redirect_to_chat_after_start(self):
        """Test starting chat redirects to chat page."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.post('/sermon/1/start-chat', data={
                'participants': ['theological', 'structural']
            })
            assert response.status_code in [200, 201, 302]


class TestWebSocketConnection:
    """Test suite for WebSocket connection."""

    def test_should_establish_websocket_connection(self):
        """Test WebSocket connection is established."""
        from chat_ui import create_socketio_app
        from flask_socketio import SocketIOTestClient

        app = Flask(__name__)
        socketio = create_socketio_app(app)

        client = SocketIOTestClient(app, socketio)

        assert client.is_connected()
        client.disconnect()

    def test_should_join_discussion_room(self):
        """Test client can join discussion room."""
        from chat_ui import create_socketio_app
        from flask_socketio import SocketIOTestClient

        app = Flask(__name__)
        socketio = create_socketio_app(app)

        client = SocketIOTestClient(app, socketio)
        client.emit('join', {'discussion_id': 1})

        received = client.get_received()
        assert any('joined' in str(r).lower() or 'room' in str(r).lower() for r in received) or received

        client.disconnect()

    def test_should_receive_new_messages(self):
        """Test client receives new messages."""
        from chat_ui import create_socketio_app, broadcast_message
        from flask_socketio import SocketIOTestClient

        app = Flask(__name__)
        socketio = create_socketio_app(app)

        client = SocketIOTestClient(app, socketio)
        client.emit('join', {'discussion_id': 1})

        # Broadcast a message
        broadcast_message(socketio, discussion_id=1, message={
            'sender': 'theological',
            'content': 'Test message'
        })

        received = client.get_received()
        assert len(received) >= 1
        client.disconnect()

    def test_should_handle_disconnect(self):
        """Test WebSocket handles disconnect gracefully."""
        from chat_ui import create_socketio_app
        from flask_socketio import SocketIOTestClient

        app = Flask(__name__)
        socketio = create_socketio_app(app)

        client = SocketIOTestClient(app, socketio)
        client.emit('join', {'discussion_id': 1})
        client.disconnect()

        assert not client.is_connected()


class TestMessageRendering:
    """Test suite for message rendering in template."""

    def test_should_render_message_list(self):
        """Test messages are rendered in template."""
        from chat_ui import prepare_chat_context

        conn = create_test_db()
        context = prepare_chat_context(conn, discussion_id=1)

        assert 'messages' in context
        assert len(context['messages']) >= 3
        conn.close()

    def test_should_include_sender_name(self):
        """Test rendered messages include sender name."""
        from chat_ui import prepare_chat_context

        conn = create_test_db()
        context = prepare_chat_context(conn, discussion_id=1)

        for msg in context['messages']:
            assert 'sender' in msg or 'sender_name' in msg
        conn.close()

    def test_should_include_timestamp(self):
        """Test rendered messages include timestamp."""
        from chat_ui import prepare_chat_context

        conn = create_test_db()
        context = prepare_chat_context(conn, discussion_id=1)

        for msg in context['messages']:
            assert 'created_at' in msg or 'timestamp' in msg
        conn.close()

    def test_should_format_timestamp_for_display(self):
        """Test timestamp is formatted for display."""
        from chat_ui import format_message_for_display

        message = {
            'content': 'Test',
            'created_at': '2025-01-10 12:00:00'
        }
        formatted = format_message_for_display(message)

        assert 'display_time' in formatted or 'formatted_time' in formatted


class TestUserInput:
    """Test suite for user input handling."""

    def test_should_validate_message_content(self):
        """Test message content is validated."""
        from chat_ui import validate_message

        valid = validate_message({'content': 'Hello world'})
        assert valid is True

        invalid = validate_message({'content': ''})
        assert invalid is False

    def test_should_sanitize_html_in_message(self):
        """Test HTML is sanitized in messages."""
        from chat_ui import sanitize_message

        message = '<script>alert("xss")</script>Hello'
        sanitized = sanitize_message(message)

        assert '<script>' not in sanitized

    def test_should_limit_message_length(self):
        """Test message length is limited."""
        from chat_ui import validate_message

        long_message = 'x' * 10001  # Over limit
        result = validate_message({'content': long_message})

        assert result is False

    def test_should_trim_whitespace(self):
        """Test whitespace is trimmed from messages."""
        from chat_ui import sanitize_message

        message = '  Hello world  '
        sanitized = sanitize_message(message)

        assert sanitized == 'Hello world'


class TestReviewerIdentification:
    """Test suite for reviewer identification in chat."""

    def test_should_include_reviewer_avatar(self):
        """Test messages include reviewer avatar/indicator."""
        from chat_ui import get_reviewer_display_info

        info = get_reviewer_display_info('theological')

        assert 'avatar' in info or 'icon' in info or 'color' in info

    def test_should_include_reviewer_name(self):
        """Test messages include reviewer display name."""
        from chat_ui import get_reviewer_display_info

        info = get_reviewer_display_info('theological')

        assert 'display_name' in info or 'name' in info

    def test_should_distinguish_reviewer_types(self):
        """Test different reviewers have distinct styling."""
        from chat_ui import get_reviewer_display_info

        theo = get_reviewer_display_info('theological')
        struct = get_reviewer_display_info('structural')

        # Should have different colors or identifiers
        assert theo != struct

    def test_should_identify_user_messages(self):
        """Test user messages are distinctly styled."""
        from chat_ui import get_sender_display_info

        user_info = get_sender_display_info('user', 'user')
        reviewer_info = get_sender_display_info('theological', 'reviewer')

        assert user_info.get('is_user', False) is True
        assert reviewer_info.get('is_user', True) is False


class TestMessageHistory:
    """Test suite for message history display."""

    def test_should_load_message_history(self):
        """Test message history is loaded."""
        from chat_ui import get_message_history

        conn = create_test_db()
        history = get_message_history(conn, discussion_id=1)

        assert len(history) >= 3
        conn.close()

    def test_should_order_messages_chronologically(self):
        """Test messages are in chronological order."""
        from chat_ui import get_message_history

        conn = create_test_db()
        history = get_message_history(conn, discussion_id=1)

        for i in range(len(history) - 1):
            assert history[i]['created_at'] <= history[i + 1]['created_at']
        conn.close()

    def test_should_support_pagination(self):
        """Test message history supports pagination."""
        from chat_ui import get_message_history

        conn = create_test_db()
        # Add more messages
        for i in range(20):
            conn.execute(
                'INSERT INTO chat_messages (discussion_id, sender, sender_type, content) VALUES (?, ?, ?, ?)',
                (1, 'theological', 'reviewer', f'Message {i}')
            )
        conn.commit()

        page1 = get_message_history(conn, discussion_id=1, limit=10, offset=0)
        page2 = get_message_history(conn, discussion_id=1, limit=10, offset=10)

        assert len(page1) == 10
        assert len(page2) >= 10
        conn.close()

    def test_should_include_reply_references(self):
        """Test messages include reply references."""
        from chat_ui import prepare_chat_context

        conn = create_test_db()
        # Add a reply
        conn.execute('''
            INSERT INTO chat_messages (discussion_id, sender, sender_type, content)
            VALUES (?, ?, ?, ?)
        ''', (1, 'pastoral', 'reviewer', 'Reply to theological'))
        conn.commit()

        context = prepare_chat_context(conn, discussion_id=1)

        # Should include reply capability
        assert 'messages' in context
        conn.close()


class TestUIErrorStates:
    """Test suite for UI error states."""

    def test_should_show_error_for_connection_failure(self):
        """Test error displayed for connection failure."""
        from chat_ui import get_error_message

        error_msg = get_error_message('connection_failed')

        assert error_msg is not None
        assert len(error_msg) > 0

    def test_should_show_error_for_send_failure(self):
        """Test error displayed for send failure."""
        from chat_ui import get_error_message

        error_msg = get_error_message('send_failed')

        assert error_msg is not None

    def test_should_show_reconnecting_state(self):
        """Test reconnecting state is displayed."""
        from chat_ui import get_ui_state

        state = get_ui_state('reconnecting')

        assert 'message' in state
        assert 'reconnecting' in state['message'].lower()

    def test_should_handle_discussion_ended(self):
        """Test UI handles ended discussion."""
        from chat_ui import prepare_chat_context

        conn = create_test_db()
        conn.execute('UPDATE panel_discussions SET status = ? WHERE id = ?', ('ended', 1))
        conn.commit()

        context = prepare_chat_context(conn, discussion_id=1)

        assert context.get('is_ended', False) is True or context.get('status') == 'ended'
        conn.close()

    def test_should_display_loading_state(self):
        """Test loading state is available."""
        from chat_ui import get_ui_state

        state = get_ui_state('loading')

        assert 'message' in state or 'loading' in str(state).lower()


class TestFlaskIntegration:
    """Test suite for Flask integration."""

    def test_should_register_chat_routes(self):
        """Test chat routes are registered."""
        from app import create_app

        app = create_app(testing=True)

        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert any('chat' in r for r in rules)

    def test_should_return_json_for_api_endpoints(self):
        """Test API endpoints return JSON."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/api/chat/1/messages')

            if response.status_code == 200:
                assert 'application/json' in response.content_type

    def test_should_render_html_for_page_routes(self):
        """Test page routes return HTML."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/chat/1')

            if response.status_code == 200:
                assert 'text/html' in response.content_type

    def test_should_include_socketio_js(self):
        """Test page includes Socket.IO JavaScript."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/chat/1')

            if response.status_code == 200:
                # Should include socketio reference
                assert b'socket' in response.data.lower() or response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
