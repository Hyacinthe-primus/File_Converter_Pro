"""Terms dialog theme resolution and stylesheet wiring tests."""

import pytest
from PySide6.QtWidgets import QDialog, QMessageBox, QWidget

from dialogs.terms_dialog import TermsAndPrivacyDialog
from qss_helpers import _dialog_buttons_qss


class _ThemeParent(QWidget):
    def __init__(self, theme_name):
        super().__init__()
        self.current_theme = theme_name


def _close(dialog, qapp):
    dialog.deleteLater()
    qapp.processEvents()


def test_parent_custom_theme_is_used_for_all_terms_assets(qapp):
    parent = _ThemeParent("Kintsugi")
    dialog = TermsAndPrivacyDialog(parent, "en", dark_mode=True)
    try:
        assert dialog._theme_name == "Kintsugi"
        assert "#14100d" in dialog._terms_qss
        assert "#1b1612" in dialog.get_html_theme_css()
        assert "#d6452d" in dialog._contact_links_css
        assert dialog.terms_tab.styleSheet() == ""
        assert dialog.privacy_tab.styleSheet() == ""
        assert dialog.accept_button.styleSheet() == _dialog_buttons_qss("Kintsugi")
        assert dialog.decline_button.styleSheet() == _dialog_buttons_qss("Kintsugi")

        contact_html = dialog.get_compact_contact_links_html()
        assert "#3498db" not in contact_html
        assert "#7c5cbf" not in contact_html
        assert "#e74c3c" not in contact_html
        assert 'class="warning"' in contact_html
    finally:
        _close(dialog, qapp)


def test_explicit_custom_theme_works_without_parent(qapp):
    dialog = TermsAndPrivacyDialog(None, "en", theme_name="Riso_Press_Night")
    try:
        assert dialog._theme_name == "Riso_Press_Night"
        assert "#ff5c8a" in dialog._terms_qss
        assert "#0d0f18" in dialog.get_html_theme_css()
        assert "#8aa2ff" in dialog._contact_links_css
    finally:
        _close(dialog, qapp)


def test_explicit_custom_theme_wins_over_parent_theme(qapp):
    parent = _ThemeParent("Kintsugi")
    dialog = TermsAndPrivacyDialog(
        parent,
        "en",
        theme_name="Riso_Press_Night",
    )
    try:
        assert dialog._theme_name == "Riso_Press_Night"
        assert "#ff5c8a" in dialog._terms_qss
    finally:
        _close(dialog, qapp)


def test_builtin_dark_and_light_fallbacks(qapp):
    dark = TermsAndPrivacyDialog(None, "en", dark_mode=True)
    try:
        assert dark._theme_name == "dark"
        assert "#1e1e1e" in dark._terms_qss
        assert "#2d2d2d" in dark.get_html_theme_css()
    finally:
        _close(dark, qapp)

    light = TermsAndPrivacyDialog(None, "en", dark_mode=False)
    try:
        assert light._theme_name == "light"
        assert "#f5f6fa" in light._terms_qss
        assert "#ffffff" in light.get_html_theme_css()
    finally:
        _close(light, qapp)


def test_decline_message_ok_button_uses_active_theme(monkeypatch, qapp):
    dialog = TermsAndPrivacyDialog(None, "en", theme_name="Kintsugi")
    monkeypatch.setattr(QMessageBox, "exec", lambda self: 0)
    try:
        box = dialog._show_required_conditions_message()
        try:
            assert dialog.decline_message_shown is True
            assert box.styleSheet() == dialog._terms_qss
            ok_button = box.button(QMessageBox.Ok)
            assert ok_button.objectName() == "BtnOK"
            assert ok_button.styleSheet() == _dialog_buttons_qss("Kintsugi")
        finally:
            box.deleteLater()
            qapp.processEvents()
    finally:
        _close(dialog, qapp)


def test_app_decline_uses_themed_message_not_default_qmessagebox(monkeypatch):
    import app.logic as logic

    calls = []

    class FakeDialog:
        decline_message_shown = False

        def __init__(self, *args, **kwargs):
            pass

        def exec(self):
            return QDialog.Rejected

        def _show_required_conditions_message(self):
            calls.append("themed")

    monkeypatch.setattr(logic, "TermsAndPrivacyDialog", FakeDialog)
    monkeypatch.setattr(
        logic.QMessageBox,
        "information",
        staticmethod(lambda *args, **kwargs: calls.append("default")),
    )

    obj = logic.AppLogicMixin.__new__(logic.AppLogicMixin)
    obj.current_language = "en"
    obj.dark_mode = False
    obj.current_theme = "light"
    obj.translate_text = lambda key: key

    with pytest.raises(SystemExit):
        obj.show_terms_dialog()

    assert calls == ["themed"]


def test_legal_html_replaces_embedded_style_with_active_theme(qapp):
    dialog = TermsAndPrivacyDialog(None, "en", theme_name="Kintsugi")
    try:
        content = (
            "<html><head><style>body { color: red; }</style></head>"
            "<body>Legal text</body></html>"
        )
        themed = dialog._apply_theme_to_html(content)
        assert "body { color: red; }" not in themed
        assert "#1b1612" in themed
        assert "Legal text" in themed
    finally:
        _close(dialog, qapp)
