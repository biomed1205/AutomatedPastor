"""Base classes for AI providers.

Defines the abstract interface that all AI providers must implement.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, List, Generator, Any, Tuple
from datetime import datetime


class ProviderStatus(Enum):
    """Status of an AI provider."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class ProviderModel:
    """Represents an available model from a provider."""
    id: str
    name: str
    context_window: int = 4096
    max_output_tokens: Optional[int] = None
    supports_streaming: bool = True
    supports_vision: bool = False
    is_default: bool = False
    description: str = ""


@dataclass
class ProviderResult:
    """Result from an AI provider execution."""
    output: str
    provider_id: str
    model_id: str
    success: bool
    error: Optional[str] = None
    duration: float = 0.0
    tokens_used: Optional[int] = None
    token_count: Optional[int] = None  # Alias for tokens_used
    metadata: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert the result to a dictionary.

        Returns:
            Dictionary representation of the result.
        """
        return {
            'output': self.output,
            'provider_id': self.provider_id,
            'model_id': self.model_id,
            'success': self.success,
            'error': self.error,
            'duration': self.duration,
            'tokens_used': self.tokens_used,
            'token_count': self.token_count,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }


class AIProvider(ABC):
    """Abstract base class for AI providers.

    All AI providers (Claude, OpenAI, Gemini, etc.) must implement this interface.
    """

    # Class attributes that subclasses should override
    provider_id: str = ""
    display_name: str = ""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize the provider.

        Args:
            api_key: Optional API key for the provider
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self._config = kwargs

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and properly configured.

        Returns:
            True if the provider can be used, False otherwise.
        """
        pass

    @abstractmethod
    def run(self, prompt: str, model: Optional[str] = None) -> ProviderResult:
        """Execute a prompt and return the result.

        Args:
            prompt: The prompt to send to the AI
            model: Optional specific model to use

        Returns:
            ProviderResult with the output and metadata
        """
        pass

    @abstractmethod
    def run_streaming(self, prompt: str, model: Optional[str] = None) -> Generator[str, None, None]:
        """Execute a prompt and stream the response.

        Args:
            prompt: The prompt to send to the AI
            model: Optional specific model to use

        Yields:
            Chunks of the response as they arrive
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[ProviderModel]:
        """Get list of available models from this provider.

        Returns:
            List of ProviderModel objects
        """
        pass

    def _requires_api_key(self) -> bool:
        """Check if this provider requires an API key.

        Default implementation returns True. Override in subclasses
        that don't require an API key (e.g., CLI-based providers).

        Returns:
            True if an API key is required
        """
        return True

    def validate_config(self) -> Tuple[bool, str]:
        """Validate the provider configuration.

        Returns:
            Tuple of (is_valid, message)
        """
        if self._requires_api_key() and not self.api_key:
            return False, f"API key is required for {self.display_name}"
        return True, "Configuration valid"

    def validate_configuration(self) -> Tuple[bool, Optional[str]]:
        """Validate the provider configuration (alias for validate_config).

        Returns:
            Tuple of (is_valid, error_message)
        """
        is_valid, message = self.validate_config()
        return is_valid, message if not is_valid else None

    def get_status(self) -> ProviderStatus:
        """Get the current status of this provider.

        Returns:
            ProviderStatus enum value
        """
        is_valid, _ = self.validate_config()
        if not is_valid:
            return ProviderStatus.DISABLED

        if self.is_available():
            return ProviderStatus.AVAILABLE
        return ProviderStatus.UNAVAILABLE
