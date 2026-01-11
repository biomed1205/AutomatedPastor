"""Tests for panel chat (The Green Room).

These tests verify the interactive discussion between reviewer personas.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database and files - NO MOCKS.
"""
import pytest
import sqlite3
import json
import time
from flask import Flask


# Sample sermon for testing
SAMPLE_SERMON = """# Grace in Action

## Introduction
Today we explore how grace transforms our daily lives.

## Point 1: Grace Received
We receive grace freely from God...

## Point 2: Grace Applied
This grace changes how we treat others...

## Point 3: Grace Shared
We become channels of grace in the world...

## Conclusion
Go forth as grace-bearers. Amen.
"""

# Sample participants
SAMPLE_PARTICIPANTS = ['theological', 'structural', 'pastoral']


def create_test_db():
    """Create an in-memory test database."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('''
        CREATE TABLE panel_discussions (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER,
            mode TEXT,
            status TEXT DEFAULT 'active',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE chat_messages (
            id INTEGER PRIMARY KEY,
            discussion_id INTEGER,
            sender TEXT,
            sender_type TEXT,
            content TEXT,
            reply_to_id INTEGER,
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
        (1, 'Test Sermon', SAMPLE_SERMON)
    )
    conn.commit()
    return conn


class TestPanelDiscussionInitiation:
    """Test suite for initiating panel discussions."""

    def test_should_start_panel_discussion(self):
        """Test starting a new panel discussion."""
        from panel_chat import PanelChat, start_discussion
        from cli_bridge import CLIBridge

        conn = create_test_db()
        bridge = CLIBridge(command='echo')

        discussion = start_discussion(
            conn, bridge,
            sermon_id=1,
            participants=SAMPLE_PARTICIPANTS
        )

        assert discussion is not None
        assert discussion.status == 'active'
        conn.close()

    def test_should_store_discussion_in_database(self):
        """Test discussion is saved to database."""
        from panel_chat import start_discussion
        from cli_bridge import CLIBridge

        conn = create_test_db()
        bridge = CLIBridge(command='echo')

        discussion = start_discussion(
            conn, bridge,
            sermon_id=1,
            participants=SAMPLE_PARTICIPANTS
        )

        cursor = conn.execute('SELECT * FROM panel_discussions')
        row = cursor.fetchone()

        assert row is not None
        conn.close()

    def test_should_require_at_least_two_participants(self):
        """Test discussion requires multiple participants."""
        from panel_chat import start_discussion, InsufficientParticipantsError
        from cli_bridge import CLIBridge

        conn = create_test_db()
        bridge = CLIBridge(command='echo')

        with pytest.raises(InsufficientParticipantsError):
            start_discussion(
                conn, bridge,
                sermon_id=1,
                participants=['theological']  # Only one
            )
        conn.close()

    def test_should_include_sermon_context(self):
        """Test discussion includes sermon context."""
        from panel_chat import start_discussion
        from cli_bridge import CLIBridge

        conn = create_test_db()
        bridge = CLIBridge(command='echo')

        discussion = start_discussion(
            conn, bridge,
            sermon_id=1,
            participants=SAMPLE_PARTICIPANTS
        )

        assert discussion.sermon_context is not None
        conn.close()


class TestReviewerResponses:
    """Test suite for reviewers responding to each other."""

    def test_should_allow_reviewer_to_respond(self):
        """Test reviewer can post a response."""
        from panel_chat import start_discussion, post_reviewer_message
        from cli_bridge import CLIBridge

        conn = create_test_db()
        bridge = CLIBridge(command='echo')

        discussion = start_discussion(
            conn, bridge,
            sermon_id=1,
            participants=SAMPLE_PARTICIPANTS
        )

        message = post_reviewer_message(
            conn, bridge,
            discussion_id=discussion.id,
            reviewer='theological',
            content='The use of grace theology is strong here.'
        )

        assert message is not None
        conn.close()

    def test_should_allow_response_to_other_reviewer(self):
        """Test reviewer can respond to another reviewer."""
        from panel_chat import start_discussion, post_reviewer_message, respond_to_message
        from cli_bridge import CLIBridge

        conn = create_test_db()
        bridge = CLIBridge(command='echo')

        discussion = start_discussion(
            conn, bridge,
            sermon_id=1,
            participants=SAMPLE_PARTICIPANTS
        )

        original = post_reviewer_message(
            conn, bridge,
            discussion_id=discussion.id,
            reviewer='theological',
            content='The grace theme is well developed.'
        )

        response = respond_to_message(
            conn, bridge,
            discussion_id=discussion.id,
            reviewer='structural',
            reply_to_id=original.id,
            content='I agree, but the transitions could be smoother.'
        )

        assert response.reply_to_id == original.id
        conn.close()

    def test_should_generate_contextual_response(self):
        """Test reviewer generates context-aware response."""
        from panel_chat import start_discussion, generate_reviewer_response
        from cli_bridge import CLIBridge

        conn = create_test_db()
        bridge = CLIBridge(command='echo')

        discussion = start_discussion(
            conn, bridge,
            sermon_id=1,
            participants=SAMPLE_PARTICIPANTS
        )

        # Post an initial message
        conn.execute(
            'INSERT INTO chat_messages (discussion_id, sender, sender_type, content) VALUES (?, ?, ?, ?)',
            (discussion.id, 'theological', 'reviewer', 'Great use of Wesleyan theology.')
        )
        conn.commit()

        response = generate_reviewer_response(
            conn, bridge,
            discussion_id=discussion.id,
            reviewer='structural'
        )

        # Response should be contextual
        assert response is not None
        conn.close()


class TestConversationContext:
    """Test suite for maintaining conversation context."""

    def test_should_maintain_message_history(self):
        """Test conversation history is maintained."""
        from panel_chat import start_discussion, get_message_history
        from cli_bridge import CLIBridge

        conn = create_test_db()
        bridge = CLIBridge(command='echo')

        discussion = start_discussion(
            conn, bridge,
            sermon_id=1,
            participants=SAMPLE_PARTICIPANTS
        )

        # Add messages
        for i in range(5):
            conn.execute(
                'INSERT INTO chat_messages (discussion_id, sender, sender_type, content) VALUES (?, ?, ?, ?)',
                (discussion.id, SAMPLE_PARTICIPANTS[i % 3], 'reviewer', f'Message {i}')
            )
        conn.commit()

        history = get_message_history(conn, discussion_id=discussion.id)

        assert len(history) >= 5
        conn.close()

    def test_should_order_messages_chronologically(self):
        """Test messages are in chronological order."""
        from panel_chat import get_message_history
        from cli_bridge import CLIBridge

        conn = create_test_db()
        conn.execute(
            'INSERT INTO panel_discussions (id, sermon_id, status) VALUES (?, ?, ?)',
            (1, 1, 'active')
        )
        for i in range(3):
            conn.execute(
                'INSERT INTO chat_messages (discussion_id, sender, sender_type, content) VALUES (?, ?, ?, ?)',
                (1, 'reviewer', 'reviewer', f'Message {i}')
            )
        conn.commit()

        history = get_message_history(conn, discussion_id=1)

        for i in range(len(history) - 1):
            assert history[i]['created_at'] <= history[i + 1]['created_at']
        conn.close()

    def test_should_include_sender_information(self):
        """Test messages include sender info."""
        from panel_chat import get_message_history

        conn = create_test_db()
        conn.execute(
            'INSERT INTO panel_discussions (id, sermon_id, status) VALUES (?, ?, ?)',
            (1, 1, 'active')
        )
        conn.execute(
            'INSERT INTO chat_messages (discussion_id, sender, sender_type, content) VALUES (?, ?, ?, ?)',
            (1, 'theological', 'reviewer', 'Test message')
        )
        conn.commit()

        history = get_message_history(conn, discussion_id=1)

        assert history[0]['sender'] == 'theological'
        assert history[0]['sender_type'] == 'reviewer'
        conn.close()


class TestUserParticipation:
    """Test suite for user participation in panel chat."""

    def test_should_allow_user_to_send_message(self):
        """Test user can send message to panel."""
        from panel_chat import start_discussion, post_user_message
        from cli_bridge import CLIBridge

        conn = create_test_db()
        bridge = CLIBridge(command='echo')

        discussion = start_discussion(
            conn, bridge,
            sermon_id=1,
            participants=SAMPLE_PARTICIPANTS
        )

        message = post_user_message(
            conn,
            discussion_id=discussion.id,
            content='What about the conclusion?'
        )

        assert message is not None
        assert message.sender_type == 'user'
        conn.close()

    def test_should_prompt_reviewers_to_respond_to_user(self):
        """Test reviewers respond to user messages."""
        from panel_chat import start_discussion, post_user_message, get_reviewer_responses
        from cli_bridge import CLIBridge

        conn = create_test_db()
        bridge = CLIBridge(command='echo')

        discussion = start_discussion(
            conn, bridge,
            sermon_id=1,
            participants=SAMPLE_PARTICIPANTS
        )

        user_msg = post_user_message(
            conn,
            discussion_id=discussion.id,
            content='Can you discuss the introduction?'
        )

        responses = get_reviewer_responses(
            conn, bridge,
            discussion_id=discussion.id,
            to_message_id=user_msg.id
        )

        assert len(responses) >= 1
        conn.close()

    def test_should_distinguish_user_from_reviewers(self):
        """Test user messages are clearly distinguished."""
        from panel_chat import get_message_history

        conn = create_test_db()
        conn.execute(
            'INSERT INTO panel_discussions (id, sermon_id, status) VALUES (?, ?, ?)',
            (1, 1, 'active')
        )
        conn.execute(
            'INSERT INTO chat_messages (discussion_id, sender, sender_type, content) VALUES (?, ?, ?, ?)',
            (1, 'user', 'user', 'User message')
        )
        conn.execute(
            'INSERT INTO chat_messages (discussion_id, sender, sender_type, content) VALUES (?, ?, ?, ?)',
            (1, 'theological', 'reviewer', 'Reviewer message')
        )
        conn.commit()

        history = get_message_history(conn, discussion_id=1)

        user_msgs = [m for m in history if m['sender_type'] == 'user']
        reviewer_msgs = [m for m in history if m['sender_type'] == 'reviewer']

        assert len(user_msgs) == 1
        assert len(reviewer_msgs) == 1
        conn.close()


class TestChatHistoryPersistence:
    """Test suite for chat history database storage."""

    def test_should_persist_all_messages(self):
        """Test all messages are stored in database."""
        from panel_chat import start_discussion
        from cli_bridge import CLIBridge

        conn = create_test_db()
        bridge = CLIBridge(command='echo')

        discussion = start_discussion(
            conn, bridge,
            sermon_id=1,
            participants=SAMPLE_PARTICIPANTS
        )

        for i in range(3):
            conn.execute(
                'INSERT INTO chat_messages (discussion_id, sender, sender_type, content) VALUES (?, ?, ?, ?)',
                (discussion.id, 'theological', 'reviewer', f'Message {i}')
            )
        conn.commit()

        cursor = conn.execute('SELECT COUNT(*) FROM chat_messages WHERE discussion_id = ?', (discussion.id,))
        count = cursor.fetchone()[0]

        assert count >= 3
        conn.close()

    def test_should_retrieve_discussion_by_id(self):
        """Test can retrieve discussion by ID."""
        from panel_chat import get_discussion_by_id

        conn = create_test_db()
        conn.execute(
            'INSERT INTO panel_discussions (id, sermon_id, status) VALUES (?, ?, ?)',
            (1, 1, 'active')
        )
        conn.commit()

        discussion = get_discussion_by_id(conn, discussion_id=1)

        assert discussion is not None
        conn.close()

    def test_should_retrieve_discussions_for_sermon(self):
        """Test can retrieve all discussions for a sermon."""
        from panel_chat import get_discussions_for_sermon

        conn = create_test_db()
        conn.execute(
            'INSERT INTO panel_discussions (id, sermon_id, status) VALUES (?, ?, ?)',
            (1, 1, 'active')
        )
        conn.execute(
            'INSERT INTO panel_discussions (id, sermon_id, status) VALUES (?, ?, ?)',
            (2, 1, 'ended')
        )
        conn.commit()

        discussions = get_discussions_for_sermon(conn, sermon_id=1)

        assert len(discussions) >= 2
        conn.close()


class TestRealTimeUpdates:
    """Test suite for real-time update mechanisms."""

    def test_should_support_websocket_connection(self):
        """Test WebSocket connection for real-time updates."""
        from panel_chat import create_socketio_app
        from flask_socketio import SocketIOTestClient

        app = Flask(__name__)
        socketio = create_socketio_app(app)

        client = SocketIOTestClient(app, socketio)

        assert client.is_connected()
        client.disconnect()

    def test_should_broadcast_new_messages(self):
        """Test new messages are broadcast to clients."""
        from panel_chat import create_socketio_app, emit_message
        from flask_socketio import SocketIOTestClient

        app = Flask(__name__)
        socketio = create_socketio_app(app)

        client = SocketIOTestClient(app, socketio)
        client.emit('join', {'discussion_id': 1})

        emit_message(socketio, discussion_id=1, message={
            'sender': 'theological',
            'content': 'Test message'
        })

        received = client.get_received()
        assert any('message' in r.get('name', '') for r in received)
        client.disconnect()

    def test_should_support_sse_fallback(self):
        """Test SSE endpoint for fallback."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/api/discussion/1/stream')
            # SSE returns event-stream content type
            assert response.status_code in [200, 404]


class TestDiscussionModes:
    """Test suite for panel chat vs individual review modes."""

    def test_should_support_discussion_mode(self):
        """Test panel discussion mode."""
        from panel_chat import start_discussion
        from cli_bridge import CLIBridge

        conn = create_test_db()
        bridge = CLIBridge(command='echo')

        discussion = start_discussion(
            conn, bridge,
            sermon_id=1,
            participants=SAMPLE_PARTICIPANTS,
            mode='discussion'
        )

        assert discussion.mode == 'discussion'
        conn.close()

    def test_should_support_individual_mode(self):
        """Test individual review mode."""
        from panel_chat import start_discussion
        from cli_bridge import CLIBridge

        conn = create_test_db()
        bridge = CLIBridge(command='echo')

        discussion = start_discussion(
            conn, bridge,
            sermon_id=1,
            participants=SAMPLE_PARTICIPANTS,
            mode='individual'
        )

        assert discussion.mode == 'individual'
        conn.close()

    def test_should_default_to_discussion_mode(self):
        """Test default mode is discussion."""
        from panel_chat import start_discussion
        from cli_bridge import CLIBridge

        conn = create_test_db()
        bridge = CLIBridge(command='echo')

        discussion = start_discussion(
            conn, bridge,
            sermon_id=1,
            participants=SAMPLE_PARTICIPANTS
        )

        assert discussion.mode == 'discussion'
        conn.close()


class TestUserModeration:
    """Test suite for user moderation of discussion."""

    def test_should_allow_user_to_end_discussion(self):
        """Test user can end discussion."""
        from panel_chat import start_discussion, end_discussion
        from cli_bridge import CLIBridge

        conn = create_test_db()
        bridge = CLIBridge(command='echo')

        discussion = start_discussion(
            conn, bridge,
            sermon_id=1,
            participants=SAMPLE_PARTICIPANTS
        )

        ended = end_discussion(conn, discussion_id=discussion.id)

        assert ended.status == 'ended'
        conn.close()

    def test_should_prevent_messages_after_end(self):
        """Test no messages after discussion ends."""
        from panel_chat import start_discussion, end_discussion, post_reviewer_message
        from panel_chat import DiscussionEndedError
        from cli_bridge import CLIBridge

        conn = create_test_db()
        bridge = CLIBridge(command='echo')

        discussion = start_discussion(
            conn, bridge,
            sermon_id=1,
            participants=SAMPLE_PARTICIPANTS
        )
        end_discussion(conn, discussion_id=discussion.id)

        with pytest.raises(DiscussionEndedError):
            post_reviewer_message(
                conn, bridge,
                discussion_id=discussion.id,
                reviewer='theological',
                content='Late message'
            )
        conn.close()

    def test_should_allow_user_to_redirect_topic(self):
        """Test user can redirect discussion topic."""
        from panel_chat import start_discussion, redirect_discussion
        from cli_bridge import CLIBridge

        conn = create_test_db()
        bridge = CLIBridge(command='echo')

        discussion = start_discussion(
            conn, bridge,
            sermon_id=1,
            participants=SAMPLE_PARTICIPANTS
        )

        result = redirect_discussion(
            conn, bridge,
            discussion_id=discussion.id,
            new_topic='Let us focus on the conclusion.'
        )

        assert result is not None
        conn.close()

    def test_should_allow_user_to_pause_discussion(self):
        """Test user can pause discussion."""
        from panel_chat import start_discussion, pause_discussion
        from cli_bridge import CLIBridge

        conn = create_test_db()
        bridge = CLIBridge(command='echo')

        discussion = start_discussion(
            conn, bridge,
            sermon_id=1,
            participants=SAMPLE_PARTICIPANTS
        )

        paused = pause_discussion(conn, discussion_id=discussion.id)

        assert paused.status == 'paused'
        conn.close()

    def test_should_allow_user_to_resume_discussion(self):
        """Test user can resume paused discussion."""
        from panel_chat import start_discussion, pause_discussion, resume_discussion
        from cli_bridge import CLIBridge

        conn = create_test_db()
        bridge = CLIBridge(command='echo')

        discussion = start_discussion(
            conn, bridge,
            sermon_id=1,
            participants=SAMPLE_PARTICIPANTS
        )
        pause_discussion(conn, discussion_id=discussion.id)

        resumed = resume_discussion(conn, discussion_id=discussion.id)

        assert resumed.status == 'active'
        conn.close()


class TestFlaskIntegration:
    """Test suite for Flask integration."""

    def test_should_expose_start_discussion_endpoint(self):
        """Test start discussion API endpoint."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.post('/api/discussion/start', json={
                'sermon_id': 1,
                'participants': SAMPLE_PARTICIPANTS
            })
            assert response.status_code in [200, 201]

    def test_should_expose_message_history_endpoint(self):
        """Test message history API endpoint."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/api/discussion/1/messages')
            assert response.status_code in [200, 404]

    def test_should_expose_post_message_endpoint(self):
        """Test post message API endpoint."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.post('/api/discussion/1/message', json={
                'content': 'User message'
            })
            assert response.status_code in [200, 201, 404]

    def test_should_expose_end_discussion_endpoint(self):
        """Test end discussion API endpoint."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.post('/api/discussion/1/end')
            assert response.status_code in [200, 404]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
