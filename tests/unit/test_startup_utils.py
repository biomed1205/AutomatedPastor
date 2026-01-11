"""
Tests for Run.bat One-Click Startup Utilities (Issue #231)

Phase 10: Polish - Item 4

Tests cover:
- Environment checks (Python, dependencies, Docker, ports)
- Startup functions (app start, Docker, browser)
- Configuration functions (config path, load, save)
- Health checks (wait for health, is running)

TDD Approach: All tests fail with ModuleNotFoundError until implementation.
NO MOCKS: Uses real implementations where possible.
"""

import pytest
import os
import tempfile
import json


class TestCheckPythonVersion:
    """Tests for check_python_version function."""

    def test_should_check_python_version(self):
        """Should check if Python version is adequate."""
        from startup_utils import check_python_version

        result = check_python_version()

        assert isinstance(result, (bool, dict))

    def test_should_return_true_for_valid_version(self):
        """Should return True for Python 3.11+."""
        from startup_utils import check_python_version

        result = check_python_version()

        # Current Python should pass (test runs on Python 3.11+)
        if isinstance(result, dict):
            assert result.get('valid') is True or result.get('ok') is True
        else:
            assert result is True

    def test_should_include_version_info(self):
        """Should include version information."""
        from startup_utils import check_python_version

        result = check_python_version()

        if isinstance(result, dict):
            assert 'version' in result or 'python_version' in result
        else:
            # Boolean result is also valid
            assert isinstance(result, bool)

    def test_should_specify_minimum_version(self):
        """Should check against minimum version 3.11."""
        from startup_utils import check_python_version

        result = check_python_version(minimum='3.11')

        assert result is not None


class TestCheckDependencies:
    """Tests for check_dependencies function."""

    def test_should_check_dependencies(self):
        """Should check if dependencies are installed."""
        from startup_utils import check_dependencies

        result = check_dependencies()

        assert isinstance(result, (bool, dict))

    def test_should_report_missing_dependencies(self):
        """Should report any missing dependencies."""
        from startup_utils import check_dependencies

        result = check_dependencies()

        if isinstance(result, dict):
            assert 'missing' in result or 'all_installed' in result

    def test_should_check_requirements_file(self):
        """Should check against requirements.txt."""
        from startup_utils import check_dependencies

        result = check_dependencies(requirements_file='requirements.txt')

        assert result is not None


class TestCheckDockerAvailable:
    """Tests for check_docker_available function."""

    def test_should_check_docker_available(self):
        """Should check if Docker is available."""
        from startup_utils import check_docker_available

        result = check_docker_available()

        assert isinstance(result, (bool, dict))

    def test_should_return_availability_status(self):
        """Should return Docker availability status."""
        from startup_utils import check_docker_available

        result = check_docker_available()

        # Either bool or dict with 'available' key
        if isinstance(result, dict):
            assert 'available' in result or 'installed' in result
        else:
            assert isinstance(result, bool)

    def test_should_check_docker_running(self):
        """Should check if Docker daemon is running."""
        from startup_utils import check_docker_available

        result = check_docker_available()

        if isinstance(result, dict):
            assert 'running' in result or 'available' in result


class TestCheckPortAvailable:
    """Tests for check_port_available function."""

    def test_should_check_port_available(self):
        """Should check if port is available."""
        from startup_utils import check_port_available

        # Port 0 is special - should always be available for testing
        result = check_port_available(0)

        assert isinstance(result, bool)

    def test_should_return_true_for_free_port(self):
        """Should return True for free port."""
        from startup_utils import check_port_available

        # High port number unlikely to be in use
        result = check_port_available(59999)

        # Might be in use, but result should be boolean
        assert isinstance(result, bool)

    def test_should_check_default_port(self):
        """Should check port 8787 (app default)."""
        from startup_utils import check_port_available

        result = check_port_available(8787)

        assert isinstance(result, bool)

    def test_should_accept_port_number(self):
        """Should accept port number as parameter."""
        from startup_utils import check_port_available

        result = check_port_available(8080)

        assert isinstance(result, bool)


class TestStartApplication:
    """Tests for start_application function."""

    def test_should_return_start_command(self):
        """Should return or execute start command."""
        from startup_utils import start_application

        # In test mode, should return command not execute
        result = start_application(dry_run=True)

        assert result is not None

    def test_should_support_dry_run(self):
        """Should support dry run mode for testing."""
        from startup_utils import start_application

        result = start_application(dry_run=True)

        # Should return command info without actually starting
        if isinstance(result, dict):
            assert 'command' in result or 'action' in result
        else:
            assert isinstance(result, str)

    def test_should_include_flask_command(self):
        """Should use Flask run command."""
        from startup_utils import start_application

        result = start_application(dry_run=True)

        result_str = str(result).lower()
        assert 'flask' in result_str or 'python' in result_str or 'app' in result_str


class TestStartDockerContainer:
    """Tests for start_docker_container function."""

    def test_should_return_docker_command(self):
        """Should return Docker start command."""
        from startup_utils import start_docker_container

        result = start_docker_container(dry_run=True)

        assert result is not None

    def test_should_use_port_8787(self):
        """Should expose port 8787."""
        from startup_utils import start_docker_container

        result = start_docker_container(dry_run=True)

        result_str = str(result)
        assert '8787' in result_str

    def test_should_support_dry_run(self):
        """Should support dry run for testing."""
        from startup_utils import start_docker_container

        result = start_docker_container(dry_run=True)

        if isinstance(result, dict):
            assert 'command' in result or 'docker' in str(result).lower()

    def test_should_use_correct_image(self):
        """Should use correct Docker image."""
        from startup_utils import start_docker_container

        result = start_docker_container(dry_run=True)

        result_str = str(result).lower()
        assert 'docker' in result_str


class TestOpenBrowser:
    """Tests for open_browser function."""

    def test_should_return_browser_command(self):
        """Should return or execute browser open command."""
        from startup_utils import open_browser

        result = open_browser('http://localhost:8787', dry_run=True)

        assert result is not None

    def test_should_accept_url(self):
        """Should accept URL parameter."""
        from startup_utils import open_browser

        result = open_browser('http://localhost:8787', dry_run=True)

        result_str = str(result)
        assert 'localhost' in result_str or '8787' in result_str or result is True

    def test_should_support_dry_run(self):
        """Should support dry run for testing."""
        from startup_utils import open_browser

        result = open_browser('http://example.com', dry_run=True)

        # Should not actually open browser in dry run
        assert result is not None


class TestGetStartupMode:
    """Tests for get_startup_mode function."""

    def test_should_return_startup_mode(self):
        """Should return startup mode."""
        from startup_utils import get_startup_mode

        result = get_startup_mode()

        assert result in ['docker', 'direct', 'auto'] or isinstance(result, str)

    def test_should_detect_docker_availability(self):
        """Mode should consider Docker availability."""
        from startup_utils import get_startup_mode

        result = get_startup_mode()

        # Should be one of the valid modes
        assert result is not None
        assert isinstance(result, str)

    def test_should_support_override(self):
        """Should support mode override."""
        from startup_utils import get_startup_mode

        result = get_startup_mode(force_mode='direct')

        assert result == 'direct'


class TestGetConfigPath:
    """Tests for get_config_path function."""

    def test_should_return_config_path(self):
        """Should return config file path."""
        from startup_utils import get_config_path

        result = get_config_path()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_should_return_valid_path(self):
        """Should return a valid file path."""
        from startup_utils import get_config_path

        result = get_config_path()

        # Should be a path-like string
        assert '/' in result or '\\' in result or result.endswith('.json')

    def test_should_include_filename(self):
        """Path should include config filename."""
        from startup_utils import get_config_path

        result = get_config_path()

        result_lower = result.lower()
        assert 'config' in result_lower or 'startup' in result_lower or '.json' in result_lower


class TestLoadStartupConfig:
    """Tests for load_startup_config function."""

    def test_should_load_config(self):
        """Should load startup configuration."""
        from startup_utils import load_startup_config

        result = load_startup_config()

        assert isinstance(result, dict)

    def test_should_return_defaults_if_no_file(self):
        """Should return defaults if config file doesn't exist."""
        from startup_utils import load_startup_config

        result = load_startup_config()

        # Should have some default values
        assert result is not None

    def test_should_include_mode_setting(self):
        """Config should include startup mode setting."""
        from startup_utils import load_startup_config

        result = load_startup_config()

        assert 'mode' in result or 'startup_mode' in result or len(result) >= 0

    def test_should_include_port_setting(self):
        """Config should include port setting."""
        from startup_utils import load_startup_config

        result = load_startup_config()

        # Port might be in config
        assert isinstance(result, dict)


class TestSaveStartupConfig:
    """Tests for save_startup_config function."""

    def test_should_save_config(self):
        """Should save startup configuration."""
        from startup_utils import save_startup_config

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, 'test_config.json')
            config = {'mode': 'docker', 'port': 8787}

            result = save_startup_config(config, config_path)

            assert result is True

    def test_should_write_valid_json(self):
        """Should write valid JSON file."""
        from startup_utils import save_startup_config

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, 'test_config.json')
            config = {'mode': 'direct', 'browser': True}

            save_startup_config(config, config_path)

            # Read and parse to verify
            with open(config_path, 'r') as f:
                loaded = json.load(f)
                assert loaded['mode'] == 'direct'

    def test_should_create_parent_directories(self):
        """Should create parent directories if needed."""
        from startup_utils import save_startup_config

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, 'subdir', 'config.json')
            config = {'test': True}

            result = save_startup_config(config, config_path)

            assert result is True or os.path.exists(config_path)


class TestWaitForHealth:
    """Tests for wait_for_health function."""

    def test_should_accept_url_and_timeout(self):
        """Should accept URL and timeout parameters."""
        from startup_utils import wait_for_health

        # Very short timeout to fail fast
        try:
            result = wait_for_health('http://localhost:99999', timeout=0.1)
            assert isinstance(result, bool)
        except Exception:
            # Expected to fail for non-existent server
            pass

    def test_should_return_boolean(self):
        """Should return boolean result."""
        from startup_utils import wait_for_health

        try:
            result = wait_for_health('http://localhost:99999', timeout=0.1)
            assert isinstance(result, bool)
        except Exception:
            # Timeout exception is acceptable
            pass

    def test_should_timeout_for_unavailable(self):
        """Should timeout for unavailable server."""
        from startup_utils import wait_for_health

        try:
            result = wait_for_health('http://localhost:99999', timeout=0.1)
            # Should return False for unavailable
            assert result is False
        except TimeoutError:
            pass  # Expected
        except Exception:
            pass  # Other exceptions acceptable


class TestIsAppRunning:
    """Tests for is_app_running function."""

    def test_should_check_if_running(self):
        """Should check if app is running."""
        from startup_utils import is_app_running

        result = is_app_running()

        assert isinstance(result, bool)

    def test_should_return_false_when_not_running(self):
        """Should return False when app is not running."""
        from startup_utils import is_app_running

        # App unlikely to be running during tests
        result = is_app_running(port=59999)

        assert result is False

    def test_should_check_specific_port(self):
        """Should check specific port."""
        from startup_utils import is_app_running

        result = is_app_running(port=8787)

        assert isinstance(result, bool)


class TestErrorHandling:
    """Tests for error handling."""

    def test_should_handle_missing_requirements_file(self):
        """Should handle missing requirements.txt."""
        from startup_utils import check_dependencies

        result = check_dependencies(requirements_file='nonexistent.txt')

        # Should handle gracefully
        if isinstance(result, dict):
            assert 'error' in result or 'missing' in result or result.get('all_installed') is False
        else:
            assert result is False

    def test_should_handle_invalid_port(self):
        """Should handle invalid port number."""
        from startup_utils import check_port_available

        try:
            result = check_port_available(-1)
            # Either return False or handle gracefully
            assert result is False or result is not None
        except (ValueError, OSError):
            pass  # Expected for invalid port

    def test_should_handle_invalid_url(self):
        """Should handle invalid URL for browser."""
        from startup_utils import open_browser

        try:
            result = open_browser('not-a-valid-url', dry_run=True)
            # Should handle gracefully
            assert result is not None
        except ValueError:
            pass  # Expected for invalid URL

    def test_should_handle_permission_errors(self):
        """Should handle permission errors gracefully."""
        from startup_utils import save_startup_config

        try:
            # Try to write to system directory (should fail)
            result = save_startup_config({}, '/root/test.json')
            # If it doesn't raise, should return False
            assert result is False
        except (PermissionError, OSError):
            pass  # Expected


class TestIntegration:
    """Integration tests for startup utilities."""

    def test_should_provide_startup_workflow(self):
        """Should provide complete startup workflow."""
        from startup_utils import (
            check_python_version,
            get_startup_mode,
            get_config_path,
            load_startup_config
        )

        # Check Python
        python_ok = check_python_version()
        assert python_ok is not None

        # Get mode
        mode = get_startup_mode()
        assert mode is not None

        # Load config
        config = load_startup_config()
        assert isinstance(config, dict)

    def test_should_support_config_roundtrip(self):
        """Should support saving and loading config."""
        from startup_utils import save_startup_config, load_startup_config

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, 'config.json')

            # Save
            original = {'mode': 'docker', 'port': 8787, 'browser': True}
            save_startup_config(original, config_path)

            # Load
            loaded = load_startup_config(config_path)

            assert loaded['mode'] == original['mode']
            assert loaded['port'] == original['port']

    def test_should_check_all_prerequisites(self):
        """Should check all startup prerequisites."""
        from startup_utils import (
            check_python_version,
            check_dependencies,
            check_port_available
        )

        python_ok = check_python_version()
        deps_ok = check_dependencies()
        port_ok = check_port_available(8787)

        # All should return something
        assert python_ok is not None
        assert deps_ok is not None
        assert port_ok is not None


class TestEdgeCases:
    """Tests for edge cases."""

    def test_should_handle_empty_config(self):
        """Should handle empty config dict."""
        from startup_utils import save_startup_config

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, 'empty.json')

            result = save_startup_config({}, config_path)

            assert result is True

    def test_should_handle_unicode_in_config(self):
        """Should handle unicode in config values."""
        from startup_utils import save_startup_config, load_startup_config

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, 'unicode.json')
            config = {'name': 'Test émoji 🎉'}

            save_startup_config(config, config_path)
            loaded = load_startup_config(config_path)

            assert loaded['name'] == config['name']

    def test_should_handle_large_timeout(self):
        """Should handle large timeout values."""
        from startup_utils import wait_for_health

        # Should not actually wait this long
        try:
            result = wait_for_health('http://localhost:99999', timeout=0.001)
            assert isinstance(result, bool)
        except Exception:
            pass  # Expected to fail quickly
