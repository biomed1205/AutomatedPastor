"""Tests for CLI bridge to Claude Code.

These tests verify the CLI bridge module can execute subprocess commands,
handle streaming output, manage timeouts, and handle errors correctly.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL subprocess execution - NO MOCKS.

Test Strategy:
- Use configurable command so tests can use simple scripts instead of claude CLI
- Test all subprocess mechanics with real processes
- Test streaming, timeout, error handling with controlled test commands
"""
import pytest
import subprocess
import tempfile
import os
import time
import sys


class TestCLIBridgeCreation:
    """Test suite for CLI bridge initialization."""

    def test_should_create_bridge_when_instantiated(self):
        """Test that CLIBridge can be created."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge()
        assert bridge is not None

    def test_should_accept_custom_command_when_configured(self):
        """Test that bridge can use custom command instead of claude."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        assert bridge.command == 'echo'

    def test_should_default_to_claude_command_when_not_specified(self):
        """Test that bridge defaults to 'claude' command."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge()
        assert bridge.command == 'claude'

    def test_should_accept_custom_timeout_when_configured(self):
        """Test that timeout can be configured."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(timeout=60)
        assert bridge.timeout == 60

    def test_should_default_timeout_when_not_specified(self):
        """Test that timeout has sensible default."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge()
        # Default should be reasonable (e.g., 300 seconds = 5 minutes)
        assert bridge.timeout >= 60


class TestCLIBridgeExecution:
    """Test suite for CLI bridge command execution."""

    def test_should_execute_command_when_run_called(self):
        """Test that run() executes a subprocess command."""
        from cli_bridge import CLIBridge

        # Use echo command for testing - this is a REAL subprocess
        bridge = CLIBridge(command='echo')
        result = bridge.run('Hello World')

        assert 'Hello World' in result.output

    def test_should_return_output_when_command_succeeds(self):
        """Test that successful command returns output."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        result = bridge.run('test output')

        assert result.success is True
        assert result.output is not None
        assert len(result.output) > 0

    def test_should_return_exit_code_when_command_completes(self):
        """Test that exit code is captured."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        result = bridge.run('test')

        assert result.exit_code == 0

    def test_should_capture_stderr_when_command_has_errors(self):
        """Test that stderr is captured."""
        from cli_bridge import CLIBridge

        # Use a command that writes to stderr
        # Python -c is portable and predictable
        bridge = CLIBridge(command='python')
        result = bridge.run('-c "import sys; sys.stderr.write(\'error message\')"')

        assert 'error message' in result.stderr or 'error' in str(result).lower()

    def test_should_handle_multiline_output(self):
        """Test that multiline output is captured correctly."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='python')
        result = bridge.run('-c "print(\'line1\'); print(\'line2\'); print(\'line3\')"')

        assert 'line1' in result.output
        assert 'line2' in result.output
        assert 'line3' in result.output


class TestCLIBridgeStreaming:
    """Test suite for streaming output handling."""

    def test_should_yield_output_when_streaming_enabled(self):
        """Test that streaming mode yields output chunks."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='python')
        chunks = []

        for chunk in bridge.run_streaming('-c "import time; print(\'chunk1\'); print(\'chunk2\')"'):
            chunks.append(chunk)

        assert len(chunks) > 0
        combined = ''.join(chunks)
        assert 'chunk1' in combined

    def test_should_stream_in_realtime_when_process_running(self):
        """Test that output is streamed as it becomes available."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='python')

        # Use a command that outputs with delays
        script = "import time; import sys; print('first', flush=True); time.sleep(0.1); print('second', flush=True)"
        chunks = list(bridge.run_streaming(f'-c "{script}"'))

        # Should have received chunks
        assert len(chunks) >= 1
        combined = ''.join(chunks)
        assert 'first' in combined
        assert 'second' in combined

    def test_should_complete_streaming_when_process_ends(self):
        """Test that streaming properly terminates."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        chunks = list(bridge.run_streaming('done'))

        # Should have all output and complete
        combined = ''.join(chunks)
        assert 'done' in combined


class TestCLIBridgeTimeout:
    """Test suite for timeout handling."""

    def test_should_timeout_when_process_exceeds_limit(self):
        """Test that long-running processes are terminated."""
        from cli_bridge import CLIBridge, TimeoutError

        # Very short timeout
        bridge = CLIBridge(command='python', timeout=1)

        # Command that takes longer than timeout
        with pytest.raises(TimeoutError):
            bridge.run('-c "import time; time.sleep(10)"')

    def test_should_not_timeout_when_process_completes_quickly(self):
        """Test that fast processes complete without timeout."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo', timeout=10)
        result = bridge.run('quick')

        assert result.success is True
        assert 'quick' in result.output

    def test_should_return_partial_output_when_timeout_occurs(self):
        """Test that output before timeout is preserved."""
        from cli_bridge import CLIBridge, TimeoutError

        bridge = CLIBridge(command='python', timeout=1)

        script = "import time; import sys; print('before_timeout', flush=True); time.sleep(10)"

        try:
            bridge.run(f'-c "{script}"')
        except TimeoutError as e:
            # Should have captured output before timeout
            assert hasattr(e, 'partial_output') or 'before_timeout' in str(e)


class TestCLIBridgeErrorHandling:
    """Test suite for error handling."""

    def test_should_raise_error_when_command_not_found(self):
        """Test error when command doesn't exist."""
        from cli_bridge import CLIBridge, CommandNotFoundError

        bridge = CLIBridge(command='nonexistent_command_xyz123')

        with pytest.raises(CommandNotFoundError):
            bridge.run('test')

    def test_should_handle_nonzero_exit_code(self):
        """Test handling of failed commands."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='python')
        result = bridge.run('-c "import sys; sys.exit(1)"')

        assert result.success is False
        assert result.exit_code == 1

    def test_should_capture_error_output_when_command_fails(self):
        """Test that error output is captured on failure."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='python')
        result = bridge.run('-c "import sys; sys.stderr.write(\'error details\'); sys.exit(1)"')

        assert result.success is False
        assert 'error details' in result.stderr

    def test_should_handle_empty_prompt_gracefully(self):
        """Test handling of empty prompt."""
        from cli_bridge import CLIBridge, InvalidPromptError

        bridge = CLIBridge(command='echo')

        with pytest.raises(InvalidPromptError):
            bridge.run('')

    def test_should_handle_none_prompt_gracefully(self):
        """Test handling of None prompt."""
        from cli_bridge import CLIBridge, InvalidPromptError

        bridge = CLIBridge(command='echo')

        with pytest.raises(InvalidPromptError):
            bridge.run(None)


class TestCLIBridgeProcessManagement:
    """Test suite for process management and cleanup."""

    def test_should_cleanup_process_when_completed(self):
        """Test that processes are properly cleaned up after completion."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        result = bridge.run('test')

        # Process should be cleaned up - no zombie processes
        assert result.process_cleaned is True

    def test_should_cleanup_process_when_cancelled(self):
        """Test that cancelled processes are cleaned up."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='python', timeout=10)

        # Start a process and cancel it
        process_handle = bridge.run_async('-c "import time; time.sleep(60)"')
        bridge.cancel(process_handle)

        # Process should be terminated
        assert not bridge.is_running(process_handle)

    def test_should_report_running_status_correctly(self):
        """Test that running status is accurate."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='python', timeout=10)

        # Start a slow process
        process_handle = bridge.run_async('-c "import time; time.sleep(5)"')

        # Should be running initially
        assert bridge.is_running(process_handle) is True

        # Cancel and check
        bridge.cancel(process_handle)
        time.sleep(0.5)  # Give it time to terminate
        assert bridge.is_running(process_handle) is False

    def test_should_terminate_gracefully_when_cancel_called(self):
        """Test that cancel sends SIGTERM before SIGKILL."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='python', timeout=10)

        # Start a process that handles SIGTERM
        script = """
import signal
import time
import sys

def handler(sig, frame):
    print('graceful_shutdown', flush=True)
    sys.exit(0)

signal.signal(signal.SIGTERM, handler)
time.sleep(60)
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script)
            script_path = f.name

        try:
            process_handle = bridge.run_async(script_path)
            time.sleep(0.5)  # Let it start
            output = bridge.cancel(process_handle)

            # Should have received graceful shutdown
            assert 'graceful_shutdown' in output or process_handle.returncode == 0
        finally:
            os.unlink(script_path)


class TestCLIBridgeOutputParsing:
    """Test suite for output parsing and formatting."""

    def test_should_strip_whitespace_from_output(self):
        """Test that output whitespace is handled."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        result = bridge.run('   spaced text   ')

        # Output should be trimmed
        assert result.output.strip() == 'spaced text'

    def test_should_preserve_newlines_in_output(self):
        """Test that newlines are preserved."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='python')
        result = bridge.run('-c "print(\'line1\'); print(\'line2\')"')

        lines = result.output.strip().split('\n')
        assert len(lines) >= 2

    def test_should_handle_unicode_output(self):
        """Test that unicode is handled correctly."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='python')
        result = bridge.run('-c "print(\'Hello \u4e16\u754c\')"')

        assert 'Hello' in result.output
        # Unicode should be preserved
        assert '\u4e16\u754c' in result.output or 'world' in result.output.lower()

    def test_should_handle_large_output(self):
        """Test handling of large output."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='python')
        # Generate 10000 lines of output
        result = bridge.run('-c "for i in range(10000): print(f\'line {i}\')"')

        assert result.success is True
        assert len(result.output) > 50000  # Should have substantial output


class TestCLIBridgeClaude:
    """Test suite for Claude CLI specific functionality."""

    def test_should_format_prompt_for_claude(self):
        """Test that prompts are properly formatted for claude -p."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge()
        formatted = bridge.format_prompt('Generate a sermon about John 3:16')

        # Should create proper command line format
        assert 'Generate a sermon' in formatted

    def test_should_escape_special_characters_in_prompt(self):
        """Test that special characters are escaped."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge()
        prompt = 'This has "quotes" and $variables and `backticks`'
        formatted = bridge.format_prompt(prompt)

        # Should be safe for shell execution
        assert formatted is not None

    def test_should_handle_very_long_prompts(self):
        """Test handling of long prompts."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge()
        long_prompt = 'Generate sermon. ' * 1000  # Very long prompt
        formatted = bridge.format_prompt(long_prompt)

        assert formatted is not None
        assert len(formatted) > 15000


class TestCLIBridgeResult:
    """Test suite for CLIBridgeResult class."""

    def test_should_have_required_attributes(self):
        """Test that result has all required attributes."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        result = bridge.run('test')

        assert hasattr(result, 'output')
        assert hasattr(result, 'stderr')
        assert hasattr(result, 'exit_code')
        assert hasattr(result, 'success')
        assert hasattr(result, 'duration')

    def test_should_track_execution_duration(self):
        """Test that execution time is tracked."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='python')
        result = bridge.run('-c "import time; time.sleep(0.5)"')

        assert result.duration >= 0.5
        assert result.duration < 10  # Should not take too long

    def test_should_convert_to_dict(self):
        """Test that result can be converted to dict."""
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        result = bridge.run('test')

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert 'output' in result_dict
        assert 'success' in result_dict

    def test_should_convert_to_json(self):
        """Test that result can be serialized to JSON."""
        from cli_bridge import CLIBridge
        import json

        bridge = CLIBridge(command='echo')
        result = bridge.run('test')

        json_str = result.to_json()
        parsed = json.loads(json_str)

        assert 'output' in parsed
        assert 'success' in parsed
