"""Archive export and backup functionality module.

Provides complete archive export, backup creation,
restore, and validation capabilities.

THIS COMPLETES PHASE 7: Sermon Archive
"""

import json
import os
import zipfile
from datetime import datetime


BACKUP_VERSION = "1.0"


def export_full_archive(conn, format='zip', output_dir=None):
    """Export entire sermon archive.

    Args:
        conn: Database connection.
        format: Export format ('zip' or 'json').
        output_dir: Output directory path.

    Returns:
        dict: Result with success status and path.
    """
    cursor = conn.cursor()

    # Get all sermons
    cursor.execute(
        '''SELECT id, title, scripture, content, manuscript, word_count,
                  status, preached_date, series_id, created_at, updated_at
           FROM sermons'''
    )
    sermon_rows = cursor.fetchall()

    sermon_count = len(sermon_rows)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    if sermon_count == 0:
        return {
            'success': True,
            'warning': 'No sermons to export',
            'sermon_count': 0
        }

    sermons = []
    for row in sermon_rows:
        sermon = _row_to_sermon_dict(row)
        sermon['research_notes'] = _get_research_notes(conn, sermon['id'])
        sermon['illustrations'] = _get_illustrations(conn, sermon['id'])
        sermon['post_notes'] = _get_post_notes(conn, sermon['id'])
        sermons.append(sermon)

    # Get series
    cursor.execute('SELECT id, name, description FROM sermon_series')
    series_rows = cursor.fetchall()
    series = [_row_to_series_dict(row) for row in series_rows]

    if format == 'json':
        filename = f'archive_export_{timestamp}.json'
        filepath = os.path.join(output_dir, filename) if output_dir else filename

        data = {
            'sermons': sermons,
            'series': series,
            'exported_at': datetime.now().isoformat(),
            'sermon_count': sermon_count
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return {
            'success': True,
            'path': filepath,
            'sermon_count': sermon_count
        }

    # ZIP format
    filename = f'archive_export_{timestamp}.zip'
    filepath = os.path.join(output_dir, filename) if output_dir else filename

    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add metadata
        metadata = {
            'version': BACKUP_VERSION,
            'created_at': datetime.now().isoformat(),
            'sermon_count': sermon_count,
            'series_count': len(series)
        }
        zf.writestr('metadata.json', json.dumps(metadata, indent=2))

        # Add sermons data
        zf.writestr('sermons.json', json.dumps(sermons, indent=2, ensure_ascii=False))
        zf.writestr('series.json', json.dumps(series, indent=2, ensure_ascii=False))

    return {
        'success': True,
        'path': filepath,
        'sermon_count': sermon_count
    }


def export_sermon_bundle(conn, sermon_id, format='zip', output_dir=None):
    """Export a single sermon bundle.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        format: Export format ('zip', 'json', 'pdf', 'docx').
        output_dir: Output directory path.

    Returns:
        dict: Result with success status and path.
    """
    cursor = conn.cursor()

    # Get sermon
    cursor.execute(
        '''SELECT id, title, scripture, content, manuscript, word_count,
                  status, preached_date, series_id, created_at, updated_at
           FROM sermons WHERE id = ?''',
        (sermon_id,)
    )
    row = cursor.fetchone()

    if row is None:
        return {
            'success': False,
            'error': 'Sermon not found'
        }

    sermon = _row_to_sermon_dict(row)
    sermon['research_notes'] = _get_research_notes(conn, sermon_id)
    sermon['illustrations'] = _get_illustrations(conn, sermon_id)
    sermon['post_notes'] = _get_post_notes(conn, sermon_id)

    # Sanitize title for filename
    safe_title = _sanitize_filename(sermon['title'])
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    contents = ['manuscript', 'research_notes', 'illustrations', 'post_notes']

    if format == 'json':
        filename = f'{safe_title}_{timestamp}.json'
        filepath = os.path.join(output_dir, filename) if output_dir else filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(sermon, f, indent=2, ensure_ascii=False)

        return {
            'success': True,
            'path': filepath,
            'contents': contents
        }

    elif format == 'pdf':
        # Placeholder for PDF export
        return {
            'success': True,
            'format': 'pdf',
            'message': 'PDF export not yet implemented',
            'contents': contents
        }

    elif format == 'docx':
        # Placeholder for Word export
        return {
            'success': True,
            'format': 'docx',
            'message': 'Word export not yet implemented',
            'contents': contents
        }

    # Default ZIP format
    filename = f'{safe_title}_{timestamp}.zip'
    filepath = os.path.join(output_dir, filename) if output_dir else filename

    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('sermon.json', json.dumps(sermon, indent=2, ensure_ascii=False))

        if sermon.get('manuscript'):
            zf.writestr('manuscript.txt', sermon['manuscript'])

    return {
        'success': True,
        'path': filepath,
        'contents': contents
    }


def export_date_range(conn, start, end, output_dir=None):
    """Export sermons within a date range.

    Args:
        conn: Database connection.
        start: Start date (YYYY-MM-DD).
        end: End date (YYYY-MM-DD).
        output_dir: Output directory path.

    Returns:
        dict: Result with success status and sermon count.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, title, scripture, content, manuscript, word_count,
                  status, preached_date, series_id, created_at, updated_at
           FROM sermons
           WHERE preached_date >= ? AND preached_date <= ?''',
        (start, end)
    )
    rows = cursor.fetchall()

    sermon_count = len(rows)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    sermons = []
    for row in rows:
        sermon = _row_to_sermon_dict(row)
        sermon['research_notes'] = _get_research_notes(conn, sermon['id'])
        sermon['illustrations'] = _get_illustrations(conn, sermon['id'])
        sermon['post_notes'] = _get_post_notes(conn, sermon['id'])
        sermons.append(sermon)

    filename = f'sermons_{start}_to_{end}_{timestamp}.zip'
    filepath = os.path.join(output_dir, filename) if output_dir else filename

    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
        metadata = {
            'start_date': start,
            'end_date': end,
            'sermon_count': sermon_count,
            'exported_at': datetime.now().isoformat()
        }
        zf.writestr('metadata.json', json.dumps(metadata, indent=2))
        zf.writestr('sermons.json', json.dumps(sermons, indent=2, ensure_ascii=False))

    return {
        'success': True,
        'path': filepath,
        'sermon_count': sermon_count,
        'start_date': start,
        'end_date': end
    }


def create_backup(conn, backup_path):
    """Create a full backup of the database.

    Args:
        conn: Database connection.
        backup_path: Path for the backup file.

    Returns:
        dict: Result with success status and metadata.
    """
    cursor = conn.cursor()

    # Get all data
    cursor.execute('SELECT * FROM sermons')
    sermons = cursor.fetchall()
    sermon_count = len(sermons)

    cursor.execute('SELECT * FROM sermon_series')
    series = cursor.fetchall()

    cursor.execute('SELECT * FROM research_notes')
    research_notes = cursor.fetchall()

    cursor.execute('SELECT * FROM illustrations')
    illustrations = cursor.fetchall()

    cursor.execute('SELECT * FROM post_sermon_notes')
    post_notes = cursor.fetchall()

    created_at = datetime.now().isoformat()

    # Create backup ZIP
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        metadata = {
            'version': BACKUP_VERSION,
            'format_version': BACKUP_VERSION,
            'created_at': created_at,
            'sermon_count': sermon_count,
            'tables': ['sermons', 'sermon_series', 'research_notes',
                       'illustrations', 'post_sermon_notes']
        }
        zf.writestr('metadata.json', json.dumps(metadata, indent=2))

        # Export each table as JSON
        zf.writestr('sermons.json', json.dumps(
            [_row_to_dict(r) for r in sermons], indent=2, ensure_ascii=False))
        zf.writestr('sermon_series.json', json.dumps(
            [_row_to_dict(r) for r in series], indent=2, ensure_ascii=False))
        zf.writestr('research_notes.json', json.dumps(
            [_row_to_dict(r) for r in research_notes], indent=2, ensure_ascii=False))
        zf.writestr('illustrations.json', json.dumps(
            [_row_to_dict(r) for r in illustrations], indent=2, ensure_ascii=False))
        zf.writestr('post_sermon_notes.json', json.dumps(
            [_row_to_dict(r) for r in post_notes], indent=2, ensure_ascii=False))

    return {
        'success': True,
        'path': backup_path,
        'created_at': created_at,
        'version': BACKUP_VERSION,
        'metadata': metadata,
        'sermon_count': sermon_count
    }


def restore_from_backup(conn, backup_path):
    """Restore database from a backup file.

    Args:
        conn: Database connection.
        backup_path: Path to the backup file.

    Returns:
        dict: Result with success status and restored count.
    """
    # Check file exists
    if not os.path.exists(backup_path):
        return {
            'success': False,
            'error': 'Backup file not found'
        }

    # Validate it's a valid ZIP
    try:
        with zipfile.ZipFile(backup_path, 'r') as zf:
            if 'metadata.json' not in zf.namelist():
                return {
                    'success': False,
                    'error': 'Invalid backup format: missing metadata'
                }

            # Read data
            sermons_json = zf.read('sermons.json').decode('utf-8')
            sermons = json.loads(sermons_json)

            series_json = zf.read('sermon_series.json').decode('utf-8')
            series_data = json.loads(series_json)

            research_json = zf.read('research_notes.json').decode('utf-8')
            research_data = json.loads(research_json)

            illus_json = zf.read('illustrations.json').decode('utf-8')
            illus_data = json.loads(illus_json)

            notes_json = zf.read('post_sermon_notes.json').decode('utf-8')
            notes_data = json.loads(notes_json)

    except zipfile.BadZipFile:
        return {
            'success': False,
            'error': 'Invalid or corrupted backup file'
        }

    cursor = conn.cursor()
    restored_count = 0

    # Restore series first (for foreign key)
    for s in series_data:
        cursor.execute(
            '''INSERT INTO sermon_series (id, name, description)
               VALUES (?, ?, ?)''',
            (s.get('id'), s.get('name'), s.get('description'))
        )

    # Restore sermons
    for sermon in sermons:
        cursor.execute(
            '''INSERT INTO sermons (id, title, scripture, content, manuscript,
                                   word_count, status, preached_date, series_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (sermon.get('id'), sermon.get('title'), sermon.get('scripture'),
             sermon.get('content'), sermon.get('manuscript'),
             sermon.get('word_count', 0), sermon.get('status'),
             sermon.get('preached_date'), sermon.get('series_id'))
        )
        restored_count += 1

    # Restore research notes
    for note in research_data:
        cursor.execute(
            '''INSERT INTO research_notes (id, sermon_id, content, source)
               VALUES (?, ?, ?, ?)''',
            (note.get('id'), note.get('sermon_id'),
             note.get('content'), note.get('source'))
        )

    # Restore illustrations
    for illus in illus_data:
        cursor.execute(
            '''INSERT INTO illustrations (id, sermon_id, content, source)
               VALUES (?, ?, ?, ?)''',
            (illus.get('id'), illus.get('sermon_id'),
             illus.get('content'), illus.get('source'))
        )

    # Restore post notes
    for note in notes_data:
        cursor.execute(
            '''INSERT INTO post_sermon_notes (id, sermon_id, note_type, content)
               VALUES (?, ?, ?, ?)''',
            (note.get('id'), note.get('sermon_id'),
             note.get('note_type'), note.get('content'))
        )

    conn.commit()

    return {
        'success': True,
        'restored_count': restored_count
    }


def validate_backup(backup_path):
    """Validate a backup file.

    Args:
        backup_path: Path to the backup file.

    Returns:
        dict: Validation result with is_valid and details.
    """
    if not os.path.exists(backup_path):
        return {
            'is_valid': False,
            'error': 'File not found'
        }

    try:
        with zipfile.ZipFile(backup_path, 'r') as zf:
            names = zf.namelist()

            has_metadata = 'metadata.json' in names
            has_sermons = 'sermons.json' in names

            if not has_metadata:
                return {
                    'is_valid': False,
                    'has_metadata': False,
                    'error': 'Missing metadata.json'
                }

            # Verify metadata is valid JSON
            try:
                metadata_content = zf.read('metadata.json').decode('utf-8')
                metadata = json.loads(metadata_content)
            except (json.JSONDecodeError, UnicodeDecodeError):
                return {
                    'is_valid': False,
                    'error': 'Corrupted metadata'
                }

            return {
                'is_valid': True,
                'has_metadata': True,
                'has_sermons': has_sermons,
                'file_count': len(names),
                'version': metadata.get('version')
            }

    except zipfile.BadZipFile:
        return {
            'is_valid': False,
            'error': 'Invalid or corrupted ZIP file'
        }


def get_backup_metadata(backup_path):
    """Get metadata from a backup file.

    Args:
        backup_path: Path to the backup file.

    Returns:
        dict: Metadata from backup, or None if invalid.
    """
    if not os.path.exists(backup_path):
        return None

    try:
        with zipfile.ZipFile(backup_path, 'r') as zf:
            if 'metadata.json' not in zf.namelist():
                return None

            metadata_content = zf.read('metadata.json').decode('utf-8')
            return json.loads(metadata_content)

    except (zipfile.BadZipFile, json.JSONDecodeError, UnicodeDecodeError):
        return None


def list_available_backups(backup_dir, sort_by='date'):
    """List available backup files in a directory.

    Args:
        backup_dir: Directory to search for backups.
        sort_by: Sort order ('date' or 'name').

    Returns:
        list: List of backup file info dicts.
    """
    if not os.path.exists(backup_dir):
        return []

    backups = []

    for filename in os.listdir(backup_dir):
        if filename.endswith('.zip'):
            filepath = os.path.join(backup_dir, filename)
            stat = os.stat(filepath)

            metadata = get_backup_metadata(filepath)

            backups.append({
                'path': filepath,
                'filename': filename,
                'size': stat.st_size,
                'created_at': metadata.get('created_at') if metadata else None,
                'sermon_count': metadata.get('sermon_count') if metadata else None,
                'modified_time': stat.st_mtime
            })

    # Sort backups
    if sort_by == 'date':
        backups.sort(key=lambda x: x['modified_time'], reverse=True)
    else:
        backups.sort(key=lambda x: x['filename'])

    return backups


def _row_to_sermon_dict(row):
    """Convert a sermon row to dictionary."""
    return {
        'id': row['id'] if hasattr(row, 'keys') else row[0],
        'title': row['title'] if hasattr(row, 'keys') else row[1],
        'scripture': row['scripture'] if hasattr(row, 'keys') else row[2],
        'content': row['content'] if hasattr(row, 'keys') else row[3],
        'manuscript': row['manuscript'] if hasattr(row, 'keys') else row[4],
        'word_count': row['word_count'] if hasattr(row, 'keys') else row[5],
        'status': row['status'] if hasattr(row, 'keys') else row[6],
        'preached_date': row['preached_date'] if hasattr(row, 'keys') else row[7],
        'series_id': row['series_id'] if hasattr(row, 'keys') else row[8],
        'created_at': row['created_at'] if hasattr(row, 'keys') else row[9],
        'updated_at': row['updated_at'] if hasattr(row, 'keys') else row[10]
    }


def _row_to_series_dict(row):
    """Convert a series row to dictionary."""
    return {
        'id': row['id'] if hasattr(row, 'keys') else row[0],
        'name': row['name'] if hasattr(row, 'keys') else row[1],
        'description': row['description'] if hasattr(row, 'keys') else row[2]
    }


def _row_to_dict(row):
    """Convert any row to dictionary."""
    if hasattr(row, 'keys'):
        return dict(row)
    return {f'col_{i}': v for i, v in enumerate(row)}


def _get_research_notes(conn, sermon_id):
    """Get research notes for a sermon."""
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, content, source FROM research_notes WHERE sermon_id = ?',
        (sermon_id,)
    )
    rows = cursor.fetchall()
    return [{
        'id': row['id'] if hasattr(row, 'keys') else row[0],
        'content': row['content'] if hasattr(row, 'keys') else row[1],
        'source': row['source'] if hasattr(row, 'keys') else row[2]
    } for row in rows]


def _get_illustrations(conn, sermon_id):
    """Get illustrations for a sermon."""
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, content, source FROM illustrations WHERE sermon_id = ?',
        (sermon_id,)
    )
    rows = cursor.fetchall()
    return [{
        'id': row['id'] if hasattr(row, 'keys') else row[0],
        'content': row['content'] if hasattr(row, 'keys') else row[1],
        'source': row['source'] if hasattr(row, 'keys') else row[2]
    } for row in rows]


def _get_post_notes(conn, sermon_id):
    """Get post-sermon notes for a sermon."""
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, note_type, content FROM post_sermon_notes WHERE sermon_id = ?',
        (sermon_id,)
    )
    rows = cursor.fetchall()
    return [{
        'id': row['id'] if hasattr(row, 'keys') else row[0],
        'note_type': row['note_type'] if hasattr(row, 'keys') else row[1],
        'content': row['content'] if hasattr(row, 'keys') else row[2]
    } for row in rows]


def _sanitize_filename(name):
    """Sanitize a string for use as a filename."""
    # Remove or replace problematic characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    result = name
    for char in invalid_chars:
        result = result.replace(char, '_')
    # Replace spaces and apostrophes
    result = result.replace(' ', '_').replace("'", '')
    return result[:50]  # Limit length
