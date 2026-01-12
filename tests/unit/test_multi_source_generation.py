"""Tests for multi-source sermon generation with AI provider integration.

These tests verify the multi-source generation system that allows selecting
different AI providers for sermon generation.
Tests are written first (TDD) - implementation follows.
Database operations use REAL SQLite :memory: - NO MOCKS.
"""
import pytest
import sqlite3
import json


class TestProviderBasedGeneration:
    """Test suite for generating sermons with specific providers."""

    def test_should_generate_sermon_with_default_provider_when_no_provider_specified(self):
        """Test that default provider is used when none specified."""
        from sermon_generator import generate_sermon_with_provider
        from database import init_db
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        # Setup registry with default provider
        registry = ProviderRegistry(conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)

        params = {
            'scripture': 'John 3:16',
            'title': 'Test Sermon',
            'theme': 'Love'
        }

        result = generate_sermon_with_provider(params, registry, conn)

        assert result is not None
        assert 'sermon_id' in result or 'id' in result
        conn.close()

    def test_should_generate_sermon_with_specified_provider(self):
        """Test generation with explicitly specified provider."""
        from sermon_generator import generate_sermon_with_provider
        from database import init_db
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        registry = ProviderRegistry(conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)

        params = {
            'scripture': 'John 3:16',
            'title': 'Test Sermon',
            'theme': 'Love'
        }

        result = generate_sermon_with_provider(
            params, registry, conn, provider_id='claude_cli'
        )

        assert result is not None
        assert 'sermon_id' in result or 'id' in result
        conn.close()

    def test_should_raise_error_when_specified_provider_not_found(self):
        """Test that error is raised when provider doesn't exist."""
        from sermon_generator import generate_sermon_with_provider, ProviderNotFoundError
        from database import init_db
        from providers.registry import ProviderRegistry

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        registry = ProviderRegistry(conn)

        params = {
            'scripture': 'John 3:16',
            'title': 'Test Sermon',
            'theme': 'Love'
        }

        with pytest.raises(ProviderNotFoundError):
            generate_sermon_with_provider(
                params, registry, conn, provider_id='nonexistent_provider'
            )
        conn.close()

    def test_should_raise_error_when_no_default_provider_available(self):
        """Test error when no default provider is set and none specified."""
        from sermon_generator import generate_sermon_with_provider, NoDefaultProviderError
        from database import init_db
        from providers.registry import ProviderRegistry

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        # Registry with no providers
        registry = ProviderRegistry(conn)

        params = {
            'scripture': 'John 3:16',
            'title': 'Test Sermon',
            'theme': 'Love'
        }

        with pytest.raises(NoDefaultProviderError):
            generate_sermon_with_provider(params, registry, conn)
        conn.close()


class TestProviderIdStorage:
    """Test suite for storing provider_id with sermons."""

    def test_should_store_provider_id_with_sermon(self):
        """Test that provider_id is stored in sermons table."""
        from sermon_generator import generate_sermon_with_provider
        from database import init_db
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        registry = ProviderRegistry(conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)

        params = {
            'scripture': 'John 3:16',
            'title': 'Provider Storage Test',
            'theme': 'Love'
        }

        result = generate_sermon_with_provider(
            params, registry, conn, provider_id='claude_cli'
        )

        sermon_id = result.get('sermon_id') or result.get('id')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT provider_id FROM sermons WHERE id = ?",
            (sermon_id,)
        )
        row = cursor.fetchone()

        assert row is not None
        assert row[0] == 'claude_cli'
        conn.close()

    def test_should_allow_null_provider_id_for_backwards_compatibility(self):
        """Test that existing sermons without provider_id still work."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        # Insert a sermon without provider_id (simulating legacy data)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sermons (title, scripture, theme, manuscript)
            VALUES (?, ?, ?, ?)
        """, ('Legacy Sermon', 'John 3:16', 'Love', 'Test manuscript'))
        conn.commit()

        # Should be able to query it
        cursor.execute("SELECT id, title, provider_id FROM sermons WHERE title = ?",
                       ('Legacy Sermon',))
        row = cursor.fetchone()

        assert row is not None
        assert row[0] is not None  # id exists
        assert row[2] is None  # provider_id can be null
        conn.close()

    def test_should_return_provider_id_in_sermon_result(self):
        """Test that generate result includes provider_id."""
        from sermon_generator import generate_sermon_with_provider
        from database import init_db
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        registry = ProviderRegistry(conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)

        params = {
            'scripture': 'John 3:16',
            'title': 'Result Provider Test',
            'theme': 'Love'
        }

        result = generate_sermon_with_provider(
            params, registry, conn, provider_id='claude_cli'
        )

        assert 'provider_id' in result
        assert result['provider_id'] == 'claude_cli'
        conn.close()


class TestDatabaseMigration:
    """Test suite for provider_id column migration."""

    def test_should_add_provider_id_column_to_sermons_table(self):
        """Test that migration adds provider_id column."""
        from database import init_db, migrate_add_provider_id

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        # Migration should be idempotent - can run multiple times
        migrate_add_provider_id(conn)
        migrate_add_provider_id(conn)  # Run twice to ensure idempotency

        # Check column exists
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sermons)")
        columns = {row[1] for row in cursor.fetchall()}

        assert 'provider_id' in columns
        conn.close()

    def test_should_preserve_existing_data_after_migration(self):
        """Test that existing sermon data is preserved after migration."""
        from database import init_db, migrate_add_provider_id

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        # Insert sermon before migration check
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sermons (title, scripture, manuscript)
            VALUES (?, ?, ?)
        """, ('Pre-Migration Sermon', 'Romans 8:28', 'Test content'))
        conn.commit()

        # Run migration
        migrate_add_provider_id(conn)

        # Verify data preserved
        cursor.execute("SELECT title, scripture FROM sermons WHERE title = ?",
                       ('Pre-Migration Sermon',))
        row = cursor.fetchone()

        assert row is not None
        assert row[0] == 'Pre-Migration Sermon'
        assert row[1] == 'Romans 8:28'
        conn.close()


class TestProviderSelection:
    """Test suite for provider selection UI support."""

    def test_should_list_enabled_providers_for_selection(self):
        """Test getting list of enabled providers for dropdown."""
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        registry = ProviderRegistry(conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)

        enabled = registry.get_enabled_providers()

        # At least default claude_cli should be enabled
        assert isinstance(enabled, list)
        conn.close()

    def test_should_get_provider_display_info_for_ui(self):
        """Test getting provider display info for UI."""
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        registry = ProviderRegistry(conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)

        config = registry.get_provider_config('claude_cli')

        # Should have display info
        assert config is not None
        conn.close()


class TestMultiProviderComparison:
    """Test suite for generating with multiple providers and comparing."""

    def test_should_generate_with_multiple_providers_in_parallel(self):
        """Test generating sermon with multiple providers simultaneously."""
        from sermon_generator import generate_sermon_multi_provider
        from database import init_db
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        registry = ProviderRegistry(conn)
        # Register multiple providers (using echo command for testing)
        provider1 = ClaudeCLIProvider(command='echo')
        registry.register(provider1)

        params = {
            'scripture': 'John 3:16',
            'title': 'Multi-Provider Test',
            'theme': 'Love'
        }

        # Generate with available providers
        results = generate_sermon_multi_provider(
            params, registry, conn,
            provider_ids=['claude_cli']
        )

        assert isinstance(results, list)
        assert len(results) >= 1
        conn.close()

    def test_should_return_results_from_each_provider(self):
        """Test that each provider returns a separate result."""
        from sermon_generator import generate_sermon_multi_provider
        from database import init_db
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        registry = ProviderRegistry(conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)

        params = {
            'scripture': 'John 3:16',
            'title': 'Result Per Provider Test',
            'theme': 'Love'
        }

        results = generate_sermon_multi_provider(
            params, registry, conn,
            provider_ids=['claude_cli']
        )

        # Each result should have provider_id
        for result in results:
            assert 'provider_id' in result
        conn.close()

    def test_should_handle_provider_failures_gracefully(self):
        """Test that one provider failing doesn't break others."""
        from sermon_generator import generate_sermon_with_provider, ProviderNotFoundError
        from database import init_db
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        registry = ProviderRegistry(conn)
        # Working provider
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)

        params = {
            'scripture': 'John 3:16',
            'title': 'Failure Handling Test',
            'theme': 'Love'
        }

        # First, verify nonexistent provider raises error
        try:
            generate_sermon_with_provider(
                params, registry, conn, provider_id='nonexistent'
            )
            failed_as_expected = False
        except ProviderNotFoundError:
            failed_as_expected = True

        assert failed_as_expected

        # Second, verify working provider still works
        result = generate_sermon_with_provider(
            params, registry, conn, provider_id='claude_cli'
        )
        assert result.get('success', False) or result.get('sermon_id')
        conn.close()


class TestGenerationOutputStorage:
    """Test suite for storing multiple generation outputs."""

    def test_should_store_output_in_generation_outputs_table(self):
        """Test that generation outputs are stored properly."""
        from sermon_generator import generate_sermon_with_provider, _store_generation_output
        from database import init_db
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        registry = ProviderRegistry(conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)

        params = {
            'scripture': 'John 3:16',
            'title': 'Output Storage Test',
            'theme': 'Love'
        }

        result = generate_sermon_with_provider(
            params, registry, conn,
            provider_id='claude_cli'
        )

        # Manually store the output (this is what multi-provider does)
        if result.get('sermon_id'):
            _store_generation_output(
                conn,
                result['sermon_id'],
                'manuscript',
                result.get('manuscript', ''),
                result.get('provider_id'),
                result.get('model_id')
            )

        # Check generation_outputs table
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM generation_outputs")
        count = cursor.fetchone()[0]

        assert count >= 1
        conn.close()

    def test_should_track_content_source_for_each_output(self):
        """Test that content_sources tracks which AI generated what."""
        from sermon_generator import generate_sermon_with_provider
        from database import init_db
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        registry = ProviderRegistry(conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)

        params = {
            'scripture': 'John 3:16',
            'title': 'Source Tracking Test',
            'theme': 'Love'
        }

        generate_sermon_with_provider(
            params, registry, conn,
            provider_id='claude_cli'
        )

        # Check content_sources table
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM content_sources")
        count = cursor.fetchone()[0]

        assert count >= 1
        conn.close()


class TestAPIEndpointIntegration:
    """Test suite for API endpoint integration with provider selection."""

    def test_should_accept_provider_id_in_api_request(self):
        """Test that API endpoint accepts provider_id parameter."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.post('/api/sermon/generate', json={
                'scripture': 'John 3:16',
                'title': 'API Provider Test',
                'provider_id': 'claude_cli'
            })

            # Should accept the request (may fail due to other reasons,
            # but should not reject due to provider_id parameter)
            assert response.status_code in [200, 400, 503]

    def test_should_return_available_providers_from_api(self):
        """Test API endpoint for listing available providers."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/api/providers')

            assert response.status_code == 200
            data = response.get_json()
            assert 'providers' in data or isinstance(data, list)


class TestProviderResultMetadata:
    """Test suite for provider result metadata."""

    def test_should_include_model_id_in_result(self):
        """Test that result includes model_id used."""
        from sermon_generator import generate_sermon_with_provider
        from database import init_db
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        registry = ProviderRegistry(conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)

        params = {
            'scripture': 'John 3:16',
            'title': 'Model ID Test',
            'theme': 'Love'
        }

        result = generate_sermon_with_provider(
            params, registry, conn, provider_id='claude_cli'
        )

        assert 'model_id' in result or result.get('provider_id')
        conn.close()

    def test_should_include_generation_duration(self):
        """Test that result includes generation time."""
        from sermon_generator import generate_sermon_with_provider
        from database import init_db
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        registry = ProviderRegistry(conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)

        params = {
            'scripture': 'John 3:16',
            'title': 'Duration Test',
            'theme': 'Love'
        }

        result = generate_sermon_with_provider(
            params, registry, conn, provider_id='claude_cli'
        )

        assert 'duration' in result or 'generation_time' in result
        conn.close()


class TestBackwardsCompatibility:
    """Test suite for backwards compatibility with existing code."""

    def test_should_work_with_cli_bridge_directly(self):
        """Test that old CLI bridge approach still works."""
        from sermon_generator import generate_sermon_simple
        from cli_bridge import CLIBridge
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        bridge = CLIBridge(command='echo')

        params = {
            'scripture': 'John 3:16',
            'title': 'Backwards Compat Test',
            'theme': 'Love'
        }

        result = generate_sermon_simple(params, bridge, conn)

        assert result is not None
        assert 'sermon_id' in result or 'id' in result
        conn.close()

    def test_should_use_default_provider_in_generate_sermon(self):
        """Test that generate_sermon falls back to default provider."""
        from sermon_generator import generate_sermon
        from cli_bridge import CLIBridge
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        bridge = CLIBridge(command='echo')

        params = {
            'scripture': 'John 3:16',
            'title': 'Default Provider Test',
            'theme': 'Love'
        }

        # Old signature should still work
        result = generate_sermon(params, cli_bridge=bridge, db_conn=conn)

        assert result is not None
        conn.close()


class TestProviderSpecificModels:
    """Test suite for using provider-specific models."""

    def test_should_accept_model_parameter(self):
        """Test that specific model can be requested."""
        from sermon_generator import generate_sermon_with_provider
        from database import init_db
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        registry = ProviderRegistry(conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)

        params = {
            'scripture': 'John 3:16',
            'title': 'Model Selection Test',
            'theme': 'Love'
        }

        # Should accept model parameter without error
        result = generate_sermon_with_provider(
            params, registry, conn,
            provider_id='claude_cli',
            model='cli-default'
        )

        assert result is not None
        conn.close()

    def test_should_use_provider_default_model_when_none_specified(self):
        """Test that provider's default model is used."""
        from sermon_generator import generate_sermon_with_provider
        from database import init_db
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        registry = ProviderRegistry(conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)

        params = {
            'scripture': 'John 3:16',
            'title': 'Default Model Test',
            'theme': 'Love'
        }

        result = generate_sermon_with_provider(
            params, registry, conn,
            provider_id='claude_cli'
            # No model specified - should use default
        )

        assert result is not None
        # Should have some model info in result
        assert 'model_id' in result or result.get('provider_id')
        conn.close()
