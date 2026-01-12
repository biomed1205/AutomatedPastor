"""Provider fallback mechanism module.

Provides fallback functionality when primary providers fail, including:
- Ordered fallback chain execution
- Health-aware provider selection
- Fallback attempt logging
"""
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from providers.base import ProviderResult
from providers.registry import ProviderRegistry


logger = logging.getLogger(__name__)


# Module-level fallback log (for testing and debugging)
_fallback_log: List[Dict[str, Any]] = []


def generate_with_fallback(
    prompt: str,
    registry: ProviderRegistry,
    provider_ids: List[str],
    model: Optional[str] = None
) -> ProviderResult:
    """Execute a prompt with fallback through multiple providers.

    Tries each provider in order until one succeeds.

    Args:
        prompt: The prompt to send to providers.
        registry: ProviderRegistry instance.
        provider_ids: Ordered list of provider IDs to try.
        model: Optional model to use.

    Returns:
        ProviderResult from the first successful provider,
        or a failure result if all providers fail.
    """
    global _fallback_log

    errors = []
    attempted_providers = []

    for provider_id in provider_ids:
        provider = registry.get_provider(provider_id)

        if not provider:
            logger.warning(f"Provider {provider_id} not found, skipping")
            _log_fallback_attempt(provider_id, False, "Provider not found")
            continue

        attempted_providers.append(provider_id)

        try:
            logger.info(f"Attempting provider: {provider_id}")
            result = provider.run(prompt, model)

            if result.success:
                logger.info(f"Provider {provider_id} succeeded")
                _log_fallback_attempt(provider_id, True, None)
                return result
            else:
                error_msg = result.error or "Unknown error"
                logger.warning(f"Provider {provider_id} failed: {error_msg}")
                errors.append(f"{provider_id}: {error_msg}")
                _log_fallback_attempt(provider_id, False, error_msg)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Provider {provider_id} exception: {error_msg}")
            errors.append(f"{provider_id}: {error_msg}")
            _log_fallback_attempt(provider_id, False, error_msg)

    # All providers failed
    error_summary = "; ".join(errors) if errors else "No providers available"
    return ProviderResult(
        output="",
        provider_id=attempted_providers[-1] if attempted_providers else "none",
        model_id=model or "",
        success=False,
        error=f"All providers failed. Errors: {error_summary}"
    )


def get_fallback_chain(conn: sqlite3.Connection, primary_provider_id: str) -> List[str]:
    """Get ordered list of fallback providers for a primary provider.

    Returns other enabled providers as potential fallbacks.

    Args:
        conn: Database connection.
        primary_provider_id: The primary provider ID.

    Returns:
        Ordered list of provider IDs for fallback.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT provider_name FROM ai_providers
        WHERE is_enabled = 1 AND provider_name != ?
        ORDER BY is_default DESC, provider_name
    """, (primary_provider_id,))

    return [row[0] for row in cursor.fetchall()]


def get_fallback_chain_by_health(
    conn: sqlite3.Connection,
    provider_ids: List[str]
) -> List[str]:
    """Get fallback chain ordered by provider health status.

    Prioritizes healthy providers, excludes down providers.

    Args:
        conn: Database connection.
        provider_ids: List of provider IDs to order.

    Returns:
        Ordered list of provider IDs (healthy first, down excluded).
    """
    if not provider_ids:
        return []

    # Get health statuses
    placeholders = ",".join("?" * len(provider_ids))
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT provider_id, status, failure_count
        FROM provider_health
        WHERE provider_id IN ({placeholders})
    """, provider_ids)

    health_map = {}
    for row in cursor.fetchall():
        health_map[row[0]] = {
            'status': row[1],
            'failure_count': row[2]
        }

    # Sort providers: healthy first, then by failure count, exclude 'down'
    def sort_key(pid):
        if pid not in health_map:
            return (1, 0)  # Unknown status, assume OK but lower priority

        status = health_map[pid]['status']
        failures = health_map[pid]['failure_count']

        if status == 'down':
            return (3, failures)  # Will be filtered out
        elif status == 'degraded':
            return (2, failures)
        else:  # healthy
            return (0, failures)

    # Sort and filter
    sorted_providers = sorted(provider_ids, key=sort_key)

    # Exclude down providers
    result = [
        pid for pid in sorted_providers
        if pid not in health_map or health_map[pid]['status'] != 'down'
    ]

    return result


def _log_fallback_attempt(provider_id: str, success: bool, error: Optional[str]) -> None:
    """Log a fallback attempt.

    Args:
        provider_id: Provider ID that was attempted.
        success: Whether the attempt succeeded.
        error: Error message if failed.
    """
    global _fallback_log

    _fallback_log.append({
        'provider_id': provider_id,
        'success': success,
        'error': error,
        'timestamp': datetime.now().isoformat()
    })


def get_fallback_log() -> List[Dict[str, Any]]:
    """Get the fallback attempt log.

    Returns:
        List of fallback attempt dictionaries.
    """
    global _fallback_log
    return list(_fallback_log)


def clear_fallback_log() -> None:
    """Clear the fallback attempt log."""
    global _fallback_log
    _fallback_log = []


def generate_sermon_with_fallback(
    params: Dict[str, Any],
    registry: ProviderRegistry,
    conn: sqlite3.Connection,
    provider_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Generate a sermon using fallback mechanism.

    Tries each provider in order until one succeeds.

    Args:
        params: Sermon generation parameters.
        registry: ProviderRegistry instance.
        conn: Database connection.
        provider_ids: Optional list of provider IDs. If None, uses all enabled.

    Returns:
        Dictionary with generation result.
    """
    from sermon_generator import build_sermon_prompt, parse_sermon_output

    # Get provider list
    if provider_ids is None:
        enabled = registry.get_enabled_providers()
        provider_ids = [p.provider_id for p in enabled]

    if not provider_ids:
        return {
            'success': False,
            'error': 'No providers available'
        }

    # Order by health if available
    provider_ids = get_fallback_chain_by_health(conn, provider_ids)

    if not provider_ids:
        return {
            'success': False,
            'error': 'All providers are down'
        }

    # Build prompt
    prompt = build_sermon_prompt(params)

    # Try with fallback
    result = generate_with_fallback(prompt, registry, provider_ids)

    if result.success:
        parsed = parse_sermon_output(result.output)
        return {
            'success': True,
            'provider_id': result.provider_id,
            'model_id': result.model_id,
            **parsed
        }
    else:
        return {
            'success': False,
            'provider_id': result.provider_id,
            'error': result.error
        }


def get_recommended_fallback_order(conn: sqlite3.Connection) -> List[str]:
    """Get recommended provider fallback order based on health and cost.

    Considers:
    - Health status (healthy providers first)
    - Historical reliability (fewer failures first)
    - Cost (cheaper providers first among equally healthy)

    Args:
        conn: Database connection.

    Returns:
        Ordered list of provider IDs.
    """
    cursor = conn.cursor()

    # Get all enabled providers with their health data
    cursor.execute("""
        SELECT
            ap.provider_name,
            COALESCE(ph.status, 'unknown') as status,
            COALESCE(ph.failure_count, 0) as failure_count
        FROM ai_providers ap
        LEFT JOIN provider_health ph ON ap.provider_name = ph.provider_id
        WHERE ap.is_enabled = 1
        ORDER BY
            CASE COALESCE(ph.status, 'unknown')
                WHEN 'healthy' THEN 0
                WHEN 'unknown' THEN 1
                WHEN 'degraded' THEN 2
                WHEN 'down' THEN 3
            END,
            COALESCE(ph.failure_count, 0),
            ap.is_default DESC
    """)

    providers = []
    for row in cursor.fetchall():
        if row[1] != 'down':  # Exclude down providers
            providers.append(row[0])

    return providers
