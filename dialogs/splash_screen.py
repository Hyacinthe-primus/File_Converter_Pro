"""ModernSplashScreen — Animated loading screen with progress steps."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QProgressBar,
                               QFrame)
from PySide6.QtCore import (Qt, QPropertyAnimation, QEasingCurve,
                            QSequentialAnimationGroup)
from PySide6.QtGui import QIcon

from utils import make_tm
from utils.translation_mixin import TranslationMixin


class ModernSplashScreen(TranslationMixin, QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.dark_mode = config.get("dark_mode", False)
        self.current_language = config.get("language", "fr")
        self._tm = make_tm(self.current_language)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 400)
        self.setWindowIcon(QIcon(self.get_icon_path()))
        self.setup_ui()
        self.setWindowTitle(self.translate_text("File Converter Pro - convertisseur de fichiers professionnels"))

    def get_icon_path(self):
        """Find icon.ico robustly (dev + PyInstaller)"""
        from utils import get_icon_path
        return get_icon_path("icon.ico")

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        self.container = QFrame()
        self.container.setObjectName("container")
        container_layout = QVBoxLayout(self.container)
        container_layout.setAlignment(Qt.AlignCenter)
        container_layout.setSpacing(20)

        self.logo_container = QWidget()
        self.logo_container.setFixedSize(120, 120)
        logo_layout = QVBoxLayout(self.logo_container)
        logo_layout.setAlignment(Qt.AlignCenter)

        self.logo_label = QLabel("📦")
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet("""
            QLabel {
                font-size: 60px;
                background: transparent;
            }
        """)
        logo_layout.addWidget(self.logo_label)

        self.title_label = QLabel("FILE CONVERTER PRO")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)

        subtitle_text = self.translate_text("Initialisation de l'application...")
        self.subtitle_label = QLabel(subtitle_text)
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                margin: 5px;
            }
        """)

        self.progress_container = QWidget()
        self.progress_container.setFixedWidth(300)
        progress_layout = QVBoxLayout(self.progress_container)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)

        self.progress_text = QLabel("0%")
        self.progress_text.setAlignment(Qt.AlignCenter)
        self.progress_text.setStyleSheet("font-size: 12px; margin-top: 5px;")

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_text)

        container_layout.addWidget(self.logo_container)
        container_layout.addWidget(self.title_label)
        container_layout.addWidget(self.subtitle_label)
        container_layout.addWidget(self.progress_container)

        layout.addWidget(self.container)
        self.setLayout(layout)

        self.apply_styles()
        self.setup_animations()

    def apply_styles(self):
        if self.dark_mode:
            self.setStyleSheet("""
                #container {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #1e2229, stop:1 #1a1d23);
                    border-radius: 20px;
                    border: 1px solid #495057;
                }
                QLabel {
                    color: #e9ecef;
                }
                QProgressBar {
                    background-color: #495057;
                    border: none;
                    border-radius: 4px;
                }
                QProgressBar::chunk {
                    background-color: #4dabf7;
                    border-radius: 4px;
                }
            """)
            self.title_label.setStyleSheet("color: #e9ecef; font-size: 32px; font-weight: bold;")
            self.subtitle_label.setStyleSheet("color: #adb5bd; font-size: 14px;")
            self.progress_text.setStyleSheet("color: #adb5bd; font-size: 12px;")
        else:
            self.setStyleSheet("""
                #container {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #ffffff, stop:1 #f8f9fa);
                    border-radius: 20px;
                    border: 1px solid #e0e0e0;
                }
                QLabel {
                    color: #2c3e50;
                }
                QProgressBar {
                    background-color: #ecf0f1;
                    border: none;
                    border-radius: 4px;
                }
                QProgressBar::chunk {
                    background-color: #3498db;
                    border-radius: 4px;
                }
            """)
            self.title_label.setStyleSheet("color: #2c3e50; font-size: 32px; font-weight: bold;")
            self.subtitle_label.setStyleSheet("color: #7f8c8d; font-size: 14px;")
            self.progress_text.setStyleSheet("color: #7f8c8d; font-size: 12px;")

    def setup_animations(self):
        self.progress_animation = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_animation.setDuration(2500)
        self.progress_animation.setStartValue(0)
        self.progress_animation.setEndValue(100)
        self.progress_animation.setEasingCurve(QEasingCurve.OutCubic)

        self.progress_animation.valueChanged.connect(self.update_progress_text)

    def update_progress_text(self, value):
        self.progress_text.setText(f"{int(value)}%")

        if value < 25:
            current_text = "Initialisation de l'application..."
        elif value < 50:
            current_text = "Chargement des modules..."
        elif value < 75:
            current_text = "Préparation de l'interface..."
        elif value < 95:
            current_text = "Presque terminé..."
        else:
            current_text = "Prêt!"

        self.subtitle_label.setText(self.translate_text(current_text))

    def start_animation(self):
        logo_animation = QPropertyAnimation(self.logo_label, b"geometry")
        logo_animation.setDuration(1000)
        logo_animation.setKeyValueAt(0, self.logo_label.geometry())
        logo_animation.setKeyValueAt(0.3, self.logo_label.geometry().adjusted(0, -15, 0, -15))
        logo_animation.setKeyValueAt(1, self.logo_label.geometry())
        logo_animation.setEasingCurve(QEasingCurve.OutBounce)

        self.animation_group = QSequentialAnimationGroup()
        self.animation_group.addAnimation(logo_animation)
        self.animation_group.addAnimation(self.progress_animation)
        self.animation_group.finished.connect(self.close)
        self.animation_group.finished.connect(self.deleteLater)
        self.animation_group.start()

    def fade_out(self, duration=500):
        """Launch a smooth fade-out animation and destroy the window"""
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(duration)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_animation.finished.connect(self.close)
        self.fade_animation.finished.connect(self.deleteLater)
        self.fade_animation.start()
