"""Google Gemini API provider implementation.

Provides direct API access to Google's Gemini models.
"""
import os
import time
from typing import Optional, List, Generator

from providers.base import AIProvider, ProviderResult, ProviderModel


class GeminiProviderError(Exception):
    """Raised when Gemini provider encounters an error."""
    pass


class GeminiProvider(AIProvider):
    """Google Gemini API provider for direct Google AI API calls.

    This provider uses the Google Generative AI SDK to make direct API calls.
    Supports both GOOGLE_API_KEY and GEMINI_API_KEY environment variables.
    """

    provider_id = "gemini"
    display_name = "Google Gemini"

    # Blue colors for Gemini branding
    color_primary = "#3B82F6"
    color_bg = "#DBEAFE"

    # Available Gemini models
    AVAILABLE_MODELS = [
        ProviderModel(
            id="gemini-2.0-flash",
            name="Gemini 2.0 Flash",
            context_window=1000000,
            max_output_tokens=8192,
            supports_streaming=True,
            supports_vision=True,
            is_default=True,
            description="Fastest Gemini 2.0 model for everyday tasks"
        ),
        ProviderModel(
            id="gemini-1.5-pro",
            name="Gemini 1.5 Pro",
            context_window=2000000,
            max_output_tokens=8192,
            supports_streaming=True,
            supports_vision=True,
            is_default=False,
            description="Most capable model with 2M context window"
        ),
        ProviderModel(
            id="gemini-1.5-flash",
            name="Gemini 1.5 Flash",
            context_window=1000000,
            max_output_tokens=8192,
            supports_streaming=True,
            supports_vision=True,
            is_default=False,
            description="Fast and efficient for high-volume tasks"
        ),
        ProviderModel(
            id="gemini-1.5-flash-8b",
            name="Gemini 1.5 Flash 8B",
            context_window=1000000,
            max_output_tokens=8192,
            supports_streaming=True,
            supports_vision=True,
            is_default=False,
            description="Smallest and fastest Flash model"
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
        """Initialize the Gemini API provider.

        Args:
            api_key: Google API key. If None, reads from GOOGLE_API_KEY or
                    GEMINI_API_KEY env vars.
            default_model: Default model to use. If None, uses gemini-2.0-flash.
            max_tokens: Maximum tokens for response (default: 8192).
            timeout: Request timeout in seconds (default: 300).
            **kwargs: Additional configuration options.
        """
        # Get API key from environment if not provided
        # Try GOOGLE_API_KEY first, then GEMINI_API_KEY
        resolved_api_key = api_key or os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
        super().__init__(api_key=resolved_api_key, **kwargs)

        self.default_model = default_model or "gemini-2.0-flash"
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._genai = None

    def _requires_api_key(self) -> bool:
        """Gemini API requires an API key.

        Returns:
            True - API key is required for this provider.
        """
        return True

    def _get_genai(self):
        """Get or configure the Google Generative AI module.

        Returns:
            Configured genai module.

        Raises:
            GeminiProviderError: If API key is not set or package not installed.
        """
        if self._genai is None:
            if not self.api_key:
                raise GeminiProviderError(
                    "Google API key not set. Set GOOGLE_API_KEY or GEMINI_API_KEY "
                    "environment variable to use Gemini API."
                )
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._genai = genai
            except ImportError:
                raise GeminiProviderError(
                    "google-generativeai package not installed. "
                    "Run: pip install google-generativeai"
                )
        return self._genai

    def _get_model(self, model_name: Optional[str] = None):
        """Get a configured Gemini model.

        Args:
            model_name: Model name to use. If None, uses default_model.

        Returns:
            Configured GenerativeModel instance.
        """
        genai = self._get_genai()
        model_to_use = model_name or self.default_model
        return genai.GenerativeModel(model_to_use)

    def is_available(self) -> bool:
        """Check if the Gemini API is available.

        Returns:
            True if API key is configured, False otherwise.
        """
        return self.api_key is not None and len(self.api_key) > 0

    def run(self, prompt: str, model: Optional[str] = None) -> ProviderResult:
        """Execute a prompt via the Google Gemini API.

        Args:
            prompt: The prompt to send to Gemini.
            model: Optional model to use. If None, uses default_model.

        Returns:
            ProviderResult with the response.
        """
        model_to_use = model or self.default_model

        if not prompt:
            return ProviderResult(
                output="",
                provider_id=self.provider_id,
                model_id=model_to_use,
                success=False,
                error="Prompt cannot be empty"
            )

        start_time = time.time()

        try:
            gemini_model = self._get_model(model_to_use)

            # Configure generation settings
            generation_config = {
                "max_output_tokens": self.max_tokens,
            }

            response = gemini_model.generate_content(
                prompt,
                generation_config=generation_config
            )

            # Extract text from response
            output = response.text if hasattr(response, 'text') else ""

            duration = time.time() - start_time

            # Get token usage if available
            tokens_used = None
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                tokens_used = getattr(response.usage_metadata, 'candidates_token_count', None)

            return ProviderResult(
                output=output,
                provider_id=self.provider_id,
                model_id=model_to_use,
                success=True,
                duration=duration,
                tokens_used=tokens_used
            )

        except GeminiProviderError:
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
            prompt: The prompt to send to Gemini.
            model: Optional model to use. If None, uses default_model.

        Yields:
            Chunks of the response as they arrive.
        """
        if not prompt:
            return

        model_to_use = model or self.default_model

        try:
            gemini_model = self._get_model(model_to_use)

            # Configure generation settings
            generation_config = {
                "max_output_tokens": self.max_tokens,
            }

            response = gemini_model.generate_content(
                prompt,
                generation_config=generation_config,
                stream=True
            )

            for chunk in response:
                if hasattr(chunk, 'text') and chunk.text:
                    yield chunk.text

        except Exception as e:
            yield f"[Error: {str(e)}]"

    def get_available_models(self) -> List[ProviderModel]:
        """Get list of available Gemini models.

        Returns:
            List of ProviderModel objects for all available Gemini models.
        """
        return self.AVAILABLE_MODELS.copy()
