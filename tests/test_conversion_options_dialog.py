"""Quick Launch filtering, keyboard use, and active-theme updates."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QWidget


class _QuickLaunchParent(QWidget):
    theme_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.dark_mode = True
        self.current_theme = "dark"
        self._src_dir = Path(__file__).resolve().parents[1] / "src"

    def translate_text(self, key):
        labels = {
            "quick_launch": "Quick Launch",
            "no_matching_conversions": "No matching conversions.",
            "quick_launch_keyboard_hint": "Navigate · Open · Close",
            "search_2": "Search...",
        }
        return labels.get(key, key)

    def get_resource_path(self, relative_path):
        return str(self._src_dir / relative_path)


def test_quick_launch_filters_and_restores_actions(qapp):
    from dialogs.conversion_options_dialog import ConversionOptionsDialog

    parent = _QuickLaunchParent()
    dialog = ConversionOptionsDialog(parent)

    dialog.search_input.setText("merge")
    matches = [
        dialog.results.item(row).text()
        for row in range(dialog.results.count())
        if not dialog.results.item(row).isHidden()
    ]
    assert matches == ["merge_pdf", "merge_word"]

    dialog.search_input.setText("no such action")
    assert dialog.result_stack.currentWidget() is dialog.empty_label

    dialog.search_input.clear()
    assert dialog.result_stack.currentWidget() is dialog.results
    assert all(not dialog.results.item(row).isHidden() for row in range(dialog.results.count()))
    dialog.close()


def test_quick_launch_keyboard_navigation_and_activation(qapp):
    from dialogs.conversion_options_dialog import ConversionOptionsDialog

    parent = _QuickLaunchParent()
    dialog = ConversionOptionsDialog(parent)
    dialog.show()
    qapp.processEvents()
    chosen = []
    dialog.conversion_chosen.connect(chosen.append)
    dialog.search_input.setText("merge")

    QTest.keyClick(dialog.search_input, Qt.Key_Down)
    assert dialog.results.hasFocus()
    assert dialog.results.currentItem().text() == "merge_pdf"

    QTest.keyClick(dialog.results, Qt.Key_Down)
    assert dialog.results.currentItem().text() == "merge_word"
    QTest.keyClick(dialog.results, Qt.Key_Return)

    assert chosen == ["launch_merge_word"]
    assert dialog.result() == dialog.DialogCode.Accepted
    dialog.close()


def test_quick_launch_reloads_theme_when_parent_theme_changes(qapp):
    from dialogs.conversion_options_dialog import ConversionOptionsDialog
    from qss_helpers import _load_qss

    parent = _QuickLaunchParent()
    dialog = ConversionOptionsDialog(parent)
    assert dialog.styleSheet() == _load_qss("quick_launch.qss", "dark")

    parent.current_theme = "light"
    parent.theme_changed.emit("light")
    assert dialog.styleSheet() == _load_qss("quick_launch.qss", "light")
    dialog.close()


def test_quick_launch_uses_custom_theme_stylesheets(qapp, tmp_path, monkeypatch):
    import qss_helpers
    from dialogs.conversion_options_dialog import ConversionOptionsDialog

    themes_dir = tmp_path / "custom_themes"
    for name, color in (("CustomA", "#123456"), ("CustomB", "#654321")):
        theme_dir = themes_dir / name
        theme_dir.mkdir(parents=True)
        (theme_dir / "quick_launch.qss").write_text(
            f"QDialog#QuickLaunchDialog {{ color: {color}; }}", encoding="utf-8"
        )
    monkeypatch.setattr(qss_helpers, "_CUSTOM_THEMES_DIR", str(themes_dir))

    parent = _QuickLaunchParent()
    parent.current_theme = "CustomA"
    dialog = ConversionOptionsDialog(parent)
    assert "#123456" in dialog.styleSheet()

    parent.theme_changed.emit("CustomB")
    assert "#654321" in dialog.styleSheet()
    dialog.close()
