"""Tests for AI provider registry.

TDD: These tests are written FIRST before implementation.
"""
import pytest
import sqlite3
from typing import Optional, List, Generator


class TestProviderRegistry:
    """Test the ProviderRegistry class."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database with schema."""
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        # Create ai_providers table
        conn.execute('''
            CREATE TABLE ai_providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_name TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                api_key_encrypted TEXT,
                default_model TEXT,
                is_enabled BOOLEAN DEFAULT FALSE,
                is_default BOOLEAN DEFAULT FALSE,
                color_primary TEXT,
                color_bg TEXT,
                config_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Seed default providers
        conn.execute('''
            INSERT INTO ai_providers (provider_name, display_name, is_enabled, is_default)
            VALUES ('test_provider', 'Test Provider', 1, 1)
        ''')
        conn.commit()
        return conn

    @pytest.fixture
    def mock_provider(self):
        """Create a mock provider for testing."""
        from providers.base import AIProvider, ProviderResult, ProviderModel

        class MockProvider(AIProvider):
            provider_id = "test_provider"
            display_name = "Test Provider"

            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self._available = True

            def is_available(self) -> bool:
                return self._available

            def run(self, prompt: str, model: Optional[str] = None) -> ProviderResult:
                return ProviderResult(
                    output=f"Mock response: {prompt}",
                    provider_id=self.provider_id,
                    model_id=model or "mock-model",
                    success=True,
                    duration=0.1
                )

            def run_streaming(self, prompt: str, model: Optional[str] = None):
                yield "chunk1"
                yield "chunk2"

            def get_available_models(self) -> List[ProviderModel]:
                return [ProviderModel(id="mock-model", name="Mock Model", context_window=4096)]

            def _requires_api_key(self) -> bool:
                return False

        return MockProvider

    def test_should_create_registry(self, db_conn):
        """Test creating a provider registry."""
        from providers.registry import ProviderRegistry

        registry = ProviderRegistry(db_conn)
        assert registry is not None

    def test_should_register_provider(self, db_conn, mock_provider):
        """Test registering a provider."""
        from providers.registry import ProviderRegistry

        registry = ProviderRegistry(db_conn)
        provider = mock_provider()
        registry.register(provider)

        assert registry.get_provider("test_provider") is provider

    def test_should_get_provider_by_id(self, db_conn, mock_provider):
        """Test getting a provider by ID."""
        from providers.registry import ProviderRegistry

        registry = ProviderRegistry(db_conn)
        provider = mock_provider()
        registry.register(provider)

        retrieved = registry.get_provider("test_provider")
        assert retrieved is not None
        assert retrieved.provider_id == "test_provider"

    def test_should_return_none_for_unknown_provider(self, db_conn):
        """Test getting unknown provider returns None."""
        from providers.registry import ProviderRegistry

        registry = ProviderRegistry(db_conn)
        assert registry.get_provider("nonexistent") is None

    def test_should_get_enabled_providers(self, db_conn, mock_provider):
        """Test getting only enabled providers."""
        from providers.registry import ProviderRegistry

        registry = ProviderRegistry(db_conn)
        provider = mock_provider()
        registry.register(provider)

        enabled = registry.get_enabled_providers()
        assert len(enabled) == 1
        assert enabled[0].provider_id == "test_provider"

    def test_should_get_default_provider(self, db_conn, mock_provider):
        """Test getting the default provider."""
        from providers.registry import ProviderRegistry

        registry = ProviderRegistry(db_conn)
        provider = mock_provider()
        registry.register(provider)

        default = registry.get_default_provider()
        assert default is not None
        assert default.provider_id == "test_provider"

    def test_should_run_on_single_provider(self, db_conn, mock_provider):
        """Test running prompt on a single provider."""
        from providers.registry import ProviderRegistry

        registry = ProviderRegistry(db_conn)
        provider = mock_provider()
        registry.register(provider)

        results = registry.run_on_providers("Hello", ["test_provider"])

        assert len(results) == 1
        assert results[0].success is True
        assert "Hello" in results[0].output

    def test_should_run_parallel_on_multiple_providers(self, db_conn, mock_provider):
        """Test running prompt on multiple providers in parallel."""
        from providers.registry import ProviderRegistry
        from providers.base import AIProvider, ProviderResult, ProviderModel

        # Create second mock provider
        class MockProvider2(AIProvider):
            provider_id = "test_provider_2"
            display_name = "Test Provider 2"

            def is_available(self):
                return True

            def run(self, prompt, model=None):
                return ProviderResult(
                    output=f"Provider2: {prompt}",
                    provider_id=self.provider_id,
                    model_id="model2",
                    success=True
                )

            def run_streaming(self, prompt, model=None):
                yield "p2chunk"

            def get_available_models(self):
                return []

            def _requires_api_key(self):
                return False

        # Add second provider to DB
        db_conn.execute('''
            INSERT INTO ai_providers (provider_name, display_name, is_enabled)
            VALUES ('test_provider_2', 'Test Provider 2', 1)
        ''')
        db_conn.commit()

        registry = ProviderRegistry(db_conn)
        registry.register(mock_provider())
        registry.register(MockProvider2())

        results = registry.run_on_providers(
            "Test prompt",
            ["test_provider", "test_provider_2"]
        )

        assert len(results) == 2
        provider_ids = {r.provider_id for r in results}
        assert provider_ids == {"test_provider", "test_provider_2"}

    def test_should_handle_provider_error_gracefully(self, db_conn):
        """Test handling provider errors."""
        from providers.registry import ProviderRegistry
        from providers.base import AIProvider, ProviderResult

        class FailingProvider(AIProvider):
            provider_id = "failing"
            display_name = "Failing Provider"

            def is_available(self):
                return True

            def run(self, prompt, model=None):
                raise Exception("Provider error")

            def run_streaming(self, prompt, model=None):
                raise Exception("Streaming error")

            def get_available_models(self):
                return []

            def _requires_api_key(self):
                return False

        db_conn.execute('''
            INSERT INTO ai_providers (provider_name, display_name, is_enabled)
            VALUES ('failing', 'Failing', 1)
        ''')
        db_conn.commit()

        registry = ProviderRegistry(db_conn)
        registry.register(FailingProvider())

        results = registry.run_on_providers("Test", ["failing"])

        assert len(results) == 1
        assert results[0].success is False
        assert results[0].error is not None

    def test_should_list_all_registered_providers(self, db_conn, mock_provider):
        """Test listing all registered providers."""
        from providers.registry import ProviderRegistry

        registry = ProviderRegistry(db_conn)
        provider = mock_provider()
        registry.register(provider)

        all_providers = registry.list_providers()
        assert "test_provider" in all_providers
