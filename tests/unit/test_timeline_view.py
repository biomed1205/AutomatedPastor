"""Tests for visual timeline view of sermon series.

These tests verify the timeline display and tracking for sermon series.
Enables visual planning and progress tracking for series.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database - NO MOCKS.
"""
import pytest
import sqlite3
from datetime import datetime, date, timedelta


def create_test_db():
    """Create an in-memory test database for timeline testing."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row

    # Create series table
    conn.execute('''
        CREATE TABLE series (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            theme TEXT,
            start_date DATE,
            end_date DATE,
            status TEXT DEFAULT 'planning',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create sermon_slots table
    conn.execute('''
        CREATE TABLE sermon_slots (
            id INTEGER PRIMARY KEY,
            series_id INTEGER NOT NULL,
            slot_number INTEGER NOT NULL,
            title TEXT,
            scripture TEXT,
            planned_date DATE,
            actual_date DATE,
            status TEXT DEFAULT 'planned',
            FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE
        )
    ''')

    # Create milestones table
    conn.execute('''
        CREATE TABLE series_milestones (
            id INTEGER PRIMARY KEY,
            series_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            milestone_date DATE NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    return conn


def insert_sample_series(conn, name='Test Series', start_date=None, end_date=None):
    """Insert a sample series and return its ID."""
    if start_date is None:
        start_date = date.today().isoformat()
    if end_date is None:
        end_date = (date.today() + timedelta(days=42)).isoformat()

    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO series (name, start_date, end_date, status)
        VALUES (?, ?, ?, ?)
    ''', (name, start_date, end_date, 'active'))
    conn.commit()
    return cursor.lastrowid


def insert_sermon_slots(conn, series_id, count, start_date=None):
    """Insert sermon slots for a series."""
    if start_date is None:
        start_date = date.today()

    cursor = conn.cursor()
    for i in range(count):
        planned = start_date + timedelta(days=7 * i)
        cursor.execute('''
            INSERT INTO sermon_slots (series_id, slot_number, title, planned_date, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (series_id, i + 1, f'Sermon {i + 1}', planned.isoformat(), 'planned'))
    conn.commit()


def complete_sermon_slots(conn, series_id, count):
    """Mark the first 'count' sermon slots as complete."""
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE sermon_slots
        SET status = 'completed', actual_date = planned_date
        WHERE series_id = ? AND slot_number <= ?
    ''', (series_id, count))
    conn.commit()


class TestGetTimelineData:
    """Test suite for getting timeline data."""

    def test_should_get_timeline_data_for_series(self):
        """Test that timeline data is retrieved for a series."""
        from timeline_view import get_timeline_data

        conn = create_test_db()
        series_id = insert_sample_series(conn)
        insert_sermon_slots(conn, series_id, 4)

        timeline = get_timeline_data(conn, series_id)

        assert timeline is not None
        assert 'series_id' in timeline or 'id' in timeline
        conn.close()

    def test_should_include_sermon_dates_in_timeline(self):
        """Test that timeline includes sermon dates."""
        from timeline_view import get_timeline_data

        conn = create_test_db()
        series_id = insert_sample_series(conn)
        insert_sermon_slots(conn, series_id, 4)

        timeline = get_timeline_data(conn, series_id)

        assert 'sermons' in timeline or 'items' in timeline or 'slots' in timeline
        items = timeline.get('sermons', timeline.get('items', timeline.get('slots', [])))
        assert len(items) == 4
        for item in items:
            assert 'planned_date' in item or 'date' in item
        conn.close()

    def test_should_include_series_info_in_timeline(self):
        """Test that timeline includes series information."""
        from timeline_view import get_timeline_data

        conn = create_test_db()
        series_id = insert_sample_series(conn, 'Lent 2024')
        insert_sermon_slots(conn, series_id, 3)

        timeline = get_timeline_data(conn, series_id)

        assert timeline.get('series_name') == 'Lent 2024' or timeline.get('name') == 'Lent 2024'
        conn.close()

    def test_should_handle_nonexistent_series(self):
        """Test that nonexistent series returns None or empty."""
        from timeline_view import get_timeline_data

        conn = create_test_db()

        timeline = get_timeline_data(conn, 999)

        assert timeline is None or timeline == {}
        conn.close()


class TestGetUpcomingSermons:
    """Test suite for getting upcoming sermons."""

    def test_should_get_upcoming_sermons_in_order(self):
        """Test that upcoming sermons are returned in date order."""
        from timeline_view import get_upcoming_sermons

        conn = create_test_db()
        series_id = insert_sample_series(conn)
        insert_sermon_slots(conn, series_id, 6, start_date=date.today())

        upcoming = get_upcoming_sermons(conn, series_id)

        assert len(upcoming) <= 5  # Default limit is 5
        # Should be in chronological order
        for i in range(len(upcoming) - 1):
            date1 = upcoming[i].get('planned_date', upcoming[i].get('date'))
            date2 = upcoming[i + 1].get('planned_date', upcoming[i + 1].get('date'))
            assert date1 <= date2
        conn.close()

    def test_should_respect_limit_parameter(self):
        """Test that limit parameter is respected."""
        from timeline_view import get_upcoming_sermons

        conn = create_test_db()
        series_id = insert_sample_series(conn)
        insert_sermon_slots(conn, series_id, 10, start_date=date.today())

        upcoming = get_upcoming_sermons(conn, series_id, limit=3)

        assert len(upcoming) == 3
        conn.close()

    def test_should_exclude_completed_sermons(self):
        """Test that completed sermons are not in upcoming."""
        from timeline_view import get_upcoming_sermons

        conn = create_test_db()
        series_id = insert_sample_series(conn)
        insert_sermon_slots(conn, series_id, 5, start_date=date.today() - timedelta(days=14))
        complete_sermon_slots(conn, series_id, 2)

        upcoming = get_upcoming_sermons(conn, series_id)

        for sermon in upcoming:
            assert sermon.get('status') != 'completed'
        conn.close()

    def test_should_return_empty_when_all_completed(self):
        """Test that empty list is returned when all completed."""
        from timeline_view import get_upcoming_sermons

        conn = create_test_db()
        series_id = insert_sample_series(conn)
        insert_sermon_slots(conn, series_id, 3, start_date=date.today() - timedelta(days=21))
        complete_sermon_slots(conn, series_id, 3)

        upcoming = get_upcoming_sermons(conn, series_id)

        assert upcoming == []
        conn.close()


class TestGetCompletedSermons:
    """Test suite for getting completed sermons."""

    def test_should_get_completed_sermons(self):
        """Test that completed sermons are retrieved."""
        from timeline_view import get_completed_sermons

        conn = create_test_db()
        series_id = insert_sample_series(conn)
        insert_sermon_slots(conn, series_id, 5, start_date=date.today() - timedelta(days=35))
        complete_sermon_slots(conn, series_id, 3)

        completed = get_completed_sermons(conn, series_id)

        assert len(completed) == 3
        for sermon in completed:
            assert sermon.get('status') == 'completed'
        conn.close()

    def test_should_return_empty_when_none_completed(self):
        """Test that empty list is returned when none completed."""
        from timeline_view import get_completed_sermons

        conn = create_test_db()
        series_id = insert_sample_series(conn)
        insert_sermon_slots(conn, series_id, 4)

        completed = get_completed_sermons(conn, series_id)

        assert completed == []
        conn.close()

    def test_should_order_completed_by_actual_date(self):
        """Test that completed sermons are ordered by actual date."""
        from timeline_view import get_completed_sermons

        conn = create_test_db()
        series_id = insert_sample_series(conn)
        insert_sermon_slots(conn, series_id, 4, start_date=date.today() - timedelta(days=28))
        complete_sermon_slots(conn, series_id, 4)

        completed = get_completed_sermons(conn, series_id)

        for i in range(len(completed) - 1):
            date1 = completed[i].get('actual_date', completed[i].get('date'))
            date2 = completed[i + 1].get('actual_date', completed[i + 1].get('date'))
            assert date1 <= date2
        conn.close()


class TestCalculateSeriesProgress:
    """Test suite for calculating series progress."""

    def test_should_calculate_zero_progress_for_new_series(self):
        """Test that new series has 0% progress."""
        from timeline_view import calculate_series_progress

        conn = create_test_db()
        series_id = insert_sample_series(conn)
        insert_sermon_slots(conn, series_id, 6)

        progress = calculate_series_progress(conn, series_id)

        assert progress == 0
        conn.close()

    def test_should_calculate_partial_progress(self):
        """Test that partial progress is calculated correctly."""
        from timeline_view import calculate_series_progress

        conn = create_test_db()
        series_id = insert_sample_series(conn)
        insert_sermon_slots(conn, series_id, 4, start_date=date.today() - timedelta(days=14))
        complete_sermon_slots(conn, series_id, 2)  # 2 of 4 = 50%

        progress = calculate_series_progress(conn, series_id)

        assert progress == 50
        conn.close()

    def test_should_calculate_complete_progress(self):
        """Test that 100% progress is calculated for completed series."""
        from timeline_view import calculate_series_progress

        conn = create_test_db()
        series_id = insert_sample_series(conn)
        insert_sermon_slots(conn, series_id, 3, start_date=date.today() - timedelta(days=21))
        complete_sermon_slots(conn, series_id, 3)

        progress = calculate_series_progress(conn, series_id)

        assert progress == 100
        conn.close()

    def test_should_handle_empty_series(self):
        """Test that empty series returns 0 progress."""
        from timeline_view import calculate_series_progress

        conn = create_test_db()
        series_id = insert_sample_series(conn)
        # No sermon slots

        progress = calculate_series_progress(conn, series_id)

        assert progress == 0 or progress is None
        conn.close()


class TestGetTimelineForDateRange:
    """Test suite for getting timeline items in date range."""

    def test_should_get_items_in_date_range(self):
        """Test that items in date range are retrieved."""
        from timeline_view import get_timeline_for_date_range

        conn = create_test_db()
        series_id = insert_sample_series(conn)
        start = date.today()
        insert_sermon_slots(conn, series_id, 6, start_date=start)

        # Query a range that includes some sermons
        range_start = start.isoformat()
        range_end = (start + timedelta(days=21)).isoformat()

        items = get_timeline_for_date_range(conn, range_start, range_end)

        assert len(items) >= 3  # Should include at least 3 weekly sermons
        conn.close()

    def test_should_return_empty_for_range_with_no_items(self):
        """Test that empty list is returned for range with no items."""
        from timeline_view import get_timeline_for_date_range

        conn = create_test_db()
        series_id = insert_sample_series(conn)
        insert_sermon_slots(conn, series_id, 4, start_date=date.today())

        # Query a range before any sermons
        range_start = (date.today() - timedelta(days=60)).isoformat()
        range_end = (date.today() - timedelta(days=30)).isoformat()

        items = get_timeline_for_date_range(conn, range_start, range_end)

        assert items == []
        conn.close()

    def test_should_include_items_from_multiple_series(self):
        """Test that items from multiple series are included."""
        from timeline_view import get_timeline_for_date_range

        conn = create_test_db()
        start = date.today()

        series1 = insert_sample_series(conn, 'Series 1')
        series2 = insert_sample_series(conn, 'Series 2')
        insert_sermon_slots(conn, series1, 3, start_date=start)
        insert_sermon_slots(conn, series2, 3, start_date=start)

        range_start = start.isoformat()
        range_end = (start + timedelta(days=14)).isoformat()

        items = get_timeline_for_date_range(conn, range_start, range_end)

        assert len(items) >= 4  # Should include sermons from both series
        conn.close()


class TestMarkSermonComplete:
    """Test suite for marking sermons complete."""

    def test_should_mark_sermon_as_complete(self):
        """Test that sermon can be marked complete."""
        from timeline_view import mark_sermon_complete, get_completed_sermons

        conn = create_test_db()
        series_id = insert_sample_series(conn)
        insert_sermon_slots(conn, series_id, 3)

        # Get first sermon slot ID
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM sermon_slots WHERE series_id = ? LIMIT 1', (series_id,))
        sermon_id = cursor.fetchone()['id']

        result = mark_sermon_complete(conn, sermon_id, date.today().isoformat())

        assert result is True
        completed = get_completed_sermons(conn, series_id)
        assert len(completed) == 1
        conn.close()

    def test_should_set_actual_date_when_completing(self):
        """Test that actual date is set when completing."""
        from timeline_view import mark_sermon_complete

        conn = create_test_db()
        series_id = insert_sample_series(conn)
        insert_sermon_slots(conn, series_id, 1)

        cursor = conn.cursor()
        cursor.execute('SELECT id FROM sermon_slots WHERE series_id = ? LIMIT 1', (series_id,))
        sermon_id = cursor.fetchone()['id']

        actual = date.today().isoformat()
        mark_sermon_complete(conn, sermon_id, actual)

        cursor.execute('SELECT actual_date FROM sermon_slots WHERE id = ?', (sermon_id,))
        row = cursor.fetchone()
        assert row['actual_date'] == actual
        conn.close()

    def test_should_return_false_for_nonexistent_sermon(self):
        """Test that marking nonexistent sermon returns False."""
        from timeline_view import mark_sermon_complete

        conn = create_test_db()

        result = mark_sermon_complete(conn, 999, date.today().isoformat())

        assert result is False
        conn.close()


class TestMilestones:
    """Test suite for series milestones."""

    def test_should_get_milestones_for_series(self):
        """Test that milestones are retrieved for a series."""
        from timeline_view import add_milestone, get_series_milestones

        conn = create_test_db()
        series_id = insert_sample_series(conn)

        add_milestone(conn, series_id, 'Kickoff Event', date.today().isoformat())
        add_milestone(conn, series_id, 'Final Service', (date.today() + timedelta(days=42)).isoformat())

        milestones = get_series_milestones(conn, series_id)

        assert len(milestones) == 2
        conn.close()

    def test_should_add_milestone_to_series(self):
        """Test that milestone can be added to series."""
        from timeline_view import add_milestone

        conn = create_test_db()
        series_id = insert_sample_series(conn)

        milestone_id = add_milestone(conn, series_id, 'Series Launch', date.today().isoformat())

        assert milestone_id is not None
        assert isinstance(milestone_id, int)
        assert milestone_id > 0
        conn.close()

    def test_should_return_milestones_in_date_order(self):
        """Test that milestones are ordered by date."""
        from timeline_view import add_milestone, get_series_milestones

        conn = create_test_db()
        series_id = insert_sample_series(conn)

        # Add in reverse order
        add_milestone(conn, series_id, 'Last', (date.today() + timedelta(days=30)).isoformat())
        add_milestone(conn, series_id, 'First', date.today().isoformat())
        add_milestone(conn, series_id, 'Middle', (date.today() + timedelta(days=15)).isoformat())

        milestones = get_series_milestones(conn, series_id)

        # Should be in date order
        dates = [m['milestone_date'] for m in milestones]
        assert dates == sorted(dates)
        conn.close()

    def test_should_return_empty_for_series_without_milestones(self):
        """Test that empty list is returned when no milestones."""
        from timeline_view import get_series_milestones

        conn = create_test_db()
        series_id = insert_sample_series(conn)

        milestones = get_series_milestones(conn, series_id)

        assert milestones == []
        conn.close()


class TestEdgeCases:
    """Test suite for edge cases."""

    def test_should_handle_series_with_no_slots(self):
        """Test that empty series is handled gracefully."""
        from timeline_view import get_timeline_data

        conn = create_test_db()
        series_id = insert_sample_series(conn)
        # No sermon slots

        timeline = get_timeline_data(conn, series_id)

        assert timeline is not None
        items = timeline.get('sermons', timeline.get('items', timeline.get('slots', [])))
        assert items == []
        conn.close()

    def test_should_handle_dates_spanning_year_boundary(self):
        """Test that dates spanning year boundary work."""
        from timeline_view import get_timeline_data

        conn = create_test_db()
        series_id = insert_sample_series(
            conn,
            start_date='2024-12-01',
            end_date='2025-01-31'
        )
        insert_sermon_slots(conn, series_id, 8, start_date=date(2024, 12, 1))

        timeline = get_timeline_data(conn, series_id)

        assert timeline is not None
        conn.close()

    def test_should_handle_unicode_in_milestone_names(self):
        """Test that unicode in milestone names is preserved."""
        from timeline_view import add_milestone, get_series_milestones

        conn = create_test_db()
        series_id = insert_sample_series(conn)

        add_milestone(conn, series_id, 'Χριστός Event', date.today().isoformat())

        milestones = get_series_milestones(conn, series_id)
        assert 'Χριστός' in milestones[0]['name']
        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
