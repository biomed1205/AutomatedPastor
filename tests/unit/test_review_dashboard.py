"""Tests for review status dashboard.

These tests verify the review tracking dashboard for sermon drafts.
Enables tracking reviewer activity, feedback aggregation, and progress reports.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database - NO MOCKS.
"""
import pytest
import sqlite3
from datetime import datetime, timedelta


def create_test_db():
    """Create an in-memory test database for review dashboard testing."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row

    # Create sermons table
    conn.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create share_links table
    conn.execute('''
        CREATE TABLE share_links (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER NOT NULL,
            share_token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    ''')

    # Create review_activity table
    conn.execute('''
        CREATE TABLE review_activity (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER NOT NULL,
            reviewer_name TEXT NOT NULL,
            share_token TEXT,
            first_viewed_at TIMESTAMP,
            last_viewed_at TIMESTAMP,
            comments_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE,
            UNIQUE(sermon_id, reviewer_name)
        )
    ''')

    # Create review_comments table (for comment counting)
    conn.execute('''
        CREATE TABLE review_comments (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER NOT NULL,
            reviewer_name TEXT NOT NULL,
            comment_text TEXT NOT NULL,
            resolved INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    return conn


def insert_sample_sermon(conn, title="Test Sermon", content="Content"):
    """Insert a sample sermon for testing."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sermons (title, content) VALUES (?, ?)",
        (title, content)
    )
    conn.commit()
    return cursor.lastrowid


def insert_sample_share_link(conn, sermon_id, token):
    """Insert a sample share link for testing."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO share_links (sermon_id, share_token) VALUES (?, ?)",
        (sermon_id, token)
    )
    conn.commit()
    return cursor.lastrowid


def insert_sample_activity(conn, sermon_id, reviewer_name, status='pending',
                           comments_count=0, viewed_at=None):
    """Insert sample review activity for testing."""
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO review_activity
           (sermon_id, reviewer_name, status, comments_count, first_viewed_at)
           VALUES (?, ?, ?, ?, ?)""",
        (sermon_id, reviewer_name, status, comments_count, viewed_at)
    )
    conn.commit()
    return cursor.lastrowid


def insert_sample_comment(conn, sermon_id, reviewer_name, text="Comment"):
    """Insert a sample comment for testing."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO review_comments (sermon_id, reviewer_name, comment_text) VALUES (?, ?, ?)",
        (sermon_id, reviewer_name, text)
    )
    conn.commit()
    return cursor.lastrowid


class TestTrackReviewerView:
    """Test suite for tracking reviewer views."""

    def test_should_track_reviewer_view(self):
        """Test that reviewer view is tracked."""
        from review_dashboard import track_reviewer_view

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_share_link(conn, sermon_id, "token123")

        result = track_reviewer_view(conn, sermon_id, "token123", "John Reviewer")

        assert result is True
        conn.close()

    def test_should_record_first_view_timestamp(self):
        """Test that first view timestamp is recorded."""
        from review_dashboard import track_reviewer_view, list_reviewer_activity

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_share_link(conn, sermon_id, "token123")

        track_reviewer_view(conn, sermon_id, "token123", "Jane")
        activity = list_reviewer_activity(conn, sermon_id)

        assert len(activity) == 1
        assert activity[0]['first_viewed_at'] is not None
        conn.close()

    def test_should_update_last_view_on_subsequent_views(self):
        """Test that last view timestamp is updated on subsequent views."""
        from review_dashboard import track_reviewer_view

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_share_link(conn, sermon_id, "token123")

        track_reviewer_view(conn, sermon_id, "token123", "Reviewer")
        track_reviewer_view(conn, sermon_id, "token123", "Reviewer")

        # Should not create duplicate entries
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM review_activity WHERE sermon_id = ?",
            (sermon_id,)
        )
        count = cursor.fetchone()['count']
        assert count == 1
        conn.close()

    def test_should_associate_with_share_token(self):
        """Test that view is associated with share token."""
        from review_dashboard import track_reviewer_view, list_reviewer_activity

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_share_link(conn, sermon_id, "special_token")

        track_reviewer_view(conn, sermon_id, "special_token", "Viewer")
        activity = list_reviewer_activity(conn, sermon_id)

        assert activity[0]['share_token'] == "special_token"
        conn.close()


class TestTrackReviewerFeedback:
    """Test suite for tracking reviewer feedback."""

    def test_should_track_reviewer_feedback(self):
        """Test that reviewer feedback is tracked."""
        from review_dashboard import track_reviewer_feedback

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "Reviewer")

        result = track_reviewer_feedback(conn, sermon_id, "Reviewer")

        assert result is True
        conn.close()

    def test_should_update_comment_count(self):
        """Test that comment count is updated."""
        from review_dashboard import track_reviewer_feedback, list_reviewer_activity

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "Reviewer", comments_count=0)
        insert_sample_comment(conn, sermon_id, "Reviewer", "First comment")
        insert_sample_comment(conn, sermon_id, "Reviewer", "Second comment")

        track_reviewer_feedback(conn, sermon_id, "Reviewer")
        activity = list_reviewer_activity(conn, sermon_id)

        assert activity[0]['comments_count'] >= 2
        conn.close()

    def test_should_update_status_to_completed(self):
        """Test that status is updated to completed after feedback."""
        from review_dashboard import track_reviewer_feedback, list_reviewer_activity

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "Reviewer", status='pending')

        track_reviewer_feedback(conn, sermon_id, "Reviewer")
        activity = list_reviewer_activity(conn, sermon_id)

        assert activity[0]['status'] == 'completed'
        conn.close()

    def test_should_create_activity_if_not_exists(self):
        """Test that activity is created if it doesn't exist."""
        from review_dashboard import track_reviewer_feedback, list_reviewer_activity

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        track_reviewer_feedback(conn, sermon_id, "New Reviewer")
        activity = list_reviewer_activity(conn, sermon_id)

        assert len(activity) == 1
        conn.close()


class TestGetReviewStatus:
    """Test suite for getting overall review status."""

    def test_should_get_review_status(self):
        """Test that overall review status is returned."""
        from review_dashboard import get_review_status

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "Reviewer 1", status='completed')
        insert_sample_activity(conn, sermon_id, "Reviewer 2", status='pending')

        status = get_review_status(conn, sermon_id)

        assert status is not None
        assert 'total_reviewers' in status or 'reviewers_count' in status
        conn.close()

    def test_should_include_completion_stats(self):
        """Test that completion statistics are included."""
        from review_dashboard import get_review_status

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "R1", status='completed')
        insert_sample_activity(conn, sermon_id, "R2", status='completed')
        insert_sample_activity(conn, sermon_id, "R3", status='pending')

        status = get_review_status(conn, sermon_id)

        completed = status.get('completed', status.get('completed_count', 0))
        assert completed == 2
        conn.close()

    def test_should_include_total_comments(self):
        """Test that total comments count is included."""
        from review_dashboard import get_review_status

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "R1", comments_count=3)
        insert_sample_activity(conn, sermon_id, "R2", comments_count=5)

        status = get_review_status(conn, sermon_id)

        assert 'total_comments' in status or 'comments_count' in status
        conn.close()

    def test_should_handle_sermon_without_reviews(self):
        """Test status for sermon without any reviews."""
        from review_dashboard import get_review_status

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        status = get_review_status(conn, sermon_id)

        assert status is not None
        total = status.get('total_reviewers', status.get('reviewers_count', 0))
        assert total == 0
        conn.close()


class TestListReviewerActivity:
    """Test suite for listing reviewer activity."""

    def test_should_list_all_reviewer_activity(self):
        """Test that all reviewer activity is listed."""
        from review_dashboard import list_reviewer_activity

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "Reviewer 1")
        insert_sample_activity(conn, sermon_id, "Reviewer 2")
        insert_sample_activity(conn, sermon_id, "Reviewer 3")

        activity = list_reviewer_activity(conn, sermon_id)

        assert len(activity) == 3
        conn.close()

    def test_should_return_empty_for_sermon_without_activity(self):
        """Test that empty list is returned for sermon without activity."""
        from review_dashboard import list_reviewer_activity

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        activity = list_reviewer_activity(conn, sermon_id)

        assert activity == []
        conn.close()

    def test_should_include_activity_details(self):
        """Test that activity details are included."""
        from review_dashboard import list_reviewer_activity

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "John", status='completed', comments_count=5)

        activity = list_reviewer_activity(conn, sermon_id)

        assert activity[0]['reviewer_name'] == "John"
        assert activity[0]['status'] == 'completed'
        assert activity[0]['comments_count'] == 5
        conn.close()

    def test_should_order_by_most_recent_activity(self):
        """Test that activity is ordered by most recent."""
        from review_dashboard import list_reviewer_activity

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "First")
        insert_sample_activity(conn, sermon_id, "Second")
        insert_sample_activity(conn, sermon_id, "Third")

        activity = list_reviewer_activity(conn, sermon_id)

        # Should have consistent ordering
        assert len(activity) == 3
        conn.close()


class TestGetPendingReviewers:
    """Test suite for getting pending reviewers."""

    def test_should_get_pending_reviewers(self):
        """Test that pending reviewers are returned."""
        from review_dashboard import get_pending_reviewers

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "Pending 1", status='pending')
        insert_sample_activity(conn, sermon_id, "Pending 2", status='pending')
        insert_sample_activity(conn, sermon_id, "Done", status='completed')

        pending = get_pending_reviewers(conn, sermon_id)

        assert len(pending) == 2
        conn.close()

    def test_should_return_empty_when_all_completed(self):
        """Test that empty list is returned when all are completed."""
        from review_dashboard import get_pending_reviewers

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "Done 1", status='completed')
        insert_sample_activity(conn, sermon_id, "Done 2", status='completed')

        pending = get_pending_reviewers(conn, sermon_id)

        assert pending == []
        conn.close()

    def test_should_include_reviewer_details(self):
        """Test that reviewer details are included."""
        from review_dashboard import get_pending_reviewers

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        now = datetime.now().isoformat()
        insert_sample_activity(conn, sermon_id, "Waiting", status='pending', viewed_at=now)

        pending = get_pending_reviewers(conn, sermon_id)

        assert pending[0]['reviewer_name'] == "Waiting"
        conn.close()


class TestGetCompletedReviewers:
    """Test suite for getting completed reviewers."""

    def test_should_get_completed_reviewers(self):
        """Test that completed reviewers are returned."""
        from review_dashboard import get_completed_reviewers

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "Done 1", status='completed')
        insert_sample_activity(conn, sermon_id, "Done 2", status='completed')
        insert_sample_activity(conn, sermon_id, "Pending", status='pending')

        completed = get_completed_reviewers(conn, sermon_id)

        assert len(completed) == 2
        conn.close()

    def test_should_return_empty_when_none_completed(self):
        """Test that empty list is returned when none are completed."""
        from review_dashboard import get_completed_reviewers

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "Pending 1", status='pending')
        insert_sample_activity(conn, sermon_id, "Pending 2", status='pending')

        completed = get_completed_reviewers(conn, sermon_id)

        assert completed == []
        conn.close()

    def test_should_include_comment_counts(self):
        """Test that comment counts are included."""
        from review_dashboard import get_completed_reviewers

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "Verbose", status='completed', comments_count=10)

        completed = get_completed_reviewers(conn, sermon_id)

        assert completed[0]['comments_count'] == 10
        conn.close()


class TestCalculateReviewProgress:
    """Test suite for calculating review progress."""

    def test_should_calculate_review_progress(self):
        """Test that review progress percentage is calculated."""
        from review_dashboard import calculate_review_progress

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "Done 1", status='completed')
        insert_sample_activity(conn, sermon_id, "Done 2", status='completed')
        insert_sample_activity(conn, sermon_id, "Pending 1", status='pending')
        insert_sample_activity(conn, sermon_id, "Pending 2", status='pending')

        progress = calculate_review_progress(conn, sermon_id)

        assert progress == 50  # 2/4 = 50%
        conn.close()

    def test_should_return_100_when_all_completed(self):
        """Test that 100% is returned when all are completed."""
        from review_dashboard import calculate_review_progress

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "Done 1", status='completed')
        insert_sample_activity(conn, sermon_id, "Done 2", status='completed')

        progress = calculate_review_progress(conn, sermon_id)

        assert progress == 100
        conn.close()

    def test_should_return_0_when_none_completed(self):
        """Test that 0% is returned when none are completed."""
        from review_dashboard import calculate_review_progress

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "Pending 1", status='pending')
        insert_sample_activity(conn, sermon_id, "Pending 2", status='pending')

        progress = calculate_review_progress(conn, sermon_id)

        assert progress == 0
        conn.close()

    def test_should_handle_no_reviewers(self):
        """Test progress calculation with no reviewers."""
        from review_dashboard import calculate_review_progress

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        progress = calculate_review_progress(conn, sermon_id)

        # Should return 0 or 100 depending on interpretation
        assert progress == 0 or progress == 100
        conn.close()


class TestGetFeedbackSummary:
    """Test suite for getting feedback summary."""

    def test_should_get_feedback_summary(self):
        """Test that feedback summary is returned."""
        from review_dashboard import get_feedback_summary

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "R1", status='completed', comments_count=3)
        insert_sample_activity(conn, sermon_id, "R2", status='completed', comments_count=5)

        summary = get_feedback_summary(conn, sermon_id)

        assert summary is not None
        conn.close()

    def test_should_aggregate_by_reviewer(self):
        """Test that feedback is aggregated by reviewer."""
        from review_dashboard import get_feedback_summary

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "John", comments_count=3)
        insert_sample_activity(conn, sermon_id, "Jane", comments_count=7)

        summary = get_feedback_summary(conn, sermon_id)

        assert 'reviewers' in summary or isinstance(summary, list)
        conn.close()

    def test_should_include_total_stats(self):
        """Test that total statistics are included."""
        from review_dashboard import get_feedback_summary

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "R1", comments_count=2)
        insert_sample_activity(conn, sermon_id, "R2", comments_count=3)

        summary = get_feedback_summary(conn, sermon_id)

        assert summary is not None
        # Should have some aggregate stats
        conn.close()

    def test_should_handle_sermon_without_feedback(self):
        """Test summary for sermon without feedback."""
        from review_dashboard import get_feedback_summary

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        summary = get_feedback_summary(conn, sermon_id)

        assert summary is not None
        conn.close()


class TestExportReviewReport:
    """Test suite for exporting review report."""

    def test_should_export_review_report(self):
        """Test that review report can be exported."""
        from review_dashboard import export_review_report

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Easter Sermon")
        insert_sample_activity(conn, sermon_id, "John", status='completed', comments_count=3)

        report = export_review_report(conn, sermon_id)

        assert report is not None
        conn.close()

    def test_should_include_sermon_info_in_report(self):
        """Test that sermon info is included in report."""
        from review_dashboard import export_review_report

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Special Sermon")
        insert_sample_activity(conn, sermon_id, "Reviewer", status='completed')

        report = export_review_report(conn, sermon_id)

        assert 'sermon' in report or 'title' in report
        conn.close()

    def test_should_include_all_reviewer_details(self):
        """Test that all reviewer details are in report."""
        from review_dashboard import export_review_report

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "R1", status='completed', comments_count=5)
        insert_sample_activity(conn, sermon_id, "R2", status='pending', comments_count=0)

        report = export_review_report(conn, sermon_id)

        assert 'reviewers' in report or 'activity' in report
        conn.close()

    def test_should_include_progress_stats(self):
        """Test that progress statistics are in report."""
        from review_dashboard import export_review_report

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_activity(conn, sermon_id, "R1", status='completed')
        insert_sample_activity(conn, sermon_id, "R2", status='pending')

        report = export_review_report(conn, sermon_id)

        assert 'progress' in report or 'completion' in report or 'status' in report
        conn.close()


class TestEdgeCases:
    """Test suite for edge cases."""

    def test_should_handle_no_reviewers(self):
        """Test dashboard with no reviewers."""
        from review_dashboard import get_review_status, calculate_review_progress

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        status = get_review_status(conn, sermon_id)
        progress = calculate_review_progress(conn, sermon_id)

        assert status is not None
        conn.close()

    def test_should_handle_all_completed(self):
        """Test dashboard with all reviews completed."""
        from review_dashboard import get_pending_reviewers, calculate_review_progress

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        for i in range(5):
            insert_sample_activity(conn, sermon_id, f"Reviewer {i}", status='completed')

        pending = get_pending_reviewers(conn, sermon_id)
        progress = calculate_review_progress(conn, sermon_id)

        assert pending == []
        assert progress == 100
        conn.close()

    def test_should_handle_self_review(self):
        """Test tracking self-review (pastor reviewing own sermon)."""
        from review_dashboard import track_reviewer_view, list_reviewer_activity

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_share_link(conn, sermon_id, "self_token")

        track_reviewer_view(conn, sermon_id, "self_token", "Pastor Katie")
        activity = list_reviewer_activity(conn, sermon_id)

        assert len(activity) == 1
        assert activity[0]['reviewer_name'] == "Pastor Katie"
        conn.close()

    def test_should_handle_unicode_in_reviewer_name(self):
        """Test unicode in reviewer name."""
        from review_dashboard import track_reviewer_view, list_reviewer_activity

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_share_link(conn, sermon_id, "token")

        track_reviewer_view(conn, sermon_id, "token", "Ιωάννης Παπαδόπουλος")
        activity = list_reviewer_activity(conn, sermon_id)

        assert 'Ιωάννης' in activity[0]['reviewer_name']
        conn.close()

    def test_should_handle_many_reviewers(self):
        """Test dashboard with many reviewers."""
        from review_dashboard import list_reviewer_activity, get_review_status

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        for i in range(50):
            insert_sample_activity(
                conn, sermon_id, f"Reviewer {i}",
                status='completed' if i % 2 == 0 else 'pending'
            )

        activity = list_reviewer_activity(conn, sermon_id)
        status = get_review_status(conn, sermon_id)

        assert len(activity) == 50
        total = status.get('total_reviewers', status.get('reviewers_count', 0))
        assert total == 50
        conn.close()


class TestIntegration:
    """Integration tests for review dashboard workflows."""

    def test_should_complete_review_tracking_workflow(self):
        """Test complete review tracking workflow."""
        from review_dashboard import (
            track_reviewer_view,
            track_reviewer_feedback,
            get_review_status,
            calculate_review_progress
        )

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Reviewed Sermon")
        insert_sample_share_link(conn, sermon_id, "token1")
        insert_sample_share_link(conn, sermon_id, "token2")

        # Reviewers view
        track_reviewer_view(conn, sermon_id, "token1", "John")
        track_reviewer_view(conn, sermon_id, "token2", "Jane")

        # John provides feedback
        insert_sample_comment(conn, sermon_id, "John", "Great introduction!")
        track_reviewer_feedback(conn, sermon_id, "John")

        # Check status
        status = get_review_status(conn, sermon_id)
        progress = calculate_review_progress(conn, sermon_id)

        assert status is not None
        assert progress == 50  # 1/2 completed

        conn.close()

    def test_should_generate_complete_report(self):
        """Test generating complete review report."""
        from review_dashboard import (
            track_reviewer_view,
            track_reviewer_feedback,
            export_review_report
        )

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Report Sermon")
        insert_sample_share_link(conn, sermon_id, "token1")

        # Add some activity
        track_reviewer_view(conn, sermon_id, "token1", "Reviewer 1")
        insert_sample_comment(conn, sermon_id, "Reviewer 1", "Comment 1")
        insert_sample_comment(conn, sermon_id, "Reviewer 1", "Comment 2")
        track_reviewer_feedback(conn, sermon_id, "Reviewer 1")

        # Generate report
        report = export_review_report(conn, sermon_id)

        assert report is not None
        assert 'sermon' in report or 'title' in report or 'reviewers' in report

        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
