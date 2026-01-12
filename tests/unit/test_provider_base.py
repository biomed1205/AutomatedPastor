"""Tests for AI provider base classes.

TDD: These tests are written FIRST before implementation.
"""
import pytest
from typing import Generator, List, Optional


class TestProviderResult:
    """Test the ProviderResult dataclass."""

    def test_should_create_successful_result(self):
        """Test creating a successful provider result."""
        from providers.base import ProviderResult

        result = ProviderResult(
            output="Hello, world!",
            provider_id="test_provider",
            model_id="test-model",
            success=True
        )

        assert result.output == "Hello, world!"
        assert result.provider_id == "test_provider"
        assert result.model_id == "test-model"
        assert result.success is True
        assert result.error is None
        assert result.duration == 0.0

    def test_should_create_failed_result_with_error(self):
        """Test creating a failed provider result."""
        from providers.base import ProviderResult

        result = ProviderResult(
            output="",
            provider_id="test_provider",
            model_id="test-model",
            success=False,
            error="Connection timeout"
        )

        assert result.success is False
        assert result.error == "Connection timeout"

    def test_should_convert_to_dict(self):
        """Test converting result to dictionary."""
        from providers.base import ProviderResult

        result = ProviderResult(
            output="Test output",
            provider_id="claude_api",
            model_id="claude-3",
            success=True,
            duration=1.5,
            tokens_used=100
        )

        d = result.to_dict()
        assert d['output'] == "Test output"
        assert d['provider_id'] == "claude_api"
        assert d['success'] is True
        assert d['duration'] == 1.5
        assert d['tokens_used'] == 100


class TestProviderModel:
    """Test the ProviderModel dataclass."""

    def test_should_create_model_info(self):
        """Test creating model information."""
        from providers.base import ProviderModel

        model = ProviderModel(
            id="gpt-4o",
            name="GPT-4o",
            context_window=128000,
            supports_streaming=True,
            is_default=True
        )

        assert model.id == "gpt-4o"
        assert model.name == "GPT-4o"
        assert model.context_window == 128000
        assert model.supports_streaming is True
        assert model.is_default is True

    def test_should_have_default_values(self):
        """Test default values for ProviderModel."""
        from providers.base import ProviderModel

        model = ProviderModel(
            id="test",
            name="Test Model",
            context_window=4096
        )

        assert model.supports_streaming is True
        assert model.is_default is False


class TestProviderStatus:
    """Test the ProviderStatus enum."""

    def test_should_have_expected_statuses(self):
        """Test that all expected statuses exist."""
        from providers.base import ProviderStatus

        assert ProviderStatus.AVAILABLE.value == "available"
        assert ProviderStatus.UNAVAILABLE.value == "unavailable"
        assert ProviderStatus.DISABLED.value == "disabled"
        assert ProviderStatus.ERROR.value == "error"


class TestAIProviderAbstract:
    """Test the AIProvider abstract base class."""

    def test_should_not_instantiate_directly(self):
        """Test that AIProvider cannot be instantiated directly."""
        from providers.base import AIProvider

        with pytest.raises(TypeError):
            AIProvider()

    def test_should_instantiate_concrete_implementation(self):
        """Test that concrete implementations can be instantiated."""
        from providers.base import AIProvider, ProviderResult, ProviderModel

        class ConcreteProvider(AIProvider):
            provider_id = "test"
            display_name = "Test Provider"

            def is_available(self) -> bool:
                return True

            def run(self, prompt: str, model: Optional[str] = None) -> ProviderResult:
                return ProviderResult(
                    output=f"Response to: {prompt}",
                    provider_id=self.provider_id,
                    model_id=model or "default",
                    success=True
                )

            def run_streaming(self, prompt: str, model: Optional[str] = None):
                yield "chunk1"
                yield "chunk2"

            def get_available_models(self) -> List[ProviderModel]:
                return [ProviderModel(id="default", name="Default", context_window=4096)]

        provider = ConcreteProvider()
        assert provider.provider_id == "test"
        assert provider.display_name == "Test Provider"

    def test_should_run_prompt(self):
        """Test running a prompt through concrete provider."""
        from providers.base import AIProvider, ProviderResult, ProviderModel

        class ConcreteProvider(AIProvider):
            provider_id = "test"
            display_name = "Test"

            def is_available(self) -> bool:
                return True

            def run(self, prompt: str, model: Optional[str] = None) -> ProviderResult:
                return ProviderResult(
                    output=f"Echo: {prompt}",
                    provider_id=self.provider_id,
                    model_id=model or "default",
                    success=True
                )

            def run_streaming(self, prompt: str, model: Optional[str] = None):
                yield prompt

            def get_available_models(self):
                return []

        provider = ConcreteProvider()
        result = provider.run("Hello")

        assert result.success is True
        assert result.output == "Echo: Hello"
        assert result.provider_id == "test"

    def test_should_validate_config_requires_api_key(self):
        """Test config validation for API key requirement."""
        from providers.base import AIProvider, ProviderResult, ProviderModel

        class APIProvider(AIProvider):
            provider_id = "api_test"
            display_name = "API Test"

            def is_available(self) -> bool:
                return self.api_key is not None

            def run(self, prompt, model=None):
                return ProviderResult("", self.provider_id, "", True)

            def run_streaming(self, prompt, model=None):
                yield ""

            def get_available_models(self):
                return []

        # Without API key
        provider = APIProvider()
        is_valid, message = provider.validate_config()
        assert is_valid is False
        assert "API key" in message

        # With API key
        provider = APIProvider(api_key="test-key")
        is_valid, message = provider.validate_config()
        assert is_valid is True

    def test_should_not_require_api_key_for_cli(self):
        """Test that CLI providers don't require API key."""
        from providers.base import AIProvider, ProviderResult, ProviderModel

        class CLIProvider(AIProvider):
            provider_id = "cli_test"
            display_name = "CLI Test"

            def _requires_api_key(self) -> bool:
                return False

            def is_available(self) -> bool:
                return True

            def run(self, prompt, model=None):
                return ProviderResult("", self.provider_id, "", True)

            def run_streaming(self, prompt, model=None):
                yield ""

            def get_available_models(self):
                return []

        provider = CLIProvider()  # No API key
        is_valid, message = provider.validate_config()
        assert is_valid is True

    def test_should_get_status(self):
        """Test getting provider status."""
        from providers.base import AIProvider, ProviderResult, ProviderStatus

        class TestProvider(AIProvider):
            provider_id = "status_test"
            display_name = "Status Test"
            _available = True

            def is_available(self) -> bool:
                return self._available

            def run(self, prompt, model=None):
                return ProviderResult("", self.provider_id, "", True)

            def run_streaming(self, prompt, model=None):
                yield ""

            def get_available_models(self):
                return []

            def _requires_api_key(self):
                return False

        provider = TestProvider()
        assert provider.get_status() == ProviderStatus.AVAILABLE

        provider._available = False
        assert provider.get_status() == ProviderStatus.UNAVAILABLE
