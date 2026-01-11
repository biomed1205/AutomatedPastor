"""
Tests for illustration deduplication functionality.

Tests the tracking and deduplication of illustrations to
prevent using the same stories/examples too frequently.

TDD: All tests should fail with ModuleNotFoundError until implementation.
NO MOCKS: Uses real SQLite in-memory database.

PHASE 8: Enhanced Features - Item 2
"""

import sqlite3
import pytest
from datetime import datetime, date, timedelta


def create_test_db():
    """Create test database with illustration tables."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Sermons table
    cursor.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            theme TEXT,
            preached_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Illustrations table
    cursor.execute('''
        CREATE TABLE illustrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            source TEXT,
            theme TEXT,
            keywords TEXT,
            hash TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Illustration usage table (many-to-many with sermons)
    cursor.execute('''
        CREATE TABLE illustration_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            illustration_id INTEGER NOT NULL,
            sermon_id INTEGER NOT NULL,
            used_date TEXT NOT NULL,
            section TEXT,
            FOREIGN KEY (illustration_id) REFERENCES illustrations(id),
            FOREIGN KEY (sermon_id) REFERENCES sermons(id)
        )
    ''')

    # Settings table
    cursor.execute('''
        CREATE TABLE illustration_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    conn.commit()
    return conn


def insert_sample_sermon(conn, title="Test Sermon", theme="grace",
                        preached_date="2024-03-17"):
    """Insert a sample sermon for testing."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sermons (title, theme, preached_date)
        VALUES (?, ?, ?)
    ''', (title, theme, preached_date))
    conn.commit()
    return cursor.lastrowid


def insert_sample_illustration(conn, text="Sample story about...",
                              source="Personal", theme="grace"):
    """Insert a sample illustration."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO illustrations (text, source, theme)
        VALUES (?, ?, ?)
    ''', (text, source, theme))
    conn.commit()
    return cursor.lastrowid


def insert_illustration_usage(conn, illustration_id, sermon_id,
                             used_date="2024-03-17"):
    """Insert an illustration usage record."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO illustration_usage (illustration_id, sermon_id, used_date)
        VALUES (?, ?, ?)
    ''', (illustration_id, sermon_id, used_date))
    conn.commit()
    return cursor.lastrowid


class TestAddIllustration:
    """Tests for add_illustration function."""

    def test_should_add_illustration(self):
        """Test adding a new illustration."""
        from illustration_dedup import add_illustration

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = add_illustration(conn, sermon_id,
                                 "The story of the prodigal son teaches us...")

        assert result is not None
        assert result['success'] is True
        assert result['illustration_id'] is not None

    def test_should_store_source(self):
        """Test storing illustration source."""
        from illustration_dedup import add_illustration

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = add_illustration(conn, sermon_id,
                                 "A story from my seminary days...",
                                 source="Personal Experience")

        cursor = conn.cursor()
        cursor.execute('SELECT source FROM illustrations WHERE id = ?',
                      (result['illustration_id'],))
        row = cursor.fetchone()
        assert row['source'] == "Personal Experience"

    def test_should_record_usage(self):
        """Test that usage is recorded when adding illustration."""
        from illustration_dedup import add_illustration

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = add_illustration(conn, sermon_id, "Test illustration")

        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM illustration_usage
                         WHERE illustration_id = ? AND sermon_id = ?''',
                      (result['illustration_id'], sermon_id))
        usage = cursor.fetchone()
        assert usage is not None

    def test_should_warn_on_duplicate(self):
        """Test warning when adding duplicate illustration."""
        from illustration_dedup import add_illustration

        conn = create_test_db()
        sermon1 = insert_sample_sermon(conn, preached_date="2024-01-01")
        sermon2 = insert_sample_sermon(conn, preached_date="2024-03-01")

        add_illustration(conn, sermon1, "The same story about grace")
        result = add_illustration(conn, sermon2, "The same story about grace")

        assert 'warning' in result or 'duplicate' in result

    def test_should_return_error_for_nonexistent_sermon(self):
        """Test error for non-existent sermon."""
        from illustration_dedup import add_illustration

        conn = create_test_db()

        result = add_illustration(conn, 9999, "Test illustration")

        assert result['success'] is False


class TestCheckDuplicate:
    """Tests for check_duplicate function."""

    def test_should_detect_exact_duplicate(self):
        """Test detecting exact duplicate illustration."""
        from illustration_dedup import check_duplicate

        conn = create_test_db()
        insert_sample_illustration(conn, text="The lost sheep parable shows us...")

        result = check_duplicate(conn, "The lost sheep parable shows us...")

        assert result['is_duplicate'] is True

    def test_should_not_flag_unique_illustration(self):
        """Test not flagging unique illustration."""
        from illustration_dedup import check_duplicate

        conn = create_test_db()
        insert_sample_illustration(conn, text="Story about grace")

        result = check_duplicate(conn, "Completely different story about love")

        assert result['is_duplicate'] is False

    def test_should_detect_similar_illustration(self):
        """Test detecting similar (not exact) illustration."""
        from illustration_dedup import check_duplicate

        conn = create_test_db()
        insert_sample_illustration(conn,
            text="The story of a father welcoming his wayward son home")

        result = check_duplicate(conn,
            "A tale of a father embracing his wandering son")

        # Should detect similarity
        assert result.get('is_similar', False) or result.get('similar_found', False)

    def test_should_include_original_when_found(self):
        """Test including original illustration when duplicate found."""
        from illustration_dedup import check_duplicate

        conn = create_test_db()
        original_id = insert_sample_illustration(conn, text="Exact duplicate text")

        result = check_duplicate(conn, "Exact duplicate text")

        assert 'original_id' in result or 'match_id' in result

    def test_should_return_empty_for_first_use(self):
        """Test handling first use (no duplicates possible)."""
        from illustration_dedup import check_duplicate

        conn = create_test_db()

        result = check_duplicate(conn, "Brand new illustration")

        assert result['is_duplicate'] is False


class TestGetIllustrationUsage:
    """Tests for get_illustration_usage function."""

    def test_should_get_usage_history(self):
        """Test getting usage history for illustration."""
        from illustration_dedup import get_illustration_usage

        conn = create_test_db()
        sermon1 = insert_sample_sermon(conn, title="Sermon 1",
                                       preached_date="2024-01-01")
        sermon2 = insert_sample_sermon(conn, title="Sermon 2",
                                       preached_date="2024-03-01")
        illust_id = insert_sample_illustration(conn)
        insert_illustration_usage(conn, illust_id, sermon1, "2024-01-01")
        insert_illustration_usage(conn, illust_id, sermon2, "2024-03-01")

        result = get_illustration_usage(conn, illust_id)

        assert len(result) == 2

    def test_should_include_sermon_info(self):
        """Test including sermon information in usage."""
        from illustration_dedup import get_illustration_usage

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, title="Sunday Sermon")
        illust_id = insert_sample_illustration(conn)
        insert_illustration_usage(conn, illust_id, sermon_id)

        result = get_illustration_usage(conn, illust_id)

        assert result[0]['sermon_title'] == "Sunday Sermon"

    def test_should_order_by_date(self):
        """Test ordering usage by date descending."""
        from illustration_dedup import get_illustration_usage

        conn = create_test_db()
        sermon1 = insert_sample_sermon(conn, title="Old",
                                       preached_date="2024-01-01")
        sermon2 = insert_sample_sermon(conn, title="New",
                                       preached_date="2024-03-01")
        illust_id = insert_sample_illustration(conn)
        insert_illustration_usage(conn, illust_id, sermon1, "2024-01-01")
        insert_illustration_usage(conn, illust_id, sermon2, "2024-03-01")

        result = get_illustration_usage(conn, illust_id)

        assert result[0]['used_date'] == "2024-03-01"

    def test_should_return_empty_for_unused(self):
        """Test returning empty for unused illustration."""
        from illustration_dedup import get_illustration_usage

        conn = create_test_db()
        illust_id = insert_sample_illustration(conn)

        result = get_illustration_usage(conn, illust_id)

        assert result == []


class TestGetRecentIllustrations:
    """Tests for get_recent_illustrations function."""

    def test_should_get_recent_illustrations(self):
        """Test getting illustrations used within timeframe."""
        from illustration_dedup import get_recent_illustrations

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, preached_date="2024-03-01")
        illust_id = insert_sample_illustration(conn)
        insert_illustration_usage(conn, illust_id, sermon_id, "2024-03-01")

        result = get_recent_illustrations(conn, days=30,
                                         from_date="2024-03-15")

        assert len(result) >= 1

    def test_should_exclude_old_illustrations(self):
        """Test excluding illustrations outside timeframe."""
        from illustration_dedup import get_recent_illustrations

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, preached_date="2023-01-01")
        illust_id = insert_sample_illustration(conn)
        insert_illustration_usage(conn, illust_id, sermon_id, "2023-01-01")

        result = get_recent_illustrations(conn, days=30,
                                         from_date="2024-03-15")

        assert len(result) == 0

    def test_should_include_usage_date(self):
        """Test including usage date in results."""
        from illustration_dedup import get_recent_illustrations

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, preached_date="2024-03-01")
        illust_id = insert_sample_illustration(conn, text="Recent story")
        insert_illustration_usage(conn, illust_id, sermon_id, "2024-03-01")

        result = get_recent_illustrations(conn, days=30,
                                         from_date="2024-03-15")

        assert result[0]['last_used'] == "2024-03-01"

    def test_should_return_empty_for_no_recent(self):
        """Test returning empty when no recent illustrations."""
        from illustration_dedup import get_recent_illustrations

        conn = create_test_db()

        result = get_recent_illustrations(conn, days=30)

        assert result == []


class TestFindSimilarIllustrations:
    """Tests for find_similar_illustrations function."""

    def test_should_find_similar_illustrations(self):
        """Test finding similar illustrations."""
        from illustration_dedup import find_similar_illustrations

        conn = create_test_db()
        insert_sample_illustration(conn,
            text="A man found a pearl of great value and sold everything")
        insert_sample_illustration(conn,
            text="The merchant discovering the precious pearl")

        result = find_similar_illustrations(conn,
            "Finding a pearl worth everything", threshold=0.5)

        assert len(result) >= 1

    def test_should_respect_threshold(self):
        """Test respecting similarity threshold."""
        from illustration_dedup import find_similar_illustrations

        conn = create_test_db()
        insert_sample_illustration(conn, text="Story about grace")

        result_high = find_similar_illustrations(conn,
            "Tale of forgiveness", threshold=0.9)
        result_low = find_similar_illustrations(conn,
            "Tale of forgiveness", threshold=0.3)

        # Higher threshold should find fewer matches
        assert len(result_high) <= len(result_low)

    def test_should_include_similarity_score(self):
        """Test including similarity score in results."""
        from illustration_dedup import find_similar_illustrations

        conn = create_test_db()
        insert_sample_illustration(conn, text="The good shepherd story")

        result = find_similar_illustrations(conn,
            "A shepherd caring for sheep", threshold=0.5)

        if len(result) > 0:
            assert 'similarity' in result[0] or 'score' in result[0]

    def test_should_return_empty_for_no_similar(self):
        """Test returning empty when no similar illustrations."""
        from illustration_dedup import find_similar_illustrations

        conn = create_test_db()
        insert_sample_illustration(conn, text="Story about trees")

        result = find_similar_illustrations(conn,
            "Completely unrelated mathematical formula", threshold=0.9)

        assert result == []


class TestGetTimeSinceLastUse:
    """Tests for get_time_since_last_use function."""

    def test_should_calculate_days_since_use(self):
        """Test calculating days since last use."""
        from illustration_dedup import get_time_since_last_use

        conn = create_test_db()
        illust_id = insert_sample_illustration(conn, text="Test story")
        sermon_id = insert_sample_sermon(conn)
        insert_illustration_usage(conn, illust_id, sermon_id, "2024-01-01")

        result = get_time_since_last_use(conn, "Test story",
                                        current_date="2024-03-01")

        assert result['days'] == 60

    def test_should_return_none_for_never_used(self):
        """Test returning None for never-used illustration text."""
        from illustration_dedup import get_time_since_last_use

        conn = create_test_db()

        result = get_time_since_last_use(conn, "Brand new story")

        assert result['days'] is None or result.get('never_used', False)

    def test_should_find_most_recent_use(self):
        """Test finding the most recent use."""
        from illustration_dedup import get_time_since_last_use

        conn = create_test_db()
        illust_id = insert_sample_illustration(conn, text="Reused story")
        sermon1 = insert_sample_sermon(conn)
        sermon2 = insert_sample_sermon(conn)
        insert_illustration_usage(conn, illust_id, sermon1, "2024-01-01")
        insert_illustration_usage(conn, illust_id, sermon2, "2024-02-01")

        result = get_time_since_last_use(conn, "Reused story",
                                        current_date="2024-03-01")

        assert result['days'] == 29  # From Feb 1 to March 1


class TestSuggestAlternatives:
    """Tests for suggest_alternatives function."""

    def test_should_suggest_alternatives_by_theme(self):
        """Test suggesting alternative illustrations by theme."""
        from illustration_dedup import suggest_alternatives

        conn = create_test_db()
        insert_sample_illustration(conn, text="Grace story 1", theme="grace")
        insert_sample_illustration(conn, text="Grace story 2", theme="grace")
        insert_sample_illustration(conn, text="Love story", theme="love")

        result = suggest_alternatives(conn, "grace")

        assert len(result) >= 2

    def test_should_exclude_recently_used(self):
        """Test excluding recently used illustrations."""
        from illustration_dedup import suggest_alternatives

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, preached_date="2024-03-01")
        illust1 = insert_sample_illustration(conn, text="Used",
                                            theme="grace")
        illust2 = insert_sample_illustration(conn, text="Not used",
                                            theme="grace")
        insert_illustration_usage(conn, illust1, sermon_id, "2024-03-01")

        result = suggest_alternatives(conn, "grace",
                                     exclude_days=30,
                                     current_date="2024-03-15")

        texts = [r['text'] for r in result]
        assert "Not used" in texts
        # Used one should be excluded or ranked lower

    def test_should_order_by_least_recently_used(self):
        """Test ordering by least recently used first."""
        from illustration_dedup import suggest_alternatives

        conn = create_test_db()
        sermon1 = insert_sample_sermon(conn)
        sermon2 = insert_sample_sermon(conn)
        illust1 = insert_sample_illustration(conn, text="Recent",
                                            theme="grace")
        illust2 = insert_sample_illustration(conn, text="Older",
                                            theme="grace")
        insert_illustration_usage(conn, illust1, sermon1, "2024-03-01")
        insert_illustration_usage(conn, illust2, sermon2, "2024-01-01")

        result = suggest_alternatives(conn, "grace")

        # Older should come first
        if len(result) >= 2:
            assert result[0]['text'] == "Older"

    def test_should_return_empty_for_no_matches(self):
        """Test returning empty when no matching theme."""
        from illustration_dedup import suggest_alternatives

        conn = create_test_db()
        insert_sample_illustration(conn, theme="grace")

        result = suggest_alternatives(conn, "nonexistent_theme")

        assert result == []


class TestSetMinimumGap:
    """Tests for set_minimum_gap function."""

    def test_should_set_minimum_gap(self):
        """Test setting minimum gap between illustration uses."""
        from illustration_dedup import set_minimum_gap, get_minimum_gap

        conn = create_test_db()

        set_minimum_gap(conn, 90)
        result = get_minimum_gap(conn)

        assert result == 90

    def test_should_update_existing_gap(self):
        """Test updating existing gap setting."""
        from illustration_dedup import set_minimum_gap, get_minimum_gap

        conn = create_test_db()

        set_minimum_gap(conn, 60)
        set_minimum_gap(conn, 120)
        result = get_minimum_gap(conn)

        assert result == 120

    def test_should_enforce_gap_in_add(self):
        """Test enforcing gap when adding illustration."""
        from illustration_dedup import set_minimum_gap, add_illustration

        conn = create_test_db()
        set_minimum_gap(conn, 90)

        sermon1 = insert_sample_sermon(conn, preached_date="2024-01-01")
        sermon2 = insert_sample_sermon(conn, preached_date="2024-02-15")

        add_illustration(conn, sermon1, "Gap test story")
        result = add_illustration(conn, sermon2, "Gap test story")

        # Should warn - only 45 days gap vs 90 required
        assert 'warning' in result or result.get('gap_violation', False)


class TestExportIllustrationLibrary:
    """Tests for export_illustration_library function."""

    def test_should_export_all_illustrations(self):
        """Test exporting all illustrations."""
        from illustration_dedup import export_illustration_library

        conn = create_test_db()
        insert_sample_illustration(conn, text="Story 1", theme="grace")
        insert_sample_illustration(conn, text="Story 2", theme="love")

        result = export_illustration_library(conn)

        assert len(result) == 2

    def test_should_include_usage_count(self):
        """Test including usage count in export."""
        from illustration_dedup import export_illustration_library

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        illust_id = insert_sample_illustration(conn, text="Used story")
        insert_illustration_usage(conn, illust_id, sermon_id)

        result = export_illustration_library(conn)

        assert result[0]['usage_count'] == 1

    def test_should_include_last_used_date(self):
        """Test including last used date in export."""
        from illustration_dedup import export_illustration_library

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        illust_id = insert_sample_illustration(conn, text="Dated story")
        insert_illustration_usage(conn, illust_id, sermon_id, "2024-03-17")

        result = export_illustration_library(conn)

        assert result[0]['last_used'] == "2024-03-17"

    def test_should_export_as_json(self):
        """Test exporting as JSON format."""
        from illustration_dedup import export_illustration_library

        conn = create_test_db()
        insert_sample_illustration(conn)

        result = export_illustration_library(conn, format='json')

        import json
        data = json.loads(result)
        assert len(data) >= 1

    def test_should_return_empty_for_empty_library(self):
        """Test returning empty for empty library."""
        from illustration_dedup import export_illustration_library

        conn = create_test_db()

        result = export_illustration_library(conn)

        assert result == [] or result == "[]"


class TestEdgeCases:
    """Tests for edge cases in illustration deduplication."""

    def test_should_handle_first_illustration(self):
        """Test handling first illustration (no comparisons)."""
        from illustration_dedup import add_illustration

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = add_illustration(conn, sermon_id, "Very first illustration")

        assert result['success'] is True
        assert 'warning' not in result

    def test_should_handle_empty_text(self):
        """Test handling empty illustration text."""
        from illustration_dedup import add_illustration

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = add_illustration(conn, sermon_id, "")

        assert result['success'] is False

    def test_should_handle_very_long_illustration(self):
        """Test handling very long illustration text."""
        from illustration_dedup import add_illustration

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        long_text = "Word " * 1000

        result = add_illustration(conn, sermon_id, long_text)

        assert result['success'] is True

    def test_should_handle_unicode_text(self):
        """Test handling unicode in illustrations."""
        from illustration_dedup import add_illustration

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = add_illustration(conn, sermon_id,
            "A story about love \u2764\ufe0f and grace \u2728")

        assert result['success'] is True

    def test_should_handle_case_insensitive_matching(self):
        """Test case-insensitive duplicate detection."""
        from illustration_dedup import check_duplicate

        conn = create_test_db()
        insert_sample_illustration(conn, text="The Good Shepherd")

        result = check_duplicate(conn, "the good shepherd")

        assert result['is_duplicate'] is True


class TestIntegration:
    """Integration tests for illustration deduplication."""

    def test_should_track_illustration_across_sermons(self):
        """Test tracking illustration usage across multiple sermons."""
        from illustration_dedup import (
            add_illustration,
            get_illustration_usage,
            check_duplicate
        )

        conn = create_test_db()

        # Use same illustration in multiple sermons
        sermon1 = insert_sample_sermon(conn, title="Sermon 1",
                                       preached_date="2024-01-01")
        sermon2 = insert_sample_sermon(conn, title="Sermon 2",
                                       preached_date="2024-06-01")
        sermon3 = insert_sample_sermon(conn, title="Sermon 3",
                                       preached_date="2024-12-01")

        result1 = add_illustration(conn, sermon1,
            "The story of the lost coin", source="Scripture")
        add_illustration(conn, sermon2,
            "The story of the lost coin")
        add_illustration(conn, sermon3,
            "The story of the lost coin")

        # Check usage
        usage = get_illustration_usage(conn, result1['illustration_id'])
        assert len(usage) >= 1

        # Check duplicate detection
        dup_check = check_duplicate(conn, "The story of the lost coin")
        assert dup_check['is_duplicate'] is True

    def test_should_suggest_safe_alternatives(self):
        """Test suggesting alternatives that are safe to use."""
        from illustration_dedup import (
            add_illustration,
            suggest_alternatives,
            set_minimum_gap
        )

        conn = create_test_db()
        set_minimum_gap(conn, 90)

        # Add several illustrations with different usage patterns
        sermon_recent = insert_sample_sermon(conn, preached_date="2024-03-01")
        sermon_old = insert_sample_sermon(conn, preached_date="2023-01-01")

        illust1 = insert_sample_illustration(conn, text="Recently used",
                                            theme="grace")
        illust2 = insert_sample_illustration(conn, text="Used long ago",
                                            theme="grace")
        illust3 = insert_sample_illustration(conn, text="Never used",
                                            theme="grace")

        insert_illustration_usage(conn, illust1, sermon_recent, "2024-03-01")
        insert_illustration_usage(conn, illust2, sermon_old, "2023-01-01")

        # Get alternatives
        alternatives = suggest_alternatives(conn, "grace",
                                          exclude_days=90,
                                          current_date="2024-03-15")

        texts = [a['text'] for a in alternatives]
        # Never used and old ones should be suggested
        assert "Never used" in texts or "Used long ago" in texts
