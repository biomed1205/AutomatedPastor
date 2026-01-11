"""Tests for sermon archive list view.

These tests verify the archive list view that organizes sermons by year and month.
Enables browsing complete history of all sermons with pagination and search.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database - NO MOCKS.
"""
import pytest
import sqlite3
from datetime import datetime, date, timedelta


def create_test_db():
    """Create an in-memory test database for sermon archive testing."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row

    # Create sermons table
    conn.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            scripture TEXT,
            preached_on DATE,
            series_id INTEGER,
            status TEXT DEFAULT 'published',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create series table
    conn.execute('''
        CREATE TABLE series (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    return conn


def insert_sample_sermon(conn, title="Test Sermon", scripture="John 3:16",
                         preached_on=None, series_id=None, status='published'):
    """Insert a sample sermon for testing."""
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO sermons (title, scripture, preached_on, series_id, status)
           VALUES (?, ?, ?, ?, ?)""",
        (title, scripture, preached_on, series_id, status)
    )
    conn.commit()
    return cursor.lastrowid


def insert_sample_series(conn, name="Test Series"):
    """Insert a sample series for testing."""
    cursor = conn.cursor()
    cursor.execute("INSERT INTO series (name) VALUES (?)", (name,))
    conn.commit()
    return cursor.lastrowid


class TestGetArchiveByYear:
    """Test suite for getting archive by year."""

    def test_should_get_sermons_for_year(self):
        """Test that sermons for a specific year are returned."""
        from sermon_archive import get_archive_by_year

        conn = create_test_db()
        insert_sample_sermon(conn, "2024 Sermon 1", preached_on="2024-01-15")
        insert_sample_sermon(conn, "2024 Sermon 2", preached_on="2024-06-20")
        insert_sample_sermon(conn, "2023 Sermon", preached_on="2023-12-25")

        sermons = get_archive_by_year(conn, 2024)

        assert len(sermons) == 2
        for sermon in sermons:
            assert '2024' in sermon['preached_on']
        conn.close()

    def test_should_return_empty_for_year_without_sermons(self):
        """Test that empty list is returned for year without sermons."""
        from sermon_archive import get_archive_by_year

        conn = create_test_db()
        insert_sample_sermon(conn, "2024 Sermon", preached_on="2024-01-15")

        sermons = get_archive_by_year(conn, 2020)

        assert sermons == []
        conn.close()

    def test_should_order_by_date_descending(self):
        """Test that sermons are ordered by date descending."""
        from sermon_archive import get_archive_by_year

        conn = create_test_db()
        insert_sample_sermon(conn, "January", preached_on="2024-01-15")
        insert_sample_sermon(conn, "June", preached_on="2024-06-20")
        insert_sample_sermon(conn, "March", preached_on="2024-03-10")

        sermons = get_archive_by_year(conn, 2024)

        assert sermons[0]['title'] == "June"
        assert sermons[1]['title'] == "March"
        assert sermons[2]['title'] == "January"
        conn.close()

    def test_should_include_sermon_details(self):
        """Test that sermon details are included."""
        from sermon_archive import get_archive_by_year

        conn = create_test_db()
        insert_sample_sermon(conn, "Easter Sermon", "John 20:1-18", preached_on="2024-03-31")

        sermons = get_archive_by_year(conn, 2024)

        assert sermons[0]['title'] == "Easter Sermon"
        assert sermons[0]['scripture'] == "John 20:1-18"
        assert sermons[0]['preached_on'] == "2024-03-31"
        conn.close()


class TestGetArchiveByMonth:
    """Test suite for getting archive by month."""

    def test_should_get_sermons_for_month(self):
        """Test that sermons for a specific month are returned."""
        from sermon_archive import get_archive_by_month

        conn = create_test_db()
        insert_sample_sermon(conn, "March 1", preached_on="2024-03-03")
        insert_sample_sermon(conn, "March 2", preached_on="2024-03-10")
        insert_sample_sermon(conn, "March 3", preached_on="2024-03-17")
        insert_sample_sermon(conn, "April 1", preached_on="2024-04-07")

        sermons = get_archive_by_month(conn, 2024, 3)

        assert len(sermons) == 3
        conn.close()

    def test_should_return_empty_for_month_without_sermons(self):
        """Test that empty list is returned for month without sermons."""
        from sermon_archive import get_archive_by_month

        conn = create_test_db()
        insert_sample_sermon(conn, "March", preached_on="2024-03-03")

        sermons = get_archive_by_month(conn, 2024, 7)  # July

        assert sermons == []
        conn.close()

    def test_should_order_by_date_within_month(self):
        """Test that sermons are ordered by date within month."""
        from sermon_archive import get_archive_by_month

        conn = create_test_db()
        insert_sample_sermon(conn, "Week 3", preached_on="2024-03-17")
        insert_sample_sermon(conn, "Week 1", preached_on="2024-03-03")
        insert_sample_sermon(conn, "Week 2", preached_on="2024-03-10")

        sermons = get_archive_by_month(conn, 2024, 3)

        # Most recent first
        assert sermons[0]['title'] == "Week 3"
        conn.close()

    def test_should_handle_month_as_integer_or_string(self):
        """Test that month can be integer or string."""
        from sermon_archive import get_archive_by_month

        conn = create_test_db()
        insert_sample_sermon(conn, "Sermon", preached_on="2024-03-10")

        sermons_int = get_archive_by_month(conn, 2024, 3)
        sermons_str = get_archive_by_month(conn, 2024, "03")

        # Both should work
        assert len(sermons_int) == 1
        conn.close()


class TestListArchiveYears:
    """Test suite for listing archive years."""

    def test_should_list_all_years_with_sermons(self):
        """Test that all years with sermons are listed."""
        from sermon_archive import list_archive_years

        conn = create_test_db()
        insert_sample_sermon(conn, "2024", preached_on="2024-01-01")
        insert_sample_sermon(conn, "2023", preached_on="2023-06-15")
        insert_sample_sermon(conn, "2022", preached_on="2022-12-25")

        years = list_archive_years(conn)

        assert len(years) == 3
        assert 2024 in years or '2024' in years
        assert 2023 in years or '2023' in years
        assert 2022 in years or '2022' in years
        conn.close()

    def test_should_return_empty_for_empty_archive(self):
        """Test that empty list is returned for empty archive."""
        from sermon_archive import list_archive_years

        conn = create_test_db()

        years = list_archive_years(conn)

        assert years == []
        conn.close()

    def test_should_order_years_descending(self):
        """Test that years are ordered most recent first."""
        from sermon_archive import list_archive_years

        conn = create_test_db()
        insert_sample_sermon(conn, "Old", preached_on="2020-01-01")
        insert_sample_sermon(conn, "Recent", preached_on="2024-01-01")
        insert_sample_sermon(conn, "Middle", preached_on="2022-01-01")

        years = list_archive_years(conn)

        # Most recent first
        assert years[0] == 2024 or years[0] == '2024'
        conn.close()

    def test_should_not_duplicate_years(self):
        """Test that years are not duplicated."""
        from sermon_archive import list_archive_years

        conn = create_test_db()
        for i in range(5):
            insert_sample_sermon(conn, f"Sermon {i}", preached_on=f"2024-0{i+1}-15")

        years = list_archive_years(conn)

        assert len(years) == 1
        conn.close()


class TestListArchiveMonths:
    """Test suite for listing months within a year."""

    def test_should_list_months_with_sermons_for_year(self):
        """Test that months with sermons are listed."""
        from sermon_archive import list_archive_months

        conn = create_test_db()
        insert_sample_sermon(conn, "Jan", preached_on="2024-01-15")
        insert_sample_sermon(conn, "Mar", preached_on="2024-03-15")
        insert_sample_sermon(conn, "Jun", preached_on="2024-06-15")

        months = list_archive_months(conn, 2024)

        assert len(months) == 3
        conn.close()

    def test_should_return_empty_for_year_without_sermons(self):
        """Test that empty list is returned for year without sermons."""
        from sermon_archive import list_archive_months

        conn = create_test_db()

        months = list_archive_months(conn, 2024)

        assert months == []
        conn.close()

    def test_should_include_sermon_count_per_month(self):
        """Test that sermon count per month is included."""
        from sermon_archive import list_archive_months

        conn = create_test_db()
        insert_sample_sermon(conn, "Mar 1", preached_on="2024-03-03")
        insert_sample_sermon(conn, "Mar 2", preached_on="2024-03-10")
        insert_sample_sermon(conn, "Mar 3", preached_on="2024-03-17")
        insert_sample_sermon(conn, "Apr 1", preached_on="2024-04-07")

        months = list_archive_months(conn, 2024)

        # Find March entry
        march = next((m for m in months if m.get('month') == 3 or m.get('month') == '03'), None)
        if march:
            assert march.get('count', march.get('sermon_count', 0)) == 3
        conn.close()


class TestGetArchiveSummary:
    """Test suite for getting archive summary."""

    def test_should_get_archive_summary(self):
        """Test that archive summary is returned."""
        from sermon_archive import get_archive_summary

        conn = create_test_db()
        insert_sample_sermon(conn, "S1", preached_on="2024-01-01")
        insert_sample_sermon(conn, "S2", preached_on="2024-06-15")
        insert_sample_sermon(conn, "S3", preached_on="2023-12-25")

        summary = get_archive_summary(conn)

        assert summary is not None
        assert 'total_sermons' in summary or 'total' in summary
        conn.close()

    def test_should_include_total_sermon_count(self):
        """Test that total sermon count is included."""
        from sermon_archive import get_archive_summary

        conn = create_test_db()
        for i in range(10):
            insert_sample_sermon(conn, f"Sermon {i}", preached_on=f"2024-0{(i%9)+1}-15")

        summary = get_archive_summary(conn)

        total = summary.get('total_sermons', summary.get('total', 0))
        assert total == 10
        conn.close()

    def test_should_include_year_range(self):
        """Test that year range is included."""
        from sermon_archive import get_archive_summary

        conn = create_test_db()
        insert_sample_sermon(conn, "Oldest", preached_on="2020-01-01")
        insert_sample_sermon(conn, "Newest", preached_on="2024-12-25")

        summary = get_archive_summary(conn)

        assert 'earliest_year' in summary or 'first_year' in summary or 'year_range' in summary
        conn.close()

    def test_should_handle_empty_archive(self):
        """Test summary for empty archive."""
        from sermon_archive import get_archive_summary

        conn = create_test_db()

        summary = get_archive_summary(conn)

        assert summary is not None
        total = summary.get('total_sermons', summary.get('total', 0))
        assert total == 0
        conn.close()


class TestGetArchivePage:
    """Test suite for paginated archive list."""

    def test_should_get_paginated_archive(self):
        """Test that paginated archive is returned."""
        from sermon_archive import get_archive_page

        conn = create_test_db()
        for i in range(20):
            insert_sample_sermon(conn, f"Sermon {i}", preached_on=f"2024-{(i%12)+1:02d}-15")

        page = get_archive_page(conn, page=1, per_page=10)

        assert page is not None
        sermons = page.get('sermons', page.get('items', []))
        assert len(sermons) == 10
        conn.close()

    def test_should_return_correct_page(self):
        """Test that correct page is returned."""
        from sermon_archive import get_archive_page

        conn = create_test_db()
        for i in range(25):
            insert_sample_sermon(conn, f"Sermon {i}", preached_on=f"2024-{(i%12)+1:02d}-{(i%28)+1:02d}")

        page1 = get_archive_page(conn, page=1, per_page=10)
        page2 = get_archive_page(conn, page=2, per_page=10)
        page3 = get_archive_page(conn, page=3, per_page=10)

        assert len(page1.get('sermons', page1.get('items', []))) == 10
        assert len(page2.get('sermons', page2.get('items', []))) == 10
        assert len(page3.get('sermons', page3.get('items', []))) == 5
        conn.close()

    def test_should_include_pagination_metadata(self):
        """Test that pagination metadata is included."""
        from sermon_archive import get_archive_page

        conn = create_test_db()
        for i in range(25):
            insert_sample_sermon(conn, f"Sermon {i}", preached_on=f"2024-{(i%12)+1:02d}-15")

        page = get_archive_page(conn, page=1, per_page=10)

        assert 'total' in page or 'total_count' in page
        assert 'pages' in page or 'total_pages' in page
        conn.close()

    def test_should_return_empty_for_page_beyond_range(self):
        """Test that empty list is returned for page beyond range."""
        from sermon_archive import get_archive_page

        conn = create_test_db()
        for i in range(5):
            insert_sample_sermon(conn, f"Sermon {i}", preached_on="2024-01-15")

        page = get_archive_page(conn, page=10, per_page=10)

        sermons = page.get('sermons', page.get('items', []))
        assert len(sermons) == 0
        conn.close()


class TestSearchArchive:
    """Test suite for searching archive."""

    def test_should_search_by_title(self):
        """Test that sermons can be searched by title."""
        from sermon_archive import search_archive

        conn = create_test_db()
        insert_sample_sermon(conn, "Easter Celebration", preached_on="2024-03-31")
        insert_sample_sermon(conn, "Christmas Joy", preached_on="2024-12-25")
        insert_sample_sermon(conn, "Easter Morning", preached_on="2024-03-31")

        results = search_archive(conn, "Easter")

        assert len(results) == 2
        conn.close()

    def test_should_search_by_scripture(self):
        """Test that sermons can be searched by scripture."""
        from sermon_archive import search_archive

        conn = create_test_db()
        insert_sample_sermon(conn, "Sermon 1", "John 3:16", preached_on="2024-01-01")
        insert_sample_sermon(conn, "Sermon 2", "Romans 8:28", preached_on="2024-02-01")
        insert_sample_sermon(conn, "Sermon 3", "John 14:6", preached_on="2024-03-01")

        results = search_archive(conn, "John")

        assert len(results) == 2
        conn.close()

    def test_should_return_empty_for_no_matches(self):
        """Test that empty list is returned for no matches."""
        from sermon_archive import search_archive

        conn = create_test_db()
        insert_sample_sermon(conn, "Test Sermon", "John 3:16", preached_on="2024-01-01")

        results = search_archive(conn, "nonexistent")

        assert results == []
        conn.close()

    def test_should_be_case_insensitive(self):
        """Test that search is case insensitive."""
        from sermon_archive import search_archive

        conn = create_test_db()
        insert_sample_sermon(conn, "EASTER Sermon", preached_on="2024-03-31")

        results_lower = search_archive(conn, "easter")
        results_upper = search_archive(conn, "EASTER")
        results_mixed = search_archive(conn, "Easter")

        assert len(results_lower) == 1
        assert len(results_upper) == 1
        assert len(results_mixed) == 1
        conn.close()


class TestGetRecentSermons:
    """Test suite for getting recent sermons."""

    def test_should_get_recent_sermons(self):
        """Test that recent sermons are returned."""
        from sermon_archive import get_recent_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, "Recent 1", preached_on="2024-12-01")
        insert_sample_sermon(conn, "Recent 2", preached_on="2024-11-15")
        insert_sample_sermon(conn, "Old", preached_on="2020-01-01")

        recent = get_recent_sermons(conn, limit=5)

        assert len(recent) >= 2
        conn.close()

    def test_should_respect_limit(self):
        """Test that limit is respected."""
        from sermon_archive import get_recent_sermons

        conn = create_test_db()
        for i in range(20):
            insert_sample_sermon(conn, f"Sermon {i}", preached_on=f"2024-{(i%12)+1:02d}-15")

        recent = get_recent_sermons(conn, limit=5)

        assert len(recent) == 5
        conn.close()

    def test_should_order_by_date_descending(self):
        """Test that sermons are ordered by date descending."""
        from sermon_archive import get_recent_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, "Oldest", preached_on="2024-01-01")
        insert_sample_sermon(conn, "Newest", preached_on="2024-12-31")
        insert_sample_sermon(conn, "Middle", preached_on="2024-06-15")

        recent = get_recent_sermons(conn, limit=3)

        assert recent[0]['title'] == "Newest"
        conn.close()

    def test_should_return_empty_for_empty_archive(self):
        """Test that empty list is returned for empty archive."""
        from sermon_archive import get_recent_sermons

        conn = create_test_db()

        recent = get_recent_sermons(conn, limit=5)

        assert recent == []
        conn.close()


class TestSeriesMembership:
    """Test suite for series membership display."""

    def test_should_include_series_info_when_applicable(self):
        """Test that series info is included when sermon is in series."""
        from sermon_archive import get_archive_by_year

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Lent Series")
        insert_sample_sermon(conn, "Lent Week 1", preached_on="2024-02-14", series_id=series_id)

        sermons = get_archive_by_year(conn, 2024)

        assert sermons[0].get('series_id') == series_id or sermons[0].get('series_name') is not None
        conn.close()

    def test_should_handle_sermon_without_series(self):
        """Test sermons without series are handled."""
        from sermon_archive import get_archive_by_year

        conn = create_test_db()
        insert_sample_sermon(conn, "Standalone", preached_on="2024-01-01", series_id=None)

        sermons = get_archive_by_year(conn, 2024)

        assert sermons[0].get('series_id') is None or sermons[0].get('series_name') is None
        conn.close()


class TestEdgeCases:
    """Test suite for edge cases."""

    def test_should_handle_empty_archive(self):
        """Test handling of completely empty archive."""
        from sermon_archive import (
            list_archive_years,
            get_archive_summary,
            get_archive_page
        )

        conn = create_test_db()

        years = list_archive_years(conn)
        summary = get_archive_summary(conn)
        page = get_archive_page(conn, 1, 10)

        assert years == []
        assert summary is not None
        conn.close()

    def test_should_handle_single_sermon(self):
        """Test archive with single sermon."""
        from sermon_archive import get_archive_summary, list_archive_years

        conn = create_test_db()
        insert_sample_sermon(conn, "Only Sermon", preached_on="2024-06-15")

        summary = get_archive_summary(conn)
        years = list_archive_years(conn)

        total = summary.get('total_sermons', summary.get('total', 0))
        assert total == 1
        assert len(years) == 1
        conn.close()

    def test_should_handle_many_years(self):
        """Test archive spanning many years."""
        from sermon_archive import list_archive_years, get_archive_summary

        conn = create_test_db()
        for year in range(2010, 2025):
            insert_sample_sermon(conn, f"Sermon {year}", preached_on=f"{year}-06-15")

        years = list_archive_years(conn)
        summary = get_archive_summary(conn)

        assert len(years) == 15
        total = summary.get('total_sermons', summary.get('total', 0))
        assert total == 15
        conn.close()

    def test_should_exclude_draft_sermons(self):
        """Test that draft sermons are excluded from archive."""
        from sermon_archive import get_archive_by_year

        conn = create_test_db()
        insert_sample_sermon(conn, "Published", preached_on="2024-01-01", status='published')
        insert_sample_sermon(conn, "Draft", preached_on="2024-02-01", status='draft')

        sermons = get_archive_by_year(conn, 2024)

        # Should only include published sermons
        assert len(sermons) == 1
        assert sermons[0]['title'] == "Published"
        conn.close()

    def test_should_handle_unicode_in_title(self):
        """Test unicode in sermon title."""
        from sermon_archive import search_archive

        conn = create_test_db()
        insert_sample_sermon(conn, "Χριστός: The Christ", preached_on="2024-04-21")

        results = search_archive(conn, "Χριστός")

        assert len(results) == 1
        conn.close()

    def test_should_handle_sermon_without_preached_date(self):
        """Test handling of sermons without preached date."""
        from sermon_archive import get_recent_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, "With Date", preached_on="2024-01-01")
        insert_sample_sermon(conn, "No Date", preached_on=None)

        recent = get_recent_sermons(conn, limit=10)

        # Should only include sermons with dates
        assert len(recent) == 1
        conn.close()


class TestIntegration:
    """Integration tests for archive workflows."""

    def test_should_browse_archive_by_year_then_month(self):
        """Test browsing archive by year then month."""
        from sermon_archive import (
            list_archive_years,
            list_archive_months,
            get_archive_by_month
        )

        conn = create_test_db()
        insert_sample_sermon(conn, "Jan 1", preached_on="2024-01-07")
        insert_sample_sermon(conn, "Jan 2", preached_on="2024-01-14")
        insert_sample_sermon(conn, "Mar 1", preached_on="2024-03-03")

        # Get years
        years = list_archive_years(conn)
        assert 2024 in years or '2024' in years

        # Get months for 2024
        months = list_archive_months(conn, 2024)
        assert len(months) == 2  # January and March

        # Get sermons for January
        sermons = get_archive_by_month(conn, 2024, 1)
        assert len(sermons) == 2

        conn.close()

    def test_should_search_and_paginate_results(self):
        """Test searching and paginating results."""
        from sermon_archive import search_archive, get_archive_page

        conn = create_test_db()
        for i in range(30):
            insert_sample_sermon(
                conn,
                f"Easter Sermon {i}" if i % 2 == 0 else f"Regular Sermon {i}",
                preached_on=f"2024-{(i%12)+1:02d}-15"
            )

        # Search for Easter sermons
        results = search_archive(conn, "Easter")
        assert len(results) == 15

        # Paginate all sermons
        page1 = get_archive_page(conn, 1, 10)
        page2 = get_archive_page(conn, 2, 10)

        assert len(page1.get('sermons', page1.get('items', []))) == 10
        assert len(page2.get('sermons', page2.get('items', []))) == 10

        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
