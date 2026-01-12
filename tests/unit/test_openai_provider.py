"""Tests for OpenAI provider.

TDD: These tests are written FIRST before implementation.
"""
import os
import pytest
from unittest.mock import patch, MagicMock


class TestOpenAIProvider:
    """Test the OpenAI provider implementation."""

    def test_should_extend_ai_provider(self):
        """Test that OpenAIProvider extends AIProvider."""
        from providers.openai_api import OpenAIProvider
        from providers.base import AIProvider

        provider = OpenAIProvider(api_key="test-key")
        assert isinstance(provider, AIProvider)

    def test_should_have_correct_provider_id(self):
        """Test provider ID is 'openai'."""
        from providers.openai_api import OpenAIProvider

        provider = OpenAIProvider(api_key="test-key")
        assert provider.provider_id == "openai"
        assert provider.display_name == "OpenAI"

    def test_should_have_correct_colors(self):
        """Test provider has green colors."""
        from providers.openai_api import OpenAIProvider

        provider = OpenAIProvider(api_key="test-key")
        assert provider.color_primary == "#10B981"
        assert provider.color_bg == "#D1FAE5"

    def test_should_require_api_key(self):
        """Test that OpenAI provider requires API key."""
        from providers.openai_api import OpenAIProvider

        # Clear env var
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

        provider = OpenAIProvider()
        is_valid, message = provider.validate_config()
        assert is_valid is False
        assert "API key" in message

    def test_should_validate_with_api_key(self):
        """Test validation passes with API key."""
        from providers.openai_api import OpenAIProvider

        provider = OpenAIProvider(api_key="sk-test-key")
        is_valid, _ = provider.validate_config()
        assert is_valid is True

    def test_should_read_api_key_from_environment(self, monkeypatch):
        """Test reading API key from OPENAI_API_KEY env var."""
        from providers.openai_api import OpenAIProvider

        monkeypatch.setenv("OPENAI_API_KEY", "sk-env-test-key")

        provider = OpenAIProvider()
        assert provider.api_key == "sk-env-test-key"

    def test_should_check_availability_with_key(self):
        """Test availability check with API key."""
        from providers.openai_api import OpenAIProvider

        provider = OpenAIProvider(api_key="sk-test-key")
        assert provider.is_available() is True

    def test_should_check_availability_without_key(self):
        """Test availability check without API key."""
        from providers.openai_api import OpenAIProvider

        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

        provider = OpenAIProvider()
        assert provider.is_available() is False

    def test_should_return_provider_result(self):
        """Test that run() returns ProviderResult."""
        from providers.openai_api import OpenAIProvider
        from providers.base import ProviderResult

        provider = OpenAIProvider(api_key="sk-test-key")

        with patch.object(provider, '_get_client') as mock_client:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
            mock_response.usage = MagicMock(total_tokens=100)
            mock_client.return_value.chat.completions.create.return_value = mock_response

            result = provider.run("test prompt")

            assert isinstance(result, ProviderResult)
            assert result.provider_id == "openai"

    def test_should_handle_api_error(self):
        """Test handling API errors gracefully."""
        from providers.openai_api import OpenAIProvider

        provider = OpenAIProvider(api_key="sk-test-key")

        with patch.object(provider, '_get_client') as mock_client:
            mock_client.return_value.chat.completions.create.side_effect = Exception("API Error")

            result = provider.run("test")

            assert result.success is False
            assert result.error is not None

    def test_should_get_available_models(self):
        """Test getting available OpenAI models."""
        from providers.openai_api import OpenAIProvider
        from providers.base import ProviderModel

        provider = OpenAIProvider(api_key="sk-test-key")
        models = provider.get_available_models()

        assert len(models) >= 3
        assert all(isinstance(m, ProviderModel) for m in models)

        model_ids = [m.id for m in models]
        assert "gpt-4o" in model_ids
        assert "gpt-4o-mini" in model_ids

    def test_should_use_default_model(self):
        """Test using default model when not specified."""
        from providers.openai_api import OpenAIProvider

        provider = OpenAIProvider(api_key="sk-test-key", default_model="gpt-4o")

        with patch.object(provider, '_get_client') as mock_client:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
            mock_response.usage = MagicMock(total_tokens=50)
            mock_client.return_value.chat.completions.create.return_value = mock_response

            provider.run("test")

            call_args = mock_client.return_value.chat.completions.create.call_args
            assert call_args.kwargs.get('model') == "gpt-4o"

    def test_should_support_streaming(self):
        """Test streaming output."""
        from providers.openai_api import OpenAIProvider

        provider = OpenAIProvider(api_key="sk-test-key")

        mock_chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=" World"))]),
        ]

        with patch.object(provider, '_get_client') as mock_client:
            mock_client.return_value.chat.completions.create.return_value = iter(mock_chunks)

            chunks = list(provider.run_streaming("test"))

            assert len(chunks) > 0

    def test_should_track_token_usage(self):
        """Test that token usage is tracked."""
        from providers.openai_api import OpenAIProvider

        provider = OpenAIProvider(api_key="sk-test-key")

        with patch.object(provider, '_get_client') as mock_client:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
            mock_response.usage = MagicMock(total_tokens=150)
            mock_client.return_value.chat.completions.create.return_value = mock_response

            result = provider.run("test")

            assert result.tokens_used == 150

    def test_should_return_successful_result_with_content(self):
        """Test that successful responses return content."""
        from providers.openai_api import OpenAIProvider

        provider = OpenAIProvider(api_key="sk-test-key")

        with patch.object(provider, '_get_client') as mock_client:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Hello World"))]
            mock_response.usage = MagicMock(total_tokens=10)
            mock_client.return_value.chat.completions.create.return_value = mock_response

            result = provider.run("test prompt")

            assert result.success is True
            assert result.output == "Hello World"

    def test_should_handle_empty_prompt(self):
        """Test handling empty prompt."""
        from providers.openai_api import OpenAIProvider

        provider = OpenAIProvider(api_key="sk-test-key")

        result = provider.run("")

        assert result.success is False
        assert "empty" in result.error.lower()

    def test_should_override_model_in_run(self):
        """Test overriding model in run() call."""
        from providers.openai_api import OpenAIProvider

        provider = OpenAIProvider(api_key="sk-test-key", default_model="gpt-4o")

        with patch.object(provider, '_get_client') as mock_client:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
            mock_response.usage = MagicMock(total_tokens=50)
            mock_client.return_value.chat.completions.create.return_value = mock_response

            provider.run("test", model="gpt-4o-mini")

            call_args = mock_client.return_value.chat.completions.create.call_args
            assert call_args.kwargs.get('model') == "gpt-4o-mini"

    def test_should_have_default_model_marked(self):
        """Test that one model is marked as default."""
        from providers.openai_api import OpenAIProvider

        provider = OpenAIProvider(api_key="sk-test-key")
        models = provider.get_available_models()

        default_models = [m for m in models if m.is_default]
        assert len(default_models) == 1
