"""Provider Registry for managing multiple AI providers.

Provides a central registry for registering, configuring, and executing
prompts across multiple AI providers in parallel or sequentially.
"""
import sqlite3
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Any
from datetime import datetime

from providers.base import AIProvider, ProviderResult


logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Central registry for AI providers.

    Manages registration, configuration, and execution of AI providers.
    Supports running prompts on multiple providers in parallel.
    """

    def __init__(self, db_conn: sqlite3.Connection):
        """Initialize the provider registry.

        Args:
            db_conn: SQLite database connection for provider configuration
        """
        self._db_conn = db_conn
        self._providers: Dict[str, AIProvider] = {}
        self._max_workers = 5  # Max parallel provider executions

    def register(self, provider: AIProvider) -> None:
        """Register an AI provider.

        Args:
            provider: The AIProvider instance to register
        """
        if not provider.provider_id:
            raise ValueError("Provider must have a provider_id")

        self._providers[provider.provider_id] = provider
        logger.info(f"Registered provider: {provider.provider_id}")

    def unregister(self, provider_id: str) -> bool:
        """Unregister an AI provider.

        Args:
            provider_id: The ID of the provider to unregister

        Returns:
            True if provider was unregistered, False if not found
        """
        if provider_id in self._providers:
            del self._providers[provider_id]
            logger.info(f"Unregistered provider: {provider_id}")
            return True
        return False

    def get_provider(self, provider_id: str) -> Optional[AIProvider]:
        """Get a provider by ID.

        Args:
            provider_id: The ID of the provider to retrieve

        Returns:
            The AIProvider instance or None if not found
        """
        return self._providers.get(provider_id)

    def list_providers(self) -> List[str]:
        """List all registered provider IDs.

        Returns:
            List of registered provider IDs
        """
        return list(self._providers.keys())

    def get_enabled_providers(self) -> List[AIProvider]:
        """Get all enabled providers from the database.

        Returns:
            List of AIProvider instances that are enabled in the database
        """
        enabled = []

        try:
            cursor = self._db_conn.execute(
                "SELECT provider_name FROM ai_providers WHERE is_enabled = 1"
            )
            enabled_ids = {row[0] for row in cursor.fetchall()}

            for provider_id, provider in self._providers.items():
                if provider_id in enabled_ids:
                    enabled.append(provider)
        except sqlite3.Error as e:
            logger.error(f"Database error getting enabled providers: {e}")

        return enabled

    def get_default_provider(self) -> Optional[AIProvider]:
        """Get the default provider.

        Returns:
            The default AIProvider or None if no default is set
        """
        try:
            cursor = self._db_conn.execute(
                "SELECT provider_name FROM ai_providers WHERE is_default = 1 LIMIT 1"
            )
            row = cursor.fetchone()

            if row:
                return self._providers.get(row[0])
        except sqlite3.Error as e:
            logger.error(f"Database error getting default provider: {e}")

        return None

    def get_provider_config(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a provider from the database.

        Args:
            provider_id: The provider ID

        Returns:
            Dictionary of configuration or None if not found
        """
        try:
            cursor = self._db_conn.execute(
                """SELECT provider_name, display_name, api_key_encrypted,
                          default_model, is_enabled, is_default,
                          color_primary, color_bg, config_json
                   FROM ai_providers WHERE provider_name = ?""",
                (provider_id,)
            )
            row = cursor.fetchone()

            if row:
                return {
                    'provider_name': row[0],
                    'display_name': row[1],
                    'api_key_encrypted': row[2],
                    'default_model': row[3],
                    'is_enabled': bool(row[4]),
                    'is_default': bool(row[5]),
                    'color_primary': row[6],
                    'color_bg': row[7],
                    'config_json': row[8]
                }
        except sqlite3.Error as e:
            logger.error(f"Database error getting provider config: {e}")

        return None

    def run_on_providers(
        self,
        prompt: str,
        provider_ids: List[str],
        model: Optional[str] = None
    ) -> List[ProviderResult]:
        """Run a prompt on multiple providers in parallel.

        Args:
            prompt: The prompt to send to providers
            provider_ids: List of provider IDs to run on
            model: Optional model to use (if None, uses provider default)

        Returns:
            List of ProviderResult objects, one per provider
        """
        results: List[ProviderResult] = []

        def execute_provider(provider_id: str) -> ProviderResult:
            """Execute a single provider and return result."""
            provider = self._providers.get(provider_id)

            if not provider:
                return ProviderResult(
                    output="",
                    provider_id=provider_id,
                    model_id=model or "",
                    success=False,
                    error=f"Provider not found: {provider_id}"
                )

            start_time = datetime.now()
            try:
                result = provider.run(prompt, model)
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"Provider {provider_id} error: {e}")
                return ProviderResult(
                    output="",
                    provider_id=provider_id,
                    model_id=model or "",
                    success=False,
                    error=str(e),
                    duration=duration
                )

        # Use ThreadPoolExecutor for parallel execution
        with ThreadPoolExecutor(max_workers=min(len(provider_ids), self._max_workers)) as executor:
            futures = {
                executor.submit(execute_provider, pid): pid
                for pid in provider_ids
            }

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    provider_id = futures[future]
                    logger.error(f"Future error for {provider_id}: {e}")
                    results.append(ProviderResult(
                        output="",
                        provider_id=provider_id,
                        model_id=model or "",
                        success=False,
                        error=str(e)
                    ))

        return results

    def run_on_default(self, prompt: str, model: Optional[str] = None) -> Optional[ProviderResult]:
        """Run a prompt on the default provider.

        Args:
            prompt: The prompt to send
            model: Optional model to use

        Returns:
            ProviderResult or None if no default provider
        """
        default = self.get_default_provider()
        if not default:
            return None

        results = self.run_on_providers(prompt, [default.provider_id], model)
        return results[0] if results else None

    def run_on_all_enabled(self, prompt: str, model: Optional[str] = None) -> List[ProviderResult]:
        """Run a prompt on all enabled providers.

        Args:
            prompt: The prompt to send
            model: Optional model to use

        Returns:
            List of ProviderResult objects
        """
        enabled = self.get_enabled_providers()
        if not enabled:
            return []

        provider_ids = [p.provider_id for p in enabled]
        return self.run_on_providers(prompt, provider_ids, model)
