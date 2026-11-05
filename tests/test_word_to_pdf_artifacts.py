from pathlib import Path

import fitz

from utils.pdf_artifacts import run_pdf_engine_with_artifact_validation, validate_pdf_artifact


def _make_pdf(path: Path, label: str = "ok") -> Path:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), label)
    document.save(str(path))
    document.close()
    return path


def _word_options() -> dict:
    return {
        "mode": "preserve_all",
        "quality": "Qualite standard (150 DPI)",
        "compress_images": True,
        "include_metadata": True,
    }


def _word_task(tmp_path: Path) -> tuple[dict, Path, Path]:
    source = tmp_path / "input.docx"
    source.write_bytes(b"docx")
    output = tmp_path / "input.pdf"
    return (
        {
            "index": 0,
            "total": 1,
            "input_path": str(source),
            "output_path": str(output),
        },
        source,
        output,
    )


def _pdf_text(path: Path) -> list[str]:
    with fitz.open(path) as document:
        return [page.get_text().strip() for page in document]


def test_validate_pdf_artifact_rejects_missing_empty_invalid_and_fake_files(tmp_path):
    missing = tmp_path / "missing.pdf"
    empty = tmp_path / "empty.pdf"
    empty.write_bytes(b"")
    text = tmp_path / "text.pdf"
    text.write_bytes(b"not a pdf")
    fake = tmp_path / "fake.pdf"
    fake.write_bytes(b"%PDF")
    valid = _make_pdf(tmp_path / "valid.pdf")

    assert validate_pdf_artifact(str(missing)) == (False, "missing output")
    assert validate_pdf_artifact(str(empty)) == (False, "empty output")
    assert validate_pdf_artifact(str(text)) == (False, "not a PDF")
    assert validate_pdf_artifact(str(fake))[0] is False
    assert validate_pdf_artifact(str(valid)) == (True, "")


def test_staged_engine_preserves_existing_destination_when_output_is_invalid(tmp_path):
    destination = _make_pdf(tmp_path / "output.pdf", "old")
    original = destination.read_bytes()

    ok, detail = run_pdf_engine_with_artifact_validation(
        str(destination),
        lambda target: Path(target).write_bytes(b"%PDF"),
    )

    assert ok is False
    assert "not a PDF" in detail
    assert destination.read_bytes() == original
    assert not list(tmp_path.glob("~fcp_pdf_stage_*"))


def test_staged_engine_replaces_destination_only_after_validation(tmp_path):
    destination = _make_pdf(tmp_path / "output.pdf", "old")

    ok, detail = run_pdf_engine_with_artifact_validation(
        str(destination),
        lambda target: _make_pdf(Path(target), "new"),
    )

    assert (ok, detail) == (True, "")
    assert _pdf_text(destination) == ["new"]


def test_main_task_propagates_engine_true_without_artifact_as_failure(app, tmp_path, monkeypatch):
    task, _source, output = _word_task(tmp_path)
    stale = _make_pdf(output, "stale")
    original = stale.read_bytes()
    monkeypatch.setattr(app, "convert_word_to_pdf_com", lambda *_args: True)
    monkeypatch.setattr(app, "_convert_docx_to_pdf_libreoffice", lambda *_args: False)
    monkeypatch.setattr(app, "_convert_docx_to_pdf_fallback_reportlab", lambda *_args: False)
    monkeypatch.setattr(app, "_postprocess_word_pdf", lambda *_args: None)

    result = app._run_word_to_pdf_task(task, _word_options())

    assert result["success"] is False
    assert "missing output" in result["error"]
    assert output.read_bytes() == original


def test_main_task_propagates_text_only_failure_and_preserves_stale_output(app, tmp_path, monkeypatch):
    task, _source, output = _word_task(tmp_path)
    stale = _make_pdf(output, "stale")
    original = stale.read_bytes()
    monkeypatch.setattr(app, "_convert_docx_to_pdf_text_only_engine", lambda *_args: None)
    monkeypatch.setattr(app, "convert_docx_to_pdf_simple", lambda *_args: False)

    result = app._run_word_to_pdf_task(task, {"mode": "text_only"})

    assert result["success"] is False
    assert result["error"]
    assert output.read_bytes() == original


def test_main_task_accepts_valid_text_only_output(app, tmp_path, monkeypatch):
    task, _source, output = _word_task(tmp_path)
    monkeypatch.setattr(
        app,
        "_convert_docx_to_pdf_text_only_engine",
        lambda _docx, pdf: _make_pdf(Path(pdf), "text"),
    )

    result = app._run_word_to_pdf_task(task, {"mode": "text_only"})

    assert result["success"] is True
    assert result["error"] == ""
    assert _pdf_text(output) == ["text"]


def test_preserve_all_continues_after_invalid_com_output(app, tmp_path, monkeypatch):
    _task, source, output = _word_task(tmp_path)
    calls = []

    def fake_com(docx_path, pdf_path, progress_callback=None):
        calls.append("com")
        Path(pdf_path).write_bytes(b"%PDF")

    def fake_libreoffice(docx_path, pdf_path, progress_callback=None):
        calls.append("libreoffice")
        _make_pdf(Path(pdf_path), "libreoffice")

    monkeypatch.setattr(app, "convert_word_to_pdf_com", fake_com)
    monkeypatch.setattr(app, "_convert_docx_to_pdf_libreoffice", fake_libreoffice)
    monkeypatch.setattr(app, "_convert_docx_to_pdf_fallback_reportlab", lambda *_args: calls.append("reportlab"))
    monkeypatch.setattr(app, "_postprocess_word_pdf", lambda *_args: None)

    ok = app.convert_docx_to_pdf_preserve_all(str(source), str(output), _word_options())

    assert ok is True
    assert calls == ["com", "libreoffice"]
    assert _pdf_text(output) == ["libreoffice"]


def test_preserve_all_total_failure_preserves_destination_and_reports_details(app, tmp_path, monkeypatch):
    _task, source, output = _word_task(tmp_path)
    original = _make_pdf(output, "stale").read_bytes()

    monkeypatch.setattr(app, "convert_word_to_pdf_com", lambda *_args: False)
    monkeypatch.setattr(app, "_convert_docx_to_pdf_libreoffice", lambda *_args: False)
    monkeypatch.setattr(app, "_convert_docx_to_pdf_fallback_reportlab", lambda *_args: False)
    monkeypatch.setattr(app, "_postprocess_word_pdf", lambda *_args: None)

    ok = app.convert_docx_to_pdf_preserve_all(str(source), str(output), _word_options())

    assert ok is False
    assert "COM" in app._last_word_to_pdf_error
    assert "LibreOffice" in app._last_word_to_pdf_error
    assert "ReportLab" in app._last_word_to_pdf_error
    assert output.read_bytes() == original


def test_batch_continues_after_invalid_engine_output(app, tmp_path, monkeypatch):
    _task, source, output = _word_task(tmp_path)
    calls = []

    def fake_com(docx_path, pdf_path, progress_callback=None):
        calls.append("com")
        Path(pdf_path).write_bytes(b"%PDF")

    def fake_libreoffice(docx_path, pdf_path, progress_callback=None):
        calls.append("libreoffice")
        _make_pdf(Path(pdf_path), "libreoffice")

    monkeypatch.setattr(app, "convert_word_to_pdf_com", fake_com)
    monkeypatch.setattr(app, "_convert_docx_to_pdf_libreoffice", fake_libreoffice)
    monkeypatch.setattr(app, "convert_docx_to_pdf_simple", lambda *_args: calls.append("simple") or True)

    assert app._batch_to_pdf(str(source), str(output), ".docx") is True
    assert calls == ["com", "libreoffice"]
    assert _pdf_text(output) == ["libreoffice"]


def test_batch_total_failure_uses_word_error_and_preserves_destination(app, tmp_path, monkeypatch):
    _task, source, output = _word_task(tmp_path)
    original = _make_pdf(output, "stale").read_bytes()

    monkeypatch.setattr(app, "convert_word_to_pdf_com", lambda *_args: False)
    monkeypatch.setattr(app, "_convert_docx_to_pdf_libreoffice", lambda *_args: False)
    monkeypatch.setattr(app, "convert_docx_to_pdf_simple", lambda *_args: False)

    assert app._batch_to_pdf(str(source), str(output), ".docx") is False
    assert app._last_batch_error.startswith("Word to PDF conversion failed:")
    assert output.read_bytes() == original


def test_main_failure_shows_warning_without_success_notification(app, tmp_path, monkeypatch):
    from app.mixins import word_to_pdf as word_module
    from templates import semantic_keys as sk

    source = tmp_path / "input.docx"
    source.write_bytes(b"docx")
    app.files_list_widget.clear()
    app.files_list = [str(source)]
    app.active_templates = {
        sk.WORD_TO_PDF: {
            "mode": "preserve_all",
            "quality": "",
            "compress_images": True,
            "include_metadata": True,
        }
    }
    warnings = []
    infos = []
    notified = []
    converted = []

    class FakeSignal:
        def __init__(self):
            self.slots = []

        def connect(self, slot):
            self.slots.append(slot)

        def emit(self, *args):
            for slot in list(self.slots):
                slot(*args)

    class FakeWorker:
        def __init__(self, tasks, runner):
            self.tasks = tasks
            self.runner = runner
            self.progress = FakeSignal()
            self.file_done = FakeSignal()
            self.finished = FakeSignal()

        def start(self):
            success_count = 0
            failed = []
            for task in self.tasks:
                result = self.runner(task)
                result.update(task)
                if result.get("success"):
                    success_count += 1
                else:
                    failed.append({"name": task["input_path"], "error": result.get("error", "")})
                self.file_done.emit(result)
            self.finished.emit(
                {
                    "success_count": success_count,
                    "total": len(self.tasks),
                    "failed": failed,
                    "total_time": 0.1,
                }
            )

    monkeypatch.setattr(word_module, "ConversionWorker", FakeWorker)
    monkeypatch.setattr(word_module.QMessageBox, "warning", lambda *args: warnings.append(args))
    monkeypatch.setattr(word_module.QMessageBox, "information", lambda *args: infos.append(args))
    monkeypatch.setattr(
        word_module,
        "run_conversion_pipeline",
        lambda *_args, **_kwargs: type("Result", (), {"success": False, "error": "conversion failed"})(),
    )
    monkeypatch.setattr(app, "get_output_directory", lambda: str(tmp_path))
    monkeypatch.setattr(app, "show_progress", lambda *_args: None)
    monkeypatch.setattr(app, "_set_ui_enabled", lambda *_args: None)
    monkeypatch.setattr(app, "record_config_usage", lambda *args: converted.append(args))
    monkeypatch.setattr(app.system_notifier, "send", lambda *args: notified.append(args))
    monkeypatch.setattr(app.db_manager, "add_conversion_record", lambda **_kwargs: None)
    monkeypatch.setattr(app.achievement_system, "check_achievement", lambda *_args: None)

    app.convert_word_to_pdf()

    assert len(warnings) == 1
    assert "input.docx" in warnings[0][2]
    assert infos == []
    assert notified == []
    assert converted == []
