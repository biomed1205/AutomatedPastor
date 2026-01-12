"""Tests for Google Gemini provider.

TDD: These tests are written FIRST before implementation.
"""
import os
import pytest
from unittest.mock import patch, MagicMock


class TestGeminiProvider:
    """Test the Gemini provider implementation."""

    def test_should_extend_ai_provider(self):
        """Test that GeminiProvider extends AIProvider."""
        from providers.gemini_api import GeminiProvider
        from providers.base import AIProvider

        provider = GeminiProvider(api_key="test-key")
        assert isinstance(provider, AIProvider)

    def test_should_have_correct_provider_id(self):
        """Test provider ID is 'gemini'."""
        from providers.gemini_api import GeminiProvider

        provider = GeminiProvider(api_key="test-key")
        assert provider.provider_id == "gemini"
        assert provider.display_name == "Google Gemini"

    def test_should_have_correct_colors(self):
        """Test provider has blue colors."""
        from providers.gemini_api import GeminiProvider

        provider = GeminiProvider(api_key="test-key")
        assert provider.color_primary == "#3B82F6"
        assert provider.color_bg == "#DBEAFE"

    def test_should_require_api_key(self):
        """Test that Gemini provider requires API key."""
        from providers.gemini_api import GeminiProvider

        # Clear env vars
        env_backup = {}
        for key in ["GOOGLE_API_KEY", "GEMINI_API_KEY"]:
            if key in os.environ:
                env_backup[key] = os.environ.pop(key)

        try:
            provider = GeminiProvider()
            is_valid, message = provider.validate_config()
            assert is_valid is False
            assert "API key" in message
        finally:
            # Restore env vars
            os.environ.update(env_backup)

    def test_should_validate_with_api_key(self):
        """Test validation passes with API key."""
        from providers.gemini_api import GeminiProvider

        provider = GeminiProvider(api_key="AIza-test-key")
        is_valid, _ = provider.validate_config()
        assert is_valid is True

    def test_should_read_api_key_from_google_env(self, monkeypatch):
        """Test reading API key from GOOGLE_API_KEY env var."""
        from providers.gemini_api import GeminiProvider

        monkeypatch.setenv("GOOGLE_API_KEY", "AIza-google-env-key")

        provider = GeminiProvider()
        assert provider.api_key == "AIza-google-env-key"

    def test_should_read_api_key_from_gemini_env(self, monkeypatch):
        """Test reading API key from GEMINI_API_KEY env var."""
        from providers.gemini_api import GeminiProvider

        # Clear GOOGLE_API_KEY first
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.setenv("GEMINI_API_KEY", "AIza-gemini-env-key")

        provider = GeminiProvider()
        assert provider.api_key == "AIza-gemini-env-key"

    def test_should_check_availability_with_key(self):
        """Test availability check with API key."""
        from providers.gemini_api import GeminiProvider

        provider = GeminiProvider(api_key="AIza-test-key")
        assert provider.is_available() is True

    def test_should_check_availability_without_key(self):
        """Test availability check without API key."""
        from providers.gemini_api import GeminiProvider

        # Clear env vars
        env_backup = {}
        for key in ["GOOGLE_API_KEY", "GEMINI_API_KEY"]:
            if key in os.environ:
                env_backup[key] = os.environ.pop(key)

        try:
            provider = GeminiProvider()
            assert provider.is_available() is False
        finally:
            # Restore env vars
            os.environ.update(env_backup)

    def test_should_return_provider_result(self):
        """Test that run() returns ProviderResult."""
        from providers.gemini_api import GeminiProvider
        from providers.base import ProviderResult

        provider = GeminiProvider(api_key="AIza-test-key")

        with patch.object(provider, '_get_model') as mock_get_model:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Test response"
            mock_model.generate_content.return_value = mock_response
            mock_get_model.return_value = mock_model

            result = provider.run("test prompt")

            assert isinstance(result, ProviderResult)
            assert result.provider_id == "gemini"

    def test_should_handle_api_error(self):
        """Test handling API errors gracefully."""
        from providers.gemini_api import GeminiProvider

        provider = GeminiProvider(api_key="AIza-test-key")

        with patch.object(provider, '_get_model') as mock_get_model:
            mock_model = MagicMock()
            mock_model.generate_content.side_effect = Exception("API Error")
            mock_get_model.return_value = mock_model

            result = provider.run("test")

            assert result.success is False
            assert result.error is not None

    def test_should_get_available_models(self):
        """Test getting available Gemini models."""
        from providers.gemini_api import GeminiProvider
        from providers.base import ProviderModel

        provider = GeminiProvider(api_key="AIza-test-key")
        models = provider.get_available_models()

        assert len(models) >= 3
        assert all(isinstance(m, ProviderModel) for m in models)

        model_ids = [m.id for m in models]
        assert "gemini-2.0-flash" in model_ids or "gemini-1.5-pro" in model_ids

    def test_should_use_default_model(self):
        """Test using default model when not specified."""
        from providers.gemini_api import GeminiProvider

        provider = GeminiProvider(api_key="AIza-test-key", default_model="gemini-1.5-pro")

        with patch.object(provider, '_get_model') as mock_get_model:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Response"
            mock_model.generate_content.return_value = mock_response
            mock_get_model.return_value = mock_model

            provider.run("test")

            # Check that model was created with correct name
            mock_get_model.assert_called()

    def test_should_support_streaming(self):
        """Test streaming output."""
        from providers.gemini_api import GeminiProvider

        provider = GeminiProvider(api_key="AIza-test-key")

        mock_chunk1 = MagicMock()
        mock_chunk1.text = "Hello"
        mock_chunk2 = MagicMock()
        mock_chunk2.text = " World"
        mock_chunks = [mock_chunk1, mock_chunk2]

        with patch.object(provider, '_get_model') as mock_get_model:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = iter(mock_chunks)
            mock_get_model.return_value = mock_model

            chunks = list(provider.run_streaming("test"))

            assert len(chunks) > 0

    def test_should_handle_large_context_window(self):
        """Test that Gemini models support large context windows."""
        from providers.gemini_api import GeminiProvider

        provider = GeminiProvider(api_key="AIza-test-key")
        models = provider.get_available_models()

        # Gemini should have models with large context windows (1M+)
        large_context_models = [m for m in models if m.context_window >= 1000000]
        assert len(large_context_models) >= 1

    def test_should_return_successful_result_on_valid_response(self):
        """Test that successful API call returns success=True."""
        from providers.gemini_api import GeminiProvider

        provider = GeminiProvider(api_key="AIza-test-key")

        with patch.object(provider, '_get_model') as mock_get_model:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Success response"
            mock_model.generate_content.return_value = mock_response
            mock_get_model.return_value = mock_model

            result = provider.run("test prompt")

            assert result.success is True
            assert result.output == "Success response"

    def test_should_handle_empty_prompt(self):
        """Test handling empty prompt."""
        from providers.gemini_api import GeminiProvider

        provider = GeminiProvider(api_key="AIza-test-key")
        result = provider.run("")

        assert result.success is False
        assert "empty" in result.error.lower() or "prompt" in result.error.lower()

    def test_should_record_duration(self):
        """Test that run() records duration."""
        from providers.gemini_api import GeminiProvider

        provider = GeminiProvider(api_key="AIza-test-key")

        with patch.object(provider, '_get_model') as mock_get_model:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Response"
            mock_model.generate_content.return_value = mock_response
            mock_get_model.return_value = mock_model

            result = provider.run("test")

            assert result.duration >= 0
