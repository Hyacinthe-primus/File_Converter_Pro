"""Shared pipeline, artifact validation, and workflow integration regressions."""

import threading
from pathlib import Path
from types import SimpleNamespace

import fitz
import pytest
from docx import Document

import utils.conversion_pipeline as pipeline_module
from utils.conversion_pipeline import run_conversion_pipeline
from utils.pdf_artifacts import validate_docx_artifact, validate_pdf_artifact


def _make_pdf(path: Path, pages=("one", "two")) -> Path:
    document = fitz.open()
    for text in pages:
        page = document.new_page()
        page.insert_text((72, 72), text)
    document.save(str(path), garbage=0, deflate=False)
    document.close()
    return path


def _make_docx(path: Path, text: str = "ok") -> Path:
    document = Document()
    document.add_paragraph(text)
    document.save(str(path))
    return path


def _result(success=True, error="", cancelled=False):
    return SimpleNamespace(success=success, error=error, cancelled=cancelled)


def test_pipeline_falls_back_and_commits_only_valid_pdf(tmp_path):
    destination = _make_pdf(tmp_path / "output.pdf", ("old",))
    calls = []

    def invalid(target):
        calls.append("invalid")
        Path(target).write_bytes(b"%PDF")

    def valid(target):
        calls.append("valid")
        _make_pdf(Path(target), ("new", "second"))

    result = run_conversion_pipeline(
        str(destination),
        [("invalid", invalid), ("valid", valid)],
        validate_pdf_artifact,
        stage_dir_prefix="~fcp_pdf_stage_",
        staged_prefix="~fcp_pdf_",
        staged_suffix=".pdf",
    )

    assert result.success is True
    assert calls == ["invalid", "valid"]
    assert result.failures[0][0] == "invalid"
    assert not list(tmp_path.glob("~fcp_pdf_stage_*"))
    with fitz.open(str(destination)) as document:
        assert [page.get_text().strip() for page in document] == ["new", "second"]


def test_pipeline_preserves_existing_pdf_when_all_engines_fail(tmp_path):
    destination = _make_pdf(tmp_path / "output.pdf", ("old",))
    original = destination.read_bytes()

    result = run_conversion_pipeline(
        str(destination),
        [("bad", lambda target: Path(target).write_bytes(b"not a pdf"))],
        validate_pdf_artifact,
        stage_dir_prefix="~fcp_pdf_stage_",
        staged_prefix="~fcp_pdf_",
        staged_suffix=".pdf",
    )

    assert result.success is False
    assert "not a PDF" in result.error
    assert destination.read_bytes() == original
    assert not list(tmp_path.glob("~fcp_pdf_stage_*"))
    assert not list(tmp_path.glob("~fcp_pdf_*"))


def test_pipeline_cancellation_blocks_commit_and_fallbacks(tmp_path):
    destination = _make_pdf(tmp_path / "output.pdf", ("old",))
    original = destination.read_bytes()
    cancel_event = threading.Event()
    calls = []

    def first(target):
        calls.append("first")
        _make_pdf(Path(target), ("cancelled",))
        cancel_event.set()

    def second(target):
        calls.append("second")
        _make_pdf(Path(target), ("second",))

    result = run_conversion_pipeline(
        str(destination),
        [("first", first), ("second", second)],
        validate_pdf_artifact,
        cancel_event=cancel_event,
        stage_mode="file",
        staged_prefix="~fcp_pdf_word_",
        staged_suffix=".pdf",
    )

    assert result.cancelled is True
    assert result.success is False
    assert calls == ["first"]
    assert destination.read_bytes() == original
    assert not list(tmp_path.glob("~fcp_pdf_word_*"))


def test_pipeline_cleanup_failure_after_commit_is_only_a_warning(tmp_path, monkeypatch):
    destination = _make_pdf(tmp_path / "output.pdf", ("old",))

    def fail_cleanup(*_args, **_kwargs):
        raise OSError("temporary file is locked")

    monkeypatch.setattr(pipeline_module.shutil, "rmtree", fail_cleanup)

    def valid(target):
        _make_pdf(Path(target), ("new",))

    result = run_conversion_pipeline(
        str(destination),
        [("valid", valid)],
        validate_pdf_artifact,
        stage_dir_prefix="~fcp_pdf_stage_",
        staged_prefix="~fcp_pdf_",
        staged_suffix=".pdf",
    )

    assert result.success is True
    assert result.cleanup_warning
    with fitz.open(str(destination)) as document:
        assert document.load_page(0).get_text().strip() == "new"


def test_pipeline_validates_docx_artifacts_before_commit(tmp_path):
    destination = _make_docx(tmp_path / "output.docx", "old")
    original = destination.read_bytes()

    result = run_conversion_pipeline(
        str(destination),
        [
            ("invalid", lambda target: Path(target).write_bytes(b"not a docx")),
            ("valid", lambda target: _make_docx(Path(target), "new")),
        ],
        validate_docx_artifact,
        stage_mode="file",
        staged_prefix="~fcp_pdf_word_",
        staged_suffix=".docx",
    )

    assert result.success is True
    assert destination.read_bytes() != original
    assert [p.text for p in Document(str(destination)).paragraphs] == ["new"]
    assert not list(tmp_path.glob("~fcp_pdf_word_*"))


def test_validate_pdf_rejects_truncated_and_corrupted_multi_page_files(tmp_path):
    good = _make_pdf(tmp_path / "good.pdf", ("page one", "page two"))
    assert validate_pdf_artifact(str(good)) == (True, "")

    truncated = tmp_path / "truncated.pdf"
    truncated.write_bytes(good.read_bytes()[:-300])
    assert validate_pdf_artifact(str(truncated))[0] is False

    corrupt = tmp_path / "corrupt.pdf"
    document = fitz.open(str(good))
    second_page = document.load_page(1)
    document.xref_set_key(second_page.xref, "Contents", "[0 0 R]")
    document.save(str(corrupt), garbage=0, deflate=False)
    document.close()
    valid, reason = validate_pdf_artifact(str(corrupt))
    assert valid is False
    assert "page 2" in reason

    corrupt_stream = tmp_path / "corrupt-stream.pdf"
    document = fitz.open(str(good))
    content_xref = document.load_page(1).get_contents()[0]
    document.update_stream(content_xref, b"NOT VALID PDF CONTENT")
    document.save(str(corrupt_stream), garbage=0, deflate=False)
    document.close()
    valid, reason = validate_pdf_artifact(str(corrupt_stream))
    assert valid is False
    assert "syntax error" in reason

    count_mismatch = tmp_path / "count-mismatch.pdf"
    document = fitz.open(str(good))
    for xref in range(1, document.xref_length()):
        try:
            key_type = document.xref_get_key(xref, "Type")
        except Exception:
            continue
        if key_type[1] == "/Pages":
            document.xref_set_key(xref, "Count", "9")
            break
    document.save(str(count_mismatch), garbage=0, deflate=False)
    document.close()
    assert validate_pdf_artifact(str(count_mismatch))[0] is False


def test_validate_pdf_rejects_encrypted_and_accepts_blank_page(tmp_path):
    encrypted = tmp_path / "encrypted.pdf"
    document = fitz.open()
    document.new_page().insert_text((72, 72), "secret")
    document.save(
        str(encrypted),
        encryption=fitz.PDF_ENCRYPT_AES_256,
        owner_pw="owner",
        user_pw="user",
    )
    document.close()
    assert validate_pdf_artifact(str(encrypted))[0] is False

    blank = tmp_path / "blank.pdf"
    document = fitz.open()
    document.new_page()
    document.save(str(blank))
    document.close()
    assert validate_pdf_artifact(str(blank)) == (True, "")


def test_validate_docx_rejects_invalid_files(tmp_path):
    valid = _make_docx(tmp_path / "valid.docx")
    invalid = tmp_path / "invalid.docx"
    invalid.write_bytes(b"not a docx")

    assert validate_docx_artifact(str(valid)) == (True, "")
    assert validate_docx_artifact(str(invalid)) == (False, "not a DOCX")


@pytest.mark.parametrize("module_name", ["watcher", "scheduler"])
def test_automation_docx_and_pdf_routes_use_shared_pipeline(module_name, monkeypatch, tmp_path):
    from context_menu import conversion_helpers
    from tasks import scheduler, watcher

    calls = []

    def fake_pipeline(*args, **kwargs):
        calls.append((args, kwargs))
        return _result()

    monkeypatch.setattr(conversion_helpers, "run_conversion_pipeline", fake_pipeline)
    module = watcher if module_name == "watcher" else scheduler
    src = _make_docx(tmp_path / "input.docx")
    out_dir = tmp_path / "out"

    module._run_conversion("docx_to_pdf", str(src), str(out_dir))

    src_pdf = _make_pdf(tmp_path / "input.pdf")
    module._run_conversion("pdf_to_docx", str(src_pdf), str(out_dir))

    assert len(calls) == 2


def test_main_and_batch_workflows_use_shared_pipeline(app, monkeypatch, tmp_path):
    import app.mixins.batch as batch_module
    import app.mixins.pdf_to_word as pdf_to_word_module
    import app.mixins.word_to_pdf as word_module

    calls = []

    def fake_pipeline(*args, **kwargs):
        calls.append((args, kwargs))
        return _result()

    monkeypatch.setattr(word_module, "run_conversion_pipeline", fake_pipeline)
    monkeypatch.setattr(pdf_to_word_module, "run_conversion_pipeline", fake_pipeline)
    monkeypatch.setattr(batch_module, "run_conversion_pipeline", fake_pipeline)

    options = {
        "mode": "preserve_all",
        "quality": "Standard (150 DPI)",
        "compress_images": True,
        "include_metadata": True,
    }
    src_docx = _make_docx(tmp_path / "input.docx")
    src_pdf = _make_pdf(tmp_path / "input.pdf")
    assert app.convert_docx_to_pdf_preserve_all(str(src_docx), str(tmp_path / "out.pdf"), options)
    assert app.convert_pdf_to_docx_with_charts(str(src_pdf), str(tmp_path / "out-charts.docx"))
    assert app.convert_pdf_to_docx_text_only(str(src_pdf), str(tmp_path / "out.docx"))
    assert app._batch_to_pdf(str(src_docx), str(tmp_path / "batch.pdf"), ".docx")

    assert len(calls) == 4


def test_quick_helpers_use_shared_pipeline(monkeypatch, tmp_path):
    from context_menu import conversion_helpers

    calls = []

    def fake_pipeline(*args, **kwargs):
        calls.append((args, kwargs))
        return _result()

    monkeypatch.setattr(conversion_helpers, "run_conversion_pipeline", fake_pipeline)
    src_docx = _make_docx(tmp_path / "input.docx")
    src_pdf = _make_pdf(tmp_path / "input.pdf")

    conversion_helpers._convert_docx_to_pdf(str(src_docx), str(tmp_path))
    conversion_helpers._convert_pdf_to_docx(str(src_pdf), str(tmp_path), mode="text_only")

    assert len(calls) == 2


def test_quick_docx_cancellation_propagates_through_helper(monkeypatch, tmp_path):
    from context_menu import conversion_helpers

    cancel_event = threading.Event()

    def fake_pipeline(*args, **kwargs):
        assert kwargs["cancel_event"] is cancel_event
        return _result(False, "conversion cancelled", cancelled=True)

    monkeypatch.setattr(conversion_helpers, "run_conversion_pipeline", fake_pipeline)
    src_docx = _make_docx(tmp_path / "input.docx")

    with pytest.raises(conversion_helpers._ConversionCancelled):
        conversion_helpers._convert_docx_to_pdf(str(src_docx), str(tmp_path), cancel_event)


def test_batch_partial_failure_is_reported(app, monkeypatch, tmp_path):
    import app.mixins.batch as batch_module
    import conversion_worker

    app.files_list_widget.clear()
    app.files_list = [str(tmp_path / "a.docx"), str(tmp_path / "b.docx")]
    for name in ("a.docx", "b.docx"):
        (tmp_path / name).write_bytes(b"docx")

    warnings = []
    infos = []
    results = [
        {"success": True, "input_path": str(tmp_path / "a.docx"), "output_path": str(tmp_path / "a.pdf")},
        {"success": False, "input_path": str(tmp_path / "b.docx"), "error": "engine failed"},
    ]

    class FakeSignal:
        def __init__(self):
            self.slots = []

        def connect(self, slot):
            self.slots.append(slot)

        def emit(self, *args):
            for slot in self.slots:
                slot(*args)

    class FakeWorker:
        def __init__(self, _tasks, _runner):
            self.progress = FakeSignal()
            self.file_done = FakeSignal()
            self.finished = FakeSignal()

        def start(self):
            for result in results:
                self.file_done.emit(result)
            self.finished.emit(
                {
                    "success_count": 1,
                    "total": 2,
                    "failed": [{"name": str(tmp_path / "b.docx"), "error": "engine failed"}],
                    "total_time": 0.1,
                }
            )

    monkeypatch.setattr(conversion_worker, "ConversionWorker", FakeWorker)
    monkeypatch.setattr(batch_module.QMessageBox, "warning", lambda *args: warnings.append(args))
    monkeypatch.setattr(batch_module.QMessageBox, "information", lambda *args: infos.append(args))
    monkeypatch.setattr(app, "show_progress", lambda *_args: None)
    monkeypatch.setattr(app.achievement_system, "record_batch_conversion", lambda *_args: None)
    monkeypatch.setattr(app.db_manager, "add_conversion_record", lambda **_kwargs: None)

    app.process_batch_conversion(str(tmp_path), "pdf")

    assert len(warnings) == 1
    assert "b.docx" in warnings[0][2]
    assert "engine failed" in warnings[0][2]
    assert infos == []


def test_watcher_merge_collection_excludes_staging_files(tmp_path):
    from tasks.watcher import MERGE_PDF_ACTION, _collect_merge_files

    normal = _make_pdf(tmp_path / "normal.pdf")
    staging = tmp_path / "~fcp_pdf_staging.pdf"
    _make_pdf(staging)

    assert _collect_merge_files(str(tmp_path), MERGE_PDF_ACTION, recursive=False) == [str(normal)]


def test_existing_output_validation_rejects_corrupt_pdf(tmp_path):
    from tasks.watcher import _existing_output_is_valid

    corrupt = tmp_path / "corrupt.pdf"
    corrupt.write_bytes(b"%PDF")
    valid_pdf = _make_pdf(tmp_path / "valid.pdf")
    valid_docx = _make_docx(tmp_path / "valid.docx")

    assert _existing_output_is_valid(corrupt) is False
    assert _existing_output_is_valid(valid_pdf) is True
    assert _existing_output_is_valid(valid_docx) is True
