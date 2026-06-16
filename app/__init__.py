"""
app/__init__.py — Public API for the app package
File Converter Pro

Exposes:
    FileConverterApp   — the main application window
    FadingMainWindow   — FileConverterApp with fade-in animation

Inheritance chain (MRO):
    AppLogicMixin(OptimizationMixin, ImageToPdfMixin, BatchMixin, ...)
      └── AppUIMixin(FileManagementMixin, PanelsMixin, ..., AppLogicMixin)
            └── FileConverterApp(AppUIMixin, QMainWindow)  ← QMainWindow mixed in here
                  └── FadingMainWindow

"""

__version__ = "1.0.6"
from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QTimer

from app.ui import AppUIMixin


class FileConverterApp(AppUIMixin, QMainWindow):
    """Main application window — combines UI and logic mixins."""
    pass


class FadingMainWindow(FileConverterApp):
    """Version of FileConverterApp with fade-in support"""
    def __init__(self, config_manager):
        """Initialize the fading window with fade-in animation support.

        Args:
            config_manager: The application configuration manager instance.
        """
        super().__init__(config_manager)
        self.setWindowOpacity(0.0)
        QTimer.singleShot(0, self.set_application_icon)

    def fade_in(self, duration=600):
        """Smooth fade-in with fluid curve (non-robotic)"""
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(duration)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.fade_animation.start()


__all__ = ['FileConverterApp', 'FadingMainWindow']
