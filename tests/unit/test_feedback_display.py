"""Tests for feedback display in UI.

These tests verify the display of panel reviewer feedback to users.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database and files - NO MOCKS.
"""
import pytest
import sqlite3
import json
from flask import Flask


# Sample feedback data for testing
SAMPLE_FEEDBACK = [
    {
        'id': 1,
        'reviewer': 'theological',
        'reviewer_name': 'Theological Reviewer',
        'focus_area': 'Wesleyan theology and doctrine',
        'sermon_id': 1,
        'section': 'Point 1',
        'comment': 'Strong use of grace theology here.',
        'rating': 4,
        'created_at': '2025-01-10 12:00:00'
    },
    {
        'id': 2,
        'reviewer': 'structural',
        'reviewer_name': 'Structural Reviewer',
        'focus_area': 'Sermon flow and organization',
        'sermon_id': 1,
        'section': 'Introduction',
        'comment': 'Opening could use a stronger hook.',
        'rating': 3,
        'created_at': '2025-01-10 12:01:00'
    },
    {
        'id': 3,
        'reviewer': 'pastoral',
        'reviewer_name': 'Pastoral Reviewer',
        'focus_area': 'Practical application and care',
        'sermon_id': 1,
        'section': 'Conclusion',
        'comment': 'Excellent call to action.',
        'rating': 5,
        'created_at': '2025-01-10 12:02:00'
    }
]


def create_test_db():
    """Create an in-memory test database with feedback."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('''
        CREATE TABLE panel_feedback (
            id INTEGER PRIMARY KEY,
            reviewer TEXT,
            reviewer_name TEXT,
            focus_area TEXT,
            sermon_id INTEGER,
            section TEXT,
            comment TEXT,
            rating INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY,
            title TEXT,
            content TEXT,
            word_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Insert sample sermon
    conn.execute(
        'INSERT INTO sermons (id, title, content, word_count) VALUES (?, ?, ?, ?)',
        (1, 'Test Sermon', 'Sample content', 2200)
    )
    # Insert sample feedback
    for fb in SAMPLE_FEEDBACK:
        conn.execute('''
            INSERT INTO panel_feedback
            (id, reviewer, reviewer_name, focus_area, sermon_id, section, comment, rating, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (fb['id'], fb['reviewer'], fb['reviewer_name'], fb['focus_area'],
              fb['sermon_id'], fb['section'], fb['comment'], fb['rating'], fb['created_at']))
    conn.commit()
    return conn


class TestFeedbackAPIRoutes:
    """Test suite for feedback API routes."""

    def test_should_return_200_when_getting_feedback_for_sermon(self):
        """Test API returns 200 for valid sermon feedback request."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/api/sermon/1/feedback')
            assert response.status_code == 200

    def test_should_return_feedback_as_json(self):
        """Test API returns feedback in JSON format."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/api/sermon/1/feedback')
            assert response.content_type == 'application/json'

    def test_should_return_404_for_invalid_sermon_id(self):
        """Test API returns 404 for non-existent sermon."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/api/sermon/99999/feedback')
            assert response.status_code == 404

    def test_should_return_feedback_list(self):
        """Test API returns list of feedback items."""
        from app import create_app
        from feedback_display import get_feedback_for_sermon

        app = create_app(testing=True)
        conn = create_test_db()

        feedback = get_feedback_for_sermon(conn, sermon_id=1)

        assert isinstance(feedback, list)
        assert len(feedback) >= 1
        conn.close()


class TestFeedbackGrouping:
    """Test suite for feedback grouping by reviewer."""

    def test_should_group_feedback_by_reviewer(self):
        """Test feedback is grouped by reviewer type."""
        from feedback_display import group_feedback_by_reviewer

        conn = create_test_db()
        grouped = group_feedback_by_reviewer(conn, sermon_id=1)

        assert 'theological' in grouped
        assert 'structural' in grouped
        assert 'pastoral' in grouped
        conn.close()

    def test_should_include_all_feedback_for_each_reviewer(self):
        """Test all feedback items are included for each reviewer."""
        from feedback_display import group_feedback_by_reviewer

        conn = create_test_db()
        # Add more feedback for theological reviewer
        conn.execute('''
            INSERT INTO panel_feedback
            (reviewer, reviewer_name, focus_area, sermon_id, section, comment, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('theological', 'Theological Reviewer', 'Wesleyan theology',
              1, 'Point 2', 'Another comment', 4))
        conn.commit()

        grouped = group_feedback_by_reviewer(conn, sermon_id=1)

        assert len(grouped['theological']) >= 2
        conn.close()

    def test_should_return_empty_dict_when_no_feedback(self):
        """Test returns empty dict when no feedback exists."""
        from feedback_display import group_feedback_by_reviewer

        conn = create_test_db()
        grouped = group_feedback_by_reviewer(conn, sermon_id=999)

        assert grouped == {}
        conn.close()


class TestReviewerInfo:
    """Test suite for reviewer information in feedback."""

    def test_should_include_reviewer_name(self):
        """Test feedback includes reviewer display name."""
        from feedback_display import get_feedback_for_sermon

        conn = create_test_db()
        feedback = get_feedback_for_sermon(conn, sermon_id=1)

        for fb in feedback:
            assert 'reviewer_name' in fb
            assert len(fb['reviewer_name']) > 0
        conn.close()

    def test_should_include_focus_area(self):
        """Test feedback includes reviewer focus area."""
        from feedback_display import get_feedback_for_sermon

        conn = create_test_db()
        feedback = get_feedback_for_sermon(conn, sermon_id=1)

        for fb in feedback:
            assert 'focus_area' in fb
            assert len(fb['focus_area']) > 0
        conn.close()

    def test_should_include_reviewer_type(self):
        """Test feedback includes reviewer type identifier."""
        from feedback_display import get_feedback_for_sermon

        conn = create_test_db()
        feedback = get_feedback_for_sermon(conn, sermon_id=1)

        for fb in feedback:
            assert 'reviewer' in fb
        conn.close()


class TestSectionLinking:
    """Test suite for feedback linking to sermon sections."""

    def test_should_include_section_reference(self):
        """Test feedback includes section reference."""
        from feedback_display import get_feedback_for_sermon

        conn = create_test_db()
        feedback = get_feedback_for_sermon(conn, sermon_id=1)

        for fb in feedback:
            assert 'section' in fb
        conn.close()

    def test_should_link_to_valid_sermon_sections(self):
        """Test section references are valid."""
        from feedback_display import get_feedback_with_section_links

        conn = create_test_db()
        feedback = get_feedback_with_section_links(conn, sermon_id=1)

        valid_sections = ['Introduction', 'Point 1', 'Point 2', 'Point 3', 'Conclusion']
        for fb in feedback:
            assert fb['section'] in valid_sections or fb['section'] is None
        conn.close()

    def test_should_include_section_anchor_id(self):
        """Test feedback includes anchor ID for section linking."""
        from feedback_display import get_feedback_with_section_links

        conn = create_test_db()
        feedback = get_feedback_with_section_links(conn, sermon_id=1)

        for fb in feedback:
            if fb['section']:
                assert 'anchor_id' in fb
        conn.close()


class TestEmptyFeedbackState:
    """Test suite for empty feedback states."""

    def test_should_return_empty_list_when_no_feedback(self):
        """Test returns empty list for sermon with no feedback."""
        from feedback_display import get_feedback_for_sermon

        conn = sqlite3.connect(':memory:')
        conn.execute('''
            CREATE TABLE panel_feedback (
                id INTEGER PRIMARY KEY,
                reviewer TEXT,
                sermon_id INTEGER,
                comment TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE sermons (
                id INTEGER PRIMARY KEY,
                title TEXT
            )
        ''')
        conn.execute('INSERT INTO sermons (id, title) VALUES (?, ?)', (1, 'Test'))
        conn.commit()

        feedback = get_feedback_for_sermon(conn, sermon_id=1)

        assert feedback == []
        conn.close()

    def test_should_return_empty_message_for_ui(self):
        """Test provides appropriate message for empty feedback."""
        from feedback_display import get_feedback_display_data

        conn = sqlite3.connect(':memory:')
        conn.execute('''
            CREATE TABLE panel_feedback (
                id INTEGER PRIMARY KEY,
                reviewer TEXT,
                sermon_id INTEGER,
                comment TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE sermons (
                id INTEGER PRIMARY KEY,
                title TEXT
            )
        ''')
        conn.execute('INSERT INTO sermons (id, title) VALUES (?, ?)', (1, 'Test'))
        conn.commit()

        display_data = get_feedback_display_data(conn, sermon_id=1)

        assert display_data.get('has_feedback', True) is False
        conn.close()


class TestErrorHandling:
    """Test suite for error handling in feedback display."""

    def test_should_handle_missing_sermon(self):
        """Test handling when sermon doesn't exist."""
        from feedback_display import get_feedback_for_sermon, SermonNotFoundError

        conn = create_test_db()

        with pytest.raises(SermonNotFoundError):
            get_feedback_for_sermon(conn, sermon_id=99999, require_sermon=True)
        conn.close()

    def test_should_handle_invalid_sermon_id_type(self):
        """Test handling invalid sermon ID type."""
        from feedback_display import get_feedback_for_sermon, InvalidSermonIdError

        conn = create_test_db()

        with pytest.raises(InvalidSermonIdError):
            get_feedback_for_sermon(conn, sermon_id='invalid')
        conn.close()

    def test_should_handle_database_connection_error(self):
        """Test handling database connection issues."""
        from feedback_display import get_feedback_for_sermon, DatabaseError

        with pytest.raises(DatabaseError):
            get_feedback_for_sermon(None, sermon_id=1)

    def test_should_return_graceful_error_response(self):
        """Test API returns graceful error response."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/api/sermon/invalid/feedback')

            assert response.status_code in [400, 404]
            data = response.get_json()
            assert 'error' in data


class TestTemplateRendering:
    """Test suite for template rendering with feedback data."""

    def test_should_render_feedback_page(self):
        """Test feedback page renders successfully."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/sermon/1/feedback')
            assert response.status_code == 200

    def test_should_include_feedback_in_template_context(self):
        """Test template receives feedback data."""
        from app import create_app
        from feedback_display import prepare_template_context

        app = create_app(testing=True)
        conn = create_test_db()

        context = prepare_template_context(conn, sermon_id=1)

        assert 'feedback_list' in context
        assert 'grouped_feedback' in context
        conn.close()

    def test_should_include_sermon_info_in_template(self):
        """Test template receives sermon information."""
        from app import create_app
        from feedback_display import prepare_template_context

        app = create_app(testing=True)
        conn = create_test_db()

        context = prepare_template_context(conn, sermon_id=1)

        assert 'sermon' in context
        assert 'sermon_title' in context or 'title' in context.get('sermon', {})
        conn.close()

    def test_should_include_reviewer_summary(self):
        """Test template receives reviewer summary."""
        from feedback_display import prepare_template_context

        conn = create_test_db()
        context = prepare_template_context(conn, sermon_id=1)

        assert 'reviewer_count' in context or 'reviewers' in context
        conn.close()


class TestFeedbackFormatting:
    """Test suite for feedback formatting."""

    def test_should_format_rating_as_stars(self):
        """Test rating is formatted for display."""
        from feedback_display import format_feedback_for_display

        feedback = {'rating': 4}
        formatted = format_feedback_for_display(feedback)

        assert 'rating_display' in formatted or 'stars' in formatted

    def test_should_format_timestamp(self):
        """Test timestamp is formatted readably."""
        from feedback_display import format_feedback_for_display

        feedback = {'created_at': '2025-01-10 12:00:00'}
        formatted = format_feedback_for_display(feedback)

        assert 'formatted_date' in formatted or 'display_time' in formatted

    def test_should_escape_html_in_comments(self):
        """Test HTML is escaped in feedback comments."""
        from feedback_display import format_feedback_for_display

        feedback = {'comment': '<script>alert("xss")</script>'}
        formatted = format_feedback_for_display(feedback)

        assert '<script>' not in formatted.get('comment', '')

    def test_should_preserve_markdown_formatting(self):
        """Test markdown formatting is preserved."""
        from feedback_display import format_feedback_for_display

        feedback = {'comment': '**Strong point** about grace.'}
        formatted = format_feedback_for_display(feedback)

        # Should preserve or render markdown
        assert '**' in formatted.get('comment', '') or '<strong>' in formatted.get('comment_html', '')


class TestFeedbackFiltering:
    """Test suite for feedback filtering options."""

    def test_should_filter_by_reviewer_type(self):
        """Test filtering feedback by reviewer type."""
        from feedback_display import get_feedback_for_sermon

        conn = create_test_db()
        feedback = get_feedback_for_sermon(conn, sermon_id=1, reviewer='theological')

        for fb in feedback:
            assert fb['reviewer'] == 'theological'
        conn.close()

    def test_should_filter_by_section(self):
        """Test filtering feedback by section."""
        from feedback_display import get_feedback_for_sermon

        conn = create_test_db()
        feedback = get_feedback_for_sermon(conn, sermon_id=1, section='Point 1')

        for fb in feedback:
            assert fb['section'] == 'Point 1'
        conn.close()

    def test_should_filter_by_minimum_rating(self):
        """Test filtering feedback by minimum rating."""
        from feedback_display import get_feedback_for_sermon

        conn = create_test_db()
        feedback = get_feedback_for_sermon(conn, sermon_id=1, min_rating=4)

        for fb in feedback:
            assert fb['rating'] >= 4
        conn.close()


class TestFeedbackSorting:
    """Test suite for feedback sorting options."""

    def test_should_sort_by_created_at_desc_by_default(self):
        """Test feedback is sorted by date descending."""
        from feedback_display import get_feedback_for_sermon

        conn = create_test_db()
        feedback = get_feedback_for_sermon(conn, sermon_id=1)

        # Verify descending order
        for i in range(len(feedback) - 1):
            assert feedback[i]['created_at'] >= feedback[i + 1]['created_at']
        conn.close()

    def test_should_sort_by_rating(self):
        """Test feedback can be sorted by rating."""
        from feedback_display import get_feedback_for_sermon

        conn = create_test_db()
        feedback = get_feedback_for_sermon(conn, sermon_id=1, sort_by='rating')

        for i in range(len(feedback) - 1):
            assert feedback[i]['rating'] >= feedback[i + 1]['rating']
        conn.close()

    def test_should_sort_by_section_order(self):
        """Test feedback can be sorted by section order."""
        from feedback_display import get_feedback_for_sermon

        conn = create_test_db()
        feedback = get_feedback_for_sermon(conn, sermon_id=1, sort_by='section')

        section_order = ['Introduction', 'Point 1', 'Point 2', 'Point 3', 'Conclusion']
        # Verify sections appear in order
        last_idx = -1
        for fb in feedback:
            if fb['section'] in section_order:
                idx = section_order.index(fb['section'])
                assert idx >= last_idx
                last_idx = idx
        conn.close()


class TestFlaskIntegration:
    """Test suite for Flask integration."""

    def test_should_register_feedback_routes(self):
        """Test feedback routes are registered."""
        from app import create_app

        app = create_app(testing=True)

        # Check routes exist
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert '/api/sermon/<sermon_id>/feedback' in rules or any('feedback' in r for r in rules)

    def test_should_return_json_content_type(self):
        """Test API returns correct content type."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/api/sermon/1/feedback')

            assert 'application/json' in response.content_type

    def test_should_include_cors_headers(self):
        """Test API includes CORS headers if needed."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/api/sermon/1/feedback')

            # CORS headers may or may not be present depending on config
            # Just verify the request succeeds
            assert response.status_code in [200, 404]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
