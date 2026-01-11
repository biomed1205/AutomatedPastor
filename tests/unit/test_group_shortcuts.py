"""Tests for group mention shortcuts in panel chat.

These tests verify the group mention shortcut functionality for The Green Room.
Group shortcuts allow users to mention multiple reviewers with a single @group.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL implementations - NO MOCKS.
"""
import pytest
import sqlite3


# Group definitions (from issue specification)
GROUP_DEFINITIONS = {
    'women': ['barbara_brown_taylor', 'fleming_rutledge', 'nadia_bolz_weber'],
    'umc': ['adam_hamilton', 'will_willimon', 'jorge_acevedo', 'matt_miofsky'],
    'all': [
        'theological', 'pastoral', 'structural', 'engagement',
        'illustration', 'scripture', 'language'
    ],
    'theological': ['will_willimon', 'fleming_rutledge'],
    'practical': ['adam_hamilton', 'matt_miofsky', 'jorge_acevedo']
}


# Default reviewer types (7 reviewers) - same as in test_mention_parsing.py
DEFAULT_REVIEWERS = [
    'theological',
    'pastoral',
    'structural',
    'engagement',
    'illustration',
    'scripture',
    'language'
]


def create_test_db():
    """Create an in-memory test database with group shortcuts table."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('''
        CREATE TABLE group_shortcuts (
            id INTEGER PRIMARY KEY,
            group_name TEXT NOT NULL UNIQUE,
            members TEXT NOT NULL,
            description TEXT,
            active INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    return conn


def insert_group(conn, group_name, members, description='Test group'):
    """Insert a group shortcut into the database."""
    import json
    conn.execute(
        'INSERT INTO group_shortcuts (group_name, members, description) VALUES (?, ?, ?)',
        (group_name, json.dumps(members), description)
    )
    conn.commit()


class TestExpandGroupMention:
    """Test suite for expanding single group mentions."""

    def test_should_expand_women_group_to_three_reviewers(self):
        """Test that @women expands to three female preacher reviewers."""
        from panel_chat import expand_group_mention

        result = expand_group_mention('women', GROUP_DEFINITIONS)

        assert len(result) == 3
        assert 'barbara_brown_taylor' in result
        assert 'fleming_rutledge' in result
        assert 'nadia_bolz_weber' in result

    def test_should_expand_umc_group_to_four_reviewers(self):
        """Test that @UMC expands to four Methodist reviewers."""
        from panel_chat import expand_group_mention

        result = expand_group_mention('umc', GROUP_DEFINITIONS)

        assert len(result) == 4
        assert 'adam_hamilton' in result
        assert 'will_willimon' in result
        assert 'jorge_acevedo' in result
        assert 'matt_miofsky' in result

    def test_should_expand_all_group_to_seven_reviewers(self):
        """Test that @all expands to all seven default reviewers."""
        from panel_chat import expand_group_mention

        result = expand_group_mention('all', GROUP_DEFINITIONS)

        assert len(result) == 7
        for reviewer in DEFAULT_REVIEWERS:
            assert reviewer in result

    def test_should_expand_theological_group_to_two_reviewers(self):
        """Test that @theological expands to theological focus reviewers."""
        from panel_chat import expand_group_mention

        result = expand_group_mention('theological', GROUP_DEFINITIONS)

        assert len(result) == 2
        assert 'will_willimon' in result
        assert 'fleming_rutledge' in result

    def test_should_expand_practical_group_to_three_reviewers(self):
        """Test that @practical expands to practical application reviewers."""
        from panel_chat import expand_group_mention

        result = expand_group_mention('practical', GROUP_DEFINITIONS)

        assert len(result) == 3
        assert 'adam_hamilton' in result
        assert 'matt_miofsky' in result
        assert 'jorge_acevedo' in result


class TestCaseInsensitiveGroupMatching:
    """Test suite for case-insensitive group matching."""

    def test_should_match_lowercase_group_name(self):
        """Test that lowercase group names are matched."""
        from panel_chat import expand_group_mention

        result = expand_group_mention('women', GROUP_DEFINITIONS)

        assert len(result) == 3

    def test_should_match_uppercase_group_name(self):
        """Test that uppercase group names are matched."""
        from panel_chat import expand_group_mention

        result = expand_group_mention('WOMEN', GROUP_DEFINITIONS)

        assert len(result) == 3

    def test_should_match_mixed_case_group_name(self):
        """Test that mixed case group names are matched."""
        from panel_chat import expand_group_mention

        result = expand_group_mention('WoMeN', GROUP_DEFINITIONS)

        assert len(result) == 3

    def test_should_match_umc_in_any_case(self):
        """Test that UMC group matches in any case."""
        from panel_chat import expand_group_mention

        lowercase = expand_group_mention('umc', GROUP_DEFINITIONS)
        uppercase = expand_group_mention('UMC', GROUP_DEFINITIONS)
        mixed = expand_group_mention('Umc', GROUP_DEFINITIONS)

        assert lowercase == uppercase == mixed


class TestUnknownGroupHandling:
    """Test suite for handling unknown group names."""

    def test_should_return_empty_list_for_unknown_group(self):
        """Test that unknown groups return empty list."""
        from panel_chat import expand_group_mention

        result = expand_group_mention('unknown_group', GROUP_DEFINITIONS)

        assert result == []

    def test_should_return_empty_list_for_empty_group_name(self):
        """Test that empty group name returns empty list."""
        from panel_chat import expand_group_mention

        result = expand_group_mention('', GROUP_DEFINITIONS)

        assert result == []

    def test_should_return_empty_list_for_none_group_name(self):
        """Test that None group name is handled safely."""
        from panel_chat import expand_group_mention

        result = expand_group_mention(None, GROUP_DEFINITIONS)

        assert result == []

    def test_should_return_empty_list_for_partial_match(self):
        """Test that partial group names don't match (e.g., 'wom' doesn't match 'women')."""
        from panel_chat import expand_group_mention

        result = expand_group_mention('wom', GROUP_DEFINITIONS)

        assert result == []


class TestMultipleGroupsInMessage:
    """Test suite for expanding multiple groups in a single message."""

    def test_should_expand_multiple_groups_in_message(self):
        """Test that multiple groups in a message are all expanded."""
        from panel_chat import expand_groups_in_message

        message = "@women and @practical please review"
        result = expand_groups_in_message(message, GROUP_DEFINITIONS)

        # Should include all from women (3) and practical (3)
        assert 'barbara_brown_taylor' in result
        assert 'fleming_rutledge' in result
        assert 'nadia_bolz_weber' in result
        assert 'adam_hamilton' in result
        assert 'matt_miofsky' in result
        assert 'jorge_acevedo' in result

    def test_should_handle_adjacent_groups(self):
        """Test that adjacent groups are both expanded."""
        from panel_chat import expand_groups_in_message

        message = "@women @umc thoughts?"
        result = expand_groups_in_message(message, GROUP_DEFINITIONS)

        # Should include all from both groups (3 + 4 = 7, but may have overlaps)
        assert len(result) >= 6  # At least 6 unique reviewers

    def test_should_handle_three_groups_in_message(self):
        """Test that three groups are all expanded."""
        from panel_chat import expand_groups_in_message

        message = "@women @theological @practical review please"
        result = expand_groups_in_message(message, GROUP_DEFINITIONS)

        # Women: 3, theological: 2, practical: 3 (with overlaps)
        # Should have at least 5 unique reviewers
        assert len(result) >= 5


class TestCombineGroupAndIndividualMentions:
    """Test suite for combining groups with individual mentions."""

    def test_should_combine_group_and_individual_mention(self):
        """Test that groups and individual mentions are combined."""
        from panel_chat import parse_all_mentions

        message = "@women @adam_hamilton what do you think?"
        result = parse_all_mentions(message, GROUP_DEFINITIONS, DEFAULT_REVIEWERS)

        # Should include women group (3) plus adam_hamilton
        assert 'barbara_brown_taylor' in result
        assert 'fleming_rutledge' in result
        assert 'nadia_bolz_weber' in result
        assert 'adam_hamilton' in result

    def test_should_combine_individual_then_group(self):
        """Test that individual mention before group works."""
        from panel_chat import parse_all_mentions

        message = "@pastoral then @theological group"
        result = parse_all_mentions(message, GROUP_DEFINITIONS, DEFAULT_REVIEWERS)

        assert 'pastoral' in result
        assert 'will_willimon' in result
        assert 'fleming_rutledge' in result

    def test_should_expand_groups_before_individual_parsing(self):
        """Test that groups are expanded before individual mention parsing."""
        from panel_chat import parse_all_mentions

        # Groups should be processed first, then individual mentions
        message = "@umc @structural please review"
        result = parse_all_mentions(message, GROUP_DEFINITIONS, DEFAULT_REVIEWERS)

        # UMC group (4) + structural individual
        assert 'adam_hamilton' in result
        assert 'will_willimon' in result
        assert 'jorge_acevedo' in result
        assert 'matt_miofsky' in result
        assert 'structural' in result


class TestNoDuplicateReviewers:
    """Test suite for ensuring no duplicate reviewers in results."""

    def test_should_not_duplicate_when_reviewer_in_multiple_groups(self):
        """Test that a reviewer appearing in multiple groups is only listed once."""
        from panel_chat import parse_all_mentions

        # fleming_rutledge is in both 'women' and 'theological'
        message = "@women @theological"
        result = parse_all_mentions(message, GROUP_DEFINITIONS, DEFAULT_REVIEWERS)

        # Count occurrences of fleming_rutledge
        fleming_count = result.count('fleming_rutledge')
        assert fleming_count == 1

    def test_should_not_duplicate_when_same_group_mentioned_twice(self):
        """Test that mentioning same group twice doesn't duplicate."""
        from panel_chat import parse_all_mentions

        message = "@women check this @women"
        result = parse_all_mentions(message, GROUP_DEFINITIONS, DEFAULT_REVIEWERS)

        # Should still only have 3 unique reviewers from women group
        assert len(result) == 3

    def test_should_not_duplicate_when_individual_matches_group_member(self):
        """Test that individual mention matching group member doesn't duplicate."""
        from panel_chat import parse_all_mentions

        # adam_hamilton is in @umc group
        message = "@umc @adam_hamilton"
        result = parse_all_mentions(message, GROUP_DEFINITIONS, DEFAULT_REVIEWERS)

        # adam_hamilton should only appear once
        adam_count = result.count('adam_hamilton')
        assert adam_count == 1

    def test_should_return_unique_list(self):
        """Test that result is always a unique list."""
        from panel_chat import parse_all_mentions

        message = "@all @theological @pastoral"
        result = parse_all_mentions(message, GROUP_DEFINITIONS, DEFAULT_REVIEWERS)

        # Check that all items are unique
        assert len(result) == len(set(result))


class TestDatabaseGroupShortcuts:
    """Test suite for custom group shortcuts from database."""

    def test_should_load_custom_groups_from_database(self):
        """Test that custom groups from database are loaded."""
        from panel_chat import expand_group_with_db

        conn = create_test_db()
        insert_group(conn, 'elders', ['john_wesley', 'charles_wesley', 'george_whitefield'])

        result = expand_group_with_db(conn, 'elders', GROUP_DEFINITIONS)

        assert 'john_wesley' in result
        assert 'charles_wesley' in result
        assert 'george_whitefield' in result
        conn.close()

    def test_should_prefer_database_over_default_definitions(self):
        """Test that database groups take precedence over defaults."""
        from panel_chat import expand_group_with_db

        conn = create_test_db()
        # Override 'women' group with custom definition
        insert_group(conn, 'women', ['custom_reviewer_1', 'custom_reviewer_2'])

        result = expand_group_with_db(conn, 'women', GROUP_DEFINITIONS)

        # Should use database definition, not default
        assert 'custom_reviewer_1' in result
        assert 'custom_reviewer_2' in result
        assert 'barbara_brown_taylor' not in result
        conn.close()

    def test_should_fall_back_to_default_when_not_in_database(self):
        """Test that default groups are used when not in database."""
        from panel_chat import expand_group_with_db

        conn = create_test_db()
        # Don't insert 'women' group - should fall back to default

        result = expand_group_with_db(conn, 'women', GROUP_DEFINITIONS)

        assert 'barbara_brown_taylor' in result
        assert len(result) == 3
        conn.close()

    def test_should_not_load_inactive_groups_from_database(self):
        """Test that inactive groups are not used."""
        from panel_chat import expand_group_with_db
        import json

        conn = create_test_db()
        conn.execute(
            'INSERT INTO group_shortcuts (group_name, members, active) VALUES (?, ?, ?)',
            ('inactive_group', json.dumps(['reviewer1', 'reviewer2']), 0)
        )
        conn.commit()

        result = expand_group_with_db(conn, 'inactive_group', GROUP_DEFINITIONS)

        # Should return empty since group is inactive and not in defaults
        assert result == []
        conn.close()

    def test_should_handle_database_with_no_custom_groups(self):
        """Test that system works when database has no custom groups."""
        from panel_chat import expand_group_with_db

        conn = create_test_db()

        result = expand_group_with_db(conn, 'umc', GROUP_DEFINITIONS)

        # Should fall back to default definition
        assert len(result) == 4
        assert 'adam_hamilton' in result
        conn.close()


class TestEdgeCases:
    """Test suite for edge cases in group expansion."""

    def test_should_handle_message_with_only_groups(self):
        """Test message containing only group mentions."""
        from panel_chat import expand_groups_in_message

        message = "@women @umc"
        result = expand_groups_in_message(message, GROUP_DEFINITIONS)

        assert len(result) >= 6

    def test_should_handle_empty_message(self):
        """Test empty message returns empty list."""
        from panel_chat import expand_groups_in_message

        message = ""
        result = expand_groups_in_message(message, GROUP_DEFINITIONS)

        assert result == []

    def test_should_handle_message_with_no_groups(self):
        """Test message with no group mentions."""
        from panel_chat import expand_groups_in_message

        message = "Hello everyone, no groups here"
        result = expand_groups_in_message(message, GROUP_DEFINITIONS)

        assert result == []

    def test_should_handle_at_symbol_without_group(self):
        """Test that lone @ symbols don't match groups."""
        from panel_chat import expand_groups_in_message

        message = "Email me @ this address"
        result = expand_groups_in_message(message, GROUP_DEFINITIONS)

        assert result == []

    def test_should_handle_group_with_punctuation_after(self):
        """Test that groups followed by punctuation are matched."""
        from panel_chat import expand_groups_in_message

        message = "@women, @umc! @practical?"
        result = expand_groups_in_message(message, GROUP_DEFINITIONS)

        assert 'barbara_brown_taylor' in result  # from women
        assert 'adam_hamilton' in result  # from umc and practical

    def test_should_handle_group_in_parentheses(self):
        """Test that groups in parentheses are matched."""
        from panel_chat import expand_groups_in_message

        message = "(cc @theological)"
        result = expand_groups_in_message(message, GROUP_DEFINITIONS)

        assert 'will_willimon' in result
        assert 'fleming_rutledge' in result

    def test_should_handle_unicode_in_message(self):
        """Test that messages with unicode are handled properly."""
        from panel_chat import expand_groups_in_message

        message = "@women says 'Grüß Gott' means hello"
        result = expand_groups_in_message(message, GROUP_DEFINITIONS)

        assert len(result) == 3

    def test_should_handle_newlines_between_groups(self):
        """Test that groups across newlines are all expanded."""
        from panel_chat import expand_groups_in_message

        message = "@women\nand\n@umc\nplease review"
        result = expand_groups_in_message(message, GROUP_DEFINITIONS)

        assert 'barbara_brown_taylor' in result
        assert 'adam_hamilton' in result


class TestGetGroupDefinitions:
    """Test suite for retrieving group definitions."""

    def test_should_get_all_group_names(self):
        """Test that all group names can be retrieved."""
        from panel_chat import get_available_groups

        result = get_available_groups(GROUP_DEFINITIONS)

        assert 'women' in result
        assert 'umc' in result
        assert 'all' in result
        assert 'theological' in result
        assert 'practical' in result

    def test_should_get_group_members(self):
        """Test that group members can be retrieved."""
        from panel_chat import get_group_members

        result = get_group_members('women', GROUP_DEFINITIONS)

        assert len(result) == 3
        assert 'barbara_brown_taylor' in result

    def test_should_return_empty_for_unknown_group_members(self):
        """Test that unknown group returns empty member list."""
        from panel_chat import get_group_members

        result = get_group_members('nonexistent', GROUP_DEFINITIONS)

        assert result == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
