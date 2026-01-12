"""Claude API provider implementation.

Provides direct API access to Anthropic's Claude models.
"""
import os
import time
from typing import Optional, List, Generator

from providers.base import AIProvider, ProviderResult, ProviderModel


class ClaudeAPIProviderError(Exception):
    """Raised when Claude API provider encounters an error."""
    pass


class ClaudeAPIProvider(AIProvider):
    """Claude API provider for direct Anthropic API calls.

    This provider uses the Anthropic Python SDK to make direct API calls.
    It's the preferred method for Docker containers and cloud deployments.
    """

    provider_id = "claude_api"
    display_name = "Claude API"

    # Amber colors (matching Claude CLI)
    color_primary = "#D97706"
    color_bg = "#FEF3C7"

    # Available Claude models
    AVAILABLE_MODELS = [
        ProviderModel(
            id="claude-sonnet-4-20250514",
            name="Claude Sonnet 4",
            context_window=200000,
            max_output_tokens=64000,
            supports_streaming=True,
            supports_vision=True,
            is_default=True,
            description="Best balance of speed and capability"
        ),
        ProviderModel(
            id="claude-3-5-sonnet-20241022",
            name="Claude 3.5 Sonnet",
            context_window=200000,
            max_output_tokens=8192,
            supports_streaming=True,
            supports_vision=True,
            is_default=False,
            description="Excellent balance of speed and capability"
        ),
        ProviderModel(
            id="claude-3-opus-20240229",
            name="Claude 3 Opus",
            context_window=200000,
            max_output_tokens=4096,
            supports_streaming=True,
            supports_vision=True,
            is_default=False,
            description="Most capable model for complex tasks"
        ),
        ProviderModel(
            id="claude-3-haiku-20240307",
            name="Claude 3 Haiku",
            context_window=200000,
            max_output_tokens=4096,
            supports_streaming=True,
            supports_vision=True,
            is_default=False,
            description="Fastest model for simple tasks"
        ),
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        max_tokens: int = 8192,
        timeout: int = 300,
        **kwargs
    ):
        """Initialize the Claude API provider.

        Args:
            api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var.
            default_model: Default model to use. If None, uses claude-sonnet-4-20250514.
            max_tokens: Maximum tokens for response (default: 8192).
            timeout: Request timeout in seconds (default: 300).
            **kwargs: Additional configuration options.
        """
        # Get API key from environment if not provided
        resolved_api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        super().__init__(api_key=resolved_api_key, **kwargs)

        self.default_model = default_model or "claude-sonnet-4-20250514"
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._client = None

    def _requires_api_key(self) -> bool:
        """Claude API requires an API key.

        Returns:
            True - API key is required for this provider.
        """
        return True

    def _get_client(self):
        """Get or create the Anthropic client.

        Returns:
            Anthropic client instance.

        Raises:
            ClaudeAPIProviderError: If API key is not set or anthropic package not installed.
        """
        if self._client is None:
            if not self.api_key:
                raise ClaudeAPIProviderError(
                    "ANTHROPIC_API_KEY environment variable not set. "
                    "Please set it to use Claude API."
                )
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ClaudeAPIProviderError(
                    "anthropic package not installed. Run: pip install anthropic"
                )
        return self._client

    def is_available(self) -> bool:
        """Check if the Claude API is available.

        Returns:
            True if API key is configured, False otherwise.
        """
        return self.api_key is not None and len(self.api_key) > 0

    def run(self, prompt: str, model: Optional[str] = None) -> ProviderResult:
        """Execute a prompt via the Anthropic API.

        Args:
            prompt: The prompt to send to Claude.
            model: Optional model to use. If None, uses default_model.

        Returns:
            ProviderResult with the response.
        """
        if not prompt:
            return ProviderResult(
                output="",
                provider_id=self.provider_id,
                model_id=model or self.default_model,
                success=False,
                error="Prompt cannot be empty"
            )

        start_time = time.time()
        model_to_use = model or self.default_model

        try:
            client = self._get_client()

            message = client.messages.create(
                model=model_to_use,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract text from response
            output = ""
            for block in message.content:
                if hasattr(block, 'text'):
                    output += block.text

            duration = time.time() - start_time

            # Get token usage if available
            tokens_used = None
            if hasattr(message, 'usage') and message.usage:
                tokens_used = getattr(message.usage, 'output_tokens', None)

            return ProviderResult(
                output=output,
                provider_id=self.provider_id,
                model_id=model_to_use,
                success=True,
                duration=duration,
                tokens_used=tokens_used
            )

        except ClaudeAPIProviderError:
            raise
        except Exception as e:
            duration = time.time() - start_time
            return ProviderResult(
                output="",
                provider_id=self.provider_id,
                model_id=model_to_use,
                success=False,
                error=str(e),
                duration=duration
            )

    def run_streaming(
        self,
        prompt: str,
        model: Optional[str] = None
    ) -> Generator[str, None, None]:
        """Execute a prompt and stream the response.

        Args:
            prompt: The prompt to send to Claude.
            model: Optional model to use. If None, uses default_model.

        Yields:
            Chunks of the response as they arrive.
        """
        if not prompt:
            return

        model_to_use = model or self.default_model

        try:
            client = self._get_client()

            with client.messages.stream(
                model=model_to_use,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            ) as stream:
                for text in stream.text_stream:
                    yield text

        except Exception as e:
            yield f"[Error: {str(e)}]"

    def get_available_models(self) -> List[ProviderModel]:
        """Get list of available Claude models.

        Returns:
            List of ProviderModel objects for all available Claude models.
        """
        return self.AVAILABLE_MODELS.copy()
