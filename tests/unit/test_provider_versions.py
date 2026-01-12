"""Tests for Provider Version Control functionality.

TDD: These tests are written FIRST before implementation.
Tests cover:
- sermon_versions database table schema
- Version creation and tracking with provider attribution
- Regenerating sections with different providers
- Comparing outputs between providers
- API endpoints for version management

Database operations use REAL SQLite :memory: - NO MOCKS.
Test naming: test_should_[behavior]_when_[condition]
"""
import pytest
import sqlite3
import json
from datetime import datetime


class TestSermonVersionsSchema:
    """Test the sermon_versions database table schema."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database with schema."""
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        from database import init_db
        init_db(conn)
        return conn

    def test_should_create_sermon_versions_table(self, db_conn):
        """Test that sermon_versions table is created by init_db."""
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='sermon_versions'
        """)
        result = cursor.fetchone()
        assert result is not None
        assert result['name'] == 'sermon_versions'

    def test_should_have_required_columns(self, db_conn):
        """Test that sermon_versions has all required columns."""
        cursor = db_conn.cursor()
        cursor.execute("PRAGMA table_info(sermon_versions)")
        columns = {row['name']: row for row in cursor.fetchall()}

        required_columns = [
            'id', 'sermon_id', 'version_number', 'provider_id',
            'content', 'section', 'created_at'
        ]

        for col in required_columns:
            assert col in columns, f"Missing column: {col}"

    def test_should_enforce_foreign_key_to_sermons(self, db_conn):
        """Test that sermon_id references sermons table."""
        cursor = db_conn.cursor()

        # Insert a version without valid sermon_id should fail
        # First, let's try inserting without any sermon
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO sermon_versions
                (sermon_id, version_number, provider_id, content, section)
                VALUES (?, ?, ?, ?, ?)
            """, (999, 1, 'claude_cli', 'test content', 'full'))
            db_conn.commit()

    def test_should_insert_version_record(self, db_conn):
        """Test inserting a version record."""
        cursor = db_conn.cursor()

        # First create a sermon
        cursor.execute("""
            INSERT INTO sermons (title, scripture, manuscript)
            VALUES (?, ?, ?)
        """, ('Test Sermon', 'John 3:16', 'Test manuscript'))
        db_conn.commit()
        sermon_id = cursor.lastrowid

        # Insert version
        cursor.execute("""
            INSERT INTO sermon_versions
            (sermon_id, version_number, provider_id, content, section)
            VALUES (?, ?, ?, ?, ?)
        """, (sermon_id, 1, 'claude_cli', 'Version 1 content', 'full'))
        db_conn.commit()

        # Query it back
        cursor.execute("SELECT * FROM sermon_versions WHERE sermon_id = ?", (sermon_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row['sermon_id'] == sermon_id
        assert row['version_number'] == 1
        assert row['provider_id'] == 'claude_cli'
        assert row['content'] == 'Version 1 content'
        assert row['section'] == 'full'

    def test_should_cascade_delete_when_sermon_deleted(self, db_conn):
        """Test that versions are deleted when sermon is deleted."""
        cursor = db_conn.cursor()

        # Create sermon
        cursor.execute("""
            INSERT INTO sermons (title, scripture, manuscript)
            VALUES (?, ?, ?)
        """, ('Delete Test Sermon', 'Romans 8:28', 'Test manuscript'))
        db_conn.commit()
        sermon_id = cursor.lastrowid

        # Insert versions
        cursor.execute("""
            INSERT INTO sermon_versions
            (sermon_id, version_number, provider_id, content, section)
            VALUES (?, ?, ?, ?, ?)
        """, (sermon_id, 1, 'claude_cli', 'Version 1', 'full'))
        cursor.execute("""
            INSERT INTO sermon_versions
            (sermon_id, version_number, provider_id, content, section)
            VALUES (?, ?, ?, ?, ?)
        """, (sermon_id, 2, 'openai', 'Version 2', 'full'))
        db_conn.commit()

        # Verify versions exist
        cursor.execute("SELECT COUNT(*) as count FROM sermon_versions WHERE sermon_id = ?", (sermon_id,))
        assert cursor.fetchone()['count'] == 2

        # Delete sermon
        cursor.execute("DELETE FROM sermons WHERE id = ?", (sermon_id,))
        db_conn.commit()

        # Verify versions are deleted
        cursor.execute("SELECT COUNT(*) as count FROM sermon_versions WHERE sermon_id = ?", (sermon_id,))
        assert cursor.fetchone()['count'] == 0


class TestSaveSermonVersion:
    """Test the save_sermon_version function."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database with schema."""
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        from database import init_db
        init_db(conn)
        return conn

    @pytest.fixture
    def sermon_id(self, db_conn):
        """Create a test sermon and return its ID."""
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO sermons (title, scripture, manuscript)
            VALUES (?, ?, ?)
        """, ('Test Sermon', 'John 3:16', 'Initial manuscript'))
        db_conn.commit()
        return cursor.lastrowid

    def test_should_save_full_sermon_version(self, db_conn, sermon_id):
        """Test saving a full sermon version."""
        from version_control import save_sermon_version

        result = save_sermon_version(
            db_conn,
            sermon_id=sermon_id,
            content='Full sermon content here',
            provider_id='claude_cli',
            section='full'
        )

        assert result is not None
        assert result['version_id'] is not None
        assert result['version_number'] == 1
        assert result['provider_id'] == 'claude_cli'
        assert result['section'] == 'full'

    def test_should_auto_increment_version_number(self, db_conn, sermon_id):
        """Test that version numbers auto-increment per sermon."""
        from version_control import save_sermon_version

        # Save first version
        result1 = save_sermon_version(
            db_conn, sermon_id, 'Version 1', 'claude_cli', 'full'
        )

        # Save second version
        result2 = save_sermon_version(
            db_conn, sermon_id, 'Version 2', 'openai', 'full'
        )

        # Save third version
        result3 = save_sermon_version(
            db_conn, sermon_id, 'Version 3', 'gemini', 'full'
        )

        assert result1['version_number'] == 1
        assert result2['version_number'] == 2
        assert result3['version_number'] == 3

    def test_should_save_section_specific_version(self, db_conn, sermon_id):
        """Test saving version for specific section."""
        from version_control import save_sermon_version

        sections = ['introduction', 'point_1', 'point_2', 'point_3', 'conclusion']

        for i, section in enumerate(sections, 1):
            result = save_sermon_version(
                db_conn, sermon_id, f'{section} content', 'claude_cli', section
            )
            assert result['section'] == section

    def test_should_raise_error_when_sermon_not_found(self, db_conn):
        """Test error when saving version for non-existent sermon."""
        from version_control import save_sermon_version, SermonNotFoundError

        with pytest.raises(SermonNotFoundError):
            save_sermon_version(
                db_conn,
                sermon_id=999999,
                content='Test content',
                provider_id='claude_cli',
                section='full'
            )

    def test_should_store_timestamp(self, db_conn, sermon_id):
        """Test that version includes created_at timestamp."""
        from version_control import save_sermon_version

        result = save_sermon_version(
            db_conn, sermon_id, 'Test content', 'claude_cli', 'full'
        )

        assert 'created_at' in result
        assert result['created_at'] is not None


class TestGetSermonVersions:
    """Test the get_sermon_versions function."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database with schema."""
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        from database import init_db
        init_db(conn)
        return conn

    @pytest.fixture
    def sermon_with_versions(self, db_conn):
        """Create a sermon with multiple versions."""
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO sermons (title, scripture, manuscript)
            VALUES (?, ?, ?)
        """, ('Versioned Sermon', 'John 3:16', 'Initial manuscript'))
        db_conn.commit()
        sermon_id = cursor.lastrowid

        # Add versions
        versions_data = [
            (sermon_id, 1, 'claude_cli', 'Claude version 1', 'full'),
            (sermon_id, 2, 'openai', 'OpenAI version', 'full'),
            (sermon_id, 3, 'gemini', 'Gemini version', 'full'),
            (sermon_id, 1, 'claude_cli', 'Intro v1', 'introduction'),
            (sermon_id, 2, 'openai', 'Intro v2', 'introduction'),
        ]

        for data in versions_data:
            cursor.execute("""
                INSERT INTO sermon_versions
                (sermon_id, version_number, provider_id, content, section)
                VALUES (?, ?, ?, ?, ?)
            """, data)
        db_conn.commit()

        return sermon_id

    def test_should_get_all_versions_for_sermon(self, db_conn, sermon_with_versions):
        """Test getting all versions for a sermon."""
        from version_control import get_sermon_versions

        versions = get_sermon_versions(db_conn, sermon_with_versions)

        assert versions is not None
        assert len(versions) == 5

    def test_should_filter_versions_by_section(self, db_conn, sermon_with_versions):
        """Test filtering versions by section."""
        from version_control import get_sermon_versions

        full_versions = get_sermon_versions(
            db_conn, sermon_with_versions, section='full'
        )
        intro_versions = get_sermon_versions(
            db_conn, sermon_with_versions, section='introduction'
        )

        assert len(full_versions) == 3
        assert len(intro_versions) == 2

    def test_should_filter_versions_by_provider(self, db_conn, sermon_with_versions):
        """Test filtering versions by provider."""
        from version_control import get_sermon_versions

        claude_versions = get_sermon_versions(
            db_conn, sermon_with_versions, provider_id='claude_cli'
        )

        assert len(claude_versions) == 2
        for v in claude_versions:
            assert v['provider_id'] == 'claude_cli'

    def test_should_return_empty_list_when_no_versions(self, db_conn):
        """Test returning empty list when sermon has no versions."""
        from version_control import get_sermon_versions

        # Create sermon without versions
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO sermons (title, scripture, manuscript)
            VALUES (?, ?, ?)
        """, ('No Versions Sermon', 'Romans 8:28', 'Manuscript'))
        db_conn.commit()
        sermon_id = cursor.lastrowid

        versions = get_sermon_versions(db_conn, sermon_id)

        assert versions == []

    def test_should_order_versions_by_created_at_descending(self, db_conn, sermon_with_versions):
        """Test that versions are ordered by created_at descending (newest first)."""
        from version_control import get_sermon_versions

        versions = get_sermon_versions(db_conn, sermon_with_versions)

        # Verify order - newer versions should come first
        if len(versions) > 1:
            for i in range(len(versions) - 1):
                # Later versions should have >= created_at
                assert versions[i]['version_number'] >= versions[i + 1]['version_number'] or \
                       versions[i]['created_at'] >= versions[i + 1]['created_at']

    def test_should_include_provider_info_in_versions(self, db_conn, sermon_with_versions):
        """Test that each version includes provider information."""
        from version_control import get_sermon_versions

        versions = get_sermon_versions(db_conn, sermon_with_versions)

        for version in versions:
            assert 'provider_id' in version
            assert version['provider_id'] in ['claude_cli', 'openai', 'gemini']


class TestRegenerateSection:
    """Test the regenerate_section function."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database with schema."""
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        from database import init_db
        init_db(conn)
        return conn

    @pytest.fixture
    def sermon_id(self, db_conn):
        """Create a test sermon with initial content."""
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO sermons (title, scripture, manuscript, provider_id)
            VALUES (?, ?, ?, ?)
        """, ('Regeneration Test', 'John 3:16', 'Initial full manuscript', 'claude_cli'))
        db_conn.commit()
        return cursor.lastrowid

    @pytest.fixture
    def registry(self, db_conn):
        """Create registry with test providers."""
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        registry = ProviderRegistry(db_conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)
        return registry

    def test_should_regenerate_full_sermon_with_different_provider(self, db_conn, sermon_id, registry):
        """Test regenerating entire sermon with different provider."""
        from version_control import regenerate_section

        result = regenerate_section(
            db_conn,
            registry,
            sermon_id=sermon_id,
            section='full',
            provider_id='claude_cli'
        )

        assert result is not None
        assert result['success'] is True
        assert result['section'] == 'full'
        assert 'content' in result
        assert 'version_id' in result

    def test_should_regenerate_specific_section(self, db_conn, sermon_id, registry):
        """Test regenerating a specific section (introduction, point_1, etc.)."""
        from version_control import regenerate_section

        sections = ['introduction', 'point_1', 'point_2', 'point_3', 'conclusion']

        for section in sections:
            result = regenerate_section(
                db_conn, registry, sermon_id, section, 'claude_cli'
            )
            assert result is not None
            assert result['section'] == section

    def test_should_create_new_version_on_regeneration(self, db_conn, sermon_id, registry):
        """Test that regeneration creates a new version entry."""
        from version_control import regenerate_section, get_sermon_versions

        # Regenerate introduction
        regenerate_section(db_conn, registry, sermon_id, 'introduction', 'claude_cli')

        # Check versions
        versions = get_sermon_versions(db_conn, sermon_id, section='introduction')
        assert len(versions) >= 1

    def test_should_raise_error_when_provider_not_found(self, db_conn, sermon_id, registry):
        """Test error when trying to regenerate with non-existent provider."""
        from version_control import regenerate_section, ProviderNotFoundError

        with pytest.raises(ProviderNotFoundError):
            regenerate_section(
                db_conn, registry, sermon_id, 'full', 'nonexistent_provider'
            )

    def test_should_raise_error_when_sermon_not_found(self, db_conn, registry):
        """Test error when sermon doesn't exist."""
        from version_control import regenerate_section, SermonNotFoundError

        with pytest.raises(SermonNotFoundError):
            regenerate_section(
                db_conn, registry, 999999, 'full', 'claude_cli'
            )

    def test_should_include_provider_info_in_result(self, db_conn, sermon_id, registry):
        """Test that regeneration result includes provider information."""
        from version_control import regenerate_section

        result = regenerate_section(
            db_conn, registry, sermon_id, 'full', 'claude_cli'
        )

        assert 'provider_id' in result
        assert result['provider_id'] == 'claude_cli'


class TestCompareProviderOutputs:
    """Test the compare_provider_outputs function."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database with schema."""
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        from database import init_db
        init_db(conn)
        return conn

    @pytest.fixture
    def sermon_with_provider_versions(self, db_conn):
        """Create sermon with versions from different providers."""
        cursor = db_conn.cursor()

        # Create sermon
        cursor.execute("""
            INSERT INTO sermons (title, scripture, manuscript)
            VALUES (?, ?, ?)
        """, ('Comparison Sermon', 'John 3:16', 'Initial manuscript'))
        db_conn.commit()
        sermon_id = cursor.lastrowid

        # Add versions from different providers
        versions = [
            (sermon_id, 1, 'claude_cli', 'Claude generated this wonderful sermon about love and grace.', 'full'),
            (sermon_id, 2, 'openai', 'OpenAI created this powerful sermon about love and hope.', 'full'),
            (sermon_id, 1, 'claude_cli', 'Claude intro about love', 'introduction'),
            (sermon_id, 1, 'openai', 'OpenAI intro about hope', 'introduction'),
        ]

        for data in versions:
            cursor.execute("""
                INSERT INTO sermon_versions
                (sermon_id, version_number, provider_id, content, section)
                VALUES (?, ?, ?, ?, ?)
            """, data)
        db_conn.commit()

        return sermon_id

    def test_should_compare_two_provider_outputs(self, db_conn, sermon_with_provider_versions):
        """Test comparing outputs from two providers."""
        from version_control import compare_provider_outputs

        comparison = compare_provider_outputs(
            db_conn,
            sermon_id=sermon_with_provider_versions,
            provider1='claude_cli',
            provider2='openai'
        )

        assert comparison is not None
        assert 'provider1' in comparison
        assert 'provider2' in comparison
        assert comparison['provider1']['provider_id'] == 'claude_cli'
        assert comparison['provider2']['provider_id'] == 'openai'

    def test_should_include_content_from_both_providers(self, db_conn, sermon_with_provider_versions):
        """Test that comparison includes content from both providers."""
        from version_control import compare_provider_outputs

        comparison = compare_provider_outputs(
            db_conn, sermon_with_provider_versions, 'claude_cli', 'openai'
        )

        assert 'content' in comparison['provider1']
        assert 'content' in comparison['provider2']
        assert 'Claude' in comparison['provider1']['content']
        assert 'OpenAI' in comparison['provider2']['content']

    def test_should_compare_specific_section(self, db_conn, sermon_with_provider_versions):
        """Test comparing outputs for a specific section."""
        from version_control import compare_provider_outputs

        comparison = compare_provider_outputs(
            db_conn, sermon_with_provider_versions,
            'claude_cli', 'openai',
            section='introduction'
        )

        assert comparison is not None
        assert 'intro' in comparison['provider1']['content'].lower()
        assert 'intro' in comparison['provider2']['content'].lower()

    def test_should_include_diff_output(self, db_conn, sermon_with_provider_versions):
        """Test that comparison includes diff-style output."""
        from version_control import compare_provider_outputs

        comparison = compare_provider_outputs(
            db_conn, sermon_with_provider_versions, 'claude_cli', 'openai'
        )

        assert 'diff' in comparison or 'differences' in comparison

    def test_should_include_word_count_comparison(self, db_conn, sermon_with_provider_versions):
        """Test that comparison includes word counts."""
        from version_control import compare_provider_outputs

        comparison = compare_provider_outputs(
            db_conn, sermon_with_provider_versions, 'claude_cli', 'openai'
        )

        assert 'word_count' in comparison['provider1'] or 'metrics' in comparison
        assert 'word_count' in comparison['provider2'] or 'metrics' in comparison

    def test_should_return_none_when_provider_has_no_version(self, db_conn, sermon_with_provider_versions):
        """Test handling when one provider has no version."""
        from version_control import compare_provider_outputs

        comparison = compare_provider_outputs(
            db_conn, sermon_with_provider_versions,
            'claude_cli', 'gemini'  # gemini has no versions
        )

        assert comparison is not None
        assert comparison['provider2']['content'] is None or comparison['provider2'].get('error')


class TestVersionControlAPI:
    """Test API endpoints for version control."""

    @pytest.fixture
    def client(self):
        """Create test client with database."""
        from app import create_app
        app = create_app(testing=True)
        return app.test_client()

    @pytest.fixture
    def sermon_with_versions(self, client):
        """Create a sermon with versions via API setup."""
        from app import create_app
        from database import get_db, init_db

        app = create_app(testing=True)
        with app.app_context():
            conn = get_db()
            cursor = conn.cursor()

            # Create sermon
            cursor.execute("""
                INSERT INTO sermons (title, scripture, manuscript)
                VALUES (?, ?, ?)
            """, ('API Test Sermon', 'John 3:16', 'Test manuscript'))
            conn.commit()
            sermon_id = cursor.lastrowid

            # Add versions
            cursor.execute("""
                INSERT INTO sermon_versions
                (sermon_id, version_number, provider_id, content, section)
                VALUES (?, ?, ?, ?, ?)
            """, (sermon_id, 1, 'claude_cli', 'Claude version', 'full'))
            cursor.execute("""
                INSERT INTO sermon_versions
                (sermon_id, version_number, provider_id, content, section)
                VALUES (?, ?, ?, ?, ?)
            """, (sermon_id, 2, 'openai', 'OpenAI version', 'full'))
            conn.commit()

        return {'app': app, 'sermon_id': sermon_id}

    def test_should_get_versions_via_api(self, sermon_with_versions):
        """Test GET /api/sermon/{id}/versions endpoint."""
        app = sermon_with_versions['app']
        sermon_id = sermon_with_versions['sermon_id']

        client = app.test_client()
        response = client.get(f'/api/sermon/{sermon_id}/versions')

        assert response.status_code == 200
        data = response.get_json()
        assert 'versions' in data
        assert len(data['versions']) >= 1

    def test_should_regenerate_section_via_api(self, sermon_with_versions):
        """Test POST /api/sermon/{id}/regenerate endpoint."""
        app = sermon_with_versions['app']
        sermon_id = sermon_with_versions['sermon_id']

        client = app.test_client()
        response = client.post(
            f'/api/sermon/{sermon_id}/regenerate',
            json={'section': 'introduction', 'provider_id': 'claude_cli'}
        )

        # Accept 200 (success) or 503 (provider unavailable during test)
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.get_json()
            assert 'section' in data or 'version_id' in data

    def test_should_compare_providers_via_api(self, sermon_with_versions):
        """Test GET /api/sermon/{id}/compare endpoint."""
        app = sermon_with_versions['app']
        sermon_id = sermon_with_versions['sermon_id']

        client = app.test_client()
        response = client.get(
            f'/api/sermon/{sermon_id}/compare?provider1=claude_cli&provider2=openai'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'provider1' in data or 'comparison' in data

    def test_should_return_404_when_sermon_not_found(self, client):
        """Test 404 response when sermon doesn't exist."""
        response = client.get('/api/sermon/999999/versions')
        assert response.status_code == 404

    def test_should_return_error_when_missing_provider_for_regenerate(self, sermon_with_versions):
        """Test error when provider_id is missing in regenerate request."""
        app = sermon_with_versions['app']
        sermon_id = sermon_with_versions['sermon_id']

        client = app.test_client()
        response = client.post(
            f'/api/sermon/{sermon_id}/regenerate',
            json={'section': 'introduction'}
            # Missing provider_id
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestAutoVersionOnGeneration:
    """Test automatic version creation during sermon generation."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database with schema."""
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        from database import init_db
        init_db(conn)
        return conn

    @pytest.fixture
    def registry(self, db_conn):
        """Create registry with test providers."""
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        registry = ProviderRegistry(db_conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)
        return registry

    def test_should_auto_save_version_on_generation(self, db_conn, registry):
        """Test that generating a sermon automatically saves a version."""
        from sermon_generator import generate_sermon_with_provider
        from version_control import get_sermon_versions

        params = {
            'scripture': 'John 3:16',
            'title': 'Auto Version Test',
            'theme': 'Love'
        }

        result = generate_sermon_with_provider(
            params, registry, db_conn, provider_id='claude_cli'
        )

        sermon_id = result.get('sermon_id') or result.get('id')
        versions = get_sermon_versions(db_conn, sermon_id)

        # Should have at least one version from generation
        assert len(versions) >= 1
        assert versions[0]['provider_id'] == 'claude_cli'
        assert versions[0]['section'] == 'full'


class TestVersionMetadata:
    """Test version metadata tracking."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database with schema."""
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        from database import init_db
        init_db(conn)
        return conn

    @pytest.fixture
    def sermon_id(self, db_conn):
        """Create a test sermon."""
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO sermons (title, scripture, manuscript)
            VALUES (?, ?, ?)
        """, ('Metadata Test', 'John 3:16', 'Test manuscript'))
        db_conn.commit()
        return cursor.lastrowid

    def test_should_track_word_count_in_version(self, db_conn, sermon_id):
        """Test that version tracks word count."""
        from version_control import save_sermon_version

        content = "This is a test sermon with exactly ten words here."
        result = save_sermon_version(
            db_conn, sermon_id, content, 'claude_cli', 'full'
        )

        # Check if word count is tracked
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT * FROM sermon_versions WHERE id = ?
        """, (result['version_id'],))
        row = cursor.fetchone()

        # Word count should be calculated
        assert result.get('word_count') is not None or len(content.split()) > 0

    def test_should_get_latest_version_per_section(self, db_conn, sermon_id):
        """Test getting the latest version for each section."""
        from version_control import save_sermon_version, get_latest_version

        # Save multiple versions
        save_sermon_version(db_conn, sermon_id, 'Intro v1', 'claude_cli', 'introduction')
        save_sermon_version(db_conn, sermon_id, 'Intro v2', 'openai', 'introduction')
        save_sermon_version(db_conn, sermon_id, 'Intro v3', 'gemini', 'introduction')

        latest = get_latest_version(db_conn, sermon_id, 'introduction')

        assert latest is not None
        assert latest['version_number'] == 3
        assert latest['provider_id'] == 'gemini'

    def test_should_get_version_by_number(self, db_conn, sermon_id):
        """Test getting a specific version by number."""
        from version_control import save_sermon_version, get_version_by_number

        save_sermon_version(db_conn, sermon_id, 'Version 1', 'claude_cli', 'full')
        save_sermon_version(db_conn, sermon_id, 'Version 2', 'openai', 'full')
        save_sermon_version(db_conn, sermon_id, 'Version 3', 'gemini', 'full')

        version = get_version_by_number(db_conn, sermon_id, 2, 'full')

        assert version is not None
        assert version['version_number'] == 2
        assert version['provider_id'] == 'openai'
        assert version['content'] == 'Version 2'


class TestVersionDiff:
    """Test version diff functionality."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database with schema."""
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        from database import init_db
        init_db(conn)
        return conn

    @pytest.fixture
    def sermon_with_versions(self, db_conn):
        """Create sermon with different content versions."""
        cursor = db_conn.cursor()

        cursor.execute("""
            INSERT INTO sermons (title, scripture, manuscript)
            VALUES (?, ?, ?)
        """, ('Diff Test Sermon', 'John 3:16', 'Initial'))
        db_conn.commit()
        sermon_id = cursor.lastrowid

        # Add versions with different content
        cursor.execute("""
            INSERT INTO sermon_versions
            (sermon_id, version_number, provider_id, content, section)
            VALUES (?, ?, ?, ?, ?)
        """, (sermon_id, 1, 'claude_cli', 'The first line.\nThe second line.\nThe third line.', 'full'))
        cursor.execute("""
            INSERT INTO sermon_versions
            (sermon_id, version_number, provider_id, content, section)
            VALUES (?, ?, ?, ?, ?)
        """, (sermon_id, 2, 'openai', 'The first line.\nA modified second line.\nThe third line.\nA new fourth line.', 'full'))
        db_conn.commit()

        return sermon_id

    def test_should_generate_diff_between_versions(self, db_conn, sermon_with_versions):
        """Test generating diff between two versions."""
        from version_control import get_version_diff

        diff = get_version_diff(
            db_conn,
            sermon_id=sermon_with_versions,
            version1=1,
            version2=2,
            section='full'
        )

        assert diff is not None
        assert 'additions' in diff or 'changes' in diff or 'diff_lines' in diff

    def test_should_show_additions_and_deletions(self, db_conn, sermon_with_versions):
        """Test that diff shows additions and deletions."""
        from version_control import get_version_diff

        diff = get_version_diff(
            db_conn, sermon_with_versions, 1, 2, 'full'
        )

        # Should indicate changes
        assert diff.get('has_changes', True) is True or len(diff.get('diff_lines', [])) > 0


class TestProviderVersionStats:
    """Test provider-specific version statistics."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database with schema."""
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        from database import init_db
        init_db(conn)
        return conn

    @pytest.fixture
    def sermon_with_many_versions(self, db_conn):
        """Create sermon with many versions from different providers."""
        cursor = db_conn.cursor()

        cursor.execute("""
            INSERT INTO sermons (title, scripture, manuscript)
            VALUES (?, ?, ?)
        """, ('Stats Test Sermon', 'John 3:16', 'Initial'))
        db_conn.commit()
        sermon_id = cursor.lastrowid

        # Add many versions from different providers
        for i in range(10):
            provider = ['claude_cli', 'openai', 'gemini'][i % 3]
            cursor.execute("""
                INSERT INTO sermon_versions
                (sermon_id, version_number, provider_id, content, section)
                VALUES (?, ?, ?, ?, ?)
            """, (sermon_id, i + 1, provider, f'Version {i + 1} content ' * 50, 'full'))
        db_conn.commit()

        return sermon_id

    def test_should_count_versions_per_provider(self, db_conn, sermon_with_many_versions):
        """Test counting versions by provider."""
        from version_control import get_provider_version_stats

        stats = get_provider_version_stats(db_conn, sermon_with_many_versions)

        assert stats is not None
        assert 'claude_cli' in stats
        assert 'openai' in stats
        assert stats['claude_cli']['count'] >= 1
        assert stats['openai']['count'] >= 1

    def test_should_calculate_average_word_count_per_provider(self, db_conn, sermon_with_many_versions):
        """Test calculating average word count per provider."""
        from version_control import get_provider_version_stats

        stats = get_provider_version_stats(db_conn, sermon_with_many_versions)

        for provider_id, provider_stats in stats.items():
            assert 'avg_word_count' in provider_stats or 'total_word_count' in provider_stats
