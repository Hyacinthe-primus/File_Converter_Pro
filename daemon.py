"""
File Converter Pro Background Daemon
Runs Watch Folders and Scheduled Tasks without the main application.
Logs to automation/daemon.log. Auto-reloads when automation/*.toml changes.
"""

import logging
import sys
import time
from pathlib import Path

LOG_MAX_LINES = 200

def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

BASE_DIR       = _get_base_dir()
AUTOMATION_DIR = BASE_DIR / "automation"
LOG_FILE       = AUTOMATION_DIR / "daemon.log"
RELOAD_FLAG    = AUTOMATION_DIR / ".reload"
STOP_FLAG      = AUTOMATION_DIR / ".stop"


def _setup_logging() -> None:
    AUTOMATION_DIR.mkdir(exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not any(isinstance(h, logging.FileHandler) for h in root.handlers):
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        root.addHandler(handler)


def _trim_log_if_clean() -> None:
    """Clear the log file if it has no errors and exceeds LOG_MAX_LINES."""
    if not LOG_FILE.exists():
        return
    try:
        lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
        if len(lines) > LOG_MAX_LINES and not any("[ERROR]" in l for l in lines):
            LOG_FILE.write_text("", encoding="utf-8")
    except Exception:
        pass


def set_autostart(enabled: bool, exe_path: str | None = None) -> None:
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        if enabled:
            if exe_path:
                path = exe_path
            elif getattr(sys, "frozen", False):
                path = f'"{sys.executable}" --daemon'
            else:
                path = f'"{sys.executable}" --daemon'
            winreg.SetValueEx(key, "FileConverterProDaemon", 0, winreg.REG_SZ, path)
        else:
            try:
                winreg.DeleteValue(key, "FileConverterProDaemon")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        logging.getLogger(__name__).error("[Daemon] Autostart registry error: %s", e)


def is_autostart_enabled() -> bool:
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run"
        )
        winreg.QueryValueEx(key, "FileConverterProDaemon")
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def run_daemon_mode() -> None:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    import signal

    _setup_logging()
    _trim_log_if_clean()
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    _app = QApplication(sys.argv)

    signal.signal(signal.SIGINT, lambda *_: _app.quit())

    from tasks.watcher   import WatcherManager
    from tasks.scheduler import SchedulerManager
    watcher   = WatcherManager()
    scheduler = SchedulerManager()
    watcher.start()
    scheduler.start()

    last_mtimes = _get_toml_mtimes()

    def _poll():
        nonlocal last_mtimes
        if STOP_FLAG.exists():
            try: STOP_FLAG.unlink()
            except OSError: pass
            watcher.stop()
            scheduler.stop()
            _app.quit()
            return
        if RELOAD_FLAG.exists():
            try: RELOAD_FLAG.unlink()
            except OSError: pass
            watcher.reload(); scheduler.reload()
            last_mtimes = _get_toml_mtimes()
            return
        current = _get_toml_mtimes()
        if current != last_mtimes:
            watcher.reload(); scheduler.reload()
            last_mtimes = current
        _trim_log_if_clean()

    timer = QTimer()
    timer.timeout.connect(_poll)
    timer.start(5000)

    _app.exec()
    watcher.stop()
    scheduler.stop()


def _get_toml_mtimes() -> dict:
    if not AUTOMATION_DIR.is_dir():
        return {}
    return {str(f): f.stat().st_mtime for f in AUTOMATION_DIR.glob("*.toml")}


def main() -> None:
    _setup_logging()
    _trim_log_if_clean()
    logging.getLogger(__name__)

    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))

    from tasks.watcher   import WatcherManager
    from tasks.scheduler import SchedulerManager

    watcher   = WatcherManager()
    scheduler = SchedulerManager()
    watcher.start()
    scheduler.start()

    last_mtimes   = _get_toml_mtimes()
    POLL_INTERVAL = 5
    trim_counter  = 0

    try:
        while True:
            time.sleep(POLL_INTERVAL)
            trim_counter += 1

            if RELOAD_FLAG.exists():
                try:
                    RELOAD_FLAG.unlink()
                except OSError:
                    pass
                watcher.reload()
                scheduler.reload()
                last_mtimes = _get_toml_mtimes()
                continue

            current_mtimes = _get_toml_mtimes()
            if current_mtimes != last_mtimes:
                watcher.reload()
                scheduler.reload()
                last_mtimes = current_mtimes

            if trim_counter >= 60:
                _trim_log_if_clean()
                trim_counter = 0

    except KeyboardInterrupt:
        pass
    finally:
        watcher.stop()
        scheduler.stop()

if __name__ == "__main__":
    main()