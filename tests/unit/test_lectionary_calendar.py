"""
Tests for lectionary calendar integration.

Tests the integration with lectionary calendars (primarily RCL)
to suggest scripture passages based on the liturgical calendar.

TDD: All tests should fail with ModuleNotFoundError until implementation.
NO MOCKS: Uses real lectionary data files.

PHASE 8: Enhanced Features - Item 1
"""

import sqlite3
import pytest
from datetime import date, datetime, timedelta


def create_test_db():
    """Create test database with lectionary tables."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Lectionary readings table
    cursor.execute('''
        CREATE TABLE lectionary_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            year TEXT NOT NULL,
            season TEXT NOT NULL,
            name TEXT,
            first_reading TEXT,
            psalm TEXT,
            second_reading TEXT,
            gospel TEXT,
            alternate_first TEXT,
            alternate_psalm TEXT
        )
    ''')

    # Liturgical seasons table
    cursor.execute('''
        CREATE TABLE liturgical_seasons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            year TEXT NOT NULL,
            color TEXT
        )
    ''')

    # Special occasions table
    cursor.execute('''
        CREATE TABLE special_occasions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            year TEXT,
            moveable INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    return conn


def insert_lectionary_reading(conn, date="2024-12-25", year="B", season="christmas",
                             name="Christmas Day", first_reading="Isaiah 9:2-7",
                             psalm="Psalm 96", second_reading="Titus 2:11-14",
                             gospel="Luke 2:1-20"):
    """Insert a lectionary reading."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO lectionary_readings
        (date, year, season, name, first_reading, psalm, second_reading, gospel)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (date, year, season, name, first_reading, psalm, second_reading, gospel))
    conn.commit()
    return cursor.lastrowid


def insert_liturgical_season(conn, name="advent", start_date="2024-12-01",
                            end_date="2024-12-24", year="B", color="purple"):
    """Insert a liturgical season."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO liturgical_seasons (name, start_date, end_date, year, color)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, start_date, end_date, year, color))
    conn.commit()
    return cursor.lastrowid


def insert_special_occasion(conn, name="Christmas", date="2024-12-25",
                           year=None, moveable=0):
    """Insert a special occasion."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO special_occasions (name, date, year, moveable)
        VALUES (?, ?, ?, ?)
    ''', (name, date, year, moveable))
    conn.commit()
    return cursor.lastrowid


class TestGetLectionaryReadings:
    """Tests for get_lectionary_readings function."""

    def test_should_get_readings_for_date(self):
        """Test getting readings for a specific date."""
        from lectionary_calendar import get_lectionary_readings

        conn = create_test_db()
        insert_lectionary_reading(conn, date="2024-12-25")

        result = get_lectionary_readings(conn, "2024-12-25")

        assert result is not None
        assert result['date'] == "2024-12-25"

    def test_should_include_all_readings(self):
        """Test that all four readings are included."""
        from lectionary_calendar import get_lectionary_readings

        conn = create_test_db()
        insert_lectionary_reading(conn, date="2024-12-25",
                                 first_reading="Isaiah 9:2-7",
                                 psalm="Psalm 96",
                                 second_reading="Titus 2:11-14",
                                 gospel="Luke 2:1-20")

        result = get_lectionary_readings(conn, "2024-12-25")

        assert result['first_reading'] == "Isaiah 9:2-7"
        assert result['psalm'] == "Psalm 96"
        assert result['second_reading'] == "Titus 2:11-14"
        assert result['gospel'] == "Luke 2:1-20"

    def test_should_include_season(self):
        """Test that liturgical season is included."""
        from lectionary_calendar import get_lectionary_readings

        conn = create_test_db()
        insert_lectionary_reading(conn, date="2024-12-25", season="christmas")

        result = get_lectionary_readings(conn, "2024-12-25")

        assert result['season'] == "christmas"

    def test_should_include_lectionary_year(self):
        """Test that lectionary year is included."""
        from lectionary_calendar import get_lectionary_readings

        conn = create_test_db()
        insert_lectionary_reading(conn, date="2024-12-25", year="B")

        result = get_lectionary_readings(conn, "2024-12-25")

        assert result['year'] == "B"

    def test_should_include_occasion_name(self):
        """Test that occasion name is included."""
        from lectionary_calendar import get_lectionary_readings

        conn = create_test_db()
        insert_lectionary_reading(conn, date="2024-12-25", name="Christmas Day")

        result = get_lectionary_readings(conn, "2024-12-25")

        assert result['name'] == "Christmas Day"

    def test_should_return_none_for_no_readings(self):
        """Test returning None when no readings for date."""
        from lectionary_calendar import get_lectionary_readings

        conn = create_test_db()

        result = get_lectionary_readings(conn, "2024-06-15")

        assert result is None


class TestGetUpcomingReadings:
    """Tests for get_upcoming_readings function."""

    def test_should_get_upcoming_readings(self):
        """Test getting readings for upcoming Sundays."""
        from lectionary_calendar import get_upcoming_readings

        conn = create_test_db()
        # Insert readings for upcoming Sundays
        insert_lectionary_reading(conn, date="2024-12-01", name="Advent 1")
        insert_lectionary_reading(conn, date="2024-12-08", name="Advent 2")
        insert_lectionary_reading(conn, date="2024-12-15", name="Advent 3")
        insert_lectionary_reading(conn, date="2024-12-22", name="Advent 4")

        result = get_upcoming_readings(conn, count=4,
                                       from_date="2024-11-30")

        assert len(result) == 4

    def test_should_limit_to_requested_count(self):
        """Test limiting to requested number of readings."""
        from lectionary_calendar import get_upcoming_readings

        conn = create_test_db()
        for i in range(10):
            insert_lectionary_reading(conn, date=f"2024-12-{(i*7)+1:02d}",
                                     name=f"Week {i}")

        result = get_upcoming_readings(conn, count=3,
                                       from_date="2024-12-01")

        assert len(result) <= 3

    def test_should_order_by_date(self):
        """Test that readings are ordered by date."""
        from lectionary_calendar import get_upcoming_readings

        conn = create_test_db()
        insert_lectionary_reading(conn, date="2024-12-15", name="Later")
        insert_lectionary_reading(conn, date="2024-12-01", name="Earlier")
        insert_lectionary_reading(conn, date="2024-12-08", name="Middle")

        result = get_upcoming_readings(conn, count=3,
                                       from_date="2024-11-30")

        assert result[0]['name'] == "Earlier"

    def test_should_return_empty_for_no_upcoming(self):
        """Test returning empty when no upcoming readings."""
        from lectionary_calendar import get_upcoming_readings

        conn = create_test_db()
        insert_lectionary_reading(conn, date="2024-01-01", name="Past")

        result = get_upcoming_readings(conn, count=4,
                                       from_date="2024-12-01")

        assert result == []


class TestGetLiturgicalSeason:
    """Tests for get_liturgical_season function."""

    def test_should_get_season_for_date(self):
        """Test getting liturgical season for a date."""
        from lectionary_calendar import get_liturgical_season

        conn = create_test_db()
        insert_liturgical_season(conn, name="advent",
                                start_date="2024-12-01",
                                end_date="2024-12-24")

        result = get_liturgical_season(conn, "2024-12-15")

        assert result['name'] == "advent"

    def test_should_include_season_color(self):
        """Test that season color is included."""
        from lectionary_calendar import get_liturgical_season

        conn = create_test_db()
        insert_liturgical_season(conn, name="advent", color="purple")

        result = get_liturgical_season(conn, "2024-12-15")

        assert result['color'] == "purple"

    def test_should_handle_boundary_dates(self):
        """Test handling dates on season boundaries."""
        from lectionary_calendar import get_liturgical_season

        conn = create_test_db()
        insert_liturgical_season(conn, name="advent",
                                start_date="2024-12-01",
                                end_date="2024-12-24")

        result_start = get_liturgical_season(conn, "2024-12-01")
        result_end = get_liturgical_season(conn, "2024-12-24")

        assert result_start['name'] == "advent"
        assert result_end['name'] == "advent"

    def test_should_return_ordinary_for_no_season(self):
        """Test returning ordinary time for dates not in special season."""
        from lectionary_calendar import get_liturgical_season

        conn = create_test_db()
        # No season inserted for July

        result = get_liturgical_season(conn, "2024-07-15")

        assert result['name'] == "ordinary" or result is None


class TestGetLectionaryYear:
    """Tests for get_lectionary_year function."""

    def test_should_get_year_a(self):
        """Test getting Year A (divisible by 3 remainder 1)."""
        from lectionary_calendar import get_lectionary_year

        # 2023 is Year A
        result = get_lectionary_year("2023-03-01")

        assert result == "A"

    def test_should_get_year_b(self):
        """Test getting Year B (divisible by 3 remainder 2)."""
        from lectionary_calendar import get_lectionary_year

        # 2024 is Year B
        result = get_lectionary_year("2024-03-01")

        assert result == "B"

    def test_should_get_year_c(self):
        """Test getting Year C (divisible by 3 remainder 0)."""
        from lectionary_calendar import get_lectionary_year

        # 2025 is Year C
        result = get_lectionary_year("2025-03-01")

        assert result == "C"

    def test_should_handle_advent_year_change(self):
        """Test handling year change in Advent (new year starts Advent)."""
        from lectionary_calendar import get_lectionary_year

        # After Advent starts, new lectionary year begins
        result = get_lectionary_year("2024-12-01")

        # Advent 2024 starts Year C
        assert result in ["B", "C"]


class TestGetSpecialOccasions:
    """Tests for get_special_occasions function."""

    def test_should_get_special_occasions_for_year(self):
        """Test getting special occasions for a year."""
        from lectionary_calendar import get_special_occasions

        conn = create_test_db()
        insert_special_occasion(conn, name="Christmas", date="2024-12-25")
        insert_special_occasion(conn, name="Easter", date="2024-03-31")

        result = get_special_occasions(conn, 2024)

        assert len(result) >= 2

    def test_should_include_fixed_dates(self):
        """Test including fixed date occasions."""
        from lectionary_calendar import get_special_occasions

        conn = create_test_db()
        insert_special_occasion(conn, name="Christmas", date="2024-12-25",
                               moveable=0)

        result = get_special_occasions(conn, 2024)

        christmas = next((o for o in result if o['name'] == "Christmas"), None)
        assert christmas is not None
        assert christmas['date'] == "2024-12-25"

    def test_should_include_moveable_feasts(self):
        """Test including moveable feasts like Easter."""
        from lectionary_calendar import get_special_occasions

        conn = create_test_db()
        insert_special_occasion(conn, name="Easter", date="2024-03-31",
                               moveable=1)

        result = get_special_occasions(conn, 2024)

        easter = next((o for o in result if o['name'] == "Easter"), None)
        assert easter is not None

    def test_should_return_empty_for_year_without_data(self):
        """Test returning empty for year without data."""
        from lectionary_calendar import get_special_occasions

        conn = create_test_db()

        result = get_special_occasions(conn, 2030)

        assert result == []


class TestSearchLectionaryByPassage:
    """Tests for search_lectionary_by_passage function."""

    def test_should_find_dates_for_passage(self):
        """Test finding dates when a passage is read."""
        from lectionary_calendar import search_lectionary_by_passage

        conn = create_test_db()
        insert_lectionary_reading(conn, date="2024-12-25",
                                 gospel="Luke 2:1-20")
        insert_lectionary_reading(conn, date="2024-12-24",
                                 gospel="Luke 2:1-20")

        result = search_lectionary_by_passage(conn, "Luke 2")

        assert len(result) >= 1

    def test_should_search_all_reading_types(self):
        """Test searching across all reading types."""
        from lectionary_calendar import search_lectionary_by_passage

        conn = create_test_db()
        insert_lectionary_reading(conn, date="2024-03-10",
                                 first_reading="Isaiah 55:1-9")
        insert_lectionary_reading(conn, date="2024-08-04",
                                 second_reading="Isaiah 55:1-9")

        result = search_lectionary_by_passage(conn, "Isaiah 55")

        assert len(result) >= 2

    def test_should_include_date_and_occasion(self):
        """Test including date and occasion in results."""
        from lectionary_calendar import search_lectionary_by_passage

        conn = create_test_db()
        insert_lectionary_reading(conn, date="2024-12-25",
                                 name="Christmas Day",
                                 gospel="Luke 2:1-20")

        result = search_lectionary_by_passage(conn, "Luke 2")

        assert result[0]['date'] == "2024-12-25"
        assert result[0]['name'] == "Christmas Day"

    def test_should_return_empty_for_no_matches(self):
        """Test returning empty for no matching passage."""
        from lectionary_calendar import search_lectionary_by_passage

        conn = create_test_db()
        insert_lectionary_reading(conn)

        result = search_lectionary_by_passage(conn, "Zephaniah 99")

        assert result == []


class TestGetSeasonReadings:
    """Tests for get_season_readings function."""

    def test_should_get_all_readings_for_season(self):
        """Test getting all readings for a liturgical season."""
        from lectionary_calendar import get_season_readings

        conn = create_test_db()
        insert_lectionary_reading(conn, date="2024-12-01", season="advent",
                                 name="Advent 1")
        insert_lectionary_reading(conn, date="2024-12-08", season="advent",
                                 name="Advent 2")
        insert_lectionary_reading(conn, date="2024-12-15", season="advent",
                                 name="Advent 3")
        insert_lectionary_reading(conn, date="2024-12-22", season="advent",
                                 name="Advent 4")

        result = get_season_readings(conn, "advent")

        assert len(result) == 4

    def test_should_filter_by_year(self):
        """Test filtering season readings by lectionary year."""
        from lectionary_calendar import get_season_readings

        conn = create_test_db()
        insert_lectionary_reading(conn, date="2023-12-03", season="advent",
                                 year="A", name="Advent 1 Year A")
        insert_lectionary_reading(conn, date="2024-12-01", season="advent",
                                 year="B", name="Advent 1 Year B")

        result = get_season_readings(conn, "advent", year="B")

        assert len(result) == 1
        assert result[0]['year'] == "B"

    def test_should_order_by_date(self):
        """Test ordering season readings by date."""
        from lectionary_calendar import get_season_readings

        conn = create_test_db()
        insert_lectionary_reading(conn, date="2024-12-22", season="advent",
                                 name="Advent 4")
        insert_lectionary_reading(conn, date="2024-12-01", season="advent",
                                 name="Advent 1")

        result = get_season_readings(conn, "advent")

        assert result[0]['name'] == "Advent 1"

    def test_should_return_empty_for_unknown_season(self):
        """Test returning empty for unknown season."""
        from lectionary_calendar import get_season_readings

        conn = create_test_db()

        result = get_season_readings(conn, "nonexistent")

        assert result == []


class TestSuggestPassagesForDate:
    """Tests for suggest_passages_for_date function."""

    def test_should_suggest_lectionary_passages(self):
        """Test suggesting passages from lectionary for date."""
        from lectionary_calendar import suggest_passages_for_date

        conn = create_test_db()
        insert_lectionary_reading(conn, date="2024-12-25",
                                 gospel="Luke 2:1-20",
                                 first_reading="Isaiah 9:2-7")

        result = suggest_passages_for_date(conn, "2024-12-25")

        assert len(result) > 0
        passages = [r['passage'] for r in result]
        assert any("Luke" in p for p in passages)

    def test_should_include_reading_type(self):
        """Test including reading type in suggestions."""
        from lectionary_calendar import suggest_passages_for_date

        conn = create_test_db()
        insert_lectionary_reading(conn, date="2024-12-25",
                                 gospel="Luke 2:1-20")

        result = suggest_passages_for_date(conn, "2024-12-25")

        gospel_suggestion = next((r for r in result
                                 if r['passage'] == "Luke 2:1-20"), None)
        assert gospel_suggestion is not None
        assert gospel_suggestion['type'] == "gospel"

    def test_should_include_occasion_context(self):
        """Test including occasion context in suggestions."""
        from lectionary_calendar import suggest_passages_for_date

        conn = create_test_db()
        insert_lectionary_reading(conn, date="2024-12-25",
                                 name="Christmas Day",
                                 gospel="Luke 2:1-20")

        result = suggest_passages_for_date(conn, "2024-12-25")

        assert result[0]['occasion'] == "Christmas Day"

    def test_should_return_empty_for_no_suggestions(self):
        """Test returning empty when no suggestions available."""
        from lectionary_calendar import suggest_passages_for_date

        conn = create_test_db()

        result = suggest_passages_for_date(conn, "2024-06-15")

        assert result == [] or result is None


class TestEdgeCases:
    """Tests for edge cases in lectionary calendar."""

    def test_should_handle_leap_year(self):
        """Test handling leap year dates."""
        from lectionary_calendar import get_lectionary_readings

        conn = create_test_db()
        insert_lectionary_reading(conn, date="2024-02-29", name="Leap Day")

        result = get_lectionary_readings(conn, "2024-02-29")

        assert result is not None

    def test_should_handle_moveable_easter(self):
        """Test handling moveable Easter date."""
        from lectionary_calendar import get_special_occasions

        conn = create_test_db()
        # Easter moves each year
        insert_special_occasion(conn, name="Easter", date="2024-03-31",
                               moveable=1)

        result = get_special_occasions(conn, 2024)

        easter = next((o for o in result if o['name'] == "Easter"), None)
        assert easter is not None

    def test_should_handle_overlapping_seasons(self):
        """Test handling dates that might overlap seasons."""
        from lectionary_calendar import get_liturgical_season

        conn = create_test_db()
        insert_liturgical_season(conn, name="christmas",
                                start_date="2024-12-25",
                                end_date="2025-01-06")

        result = get_liturgical_season(conn, "2024-12-25")

        assert result['name'] == "christmas"

    def test_should_handle_empty_database(self):
        """Test handling empty lectionary database."""
        from lectionary_calendar import get_lectionary_readings

        conn = create_test_db()

        result = get_lectionary_readings(conn, "2024-12-25")

        assert result is None

    def test_should_handle_alternate_readings(self):
        """Test handling alternate readings option."""
        from lectionary_calendar import get_lectionary_readings

        conn = create_test_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO lectionary_readings
            (date, year, season, name, first_reading, psalm,
             second_reading, gospel, alternate_first, alternate_psalm)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ("2024-12-25", "B", "christmas", "Christmas",
              "Isaiah 9:2-7", "Psalm 96",
              "Titus 2:11-14", "Luke 2:1-20",
              "Isaiah 62:6-12", "Psalm 97"))
        conn.commit()

        result = get_lectionary_readings(conn, "2024-12-25")

        assert result['alternate_first'] == "Isaiah 62:6-12"


class TestIntegration:
    """Integration tests for lectionary calendar."""

    def test_should_plan_sermon_series_from_lectionary(self):
        """Test planning a sermon series using lectionary."""
        from lectionary_calendar import (
            get_upcoming_readings,
            get_liturgical_season
        )

        conn = create_test_db()

        # Set up Advent season
        insert_liturgical_season(conn, name="advent",
                                start_date="2024-12-01",
                                end_date="2024-12-24",
                                color="purple")

        # Insert Advent readings
        insert_lectionary_reading(conn, date="2024-12-01",
                                 season="advent", name="Advent 1",
                                 gospel="Mark 13:24-37")
        insert_lectionary_reading(conn, date="2024-12-08",
                                 season="advent", name="Advent 2",
                                 gospel="Mark 1:1-8")
        insert_lectionary_reading(conn, date="2024-12-15",
                                 season="advent", name="Advent 3",
                                 gospel="John 1:6-8, 19-28")
        insert_lectionary_reading(conn, date="2024-12-22",
                                 season="advent", name="Advent 4",
                                 gospel="Luke 1:26-38")

        # Get upcoming readings for planning
        readings = get_upcoming_readings(conn, count=4,
                                         from_date="2024-11-30")

        assert len(readings) == 4

        # Check season for planning
        season = get_liturgical_season(conn, "2024-12-15")
        assert season['name'] == "advent"
        assert season['color'] == "purple"

    def test_should_find_all_gospel_occurrences(self):
        """Test finding when a gospel is read throughout the year."""
        from lectionary_calendar import search_lectionary_by_passage

        conn = create_test_db()

        # John 3:16 might appear multiple times
        insert_lectionary_reading(conn, date="2024-03-10",
                                 gospel="John 3:14-21", name="Lent 4")
        insert_lectionary_reading(conn, date="2024-05-26",
                                 gospel="John 3:1-17", name="Trinity Sunday")

        result = search_lectionary_by_passage(conn, "John 3")

        assert len(result) >= 2
