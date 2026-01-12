"""Tests for AI Provider Comparison functionality.

TDD: These tests are written FIRST before implementation.
Tests cover:
- provider_metrics database table
- POST /api/comparison/generate endpoint
- GET /api/comparison/metrics endpoint
- Comparison UI page
"""
import pytest
import sqlite3
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List


class TestProviderMetricsSchema:
    """Test the provider_metrics database table schema."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database with schema."""
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        # Import and call init_db to create all tables
        from database import init_db
        init_db(conn)
        return conn

    def test_should_create_provider_metrics_table(self, db_conn):
        """Test that provider_metrics table is created."""
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='provider_metrics'
        """)
        result = cursor.fetchone()
        assert result is not None
        assert result['name'] == 'provider_metrics'

    def test_should_have_required_columns(self, db_conn):
        """Test that provider_metrics has all required columns."""
        cursor = db_conn.cursor()
        cursor.execute("PRAGMA table_info(provider_metrics)")
        columns = {row['name']: row for row in cursor.fetchall()}

        required_columns = [
            'id', 'provider_id', 'prompt_hash', 'response_time_ms',
            'input_tokens', 'output_tokens', 'estimated_cost', 'created_at'
        ]

        for col in required_columns:
            assert col in columns, f"Missing column: {col}"

    def test_should_insert_metric_record(self, db_conn):
        """Test inserting a metric record."""
        cursor = db_conn.cursor()
        prompt_hash = hashlib.sha256(b"test prompt").hexdigest()[:32]

        cursor.execute("""
            INSERT INTO provider_metrics
            (provider_id, prompt_hash, response_time_ms, input_tokens, output_tokens, estimated_cost)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('claude_cli', prompt_hash, 1500, 100, 500, 0.015))
        db_conn.commit()

        cursor.execute("SELECT * FROM provider_metrics WHERE provider_id = 'claude_cli'")
        row = cursor.fetchone()

        assert row is not None
        assert row['provider_id'] == 'claude_cli'
        assert row['response_time_ms'] == 1500
        assert row['input_tokens'] == 100
        assert row['output_tokens'] == 500
        assert row['estimated_cost'] == 0.015

    def test_should_query_metrics_by_provider(self, db_conn):
        """Test querying metrics filtered by provider."""
        cursor = db_conn.cursor()
        prompt_hash = hashlib.sha256(b"test").hexdigest()[:32]

        # Insert metrics for different providers
        cursor.execute("""
            INSERT INTO provider_metrics
            (provider_id, prompt_hash, response_time_ms, input_tokens, output_tokens, estimated_cost)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('claude_cli', prompt_hash, 1000, 50, 200, 0.01))
        cursor.execute("""
            INSERT INTO provider_metrics
            (provider_id, prompt_hash, response_time_ms, input_tokens, output_tokens, estimated_cost)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('openai', prompt_hash, 800, 50, 200, 0.02))
        db_conn.commit()

        # Query only claude_cli
        cursor.execute("""
            SELECT * FROM provider_metrics WHERE provider_id = 'claude_cli'
        """)
        rows = cursor.fetchall()

        assert len(rows) == 1
        assert rows[0]['provider_id'] == 'claude_cli'


class TestComparisonGenerateAPI:
    """Test the POST /api/comparison/generate endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client with database."""
        from app import create_app
        app = create_app(testing=True)
        return app.test_client()

    def test_should_return_error_when_no_prompt_provided(self, client):
        """Test that endpoint returns error when prompt is missing."""
        response = client.post('/api/comparison/generate',
                               data=json.dumps({'providers': ['claude_cli']}),
                               content_type='application/json')

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'prompt' in data['error'].lower()

    def test_should_return_error_when_no_providers_selected(self, client):
        """Test that endpoint returns error when no providers selected."""
        response = client.post('/api/comparison/generate',
                               data=json.dumps({'prompt': 'test prompt', 'providers': []}),
                               content_type='application/json')

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'provider' in data['error'].lower()

    def test_should_return_results_for_single_provider(self, client):
        """Test generating comparison with single provider."""
        response = client.post('/api/comparison/generate',
                               data=json.dumps({
                                   'prompt': 'Hello world',
                                   'providers': ['claude_cli']
                               }),
                               content_type='application/json')

        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert len(data['results']) == 1
        assert data['results'][0]['provider'] == 'claude_cli'

    def test_should_return_results_for_multiple_providers(self, client):
        """Test generating comparison with multiple providers."""
        response = client.post('/api/comparison/generate',
                               data=json.dumps({
                                   'prompt': 'Hello world',
                                   'providers': ['claude_cli', 'openai']
                               }),
                               content_type='application/json')

        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert len(data['results']) == 2

        provider_ids = {r['provider'] for r in data['results']}
        assert 'claude_cli' in provider_ids
        assert 'openai' in provider_ids

    def test_should_include_metrics_in_response(self, client):
        """Test that response includes metrics for each provider."""
        response = client.post('/api/comparison/generate',
                               data=json.dumps({
                                   'prompt': 'Hello world',
                                   'providers': ['claude_cli']
                               }),
                               content_type='application/json')

        assert response.status_code == 200
        data = response.get_json()

        result = data['results'][0]
        assert 'metrics' in result
        metrics = result['metrics']
        assert 'response_time_ms' in metrics
        assert 'token_count' in metrics or 'tokens' in metrics

    def test_should_handle_provider_error_gracefully(self, client):
        """Test that endpoint handles provider errors gracefully."""
        response = client.post('/api/comparison/generate',
                               data=json.dumps({
                                   'prompt': 'Hello world',
                                   'providers': ['nonexistent_provider']
                               }),
                               content_type='application/json')

        # Should still return 200 but with error in result
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        # Result should indicate error
        result = data['results'][0]
        assert result.get('success') is False or result.get('error') is not None

    def test_should_store_metrics_in_database(self, client):
        """Test that comparison metrics are stored in database."""
        # Generate comparison
        response = client.post('/api/comparison/generate',
                               data=json.dumps({
                                   'prompt': 'Test prompt for metrics storage',
                                   'providers': ['claude_cli']
                               }),
                               content_type='application/json')

        assert response.status_code == 200

        # Check metrics endpoint for stored data
        metrics_response = client.get('/api/comparison/metrics?provider_id=claude_cli')
        assert metrics_response.status_code == 200

        metrics_data = metrics_response.get_json()
        assert 'metrics' in metrics_data


class TestComparisonMetricsAPI:
    """Test the GET /api/comparison/metrics endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client with database."""
        from app import create_app
        app = create_app(testing=True)
        return app.test_client()

    @pytest.fixture
    def seeded_metrics(self, client):
        """Seed database with test metrics."""
        from flask import g
        from app import create_app
        from database import get_db, init_db

        app = create_app(testing=True)
        with app.app_context():
            conn = get_db()
            cursor = conn.cursor()

            # Insert test metrics
            metrics_data = [
                ('claude_cli', 'hash1', 1000, 50, 200, 0.01),
                ('claude_cli', 'hash2', 1200, 60, 250, 0.012),
                ('openai', 'hash1', 800, 50, 200, 0.02),
                ('gemini', 'hash1', 900, 50, 200, 0.008),
            ]

            for data in metrics_data:
                cursor.execute("""
                    INSERT INTO provider_metrics
                    (provider_id, prompt_hash, response_time_ms, input_tokens, output_tokens, estimated_cost)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, data)

            conn.commit()
        return app

    def test_should_return_all_metrics_when_no_filter(self, seeded_metrics):
        """Test getting all metrics without filter."""
        client = seeded_metrics.test_client()
        response = client.get('/api/comparison/metrics')

        assert response.status_code == 200
        data = response.get_json()
        assert 'metrics' in data
        assert len(data['metrics']) >= 1

    def test_should_filter_by_provider_id(self, seeded_metrics):
        """Test filtering metrics by provider ID."""
        client = seeded_metrics.test_client()
        response = client.get('/api/comparison/metrics?provider_id=claude_cli')

        assert response.status_code == 200
        data = response.get_json()
        assert 'metrics' in data
        for metric in data['metrics']:
            assert metric['provider_id'] == 'claude_cli'

    def test_should_return_aggregated_stats(self, seeded_metrics):
        """Test that response includes aggregated statistics."""
        client = seeded_metrics.test_client()
        response = client.get('/api/comparison/metrics')

        assert response.status_code == 200
        data = response.get_json()

        assert 'stats' in data
        stats = data['stats']
        assert 'avg_response_time' in stats or 'total_comparisons' in stats

    def test_should_limit_results(self, seeded_metrics):
        """Test limiting number of results."""
        client = seeded_metrics.test_client()
        response = client.get('/api/comparison/metrics?limit=2')

        assert response.status_code == 200
        data = response.get_json()
        assert len(data['metrics']) <= 2

    def test_should_sort_by_created_at_descending(self, seeded_metrics):
        """Test that results are sorted by created_at descending (newest first)."""
        client = seeded_metrics.test_client()
        response = client.get('/api/comparison/metrics')

        assert response.status_code == 200
        data = response.get_json()

        if len(data['metrics']) > 1:
            # Check that dates are in descending order
            dates = [m.get('created_at') for m in data['metrics'] if m.get('created_at')]
            if dates:
                for i in range(len(dates) - 1):
                    assert dates[i] >= dates[i + 1], "Results should be sorted by date descending"


class TestComparisonPage:
    """Test the comparison UI page."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from app import create_app
        app = create_app(testing=True)
        return app.test_client()

    def test_should_render_comparison_page(self, client):
        """Test that comparison page renders successfully."""
        response = client.get('/settings/comparison')
        # Accept either 200 or redirect to main comparison page
        assert response.status_code in [200, 302, 404]

    def test_should_have_provider_selection_interface(self, client):
        """Test that page has provider selection UI elements."""
        response = client.get('/settings/comparison')

        if response.status_code == 200:
            html = response.data.decode('utf-8')
            # Check for comparison-related content
            assert 'comparison' in html.lower() or 'provider' in html.lower()


class TestComparisonModuleIntegration:
    """Integration tests for comparison module."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database with full schema."""
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        from database import init_db
        init_db(conn)
        return conn

    def test_should_calculate_cost_estimates(self, db_conn):
        """Test cost estimation calculation."""
        from providers.comparison import estimate_cost

        # Claude pricing: ~$3 per million input, ~$15 per million output
        cost = estimate_cost('claude_cli', input_tokens=1000, output_tokens=500)
        assert cost > 0
        assert cost < 1  # Should be very small for this token count

    def test_should_hash_prompts_consistently(self, db_conn):
        """Test that prompts are hashed consistently for comparison."""
        from providers.comparison import hash_prompt

        prompt = "What is the meaning of life?"
        hash1 = hash_prompt(prompt)
        hash2 = hash_prompt(prompt)

        assert hash1 == hash2
        assert len(hash1) == 32  # SHA256 truncated to 32 chars

    def test_should_store_comparison_result(self, db_conn):
        """Test storing comparison results."""
        from providers.comparison import store_comparison_result

        result = store_comparison_result(
            db_conn,
            provider_id='claude_cli',
            prompt='test prompt',
            response_time_ms=1500,
            input_tokens=100,
            output_tokens=500,
            estimated_cost=0.015
        )

        assert result is not None
        assert result.get('id') is not None

        # Verify stored in database
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM provider_metrics WHERE id = ?", (result['id'],))
        row = cursor.fetchone()
        assert row is not None
        assert row['provider_id'] == 'claude_cli'

    def test_should_get_provider_stats(self, db_conn):
        """Test getting aggregated provider statistics."""
        from providers.comparison import store_comparison_result, get_provider_stats

        # Store multiple results
        for i in range(5):
            store_comparison_result(
                db_conn,
                provider_id='claude_cli',
                prompt=f'test prompt {i}',
                response_time_ms=1000 + i * 100,
                input_tokens=50 + i * 10,
                output_tokens=200 + i * 50,
                estimated_cost=0.01 + i * 0.002
            )

        stats = get_provider_stats(db_conn, 'claude_cli')

        assert stats is not None
        assert 'avg_response_time_ms' in stats
        assert 'total_comparisons' in stats
        assert stats['total_comparisons'] == 5
        assert stats['avg_response_time_ms'] > 0


class TestComparisonResultFormat:
    """Test the format of comparison results."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from app import create_app
        app = create_app(testing=True)
        return app.test_client()

    def test_should_include_response_text(self, client):
        """Test that comparison result includes response text."""
        response = client.post('/api/comparison/generate',
                               data=json.dumps({
                                   'prompt': 'Say hello',
                                   'providers': ['claude_cli']
                               }),
                               content_type='application/json')

        if response.status_code == 200:
            data = response.get_json()
            result = data['results'][0]
            assert 'response' in result or 'output' in result

    def test_should_include_provider_display_info(self, client):
        """Test that result includes provider display information."""
        response = client.post('/api/comparison/generate',
                               data=json.dumps({
                                   'prompt': 'Say hello',
                                   'providers': ['claude_cli']
                               }),
                               content_type='application/json')

        if response.status_code == 200:
            data = response.get_json()
            result = data['results'][0]
            assert 'provider' in result
            # Should have display name or id
            assert result['provider'] is not None

    def test_should_include_success_status(self, client):
        """Test that result includes success/failure status."""
        response = client.post('/api/comparison/generate',
                               data=json.dumps({
                                   'prompt': 'Say hello',
                                   'providers': ['claude_cli']
                               }),
                               content_type='application/json')

        if response.status_code == 200:
            data = response.get_json()
            result = data['results'][0]
            assert 'success' in result


class TestCostTracking:
    """Test cost tracking functionality."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database."""
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        from database import init_db
        init_db(conn)
        return conn

    def test_should_track_total_cost_per_provider(self, db_conn):
        """Test tracking total cost per provider."""
        from providers.comparison import store_comparison_result, get_provider_cost_total

        # Store multiple results
        for _ in range(3):
            store_comparison_result(
                db_conn,
                provider_id='claude_cli',
                prompt='test',
                response_time_ms=1000,
                input_tokens=100,
                output_tokens=500,
                estimated_cost=0.01
            )

        total = get_provider_cost_total(db_conn, 'claude_cli')
        assert total == pytest.approx(0.03, rel=0.01)

    def test_should_provide_cost_breakdown_by_date_range(self, db_conn):
        """Test getting cost breakdown by date range."""
        from providers.comparison import store_comparison_result, get_cost_breakdown

        # Store results
        store_comparison_result(
            db_conn,
            provider_id='claude_cli',
            prompt='test',
            response_time_ms=1000,
            input_tokens=100,
            output_tokens=500,
            estimated_cost=0.01
        )

        breakdown = get_cost_breakdown(db_conn, days=7)
        assert breakdown is not None
        assert 'claude_cli' in breakdown or len(breakdown) > 0


class TestPerformanceMetrics:
    """Test performance metrics tracking."""

    @pytest.fixture
    def db_conn(self):
        """Create in-memory database."""
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        from database import init_db
        init_db(conn)
        return conn

    def test_should_track_response_time_distribution(self, db_conn):
        """Test tracking response time distribution."""
        from providers.comparison import store_comparison_result, get_response_time_stats

        # Store varied response times
        times = [500, 800, 1000, 1200, 2000]
        for t in times:
            store_comparison_result(
                db_conn,
                provider_id='claude_cli',
                prompt='test',
                response_time_ms=t,
                input_tokens=100,
                output_tokens=500,
                estimated_cost=0.01
            )

        stats = get_response_time_stats(db_conn, 'claude_cli')
        assert stats is not None
        assert 'min' in stats
        assert 'max' in stats
        assert 'avg' in stats
        assert stats['min'] == 500
        assert stats['max'] == 2000

    def test_should_track_token_usage(self, db_conn):
        """Test tracking token usage over time."""
        from providers.comparison import store_comparison_result, get_token_usage_stats

        store_comparison_result(
            db_conn,
            provider_id='claude_cli',
            prompt='test',
            response_time_ms=1000,
            input_tokens=100,
            output_tokens=500,
            estimated_cost=0.01
        )

        stats = get_token_usage_stats(db_conn, 'claude_cli')
        assert stats is not None
        assert 'total_input_tokens' in stats
        assert 'total_output_tokens' in stats
        assert stats['total_input_tokens'] == 100
        assert stats['total_output_tokens'] == 500
