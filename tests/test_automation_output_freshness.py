"""Watcher/Scheduler output validation and freshness regressions."""

import logging
import os
from pathlib import Path

import fitz
from PIL import Image

from tasks import scheduler, watcher


def _make_pdf(path: Path, text: str = "content") -> Path:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    document.save(str(path))
    document.close()
    return path


def _make_png(path: Path) -> Path:
    Image.new("RGB", (8, 8), (20, 100, 200)).save(path)
    return path


def _scheduler_task(root: Path, output_dir: Path) -> dict:
    return {
        "name": "test",
        "path": str(root),
        "output_dir": str(output_dir),
        "rules": {"txt": [{"kind": "convert", "fmt": "pdf"}]},
        "recursive": False,
        "trigger": {"type": "interval"},
        "toml_file": None,
        "ocr": False,
    }


def test_existing_output_validation_rejects_invalid_and_wrong_formats(tmp_path):
    valid_png = _make_png(tmp_path / "valid.png")
    wrong_png = tmp_path / "wrong.png"
    wrong_png.write_bytes(b"%PDF-1.7\nnot a png")
    empty_png = tmp_path / "empty.png"
    empty_png.write_bytes(b"")

    assert watcher._existing_output_is_valid(valid_png) is True
    assert watcher._existing_output_is_valid(wrong_png) is False
    assert watcher._existing_output_is_valid(empty_png) is False
    assert watcher._existing_output_is_valid(tmp_path / "missing.pdf") is False


def test_scheduler_skips_unchanged_source_with_current_valid_output(
    monkeypatch, tmp_path
):
    source = tmp_path / "source.txt"
    source.write_text("source")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    _make_pdf(output_dir / "source.pdf")
    calls = []
    monkeypatch.setattr(
        scheduler, "_run_conversion", lambda *args, **kwargs: calls.append(args)
    )
    task = _scheduler_task(tmp_path, output_dir)

    scheduler._run_task(task)
    scheduler._run_task(task)

    assert calls == []


def test_scheduler_reprocesses_modified_source_then_deduplicates(
    monkeypatch, tmp_path
):
    source = tmp_path / "source.txt"
    source.write_text("source")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    output = _make_pdf(output_dir / "source.pdf")
    old = 1_000_000_000
    os.utime(output, ns=(old, old))
    calls = []

    def fake_conversion(_conversion_type, _src, directory, **_kwargs):
        calls.append(_src)
        _make_pdf(Path(directory) / "source.pdf", "new")

    monkeypatch.setattr(scheduler, "_run_conversion", fake_conversion)
    task = _scheduler_task(tmp_path, output_dir)

    scheduler._run_task(task)
    scheduler._run_task(task)

    assert calls == [str(source)]


def test_scheduler_stale_output_from_noop_conversion_is_not_accepted(
    monkeypatch, tmp_path, caplog
):
    source = tmp_path / "source.txt"
    source.write_text("source")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    output = _make_pdf(output_dir / "source.pdf")
    old = 1_000_000_000
    os.utime(output, ns=(old, old))
    calls = []
    monkeypatch.setattr(
        scheduler, "_run_conversion", lambda *args, **kwargs: calls.append(args)
    )
    caplog.set_level(logging.ERROR, logger="tasks.scheduler")

    scheduler._run_task(_scheduler_task(tmp_path, output_dir))
    scheduler._run_task(_scheduler_task(tmp_path, output_dir))

    assert len(calls) == 2
    assert "output was not updated by the current conversion" in caplog.text


def test_scheduler_rejects_invalid_output_from_current_attempt(
    monkeypatch, tmp_path, caplog
):
    source = tmp_path / "source.txt"
    source.write_text("source")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    calls = []

    def fake_conversion(_conversion_type, _src, directory, **_kwargs):
        calls.append(_src)
        (Path(directory) / "source.pdf").write_bytes(b"not a PDF")

    monkeypatch.setattr(scheduler, "_run_conversion", fake_conversion)
    caplog.set_level(logging.ERROR, logger="tasks.scheduler")

    scheduler._run_task(_scheduler_task(tmp_path, output_dir))
    scheduler._run_task(_scheduler_task(tmp_path, output_dir))

    assert len(calls) == 2
    assert "not a PDF" in caplog.text


def test_watcher_rejects_stale_preexisting_output(monkeypatch, tmp_path, caplog):
    source = tmp_path / "source.txt"
    source.write_text("source")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    _make_pdf(output_dir / "source.pdf")
    monkeypatch.setattr(watcher, "_run_conversion", lambda *args, **kwargs: None)
    handler = watcher._FolderEventHandler(
        {
            "name": "test",
            "path": str(tmp_path),
            "output_dir": str(output_dir),
            "rules": {},
            "recursive": False,
            "convert_existing": False,
            "ocr": False,
        }
    )
    caplog.set_level(logging.ERROR, logger="tasks.watcher")

    handler._dispatch_convert(str(source), "txt", "pdf", str(output_dir))

    assert "output was not updated by the current conversion" in caplog.text


def test_watcher_rejects_invalid_generated_output(monkeypatch, tmp_path, caplog):
    source = tmp_path / "source.txt"
    source.write_text("source")
    output_dir = tmp_path / "out"
    output_dir.mkdir()

    def fake_conversion(_conversion_type, _src, directory, **_kwargs):
        (Path(directory) / "source.pdf").write_bytes(b"not a PDF")

    monkeypatch.setattr(watcher, "_run_conversion", fake_conversion)
    handler = watcher._FolderEventHandler(
        {
            "name": "test",
            "path": str(tmp_path),
            "output_dir": str(output_dir),
            "rules": {},
            "recursive": False,
            "convert_existing": False,
            "ocr": False,
        }
    )
    caplog.set_level(logging.ERROR, logger="tasks.watcher")

    handler._dispatch_convert(str(source), "txt", "pdf", str(output_dir))

    assert "not a PDF" in caplog.text


def test_invalid_merge_output_is_not_registered(tmp_path):
    source = _make_pdf(tmp_path / "source.pdf")
    invalid = tmp_path / "merged_invalid.pdf"
    invalid.write_bytes(b"not a PDF")

    watcher._save_merge_state(
        str(tmp_path),
        watcher.MERGE_PDF_ACTION,
        [str(source)],
        output_path=str(invalid),
    )

    assert watcher._merge_already_done(
        str(tmp_path), watcher.MERGE_PDF_ACTION, [str(source)]
    ) is False
