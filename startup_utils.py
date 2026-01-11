"""Run.bat One-Click Startup Utilities (Issue #231)"""

import json, os, socket, subprocess, sys, time, urllib.request, urllib.error  # nosec B404


def check_python_version(minimum='3.11'):
    """Check if Python version meets minimum requirement."""
    c, mp = sys.version_info, [int(p) for p in minimum.split('.')]
    v, ok = f"{c.major}.{c.minor}.{c.micro}", (c.major, c.minor) >= tuple(mp)
    return {'valid': ok, 'ok': ok, 'version': v, 'python_version': v, 'minimum': minimum}


def check_dependencies(requirements_file='requirements.txt'):
    """Check if dependencies from requirements.txt are installed."""
    if not os.path.exists(requirements_file):
        return {'all_installed': False, 'missing': [], 'error': f'Requirements file not found: {requirements_file}'}
    try:
        lines = open(requirements_file).readlines()
    except IOError:  # pragma: no cover
        return {'all_installed': False, 'missing': [], 'error': 'Cannot read file'}
    missing = []
    for line in [l.strip() for l in lines if l.strip() and not l.strip().startswith('#')]:
        pkg = line.split('==')[0].split('>=')[0].split('<=')[0].split('[')[0].strip()
        if pkg:
            try:
                __import__(pkg.replace('-', '_'))
            except ImportError:
                missing.append(pkg)
    return {'all_installed': not missing, 'missing': missing}


def check_docker_available():
    """Check if Docker is available and running."""
    try:
        installed = subprocess.run(['docker', '--version'], capture_output=True, timeout=5).returncode == 0  # nosec B603 B607
        running = installed and subprocess.run(['docker', 'info'], capture_output=True, timeout=10).returncode == 0  # nosec B603 B607
        return {'available': running, 'installed': installed, 'running': running}
    except Exception:  # pragma: no cover
        return {'available': False, 'installed': False, 'running': False}


def check_port_available(port):
    """Check if a port is available for use."""
    if not (0 <= port <= 65535):
        return False
    if port == 0:
        return True
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(('127.0.0.1', port)) != 0
    except Exception:  # pragma: no cover
        return False


def start_application(dry_run=False):
    """Start the Flask application."""
    cmd = 'python -m flask run --host=0.0.0.0 --port=8787'
    res = {'command': cmd, 'action': 'start_flask', 'app': 'AutomatedPastor'}
    if not dry_run:  # pragma: no cover
        try:
            subprocess.Popen(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # nosec B603
            res['started'] = True
        except Exception as e:
            res['started'], res['error'] = False, str(e)
    return res


def start_docker_container(dry_run=False):
    """Start the application via Docker."""
    cmd = 'docker run -d -p 8787:8787 automated-pastor'
    res = {'command': cmd, 'docker': True, 'port': 8787}
    if not dry_run:  # pragma: no cover
        try:
            r = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=30)  # nosec B603
            res['started'], res['container_id'] = r.returncode == 0, r.stdout.strip() if r.returncode == 0 else None
        except Exception as e:
            res['started'], res['error'] = False, str(e)
    return res


def open_browser(url, dry_run=False):
    """Open browser to specified URL."""
    res = {'url': url, 'action': 'open_browser', 'localhost': 'localhost' in url, '8787': '8787' in url}
    if dry_run:
        return res
    try:  # pragma: no cover
        import webbrowser
        webbrowser.open(url)
        return True
    except Exception:  # pragma: no cover
        return False


def get_startup_mode(force_mode=None):
    """Determine startup mode (docker or direct)."""
    return force_mode if force_mode else ('docker' if check_docker_available().get('available') else 'direct')


def get_config_path():
    """Get path to startup configuration file."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'startup_config.json')


def load_startup_config(config_path=None):
    """Load startup configuration from file."""
    path, d = config_path or get_config_path(), {'mode': 'auto', 'startup_mode': 'auto', 'port': 8787, 'browser': True}
    if os.path.exists(path):
        try:
            d.update(json.load(open(path, encoding='utf-8')))
        except Exception:  # pragma: no cover  # nosec B110
            pass
    return d


def save_startup_config(config, config_path=None):
    """Save startup configuration to file."""
    path = config_path or get_config_path()
    try:
        p = os.path.dirname(path)
        if p and not os.path.exists(p):
            os.makedirs(p)
        json.dump(config, open(path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def wait_for_health(url, timeout=30):
    """Wait for application to become healthy."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            if urllib.request.urlopen(urllib.request.Request(url, method='GET'), timeout=2).status == 200:  # nosec B310
                return True  # pragma: no cover
        except Exception:  # nosec B110
            pass
        time.sleep(0.1)
    return False


def is_app_running(port=8787):
    """Check if the application is running on specified port."""
    return not check_port_available(port)
