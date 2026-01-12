"""Provider health monitoring module.

Provides health checking, status tracking, and error logging for AI providers.
"""
import sqlite3
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

from providers.base import AIProvider


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status values for providers."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass
class ProviderHealthStatus:
    """Health status result for a provider."""
    provider_id: str
    status: HealthStatus
    last_check: datetime
    last_success: Optional[datetime] = None
    failure_count: int = 0
    error_message: Optional[str] = None
    response_time_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'provider_id': self.provider_id,
            'status': self.status.value,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'last_success': self.last_success.isoformat() if self.last_success else None,
            'failure_count': self.failure_count,
            'error_message': self.error_message,
            'response_time_ms': self.response_time_ms
        }


def check_provider_health(provider: AIProvider) -> ProviderHealthStatus:
    """Check the health status of a provider.

    Performs a basic health check by:
    1. Checking if the provider is available
    2. Attempting a minimal test prompt

    Args:
        provider: The AIProvider instance to check.

    Returns:
        ProviderHealthStatus with the check results.
    """
    check_time = datetime.now()

    try:
        # First check availability
        if not provider.is_available():
            return ProviderHealthStatus(
                provider_id=provider.provider_id,
                status=HealthStatus.DOWN,
                last_check=check_time,
                error_message="Provider reports unavailable"
            )

        # Try a minimal test prompt
        start_time = datetime.now()
        result = provider.run("health check: respond with 'OK'")
        end_time = datetime.now()
        response_time_ms = (end_time - start_time).total_seconds() * 1000

        if result.success:
            return ProviderHealthStatus(
                provider_id=provider.provider_id,
                status=HealthStatus.HEALTHY,
                last_check=check_time,
                last_success=check_time,
                failure_count=0,
                response_time_ms=response_time_ms
            )
        else:
            return ProviderHealthStatus(
                provider_id=provider.provider_id,
                status=HealthStatus.DEGRADED,
                last_check=check_time,
                error_message=result.error or "Unknown error",
                response_time_ms=response_time_ms
            )

    except Exception as e:
        logger.error(f"Health check failed for {provider.provider_id}: {e}")
        return ProviderHealthStatus(
            provider_id=provider.provider_id,
            status=HealthStatus.DOWN,
            last_check=check_time,
            error_message=str(e)
        )


def store_health_status(conn: sqlite3.Connection, status: ProviderHealthStatus) -> None:
    """Store health status in the database.

    Updates or inserts the health status for a provider.

    Args:
        conn: Database connection.
        status: ProviderHealthStatus to store.
    """
    cursor = conn.cursor()

    # Check if record exists
    cursor.execute(
        "SELECT id, failure_count FROM provider_health WHERE provider_id = ?",
        (status.provider_id,)
    )
    existing = cursor.fetchone()

    if status.status == HealthStatus.HEALTHY:
        failure_count = 0
        last_success = status.last_check.isoformat()
    else:
        # Increment failure count if there's an existing record
        current_failures = existing[1] if existing else 0
        failure_count = current_failures + 1
        last_success = None

    if existing:
        # Update existing record
        if last_success:
            cursor.execute("""
                UPDATE provider_health
                SET status = ?, last_check = ?, last_success = ?,
                    failure_count = ?, error_message = ?, updated_at = ?
                WHERE provider_id = ?
            """, (
                status.status.value,
                status.last_check.isoformat(),
                last_success,
                failure_count,
                status.error_message,
                datetime.now().isoformat(),
                status.provider_id
            ))
        else:
            cursor.execute("""
                UPDATE provider_health
                SET status = ?, last_check = ?, failure_count = ?,
                    error_message = ?, updated_at = ?
                WHERE provider_id = ?
            """, (
                status.status.value,
                status.last_check.isoformat(),
                failure_count,
                status.error_message,
                datetime.now().isoformat(),
                status.provider_id
            ))
    else:
        # Insert new record
        cursor.execute("""
            INSERT INTO provider_health (
                provider_id, status, last_check, last_success, failure_count, error_message
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            status.provider_id,
            status.status.value,
            status.last_check.isoformat(),
            last_success,
            failure_count,
            status.error_message
        ))

    conn.commit()


def get_health_status(conn: sqlite3.Connection, provider_id: str) -> Optional[Dict[str, Any]]:
    """Get health status for a specific provider.

    Args:
        conn: Database connection.
        provider_id: Provider identifier.

    Returns:
        Dictionary with health status or None if not found.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT provider_id, status, last_check, last_success, failure_count, error_message
        FROM provider_health
        WHERE provider_id = ?
    """, (provider_id,))

    row = cursor.fetchone()
    if row:
        return {
            'provider_id': row[0],
            'status': row[1],
            'last_check': row[2],
            'last_success': row[3],
            'failure_count': row[4],
            'error_message': row[5]
        }
    return None


def get_all_health_statuses(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Get health statuses for all providers.

    Args:
        conn: Database connection.

    Returns:
        List of dictionaries with health status information.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT provider_id, status, last_check, last_success, failure_count, error_message
        FROM provider_health
        ORDER BY provider_id
    """)

    statuses = []
    for row in cursor.fetchall():
        statuses.append({
            'provider_id': row[0],
            'status': row[1],
            'last_check': row[2],
            'last_success': row[3],
            'failure_count': row[4],
            'error_message': row[5]
        })

    return statuses


def log_provider_error(conn: sqlite3.Connection, provider_id: str, error_message: str,
                       error_type: str = "general") -> None:
    """Log a provider error.

    Args:
        conn: Database connection.
        provider_id: Provider identifier.
        error_message: Error message to log.
        error_type: Type of error (e.g., 'timeout', 'api_error', 'connection').
    """
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO provider_error_log (provider_id, error_message, error_type)
        VALUES (?, ?, ?)
    """, (provider_id, error_message, error_type))
    conn.commit()


def get_recent_errors(conn: sqlite3.Connection, provider_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent errors for a provider.

    Args:
        conn: Database connection.
        provider_id: Provider identifier.
        limit: Maximum number of errors to return.

    Returns:
        List of error dictionaries.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, provider_id, error_message, error_type, created_at
        FROM provider_error_log
        WHERE provider_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (provider_id, limit))

    errors = []
    for row in cursor.fetchall():
        errors.append({
            'id': row[0],
            'provider_id': row[1],
            'error_message': row[2],
            'error_type': row[3],
            'created_at': row[4]
        })

    return errors


def is_provider_healthy(conn: sqlite3.Connection, provider_id: str) -> bool:
    """Quick check if a provider is healthy.

    Args:
        conn: Database connection.
        provider_id: Provider identifier.

    Returns:
        True if provider is healthy, False otherwise.
    """
    status = get_health_status(conn, provider_id)
    if status:
        return status['status'] == 'healthy'
    return True  # Assume healthy if no status recorded yet


def get_healthy_providers(conn: sqlite3.Connection) -> List[str]:
    """Get list of healthy provider IDs.

    Args:
        conn: Database connection.

    Returns:
        List of provider IDs that are healthy.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT provider_id FROM provider_health
        WHERE status = 'healthy'
    """)

    return [row[0] for row in cursor.fetchall()]
