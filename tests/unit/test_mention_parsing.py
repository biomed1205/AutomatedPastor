"""Tests for @ mention parsing in panel chat.

These tests verify the @mention parsing functionality for The Green Room.
Mentions allow users to address specific reviewers in the chat.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database - NO MOCKS.
"""
import pytest
import sqlite3


# Default reviewer types (7 reviewers)
DEFAULT_REVIEWERS = [
    'theological',      # Theological accuracy reviewer
    'pastoral',         # Pastoral application reviewer
    'structural',       # Sermon structure reviewer
    'engagement',       # Audience engagement reviewer
    'illustration',     # Illustration quality reviewer
    'scripture',        # Scripture handling reviewer
    'language'          # Language/clarity reviewer
]


def create_test_db():
    """Create an in-memory test database with custom reviewers table."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('''
        CREATE TABLE custom_reviewers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            prompt_template TEXT,
            active INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    return conn


def insert_custom_reviewer(conn, name, description='Test reviewer'):
    """Insert a custom reviewer into the database."""
    conn.execute(
        'INSERT INTO custom_reviewers (name, description) VALUES (?, ?)',
        (name, description)
    )
    conn.commit()


class TestSingleMentionParsing:
    """Test suite for parsing single @mentions."""

    def test_should_parse_single_mention_when_valid_reviewer_name(self):
        """Test parsing a single @mention with a valid default reviewer name."""
        from panel_chat import parse_mentions

        message = "What do you think @theological?"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert 'theological' in result
        assert len(result) == 1

    def test_should_parse_single_mention_when_at_start_of_message(self):
        """Test parsing @mention at the beginning of a message."""
        from panel_chat import parse_mentions

        message = "@pastoral can you review the application section?"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert 'pastoral' in result
        assert len(result) == 1

    def test_should_parse_single_mention_when_at_end_of_message(self):
        """Test parsing @mention at the end of a message."""
        from panel_chat import parse_mentions

        message = "Great insights on the structure @structural"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert 'structural' in result
        assert len(result) == 1

    def test_should_parse_single_mention_when_in_middle_of_message(self):
        """Test parsing @mention in the middle of a message."""
        from panel_chat import parse_mentions

        message = "I agree with @engagement that the opening needs work"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert 'engagement' in result
        assert len(result) == 1


class TestMultipleMentionParsing:
    """Test suite for parsing multiple @mentions."""

    def test_should_parse_multiple_mentions_when_two_reviewers_mentioned(self):
        """Test parsing multiple @mentions in a single message."""
        from panel_chat import parse_mentions

        message = "@theological @pastoral what are your thoughts?"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert 'theological' in result
        assert 'pastoral' in result
        assert len(result) == 2

    def test_should_parse_multiple_mentions_when_scattered_throughout_message(self):
        """Test parsing @mentions scattered throughout the message."""
        from panel_chat import parse_mentions

        message = "Hey @illustration, I think @language has a point about clarity"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert 'illustration' in result
        assert 'language' in result
        assert len(result) == 2

    def test_should_parse_all_seven_default_reviewers_when_all_mentioned(self):
        """Test parsing all 7 default reviewers in a single message."""
        from panel_chat import parse_mentions

        message = "@theological @pastoral @structural @engagement @illustration @scripture @language thoughts?"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        for reviewer in DEFAULT_REVIEWERS:
            assert reviewer in result
        assert len(result) == 7

    def test_should_return_unique_mentions_when_same_reviewer_mentioned_twice(self):
        """Test that duplicate mentions return only unique names."""
        from panel_chat import parse_mentions

        message = "@theological you make a great point @theological"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert 'theological' in result
        assert len(result) == 1  # Should not have duplicates


class TestCaseInsensitiveParsing:
    """Test suite for case-insensitive mention parsing."""

    def test_should_be_case_insensitive_when_lowercase_mention(self):
        """Test that lowercase @mentions are recognized."""
        from panel_chat import parse_mentions

        message = "@theological please review"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert 'theological' in result

    def test_should_be_case_insensitive_when_uppercase_mention(self):
        """Test that uppercase @mentions are recognized."""
        from panel_chat import parse_mentions

        message = "@THEOLOGICAL please review"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert 'theological' in result

    def test_should_be_case_insensitive_when_mixed_case_mention(self):
        """Test that mixed case @mentions are recognized."""
        from panel_chat import parse_mentions

        message = "@ThEoLoGiCaL please review"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert 'theological' in result

    def test_should_normalize_to_lowercase_when_returning_mentions(self):
        """Test that returned mentions are normalized to lowercase."""
        from panel_chat import parse_mentions

        message = "@PASTORAL @Structural @ENGAGEMENT"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        # All returned names should be lowercase
        for name in result:
            assert name == name.lower()


class TestInvalidMentionHandling:
    """Test suite for handling invalid @mentions."""

    def test_should_ignore_invalid_mentions_when_name_not_in_list(self):
        """Test that @mentions with invalid names are ignored."""
        from panel_chat import parse_mentions

        message = "@unknown @notareviewer please review"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert len(result) == 0

    def test_should_ignore_at_symbol_when_not_followed_by_word(self):
        """Test that lone @ symbols are ignored."""
        from panel_chat import parse_mentions

        message = "Send email to user@example.com and @ for more info"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert len(result) == 0

    def test_should_ignore_at_symbol_when_followed_by_number(self):
        """Test that @ followed by numbers is ignored."""
        from panel_chat import parse_mentions

        message = "See reference @123 for details"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert len(result) == 0

    def test_should_parse_valid_mentions_when_mixed_with_invalid(self):
        """Test that valid mentions are found among invalid ones."""
        from panel_chat import parse_mentions

        message = "@theological and @invalid should both be checked"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert 'theological' in result
        assert len(result) == 1

    def test_should_ignore_email_addresses_when_parsing_mentions(self):
        """Test that email addresses are not parsed as mentions."""
        from panel_chat import parse_mentions

        message = "Contact pastoral@church.org about this @pastoral"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        # Should only find @pastoral, not the email
        assert 'pastoral' in result
        assert len(result) == 1


class TestEmptyAndEdgeCases:
    """Test suite for empty messages and edge cases."""

    def test_should_return_empty_list_when_no_mentions_in_message(self):
        """Test that messages without @mentions return empty list."""
        from panel_chat import parse_mentions

        message = "This is a message without any mentions"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert result == []

    def test_should_return_empty_list_when_empty_message(self):
        """Test that empty message returns empty list."""
        from panel_chat import parse_mentions

        message = ""
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert result == []

    def test_should_return_empty_list_when_only_whitespace(self):
        """Test that whitespace-only message returns empty list."""
        from panel_chat import parse_mentions

        message = "   \n\t  "
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert result == []

    def test_should_handle_mention_with_punctuation_after(self):
        """Test that mentions followed by punctuation are parsed."""
        from panel_chat import parse_mentions

        message = "@theological, @pastoral! @structural?"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert 'theological' in result
        assert 'pastoral' in result
        assert 'structural' in result
        assert len(result) == 3

    def test_should_handle_mention_in_parentheses(self):
        """Test that mentions in parentheses are parsed."""
        from panel_chat import parse_mentions

        message = "(cc @theological) for this discussion"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert 'theological' in result
        assert len(result) == 1


class TestCustomReviewerParsing:
    """Test suite for parsing custom reviewer @mentions from database."""

    def test_should_match_custom_reviewers_from_database(self):
        """Test that custom reviewers from database are matched."""
        from panel_chat import parse_mentions_with_db

        conn = create_test_db()
        insert_custom_reviewer(conn, 'homiletics')
        insert_custom_reviewer(conn, 'exegesis')

        message = "@homiletics can you check the hermeneutics?"
        result = parse_mentions_with_db(conn, message, DEFAULT_REVIEWERS)

        assert 'homiletics' in result
        conn.close()

    def test_should_match_both_default_and_custom_reviewers(self):
        """Test that both default and custom reviewers are matched."""
        from panel_chat import parse_mentions_with_db

        conn = create_test_db()
        insert_custom_reviewer(conn, 'exegesis')

        message = "@theological and @exegesis please review the scripture handling"
        result = parse_mentions_with_db(conn, message, DEFAULT_REVIEWERS)

        assert 'theological' in result
        assert 'exegesis' in result
        assert len(result) == 2
        conn.close()

    def test_should_be_case_insensitive_for_custom_reviewers(self):
        """Test that custom reviewer matching is case-insensitive."""
        from panel_chat import parse_mentions_with_db

        conn = create_test_db()
        insert_custom_reviewer(conn, 'homiletics')

        message = "@HOMILETICS please check"
        result = parse_mentions_with_db(conn, message, DEFAULT_REVIEWERS)

        assert 'homiletics' in result
        conn.close()

    def test_should_not_match_inactive_custom_reviewers(self):
        """Test that inactive custom reviewers are not matched."""
        from panel_chat import parse_mentions_with_db

        conn = create_test_db()
        conn.execute(
            'INSERT INTO custom_reviewers (name, description, active) VALUES (?, ?, ?)',
            ('inactive_reviewer', 'Inactive', 0)
        )
        conn.commit()

        message = "@inactive_reviewer please check"
        result = parse_mentions_with_db(conn, message, DEFAULT_REVIEWERS)

        assert 'inactive_reviewer' not in result
        assert len(result) == 0
        conn.close()

    def test_should_handle_database_with_no_custom_reviewers(self):
        """Test parsing works when no custom reviewers exist."""
        from panel_chat import parse_mentions_with_db

        conn = create_test_db()

        message = "@theological please review"
        result = parse_mentions_with_db(conn, message, DEFAULT_REVIEWERS)

        assert 'theological' in result
        assert len(result) == 1
        conn.close()


class TestMentionExtractionFunction:
    """Test suite for the core mention extraction functionality."""

    def test_should_extract_all_at_patterns_from_message(self):
        """Test that all @ patterns are extracted from message."""
        from panel_chat import extract_mention_patterns

        message = "@theological @pastoral @unknown"
        patterns = extract_mention_patterns(message)

        assert len(patterns) >= 3
        assert 'theological' in [p.lower() for p in patterns]
        assert 'pastoral' in [p.lower() for p in patterns]
        assert 'unknown' in [p.lower() for p in patterns]

    def test_should_return_patterns_without_at_symbol(self):
        """Test that extracted patterns do not include @ symbol."""
        from panel_chat import extract_mention_patterns

        message = "@theological"
        patterns = extract_mention_patterns(message)

        assert '@' not in patterns[0]

    def test_should_handle_unicode_in_message(self):
        """Test that messages with unicode are handled properly."""
        from panel_chat import parse_mentions

        message = "@theological says 'Grüß Gott' means hello"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert 'theological' in result

    def test_should_handle_newlines_in_message(self):
        """Test that mentions across newlines are parsed."""
        from panel_chat import parse_mentions

        message = "@theological\nand\n@pastoral\nboth agree"
        result = parse_mentions(message, DEFAULT_REVIEWERS)

        assert 'theological' in result
        assert 'pastoral' in result
        assert len(result) == 2


class TestMentionRouting:
    """Test suite for routing messages to mentioned reviewers."""

    def test_should_identify_mentioned_reviewers_for_routing(self):
        """Test that mentioned reviewers can be identified for message routing."""
        from panel_chat import get_mentioned_reviewers

        conn = create_test_db()

        message = "@theological @pastoral your thoughts?"
        reviewers = get_mentioned_reviewers(conn, message, DEFAULT_REVIEWERS)

        assert 'theological' in reviewers
        assert 'pastoral' in reviewers
        conn.close()

    def test_should_return_empty_when_no_reviewers_to_route_to(self):
        """Test that empty list is returned when no valid mentions."""
        from panel_chat import get_mentioned_reviewers

        conn = create_test_db()

        message = "Hello everyone, no specific mentions here"
        reviewers = get_mentioned_reviewers(conn, message, DEFAULT_REVIEWERS)

        assert reviewers == []
        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
