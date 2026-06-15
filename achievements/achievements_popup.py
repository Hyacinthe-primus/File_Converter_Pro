"""
Achievements Popup

"""

import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QUrl, Signal
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtMultimedia import QSoundEffect
import sys
_PKG_DIR  = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_PKG_DIR)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)
from translations import TranslationManager
from utils.translation_mixin import TranslationMixin

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
        if hasattr(parent, 'dark_mode'):
            self.dark_mode = parent.dark_mode
        elif hasattr(parent, 'config') and 'dark_mode' in parent.config:
            self.dark_mode = parent.config.get('dark_mode', True)
        self.sound_effect = None

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
        self.setFixedWidth(400)
        self.setSizeGripEnabled(False)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        
        container = QFrame()
        container.setObjectName("container")
        font_family = self.custom_font.family() if hasattr(self, 'custom_font') else "Segoe UI"
        container.setStyleSheet(f"""
            #container {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a1d23, stop:0.3 #2d333b, stop:1 #1a1d23);
                border-radius: 15px;
                border: 3px solid #FFD700;
                font-family: '{font_family}';
            }}
        """)
        
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(15)
        
        # Icon
        icon_path = self.achievement_system.get_achievement_icon_path(self.achievement["icon"])
        icon_label = QLabel()
        icon_label.setAttribute(Qt.WA_TranslucentBackground)
        icon_label.setStyleSheet("background: transparent;")
        
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                if pixmap.hasAlphaChannel():
                    scaled = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                else:
                    scaled = pixmap.toImage().convertToFormat(QImage.Format_ARGB32)
                    scaled = QPixmap.fromImage(scaled).scaled(
                        64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                icon_label.setPixmap(scaled)
        else:
            icon_label.setText("🏆")
            icon_label.setStyleSheet("font-size: 48px;")
        
        container_layout.addWidget(icon_label)
        
        content_layout = QVBoxLayout()
        content_layout.setSpacing(5)
        
        title_text = self.translate_text("SUCCÈS DÉBLOQUÉ")
        title_label = QLabel(f"🏆 {title_text} 🏆")
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #FFD700;
            background: transparent;
        """)
        content_layout.addWidget(title_label)
        
        _raw_name = self.achievement["name"]
        if isinstance(_raw_name, str):
            name = self._tm.translate_text(_raw_name)
        else:
            name = _raw_name.get(self.language, _raw_name.get("fr", ""))
        name_color = "#1e293b" if not self.dark_mode else "#e9ecef"
        name_label = QLabel(name)
        name_label.setStyleSheet(f"font-size: 16px; font-weight: bold;color: {name_color}; background: transparent;")
        name_label.setWordWrap(True)
        content_layout.addWidget(name_label)
        
        _raw_desc = self.achievement["description"]
        if isinstance(_raw_desc, str):
            description = self._tm.translate_text(_raw_desc)
        else:
            description = _raw_desc.get(self.language, _raw_desc.get("fr", ""))
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            font-size: 12px;
            color: #adb5bd;
            background: transparent;
        """)
        desc_label.setWordWrap(True)
        content_layout.addWidget(desc_label)
        
        reward_layout = QHBoxLayout()
        reward_layout.addStretch()
        
        xp_label = QLabel(f"+{self.achievement['reward_xp']} XP")
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
        min_height = 120
        max_height = 180  
        self.setFixedHeight(max(min_height, min(self.sizeHint().height(), max_height)))
        
        screen_geometry = self.screen().availableGeometry()
        self.move(screen_geometry.width() - self.width() - 20, 50)

    def apply_theme_style(self):
        """Apply style adapted to light or dark theme"""
        container = self.findChild(QFrame, "container")
        if not container:
            return
        
        if self.dark_mode:
            container.setStyleSheet("""
                #container {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #1a1d23, stop:0.3 #2d333b, stop:1 #1a1d23);
                    border: 3px solid #FFD700;
                    border-radius: 15px;
                }
                QLabel {
                    color: #e9ecef;
                }
            """)
        else:
            container.setStyleSheet("""
                #container {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #f8f9fa, stop:0.3 #e9ecef, stop:1 #f8f9fa);
                    border: 3px solid #FFC107;
                    border-radius: 15px;
                }
                QLabel {
                    color: #212529;
                }
                QLabel[style="title"] {
                    color: #d97706;
                }
                QLabel[style="name"] {
                    color: #1e293b;
                    font-weight: bold;
                }
                QLabel[style="desc"] {
                    color: #4b5563;
                }
                QLabel[style="xp"] {
                    color: #d97706;
                    background-color: rgba(217, 119, 6, 0.1);
                    border: 1px solid rgba(217, 119, 6, 0.3);
                }
            """)

            for child in self.findChildren(QLabel):
                text = child.text()
                if "SUCCÈS DÉBLOQUÉ" in text or "ACHIEVEMENT UNLOCKED" in text:
                    child.setProperty("style", "title")
                    child.setStyleSheet("font-size: 14px; font-weight: bold; color: #d97706;")
                _n = self.achievement["name"]
                _ach_name = _n if isinstance(_n, str) else _n.get("fr", "")
                if child.font().bold() and text == _ach_name:
                    child.setProperty("style", "name")
                    child.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e293b;")
                elif child.font().pointSize() == 12:
                    child.setProperty("style", "desc")
                    child.setStyleSheet("font-size: 12px; color: #4b5563;")
                elif "+" in text and "XP" in text:
                    child.setProperty("style", "xp")
                    child.setStyleSheet("""
                        font-size: 14px;
                        font-weight: bold;
                        color: #d97706;
                        background-color: rgba(217, 119, 6, 0.1);
                        padding: 2px 8px;
                        border-radius: 10px;
                        border: 1px solid rgba(217, 119, 6, 0.3);
                    """)

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
                
                from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
                from PySide6.QtCore import QUrl
                
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
            0: "NoMedia", 1: "Loading", 2: "Loaded", 3: "Stalled",
            4: "Buffering", 5: "Buffered", 6: "EndOfMedia", 7: "InvalidMedia"
        }
        print(f"Media status: {status_names.get(status, status)}")

    def handle_playback_state(self, state):
        """Track playback state"""
        state_names = {0: "Stopped", 1: "Playing", 2: "Paused"}
        print(f"Playback state: {state_names.get(state, state)}")

    def on_sound_status_changed(self):
        """Handle sound status change"""
        status = self.sound_effect.status()
        if status == QSoundEffect.Error:
            print("Error during sound playback")
        elif status == QSoundEffect.Loading:
            print("Loading sound...")
        elif status == QSoundEffect.Ready:
            print("Sound loaded and ready")

    def play_fallback_sound(self):
        """Play a fallback sound"""
        try:
            fallback_sounds = [
                "trophy_progression.wav",
                "first_step.wav",
                "conversion_done.wav"
            ]
            
            for sound_file in fallback_sounds:
                sound_path = self.achievement_system.get_sound_path(sound_file)
                if sound_path and os.path.exists(sound_path):
                    self.sound_effect = QSoundEffect()
                    self.sound_effect.setSource(QUrl.fromLocalFile(sound_path))
                    self.sound_effect.setVolume(0.7)
                    self.sound_effect.play()
                    print(f"Fallback sound played: {sound_file}")
                    return
            
            print("No fallback sound found")
        
        except Exception as e:
            print(f"Fallback sound playback error: {e}")

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