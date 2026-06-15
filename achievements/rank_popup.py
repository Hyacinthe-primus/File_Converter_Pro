"""
Rank Popup
- Animated notification for rank progression
- Uses same assets/sounds as achievements
- Theme-aware and multi-language

"""

import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QFont, QColor
from PySide6.QtCore import QUrl
import sys
_PKG_DIR  = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_PKG_DIR)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from translations import TranslationManager
from utils.translation_mixin import TranslationMixin

class RankPopup(TranslationMixin, QDialog):

    def __init__(self, rank_data, achievement_system, parent=None, language="fr"):
        super().__init__(parent)
        self.rank_data = rank_data
        self.achievement_system = achievement_system
        self.language = language
        self._tm = TranslationManager()
        self._tm.set_language(language)
        self.dark_mode = getattr(parent, 'dark_mode', True)

    def setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(400)

        layout = QVBoxLayout(self)
        container = QFrame()
        container.setObjectName("container")
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(15)
        rank_color = self.rank_data.get("color", "#FFD700")

        if self.dark_mode:
            container.setStyleSheet(f"""
            #container {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #1a1d23, stop:0.3 #2d333b, stop:1 #1a1d23);
                border: 3px solid {rank_color};
                border-radius: 15px;
            }}
            QLabel {{
                color: #e9ecef;
            }}
            """)
        else:
            base_color = QColor(rank_color)
            if base_color.lightness() > 180:  # If too light
                darker_color = base_color.darker(130).name()
            else:
                darker_color = rank_color
            container.setStyleSheet(f"""
            #container {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #f8f9fa, stop:0.3 #e9ecef, stop:1 #f8f9fa);
                border: 3px solid {darker_color};
                border-radius: 15px;
            }}
            QLabel {{
                color: #212529;
            }}
            """)
        
        icon_path = self.achievement_system.get_achievement_icon_path(self.rank_data["icon"])
        icon_label = QLabel()
        icon_label.setAttribute(Qt.WA_TranslucentBackground)
        icon_label.setStyleSheet("background: transparent;")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("🎖️")
            icon_label.setStyleSheet("font-size: 48px;")
        container_layout.addWidget(icon_label)
        
        content_layout = QVBoxLayout()
        
        rank_up_text = self.translate_text("Rank Up!")
        self.rank_up_label = QLabel(rank_up_text.upper())
        self.rank_up_label.setAttribute(Qt.WA_TranslucentBackground)
        self.rank_up_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #FFD700;
            background-color: rgba(255, 215, 0, 0.06);
            padding: 4px 12px;
            border-radius: 12px;
            letter-spacing: 1.5px;
        """)
        content_layout.addWidget(self.rank_up_label, alignment=Qt.AlignCenter)
        
        title_label = QLabel(self.translate_text("🏆 NOUVEAU TITRE 🏆"))
        title_label.setAttribute(Qt.WA_TranslucentBackground)
        text_color = self.rank_data.get("color", "#FFFFFF")
        title_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {text_color};")
        content_layout.addWidget(title_label)
        
        _raw_name = self.rank_data["name"]
        if isinstance(_raw_name, str):
            name = self._tm.translate_text(_raw_name)
        else:
            name = _raw_name.get(self.language, _raw_name.get("fr", ""))
        name_label = QLabel(name)
        name_label.setAttribute(Qt.WA_TranslucentBackground)
        name_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {text_color};")
        content_layout.addWidget(name_label)
        
        reward_layout = QHBoxLayout()
        reward_layout.addStretch()
        xp_label = QLabel(f"+{self.achievement_system.get_total_xp()} XP")
        xp_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #FFD700;
            background-color: rgba(255, 215, 0, 0.2);
            padding: 2px 8px;
            border-radius: 10px;
        """)
        reward_layout.addWidget(xp_label)
        content_layout.addLayout(reward_layout)
        
        container_layout.addLayout(content_layout, 1)
        layout.addWidget(container)
        
        self.adjustSize()
        self.setFixedHeight(min(180, max(120, self.sizeHint().height())))
        screen = self.screen().availableGeometry()
        self.move(screen.width() - self.width() - 20, 50)
        
        font_path = os.path.join(_ROOT_DIR, "fonts", "Inter-Regular.ttf")
        if os.path.exists(font_path):
            from PySide6.QtGui import QFontDatabase
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    inter_font = QFont(families[0], 12)
                    for label in [self.rank_up_label, title_label, name_label]:
                        label.setFont(inter_font)
                    rank_up_font = QFont(families[0], 16, QFont.Bold)
                    self.rank_up_label.setFont(rank_up_font)

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
                from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
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