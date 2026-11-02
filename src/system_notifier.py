"""
system_notifier.py

Cross-platform system notification manager for File Converter Pro.

Handles native notifications with platform-specific backends:
    - Windows: native toast notifications through a fixed PowerShell script
    - Linux / macOS: system tray notifications via QSystemTrayIcon

Features:
    - Native Windows toast notifications with structured XML/data payloads
    - Cross-platform fallback via Qt system tray
    - FR/EN translations

"""

import base64
import json
import os
import platform
import re
import webbrowser
import xml.etree.ElementTree as ET
from importlib.util import find_spec

IS_WINDOWS = platform.system() == "Windows"
WINOTIFY_AVAILABLE = IS_WINDOWS and find_spec("winotify") is not None

_TOAST_ENV_VAR = "FCP_TOAST_PAYLOAD"
_NOTIF_PLACEHOLDER_RE = re.compile(r"\{(task|app)\}")
_TOAST_PS_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$payloadText = $env:FCP_TOAST_PAYLOAD
if ([string]::IsNullOrEmpty($payloadText)) { exit 1 }
$data = $payloadText | ConvertFrom-Json
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
[Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml([string]$data.xml)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
$toast.Tag = [string]$data.tag
$toast.Group = [string]$data.group
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier([string]$data.app_id)
$notifier.Show($toast)
"""


def _build_toast_xml(
    title: str,
    message: str,
    action_label: str,
    action_url: str,
    icon: str,
    duration: str,
) -> str:
    if duration not in ("short", "long"):
        raise ValueError("Duration is not 'short' or 'long'")

    toast = ET.Element("toast", {"duration": duration})
    visual = ET.SubElement(toast, "visual")
    binding = ET.SubElement(visual, "binding", {"template": "ToastImageAndText02"})
    ET.SubElement(binding, "image", {"id": "1", "src": icon})
    title_node = ET.SubElement(binding, "text", {"id": "1"})
    title_node.text = title
    message_node = ET.SubElement(binding, "text", {"id": "2"})
    message_node.text = message
    actions = ET.SubElement(toast, "actions")
    ET.SubElement(
        actions,
        "action",
        {
            "activationType": "protocol",
            "content": action_label,
            "arguments": action_url,
        },
    )
    ET.SubElement(toast, "audio", {"silent": "true"})
    return ET.tostring(toast, encoding="unicode")


def _build_toast_payload(
    app_id: str,
    title: str,
    message: str,
    action_label: str,
    action_url: str,
    icon: str,
    duration: str,
) -> dict:
    return {
        "xml": _build_toast_xml(title, message, action_label, action_url, icon, duration),
        "app_id": app_id,
        "tag": title,
        "group": app_id,
    }


def _encode_ps_command(script: str) -> str:
    return base64.b64encode(script.encode("utf-16-le")).decode("ascii")


def _build_ps_invocation(payload: dict) -> tuple[list[str], dict]:
    env = os.environ.copy()
    env[_TOAST_ENV_VAR] = json.dumps(payload, ensure_ascii=True)
    command = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-EncodedCommand",
        _encode_ps_command(_TOAST_PS_SCRIPT),
    ]
    return command, env


def _compare_versions(a: str, b: str) -> int:
    """Compare two dotted version strings numerically.

    Returns negative if a < b, 0 if equal, positive if a > b.
    Non-numeric segments (e.g. "1.0.8-rc1") are ignored for ordering.
    """
    a_parts = [int(p) for p in re.findall(r"\d+", a)]
    b_parts = [int(p) for p in re.findall(r"\d+", b)]
    for x, y in zip(a_parts, b_parts):
        if x != y:
            return -1 if x < y else 1
    return (len(a_parts) > len(b_parts)) - (len(a_parts) < len(b_parts))

if IS_WINDOWS and not WINOTIFY_AVAILABLE:
    print("[NOTIFIER] winotify not installed — falling back to Qt tray")


def _run_windows_toast(payload: dict) -> None:
    import subprocess

    command, env = _build_ps_invocation(payload)
    startupinfo = None
    if hasattr(subprocess, "STARTUPINFO"):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startupinfo,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        env=env,
    )


from PySide6.QtCore import QObject, Signal  # noqa: E402
from PySide6.QtGui import QAction, QIcon  # noqa: E402
from PySide6.QtWidgets import QMenu, QSystemTrayIcon  # noqa: E402


def open_url(url: str) -> None:
    webbrowser.open(url)


class QtNotifier:
    """Qt-based system tray notifier (fallback for non-Windows or missing winotify)."""

    def __init__(self) -> None:
        self.tray = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon()
            from utils import resource_path
            self.tray.setIcon(QIcon(resource_path(os.path.join("Assets", "icon.png"))))
            self.tray.show()
        else:
            print("[NOTIFIER] No system tray available — desktop notifications disabled")

    def notify_with_actions(self, title: str, message: str, actions: list) -> None:
        if self.tray is None:
            return
        self.tray.showMessage(title, message)
        menu = QMenu()
        for label, callback in actions:
            action = QAction(label)
            action.triggered.connect(callback)
            menu.addAction(action)
        self.tray.setContextMenu(menu)


class _NotifierBridge(QObject):
    """Forwards notification requests from worker threads to the Qt main thread."""

    notify_request = Signal(str, str, str, str, str)  # title, message, action_label, action_url, duration
    update_available = Signal(str, str, str)  # title, message, release_url


try:
    from utils.subprocess_console import suppress_console_for

    # playsound3 probes every backend at import time (Ffplay.check runs
    # "ffplay -version"), which flashes a console window in the GUI build.
    suppress_console_for("ffplay")

    from playsound3 import playsound

    PLAY_SOUND_AVAILABLE = True
except ImportError:
    PLAY_SOUND_AVAILABLE = False
    print("[NOTIFIER] playsound3 not installed")


class SystemNotifier:
    """
    Cross-platform notification manager for File Converter Pro.

    Displays system notifications when:
    - The 'enable_system_notifications' option is enabled in settings
    - The application is in the background or minimized
    - The operation is not excluded (PDF Protection, Optimization)

    Backend selection (automatic):
    - Windows + winotify installed  → native Windows toast through a fixed
      PowerShell script with notification values supplied as structured data
    - Otherwise                     → Qt system tray notification
    """

    EXCLUDED_OPERATIONS = {
        "protect_pdf",
        "office_optimization",
    }
    LEGACY_EXCLUDED_OPERATIONS = {
        "Protection PDF": "protect_pdf",
        "Optimisation bureautique": "office_optimization",
    }

    REPO_URL = "https://github.com/Hyacinthe-primus"

    def __init__(self, app_instance=None, language: str = "fr") -> None:
        """
        Args:
            app_instance: Reference to the main FileConverterApp instance
            language: Interface language ("fr" or "en")
        """
        self.app_instance = app_instance
        self.language = language
        self._tm = None
        self._fallback_tm = None
        self.app_name = "File Converter Pro"
        self.app_id = "FileConverterPro.SystemNotifier"

        self.icon_path = self._get_resource_path(os.path.join("Assets", "icon.png"))
        self.sound_path = self._get_resource_path(os.path.join("SFX", "notif.mp3"))
        self.toast_icon_path = self.icon_path if os.path.exists(self.icon_path) else ""

        self._qt_notifier = QtNotifier()
        self._bridge = _NotifierBridge()
        self._bridge.notify_request.connect(self._show_notification)
        self._bridge.update_available.connect(self._show_update_notification)

        backend = "Windows toast (PowerShell)" if (IS_WINDOWS and WINOTIFY_AVAILABLE) else "Qt tray"
        print(
            f"[NOTIFIER] Initialized — backend: {backend} | "
            f"Icon: {os.path.exists(self.toast_icon_path) if self.toast_icon_path else 'None'}"
        )

    def set_translator(self, tm) -> None:
        """Share the app-wide TranslationManager (includes loaded .lang files)."""
        self._tm = tm
        self._tm.set_language(self.language)

    def set_language(self, language: str) -> None:
        """Sync language."""
        self.language = language
        if self._tm is not None:
            self._tm.set_language(language)
        fallback = getattr(self, "_fallback_tm", None)
        if fallback is not None:
            fallback.set_language(language)

    def _translation_manager(self):
        if self._tm is not None:
            return self._tm
        fallback = getattr(self, "_fallback_tm", None)
        if fallback is None:
            from translations import TranslationManager

            fallback = TranslationManager()
            fallback.set_language(self.language)
            self._fallback_tm = fallback
        return fallback

    def _get_resource_path(self, relative_path: str) -> str:
        """Return absolute path to a resource, compatible with dev and PyInstaller."""
        from utils import resource_path

        return resource_path(relative_path)

    def _translate_message(self, task_name: str) -> str:
        """Translate the notification body via the shared TranslationManager."""
        fallback = "Task « {task} » in {app} completed successfully"
        template = fallback
        candidate = self._translation_manager().translate_text("notif_task_done_fr")
        if isinstance(candidate, str) and "{task}" in candidate:
            template = candidate

        def replace(match):
            return task_name if match.group(1) == "task" else self.app_name

        return _NOTIF_PLACEHOLDER_RE.sub(replace, template)

    def _repo_button_label(self) -> str:
        """Return the GitHub button label via TranslationManager."""
        label = self._translation_manager().translate_text("open_github_repository")
        if isinstance(label, str) and label.strip() and label != "open_github_repository":
            return label
        return "📂 Open GitHub Repository"

    def _get_task_display_name(self, operation_key: str) -> str:
        """Convert an operation key into a human-readable name for the notification."""
        task_names = {
            "pdf_to_word": "pdf_to_word_2",
            "word_to_pdf": "word_to_pdf_2",
            "image_to_pdf": "images_to_pdf_3",
            "image_to_pdf_s": "images_to_pdf_separate",
            "merge_pdf": "pdf_merge",
            "merge_word": "word_merge",
            "split_pdf": "pdf_split",
            "batch_conversion": "batch_conversion_2",
            "batch_rename": "batch_renaming",
            "file_compression": "file_compression",
            "txt_to_pdf": "TXT → PDF",
            "rtf_to_pdf": "RTF → PDF",
            "txt_to_docx": "TXT → DOCX",
            "rtf_to_docx": "RTF → DOCX",
            "csv_to_json": "CSV → JSON",
            "json_to_csv": "JSON → CSV",
            "xlsx_to_pdf": "Excel → PDF",
            "xlsx_to_json": "Excel → JSON",
            "xlsx_to_csv": "Excel → CSV",
            "pptx_to_pdf": "PowerPoint → PDF",
            "markdown_to_html": "Markdown → HTML",
            "html_to_pdf": "HTML → PDF",
            "pdf_to_html": "PDF → HTML",
            "epub_to_pdf": "EPUB → PDF",
            "odt_to_docx": "ODT → DOCX",
            "ods_to_xlsx": "ODS → XLSX",
            "odp_to_pptx": "ODP → PPTX",
            "odt_to_pdf": "ODT → PDF",
            "ods_to_pdf": "ODS → PDF",
            "odp_to_pdf": "ODP → PDF",
            "image_to_png": "Image → PNG",
            "image_to_jpeg": "Image → JPEG",
            "image_to_jpg": "Image → JPG",
            "image_to_bmp": "Image → BMP",
            "image_to_heic": "Image → HEIC",
            "image_to_webp": "Image → WEBP",
            "image_to_tiff": "Image → TIFF",
            "image_to_psd": "Image → PSD",
            "image_to_svg": "Image → SVG",
            "image_to_avif": "Image → AVIF",
            "image_to_j2k": "Image → J2K",
            "image_to_dng": "Image → DNG",
            "image_to_ico": "Image → ICO",
        }
        tm = self._translation_manager()
        key = task_names.get(operation_key, operation_key)
        translated = tm.translate_text(key)
        if isinstance(translated, str) and translated != key:
            return translated
        if operation_key in task_names:
            return key

        if operation_key.startswith(("video_to_", "audio_to_")):
            source, target = operation_key.split("_to_", 1)
            source_label = tm.translate_text(source)
            if not isinstance(source_label, str) or source_label == source:
                source_label = source.upper()
            return f"{source_label} → {target.upper()}"

        translated = tm.translate_operation_type(operation_key)
        if isinstance(translated, str) and translated:
            return translated
        return operation_key

    def _play_sound(self) -> None:
        """Play the notification sound if available."""
        if PLAY_SOUND_AVAILABLE and self.sound_path and os.path.exists(self.sound_path):
            try:
                print(f"[NOTIFIER] Playing sound: {self.sound_path}")
                playsound(self.sound_path, block=False)
            except Exception as e:
                print(f"[NOTIFIER] Sound error: {e}")
        else:
            print("[NOTIFIER] Sound skipped (file missing or playsound3 not installed)")

    # Public API

    def should_notify(self, operation_type: str) -> bool:
        """Return True if this operation should trigger a notification."""
        if not operation_type:
            return False
        operation = self.LEGACY_EXCLUDED_OPERATIONS.get(operation_type, operation_type)
        return operation not in self.EXCLUDED_OPERATIONS

    def send(self, operation_type: str, config_enabled: bool = True) -> bool:
        """
        Send a system notification for a completed operation.

        Args:
            operation_type: Operation key (e.g. "pdf_to_word")
            config_enabled: Value of 'enable_system_notifications' from settings

        Returns:
            True if the notification was sent, False otherwise.
        """
        if not config_enabled:
            print("[NOTIFIER] Notifications disabled in settings")
            return False

        if not self.should_notify(operation_type):
            print(f"[NOTIFIER] Excluded operation: {operation_type}")
            return False

        try:
            task_name = self._get_task_display_name(operation_type)
            message = self._translate_message(task_name)
            print(f"[NOTIFIER] Sending notification: {operation_type} → '{message}'")

            self._bridge.notify_request.emit(
                self.app_name,
                message,
                self._repo_button_label(),
                self.REPO_URL,
                "short",
            )
            self._play_sound()
            return True

        except Exception as e:
            print(f"[NOTIFIER] CRITICAL ERROR: {e}")
            import traceback

            traceback.print_exc()
            return False

    def check_and_notify_update(self) -> bool:
        """Check GitHub releases in the background; show the result on the Qt main thread."""
        try:
            import requests

            resp = requests.get(
                "https://api.github.com/repos/Hyacinthe-primus/File_Converter_Pro/releases/latest",
                timeout=5,
            )
            latest = resp.json()["tag_name"].lstrip("v")
            from app import __version__

            current = __version__.lstrip("v")

            if _compare_versions(current, latest) >= 0:
                if _compare_versions(current, latest) > 0:
                    print(f"[NOTIFIER] Up to date ({current}) - ahead of GitHub version {latest}")
                else:
                    print(f"[NOTIFIER] Up to date ({current})")
                return False

            print(f"[NOTIFIER] Update available: {current} → {latest}")

            release_url = "https://github.com/Hyacinthe-primus/File_Converter_Pro/releases/latest"
            title = "File Converter Pro - Update Available"
            message = f"Version {latest} is available. You're on {current}"
            self._bridge.update_available.emit(title, message, release_url)
            return True

        except Exception as e:
            print(f"[NOTIFIER] ❌ Update check failed: {e}")
            return False

    def _show_notification(self, title: str, message: str, action_label: str, action_url: str, duration: str) -> None:
        """Runs on the Qt main thread — safe to touch the tray here."""
        try:
            icon = getattr(self, "toast_icon_path", "") or ""
            if icon and not os.path.exists(icon):
                icon = ""
            if IS_WINDOWS and WINOTIFY_AVAILABLE:
                payload = _build_toast_payload(
                    self.app_id,
                    title,
                    message,
                    action_label,
                    action_url,
                    icon,
                    duration,
                )
                _run_windows_toast(payload)
            else:
                self._qt_notifier.notify_with_actions(
                    title=title,
                    message=message,
                    actions=[(action_label, lambda: open_url(action_url))],
                )
        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"[NOTIFIER] Notification error: {e}")

    def _show_update_notification(self, title: str, message: str, release_url: str) -> None:
        """Runs on the Qt main thread — safe to touch the tray here."""
        self._show_notification(title, message, "⬇️ Download", release_url, "long")
        self._play_sound()
