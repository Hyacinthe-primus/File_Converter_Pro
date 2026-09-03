"""Tests for the scanlayer OCR integration (image -> searchable PDF).

Covers the OCR activation logic, scanlayer configuration (tesseract
resolution + orientation), the external-binary entry, config defaults,
the Settings dialog OCR controls, and the enabled panel checkbox.
"""

import os
import sys

from app.mixins.image_to_pdf import ImageToPdfMixin


def _base_config():
    return {
        "ocr_enabled": False,
        "ocr_orientation": "auto",
    }


class _StubCheckbox:
    def __init__(self, checked: bool):
        self._checked = checked

    def isChecked(self):
        return self._checked


class _StubMixin(ImageToPdfMixin):
    """Minimal stand-in for the app object carrying what the OCR logic needs."""

    def __init__(self, config: dict, ocr_checked: bool = False):
        self.config = dict(config)
        self.ocr_checkbox = _StubCheckbox(ocr_checked)


def _stub_merge(self, image_files, output_file, orientation):
    """Stand-in for the per-image merge that records OCR usage."""
    self.achievement_system.record_ocr_usage(len(image_files))
    return None


class TestOcrActive:
    def test_ocr_inactive_when_checkbox_off(self):
        from app.mixins.image_to_pdf import ImageToPdfMixin

        m = _StubMixin(_base_config(), ocr_checked=False)
        assert ImageToPdfMixin._ocr_active(m) is False

    def test_checkbox_enables_ocr(self):
        from app.mixins.image_to_pdf import ImageToPdfMixin

        m = _StubMixin(_base_config(), ocr_checked=True)
        assert ImageToPdfMixin._ocr_active(m) is True

    def test_missing_checkbox_is_inactive(self):
        from app.mixins.image_to_pdf import ImageToPdfMixin

        m = _StubMixin(_base_config())
        del m.ocr_checkbox
        assert ImageToPdfMixin._ocr_active(m) is False


class TestOcrOrientationValue:
    def _value(self, config_value):
        from app.mixins.image_to_pdf import ImageToPdfMixin

        m = _StubMixin({"ocr_orientation": config_value})
        return ImageToPdfMixin._ocr_orientation_value(m)

    def test_auto_maps_to_none(self):
        assert self._value("auto") is None

    def test_none_string_maps_to_none(self):
        assert self._value("none") == "none"

    def test_empty_maps_to_none(self):
        assert self._value("") is None

    def test_numeric_string_maps_to_float(self):
        assert self._value("45") == 45.0

    def test_decimal_string_maps_to_float(self):
        assert self._value("-12.5") == -12.5

    def test_invalid_text_maps_to_none(self):
        assert self._value("not-an-angle") is None

    def test_bool_false_maps_to_none(self):
        assert self._value(False) == "none"

    def test_none_value_maps_to_none(self):
        assert self._value(None) == "none"


class TestConfigureScanlayer:
    def test_configures_tesseract_and_auto_orientation(self, monkeypatch):
        from app.mixins.image_to_pdf import ImageToPdfMixin

        calls = {}

        class _FakeScanlayer:
            @staticmethod
            def configure(**kwargs):
                calls["kwargs"] = kwargs

        monkeypatch.setattr("external_binaries.resolve_binary", lambda name: r"C:\tess\tesseract.exe")
        monkeypatch.setitem(sys.modules, "scanlayer", _FakeScanlayer)

        m = _StubMixin(_base_config())
        tesseract, orientation = ImageToPdfMixin._configure_scanlayer(m)

        assert tesseract == r"C:\tess\tesseract.exe"
        assert orientation is None
        assert calls["kwargs"] == {"tesseract_cmd": r"C:\tess\tesseract.exe"}

    def test_orientation_none_when_setting_none(self, monkeypatch):
        from app.mixins.image_to_pdf import ImageToPdfMixin

        monkeypatch.setattr("external_binaries.resolve_binary", lambda name: "/usr/bin/tesseract")

        class _FakeScanlayer:
            @staticmethod
            def configure(**kwargs):
                pass

        monkeypatch.setitem(sys.modules, "scanlayer", _FakeScanlayer)

        cfg = _base_config()
        cfg["ocr_orientation"] = "none"
        m = _StubMixin(cfg)
        _tesseract, orientation = ImageToPdfMixin._configure_scanlayer(m)
        assert orientation == "none"

    def test_orientation_custom_degrees(self, monkeypatch):
        from app.mixins.image_to_pdf import ImageToPdfMixin

        monkeypatch.setattr("external_binaries.resolve_binary", lambda name: "/usr/bin/tesseract")

        class _FakeScanlayer:
            @staticmethod
            def configure(**kwargs):
                pass

        monkeypatch.setitem(sys.modules, "scanlayer", _FakeScanlayer)

        cfg = _base_config()
        cfg["ocr_orientation"] = "90"
        m = _StubMixin(cfg)
        _tesseract, orientation = ImageToPdfMixin._configure_scanlayer(m)
        assert orientation == 90.0

    def test_no_tesseract_still_returns_none_orientation(self, monkeypatch):
        from app.mixins.image_to_pdf import ImageToPdfMixin

        calls = []

        class _FakeScanlayer:
            @staticmethod
            def configure(**kwargs):
                calls.append(kwargs)

        monkeypatch.setattr("external_binaries.resolve_binary", lambda name: None)
        monkeypatch.setitem(sys.modules, "scanlayer", _FakeScanlayer)

        m = _StubMixin(_base_config())
        tesseract, orientation = ImageToPdfMixin._configure_scanlayer(m)
        assert tesseract is None
        assert orientation is None
        assert calls == []


class TestTesseractExternalBinary:
    def test_tesseract_declared_in_tools(self):
        import external_binaries as eb

        assert "tesseract" in eb.TOOLS

    def test_tesseract_entry_in_shipped_conf(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        conf_path = os.path.join(repo_root, "src", "config", "external_binaries.conf")
        with open(conf_path, encoding="utf-8") as fh:
            content = fh.read()
        assert "tesseract" in content


class TestConfigDefaults:
    def test_ocr_keys_in_default_config(self):
        from config import DEFAULT_CONFIG

        assert "ocr_enabled" in DEFAULT_CONFIG
        assert "ocr_orientation" in DEFAULT_CONFIG

    def test_ocr_default_values(self):
        from config import DEFAULT_CONFIG

        assert DEFAULT_CONFIG["ocr_enabled"] is False
        assert DEFAULT_CONFIG["ocr_orientation"] == "auto"


class TestSettingsDialogOcr:
    def _make_dialog(self, **overrides):
        from dialogs.settings_dialog import SettingsDialog

        cfg = _base_config()
        cfg.update(overrides)
        return SettingsDialog(cfg, parent=None, language="fr")

    def _cleanup(self, qapp, dlg):
        dlg.close()
        qapp.processEvents()

    def test_ocr_controls_exist(self, qapp):
        dlg = self._make_dialog()
        assert hasattr(dlg, "ocr_orientation_combo")
        assert not hasattr(dlg, "ocr_always_create_pdf_checkbox")
        assert not hasattr(dlg, "ocr_enabled_checkbox")
        self._cleanup(qapp, dlg)

    def test_orientation_combo_has_none_and_auto(self, qapp):
        dlg = self._make_dialog()
        datas = [dlg.ocr_orientation_combo.itemData(i) for i in range(dlg.ocr_orientation_combo.count())]
        assert "none" in datas
        assert "auto" in datas
        self._cleanup(qapp, dlg)

    def test_orientation_combo_is_editable_for_custom_values(self, qapp):
        dlg = self._make_dialog()
        assert dlg.ocr_orientation_combo.isEditable() is True
        self._cleanup(qapp, dlg)

    def test_get_settings_returns_ocr_keys(self, qapp):
        dlg = self._make_dialog()
        settings = dlg.get_settings()
        assert "ocr_orientation" in settings
        assert "ocr_always_create_pdf" not in settings
        assert settings["ocr_orientation"] == "auto"
        self._cleanup(qapp, dlg)

    def test_get_settings_returns_none_preset(self, qapp):
        dlg = self._make_dialog()
        for idx in range(dlg.ocr_orientation_combo.count()):
            if dlg.ocr_orientation_combo.itemData(idx) == "none":
                dlg.ocr_orientation_combo.setCurrentIndex(idx)
                break
        assert dlg.get_settings()["ocr_orientation"] == "none"
        self._cleanup(qapp, dlg)

    def test_get_settings_returns_custom_degrees(self, qapp):
        dlg = self._make_dialog()
        dlg.ocr_orientation_combo.setCurrentIndex(1)
        dlg.ocr_orientation_combo.setEditText("30")
        assert dlg.get_settings()["ocr_orientation"] == "30"
        self._cleanup(qapp, dlg)

    def test_restore_defaults_resets_ocr(self, qapp):
        dlg = self._make_dialog(ocr_orientation="90")
        for idx in range(dlg.ocr_orientation_combo.count()):
            if dlg.ocr_orientation_combo.itemData(idx) == "none":
                dlg.ocr_orientation_combo.setCurrentIndex(idx)
                break
        dlg.restore_defaults()
        assert dlg.get_settings()["ocr_orientation"] == "auto"
        self._cleanup(qapp, dlg)

    def test_orientation_combo_reflects_custom_config(self, qapp):
        dlg = self._make_dialog(ocr_orientation="45")
        assert dlg.get_settings()["ocr_orientation"] == "45"
        self._cleanup(qapp, dlg)


class TestPanelsOcrCheckbox:
    def test_panel_checkbox_enabled(self, app):
        assert app.ocr_checkbox.isEnabled() is True

    def test_panel_checkbox_toggle_updates_config(self, app):
        app.ocr_checkbox.setChecked(True)
        app.ocr_checkbox.stateChanged.emit(2)
        assert app.config.get("ocr_enabled") is True
        app.ocr_checkbox.setChecked(False)
        app.ocr_checkbox.stateChanged.emit(0)
        assert app.config.get("ocr_enabled") is False

    def test_app_ocr_active_matches_config(self, app):
        app.ocr_checkbox.setChecked(False)
        assert app._ocr_active() is False

        app.ocr_checkbox.setChecked(True)
        assert app._ocr_active() is True


class TestOcrAchievementWiring:
    def _clean_ocr(self, app, monkeypatch, tmp_path):
        import sys

        from app.mixins import image_to_pdf

        calls = {"ocr_pages": []}

        class _FakeResult:
            words_count = 1

        class _FakeScanlayer:
            @staticmethod
            def convert(**kwargs):
                return _FakeResult()

            @staticmethod
            def configure(**kwargs):
                return None

        monkeypatch.setitem(sys.modules, "scanlayer", _FakeScanlayer)
        monkeypatch.setattr(image_to_pdf.ImageToPdfMixin, "_configure_scanlayer", lambda self: (None, None))
        monkeypatch.setattr(app, "show_progress", lambda *a, **k: None)
        monkeypatch.setattr(app, "get_output_directory", lambda *a, **k: str(tmp_path))
        monkeypatch.setattr(app.db_manager, "add_conversion_record", lambda *a, **k: None)
        monkeypatch.setattr(app, "system_notifier", type("_N", (), {"send": lambda *a, **k: None})())
        monkeypatch.setattr(app.progress_bar, "setValue", lambda *a, **k: None)
        monkeypatch.setattr(image_to_pdf.ImageToPdfMixin, "_merge_images_with_ocr_to_pdf", _stub_merge)
        monkeypatch.setattr(app.achievement_system, "record_ocr_usage", lambda pages: calls["ocr_pages"].append(pages))
        monkeypatch.setattr(image_to_pdf.QMessageBox, "information", lambda *a, **k: None)
        return calls

    def test_separate_ocr_counts_pages(self, app, monkeypatch, tmp_path):
        calls = self._clean_ocr(app, monkeypatch, tmp_path)
        img = tmp_path / "img.png"
        img.write_bytes(b"\x89PNG not-really-an-image")
        app.ocr_convert_images_to_separate_pdfs([str(img)], [])
        assert calls["ocr_pages"] == [1]

    def test_merged_ocr_counts_total_pages(self, app, monkeypatch, tmp_path):
        calls = self._clean_ocr(app, monkeypatch, tmp_path)
        imgs = []
        for name in ("a.png", "b.png", "c.png"):
            p = tmp_path / name
            p.write_bytes(b"\x89PNG not-really-an-image")
            imgs.append(str(p))
        app.ocr_convert_images_to_merged_pdf(imgs, [])
        assert calls["ocr_pages"] == [3]
