"""Tests for custom reviewer support.

These tests verify that users can create their own reviewer personas
that work alongside default reviewers.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database and files - NO MOCKS.
"""
import pytest
import sqlite3
import tempfile
import os
import json


# Sample custom reviewer data
SAMPLE_CUSTOM_REVIEWER = {
    'name': 'Youth Ministry Expert',
    'identifier': 'youth_ministry',
    'focus_area': 'Relevance and accessibility for young people',
    'prompt_template': 'Review this sermon for its appeal and relevance to youth ages 13-25.',
    'created_by': 'user_1'
}

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


def create_test_db():
    """Create an in-memory test database."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('''
        CREATE TABLE custom_reviewers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            identifier TEXT UNIQUE NOT NULL,
            focus_area TEXT NOT NULL,
            prompt_template TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY,
            title TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE panel_feedback (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER,
            reviewer TEXT,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn


class TestCustomReviewerCreation:
    """Test suite for creating custom reviewers."""

    def test_should_create_custom_reviewer_with_required_fields(self):
        """Test creating a custom reviewer with name and focus area."""
        from custom_reviewers import CustomReviewer, create_custom_reviewer

        conn = create_test_db()
        reviewer = create_custom_reviewer(
            conn,
            name='Youth Ministry Expert',
            focus_area='Youth relevance',
            identifier='youth_ministry'
        )

        assert reviewer is not None
        assert reviewer.name == 'Youth Ministry Expert'
        conn.close()

    def test_should_generate_identifier_if_not_provided(self):
        """Test identifier is auto-generated from name."""
        from custom_reviewers import create_custom_reviewer

        conn = create_test_db()
        reviewer = create_custom_reviewer(
            conn,
            name='Youth Ministry Expert',
            focus_area='Youth relevance'
        )

        assert reviewer.identifier is not None
        assert 'youth' in reviewer.identifier.lower()
        conn.close()

    def test_should_require_name(self):
        """Test that name is required."""
        from custom_reviewers import create_custom_reviewer, ValidationError

        conn = create_test_db()

        with pytest.raises(ValidationError) as exc_info:
            create_custom_reviewer(conn, name='', focus_area='Focus')

        assert 'name' in str(exc_info.value).lower()
        conn.close()

    def test_should_require_focus_area(self):
        """Test that focus area is required."""
        from custom_reviewers import create_custom_reviewer, ValidationError

        conn = create_test_db()

        with pytest.raises(ValidationError) as exc_info:
            create_custom_reviewer(conn, name='Reviewer', focus_area='')

        assert 'focus' in str(exc_info.value).lower()
        conn.close()

    def test_should_accept_optional_prompt_template(self):
        """Test custom prompt template can be provided."""
        from custom_reviewers import create_custom_reviewer

        conn = create_test_db()
        reviewer = create_custom_reviewer(
            conn,
            name='Custom Reviewer',
            focus_area='Custom focus',
            prompt_template='Review with specific criteria...'
        )

        assert reviewer.prompt_template is not None
        conn.close()

    def test_should_store_creator_id(self):
        """Test reviewer stores creator information."""
        from custom_reviewers import create_custom_reviewer

        conn = create_test_db()
        reviewer = create_custom_reviewer(
            conn,
            name='Custom Reviewer',
            focus_area='Focus',
            created_by='user_123'
        )

        assert reviewer.created_by == 'user_123'
        conn.close()


class TestCustomReviewerPersistence:
    """Test suite for saving and loading custom reviewers."""

    def test_should_save_reviewer_to_database(self):
        """Test reviewer is saved to database."""
        from custom_reviewers import create_custom_reviewer

        conn = create_test_db()
        reviewer = create_custom_reviewer(
            conn,
            name='Test Reviewer',
            focus_area='Test focus'
        )

        cursor = conn.execute('SELECT * FROM custom_reviewers')
        row = cursor.fetchone()

        assert row is not None
        assert row['name'] == 'Test Reviewer'
        conn.close()

    def test_should_load_reviewer_by_id(self):
        """Test loading reviewer by ID."""
        from custom_reviewers import create_custom_reviewer, get_custom_reviewer

        conn = create_test_db()
        created = create_custom_reviewer(
            conn,
            name='Test Reviewer',
            focus_area='Focus'
        )

        loaded = get_custom_reviewer(conn, reviewer_id=created.id)

        assert loaded.name == 'Test Reviewer'
        conn.close()

    def test_should_load_reviewer_by_identifier(self):
        """Test loading reviewer by identifier."""
        from custom_reviewers import create_custom_reviewer, get_custom_reviewer_by_identifier

        conn = create_test_db()
        create_custom_reviewer(
            conn,
            name='Test Reviewer',
            focus_area='Focus',
            identifier='test_reviewer'
        )

        loaded = get_custom_reviewer_by_identifier(conn, 'test_reviewer')

        assert loaded.name == 'Test Reviewer'
        conn.close()

    def test_should_save_reviewer_to_file(self):
        """Test saving reviewer to JSON file."""
        from custom_reviewers import create_custom_reviewer, save_reviewer_to_file

        conn = create_test_db()
        reviewer = create_custom_reviewer(
            conn,
            name='Test Reviewer',
            focus_area='Focus'
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = save_reviewer_to_file(reviewer, tmpdir)

            assert os.path.exists(filepath)
            with open(filepath) as f:
                data = json.load(f)
                assert data['name'] == 'Test Reviewer'
        conn.close()

    def test_should_load_reviewer_from_file(self):
        """Test loading reviewer from JSON file."""
        from custom_reviewers import load_reviewer_from_file, CustomReviewer

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'reviewer.json')
            with open(filepath, 'w') as f:
                json.dump(SAMPLE_CUSTOM_REVIEWER, f)

            reviewer = load_reviewer_from_file(filepath)

            assert reviewer.name == SAMPLE_CUSTOM_REVIEWER['name']

    def test_should_list_all_custom_reviewers(self):
        """Test listing all custom reviewers."""
        from custom_reviewers import create_custom_reviewer, list_custom_reviewers

        conn = create_test_db()
        create_custom_reviewer(conn, name='Reviewer 1', focus_area='Focus 1')
        create_custom_reviewer(conn, name='Reviewer 2', focus_area='Focus 2')

        reviewers = list_custom_reviewers(conn)

        assert len(reviewers) >= 2
        conn.close()


class TestCustomReviewerFeedback:
    """Test suite for custom reviewer providing feedback."""

    def test_should_provide_feedback_on_sermon(self):
        """Test custom reviewer can provide feedback."""
        from custom_reviewers import create_custom_reviewer, get_feedback
        from cli_bridge import CLIBridge

        conn = create_test_db()
        conn.execute(
            'INSERT INTO sermons (id, title, content) VALUES (?, ?, ?)',
            (1, 'Test Sermon', SAMPLE_SERMON)
        )
        conn.commit()

        reviewer = create_custom_reviewer(
            conn,
            name='Youth Reviewer',
            focus_area='Youth relevance'
        )

        bridge = CLIBridge(command='echo')
        feedback = get_feedback(bridge, reviewer, SAMPLE_SERMON)

        assert feedback is not None
        conn.close()

    def test_should_include_focus_area_in_feedback(self):
        """Test feedback reflects reviewer's focus area."""
        from custom_reviewers import create_custom_reviewer, get_feedback
        from cli_bridge import CLIBridge

        conn = create_test_db()
        reviewer = create_custom_reviewer(
            conn,
            name='Youth Reviewer',
            focus_area='Youth ministry and engagement'
        )

        bridge = CLIBridge(command='echo')
        feedback = get_feedback(bridge, reviewer, SAMPLE_SERMON)

        assert feedback.get('focus_area', '') == 'Youth ministry and engagement'
        conn.close()

    def test_should_save_feedback_to_database(self):
        """Test feedback is saved to database."""
        from custom_reviewers import create_custom_reviewer, get_and_save_feedback
        from cli_bridge import CLIBridge

        conn = create_test_db()
        conn.execute(
            'INSERT INTO sermons (id, title, content) VALUES (?, ?, ?)',
            (1, 'Test Sermon', SAMPLE_SERMON)
        )
        conn.commit()

        reviewer = create_custom_reviewer(
            conn,
            name='Youth Reviewer',
            focus_area='Youth focus',
            identifier='youth'
        )

        bridge = CLIBridge(command='echo')
        get_and_save_feedback(bridge, conn, reviewer, sermon_id=1, sermon_text=SAMPLE_SERMON)

        cursor = conn.execute('SELECT * FROM panel_feedback WHERE reviewer = ?', ('youth',))
        row = cursor.fetchone()

        assert row is not None
        conn.close()


class TestCustomReviewerInPanel:
    """Test suite for custom reviewers in panel alongside defaults."""

    def test_should_add_custom_reviewer_to_panel(self):
        """Test adding custom reviewer to panel."""
        from panel_feedback import FeedbackPanel
        from custom_reviewers import create_custom_reviewer
        from cli_bridge import CLIBridge

        conn = create_test_db()
        reviewer = create_custom_reviewer(
            conn,
            name='Youth Reviewer',
            focus_area='Youth relevance'
        )

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        panel.add_custom_reviewer(reviewer)

        assert panel.has_reviewer(reviewer.identifier)
        conn.close()

    def test_should_run_custom_reviewer_with_defaults(self):
        """Test custom reviewer runs alongside default reviewers."""
        from panel_feedback import FeedbackPanel
        from custom_reviewers import create_custom_reviewer
        from cli_bridge import CLIBridge

        conn = create_test_db()
        reviewer = create_custom_reviewer(
            conn,
            name='Youth Reviewer',
            focus_area='Youth focus',
            identifier='youth'
        )

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)
        panel.add_custom_reviewer(reviewer)

        all_feedback = panel.get_all_feedback(SAMPLE_SERMON)

        # Should include custom reviewer feedback
        reviewers = [f.get('reviewer') for f in all_feedback]
        assert 'youth' in reviewers
        conn.close()

    def test_should_include_custom_reviewers_in_feedback_list(self):
        """Test custom reviewers appear in panel feedback list."""
        from panel_feedback import FeedbackPanel
        from custom_reviewers import create_custom_reviewer
        from cli_bridge import CLIBridge

        conn = create_test_db()
        reviewer = create_custom_reviewer(
            conn,
            name='Custom Reviewer',
            focus_area='Custom focus',
            identifier='custom'
        )

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)
        panel.add_custom_reviewer(reviewer)

        all_reviewers = panel.list_all_reviewers()

        assert any(r['identifier'] == 'custom' for r in all_reviewers)
        conn.close()


class TestCustomReviewerEditing:
    """Test suite for editing existing custom reviewers."""

    def test_should_update_reviewer_name(self):
        """Test updating reviewer name."""
        from custom_reviewers import create_custom_reviewer, update_custom_reviewer

        conn = create_test_db()
        reviewer = create_custom_reviewer(
            conn,
            name='Original Name',
            focus_area='Focus'
        )

        updated = update_custom_reviewer(conn, reviewer.id, name='New Name')

        assert updated.name == 'New Name'
        conn.close()

    def test_should_update_focus_area(self):
        """Test updating focus area."""
        from custom_reviewers import create_custom_reviewer, update_custom_reviewer

        conn = create_test_db()
        reviewer = create_custom_reviewer(
            conn,
            name='Reviewer',
            focus_area='Original Focus'
        )

        updated = update_custom_reviewer(conn, reviewer.id, focus_area='New Focus')

        assert updated.focus_area == 'New Focus'
        conn.close()

    def test_should_update_prompt_template(self):
        """Test updating prompt template."""
        from custom_reviewers import create_custom_reviewer, update_custom_reviewer

        conn = create_test_db()
        reviewer = create_custom_reviewer(
            conn,
            name='Reviewer',
            focus_area='Focus',
            prompt_template='Original prompt'
        )

        updated = update_custom_reviewer(conn, reviewer.id, prompt_template='New prompt')

        assert updated.prompt_template == 'New prompt'
        conn.close()

    def test_should_update_updated_at_timestamp(self):
        """Test updated_at is changed on update."""
        from custom_reviewers import create_custom_reviewer, update_custom_reviewer

        conn = create_test_db()
        reviewer = create_custom_reviewer(
            conn,
            name='Reviewer',
            focus_area='Focus'
        )

        original_updated = reviewer.updated_at
        updated = update_custom_reviewer(conn, reviewer.id, name='New Name')

        assert updated.updated_at != original_updated
        conn.close()


class TestCustomReviewerDeletion:
    """Test suite for deleting custom reviewers."""

    def test_should_delete_reviewer_from_database(self):
        """Test deleting reviewer from database."""
        from custom_reviewers import create_custom_reviewer, delete_custom_reviewer

        conn = create_test_db()
        reviewer = create_custom_reviewer(
            conn,
            name='Reviewer',
            focus_area='Focus'
        )

        delete_custom_reviewer(conn, reviewer.id)

        cursor = conn.execute('SELECT * FROM custom_reviewers WHERE id = ?', (reviewer.id,))
        row = cursor.fetchone()

        assert row is None
        conn.close()

    def test_should_return_true_on_successful_deletion(self):
        """Test returns True when deletion succeeds."""
        from custom_reviewers import create_custom_reviewer, delete_custom_reviewer

        conn = create_test_db()
        reviewer = create_custom_reviewer(
            conn,
            name='Reviewer',
            focus_area='Focus'
        )

        result = delete_custom_reviewer(conn, reviewer.id)

        assert result is True
        conn.close()

    def test_should_raise_error_for_nonexistent_reviewer(self):
        """Test error when deleting nonexistent reviewer."""
        from custom_reviewers import delete_custom_reviewer, ReviewerNotFoundError

        conn = create_test_db()

        with pytest.raises(ReviewerNotFoundError):
            delete_custom_reviewer(conn, reviewer_id=99999)
        conn.close()

    def test_should_not_delete_default_reviewers(self):
        """Test cannot delete default reviewers."""
        from custom_reviewers import delete_custom_reviewer, CannotDeleteDefaultError

        conn = create_test_db()

        with pytest.raises(CannotDeleteDefaultError):
            delete_custom_reviewer(conn, identifier='theological')
        conn.close()


class TestCustomReviewerValidation:
    """Test suite for custom reviewer validation."""

    def test_should_reject_duplicate_identifier(self):
        """Test duplicate identifiers are rejected."""
        from custom_reviewers import create_custom_reviewer, DuplicateIdentifierError

        conn = create_test_db()
        create_custom_reviewer(
            conn,
            name='Reviewer 1',
            focus_area='Focus',
            identifier='duplicate'
        )

        with pytest.raises(DuplicateIdentifierError):
            create_custom_reviewer(
                conn,
                name='Reviewer 2',
                focus_area='Focus',
                identifier='duplicate'
            )
        conn.close()

    def test_should_validate_identifier_format(self):
        """Test identifier format is validated."""
        from custom_reviewers import create_custom_reviewer, InvalidIdentifierError

        conn = create_test_db()

        with pytest.raises(InvalidIdentifierError):
            create_custom_reviewer(
                conn,
                name='Reviewer',
                focus_area='Focus',
                identifier='invalid identifier!'  # Contains spaces and special chars
            )
        conn.close()

    def test_should_validate_name_length(self):
        """Test name length is validated."""
        from custom_reviewers import create_custom_reviewer, ValidationError

        conn = create_test_db()

        with pytest.raises(ValidationError):
            create_custom_reviewer(
                conn,
                name='A' * 500,  # Too long
                focus_area='Focus'
            )
        conn.close()

    def test_should_validate_focus_area_length(self):
        """Test focus area length is validated."""
        from custom_reviewers import create_custom_reviewer, ValidationError

        conn = create_test_db()

        with pytest.raises(ValidationError):
            create_custom_reviewer(
                conn,
                name='Reviewer',
                focus_area='A' * 1000  # Too long
            )
        conn.close()


class TestUIRoutes:
    """Test suite for UI routes for custom reviewer management."""

    def test_should_return_200_for_list_reviewers_page(self):
        """Test custom reviewers list page returns 200."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/custom-reviewers')
            assert response.status_code == 200

    def test_should_return_200_for_create_reviewer_page(self):
        """Test create reviewer page returns 200."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/custom-reviewers/new')
            assert response.status_code == 200

    def test_should_create_reviewer_via_post(self):
        """Test creating reviewer via POST."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.post('/api/custom-reviewers', json={
                'name': 'Test Reviewer',
                'focus_area': 'Test focus'
            })
            assert response.status_code in [200, 201]

    def test_should_return_400_for_invalid_data(self):
        """Test POST returns 400 for invalid data."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.post('/api/custom-reviewers', json={
                'name': ''  # Missing focus_area, empty name
            })
            assert response.status_code == 400

    def test_should_delete_reviewer_via_delete(self):
        """Test deleting reviewer via DELETE."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            # First create a reviewer
            create_response = client.post('/api/custom-reviewers', json={
                'name': 'To Delete',
                'focus_area': 'Focus'
            })
            reviewer_id = create_response.get_json().get('id')

            # Then delete it
            response = client.delete(f'/api/custom-reviewers/{reviewer_id}')
            assert response.status_code in [200, 204]

    def test_should_update_reviewer_via_put(self):
        """Test updating reviewer via PUT."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            # First create a reviewer
            create_response = client.post('/api/custom-reviewers', json={
                'name': 'Original',
                'focus_area': 'Focus'
            })
            reviewer_id = create_response.get_json().get('id')

            # Then update it
            response = client.put(f'/api/custom-reviewers/{reviewer_id}', json={
                'name': 'Updated'
            })
            assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
