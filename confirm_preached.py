"""Confirm preached functionality module.

Provides workflow for marking sermons as preached with dates,
tracking status transitions, and generating confirmation receipts.
"""

from datetime import datetime, date
import re


def _validate_date(date_str):
    """Validate date string format YYYY-MM-DD."""
    if not date_str:
        return False
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, date_str):
        return False
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def mark_as_preached(conn, sermon_id, preached_date, confirmed_by=None):
    """Mark a sermon as preached.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        preached_date: Date the sermon was preached (YYYY-MM-DD).
        confirmed_by: Optional name of confirmer.

    Returns:
        dict: Result with success status and details.
    """
    # Validate date format
    if not _validate_date(preached_date):
        return {
            'success': False,
            'error': 'Invalid date format. Use YYYY-MM-DD.'
        }

    cursor = conn.cursor()

    # Check sermon exists
    cursor.execute('SELECT id, status FROM sermons WHERE id = ?', (sermon_id,))
    row = cursor.fetchone()
    if row is None:
        return {
            'success': False,
            'error': 'Sermon not found'
        }

    current_status = row['status'] if hasattr(row, 'keys') else row[1]

    # Check if cancelled
    if current_status == 'cancelled':
        return {
            'success': False,
            'error': 'Cannot mark cancelled sermon as preached'
        }

    # Check if already preached
    cursor.execute(
        'SELECT id, preached_date FROM preached_records WHERE sermon_id = ?',
        (sermon_id,)
    )
    existing = cursor.fetchone()
    if existing is not None:
        existing_date = existing['preached_date'] if hasattr(existing, 'keys') else existing[1]
        return {
            'success': True,
            'sermon_id': sermon_id,
            'preached_date': preached_date,
            'confirmed_by': confirmed_by,
            'confirmed_at': datetime.now().isoformat(),
            'warning': f'Sermon already preached on {existing_date}'
        }

    # Check for future date
    result = {
        'success': True,
        'sermon_id': sermon_id,
        'preached_date': preached_date,
        'confirmed_by': confirmed_by,
        'confirmed_at': datetime.now().isoformat()
    }

    try:
        preached_dt = datetime.strptime(preached_date, '%Y-%m-%d').date()
        if preached_dt > date.today():
            result['warning'] = 'Future date - sermon scheduled but not yet preached'
    except ValueError:
        pass

    # Create preached record
    confirmed_at = datetime.now().isoformat()
    cursor.execute(
        '''INSERT INTO preached_records (sermon_id, preached_date, confirmed_by, confirmed_at)
           VALUES (?, ?, ?, ?)''',
        (sermon_id, preached_date, confirmed_by, confirmed_at)
    )

    # Update sermon status
    cursor.execute(
        'UPDATE sermons SET status = ? WHERE id = ?',
        ('preached', sermon_id)
    )

    conn.commit()
    return result


def get_preached_status(conn, sermon_id):
    """Get the preached status of a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        dict: Status information, or None if sermon not found.
    """
    cursor = conn.cursor()

    # Check sermon exists
    cursor.execute('SELECT id, status FROM sermons WHERE id = ?', (sermon_id,))
    row = cursor.fetchone()
    if row is None:
        return None

    current_status = row['status'] if hasattr(row, 'keys') else row[1]

    # Check for preached record
    cursor.execute(
        '''SELECT preached_date, confirmed_by, confirmed_at
           FROM preached_records WHERE sermon_id = ?
           ORDER BY id DESC LIMIT 1''',
        (sermon_id,)
    )
    record = cursor.fetchone()

    if record is not None:
        return {
            'sermon_id': sermon_id,
            'is_preached': True,
            'status': current_status,
            'preached_date': record['preached_date'] if hasattr(record, 'keys') else record[0],
            'confirmed_by': record['confirmed_by'] if hasattr(record, 'keys') else record[1],
            'confirmed_at': record['confirmed_at'] if hasattr(record, 'keys') else record[2]
        }

    return {
        'sermon_id': sermon_id,
        'is_preached': False,
        'status': current_status,
        'preached_date': None,
        'confirmed_by': None,
        'confirmed_at': None
    }


def update_preached_date(conn, sermon_id, new_date):
    """Update the preached date of a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        new_date: New preached date (YYYY-MM-DD).

    Returns:
        dict: Result with success status.
    """
    cursor = conn.cursor()

    # Check for existing preached record
    cursor.execute(
        'SELECT id FROM preached_records WHERE sermon_id = ?',
        (sermon_id,)
    )
    record = cursor.fetchone()

    if record is None:
        return {
            'success': False,
            'error': 'No preached record found for this sermon'
        }

    record_id = record['id'] if hasattr(record, 'keys') else record[0]

    # Update the date
    cursor.execute(
        'UPDATE preached_records SET preached_date = ? WHERE id = ?',
        (new_date, record_id)
    )
    conn.commit()

    return {
        'success': True,
        'sermon_id': sermon_id,
        'new_date': new_date
    }


def list_preached_sermons(conn, start_date=None, end_date=None):
    """List preached sermons with optional date filtering.

    Args:
        conn: Database connection.
        start_date: Optional start date filter.
        end_date: Optional end date filter.

    Returns:
        list: List of preached sermon dictionaries.
    """
    cursor = conn.cursor()

    query = '''SELECT s.id, s.title, s.scripture, s.scheduled_date, s.status,
                      pr.preached_date, pr.confirmed_by, pr.confirmed_at
               FROM sermons s
               JOIN preached_records pr ON s.id = pr.sermon_id
               WHERE 1=1'''
    params = []

    if start_date:
        query += ' AND pr.preached_date >= ?'
        params.append(start_date)

    if end_date:
        query += ' AND pr.preached_date <= ?'
        params.append(end_date)

    query += ' ORDER BY pr.preached_date DESC'

    cursor.execute(query, params)
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'title': row['title'] if hasattr(row, 'keys') else row[1],
            'scripture': row['scripture'] if hasattr(row, 'keys') else row[2],
            'scheduled_date': row['scheduled_date'] if hasattr(row, 'keys') else row[3],
            'status': row['status'] if hasattr(row, 'keys') else row[4],
            'preached_date': row['preached_date'] if hasattr(row, 'keys') else row[5],
            'confirmed_by': row['confirmed_by'] if hasattr(row, 'keys') else row[6],
            'confirmed_at': row['confirmed_at'] if hasattr(row, 'keys') else row[7]
        })

    return result


def get_unpreached_sermons(conn):
    """Get all unpreached sermons.

    Args:
        conn: Database connection.

    Returns:
        list: List of unpreached sermon dictionaries ordered by scheduled_date.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT s.id, s.title, s.scripture, s.scheduled_date, s.status
           FROM sermons s
           WHERE s.id NOT IN (SELECT sermon_id FROM preached_records)
             AND s.status != 'preached'
           ORDER BY s.scheduled_date'''
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'title': row['title'] if hasattr(row, 'keys') else row[1],
            'scripture': row['scripture'] if hasattr(row, 'keys') else row[2],
            'scheduled_date': row['scheduled_date'] if hasattr(row, 'keys') else row[3],
            'status': row['status'] if hasattr(row, 'keys') else row[4]
        })

    return result


def check_duplicate_preaching(conn, sermon_id, check_date):
    """Check for duplicate preaching on the same or nearby date.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        check_date: Date to check (YYYY-MM-DD).

    Returns:
        dict: Result with duplicate/warning status.
    """
    cursor = conn.cursor()

    # Get existing preached dates for this sermon
    cursor.execute(
        'SELECT preached_date FROM preached_records WHERE sermon_id = ?',
        (sermon_id,)
    )
    rows = cursor.fetchall()

    existing_dates = []
    is_duplicate = False
    has_warning = False
    warning = None

    for row in rows:
        preached_date = row['preached_date'] if hasattr(row, 'keys') else row[0]
        existing_dates.append(preached_date)

        if preached_date == check_date:
            is_duplicate = True

        # Check for nearby dates (within 30 days)
        if not is_duplicate:
            try:
                existing_dt = datetime.strptime(preached_date, '%Y-%m-%d').date()
                check_dt = datetime.strptime(check_date, '%Y-%m-%d').date()
                diff = abs((check_dt - existing_dt).days)
                if diff <= 30:
                    has_warning = True
                    warning = f'Sermon was previously preached on {preached_date} (nearby date)'
            except ValueError:
                pass

    return {
        'sermon_id': sermon_id,
        'check_date': check_date,
        'is_duplicate': is_duplicate,
        'has_warning': has_warning,
        'warning': warning,
        'existing_dates': existing_dates
    }


def generate_preached_receipt(conn, sermon_id):
    """Generate a preached receipt for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        dict: Receipt data, or None if not preached.
    """
    cursor = conn.cursor()

    # Get sermon details
    cursor.execute(
        '''SELECT s.id, s.title, s.scripture, s.scheduled_date,
                  pr.preached_date, pr.confirmed_by, pr.confirmed_at
           FROM sermons s
           JOIN preached_records pr ON s.id = pr.sermon_id
           WHERE s.id = ?
           ORDER BY pr.id DESC LIMIT 1''',
        (sermon_id,)
    )
    row = cursor.fetchone()

    if row is None:
        return None

    return {
        'sermon_id': row['id'] if hasattr(row, 'keys') else row[0],
        'title': row['title'] if hasattr(row, 'keys') else row[1],
        'scripture': row['scripture'] if hasattr(row, 'keys') else row[2],
        'scheduled_date': row['scheduled_date'] if hasattr(row, 'keys') else row[3],
        'preached_date': row['preached_date'] if hasattr(row, 'keys') else row[4],
        'confirmed_by': row['confirmed_by'] if hasattr(row, 'keys') else row[5],
        'confirmed_at': row['confirmed_at'] if hasattr(row, 'keys') else row[6],
        'generated_at': datetime.now().isoformat()
    }


def get_preaching_history(conn, sermon_id):
    """Get the preaching status history for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: List of status history entries ordered chronologically.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, sermon_id, old_status, new_status, changed_by, changed_at, reason
           FROM sermon_status_history
           WHERE sermon_id = ?
           ORDER BY id ASC''',
        (sermon_id,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
            'old_status': row['old_status'] if hasattr(row, 'keys') else row[2],
            'new_status': row['new_status'] if hasattr(row, 'keys') else row[3],
            'changed_by': row['changed_by'] if hasattr(row, 'keys') else row[4],
            'changed_at': row['changed_at'] if hasattr(row, 'keys') else row[5],
            'reason': row['reason'] if hasattr(row, 'keys') else row[6]
        })

    return result
