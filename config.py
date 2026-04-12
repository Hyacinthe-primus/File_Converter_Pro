"""
Configuration Manager - File Converter Pro

Handles application settings, system theme detection, and secure storage.

Key Features:
    - Windows Dark Mode detection via Registry
    - Encrypted configuration storage using Fernet (cryptography)
    - User preferences management (language, theme, paths, notifications)
    - Secure key generation and management for sensitive data

Author: Hyacinthe
Version: 1.0
"""

import os
import json
try:
    import winreg
except ImportError:
    winreg = None
from cryptography.fernet import Fernet
import subprocess
import sys

# Constants

CONFIG_FILE = "file_converter_config.dat"
KEY_FILE    = "file_converter_key.key"

DEFAULT_CONFIG: dict = {
    "dark_mode":                  False,
    # NOTE: "language" is intentionally absent from defaults.
    # Absence means "fresh install — let the caller decide the language"
    "last_project":               None,
    "auto_open_last_project":     False,
    "conversion_quality":         "standard",
    "default_output_folder":      None,
    "enable_notifications":       True,
    "compression_level":          "normal",
    "accepted_terms":             False,
    "accepted_privacy":           False,
    "terms_acceptance_timestamp": None,
    "enable_system_notifications": True,
    "show_file_previews":         True,
    "backup_before_conversion":   False,
    "pdf_to_word_mode":           "with_images",
    "show_dashboard_on_startup":  False,
    "keep_history_days":          365,
    "auto_save_templates":        True,
    "separate_image_pdfs":        False,
    "use_system_theme":           True,
}

from PySide6.QtWidgets import QApplication

def is_dark_mode_qt():
    app = QApplication.instance()
    if not app:
        return False

    palette = app.palette()
    return palette.color(palette.Window).lightness() < 128

def is_dark_mode():
    """
    Detect whether OS is currently using dark mode.
    Returns False if the registry key is unavailable.
    """
    if sys.platform == "win32":
        return is_windows_dark_mode()
    elif sys.platform.startswith("linux"):
        return is_linux_dark_mode()
    return False

# System utilities (Linux-only)

def is_linux_dark_mode():
    try:
        result = subprocess.check_output([
            "gsettings",
            "get",
            "org.gnome.desktop.interface",
            "color-scheme"
        ]).decode().strip()

        return result == "'prefer-dark'"
    except Exception:
        return False

# System utilities (Windows-only)

def is_windows_dark_mode() -> bool:
    """
    Detect whether Windows is currently using dark mode.
    Returns False on non-Windows systems or if the registry key is unavailable.
    """
    try:
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        key = winreg.OpenKey(
            registry,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return value == 0
    except Exception:
        return False

def _load_or_create_key(key_file: str) -> bytes | None:
    """Load an existing Fernet key or generate and persist a new one."""
    try:
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()

        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)
        return key

    except Exception as e:
        print(f"Error managing encryption key: {e}")
        return None

def _build_cipher(key_file: str) -> Fernet | None:
    """Return a Fernet cipher suite, or None if key loading fails."""
    key = _load_or_create_key(key_file)
    return Fernet(key) if key else None

def _decrypt_config(path: str, cipher: Fernet) -> dict:
    """Read and decrypt an encrypted config file."""
    with open(path, "rb") as f:
        encrypted = f.read()
    decrypted = cipher.decrypt(encrypted)
    return json.loads(decrypted.decode("utf-8"))

def _read_plain_config(path: str) -> dict:
    """Read a plain-text JSON config file (fallback when cipher is unavailable)."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _encrypt_and_write(path: str, data: dict, cipher: Fernet) -> None:
    """Serialize *data* to JSON, encrypt it, and write to *path*."""
    raw = json.dumps(data, indent=4, ensure_ascii=False).encode("utf-8")
    with open(path, "wb") as f:
        f.write(cipher.encrypt(raw))

def _write_plain_config(path: str, data: dict) -> None:
    """Write *data* as plain-text JSON to *path* (fallback)."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


class ConfigManager:
    """Load, save, and manage user preferences for File Converter Pro."""

    def __init__(
        self,
        config_file: str = CONFIG_FILE,
        key_file: str    = KEY_FILE,
    ) -> None:
        self.config_file    = config_file
        self.key_file       = key_file
        self.default_config = DEFAULT_CONFIG.copy()
        self.cipher_suite   = _build_cipher(self.key_file)

    def load_config(self) -> dict:
        """
        Load configuration from disk.
        - First launch: returns defaults with the system theme applied.
        - Subsequent launches: merges saved values over defaults.
        """
        try:
            if os.path.exists(self.config_file):
                saved = self._read_config()
                return {**self.default_config, **saved}

            return self._first_launch_defaults()

        except Exception as e:
            print(f"Error loading config: {e}")
            return self.default_config.copy()

    def save_config(self, config: dict) -> bool:
        """Persist *config* to disk (encrypted when possible)."""
        try:
            if self.cipher_suite:
                _encrypt_and_write(self.config_file, config, self.cipher_suite)
            else:
                _write_plain_config(self.config_file, config)
            return True

        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def _read_config(self) -> dict:
        """
        Dispatch to the appropriate reader based on cipher availability.

        Falls back to plain-text JSON when decryption fails — this covers
        the case where the installer wrote a minimal plain-text config
        (containing just {"language": "en/fr"}) before the app was ever
        launched. On the next save_config() call the file will be
        transparently re-written in encrypted form.
        """
        if self.cipher_suite:
            try:
                return _decrypt_config(self.config_file, self.cipher_suite)
            except Exception:
                # File is plain-text (e.g. written by the Inno Setup installer
                # on first install before the app was launched for the first time).
                return _read_plain_config(self.config_file)
        return _read_plain_config(self.config_file)

    def _first_launch_defaults(self) -> dict:
        """Build the default config with the system theme pre-applied.
        Language is NOT set here — AppBootstrap applies it after parsing
        the CLI flag (--fr / --en / --lang <code> from installer)."""
        defaults = self.default_config.copy()
        defaults["dark_mode"] = is_windows_dark_mode()
        return defaults