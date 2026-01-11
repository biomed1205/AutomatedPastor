"""Shareable links generation module.

Provides secure shareable links system for sermon drafts with tokens,
password protection, expiration, and access tracking.
"""

import secrets
import hashlib
from datetime import datetime


def create_share_link(conn, sermon_id, expires_at=None, password=None, created_by=None):
    """Create a shareable link for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon to share.
        expires_at: Optional expiration datetime.
        password: Optional password for protection.
        created_by: Optional user ID who created the link.

    Returns:
        dict: Share link details with token, or None if sermon doesn't exist.
    """
    cursor = conn.cursor()

    # Check sermon exists
    cursor.execute('SELECT id FROM sermons WHERE id = ?', (sermon_id,))
    if cursor.fetchone() is None:
        return None

    # Generate cryptographically secure token
    token = secrets.token_urlsafe(32)

    # Hash password if provided
    password_hash = None
    if password:
        password_hash = hashlib.sha256(password.encode()).hexdigest()

    # Format expiration
    expires_str = None
    if expires_at:
        if isinstance(expires_at, datetime):
            expires_str = expires_at.isoformat()
        else:
            expires_str = expires_at

    # Insert share link
    cursor.execute(
        '''INSERT INTO share_links (sermon_id, share_token, password_hash, expires_at, created_by)
           VALUES (?, ?, ?, ?, ?)''',
        (sermon_id, token, password_hash, expires_str, created_by)
    )
    conn.commit()

    return {
        'id': cursor.lastrowid,
        'token': token,
        'share_token': token,
        'sermon_id': sermon_id,
        'expires_at': expires_str,
        'has_password': password is not None,
        'password_protected': password is not None,
        'created_by': created_by
    }


def get_share_link(conn, token):
    """Get share link details by token.

    Args:
        conn: Database connection.
        token: Share token to look up.

    Returns:
        dict: Share link details, or None if not found.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT sl.id, sl.sermon_id, sl.share_token, sl.password_hash,
                  sl.expires_at, sl.is_revoked, sl.created_by, sl.created_at,
                  s.title, s.content
           FROM share_links sl
           JOIN sermons s ON sl.sermon_id = s.id
           WHERE sl.share_token = ?''',
        (token,)
    )
    row = cursor.fetchone()

    if row is None:
        return None

    # Check if expired
    expires_at = row['expires_at'] if hasattr(row, 'keys') else row[4]
    is_expired = False
    if expires_at:
        try:
            exp_dt = datetime.fromisoformat(expires_at) if isinstance(expires_at, str) else expires_at
            is_expired = exp_dt < datetime.now()
        except (ValueError, TypeError):
            pass

    return {
        'id': row['id'] if hasattr(row, 'keys') else row[0],
        'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
        'share_token': row['share_token'] if hasattr(row, 'keys') else row[2],
        'token': row['share_token'] if hasattr(row, 'keys') else row[2],
        'password_hash': row['password_hash'] if hasattr(row, 'keys') else row[3],
        'has_password': (row['password_hash'] if hasattr(row, 'keys') else row[3]) is not None,
        'expires_at': expires_at,
        'is_revoked': row['is_revoked'] if hasattr(row, 'keys') else row[5],
        'is_expired': is_expired,
        'expired': is_expired,
        'created_by': row['created_by'] if hasattr(row, 'keys') else row[6],
        'created_at': row['created_at'] if hasattr(row, 'keys') else row[7],
        'sermon_title': row['title'] if hasattr(row, 'keys') else row[8],
        'sermon_content': row['content'] if hasattr(row, 'keys') else row[9]
    }


def validate_share_link(conn, token, password=None):
    """Validate a share link token.

    Args:
        conn: Database connection.
        token: Share token to validate.
        password: Optional password if link is protected.

    Returns:
        tuple: (is_valid, message) where is_valid is bool and message explains result.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, sermon_id, password_hash, expires_at, is_revoked
           FROM share_links WHERE share_token = ?''',
        (token,)
    )
    row = cursor.fetchone()

    if row is None:
        return False, 'Link not found or invalid token'

    is_revoked = row['is_revoked'] if hasattr(row, 'keys') else row[4]
    if is_revoked:
        return False, 'This link has been revoked'

    # Check expiration
    expires_at = row['expires_at'] if hasattr(row, 'keys') else row[3]
    if expires_at:
        try:
            exp_dt = datetime.fromisoformat(expires_at) if isinstance(expires_at, str) else expires_at
            if exp_dt < datetime.now():
                return False, 'This link has expired'
        except (ValueError, TypeError):
            pass

    # Check password
    password_hash = row['password_hash'] if hasattr(row, 'keys') else row[2]
    if password_hash:
        if password is None:
            return False, 'Password required'
        provided_hash = hashlib.sha256(password.encode()).hexdigest()
        if provided_hash != password_hash:
            return False, 'Incorrect password'

    return True, 'Valid'


def list_share_links(conn, sermon_id):
    """List all share links for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: List of share link dictionaries.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, sermon_id, share_token, password_hash, expires_at,
                  is_revoked, created_by, created_at
           FROM share_links
           WHERE sermon_id = ?
           ORDER BY created_at DESC''',
        (sermon_id,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        expires_at = row['expires_at'] if hasattr(row, 'keys') else row[4]
        is_expired = False
        if expires_at:
            try:
                exp_dt = datetime.fromisoformat(expires_at) if isinstance(expires_at, str) else expires_at
                is_expired = exp_dt < datetime.now()
            except (ValueError, TypeError):
                pass

        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
            'share_token': row['share_token'] if hasattr(row, 'keys') else row[2],
            'token': row['share_token'] if hasattr(row, 'keys') else row[2],
            'has_password': (row['password_hash'] if hasattr(row, 'keys') else row[3]) is not None,
            'expires_at': expires_at,
            'is_revoked': row['is_revoked'] if hasattr(row, 'keys') else row[5],
            'is_expired': is_expired,
            'created_by': row['created_by'] if hasattr(row, 'keys') else row[6],
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[7]
        })

    return result


def revoke_share_link(conn, token):
    """Revoke a share link.

    Args:
        conn: Database connection.
        token: Share token to revoke.

    Returns:
        bool: True if revoked, False if not found.
    """
    cursor = conn.cursor()

    # Check if link exists
    cursor.execute('SELECT id FROM share_links WHERE share_token = ?', (token,))
    if cursor.fetchone() is None:
        return False

    cursor.execute(
        'UPDATE share_links SET is_revoked = 1 WHERE share_token = ?',
        (token,)
    )
    conn.commit()
    return True


def record_share_access(conn, token, details):
    """Record access to a share link.

    Args:
        conn: Database connection.
        token: Share token that was accessed.
        details: dict with accessor info (ip, name, email).

    Returns:
        bool: True if recorded, False if token not found.
    """
    cursor = conn.cursor()

    # Get link ID
    cursor.execute('SELECT id FROM share_links WHERE share_token = ?', (token,))
    row = cursor.fetchone()
    if row is None:
        return False

    link_id = row['id'] if hasattr(row, 'keys') else row[0]

    cursor.execute(
        '''INSERT INTO share_access_log
           (share_link_id, share_token, accessor_ip, accessor_name, accessor_email)
           VALUES (?, ?, ?, ?, ?)''',
        (
            link_id,
            token,
            details.get('ip'),
            details.get('name'),
            details.get('email')
        )
    )
    conn.commit()
    return True


def get_share_stats(conn, sermon_id):
    """Get sharing statistics for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        dict: Statistics including link count and access count.
    """
    cursor = conn.cursor()

    # Count links
    cursor.execute(
        'SELECT COUNT(*) as count FROM share_links WHERE sermon_id = ?',
        (sermon_id,)
    )
    row = cursor.fetchone()
    link_count = row['count'] if hasattr(row, 'keys') else row[0]

    # Count accesses
    cursor.execute(
        '''SELECT COUNT(*) as count FROM share_access_log sal
           JOIN share_links sl ON sal.share_link_id = sl.id
           WHERE sl.sermon_id = ?''',
        (sermon_id,)
    )
    row = cursor.fetchone()
    access_count = row['count'] if hasattr(row, 'keys') else row[0]

    # Count unique visitors by email
    cursor.execute(
        '''SELECT COUNT(DISTINCT accessor_email) as count FROM share_access_log sal
           JOIN share_links sl ON sal.share_link_id = sl.id
           WHERE sl.sermon_id = ? AND accessor_email IS NOT NULL''',
        (sermon_id,)
    )
    row = cursor.fetchone()
    unique_visitors = row['count'] if hasattr(row, 'keys') else row[0]

    # Count active links (not revoked, not expired)
    cursor.execute(
        '''SELECT COUNT(*) as count FROM share_links
           WHERE sermon_id = ? AND is_revoked = 0
           AND (expires_at IS NULL OR expires_at > ?)''',
        (sermon_id, datetime.now().isoformat())
    )
    row = cursor.fetchone()
    active_links = row['count'] if hasattr(row, 'keys') else row[0]

    return {
        'sermon_id': sermon_id,
        'total_links': link_count,
        'link_count': link_count,
        'total_accesses': access_count,
        'access_count': access_count,
        'unique_visitors': unique_visitors,
        'active_links': active_links
    }


def revoke_all_links(conn, sermon_id):
    """Revoke all share links for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        int: Number of links revoked.
    """
    cursor = conn.cursor()

    cursor.execute(
        'UPDATE share_links SET is_revoked = 1 WHERE sermon_id = ? AND is_revoked = 0',
        (sermon_id,)
    )
    count = cursor.rowcount
    conn.commit()
    return count if count > 0 else True


def cleanup_expired_links(conn, days_past_expiration=0):
    """Clean up expired share links.

    Args:
        conn: Database connection.
        days_past_expiration: Delete links expired more than this many days ago.

    Returns:
        int: Number of links cleaned up.
    """
    cursor = conn.cursor()

    cutoff = datetime.now().isoformat()

    cursor.execute(
        '''DELETE FROM share_links
           WHERE expires_at IS NOT NULL AND expires_at < ?''',
        (cutoff,)
    )
    count = cursor.rowcount
    conn.commit()
    return count
