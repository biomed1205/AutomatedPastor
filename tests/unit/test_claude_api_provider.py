"""Tests for Claude API provider.

TDD: These tests are written FIRST before implementation.
"""
import os
import pytest
from unittest.mock import patch, MagicMock


class TestClaudeAPIProvider:
    """Test the Claude API provider implementation."""

    def test_should_extend_ai_provider(self):
        """Test that ClaudeAPIProvider extends AIProvider."""
        from providers.claude_api import ClaudeAPIProvider
        from providers.base import AIProvider

        provider = ClaudeAPIProvider(api_key="test-key")
        assert isinstance(provider, AIProvider)

    def test_should_have_correct_provider_id(self):
        """Test provider ID is 'claude_api'."""
        from providers.claude_api import ClaudeAPIProvider

        provider = ClaudeAPIProvider(api_key="test-key")
        assert provider.provider_id == "claude_api"
        assert provider.display_name == "Claude API"

    def test_should_have_correct_colors(self):
        """Test provider has amber colors (same as CLI)."""
        from providers.claude_api import ClaudeAPIProvider

        provider = ClaudeAPIProvider(api_key="test-key")
        assert provider.color_primary == "#D97706"
        assert provider.color_bg == "#FEF3C7"

    def test_should_require_api_key(self):
        """Test that API provider requires API key."""
        from providers.claude_api import ClaudeAPIProvider

        # Clear env var to ensure clean test
        env_backup = os.environ.get("ANTHROPIC_API_KEY")
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]

        try:
            provider = ClaudeAPIProvider()  # No API key
            is_valid, message = provider.validate_config()
            assert is_valid is False
            assert "API key" in message
        finally:
            if env_backup:
                os.environ["ANTHROPIC_API_KEY"] = env_backup

    def test_should_validate_with_api_key(self):
        """Test validation passes with API key."""
        from providers.claude_api import ClaudeAPIProvider

        provider = ClaudeAPIProvider(api_key="test-key")
        is_valid, _ = provider.validate_config()
        assert is_valid is True

    def test_should_read_api_key_from_environment(self, monkeypatch):
        """Test reading API key from ANTHROPIC_API_KEY env var."""
        from providers.claude_api import ClaudeAPIProvider

        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-test-key")

        provider = ClaudeAPIProvider()
        assert provider.api_key == "env-test-key"

    def test_should_check_availability_with_key(self):
        """Test availability check with API key."""
        from providers.claude_api import ClaudeAPIProvider

        provider = ClaudeAPIProvider(api_key="test-key")
        # Should be available if key is set (actual API call not required)
        assert provider.is_available() is True

    def test_should_check_availability_without_key(self, monkeypatch):
        """Test availability check without API key."""
        from providers.claude_api import ClaudeAPIProvider

        # Clear env var
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        provider = ClaudeAPIProvider()
        assert provider.is_available() is False

    def test_should_return_provider_result(self):
        """Test that run() returns ProviderResult."""
        from providers.claude_api import ClaudeAPIProvider
        from providers.base import ProviderResult

        provider = ClaudeAPIProvider(api_key="test-key")

        # Mock the anthropic client
        with patch.object(provider, '_get_client') as mock_client:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Test response")]
            mock_client.return_value.messages.create.return_value = mock_response

            result = provider.run("test prompt")

            assert isinstance(result, ProviderResult)
            assert result.provider_id == "claude_api"

    def test_should_handle_api_error(self):
        """Test handling API errors gracefully."""
        from providers.claude_api import ClaudeAPIProvider

        provider = ClaudeAPIProvider(api_key="test-key")

        with patch.object(provider, '_get_client') as mock_client:
            mock_client.return_value.messages.create.side_effect = Exception("API Error")

            result = provider.run("test")

            assert result.success is False
            assert result.error is not None

    def test_should_track_duration(self):
        """Test that execution duration is tracked."""
        from providers.claude_api import ClaudeAPIProvider

        provider = ClaudeAPIProvider(api_key="test-key")

        with patch.object(provider, '_get_client') as mock_client:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Response")]
            mock_client.return_value.messages.create.return_value = mock_response

            result = provider.run("test")

            assert result.duration >= 0

    def test_should_get_available_models(self):
        """Test getting available Claude models."""
        from providers.claude_api import ClaudeAPIProvider
        from providers.base import ProviderModel

        provider = ClaudeAPIProvider(api_key="test-key")
        models = provider.get_available_models()

        assert len(models) >= 1
        assert all(isinstance(m, ProviderModel) for m in models)
        # Should include Claude Sonnet
        model_ids = [m.id for m in models]
        assert any("sonnet" in m.lower() for m in model_ids)

    def test_should_use_default_model(self):
        """Test using default model when not specified."""
        from providers.claude_api import ClaudeAPIProvider

        provider = ClaudeAPIProvider(api_key="test-key", default_model="claude-3-haiku-20240307")

        with patch.object(provider, '_get_client') as mock_client:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Response")]
            mock_client.return_value.messages.create.return_value = mock_response

            provider.run("test")

            # Check that default model was used
            call_args = mock_client.return_value.messages.create.call_args
            assert call_args.kwargs.get('model') == "claude-3-haiku-20240307"

    def test_should_override_model(self):
        """Test overriding model in run call."""
        from providers.claude_api import ClaudeAPIProvider

        provider = ClaudeAPIProvider(api_key="test-key", default_model="claude-3-haiku-20240307")

        with patch.object(provider, '_get_client') as mock_client:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Response")]
            mock_client.return_value.messages.create.return_value = mock_response

            provider.run("test", model="claude-3-opus-20240229")

            call_args = mock_client.return_value.messages.create.call_args
            assert call_args.kwargs.get('model') == "claude-3-opus-20240229"

    def test_should_support_streaming(self):
        """Test streaming output."""
        from providers.claude_api import ClaudeAPIProvider

        provider = ClaudeAPIProvider(api_key="test-key")

        # Mock streaming response using context manager pattern
        with patch.object(provider, '_get_client') as mock_client:
            # Create mock stream context manager
            mock_stream = MagicMock()
            mock_stream.text_stream = iter(["Hello", " World"])
            mock_stream.__enter__ = MagicMock(return_value=mock_stream)
            mock_stream.__exit__ = MagicMock(return_value=False)
            mock_client.return_value.messages.stream.return_value = mock_stream

            chunks = list(provider.run_streaming("test"))

            assert len(chunks) > 0

    def test_should_set_max_tokens(self):
        """Test that max_tokens is set correctly."""
        from providers.claude_api import ClaudeAPIProvider

        provider = ClaudeAPIProvider(api_key="test-key", max_tokens=4096)

        with patch.object(provider, '_get_client') as mock_client:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Response")]
            mock_client.return_value.messages.create.return_value = mock_response

            provider.run("test")

            call_args = mock_client.return_value.messages.create.call_args
            assert call_args.kwargs.get('max_tokens') == 4096

    def test_should_have_default_max_tokens(self):
        """Test that default max_tokens is 8192."""
        from providers.claude_api import ClaudeAPIProvider

        provider = ClaudeAPIProvider(api_key="test-key")

        with patch.object(provider, '_get_client') as mock_client:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Response")]
            mock_client.return_value.messages.create.return_value = mock_response

            provider.run("test")

            call_args = mock_client.return_value.messages.create.call_args
            assert call_args.kwargs.get('max_tokens') == 8192


class TestAPIBridgeBackwardCompat:
    """Test backward compatibility with original APIBridge."""

    def test_should_import_api_bridge(self):
        """Test that original APIBridge import still works."""
        from api_bridge import APIBridge

        bridge = APIBridge(api_key="test-key")
        assert bridge is not None

    def test_should_have_run_method(self):
        """Test that run method exists."""
        from api_bridge import APIBridge

        bridge = APIBridge(api_key="test-key")
        assert hasattr(bridge, 'run')
        assert callable(bridge.run)

    def test_should_maintain_cli_bridge_result_compatibility(self):
        """Test result has expected attributes."""
        from api_bridge import APIBridge

        bridge = APIBridge(api_key="test-key")

        with patch.object(bridge, '_get_client') as mock_client:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Test")]
            mock_client.return_value.messages.create.return_value = mock_response

            result = bridge.run("test")

            # Should have CLIBridgeResult-compatible attributes
            assert hasattr(result, 'output')
            assert hasattr(result, 'success')

    def test_should_handle_empty_prompt(self):
        """Test handling of empty prompt."""
        from api_bridge import APIBridge

        bridge = APIBridge(api_key="test-key")
        result = bridge.run("")

        assert result.success is False
        assert result.output == ""

    def test_should_use_get_bridge_function(self):
        """Test get_bridge function returns appropriate bridge."""
        from api_bridge import get_bridge, APIBridge

        # With API key in env
        os.environ["ANTHROPIC_API_KEY"] = "test-key"
        try:
            bridge = get_bridge(prefer_api=True)
            assert isinstance(bridge, APIBridge)
        finally:
            del os.environ["ANTHROPIC_API_KEY"]


class TestClaudeAPIProviderIntegration:
    """Integration tests for Claude API provider with the AIProvider interface."""

    def test_should_work_with_provider_registry(self):
        """Test that provider can be registered and discovered."""
        from providers.claude_api import ClaudeAPIProvider
        from providers.base import AIProvider

        # Provider should be a subclass of AIProvider
        assert issubclass(ClaudeAPIProvider, AIProvider)

    def test_should_provide_result_with_all_fields(self):
        """Test that ProviderResult has all required fields."""
        from providers.claude_api import ClaudeAPIProvider
        from providers.base import ProviderResult

        provider = ClaudeAPIProvider(api_key="test-key")

        with patch.object(provider, '_get_client') as mock_client:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Test output")]
            mock_response.usage = MagicMock(output_tokens=50)
            mock_client.return_value.messages.create.return_value = mock_response

            result = provider.run("test")

            # Check all required fields
            assert hasattr(result, 'output')
            assert hasattr(result, 'provider_id')
            assert hasattr(result, 'model_id')
            assert hasattr(result, 'success')
            assert hasattr(result, 'error')
            assert hasattr(result, 'duration')

    def test_should_get_status_available(self):
        """Test get_status returns AVAILABLE when configured."""
        from providers.claude_api import ClaudeAPIProvider
        from providers.base import ProviderStatus

        provider = ClaudeAPIProvider(api_key="test-key")
        status = provider.get_status()

        assert status == ProviderStatus.AVAILABLE

    def test_should_get_status_unavailable_without_key(self, monkeypatch):
        """Test get_status returns appropriate status without key."""
        from providers.claude_api import ClaudeAPIProvider
        from providers.base import ProviderStatus

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        provider = ClaudeAPIProvider()
        status = provider.get_status()

        # Should be DISABLED because config validation fails (no API key)
        assert status == ProviderStatus.DISABLED
