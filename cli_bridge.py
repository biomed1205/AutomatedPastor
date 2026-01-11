"""CLI bridge module for executing Claude Code CLI commands.

Provides subprocess execution with streaming output, timeout handling,
and proper process management.
"""
import subprocess
import time
import json
import shlex
import signal
import os


class TimeoutError(Exception):
    """Raised when a command exceeds the timeout limit."""

    def __init__(self, message, partial_output=''):
        super().__init__(message)
        self.partial_output = partial_output


class CommandNotFoundError(Exception):
    """Raised when the specified command is not found."""
    pass


class InvalidPromptError(Exception):
    """Raised when the prompt is invalid (empty or None)."""
    pass


class CLIBridgeResult:
    """Result of a CLI bridge command execution."""

    def __init__(self, output='', stderr='', exit_code=0, duration=0.0, process_cleaned=True):
        self.output = output
        self.stderr = stderr
        self.exit_code = exit_code
        self.duration = duration
        self.process_cleaned = process_cleaned

    @property
    def success(self):
        """Return True if command succeeded (exit code 0)."""
        return self.exit_code == 0

    def to_dict(self):
        """Convert result to dictionary."""
        return {
            'output': self.output,
            'stderr': self.stderr,
            'exit_code': self.exit_code,
            'success': self.success,
            'duration': self.duration,
            'process_cleaned': self.process_cleaned
        }

    def to_json(self):
        """Convert result to JSON string."""
        return json.dumps(self.to_dict())


class CLIBridge:
    """Bridge for executing CLI commands via subprocess."""

    def __init__(self, command='claude', timeout=None):
        """Initialize CLI bridge.

        Args:
            command: Command to execute (default: 'claude')
            timeout: Timeout in seconds (default: 300)
        """
        self.command = command
        self.timeout = timeout if timeout is not None else 300
        self._processes = {}

    def run(self, prompt):
        """Execute command and return result.

        Args:
            prompt: Prompt/arguments to pass to the command.

        Returns:
            CLIBridgeResult with output, stderr, exit_code, etc.

        Raises:
            InvalidPromptError: If prompt is None or empty.
            CommandNotFoundError: If command is not found.
            TimeoutError: If command exceeds timeout.
        """
        if prompt is None or prompt == '':
            raise InvalidPromptError('Prompt cannot be None or empty')

        start_time = time.time()
        cmd = [self.command] + shlex.split(prompt)

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
                duration = time.time() - start_time

                return CLIBridgeResult(
                    output=stdout,
                    stderr=stderr,
                    exit_code=process.returncode,
                    duration=duration,
                    process_cleaned=True
                )

            except subprocess.TimeoutExpired:
                # Capture partial output before killing
                process.kill()
                stdout, stderr = process.communicate()
                duration = time.time() - start_time

                raise TimeoutError(
                    f'Command timed out after {self.timeout} seconds',
                    partial_output=stdout or ''
                )

        except FileNotFoundError:
            raise CommandNotFoundError(f'Command not found: {self.command}')

    def run_streaming(self, prompt):
        """Execute command and yield output as it becomes available.

        Args:
            prompt: Prompt/arguments to pass to the command.

        Yields:
            Output chunks as they become available.
        """
        if prompt is None or prompt == '':
            raise InvalidPromptError('Prompt cannot be None or empty')

        cmd = [self.command] + shlex.split(prompt)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        try:
            for line in process.stdout:
                yield line
        finally:
            process.wait()

    def run_async(self, prompt):
        """Start command asynchronously and return process handle.

        Args:
            prompt: Prompt/arguments to pass to the command.

        Returns:
            Process handle (Popen object).
        """
        if prompt is None or prompt == '':
            raise InvalidPromptError('Prompt cannot be None or empty')

        cmd = [self.command] + shlex.split(prompt)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        self._processes[id(process)] = process
        return process

    def cancel(self, process_handle):
        """Cancel a running process.

        Args:
            process_handle: Process handle from run_async().

        Returns:
            Any output captured before termination.
        """
        output = ''

        if process_handle.poll() is None:
            # Try graceful termination first
            process_handle.terminate()

            try:
                stdout, _ = process_handle.communicate(timeout=2)
                output = stdout or ''
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate
                process_handle.kill()
                process_handle.communicate()

        # Cleanup from tracking dict
        if id(process_handle) in self._processes:
            del self._processes[id(process_handle)]

        return output

    def is_running(self, process_handle):
        """Check if a process is still running.

        Args:
            process_handle: Process handle from run_async().

        Returns:
            True if process is running, False otherwise.
        """
        return process_handle.poll() is None

    def format_prompt(self, prompt):
        """Format a prompt for Claude CLI execution.

        Args:
            prompt: The prompt text.

        Returns:
            Formatted prompt string.
        """
        # Return the prompt as-is for now, escaping handled by shlex
        return prompt
