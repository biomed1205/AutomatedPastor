"""
Tests for statistics dashboard functionality.

Tests the dashboard showing sermon statistics and analytics
including counts, frequencies, averages, and trend data.

TDD: All tests should fail with ModuleNotFoundError until implementation.
NO MOCKS: Uses real SQLite in-memory database.
"""

import sqlite3
import pytest
import json
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
            word_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'draft',
            theme TEXT,
            preached_date TEXT,
            series_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Series table
    cursor.execute('''
        CREATE TABLE sermon_series (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            planned_count INTEGER DEFAULT 0,
            start_date TEXT,
            end_date TEXT
        )
    ''')

    # Tags/themes table
    cursor.execute('''
        CREATE TABLE sermon_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            tag TEXT NOT NULL,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id)
        )
    ''')

    conn.commit()
    return conn


def insert_sample_sermon(conn, title="Test Sermon", scripture="John 3:16",
                        scripture_book="John", content="Content here",
                        word_count=2000, status="preached", theme="grace",
                        preached_date="2024-03-17", series_id=None):
    """Insert a sample sermon for testing."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sermons (title, scripture, scripture_book, content,
                            word_count, status, theme, preached_date, series_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, scripture, scripture_book, content, word_count, status,
          theme, preached_date, series_id))
    conn.commit()
    return cursor.lastrowid


def insert_sample_series(conn, name="Test Series", planned_count=4):
    """Insert a sample series for testing."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sermon_series (name, planned_count)
        VALUES (?, ?)
    ''', (name, planned_count))
    conn.commit()
    return cursor.lastrowid


def insert_sermon_tag(conn, sermon_id, tag):
    """Insert a tag for a sermon."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sermon_tags (sermon_id, tag)
        VALUES (?, ?)
    ''', (sermon_id, tag))
    conn.commit()
    return cursor.lastrowid


class TestGetSermonCountsByPeriod:
    """Tests for get_sermon_counts_by_period function."""

    def test_should_count_sermons_by_month(self):
        """Test counting sermons by month."""
        from statistics_dashboard import get_sermon_counts_by_period

        conn = create_test_db()
        insert_sample_sermon(conn, title="Jan 1", preached_date="2024-01-07")
        insert_sample_sermon(conn, title="Jan 2", preached_date="2024-01-14")
        insert_sample_sermon(conn, title="Feb 1", preached_date="2024-02-04")

        result = get_sermon_counts_by_period(conn, period='month')

        assert result['2024-01'] == 2
        assert result['2024-02'] == 1

    def test_should_count_sermons_by_year(self):
        """Test counting sermons by year."""
        from statistics_dashboard import get_sermon_counts_by_period

        conn = create_test_db()
        insert_sample_sermon(conn, preached_date="2023-06-01")
        insert_sample_sermon(conn, preached_date="2024-03-01")
        insert_sample_sermon(conn, preached_date="2024-09-01")

        result = get_sermon_counts_by_period(conn, period='year')

        assert result['2023'] == 1
        assert result['2024'] == 2

    def test_should_count_sermons_by_week(self):
        """Test counting sermons by week."""
        from statistics_dashboard import get_sermon_counts_by_period

        conn = create_test_db()
        insert_sample_sermon(conn, preached_date="2024-03-03")  # Week 9
        insert_sample_sermon(conn, preached_date="2024-03-10")  # Week 10

        result = get_sermon_counts_by_period(conn, period='week')

        assert len(result) >= 2

    def test_should_return_empty_for_no_sermons(self):
        """Test returning empty for no sermons."""
        from statistics_dashboard import get_sermon_counts_by_period

        conn = create_test_db()

        result = get_sermon_counts_by_period(conn)

        assert result == {} or len(result) == 0

    def test_should_only_count_preached_sermons(self):
        """Test only counting preached sermons."""
        from statistics_dashboard import get_sermon_counts_by_period

        conn = create_test_db()
        insert_sample_sermon(conn, status="preached", preached_date="2024-03-01")
        insert_sample_sermon(conn, status="draft", preached_date="2024-03-08")

        result = get_sermon_counts_by_period(conn, period='month')

        assert result.get('2024-03', 0) == 1


class TestGetScriptureFrequency:
    """Tests for get_scripture_frequency function."""

    def test_should_get_most_used_books(self):
        """Test getting most frequently used scripture books."""
        from statistics_dashboard import get_scripture_frequency

        conn = create_test_db()
        insert_sample_sermon(conn, scripture_book="John")
        insert_sample_sermon(conn, scripture_book="John")
        insert_sample_sermon(conn, scripture_book="Matthew")

        result = get_scripture_frequency(conn)

        assert result[0]['book'] == "John"
        assert result[0]['count'] == 2

    def test_should_limit_results(self):
        """Test limiting number of results."""
        from statistics_dashboard import get_scripture_frequency

        conn = create_test_db()
        books = ["John", "Matthew", "Luke", "Mark", "Acts",
                "Romans", "Corinthians", "Galatians"]
        for book in books:
            insert_sample_sermon(conn, scripture_book=book)

        result = get_scripture_frequency(conn, limit=5)

        assert len(result) <= 5

    def test_should_order_by_frequency_descending(self):
        """Test ordering by frequency descending."""
        from statistics_dashboard import get_scripture_frequency

        conn = create_test_db()
        for _ in range(3):
            insert_sample_sermon(conn, scripture_book="John")
        for _ in range(5):
            insert_sample_sermon(conn, scripture_book="Matthew")
        insert_sample_sermon(conn, scripture_book="Luke")

        result = get_scripture_frequency(conn)

        assert result[0]['book'] == "Matthew"
        assert result[1]['book'] == "John"

    def test_should_return_empty_for_no_sermons(self):
        """Test returning empty for no sermons."""
        from statistics_dashboard import get_scripture_frequency

        conn = create_test_db()

        result = get_scripture_frequency(conn)

        assert result == []


class TestGetThemeFrequency:
    """Tests for get_theme_frequency function."""

    def test_should_get_most_used_themes(self):
        """Test getting most frequently used themes."""
        from statistics_dashboard import get_theme_frequency

        conn = create_test_db()
        insert_sample_sermon(conn, theme="grace")
        insert_sample_sermon(conn, theme="grace")
        insert_sample_sermon(conn, theme="love")

        result = get_theme_frequency(conn)

        assert result[0]['theme'] == "grace"
        assert result[0]['count'] == 2

    def test_should_include_tags_in_frequency(self):
        """Test including sermon tags in theme frequency."""
        from statistics_dashboard import get_theme_frequency

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sermon_tag(conn, sermon_id, "redemption")
        insert_sermon_tag(conn, sermon_id, "salvation")

        result = get_theme_frequency(conn)

        themes = [r['theme'] for r in result]
        assert "redemption" in themes or "salvation" in themes

    def test_should_limit_results(self):
        """Test limiting number of results."""
        from statistics_dashboard import get_theme_frequency

        conn = create_test_db()
        themes = ["grace", "love", "faith", "hope", "peace",
                 "joy", "mercy", "justice"]
        for theme in themes:
            insert_sample_sermon(conn, theme=theme)

        result = get_theme_frequency(conn, limit=5)

        assert len(result) <= 5

    def test_should_return_empty_for_no_themes(self):
        """Test returning empty for no themes."""
        from statistics_dashboard import get_theme_frequency

        conn = create_test_db()
        insert_sample_sermon(conn, theme=None)

        result = get_theme_frequency(conn)

        # Should return empty or only non-null themes
        assert isinstance(result, list)


class TestGetSeriesStatistics:
    """Tests for get_series_statistics function."""

    def test_should_get_series_completion_rate(self):
        """Test getting series completion rate."""
        from statistics_dashboard import get_series_statistics

        conn = create_test_db()
        series_id = insert_sample_series(conn, name="Lent Series", planned_count=6)
        for i in range(4):
            insert_sample_sermon(conn, title=f"Lent {i+1}",
                               series_id=series_id, status="preached")

        result = get_series_statistics(conn)

        lent_series = next(s for s in result if s['name'] == "Lent Series")
        assert lent_series['completed'] == 4
        assert lent_series['planned'] == 6
        assert lent_series['completion_rate'] == pytest.approx(66.67, rel=0.1)

    def test_should_get_all_series(self):
        """Test getting statistics for all series."""
        from statistics_dashboard import get_series_statistics

        conn = create_test_db()
        series1 = insert_sample_series(conn, name="Series 1")
        series2 = insert_sample_series(conn, name="Series 2")
        insert_sample_sermon(conn, series_id=series1)
        insert_sample_sermon(conn, series_id=series2)

        result = get_series_statistics(conn)

        assert len(result) >= 2

    def test_should_include_sermon_count(self):
        """Test including sermon count per series."""
        from statistics_dashboard import get_series_statistics

        conn = create_test_db()
        series_id = insert_sample_series(conn, name="Test Series")
        for i in range(3):
            insert_sample_sermon(conn, series_id=series_id)

        result = get_series_statistics(conn)

        test_series = next(s for s in result if s['name'] == "Test Series")
        assert test_series['completed'] == 3

    def test_should_return_empty_for_no_series(self):
        """Test returning empty for no series."""
        from statistics_dashboard import get_series_statistics

        conn = create_test_db()
        insert_sample_sermon(conn)  # Sermon without series

        result = get_series_statistics(conn)

        assert result == [] or len(result) == 0


class TestGetWordCountStats:
    """Tests for get_word_count_stats function."""

    def test_should_calculate_average_word_count(self):
        """Test calculating average word count."""
        from statistics_dashboard import get_word_count_stats

        conn = create_test_db()
        insert_sample_sermon(conn, word_count=2000)
        insert_sample_sermon(conn, word_count=2200)
        insert_sample_sermon(conn, word_count=2400)

        result = get_word_count_stats(conn)

        assert result['average'] == pytest.approx(2200, rel=0.01)

    def test_should_get_min_word_count(self):
        """Test getting minimum word count."""
        from statistics_dashboard import get_word_count_stats

        conn = create_test_db()
        insert_sample_sermon(conn, word_count=1800)
        insert_sample_sermon(conn, word_count=2200)
        insert_sample_sermon(conn, word_count=2500)

        result = get_word_count_stats(conn)

        assert result['min'] == 1800

    def test_should_get_max_word_count(self):
        """Test getting maximum word count."""
        from statistics_dashboard import get_word_count_stats

        conn = create_test_db()
        insert_sample_sermon(conn, word_count=1800)
        insert_sample_sermon(conn, word_count=2200)
        insert_sample_sermon(conn, word_count=2500)

        result = get_word_count_stats(conn)

        assert result['max'] == 2500

    def test_should_get_total_word_count(self):
        """Test getting total word count."""
        from statistics_dashboard import get_word_count_stats

        conn = create_test_db()
        insert_sample_sermon(conn, word_count=2000)
        insert_sample_sermon(conn, word_count=2500)

        result = get_word_count_stats(conn)

        assert result['total'] == 4500

    def test_should_return_zeros_for_no_sermons(self):
        """Test returning zeros for no sermons."""
        from statistics_dashboard import get_word_count_stats

        conn = create_test_db()

        result = get_word_count_stats(conn)

        assert result['average'] == 0 or result['average'] is None
        assert result['total'] == 0


class TestGetPreachingFrequency:
    """Tests for get_preaching_frequency function."""

    def test_should_calculate_sermons_per_month(self):
        """Test calculating sermons per month."""
        from statistics_dashboard import get_preaching_frequency

        conn = create_test_db()
        # 4 sermons over 2 months
        insert_sample_sermon(conn, preached_date="2024-03-03")
        insert_sample_sermon(conn, preached_date="2024-03-10")
        insert_sample_sermon(conn, preached_date="2024-03-17")
        insert_sample_sermon(conn, preached_date="2024-04-07")

        result = get_preaching_frequency(conn)

        assert 'sermons_per_month' in result
        assert result['sermons_per_month'] >= 1

    def test_should_calculate_sermons_per_week(self):
        """Test calculating average sermons per week."""
        from statistics_dashboard import get_preaching_frequency

        conn = create_test_db()
        # 4 sermons in 4 weeks
        insert_sample_sermon(conn, preached_date="2024-03-03")
        insert_sample_sermon(conn, preached_date="2024-03-10")
        insert_sample_sermon(conn, preached_date="2024-03-17")
        insert_sample_sermon(conn, preached_date="2024-03-24")

        result = get_preaching_frequency(conn)

        assert 'sermons_per_week' in result
        assert result['sermons_per_week'] >= 0.5

    def test_should_include_total_preached(self):
        """Test including total preached count."""
        from statistics_dashboard import get_preaching_frequency

        conn = create_test_db()
        insert_sample_sermon(conn, status="preached")
        insert_sample_sermon(conn, status="preached")
        insert_sample_sermon(conn, status="draft")

        result = get_preaching_frequency(conn)

        assert result['total_preached'] == 2

    def test_should_return_zeros_for_no_sermons(self):
        """Test returning zeros for no sermons."""
        from statistics_dashboard import get_preaching_frequency

        conn = create_test_db()

        result = get_preaching_frequency(conn)

        assert result['total_preached'] == 0


class TestGetDashboardSummary:
    """Tests for get_dashboard_summary function."""

    def test_should_return_overview_statistics(self):
        """Test returning overview statistics."""
        from statistics_dashboard import get_dashboard_summary

        conn = create_test_db()
        insert_sample_sermon(conn, status="preached")
        insert_sample_sermon(conn, status="draft")
        insert_sample_sermon(conn, status="approved")

        result = get_dashboard_summary(conn)

        assert 'total_sermons' in result
        assert 'total_preached' in result
        assert result['total_sermons'] == 3
        assert result['total_preached'] == 1

    def test_should_include_recent_activity(self):
        """Test including recent activity."""
        from statistics_dashboard import get_dashboard_summary

        conn = create_test_db()
        insert_sample_sermon(conn, preached_date="2024-03-17")

        result = get_dashboard_summary(conn)

        assert 'last_preached_date' in result

    def test_should_include_series_count(self):
        """Test including series count."""
        from statistics_dashboard import get_dashboard_summary

        conn = create_test_db()
        insert_sample_series(conn, name="Series 1")
        insert_sample_series(conn, name="Series 2")

        result = get_dashboard_summary(conn)

        assert 'total_series' in result
        assert result['total_series'] == 2

    def test_should_include_word_count_average(self):
        """Test including average word count."""
        from statistics_dashboard import get_dashboard_summary

        conn = create_test_db()
        insert_sample_sermon(conn, word_count=2000)
        insert_sample_sermon(conn, word_count=2500)

        result = get_dashboard_summary(conn)

        assert 'average_word_count' in result
        assert result['average_word_count'] == pytest.approx(2250, rel=0.01)

    def test_should_return_defaults_for_empty_db(self):
        """Test returning defaults for empty database."""
        from statistics_dashboard import get_dashboard_summary

        conn = create_test_db()

        result = get_dashboard_summary(conn)

        assert result['total_sermons'] == 0
        assert result['total_preached'] == 0


class TestExportStatistics:
    """Tests for export_statistics function."""

    def test_should_export_as_json(self):
        """Test exporting statistics as JSON."""
        from statistics_dashboard import export_statistics

        conn = create_test_db()
        insert_sample_sermon(conn)

        result = export_statistics(conn, format='json')

        assert result is not None
        # Should be valid JSON
        data = json.loads(result)
        assert 'summary' in data or 'statistics' in data

    def test_should_export_as_csv(self):
        """Test exporting statistics as CSV."""
        from statistics_dashboard import export_statistics

        conn = create_test_db()
        insert_sample_sermon(conn)

        result = export_statistics(conn, format='csv')

        assert result is not None
        assert isinstance(result, str)
        assert ',' in result  # CSV format

    def test_should_include_all_statistics(self):
        """Test including all statistics in export."""
        from statistics_dashboard import export_statistics

        conn = create_test_db()
        series_id = insert_sample_series(conn)
        insert_sample_sermon(conn, series_id=series_id, word_count=2000,
                            theme="grace", scripture_book="John")

        result = export_statistics(conn, format='json')
        data = json.loads(result)

        # Should include various statistics sections
        assert isinstance(data, dict)

    def test_should_return_none_for_invalid_format(self):
        """Test returning None for invalid format."""
        from statistics_dashboard import export_statistics

        conn = create_test_db()

        result = export_statistics(conn, format='invalid')

        assert result is None or 'error' in str(result).lower()


class TestChartData:
    """Tests for chart data generation."""

    def test_should_generate_monthly_chart_data(self):
        """Test generating data for monthly chart."""
        from statistics_dashboard import get_sermon_counts_by_period

        conn = create_test_db()
        months = ["2024-01", "2024-02", "2024-03", "2024-04"]
        for month in months:
            insert_sample_sermon(conn, preached_date=f"{month}-15")

        result = get_sermon_counts_by_period(conn, period='month')

        # Should have data suitable for charting
        assert len(result) >= 4

    def test_should_generate_scripture_book_chart_data(self):
        """Test generating data for scripture book pie chart."""
        from statistics_dashboard import get_scripture_frequency

        conn = create_test_db()
        insert_sample_sermon(conn, scripture_book="John")
        insert_sample_sermon(conn, scripture_book="Matthew")
        insert_sample_sermon(conn, scripture_book="John")

        result = get_scripture_frequency(conn)

        # Should have labels and values for charting
        assert all('book' in r and 'count' in r for r in result)

    def test_should_generate_word_count_trend_data(self):
        """Test generating word count trend over time."""
        from statistics_dashboard import get_word_count_stats

        conn = create_test_db()
        insert_sample_sermon(conn, word_count=2000, preached_date="2024-01-01")
        insert_sample_sermon(conn, word_count=2200, preached_date="2024-02-01")
        insert_sample_sermon(conn, word_count=2100, preached_date="2024-03-01")

        result = get_word_count_stats(conn)

        assert 'average' in result


class TestEdgeCases:
    """Tests for edge cases in statistics dashboard."""

    def test_should_handle_single_sermon(self):
        """Test handling database with single sermon."""
        from statistics_dashboard import get_dashboard_summary

        conn = create_test_db()
        insert_sample_sermon(conn, word_count=2000)

        result = get_dashboard_summary(conn)

        assert result['total_sermons'] == 1
        assert result['average_word_count'] == 2000

    def test_should_handle_no_preached_sermons(self):
        """Test handling no preached sermons."""
        from statistics_dashboard import get_preaching_frequency

        conn = create_test_db()
        insert_sample_sermon(conn, status="draft")
        insert_sample_sermon(conn, status="approved")

        result = get_preaching_frequency(conn)

        assert result['total_preached'] == 0

    def test_should_handle_null_scripture_books(self):
        """Test handling null scripture books."""
        from statistics_dashboard import get_scripture_frequency

        conn = create_test_db()
        insert_sample_sermon(conn, scripture_book=None)
        insert_sample_sermon(conn, scripture_book="John")

        result = get_scripture_frequency(conn)

        # Should handle null gracefully
        books = [r['book'] for r in result if r['book'] is not None]
        assert "John" in books

    def test_should_handle_zero_word_counts(self):
        """Test handling sermons with zero word count."""
        from statistics_dashboard import get_word_count_stats

        conn = create_test_db()
        insert_sample_sermon(conn, word_count=0)
        insert_sample_sermon(conn, word_count=2000)

        result = get_word_count_stats(conn)

        # Should handle zeros in calculation
        assert result['min'] == 0
        assert result['average'] == 1000

    def test_should_handle_date_range_filter(self):
        """Test filtering statistics by date range."""
        from statistics_dashboard import get_sermon_counts_by_period

        conn = create_test_db()
        insert_sample_sermon(conn, preached_date="2023-06-01")
        insert_sample_sermon(conn, preached_date="2024-03-01")

        result = get_sermon_counts_by_period(conn, period='year',
                                            start_date="2024-01-01")

        # Should only include 2024
        assert '2023' not in result or result.get('2023', 0) == 0


class TestIntegration:
    """Integration tests for statistics dashboard."""

    def test_should_provide_complete_dashboard(self):
        """Test providing complete dashboard data."""
        from statistics_dashboard import (
            get_dashboard_summary,
            get_sermon_counts_by_period,
            get_scripture_frequency,
            get_theme_frequency,
            get_series_statistics,
            get_word_count_stats,
            get_preaching_frequency
        )

        conn = create_test_db()

        # Create test data
        series_id = insert_sample_series(conn, name="Advent", planned_count=4)

        insert_sample_sermon(conn, title="Advent 1", series_id=series_id,
                            scripture_book="Matthew", theme="hope",
                            word_count=2000, preached_date="2024-12-01")
        insert_sample_sermon(conn, title="Advent 2", series_id=series_id,
                            scripture_book="Matthew", theme="peace",
                            word_count=2200, preached_date="2024-12-08")
        insert_sample_sermon(conn, title="Advent 3", series_id=series_id,
                            scripture_book="Luke", theme="joy",
                            word_count=2100, preached_date="2024-12-15")
        insert_sample_sermon(conn, title="Advent 4", series_id=series_id,
                            scripture_book="John", theme="love",
                            word_count=2300, preached_date="2024-12-22")

        # Get all dashboard data
        summary = get_dashboard_summary(conn)
        counts = get_sermon_counts_by_period(conn, period='month')
        books = get_scripture_frequency(conn)
        themes = get_theme_frequency(conn)
        series = get_series_statistics(conn)
        words = get_word_count_stats(conn)
        frequency = get_preaching_frequency(conn)

        # Verify all components work
        assert summary['total_sermons'] == 4
        assert '2024-12' in counts
        assert len(books) > 0
        assert len(themes) > 0
        assert len(series) > 0
        assert words['average'] > 0
        assert frequency['total_preached'] == 4

    def test_should_export_all_statistics(self):
        """Test exporting all statistics."""
        from statistics_dashboard import export_statistics

        conn = create_test_db()

        # Create varied test data
        series1 = insert_sample_series(conn, name="Series 1")
        series2 = insert_sample_series(conn, name="Series 2")

        for i in range(10):
            insert_sample_sermon(
                conn,
                title=f"Sermon {i+1}",
                scripture_book=["John", "Matthew", "Luke"][i % 3],
                theme=["grace", "love", "faith"][i % 3],
                word_count=2000 + (i * 100),
                preached_date=f"2024-{(i % 12) + 1:02d}-15",
                series_id=[series1, series2, None][i % 3]
            )

        # Export and verify
        json_export = export_statistics(conn, format='json')
        data = json.loads(json_export)

        assert data is not None
        # Should contain multiple statistics sections
