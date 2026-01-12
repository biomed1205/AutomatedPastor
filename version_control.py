"""Version Control module for sermon content.

Provides functionality for tracking provider-specific versions of sermon content,
regenerating sections with different providers, and comparing outputs.
"""
import sqlite3
import difflib
from datetime import datetime
from typing import Dict, List, Optional, Any


class SermonNotFoundError(Exception):
    """Raised when a sermon is not found in the database."""
    pass


class ProviderNotFoundError(Exception):
    """Raised when a specified provider is not found in the registry."""
    pass


class VersionNotFoundError(Exception):
    """Raised when a specified version is not found."""
    pass


def save_sermon_version(
    db_conn: sqlite3.Connection,
    sermon_id: int,
    content: str,
    provider_id: str,
    section: str = 'full'
) -> Dict[str, Any]:
    """Save a new version of sermon content.

    Automatically increments the version number for the given sermon/section.

    Args:
        db_conn: Database connection.
        sermon_id: ID of the sermon.
        content: The content to save.
        provider_id: ID of the provider that generated the content.
        section: The section of the sermon ('full', 'introduction', 'point_1',
                'point_2', 'point_3', 'conclusion').

    Returns:
        dict: Version information including version_id, version_number, etc.

    Raises:
        SermonNotFoundError: If the sermon doesn't exist.
    """
    cursor = db_conn.cursor()

    # Verify sermon exists
    cursor.execute("SELECT id FROM sermons WHERE id = ?", (sermon_id,))
    if not cursor.fetchone():
        raise SermonNotFoundError(f"Sermon with id {sermon_id} not found")

    # Get next version number for this sermon/section
    cursor.execute("""
        SELECT COALESCE(MAX(version_number), 0) + 1
        FROM sermon_versions
        WHERE sermon_id = ? AND section = ?
    """, (sermon_id, section))
    version_number = cursor.fetchone()[0]

    # Calculate word count
    word_count = len(content.split()) if content else 0

    # Insert the version
    cursor.execute("""
        INSERT INTO sermon_versions
        (sermon_id, version_number, provider_id, content, section, word_count)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (sermon_id, version_number, provider_id, content, section, word_count))
    db_conn.commit()

    version_id = cursor.lastrowid

    # Get the created_at timestamp
    cursor.execute("SELECT created_at FROM sermon_versions WHERE id = ?", (version_id,))
    row = cursor.fetchone()
    created_at = row[0] if row else None

    return {
        'version_id': version_id,
        'version_number': version_number,
        'sermon_id': sermon_id,
        'provider_id': provider_id,
        'section': section,
        'word_count': word_count,
        'created_at': created_at
    }


def get_sermon_versions(
    db_conn: sqlite3.Connection,
    sermon_id: int,
    section: Optional[str] = None,
    provider_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get all versions for a sermon.

    Args:
        db_conn: Database connection.
        sermon_id: ID of the sermon.
        section: Optional filter by section.
        provider_id: Optional filter by provider.

    Returns:
        list: List of version dictionaries ordered by created_at descending.
    """
    cursor = db_conn.cursor()

    query = """
        SELECT id, sermon_id, version_number, provider_id, content, section,
               word_count, created_at
        FROM sermon_versions
        WHERE sermon_id = ?
    """
    params = [sermon_id]

    if section:
        query += " AND section = ?"
        params.append(section)

    if provider_id:
        query += " AND provider_id = ?"
        params.append(provider_id)

    query += " ORDER BY version_number DESC, created_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    versions = []
    for row in rows:
        versions.append({
            'id': row[0],
            'sermon_id': row[1],
            'version_number': row[2],
            'provider_id': row[3],
            'content': row[4],
            'section': row[5],
            'word_count': row[6],
            'created_at': row[7]
        })

    return versions


def get_latest_version(
    db_conn: sqlite3.Connection,
    sermon_id: int,
    section: str = 'full'
) -> Optional[Dict[str, Any]]:
    """Get the latest version for a sermon section.

    Args:
        db_conn: Database connection.
        sermon_id: ID of the sermon.
        section: The section to get.

    Returns:
        dict: The latest version or None if no versions exist.
    """
    cursor = db_conn.cursor()

    cursor.execute("""
        SELECT id, sermon_id, version_number, provider_id, content, section,
               word_count, created_at
        FROM sermon_versions
        WHERE sermon_id = ? AND section = ?
        ORDER BY version_number DESC
        LIMIT 1
    """, (sermon_id, section))

    row = cursor.fetchone()
    if not row:
        return None

    return {
        'id': row[0],
        'sermon_id': row[1],
        'version_number': row[2],
        'provider_id': row[3],
        'content': row[4],
        'section': row[5],
        'word_count': row[6],
        'created_at': row[7]
    }


def get_version_by_number(
    db_conn: sqlite3.Connection,
    sermon_id: int,
    version_number: int,
    section: str = 'full'
) -> Optional[Dict[str, Any]]:
    """Get a specific version by version number.

    Args:
        db_conn: Database connection.
        sermon_id: ID of the sermon.
        version_number: The version number to retrieve.
        section: The section to get.

    Returns:
        dict: The version or None if not found.
    """
    cursor = db_conn.cursor()

    cursor.execute("""
        SELECT id, sermon_id, version_number, provider_id, content, section,
               word_count, created_at
        FROM sermon_versions
        WHERE sermon_id = ? AND version_number = ? AND section = ?
    """, (sermon_id, version_number, section))

    row = cursor.fetchone()
    if not row:
        return None

    return {
        'id': row[0],
        'sermon_id': row[1],
        'version_number': row[2],
        'provider_id': row[3],
        'content': row[4],
        'section': row[5],
        'word_count': row[6],
        'created_at': row[7]
    }


def regenerate_section(
    db_conn: sqlite3.Connection,
    registry,  # ProviderRegistry
    sermon_id: int,
    section: str,
    provider_id: str
) -> Dict[str, Any]:
    """Regenerate a sermon section with a specific provider.

    Args:
        db_conn: Database connection.
        registry: ProviderRegistry instance.
        sermon_id: ID of the sermon.
        section: The section to regenerate ('full', 'introduction', 'point_1', etc.)
        provider_id: ID of the provider to use.

    Returns:
        dict: Result including the new content, version_id, etc.

    Raises:
        SermonNotFoundError: If sermon doesn't exist.
        ProviderNotFoundError: If provider doesn't exist.
    """
    cursor = db_conn.cursor()

    # Verify sermon exists and get its data
    cursor.execute("""
        SELECT id, title, scripture, theme, main_point, manuscript
        FROM sermons WHERE id = ?
    """, (sermon_id,))
    sermon_row = cursor.fetchone()

    if not sermon_row:
        raise SermonNotFoundError(f"Sermon with id {sermon_id} not found")

    # Get the provider
    provider = registry.get_provider(provider_id)
    if not provider:
        raise ProviderNotFoundError(f"Provider not found: {provider_id}")

    # Build the regeneration prompt based on section
    title = sermon_row[1]
    scripture = sermon_row[2]
    theme = sermon_row[3] or ''
    main_point = sermon_row[4] or ''
    current_manuscript = sermon_row[5] or ''

    if section == 'full':
        prompt = _build_full_sermon_prompt(scripture, title, theme, main_point)
    else:
        prompt = _build_section_prompt(
            section, scripture, title, theme, main_point, current_manuscript
        )

    # Generate content
    result = provider.run(prompt)

    if not result.success:
        return {
            'success': False,
            'error': result.error or 'Generation failed',
            'section': section,
            'provider_id': provider_id
        }

    # Save the new version
    version_info = save_sermon_version(
        db_conn, sermon_id, result.output, provider_id, section
    )

    return {
        'success': True,
        'section': section,
        'provider_id': provider_id,
        'content': result.output,
        'version_id': version_info['version_id'],
        'version_number': version_info['version_number'],
        'word_count': version_info['word_count']
    }


def _build_full_sermon_prompt(
    scripture: str,
    title: str,
    theme: str,
    main_point: str
) -> str:
    """Build a prompt for regenerating a full sermon."""
    prompt_parts = [
        "Generate a sermon with the following requirements:",
        "",
        f"Scripture: {scripture}",
        f"Title: {title}",
    ]

    if theme:
        prompt_parts.append(f"Theme: {theme}")

    if main_point:
        prompt_parts.append(f"Main Point: {main_point}")

    prompt_parts.extend([
        "",
        "Requirements:",
        "- Length: 2000-2500 words (approximately 15 minutes)",
        "- Theology: Wesleyan/United Methodist",
        "- Structure: Clear 3-point outline",
        "- Include: Scripture engagement, contemporary illustrations, practical application",
        "- Avoid: Personal stories, political content",
        "",
        "Format the output with:",
        "# [Title]",
        "## Outline",
        "[numbered outline]",
        "## Manuscript",
        "[full sermon text]"
    ])

    return '\n'.join(prompt_parts)


def _build_section_prompt(
    section: str,
    scripture: str,
    title: str,
    theme: str,
    main_point: str,
    current_manuscript: str
) -> str:
    """Build a prompt for regenerating a specific section."""
    section_names = {
        'introduction': 'Introduction',
        'point_1': 'First Point',
        'point_2': 'Second Point',
        'point_3': 'Third Point',
        'conclusion': 'Conclusion'
    }

    section_name = section_names.get(section, section.replace('_', ' ').title())

    prompt_parts = [
        f"Generate the {section_name} section of a sermon:",
        "",
        f"Scripture: {scripture}",
        f"Title: {title}",
    ]

    if theme:
        prompt_parts.append(f"Theme: {theme}")

    if main_point:
        prompt_parts.append(f"Main Point: {main_point}")

    if current_manuscript:
        prompt_parts.extend([
            "",
            "Current sermon content (for context):",
            current_manuscript[:1000] + "..." if len(current_manuscript) > 1000 else current_manuscript
        ])

    prompt_parts.extend([
        "",
        f"Write only the {section_name} section.",
        "Requirements:",
        "- Theology: Wesleyan/United Methodist",
        "- Include: Scripture engagement, contemporary illustrations",
        "- Avoid: Personal stories, political content"
    ])

    return '\n'.join(prompt_parts)


def compare_provider_outputs(
    db_conn: sqlite3.Connection,
    sermon_id: int,
    provider1: str,
    provider2: str,
    section: str = 'full'
) -> Dict[str, Any]:
    """Compare outputs between two providers.

    Args:
        db_conn: Database connection.
        sermon_id: ID of the sermon.
        provider1: First provider ID.
        provider2: Second provider ID.
        section: Section to compare.

    Returns:
        dict: Comparison data including content from both providers and diff.
    """
    # Get latest version from each provider
    versions1 = get_sermon_versions(db_conn, sermon_id, section=section, provider_id=provider1)
    versions2 = get_sermon_versions(db_conn, sermon_id, section=section, provider_id=provider2)

    result = {
        'sermon_id': sermon_id,
        'section': section,
        'provider1': {
            'provider_id': provider1,
            'content': None,
            'version_number': None,
            'word_count': None,
            'created_at': None
        },
        'provider2': {
            'provider_id': provider2,
            'content': None,
            'version_number': None,
            'word_count': None,
            'created_at': None
        },
        'diff': None,
        'differences': []
    }

    if versions1:
        v1 = versions1[0]  # Latest version
        result['provider1'] = {
            'provider_id': provider1,
            'content': v1['content'],
            'version_number': v1['version_number'],
            'word_count': v1['word_count'],
            'created_at': v1['created_at']
        }

    if versions2:
        v2 = versions2[0]  # Latest version
        result['provider2'] = {
            'provider_id': provider2,
            'content': v2['content'],
            'version_number': v2['version_number'],
            'word_count': v2['word_count'],
            'created_at': v2['created_at']
        }

    # Generate diff if both have content
    if result['provider1']['content'] and result['provider2']['content']:
        content1 = result['provider1']['content']
        content2 = result['provider2']['content']

        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            content1.splitlines(keepends=True),
            content2.splitlines(keepends=True),
            fromfile=f'{provider1} version',
            tofile=f'{provider2} version',
            lineterm=''
        ))

        result['diff'] = ''.join(diff_lines)

        # Calculate differences summary
        additions = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))

        result['differences'] = {
            'additions': additions,
            'deletions': deletions,
            'has_changes': additions > 0 or deletions > 0
        }

    return result


def get_version_diff(
    db_conn: sqlite3.Connection,
    sermon_id: int,
    version1: int,
    version2: int,
    section: str = 'full'
) -> Dict[str, Any]:
    """Get diff between two specific versions.

    Args:
        db_conn: Database connection.
        sermon_id: ID of the sermon.
        version1: First version number.
        version2: Second version number.
        section: Section to compare.

    Returns:
        dict: Diff data including additions, deletions, and diff lines.
    """
    v1 = get_version_by_number(db_conn, sermon_id, version1, section)
    v2 = get_version_by_number(db_conn, sermon_id, version2, section)

    result = {
        'sermon_id': sermon_id,
        'section': section,
        'version1': version1,
        'version2': version2,
        'diff_lines': [],
        'additions': 0,
        'deletions': 0,
        'has_changes': False
    }

    if not v1 or not v2:
        return result

    content1 = v1['content'] or ''
    content2 = v2['content'] or ''

    # Generate unified diff
    diff_lines = list(difflib.unified_diff(
        content1.splitlines(keepends=True),
        content2.splitlines(keepends=True),
        fromfile=f'Version {version1}',
        tofile=f'Version {version2}',
        lineterm=''
    ))

    result['diff_lines'] = diff_lines
    result['additions'] = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
    result['deletions'] = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))
    result['has_changes'] = result['additions'] > 0 or result['deletions'] > 0
    result['changes'] = result['additions'] + result['deletions']

    return result


def get_provider_version_stats(
    db_conn: sqlite3.Connection,
    sermon_id: int
) -> Dict[str, Dict[str, Any]]:
    """Get version statistics per provider for a sermon.

    Args:
        db_conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        dict: Statistics per provider including count, avg word count, etc.
    """
    cursor = db_conn.cursor()

    cursor.execute("""
        SELECT
            provider_id,
            COUNT(*) as count,
            AVG(word_count) as avg_word_count,
            SUM(word_count) as total_word_count,
            MIN(created_at) as first_version,
            MAX(created_at) as last_version
        FROM sermon_versions
        WHERE sermon_id = ?
        GROUP BY provider_id
    """, (sermon_id,))

    rows = cursor.fetchall()

    stats = {}
    for row in rows:
        stats[row[0]] = {
            'count': row[1],
            'avg_word_count': round(row[2]) if row[2] else 0,
            'total_word_count': row[3] or 0,
            'first_version': row[4],
            'last_version': row[5]
        }

    return stats
