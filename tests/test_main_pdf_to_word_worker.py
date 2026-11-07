"""Main PDF-to-Word worker, cancellation, and reporting regressions."""

import threading
from pathlib import Path
from types import SimpleNamespace

import fitz
from docx import Document
from PIL import Image

import app.mixins.pdf_to_word as pdf_to_word_module
from app.mixins.pdf_to_word import PdfToWordMixin
from templates import semantic_keys as sk
from translations import TranslationManager


class _EmptySelection:
    @staticmethod
    def selectedItems():
        return []


class _Signal:
    def __init__(self):
        self.slots = []

    def connect(self, slot):
        self.slots.append(slot)

    def emit(self, *args):
        for slot in list(self.slots):
            slot(*args)


class _FakeWorker:
    instances = []

    def __init__(self, tasks, runner):
        self.tasks = tasks
        self.runner = runner
        self.progress = _Signal()
        self.file_done = _Signal()
        self.finished = _Signal()
        self.error = _Signal()
        self.started = False
        _FakeWorker.instances.append(self)

    def start(self):
        self.started = True

    def requestInterruption(self):
        pass


class _Harness(PdfToWordMixin):
    def __init__(self, output_dir: Path, mode: str):
        self.output_dir = output_dir
        self.config = {
            "enable_system_notifications": False,
            "backup_before_conversion": False,
            "pdf_to_word_mode": mode,
        }
        self.active_templates = {sk.PDF_TO_WORD: {"mode": mode}}
        self.files_list_widget = _EmptySelection()
        self.current_language = "en"
        self.files_list = []
        self.progress_values = []
        self.ui_enabled = []
        self.records = []
        self.notifications = []
        self.config_usage = []
        self.progress_bar = SimpleNamespace(setValue=self.progress_values.append)
        self.db_manager = SimpleNamespace(
            add_conversion_record=lambda **kwargs: self.records.append(kwargs)
        )
        self.achievement_system = SimpleNamespace(
            record_conversion=lambda *_args, **_kwargs: None,
            mark_format_as_used=lambda *_args, **_kwargs: None,
        )
        self.system_notifier = SimpleNamespace(
            send=lambda *args, **_kwargs: self.notifications.append(args)
        )
        self._tm = TranslationManager()
        self._tm.set_language("en")

    def get_output_directory(self, _filename=None):
        return str(self.output_dir)

    def translate_text(self, text):
        return self._tm.translate_text(text)

    def show_progress(self, *_args, **_kwargs):
        return None

    def _set_ui_enabled(self, enabled):
        self.ui_enabled.append(enabled)

    def record_config_usage(self, *_args, **_kwargs):
        self.config_usage.append(_args)


def _make_text_pdf(path: Path, text: str = "Main PDF text") -> Path:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    document.save(str(path))
    document.close()
    return path


def _make_image_pdf(path: Path) -> Path:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "PDF with image")
    image_bytes = Path(path).with_suffix(".png")
    Image.new("RGB", (40, 30), (120, 30, 30)).save(image_bytes)
    page.insert_image(fitz.Rect(72, 100, 180, 180), filename=str(image_bytes))
    document.save(str(path))
    document.close()
    return path


def _messages(monkeypatch):
    information, warning, critical = [], [], []
    monkeypatch.setattr(
        pdf_to_word_module.QMessageBox,
        "information",
        staticmethod(lambda *args: information.append(args)),
    )
    monkeypatch.setattr(
        pdf_to_word_module.QMessageBox,
        "warning",
        staticmethod(lambda *args: warning.append(args)),
    )
    monkeypatch.setattr(
        pdf_to_word_module.QMessageBox,
        "critical",
        staticmethod(lambda *args: critical.append(args)),
    )
    return information, warning, critical


def _run_worker_synchronously(monkeypatch):
    from conversion_worker import ConversionWorker

    monkeypatch.setattr(ConversionWorker, "start", lambda self: self.run())


def test_text_only_path_starts_worker_without_converting_synchronously(
    monkeypatch, tmp_path
):
    source = _make_text_pdf(tmp_path / "source.pdf")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    app = _Harness(output_dir, "text_only")
    app.files_list = [str(source)]
    _FakeWorker.instances.clear()
    import conversion_worker

    monkeypatch.setattr(conversion_worker, "ConversionWorker", _FakeWorker)
    converted = []
    app.convert_pdf_to_docx_text_only = lambda *_args, **_kwargs: converted.append(True)

    app.convert_pdfs_without_images([str(source)])

    assert len(_FakeWorker.instances) == 1
    assert _FakeWorker.instances[0].started is True
    assert converted == []


def test_text_only_worker_produces_valid_docx(monkeypatch, tmp_path):
    source = _make_text_pdf(tmp_path / "source.pdf")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    app = _Harness(output_dir, "text_only")
    app.files_list = [str(source)]
    _messages(monkeypatch)
    _run_worker_synchronously(monkeypatch)

    app.convert_pdf_to_word()

    from conversion_worker import ConversionWorker

    assert isinstance(app._pdf_to_word_worker, ConversionWorker)
    output = output_dir / "source.docx"
    assert output.is_file()
    assert any("Main PDF text" in p.text for p in Document(output).paragraphs)
    assert app.progress_values[-1] == 100
    assert app.ui_enabled == [False, True]


def test_with_images_worker_produces_valid_docx(monkeypatch, tmp_path):
    source = _make_image_pdf(tmp_path / "source.pdf")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    app = _Harness(output_dir, "with_images")
    app.files_list = [str(source)]
    _messages(monkeypatch)
    _run_worker_synchronously(monkeypatch)
    app._try_word_com_pdf_to_docx = lambda *_args: False
    app._convert_pdf_to_docx_pdf2docx_with_charts = lambda *_args: False

    app.convert_pdf_to_word()

    from conversion_worker import ConversionWorker

    assert isinstance(app._pdf_to_word_worker, ConversionWorker)
    output = output_dir / "source.docx"
    assert output.is_file()
    assert Document(output).paragraphs


def test_worker_failure_is_reported(monkeypatch, tmp_path):
    source = _make_text_pdf(tmp_path / "source.pdf")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    app = _Harness(output_dir, "text_only")
    app.files_list = [str(source)]
    information, warning, critical = _messages(monkeypatch)
    _run_worker_synchronously(monkeypatch)
    app.convert_pdf_to_docx_text_only = lambda *_args, **_kwargs: False
    app._last_pdf_to_word_error = "text conversion failed"

    app.convert_pdf_to_word()

    assert information == []
    assert critical == []
    assert len(warning) == 1
    assert "text conversion failed" in warning[0][2]


def test_worker_cancellation_does_not_report_success(monkeypatch, tmp_path):
    source = _make_text_pdf(tmp_path / "source.pdf")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    app = _Harness(output_dir, "text_only")
    app.files_list = [str(source)]
    information, warning, critical = _messages(monkeypatch)
    _run_worker_synchronously(monkeypatch)

    def cancel_conversion(_pdf, _out, cancel_event=None):
        app.cancel_pdf_to_word()
        return False

    app.convert_pdf_to_docx_text_only = cancel_conversion

    app.convert_pdf_to_word()

    assert information == []
    assert critical == []
    assert len(warning) == 1
    assert "cancelled" in warning[0][2].lower()
    assert app.notifications == []


def test_text_only_cancellation_preserves_existing_destination(tmp_path):
    source = _make_text_pdf(tmp_path / "source.pdf")
    output = tmp_path / "source.docx"
    output.write_bytes(b"old destination")
    app = _Harness(tmp_path, "text_only")
    cancel_event = threading.Event()
    cancel_event.set()

    assert (
        app.convert_pdf_to_docx_text_only(
            str(source), str(output), cancel_event=cancel_event
        )
        is False
    )
    assert output.read_bytes() == b"old destination"
    assert not list(tmp_path.glob("~fcp_pdf_word_*"))


def test_with_images_cancellation_preserves_existing_destination(tmp_path):
    source = _make_image_pdf(tmp_path / "source.pdf")
    output = tmp_path / "source.docx"
    output.write_bytes(b"old destination")
    app = _Harness(tmp_path, "with_images")
    cancel_event = threading.Event()
    cancel_event.set()

    assert (
        app.convert_pdf_to_docx_improved(
            str(source), str(output), cancel_event=cancel_event
        )
        is False
    )
    assert output.read_bytes() == b"old destination"
    assert not list(tmp_path.glob("~fcp_pdf_word_*"))
