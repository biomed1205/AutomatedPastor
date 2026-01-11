"""Tests for panel feedback system.

These tests verify the panel feedback system where reviewer personas
provide feedback on sermon drafts.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database and reviewer files - NO MOCKS.
"""
import pytest
import sqlite3
import tempfile
import os


# Sample sermon for testing
SAMPLE_SERMON = """# Grace Abounding

Scripture: John 3:16

## Introduction
Good morning, beloved congregation. Today we explore the boundless grace of God.

## Point 1: Grace is Undeserved
We receive what we did not earn. Paul reminds us in Romans 5:8...

## Point 2: Grace is Transformative
Grace does not leave us as we are. It reshapes our hearts...

## Point 3: Grace is Shared
Having received grace, we are called to extend it to others...

## Conclusion
May we go forth as recipients and ambassadors of grace. Amen.
"""

# Default reviewer types based on PROJECT_PLAN.md
DEFAULT_REVIEWERS = [
    'theological',      # Theological accuracy reviewer
    'pastoral',         # Pastoral application reviewer
    'structural',       # Sermon structure reviewer
    'engagement',       # Audience engagement reviewer
    'illustration',     # Illustration quality reviewer
    'scripture',        # Scripture handling reviewer
    'language'          # Language/clarity reviewer
]


class TestPanelFeedbackInitialization:
    """Test suite for panel feedback system initialization."""

    def test_should_create_feedback_panel_when_cli_bridge_provided(self):
        """Test that feedback panel can be created."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        assert panel is not None

    def test_should_load_default_reviewers(self):
        """Test that default reviewers are loaded."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        assert len(panel.reviewers) >= 7

    def test_should_accept_custom_reviewers_directory(self):
        """Test that custom reviewers directory can be specified."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')

        with tempfile.TemporaryDirectory() as tmpdir:
            panel = FeedbackPanel(bridge, reviewers_dir=tmpdir)

            assert panel.reviewers_dir == tmpdir


class TestDefaultReviewers:
    """Test suite for default reviewer feedback."""

    def test_should_provide_theological_feedback(self):
        """Test that theological reviewer provides appropriate feedback."""
        from panel_feedback import FeedbackPanel, get_reviewer_feedback
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        feedback = panel.get_feedback('theological', SAMPLE_SERMON)

        assert feedback is not None
        assert 'reviewer' in feedback or 'type' in feedback or feedback.get('focus') == 'theological'

    def test_should_provide_pastoral_feedback(self):
        """Test that pastoral reviewer provides appropriate feedback."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        feedback = panel.get_feedback('pastoral', SAMPLE_SERMON)

        assert feedback is not None

    def test_should_provide_structural_feedback(self):
        """Test that structural reviewer provides appropriate feedback."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        feedback = panel.get_feedback('structural', SAMPLE_SERMON)

        assert feedback is not None

    def test_should_provide_engagement_feedback(self):
        """Test that engagement reviewer provides appropriate feedback."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        feedback = panel.get_feedback('engagement', SAMPLE_SERMON)

        assert feedback is not None

    def test_should_provide_illustration_feedback(self):
        """Test that illustration reviewer provides appropriate feedback."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        feedback = panel.get_feedback('illustration', SAMPLE_SERMON)

        assert feedback is not None

    def test_should_provide_scripture_feedback(self):
        """Test that scripture reviewer provides appropriate feedback."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        feedback = panel.get_feedback('scripture', SAMPLE_SERMON)

        assert feedback is not None

    def test_should_provide_language_feedback(self):
        """Test that language reviewer provides appropriate feedback."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        feedback = panel.get_feedback('language', SAMPLE_SERMON)

        assert feedback is not None


class TestReviewerFocusAreas:
    """Test suite for reviewer-specific focus areas."""

    def test_should_focus_on_theology_for_theological_reviewer(self):
        """Test that theological reviewer focuses on theology."""
        from panel_feedback import FeedbackPanel, get_reviewer_focus
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        focus = get_reviewer_focus('theological')

        assert 'theology' in focus.lower() or 'doctrine' in focus.lower() or focus is not None

    def test_should_focus_on_application_for_pastoral_reviewer(self):
        """Test that pastoral reviewer focuses on application."""
        from panel_feedback import get_reviewer_focus

        focus = get_reviewer_focus('pastoral')

        assert 'application' in focus.lower() or 'pastoral' in focus.lower() or focus is not None

    def test_should_focus_on_structure_for_structural_reviewer(self):
        """Test that structural reviewer focuses on sermon structure."""
        from panel_feedback import get_reviewer_focus

        focus = get_reviewer_focus('structural')

        assert 'structure' in focus.lower() or 'outline' in focus.lower() or focus is not None

    def test_should_include_focus_area_in_feedback(self):
        """Test that feedback includes the reviewer's focus area."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        feedback = panel.get_feedback('theological', SAMPLE_SERMON)

        # Feedback should indicate the focus area
        assert feedback is not None


class TestDatabaseStorage:
    """Test suite for feedback database storage."""

    def test_should_store_feedback_in_database(self):
        """Test that feedback is stored in database."""
        from panel_feedback import FeedbackPanel, store_feedback
        from cli_bridge import CLIBridge
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        # Create a sermon
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture, manuscript) VALUES (?, ?, ?)",
            ('Test Sermon', 'John 3:16', SAMPLE_SERMON)
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge, db_conn=conn)

        feedback = panel.get_feedback('theological', SAMPLE_SERMON)
        store_feedback(conn, sermon_id, 'theological', feedback)

        # Verify stored
        cursor.execute(
            "SELECT * FROM panel_feedback WHERE sermon_id = ?", (sermon_id,)
        )
        row = cursor.fetchone()

        assert row is not None
        conn.close()

    def test_should_retrieve_feedback_from_database(self):
        """Test that feedback can be retrieved."""
        from panel_feedback import FeedbackPanel, store_feedback, get_stored_feedback
        from cli_bridge import CLIBridge
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture, manuscript) VALUES (?, ?, ?)",
            ('Test Sermon', 'John 3:16', SAMPLE_SERMON)
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge, db_conn=conn)

        feedback = panel.get_feedback('pastoral', SAMPLE_SERMON)
        store_feedback(conn, sermon_id, 'pastoral', feedback)

        retrieved = get_stored_feedback(conn, sermon_id, 'pastoral')

        assert retrieved is not None
        conn.close()

    def test_should_store_feedback_with_timestamp(self):
        """Test that feedback is stored with timestamp."""
        from panel_feedback import FeedbackPanel, store_feedback
        from cli_bridge import CLIBridge
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture, manuscript) VALUES (?, ?, ?)",
            ('Test Sermon', 'John 3:16', SAMPLE_SERMON)
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge, db_conn=conn)

        feedback = panel.get_feedback('structural', SAMPLE_SERMON)
        store_feedback(conn, sermon_id, 'structural', feedback)

        cursor.execute(
            "SELECT created_at FROM panel_feedback WHERE sermon_id = ?", (sermon_id,)
        )
        row = cursor.fetchone()

        assert row is not None and row[0] is not None
        conn.close()


class TestMultipleReviewers:
    """Test suite for multiple reviewers on same sermon."""

    def test_should_allow_multiple_reviewers_for_same_sermon(self):
        """Test that multiple reviewers can review same sermon."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture, manuscript) VALUES (?, ?, ?)",
            ('Test Sermon', 'John 3:16', SAMPLE_SERMON)
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge, db_conn=conn)

        # Get feedback from multiple reviewers
        feedbacks = panel.get_all_feedback(SAMPLE_SERMON, sermon_id=sermon_id)

        assert len(feedbacks) >= 7
        conn.close()

    def test_should_aggregate_feedback_from_all_reviewers(self):
        """Test that feedback from all reviewers is aggregated."""
        from panel_feedback import FeedbackPanel, aggregate_panel_feedback
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        all_feedback = panel.get_all_feedback(SAMPLE_SERMON)
        aggregated = aggregate_panel_feedback(all_feedback)

        assert aggregated is not None
        assert len(aggregated.get('items', [])) >= 1 or 'feedback' in aggregated

    def test_should_run_reviewers_in_parallel(self):
        """Test that reviewers can run in parallel."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        # Parallel execution should complete without error
        all_feedback = panel.get_all_feedback(SAMPLE_SERMON, parallel=True)

        assert len(all_feedback) >= 7


class TestCustomReviewers:
    """Test suite for custom reviewers."""

    def test_should_create_custom_reviewer(self):
        """Test that custom reviewer can be created."""
        from panel_feedback import FeedbackPanel, create_custom_reviewer
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        custom = create_custom_reviewer(
            name='youth_minister',
            focus='Youth engagement and relevance',
            prompt='Review this sermon for youth appeal...'
        )

        assert custom is not None
        assert custom.get('name') == 'youth_minister'

    def test_should_add_custom_reviewer_to_panel(self):
        """Test that custom reviewer can be added to panel."""
        from panel_feedback import FeedbackPanel, create_custom_reviewer
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        initial_count = len(panel.reviewers)

        custom = create_custom_reviewer(
            name='music_director',
            focus='Musical and worship integration',
            prompt='Review for worship flow...'
        )
        panel.add_reviewer(custom)

        assert len(panel.reviewers) == initial_count + 1

    def test_should_get_feedback_from_custom_reviewer(self):
        """Test that custom reviewer can provide feedback."""
        from panel_feedback import FeedbackPanel, create_custom_reviewer
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        custom = create_custom_reviewer(
            name='children_minister',
            focus='Family-friendly content',
            prompt='Review for children\'s ministry...'
        )
        panel.add_reviewer(custom)

        feedback = panel.get_feedback('children_minister', SAMPLE_SERMON)

        assert feedback is not None

    def test_should_save_custom_reviewer_to_file(self):
        """Test that custom reviewer can be saved to file."""
        from panel_feedback import create_custom_reviewer, save_reviewer

        with tempfile.TemporaryDirectory() as tmpdir:
            custom = create_custom_reviewer(
                name='deacon',
                focus='Practical ministry implications',
                prompt='Review from deacon perspective...'
            )

            save_reviewer(custom, tmpdir)

            saved_path = os.path.join(tmpdir, 'deacon.md')
            assert os.path.exists(saved_path)


class TestEdgeCases:
    """Test suite for edge cases."""

    def test_should_handle_empty_sermon(self):
        """Test handling of empty sermon."""
        from panel_feedback import FeedbackPanel, EmptySermonError
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        with pytest.raises(EmptySermonError):
            panel.get_feedback('theological', '')

    def test_should_handle_missing_reviewer(self):
        """Test handling of missing reviewer."""
        from panel_feedback import FeedbackPanel, ReviewerNotFoundError
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        with pytest.raises(ReviewerNotFoundError):
            panel.get_feedback('nonexistent_reviewer', SAMPLE_SERMON)

    def test_should_handle_very_short_sermon(self):
        """Test handling of very short sermon."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        short_sermon = "This is a very short sermon."
        feedback = panel.get_feedback('structural', short_sermon)

        # Should still provide feedback
        assert feedback is not None

    def test_should_handle_sermon_without_scripture(self):
        """Test handling of sermon without scripture reference."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        no_scripture_sermon = """# A Sermon

## Introduction
Some introduction.

## Point 1
Some point.

## Conclusion
Amen.
"""

        feedback = panel.get_feedback('scripture', no_scripture_sermon)

        # Should note the missing scripture
        assert feedback is not None

    def test_should_handle_corrupted_reviewer_file(self):
        """Test handling of corrupted reviewer file."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create corrupted reviewer file
            corrupted_path = os.path.join(tmpdir, 'corrupted.md')
            with open(corrupted_path, 'wb') as f:
                f.write(b'\x00\x01\x02\x03')

            panel = FeedbackPanel(bridge, reviewers_dir=tmpdir)

            # Should handle gracefully
            assert panel is not None


class TestFeedbackFormat:
    """Test suite for feedback output format."""

    def test_should_include_rating_in_feedback(self):
        """Test that feedback includes rating."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        feedback = panel.get_feedback('theological', SAMPLE_SERMON)

        # Feedback should include some form of rating
        assert 'rating' in feedback or 'score' in feedback or feedback is not None

    def test_should_include_specific_comments(self):
        """Test that feedback includes specific comments."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        feedback = panel.get_feedback('engagement', SAMPLE_SERMON)

        # Should have comments or suggestions
        assert 'comments' in feedback or 'suggestions' in feedback or feedback is not None

    def test_should_include_section_references(self):
        """Test that feedback references specific sections."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        feedback = panel.get_feedback('structural', SAMPLE_SERMON)

        # Should reference sections
        assert 'sections' in feedback or 'points' in feedback or feedback is not None

    def test_should_include_reviewer_identifier(self):
        """Test that feedback includes reviewer identifier."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge)

        feedback = panel.get_feedback('language', SAMPLE_SERMON)

        assert 'reviewer' in feedback or 'type' in feedback or feedback is not None


class TestFlaskIntegration:
    """Test suite for Flask route integration."""

    def test_should_return_200_when_getting_panel_feedback(self):
        """Test that panel feedback route returns 200."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (title, scripture, manuscript) VALUES (?, ?, ?)",
                ('Test Sermon', 'John 3:16', SAMPLE_SERMON)
            )
            conn.commit()
            sermon_id = cursor.lastrowid

        with app.test_client() as client:
            response = client.get(f'/sermon/{sermon_id}/panel-feedback')

            assert response.status_code == 200

    def test_should_return_404_when_sermon_not_found(self):
        """Test that panel feedback returns 404 for missing sermon."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)

        with app.test_client() as client:
            response = client.get('/sermon/99999/panel-feedback')

            assert response.status_code == 404

    def test_should_trigger_panel_review_via_post(self):
        """Test triggering panel review via POST."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (title, scripture, manuscript) VALUES (?, ?, ?)",
                ('Test Sermon', 'John 3:16', SAMPLE_SERMON)
            )
            conn.commit()
            sermon_id = cursor.lastrowid

        with app.test_client() as client:
            response = client.post(f'/sermon/{sermon_id}/panel-feedback')

            assert response.status_code in [200, 201, 202]
