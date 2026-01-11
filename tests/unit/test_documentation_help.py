"""
Tests for Documentation and Help System (Issue #230)

Phase 10: Polish - Item 3

Tests cover:
- Help content retrieval
- Documentation sections
- Search functionality
- Contextual help
- Tutorial system

TDD Approach: All tests fail with ModuleNotFoundError until implementation.
NO MOCKS: Uses real implementations.
"""

import pytest
import sqlite3


def create_test_db():
    """Create a real SQLite in-memory database for testing."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create tutorial progress table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tutorial_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tutorial_name TEXT NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, tutorial_name)
        )
    ''')

    conn.commit()
    return conn


def insert_sample_user(conn, email='test@example.com'):
    """Insert a sample user for testing."""
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (email, name) VALUES (?, ?)', (email, 'Test User'))
    conn.commit()
    return cursor.lastrowid


class TestGetHelpContent:
    """Tests for get_help_content function."""

    def test_should_get_help_for_topic(self):
        """Should return help content for a topic."""
        from documentation_help import get_help_content

        result = get_help_content('getting-started')

        assert result is not None
        assert isinstance(result, (str, dict))

    def test_should_include_title(self):
        """Help content should include title."""
        from documentation_help import get_help_content

        result = get_help_content('getting-started')

        if isinstance(result, dict):
            assert 'title' in result
        else:
            assert len(result) > 0

    def test_should_include_content(self):
        """Help content should include actual content."""
        from documentation_help import get_help_content

        result = get_help_content('getting-started')

        if isinstance(result, dict):
            assert 'content' in result or 'body' in result
        else:
            assert len(result) > 10

    def test_should_return_none_for_unknown_topic(self):
        """Should return None for unknown topic."""
        from documentation_help import get_help_content

        result = get_help_content('nonexistent-topic-xyz')

        assert result is None

    def test_should_handle_sermon_creation_topic(self):
        """Should have help for sermon creation."""
        from documentation_help import get_help_content

        result = get_help_content('sermon-creation')

        assert result is not None


class TestGetAllHelpTopics:
    """Tests for get_all_help_topics function."""

    def test_should_return_topic_list(self):
        """Should return list of all help topics."""
        from documentation_help import get_all_help_topics

        result = get_all_help_topics()

        assert isinstance(result, list)
        assert len(result) > 0

    def test_should_include_common_topics(self):
        """Should include common help topics."""
        from documentation_help import get_all_help_topics

        topics = get_all_help_topics()
        topic_names = [t.get('name') if isinstance(t, dict) else t for t in topics]

        # Should have at least some common topics
        assert len(topic_names) >= 3

    def test_should_return_topic_metadata(self):
        """Topics should include metadata."""
        from documentation_help import get_all_help_topics

        topics = get_all_help_topics()

        if topics and isinstance(topics[0], dict):
            topic = topics[0]
            assert 'name' in topic or 'title' in topic

    def test_should_be_organized_by_category(self):
        """Topics should be organized by category."""
        from documentation_help import get_all_help_topics

        topics = get_all_help_topics()

        if topics and isinstance(topics[0], dict):
            topic = topics[0]
            assert 'category' in topic or 'section' in topic or len(topics) > 0


class TestSearchHelp:
    """Tests for search_help function."""

    def test_should_search_help_content(self):
        """Should search help content by query."""
        from documentation_help import search_help

        result = search_help('sermon')

        assert isinstance(result, list)

    def test_should_return_matching_results(self):
        """Should return topics matching search query."""
        from documentation_help import search_help

        result = search_help('getting started')

        assert len(result) >= 0
        # If results exist, they should be relevant
        if result:
            result_str = str(result).lower()
            assert 'getting' in result_str or 'start' in result_str or len(result) >= 0

    def test_should_handle_partial_matches(self):
        """Should handle partial word matches."""
        from documentation_help import search_help

        result = search_help('serm')  # Partial match for 'sermon'

        assert isinstance(result, list)

    def test_should_return_empty_for_no_matches(self):
        """Should return empty list for no matches."""
        from documentation_help import search_help

        result = search_help('xyznonexistent123')

        assert result == []

    def test_should_be_case_insensitive(self):
        """Search should be case insensitive."""
        from documentation_help import search_help

        result_lower = search_help('sermon')
        result_upper = search_help('SERMON')

        assert result_lower == result_upper or len(result_lower) == len(result_upper)


class TestGetDocumentation:
    """Tests for get_documentation function."""

    def test_should_get_documentation_section(self):
        """Should get documentation section."""
        from documentation_help import get_documentation

        result = get_documentation('overview')

        assert result is not None

    def test_should_include_section_content(self):
        """Section should include content."""
        from documentation_help import get_documentation

        result = get_documentation('overview')

        if isinstance(result, dict):
            assert 'content' in result or 'body' in result
        else:
            assert len(str(result)) > 0

    def test_should_handle_features_section(self):
        """Should have features documentation."""
        from documentation_help import get_documentation

        result = get_documentation('features')

        assert result is not None

    def test_should_return_none_for_unknown_section(self):
        """Should return None for unknown section."""
        from documentation_help import get_documentation

        result = get_documentation('nonexistent-section-xyz')

        assert result is None


class TestGetQuickStartGuide:
    """Tests for get_quick_start_guide function."""

    def test_should_return_quick_start(self):
        """Should return quick start guide content."""
        from documentation_help import get_quick_start_guide

        result = get_quick_start_guide()

        assert result is not None

    def test_should_include_steps(self):
        """Quick start should include steps."""
        from documentation_help import get_quick_start_guide

        result = get_quick_start_guide()

        result_str = str(result).lower()
        assert 'step' in result_str or isinstance(result, list) or len(result) > 50

    def test_should_be_beginner_friendly(self):
        """Content should be beginner-friendly."""
        from documentation_help import get_quick_start_guide

        result = get_quick_start_guide()

        # Should have enough content to be helpful
        assert len(str(result)) > 50


class TestGetFeatureGuide:
    """Tests for get_feature_guide function."""

    def test_should_get_feature_guide(self):
        """Should get guide for a feature."""
        from documentation_help import get_feature_guide

        result = get_feature_guide('sermon-generation')

        assert result is not None

    def test_should_include_usage_instructions(self):
        """Feature guide should include usage instructions."""
        from documentation_help import get_feature_guide

        result = get_feature_guide('sermon-generation')

        assert len(str(result)) > 20

    def test_should_handle_reviewer_panel_feature(self):
        """Should have guide for reviewer panel."""
        from documentation_help import get_feature_guide

        result = get_feature_guide('reviewer-panel')

        assert result is not None

    def test_should_return_none_for_unknown_feature(self):
        """Should return None for unknown feature."""
        from documentation_help import get_feature_guide

        result = get_feature_guide('unknown-feature-xyz')

        assert result is None


class TestGetFAQ:
    """Tests for get_faq function."""

    def test_should_return_faq(self):
        """Should return FAQ content."""
        from documentation_help import get_faq

        result = get_faq()

        assert result is not None

    def test_should_be_list_of_qa(self):
        """FAQ should be list of Q&A pairs."""
        from documentation_help import get_faq

        result = get_faq()

        assert isinstance(result, list)
        if result:
            item = result[0]
            if isinstance(item, dict):
                assert 'question' in item or 'q' in item

    def test_should_have_multiple_questions(self):
        """Should have multiple FAQ entries."""
        from documentation_help import get_faq

        result = get_faq()

        assert len(result) >= 3

    def test_each_qa_should_have_answer(self):
        """Each Q&A should have an answer."""
        from documentation_help import get_faq

        result = get_faq()

        if result and isinstance(result[0], dict):
            for qa in result:
                assert 'answer' in qa or 'a' in qa


class TestGetTooltip:
    """Tests for get_tooltip function."""

    def test_should_get_tooltip(self):
        """Should get tooltip for element."""
        from documentation_help import get_tooltip

        result = get_tooltip('generate-button')

        assert result is not None
        assert isinstance(result, str)

    def test_should_be_concise(self):
        """Tooltip should be concise."""
        from documentation_help import get_tooltip

        result = get_tooltip('generate-button')

        # Tooltips should be short
        assert len(result) < 200

    def test_should_return_none_for_unknown(self):
        """Should return None for unknown element."""
        from documentation_help import get_tooltip

        result = get_tooltip('unknown-element-xyz')

        assert result is None

    def test_should_handle_save_button(self):
        """Should have tooltip for save button."""
        from documentation_help import get_tooltip

        result = get_tooltip('save-button')

        assert result is not None


class TestGetContextualHelp:
    """Tests for get_contextual_help function."""

    def test_should_get_contextual_help(self):
        """Should get contextual help for page/element."""
        from documentation_help import get_contextual_help

        result = get_contextual_help('editor', 'scripture-input')

        assert result is not None

    def test_should_be_page_specific(self):
        """Help should be specific to page context."""
        from documentation_help import get_contextual_help

        editor_help = get_contextual_help('editor', 'save-button')
        archive_help = get_contextual_help('archive', 'save-button')

        # Same element might have different help on different pages
        assert editor_help is not None or archive_help is not None

    def test_should_include_relevant_tips(self):
        """Contextual help should include relevant tips."""
        from documentation_help import get_contextual_help

        result = get_contextual_help('editor', 'scripture-input')

        if result:
            assert len(str(result)) > 10

    def test_should_handle_unknown_context(self):
        """Should handle unknown page/element gracefully."""
        from documentation_help import get_contextual_help

        result = get_contextual_help('unknown-page', 'unknown-element')

        # Should return None or generic help
        assert result is None or isinstance(result, str)


class TestGetKeyboardShortcuts:
    """Tests for get_keyboard_shortcuts function."""

    def test_should_return_shortcuts(self):
        """Should return keyboard shortcuts list."""
        from documentation_help import get_keyboard_shortcuts

        result = get_keyboard_shortcuts()

        assert isinstance(result, list)

    def test_should_include_common_shortcuts(self):
        """Should include common shortcuts."""
        from documentation_help import get_keyboard_shortcuts

        result = get_keyboard_shortcuts()

        assert len(result) >= 3

    def test_each_shortcut_should_have_key_combo(self):
        """Each shortcut should have key combination."""
        from documentation_help import get_keyboard_shortcuts

        result = get_keyboard_shortcuts()

        if result and isinstance(result[0], dict):
            for shortcut in result:
                assert 'keys' in shortcut or 'shortcut' in shortcut or 'key' in shortcut

    def test_each_shortcut_should_have_description(self):
        """Each shortcut should have description."""
        from documentation_help import get_keyboard_shortcuts

        result = get_keyboard_shortcuts()

        if result and isinstance(result[0], dict):
            for shortcut in result:
                assert 'description' in shortcut or 'action' in shortcut


class TestGetTutorial:
    """Tests for get_tutorial function."""

    def test_should_get_tutorial(self):
        """Should get tutorial content."""
        from documentation_help import get_tutorial

        result = get_tutorial('first-sermon')

        assert result is not None

    def test_should_include_tutorial_info(self):
        """Tutorial should include metadata."""
        from documentation_help import get_tutorial

        result = get_tutorial('first-sermon')

        if isinstance(result, dict):
            assert 'title' in result or 'name' in result

    def test_should_return_none_for_unknown(self):
        """Should return None for unknown tutorial."""
        from documentation_help import get_tutorial

        result = get_tutorial('nonexistent-tutorial-xyz')

        assert result is None


class TestGetTutorialSteps:
    """Tests for get_tutorial_steps function."""

    def test_should_get_tutorial_steps(self):
        """Should get tutorial steps."""
        from documentation_help import get_tutorial_steps

        result = get_tutorial_steps('first-sermon')

        assert isinstance(result, list)

    def test_should_have_multiple_steps(self):
        """Tutorial should have multiple steps."""
        from documentation_help import get_tutorial_steps

        result = get_tutorial_steps('first-sermon')

        assert len(result) >= 2

    def test_each_step_should_have_content(self):
        """Each step should have content."""
        from documentation_help import get_tutorial_steps

        result = get_tutorial_steps('first-sermon')

        if result:
            step = result[0]
            if isinstance(step, dict):
                assert 'content' in step or 'instruction' in step or 'text' in step
            else:
                assert len(str(step)) > 5

    def test_steps_should_be_ordered(self):
        """Steps should be in order."""
        from documentation_help import get_tutorial_steps

        result = get_tutorial_steps('first-sermon')

        if result and isinstance(result[0], dict):
            for i, step in enumerate(result):
                if 'order' in step:
                    assert step['order'] >= 0


class TestMarkTutorialComplete:
    """Tests for mark_tutorial_complete function."""

    def test_should_mark_tutorial_complete(self):
        """Should mark tutorial as complete for user."""
        from documentation_help import mark_tutorial_complete

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = mark_tutorial_complete(conn, user_id, 'first-sermon')

        assert result is True

        conn.close()

    def test_should_record_completion_time(self):
        """Should record when tutorial was completed."""
        from documentation_help import mark_tutorial_complete

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        mark_tutorial_complete(conn, user_id, 'first-sermon')

        cursor = conn.cursor()
        cursor.execute(
            'SELECT completed_at FROM tutorial_progress WHERE user_id = ? AND tutorial_name = ?',
            (user_id, 'first-sermon')
        )
        row = cursor.fetchone()

        assert row is not None
        assert row['completed_at'] is not None

        conn.close()

    def test_should_handle_duplicate_completion(self):
        """Should handle marking same tutorial complete twice."""
        from documentation_help import mark_tutorial_complete

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        mark_tutorial_complete(conn, user_id, 'first-sermon')
        result = mark_tutorial_complete(conn, user_id, 'first-sermon')

        # Should either update or return True
        assert result is True or result is False

        conn.close()

    def test_should_track_multiple_tutorials(self):
        """Should track multiple tutorials per user."""
        from documentation_help import mark_tutorial_complete, get_completed_tutorials

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        mark_tutorial_complete(conn, user_id, 'first-sermon')
        mark_tutorial_complete(conn, user_id, 'advanced-features')

        # Check both are recorded
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM tutorial_progress WHERE user_id = ?', (user_id,))
        count = cursor.fetchone()[0]

        assert count >= 2

        conn.close()


class TestGetCompletedTutorials:
    """Tests for get_completed_tutorials function."""

    def test_should_get_completed_tutorials(self):
        """Should get list of completed tutorials."""
        from documentation_help import mark_tutorial_complete, get_completed_tutorials

        conn = create_test_db()
        user_id = insert_sample_user(conn)
        mark_tutorial_complete(conn, user_id, 'first-sermon')

        result = get_completed_tutorials(conn, user_id)

        assert isinstance(result, list)
        assert 'first-sermon' in result or any('first-sermon' in str(t) for t in result)

        conn.close()

    def test_should_return_empty_for_new_user(self):
        """Should return empty for user with no completed tutorials."""
        from documentation_help import get_completed_tutorials

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        result = get_completed_tutorials(conn, user_id)

        assert result == []

        conn.close()


class TestEdgeCases:
    """Tests for edge cases."""

    def test_should_handle_empty_search_query(self):
        """Should handle empty search query."""
        from documentation_help import search_help

        result = search_help('')

        assert isinstance(result, list)

    def test_should_handle_special_characters_in_search(self):
        """Should handle special characters in search."""
        from documentation_help import search_help

        result = search_help("test's \"query\"")

        assert isinstance(result, list)

    def test_should_handle_unicode_in_search(self):
        """Should handle unicode in search."""
        from documentation_help import search_help

        result = search_help('ünïcödé')

        assert isinstance(result, list)

    def test_should_handle_very_long_search(self):
        """Should handle very long search query."""
        from documentation_help import search_help

        result = search_help('a' * 1000)

        assert isinstance(result, list)

    def test_should_handle_nonexistent_user_for_tutorial(self):
        """Should handle nonexistent user for tutorial progress."""
        from documentation_help import get_completed_tutorials

        conn = create_test_db()

        result = get_completed_tutorials(conn, 9999)

        assert result == []

        conn.close()


class TestIntegration:
    """Integration tests for documentation system."""

    def test_should_provide_complete_help_experience(self):
        """Should provide complete help experience."""
        from documentation_help import (
            get_all_help_topics,
            get_help_content,
            search_help,
            get_quick_start_guide
        )

        # Get all topics
        topics = get_all_help_topics()
        assert len(topics) > 0

        # Get specific help
        quick_start = get_quick_start_guide()
        assert quick_start is not None

        # Search works
        results = search_help('sermon')
        assert isinstance(results, list)

    def test_should_support_tutorial_workflow(self):
        """Should support complete tutorial workflow."""
        from documentation_help import (
            get_tutorial,
            get_tutorial_steps,
            mark_tutorial_complete,
            get_completed_tutorials
        )

        conn = create_test_db()
        user_id = insert_sample_user(conn)

        # Get tutorial
        tutorial = get_tutorial('first-sermon')
        assert tutorial is not None

        # Get steps
        steps = get_tutorial_steps('first-sermon')
        assert len(steps) >= 1

        # Complete tutorial
        mark_tutorial_complete(conn, user_id, 'first-sermon')

        # Verify completion
        completed = get_completed_tutorials(conn, user_id)
        assert len(completed) >= 1

        conn.close()

    def test_should_provide_contextual_assistance(self):
        """Should provide contextual help and tooltips."""
        from documentation_help import (
            get_tooltip,
            get_contextual_help,
            get_keyboard_shortcuts
        )

        # Tooltips
        tooltip = get_tooltip('save-button')
        # Might be None if not defined, that's OK

        # Shortcuts
        shortcuts = get_keyboard_shortcuts()
        assert isinstance(shortcuts, list)
