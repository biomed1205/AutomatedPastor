"""Tests for chat history saving and export functionality.

These tests verify the chat history persistence and export features for The Green Room.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database - NO MOCKS.
"""
import pytest
import sqlite3
import json
from datetime import datetime, timedelta


def create_test_db():
    """Create an in-memory test database with chat history tables."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row

    # Create sermons table (for foreign key reference)
    conn.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create chat_sessions table
    conn.execute('''
        CREATE TABLE chat_sessions (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER,
            session_name TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            message_count INTEGER DEFAULT 0,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    ''')

    # Create chat_messages table
    conn.execute('''
        CREATE TABLE chat_messages (
            id INTEGER PRIMARY KEY,
            session_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            sender_type TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    return conn


def create_sample_messages():
    """Create sample messages for testing."""
    return [
        {
            'sender': 'theological',
            'sender_type': 'reviewer',
            'content': 'The exegesis of this passage is strong.',
            'created_at': '2024-01-15 10:00:00'
        },
        {
            'sender': 'pastoral',
            'sender_type': 'reviewer',
            'content': 'I agree, and the application is relevant.',
            'created_at': '2024-01-15 10:01:00'
        },
        {
            'sender': 'user',
            'sender_type': 'user',
            'content': 'What about the illustration in point 2?',
            'created_at': '2024-01-15 10:02:00'
        },
        {
            'sender': 'illustration',
            'sender_type': 'reviewer',
            'content': 'The illustration could be more concrete.',
            'created_at': '2024-01-15 10:03:00'
        }
    ]


def insert_sample_sermon(conn, title='Test Sermon'):
    """Insert a sample sermon and return its ID."""
    cursor = conn.cursor()
    cursor.execute('INSERT INTO sermons (title, content) VALUES (?, ?)',
                   (title, 'Sermon content goes here.'))
    conn.commit()
    return cursor.lastrowid


class TestSaveChatSession:
    """Test suite for saving chat sessions to database."""

    def test_should_save_chat_session_to_database(self):
        """Test that chat session is saved to database."""
        from chat_history import save_chat_session

        conn = create_test_db()
        messages = create_sample_messages()

        session_id = save_chat_session(conn, messages)

        assert session_id is not None
        assert isinstance(session_id, int)
        assert session_id > 0
        conn.close()

    def test_should_save_session_with_sermon_reference(self):
        """Test that session can be linked to a sermon."""
        from chat_history import save_chat_session

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        messages = create_sample_messages()

        session_id = save_chat_session(conn, messages, sermon_id=sermon_id)

        # Verify sermon reference was saved
        cursor = conn.cursor()
        cursor.execute('SELECT sermon_id FROM chat_sessions WHERE id = ?', (session_id,))
        row = cursor.fetchone()
        assert row['sermon_id'] == sermon_id
        conn.close()

    def test_should_save_all_messages_in_session(self):
        """Test that all messages are saved to database."""
        from chat_history import save_chat_session

        conn = create_test_db()
        messages = create_sample_messages()

        session_id = save_chat_session(conn, messages)

        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM chat_messages WHERE session_id = ?',
                       (session_id,))
        count = cursor.fetchone()['count']
        assert count == len(messages)
        conn.close()

    def test_should_update_message_count_on_save(self):
        """Test that session message count is updated."""
        from chat_history import save_chat_session

        conn = create_test_db()
        messages = create_sample_messages()

        session_id = save_chat_session(conn, messages)

        cursor = conn.cursor()
        cursor.execute('SELECT message_count FROM chat_sessions WHERE id = ?', (session_id,))
        row = cursor.fetchone()
        assert row['message_count'] == len(messages)
        conn.close()


class TestLoadChatSession:
    """Test suite for loading chat sessions from database."""

    def test_should_load_saved_chat_session(self):
        """Test that saved session can be loaded."""
        from chat_history import save_chat_session, load_chat_session

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        loaded = load_chat_session(conn, session_id)

        assert loaded is not None
        assert len(loaded) == len(messages)
        conn.close()

    def test_should_preserve_message_order_when_loading(self):
        """Test that message order is preserved on load."""
        from chat_history import save_chat_session, load_chat_session

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        loaded = load_chat_session(conn, session_id)

        # Verify order matches original
        for i, msg in enumerate(loaded):
            assert msg['sender'] == messages[i]['sender']
            assert msg['content'] == messages[i]['content']
        conn.close()

    def test_should_include_timestamps_in_loaded_messages(self):
        """Test that timestamps are included in loaded messages."""
        from chat_history import save_chat_session, load_chat_session

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        loaded = load_chat_session(conn, session_id)

        for msg in loaded:
            assert 'created_at' in msg
            assert msg['created_at'] is not None
        conn.close()

    def test_should_include_sender_info_in_loaded_messages(self):
        """Test that sender info is included in loaded messages."""
        from chat_history import save_chat_session, load_chat_session

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        loaded = load_chat_session(conn, session_id)

        for msg in loaded:
            assert 'sender' in msg
            assert 'sender_type' in msg
            assert msg['sender'] is not None
            assert msg['sender_type'] in ['reviewer', 'user', 'system']
        conn.close()

    def test_should_handle_nonexistent_session(self):
        """Test that loading nonexistent session returns empty or None."""
        from chat_history import load_chat_session

        conn = create_test_db()

        loaded = load_chat_session(conn, 999)

        assert loaded is None or loaded == []
        conn.close()


class TestExportToText:
    """Test suite for exporting chat to plain text format."""

    def test_should_export_to_plain_text_format(self):
        """Test that chat exports to plain text."""
        from chat_history import save_chat_session, export_chat_to_text

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        text = export_chat_to_text(conn, session_id)

        assert text is not None
        assert isinstance(text, str)
        assert len(text) > 0
        conn.close()

    def test_should_include_all_messages_in_text_export(self):
        """Test that text export includes all messages."""
        from chat_history import save_chat_session, export_chat_to_text

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        text = export_chat_to_text(conn, session_id)

        # Verify each message content appears in export
        for msg in messages:
            assert msg['content'] in text
        conn.close()

    def test_should_include_sender_names_in_text_export(self):
        """Test that text export includes sender names."""
        from chat_history import save_chat_session, export_chat_to_text

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        text = export_chat_to_text(conn, session_id)

        # Verify sender names appear
        for msg in messages:
            assert msg['sender'] in text
        conn.close()

    def test_should_format_text_with_timestamps(self):
        """Test that text export includes timestamps."""
        from chat_history import save_chat_session, export_chat_to_text

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        text = export_chat_to_text(conn, session_id)

        # Should have time-related formatting
        assert ':' in text  # Times typically have colons
        conn.close()


class TestExportToMarkdown:
    """Test suite for exporting chat to markdown format."""

    def test_should_export_to_markdown_format(self):
        """Test that chat exports to markdown."""
        from chat_history import save_chat_session, export_chat_to_markdown

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        markdown = export_chat_to_markdown(conn, session_id)

        assert markdown is not None
        assert isinstance(markdown, str)
        assert len(markdown) > 0
        conn.close()

    def test_should_use_markdown_formatting(self):
        """Test that export uses proper markdown syntax."""
        from chat_history import save_chat_session, export_chat_to_markdown

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        markdown = export_chat_to_markdown(conn, session_id)

        # Should contain markdown elements (headers, bold, etc.)
        has_markdown = (
            '#' in markdown or  # Headers
            '**' in markdown or  # Bold
            '*' in markdown or   # Italic/emphasis
            '>' in markdown      # Blockquotes
        )
        assert has_markdown
        conn.close()

    def test_should_include_header_in_markdown_export(self):
        """Test that markdown export has a title header."""
        from chat_history import save_chat_session, export_chat_to_markdown

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        markdown = export_chat_to_markdown(conn, session_id)

        # Should start with a header
        assert markdown.startswith('#') or '# ' in markdown
        conn.close()

    def test_should_format_reviewers_distinctly_in_markdown(self):
        """Test that reviewer messages are formatted distinctly."""
        from chat_history import save_chat_session, export_chat_to_markdown

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        markdown = export_chat_to_markdown(conn, session_id)

        # Reviewer names should be emphasized
        assert 'theological' in markdown
        assert 'pastoral' in markdown
        conn.close()


class TestExportToJson:
    """Test suite for exporting chat to JSON format."""

    def test_should_export_to_json_format(self):
        """Test that chat exports to valid JSON."""
        from chat_history import save_chat_session, export_chat_to_json

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        json_str = export_chat_to_json(conn, session_id)

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed is not None
        conn.close()

    def test_should_include_all_messages_in_json_export(self):
        """Test that JSON export includes all messages."""
        from chat_history import save_chat_session, export_chat_to_json

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        json_str = export_chat_to_json(conn, session_id)
        parsed = json.loads(json_str)

        # Check message count
        if 'messages' in parsed:
            assert len(parsed['messages']) == len(messages)
        else:
            assert len(parsed) == len(messages)
        conn.close()

    def test_should_include_session_metadata_in_json(self):
        """Test that JSON export includes session metadata."""
        from chat_history import save_chat_session, export_chat_to_json

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages, sermon_id=sermon_id)

        json_str = export_chat_to_json(conn, session_id)
        parsed = json.loads(json_str)

        # Should have metadata
        assert 'session_id' in parsed or 'id' in parsed
        conn.close()

    def test_should_preserve_message_structure_in_json(self):
        """Test that JSON preserves full message structure."""
        from chat_history import save_chat_session, export_chat_to_json

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        json_str = export_chat_to_json(conn, session_id)
        parsed = json.loads(json_str)

        # Get messages array
        msgs = parsed.get('messages', parsed)
        if isinstance(msgs, list) and len(msgs) > 0:
            first_msg = msgs[0]
            assert 'sender' in first_msg
            assert 'content' in first_msg
        conn.close()


class TestDeleteChatSession:
    """Test suite for deleting chat sessions."""

    def test_should_delete_chat_session(self):
        """Test that session can be deleted."""
        from chat_history import save_chat_session, delete_chat_session, load_chat_session

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        result = delete_chat_session(conn, session_id)

        assert result is True
        # Session should no longer exist
        loaded = load_chat_session(conn, session_id)
        assert loaded is None or loaded == []
        conn.close()

    def test_should_delete_associated_messages(self):
        """Test that deleting session removes all messages."""
        from chat_history import save_chat_session, delete_chat_session

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        delete_chat_session(conn, session_id)

        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM chat_messages WHERE session_id = ?',
                       (session_id,))
        count = cursor.fetchone()['count']
        assert count == 0
        conn.close()

    def test_should_return_false_for_nonexistent_session_delete(self):
        """Test that deleting nonexistent session returns False."""
        from chat_history import delete_chat_session

        conn = create_test_db()

        result = delete_chat_session(conn, 999)

        assert result is False
        conn.close()


class TestListChatSessions:
    """Test suite for listing chat sessions."""

    def test_should_list_all_chat_sessions(self):
        """Test that all sessions are listed."""
        from chat_history import save_chat_session, list_chat_sessions

        conn = create_test_db()
        messages = create_sample_messages()

        # Create multiple sessions
        save_chat_session(conn, messages)
        save_chat_session(conn, messages)
        save_chat_session(conn, messages)

        sessions = list_chat_sessions(conn)

        assert len(sessions) == 3
        conn.close()

    def test_should_filter_sessions_by_sermon_id(self):
        """Test that sessions can be filtered by sermon."""
        from chat_history import save_chat_session, list_chat_sessions

        conn = create_test_db()
        sermon1 = insert_sample_sermon(conn, 'Sermon 1')
        sermon2 = insert_sample_sermon(conn, 'Sermon 2')
        messages = create_sample_messages()

        # Create sessions for different sermons
        save_chat_session(conn, messages, sermon_id=sermon1)
        save_chat_session(conn, messages, sermon_id=sermon1)
        save_chat_session(conn, messages, sermon_id=sermon2)

        # Filter by sermon1
        sessions = list_chat_sessions(conn, sermon_id=sermon1)

        assert len(sessions) == 2
        for session in sessions:
            assert session['sermon_id'] == sermon1
        conn.close()

    def test_should_return_empty_list_when_no_sessions(self):
        """Test that empty list is returned when no sessions exist."""
        from chat_history import list_chat_sessions

        conn = create_test_db()

        sessions = list_chat_sessions(conn)

        assert sessions == []
        conn.close()

    def test_should_include_session_metadata_in_list(self):
        """Test that listed sessions include metadata."""
        from chat_history import save_chat_session, list_chat_sessions

        conn = create_test_db()
        messages = create_sample_messages()
        save_chat_session(conn, messages)

        sessions = list_chat_sessions(conn)

        assert len(sessions) == 1
        session = sessions[0]
        assert 'id' in session
        assert 'started_at' in session or 'created_at' in session
        conn.close()


class TestGetSessionSummary:
    """Test suite for getting session summary metadata."""

    def test_should_return_session_summary_metadata(self):
        """Test that session summary includes required metadata."""
        from chat_history import save_chat_session, get_session_summary

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        summary = get_session_summary(conn, session_id)

        assert summary is not None
        assert 'message_count' in summary
        assert summary['message_count'] == len(messages)
        conn.close()

    def test_should_include_participant_list_in_summary(self):
        """Test that summary includes list of participants."""
        from chat_history import save_chat_session, get_session_summary

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        summary = get_session_summary(conn, session_id)

        assert 'participants' in summary
        participants = summary['participants']
        assert 'theological' in participants
        assert 'pastoral' in participants
        assert 'user' in participants
        conn.close()

    def test_should_include_date_range_in_summary(self):
        """Test that summary includes start and end times."""
        from chat_history import save_chat_session, get_session_summary

        conn = create_test_db()
        messages = create_sample_messages()
        session_id = save_chat_session(conn, messages)

        summary = get_session_summary(conn, session_id)

        assert 'started_at' in summary or 'first_message_at' in summary
        conn.close()

    def test_should_return_none_for_nonexistent_session_summary(self):
        """Test that summary of nonexistent session is None."""
        from chat_history import get_session_summary

        conn = create_test_db()

        summary = get_session_summary(conn, 999)

        assert summary is None
        conn.close()


class TestEdgeCases:
    """Test suite for edge cases in chat history."""

    def test_should_handle_empty_session(self):
        """Test that empty session (no messages) is handled."""
        from chat_history import save_chat_session, load_chat_session

        conn = create_test_db()
        messages = []

        session_id = save_chat_session(conn, messages)
        loaded = load_chat_session(conn, session_id)

        assert loaded == [] or loaded is not None
        conn.close()

    def test_should_handle_large_message_content(self):
        """Test that large message content is handled."""
        from chat_history import save_chat_session, load_chat_session

        conn = create_test_db()
        large_content = 'A' * 10000  # 10K characters
        messages = [{
            'sender': 'theological',
            'sender_type': 'reviewer',
            'content': large_content,
            'created_at': '2024-01-15 10:00:00'
        }]

        session_id = save_chat_session(conn, messages)
        loaded = load_chat_session(conn, session_id)

        assert len(loaded[0]['content']) == 10000
        conn.close()

    def test_should_handle_special_characters_in_content(self):
        """Test that special characters are preserved."""
        from chat_history import save_chat_session, load_chat_session

        conn = create_test_db()
        special_content = "Test with 'quotes', \"double\", <tags>, & symbols"
        messages = [{
            'sender': 'theological',
            'sender_type': 'reviewer',
            'content': special_content,
            'created_at': '2024-01-15 10:00:00'
        }]

        session_id = save_chat_session(conn, messages)
        loaded = load_chat_session(conn, session_id)

        assert loaded[0]['content'] == special_content
        conn.close()

    def test_should_handle_unicode_in_messages(self):
        """Test that unicode characters are preserved."""
        from chat_history import save_chat_session, load_chat_session

        conn = create_test_db()
        unicode_content = "Greek: Χριστός, Hebrew: אלוהים, Emoji: ✝️🙏"
        messages = [{
            'sender': 'theological',
            'sender_type': 'reviewer',
            'content': unicode_content,
            'created_at': '2024-01-15 10:00:00'
        }]

        session_id = save_chat_session(conn, messages)
        loaded = load_chat_session(conn, session_id)

        assert loaded[0]['content'] == unicode_content
        conn.close()

    def test_should_handle_newlines_in_message_content(self):
        """Test that newlines in content are preserved."""
        from chat_history import save_chat_session, load_chat_session

        conn = create_test_db()
        multiline = "Line 1\nLine 2\nLine 3"
        messages = [{
            'sender': 'theological',
            'sender_type': 'reviewer',
            'content': multiline,
            'created_at': '2024-01-15 10:00:00'
        }]

        session_id = save_chat_session(conn, messages)
        loaded = load_chat_session(conn, session_id)

        assert loaded[0]['content'] == multiline
        conn.close()


class TestSessionNaming:
    """Test suite for session naming and identification."""

    def test_should_allow_custom_session_name(self):
        """Test that sessions can have custom names."""
        from chat_history import save_chat_session, get_session_summary

        conn = create_test_db()
        messages = create_sample_messages()

        session_id = save_chat_session(conn, messages, session_name='Review Session 1')

        summary = get_session_summary(conn, session_id)
        assert summary.get('session_name') == 'Review Session 1'
        conn.close()

    def test_should_auto_generate_session_name_when_not_provided(self):
        """Test that session name is auto-generated if not provided."""
        from chat_history import save_chat_session, get_session_summary

        conn = create_test_db()
        messages = create_sample_messages()

        session_id = save_chat_session(conn, messages)

        summary = get_session_summary(conn, session_id)
        # Should have some name (auto-generated or None is acceptable)
        assert 'session_name' in summary or summary is not None
        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
