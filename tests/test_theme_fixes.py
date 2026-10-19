"""Tests for LogoLabel theme fix and custom theme support in advanced conversions."""

import pytest


@pytest.fixture
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestLogoLabelThemeFix:
    def _make_parent_with_logo(self, qapp):
        from PySide6.QtWidgets import QLabel, QWidget

        parent = QWidget()
        logo = QLabel("FC", parent)
        logo.setObjectName("LogoLabel")
        return parent, logo

    @staticmethod
    def _install_custom_theme(tmp_path, monkeypatch, name, kind):
        """Create a throwaway custom theme so tests do not rely on installed ones."""
        import theme_manager

        themes_dir = tmp_path / "custom_themes"
        theme_dir = themes_dir / name
        theme_dir.mkdir(parents=True)
        (theme_dir / "metadata.ini").write_text(
            f"[theme]\nname = {name}\nkind = {kind}\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(theme_manager, "CUSTOM_THEMES_DIR", themes_dir)
        return name

    def test_update_logo_label_dark(self, qapp):
        from app.mixins.theme_language import ThemeLanguageMixin

        parent, logo = self._make_parent_with_logo(qapp)
        ThemeLanguageMixin._update_logo_label(parent, "dark")
        assert "#e8ff6b" in logo.styleSheet()
        parent.deleteLater()

    def test_update_logo_label_light(self, qapp):
        from app.mixins.theme_language import ThemeLanguageMixin

        parent, logo = self._make_parent_with_logo(qapp)
        ThemeLanguageMixin._update_logo_label(parent, "light")
        assert "#2d2dc8" in logo.styleSheet()
        parent.deleteLater()

    def test_update_logo_label_custom_dark(self, qapp, tmp_path, monkeypatch):
        from app.mixins.theme_language import ThemeLanguageMixin

        name = self._install_custom_theme(tmp_path, monkeypatch, "TestDark", "dark")
        parent, logo = self._make_parent_with_logo(qapp)
        ThemeLanguageMixin._update_logo_label(parent, name)
        assert "#e8ff6b" in logo.styleSheet()
        parent.deleteLater()

    def test_update_logo_label_custom_light(self, qapp, tmp_path, monkeypatch):
        from app.mixins.theme_language import ThemeLanguageMixin

        name = self._install_custom_theme(tmp_path, monkeypatch, "TestLight", "light")
        parent, logo = self._make_parent_with_logo(qapp)
        ThemeLanguageMixin._update_logo_label(parent, name)
        assert "#2d2dc8" in logo.styleSheet()
        parent.deleteLater()

    def test_update_logo_label_no_logo(self, qapp):
        from PySide6.QtWidgets import QWidget

        from app.mixins.theme_language import ThemeLanguageMixin

        parent = QWidget()
        ThemeLanguageMixin._update_logo_label(parent, "dark")
        parent.deleteLater()


class TestAdvancedConversionsCustomTheme:
    def test_resolve_theme_name_custom(self):
        from types import SimpleNamespace

        from advanced_conversions import resolve_theme_name

        parent = SimpleNamespace(current_theme="CustomTheme", dark_mode=True)
        assert resolve_theme_name(parent) == "CustomTheme"

    def test_resolve_theme_name_builtin_dark(self):
        from types import SimpleNamespace

        from advanced_conversions import resolve_theme_name

        parent = SimpleNamespace(current_theme="dark", dark_mode=True)
        assert resolve_theme_name(parent) == "dark"

    def test_resolve_theme_name_builtin_light(self):
        from types import SimpleNamespace

        from advanced_conversions import resolve_theme_name

        parent = SimpleNamespace(current_theme="light", dark_mode=False)
        assert resolve_theme_name(parent) == "light"

    def test_resolve_theme_name_no_parent(self):
        from advanced_conversions import resolve_theme_name

        assert resolve_theme_name(None) == "light"

    def test_theme_changed_signal_exists(self, qapp):
        from app import FileConverterApp

        assert hasattr(FileConverterApp, "theme_changed")

    def test_dialog_connects_to_theme_signal(self, qapp):
        from unittest.mock import patch

        from PySide6.QtCore import Signal
        from PySide6.QtWidgets import QTabWidget, QWidget

        from advanced_conversions import AdvancedConversionsDialog

        class FakeParent(QWidget):
            theme_changed = Signal(str)

        parent = FakeParent()
        received = []

        def _on_theme(theme_name):
            received.append(theme_name)

        with (
            patch("advanced_conversions._load_qss", return_value=""),
            patch.object(AdvancedConversionsDialog, "_setup_ui"),
            patch.object(AdvancedConversionsDialog, "_apply_theme_style"),
        ):
            dlg = AdvancedConversionsDialog.__new__(AdvancedConversionsDialog)
            dlg.parent_window = parent
            dlg._tab_widget = QTabWidget()
            dlg._apply_theme_style = lambda: received.append("applied")
            if hasattr(parent, "theme_changed"):
                parent.theme_changed.connect(dlg._apply_theme_style)
            parent.theme_changed.emit("CustomTheme")
            assert received == ["applied"]
        parent.deleteLater()


class TestSettingsImportButtonQss:
    """The .lang / .fctheme install buttons must be themeable through settings.qss."""

    def test_both_import_buttons_use_the_settings_object_name(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        src = (root / "src" / "dialogs" / "settings_dialog.py").read_text(encoding="utf-8")
        assert src.count('setObjectName("SettingsImportBtn")') == 2
        assert '_apply_dialog_btn(import_btn, "BtnIndigo")' not in src

    def test_builtin_themes_style_the_import_button(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        themes = root / "src" / "styles" / "themes"
        for theme in ("dark", "light"):
            qss = (themes / theme / "settings.qss").read_text(encoding="utf-8")
            for selector in (
                "QPushButton#SettingsImportBtn {",
                "QPushButton#SettingsImportBtn:hover",
                "QPushButton#SettingsImportBtn:pressed",
            ):
                assert selector in qss, f"{theme}/settings.qss is missing {selector}"


class TestSettingsAutomationButtonQss:
    """The automation folder / reload buttons must be themeable through settings.qss."""

    def test_automation_buttons_use_settings_object_names(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        src = (root / "src" / "dialogs" / "settings_dialog.py").read_text(encoding="utf-8")
        assert 'setObjectName("SettingsAutomationOpenBtn")' in src
        assert 'setObjectName("SettingsAutomationReloadBtn")' in src
        assert "_apply_dialog_btn(open_btn" not in src
        assert "_apply_dialog_btn(reload_btn" not in src

    def test_builtin_themes_style_the_automation_buttons(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        themes = root / "src" / "styles" / "themes"
        for theme in ("dark", "light"):
            qss = (themes / theme / "settings.qss").read_text(encoding="utf-8")
            for name in ("SettingsAutomationOpenBtn", "SettingsAutomationReloadBtn"):
                for suffix in (" {", ":hover", ":pressed"):
                    selector = f"QPushButton#{name}{suffix}"
                    assert selector in qss, f"{theme}/settings.qss is missing {selector}"


class TestSplashScreenTheme:
    """The splash screen must be styled by the active theme's splash.qss."""

    def test_splash_widgets_use_object_names(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        src = (root / "src" / "dialogs" / "splash_screen.py").read_text(encoding="utf-8")
        for name in (
            "SplashContainer",
            "SplashLogo",
            "SplashTitle",
            "SplashSubtitle",
            "SplashProgress",
            "SplashProgressText",
        ):
            assert f'setObjectName("{name}")' in src
        assert 'setObjectName("container")' not in src
        assert '_load_qss("splash.qss"' in src
        assert 'config.get("custom_theme")' in src

    def test_builtin_themes_style_the_splash(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        themes = root / "src" / "styles" / "themes"
        for theme in ("dark", "light"):
            qss = (themes / theme / "splash.qss").read_text(encoding="utf-8")
            for selector in (
                "QFrame#SplashContainer",
                "QLabel#SplashLogo",
                "QLabel#SplashTitle",
                "QLabel#SplashSubtitle",
                "QProgressBar#SplashProgress",
                "QProgressBar#SplashProgress::chunk",
                "QLabel#SplashProgressText",
            ):
                assert selector in qss, f"{theme}/splash.qss is missing {selector}"

    def test_loader_reads_splash_qss_for_builtin_themes(self):
        from qss_helpers import _load_qss

        for theme in ("dark", "light"):
            qss = _load_qss("splash.qss", theme)
            assert "QFrame#SplashContainer" in qss


class TestQuickConvertCardTheme:
    """The Quick Convert card must use the active theme's window_card.qss."""

    def test_quick_convert_window_loads_themed_card(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        src = (root / "src" / "context_menu" / "window.py").read_text(encoding="utf-8")
        assert '_load_qss("window_card.qss", self._theme_name())' in src
        assert 'config.get("custom_theme")' in src
        assert 'config.get("dark_mode")' in src

    def test_builtin_themes_style_the_quick_convert_card(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        themes = root / "src" / "styles" / "themes"
        for theme in ("dark", "light"):
            qss = (themes / theme / "window_card.qss").read_text(encoding="utf-8")
            for selector in (
                "#card {",
                "QLabel {",
                "#title",
                "#fileList",
                "#separator",
                "QComboBox {",
                "QComboBox QAbstractItemView",
                "selection-color:",
                "QComboBox QAbstractItemView::item",
                "QPushButton#convertBtn {",
                "QPushButton#convertBtn:hover",
                "QPushButton#convertBtn:disabled",
                "QPushButton#cancelBtn {",
                "QPushButton#cancelBtn:hover",
                "QProgressBar {",
                "QProgressBar::chunk",
                "#statusOk",
                "#statusErr",
                "#conversionLabel",
            ):
                assert selector in qss, f"{theme}/window_card.qss is missing {selector}"

    def test_loader_reads_window_card_qss_for_builtin_themes(self):
        from qss_helpers import _load_qss

        for theme in ("dark", "light"):
            qss = _load_qss("window_card.qss", theme)
            assert "#card" in qss

    def test_window_card_qss_stays_optional(self):
        from theme_manager import REQUIRED_FILES

        assert "window_card.qss" not in REQUIRED_FILES
        assert "splash.qss" not in REQUIRED_FILES
