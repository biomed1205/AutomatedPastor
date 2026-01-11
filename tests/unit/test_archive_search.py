"""
Tests for archive search and filter functionality.

Tests the comprehensive search and filtering capabilities
for the sermon archive including full-text search, date filters,
scripture filters, and saved searches.

TDD: All tests should fail with ModuleNotFoundError until implementation.
NO MOCKS: Uses real SQLite in-memory database.
"""

import sqlite3
import pytest
from datetime import datetime


def create_test_db():
    """Create test database with sermon and related tables."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Sermons table
    cursor.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            scripture TEXT,
            scripture_book TEXT,
            content TEXT,
            status TEXT DEFAULT 'draft',
            preached_date TEXT,
            series_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Series table
    cursor.execute('''
        CREATE TABLE sermon_series (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            start_date TEXT,
            end_date TEXT
        )
    ''')

    # Saved searches table
    cursor.execute('''
        CREATE TABLE saved_searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filter_name TEXT NOT NULL UNIQUE,
            filter_params TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Full-text search virtual table for SQLite FTS5
    cursor.execute('''
        CREATE VIRTUAL TABLE sermons_fts USING fts5(
            title, scripture, content, sermon_id UNINDEXED
        )
    ''')

    conn.commit()
    return conn


def insert_sample_sermon(conn, title="Test Sermon", scripture="John 3:16",
                        scripture_book="John", content="Sermon content here",
                        status="preached", preached_date="2024-03-17",
                        series_id=None):
    """Insert a sample sermon for testing."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sermons (title, scripture, scripture_book, content,
                            status, preached_date, series_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, scripture, scripture_book, content, status, preached_date,
          series_id))
    sermon_id = cursor.lastrowid

    # Also insert into FTS table
    cursor.execute('''
        INSERT INTO sermons_fts (title, scripture, content, sermon_id)
        VALUES (?, ?, ?, ?)
    ''', (title, scripture, content, sermon_id))

    conn.commit()
    return sermon_id


def insert_sample_series(conn, name="Test Series", description="A test series"):
    """Insert a sample series for testing."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sermon_series (name, description)
        VALUES (?, ?)
    ''', (name, description))
    conn.commit()
    return cursor.lastrowid


def insert_saved_search(conn, filter_name, filter_params):
    """Insert a saved search for testing."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO saved_searches (filter_name, filter_params)
        VALUES (?, ?)
    ''', (filter_name, filter_params))
    conn.commit()
    return cursor.lastrowid


class TestSearchSermons:
    """Tests for search_sermons function."""

    def test_should_search_by_title(self):
        """Test searching sermons by title."""
        from archive_search import search_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, title="The Good Shepherd")
        insert_sample_sermon(conn, title="Living Water")

        result = search_sermons(conn, "Shepherd")

        assert len(result) == 1
        assert result[0]['title'] == "The Good Shepherd"

    def test_should_search_by_content(self):
        """Test searching sermons by content."""
        from archive_search import search_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, title="Sermon 1",
                            content="Jesus spoke about forgiveness")
        insert_sample_sermon(conn, title="Sermon 2",
                            content="The parable teaches us about love")

        result = search_sermons(conn, "forgiveness")

        assert len(result) == 1
        assert result[0]['title'] == "Sermon 1"

    def test_should_search_by_scripture(self):
        """Test searching sermons by scripture reference."""
        from archive_search import search_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, title="Sermon 1", scripture="John 3:16")
        insert_sample_sermon(conn, title="Sermon 2", scripture="Matthew 5:1-12")

        result = search_sermons(conn, "John 3:16")

        assert len(result) == 1
        assert result[0]['scripture'] == "John 3:16"

    def test_should_return_empty_for_no_matches(self):
        """Test returning empty when no matches found."""
        from archive_search import search_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, title="Test Sermon")

        result = search_sermons(conn, "nonexistent query")

        assert result == []

    def test_should_search_case_insensitive(self):
        """Test case-insensitive searching."""
        from archive_search import search_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, title="The GOOD Shepherd")

        result = search_sermons(conn, "good shepherd")

        assert len(result) == 1

    def test_should_return_multiple_matches(self):
        """Test returning multiple matching sermons."""
        from archive_search import search_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, title="Grace Part 1",
                            content="Amazing grace discussion")
        insert_sample_sermon(conn, title="Grace Part 2",
                            content="More about grace")

        result = search_sermons(conn, "grace")

        assert len(result) == 2


class TestFilterByDateRange:
    """Tests for filter_by_date_range function."""

    def test_should_filter_by_start_date(self):
        """Test filtering sermons by start date."""
        from archive_search import filter_by_date_range

        conn = create_test_db()
        insert_sample_sermon(conn, title="Old Sermon", preached_date="2024-01-01")
        insert_sample_sermon(conn, title="New Sermon", preached_date="2024-03-01")

        result = filter_by_date_range(conn, start_date="2024-02-01")

        assert len(result) == 1
        assert result[0]['title'] == "New Sermon"

    def test_should_filter_by_end_date(self):
        """Test filtering sermons by end date."""
        from archive_search import filter_by_date_range

        conn = create_test_db()
        insert_sample_sermon(conn, title="Early Sermon", preached_date="2024-01-15")
        insert_sample_sermon(conn, title="Later Sermon", preached_date="2024-03-15")

        result = filter_by_date_range(conn, end_date="2024-02-01")

        assert len(result) == 1
        assert result[0]['title'] == "Early Sermon"

    def test_should_filter_by_date_range(self):
        """Test filtering sermons by date range."""
        from archive_search import filter_by_date_range

        conn = create_test_db()
        insert_sample_sermon(conn, title="Before", preached_date="2024-01-01")
        insert_sample_sermon(conn, title="During", preached_date="2024-02-15")
        insert_sample_sermon(conn, title="After", preached_date="2024-04-01")

        result = filter_by_date_range(conn, start_date="2024-02-01",
                                     end_date="2024-03-01")

        assert len(result) == 1
        assert result[0]['title'] == "During"

    def test_should_return_all_for_no_date_limits(self):
        """Test returning all sermons when no date limits."""
        from archive_search import filter_by_date_range

        conn = create_test_db()
        insert_sample_sermon(conn, title="Sermon 1", preached_date="2024-01-01")
        insert_sample_sermon(conn, title="Sermon 2", preached_date="2024-02-01")

        result = filter_by_date_range(conn)

        assert len(result) == 2

    def test_should_include_dates_on_boundaries(self):
        """Test that dates on boundaries are included."""
        from archive_search import filter_by_date_range

        conn = create_test_db()
        insert_sample_sermon(conn, title="On Start", preached_date="2024-02-01")
        insert_sample_sermon(conn, title="On End", preached_date="2024-02-28")

        result = filter_by_date_range(conn, start_date="2024-02-01",
                                     end_date="2024-02-28")

        assert len(result) == 2


class TestFilterByScriptureBook:
    """Tests for filter_by_scripture_book function."""

    def test_should_filter_by_book(self):
        """Test filtering sermons by scripture book."""
        from archive_search import filter_by_scripture_book

        conn = create_test_db()
        insert_sample_sermon(conn, title="John Sermon", scripture_book="John")
        insert_sample_sermon(conn, title="Matthew Sermon", scripture_book="Matthew")

        result = filter_by_scripture_book(conn, "John")

        assert len(result) == 1
        assert result[0]['title'] == "John Sermon"

    def test_should_handle_multiple_books(self):
        """Test filtering with multiple sermons from same book."""
        from archive_search import filter_by_scripture_book

        conn = create_test_db()
        insert_sample_sermon(conn, title="John 1", scripture_book="John")
        insert_sample_sermon(conn, title="John 2", scripture_book="John")
        insert_sample_sermon(conn, title="Matthew 1", scripture_book="Matthew")

        result = filter_by_scripture_book(conn, "John")

        assert len(result) == 2

    def test_should_return_empty_for_no_matches(self):
        """Test returning empty when no sermons from book."""
        from archive_search import filter_by_scripture_book

        conn = create_test_db()
        insert_sample_sermon(conn, scripture_book="John")

        result = filter_by_scripture_book(conn, "Revelation")

        assert result == []

    def test_should_be_case_insensitive(self):
        """Test case-insensitive book matching."""
        from archive_search import filter_by_scripture_book

        conn = create_test_db()
        insert_sample_sermon(conn, scripture_book="Matthew")

        result = filter_by_scripture_book(conn, "matthew")

        assert len(result) == 1


class TestFilterBySeries:
    """Tests for filter_by_series function."""

    def test_should_filter_by_series_id(self):
        """Test filtering sermons by series ID."""
        from archive_search import filter_by_series

        conn = create_test_db()
        series1 = insert_sample_series(conn, name="Lent Series")
        series2 = insert_sample_series(conn, name="Advent Series")
        insert_sample_sermon(conn, title="Lent 1", series_id=series1)
        insert_sample_sermon(conn, title="Advent 1", series_id=series2)

        result = filter_by_series(conn, series1)

        assert len(result) == 1
        assert result[0]['title'] == "Lent 1"

    def test_should_return_all_in_series(self):
        """Test returning all sermons in a series."""
        from archive_search import filter_by_series

        conn = create_test_db()
        series_id = insert_sample_series(conn, name="Summer Series")
        insert_sample_sermon(conn, title="Week 1", series_id=series_id)
        insert_sample_sermon(conn, title="Week 2", series_id=series_id)
        insert_sample_sermon(conn, title="Other", series_id=None)

        result = filter_by_series(conn, series_id)

        assert len(result) == 2

    def test_should_return_empty_for_nonexistent_series(self):
        """Test returning empty for non-existent series."""
        from archive_search import filter_by_series

        conn = create_test_db()
        insert_sample_sermon(conn, series_id=None)

        result = filter_by_series(conn, 9999)

        assert result == []


class TestFilterByStatus:
    """Tests for filter_by_status function."""

    def test_should_filter_by_status(self):
        """Test filtering sermons by status."""
        from archive_search import filter_by_status

        conn = create_test_db()
        insert_sample_sermon(conn, title="Draft", status="draft")
        insert_sample_sermon(conn, title="Preached", status="preached")

        result = filter_by_status(conn, "preached")

        assert len(result) == 1
        assert result[0]['title'] == "Preached"

    def test_should_handle_multiple_statuses(self):
        """Test filtering with multiple sermons of same status."""
        from archive_search import filter_by_status

        conn = create_test_db()
        insert_sample_sermon(conn, title="Draft 1", status="draft")
        insert_sample_sermon(conn, title="Draft 2", status="draft")
        insert_sample_sermon(conn, title="Approved", status="approved")

        result = filter_by_status(conn, "draft")

        assert len(result) == 2

    def test_should_return_empty_for_no_matching_status(self):
        """Test returning empty when no sermons with status."""
        from archive_search import filter_by_status

        conn = create_test_db()
        insert_sample_sermon(conn, status="draft")

        result = filter_by_status(conn, "archived")

        assert result == []


class TestCombinedFilters:
    """Tests for combined filter functionality."""

    def test_should_combine_search_and_date_filter(self):
        """Test combining text search with date filter."""
        from archive_search import search_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, title="Grace Old", preached_date="2024-01-01",
                            content="Amazing grace")
        insert_sample_sermon(conn, title="Grace New", preached_date="2024-03-01",
                            content="Grace discussion")

        result = search_sermons(conn, "grace", start_date="2024-02-01")

        assert len(result) == 1
        assert result[0]['title'] == "Grace New"

    def test_should_combine_search_and_book_filter(self):
        """Test combining text search with scripture book filter."""
        from archive_search import search_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, title="Love in John", scripture_book="John",
                            content="Love passage")
        insert_sample_sermon(conn, title="Love in Matthew", scripture_book="Matthew",
                            content="Love teaching")

        result = search_sermons(conn, "love", scripture_book="John")

        assert len(result) == 1
        assert result[0]['title'] == "Love in John"

    def test_should_combine_search_and_status_filter(self):
        """Test combining text search with status filter."""
        from archive_search import search_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, title="Grace Draft", status="draft",
                            content="Grace notes")
        insert_sample_sermon(conn, title="Grace Preached", status="preached",
                            content="Grace sermon")

        result = search_sermons(conn, "grace", status="preached")

        assert len(result) == 1
        assert result[0]['title'] == "Grace Preached"

    def test_should_combine_multiple_filters(self):
        """Test combining multiple filters together."""
        from archive_search import search_sermons

        conn = create_test_db()
        series_id = insert_sample_series(conn, name="Love Series")

        insert_sample_sermon(conn, title="Target",
                            scripture_book="John", series_id=series_id,
                            status="preached", preached_date="2024-03-01",
                            content="Love discussion")
        insert_sample_sermon(conn, title="Wrong Book",
                            scripture_book="Matthew", series_id=series_id,
                            status="preached", content="Love")
        insert_sample_sermon(conn, title="Wrong Status",
                            scripture_book="John", series_id=series_id,
                            status="draft", content="Love")

        result = search_sermons(conn, "love",
                               scripture_book="John",
                               status="preached",
                               series_id=series_id)

        assert len(result) == 1
        assert result[0]['title'] == "Target"


class TestSortResults:
    """Tests for sorting search results."""

    def test_should_sort_by_date_descending(self):
        """Test sorting results by date descending."""
        from archive_search import search_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, title="Old", preached_date="2024-01-01",
                            content="Sermon")
        insert_sample_sermon(conn, title="New", preached_date="2024-03-01",
                            content="Sermon")

        result = search_sermons(conn, "sermon", sort_by="date", sort_order="desc")

        assert result[0]['title'] == "New"
        assert result[1]['title'] == "Old"

    def test_should_sort_by_date_ascending(self):
        """Test sorting results by date ascending."""
        from archive_search import search_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, title="Old", preached_date="2024-01-01",
                            content="Sermon")
        insert_sample_sermon(conn, title="New", preached_date="2024-03-01",
                            content="Sermon")

        result = search_sermons(conn, "sermon", sort_by="date", sort_order="asc")

        assert result[0]['title'] == "Old"
        assert result[1]['title'] == "New"

    def test_should_sort_by_title(self):
        """Test sorting results by title."""
        from archive_search import search_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, title="Zebra", content="Sermon")
        insert_sample_sermon(conn, title="Apple", content="Sermon")

        result = search_sermons(conn, "sermon", sort_by="title")

        assert result[0]['title'] == "Apple"
        assert result[1]['title'] == "Zebra"

    def test_should_sort_by_scripture(self):
        """Test sorting results by scripture reference."""
        from archive_search import search_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, title="Sermon 1", scripture="Matthew 5:1",
                            content="Sermon")
        insert_sample_sermon(conn, title="Sermon 2", scripture="John 3:16",
                            content="Sermon")

        result = search_sermons(conn, "sermon", sort_by="scripture")

        assert result[0]['scripture'] == "John 3:16"


class TestSearchWithHighlighting:
    """Tests for search_with_highlighting function."""

    def test_should_return_highlighted_matches(self):
        """Test returning highlighted search matches."""
        from archive_search import search_with_highlighting

        conn = create_test_db()
        insert_sample_sermon(conn, title="Test", content="The grace of God is amazing")

        result = search_with_highlighting(conn, "grace")

        assert len(result) > 0
        assert 'snippet' in result[0] or 'highlight' in result[0]

    def test_should_highlight_in_title(self):
        """Test highlighting matches in title."""
        from archive_search import search_with_highlighting

        conn = create_test_db()
        insert_sample_sermon(conn, title="Amazing Grace", content="Content here")

        result = search_with_highlighting(conn, "grace")

        # Should have some form of highlighting indicator
        assert len(result) > 0

    def test_should_return_context_around_match(self):
        """Test returning context around matched term."""
        from archive_search import search_with_highlighting

        conn = create_test_db()
        long_content = "This is a long sermon about " + "text " * 50 + "grace " + "more " * 50
        insert_sample_sermon(conn, title="Long Sermon", content=long_content)

        result = search_with_highlighting(conn, "grace")

        assert len(result) > 0
        # Should include surrounding context

    def test_should_handle_multiple_matches(self):
        """Test handling multiple matches in same sermon."""
        from archive_search import search_with_highlighting

        conn = create_test_db()
        insert_sample_sermon(conn, title="Grace Upon Grace",
                            content="Grace is the foundation of grace-filled living")

        result = search_with_highlighting(conn, "grace")

        assert len(result) > 0


class TestGetSearchSuggestions:
    """Tests for get_search_suggestions function."""

    def test_should_suggest_matching_titles(self):
        """Test suggesting titles matching partial query."""
        from archive_search import get_search_suggestions

        conn = create_test_db()
        insert_sample_sermon(conn, title="The Good Shepherd")
        insert_sample_sermon(conn, title="Living Water")

        result = get_search_suggestions(conn, "good")

        assert len(result) > 0
        assert any("Good" in s for s in result)

    def test_should_suggest_matching_scriptures(self):
        """Test suggesting scripture references."""
        from archive_search import get_search_suggestions

        conn = create_test_db()
        insert_sample_sermon(conn, scripture="John 3:16")
        insert_sample_sermon(conn, scripture="John 14:6")

        result = get_search_suggestions(conn, "john")

        assert len(result) > 0

    def test_should_limit_suggestions(self):
        """Test limiting number of suggestions."""
        from archive_search import get_search_suggestions

        conn = create_test_db()
        for i in range(20):
            insert_sample_sermon(conn, title=f"Grace Sermon {i}")

        result = get_search_suggestions(conn, "grace", limit=5)

        assert len(result) <= 5

    def test_should_return_empty_for_no_matches(self):
        """Test returning empty for no matching suggestions."""
        from archive_search import get_search_suggestions

        conn = create_test_db()
        insert_sample_sermon(conn, title="Test Sermon")

        result = get_search_suggestions(conn, "xyz123")

        assert result == []


class TestSaveSearchFilter:
    """Tests for save_search_filter function."""

    def test_should_save_filter(self):
        """Test saving a search filter."""
        from archive_search import save_search_filter

        conn = create_test_db()
        params = {"scripture_book": "John", "status": "preached"}

        result = save_search_filter(conn, "John Preached", params)

        assert result['success'] is True
        assert result['filter_id'] is not None

    def test_should_store_filter_params(self):
        """Test that filter parameters are stored correctly."""
        from archive_search import save_search_filter

        conn = create_test_db()
        params = {"start_date": "2024-01-01", "end_date": "2024-12-31"}

        save_search_filter(conn, "Year 2024", params)

        cursor = conn.cursor()
        cursor.execute('SELECT filter_params FROM saved_searches WHERE filter_name = ?',
                      ("Year 2024",))
        row = cursor.fetchone()
        assert row is not None

    def test_should_reject_duplicate_names(self):
        """Test rejecting duplicate filter names."""
        from archive_search import save_search_filter

        conn = create_test_db()
        save_search_filter(conn, "My Filter", {"status": "draft"})

        result = save_search_filter(conn, "My Filter", {"status": "preached"})

        assert result['success'] is False

    def test_should_allow_update_existing(self):
        """Test updating existing saved filter."""
        from archive_search import save_search_filter

        conn = create_test_db()
        save_search_filter(conn, "My Filter", {"status": "draft"})

        result = save_search_filter(conn, "My Filter", {"status": "preached"},
                                   update_existing=True)

        assert result['success'] is True


class TestLoadSavedFilter:
    """Tests for load_saved_filter function."""

    def test_should_load_saved_filter(self):
        """Test loading a saved filter."""
        from archive_search import save_search_filter, load_saved_filter

        conn = create_test_db()
        params = {"scripture_book": "Matthew", "status": "preached"}
        save_search_filter(conn, "Matthew Preached", params)

        result = load_saved_filter(conn, "Matthew Preached")

        assert result is not None
        assert result['scripture_book'] == "Matthew"
        assert result['status'] == "preached"

    def test_should_return_none_for_nonexistent(self):
        """Test returning None for non-existent filter."""
        from archive_search import load_saved_filter

        conn = create_test_db()

        result = load_saved_filter(conn, "Nonexistent Filter")

        assert result is None

    def test_should_use_loaded_filter_in_search(self):
        """Test using loaded filter in search."""
        from archive_search import (save_search_filter, load_saved_filter,
                                    search_sermons)

        conn = create_test_db()
        insert_sample_sermon(conn, title="Target", scripture_book="John",
                            status="preached", content="Love message")
        insert_sample_sermon(conn, title="Wrong", scripture_book="Matthew",
                            status="draft", content="Love message")

        params = {"scripture_book": "John", "status": "preached"}
        save_search_filter(conn, "John Preached", params)

        loaded = load_saved_filter(conn, "John Preached")
        result = search_sermons(conn, "love", **loaded)

        assert len(result) == 1
        assert result[0]['title'] == "Target"


class TestEdgeCases:
    """Tests for edge cases in archive search."""

    def test_should_handle_empty_search_query(self):
        """Test handling empty search query."""
        from archive_search import search_sermons

        conn = create_test_db()
        insert_sample_sermon(conn)

        result = search_sermons(conn, "")

        # Should return all or none depending on implementation
        assert isinstance(result, list)

    def test_should_handle_special_characters(self):
        """Test handling special characters in query."""
        from archive_search import search_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, title="What's Next?", content="Test content")

        result = search_sermons(conn, "What's")

        # Should handle without error
        assert isinstance(result, list)

    def test_should_handle_very_long_query(self):
        """Test handling very long search query."""
        from archive_search import search_sermons

        conn = create_test_db()
        insert_sample_sermon(conn)
        long_query = "word " * 100

        result = search_sermons(conn, long_query)

        assert isinstance(result, list)

    def test_should_handle_unicode_query(self):
        """Test handling unicode characters in query."""
        from archive_search import search_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, title="Love \u2764\ufe0f", content="Heart content")

        result = search_sermons(conn, "\u2764")

        assert isinstance(result, list)

    def test_should_handle_no_sermons(self):
        """Test handling empty database."""
        from archive_search import search_sermons

        conn = create_test_db()

        result = search_sermons(conn, "anything")

        assert result == []

    def test_should_handle_invalid_date_format(self):
        """Test handling invalid date format in filter."""
        from archive_search import filter_by_date_range

        conn = create_test_db()
        insert_sample_sermon(conn)

        result = filter_by_date_range(conn, start_date="invalid-date")

        # Should handle gracefully
        assert isinstance(result, (list, dict))


class TestIntegration:
    """Integration tests for archive search."""

    def test_should_complete_search_workflow(self):
        """Test complete search and filter workflow."""
        from archive_search import (
            search_sermons,
            save_search_filter,
            load_saved_filter,
            get_search_suggestions
        )

        conn = create_test_db()

        # Create series
        series_id = insert_sample_series(conn, name="Grace Series")

        # Add sermons
        insert_sample_sermon(conn, title="Grace Part 1",
                            scripture_book="John", status="preached",
                            preached_date="2024-03-01", series_id=series_id,
                            content="First part of grace discussion")
        insert_sample_sermon(conn, title="Grace Part 2",
                            scripture_book="John", status="preached",
                            preached_date="2024-03-08", series_id=series_id,
                            content="Second part about grace")
        insert_sample_sermon(conn, title="Other Sermon",
                            scripture_book="Matthew", status="draft",
                            content="Different topic")

        # Get suggestions
        suggestions = get_search_suggestions(conn, "gra")
        assert len(suggestions) > 0

        # Search with filters
        results = search_sermons(conn, "grace",
                                scripture_book="John",
                                status="preached",
                                series_id=series_id)
        assert len(results) == 2

        # Save filter
        params = {"scripture_book": "John", "status": "preached", "series_id": series_id}
        save_search_filter(conn, "Grace Series Filter", params)

        # Load and use filter
        loaded = load_saved_filter(conn, "Grace Series Filter")
        assert loaded is not None

    def test_should_handle_complex_search_scenario(self):
        """Test complex search with multiple filters and sorting."""
        from archive_search import search_sermons, search_with_highlighting

        conn = create_test_db()
        series_id = insert_sample_series(conn, name="Lent")

        # Create multiple sermons
        for i in range(10):
            insert_sample_sermon(
                conn,
                title=f"Lent Week {i+1}",
                scripture_book="Matthew" if i % 2 == 0 else "John",
                status="preached",
                preached_date=f"2024-03-{(i+1):02d}",
                series_id=series_id,
                content=f"Week {i+1} lenten reflection on grace and love"
            )

        # Complex search
        results = search_sermons(
            conn, "grace",
            scripture_book="Matthew",
            series_id=series_id,
            start_date="2024-03-01",
            end_date="2024-03-15",
            sort_by="date",
            sort_order="desc"
        )

        assert len(results) > 0

        # Search with highlighting
        highlighted = search_with_highlighting(conn, "grace")
        assert len(highlighted) > 0
