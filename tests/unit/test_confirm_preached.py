"""
Tests for confirm preached functionality.

Tests the workflow for marking sermons as preached with dates,
tracking status transitions, and generating confirmation receipts.

TDD: All tests should fail with ModuleNotFoundError until implementation.
NO MOCKS: Uses real SQLite in-memory database.
"""

import sqlite3
import pytest
from datetime import datetime, date, timedelta


def create_test_db():
    """Create test database with sermon and preaching tables."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Sermons table
    cursor.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            scripture TEXT,
            scheduled_date TEXT,
            status TEXT DEFAULT 'draft',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Preached records table
    cursor.execute('''
        CREATE TABLE preached_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            preached_date TEXT NOT NULL,
            confirmed_by TEXT,
            confirmed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id)
        )
    ''')

    # Sermon status history table
    cursor.execute('''
        CREATE TABLE sermon_status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            old_status TEXT,
            new_status TEXT NOT NULL,
            changed_by TEXT,
            changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            reason TEXT,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id)
        )
    ''')

    conn.commit()
    return conn


def insert_sample_sermon(conn, title="Test Sermon", scripture="John 3:16",
                        scheduled_date="2024-03-17", status="approved"):
    """Insert a sample sermon for testing."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sermons (title, scripture, scheduled_date, status)
        VALUES (?, ?, ?, ?)
    ''', (title, scripture, scheduled_date, status))
    conn.commit()
    return cursor.lastrowid


def insert_preached_record(conn, sermon_id, preached_date="2024-03-17",
                          confirmed_by="Pastor Katie"):
    """Insert a preached record."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO preached_records (sermon_id, preached_date, confirmed_by)
        VALUES (?, ?, ?)
    ''', (sermon_id, preached_date, confirmed_by))
    conn.commit()
    return cursor.lastrowid


def insert_status_history(conn, sermon_id, old_status, new_status,
                         changed_by="System"):
    """Insert a status history record."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sermon_status_history (sermon_id, old_status, new_status, changed_by)
        VALUES (?, ?, ?, ?)
    ''', (sermon_id, old_status, new_status, changed_by))
    conn.commit()
    return cursor.lastrowid


class TestMarkAsPreached:
    """Tests for mark_as_preached function."""

    def test_should_mark_sermon_as_preached(self):
        """Test marking a sermon as preached with date."""
        from confirm_preached import mark_as_preached

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="approved")

        result = mark_as_preached(conn, sermon_id, "2024-03-17")

        assert result is not None
        assert result['success'] is True
        assert result['sermon_id'] == sermon_id
        assert result['preached_date'] == "2024-03-17"

    def test_should_record_confirmed_by(self):
        """Test recording who confirmed the sermon was preached."""
        from confirm_preached import mark_as_preached

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="approved")

        result = mark_as_preached(conn, sermon_id, "2024-03-17",
                                 confirmed_by="Pastor Katie")

        assert result['confirmed_by'] == "Pastor Katie"

    def test_should_update_sermon_status_to_preached(self):
        """Test that sermon status is updated when marked as preached."""
        from confirm_preached import mark_as_preached

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="approved")

        mark_as_preached(conn, sermon_id, "2024-03-17")

        cursor = conn.cursor()
        cursor.execute('SELECT status FROM sermons WHERE id = ?', (sermon_id,))
        row = cursor.fetchone()
        assert row['status'] == 'preached'

    def test_should_create_preached_record(self):
        """Test that a preached record is created."""
        from confirm_preached import mark_as_preached

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="approved")

        mark_as_preached(conn, sermon_id, "2024-03-17")

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM preached_records WHERE sermon_id = ?',
                      (sermon_id,))
        record = cursor.fetchone()
        assert record is not None
        assert record['preached_date'] == "2024-03-17"

    def test_should_record_timestamp_when_marking_preached(self):
        """Test that confirmation timestamp is recorded."""
        from confirm_preached import mark_as_preached

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="approved")

        result = mark_as_preached(conn, sermon_id, "2024-03-17")

        assert 'confirmed_at' in result
        assert result['confirmed_at'] is not None

    def test_should_return_error_for_nonexistent_sermon(self):
        """Test error handling for non-existent sermon."""
        from confirm_preached import mark_as_preached

        conn = create_test_db()

        result = mark_as_preached(conn, 9999, "2024-03-17")

        assert result['success'] is False
        assert 'error' in result

    def test_should_warn_when_sermon_already_preached(self):
        """Test warning when trying to mark already preached sermon."""
        from confirm_preached import mark_as_preached

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_preached_record(conn, sermon_id)

        result = mark_as_preached(conn, sermon_id, "2024-03-24")

        assert 'warning' in result
        assert 'already preached' in result['warning'].lower()


class TestGetPreachedStatus:
    """Tests for get_preached_status function."""

    def test_should_return_preached_status_true(self):
        """Test returning True for preached sermon."""
        from confirm_preached import get_preached_status

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_preached_record(conn, sermon_id)

        result = get_preached_status(conn, sermon_id)

        assert result['is_preached'] is True

    def test_should_return_preached_status_false(self):
        """Test returning False for unpreached sermon."""
        from confirm_preached import get_preached_status

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="approved")

        result = get_preached_status(conn, sermon_id)

        assert result['is_preached'] is False

    def test_should_include_preached_date_when_preached(self):
        """Test including preached date in status."""
        from confirm_preached import get_preached_status

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_preached_record(conn, sermon_id, preached_date="2024-03-17")

        result = get_preached_status(conn, sermon_id)

        assert result['preached_date'] == "2024-03-17"

    def test_should_include_confirmed_by_when_preached(self):
        """Test including confirmed_by in status."""
        from confirm_preached import get_preached_status

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_preached_record(conn, sermon_id, confirmed_by="Pastor Katie")

        result = get_preached_status(conn, sermon_id)

        assert result['confirmed_by'] == "Pastor Katie"

    def test_should_return_none_for_nonexistent_sermon(self):
        """Test handling non-existent sermon."""
        from confirm_preached import get_preached_status

        conn = create_test_db()

        result = get_preached_status(conn, 9999)

        assert result is None


class TestUpdatePreachedDate:
    """Tests for update_preached_date function."""

    def test_should_update_preached_date(self):
        """Test updating the preached date."""
        from confirm_preached import update_preached_date

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_preached_record(conn, sermon_id, preached_date="2024-03-17")

        result = update_preached_date(conn, sermon_id, "2024-03-24")

        assert result['success'] is True
        assert result['new_date'] == "2024-03-24"

    def test_should_preserve_confirmed_by_on_update(self):
        """Test that confirmed_by is preserved when updating date."""
        from confirm_preached import update_preached_date

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_preached_record(conn, sermon_id, confirmed_by="Pastor Katie")

        update_preached_date(conn, sermon_id, "2024-03-24")

        cursor = conn.cursor()
        cursor.execute('SELECT confirmed_by FROM preached_records WHERE sermon_id = ?',
                      (sermon_id,))
        record = cursor.fetchone()
        assert record['confirmed_by'] == "Pastor Katie"

    def test_should_return_error_for_unpreached_sermon(self):
        """Test error when updating date for unpreached sermon."""
        from confirm_preached import update_preached_date

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="approved")

        result = update_preached_date(conn, sermon_id, "2024-03-24")

        assert result['success'] is False
        assert 'error' in result

    def test_should_return_error_for_nonexistent_sermon(self):
        """Test error for non-existent sermon."""
        from confirm_preached import update_preached_date

        conn = create_test_db()

        result = update_preached_date(conn, 9999, "2024-03-24")

        assert result['success'] is False


class TestListPreachedSermons:
    """Tests for list_preached_sermons function."""

    def test_should_list_all_preached_sermons(self):
        """Test listing all preached sermons."""
        from confirm_preached import list_preached_sermons

        conn = create_test_db()
        sermon1 = insert_sample_sermon(conn, title="Sermon 1", status="preached")
        sermon2 = insert_sample_sermon(conn, title="Sermon 2", status="preached")
        insert_preached_record(conn, sermon1, preached_date="2024-03-10")
        insert_preached_record(conn, sermon2, preached_date="2024-03-17")

        result = list_preached_sermons(conn)

        assert len(result) == 2

    def test_should_filter_by_start_date(self):
        """Test filtering by start date."""
        from confirm_preached import list_preached_sermons

        conn = create_test_db()
        sermon1 = insert_sample_sermon(conn, title="Sermon 1", status="preached")
        sermon2 = insert_sample_sermon(conn, title="Sermon 2", status="preached")
        insert_preached_record(conn, sermon1, preached_date="2024-03-10")
        insert_preached_record(conn, sermon2, preached_date="2024-03-17")

        result = list_preached_sermons(conn, start_date="2024-03-15")

        assert len(result) == 1
        assert result[0]['preached_date'] == "2024-03-17"

    def test_should_filter_by_end_date(self):
        """Test filtering by end date."""
        from confirm_preached import list_preached_sermons

        conn = create_test_db()
        sermon1 = insert_sample_sermon(conn, title="Sermon 1", status="preached")
        sermon2 = insert_sample_sermon(conn, title="Sermon 2", status="preached")
        insert_preached_record(conn, sermon1, preached_date="2024-03-10")
        insert_preached_record(conn, sermon2, preached_date="2024-03-17")

        result = list_preached_sermons(conn, end_date="2024-03-15")

        assert len(result) == 1
        assert result[0]['preached_date'] == "2024-03-10"

    def test_should_filter_by_date_range(self):
        """Test filtering by date range."""
        from confirm_preached import list_preached_sermons

        conn = create_test_db()
        sermon1 = insert_sample_sermon(conn, title="Sermon 1", status="preached")
        sermon2 = insert_sample_sermon(conn, title="Sermon 2", status="preached")
        sermon3 = insert_sample_sermon(conn, title="Sermon 3", status="preached")
        insert_preached_record(conn, sermon1, preached_date="2024-03-10")
        insert_preached_record(conn, sermon2, preached_date="2024-03-17")
        insert_preached_record(conn, sermon3, preached_date="2024-03-24")

        result = list_preached_sermons(conn,
                                       start_date="2024-03-12",
                                       end_date="2024-03-20")

        assert len(result) == 1
        assert result[0]['preached_date'] == "2024-03-17"

    def test_should_return_empty_when_no_preached_sermons(self):
        """Test returning empty list when no sermons preached."""
        from confirm_preached import list_preached_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, status="approved")

        result = list_preached_sermons(conn)

        assert result == []

    def test_should_include_sermon_details(self):
        """Test including sermon details in list."""
        from confirm_preached import list_preached_sermons

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, title="Test Sermon",
                                        scripture="John 3:16", status="preached")
        insert_preached_record(conn, sermon_id, preached_date="2024-03-17")

        result = list_preached_sermons(conn)

        assert result[0]['title'] == "Test Sermon"
        assert result[0]['scripture'] == "John 3:16"


class TestGetUnpreachedSermons:
    """Tests for get_unpreached_sermons function."""

    def test_should_get_unpreached_sermons(self):
        """Test getting all unpreached sermons."""
        from confirm_preached import get_unpreached_sermons

        conn = create_test_db()
        sermon1 = insert_sample_sermon(conn, title="Sermon 1", status="approved")
        sermon2 = insert_sample_sermon(conn, title="Sermon 2", status="preached")
        insert_preached_record(conn, sermon2)

        result = get_unpreached_sermons(conn)

        assert len(result) == 1
        assert result[0]['title'] == "Sermon 1"

    def test_should_include_scheduled_date(self):
        """Test including scheduled date in results."""
        from confirm_preached import get_unpreached_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, title="Sermon 1",
                            scheduled_date="2024-03-17", status="approved")

        result = get_unpreached_sermons(conn)

        assert result[0]['scheduled_date'] == "2024-03-17"

    def test_should_order_by_scheduled_date(self):
        """Test ordering by scheduled date ascending."""
        from confirm_preached import get_unpreached_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, title="Later",
                            scheduled_date="2024-03-24", status="approved")
        insert_sample_sermon(conn, title="Earlier",
                            scheduled_date="2024-03-17", status="approved")

        result = get_unpreached_sermons(conn)

        assert result[0]['title'] == "Earlier"
        assert result[1]['title'] == "Later"

    def test_should_return_empty_when_all_preached(self):
        """Test returning empty when all sermons preached."""
        from confirm_preached import get_unpreached_sermons

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_preached_record(conn, sermon_id)

        result = get_unpreached_sermons(conn)

        assert result == []


class TestCheckDuplicatePreaching:
    """Tests for check_duplicate_preaching function."""

    def test_should_detect_duplicate_on_same_date(self):
        """Test detecting same sermon preached on same date."""
        from confirm_preached import check_duplicate_preaching

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_preached_record(conn, sermon_id, preached_date="2024-03-17")

        result = check_duplicate_preaching(conn, sermon_id, "2024-03-17")

        assert result['is_duplicate'] is True

    def test_should_not_detect_duplicate_for_different_date(self):
        """Test no duplicate for different dates."""
        from confirm_preached import check_duplicate_preaching

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="approved")

        result = check_duplicate_preaching(conn, sermon_id, "2024-03-17")

        assert result['is_duplicate'] is False

    def test_should_warn_for_nearby_date(self):
        """Test warning when preaching near existing date."""
        from confirm_preached import check_duplicate_preaching

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_preached_record(conn, sermon_id, preached_date="2024-03-17")

        result = check_duplicate_preaching(conn, sermon_id, "2024-03-24")

        assert result['has_warning'] is True
        assert 'nearby' in result.get('warning', '').lower() or 'previous' in result.get('warning', '').lower()

    def test_should_include_existing_preached_dates(self):
        """Test including existing preached dates in response."""
        from confirm_preached import check_duplicate_preaching

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_preached_record(conn, sermon_id, preached_date="2024-03-17")

        result = check_duplicate_preaching(conn, sermon_id, "2024-03-24")

        assert 'existing_dates' in result
        assert "2024-03-17" in result['existing_dates']


class TestGeneratePreachedReceipt:
    """Tests for generate_preached_receipt function."""

    def test_should_generate_receipt(self):
        """Test generating a preached receipt."""
        from confirm_preached import generate_preached_receipt

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, title="Test Sermon",
                                        scripture="John 3:16", status="preached")
        insert_preached_record(conn, sermon_id, preached_date="2024-03-17",
                              confirmed_by="Pastor Katie")

        result = generate_preached_receipt(conn, sermon_id)

        assert result is not None
        assert result['title'] == "Test Sermon"
        assert result['preached_date'] == "2024-03-17"

    def test_should_include_sermon_details_in_receipt(self):
        """Test including full sermon details in receipt."""
        from confirm_preached import generate_preached_receipt

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, title="Test Sermon",
                                        scripture="John 3:16", status="preached")
        insert_preached_record(conn, sermon_id, preached_date="2024-03-17")

        result = generate_preached_receipt(conn, sermon_id)

        assert result['scripture'] == "John 3:16"

    def test_should_include_confirmation_details(self):
        """Test including confirmation details in receipt."""
        from confirm_preached import generate_preached_receipt

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_preached_record(conn, sermon_id, confirmed_by="Pastor Katie")

        result = generate_preached_receipt(conn, sermon_id)

        assert result['confirmed_by'] == "Pastor Katie"
        assert 'confirmed_at' in result

    def test_should_return_none_for_unpreached_sermon(self):
        """Test returning None for unpreached sermon."""
        from confirm_preached import generate_preached_receipt

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="approved")

        result = generate_preached_receipt(conn, sermon_id)

        assert result is None

    def test_should_return_none_for_nonexistent_sermon(self):
        """Test returning None for non-existent sermon."""
        from confirm_preached import generate_preached_receipt

        conn = create_test_db()

        result = generate_preached_receipt(conn, 9999)

        assert result is None


class TestGetPreachingHistory:
    """Tests for get_preaching_history function."""

    def test_should_get_status_history(self):
        """Test getting status change history."""
        from confirm_preached import get_preaching_history

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_status_history(conn, sermon_id, "draft", "approved")
        insert_status_history(conn, sermon_id, "approved", "preached")

        result = get_preaching_history(conn, sermon_id)

        assert len(result) >= 2

    def test_should_order_history_chronologically(self):
        """Test history ordered by time."""
        from confirm_preached import get_preaching_history

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_status_history(conn, sermon_id, "draft", "approved")
        insert_status_history(conn, sermon_id, "approved", "preached")

        result = get_preaching_history(conn, sermon_id)

        # First entry should be earliest status change
        assert result[0]['old_status'] == "draft"
        assert result[0]['new_status'] == "approved"

    def test_should_include_changed_by(self):
        """Test including who made the change."""
        from confirm_preached import get_preaching_history

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_status_history(conn, sermon_id, "approved", "preached",
                             changed_by="Pastor Katie")

        result = get_preaching_history(conn, sermon_id)

        assert result[0]['changed_by'] == "Pastor Katie"

    def test_should_return_empty_for_no_history(self):
        """Test returning empty for sermon without history."""
        from confirm_preached import get_preaching_history

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = get_preaching_history(conn, sermon_id)

        assert result == []


class TestEdgeCases:
    """Tests for edge cases in confirm preached functionality."""

    def test_should_handle_future_preached_date(self):
        """Test handling future date for preaching."""
        from confirm_preached import mark_as_preached

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="approved")
        future_date = (date.today() + timedelta(days=30)).isoformat()

        result = mark_as_preached(conn, sermon_id, future_date)

        # Should warn about future date but allow it (for scheduling)
        assert result is not None
        if 'warning' in result:
            assert 'future' in result['warning'].lower()

    def test_should_handle_cancelled_sermon(self):
        """Test handling cancelled sermon."""
        from confirm_preached import mark_as_preached

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="cancelled")

        result = mark_as_preached(conn, sermon_id, "2024-03-17")

        # Should reject or warn about cancelled sermon
        assert 'error' in result or 'warning' in result

    def test_should_handle_very_old_preached_date(self):
        """Test handling very old preached date."""
        from confirm_preached import mark_as_preached

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="approved")

        result = mark_as_preached(conn, sermon_id, "2020-01-01")

        # Should allow with possible warning
        assert result is not None
        assert result.get('success', False) is True or 'warning' in result

    def test_should_handle_multiple_preaching_records(self):
        """Test handling sermon preached multiple times (re-preaching)."""
        from confirm_preached import mark_as_preached, list_preached_sermons

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_preached_record(conn, sermon_id, preached_date="2024-03-17")

        # Sermon preached again at different church/event
        result = mark_as_preached(conn, sermon_id, "2024-04-14",
                                 confirmed_by="Guest Preaching")

        # Should allow or warn but track
        assert result is not None

    def test_should_validate_date_format(self):
        """Test validation of date format."""
        from confirm_preached import mark_as_preached

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="approved")

        result = mark_as_preached(conn, sermon_id, "invalid-date")

        assert result['success'] is False
        assert 'error' in result


class TestIntegration:
    """Integration tests for confirm preached workflow."""

    def test_should_complete_full_preaching_workflow(self):
        """Test complete workflow from approved to preached."""
        from confirm_preached import (
            mark_as_preached,
            get_preached_status,
            generate_preached_receipt
        )

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, title="Sunday Sermon",
                                        scripture="Matthew 5:1-12",
                                        status="approved")

        # Mark as preached
        result = mark_as_preached(conn, sermon_id, "2024-03-17",
                                 confirmed_by="Pastor Katie")
        assert result['success'] is True

        # Check status
        status = get_preached_status(conn, sermon_id)
        assert status['is_preached'] is True
        assert status['preached_date'] == "2024-03-17"

        # Generate receipt
        receipt = generate_preached_receipt(conn, sermon_id)
        assert receipt['title'] == "Sunday Sermon"
        assert receipt['preached_date'] == "2024-03-17"

    def test_should_track_sermon_through_status_changes(self):
        """Test tracking sermon through multiple status changes."""
        from confirm_preached import mark_as_preached, get_preaching_history

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="approved")

        # Simulate status history
        insert_status_history(conn, sermon_id, "draft", "review")
        insert_status_history(conn, sermon_id, "review", "approved")

        # Mark as preached
        mark_as_preached(conn, sermon_id, "2024-03-17")
        insert_status_history(conn, sermon_id, "approved", "preached",
                             changed_by="System")

        # Get history
        history = get_preaching_history(conn, sermon_id)

        assert len(history) >= 3
        statuses = [h['new_status'] for h in history]
        assert 'review' in statuses
        assert 'approved' in statuses
        assert 'preached' in statuses
