"""Tests for provider settings UI.

TDD: These tests are written FIRST before implementation.
"""
import pytest
from app import create_app
from database import init_db, get_db


class TestProviderSettingsUI:
    """Test the provider settings page."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app(testing=True)
        app.config['TESTING'] = True

        with app.test_client() as client:
            with app.app_context():
                conn = get_db()
                init_db(conn)
            yield client

    def test_should_load_settings_page(self, client):
        """Test that /settings/providers page loads."""
        response = client.get('/settings/providers')

        assert response.status_code == 200

    def test_should_contain_provider_list(self, client):
        """Test page contains provider list section."""
        response = client.get('/settings/providers')
        html = response.data.decode()

        assert 'Claude CLI' in html or 'claude_cli' in html
        assert 'OpenAI' in html or 'openai' in html
        assert 'Gemini' in html or 'gemini' in html

    def test_should_have_api_key_inputs(self, client):
        """Test page has API key input fields."""
        response = client.get('/settings/providers')
        html = response.data.decode()

        # Should have password-type inputs for API keys
        assert 'type="password"' in html or 'api_key' in html.lower()

    def test_should_have_enable_toggle(self, client):
        """Test page has enable/disable toggles."""
        response = client.get('/settings/providers')
        html = response.data.decode()

        # Should have toggle or checkbox for enabling
        assert 'is_enabled' in html.lower() or 'enabled' in html.lower() or 'toggle' in html.lower()

    def test_should_have_test_connection_button(self, client):
        """Test page has test connection button."""
        response = client.get('/settings/providers')
        html = response.data.decode()

        assert 'test' in html.lower()

    def test_should_have_default_selection(self, client):
        """Test page has default provider selection."""
        response = client.get('/settings/providers')
        html = response.data.decode()

        assert 'default' in html.lower()

    def test_should_show_provider_colors(self, client):
        """Test page shows provider color indicators."""
        response = client.get('/settings/providers')
        html = response.data.decode()

        # Should contain color values for providers
        assert '#D97706' in html or '#10B981' in html or '#3B82F6' in html or 'bg-amber' in html or 'bg-green' in html or 'bg-blue' in html

    def test_should_have_model_selection(self, client):
        """Test page has model selection dropdowns."""
        response = client.get('/settings/providers')
        html = response.data.decode()

        assert 'model' in html.lower()

    def test_should_use_alpine_js(self, client):
        """Test page uses Alpine.js for interactivity."""
        response = client.get('/settings/providers')
        html = response.data.decode()

        assert 'x-data' in html

    def test_should_extend_base_template(self, client):
        """Test page extends base template (has navigation)."""
        response = client.get('/settings/providers')
        html = response.data.decode()

        # Should have navigation from base template
        assert 'nav' in html.lower() or 'sidebar' in html.lower()
