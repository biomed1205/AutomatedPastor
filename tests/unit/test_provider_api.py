"""Tests for provider management API endpoints.

TDD: These tests are written FIRST before implementation.
"""
import pytest
import json
from app import create_app
from database import init_db, get_db


class TestProviderAPIEndpoints:
    """Test the provider management API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client with fresh database."""
        app = create_app(testing=True)
        app.config['TESTING'] = True

        with app.test_client() as client:
            with app.app_context():
                conn = get_db()
                init_db(conn)
            yield client

    def test_should_list_all_providers(self, client):
        """Test GET /api/providers returns all providers."""
        response = client.get('/api/providers')

        assert response.status_code == 200
        data = response.get_json()

        assert 'providers' in data
        assert len(data['providers']) >= 4  # claude_cli, claude_api, openai, gemini

        provider_names = [p['provider_name'] for p in data['providers']]
        assert 'claude_cli' in provider_names
        assert 'openai' in provider_names

    def test_should_get_single_provider(self, client):
        """Test GET /api/providers/<id> returns single provider."""
        response = client.get('/api/providers/claude_cli')

        assert response.status_code == 200
        data = response.get_json()

        assert data['provider_name'] == 'claude_cli'
        assert data['display_name'] == 'Claude CLI'
        assert data['is_enabled'] is True
        assert data['is_default'] is True
        assert 'color_primary' in data

    def test_should_return_404_for_unknown_provider(self, client):
        """Test GET /api/providers/<id> returns 404 for unknown provider."""
        response = client.get('/api/providers/nonexistent')

        assert response.status_code == 404

    def test_should_update_provider_config(self, client):
        """Test PUT /api/providers/<id> updates provider config."""
        response = client.put(
            '/api/providers/openai',
            data=json.dumps({
                'api_key': 'sk-test-new-key',
                'default_model': 'gpt-4o',
                'is_enabled': True
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

        # Verify update persisted
        response = client.get('/api/providers/openai')
        data = response.get_json()
        assert data['is_enabled'] is True
        assert data['default_model'] == 'gpt-4o'
        # API key should be masked in response
        assert 'api_key_masked' in data or data.get('has_api_key') is True

    def test_should_not_return_raw_api_key(self, client):
        """Test that raw API key is never returned in responses."""
        # First set an API key
        client.put(
            '/api/providers/openai',
            data=json.dumps({'api_key': 'sk-secret-key-12345'}),
            content_type='application/json'
        )

        # Now get the provider
        response = client.get('/api/providers/openai')
        data = response.get_json()

        # Should not contain raw API key
        assert 'sk-secret-key-12345' not in json.dumps(data)
        # But should indicate key is set
        assert data.get('has_api_key') is True or 'api_key_masked' in data

    def test_should_set_default_provider(self, client):
        """Test setting a provider as default."""
        response = client.put(
            '/api/providers/claude_api',
            data=json.dumps({
                'is_default': True,
                'api_key': 'test-key-for-api'
            }),
            content_type='application/json'
        )

        assert response.status_code == 200

        # Verify only one default
        response = client.get('/api/providers')
        data = response.get_json()
        default_count = sum(1 for p in data['providers'] if p.get('is_default'))
        assert default_count == 1

        # Verify claude_api is now default
        response = client.get('/api/providers/claude_api')
        data = response.get_json()
        assert data['is_default'] is True

    def test_should_get_provider_models(self, client):
        """Test GET /api/providers/<id>/models returns available models."""
        response = client.get('/api/providers/claude_cli/models')

        assert response.status_code == 200
        data = response.get_json()

        assert 'models' in data
        assert len(data['models']) >= 1

        # Each model should have required fields
        for model in data['models']:
            assert 'id' in model
            assert 'name' in model
            assert 'context_window' in model

    def test_should_test_provider_connection(self, client):
        """Test POST /api/providers/<id>/test tests provider connection."""
        # This tests against claude_cli which doesn't need API key
        response = client.post('/api/providers/claude_cli/test')

        assert response.status_code == 200
        data = response.get_json()

        assert 'available' in data
        # claude_cli may or may not be available depending on environment

    def test_should_fail_test_without_api_key(self, client):
        """Test that provider test fails without API key for API providers."""
        # OpenAI needs API key
        response = client.post('/api/providers/openai/test')

        data = response.get_json()

        # Should indicate not available or error
        assert data.get('available') is False or 'error' in data

    def test_should_enable_provider(self, client):
        """Test enabling a provider."""
        response = client.put(
            '/api/providers/gemini',
            data=json.dumps({
                'is_enabled': True,
                'api_key': 'test-gemini-key'
            }),
            content_type='application/json'
        )

        assert response.status_code == 200

        response = client.get('/api/providers/gemini')
        data = response.get_json()
        assert data['is_enabled'] is True

    def test_should_disable_provider(self, client):
        """Test disabling a provider."""
        response = client.put(
            '/api/providers/claude_cli',
            data=json.dumps({'is_enabled': False}),
            content_type='application/json'
        )

        assert response.status_code == 200

        response = client.get('/api/providers/claude_cli')
        data = response.get_json()
        assert data['is_enabled'] is False

    def test_should_get_enabled_providers(self, client):
        """Test GET /api/providers?enabled=true returns only enabled."""
        response = client.get('/api/providers?enabled=true')

        assert response.status_code == 200
        data = response.get_json()

        for provider in data['providers']:
            assert provider['is_enabled'] is True

    def test_should_return_404_for_unknown_provider_models(self, client):
        """Test GET /api/providers/<id>/models returns 404 for unknown provider."""
        response = client.get('/api/providers/nonexistent/models')

        assert response.status_code == 404

    def test_should_return_404_for_unknown_provider_test(self, client):
        """Test POST /api/providers/<id>/test returns 404 for unknown provider."""
        response = client.post('/api/providers/nonexistent/test')

        assert response.status_code == 404

    def test_should_reject_invalid_update_data(self, client):
        """Test PUT /api/providers/<id> validates input data."""
        # Test with invalid provider ID
        response = client.put(
            '/api/providers/nonexistent',
            data=json.dumps({'is_enabled': True}),
            content_type='application/json'
        )

        assert response.status_code == 404
