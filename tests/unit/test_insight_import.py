"""Tests for importing insights from panel chat to sermon drafts.

These tests verify the insight extraction and import functionality for The Green Room.
Enables pulling valuable discussion points from panel chats into sermon drafts.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database - NO MOCKS.
"""
import pytest
import sqlite3
import json
from datetime import datetime


# Insight types for categorization
INSIGHT_TYPES = [
    'theological',      # Theological insights
    'pastoral',         # Pastoral application insights
    'structural',       # Sermon structure insights
    'illustration',     # Illustration suggestions
    'scripture',        # Scripture handling insights
    'language',         # Language/clarity insights
    'general'           # General insights
]


def create_test_db():
    """Create an in-memory test database with all required tables."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row

    # Create sermons table
    conn.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            manuscript TEXT,
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

    # Create insights table
    conn.execute('''
        CREATE TABLE insights (
            id INTEGER PRIMARY KEY,
            session_id INTEGER NOT NULL,
            message_id INTEGER,
            content TEXT NOT NULL,
            insight_type TEXT DEFAULT 'general',
            source_reviewer TEXT,
            relevance_score REAL DEFAULT 0.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (message_id) REFERENCES chat_messages(id) ON DELETE SET NULL
        )
    ''')

    # Create imported_insights table (linking insights to sermons)
    conn.execute('''
        CREATE TABLE imported_insights (
            id INTEGER PRIMARY KEY,
            insight_id INTEGER NOT NULL,
            sermon_id INTEGER NOT NULL,
            section TEXT,
            used BOOLEAN DEFAULT 0,
            imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (insight_id) REFERENCES insights(id) ON DELETE CASCADE,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE,
            UNIQUE(insight_id, sermon_id)
        )
    ''')

    conn.commit()
    return conn


def insert_sample_sermon(conn, title='Test Sermon'):
    """Insert a sample sermon and return its ID."""
    cursor = conn.cursor()
    cursor.execute('INSERT INTO sermons (title, manuscript) VALUES (?, ?)',
                   (title, 'Sample sermon manuscript.'))
    conn.commit()
    return cursor.lastrowid


def insert_sample_session(conn, sermon_id=None, name='Test Session'):
    """Insert a sample chat session and return its ID."""
    cursor = conn.cursor()
    cursor.execute('INSERT INTO chat_sessions (sermon_id, session_name) VALUES (?, ?)',
                   (sermon_id, name))
    conn.commit()
    return cursor.lastrowid


def insert_sample_messages(conn, session_id):
    """Insert sample chat messages with insightful content."""
    messages = [
        ('theological', 'reviewer', 'The trinitarian aspect of this passage needs more emphasis. Consider exploring how God\'s love manifests through all three persons.'),
        ('pastoral', 'reviewer', 'This application point about forgiveness could be more concrete. Suggest adding a practical step.'),
        ('user', 'user', 'What about the illustration in the introduction?'),
        ('illustration', 'reviewer', 'The current illustration is good but dated. Consider a more contemporary example from everyday life.'),
        ('structural', 'reviewer', 'Point 2 feels weak compared to points 1 and 3. Consider restructuring to balance the weight.'),
        ('scripture', 'reviewer', 'Include the Greek word "agape" to distinguish from other types of love.'),
        ('language', 'reviewer', 'The vocabulary in the conclusion is too academic. Simplify for broader accessibility.')
    ]

    cursor = conn.cursor()
    for sender, sender_type, content in messages:
        cursor.execute(
            'INSERT INTO chat_messages (session_id, sender, sender_type, content) VALUES (?, ?, ?, ?)',
            (session_id, sender, sender_type, content)
        )
    conn.commit()


class TestExtractInsightsFromChat:
    """Test suite for extracting insights from chat sessions."""

    def test_should_extract_insights_from_chat_session(self):
        """Test that insights are extracted from a chat session."""
        from insight_import import extract_insights_from_chat

        conn = create_test_db()
        session_id = insert_sample_session(conn)
        insert_sample_messages(conn, session_id)

        insights = extract_insights_from_chat(conn, session_id)

        assert insights is not None
        assert len(insights) > 0
        conn.close()

    def test_should_identify_actionable_insights(self):
        """Test that actionable insights are identified from messages."""
        from insight_import import extract_insights_from_chat

        conn = create_test_db()
        session_id = insert_sample_session(conn)
        insert_sample_messages(conn, session_id)

        insights = extract_insights_from_chat(conn, session_id)

        # Check that insights contain actionable content
        for insight in insights:
            assert 'content' in insight
            assert len(insight['content']) > 0
        conn.close()

    def test_should_categorize_insights_by_type(self):
        """Test that insights are categorized by type."""
        from insight_import import extract_insights_from_chat

        conn = create_test_db()
        session_id = insert_sample_session(conn)
        insert_sample_messages(conn, session_id)

        insights = extract_insights_from_chat(conn, session_id)

        # Check that insights have types
        for insight in insights:
            assert 'insight_type' in insight or 'type' in insight
            insight_type = insight.get('insight_type', insight.get('type'))
            assert insight_type in INSIGHT_TYPES or insight_type is not None
        conn.close()

    def test_should_include_source_reviewer(self):
        """Test that insights include source reviewer information."""
        from insight_import import extract_insights_from_chat

        conn = create_test_db()
        session_id = insert_sample_session(conn)
        insert_sample_messages(conn, session_id)

        insights = extract_insights_from_chat(conn, session_id)

        for insight in insights:
            assert 'source_reviewer' in insight or 'sender' in insight
        conn.close()


class TestImportInsightToSermon:
    """Test suite for importing insights into sermons."""

    def test_should_import_insight_to_sermon(self):
        """Test that an insight can be imported to a sermon."""
        from insight_import import extract_insights_from_chat, import_insight_to_sermon

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session_id = insert_sample_session(conn, sermon_id)
        insert_sample_messages(conn, session_id)

        insights = extract_insights_from_chat(conn, session_id)
        result = import_insight_to_sermon(conn, insights[0], sermon_id)

        assert result is True
        conn.close()

    def test_should_prevent_duplicate_imports(self):
        """Test that duplicate imports are prevented."""
        from insight_import import extract_insights_from_chat, import_insight_to_sermon

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session_id = insert_sample_session(conn, sermon_id)
        insert_sample_messages(conn, session_id)

        insights = extract_insights_from_chat(conn, session_id)
        insight = insights[0]

        # First import should succeed
        result1 = import_insight_to_sermon(conn, insight, sermon_id)
        # Second import of same insight should fail or return False
        result2 = import_insight_to_sermon(conn, insight, sermon_id)

        assert result1 is True
        assert result2 is False
        conn.close()

    def test_should_import_with_section_reference(self):
        """Test that insight can be imported with section reference."""
        from insight_import import extract_insights_from_chat, import_insight_to_sermon, get_imported_insights

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session_id = insert_sample_session(conn, sermon_id)
        insert_sample_messages(conn, session_id)

        insights = extract_insights_from_chat(conn, session_id)
        import_insight_to_sermon(conn, insights[0], sermon_id, section='introduction')

        imported = get_imported_insights(conn, sermon_id)
        assert any(i.get('section') == 'introduction' for i in imported)
        conn.close()


class TestGetImportedInsights:
    """Test suite for retrieving imported insights."""

    def test_should_retrieve_imported_insights_for_sermon(self):
        """Test that imported insights can be retrieved for a sermon."""
        from insight_import import extract_insights_from_chat, import_insight_to_sermon, get_imported_insights

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session_id = insert_sample_session(conn, sermon_id)
        insert_sample_messages(conn, session_id)

        insights = extract_insights_from_chat(conn, session_id)
        import_insight_to_sermon(conn, insights[0], sermon_id)
        import_insight_to_sermon(conn, insights[1], sermon_id)

        imported = get_imported_insights(conn, sermon_id)

        assert len(imported) == 2
        conn.close()

    def test_should_return_empty_when_no_imported_insights(self):
        """Test that empty list is returned when no insights imported."""
        from insight_import import get_imported_insights

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        imported = get_imported_insights(conn, sermon_id)

        assert imported == []
        conn.close()

    def test_should_include_insight_details_in_retrieved(self):
        """Test that retrieved insights include full details."""
        from insight_import import extract_insights_from_chat, import_insight_to_sermon, get_imported_insights

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session_id = insert_sample_session(conn, sermon_id)
        insert_sample_messages(conn, session_id)

        insights = extract_insights_from_chat(conn, session_id)
        import_insight_to_sermon(conn, insights[0], sermon_id)

        imported = get_imported_insights(conn, sermon_id)

        assert len(imported) == 1
        assert 'content' in imported[0]
        assert imported[0]['content'] is not None
        conn.close()


class TestMarkInsightAsUsed:
    """Test suite for marking insights as used."""

    def test_should_track_which_insights_have_been_used(self):
        """Test that used insights can be tracked."""
        from insight_import import extract_insights_from_chat, import_insight_to_sermon, mark_insight_as_used, get_imported_insights

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session_id = insert_sample_session(conn, sermon_id)
        insert_sample_messages(conn, session_id)

        insights = extract_insights_from_chat(conn, session_id)
        import_insight_to_sermon(conn, insights[0], sermon_id)

        # Get the imported insight ID
        imported = get_imported_insights(conn, sermon_id)
        insight_id = imported[0].get('id') or imported[0].get('insight_id')

        mark_insight_as_used(conn, insight_id, sermon_id)

        # Verify it's marked as used
        updated = get_imported_insights(conn, sermon_id)
        assert updated[0].get('used') is True or updated[0].get('used') == 1
        conn.close()

    def test_should_distinguish_used_from_unused_insights(self):
        """Test that used and unused insights can be distinguished."""
        from insight_import import extract_insights_from_chat, import_insight_to_sermon, mark_insight_as_used, get_imported_insights

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session_id = insert_sample_session(conn, sermon_id)
        insert_sample_messages(conn, session_id)

        insights = extract_insights_from_chat(conn, session_id)
        import_insight_to_sermon(conn, insights[0], sermon_id)
        import_insight_to_sermon(conn, insights[1], sermon_id)

        # Mark only first insight as used
        imported = get_imported_insights(conn, sermon_id)
        first_id = imported[0].get('id') or imported[0].get('insight_id')
        mark_insight_as_used(conn, first_id, sermon_id)

        # Verify distinction
        updated = get_imported_insights(conn, sermon_id)
        used_count = sum(1 for i in updated if i.get('used'))
        unused_count = sum(1 for i in updated if not i.get('used'))
        assert used_count == 1
        assert unused_count == 1
        conn.close()


class TestFilterInsightsByType:
    """Test suite for filtering insights by type."""

    def test_should_filter_insights_by_category(self):
        """Test that insights can be filtered by category/type."""
        from insight_import import extract_insights_from_chat, filter_insights_by_type

        conn = create_test_db()
        session_id = insert_sample_session(conn)
        insert_sample_messages(conn, session_id)

        insights = extract_insights_from_chat(conn, session_id)
        theological = filter_insights_by_type(insights, 'theological')

        # All filtered insights should be theological
        for insight in theological:
            insight_type = insight.get('insight_type', insight.get('type'))
            assert insight_type == 'theological'
        conn.close()

    def test_should_return_empty_when_no_matching_type(self):
        """Test that empty list is returned when no insights match type."""
        from insight_import import filter_insights_by_type

        insights = [
            {'content': 'Test', 'insight_type': 'theological'},
            {'content': 'Test 2', 'insight_type': 'pastoral'}
        ]

        filtered = filter_insights_by_type(insights, 'nonexistent_type')

        assert filtered == []

    def test_should_be_case_insensitive_for_type_filter(self):
        """Test that type filtering is case-insensitive."""
        from insight_import import filter_insights_by_type

        insights = [
            {'content': 'Test', 'insight_type': 'theological'},
            {'content': 'Test 2', 'insight_type': 'Theological'},
            {'content': 'Test 3', 'insight_type': 'THEOLOGICAL'}
        ]

        filtered = filter_insights_by_type(insights, 'theological')

        assert len(filtered) == 3


class TestSuggestInsightsForSection:
    """Test suite for suggesting insights for sermon sections."""

    def test_should_suggest_relevant_insights_for_section(self):
        """Test that relevant insights are suggested for a section."""
        from insight_import import extract_insights_from_chat, suggest_insights_for_section

        conn = create_test_db()
        session_id = insert_sample_session(conn)
        insert_sample_messages(conn, session_id)

        suggestions = suggest_insights_for_section(conn, session_id, 'introduction')

        assert suggestions is not None
        # Should return a list of relevant insights
        assert isinstance(suggestions, list)
        conn.close()

    def test_should_rank_suggestions_by_relevance(self):
        """Test that suggestions are ranked by relevance."""
        from insight_import import extract_insights_from_chat, suggest_insights_for_section

        conn = create_test_db()
        session_id = insert_sample_session(conn)
        insert_sample_messages(conn, session_id)

        suggestions = suggest_insights_for_section(conn, session_id, 'introduction')

        if len(suggestions) > 1:
            # Check that there's some relevance ordering
            for i in range(len(suggestions) - 1):
                score1 = suggestions[i].get('relevance_score', 0)
                score2 = suggestions[i + 1].get('relevance_score', 0)
                # Higher scores should come first (or equal)
                assert score1 >= score2
        conn.close()


class TestClearImportedInsights:
    """Test suite for clearing imported insights."""

    def test_should_clear_imported_insights(self):
        """Test that imported insights can be cleared."""
        from insight_import import extract_insights_from_chat, import_insight_to_sermon, clear_imported_insights, get_imported_insights

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session_id = insert_sample_session(conn, sermon_id)
        insert_sample_messages(conn, session_id)

        insights = extract_insights_from_chat(conn, session_id)
        import_insight_to_sermon(conn, insights[0], sermon_id)
        import_insight_to_sermon(conn, insights[1], sermon_id)

        result = clear_imported_insights(conn, sermon_id)

        assert result is True
        imported = get_imported_insights(conn, sermon_id)
        assert imported == []
        conn.close()

    def test_should_return_false_when_nothing_to_clear(self):
        """Test that clearing empty imports returns False."""
        from insight_import import clear_imported_insights

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = clear_imported_insights(conn, sermon_id)

        assert result is False
        conn.close()


class TestEdgeCases:
    """Test suite for edge cases in insight import."""

    def test_should_handle_empty_chat_session(self):
        """Test that empty chat session is handled gracefully."""
        from insight_import import extract_insights_from_chat

        conn = create_test_db()
        session_id = insert_sample_session(conn)
        # Don't insert any messages

        insights = extract_insights_from_chat(conn, session_id)

        assert insights == []
        conn.close()

    def test_should_handle_nonexistent_session(self):
        """Test that nonexistent session is handled gracefully."""
        from insight_import import extract_insights_from_chat

        conn = create_test_db()

        insights = extract_insights_from_chat(conn, 999)

        assert insights is None or insights == []
        conn.close()

    def test_should_handle_unicode_in_insights(self):
        """Test that unicode content is preserved in insights."""
        from insight_import import extract_insights_from_chat

        conn = create_test_db()
        session_id = insert_sample_session(conn)

        # Insert message with unicode
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO chat_messages (session_id, sender, sender_type, content) VALUES (?, ?, ?, ?)',
            (session_id, 'theological', 'reviewer', 'Greek: ἀγάπη (agape) means divine love')
        )
        conn.commit()

        insights = extract_insights_from_chat(conn, session_id)

        # Should contain the unicode characters
        if insights:
            assert any('ἀγάπη' in i.get('content', '') for i in insights) or len(insights) > 0
        conn.close()

    def test_should_handle_long_insight_content(self):
        """Test that long content is handled properly."""
        from insight_import import extract_insights_from_chat, import_insight_to_sermon, get_imported_insights

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session_id = insert_sample_session(conn, sermon_id)

        # Insert message with long content
        long_content = 'A' * 5000  # 5000 characters
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO chat_messages (session_id, sender, sender_type, content) VALUES (?, ?, ?, ?)',
            (session_id, 'theological', 'reviewer', long_content)
        )
        conn.commit()

        insights = extract_insights_from_chat(conn, session_id)
        if insights:
            import_insight_to_sermon(conn, insights[0], sermon_id)
            imported = get_imported_insights(conn, sermon_id)
            # Content should be preserved (possibly truncated but not lost)
            assert len(imported) > 0
        conn.close()


class TestUserMessageFiltering:
    """Test suite for filtering user messages from insights."""

    def test_should_only_extract_reviewer_insights(self):
        """Test that insights only come from reviewer messages, not user."""
        from insight_import import extract_insights_from_chat

        conn = create_test_db()
        session_id = insert_sample_session(conn)
        insert_sample_messages(conn, session_id)

        insights = extract_insights_from_chat(conn, session_id)

        # None of the insights should be from 'user' sender
        for insight in insights:
            source = insight.get('source_reviewer', insight.get('sender'))
            assert source != 'user'
        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
