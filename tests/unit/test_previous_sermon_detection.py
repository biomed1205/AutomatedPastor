"""
Tests for Previous Sermon Detection (Issue #194)

Phase 8: Enhanced Features - Item 5 (FINAL)

Tests cover:
- Topic recency checking
- Scripture recency checking
- Last preached date tracking
- Similar sermon detection
- Recency threshold configuration
- Warning generation
- Warning dismissal
- Diversity reports
- Fresh topic suggestions
- Edge cases: no history, intentional repetition, series context

TDD Approach: All tests fail with ModuleNotFoundError until implementation.
NO MOCKS: Uses real SQLite :memory: database.
"""

import pytest
import sqlite3
from datetime import datetime, timedelta


def create_test_db():
    """Create a real SQLite in-memory database for testing."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create sermon archive tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sermons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            primary_scripture TEXT,
            topic TEXT,
            theme TEXT,
            date_preached DATE,
            word_count INTEGER,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create topic tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topic_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER,
            topic TEXT NOT NULL,
            date_used DATE,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id)
        )
    ''')

    # Create scripture tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scripture_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER,
            passage TEXT NOT NULL,
            date_used DATE,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id)
        )
    ''')

    # Create recency settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recency_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            threshold_days INTEGER DEFAULT 90,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create warnings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sermon_warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER,
            warning_type TEXT,
            warning_message TEXT,
            dismissed INTEGER DEFAULT 0,
            dismissed_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id)
        )
    ''')

    # Create series table for intentional repetition
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sermon_series (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            start_date DATE,
            end_date DATE,
            allows_repetition INTEGER DEFAULT 1
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS series_sermons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            series_id INTEGER,
            sermon_id INTEGER,
            order_in_series INTEGER,
            FOREIGN KEY (series_id) REFERENCES sermon_series(id),
            FOREIGN KEY (sermon_id) REFERENCES sermons(id)
        )
    ''')

    conn.commit()
    return conn


def insert_sample_sermon(conn, title, scripture, topic, days_ago=0):
    """Insert a sample sermon with calculated date."""
    cursor = conn.cursor()
    date_preached = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

    cursor.execute('''
        INSERT INTO sermons (title, primary_scripture, topic, date_preached, word_count)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, scripture, topic, date_preached, 2200))

    sermon_id = cursor.lastrowid

    # Track topic usage
    cursor.execute('''
        INSERT INTO topic_usage (sermon_id, topic, date_used)
        VALUES (?, ?, ?)
    ''', (sermon_id, topic, date_preached))

    # Track scripture usage
    cursor.execute('''
        INSERT INTO scripture_usage (sermon_id, passage, date_used)
        VALUES (?, ?, ?)
    ''', (sermon_id, scripture, date_preached))

    conn.commit()
    return sermon_id


def insert_sample_series(conn, name, sermon_ids):
    """Insert a sample sermon series."""
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO sermon_series (name, description, allows_repetition)
        VALUES (?, ?, ?)
    ''', (name, f'A series about {name}', 1))

    series_id = cursor.lastrowid

    for order, sermon_id in enumerate(sermon_ids, 1):
        cursor.execute('''
            INSERT INTO series_sermons (series_id, sermon_id, order_in_series)
            VALUES (?, ?, ?)
        ''', (series_id, sermon_id, order))

    conn.commit()
    return series_id


class TestCheckRecentTopic:
    """Tests for check_recent_topic function."""

    def test_should_detect_recent_topic(self):
        """Should detect when a topic was preached recently."""
        from previous_sermon_detection import check_recent_topic

        conn = create_test_db()
        insert_sample_sermon(conn, 'Grace and Mercy', 'Romans 5:8', 'grace', days_ago=30)

        result = check_recent_topic(conn, 'grace', days=90)

        assert result['is_recent'] is True
        assert result['days_since'] <= 30

        conn.close()

    def test_should_not_detect_old_topic(self):
        """Should not flag topic preached outside threshold."""
        from previous_sermon_detection import check_recent_topic

        conn = create_test_db()
        insert_sample_sermon(conn, 'Old Sermon', 'John 3:16', 'grace', days_ago=120)

        result = check_recent_topic(conn, 'grace', days=90)

        assert result['is_recent'] is False

        conn.close()

    def test_should_return_sermon_details(self):
        """Should return details of the recent sermon."""
        from previous_sermon_detection import check_recent_topic

        conn = create_test_db()
        insert_sample_sermon(conn, 'Grace Abounds', 'Romans 5:8', 'grace', days_ago=45)

        result = check_recent_topic(conn, 'grace', days=90)

        assert 'sermon_title' in result
        assert result['sermon_title'] == 'Grace Abounds'
        assert 'scripture' in result

        conn.close()

    def test_should_handle_no_history(self):
        """Should handle topic with no history."""
        from previous_sermon_detection import check_recent_topic

        conn = create_test_db()

        result = check_recent_topic(conn, 'brand_new_topic', days=90)

        assert result['is_recent'] is False
        assert result.get('last_preached') is None

        conn.close()

    def test_should_use_custom_threshold(self):
        """Should respect custom day threshold."""
        from previous_sermon_detection import check_recent_topic

        conn = create_test_db()
        insert_sample_sermon(conn, 'Test Sermon', 'John 1:1', 'forgiveness', days_ago=45)

        # 60 day threshold - should detect
        result_60 = check_recent_topic(conn, 'forgiveness', days=60)
        assert result_60['is_recent'] is True

        # 30 day threshold - should not detect
        result_30 = check_recent_topic(conn, 'forgiveness', days=30)
        assert result_30['is_recent'] is False

        conn.close()


class TestCheckRecentScripture:
    """Tests for check_recent_scripture function."""

    def test_should_detect_recent_scripture(self):
        """Should detect when scripture was used recently."""
        from previous_sermon_detection import check_recent_scripture

        conn = create_test_db()
        insert_sample_sermon(conn, 'Love Scripture', 'John 3:16', 'love', days_ago=20)

        result = check_recent_scripture(conn, 'John 3:16', days=90)

        assert result['is_recent'] is True
        assert result['days_since'] <= 20

        conn.close()

    def test_should_not_detect_old_scripture(self):
        """Should not flag scripture used outside threshold."""
        from previous_sermon_detection import check_recent_scripture

        conn = create_test_db()
        insert_sample_sermon(conn, 'Old Sermon', 'Romans 8:28', 'hope', days_ago=180)

        result = check_recent_scripture(conn, 'Romans 8:28', days=90)

        assert result['is_recent'] is False

        conn.close()

    def test_should_match_partial_scripture(self):
        """Should match scripture with verse ranges."""
        from previous_sermon_detection import check_recent_scripture

        conn = create_test_db()
        insert_sample_sermon(conn, 'Psalm Sermon', 'Psalm 23:1-6', 'comfort', days_ago=30)

        # Check for partial match
        result = check_recent_scripture(conn, 'Psalm 23', days=90)

        assert result['is_recent'] is True

        conn.close()

    def test_should_return_sermon_details(self):
        """Should return sermon details with scripture."""
        from previous_sermon_detection import check_recent_scripture

        conn = create_test_db()
        insert_sample_sermon(conn, 'Isaiah Teaching', 'Isaiah 40:31', 'strength', days_ago=25)

        result = check_recent_scripture(conn, 'Isaiah 40:31', days=90)

        assert 'sermon_title' in result
        assert result['sermon_title'] == 'Isaiah Teaching'
        assert 'topic' in result

        conn.close()


class TestGetLastPreachedDate:
    """Tests for get_last_preached_date function."""

    def test_should_get_last_preached_date(self):
        """Should return the last date a topic was preached."""
        from previous_sermon_detection import get_last_preached_date

        conn = create_test_db()
        insert_sample_sermon(conn, 'Recent Grace', 'Rom 5:8', 'grace', days_ago=10)
        insert_sample_sermon(conn, 'Old Grace', 'Eph 2:8', 'grace', days_ago=100)

        result = get_last_preached_date(conn, 'grace')

        expected_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        assert result == expected_date

        conn.close()

    def test_should_return_none_for_new_topic(self):
        """Should return None for never-preached topic."""
        from previous_sermon_detection import get_last_preached_date

        conn = create_test_db()

        result = get_last_preached_date(conn, 'never_preached_topic')

        assert result is None

        conn.close()

    def test_should_get_last_date_for_scripture(self):
        """Should also work for scripture passages."""
        from previous_sermon_detection import get_last_preached_date

        conn = create_test_db()
        insert_sample_sermon(conn, 'John Sermon', 'John 3:16', 'love', days_ago=15)

        result = get_last_preached_date(conn, 'John 3:16', is_scripture=True)

        expected_date = (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')
        assert result == expected_date

        conn.close()


class TestGetSimilarRecentSermons:
    """Tests for get_similar_recent_sermons function."""

    def test_should_find_similar_sermons_by_topic(self):
        """Should find sermons with similar topics."""
        from previous_sermon_detection import get_similar_recent_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, 'Grace Part 1', 'Rom 5:8', 'grace', days_ago=30)
        insert_sample_sermon(conn, 'Grace Part 2', 'Eph 2:8', 'grace', days_ago=60)

        sermon_params = {'topic': 'grace', 'scripture': 'Titus 2:11'}
        result = get_similar_recent_sermons(conn, sermon_params)

        assert len(result) >= 2

        conn.close()

    def test_should_find_similar_sermons_by_scripture(self):
        """Should find sermons with similar scripture."""
        from previous_sermon_detection import get_similar_recent_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, 'Romans Study', 'Romans 8:28', 'providence', days_ago=45)

        sermon_params = {'topic': 'hope', 'scripture': 'Romans 8:28'}
        result = get_similar_recent_sermons(conn, sermon_params)

        assert len(result) >= 1
        assert result[0]['primary_scripture'] == 'Romans 8:28'

        conn.close()

    def test_should_return_empty_for_unique_content(self):
        """Should return empty list for unique sermon."""
        from previous_sermon_detection import get_similar_recent_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, 'Other Sermon', 'Genesis 1:1', 'creation', days_ago=30)

        sermon_params = {'topic': 'eschatology', 'scripture': 'Revelation 21:1'}
        result = get_similar_recent_sermons(conn, sermon_params)

        assert len(result) == 0

        conn.close()

    def test_should_include_similarity_score(self):
        """Should include similarity score in results."""
        from previous_sermon_detection import get_similar_recent_sermons

        conn = create_test_db()
        insert_sample_sermon(conn, 'Love Sermon', 'John 3:16', 'love', days_ago=20)

        sermon_params = {'topic': 'love', 'scripture': '1 John 4:8'}
        result = get_similar_recent_sermons(conn, sermon_params)

        assert len(result) >= 1
        assert 'similarity_score' in result[0]
        assert result[0]['similarity_score'] > 0

        conn.close()


class TestSetRecencyThreshold:
    """Tests for set_recency_threshold function."""

    def test_should_set_threshold(self):
        """Should set the recency threshold days."""
        from previous_sermon_detection import set_recency_threshold

        conn = create_test_db()

        result = set_recency_threshold(conn, 60)

        assert result is True

        cursor = conn.cursor()
        cursor.execute('SELECT threshold_days FROM recency_settings ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        assert row['threshold_days'] == 60

        conn.close()

    def test_should_update_existing_threshold(self):
        """Should update existing threshold setting."""
        from previous_sermon_detection import set_recency_threshold

        conn = create_test_db()

        set_recency_threshold(conn, 90)
        set_recency_threshold(conn, 120)

        cursor = conn.cursor()
        cursor.execute('SELECT threshold_days FROM recency_settings ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        assert row['threshold_days'] == 120

        conn.close()

    def test_should_reject_invalid_threshold(self):
        """Should reject negative or zero threshold."""
        from previous_sermon_detection import set_recency_threshold

        conn = create_test_db()

        result_zero = set_recency_threshold(conn, 0)
        result_negative = set_recency_threshold(conn, -30)

        assert result_zero is False
        assert result_negative is False

        conn.close()

    def test_should_get_current_threshold(self):
        """Should retrieve current threshold."""
        from previous_sermon_detection import set_recency_threshold, get_recency_threshold

        conn = create_test_db()
        set_recency_threshold(conn, 75)

        result = get_recency_threshold(conn)

        assert result == 75

        conn.close()


class TestGetWarningForSermon:
    """Tests for get_warning_for_sermon function."""

    def test_should_generate_topic_warning(self):
        """Should generate warning for recent topic."""
        from previous_sermon_detection import get_warning_for_sermon

        conn = create_test_db()
        insert_sample_sermon(conn, 'Recent Grace', 'Rom 5:8', 'grace', days_ago=30)

        sermon_params = {'topic': 'grace', 'scripture': 'Eph 2:8', 'title': 'More Grace'}
        result = get_warning_for_sermon(conn, sermon_params)

        assert len(result) >= 1
        assert any(w['warning_type'] == 'recent_topic' for w in result)

        conn.close()

    def test_should_generate_scripture_warning(self):
        """Should generate warning for recent scripture."""
        from previous_sermon_detection import get_warning_for_sermon

        conn = create_test_db()
        insert_sample_sermon(conn, 'John Sermon', 'John 3:16', 'love', days_ago=45)

        sermon_params = {'topic': 'salvation', 'scripture': 'John 3:16', 'title': 'Saved'}
        result = get_warning_for_sermon(conn, sermon_params)

        assert len(result) >= 1
        assert any(w['warning_type'] == 'recent_scripture' for w in result)

        conn.close()

    def test_should_return_no_warnings_for_fresh_content(self):
        """Should return empty warnings for fresh content."""
        from previous_sermon_detection import get_warning_for_sermon

        conn = create_test_db()
        # Insert old sermon
        insert_sample_sermon(conn, 'Old Sermon', 'Genesis 1:1', 'creation', days_ago=365)

        sermon_params = {'topic': 'stewardship', 'scripture': 'Matthew 25:14', 'title': 'Talents'}
        result = get_warning_for_sermon(conn, sermon_params)

        assert len(result) == 0

        conn.close()

    def test_should_include_warning_details(self):
        """Should include detailed warning information."""
        from previous_sermon_detection import get_warning_for_sermon

        conn = create_test_db()
        insert_sample_sermon(conn, 'Forgiveness Sermon', 'Matt 18:21', 'forgiveness', days_ago=20)

        sermon_params = {'topic': 'forgiveness', 'scripture': 'Col 3:13', 'title': 'Forgive Again'}
        result = get_warning_for_sermon(conn, sermon_params)

        warning = result[0]
        assert 'warning_message' in warning
        assert 'previous_sermon' in warning
        assert 'days_since' in warning

        conn.close()


class TestDismissWarning:
    """Tests for dismiss_warning function."""

    def test_should_dismiss_warning(self):
        """Should dismiss a warning with reason."""
        from previous_sermon_detection import dismiss_warning

        conn = create_test_db()
        cursor = conn.cursor()

        # Insert a warning
        cursor.execute('''
            INSERT INTO sermon_warnings (sermon_id, warning_type, warning_message)
            VALUES (?, ?, ?)
        ''', (1, 'recent_topic', 'Topic was preached 30 days ago'))
        warning_id = cursor.lastrowid
        conn.commit()

        result = dismiss_warning(conn, 1, warning_id, reason='Intentional series')

        assert result is True

        cursor.execute('SELECT dismissed, dismissed_reason FROM sermon_warnings WHERE id = ?', (warning_id,))
        row = cursor.fetchone()
        assert row['dismissed'] == 1
        assert row['dismissed_reason'] == 'Intentional series'

        conn.close()

    def test_should_return_false_for_nonexistent(self):
        """Should return False for nonexistent warning."""
        from previous_sermon_detection import dismiss_warning

        conn = create_test_db()

        result = dismiss_warning(conn, 1, 9999, reason='Test')

        assert result is False

        conn.close()

    def test_should_require_reason(self):
        """Should require a reason for dismissal."""
        from previous_sermon_detection import dismiss_warning

        conn = create_test_db()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO sermon_warnings (sermon_id, warning_type, warning_message)
            VALUES (?, ?, ?)
        ''', (1, 'recent_topic', 'Test warning'))
        warning_id = cursor.lastrowid
        conn.commit()

        result = dismiss_warning(conn, 1, warning_id, reason='')

        assert result is False

        conn.close()


class TestGenerateDiversityReport:
    """Tests for generate_diversity_report function."""

    def test_should_generate_report(self):
        """Should generate a diversity report."""
        from previous_sermon_detection import generate_diversity_report

        conn = create_test_db()
        insert_sample_sermon(conn, 'Sermon 1', 'Matt 5:1', 'beatitudes', days_ago=30)
        insert_sample_sermon(conn, 'Sermon 2', 'Rom 8:28', 'providence', days_ago=60)
        insert_sample_sermon(conn, 'Sermon 3', 'John 3:16', 'salvation', days_ago=90)

        result = generate_diversity_report(conn, months=6)

        assert 'total_sermons' in result
        assert result['total_sermons'] == 3
        assert 'unique_topics' in result
        assert 'unique_scriptures' in result

        conn.close()

    def test_should_include_topic_frequency(self):
        """Should include topic frequency breakdown."""
        from previous_sermon_detection import generate_diversity_report

        conn = create_test_db()
        insert_sample_sermon(conn, 'Grace 1', 'Rom 5:8', 'grace', days_ago=30)
        insert_sample_sermon(conn, 'Grace 2', 'Eph 2:8', 'grace', days_ago=60)
        insert_sample_sermon(conn, 'Love 1', 'John 3:16', 'love', days_ago=90)

        result = generate_diversity_report(conn, months=6)

        assert 'topic_frequency' in result
        assert result['topic_frequency']['grace'] == 2
        assert result['topic_frequency']['love'] == 1

        conn.close()

    def test_should_include_scripture_coverage(self):
        """Should include scripture book coverage."""
        from previous_sermon_detection import generate_diversity_report

        conn = create_test_db()
        insert_sample_sermon(conn, 'Matt Sermon', 'Matthew 5:1', 'beatitudes', days_ago=30)
        insert_sample_sermon(conn, 'John Sermon', 'John 3:16', 'love', days_ago=60)
        insert_sample_sermon(conn, 'Rom Sermon', 'Romans 8:28', 'hope', days_ago=90)

        result = generate_diversity_report(conn, months=6)

        assert 'scripture_books' in result
        assert len(result['scripture_books']) >= 3

        conn.close()

    def test_should_identify_overused_topics(self):
        """Should identify topics used too frequently."""
        from previous_sermon_detection import generate_diversity_report

        conn = create_test_db()
        # Insert same topic multiple times
        for i in range(5):
            insert_sample_sermon(conn, f'Grace {i}', f'Text {i}', 'grace', days_ago=30+i*7)

        result = generate_diversity_report(conn, months=6)

        assert 'overused_topics' in result
        assert 'grace' in result['overused_topics']

        conn.close()

    def test_should_suggest_underrepresented_areas(self):
        """Should suggest underrepresented areas."""
        from previous_sermon_detection import generate_diversity_report

        conn = create_test_db()
        insert_sample_sermon(conn, 'NT Sermon', 'Matthew 5:1', 'beatitudes', days_ago=30)

        result = generate_diversity_report(conn, months=12)

        assert 'suggestions' in result
        # Should suggest OT coverage

        conn.close()


class TestSuggestFreshTopics:
    """Tests for suggest_fresh_topics function."""

    def test_should_suggest_topics(self):
        """Should suggest topics not recently covered."""
        from previous_sermon_detection import suggest_fresh_topics

        conn = create_test_db()
        insert_sample_sermon(conn, 'Grace Sermon', 'Rom 5:8', 'grace', days_ago=30)
        insert_sample_sermon(conn, 'Love Sermon', 'John 3:16', 'love', days_ago=60)

        result = suggest_fresh_topics(conn)

        assert isinstance(result, list)
        assert len(result) > 0
        # Should not include recently used topics
        suggested_names = [t['topic'] for t in result]
        assert 'grace' not in suggested_names

        conn.close()

    def test_should_include_liturgical_suggestions(self):
        """Should include liturgical calendar suggestions."""
        from previous_sermon_detection import suggest_fresh_topics

        conn = create_test_db()

        result = suggest_fresh_topics(conn, include_liturgical=True)

        assert any(t.get('source') == 'liturgical' for t in result)

        conn.close()

    def test_should_prioritize_by_gap(self):
        """Should prioritize topics by time since last use."""
        from previous_sermon_detection import suggest_fresh_topics

        conn = create_test_db()
        insert_sample_sermon(conn, 'Old Hope', 'Rom 15:13', 'hope', days_ago=300)
        insert_sample_sermon(conn, 'Recent Faith', 'Heb 11:1', 'faith', days_ago=30)

        result = suggest_fresh_topics(conn)

        # Hope should rank higher due to longer gap
        hope_topics = [t for t in result if t.get('topic') == 'hope']
        faith_topics = [t for t in result if t.get('topic') == 'faith']

        if hope_topics and faith_topics:
            assert hope_topics[0].get('priority', 0) >= faith_topics[0].get('priority', 0)

        conn.close()


class TestSeriesContext:
    """Tests for sermon series context handling."""

    def test_should_allow_repetition_in_series(self):
        """Should allow intentional repetition within a series."""
        from previous_sermon_detection import get_warning_for_sermon

        conn = create_test_db()

        # Create sermon and series
        sermon_id = insert_sample_sermon(conn, 'Grace Part 1', 'Rom 5:8', 'grace', days_ago=7)
        series_id = insert_sample_series(conn, 'Grace Series', [sermon_id])

        sermon_params = {
            'topic': 'grace',
            'scripture': 'Eph 2:8',
            'title': 'Grace Part 2',
            'series_id': series_id
        }
        result = get_warning_for_sermon(conn, sermon_params)

        # Should not warn when part of same series
        topic_warnings = [w for w in result if w['warning_type'] == 'recent_topic']
        assert len(topic_warnings) == 0 or all(w.get('is_series') for w in topic_warnings)

        conn.close()

    def test_should_track_series_progression(self):
        """Should track sermon progression within series."""
        from previous_sermon_detection import get_series_context

        conn = create_test_db()

        sermon1_id = insert_sample_sermon(conn, 'Part 1', 'Rom 1:1', 'romans', days_ago=14)
        sermon2_id = insert_sample_sermon(conn, 'Part 2', 'Rom 2:1', 'romans', days_ago=7)
        series_id = insert_sample_series(conn, 'Romans Study', [sermon1_id, sermon2_id])

        result = get_series_context(conn, series_id)

        assert result['sermon_count'] == 2
        assert 'next_suggested' in result

        conn.close()


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_should_handle_empty_database(self):
        """Should handle database with no sermons."""
        from previous_sermon_detection import check_recent_topic, generate_diversity_report

        conn = create_test_db()

        topic_result = check_recent_topic(conn, 'any_topic', days=90)
        report_result = generate_diversity_report(conn, months=12)

        assert topic_result['is_recent'] is False
        assert report_result['total_sermons'] == 0

        conn.close()

    def test_should_handle_special_characters_in_topic(self):
        """Should handle special characters in topics."""
        from previous_sermon_detection import check_recent_topic

        conn = create_test_db()
        insert_sample_sermon(conn, 'Test', 'John 1:1', "God's Grace & Love", days_ago=30)

        result = check_recent_topic(conn, "God's Grace & Love", days=90)

        assert result['is_recent'] is True

        conn.close()

    def test_should_handle_unicode_content(self):
        """Should handle unicode in topics and scriptures."""
        from previous_sermon_detection import check_recent_topic

        conn = create_test_db()
        insert_sample_sermon(conn, 'Greek Study', 'John 1:1', 'logos (λόγος)', days_ago=30)

        result = check_recent_topic(conn, 'logos (λόγος)', days=90)

        assert result['is_recent'] is True

        conn.close()

    def test_should_handle_case_insensitive_matching(self):
        """Should match topics case-insensitively."""
        from previous_sermon_detection import check_recent_topic

        conn = create_test_db()
        insert_sample_sermon(conn, 'Grace Sermon', 'Rom 5:8', 'Grace', days_ago=30)

        result = check_recent_topic(conn, 'grace', days=90)

        assert result['is_recent'] is True

        conn.close()

    def test_should_handle_boundary_dates(self):
        """Should correctly handle boundary date conditions."""
        from previous_sermon_detection import check_recent_topic

        conn = create_test_db()
        insert_sample_sermon(conn, 'Boundary Test', 'John 1:1', 'boundary', days_ago=90)

        # Exactly at threshold
        result_at = check_recent_topic(conn, 'boundary', days=90)
        # Just outside threshold
        result_outside = check_recent_topic(conn, 'boundary', days=89)

        assert result_at['is_recent'] is True  # Inclusive of boundary
        assert result_outside['is_recent'] is False

        conn.close()

    def test_should_handle_multiple_warnings(self):
        """Should generate multiple warnings when applicable."""
        from previous_sermon_detection import get_warning_for_sermon

        conn = create_test_db()
        # Insert sermon with both topic and scripture recently used
        insert_sample_sermon(conn, 'Full Match', 'John 3:16', 'salvation', days_ago=20)

        sermon_params = {
            'topic': 'salvation',
            'scripture': 'John 3:16',
            'title': 'Saved Again'
        }
        result = get_warning_for_sermon(conn, sermon_params)

        # Should have both topic and scripture warnings
        assert len(result) >= 2
        warning_types = [w['warning_type'] for w in result]
        assert 'recent_topic' in warning_types
        assert 'recent_scripture' in warning_types

        conn.close()


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_should_complete_warning_workflow(self):
        """Should complete full warning check and dismiss workflow."""
        from previous_sermon_detection import (
            get_warning_for_sermon,
            dismiss_warning,
            check_recent_topic
        )

        conn = create_test_db()

        # Setup: Create recent sermon
        insert_sample_sermon(conn, 'Recent Topic', 'Matt 5:1', 'beatitudes', days_ago=30)

        # Check for warnings
        sermon_params = {'topic': 'beatitudes', 'scripture': 'Matt 5:3', 'title': 'Blessed'}
        warnings = get_warning_for_sermon(conn, sermon_params)

        assert len(warnings) >= 1

        # Store warning
        cursor = conn.cursor()
        for warning in warnings:
            cursor.execute('''
                INSERT INTO sermon_warnings (sermon_id, warning_type, warning_message)
                VALUES (?, ?, ?)
            ''', (1, warning['warning_type'], warning['warning_message']))
        conn.commit()

        # Dismiss warning with reason
        warning_id = cursor.lastrowid
        dismiss_result = dismiss_warning(conn, 1, warning_id, reason='Continuing series')

        assert dismiss_result is True

        conn.close()

    def test_should_complete_diversity_analysis(self):
        """Should complete full diversity analysis workflow."""
        from previous_sermon_detection import (
            generate_diversity_report,
            suggest_fresh_topics
        )

        conn = create_test_db()

        # Create diverse sermon history
        insert_sample_sermon(conn, 'NT Sermon 1', 'Matthew 5:1', 'beatitudes', days_ago=30)
        insert_sample_sermon(conn, 'NT Sermon 2', 'John 3:16', 'love', days_ago=60)
        insert_sample_sermon(conn, 'NT Sermon 3', 'Romans 8:28', 'hope', days_ago=90)
        insert_sample_sermon(conn, 'NT Sermon 4', 'Galatians 5:22', 'fruit', days_ago=120)

        # Generate report
        report = generate_diversity_report(conn, months=12)

        assert report['total_sermons'] == 4
        assert report['unique_topics'] == 4

        # Get suggestions
        suggestions = suggest_fresh_topics(conn)

        assert isinstance(suggestions, list)

        conn.close()

    def test_should_handle_year_of_sermons(self):
        """Should handle a full year of sermon data."""
        from previous_sermon_detection import generate_diversity_report

        conn = create_test_db()

        # Create approximately 52 sermons (one per week)
        topics = ['grace', 'love', 'faith', 'hope', 'peace', 'joy', 'patience',
                  'kindness', 'goodness', 'faithfulness', 'gentleness', 'self-control']

        for i in range(52):
            topic = topics[i % len(topics)]
            days_ago = i * 7
            insert_sample_sermon(conn, f'Sermon {i}', f'Text {i}', topic, days_ago=days_ago)

        report = generate_diversity_report(conn, months=12)

        assert report['total_sermons'] == 52
        assert 'topic_frequency' in report
        assert 'overused_topics' in report or 'balanced' in str(report)

        conn.close()
