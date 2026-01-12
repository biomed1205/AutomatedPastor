"""Tests for Claude CLI provider.

TDD: These tests are written FIRST before implementation.
"""
import pytest
import shutil
from typing import Optional


class TestClaudeCLIProvider:
    """Test the Claude CLI provider implementation."""

    def test_should_extend_ai_provider(self):
        """Test that ClaudeCLIProvider extends AIProvider."""
        from providers.claude_cli import ClaudeCLIProvider
        from providers.base import AIProvider

        provider = ClaudeCLIProvider()
        assert isinstance(provider, AIProvider)

    def test_should_have_correct_provider_id(self):
        """Test provider ID is 'claude_cli'."""
        from providers.claude_cli import ClaudeCLIProvider

        provider = ClaudeCLIProvider()
        assert provider.provider_id == "claude_cli"
        assert provider.display_name == "Claude CLI"

    def test_should_have_correct_colors(self):
        """Test provider has amber colors."""
        from providers.claude_cli import ClaudeCLIProvider

        provider = ClaudeCLIProvider()
        assert provider.color_primary == "#D97706"
        assert provider.color_bg == "#FEF3C7"

    def test_should_not_require_api_key(self):
        """Test that CLI provider doesn't require API key."""
        from providers.claude_cli import ClaudeCLIProvider

        provider = ClaudeCLIProvider()
        is_valid, _ = provider.validate_config()
        assert is_valid is True

    def test_should_check_cli_availability(self):
        """Test checking if Claude CLI is available."""
        from providers.claude_cli import ClaudeCLIProvider

        provider = ClaudeCLIProvider()
        # Will be True if 'claude' command exists, False otherwise
        available = provider.is_available()

        # Check matches actual system state
        claude_exists = shutil.which('claude') is not None
        assert available == claude_exists

    def test_should_return_provider_result_from_run(self):
        """Test that run() returns ProviderResult."""
        from providers.claude_cli import ClaudeCLIProvider
        from providers.base import ProviderResult

        # Use echo command for testing
        provider = ClaudeCLIProvider(command='echo')
        result = provider.run("test message")

        assert isinstance(result, ProviderResult)
        assert result.provider_id == "claude_cli"

    def test_should_handle_successful_command(self):
        """Test handling successful command execution."""
        from providers.claude_cli import ClaudeCLIProvider

        provider = ClaudeCLIProvider(command='echo')
        result = provider.run("hello world")

        assert result.success is True
        assert "hello world" in result.output
        assert result.error is None or result.error == ""

    def test_should_handle_command_not_found(self):
        """Test handling non-existent command."""
        from providers.claude_cli import ClaudeCLIProvider

        provider = ClaudeCLIProvider(command='nonexistent_command_12345')
        result = provider.run("test")

        assert result.success is False
        assert result.error is not None

    def test_should_track_duration(self):
        """Test that execution duration is tracked."""
        from providers.claude_cli import ClaudeCLIProvider

        provider = ClaudeCLIProvider(command='echo')
        result = provider.run("test")

        assert result.duration > 0

    def test_should_get_available_models(self):
        """Test getting available models for CLI."""
        from providers.claude_cli import ClaudeCLIProvider
        from providers.base import ProviderModel

        provider = ClaudeCLIProvider()
        models = provider.get_available_models()

        assert len(models) >= 1
        assert all(isinstance(m, ProviderModel) for m in models)
        # CLI should have at least one "model" representing CLI mode
        assert any(m.id == "cli-default" for m in models)

    def test_should_support_streaming(self):
        """Test streaming output."""
        from providers.claude_cli import ClaudeCLIProvider

        provider = ClaudeCLIProvider(command='echo')
        chunks = list(provider.run_streaming("test line"))

        # Should yield at least one chunk
        assert len(chunks) > 0
        # Combined output should contain the input
        combined = "".join(chunks)
        assert "test" in combined

    def test_should_maintain_backward_compatibility(self):
        """Test backward compatibility with old CLIBridge interface."""
        from providers.claude_cli import ClaudeCLIProvider

        # Old interface used CLIBridgeResult
        provider = ClaudeCLIProvider(command='echo')

        # These should still work (backward compat)
        result = provider.run("test")
        assert hasattr(result, 'output')
        assert hasattr(result, 'success')
        assert hasattr(result, 'duration')

    def test_should_handle_timeout(self):
        """Test timeout handling."""
        from providers.claude_cli import ClaudeCLIProvider

        # Use sleep command with short timeout
        provider = ClaudeCLIProvider(command='sleep', timeout=1)
        result = provider.run("10")  # Try to sleep 10 seconds

        # Should fail due to timeout
        assert result.success is False

    def test_should_allow_custom_command(self):
        """Test using custom command."""
        from providers.claude_cli import ClaudeCLIProvider

        provider = ClaudeCLIProvider(command='printf')
        result = provider.run("formatted output")

        assert result.success is True


class TestCLIBridgeBackwardCompat:
    """Test backward compatibility with original CLIBridge."""

    def test_should_import_cli_bridge(self):
        """Test that original CLIBridge import still works."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        assert bridge is not None

    def test_should_run_with_old_interface(self):
        """Test running with old interface."""
        from cli_bridge import CLIBridge, CLIBridgeResult

        bridge = CLIBridge(command='echo')
        result = bridge.run("test")

        # Old interface returned CLIBridgeResult
        assert hasattr(result, 'output')
        assert hasattr(result, 'stderr')
        assert hasattr(result, 'exit_code')
        assert hasattr(result, 'success')
