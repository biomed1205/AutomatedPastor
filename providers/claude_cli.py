"""Claude CLI provider implementation.

Wraps the existing CLIBridge to implement the AIProvider interface,
maintaining full backward compatibility with the original implementation.
"""
import shutil
import subprocess
import time
import shlex
from typing import Generator, List, Optional

from providers.base import AIProvider, ProviderResult, ProviderModel


class ClaudeCLIProvider(AIProvider):
    """Claude CLI provider that wraps the Claude CLI command.

    Implements the AIProvider interface while maintaining backward
    compatibility with the original CLIBridge class.
    """

    provider_id = "claude_cli"
    display_name = "Claude CLI"
    color_primary = "#D97706"  # Amber
    color_bg = "#FEF3C7"  # Light amber

    def __init__(
        self,
        command: str = 'claude',
        timeout: Optional[int] = None,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """Initialize the Claude CLI provider.

        Args:
            command: Command to execute (default: 'claude')
            timeout: Timeout in seconds (default: 300)
            api_key: Not used for CLI provider, included for interface compatibility
            **kwargs: Additional configuration options
        """
        super().__init__(api_key=api_key, **kwargs)
        self.command = command
        self.timeout = timeout if timeout is not None else 300
        self._processes = {}

    def _requires_api_key(self) -> bool:
        """CLI provider does not require an API key.

        Returns:
            False - CLI uses system authentication
        """
        return False

    def is_available(self) -> bool:
        """Check if the Claude CLI command is available.

        Returns:
            True if the command exists in PATH
        """
        return shutil.which(self.command) is not None

    def run(self, prompt: str, model: Optional[str] = None) -> ProviderResult:
        """Execute a prompt via the CLI and return the result.

        Args:
            prompt: The prompt/arguments to pass to the command
            model: Optional model parameter (not used for CLI)

        Returns:
            ProviderResult with output and metadata
        """
        if prompt is None or prompt == '':
            return ProviderResult(
                output="",
                provider_id=self.provider_id,
                model_id=model or "cli-default",
                success=False,
                error="Prompt cannot be None or empty"
            )

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

                success = process.returncode == 0

                return ProviderResult(
                    output=stdout,
                    provider_id=self.provider_id,
                    model_id=model or "cli-default",
                    success=success,
                    error=stderr if not success else None,
                    duration=duration
                )

            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                duration = time.time() - start_time

                return ProviderResult(
                    output=stdout or "",
                    provider_id=self.provider_id,
                    model_id=model or "cli-default",
                    success=False,
                    error=f"Command timed out after {self.timeout} seconds",
                    duration=duration
                )

        except FileNotFoundError:
            duration = time.time() - start_time
            return ProviderResult(
                output="",
                provider_id=self.provider_id,
                model_id=model or "cli-default",
                success=False,
                error=f"Command not found: {self.command}",
                duration=duration
            )

    def run_streaming(self, prompt: str, model: Optional[str] = None) -> Generator[str, None, None]:
        """Execute a prompt and stream the response.

        Args:
            prompt: The prompt/arguments to pass to the command
            model: Optional model parameter (not used for CLI)

        Yields:
            Output chunks as they become available
        """
        if prompt is None or prompt == '':
            yield ""
            return

        cmd = [self.command] + shlex.split(prompt)

        try:
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
        except FileNotFoundError:
            yield ""

    def get_available_models(self) -> List[ProviderModel]:
        """Get available models for CLI.

        Returns:
            List with a single model representing CLI mode
        """
        return [
            ProviderModel(
                id="cli-default",
                name="Claude CLI",
                context_window=200000,  # Claude's context window
                supports_streaming=True,
                is_default=True,
                description="Claude via CLI"
            )
        ]

    # Backward compatibility methods from CLIBridge

    def run_async(self, prompt: str):
        """Start command asynchronously and return process handle.

        Args:
            prompt: Prompt/arguments to pass to the command.

        Returns:
            Process handle (Popen object).
        """
        if prompt is None or prompt == '':
            raise ValueError('Prompt cannot be None or empty')

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
            process_handle.terminate()

            try:
                stdout, _ = process_handle.communicate(timeout=2)
                output = stdout or ''
            except subprocess.TimeoutExpired:
                process_handle.kill()
                process_handle.communicate()

        if id(process_handle) in self._processes:
            del self._processes[id(process_handle)]

        return output

    def is_running(self, process_handle) -> bool:
        """Check if a process is still running.

        Args:
            process_handle: Process handle from run_async().

        Returns:
            True if process is running, False otherwise.
        """
        return process_handle.poll() is None

    def format_prompt(self, prompt: str) -> str:
        """Format a prompt for Claude CLI execution.

        Args:
            prompt: The prompt text.

        Returns:
            Formatted prompt string.
        """
        return prompt
