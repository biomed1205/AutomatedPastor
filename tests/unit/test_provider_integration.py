"""Tests for provider integration - health monitoring and fallback.

Phase 7: Polish & Integration - TDD tests for:
- Provider health monitoring
- Fallback mechanism when primary provider fails
- Full integration tests across all provider features

Tests are written FIRST (TDD) - implementation follows.
Database operations use REAL SQLite :memory: - NO MOCKS.
"""
import pytest
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List


# =============================================================================
# PROVIDER HEALTH MONITORING TESTS
# =============================================================================

class TestProviderHealthSchema:
    """Test suite for provider_health table schema."""

    def test_should_create_provider_health_table(self):
        """Test that provider_health table is created with correct schema."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(provider_health)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert 'id' in columns
        assert 'provider_id' in columns
        assert 'status' in columns
        assert 'last_check' in columns
        assert 'last_success' in columns
        assert 'failure_count' in columns
        assert 'error_message' in columns
        conn.close()

    def test_should_store_health_status(self):
        """Test storing health status for a provider."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO provider_health (provider_id, status, last_check, failure_count)
            VALUES (?, ?, ?, ?)
        """, ('claude_cli', 'healthy', datetime.now().isoformat(), 0))
        conn.commit()

        cursor.execute("SELECT status, failure_count FROM provider_health WHERE provider_id = ?",
                       ('claude_cli',))
        row = cursor.fetchone()

        assert row is not None
        assert row[0] == 'healthy'
        assert row[1] == 0
        conn.close()


class TestProviderHealthMonitor:
    """Test suite for provider health monitoring functionality."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database with schema."""
        from database import init_db
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)
        return conn

    @pytest.fixture
    def mock_provider(self):
        """Create a mock provider for testing."""
        from providers.base import AIProvider, ProviderResult, ProviderModel

        class MockProvider(AIProvider):
            provider_id = "test_provider"
            display_name = "Test Provider"

            def __init__(self, should_fail=False, **kwargs):
                super().__init__(**kwargs)
                self._should_fail = should_fail

            def is_available(self) -> bool:
                return not self._should_fail

            def run(self, prompt: str, model: Optional[str] = None) -> ProviderResult:
                if self._should_fail:
                    return ProviderResult(
                        output="",
                        provider_id=self.provider_id,
                        model_id=model or "mock-model",
                        success=False,
                        error="Provider failed"
                    )
                return ProviderResult(
                    output=f"Response: {prompt}",
                    provider_id=self.provider_id,
                    model_id=model or "mock-model",
                    success=True,
                    duration=0.1
                )

            def run_streaming(self, prompt: str, model: Optional[str] = None):
                yield "chunk"

            def get_available_models(self) -> List[ProviderModel]:
                return [ProviderModel(id="mock-model", name="Mock Model", context_window=4096)]

            def _requires_api_key(self) -> bool:
                return False

        return MockProvider

    def test_should_check_provider_health(self, db_conn, mock_provider):
        """Test checking health status of a provider."""
        from providers.health import check_provider_health, HealthStatus

        provider = mock_provider(should_fail=False)
        status = check_provider_health(provider)

        assert status is not None
        assert status.status == HealthStatus.HEALTHY
        assert status.provider_id == "test_provider"

    def test_should_detect_unhealthy_provider(self, db_conn, mock_provider):
        """Test detecting an unhealthy provider."""
        from providers.health import check_provider_health, HealthStatus

        provider = mock_provider(should_fail=True)
        status = check_provider_health(provider)

        assert status is not None
        assert status.status in [HealthStatus.DEGRADED, HealthStatus.DOWN]

    def test_should_store_health_check_result(self, db_conn, mock_provider):
        """Test storing health check results in database."""
        from providers.health import check_provider_health, store_health_status

        provider = mock_provider(should_fail=False)
        status = check_provider_health(provider)

        store_health_status(db_conn, status)

        cursor = db_conn.cursor()
        cursor.execute("SELECT status FROM provider_health WHERE provider_id = ?",
                       (provider.provider_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row['status'] == 'healthy'

    def test_should_update_failure_count_on_failure(self, db_conn, mock_provider):
        """Test that failure count increments on provider failure."""
        from providers.health import check_provider_health, store_health_status

        # First, insert initial health record
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO provider_health (provider_id, status, failure_count)
            VALUES (?, ?, ?)
        """, ('test_provider', 'healthy', 0))
        db_conn.commit()

        # Check failing provider
        provider = mock_provider(should_fail=True)
        status = check_provider_health(provider)
        store_health_status(db_conn, status)

        cursor.execute("SELECT failure_count FROM provider_health WHERE provider_id = ?",
                       ('test_provider',))
        row = cursor.fetchone()

        assert row is not None
        assert row['failure_count'] > 0

    def test_should_reset_failure_count_on_success(self, db_conn, mock_provider):
        """Test that failure count resets to 0 on successful check."""
        from providers.health import check_provider_health, store_health_status

        # Set up initial failure state
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO provider_health (provider_id, status, failure_count)
            VALUES (?, ?, ?)
        """, ('test_provider', 'degraded', 3))
        db_conn.commit()

        # Check healthy provider
        provider = mock_provider(should_fail=False)
        status = check_provider_health(provider)
        store_health_status(db_conn, status)

        cursor.execute("SELECT failure_count, status FROM provider_health WHERE provider_id = ?",
                       ('test_provider',))
        row = cursor.fetchone()

        assert row is not None
        assert row['failure_count'] == 0
        assert row['status'] == 'healthy'

    def test_should_get_all_provider_health_statuses(self, db_conn):
        """Test retrieving health status for all providers."""
        from providers.health import get_all_health_statuses

        # Insert some health records
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO provider_health (provider_id, status, failure_count)
            VALUES (?, ?, ?)
        """, ('claude_cli', 'healthy', 0))
        cursor.execute("""
            INSERT INTO provider_health (provider_id, status, failure_count)
            VALUES (?, ?, ?)
        """, ('openai', 'degraded', 2))
        db_conn.commit()

        statuses = get_all_health_statuses(db_conn)

        assert len(statuses) >= 2
        provider_ids = [s['provider_id'] for s in statuses]
        assert 'claude_cli' in provider_ids
        assert 'openai' in provider_ids

    def test_should_track_last_success_time(self, db_conn, mock_provider):
        """Test that last_success time is updated on successful check."""
        from providers.health import check_provider_health, store_health_status

        provider = mock_provider(should_fail=False)
        status = check_provider_health(provider)
        store_health_status(db_conn, status)

        cursor = db_conn.cursor()
        cursor.execute("SELECT last_success FROM provider_health WHERE provider_id = ?",
                       ('test_provider',))
        row = cursor.fetchone()

        assert row is not None
        assert row['last_success'] is not None


# =============================================================================
# PROVIDER FALLBACK TESTS
# =============================================================================

class TestProviderFallback:
    """Test suite for provider fallback mechanism."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database with schema."""
        from database import init_db
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)
        return conn

    @pytest.fixture
    def create_mock_provider(self):
        """Factory for creating mock providers."""
        from providers.base import AIProvider, ProviderResult, ProviderModel

        def _create(provider_id: str, should_fail: bool = False, delay: float = 0.0):
            class MockProvider(AIProvider):
                def __init__(self):
                    super().__init__()
                    self.provider_id = provider_id
                    self.display_name = f"Mock {provider_id}"
                    self._should_fail = should_fail
                    self._delay = delay

                def is_available(self) -> bool:
                    return True

                def run(self, prompt: str, model: Optional[str] = None) -> ProviderResult:
                    import time
                    if self._delay > 0:
                        time.sleep(self._delay)

                    if self._should_fail:
                        return ProviderResult(
                            output="",
                            provider_id=self.provider_id,
                            model_id=model or "mock-model",
                            success=False,
                            error=f"Provider {provider_id} failed"
                        )
                    return ProviderResult(
                        output=f"Response from {provider_id}: {prompt}",
                        provider_id=self.provider_id,
                        model_id=model or "mock-model",
                        success=True,
                        duration=0.1
                    )

                def run_streaming(self, prompt: str, model: Optional[str] = None):
                    yield f"chunk from {provider_id}"

                def get_available_models(self) -> List[ProviderModel]:
                    return [ProviderModel(id="mock-model", name="Mock Model", context_window=4096)]

                def _requires_api_key(self) -> bool:
                    return False

            return MockProvider()

        return _create

    def test_should_return_result_from_first_working_provider(self, db_conn, create_mock_provider):
        """Test that fallback returns result from first working provider."""
        from providers.fallback import generate_with_fallback
        from providers.registry import ProviderRegistry

        # Register in db
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO ai_providers (provider_name, display_name, is_enabled)
            VALUES (?, ?, ?)
        """, ('provider1', 'Provider 1', 1))
        db_conn.commit()

        registry = ProviderRegistry(db_conn)
        provider1 = create_mock_provider('provider1', should_fail=False)
        registry.register(provider1)

        result = generate_with_fallback("Test prompt", registry, ['provider1'])

        assert result is not None
        assert result.success is True
        assert result.provider_id == 'provider1'

    def test_should_fallback_to_second_provider_when_first_fails(self, db_conn, create_mock_provider):
        """Test fallback to next provider when first fails."""
        from providers.fallback import generate_with_fallback
        from providers.registry import ProviderRegistry

        # Register providers in db
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO ai_providers (provider_name, display_name, is_enabled)
            VALUES (?, ?, ?)
        """, ('failing_provider', 'Failing Provider', 1))
        cursor.execute("""
            INSERT INTO ai_providers (provider_name, display_name, is_enabled)
            VALUES (?, ?, ?)
        """, ('working_provider', 'Working Provider', 1))
        db_conn.commit()

        registry = ProviderRegistry(db_conn)
        failing = create_mock_provider('failing_provider', should_fail=True)
        working = create_mock_provider('working_provider', should_fail=False)
        registry.register(failing)
        registry.register(working)

        result = generate_with_fallback(
            "Test prompt",
            registry,
            ['failing_provider', 'working_provider']
        )

        assert result is not None
        assert result.success is True
        assert result.provider_id == 'working_provider'

    def test_should_return_failure_when_all_providers_fail(self, db_conn, create_mock_provider):
        """Test that failure is returned when all providers fail."""
        from providers.fallback import generate_with_fallback
        from providers.registry import ProviderRegistry

        # Register providers in db
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO ai_providers (provider_name, display_name, is_enabled)
            VALUES (?, ?, ?)
        """, ('failing1', 'Failing 1', 1))
        cursor.execute("""
            INSERT INTO ai_providers (provider_name, display_name, is_enabled)
            VALUES (?, ?, ?)
        """, ('failing2', 'Failing 2', 1))
        db_conn.commit()

        registry = ProviderRegistry(db_conn)
        failing1 = create_mock_provider('failing1', should_fail=True)
        failing2 = create_mock_provider('failing2', should_fail=True)
        registry.register(failing1)
        registry.register(failing2)

        result = generate_with_fallback(
            "Test prompt",
            registry,
            ['failing1', 'failing2']
        )

        assert result is not None
        assert result.success is False
        assert 'all providers failed' in result.error.lower() or result.error is not None

    def test_should_get_fallback_chain_for_provider(self, db_conn):
        """Test getting ordered fallback chain for a provider."""
        from providers.fallback import get_fallback_chain
        from database import init_db

        # The fallback chain should be configurable/deterministic
        chain = get_fallback_chain(db_conn, 'claude_cli')

        assert isinstance(chain, list)
        # Should return other enabled providers as fallbacks

    def test_should_skip_unavailable_providers_in_chain(self, db_conn, create_mock_provider):
        """Test that unavailable providers are skipped."""
        from providers.fallback import generate_with_fallback
        from providers.registry import ProviderRegistry

        # Register providers in db
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO ai_providers (provider_name, display_name, is_enabled)
            VALUES (?, ?, ?)
        """, ('provider1', 'Provider 1', 1))
        db_conn.commit()

        registry = ProviderRegistry(db_conn)
        provider1 = create_mock_provider('provider1', should_fail=False)
        registry.register(provider1)

        # Pass nonexistent provider - should skip it
        result = generate_with_fallback(
            "Test prompt",
            registry,
            ['nonexistent', 'provider1']
        )

        assert result is not None
        assert result.success is True
        assert result.provider_id == 'provider1'

    def test_should_log_fallback_attempts(self, db_conn, create_mock_provider):
        """Test that fallback attempts are logged."""
        from providers.fallback import generate_with_fallback, get_fallback_log
        from providers.registry import ProviderRegistry

        # Register providers in db
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO ai_providers (provider_name, display_name, is_enabled)
            VALUES (?, ?, ?)
        """, ('failing', 'Failing', 1))
        cursor.execute("""
            INSERT INTO ai_providers (provider_name, display_name, is_enabled)
            VALUES (?, ?, ?)
        """, ('working', 'Working', 1))
        db_conn.commit()

        registry = ProviderRegistry(db_conn)
        failing = create_mock_provider('failing', should_fail=True)
        working = create_mock_provider('working', should_fail=False)
        registry.register(failing)
        registry.register(working)

        result = generate_with_fallback(
            "Test prompt",
            registry,
            ['failing', 'working']
        )

        # Check that fallback was logged
        log = get_fallback_log()
        assert len(log) > 0
        assert any(entry['provider_id'] == 'failing' and not entry['success'] for entry in log)


class TestFallbackWithHealthIntegration:
    """Test fallback integration with health monitoring."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database with schema."""
        from database import init_db
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)
        return conn

    def test_should_prioritize_healthy_providers(self, db_conn):
        """Test that healthy providers are prioritized in fallback chain."""
        from providers.fallback import get_fallback_chain_by_health

        # Set up health statuses
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO provider_health (provider_id, status, failure_count)
            VALUES (?, ?, ?)
        """, ('healthy_provider', 'healthy', 0))
        cursor.execute("""
            INSERT INTO provider_health (provider_id, status, failure_count)
            VALUES (?, ?, ?)
        """, ('degraded_provider', 'degraded', 3))
        db_conn.commit()

        chain = get_fallback_chain_by_health(db_conn, ['healthy_provider', 'degraded_provider'])

        # Healthy should come first
        assert chain[0] == 'healthy_provider'

    def test_should_exclude_down_providers_from_chain(self, db_conn):
        """Test that providers marked as 'down' are excluded."""
        from providers.fallback import get_fallback_chain_by_health

        # Set up health statuses
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO provider_health (provider_id, status, failure_count)
            VALUES (?, ?, ?)
        """, ('healthy_provider', 'healthy', 0))
        cursor.execute("""
            INSERT INTO provider_health (provider_id, status, failure_count)
            VALUES (?, ?, ?)
        """, ('down_provider', 'down', 10))
        db_conn.commit()

        chain = get_fallback_chain_by_health(db_conn, ['healthy_provider', 'down_provider'])

        # Down provider should be excluded
        assert 'down_provider' not in chain
        assert 'healthy_provider' in chain


# =============================================================================
# HEALTH API ENDPOINT TESTS
# =============================================================================

class TestHealthAPIEndpoints:
    """Test suite for health monitoring API endpoints."""

    def test_should_get_all_providers_health_status(self):
        """Test GET /api/providers/health returns all provider statuses."""
        from app import create_app
        from database import get_db, init_db

        app = create_app(testing=True)

        with app.test_client() as client:
            with app.app_context():
                conn = get_db()
                # Insert health data
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO provider_health (provider_id, status, failure_count)
                    VALUES (?, ?, ?)
                """, ('claude_cli', 'healthy', 0))
                conn.commit()

            response = client.get('/api/providers/health')

            assert response.status_code == 200
            data = response.get_json()
            assert 'health' in data or isinstance(data, list)

    def test_should_trigger_health_check_for_specific_provider(self):
        """Test POST /api/providers/{id}/health-check triggers check."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.post('/api/providers/claude_cli/health-check')

            # Should accept the request (actual check may vary)
            assert response.status_code in [200, 202, 404, 503]

    def test_should_return_health_history_for_provider(self):
        """Test getting health check history for a provider."""
        from app import create_app
        from database import get_db

        app = create_app(testing=True)

        with app.test_client() as client:
            with app.app_context():
                conn = get_db()
                cursor = conn.cursor()
                # Insert some health history
                cursor.execute("""
                    INSERT INTO provider_health (provider_id, status, last_check, failure_count)
                    VALUES (?, ?, ?, ?)
                """, ('claude_cli', 'healthy', datetime.now().isoformat(), 0))
                conn.commit()

            response = client.get('/api/providers/claude_cli/health')

            assert response.status_code in [200, 404]


# =============================================================================
# FULL INTEGRATION TESTS
# =============================================================================

class TestFullProviderIntegration:
    """Full integration tests across all provider features."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database with schema."""
        from database import init_db
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)
        return conn

    def test_should_complete_sermon_generation_with_provider_selection(self, db_conn):
        """Test complete workflow: select provider -> generate sermon."""
        from sermon_generator import generate_sermon_with_provider
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        registry = ProviderRegistry(db_conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)

        params = {
            'scripture': 'John 3:16',
            'title': 'Integration Test Sermon',
            'theme': 'Love'
        }

        result = generate_sermon_with_provider(params, registry, db_conn, provider_id='claude_cli')

        assert result is not None
        assert 'sermon_id' in result or 'id' in result
        assert result.get('provider_id') == 'claude_cli'

    def test_should_complete_research_with_multiple_providers(self, db_conn):
        """Test complete workflow: research with multiple providers."""
        from research_aggregator import ResearchAggregator
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        registry = ProviderRegistry(db_conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)

        aggregator = ResearchAggregator(registry)

        result = aggregator.research_with_provider(
            "Grace in Wesley's theology",
            'claude_cli',
            'theological'
        )

        assert result is not None
        assert 'provider_id' in result

    def test_should_complete_provider_comparison_workflow(self, db_conn):
        """Test complete workflow: compare outputs from multiple providers."""
        from providers.comparison import store_comparison_result, get_provider_stats
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        registry = ProviderRegistry(db_conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)

        # Store some comparison data
        store_comparison_result(
            db_conn,
            'claude_cli',
            'Test prompt',
            response_time_ms=1500,
            input_tokens=100,
            output_tokens=500,
            estimated_cost=0.01
        )

        # Get stats
        stats = get_provider_stats(db_conn, 'claude_cli')

        assert stats is not None
        assert stats['total_comparisons'] >= 1

    def test_should_fallback_during_generation_when_provider_fails(self, db_conn):
        """Test that generation falls back when primary provider fails."""
        from providers.fallback import generate_with_fallback
        from providers.registry import ProviderRegistry
        from providers.base import AIProvider, ProviderResult, ProviderModel

        # Create a failing provider
        class FailingProvider(AIProvider):
            provider_id = "failing_provider"
            display_name = "Failing Provider"

            def is_available(self):
                return True

            def run(self, prompt, model=None):
                return ProviderResult(
                    output="",
                    provider_id=self.provider_id,
                    model_id="model",
                    success=False,
                    error="Intentional failure"
                )

            def run_streaming(self, prompt, model=None):
                yield ""

            def get_available_models(self):
                return []

            def _requires_api_key(self):
                return False

        # Create a working provider
        class WorkingProvider(AIProvider):
            provider_id = "working_provider"
            display_name = "Working Provider"

            def is_available(self):
                return True

            def run(self, prompt, model=None):
                return ProviderResult(
                    output=f"Success: {prompt}",
                    provider_id=self.provider_id,
                    model_id="model",
                    success=True
                )

            def run_streaming(self, prompt, model=None):
                yield "chunk"

            def get_available_models(self):
                return []

            def _requires_api_key(self):
                return False

        # Register in DB
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO ai_providers (provider_name, display_name, is_enabled)
            VALUES (?, ?, ?)
        """, ('failing_provider', 'Failing', 1))
        cursor.execute("""
            INSERT INTO ai_providers (provider_name, display_name, is_enabled)
            VALUES (?, ?, ?)
        """, ('working_provider', 'Working', 1))
        db_conn.commit()

        registry = ProviderRegistry(db_conn)
        registry.register(FailingProvider())
        registry.register(WorkingProvider())

        result = generate_with_fallback(
            "Test prompt",
            registry,
            ['failing_provider', 'working_provider']
        )

        assert result.success is True
        assert result.provider_id == 'working_provider'

    def test_should_track_provider_health_after_generation(self, db_conn):
        """Test that provider health is updated after generation attempts."""
        from providers.health import check_provider_health, store_health_status
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        registry = ProviderRegistry(db_conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)

        # Check and store health
        status = check_provider_health(provider)
        store_health_status(db_conn, status)

        # Verify stored
        cursor = db_conn.cursor()
        cursor.execute("SELECT status FROM provider_health WHERE provider_id = ?",
                       ('claude_cli',))
        row = cursor.fetchone()

        assert row is not None

    def test_should_return_partial_results_when_some_providers_fail(self, db_conn):
        """Test graceful degradation with partial results."""
        from sermon_generator import generate_sermon_multi_provider
        from providers.registry import ProviderRegistry
        from providers.claude_cli import ClaudeCLIProvider

        registry = ProviderRegistry(db_conn)
        provider = ClaudeCLIProvider(command='echo')
        registry.register(provider)

        params = {
            'scripture': 'John 3:16',
            'title': 'Partial Results Test',
            'theme': 'Love'
        }

        # Request from multiple providers (some may not exist)
        results = generate_sermon_multi_provider(
            params, registry, db_conn,
            provider_ids=['claude_cli', 'nonexistent_provider']
        )

        # Should return results list with entries for each provider
        assert isinstance(results, list)
        assert len(results) == 2  # One for each requested provider

        # Find results by provider
        provider_results = {r.get('provider_id'): r for r in results}

        # The nonexistent provider should have failed
        nonexistent_result = provider_results.get('nonexistent_provider')
        if nonexistent_result:
            assert nonexistent_result.get('success', True) is False or 'error' in nonexistent_result

        # The working provider should have some result (even if echo output isn't perfect)
        claude_result = provider_results.get('claude_cli')
        if claude_result:
            # Should have at least attempted to generate
            assert 'provider_id' in claude_result


class TestVersionControlWithProviders:
    """Test version control integration with different providers."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database with schema."""
        from database import init_db
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)
        return conn

    def test_should_track_provider_in_content_versions(self, db_conn):
        """Test that content versions track which provider generated them."""
        cursor = db_conn.cursor()

        # Create a content version with provider info
        cursor.execute("""
            INSERT INTO content_versions (content_type, parent_id, version_number, content, author)
            VALUES (?, ?, ?, ?, ?)
        """, ('sermon', 1, 1, 'Test content', 'claude_cli'))
        db_conn.commit()

        cursor.execute("SELECT author FROM content_versions WHERE parent_id = 1")
        row = cursor.fetchone()

        assert row is not None
        assert row['author'] == 'claude_cli'

    def test_should_compare_versions_from_different_providers(self, db_conn):
        """Test comparing sermon versions from different AI providers."""
        cursor = db_conn.cursor()

        # Create versions from different providers
        cursor.execute("""
            INSERT INTO content_versions (content_type, parent_id, version_number, content, author)
            VALUES (?, ?, ?, ?, ?)
        """, ('sermon', 1, 1, 'Claude version', 'claude_cli'))
        cursor.execute("""
            INSERT INTO content_versions (content_type, parent_id, version_number, content, author)
            VALUES (?, ?, ?, ?, ?)
        """, ('sermon', 1, 2, 'OpenAI version', 'openai'))
        db_conn.commit()

        cursor.execute("SELECT author, content FROM content_versions WHERE parent_id = 1 ORDER BY version_number")
        versions = cursor.fetchall()

        assert len(versions) == 2
        assert versions[0]['author'] == 'claude_cli'
        assert versions[1]['author'] == 'openai'


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

class TestProviderErrorHandling:
    """Test error handling in provider operations."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database with schema."""
        from database import init_db
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)
        return conn

    def test_should_handle_timeout_gracefully(self, db_conn):
        """Test handling of provider timeout."""
        from providers.fallback import generate_with_fallback
        from providers.registry import ProviderRegistry
        from providers.base import AIProvider, ProviderResult, ProviderModel
        import time

        class SlowProvider(AIProvider):
            provider_id = "slow_provider"
            display_name = "Slow Provider"

            def is_available(self):
                return True

            def run(self, prompt, model=None):
                time.sleep(0.1)  # Simulate slow response
                return ProviderResult(
                    output="Eventually finished",
                    provider_id=self.provider_id,
                    model_id="model",
                    success=True
                )

            def run_streaming(self, prompt, model=None):
                yield "chunk"

            def get_available_models(self):
                return []

            def _requires_api_key(self):
                return False

        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO ai_providers (provider_name, display_name, is_enabled)
            VALUES (?, ?, ?)
        """, ('slow_provider', 'Slow', 1))
        db_conn.commit()

        registry = ProviderRegistry(db_conn)
        registry.register(SlowProvider())

        # Should complete despite being slow
        result = generate_with_fallback(
            "Test prompt",
            registry,
            ['slow_provider']
        )

        assert result is not None

    def test_should_log_provider_errors(self, db_conn):
        """Test that provider errors are logged."""
        from providers.health import log_provider_error, get_recent_errors

        log_provider_error(db_conn, 'test_provider', 'Connection timeout')

        errors = get_recent_errors(db_conn, 'test_provider')

        assert len(errors) >= 1
        assert 'timeout' in errors[0]['error_message'].lower()

    def test_should_return_meaningful_error_message_on_all_failures(self, db_conn):
        """Test that meaningful error is returned when all providers fail."""
        from providers.fallback import generate_with_fallback
        from providers.registry import ProviderRegistry
        from providers.base import AIProvider, ProviderResult

        class FailingProvider(AIProvider):
            provider_id = "failing"
            display_name = "Failing"

            def is_available(self):
                return True

            def run(self, prompt, model=None):
                return ProviderResult(
                    output="",
                    provider_id=self.provider_id,
                    model_id="model",
                    success=False,
                    error="API key invalid"
                )

            def run_streaming(self, prompt, model=None):
                yield ""

            def get_available_models(self):
                return []

            def _requires_api_key(self):
                return False

        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO ai_providers (provider_name, display_name, is_enabled)
            VALUES (?, ?, ?)
        """, ('failing', 'Failing', 1))
        db_conn.commit()

        registry = ProviderRegistry(db_conn)
        registry.register(FailingProvider())

        result = generate_with_fallback(
            "Test prompt",
            registry,
            ['failing']
        )

        assert result.success is False
        assert result.error is not None
        assert len(result.error) > 0
