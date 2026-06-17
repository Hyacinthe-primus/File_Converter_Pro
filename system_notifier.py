"""
system_notifier.py

Cross-platform system notification manager for File Converter Pro.

Handles native notifications with platform-specific backends:
    - Windows: native toast notifications via winotify
    - Linux / macOS: system tray notifications via QSystemTrayIcon

Features:
    - Native Windows toast notifications (winotify)
    - Cross-platform fallback via Qt system tray
    - FR/EN translations

"""

import os
import platform
import webbrowser


IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    try:
        from winotify import Notification as WinotifyNotification
        WINOTIFY_AVAILABLE = True
    except ImportError:
        WINOTIFY_AVAILABLE = False
        print("[NOTIFIER] ⚠️ winotify not installed — falling back to Qt tray")
else:
    WINOTIFY_AVAILABLE = False

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QAction, QIcon
from app import __version__

def open_url(url: str) -> None:
    webbrowser.open(url)


class QtNotifier:
    """Qt-based system tray notifier (fallback for non-Windows or missing winotify)."""

    def __init__(self) -> None:
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon("icon.png"))
        self.tray.show()

    def notify(self, title: str, message: str) -> None:
        self.tray.showMessage(title, message)

    def notify_with_actions(self, title: str, message: str, actions: list) -> None:
        self.tray.showMessage(title, message)
        menu = QMenu()
        for label, callback in actions:
            action = QAction(label)
            action.triggered.connect(callback)
            menu.addAction(action)
        self.tray.setContextMenu(menu)

try:
    from playsound3 import playsound
    PLAY_SOUND_AVAILABLE = True
except ImportError:
    PLAY_SOUND_AVAILABLE = False
    print("[NOTIFIER] ⚠️ playsound3 not installed")


class SystemNotifier:
    """
    Cross-platform notification manager for File Converter Pro.

    Displays system notifications when:
    - The 'enable_system_notifications' option is enabled in settings
    - The application is in the background or minimized
    - The operation is not excluded (PDF Protection, Optimization)

    Backend selection (automatic):
    - Windows + winotify installed  → native Windows toast (rich, with actions)
    - Otherwise                     → Qt system tray notification
    """

    EXCLUDED_OPERATIONS = [
        "protect_pdf",
        "office_optimization",
        "Protection PDF",
        "Optimisation bureautique",
    ]

    REPO_URL = "https://github.com/Hyacinthe-primus"

    def __init__(self, app_instance=None, language: str = "fr") -> None:
        """
        Args:
            app_instance: Reference to the main FileConverterApp instance
            language: Interface language ("fr" or "en")
        """
        self.app_instance = app_instance
        self.language     = language
        self._tm          = None
        self.app_name     = "File Converter Pro"
        self.app_id       = "FileConverterPro.SystemNotifier"

        self.icon_path  = self._get_resource_path("icon.png")
        self.sound_path = self._get_resource_path(os.path.join("SFX", "notif.mp3"))
        self.toast_icon_path = self.icon_path if os.path.exists(self.icon_path) else ""

        self._qt_notifier = QtNotifier()

        backend = "winotify (Windows)" if (IS_WINDOWS and WINOTIFY_AVAILABLE) else "Qt tray"
        print(f"[NOTIFIER] Initialized — backend: {backend} | "
              f"Icon: {os.path.exists(self.toast_icon_path) if self.toast_icon_path else 'None'}")

    def set_translator(self, tm) -> None:
        """Share the app-wide TranslationManager (includes loaded .lang files)."""
        self._tm = tm
        self._tm.set_language(self.language)

    def set_language(self, language: str) -> None:
        """Sync language."""
        self.language = language
        if self._tm is not None:
            self._tm.set_language(language)

    def _get_resource_path(self, relative_path: str) -> str:
        """Return absolute path to a resource, compatible with dev and PyInstaller."""
        from utils import resource_path
        return resource_path(relative_path)

    def _translate_message(self, task_name: str) -> str:
        """Translate the notification body via the shared TranslationManager."""
        fallback = "Task « {task} » in {app} completed successfully"
        if self._tm is not None:
            template = self._tm.translate_text("notif_task_done_fr")
            if "{task}" not in template:
                template = fallback
        else:
            template = fallback
        return template.format(task=task_name, app=self.app_name)

    def _repo_button_label(self) -> str:
        """Return the GitHub button label via TranslationManager."""
        if self._tm is not None:
            label = self._tm.translate_text("📂 Ouvrir le dépôt GitHub")
            if label != "📂 Ouvrir le dépôt GitHub":
                return label
        return "📂 Open GitHub Repository" if self.language != "fr" else "📂 Ouvrir le dépôt GitHub"

    def _get_task_display_name(self, operation_key: str) -> str:
        """Convert an operation key into a human-readable name for the notification."""
        task_names = {
            "pdf_to_word":      "PDF → Word",
            "word_to_pdf":      "Word → PDF",
            "image_to_pdf":     "Images → PDF",
            "image_to_pdf_s":   "Images → PDF (séparés)",
            "merge_pdf":        "Fusion PDF",
            "merge_word":       "Fusion Word",
            "split_pdf":        "Division PDF",
            "batch_conversion": "Conversion par lot",
            "batch_rename":     "Renommage par lot",
            "file_compression": "Compression de fichiers",
            "txt_to_pdf":       "TXT → PDF",
            "rtf_to_pdf":       "RTF → PDF",
            "txt_to_docx":      "TXT → DOCX",
            "rtf_to_docx":      "RTF → DOCX",
            "csv_to_json":      "CSV → JSON",
            "json_to_csv":      "JSON → CSV",
            "xlsx_to_pdf":      "Excel → PDF",
            "xlsx_to_json":     "Excel → JSON",
            "xlsx_to_csv":      "Excel → CSV",
            "pptx_to_pdf":      "PowerPoint → PDF",
            "html_to_pdf":      "HTML → PDF",
            "pdf_to_html":      "PDF → HTML",
            "epub_to_pdf":      "EPUB → PDF",
            "image_to_png":     "Image → PNG",
            "image_to_jpeg":    "Image → JPEG",
            "image_to_jpg":     "Image → JPG",
            "image_to_bmp":     "Image → BMP",
            "image_to_heic":    "Image → HEIC",
            "image_to_webp":    "Image → WEBP",
            "image_to_tiff":    "Image → TIFF",
            "image_to_psd":     "Image → PSD",
            "image_to_svg":     "Image → SVG",
            "image_to_avif":    "Image → AVIF",
            "image_to_j2k":     "Image → J2K",
            "image_to_dng":     "Image → DNG",
            "image_to_ico":     "Image → ICO",
            "video_to_mp4":     "Vidéo → MP4",
            "video_to_webm":    "Vidéo → WEBM",
            "video_to_mkv":     "Vidéo → MKV",
            "video_to_mov":     "Vidéo → MOV",
            "video_to_avi":     "Vidéo → AVI",
            "video_to_mp3":     "Vidéo → MP3",
            "video_to_wav":     "Vidéo → WAV",
            "video_to_aac":     "Vidéo → AAC",
            "video_to_flac":    "Vidéo → FLAC",
            "audio_to_mp3":     "Audio → MP3",
            "audio_to_wav":     "Audio → WAV",
            "audio_to_aac":     "Audio → AAC",
            "audio_to_ogg":     "Audio → OGG",
            "audio_to_flac":    "Audio → FLAC",
            "audio_to_m4a":     "Audio → M4A",
        }
        fr_key = task_names.get(operation_key, operation_key)
        if self._tm is not None:
            translated = self._tm.translate_text(fr_key)
            if translated != fr_key:
                return translated
        return fr_key

    def _play_sound(self) -> None:
        """Play the notification sound if available."""
        if PLAY_SOUND_AVAILABLE and self.sound_path and os.path.exists(self.sound_path):
            try:
                print(f"[NOTIFIER] 🔊 Playing sound: {self.sound_path}")
                playsound(self.sound_path, block=False)
            except Exception as e:
                print(f"[NOTIFIER] ❌ Sound error: {e}")
        else:
            print("[NOTIFIER] ⚠️ Sound skipped (file missing or playsound3 not installed)")

    # Public API

    def should_notify(self, operation_type: str) -> bool:
        """Return True if this operation should trigger a notification."""
        if not operation_type:
            return False
        return operation_type not in self.EXCLUDED_OPERATIONS

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
            print("[NOTIFIER] ❌ Notifications disabled in settings")
            return False

        if not self.should_notify(operation_type):
            print(f"[NOTIFIER] ⚠️ Excluded operation: {operation_type}")
            return False

        try:
            task_name = self._get_task_display_name(operation_type)
            message   = self._translate_message(task_name)

            print(f"[NOTIFIER] 📤 Sending notification: {operation_type} → '{message}'")

            icon_to_use = ""
            if self.toast_icon_path and os.path.exists(self.toast_icon_path):
                icon_to_use = self.toast_icon_path
                print(f"[NOTIFIER] 🖼️ Icon used: {icon_to_use}")
            else:
                print("[NOTIFIER] ⚠️ No icon available")

            if IS_WINDOWS and WINOTIFY_AVAILABLE:
                toast = WinotifyNotification(
                    app_id=self.app_id,
                    title=self.app_name,
                    msg=message,
                    duration="short",
                    icon=icon_to_use,
                )
                toast.add_actions(
                    label=self._repo_button_label(),
                    launch=self.REPO_URL,
                )
                toast.show()
            else:
                self._qt_notifier.notify_with_actions(
                    title=self.app_name,
                    message=message,
                    actions=[
                        (self._repo_button_label(), lambda: open_url(self.REPO_URL)),
                    ],
                )

            self._play_sound()
            return True

        except Exception as e:
            print(f"[NOTIFIER] 💥 CRITICAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False

    def send_custom(
        self,
        title: str,
        message: str,
        operation_type: str | None = None,
        duration: str = "short",
    ) -> bool:
        """Send a custom notification (for advanced use)."""
        if operation_type and not self.should_notify(operation_type):
            return False

        try:
            if IS_WINDOWS and WINOTIFY_AVAILABLE:
                toast = WinotifyNotification(
                    app_id=self.app_id,
                    title=title,
                    msg=message,
                    duration=duration,
                    icon=self.toast_icon_path if self.toast_icon_path and os.path.exists(self.toast_icon_path) else "",
                )
                toast.add_actions(
                    label=self._repo_button_label(),
                    launch=self.REPO_URL,
                )
                toast.show()
            else:
                self._qt_notifier.notify_with_actions(
                    title=title,
                    message=message,
                    actions=[
                        (self._repo_button_label(), lambda: open_url(self.REPO_URL)),
                    ],
                )

            self._play_sound()
            return True

        except Exception as e:
            print(f"[NOTIFIER] Custom notification error: {e}")
            return False
    
    def check_and_notify_update(self) -> bool:
        """Check GitHub releases and notify if a newer version is available."""
        try:
            import requests

            resp = requests.get(
                "https://api.github.com/repos/Hyacinthe-primus/File_Converter_Pro/releases/latest",
                timeout=5,
            )
            latest = resp.json()["tag_name"].lstrip("v")
            current = __version__.lstrip("v")

            if latest == current:
                print(f"[NOTIFIER] Up to date ({current})")
                return False

            print(f"[NOTIFIER] 🆕 Update available: {current} → {latest}")

            release_url = "https://github.com/Hyacinthe-primus/File_Converter_Pro/releases/latest"
            title   = "File Converter Pro — Update Available"
            message = f"Version {latest} is available. You're on {current}"

            if IS_WINDOWS and WINOTIFY_AVAILABLE:
                toast = WinotifyNotification(
                    app_id=self.app_id,
                    title=title,
                    msg=message,
                    duration="long",
                    icon=self.toast_icon_path if os.path.exists(self.toast_icon_path) else "",
                )
                toast.add_actions(label="⬇️ Download", launch=release_url)
                toast.show()
            else:
                self._qt_notifier.notify_with_actions(
                    title=title,
                    message=message,
                    actions=[("⬇️ Download", lambda: open_url(release_url))],
                )

            self._play_sound()
            return True

        except Exception as e:
            print(f"[NOTIFIER] ❌ Update check failed: {e}")
            return False