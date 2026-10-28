"""ModernSplashScreen - Animated loading screen with progress steps."""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QSequentialAnimationGroup, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QLabel, QProgressBar, QVBoxLayout, QWidget

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
        self.setWindowTitle(self.translate_text("file_converter_pro_professional_file_converter"))

    def get_icon_path(self):
        """Find icon.ico robustly (dev + PyInstaller)"""
        from utils import get_icon_path

        return get_icon_path("icon.ico")

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        self.container = QFrame()
        self.container.setObjectName("SplashContainer")
        container_layout = QVBoxLayout(self.container)
        container_layout.setAlignment(Qt.AlignCenter)
        container_layout.setSpacing(20)

        self.logo_container = QWidget()
        self.logo_container.setFixedSize(120, 120)
        logo_layout = QVBoxLayout(self.logo_container)
        logo_layout.setAlignment(Qt.AlignCenter)

        self.logo_label = QLabel("📦")
        self.logo_label.setObjectName("SplashLogo")
        self.logo_label.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(self.logo_label)

        self.title_label = QLabel("FILE CONVERTER PRO")
        self.title_label.setObjectName("SplashTitle")
        self.title_label.setAlignment(Qt.AlignCenter)

        subtitle_text = self.translate_text("initializing_application")
        self.subtitle_label = QLabel(subtitle_text)
        self.subtitle_label.setObjectName("SplashSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignCenter)

        self.progress_container = QWidget()
        self.progress_container.setFixedWidth(300)
        progress_layout = QVBoxLayout(self.progress_container)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("SplashProgress")
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)

        self.progress_text = QLabel("0%")
        self.progress_text.setObjectName("SplashProgressText")
        self.progress_text.setAlignment(Qt.AlignCenter)

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

    def _theme_name(self) -> str:
        """Active custom theme when one is installed, otherwise dark/light."""
        custom = self.config.get("custom_theme")
        if custom and custom not in ("dark", "light"):
            from theme_manager import get_custom_themes

            if any(theme.folder_name == custom for theme in get_custom_themes()):
                return custom
        return "dark" if self.dark_mode else "light"

    def apply_styles(self):
        from qss_helpers import _load_qss

        self.setStyleSheet(_load_qss("splash.qss", self._theme_name()))

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
            current_text = "initializing_application"
        elif value < 50:
            current_text = "loading_modules"
        elif value < 75:
            current_text = "preparing_interface"
        elif value < 95:
            current_text = "almost_done"
        else:
            current_text = "ready_2"

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
