"""
Rank Popup
- Animated notification for rank progression
- Uses same assets/sounds as achievements
- Theme-aware and multi-language

"""

import os
import sys

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QDialog, QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QVBoxLayout

from utils import SRC_DIR

_ROOT_DIR = str(SRC_DIR)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from translations import TranslationManager
from utils.translation_mixin import TranslationMixin

from .theme import get_achievements_palette, load_achievements_qss, resolve_theme_name


class RankPopup(TranslationMixin, QDialog):
    def __init__(self, rank_data, achievement_system, parent=None, language="fr"):
        super().__init__(parent)
        self.rank_data = rank_data
        self.achievement_system = achievement_system
        self.language = language
        self._tm = TranslationManager()
        self._tm.set_language(language)
        self.dark_mode = getattr(parent, "dark_mode", True)
        self._theme = resolve_theme_name(parent, self.dark_mode)
        self._palette = get_achievements_palette(self._theme, self.dark_mode)

    def setup_ui(self):
        self.setObjectName("RankPopup")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(400)

        layout = QVBoxLayout(self)
        container = QFrame()
        container.setObjectName("RankPopupContainer")
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(15)

        icon_path = self.achievement_system.get_achievement_icon_path(self.rank_data["icon"])
        icon_label = QLabel()
        icon_label.setObjectName("RankPopupIcon")
        icon_label.setAttribute(Qt.WA_TranslucentBackground)
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("🎖️")
        container_layout.addWidget(icon_label)

        content_layout = QVBoxLayout()

        rank_up_text = self.translate_text("rank_up")
        self.rank_up_label = QLabel(rank_up_text.upper())
        self.rank_up_label.setObjectName("RankPopupRankUp")
        self.rank_up_label.setAttribute(Qt.WA_TranslucentBackground)
        content_layout.addWidget(self.rank_up_label, alignment=Qt.AlignCenter)

        title_label = QLabel(self.translate_text("advanced_to_a_new_tier"))
        title_label.setObjectName("RankPopupTitle")
        title_label.setAttribute(Qt.WA_TranslucentBackground)
        content_layout.addWidget(title_label)

        _raw_name = self.rank_data["name"]
        if isinstance(_raw_name, str):
            name = self._tm.translate_text(_raw_name)
        else:
            name = _raw_name.get(self.language, _raw_name.get("fr", ""))
        name_label = QLabel(name)
        name_label.setObjectName("RankPopupName")
        name_label.setAttribute(Qt.WA_TranslucentBackground)
        content_layout.addWidget(name_label)

        reward_layout = QHBoxLayout()
        reward_layout.addStretch()
        xp_label = QLabel(f"+{self.achievement_system.get_total_xp()} XP")
        xp_label.setObjectName("RankPopupXP")
        reward_layout.addWidget(xp_label)
        content_layout.addLayout(reward_layout)

        container_layout.addLayout(content_layout, 1)
        layout.addWidget(container)

        self.adjustSize()
        self.setFixedHeight(min(180, max(120, self.sizeHint().height())))
        screen = self.screen().availableGeometry()
        self.move(screen.width() - self.width() - 20, 50)

        self.apply_theme_style()

    def apply_theme_style(self):
        qss = load_achievements_qss(self._theme)
        rank_id = self.rank_data.get("id", "")
        rank_color = (
            self._palette.ranks.get(rank_id)
            or self.rank_data.get("color", self._palette.gold)
        )
        if not self._palette.dark:
            base_color = QColor(rank_color)
            if base_color.lightness() > 180:
                rank_color = base_color.darker(130).name()
        qss += (
            f"\n#RankPopupContainer {{ border: 3px solid {rank_color}; }}\n"
            f"#RankPopupTitle, #RankPopupName {{ color: {rank_color}; }}\n"
        )
        self.setStyleSheet(qss)

    def set_translator(self, tm) -> None:
        """Share the app-wide TranslationManager, then build the UI."""
        self._tm = tm
        self._tm.set_language(self.language)
        self.setup_ui()
        self.play_sound()
        self.setup_animations()

    def play_sound(self):
        try:
            sound_file = self.achievement_system.get_sound_path(self.rank_data["sound"])
            if sound_file and os.path.exists(sound_file):
                from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

                self.media_player = QMediaPlayer()
                self.audio_output = QAudioOutput()
                self.media_player.setAudioOutput(self.audio_output)
                self.audio_output.setVolume(0.7)
                self.media_player.setSource(QUrl.fromLocalFile(sound_file))
                self.media_player.play()
        except Exception as e:
            print(f"Error playing rank sound: {e}")

    def setup_animations(self):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.enter_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.enter_animation.setDuration(500)
        self.enter_animation.setStartValue(0.0)
        self.enter_animation.setEndValue(1.0)
        self.enter_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.enter_animation.start()
        QTimer.singleShot(5000, self.fade_out)

    def fade_out(self):
        self.exit_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.exit_animation.setDuration(500)
        self.exit_animation.setStartValue(1.0)
        self.exit_animation.setEndValue(0.0)
        self.exit_animation.setEasingCurve(QEasingCurve.InCubic)
        self.exit_animation.start()
        QTimer.singleShot(500, self.close)
