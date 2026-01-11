"""
Tests for theme/scripture usage tracking functionality.

Tests tracking which themes and scripture passages have been used
to help variety in preaching and identify coverage gaps.

TDD: All tests should fail with ModuleNotFoundError until implementation.
NO MOCKS: Uses real SQLite in-memory database.

PHASE 8: Enhanced Features - Item 3
"""

import sqlite3
import pytest
from datetime import datetime, date, timedelta


def create_test_db():
    """Create test database with usage tracking tables."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Sermons table
    cursor.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            preached_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Scripture usage table
    cursor.execute('''
        CREATE TABLE scripture_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            passage TEXT NOT NULL,
            book TEXT NOT NULL,
            chapter INTEGER,
            is_primary INTEGER DEFAULT 0,
            used_date TEXT,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id)
        )
    ''')

    # Theme usage table
    cursor.execute('''
        CREATE TABLE theme_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            theme TEXT NOT NULL,
            is_primary INTEGER DEFAULT 0,
            used_date TEXT,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id)
        )
    ''')

    # Bible books reference table
    cursor.execute('''
        CREATE TABLE bible_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            testament TEXT,
            book_order INTEGER
        )
    ''')

    # Standard themes reference table
    cursor.execute('''
        CREATE TABLE standard_themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT
        )
    ''')

    conn.commit()
    return conn


def insert_sample_sermon(conn, title="Test Sermon", preached_date="2024-03-17"):
    """Insert a sample sermon for testing."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sermons (title, preached_date)
        VALUES (?, ?)
    ''', (title, preached_date))
    conn.commit()
    return cursor.lastrowid


def insert_scripture_usage(conn, sermon_id, passage="John 3:16",
                          book="John", chapter=3, is_primary=1,
                          used_date="2024-03-17"):
    """Insert a scripture usage record."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scripture_usage (sermon_id, passage, book, chapter,
                                    is_primary, used_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (sermon_id, passage, book, chapter, is_primary, used_date))
    conn.commit()
    return cursor.lastrowid


def insert_theme_usage(conn, sermon_id, theme="grace", is_primary=1,
                      used_date="2024-03-17"):
    """Insert a theme usage record."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO theme_usage (sermon_id, theme, is_primary, used_date)
        VALUES (?, ?, ?, ?)
    ''', (sermon_id, theme, is_primary, used_date))
    conn.commit()
    return cursor.lastrowid


def insert_bible_book(conn, name, testament="NT", book_order=43):
    """Insert a Bible book reference."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bible_books (name, testament, book_order)
        VALUES (?, ?, ?)
    ''', (name, testament, book_order))
    conn.commit()
    return cursor.lastrowid


def insert_standard_theme(conn, name, category="theological"):
    """Insert a standard theme reference."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO standard_themes (name, category)
        VALUES (?, ?)
    ''', (name, category))
    conn.commit()
    return cursor.lastrowid


class TestTrackScriptureUsage:
    """Tests for track_scripture_usage function."""

    def test_should_track_scripture_usage(self):
        """Test tracking scripture passage usage."""
        from usage_tracking import track_scripture_usage

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = track_scripture_usage(conn, sermon_id, "John 3:16")

        assert result['success'] is True

    def test_should_extract_book_name(self):
        """Test extracting book name from passage."""
        from usage_tracking import track_scripture_usage

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        track_scripture_usage(conn, sermon_id, "Matthew 5:1-12")

        cursor = conn.cursor()
        cursor.execute('SELECT book FROM scripture_usage WHERE sermon_id = ?',
                      (sermon_id,))
        row = cursor.fetchone()
        assert row['book'] == "Matthew"

    def test_should_mark_as_primary(self):
        """Test marking scripture as primary."""
        from usage_tracking import track_scripture_usage

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        track_scripture_usage(conn, sermon_id, "Luke 15:11-32",
                             is_primary=True)

        cursor = conn.cursor()
        cursor.execute('SELECT is_primary FROM scripture_usage WHERE sermon_id = ?',
                      (sermon_id,))
        row = cursor.fetchone()
        assert row['is_primary'] == 1

    def test_should_record_date(self):
        """Test recording usage date."""
        from usage_tracking import track_scripture_usage

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, preached_date="2024-03-17")

        track_scripture_usage(conn, sermon_id, "Romans 8:28")

        cursor = conn.cursor()
        cursor.execute('SELECT used_date FROM scripture_usage WHERE sermon_id = ?',
                      (sermon_id,))
        row = cursor.fetchone()
        assert row['used_date'] is not None

    def test_should_return_error_for_invalid_passage(self):
        """Test error for invalid passage format."""
        from usage_tracking import track_scripture_usage

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = track_scripture_usage(conn, sermon_id, "Not a valid passage")

        assert result['success'] is False or 'warning' in result


class TestTrackThemeUsage:
    """Tests for track_theme_usage function."""

    def test_should_track_theme_usage(self):
        """Test tracking theme usage."""
        from usage_tracking import track_theme_usage

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = track_theme_usage(conn, sermon_id, "grace")

        assert result['success'] is True

    def test_should_normalize_theme_name(self):
        """Test normalizing theme name (lowercase, trimmed)."""
        from usage_tracking import track_theme_usage

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        track_theme_usage(conn, sermon_id, "  GRACE  ")

        cursor = conn.cursor()
        cursor.execute('SELECT theme FROM theme_usage WHERE sermon_id = ?',
                      (sermon_id,))
        row = cursor.fetchone()
        assert row['theme'] == "grace"

    def test_should_mark_as_primary(self):
        """Test marking theme as primary."""
        from usage_tracking import track_theme_usage

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        track_theme_usage(conn, sermon_id, "forgiveness", is_primary=True)

        cursor = conn.cursor()
        cursor.execute('SELECT is_primary FROM theme_usage WHERE sermon_id = ?',
                      (sermon_id,))
        row = cursor.fetchone()
        assert row['is_primary'] == 1

    def test_should_allow_multiple_themes(self):
        """Test allowing multiple themes per sermon."""
        from usage_tracking import track_theme_usage

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        track_theme_usage(conn, sermon_id, "grace")
        track_theme_usage(conn, sermon_id, "redemption")

        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM theme_usage WHERE sermon_id = ?',
                      (sermon_id,))
        row = cursor.fetchone()
        assert row['count'] == 2


class TestGetScriptureFrequency:
    """Tests for get_scripture_frequency function."""

    def test_should_get_frequency_for_all_books(self):
        """Test getting frequency for all books."""
        from usage_tracking import get_scripture_frequency

        conn = create_test_db()
        sermon1 = insert_sample_sermon(conn)
        sermon2 = insert_sample_sermon(conn)
        insert_scripture_usage(conn, sermon1, book="John")
        insert_scripture_usage(conn, sermon2, book="John")
        insert_scripture_usage(conn, sermon2, book="Matthew")

        result = get_scripture_frequency(conn)

        john_entry = next((r for r in result if r['book'] == "John"), None)
        assert john_entry is not None
        assert john_entry['count'] == 2

    def test_should_filter_by_book(self):
        """Test filtering frequency by specific book."""
        from usage_tracking import get_scripture_frequency

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_scripture_usage(conn, sermon_id, "John 3:16", book="John")
        insert_scripture_usage(conn, sermon_id, "John 1:1", book="John")

        result = get_scripture_frequency(conn, book="John")

        assert len(result) >= 1
        assert all(r['book'] == "John" for r in result)

    def test_should_order_by_frequency(self):
        """Test ordering by frequency descending."""
        from usage_tracking import get_scripture_frequency

        conn = create_test_db()
        for _ in range(3):
            sermon = insert_sample_sermon(conn)
            insert_scripture_usage(conn, sermon, book="John")
        sermon = insert_sample_sermon(conn)
        insert_scripture_usage(conn, sermon, book="Matthew")

        result = get_scripture_frequency(conn)

        assert result[0]['book'] == "John"

    def test_should_return_empty_for_no_usage(self):
        """Test returning empty when no scripture used."""
        from usage_tracking import get_scripture_frequency

        conn = create_test_db()

        result = get_scripture_frequency(conn)

        assert result == []


class TestGetThemeFrequency:
    """Tests for get_theme_frequency function."""

    def test_should_get_theme_frequency(self):
        """Test getting frequency of all themes."""
        from usage_tracking import get_theme_frequency

        conn = create_test_db()
        sermon1 = insert_sample_sermon(conn)
        sermon2 = insert_sample_sermon(conn)
        insert_theme_usage(conn, sermon1, "grace")
        insert_theme_usage(conn, sermon2, "grace")
        insert_theme_usage(conn, sermon2, "love")

        result = get_theme_frequency(conn)

        grace_entry = next((r for r in result if r['theme'] == "grace"), None)
        assert grace_entry is not None
        assert grace_entry['count'] == 2

    def test_should_order_by_frequency(self):
        """Test ordering themes by frequency."""
        from usage_tracking import get_theme_frequency

        conn = create_test_db()
        for _ in range(5):
            sermon = insert_sample_sermon(conn)
            insert_theme_usage(conn, sermon, "grace")
        for _ in range(2):
            sermon = insert_sample_sermon(conn)
            insert_theme_usage(conn, sermon, "love")

        result = get_theme_frequency(conn)

        assert result[0]['theme'] == "grace"

    def test_should_include_last_used_date(self):
        """Test including last used date."""
        from usage_tracking import get_theme_frequency

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_theme_usage(conn, sermon_id, "hope", used_date="2024-03-17")

        result = get_theme_frequency(conn)

        hope_entry = next((r for r in result if r['theme'] == "hope"), None)
        assert hope_entry['last_used'] == "2024-03-17"


class TestGetUncoveredBooks:
    """Tests for get_uncovered_books function."""

    def test_should_find_uncovered_books(self):
        """Test finding Bible books never preached from."""
        from usage_tracking import get_uncovered_books

        conn = create_test_db()
        # Add Bible books reference
        insert_bible_book(conn, "Genesis", "OT", 1)
        insert_bible_book(conn, "Exodus", "OT", 2)
        insert_bible_book(conn, "John", "NT", 43)

        # Only preach from John
        sermon_id = insert_sample_sermon(conn)
        insert_scripture_usage(conn, sermon_id, book="John")

        result = get_uncovered_books(conn)

        uncovered = [r['name'] for r in result]
        assert "Genesis" in uncovered
        assert "Exodus" in uncovered
        assert "John" not in uncovered

    def test_should_filter_by_testament(self):
        """Test filtering uncovered books by testament."""
        from usage_tracking import get_uncovered_books

        conn = create_test_db()
        insert_bible_book(conn, "Genesis", "OT", 1)
        insert_bible_book(conn, "John", "NT", 43)

        result = get_uncovered_books(conn, testament="OT")

        assert all(r['testament'] == "OT" for r in result)

    def test_should_return_empty_when_all_covered(self):
        """Test returning empty when all books covered."""
        from usage_tracking import get_uncovered_books

        conn = create_test_db()
        insert_bible_book(conn, "John", "NT", 43)

        sermon_id = insert_sample_sermon(conn)
        insert_scripture_usage(conn, sermon_id, book="John")

        result = get_uncovered_books(conn)

        assert len(result) == 0


class TestGetThemeGaps:
    """Tests for get_theme_gaps function."""

    def test_should_find_theme_gaps(self):
        """Test finding themes not covered recently."""
        from usage_tracking import get_theme_gaps

        conn = create_test_db()
        # Add standard themes
        insert_standard_theme(conn, "grace")
        insert_standard_theme(conn, "love")
        insert_standard_theme(conn, "faith")

        # Only cover grace recently
        sermon_id = insert_sample_sermon(conn, preached_date="2024-03-01")
        insert_theme_usage(conn, sermon_id, "grace", used_date="2024-03-01")

        result = get_theme_gaps(conn, months=12,
                               current_date="2024-03-17")

        missing = [r['name'] for r in result]
        assert "love" in missing
        assert "faith" in missing

    def test_should_respect_time_window(self):
        """Test respecting the time window for gaps."""
        from usage_tracking import get_theme_gaps

        conn = create_test_db()
        insert_standard_theme(conn, "hope")

        # Use theme over a year ago
        sermon_id = insert_sample_sermon(conn, preached_date="2022-01-01")
        insert_theme_usage(conn, sermon_id, "hope", used_date="2022-01-01")

        result = get_theme_gaps(conn, months=12,
                               current_date="2024-03-17")

        missing = [r['name'] for r in result]
        assert "hope" in missing

    def test_should_return_empty_when_all_covered(self):
        """Test returning empty when all themes recently covered."""
        from usage_tracking import get_theme_gaps

        conn = create_test_db()
        insert_standard_theme(conn, "grace")

        sermon_id = insert_sample_sermon(conn, preached_date="2024-03-01")
        insert_theme_usage(conn, sermon_id, "grace", used_date="2024-03-01")

        result = get_theme_gaps(conn, months=12,
                               current_date="2024-03-17")

        assert len(result) == 0


class TestGetUsageReport:
    """Tests for get_usage_report function."""

    def test_should_generate_usage_report(self):
        """Test generating usage report for date range."""
        from usage_tracking import get_usage_report

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, preached_date="2024-03-17")
        insert_scripture_usage(conn, sermon_id, used_date="2024-03-17")
        insert_theme_usage(conn, sermon_id, used_date="2024-03-17")

        result = get_usage_report(conn, "2024-03-01", "2024-03-31")

        assert 'scriptures' in result
        assert 'themes' in result

    def test_should_filter_by_date_range(self):
        """Test filtering report by date range."""
        from usage_tracking import get_usage_report

        conn = create_test_db()
        old_sermon = insert_sample_sermon(conn, preached_date="2024-01-01")
        new_sermon = insert_sample_sermon(conn, preached_date="2024-03-15")
        insert_scripture_usage(conn, old_sermon, used_date="2024-01-01")
        insert_scripture_usage(conn, new_sermon, used_date="2024-03-15")

        result = get_usage_report(conn, "2024-03-01", "2024-03-31")

        assert result['scripture_count'] == 1

    def test_should_include_sermon_count(self):
        """Test including sermon count in report."""
        from usage_tracking import get_usage_report

        conn = create_test_db()
        for i in range(3):
            sermon = insert_sample_sermon(conn, preached_date=f"2024-03-{10+i}")
            insert_scripture_usage(conn, sermon, used_date=f"2024-03-{10+i}")

        result = get_usage_report(conn, "2024-03-01", "2024-03-31")

        assert result['sermon_count'] == 3


class TestSuggestUnderusedScriptures:
    """Tests for suggest_underused_scriptures function."""

    def test_should_suggest_underused_books(self):
        """Test suggesting underused scripture books."""
        from usage_tracking import suggest_underused_scriptures

        conn = create_test_db()
        # Add books
        insert_bible_book(conn, "Genesis", "OT", 1)
        insert_bible_book(conn, "Matthew", "NT", 40)
        insert_bible_book(conn, "John", "NT", 43)

        # Heavy use of John
        for i in range(10):
            sermon = insert_sample_sermon(conn, preached_date=f"2024-{i+1:02d}-01")
            insert_scripture_usage(conn, sermon, book="John")

        result = suggest_underused_scriptures(conn, limit=5)

        books = [r['book'] for r in result]
        assert "Genesis" in books
        assert "Matthew" in books

    def test_should_prioritize_never_used(self):
        """Test prioritizing never-used books."""
        from usage_tracking import suggest_underused_scriptures

        conn = create_test_db()
        insert_bible_book(conn, "Zephaniah", "OT", 36)
        insert_bible_book(conn, "John", "NT", 43)

        sermon = insert_sample_sermon(conn)
        insert_scripture_usage(conn, sermon, book="John")

        result = suggest_underused_scriptures(conn, limit=10)

        if len(result) > 0:
            assert result[0]['usage_count'] == 0

    def test_should_respect_limit(self):
        """Test respecting suggestion limit."""
        from usage_tracking import suggest_underused_scriptures

        conn = create_test_db()
        for i in range(20):
            insert_bible_book(conn, f"Book{i}", "OT", i)

        result = suggest_underused_scriptures(conn, limit=5)

        assert len(result) <= 5


class TestSuggestUnderusedThemes:
    """Tests for suggest_underused_themes function."""

    def test_should_suggest_underused_themes(self):
        """Test suggesting underused themes."""
        from usage_tracking import suggest_underused_themes

        conn = create_test_db()
        # Add standard themes
        insert_standard_theme(conn, "grace")
        insert_standard_theme(conn, "love")
        insert_standard_theme(conn, "justice")

        # Heavy use of grace
        for i in range(5):
            sermon = insert_sample_sermon(conn)
            insert_theme_usage(conn, sermon, "grace")

        result = suggest_underused_themes(conn, limit=5)

        themes = [r['theme'] for r in result]
        assert "love" in themes
        assert "justice" in themes

    def test_should_include_days_since_use(self):
        """Test including days since last use."""
        from usage_tracking import suggest_underused_themes

        conn = create_test_db()
        insert_standard_theme(conn, "hope")

        sermon = insert_sample_sermon(conn, preached_date="2024-01-01")
        insert_theme_usage(conn, sermon, "hope", used_date="2024-01-01")

        result = suggest_underused_themes(conn, limit=5,
                                         current_date="2024-03-17")

        hope_entry = next((r for r in result if r['theme'] == "hope"), None)
        if hope_entry:
            assert hope_entry['days_since_use'] > 60

    def test_should_respect_limit(self):
        """Test respecting suggestion limit."""
        from usage_tracking import suggest_underused_themes

        conn = create_test_db()
        for i in range(20):
            insert_standard_theme(conn, f"theme{i}")

        result = suggest_underused_themes(conn, limit=5)

        assert len(result) <= 5


class TestEdgeCases:
    """Tests for edge cases in usage tracking."""

    def test_should_handle_no_history(self):
        """Test handling when no usage history exists."""
        from usage_tracking import get_scripture_frequency, get_theme_frequency

        conn = create_test_db()

        scripture_result = get_scripture_frequency(conn)
        theme_result = get_theme_frequency(conn)

        assert scripture_result == []
        assert theme_result == []

    def test_should_handle_single_sermon(self):
        """Test handling single sermon in system."""
        from usage_tracking import get_usage_report

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, preached_date="2024-03-17")
        insert_scripture_usage(conn, sermon_id)
        insert_theme_usage(conn, sermon_id)

        result = get_usage_report(conn, "2024-01-01", "2024-12-31")

        assert result['sermon_count'] == 1

    def test_should_handle_multiple_scriptures_per_sermon(self):
        """Test handling multiple scriptures per sermon."""
        from usage_tracking import track_scripture_usage

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        track_scripture_usage(conn, sermon_id, "John 3:16", is_primary=True)
        track_scripture_usage(conn, sermon_id, "Romans 8:28", is_primary=False)
        track_scripture_usage(conn, sermon_id, "Psalm 23", is_primary=False)

        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM scripture_usage WHERE sermon_id = ?',
                      (sermon_id,))
        row = cursor.fetchone()
        assert row['count'] == 3

    def test_should_handle_unicode_themes(self):
        """Test handling unicode in themes."""
        from usage_tracking import track_theme_usage

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = track_theme_usage(conn, sermon_id, "love \u2764\ufe0f")

        assert result['success'] is True


class TestIntegration:
    """Integration tests for usage tracking."""

    def test_should_track_complete_sermon_usage(self):
        """Test tracking complete sermon with multiple scriptures and themes."""
        from usage_tracking import (
            track_scripture_usage,
            track_theme_usage,
            get_usage_report
        )

        conn = create_test_db()

        # Create sermon with full usage tracking
        sermon_id = insert_sample_sermon(conn, title="Grace and Forgiveness",
                                        preached_date="2024-03-17")

        # Track scriptures
        track_scripture_usage(conn, sermon_id, "Luke 15:11-32", is_primary=True)
        track_scripture_usage(conn, sermon_id, "Ephesians 2:8-9")

        # Track themes
        track_theme_usage(conn, sermon_id, "grace", is_primary=True)
        track_theme_usage(conn, sermon_id, "forgiveness")
        track_theme_usage(conn, sermon_id, "love")

        # Get report
        report = get_usage_report(conn, "2024-03-01", "2024-03-31")

        assert report['sermon_count'] == 1
        assert report['scripture_count'] == 2
        assert report['theme_count'] == 3

    def test_should_identify_preaching_patterns(self):
        """Test identifying preaching patterns over time."""
        from usage_tracking import (
            track_scripture_usage,
            track_theme_usage,
            get_scripture_frequency,
            get_theme_frequency,
            suggest_underused_scriptures,
            suggest_underused_themes
        )

        conn = create_test_db()

        # Add reference data
        for book in ["Genesis", "Exodus", "Matthew", "Mark", "Luke", "John"]:
            insert_bible_book(conn, book)
        for theme in ["grace", "love", "faith", "hope", "justice"]:
            insert_standard_theme(conn, theme)

        # Create pattern: heavy John/grace usage
        for month in range(1, 7):
            sermon = insert_sample_sermon(conn,
                                         preached_date=f"2024-{month:02d}-15")
            track_scripture_usage(conn, sermon, f"John {month}:1-10")
            track_theme_usage(conn, sermon, "grace")

        # Check frequencies
        scripture_freq = get_scripture_frequency(conn)
        theme_freq = get_theme_frequency(conn)

        assert scripture_freq[0]['book'] == "John"
        assert theme_freq[0]['theme'] == "grace"

        # Get suggestions for variety
        scripture_suggestions = suggest_underused_scriptures(conn)
        theme_suggestions = suggest_underused_themes(conn)

        scripture_books = [s['book'] for s in scripture_suggestions]
        assert "Genesis" in scripture_books

        suggested_themes = [t['theme'] for t in theme_suggestions]
        assert any(t in suggested_themes for t in ["love", "faith", "hope", "justice"])
