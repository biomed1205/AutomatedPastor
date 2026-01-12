"""Tests for enhanced multi-provider research capabilities.

These tests verify the enhanced research system that queries multiple AI providers
in parallel, aggregates results, and deduplicates similar findings.
Tests are written FIRST (TDD) - NO MOCKS - use real implementations.
"""
import pytest
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor


class TestResearchAggregatorInitialization:
    """Test suite for ResearchAggregator initialization."""

    def test_should_create_aggregator_when_registry_provided(self):
        """Test that aggregator can be created with a provider registry."""
        from research_aggregator import ResearchAggregator
        from providers.registry import ProviderRegistry
        from database import init_db

        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)

        registry = ProviderRegistry(conn)
        aggregator = ResearchAggregator(registry)

        assert aggregator is not None
        assert aggregator.registry is registry

    def test_should_initialize_with_default_settings(self):
        """Test that aggregator has sensible default settings."""
        from research_aggregator import ResearchAggregator
        from providers.registry import ProviderRegistry
        from database import init_db

        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)

        registry = ProviderRegistry(conn)
        aggregator = ResearchAggregator(registry)

        # Should have timeout and max_workers defaults
        assert aggregator.timeout > 0
        assert aggregator.max_workers >= 1

    def test_should_accept_custom_timeout(self):
        """Test that timeout can be configured."""
        from research_aggregator import ResearchAggregator
        from providers.registry import ProviderRegistry
        from database import init_db

        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)

        registry = ProviderRegistry(conn)
        aggregator = ResearchAggregator(registry, timeout=120)

        assert aggregator.timeout == 120

    def test_should_accept_custom_max_workers(self):
        """Test that max_workers can be configured."""
        from research_aggregator import ResearchAggregator
        from providers.registry import ProviderRegistry
        from database import init_db

        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)

        registry = ProviderRegistry(conn)
        aggregator = ResearchAggregator(registry, max_workers=5)

        assert aggregator.max_workers == 5


class TestSingleProviderResearch:
    """Test suite for research with a single provider."""

    def test_should_execute_research_on_single_provider(self):
        """Test executing research on one specific provider."""
        from research_aggregator import ResearchAggregator
        from providers.registry import ProviderRegistry
        from providers.base import AIProvider, ProviderResult
        from database import init_db

        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)

        registry = ProviderRegistry(conn)

        # Create a test provider
        class TestProvider(AIProvider):
            provider_id = "test_provider"
            display_name = "Test Provider"

            def is_available(self):
                return True

            def run(self, prompt, model=None):
                return ProviderResult(
                    output="Test research result about grace",
                    provider_id=self.provider_id,
                    model_id="test-model",
                    success=True
                )

            def run_streaming(self, prompt, model=None):
                yield "Test"

            def get_available_models(self):
                return []

        test_provider = TestProvider()
        registry.register(test_provider)

        aggregator = ResearchAggregator(registry)
        result = aggregator.research_with_provider(
            topic="Grace in John 3:16",
            provider_id="test_provider"
        )

        assert result is not None
        assert result['success'] is True
        assert 'output' in result

    def test_should_return_error_when_provider_not_found(self):
        """Test error handling when provider doesn't exist."""
        from research_aggregator import ResearchAggregator
        from providers.registry import ProviderRegistry
        from database import init_db

        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)

        registry = ProviderRegistry(conn)
        aggregator = ResearchAggregator(registry)

        result = aggregator.research_with_provider(
            topic="Test topic",
            provider_id="nonexistent_provider"
        )

        assert result['success'] is False
        assert 'error' in result


class TestMultiProviderResearch:
    """Test suite for parallel multi-provider research."""

    def test_should_query_multiple_providers_in_parallel(self):
        """Test that multiple providers are queried simultaneously."""
        from research_aggregator import ResearchAggregator
        from providers.registry import ProviderRegistry
        from providers.base import AIProvider, ProviderResult
        from database import init_db
        import time as time_module

        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)

        registry = ProviderRegistry(conn)

        # Create test providers that simulate work
        class SlowTestProvider(AIProvider):
            def __init__(self, provider_id_val, delay=0.1):
                super().__init__()
                self.provider_id = provider_id_val
                self.display_name = f"Test {provider_id_val}"
                self._delay = delay

            def is_available(self):
                return True

            def run(self, prompt, model=None):
                time_module.sleep(self._delay)
                return ProviderResult(
                    output=f"Result from {self.provider_id}",
                    provider_id=self.provider_id,
                    model_id="test-model",
                    success=True
                )

            def run_streaming(self, prompt, model=None):
                yield "Test"

            def get_available_models(self):
                return []

        # Register multiple providers
        for i in range(3):
            provider = SlowTestProvider(f"test_provider_{i}")
            registry.register(provider)

        aggregator = ResearchAggregator(registry)

        # Time the parallel execution
        start = time_module.time()
        results = aggregator.research_with_providers(
            topic="Grace in John 3:16",
            provider_ids=["test_provider_0", "test_provider_1", "test_provider_2"]
        )
        duration = time_module.time() - start

        # Should complete in roughly the time of one provider (parallel)
        # Allow some overhead but should be much less than 0.3s (sequential)
        assert duration < 0.25
        assert len(results['results']) == 3

    def test_should_use_all_enabled_providers_when_none_specified(self):
        """Test that all enabled providers are used by default."""
        from research_aggregator import ResearchAggregator
        from providers.registry import ProviderRegistry
        from providers.base import AIProvider, ProviderResult
        from database import init_db

        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)

        registry = ProviderRegistry(conn)

        # Create and register test providers
        class SimpleTestProvider(AIProvider):
            def __init__(self, provider_id_val):
                super().__init__()
                self.provider_id = provider_id_val
                self.display_name = f"Test {provider_id_val}"

            def is_available(self):
                return True

            def run(self, prompt, model=None):
                return ProviderResult(
                    output=f"Result from {self.provider_id}",
                    provider_id=self.provider_id,
                    model_id="test-model",
                    success=True
                )

            def run_streaming(self, prompt, model=None):
                yield "Test"

            def get_available_models(self):
                return []

        # Register providers and enable them in DB
        cursor = conn.cursor()
        for i in range(2):
            provider_id = f"multi_test_{i}"
            provider = SimpleTestProvider(provider_id)
            registry.register(provider)
            # Insert into DB as enabled
            cursor.execute(
                "INSERT INTO ai_providers (provider_name, display_name, is_enabled) VALUES (?, ?, ?)",
                (provider_id, f"Multi Test {i}", 1)
            )
        conn.commit()

        aggregator = ResearchAggregator(registry)
        results = aggregator.research_all_providers(topic="Test topic")

        # Should have used all enabled providers
        assert len(results['results']) >= 2

    def test_should_handle_provider_failures_gracefully(self):
        """Test that one failing provider doesn't stop others."""
        from research_aggregator import ResearchAggregator
        from providers.registry import ProviderRegistry
        from providers.base import AIProvider, ProviderResult
        from database import init_db

        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)

        registry = ProviderRegistry(conn)

        class FailingProvider(AIProvider):
            provider_id = "failing_provider"
            display_name = "Failing Provider"

            def is_available(self):
                return True

            def run(self, prompt, model=None):
                return ProviderResult(
                    output="",
                    provider_id=self.provider_id,
                    model_id="test-model",
                    success=False,
                    error="Simulated failure"
                )

            def run_streaming(self, prompt, model=None):
                yield ""

            def get_available_models(self):
                return []

        class WorkingProvider(AIProvider):
            provider_id = "working_provider"
            display_name = "Working Provider"

            def is_available(self):
                return True

            def run(self, prompt, model=None):
                return ProviderResult(
                    output="Success result",
                    provider_id=self.provider_id,
                    model_id="test-model",
                    success=True
                )

            def run_streaming(self, prompt, model=None):
                yield "Success"

            def get_available_models(self):
                return []

        registry.register(FailingProvider())
        registry.register(WorkingProvider())

        aggregator = ResearchAggregator(registry)
        results = aggregator.research_with_providers(
            topic="Test topic",
            provider_ids=["failing_provider", "working_provider"]
        )

        # Should have results from both, one error one success
        assert len(results['results']) == 2
        successful = [r for r in results['results'] if r.get('success')]
        failed = [r for r in results['results'] if not r.get('success')]
        assert len(successful) >= 1
        assert len(failed) >= 1


class TestResultAggregation:
    """Test suite for aggregating research results from multiple providers."""

    def test_should_combine_results_from_all_providers(self):
        """Test that results from all providers are combined."""
        from research_aggregator import ResearchAggregator, aggregate_research_results
        from providers.base import ProviderResult

        results = [
            {
                'provider_id': 'provider_a',
                'output': 'Insight about grace from provider A',
                'success': True
            },
            {
                'provider_id': 'provider_b',
                'output': 'Insight about grace from provider B',
                'success': True
            }
        ]

        aggregated = aggregate_research_results(results)

        assert 'combined' in aggregated or 'insights' in aggregated
        assert len(aggregated.get('provider_sources', {})) == 2

    def test_should_track_which_provider_gave_each_insight(self):
        """Test that provider sources are tracked for each insight."""
        from research_aggregator import aggregate_research_results

        results = [
            {
                'provider_id': 'claude',
                'output': 'Grace is unmerited favor',
                'success': True
            },
            {
                'provider_id': 'openai',
                'output': 'Grace represents divine love',
                'success': True
            }
        ]

        aggregated = aggregate_research_results(results)

        # Should have provider_sources mapping
        assert 'provider_sources' in aggregated
        assert 'claude' in aggregated['provider_sources']
        assert 'openai' in aggregated['provider_sources']

    def test_should_separate_successful_and_failed_results(self):
        """Test that errors are tracked separately from successes."""
        from research_aggregator import aggregate_research_results

        results = [
            {
                'provider_id': 'working',
                'output': 'Good insight',
                'success': True
            },
            {
                'provider_id': 'broken',
                'output': '',
                'success': False,
                'error': 'Connection failed'
            }
        ]

        aggregated = aggregate_research_results(results)

        assert 'errors' in aggregated
        assert len(aggregated['errors']) == 1
        assert aggregated['errors'][0]['provider_id'] == 'broken'


class TestDeduplication:
    """Test suite for deduplicating similar research findings."""

    def test_should_identify_similar_findings(self):
        """Test that semantically similar findings are identified."""
        from research_aggregator import deduplicate_findings

        findings = [
            {'content': 'Grace is unmerited favor from God', 'provider': 'claude'},
            {'content': 'Grace represents undeserved favor from the divine', 'provider': 'openai'},
            {'content': 'The parables teach kingdom values', 'provider': 'gemini'}
        ]

        deduplicated = deduplicate_findings(findings)

        # Should group similar findings together
        assert 'groups' in deduplicated or 'unique' in deduplicated
        # The two grace-related findings should be grouped
        # The parables finding should be separate

    def test_should_mark_consensus_findings(self):
        """Test that findings with consensus are marked."""
        from research_aggregator import deduplicate_findings

        findings = [
            {'content': 'John 3:16 is about Gods love', 'provider': 'claude'},
            {'content': 'John 3:16 speaks of divine love', 'provider': 'openai'},
            {'content': 'John 3:16 expresses Gods love for humanity', 'provider': 'gemini'}
        ]

        deduplicated = deduplicate_findings(findings)

        # Should identify this as a consensus finding (3 providers agree)
        assert 'consensus' in deduplicated or 'agreement_count' in deduplicated.get('groups', [{}])[0]

    def test_should_preserve_unique_findings(self):
        """Test that unique insights from each provider are preserved."""
        from research_aggregator import deduplicate_findings

        findings = [
            {'content': 'Insight unique to Claude about historical context', 'provider': 'claude'},
            {'content': 'Insight unique to OpenAI about Greek translation', 'provider': 'openai'},
            {'content': 'Insight unique to Gemini about Jewish customs', 'provider': 'gemini'}
        ]

        deduplicated = deduplicate_findings(findings)

        # All three should be preserved as unique
        unique_count = len(deduplicated.get('unique', deduplicated.get('groups', [])))
        assert unique_count >= 3


class TestResearchPromptBuilding:
    """Test suite for building research prompts."""

    def test_should_build_prompt_with_topic(self):
        """Test that prompts include the research topic."""
        from research_aggregator import build_research_prompt

        prompt = build_research_prompt(topic="Grace in John 3:16")

        assert "John 3:16" in prompt
        assert "grace" in prompt.lower() or "Grace" in prompt

    def test_should_include_context_when_provided(self):
        """Test that additional context is included in prompts."""
        from research_aggregator import build_research_prompt

        prompt = build_research_prompt(
            topic="Grace in John 3:16",
            context={
                'theme': 'salvation',
                'audience': 'university congregation'
            }
        )

        assert "salvation" in prompt.lower() or "university" in prompt.lower()

    def test_should_include_research_type_instructions(self):
        """Test that research type affects prompt instructions."""
        from research_aggregator import build_research_prompt

        biblical_prompt = build_research_prompt(
            topic="John 3:16",
            research_type="biblical_context"
        )

        illustration_prompt = build_research_prompt(
            topic="John 3:16",
            research_type="illustrations"
        )

        # Prompts should be different based on type
        assert biblical_prompt != illustration_prompt


class TestAPIEndpoint:
    """Test suite for the multi-provider research API endpoint."""

    def test_should_return_results_from_api_endpoint(self):
        """Test that API endpoint returns research results."""
        from app import create_app
        from flask import json

        app = create_app(testing=True)
        client = app.test_client()

        response = client.post(
            '/api/research/multi-provider',
            data=json.dumps({
                'topic': 'Grace in John 3:16'
            }),
            content_type='application/json'
        )

        assert response.status_code in [200, 201, 503]  # 503 if no providers available
        if response.status_code in [200, 201]:
            data = json.loads(response.data)
            assert 'results' in data or 'error' in data

    def test_should_accept_provider_list_in_request(self):
        """Test that specific providers can be requested."""
        from app import create_app
        from flask import json

        app = create_app(testing=True)
        client = app.test_client()

        response = client.post(
            '/api/research/multi-provider',
            data=json.dumps({
                'topic': 'Grace in John 3:16',
                'providers': ['claude_cli']
            }),
            content_type='application/json'
        )

        # Should accept the request (may fail if provider not available)
        assert response.status_code in [200, 201, 400, 503]

    def test_should_return_error_for_missing_topic(self):
        """Test that missing topic returns an error."""
        from app import create_app
        from flask import json

        app = create_app(testing=True)
        client = app.test_client()

        response = client.post(
            '/api/research/multi-provider',
            data=json.dumps({}),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_should_include_provider_sources_in_response(self):
        """Test that response includes provider source information."""
        from app import create_app
        from flask import json
        from providers.registry import ProviderRegistry
        from providers.base import AIProvider, ProviderResult
        from database import get_db, init_db

        app = create_app(testing=True)

        with app.app_context():
            conn = get_db()
            init_db(conn)

            # Create a simple test provider
            class InlineTestProvider(AIProvider):
                provider_id = "inline_test"
                display_name = "Inline Test"

                def is_available(self):
                    return True

                def run(self, prompt, model=None):
                    return ProviderResult(
                        output="Test result for API",
                        provider_id=self.provider_id,
                        model_id="test",
                        success=True
                    )

                def run_streaming(self, prompt, model=None):
                    yield "Test"

                def get_available_models(self):
                    return []

            # Register in the app's registry if available
            registry = ProviderRegistry(conn)
            registry.register(InlineTestProvider())

            # Insert provider into database
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO ai_providers (provider_name, display_name, is_enabled) VALUES (?, ?, ?)",
                ("inline_test", "Inline Test", 1)
            )
            conn.commit()

        client = app.test_client()
        response = client.post(
            '/api/research/multi-provider',
            data=json.dumps({
                'topic': 'Test topic'
            }),
            content_type='application/json'
        )

        # Even if providers aren't fully configured, response structure should be correct
        if response.status_code in [200, 201]:
            data = json.loads(response.data)
            # Should have provider_sources field when successful
            assert 'provider_sources' in data or 'results' in data


class TestSimilarityScoring:
    """Test suite for semantic similarity scoring."""

    def test_should_calculate_similarity_between_texts(self):
        """Test that similarity can be calculated between two texts."""
        from research_aggregator import calculate_similarity

        text1 = "Grace is unmerited favor from God"
        text2 = "Grace represents undeserved favor from the divine"
        text3 = "The weather is nice today"

        sim_high = calculate_similarity(text1, text2)
        sim_low = calculate_similarity(text1, text3)

        # Similar texts should have higher score than dissimilar
        assert sim_high > sim_low

    def test_should_return_score_between_zero_and_one(self):
        """Test that similarity scores are normalized."""
        from research_aggregator import calculate_similarity

        score = calculate_similarity(
            "Grace is important in Christian theology",
            "Grace matters in Christian thought"
        )

        assert 0.0 <= score <= 1.0

    def test_should_handle_empty_texts(self):
        """Test that empty texts don't cause errors."""
        from research_aggregator import calculate_similarity

        score = calculate_similarity("", "Some text")
        assert score == 0.0

        score = calculate_similarity("", "")
        assert score == 0.0


class TestResearchCaching:
    """Test suite for caching research results."""

    def test_should_cache_research_results(self):
        """Test that research results can be cached."""
        from research_aggregator import ResearchAggregator
        from providers.registry import ProviderRegistry
        from providers.base import AIProvider, ProviderResult
        from database import init_db

        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)

        registry = ProviderRegistry(conn)

        call_count = 0

        class CountingProvider(AIProvider):
            provider_id = "counting_provider"
            display_name = "Counting Provider"

            def is_available(self):
                return True

            def run(self, prompt, model=None):
                nonlocal call_count
                call_count += 1
                return ProviderResult(
                    output=f"Result {call_count}",
                    provider_id=self.provider_id,
                    model_id="test",
                    success=True
                )

            def run_streaming(self, prompt, model=None):
                yield "Test"

            def get_available_models(self):
                return []

        registry.register(CountingProvider())

        aggregator = ResearchAggregator(registry, use_cache=True)

        # First call should invoke provider
        result1 = aggregator.research_with_provider(
            topic="Grace in John 3:16",
            provider_id="counting_provider"
        )

        # Second call with same topic should use cache
        result2 = aggregator.research_with_provider(
            topic="Grace in John 3:16",
            provider_id="counting_provider"
        )

        # Provider should only be called once
        assert call_count == 1

    def test_should_bypass_cache_when_disabled(self):
        """Test that cache can be bypassed."""
        from research_aggregator import ResearchAggregator
        from providers.registry import ProviderRegistry
        from providers.base import AIProvider, ProviderResult
        from database import init_db

        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)

        registry = ProviderRegistry(conn)

        call_count = 0

        class CountingProvider(AIProvider):
            provider_id = "counting_provider_2"
            display_name = "Counting Provider 2"

            def is_available(self):
                return True

            def run(self, prompt, model=None):
                nonlocal call_count
                call_count += 1
                return ProviderResult(
                    output=f"Result {call_count}",
                    provider_id=self.provider_id,
                    model_id="test",
                    success=True
                )

            def run_streaming(self, prompt, model=None):
                yield "Test"

            def get_available_models(self):
                return []

        registry.register(CountingProvider())

        aggregator = ResearchAggregator(registry, use_cache=False)

        # Each call should invoke provider
        aggregator.research_with_provider(
            topic="Grace in John 3:16",
            provider_id="counting_provider_2"
        )
        aggregator.research_with_provider(
            topic="Grace in John 3:16",
            provider_id="counting_provider_2"
        )

        # Provider should be called twice
        assert call_count == 2


class TestResearchTypes:
    """Test suite for different research types."""

    def test_should_support_biblical_context_research(self):
        """Test researching biblical context."""
        from research_aggregator import ResearchAggregator
        from providers.registry import ProviderRegistry
        from providers.base import AIProvider, ProviderResult
        from database import init_db

        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)

        registry = ProviderRegistry(conn)

        class TestProvider(AIProvider):
            provider_id = "test_biblical"
            display_name = "Test Biblical"

            def is_available(self):
                return True

            def run(self, prompt, model=None):
                return ProviderResult(
                    output="Historical context of John 3:16...",
                    provider_id=self.provider_id,
                    model_id="test",
                    success=True
                )

            def run_streaming(self, prompt, model=None):
                yield "Test"

            def get_available_models(self):
                return []

        registry.register(TestProvider())

        aggregator = ResearchAggregator(registry)
        result = aggregator.research_with_provider(
            topic="John 3:16",
            provider_id="test_biblical",
            research_type="biblical_context"
        )

        assert result['success'] is True

    def test_should_support_illustration_research(self):
        """Test researching sermon illustrations."""
        from research_aggregator import ResearchAggregator
        from providers.registry import ProviderRegistry
        from providers.base import AIProvider, ProviderResult
        from database import init_db

        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)

        registry = ProviderRegistry(conn)

        class TestProvider(AIProvider):
            provider_id = "test_illustration"
            display_name = "Test Illustration"

            def is_available(self):
                return True

            def run(self, prompt, model=None):
                return ProviderResult(
                    output="Illustration about grace...",
                    provider_id=self.provider_id,
                    model_id="test",
                    success=True
                )

            def run_streaming(self, prompt, model=None):
                yield "Test"

            def get_available_models(self):
                return []

        registry.register(TestProvider())

        aggregator = ResearchAggregator(registry)
        result = aggregator.research_with_provider(
            topic="Grace",
            provider_id="test_illustration",
            research_type="illustrations"
        )

        assert result['success'] is True

    def test_should_support_theological_research(self):
        """Test researching theological insights."""
        from research_aggregator import ResearchAggregator
        from providers.registry import ProviderRegistry
        from providers.base import AIProvider, ProviderResult
        from database import init_db

        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)

        registry = ProviderRegistry(conn)

        class TestProvider(AIProvider):
            provider_id = "test_theological"
            display_name = "Test Theological"

            def is_available(self):
                return True

            def run(self, prompt, model=None):
                return ProviderResult(
                    output="Wesleyan perspective on grace...",
                    provider_id=self.provider_id,
                    model_id="test",
                    success=True
                )

            def run_streaming(self, prompt, model=None):
                yield "Test"

            def get_available_models(self):
                return []

        registry.register(TestProvider())

        aggregator = ResearchAggregator(registry)
        result = aggregator.research_with_provider(
            topic="Grace",
            provider_id="test_theological",
            research_type="theological"
        )

        assert result['success'] is True


class TestIntegrationWithSermon:
    """Test suite for integration with sermon creation workflow."""

    def test_should_store_research_results_for_sermon(self):
        """Test that research results can be stored with a sermon."""
        from research_aggregator import ResearchAggregator, store_research_for_sermon
        from providers.registry import ProviderRegistry
        from database import init_db

        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)

        # Create a test sermon
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ("Test Sermon", "John 3:16")
        )
        sermon_id = cursor.lastrowid
        conn.commit()

        research_data = {
            'results': [
                {'provider_id': 'claude', 'output': 'Claude insight', 'success': True},
                {'provider_id': 'openai', 'output': 'OpenAI insight', 'success': True}
            ],
            'provider_sources': {'claude': 'Claude insight', 'openai': 'OpenAI insight'}
        }

        stored = store_research_for_sermon(conn, sermon_id, research_data)

        assert stored is True

        # Verify storage
        cursor.execute(
            "SELECT research_data FROM sermons WHERE id = ?",
            (sermon_id,)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row['research_data'] is not None

    def test_should_retrieve_research_results_for_sermon(self):
        """Test that stored research can be retrieved."""
        from research_aggregator import store_research_for_sermon, get_research_for_sermon
        from database import init_db
        import json

        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        init_db(conn)

        # Create a test sermon
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ("Test Sermon 2", "John 3:16")
        )
        sermon_id = cursor.lastrowid
        conn.commit()

        research_data = {
            'results': [
                {'provider_id': 'claude', 'output': 'Claude insight', 'success': True}
            ],
            'provider_sources': {'claude': 'Claude insight'}
        }

        store_research_for_sermon(conn, sermon_id, research_data)

        retrieved = get_research_for_sermon(conn, sermon_id)

        assert retrieved is not None
        assert 'results' in retrieved or 'provider_sources' in retrieved
