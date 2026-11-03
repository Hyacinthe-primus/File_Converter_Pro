"""Tests for custom WxH image-to-ICO settings and conversion."""

import pytest
from PIL import Image

from converter.converters import AdvancedConverterEngine


def _make_dialog(config=None, language="en"):
    from dialogs.settings_dialog import SettingsDialog

    return SettingsDialog(config or {}, None, language)


def _make_png(path, size=(512, 512), color=(220, 30, 30, 255)):
    Image.new("RGBA", size, color).save(path)
    return str(path)


@pytest.fixture
def engine():
    return AdvancedConverterEngine()


class TestIconSizeSettings:
    def test_default_is_multi_layer(self, qapp):
        dialog = _make_dialog()
        try:
            assert dialog.get_settings()["image_to_icon_layer"] == "multi"
            assert dialog.icon_layer_custom_input.isHidden() is True
        finally:
            dialog.deleteLater()
            qapp.processEvents()

    def test_saved_custom_size_is_loaded_and_returned(self, qapp):
        dialog = _make_dialog({"image_to_icon_layer": "200x100"})
        try:
            assert dialog.icon_layer_combo.currentData() == "custom"
            assert dialog.icon_layer_custom_input.text() == "200x100"
            assert dialog.icon_layer_custom_input.isHidden() is False
            assert dialog.get_settings()["image_to_icon_layer"] == "200x100"
        finally:
            dialog.deleteLater()
            qapp.processEvents()

    def test_legacy_numeric_value_becomes_custom_square(self, qapp):
        dialog = _make_dialog({"image_to_icon_layer": "200"})
        try:
            assert dialog.icon_layer_combo.currentData() == "custom"
            assert dialog.icon_layer_custom_input.text() == "200x200"
            assert dialog.get_settings()["image_to_icon_layer"] == "200x200"
        finally:
            dialog.deleteLater()
            qapp.processEvents()

    def test_selecting_custom_shows_input(self, qapp):
        dialog = _make_dialog()
        try:
            index = dialog.icon_layer_combo.findData("custom")
            dialog.icon_layer_combo.setCurrentIndex(index)
            assert dialog.icon_layer_custom_input.isHidden() is False

            dialog.icon_layer_custom_input.setText("64x32")
            assert dialog.get_settings()["image_to_icon_layer"] == "64x32"
        finally:
            dialog.deleteLater()
            qapp.processEvents()

    def test_restore_defaults_clears_custom_size(self, qapp):
        dialog = _make_dialog({"image_to_icon_layer": "64x32"})
        try:
            dialog.restore_defaults()
            assert dialog.icon_layer_combo.currentData() == "multi"
            assert dialog.icon_layer_custom_input.text() == ""
            assert dialog.icon_layer_custom_input.isHidden() is True
            assert dialog.get_settings()["image_to_icon_layer"] == "multi"
        finally:
            dialog.deleteLater()
            qapp.processEvents()

    def test_invalid_custom_size_blocks_accept(self, qapp, monkeypatch):
        from PySide6.QtWidgets import QMessageBox

        dialog = _make_dialog()
        warnings = []
        accepted = []
        monkeypatch.setattr(
            QMessageBox, "warning", staticmethod(lambda *args, **kwargs: warnings.append(args))
        )
        monkeypatch.setattr(dialog, "accept", lambda: accepted.append(True))
        try:
            index = dialog.icon_layer_combo.findData("custom")
            dialog.icon_layer_combo.setCurrentIndex(index)
            dialog.icon_layer_custom_input.setText("512x512")

            dialog._accept_settings()

            assert warnings
            assert accepted == []
            assert dialog.get_settings()["image_to_icon_layer"] == "multi"
        finally:
            dialog.deleteLater()
            qapp.processEvents()

    def test_valid_custom_size_allows_accept(self, qapp, monkeypatch):
        dialog = _make_dialog()
        accepted = []
        monkeypatch.setattr(dialog, "accept", lambda: accepted.append(True))
        try:
            index = dialog.icon_layer_combo.findData("custom")
            dialog.icon_layer_combo.setCurrentIndex(index)
            dialog.icon_layer_custom_input.setText("256x128")

            dialog._accept_settings()

            assert accepted == [True]
            assert dialog.get_settings()["image_to_icon_layer"] == "256x128"
        finally:
            dialog.deleteLater()
            qapp.processEvents()


class TestIconSizeConverter:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("256x128", (256, 128)),
            ("32X16", (32, 16)),
            ("64", (64, 64)),
            ("0x16", None),
            ("257x16", None),
            ("abc", None),
            ("10x10x10", None),
        ],
    )
    def test_parse_icon_size(self, value, expected):
        assert AdvancedConverterEngine._parse_icon_size(value) == expected

    def test_custom_non_square_size_is_exact(self, engine, tmp_path, monkeypatch):
        src = _make_png(tmp_path / "source.png")
        dst = tmp_path / "icon.ico"
        monkeypatch.setattr(engine, "_icon_layer_setting", lambda: "200x100")

        assert engine._image_to_ico(src, str(dst)) is True

        with Image.open(dst) as icon:
            assert icon.size == (200, 100)
            assert icon.info.get("sizes") == {(200, 100)}

    def test_legacy_numeric_size_still_works(self, engine, tmp_path, monkeypatch):
        src = _make_png(tmp_path / "source.png")
        dst = tmp_path / "icon.ico"
        monkeypatch.setattr(engine, "_icon_layer_setting", lambda: "64")

        assert engine._image_to_ico(src, str(dst)) is True

        with Image.open(dst) as icon:
            assert icon.size == (64, 64)

    def test_multi_layer_still_contains_all_sizes(self, engine, tmp_path, monkeypatch):
        src = _make_png(tmp_path / "source.png")
        dst = tmp_path / "icon.ico"
        monkeypatch.setattr(engine, "_icon_layer_setting", lambda: "multi")

        assert engine._image_to_ico(src, str(dst)) is True

        with Image.open(dst) as icon:
            assert icon.info.get("sizes") == {
                (256, 256),
                (128, 128),
                (64, 64),
                (48, 48),
                (32, 32),
                (16, 16),
            }
