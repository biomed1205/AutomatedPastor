"""Tests for Flask application with health endpoint.

These tests verify the Flask app can be created, configured, and responds
correctly to health check requests.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL implementations - NO MOCKS.
"""
import pytest
import json


class TestFlaskAppCreation:
    """Test suite for Flask application creation and configuration."""

    def test_should_create_app_when_called_with_test_config(self):
        """Test that Flask app can be created with test configuration."""
        # Arrange
        from app import create_app
        test_config = {'TESTING': True}

        # Act
        app = create_app(test_config)

        # Assert
        assert app is not None
        assert app.config['TESTING'] is True

    def test_should_apply_custom_config_when_provided(self):
        """Test that custom configuration is applied to the app."""
        # Arrange
        from app import create_app
        custom_config = {
            'TESTING': True,
            'DATABASE': ':memory:',
            'SECRET_KEY': 'test-secret-key'
        }

        # Act
        app = create_app(custom_config)

        # Assert
        assert app.config['DATABASE'] == ':memory:'
        assert app.config['SECRET_KEY'] == 'test-secret-key'

    def test_should_use_default_config_when_no_config_provided(self):
        """Test that app uses sensible defaults when no config given."""
        # Arrange
        from app import create_app

        # Act
        app = create_app()

        # Assert
        assert app is not None
        # App should be created successfully with defaults


class TestHealthEndpoint:
    """Test suite for /health endpoint."""

    def test_should_return_200_when_health_endpoint_called(self):
        """Test that GET /health returns HTTP 200 status code."""
        # Arrange
        from app import create_app
        app = create_app({'TESTING': True})

        # Act
        with app.test_client() as client:
            response = client.get('/health')

        # Assert
        assert response.status_code == 200

    def test_should_return_json_when_health_endpoint_called(self):
        """Test that /health returns JSON content type."""
        # Arrange
        from app import create_app
        app = create_app({'TESTING': True})

        # Act
        with app.test_client() as client:
            response = client.get('/health')

        # Assert
        assert response.content_type == 'application/json'

    def test_should_return_healthy_status_when_health_endpoint_called(self):
        """Test that /health returns {"status": "healthy"} in body."""
        # Arrange
        from app import create_app
        app = create_app({'TESTING': True})

        # Act
        with app.test_client() as client:
            response = client.get('/health')
            data = json.loads(response.data)

        # Assert
        assert data == {'status': 'healthy'}

    def test_should_only_accept_get_method_for_health_endpoint(self):
        """Test that /health rejects non-GET requests."""
        # Arrange
        from app import create_app
        app = create_app({'TESTING': True})

        # Act & Assert
        with app.test_client() as client:
            post_response = client.post('/health')
            put_response = client.put('/health')
            delete_response = client.delete('/health')

        # POST, PUT, DELETE should return 405 Method Not Allowed
        assert post_response.status_code == 405
        assert put_response.status_code == 405
        assert delete_response.status_code == 405


class TestAppConfiguration:
    """Test suite for app configuration and port settings."""

    def test_should_configure_port_8787_when_default_config_used(self):
        """Test that app is configured to run on port 8787."""
        # Arrange
        from app import create_app, DEFAULT_PORT

        # Act
        app = create_app({'TESTING': True})

        # Assert
        assert DEFAULT_PORT == 8787

    def test_should_have_debug_disabled_in_production_config(self):
        """Test that debug mode is off unless explicitly enabled."""
        # Arrange
        from app import create_app

        # Act
        app = create_app()  # No TESTING or DEBUG flag

        # Assert
        # In production, debug should be False
        assert app.config.get('DEBUG', False) is False

    def test_should_enable_testing_mode_when_testing_config_true(self):
        """Test that TESTING mode is properly enabled."""
        # Arrange
        from app import create_app

        # Act
        app = create_app({'TESTING': True})

        # Assert
        assert app.testing is True


class TestErrorHandling:
    """Test suite for error handling in the app."""

    def test_should_return_404_when_unknown_route_accessed(self):
        """Test that unknown routes return 404."""
        # Arrange
        from app import create_app
        app = create_app({'TESTING': True})

        # Act
        with app.test_client() as client:
            response = client.get('/nonexistent-route-12345')

        # Assert
        assert response.status_code == 404

    def test_should_return_json_error_for_404(self):
        """Test that 404 errors return JSON response."""
        # Arrange
        from app import create_app
        app = create_app({'TESTING': True})

        # Act
        with app.test_client() as client:
            response = client.get('/nonexistent-route-12345')

        # Assert
        # Should return JSON error, not HTML
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert 'error' in data
