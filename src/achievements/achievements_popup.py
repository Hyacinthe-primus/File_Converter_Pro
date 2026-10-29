"""
Achievements Popup

"""

import os
import sys

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QDialog, QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QVBoxLayout

from utils import SRC_DIR

_ROOT_DIR = str(SRC_DIR)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)
from translations import TranslationManager
from utils.translation_mixin import TranslationMixin

from .theme import get_achievements_palette, load_achievements_qss, resolve_theme_name


class AchievementPopup(TranslationMixin, QDialog):
    """Achievement acquisition popup"""

    finished_display = Signal()

    def __init__(self, achievement, achievement_system, parent=None, language="fr"):
        super().__init__(parent)
        self.achievement = achievement
        self.achievement_system = achievement_system
        self.language = language
        self._tm = TranslationManager()
        self._tm.set_language(language)
        self.dark_mode = True
        parent = self.parent()
        if hasattr(parent, "dark_mode"):
            self.dark_mode = parent.dark_mode
        elif hasattr(parent, "config") and "dark_mode" in parent.config:
            self.dark_mode = parent.config.get("dark_mode", True)
        self._theme = resolve_theme_name(parent, self.dark_mode)
        self._palette = get_achievements_palette(self._theme, self.dark_mode)

    def set_translator(self, tm) -> None:
        """Share the app-wide TranslationManager, then build the UI."""
        self._tm = tm
        self._tm.set_language(self.language)
        self.setup_ui()
        self.setup_animations()
        self.play_sound()
        self.apply_theme_style()

    def setup_ui(self):
        """Configure the interface"""
        self.setObjectName("AchievementPopup")
        self.setFixedWidth(400)
        self.setSizeGripEnabled(False)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame()
        container.setObjectName("AchievementPopupContainer")
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(15)

        # Icon
        icon_path = self.achievement_system.get_achievement_icon_path(self.achievement["icon"])
        icon_label = QLabel()
        icon_label.setObjectName("AchievementPopupIcon")
        icon_label.setAttribute(Qt.WA_TranslucentBackground)

        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                if pixmap.hasAlphaChannel():
                    scaled = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                else:
                    scaled = pixmap.toImage().convertToFormat(QImage.Format_ARGB32)
                    scaled = QPixmap.fromImage(scaled).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label.setPixmap(scaled)
        else:
            icon_label.setText("🏆")

        container_layout.addWidget(icon_label)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(5)

        title_text = self.translate_text("achievement_unlocked")
        title_label = QLabel(f"🏆 {title_text} 🏆")
        title_label.setObjectName("AchievementPopupTitle")
        content_layout.addWidget(title_label)

        _raw_name = self.achievement["name"]
        if isinstance(_raw_name, str):
            name = self._tm.translate_text(_raw_name)
        else:
            name = _raw_name.get(self.language, _raw_name.get("fr", ""))
        name_label = QLabel(name)
        name_label.setObjectName("AchievementPopupName")
        name_label.setWordWrap(True)
        content_layout.addWidget(name_label)

        _raw_desc = self.achievement["description"]
        if isinstance(_raw_desc, str):
            description = self._tm.translate_text(_raw_desc)
        else:
            description = _raw_desc.get(self.language, _raw_desc.get("fr", ""))
        desc_label = QLabel(description)
        desc_label.setObjectName("AchievementPopupDesc")
        desc_label.setWordWrap(True)
        content_layout.addWidget(desc_label)

        reward_layout = QHBoxLayout()
        reward_layout.addStretch()

        xp_label = QLabel(f"+{self.achievement['reward_xp']} XP")
        xp_label.setObjectName("AchievementPopupXP")
        reward_layout.addWidget(xp_label)

        content_layout.addLayout(reward_layout)
        container_layout.addLayout(content_layout, 1)

        layout.addWidget(container)

        self.adjustSize()
        min_height = 120
        max_height = 180
        self.setFixedHeight(max(min_height, min(self.sizeHint().height(), max_height)))

        screen_geometry = self.screen().availableGeometry()
        self.move(screen_geometry.width() - self.width() - 20, 50)

    def apply_theme_style(self):
        """Apply the theme's achievements stylesheet."""
        self.setStyleSheet(load_achievements_qss(self._theme))

    def setup_animations(self):
        """Configure animations"""

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self.enter_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.enter_animation.setDuration(500)
        self.enter_animation.setStartValue(0.0)
        self.enter_animation.setEndValue(1.0)
        self.enter_animation.setEasingCurve(QEasingCurve.OutCubic)

        self.exit_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.exit_animation.setDuration(500)
        self.exit_animation.setStartValue(1.0)
        self.exit_animation.setEndValue(0.0)
        self.exit_animation.setEasingCurve(QEasingCurve.InCubic)

        self.show()
        self.enter_animation.start()

        QTimer.singleShot(6500, self.hide_popup)

    def play_sound(self):
        """Play achievement sound"""
        try:
            sound_file = self.achievement_system.get_sound_path(
                self.achievement_system.get_achievement_sound(self.achievement["id"])
            )

            print(f"Attempting to play sound: {sound_file}")

            if sound_file and os.path.exists(sound_file):
                print(f"Sound file found: {sound_file}")

                from PySide6.QtCore import QUrl
                from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

                self.media_player = QMediaPlayer()
                self.audio_output = QAudioOutput()
                self.media_player.setAudioOutput(self.audio_output)

                self.audio_output.setVolume(0.7)

                url = QUrl.fromLocalFile(sound_file)
                print(f"URL created: {url.toString()}")

                self.media_player.setSource(url)

                self.media_player.errorOccurred.connect(self.handle_player_error)
                self.media_player.mediaStatusChanged.connect(self.handle_media_status)
                self.media_player.playbackStateChanged.connect(self.handle_playback_state)

                self.media_player.play()

                print("Sound sent for playback")

            else:
                print(f"Sound file NOT found or empty path: {sound_file}")

        except Exception as e:
            print(f"Achievement sound playback error: {e}")
            import traceback

            traceback.print_exc()

    def handle_player_error(self, error):
        """Handle player errors"""
        print(f"MediaPlayer error: {error}")
        print(f"Error message: {self.media_player.errorString()}")

    def handle_media_status(self, status):
        """Track media status"""
        status_names = {
            0: "NoMedia",
            1: "Loading",
            2: "Loaded",
            3: "Stalled",
            4: "Buffering",
            5: "Buffered",
            6: "EndOfMedia",
            7: "InvalidMedia",
        }
        print(f"Media status: {status_names.get(status, status)}")

    def handle_playback_state(self, state):
        """Track playback state"""
        state_names = {0: "Stopped", 1: "Playing", 2: "Paused"}
        print(f"Playback state: {state_names.get(state, state)}")

    def hide_popup(self):
        """Hide the popup"""
        self.exit_animation.start()
        QTimer.singleShot(500, self.on_close_complete)

    def on_close_complete(self):
        """Called when the closing animation is finished"""
        self.close()
        self.finished_display.emit()

    def mousePressEvent(self, event):
        """Close on click"""
        self.hide_popup()
