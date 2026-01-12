"""OpenAI API provider implementation.

Provides direct API access to OpenAI's GPT models.
"""
import os
import time
from typing import Optional, List, Generator

from providers.base import AIProvider, ProviderResult, ProviderModel


class OpenAIProviderError(Exception):
    """Raised when OpenAI provider encounters an error."""
    pass


class OpenAIProvider(AIProvider):
    """OpenAI API provider for direct OpenAI API calls.

    This provider uses the OpenAI Python SDK to make direct API calls.
    Supports GPT-4o, GPT-4o-mini, GPT-4-turbo, o1, and o1-mini models.
    """

    provider_id = "openai"
    display_name = "OpenAI"

    # Green colors for OpenAI
    color_primary = "#10B981"
    color_bg = "#D1FAE5"

    # Available OpenAI models
    AVAILABLE_MODELS = [
        ProviderModel(
            id="gpt-4o",
            name="GPT-4o",
            context_window=128000,
            max_output_tokens=16384,
            supports_streaming=True,
            supports_vision=True,
            is_default=True,
            description="Most capable GPT-4 model with vision"
        ),
        ProviderModel(
            id="gpt-4o-mini",
            name="GPT-4o Mini",
            context_window=128000,
            max_output_tokens=16384,
            supports_streaming=True,
            supports_vision=True,
            is_default=False,
            description="Smaller, faster, and cheaper GPT-4o variant"
        ),
        ProviderModel(
            id="gpt-4-turbo",
            name="GPT-4 Turbo",
            context_window=128000,
            max_output_tokens=4096,
            supports_streaming=True,
            supports_vision=True,
            is_default=False,
            description="GPT-4 Turbo with improved performance"
        ),
        ProviderModel(
            id="o1",
            name="o1",
            context_window=200000,
            max_output_tokens=100000,
            supports_streaming=False,
            supports_vision=True,
            is_default=False,
            description="Advanced reasoning model"
        ),
        ProviderModel(
            id="o1-mini",
            name="o1 Mini",
            context_window=128000,
            max_output_tokens=65536,
            supports_streaming=False,
            supports_vision=False,
            is_default=False,
            description="Smaller, faster reasoning model"
        ),
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        max_tokens: int = 4096,
        timeout: int = 300,
        **kwargs
    ):
        """Initialize the OpenAI API provider.

        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.
            default_model: Default model to use. If None, uses gpt-4o.
            max_tokens: Maximum tokens for response (default: 4096).
            timeout: Request timeout in seconds (default: 300).
            **kwargs: Additional configuration options.
        """
        # Get API key from environment if not provided
        resolved_api_key = api_key or os.environ.get('OPENAI_API_KEY')
        super().__init__(api_key=resolved_api_key, **kwargs)

        self.default_model = default_model or "gpt-4o"
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._client = None

    def _requires_api_key(self) -> bool:
        """OpenAI API requires an API key.

        Returns:
            True - API key is required for this provider.
        """
        return True

    def _get_client(self):
        """Get or create the OpenAI client.

        Returns:
            OpenAI client instance.

        Raises:
            OpenAIProviderError: If API key is not set or openai package not installed.
        """
        if self._client is None:
            if not self.api_key:
                raise OpenAIProviderError(
                    "OPENAI_API_KEY environment variable not set. "
                    "Please set it to use OpenAI API."
                )
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                raise OpenAIProviderError(
                    "openai package not installed. Run: pip install openai"
                )
        return self._client

    def is_available(self) -> bool:
        """Check if the OpenAI API is available.

        Returns:
            True if API key is configured, False otherwise.
        """
        return self.api_key is not None and len(self.api_key) > 0

    def run(self, prompt: str, model: Optional[str] = None) -> ProviderResult:
        """Execute a prompt via the OpenAI API.

        Args:
            prompt: The prompt to send to OpenAI.
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

            response = client.chat.completions.create(
                model=model_to_use,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract text from response
            output = ""
            if response.choices and len(response.choices) > 0:
                message = response.choices[0].message
                if message and message.content:
                    output = message.content

            duration = time.time() - start_time

            # Get token usage if available
            tokens_used = None
            if hasattr(response, 'usage') and response.usage:
                tokens_used = getattr(response.usage, 'total_tokens', None)

            return ProviderResult(
                output=output,
                provider_id=self.provider_id,
                model_id=model_to_use,
                success=True,
                duration=duration,
                tokens_used=tokens_used
            )

        except OpenAIProviderError:
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
            prompt: The prompt to send to OpenAI.
            model: Optional model to use. If None, uses default_model.

        Yields:
            Chunks of the response as they arrive.
        """
        if not prompt:
            return

        model_to_use = model or self.default_model

        try:
            client = self._get_client()

            stream = client.chat.completions.create(
                model=model_to_use,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                stream=True
            )

            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content

        except Exception as e:
            yield f"[Error: {str(e)}]"

    def get_available_models(self) -> List[ProviderModel]:
        """Get list of available OpenAI models.

        Returns:
            List of ProviderModel objects for all available OpenAI models.
        """
        return self.AVAILABLE_MODELS.copy()
