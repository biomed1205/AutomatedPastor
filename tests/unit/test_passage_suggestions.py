"""Tests for passage suggestion engine.

These tests verify the passage suggestion engine that recommends
scripture passages based on themes, series context, and user preferences.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database - NO MOCKS.
"""
import pytest
import sqlite3
import time
from datetime import datetime


def create_test_db():
    """Create an in-memory test database for passage suggestion testing."""
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

    # Create sermons table
    conn.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY,
            series_id INTEGER,
            title TEXT NOT NULL,
            scripture TEXT,
            theme TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE SET NULL
        )
    ''')

    # Create passage_cache table
    conn.execute('''
        CREATE TABLE passage_cache (
            id INTEGER PRIMARY KEY,
            cache_key TEXT UNIQUE NOT NULL,
            suggestions TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL
        )
    ''')

    # Create passages table for known passages
    conn.execute('''
        CREATE TABLE passages (
            id INTEGER PRIMARY KEY,
            reference TEXT UNIQUE NOT NULL,
            testament TEXT,
            genre TEXT,
            themes TEXT,
            context TEXT,
            related_passages TEXT
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


def insert_sample_sermon(conn, series_id, title, scripture, theme=None):
    """Insert a sample sermon for testing."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sermons (series_id, title, scripture, theme) VALUES (?, ?, ?, ?)",
        (series_id, title, scripture, theme)
    )
    conn.commit()
    return cursor.lastrowid


def insert_sample_passage(conn, reference, testament="NT", genre="gospel",
                          themes="hope,faith", context="", related=""):
    """Insert a sample passage for testing."""
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO passages (reference, testament, genre, themes, context, related_passages)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (reference, testament, genre, themes, context, related)
    )
    conn.commit()
    return cursor.lastrowid


class TestSuggestPassagesForTheme:
    """Test suite for theme-based passage suggestions."""

    def test_should_suggest_passages_for_theme(self):
        """Test that passages are suggested based on theme."""
        from passage_suggestions import suggest_passages_for_theme

        suggestions = suggest_passages_for_theme("hope")

        assert suggestions is not None
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

    def test_should_return_default_count_of_passages(self):
        """Test that default count of 5 passages is returned."""
        from passage_suggestions import suggest_passages_for_theme

        suggestions = suggest_passages_for_theme("love")

        assert len(suggestions) == 5

    def test_should_respect_custom_count_parameter(self):
        """Test that custom count is respected."""
        from passage_suggestions import suggest_passages_for_theme

        suggestions = suggest_passages_for_theme("faith", count=3)

        assert len(suggestions) == 3

    def test_should_return_passages_with_reference_field(self):
        """Test that each suggestion has a scripture reference."""
        from passage_suggestions import suggest_passages_for_theme

        suggestions = suggest_passages_for_theme("grace")

        for suggestion in suggestions:
            assert 'reference' in suggestion or 'scripture' in suggestion

    def test_should_handle_empty_theme(self):
        """Test that empty theme returns general passages."""
        from passage_suggestions import suggest_passages_for_theme

        suggestions = suggest_passages_for_theme("")

        assert suggestions is not None
        assert len(suggestions) > 0

    def test_should_handle_unknown_theme(self):
        """Test that unknown theme still returns passages."""
        from passage_suggestions import suggest_passages_for_theme

        suggestions = suggest_passages_for_theme("obscurethemenobodyuses")

        assert suggestions is not None
        # Should still return some general passages


class TestSuggestPassagesForSeries:
    """Test suite for series-context passage suggestions."""

    def test_should_suggest_passages_for_series(self):
        """Test that passages are suggested based on series context."""
        from passage_suggestions import suggest_passages_for_series

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Lent Series", "Repentance")

        suggestions = suggest_passages_for_series(conn, series_id)

        assert suggestions is not None
        assert isinstance(suggestions, list)
        conn.close()

    def test_should_return_default_count_of_10(self):
        """Test that default count of 10 passages is returned."""
        from passage_suggestions import suggest_passages_for_series

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Easter Series", "Resurrection")

        suggestions = suggest_passages_for_series(conn, series_id)

        assert len(suggestions) == 10
        conn.close()

    def test_should_consider_existing_sermons_in_series(self):
        """Test that existing sermons influence suggestions."""
        from passage_suggestions import suggest_passages_for_series

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Gospel of John", "Light")
        insert_sample_sermon(conn, series_id, "Sermon 1", "John 1:1-14")
        insert_sample_sermon(conn, series_id, "Sermon 2", "John 3:16-21")

        suggestions = suggest_passages_for_series(conn, series_id, count=5)

        # Suggestions should exist and ideally avoid already-used passages
        assert suggestions is not None
        assert len(suggestions) <= 5
        conn.close()

    def test_should_handle_nonexistent_series(self):
        """Test that nonexistent series returns empty or None."""
        from passage_suggestions import suggest_passages_for_series

        conn = create_test_db()

        suggestions = suggest_passages_for_series(conn, 9999)

        assert suggestions is None or suggestions == []
        conn.close()

    def test_should_use_series_theme_for_suggestions(self):
        """Test that series theme influences passage suggestions."""
        from passage_suggestions import suggest_passages_for_series

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Hope in Hard Times", "Hope and Perseverance")

        suggestions = suggest_passages_for_series(conn, series_id, count=5)

        assert suggestions is not None
        assert len(suggestions) > 0
        conn.close()


class TestFilterByTestament:
    """Test suite for filtering passages by testament."""

    def test_should_filter_by_old_testament(self):
        """Test filtering for Old Testament passages only."""
        from passage_suggestions import filter_by_testament

        passages = [
            {'reference': 'Genesis 1:1', 'testament': 'OT'},
            {'reference': 'John 3:16', 'testament': 'NT'},
            {'reference': 'Psalm 23:1', 'testament': 'OT'},
            {'reference': 'Romans 8:28', 'testament': 'NT'}
        ]

        filtered = filter_by_testament(passages, 'OT')

        assert len(filtered) == 2
        assert all(p['testament'] == 'OT' for p in filtered)

    def test_should_filter_by_new_testament(self):
        """Test filtering for New Testament passages only."""
        from passage_suggestions import filter_by_testament

        passages = [
            {'reference': 'Genesis 1:1', 'testament': 'OT'},
            {'reference': 'John 3:16', 'testament': 'NT'},
            {'reference': 'Matthew 5:1', 'testament': 'NT'}
        ]

        filtered = filter_by_testament(passages, 'NT')

        assert len(filtered) == 2
        assert all(p['testament'] == 'NT' for p in filtered)

    def test_should_return_empty_list_when_no_matches(self):
        """Test that empty list is returned when no passages match."""
        from passage_suggestions import filter_by_testament

        passages = [
            {'reference': 'Genesis 1:1', 'testament': 'OT'},
            {'reference': 'Exodus 20:1', 'testament': 'OT'}
        ]

        filtered = filter_by_testament(passages, 'NT')

        assert filtered == []

    def test_should_handle_empty_passage_list(self):
        """Test handling of empty passage list."""
        from passage_suggestions import filter_by_testament

        filtered = filter_by_testament([], 'OT')

        assert filtered == []


class TestFilterByGenre:
    """Test suite for filtering passages by genre."""

    def test_should_filter_by_gospel_genre(self):
        """Test filtering for gospel passages."""
        from passage_suggestions import filter_by_genre

        passages = [
            {'reference': 'Matthew 5:1', 'genre': 'gospel'},
            {'reference': 'Romans 8:28', 'genre': 'epistle'},
            {'reference': 'John 3:16', 'genre': 'gospel'}
        ]

        filtered = filter_by_genre(passages, 'gospel')

        assert len(filtered) == 2
        assert all(p['genre'] == 'gospel' for p in filtered)

    def test_should_filter_by_epistle_genre(self):
        """Test filtering for epistle passages."""
        from passage_suggestions import filter_by_genre

        passages = [
            {'reference': 'Romans 8:28', 'genre': 'epistle'},
            {'reference': '1 Corinthians 13:1', 'genre': 'epistle'},
            {'reference': 'Genesis 1:1', 'genre': 'narrative'}
        ]

        filtered = filter_by_genre(passages, 'epistle')

        assert len(filtered) == 2

    def test_should_filter_by_wisdom_genre(self):
        """Test filtering for wisdom literature."""
        from passage_suggestions import filter_by_genre

        passages = [
            {'reference': 'Proverbs 3:5', 'genre': 'wisdom'},
            {'reference': 'Ecclesiastes 3:1', 'genre': 'wisdom'},
            {'reference': 'John 1:1', 'genre': 'gospel'}
        ]

        filtered = filter_by_genre(passages, 'wisdom')

        assert len(filtered) == 2

    def test_should_filter_by_prophecy_genre(self):
        """Test filtering for prophetic passages."""
        from passage_suggestions import filter_by_genre

        passages = [
            {'reference': 'Isaiah 53:1', 'genre': 'prophecy'},
            {'reference': 'Jeremiah 29:11', 'genre': 'prophecy'},
            {'reference': 'Psalm 23:1', 'genre': 'poetry'}
        ]

        filtered = filter_by_genre(passages, 'prophecy')

        assert len(filtered) == 2

    def test_should_handle_unknown_genre(self):
        """Test handling of unknown genre."""
        from passage_suggestions import filter_by_genre

        passages = [
            {'reference': 'Matthew 5:1', 'genre': 'gospel'},
            {'reference': 'Romans 8:28', 'genre': 'epistle'}
        ]

        filtered = filter_by_genre(passages, 'unknowngenre')

        assert filtered == []


class TestGetPassageContext:
    """Test suite for getting passage context/background."""

    def test_should_return_context_for_passage(self):
        """Test that context is returned for a passage."""
        from passage_suggestions import get_passage_context

        context = get_passage_context("John 3:16")

        assert context is not None
        assert isinstance(context, dict)

    def test_should_include_historical_background(self):
        """Test that context includes historical background."""
        from passage_suggestions import get_passage_context

        context = get_passage_context("Romans 8:28")

        assert 'background' in context or 'historical' in context or 'context' in context

    def test_should_include_book_info(self):
        """Test that context includes information about the book."""
        from passage_suggestions import get_passage_context

        context = get_passage_context("Genesis 1:1")

        assert 'book' in context or 'author' in context or 'testament' in context

    def test_should_handle_unknown_passage(self):
        """Test handling of unknown/invalid passage."""
        from passage_suggestions import get_passage_context

        context = get_passage_context("NotABook 99:99")

        assert context is None or context.get('error') is not None or context == {}


class TestSuggestComplementaryPassages:
    """Test suite for complementary passage suggestions."""

    def test_should_suggest_complementary_passages(self):
        """Test that complementary passages are suggested."""
        from passage_suggestions import suggest_complementary_passages

        suggestions = suggest_complementary_passages("John 3:16")

        assert suggestions is not None
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

    def test_should_return_related_passages(self):
        """Test that related/thematically connected passages are returned."""
        from passage_suggestions import suggest_complementary_passages

        # For John 3:16, might suggest other passages about salvation
        suggestions = suggest_complementary_passages("Romans 8:28")

        assert suggestions is not None
        for suggestion in suggestions:
            assert 'reference' in suggestion or 'scripture' in suggestion

    def test_should_handle_old_testament_passage(self):
        """Test complementary suggestions for OT passage."""
        from passage_suggestions import suggest_complementary_passages

        suggestions = suggest_complementary_passages("Psalm 23:1")

        assert suggestions is not None
        assert len(suggestions) > 0

    def test_should_suggest_cross_testament_connections(self):
        """Test that cross-testament passages are suggested when appropriate."""
        from passage_suggestions import suggest_complementary_passages

        # Isaiah 53 should connect to NT fulfillment passages
        suggestions = suggest_complementary_passages("Isaiah 53:5")

        assert suggestions is not None
        # Should have at least one suggestion


class TestRankPassagesByRelevance:
    """Test suite for ranking passages by relevance."""

    def test_should_rank_passages_by_relevance(self):
        """Test that passages are ranked by relevance to criteria."""
        from passage_suggestions import rank_passages_by_relevance

        passages = [
            {'reference': 'John 3:16', 'themes': 'love,salvation'},
            {'reference': 'Romans 8:28', 'themes': 'hope,providence'},
            {'reference': '1 John 4:8', 'themes': 'love,god'}
        ]
        criteria = {'theme': 'love'}

        ranked = rank_passages_by_relevance(passages, criteria)

        assert ranked is not None
        assert isinstance(ranked, list)
        assert len(ranked) == 3

    def test_should_return_most_relevant_first(self):
        """Test that most relevant passages come first."""
        from passage_suggestions import rank_passages_by_relevance

        passages = [
            {'reference': 'Genesis 1:1', 'themes': 'creation'},
            {'reference': '1 Corinthians 13:1', 'themes': 'love,charity'},
            {'reference': '1 John 4:8', 'themes': 'love,god,nature'}
        ]
        criteria = {'theme': 'love'}

        ranked = rank_passages_by_relevance(passages, criteria)

        # First result should contain 'love' in themes
        assert 'love' in ranked[0].get('themes', '')

    def test_should_handle_multiple_criteria(self):
        """Test ranking with multiple criteria."""
        from passage_suggestions import rank_passages_by_relevance

        passages = [
            {'reference': 'John 3:16', 'themes': 'love,salvation', 'testament': 'NT'},
            {'reference': 'Psalm 23:1', 'themes': 'comfort,shepherd', 'testament': 'OT'},
            {'reference': 'Romans 5:8', 'themes': 'love,grace', 'testament': 'NT'}
        ]
        criteria = {'theme': 'love', 'testament': 'NT'}

        ranked = rank_passages_by_relevance(passages, criteria)

        assert ranked is not None
        assert len(ranked) == 3

    def test_should_handle_empty_criteria(self):
        """Test ranking with empty criteria."""
        from passage_suggestions import rank_passages_by_relevance

        passages = [
            {'reference': 'John 3:16', 'themes': 'love'},
            {'reference': 'Romans 8:28', 'themes': 'hope'}
        ]

        ranked = rank_passages_by_relevance(passages, {})

        # Should return passages in some order
        assert ranked is not None
        assert len(ranked) == 2

    def test_should_handle_empty_passages_list(self):
        """Test ranking with empty passages list."""
        from passage_suggestions import rank_passages_by_relevance

        ranked = rank_passages_by_relevance([], {'theme': 'love'})

        assert ranked == []


class TestCacheSuggestions:
    """Test suite for caching passage suggestions."""

    def test_should_cache_suggestions(self):
        """Test that suggestions are cached."""
        from passage_suggestions import cache_suggestions, get_cached_suggestions

        conn = create_test_db()
        suggestions = [
            {'reference': 'John 3:16'},
            {'reference': 'Romans 8:28'}
        ]

        result = cache_suggestions(conn, 'theme:hope', suggestions, ttl=3600)

        assert result is True
        conn.close()

    def test_should_retrieve_cached_suggestions(self):
        """Test that cached suggestions can be retrieved."""
        from passage_suggestions import cache_suggestions, get_cached_suggestions

        conn = create_test_db()
        suggestions = [
            {'reference': 'John 3:16'},
            {'reference': 'Romans 8:28'}
        ]
        cache_suggestions(conn, 'theme:love', suggestions, ttl=3600)

        cached = get_cached_suggestions(conn, 'theme:love')

        assert cached is not None
        assert len(cached) == 2
        conn.close()

    def test_should_return_none_for_missing_cache(self):
        """Test that None is returned for missing cache entry."""
        from passage_suggestions import get_cached_suggestions

        conn = create_test_db()

        cached = get_cached_suggestions(conn, 'nonexistent:key')

        assert cached is None
        conn.close()

    def test_should_expire_cached_suggestions(self):
        """Test that expired cache entries are not returned."""
        from passage_suggestions import cache_suggestions, get_cached_suggestions

        conn = create_test_db()
        suggestions = [{'reference': 'John 3:16'}]

        # Cache with 0 TTL (already expired)
        cache_suggestions(conn, 'theme:expired', suggestions, ttl=0)

        cached = get_cached_suggestions(conn, 'theme:expired')

        assert cached is None
        conn.close()

    def test_should_update_existing_cache(self):
        """Test that caching overwrites existing entry."""
        from passage_suggestions import cache_suggestions, get_cached_suggestions

        conn = create_test_db()
        cache_suggestions(conn, 'theme:update', [{'reference': 'Old'}], ttl=3600)
        cache_suggestions(conn, 'theme:update', [{'reference': 'New'}], ttl=3600)

        cached = get_cached_suggestions(conn, 'theme:update')

        assert cached is not None
        assert cached[0]['reference'] == 'New'
        conn.close()


class TestEdgeCases:
    """Test suite for edge cases and special scenarios."""

    def test_should_handle_unicode_in_theme(self):
        """Test that unicode themes are handled."""
        from passage_suggestions import suggest_passages_for_theme

        suggestions = suggest_passages_for_theme("ἀγάπη")  # Greek for love

        assert suggestions is not None

    def test_should_handle_very_long_theme(self):
        """Test handling of very long theme string."""
        from passage_suggestions import suggest_passages_for_theme

        long_theme = "love " * 100
        suggestions = suggest_passages_for_theme(long_theme, count=3)

        assert suggestions is not None

    def test_should_handle_special_characters_in_passage_reference(self):
        """Test handling of special characters in passage reference."""
        from passage_suggestions import get_passage_context

        # Some versions use different notation
        context = get_passage_context("1 John 4:7-8")

        assert context is not None or context == {}

    def test_should_suggest_passages_with_database_lookup(self):
        """Test that database-stored passages are used in suggestions."""
        from passage_suggestions import suggest_passages_for_series

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Love Series", "Love")

        # Insert some known passages
        insert_sample_passage(conn, "1 Corinthians 13:4-7", "NT", "epistle", "love,patience")
        insert_sample_passage(conn, "1 John 4:7-8", "NT", "epistle", "love,god")
        insert_sample_passage(conn, "John 3:16", "NT", "gospel", "love,salvation")

        suggestions = suggest_passages_for_series(conn, series_id, count=5)

        assert suggestions is not None
        conn.close()


class TestIntegration:
    """Integration tests for passage suggestion workflows."""

    def test_should_filter_then_rank_passages(self):
        """Test combining filter and rank operations."""
        from passage_suggestions import (
            filter_by_testament,
            filter_by_genre,
            rank_passages_by_relevance
        )

        passages = [
            {'reference': 'John 3:16', 'testament': 'NT', 'genre': 'gospel', 'themes': 'love,salvation'},
            {'reference': 'Romans 8:28', 'testament': 'NT', 'genre': 'epistle', 'themes': 'hope'},
            {'reference': 'Genesis 1:1', 'testament': 'OT', 'genre': 'narrative', 'themes': 'creation'},
            {'reference': '1 John 4:8', 'testament': 'NT', 'genre': 'epistle', 'themes': 'love,god'}
        ]

        # Filter to NT only
        nt_passages = filter_by_testament(passages, 'NT')
        # Filter to epistles
        epistles = filter_by_genre(nt_passages, 'epistle')
        # Rank by theme
        ranked = rank_passages_by_relevance(epistles, {'theme': 'love'})

        assert len(ranked) == 2  # Romans 8:28 and 1 John 4:8

    def test_should_suggest_and_cache_workflow(self):
        """Test suggesting passages and caching the results."""
        from passage_suggestions import (
            suggest_passages_for_theme,
            cache_suggestions,
            get_cached_suggestions
        )

        conn = create_test_db()

        # First, get suggestions
        suggestions = suggest_passages_for_theme("forgiveness", count=5)

        # Cache them
        cache_suggestions(conn, 'theme:forgiveness', suggestions, ttl=3600)

        # Retrieve from cache
        cached = get_cached_suggestions(conn, 'theme:forgiveness')

        assert cached is not None
        assert len(cached) == 5
        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
