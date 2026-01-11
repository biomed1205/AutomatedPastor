"""Password authentication module for AutomatedPastor.

Provides password hashing, verification, and session management
using bcrypt for secure password storage.
"""
import os
import bcrypt


class InvalidPasswordError(Exception):
    """Raised when password is invalid (empty or None)."""
    pass


class MissingPasswordError(Exception):
    """Raised when APP_PASSWORD environment variable is not set."""
    pass


# Module-level session state (for testing without Flask context)
_session = {}
_app_password_hash = None


def reset_auth_state():
    """Reset all auth state (for testing)."""
    global _session, _app_password_hash
    _session = {}
    _app_password_hash = None


def hash_password(password):
    """Hash a password using bcrypt.

    Args:
        password: The plaintext password to hash.

    Returns:
        The bcrypt hash as a string.

    Raises:
        InvalidPasswordError: If password is None or empty.
    """
    if password is None or password == '':
        raise InvalidPasswordError('Password cannot be None or empty')

    # Encode to bytes and hash
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)

    return hashed.decode('utf-8')


def verify_password(password, hashed):
    """Verify a password against a bcrypt hash.

    Args:
        password: The plaintext password to verify.
        hashed: The bcrypt hash to verify against.

    Returns:
        True if password matches, False otherwise.
    """
    if password is None or password == '':
        return False

    try:
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except (ValueError, TypeError):
        return False


def set_app_password(password_hash):
    """Set the application password hash.

    Args:
        password_hash: The bcrypt hash of the password.
    """
    global _app_password_hash, _session
    _app_password_hash = password_hash
    # Clear any existing session when password changes
    _session = {}


def get_app_password_hash():
    """Get the application password hash from environment.

    Returns:
        The password hash string.

    Raises:
        MissingPasswordError: If APP_PASSWORD is not set.
    """
    # Check environment first
    env_hash = os.environ.get('APP_PASSWORD')
    if env_hash:
        return env_hash

    # Fall back to module-level (for testing)
    if _app_password_hash:
        return _app_password_hash

    raise MissingPasswordError('APP_PASSWORD environment variable not set')


def login(password):
    """Attempt to log in with the given password.

    Args:
        password: The password to verify.

    Returns:
        True if login successful, False otherwise.
    """
    try:
        stored_hash = get_app_password_hash()
        if verify_password(password, stored_hash):
            _session['authenticated'] = True
            _session['expired'] = False
            return True
    except MissingPasswordError:
        pass

    return False


def logout():
    """Log out the current user by clearing the session."""
    clear_session()


def is_authenticated():
    """Check if the current session is authenticated.

    Returns:
        True if authenticated, False otherwise.
    """
    if _session.get('expired', False):
        return False
    return _session.get('authenticated', False)


def clear_session():
    """Clear all session data."""
    global _session
    _session = {}


def expire_session():
    """Force the current session to expire."""
    _session['expired'] = True


def login_required(f):
    """Decorator to require login for a route.

    Args:
        f: The route function to protect.

    Returns:
        Wrapped function that checks authentication.
    """
    from functools import wraps
    from flask import redirect, url_for, request

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            next_url = request.path
            return redirect(url_for('login_page', next=next_url))
        return f(*args, **kwargs)

    return decorated_function
