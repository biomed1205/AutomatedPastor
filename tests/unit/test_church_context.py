"""
Tests for church context awareness functionality.

Tests storing and utilizing church-specific context (congregation
demographics, theology preferences, etc.) to tailor sermon generation.

TDD: All tests should fail with ModuleNotFoundError until implementation.
NO MOCKS: Uses real SQLite in-memory database.

PHASE 8: Enhanced Features - Item 4
"""

import sqlite3
import pytest
import json
from datetime import datetime


def create_test_db():
    """Create test database with church context tables."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Church profile table
    cursor.execute('''
        CREATE TABLE church_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            denomination TEXT,
            location TEXT,
            size TEXT,
            founded_year INTEGER,
            website TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Congregation demographics table
    cursor.execute('''
        CREATE TABLE congregation_demographics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            church_id INTEGER NOT NULL,
            age_distribution TEXT,
            education_level TEXT,
            political_leaning TEXT,
            economic_background TEXT,
            cultural_diversity TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (church_id) REFERENCES church_profile(id)
        )
    ''')

    # Pastor preferences table
    cursor.execute('''
        CREATE TABLE pastor_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            church_id INTEGER NOT NULL,
            sermon_length_min INTEGER DEFAULT 2000,
            sermon_length_max INTEGER DEFAULT 2500,
            illustration_preference TEXT,
            application_style TEXT,
            use_personal_stories INTEGER DEFAULT 0,
            humor_level TEXT DEFAULT 'moderate',
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (church_id) REFERENCES church_profile(id)
        )
    ''')

    # Theological context table
    cursor.execute('''
        CREATE TABLE theological_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            church_id INTEGER NOT NULL,
            tradition TEXT,
            emphasis TEXT,
            scripture_approach TEXT,
            social_stance TEXT,
            topics_to_avoid TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (church_id) REFERENCES church_profile(id)
        )
    ''')

    conn.commit()
    return conn


def insert_church_profile(conn, name="University UMC",
                         denomination="United Methodist",
                         location="Baton Rouge, LA", size="medium"):
    """Insert a sample church profile."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO church_profile (name, denomination, location, size)
        VALUES (?, ?, ?, ?)
    ''', (name, denomination, location, size))
    conn.commit()
    return cursor.lastrowid


def insert_demographics(conn, church_id, age_distribution="mixed",
                       education_level="college-educated",
                       political_leaning="purple"):
    """Insert congregation demographics."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO congregation_demographics
        (church_id, age_distribution, education_level, political_leaning)
        VALUES (?, ?, ?, ?)
    ''', (church_id, age_distribution, education_level, political_leaning))
    conn.commit()
    return cursor.lastrowid


def insert_pastor_preferences(conn, church_id, sermon_length_min=2000,
                             sermon_length_max=2500):
    """Insert pastor preferences."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO pastor_preferences
        (church_id, sermon_length_min, sermon_length_max)
        VALUES (?, ?, ?)
    ''', (church_id, sermon_length_min, sermon_length_max))
    conn.commit()
    return cursor.lastrowid


def insert_theological_context(conn, church_id, tradition="Wesleyan",
                              emphasis="grace-focused"):
    """Insert theological context."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO theological_context (church_id, tradition, emphasis)
        VALUES (?, ?, ?)
    ''', (church_id, tradition, emphasis))
    conn.commit()
    return cursor.lastrowid


class TestCreateChurchProfile:
    """Tests for create_church_profile function."""

    def test_should_create_church_profile(self):
        """Test creating a new church profile."""
        from church_context import create_church_profile

        conn = create_test_db()

        result = create_church_profile(conn, name="First Baptist Church",
                                       denomination="Baptist",
                                       location="Dallas, TX")

        assert result['success'] is True
        assert result['church_id'] is not None

    def test_should_store_all_fields(self):
        """Test storing all profile fields."""
        from church_context import create_church_profile

        conn = create_test_db()

        result = create_church_profile(conn,
                                       name="Grace Community",
                                       denomination="Non-denominational",
                                       location="Phoenix, AZ",
                                       size="large",
                                       founded_year=1985,
                                       website="https://gracecc.org")

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM church_profile WHERE id = ?',
                      (result['church_id'],))
        row = cursor.fetchone()
        assert row['name'] == "Grace Community"
        assert row['denomination'] == "Non-denominational"
        assert row['founded_year'] == 1985

    def test_should_reject_without_name(self):
        """Test rejecting profile without name."""
        from church_context import create_church_profile

        conn = create_test_db()

        result = create_church_profile(conn, denomination="Methodist")

        assert result['success'] is False

    def test_should_return_error_for_duplicate_name(self):
        """Test handling duplicate church names."""
        from church_context import create_church_profile

        conn = create_test_db()

        create_church_profile(conn, name="Unique Church")
        result = create_church_profile(conn, name="Unique Church")

        assert result['success'] is False or 'warning' in result


class TestUpdateChurchProfile:
    """Tests for update_church_profile function."""

    def test_should_update_profile_fields(self):
        """Test updating profile fields."""
        from church_context import update_church_profile

        conn = create_test_db()
        church_id = insert_church_profile(conn, name="Old Name")

        result = update_church_profile(conn, church_id, name="New Name")

        assert result['success'] is True

        cursor = conn.cursor()
        cursor.execute('SELECT name FROM church_profile WHERE id = ?',
                      (church_id,))
        row = cursor.fetchone()
        assert row['name'] == "New Name"

    def test_should_update_timestamp(self):
        """Test updating timestamp on profile change."""
        from church_context import update_church_profile

        conn = create_test_db()
        church_id = insert_church_profile(conn)

        result = update_church_profile(conn, church_id, size="large")

        cursor = conn.cursor()
        cursor.execute('SELECT updated_at FROM church_profile WHERE id = ?',
                      (church_id,))
        row = cursor.fetchone()
        assert row['updated_at'] is not None

    def test_should_return_error_for_nonexistent(self):
        """Test error for non-existent church."""
        from church_context import update_church_profile

        conn = create_test_db()

        result = update_church_profile(conn, 9999, name="New Name")

        assert result['success'] is False


class TestGetChurchProfile:
    """Tests for get_church_profile function."""

    def test_should_get_church_profile(self):
        """Test getting church profile."""
        from church_context import get_church_profile

        conn = create_test_db()
        church_id = insert_church_profile(conn, name="Test Church",
                                         denomination="Methodist")

        result = get_church_profile(conn, church_id)

        assert result is not None
        assert result['name'] == "Test Church"
        assert result['denomination'] == "Methodist"

    def test_should_include_all_sections(self):
        """Test including all profile sections."""
        from church_context import get_church_profile

        conn = create_test_db()
        church_id = insert_church_profile(conn)
        insert_demographics(conn, church_id)
        insert_pastor_preferences(conn, church_id)
        insert_theological_context(conn, church_id)

        result = get_church_profile(conn, church_id)

        assert 'demographics' in result
        assert 'preferences' in result
        assert 'theology' in result

    def test_should_return_none_for_nonexistent(self):
        """Test returning None for non-existent church."""
        from church_context import get_church_profile

        conn = create_test_db()

        result = get_church_profile(conn, 9999)

        assert result is None


class TestSetCongregationDemographics:
    """Tests for set_congregation_demographics function."""

    def test_should_set_demographics(self):
        """Test setting congregation demographics."""
        from church_context import set_congregation_demographics

        conn = create_test_db()
        church_id = insert_church_profile(conn)

        result = set_congregation_demographics(conn, church_id, {
            'age_distribution': 'mixed',
            'education_level': 'graduate-educated',
            'political_leaning': 'purple'
        })

        assert result['success'] is True

    def test_should_store_all_fields(self):
        """Test storing all demographic fields."""
        from church_context import set_congregation_demographics

        conn = create_test_db()
        church_id = insert_church_profile(conn)

        set_congregation_demographics(conn, church_id, {
            'age_distribution': 'young-families',
            'education_level': 'mixed',
            'political_leaning': 'moderate',
            'economic_background': 'middle-class',
            'cultural_diversity': 'diverse'
        })

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM congregation_demographics WHERE church_id = ?',
                      (church_id,))
        row = cursor.fetchone()
        assert row['cultural_diversity'] == 'diverse'

    def test_should_update_existing_demographics(self):
        """Test updating existing demographics."""
        from church_context import set_congregation_demographics

        conn = create_test_db()
        church_id = insert_church_profile(conn)
        insert_demographics(conn, church_id, age_distribution="elderly")

        set_congregation_demographics(conn, church_id, {
            'age_distribution': 'young-families'
        })

        cursor = conn.cursor()
        cursor.execute('SELECT age_distribution FROM congregation_demographics WHERE church_id = ?',
                      (church_id,))
        row = cursor.fetchone()
        assert row['age_distribution'] == 'young-families'


class TestGetCongregationDemographics:
    """Tests for get_congregation_demographics function."""

    def test_should_get_demographics(self):
        """Test getting congregation demographics."""
        from church_context import get_congregation_demographics

        conn = create_test_db()
        church_id = insert_church_profile(conn)
        insert_demographics(conn, church_id, age_distribution="mixed",
                          education_level="college-educated")

        result = get_congregation_demographics(conn, church_id)

        assert result is not None
        assert result['age_distribution'] == 'mixed'
        assert result['education_level'] == 'college-educated'

    def test_should_return_none_for_no_demographics(self):
        """Test returning None when no demographics set."""
        from church_context import get_congregation_demographics

        conn = create_test_db()
        church_id = insert_church_profile(conn)

        result = get_congregation_demographics(conn, church_id)

        assert result is None


class TestSetPastorPreferences:
    """Tests for set_pastor_preferences function."""

    def test_should_set_preferences(self):
        """Test setting pastor preferences."""
        from church_context import set_pastor_preferences

        conn = create_test_db()
        church_id = insert_church_profile(conn)

        result = set_pastor_preferences(conn, church_id, {
            'sermon_length_min': 2000,
            'sermon_length_max': 2500,
            'illustration_preference': 'contemporary',
            'use_personal_stories': False
        })

        assert result['success'] is True

    def test_should_store_all_preferences(self):
        """Test storing all preference fields."""
        from church_context import set_pastor_preferences

        conn = create_test_db()
        church_id = insert_church_profile(conn)

        set_pastor_preferences(conn, church_id, {
            'sermon_length_min': 1800,
            'sermon_length_max': 2200,
            'illustration_preference': 'literary',
            'application_style': 'practical',
            'use_personal_stories': True,
            'humor_level': 'minimal'
        })

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pastor_preferences WHERE church_id = ?',
                      (church_id,))
        row = cursor.fetchone()
        assert row['humor_level'] == 'minimal'


class TestGetPastorPreferences:
    """Tests for get_pastor_preferences function."""

    def test_should_get_preferences(self):
        """Test getting pastor preferences."""
        from church_context import get_pastor_preferences

        conn = create_test_db()
        church_id = insert_church_profile(conn)
        insert_pastor_preferences(conn, church_id, sermon_length_min=2000,
                                 sermon_length_max=2500)

        result = get_pastor_preferences(conn, church_id)

        assert result is not None
        assert result['sermon_length_min'] == 2000
        assert result['sermon_length_max'] == 2500

    def test_should_return_defaults_when_not_set(self):
        """Test returning defaults when preferences not set."""
        from church_context import get_pastor_preferences

        conn = create_test_db()
        church_id = insert_church_profile(conn)

        result = get_pastor_preferences(conn, church_id)

        # Should return defaults or None
        assert result is None or result.get('sermon_length_min', 2000) == 2000


class TestSetTheologicalContext:
    """Tests for set_theological_context function."""

    def test_should_set_theological_context(self):
        """Test setting theological context."""
        from church_context import set_theological_context

        conn = create_test_db()
        church_id = insert_church_profile(conn)

        result = set_theological_context(conn, church_id, {
            'tradition': 'Wesleyan',
            'emphasis': 'grace-focused, inclusive'
        })

        assert result['success'] is True

    def test_should_store_all_theology_fields(self):
        """Test storing all theology fields."""
        from church_context import set_theological_context

        conn = create_test_db()
        church_id = insert_church_profile(conn)

        set_theological_context(conn, church_id, {
            'tradition': 'Reformed',
            'emphasis': 'scripture-centered',
            'scripture_approach': 'expository',
            'social_stance': 'moderate',
            'topics_to_avoid': 'partisan politics'
        })

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM theological_context WHERE church_id = ?',
                      (church_id,))
        row = cursor.fetchone()
        assert row['topics_to_avoid'] == 'partisan politics'


class TestApplyContextToGeneration:
    """Tests for apply_context_to_generation function."""

    def test_should_apply_context_to_params(self):
        """Test applying context to sermon generation params."""
        from church_context import apply_context_to_generation

        conn = create_test_db()
        church_id = insert_church_profile(conn, denomination="Methodist")
        insert_pastor_preferences(conn, church_id, sermon_length_min=2000)
        insert_theological_context(conn, church_id, tradition="Wesleyan")

        params = {'scripture': 'John 3:16', 'theme': 'grace'}
        result = apply_context_to_generation(conn, church_id, params)

        assert result is not None
        assert result.get('tradition') == 'Wesleyan' or 'context' in result

    def test_should_include_word_count_range(self):
        """Test including word count range from preferences."""
        from church_context import apply_context_to_generation

        conn = create_test_db()
        church_id = insert_church_profile(conn)
        insert_pastor_preferences(conn, church_id,
                                 sermon_length_min=1800,
                                 sermon_length_max=2200)

        params = {'scripture': 'Matthew 5:1-12'}
        result = apply_context_to_generation(conn, church_id, params)

        assert 'word_count' in result or 'length' in result or 'min_words' in result

    def test_should_include_topics_to_avoid(self):
        """Test including topics to avoid."""
        from church_context import apply_context_to_generation

        conn = create_test_db()
        church_id = insert_church_profile(conn)
        insert_theological_context(conn, church_id,
                                  tradition="Methodist")
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE theological_context SET topics_to_avoid = ?
            WHERE church_id = ?
        ''', ('partisan politics, personal family anecdotes', church_id))
        conn.commit()

        params = {'scripture': 'Romans 13'}
        result = apply_context_to_generation(conn, church_id, params)

        assert 'avoid' in result or 'topics_to_avoid' in result or 'context' in result


class TestExportChurchProfile:
    """Tests for export_church_profile function."""

    def test_should_export_profile_as_json(self):
        """Test exporting church profile as JSON."""
        from church_context import export_church_profile

        conn = create_test_db()
        church_id = insert_church_profile(conn, name="Export Test Church")
        insert_demographics(conn, church_id)
        insert_pastor_preferences(conn, church_id)
        insert_theological_context(conn, church_id)

        result = export_church_profile(conn, church_id)

        assert result is not None
        data = json.loads(result)
        assert data['name'] == "Export Test Church"

    def test_should_include_all_sections(self):
        """Test including all profile sections in export."""
        from church_context import export_church_profile

        conn = create_test_db()
        church_id = insert_church_profile(conn)
        insert_demographics(conn, church_id, age_distribution="mixed")
        insert_pastor_preferences(conn, church_id, sermon_length_min=2000)
        insert_theological_context(conn, church_id, tradition="Wesleyan")

        result = export_church_profile(conn, church_id)
        data = json.loads(result)

        assert 'demographics' in data
        assert 'preferences' in data
        assert 'theology' in data

    def test_should_return_none_for_nonexistent(self):
        """Test returning None for non-existent church."""
        from church_context import export_church_profile

        conn = create_test_db()

        result = export_church_profile(conn, 9999)

        assert result is None


class TestImportChurchProfile:
    """Tests for import_church_profile function."""

    def test_should_import_profile_from_json(self):
        """Test importing church profile from JSON."""
        from church_context import import_church_profile

        conn = create_test_db()
        profile_data = json.dumps({
            'name': 'Imported Church',
            'denomination': 'Presbyterian',
            'location': 'Nashville, TN',
            'demographics': {
                'age_distribution': 'elderly',
                'education_level': 'mixed'
            }
        })

        result = import_church_profile(conn, profile_data)

        assert result['success'] is True
        assert result['church_id'] is not None

    def test_should_import_all_sections(self):
        """Test importing all profile sections."""
        from church_context import import_church_profile, get_church_profile

        conn = create_test_db()
        profile_data = json.dumps({
            'name': 'Complete Import',
            'denomination': 'Baptist',
            'demographics': {'age_distribution': 'mixed'},
            'preferences': {'sermon_length_min': 1500},
            'theology': {'tradition': 'Baptist'}
        })

        result = import_church_profile(conn, profile_data)
        profile = get_church_profile(conn, result['church_id'])

        assert profile['demographics'] is not None
        assert profile['preferences'] is not None
        assert profile['theology'] is not None

    def test_should_handle_invalid_json(self):
        """Test handling invalid JSON data."""
        from church_context import import_church_profile

        conn = create_test_db()

        result = import_church_profile(conn, "not valid json")

        assert result['success'] is False


class TestEdgeCases:
    """Tests for edge cases in church context."""

    def test_should_handle_no_profile(self):
        """Test handling when no profile exists."""
        from church_context import apply_context_to_generation

        conn = create_test_db()

        params = {'scripture': 'John 3:16'}
        result = apply_context_to_generation(conn, 9999, params)

        # Should return params unchanged or with defaults
        assert result is not None

    def test_should_handle_incomplete_profile(self):
        """Test handling incomplete profile data."""
        from church_context import get_church_profile

        conn = create_test_db()
        church_id = insert_church_profile(conn, name="Minimal Church")
        # No demographics, preferences, or theology

        result = get_church_profile(conn, church_id)

        assert result is not None
        assert result['name'] == "Minimal Church"

    def test_should_handle_conflicting_preferences(self):
        """Test handling conflicting preference values."""
        from church_context import set_pastor_preferences

        conn = create_test_db()
        church_id = insert_church_profile(conn)

        # Min greater than max - should handle gracefully
        result = set_pastor_preferences(conn, church_id, {
            'sermon_length_min': 3000,
            'sermon_length_max': 2000
        })

        assert result['success'] is False or 'warning' in result

    def test_should_handle_unicode_in_profile(self):
        """Test handling unicode characters in profile."""
        from church_context import create_church_profile

        conn = create_test_db()

        result = create_church_profile(conn,
                                       name="Iglesia de la Gracia \u2764\ufe0f",
                                       location="San Antonio, TX")

        assert result['success'] is True


class TestIntegration:
    """Integration tests for church context."""

    def test_should_create_complete_profile(self):
        """Test creating complete church profile with all sections."""
        from church_context import (
            create_church_profile,
            set_congregation_demographics,
            set_pastor_preferences,
            set_theological_context,
            get_church_profile
        )

        conn = create_test_db()

        # Create profile
        result = create_church_profile(conn,
                                       name="University UMC",
                                       denomination="United Methodist",
                                       location="Baton Rouge, LA",
                                       size="medium")
        church_id = result['church_id']

        # Set demographics
        set_congregation_demographics(conn, church_id, {
            'age_distribution': 'mixed',
            'education_level': 'college-educated',
            'political_leaning': 'purple',
            'cultural_diversity': 'diverse'
        })

        # Set preferences
        set_pastor_preferences(conn, church_id, {
            'sermon_length_min': 2000,
            'sermon_length_max': 2500,
            'illustration_preference': 'contemporary',
            'use_personal_stories': False,
            'humor_level': 'moderate'
        })

        # Set theology
        set_theological_context(conn, church_id, {
            'tradition': 'Wesleyan',
            'emphasis': 'grace-focused, inclusive',
            'scripture_approach': 'contextual',
            'topics_to_avoid': 'partisan politics'
        })

        # Get complete profile
        profile = get_church_profile(conn, church_id)

        assert profile['name'] == "University UMC"
        assert profile['demographics']['political_leaning'] == 'purple'
        assert profile['preferences']['use_personal_stories'] == False
        assert profile['theology']['tradition'] == 'Wesleyan'

    def test_should_export_and_import_profile(self):
        """Test exporting and importing a profile."""
        from church_context import (
            create_church_profile,
            set_congregation_demographics,
            export_church_profile,
            import_church_profile,
            get_church_profile
        )

        conn = create_test_db()

        # Create original profile
        result = create_church_profile(conn, name="Original Church",
                                       denomination="Methodist")
        church_id = result['church_id']
        set_congregation_demographics(conn, church_id, {
            'age_distribution': 'young-families'
        })

        # Export
        exported = export_church_profile(conn, church_id)

        # Create new database and import
        new_conn = create_test_db()
        import_result = import_church_profile(new_conn, exported)

        # Verify import
        imported_profile = get_church_profile(new_conn, import_result['church_id'])
        assert imported_profile['name'] == "Original Church"
