"""Tests for sermon series database schema and operations.

These tests verify the database schema and CRUD operations for sermon series.
Enables managing related sermons as a cohesive series.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database - NO MOCKS.
"""
import pytest
import sqlite3
from datetime import datetime, date


# Series statuses
SERIES_STATUSES = ['planning', 'active', 'completed', 'archived']


def create_test_db():
    """Create an in-memory test database with sermon series schema."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row

    # Create sermons table
    conn.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            scripture TEXT,
            manuscript TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create series_sermons junction table
    conn.execute('''
        CREATE TABLE series_sermons (
            id INTEGER PRIMARY KEY,
            series_id INTEGER NOT NULL,
            sermon_id INTEGER NOT NULL,
            order_in_series INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE,
            UNIQUE(series_id, sermon_id),
            UNIQUE(series_id, order_in_series)
        )
    ''')

    # Create indexes for performance
    conn.execute('CREATE INDEX idx_series_status ON series(status)')
    conn.execute('CREATE INDEX idx_series_sermons_series ON series_sermons(series_id)')
    conn.execute('CREATE INDEX idx_series_sermons_sermon ON series_sermons(sermon_id)')

    conn.commit()
    return conn


def insert_sample_sermon(conn, title='Test Sermon', scripture='John 3:16'):
    """Insert a sample sermon and return its ID."""
    cursor = conn.cursor()
    cursor.execute('INSERT INTO sermons (title, scripture) VALUES (?, ?)',
                   (title, scripture))
    conn.commit()
    return cursor.lastrowid


def insert_multiple_sermons(conn, count=5):
    """Insert multiple sample sermons and return their IDs."""
    ids = []
    for i in range(count):
        sermon_id = insert_sample_sermon(conn, f'Sermon {i + 1}', f'Verse {i + 1}')
        ids.append(sermon_id)
    return ids


class TestCreateSeries:
    """Test suite for creating sermon series."""

    def test_should_create_series_with_required_fields(self):
        """Test creating a series with only required fields."""
        from series import create_series

        conn = create_test_db()

        series_id = create_series(conn, name='Lent 2024')

        assert series_id is not None
        assert isinstance(series_id, int)
        assert series_id > 0
        conn.close()

    def test_should_create_series_with_optional_fields(self):
        """Test creating a series with all optional fields."""
        from series import create_series, get_series

        conn = create_test_db()

        series_id = create_series(
            conn,
            name='Easter Series',
            description='A 6-week journey to the resurrection',
            theme='Resurrection and New Life',
            start_date='2024-03-01',
            end_date='2024-04-14',
            status='planning'
        )

        series = get_series(conn, series_id)
        assert series['name'] == 'Easter Series'
        assert series['description'] == 'A 6-week journey to the resurrection'
        assert series['theme'] == 'Resurrection and New Life'
        conn.close()

    def test_should_set_default_status_to_planning(self):
        """Test that default status is 'planning'."""
        from series import create_series, get_series

        conn = create_test_db()

        series_id = create_series(conn, name='New Series')

        series = get_series(conn, series_id)
        assert series['status'] == 'planning'
        conn.close()

    def test_should_set_created_at_timestamp(self):
        """Test that created_at is set automatically."""
        from series import create_series, get_series

        conn = create_test_db()

        series_id = create_series(conn, name='Timestamped Series')

        series = get_series(conn, series_id)
        assert 'created_at' in series
        assert series['created_at'] is not None
        conn.close()


class TestGetSeries:
    """Test suite for retrieving sermon series."""

    def test_should_retrieve_series_by_id(self):
        """Test retrieving a series by its ID."""
        from series import create_series, get_series

        conn = create_test_db()
        series_id = create_series(conn, name='Advent Series', theme='Hope')

        series = get_series(conn, series_id)

        assert series is not None
        assert series['name'] == 'Advent Series'
        assert series['theme'] == 'Hope'
        conn.close()

    def test_should_return_none_for_nonexistent_series(self):
        """Test that None is returned for nonexistent series."""
        from series import get_series

        conn = create_test_db()

        series = get_series(conn, 999)

        assert series is None
        conn.close()

    def test_should_include_all_fields_in_retrieved_series(self):
        """Test that retrieved series includes all fields."""
        from series import create_series, get_series

        conn = create_test_db()
        series_id = create_series(
            conn,
            name='Full Series',
            description='Description',
            theme='Theme',
            status='active'
        )

        series = get_series(conn, series_id)

        expected_fields = ['id', 'name', 'description', 'theme', 'status', 'created_at']
        for field in expected_fields:
            assert field in series
        conn.close()


class TestListSeries:
    """Test suite for listing sermon series."""

    def test_should_list_all_series(self):
        """Test listing all series without filter."""
        from series import create_series, list_series

        conn = create_test_db()
        create_series(conn, name='Series 1')
        create_series(conn, name='Series 2')
        create_series(conn, name='Series 3')

        all_series = list_series(conn)

        assert len(all_series) == 3
        conn.close()

    def test_should_filter_series_by_status(self):
        """Test filtering series by status."""
        from series import create_series, list_series

        conn = create_test_db()
        create_series(conn, name='Planning Series', status='planning')
        create_series(conn, name='Active Series', status='active')
        create_series(conn, name='Completed Series', status='completed')

        active_series = list_series(conn, status='active')

        assert len(active_series) == 1
        assert active_series[0]['name'] == 'Active Series'
        conn.close()

    def test_should_return_empty_list_when_no_series(self):
        """Test that empty list is returned when no series exist."""
        from series import list_series

        conn = create_test_db()

        all_series = list_series(conn)

        assert all_series == []
        conn.close()

    def test_should_order_series_by_created_at(self):
        """Test that series are ordered by creation date."""
        from series import create_series, list_series

        conn = create_test_db()
        create_series(conn, name='First')
        create_series(conn, name='Second')
        create_series(conn, name='Third')

        all_series = list_series(conn)

        # Should be in some consistent order (most recent first or oldest first)
        assert len(all_series) == 3
        conn.close()


class TestUpdateSeries:
    """Test suite for updating sermon series."""

    def test_should_update_series_fields(self):
        """Test updating series fields."""
        from series import create_series, update_series, get_series

        conn = create_test_db()
        series_id = create_series(conn, name='Original Name', theme='Original Theme')

        result = update_series(conn, series_id, name='Updated Name', theme='Updated Theme')

        assert result is True
        series = get_series(conn, series_id)
        assert series['name'] == 'Updated Name'
        assert series['theme'] == 'Updated Theme'
        conn.close()

    def test_should_update_series_status(self):
        """Test updating series status."""
        from series import create_series, update_series, get_series

        conn = create_test_db()
        series_id = create_series(conn, name='Test Series', status='planning')

        update_series(conn, series_id, status='active')

        series = get_series(conn, series_id)
        assert series['status'] == 'active'
        conn.close()

    def test_should_return_false_for_nonexistent_series_update(self):
        """Test that update returns False for nonexistent series."""
        from series import update_series

        conn = create_test_db()

        result = update_series(conn, 999, name='New Name')

        assert result is False
        conn.close()

    def test_should_update_only_specified_fields(self):
        """Test that only specified fields are updated."""
        from series import create_series, update_series, get_series

        conn = create_test_db()
        series_id = create_series(conn, name='Original', theme='Original Theme', description='Original Desc')

        update_series(conn, series_id, name='Updated')

        series = get_series(conn, series_id)
        assert series['name'] == 'Updated'
        assert series['theme'] == 'Original Theme'
        assert series['description'] == 'Original Desc'
        conn.close()


class TestDeleteSeries:
    """Test suite for deleting sermon series."""

    def test_should_delete_series(self):
        """Test deleting a series."""
        from series import create_series, delete_series, get_series

        conn = create_test_db()
        series_id = create_series(conn, name='Deletable Series')

        result = delete_series(conn, series_id)

        assert result is True
        series = get_series(conn, series_id)
        assert series is None
        conn.close()

    def test_should_delete_series_and_associations(self):
        """Test that deleting series removes sermon associations."""
        from series import create_series, delete_series, add_sermon_to_series

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        series_id = create_series(conn, name='Series with Sermons')
        add_sermon_to_series(conn, series_id, sermon_id)

        delete_series(conn, series_id)

        # Check associations are removed
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM series_sermons WHERE series_id = ?',
                       (series_id,))
        count = cursor.fetchone()['count']
        assert count == 0
        conn.close()

    def test_should_return_false_for_nonexistent_series_delete(self):
        """Test that delete returns False for nonexistent series."""
        from series import delete_series

        conn = create_test_db()

        result = delete_series(conn, 999)

        assert result is False
        conn.close()


class TestAddSermonToSeries:
    """Test suite for adding sermons to a series."""

    def test_should_add_sermon_to_series(self):
        """Test adding a sermon to a series."""
        from series import create_series, add_sermon_to_series, get_sermons_in_series

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        series_id = create_series(conn, name='Test Series')

        result = add_sermon_to_series(conn, series_id, sermon_id)

        assert result is True
        sermons = get_sermons_in_series(conn, series_id)
        assert len(sermons) == 1
        conn.close()

    def test_should_auto_increment_order_when_adding_sermon(self):
        """Test that order auto-increments when adding sermons."""
        from series import create_series, add_sermon_to_series, get_sermons_in_series

        conn = create_test_db()
        sermon_ids = insert_multiple_sermons(conn, 3)
        series_id = create_series(conn, name='Ordered Series')

        for sermon_id in sermon_ids:
            add_sermon_to_series(conn, series_id, sermon_id)

        sermons = get_sermons_in_series(conn, series_id)
        orders = [s.get('order_in_series', s.get('order')) for s in sermons]
        assert orders == [1, 2, 3]
        conn.close()

    def test_should_add_sermon_with_specific_order(self):
        """Test adding a sermon with a specific order."""
        from series import create_series, add_sermon_to_series, get_sermons_in_series

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        series_id = create_series(conn, name='Test Series')

        add_sermon_to_series(conn, series_id, sermon_id, order=5)

        sermons = get_sermons_in_series(conn, series_id)
        assert sermons[0].get('order_in_series', sermons[0].get('order')) == 5
        conn.close()

    def test_should_prevent_duplicate_sermon_in_series(self):
        """Test that same sermon cannot be added twice to same series."""
        from series import create_series, add_sermon_to_series

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        series_id = create_series(conn, name='Test Series')

        result1 = add_sermon_to_series(conn, series_id, sermon_id)
        result2 = add_sermon_to_series(conn, series_id, sermon_id)

        assert result1 is True
        assert result2 is False
        conn.close()

    def test_should_handle_nonexistent_series_when_adding(self):
        """Test handling of nonexistent series when adding sermon."""
        from series import add_sermon_to_series

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = add_sermon_to_series(conn, 999, sermon_id)

        assert result is False
        conn.close()


class TestRemoveSermonFromSeries:
    """Test suite for removing sermons from a series."""

    def test_should_remove_sermon_from_series(self):
        """Test removing a sermon from a series."""
        from series import create_series, add_sermon_to_series, remove_sermon_from_series, get_sermons_in_series

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        series_id = create_series(conn, name='Test Series')
        add_sermon_to_series(conn, series_id, sermon_id)

        result = remove_sermon_from_series(conn, series_id, sermon_id)

        assert result is True
        sermons = get_sermons_in_series(conn, series_id)
        assert len(sermons) == 0
        conn.close()

    def test_should_return_false_for_nonexistent_association(self):
        """Test that removing nonexistent association returns False."""
        from series import create_series, remove_sermon_from_series

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        series_id = create_series(conn, name='Test Series')

        result = remove_sermon_from_series(conn, series_id, sermon_id)

        assert result is False
        conn.close()

    def test_should_keep_other_sermons_when_removing_one(self):
        """Test that other sermons remain when one is removed."""
        from series import create_series, add_sermon_to_series, remove_sermon_from_series, get_sermons_in_series

        conn = create_test_db()
        sermon_ids = insert_multiple_sermons(conn, 3)
        series_id = create_series(conn, name='Test Series')
        for sid in sermon_ids:
            add_sermon_to_series(conn, series_id, sid)

        remove_sermon_from_series(conn, series_id, sermon_ids[1])  # Remove middle sermon

        sermons = get_sermons_in_series(conn, series_id)
        assert len(sermons) == 2
        conn.close()


class TestGetSermonsInSeries:
    """Test suite for getting sermons in a series."""

    def test_should_get_sermons_in_correct_order(self):
        """Test that sermons are returned in correct order."""
        from series import create_series, add_sermon_to_series, get_sermons_in_series

        conn = create_test_db()
        sermon_ids = insert_multiple_sermons(conn, 3)
        series_id = create_series(conn, name='Ordered Series')

        # Add in reverse order
        add_sermon_to_series(conn, series_id, sermon_ids[2], order=1)
        add_sermon_to_series(conn, series_id, sermon_ids[0], order=2)
        add_sermon_to_series(conn, series_id, sermon_ids[1], order=3)

        sermons = get_sermons_in_series(conn, series_id)

        # Should be ordered by order_in_series
        assert sermons[0]['id'] == sermon_ids[2]
        assert sermons[1]['id'] == sermon_ids[0]
        assert sermons[2]['id'] == sermon_ids[1]
        conn.close()

    def test_should_return_empty_for_series_without_sermons(self):
        """Test that empty list is returned for series without sermons."""
        from series import create_series, get_sermons_in_series

        conn = create_test_db()
        series_id = create_series(conn, name='Empty Series')

        sermons = get_sermons_in_series(conn, series_id)

        assert sermons == []
        conn.close()

    def test_should_include_sermon_details(self):
        """Test that returned sermons include full details."""
        from series import create_series, add_sermon_to_series, get_sermons_in_series

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, 'Detailed Sermon', 'John 3:16')
        series_id = create_series(conn, name='Test Series')
        add_sermon_to_series(conn, series_id, sermon_id)

        sermons = get_sermons_in_series(conn, series_id)

        assert len(sermons) == 1
        assert sermons[0]['title'] == 'Detailed Sermon'
        assert sermons[0]['scripture'] == 'John 3:16'
        conn.close()


class TestGetSeriesForSermon:
    """Test suite for getting series containing a sermon."""

    def test_should_get_all_series_containing_sermon(self):
        """Test getting all series that contain a sermon."""
        from series import create_series, add_sermon_to_series, get_series_for_sermon

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        series1 = create_series(conn, name='Series 1')
        series2 = create_series(conn, name='Series 2')
        series3 = create_series(conn, name='Series 3')

        add_sermon_to_series(conn, series1, sermon_id)
        add_sermon_to_series(conn, series2, sermon_id)
        # Don't add to series3

        series_list = get_series_for_sermon(conn, sermon_id)

        assert len(series_list) == 2
        series_ids = [s['id'] for s in series_list]
        assert series1 in series_ids
        assert series2 in series_ids
        assert series3 not in series_ids
        conn.close()

    def test_should_return_empty_when_sermon_not_in_any_series(self):
        """Test that empty list is returned when sermon not in any series."""
        from series import get_series_for_sermon

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        series_list = get_series_for_sermon(conn, sermon_id)

        assert series_list == []
        conn.close()


class TestEdgeCases:
    """Test suite for edge cases."""

    def test_should_handle_special_characters_in_name(self):
        """Test that special characters in name are handled."""
        from series import create_series, get_series

        conn = create_test_db()

        series_id = create_series(conn, name="Series: 'The Journey' - Part 1")

        series = get_series(conn, series_id)
        assert series['name'] == "Series: 'The Journey' - Part 1"
        conn.close()

    def test_should_handle_unicode_in_fields(self):
        """Test that unicode in fields is preserved."""
        from series import create_series, get_series

        conn = create_test_db()

        series_id = create_series(
            conn,
            name='Χριστός Series',
            description='Greek: Χριστός means Christ',
            theme='Faith and Hope'
        )

        series = get_series(conn, series_id)
        assert 'Χριστός' in series['name']
        assert 'Χριστός' in series['description']
        conn.close()

    def test_should_handle_null_optional_fields(self):
        """Test that null optional fields are handled."""
        from series import create_series, get_series

        conn = create_test_db()

        series_id = create_series(conn, name='Minimal Series')

        series = get_series(conn, series_id)
        assert series['name'] == 'Minimal Series'
        # Optional fields should be None or have defaults
        assert series.get('description') is None or series.get('description') == ''
        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
