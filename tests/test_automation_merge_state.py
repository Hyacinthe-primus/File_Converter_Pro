"""Watcher and Scheduler merge-state regression tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

import fitz

from tasks import scheduler, watcher


def _make_pdf(path: Path, text: str) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(str(path))
    doc.close()
    return path


def _make_docx(path: Path, text: str) -> Path:
    from docx import Document

    doc = Document()
    doc.add_paragraph(text)
    doc.save(str(path))
    return path


def _outputs(root: Path, suffix: str = "pdf") -> list[Path]:
    return sorted(root.glob(f"merged_*.{suffix}"))


def _page_count(path: Path) -> int:
    with fitz.open(str(path)) as doc:
        return doc.page_count


def _merge_state(root: Path, action: str = watcher.MERGE_PDF_ACTION) -> dict:
    state_path = watcher._merge_state_path(str(root), action)
    return json.loads(state_path.read_text())


def _watcher(
    root: Path,
    extension: str = "pdf",
    action: str = watcher.MERGE_PDF_ACTION,
) -> watcher._FolderEventHandler:
    return watcher._FolderEventHandler(
        {
            "name": "test",
            "path": str(root),
            "output_dir": "",
            "rules": {extension: [{"kind": "merge", "action": action, "sort": "none"}]},
            "recursive": False,
            "convert_existing": False,
            "ocr": False,
        }
    )


def _scheduler_task(root: Path) -> dict:
    return {
        "name": "test",
        "path": str(root),
        "output_dir": "",
        "rules": {"pdf": [{"kind": "merge", "action": watcher.MERGE_PDF_ACTION, "sort": "none"}]},
        "recursive": False,
        "trigger": {"type": "cron"},
        "toml_file": None,
        "ocr": False,
    }


def test_watcher_merge_empty_output_dir_does_not_reingest_output(tmp_path):
    _make_pdf(tmp_path / "a.pdf", "A")
    _make_pdf(tmp_path / "b.pdf", "B")
    handler = _watcher(tmp_path)

    handler._fire_merge(watcher.MERGE_PDF_ACTION, "none", str(tmp_path))
    outputs = _outputs(tmp_path)
    assert len(outputs) == 1

    state = _merge_state(tmp_path)
    assert Path(state["output"]["path"]) == outputs[0]

    handler._fire_merge(watcher.MERGE_PDF_ACTION, "none", str(tmp_path))
    assert len(_outputs(tmp_path)) == 1


def test_watcher_process_existing_does_not_reingest_output(tmp_path):
    _make_pdf(tmp_path / "a.pdf", "A")
    _make_pdf(tmp_path / "b.pdf", "B")
    config = {
        "name": "test",
        "path": str(tmp_path),
        "output_dir": "",
        "rules": {"pdf": [{"kind": "merge", "action": watcher.MERGE_PDF_ACTION, "sort": "none"}]},
        "recursive": False,
        "convert_existing": True,
        "ocr": False,
    }
    manager = watcher.WatcherManager()

    manager._process_existing(config)
    assert len(_outputs(tmp_path)) == 1

    manager._process_existing(config)
    assert len(_outputs(tmp_path)) == 1


def test_scheduler_merge_empty_output_dir_does_not_reingest_output(tmp_path):
    _make_pdf(tmp_path / "a.pdf", "A")
    _make_pdf(tmp_path / "b.pdf", "B")
    task = _scheduler_task(tmp_path)

    scheduler._run_task(task)
    outputs = _outputs(tmp_path)
    assert len(outputs) == 1

    state = _merge_state(tmp_path)
    assert Path(state["output"]["path"]) == outputs[0]

    scheduler._run_task(task)
    assert len(_outputs(tmp_path)) == 1


def test_watcher_merge_regenerates_a_missing_output(tmp_path):
    _make_pdf(tmp_path / "a.pdf", "A")
    _make_pdf(tmp_path / "b.pdf", "B")
    handler = _watcher(tmp_path)
    input_files = [str(tmp_path / "a.pdf"), str(tmp_path / "b.pdf")]

    handler._fire_merge(watcher.MERGE_PDF_ACTION, "none", str(tmp_path))
    output = _outputs(tmp_path)[0]
    output.unlink()

    assert watcher._merge_already_done(str(tmp_path), watcher.MERGE_PDF_ACTION, input_files) is False

    handler._fire_merge(watcher.MERGE_PDF_ACTION, "none", str(tmp_path))
    assert len(_outputs(tmp_path)) == 1
    assert _outputs(tmp_path)[0].exists()


def test_scheduler_merge_regenerates_a_missing_output(tmp_path):
    _make_pdf(tmp_path / "a.pdf", "A")
    _make_pdf(tmp_path / "b.pdf", "B")
    task = _scheduler_task(tmp_path)

    scheduler._run_task(task)
    _outputs(tmp_path)[0].unlink()

    scheduler._run_task(task)
    assert len(_outputs(tmp_path)) == 1


def test_watcher_merge_runs_again_when_a_source_is_added(tmp_path):
    _make_pdf(tmp_path / "a.pdf", "A")
    _make_pdf(tmp_path / "b.pdf", "B")
    handler = _watcher(tmp_path)

    handler._fire_merge(watcher.MERGE_PDF_ACTION, "none", str(tmp_path))
    assert len(_outputs(tmp_path)) == 1

    _make_pdf(tmp_path / "c.pdf", "C")
    handler._fire_merge(watcher.MERGE_PDF_ACTION, "none", str(tmp_path))
    outputs = _outputs(tmp_path)
    assert len(outputs) == 2
    assert any(_page_count(path) == 3 for path in outputs)


def test_scheduler_merge_runs_again_when_a_source_is_added(tmp_path):
    _make_pdf(tmp_path / "a.pdf", "A")
    _make_pdf(tmp_path / "b.pdf", "B")
    task = _scheduler_task(tmp_path)

    scheduler._run_task(task)
    assert len(_outputs(tmp_path)) == 1

    _make_pdf(tmp_path / "c.pdf", "C")
    scheduler._run_task(task)
    outputs = _outputs(tmp_path)
    assert len(outputs) == 2
    assert any(_page_count(path) == 3 for path in outputs)


def test_watcher_merge_runs_again_when_a_source_changes(tmp_path):
    first = _make_pdf(tmp_path / "a.pdf", "A")
    _make_pdf(tmp_path / "b.pdf", "B")
    handler = _watcher(tmp_path)

    handler._fire_merge(watcher.MERGE_PDF_ACTION, "none", str(tmp_path))
    assert len(_outputs(tmp_path)) == 1

    stat = first.stat()
    os.utime(first, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    handler._fire_merge(watcher.MERGE_PDF_ACTION, "none", str(tmp_path))
    assert len(_outputs(tmp_path)) == 2


def test_watcher_docx_merge_does_not_reingest_output(tmp_path):
    _make_docx(tmp_path / "a.docx", "A")
    _make_docx(tmp_path / "b.docx", "B")
    handler = _watcher(tmp_path, extension="docx", action=watcher.MERGE_DOCX_ACTION)

    handler._fire_merge(watcher.MERGE_DOCX_ACTION, "none", str(tmp_path))
    assert len(_outputs(tmp_path, "docx")) == 1

    handler._fire_merge(watcher.MERGE_DOCX_ACTION, "none", str(tmp_path))
    assert len(_outputs(tmp_path, "docx")) == 1


def test_pdf_merge_excludes_tracked_image_merge_output(tmp_path):
    _make_pdf(tmp_path / "a.pdf", "A")
    _make_pdf(tmp_path / "b.pdf", "B")
    generated = _make_pdf(tmp_path / "merged_images_20200101_120000.pdf", "generated")
    watcher._save_merge_state(
        str(tmp_path),
        watcher.MERGE_IMAGE_ACTION,
        [],
        output_path=str(generated),
    )
    handler = _watcher(tmp_path)

    handler._fire_merge(watcher.MERGE_PDF_ACTION, "none", str(tmp_path))

    assert len(_outputs(tmp_path)) == 2
    assert max(_page_count(path) for path in _outputs(tmp_path)) == 2


def test_merge_collection_keeps_lookalike_user_file_but_excludes_tracked_output(tmp_path):
    _make_pdf(tmp_path / "a.pdf", "A")
    _make_pdf(tmp_path / "b.pdf", "B")
    handler = _watcher(tmp_path)
    handler._fire_merge(watcher.MERGE_PDF_ACTION, "none", str(tmp_path))

    generated = _outputs(tmp_path)[0]
    lookalike = _make_pdf(tmp_path / "merged_20200101_120000.pdf", "user")
    excluded = watcher._merge_generated_output_paths(str(tmp_path), watcher.MERGE_PDF_ACTION)

    files = watcher._collect_merge_files(
        str(tmp_path),
        watcher.MERGE_PDF_ACTION,
        recursive=False,
        exclude_paths=excluded,
    )

    assert str(generated) not in files
    assert str(lookalike) in files
