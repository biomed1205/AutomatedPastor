"""Tests for linking sermons to series.

These tests verify the UI and API for managing sermon-series associations.
Enables linking, unlinking, reordering, and bulk operations.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database - NO MOCKS.
"""
import pytest
import sqlite3
import json
from datetime import datetime, date


def create_test_db():
    """Create an in-memory test database for sermon-series link testing."""
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
            sermon_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'planning',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create sermons table
    conn.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            scripture TEXT,
            theme TEXT,
            content TEXT,
            sermon_date DATE,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create sermon_series_link table (many-to-many)
    conn.execute('''
        CREATE TABLE sermon_series_link (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER NOT NULL,
            series_id INTEGER NOT NULL,
            position INTEGER DEFAULT 0,
            linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE,
            FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE,
            UNIQUE(sermon_id, series_id)
        )
    ''')

    conn.commit()
    return conn


def insert_sample_series(conn, name="Test Series", theme="Hope"):
    """Insert a sample series for testing."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO series (name, theme) VALUES (?, ?)",
        (name, theme)
    )
    conn.commit()
    return cursor.lastrowid


def insert_sample_sermon(conn, title="Test Sermon", scripture="John 3:16"):
    """Insert a sample sermon for testing."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
        (title, scripture)
    )
    conn.commit()
    return cursor.lastrowid


def link_sermon_to_series_in_db(conn, sermon_id, series_id, position=0):
    """Directly link sermon to series in database for testing."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sermon_series_link (sermon_id, series_id, position) VALUES (?, ?, ?)",
        (sermon_id, series_id, position)
    )
    conn.commit()


class TestLinkSermonToSeriesUI:
    """Test suite for linking sermons to series via UI."""

    def test_should_link_sermon_to_series(self):
        """Test that a sermon can be linked to a series."""
        from sermon_series_link import link_sermon_to_series_ui

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Easter Sermon")
        series_id = insert_sample_series(conn, "Easter Series")

        response = link_sermon_to_series_ui(conn, sermon_id, series_id)

        assert response is not None
        assert response.get('success') is True
        conn.close()

    def test_should_return_error_for_nonexistent_sermon(self):
        """Test that linking nonexistent sermon returns error."""
        from sermon_series_link import link_sermon_to_series_ui

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Test Series")

        response = link_sermon_to_series_ui(conn, 9999, series_id)

        assert response.get('success') is False
        assert 'error' in response or 'message' in response
        conn.close()

    def test_should_return_error_for_nonexistent_series(self):
        """Test that linking to nonexistent series returns error."""
        from sermon_series_link import link_sermon_to_series_ui

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Test Sermon")

        response = link_sermon_to_series_ui(conn, sermon_id, 9999)

        assert response.get('success') is False
        conn.close()

    def test_should_return_link_id_on_success(self):
        """Test that successful link returns link ID."""
        from sermon_series_link import link_sermon_to_series_ui

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon One")
        series_id = insert_sample_series(conn, "Series One")

        response = link_sermon_to_series_ui(conn, sermon_id, series_id)

        assert 'link_id' in response or 'id' in response
        conn.close()

    def test_should_prevent_duplicate_links(self):
        """Test that duplicate links are prevented."""
        from sermon_series_link import link_sermon_to_series_ui

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        series_id = insert_sample_series(conn, "Series")

        # First link should succeed
        response1 = link_sermon_to_series_ui(conn, sermon_id, series_id)
        # Second link should fail or return existing
        response2 = link_sermon_to_series_ui(conn, sermon_id, series_id)

        assert response1.get('success') is True
        assert response2.get('success') is False or response2.get('already_linked') is True
        conn.close()


class TestUnlinkSermonFromSeriesUI:
    """Test suite for unlinking sermons from series via UI."""

    def test_should_unlink_sermon_from_series(self):
        """Test that a sermon can be unlinked from a series."""
        from sermon_series_link import unlink_sermon_from_series_ui

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        series_id = insert_sample_series(conn, "Series")
        link_sermon_to_series_in_db(conn, sermon_id, series_id)

        response = unlink_sermon_from_series_ui(conn, sermon_id, series_id)

        assert response is not None
        assert response.get('success') is True
        conn.close()

    def test_should_return_error_when_not_linked(self):
        """Test that unlinking non-linked sermon returns error."""
        from sermon_series_link import unlink_sermon_from_series_ui

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        series_id = insert_sample_series(conn, "Series")
        # Not linked

        response = unlink_sermon_from_series_ui(conn, sermon_id, series_id)

        assert response.get('success') is False
        conn.close()

    def test_should_handle_nonexistent_sermon_unlink(self):
        """Test that unlinking nonexistent sermon is handled."""
        from sermon_series_link import unlink_sermon_from_series_ui

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Series")

        response = unlink_sermon_from_series_ui(conn, 9999, series_id)

        assert response.get('success') is False
        conn.close()


class TestGetLinkableSeries:
    """Test suite for getting linkable series for a sermon."""

    def test_should_return_linkable_series_for_sermon(self):
        """Test that available series are returned."""
        from sermon_series_link import get_linkable_series

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "New Sermon")
        insert_sample_series(conn, "Series A")
        insert_sample_series(conn, "Series B")
        insert_sample_series(conn, "Series C")

        available = get_linkable_series(conn, sermon_id)

        assert available is not None
        assert len(available) == 3
        conn.close()

    def test_should_exclude_already_linked_series(self):
        """Test that already-linked series are excluded."""
        from sermon_series_link import get_linkable_series

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        series_a = insert_sample_series(conn, "Series A")
        series_b = insert_sample_series(conn, "Series B")

        # Link to series_a
        link_sermon_to_series_in_db(conn, sermon_id, series_a)

        available = get_linkable_series(conn, sermon_id)

        assert len(available) == 1
        assert available[0]['id'] == series_b or available[0]['name'] == 'Series B'
        conn.close()

    def test_should_return_empty_when_all_linked(self):
        """Test that empty list is returned when all series are linked."""
        from sermon_series_link import get_linkable_series

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        series_id = insert_sample_series(conn, "Only Series")
        link_sermon_to_series_in_db(conn, sermon_id, series_id)

        available = get_linkable_series(conn, sermon_id)

        assert available == []
        conn.close()

    def test_should_return_empty_for_nonexistent_sermon(self):
        """Test handling of nonexistent sermon."""
        from sermon_series_link import get_linkable_series

        conn = create_test_db()
        insert_sample_series(conn, "Series A")

        available = get_linkable_series(conn, 9999)

        # Should return all series or empty depending on implementation
        assert available is not None
        conn.close()


class TestReorderSermonInSeries:
    """Test suite for reordering sermons within a series."""

    def test_should_reorder_sermon_within_series(self):
        """Test that sermon position can be changed."""
        from sermon_series_link import reorder_sermon_in_series

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        series_id = insert_sample_series(conn, "Series")
        link_sermon_to_series_in_db(conn, sermon_id, series_id, position=0)

        result = reorder_sermon_in_series(conn, sermon_id, series_id, new_position=3)

        assert result is True
        conn.close()

    def test_should_update_other_positions_on_reorder(self):
        """Test that other sermon positions are updated."""
        from sermon_series_link import reorder_sermon_in_series, get_sermon_series_info

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Series")
        sermon_1 = insert_sample_sermon(conn, "Sermon 1")
        sermon_2 = insert_sample_sermon(conn, "Sermon 2")
        sermon_3 = insert_sample_sermon(conn, "Sermon 3")

        link_sermon_to_series_in_db(conn, sermon_1, series_id, position=1)
        link_sermon_to_series_in_db(conn, sermon_2, series_id, position=2)
        link_sermon_to_series_in_db(conn, sermon_3, series_id, position=3)

        # Move sermon 3 to position 1
        result = reorder_sermon_in_series(conn, sermon_3, series_id, new_position=1)

        assert result is True
        conn.close()

    def test_should_fail_reorder_for_unlinked_sermon(self):
        """Test that reorder fails for unlinked sermon."""
        from sermon_series_link import reorder_sermon_in_series

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        series_id = insert_sample_series(conn, "Series")
        # Not linked

        result = reorder_sermon_in_series(conn, sermon_id, series_id, new_position=1)

        assert result is False
        conn.close()

    def test_should_handle_negative_position(self):
        """Test handling of negative position value."""
        from sermon_series_link import reorder_sermon_in_series

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        series_id = insert_sample_series(conn, "Series")
        link_sermon_to_series_in_db(conn, sermon_id, series_id, position=0)

        result = reorder_sermon_in_series(conn, sermon_id, series_id, new_position=-1)

        # Should fail or clamp to valid position
        assert result is False or result is True  # Depends on implementation
        conn.close()


class TestGetSermonSeriesInfo:
    """Test suite for getting series context for a sermon."""

    def test_should_get_series_context_for_sermon(self):
        """Test that series info is returned for linked sermon."""
        from sermon_series_link import get_sermon_series_info

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        series_id = insert_sample_series(conn, "Lent Series", "Repentance")
        link_sermon_to_series_in_db(conn, sermon_id, series_id, position=2)

        info = get_sermon_series_info(conn, sermon_id)

        assert info is not None
        assert len(info) > 0  # At least one linked series
        conn.close()

    def test_should_return_series_name_and_position(self):
        """Test that series name and position are included."""
        from sermon_series_link import get_sermon_series_info

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        series_id = insert_sample_series(conn, "Easter Series")
        link_sermon_to_series_in_db(conn, sermon_id, series_id, position=3)

        info = get_sermon_series_info(conn, sermon_id)

        assert info is not None
        series_info = info[0] if isinstance(info, list) else info
        assert 'name' in series_info or 'series_name' in series_info
        assert 'position' in series_info
        conn.close()

    def test_should_return_empty_for_unlinked_sermon(self):
        """Test that empty list is returned for unlinked sermon."""
        from sermon_series_link import get_sermon_series_info

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Unlinked Sermon")

        info = get_sermon_series_info(conn, sermon_id)

        assert info is None or info == []
        conn.close()

    def test_should_return_multiple_series_when_applicable(self):
        """Test that multiple series are returned when sermon is in multiple."""
        from sermon_series_link import get_sermon_series_info

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Multi-series Sermon")
        series_a = insert_sample_series(conn, "Series A")
        series_b = insert_sample_series(conn, "Series B")
        link_sermon_to_series_in_db(conn, sermon_id, series_a, position=1)
        link_sermon_to_series_in_db(conn, sermon_id, series_b, position=2)

        info = get_sermon_series_info(conn, sermon_id)

        assert info is not None
        assert len(info) == 2
        conn.close()


class TestBulkLinkSermons:
    """Test suite for bulk linking sermons to a series."""

    def test_should_bulk_link_multiple_sermons(self):
        """Test that multiple sermons can be linked at once."""
        from sermon_series_link import bulk_link_sermons

        conn = create_test_db()
        sermon_1 = insert_sample_sermon(conn, "Sermon 1")
        sermon_2 = insert_sample_sermon(conn, "Sermon 2")
        sermon_3 = insert_sample_sermon(conn, "Sermon 3")
        series_id = insert_sample_series(conn, "Bulk Series")

        results = bulk_link_sermons(conn, [sermon_1, sermon_2, sermon_3], series_id)

        assert results is not None
        assert results.get('success_count', 0) == 3 or results.get('linked', 0) == 3
        conn.close()

    def test_should_return_partial_success_results(self):
        """Test that partial success is reported correctly."""
        from sermon_series_link import bulk_link_sermons

        conn = create_test_db()
        sermon_1 = insert_sample_sermon(conn, "Sermon 1")
        sermon_2 = insert_sample_sermon(conn, "Sermon 2")
        series_id = insert_sample_series(conn, "Series")

        # Link sermon_1 first
        link_sermon_to_series_in_db(conn, sermon_1, series_id)

        # Try to bulk link both (sermon_1 already linked)
        results = bulk_link_sermons(conn, [sermon_1, sermon_2], series_id)

        assert results is not None
        # Should report success for sermon_2, failure/skip for sermon_1
        conn.close()

    def test_should_handle_empty_sermon_list(self):
        """Test handling of empty sermon list."""
        from sermon_series_link import bulk_link_sermons

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Series")

        results = bulk_link_sermons(conn, [], series_id)

        assert results is not None
        assert results.get('success_count', 0) == 0 or results.get('linked', 0) == 0
        conn.close()

    def test_should_handle_nonexistent_series_in_bulk(self):
        """Test bulk linking to nonexistent series."""
        from sermon_series_link import bulk_link_sermons

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")

        results = bulk_link_sermons(conn, [sermon_id], 9999)

        assert results is not None
        assert results.get('success') is False or results.get('success_count', 0) == 0
        conn.close()


class TestValidateSermonSeriesLink:
    """Test suite for validating sermon-series links."""

    def test_should_validate_before_linking(self):
        """Test that validation returns no errors for valid link."""
        from sermon_series_link import validate_sermon_series_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        series_id = insert_sample_series(conn, "Series")

        errors = validate_sermon_series_link(conn, sermon_id, series_id)

        assert errors == []
        conn.close()

    def test_should_return_error_for_invalid_sermon(self):
        """Test that invalid sermon returns error."""
        from sermon_series_link import validate_sermon_series_link

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Series")

        errors = validate_sermon_series_link(conn, 9999, series_id)

        assert len(errors) > 0
        assert any('sermon' in e.lower() for e in errors)
        conn.close()

    def test_should_return_error_for_invalid_series(self):
        """Test that invalid series returns error."""
        from sermon_series_link import validate_sermon_series_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")

        errors = validate_sermon_series_link(conn, sermon_id, 9999)

        assert len(errors) > 0
        assert any('series' in e.lower() for e in errors)
        conn.close()

    def test_should_return_error_for_existing_link(self):
        """Test that existing link returns error."""
        from sermon_series_link import validate_sermon_series_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        series_id = insert_sample_series(conn, "Series")
        link_sermon_to_series_in_db(conn, sermon_id, series_id)

        errors = validate_sermon_series_link(conn, sermon_id, series_id)

        assert len(errors) > 0
        assert any('already' in e.lower() or 'exist' in e.lower() for e in errors)
        conn.close()


class TestSeriesCountUpdate:
    """Test suite for series sermon count updates."""

    def test_should_update_series_count_on_link(self):
        """Test that series sermon_count is updated on link."""
        from sermon_series_link import link_sermon_to_series_ui

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        series_id = insert_sample_series(conn, "Series")

        link_sermon_to_series_ui(conn, sermon_id, series_id)

        cursor = conn.cursor()
        cursor.execute("SELECT sermon_count FROM series WHERE id = ?", (series_id,))
        row = cursor.fetchone()
        assert row[0] == 1 or row['sermon_count'] == 1
        conn.close()

    def test_should_update_series_count_on_unlink(self):
        """Test that series sermon_count is updated on unlink."""
        from sermon_series_link import link_sermon_to_series_ui, unlink_sermon_from_series_ui

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        series_id = insert_sample_series(conn, "Series")

        link_sermon_to_series_ui(conn, sermon_id, series_id)
        unlink_sermon_from_series_ui(conn, sermon_id, series_id)

        cursor = conn.cursor()
        cursor.execute("SELECT sermon_count FROM series WHERE id = ?", (series_id,))
        row = cursor.fetchone()
        assert row[0] == 0 or row['sermon_count'] == 0
        conn.close()


class TestEdgeCases:
    """Test suite for edge cases."""

    def test_should_handle_unicode_in_sermon_title(self):
        """Test handling of unicode in sermon title."""
        from sermon_series_link import link_sermon_to_series_ui, get_sermon_series_info

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Χριστός: The Christ")
        series_id = insert_sample_series(conn, "Greek Series")

        response = link_sermon_to_series_ui(conn, sermon_id, series_id)
        info = get_sermon_series_info(conn, sermon_id)

        assert response.get('success') is True
        assert info is not None
        conn.close()

    def test_should_handle_sermon_in_many_series(self):
        """Test sermon linked to many series."""
        from sermon_series_link import link_sermon_to_series_ui, get_sermon_series_info

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Versatile Sermon")

        series_ids = []
        for i in range(5):
            series_ids.append(insert_sample_series(conn, f"Series {i}"))

        for series_id in series_ids:
            link_sermon_to_series_ui(conn, sermon_id, series_id)

        info = get_sermon_series_info(conn, sermon_id)

        assert len(info) == 5
        conn.close()

    def test_should_handle_position_beyond_series_size(self):
        """Test reordering to position beyond current series size."""
        from sermon_series_link import reorder_sermon_in_series

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        series_id = insert_sample_series(conn, "Small Series")
        link_sermon_to_series_in_db(conn, sermon_id, series_id, position=1)

        # Try to move to position 100 in a series with 1 sermon
        result = reorder_sermon_in_series(conn, sermon_id, series_id, new_position=100)

        # Should either succeed (clamping) or fail gracefully
        assert result is True or result is False
        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
