"""Provider comparison module for tracking and analyzing AI provider performance.

Provides utilities for:
- Comparing responses from multiple providers
- Tracking performance metrics (response time, token usage, cost)
- Computing and storing comparison statistics
"""
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


# Cost estimates per million tokens (approximate, varies by model)
COST_ESTIMATES = {
    'claude_cli': {'input': 3.0, 'output': 15.0},
    'claude_api': {'input': 3.0, 'output': 15.0},
    'openai': {'input': 5.0, 'output': 15.0},
    'gemini': {'input': 0.5, 'output': 1.5},
}


def hash_prompt(prompt: str) -> str:
    """Generate a consistent hash for a prompt.

    Args:
        prompt: The prompt text to hash.

    Returns:
        A 32-character hexadecimal hash string.
    """
    return hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:32]


def estimate_cost(provider_id: str, input_tokens: int = 0, output_tokens: int = 0) -> float:
    """Estimate the cost for a provider based on token usage.

    Args:
        provider_id: The provider identifier.
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.

    Returns:
        Estimated cost in dollars.
    """
    rates = COST_ESTIMATES.get(provider_id, {'input': 5.0, 'output': 15.0})

    input_cost = (input_tokens / 1_000_000) * rates['input']
    output_cost = (output_tokens / 1_000_000) * rates['output']

    return input_cost + output_cost


def store_comparison_result(
    conn: sqlite3.Connection,
    provider_id: str,
    prompt: str,
    response_time_ms: int,
    input_tokens: int,
    output_tokens: int,
    estimated_cost: float
) -> Dict[str, Any]:
    """Store a comparison result in the database.

    Args:
        conn: Database connection.
        provider_id: The provider identifier.
        prompt: The original prompt.
        response_time_ms: Response time in milliseconds.
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.
        estimated_cost: Estimated cost in dollars.

    Returns:
        Dictionary with the stored record ID.
    """
    cursor = conn.cursor()
    prompt_hash = hash_prompt(prompt)

    cursor.execute("""
        INSERT INTO provider_metrics
        (provider_id, prompt_hash, response_time_ms, input_tokens, output_tokens, estimated_cost)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (provider_id, prompt_hash, response_time_ms, input_tokens, output_tokens, estimated_cost))
    conn.commit()

    return {'id': cursor.lastrowid}


def get_provider_stats(conn: sqlite3.Connection, provider_id: str) -> Optional[Dict[str, Any]]:
    """Get aggregated statistics for a provider.

    Args:
        conn: Database connection.
        provider_id: The provider identifier.

    Returns:
        Dictionary with provider statistics or None if no data.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*) as total_comparisons,
            AVG(response_time_ms) as avg_response_time_ms,
            MIN(response_time_ms) as min_response_time_ms,
            MAX(response_time_ms) as max_response_time_ms,
            SUM(input_tokens) as total_input_tokens,
            SUM(output_tokens) as total_output_tokens,
            SUM(estimated_cost) as total_cost
        FROM provider_metrics
        WHERE provider_id = ?
    """, (provider_id,))

    row = cursor.fetchone()
    if row and row['total_comparisons'] > 0:
        return {
            'total_comparisons': row['total_comparisons'],
            'avg_response_time_ms': row['avg_response_time_ms'],
            'min_response_time_ms': row['min_response_time_ms'],
            'max_response_time_ms': row['max_response_time_ms'],
            'total_input_tokens': row['total_input_tokens'],
            'total_output_tokens': row['total_output_tokens'],
            'total_cost': row['total_cost']
        }
    return None


def get_provider_cost_total(conn: sqlite3.Connection, provider_id: str) -> float:
    """Get total cost for a provider.

    Args:
        conn: Database connection.
        provider_id: The provider identifier.

    Returns:
        Total cost in dollars.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(estimated_cost), 0) as total
        FROM provider_metrics
        WHERE provider_id = ?
    """, (provider_id,))

    row = cursor.fetchone()
    return float(row['total']) if row else 0.0


def get_cost_breakdown(conn: sqlite3.Connection, days: int = 7) -> Dict[str, float]:
    """Get cost breakdown by provider for the last N days.

    Args:
        conn: Database connection.
        days: Number of days to look back.

    Returns:
        Dictionary mapping provider_id to total cost.
    """
    cursor = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    cursor.execute("""
        SELECT provider_id, SUM(estimated_cost) as total
        FROM provider_metrics
        WHERE created_at >= ?
        GROUP BY provider_id
    """, (cutoff,))

    return {row['provider_id']: float(row['total']) for row in cursor.fetchall()}


def get_response_time_stats(conn: sqlite3.Connection, provider_id: str) -> Optional[Dict[str, Any]]:
    """Get response time statistics for a provider.

    Args:
        conn: Database connection.
        provider_id: The provider identifier.

    Returns:
        Dictionary with min, max, avg response times or None if no data.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            MIN(response_time_ms) as min,
            MAX(response_time_ms) as max,
            AVG(response_time_ms) as avg
        FROM provider_metrics
        WHERE provider_id = ?
    """, (provider_id,))

    row = cursor.fetchone()
    if row and row['min'] is not None:
        return {
            'min': row['min'],
            'max': row['max'],
            'avg': row['avg']
        }
    return None


def get_token_usage_stats(conn: sqlite3.Connection, provider_id: str) -> Optional[Dict[str, Any]]:
    """Get token usage statistics for a provider.

    Args:
        conn: Database connection.
        provider_id: The provider identifier.

    Returns:
        Dictionary with total input and output tokens or None if no data.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COALESCE(SUM(input_tokens), 0) as total_input_tokens,
            COALESCE(SUM(output_tokens), 0) as total_output_tokens
        FROM provider_metrics
        WHERE provider_id = ?
    """, (provider_id,))

    row = cursor.fetchone()
    if row:
        return {
            'total_input_tokens': row['total_input_tokens'],
            'total_output_tokens': row['total_output_tokens']
        }
    return None


def get_all_metrics(
    conn: sqlite3.Connection,
    provider_id: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get all metrics, optionally filtered by provider.

    Args:
        conn: Database connection.
        provider_id: Optional provider ID to filter by.
        limit: Maximum number of results.

    Returns:
        List of metric records.
    """
    cursor = conn.cursor()

    if provider_id:
        cursor.execute("""
            SELECT * FROM provider_metrics
            WHERE provider_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (provider_id, limit))
    else:
        cursor.execute("""
            SELECT * FROM provider_metrics
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

    results = []
    for row in cursor.fetchall():
        results.append({
            'id': row['id'],
            'provider_id': row['provider_id'],
            'prompt_hash': row['prompt_hash'],
            'response_time_ms': row['response_time_ms'],
            'input_tokens': row['input_tokens'],
            'output_tokens': row['output_tokens'],
            'estimated_cost': row['estimated_cost'],
            'created_at': row['created_at']
        })

    return results


def get_aggregated_stats(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Get aggregated statistics across all providers.

    Args:
        conn: Database connection.

    Returns:
        Dictionary with aggregated statistics.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*) as total_comparisons,
            AVG(response_time_ms) as avg_response_time,
            SUM(estimated_cost) as total_cost,
            COUNT(DISTINCT provider_id) as providers_used
        FROM provider_metrics
    """)

    row = cursor.fetchone()
    return {
        'total_comparisons': row['total_comparisons'] or 0,
        'avg_response_time': row['avg_response_time'] or 0,
        'total_cost': row['total_cost'] or 0,
        'providers_used': row['providers_used'] or 0
    }
