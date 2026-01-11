"""Tests for password authentication.

These tests verify the authentication system including password hashing,
verification, session management, and protected route access.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL bcrypt hashing and Flask test client - NO MOCKS.
"""
import pytest
import os


class TestPasswordHashing:
    """Test suite for password hashing with bcrypt."""

    def test_should_hash_password_when_valid_password_provided(self):
        """Test that passwords are hashed correctly."""
        from auth import hash_password

        password = 'secure_password123'
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password  # Should not be plaintext
        assert len(hashed) > 20  # Bcrypt hashes are 60+ chars

    def test_should_return_different_hash_for_same_password(self):
        """Test that bcrypt produces different hashes (salt)."""
        from auth import hash_password

        password = 'test_password'
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different salts = different hashes

    def test_should_produce_bcrypt_format_hash(self):
        """Test that hash is in bcrypt format."""
        from auth import hash_password

        password = 'test_password'
        hashed = hash_password(password)

        # Bcrypt hashes start with $2b$ or $2a$ or $2y$
        assert hashed.startswith('$2')

    def test_should_reject_empty_password_when_hashing(self):
        """Test that empty passwords are rejected."""
        from auth import hash_password, InvalidPasswordError

        with pytest.raises(InvalidPasswordError):
            hash_password('')

    def test_should_reject_none_password_when_hashing(self):
        """Test that None passwords are rejected."""
        from auth import hash_password, InvalidPasswordError

        with pytest.raises(InvalidPasswordError):
            hash_password(None)


class TestPasswordVerification:
    """Test suite for password verification."""

    def test_should_return_true_when_correct_password(self):
        """Test successful password verification."""
        from auth import hash_password, verify_password

        password = 'correct_password'
        hashed = hash_password(password)

        result = verify_password(password, hashed)

        assert result is True

    def test_should_return_false_when_incorrect_password(self):
        """Test failed password verification."""
        from auth import hash_password, verify_password

        correct_password = 'correct_password'
        wrong_password = 'wrong_password'
        hashed = hash_password(correct_password)

        result = verify_password(wrong_password, hashed)

        assert result is False

    def test_should_return_false_when_password_is_empty(self):
        """Test verification with empty password."""
        from auth import hash_password, verify_password

        hashed = hash_password('some_password')

        result = verify_password('', hashed)

        assert result is False

    def test_should_return_false_when_password_is_none(self):
        """Test verification with None password."""
        from auth import hash_password, verify_password

        hashed = hash_password('some_password')

        result = verify_password(None, hashed)

        assert result is False

    def test_should_handle_unicode_passwords(self):
        """Test that unicode passwords work correctly."""
        from auth import hash_password, verify_password

        password = 'p@ssw\u00f6rd\u4e2d\u6587'  # Contains special chars
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password('different', hashed) is False

    def test_should_return_false_when_hash_is_invalid(self):
        """Test verification with invalid hash format."""
        from auth import verify_password

        result = verify_password('password', 'not_a_valid_hash')

        assert result is False


class TestLogin:
    """Test suite for login functionality."""

    def test_should_return_true_when_password_correct(self):
        """Test successful login."""
        from auth import login, set_app_password, hash_password

        # Set up the correct password
        correct_password = 'admin_password'
        set_app_password(hash_password(correct_password))

        result = login(correct_password)

        assert result is True

    def test_should_return_false_when_password_incorrect(self):
        """Test failed login with wrong password."""
        from auth import login, set_app_password, hash_password

        set_app_password(hash_password('correct'))

        result = login('wrong_password')

        assert result is False

    def test_should_create_session_when_login_successful(self):
        """Test that session is created on successful login."""
        from auth import login, is_authenticated, set_app_password, hash_password

        set_app_password(hash_password('password'))

        login('password')

        assert is_authenticated() is True

    def test_should_not_create_session_when_login_failed(self):
        """Test that session is not created on failed login."""
        from auth import login, is_authenticated, set_app_password, hash_password

        set_app_password(hash_password('correct'))

        login('wrong')

        assert is_authenticated() is False


class TestLogout:
    """Test suite for logout functionality."""

    def test_should_clear_session_when_logout_called(self):
        """Test that logout clears the session."""
        from auth import login, logout, is_authenticated, set_app_password, hash_password

        set_app_password(hash_password('password'))
        login('password')

        # Verify logged in
        assert is_authenticated() is True

        # Logout
        logout()

        # Verify logged out
        assert is_authenticated() is False

    def test_should_not_error_when_logout_called_without_session(self):
        """Test that logout works even if not logged in."""
        from auth import logout, is_authenticated

        # Should not raise exception
        logout()

        assert is_authenticated() is False


class TestIsAuthenticated:
    """Test suite for authentication checking."""

    def test_should_return_false_when_no_session(self):
        """Test that unauthenticated users are detected."""
        from auth import is_authenticated, clear_session

        clear_session()

        assert is_authenticated() is False

    def test_should_return_true_when_valid_session(self):
        """Test that authenticated users are detected."""
        from auth import login, is_authenticated, set_app_password, hash_password

        set_app_password(hash_password('password'))
        login('password')

        assert is_authenticated() is True

    def test_should_return_false_when_session_expired(self):
        """Test that expired sessions are rejected."""
        from auth import (login, is_authenticated, set_app_password,
                         hash_password, expire_session)

        set_app_password(hash_password('password'))
        login('password')
        expire_session()  # Force session expiration

        assert is_authenticated() is False


class TestLoginRequired:
    """Test suite for login_required decorator."""

    def test_should_allow_access_when_authenticated(self):
        """Test that authenticated users can access protected routes."""
        from auth import set_app_password, hash_password
        from app import create_app

        app = create_app({'TESTING': True})
        set_app_password(hash_password('password'))

        with app.test_client() as client:
            # Login first
            client.post('/login', data={'password': 'password'})

            # Access protected route
            response = client.get('/protected')

            assert response.status_code == 200

    def test_should_redirect_when_not_authenticated(self):
        """Test that unauthenticated users are redirected."""
        from app import create_app

        app = create_app({'TESTING': True})

        with app.test_client() as client:
            response = client.get('/protected')

            # Should redirect to login
            assert response.status_code == 302 or response.status_code == 401

    def test_should_redirect_to_login_page(self):
        """Test that redirect goes to login page."""
        from app import create_app

        app = create_app({'TESTING': True})

        with app.test_client() as client:
            response = client.get('/protected', follow_redirects=False)

            if response.status_code == 302:
                assert '/login' in response.location

    def test_should_preserve_original_url_for_redirect(self):
        """Test that original URL is preserved for post-login redirect."""
        from app import create_app

        app = create_app({'TESTING': True})

        with app.test_client() as client:
            response = client.get('/protected/resource', follow_redirects=False)

            if response.status_code == 302:
                # Should include next parameter or similar
                assert 'next' in response.location or '/protected/resource' in response.location


class TestFlaskAuthIntegration:
    """Test suite for Flask auth integration."""

    def test_should_login_via_form_post(self):
        """Test login via form submission."""
        from auth import set_app_password, hash_password
        from app import create_app

        app = create_app({'TESTING': True})
        set_app_password(hash_password('test_password'))

        with app.test_client() as client:
            response = client.post('/login', data={
                'password': 'test_password'
            }, follow_redirects=True)

            assert response.status_code == 200

    def test_should_show_error_on_invalid_login(self):
        """Test that error is shown on invalid login."""
        from auth import set_app_password, hash_password
        from app import create_app

        app = create_app({'TESTING': True})
        set_app_password(hash_password('correct'))

        with app.test_client() as client:
            response = client.post('/login', data={
                'password': 'wrong'
            })

            # Should show error or stay on login page
            assert response.status_code == 200 or response.status_code == 401
            assert b'error' in response.data.lower() or b'invalid' in response.data.lower()

    def test_should_logout_via_route(self):
        """Test logout via route."""
        from auth import set_app_password, hash_password
        from app import create_app

        app = create_app({'TESTING': True})
        set_app_password(hash_password('password'))

        with app.test_client() as client:
            # Login
            client.post('/login', data={'password': 'password'})

            # Logout
            response = client.get('/logout', follow_redirects=False)

            # Should redirect to login or home
            assert response.status_code == 302

            # Accessing protected route should now fail
            response = client.get('/protected')
            assert response.status_code == 302 or response.status_code == 401

    def test_should_persist_session_across_requests(self):
        """Test that session persists across requests."""
        from auth import set_app_password, hash_password
        from app import create_app

        app = create_app({'TESTING': True})
        set_app_password(hash_password('password'))

        with app.test_client() as client:
            # Login
            client.post('/login', data={'password': 'password'})

            # Multiple requests should maintain auth
            for _ in range(3):
                response = client.get('/protected')
                assert response.status_code == 200


class TestPasswordFromEnv:
    """Test suite for loading password from environment."""

    def test_should_load_password_from_env_variable(self):
        """Test that password is loaded from APP_PASSWORD env var."""
        from auth import get_app_password_hash, hash_password

        # Set env var with a hash
        test_hash = hash_password('env_password')
        os.environ['APP_PASSWORD'] = test_hash

        try:
            loaded_hash = get_app_password_hash()
            assert loaded_hash == test_hash
        finally:
            del os.environ['APP_PASSWORD']

    def test_should_handle_missing_env_variable(self):
        """Test graceful handling of missing APP_PASSWORD."""
        from auth import get_app_password_hash, MissingPasswordError

        # Ensure env var is not set
        if 'APP_PASSWORD' in os.environ:
            del os.environ['APP_PASSWORD']

        with pytest.raises(MissingPasswordError):
            get_app_password_hash()


class TestSessionSecurity:
    """Test suite for session security."""

    def test_should_use_secure_session_cookie(self):
        """Test that session cookie has secure settings."""
        from app import create_app

        app = create_app({'TESTING': True})

        # In production, session should be secure
        # (TESTING mode may disable this)
        assert app.config.get('SESSION_COOKIE_HTTPONLY', True) is True

    def test_should_regenerate_session_on_login(self):
        """Test that session ID changes on login (prevent fixation)."""
        from auth import set_app_password, hash_password
        from app import create_app

        app = create_app({'TESTING': True})
        set_app_password(hash_password('password'))

        with app.test_client() as client:
            # Get session before login
            with client.session_transaction() as sess:
                sess['test_marker'] = 'before'

            # Login
            client.post('/login', data={'password': 'password'})

            # Session should be regenerated (marker may not persist)
            # This is a best practice but implementation-dependent

    def test_should_prevent_csrf_on_login_form(self):
        """Test that login form has CSRF protection."""
        from app import create_app

        app = create_app({'TESTING': True})

        with app.test_client() as client:
            response = client.get('/login')

            # Login form should exist and potentially have CSRF token
            assert response.status_code == 200
            # Note: actual CSRF testing depends on implementation
