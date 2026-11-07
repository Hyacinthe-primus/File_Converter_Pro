"""Main Image-to-PDF result reporting regressions."""

from pathlib import Path
from types import SimpleNamespace

import fitz
from PIL import Image

import app.mixins.image_to_pdf as image_module
from app.mixins.image_to_pdf import ImageToPdfMixin
from translations import TranslationManager


def _make_image(path: Path) -> Path:
    Image.new("RGB", (24, 18), "white").save(path)
    return path


class _Harness(ImageToPdfMixin):
    def __init__(self, output_dir: Path, fixed_output: Path | None = None):
        self.output_dir = output_dir
        self.fixed_output = fixed_output
        self.config = {
            "enable_system_notifications": False,
            "backup_before_conversion": False,
        }
        self.notifications = []
        self.db_manager = SimpleNamespace(add_conversion_record=lambda **_kwargs: None)
        self.achievement_system = SimpleNamespace(
            record_conversion=lambda *_args, **_kwargs: None,
            record_ocr_usage=lambda *_args, **_kwargs: None,
        )
        self.progress_bar = SimpleNamespace(setValue=lambda _value: None)
        self.system_notifier = SimpleNamespace(
            send=lambda *args, **_kwargs: self.notifications.append(args)
        )
        self._tm = TranslationManager()
        self._tm.set_language("en")

    def get_output_directory(self, filename=None):
        if self.fixed_output is not None:
            return str(self.fixed_output)
        if filename:
            return str(self.output_dir / filename)
        return str(self.output_dir)

    def translate_text(self, text):
        return self._tm.translate_text(text)

    def show_progress(self, *_args, **_kwargs):
        return None

    def record_config_usage(self, *_args, **_kwargs):
        return None


def _messages(monkeypatch):
    information, warning, critical = [], [], []
    monkeypatch.setattr(
        image_module.QMessageBox,
        "information",
        staticmethod(lambda *args: information.append(args)),
    )
    monkeypatch.setattr(
        image_module.QMessageBox,
        "warning",
        staticmethod(lambda *args: warning.append(args)),
    )
    monkeypatch.setattr(
        image_module.QMessageBox,
        "critical",
        staticmethod(lambda *args: critical.append(args)),
    )
    return information, warning, critical


def test_successful_separate_conversion_reports_success(tmp_path, monkeypatch):
    source = _make_image(tmp_path / "source.png")
    app = _Harness(tmp_path)
    information, warning, critical = _messages(monkeypatch)

    app.convert_images_to_separate_pdfs([str(source)], [])

    assert len(information) == 1
    assert "1/1" in information[0][2]
    assert warning == []
    assert critical == []


def test_total_separate_failure_reports_error_details(tmp_path, monkeypatch):
    import context_menu.conversion_helpers as helpers

    source = _make_image(tmp_path / "source.png")
    app = _Harness(tmp_path)
    information, warning, critical = _messages(monkeypatch)
    monkeypatch.setattr(
        helpers,
        "_convert_image_to_pdf",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("decode exploded")),
    )

    app.convert_images_to_separate_pdfs([str(source)], [])

    assert information == []
    assert warning == []
    assert len(critical) == 1
    assert "source.png" in critical[0][2]
    assert "decode exploded" in critical[0][2]
    assert app.notifications == []


def test_partial_separate_failure_reports_warning_details(tmp_path, monkeypatch):
    good = _make_image(tmp_path / "good.png")
    bad = _make_image(tmp_path / "bad.png")
    app = _Harness(tmp_path)
    information, warning, critical = _messages(monkeypatch)
    import context_menu.conversion_helpers as helpers

    def convert(source, output_dir):
        if Path(source).name == "bad.png":
            raise RuntimeError("bad image")
        Path(output_dir, f"{Path(source).stem}.pdf").write_bytes(b"converted")

    monkeypatch.setattr(helpers, "_convert_image_to_pdf", convert)

    app.convert_images_to_separate_pdfs([str(good), str(bad)], [])

    assert information == []
    assert critical == []
    assert len(warning) == 1
    assert "1/2" in warning[0][2]
    assert "bad.png" in warning[0][2]
    assert "bad image" in warning[0][2]


def test_successful_merged_conversion_reports_success(tmp_path, monkeypatch):
    images = [_make_image(tmp_path / "one.png"), _make_image(tmp_path / "two.png")]
    output = tmp_path / "merged.pdf"
    app = _Harness(tmp_path, fixed_output=output)
    information, warning, critical = _messages(monkeypatch)

    app.convert_images_to_merged_pdf([str(path) for path in images], [])

    assert len(information) == 1
    assert warning == []
    assert critical == []
    with fitz.open(output) as document:
        assert document.page_count == 2


def test_total_merged_load_failure_reports_error_details(tmp_path, monkeypatch):
    images = [_make_image(tmp_path / "one.png"), _make_image(tmp_path / "two.png")]
    output = tmp_path / "merged.pdf"
    output.write_bytes(b"previous")
    app = _Harness(tmp_path, fixed_output=output)
    information, warning, critical = _messages(monkeypatch)
    monkeypatch.setattr(
        ImageToPdfMixin,
        "_open_image_for_pdf",
        lambda _self, _path: (_ for _ in ()).throw(RuntimeError("cannot decode")),
    )

    app.convert_images_to_merged_pdf([str(path) for path in images], [])

    assert information == []
    assert warning == []
    assert len(critical) == 1
    assert "one.png" in critical[0][2]
    assert "two.png" in critical[0][2]
    assert "cannot decode" in critical[0][2]
    assert output.read_bytes() == b"previous"
    assert app.notifications == []


def test_partial_merged_load_failure_reports_warning(tmp_path, monkeypatch):
    good = _make_image(tmp_path / "good.png")
    bad = _make_image(tmp_path / "bad.png")
    output = tmp_path / "merged.pdf"
    app = _Harness(tmp_path, fixed_output=output)
    information, warning, critical = _messages(monkeypatch)
    real_open = ImageToPdfMixin._open_image_for_pdf

    def open_image(self, path):
        if Path(path).name == "bad.png":
            raise RuntimeError("bad decode")
        return real_open(self, path)

    monkeypatch.setattr(ImageToPdfMixin, "_open_image_for_pdf", open_image)

    app.convert_images_to_merged_pdf([str(good), str(bad)], [])

    assert information == []
    assert critical == []
    assert len(warning) == 1
    assert "bad.png" in warning[0][2]
    assert "bad decode" in warning[0][2]
    with fitz.open(output) as document:
        assert document.page_count == 1
