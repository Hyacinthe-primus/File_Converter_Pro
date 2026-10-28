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

    def test_import_button_and_theme_link_are_themeable(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        src = (root / "src" / "dialogs" / "settings_dialog.py").read_text(encoding="utf-8")
        assert src.count('setObjectName("SettingsImportBtn")') == 2
        assert '_apply_dialog_btn(import_btn, "BtnIndigo")' not in src
        assert 'THEMES_URL = "https://github.com/Hyacinthe-primus/FCP-themes"' in src
        assert 'setObjectName("SettingsLink")' in src
        assert "setOpenExternalLinks(True)" in src

    def test_builtin_themes_style_the_import_button_and_theme_link(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        themes = root / "src" / "styles" / "themes"
        for theme in ("dark", "light"):
            qss = (themes / theme / "settings.qss").read_text(encoding="utf-8")
            for selector in (
                "QPushButton#SettingsImportBtn {",
                "QPushButton#SettingsImportBtn:hover",
                "QPushButton#SettingsImportBtn:pressed",
                "QLabel#SettingsLink {",
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


class TestDialogButtonsTheme:
    """Dialog action buttons must follow each theme's actual button styling."""

    def test_dialog_button_rules_come_from_theme_style(self):
        from qss_helpers import _dialog_buttons_qss

        dark = _dialog_buttons_qss("dark")
        light = _dialog_buttons_qss("light")
        assert "QPushButton#BtnOK" in dark
        assert "QPushButton#BtnOK" in light
        assert "QMainWindow" not in dark
        assert dark != light
        assert "background-color: #21262d" in dark
        assert "background-color: #0969da" in light

    def test_custom_theme_uses_style_qss_instead_of_stale_buttons_qss(self, tmp_path, monkeypatch):
        from pathlib import Path

        import qss_helpers

        root = Path(__file__).resolve().parents[1]
        stale_buttons = (root / "src" / "styles" / "themes" / "buttons.qss").read_text(encoding="utf-8")
        theme_dir = tmp_path / "MyTheme"
        theme_dir.mkdir()
        (theme_dir / "style.qss").write_text(
            "QPushButton#BtnOK { background: #123456; }", encoding="utf-8"
        )
        (theme_dir / "buttons.qss").write_text(stale_buttons, encoding="utf-8")
        monkeypatch.setattr(qss_helpers, "_CUSTOM_THEMES_DIR", str(tmp_path))
        qss = qss_helpers._dialog_buttons_qss("MyTheme")
        assert "#123456" in qss
        assert "rgba(40,167,69,0.20)" not in qss

    def test_custom_theme_can_override_buttons_qss(self, tmp_path, monkeypatch):
        import qss_helpers

        theme_dir = tmp_path / "MyTheme"
        theme_dir.mkdir()
        (theme_dir / "style.qss").write_text(
            "QPushButton#BtnOK { background: #123456; }", encoding="utf-8"
        )
        (theme_dir / "buttons.qss").write_text(
            "QPushButton#BtnOK { background: #abcdef; }", encoding="utf-8"
        )
        monkeypatch.setattr(qss_helpers, "_CUSTOM_THEMES_DIR", str(tmp_path))
        qss = qss_helpers._dialog_buttons_qss("MyTheme")
        assert "#abcdef" in qss
        assert "#123456" not in qss

    def test_custom_theme_without_button_rules_falls_back_to_buttons_qss(self, tmp_path, monkeypatch):
        from pathlib import Path

        import qss_helpers

        root = Path(__file__).resolve().parents[1]
        stale_buttons = (root / "src" / "styles" / "themes" / "buttons.qss").read_text(encoding="utf-8")
        theme_dir = tmp_path / "MyTheme"
        theme_dir.mkdir()
        (theme_dir / "style.qss").write_text("QLabel { color: red; }", encoding="utf-8")
        (theme_dir / "buttons.qss").write_text(stale_buttons, encoding="utf-8")
        monkeypatch.setattr(qss_helpers, "_CUSTOM_THEMES_DIR", str(tmp_path))
        qss = qss_helpers._dialog_buttons_qss("MyTheme")
        assert "rgba(40,167,69,0.20)" in qss

    def test_apply_dialog_btn_refreshes_with_theme(self, qapp):
        from PySide6.QtWidgets import QPushButton

        from qss_helpers import _apply_dialog_btn, set_theme

        btn = QPushButton()
        try:
            set_theme("dark")
            _apply_dialog_btn(btn, "BtnOK")
            dark_qss = btn.styleSheet()
            set_theme("light")
            _apply_dialog_btn(btn, "BtnOK")
            light_qss = btn.styleSheet()
        finally:
            set_theme(None)
        assert "background-color: #21262d" in dark_qss
        assert "background-color: #0969da" in light_qss
        assert dark_qss != light_qss

    def test_builtin_themes_style_dialog_buttons(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        themes = root / "src" / "styles" / "themes"
        selectors = (
            "QPushButton#BtnOK {",
            "QPushButton#BtnCancel {",
            "QPushButton#BtnDecline {",
            "QPushButton#BtnCancelGlassy {",
            "QPushButton#BtnReconvert {",
            "QPushButton#BtnDeleteSelection {",
            "QPushButton#BtnFolderAsItem {",
            "QPushButton#BtnFolderContent {",
        )
        for theme in ("dark", "light"):
            qss = (themes / theme / "buttons.qss").read_text(encoding="utf-8")
            for selector in selectors:
                assert selector in qss, f"{theme}/buttons.qss is missing {selector}"

    def test_loader_reads_buttons_qss_for_builtin_themes(self):
        from qss_helpers import _load_qss

        for theme in ("dark", "light"):
            qss = _load_qss("buttons.qss", theme)
            assert "QPushButton#BtnFolderContent" in qss

    def test_buttons_qss_stays_optional(self):
        from theme_manager import REQUIRED_FILES

        assert "buttons.qss" not in REQUIRED_FILES


class TestFileSizeSelectionColor:
    """The selected file-size label must follow the theme, not a fixed color."""

    def test_uses_item_selected_text_color(self, qapp):
        from PySide6.QtGui import QColor
        from PySide6.QtWidgets import QListWidget

        from widgets import _selection_text_color

        widget = QListWidget()
        widget.setStyleSheet(
            "QListWidget::item:selected {"
            " background-color: #ffd23f; color: #14162a;"
            " border-left: 4px solid #ff5c8a; }"
        )
        assert _selection_text_color(widget, QColor("#ffffff")).name() == "#14162a"
        widget.deleteLater()

    def test_delegate_uses_theme_selected_text_color(self, qapp):
        from PySide6.QtWidgets import QListWidget, QStyle, QStyleOptionViewItem

        from widgets import FileSizeDelegate

        widget = QListWidget()
        widget.setStyleSheet("QListWidget::item:selected { color: #14162a; }")
        option = QStyleOptionViewItem()
        option.initFrom(widget)
        option.widget = widget
        option.state |= QStyle.State_Selected
        delegate = FileSizeDelegate(widget)
        assert delegate._selected_text_color(option).name() == "#14162a"
        widget.deleteLater()

    def test_uses_list_selection_color_fallback(self, qapp):
        from PySide6.QtGui import QColor
        from PySide6.QtWidgets import QListWidget

        from widgets import _selection_text_color

        widget = QListWidget()
        widget.setStyleSheet("QListWidget { selection-color: #123456; }")
        assert _selection_text_color(widget, QColor("#ffffff")).name() == "#123456"
        widget.deleteLater()

    def test_falls_back_to_palette_color(self, qapp):
        from PySide6.QtGui import QColor
        from PySide6.QtWidgets import QListWidget

        from widgets import _selection_text_color

        widget = QListWidget()
        assert _selection_text_color(widget, QColor("#abcdef")).name() == "#abcdef"
        widget.deleteLater()
