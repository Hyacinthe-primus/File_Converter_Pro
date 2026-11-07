"""Destination filename collision regressions."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import fitz
import pytest
from PIL import Image

import context_menu.conversion_helpers as conversion_helpers
import context_menu.window as cm_window


def _make_pdf(path: Path, text: str) -> Path:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    document.save(str(path))
    document.close()
    return path


def _make_image(path: Path) -> Path:
    Image.new("RGB", (16, 12), "white").save(path)
    return path


def _pdf_texts(path: Path) -> list[str]:
    with fitz.open(str(path)) as document:
        return [page.get_text().strip() for page in document]


class _Signal:
    def __init__(self):
        self.slots = []

    def connect(self, slot):
        self.slots.append(slot)

    def emit(self, *args):
        for slot in list(self.slots):
            slot(*args)


class _RunnerWorker:
    def __init__(self, tasks, runner):
        self.tasks = tasks
        self.runner = runner
        self.progress = _Signal()
        self.file_done = _Signal()
        self.finished = _Signal()
        self.error = _Signal()

    def start(self):
        success_count = 0
        failed = []
        for task in self.tasks:
            result = self.runner(task)
            result.update(task)
            if result.get("success"):
                success_count += 1
            else:
                failed.append(
                    {"name": task["input_path"], "error": result.get("error", "")}
                )
            self.file_done.emit(result)
        self.finished.emit(
            {
                "success_count": success_count,
                "total": len(self.tasks),
                "failed": failed,
                "total_time": 0.01,
            }
        )


def _prepare_batch_app(app, monkeypatch, sources):
    app.config["backup_before_conversion"] = False
    app.files_list = [str(path) for path in sources]
    app.files_list_widget.clear()
    monkeypatch.setattr(app, "cleanup_temp_files", lambda: None)
    monkeypatch.setattr(app, "show_progress", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app.db_manager, "add_conversion_record", lambda **_kwargs: None)
    monkeypatch.setattr(
        app.achievement_system, "record_batch_conversion", lambda *_args, **_kwargs: None
    )
    import conversion_worker
    from app.mixins import batch as batch_module

    monkeypatch.setattr(conversion_worker, "ConversionWorker", _RunnerWorker)
    monkeypatch.setattr(
        batch_module.QMessageBox,
        "information",
        staticmethod(lambda *_args: None),
    )
    monkeypatch.setattr(
        batch_module.QMessageBox,
        "warning",
        staticmethod(lambda *_args: None),
    )


def test_batch_duplicate_basenames_get_unique_outputs(app, monkeypatch, tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    first = _make_image(first_dir / "same.png")
    second = _make_image(second_dir / "same.png")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    existing = output_dir / "same.pdf"
    existing.write_bytes(b"existing destination")

    _prepare_batch_app(app, monkeypatch, [first, second])
    app.process_batch_conversion(str(output_dir), "pdf")

    assert existing.read_bytes() == b"existing destination"
    outputs = sorted(output_dir.glob("same_*.pdf"))
    assert [path.name for path in outputs] == ["same_1.pdf", "same_2.pdf"]
    for path in outputs:
        assert _pdf_texts(path)


def test_batch_failure_removes_reserved_destination(app, monkeypatch, tmp_path):
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image")
    output_dir = tmp_path / "out"
    output_dir.mkdir()

    _prepare_batch_app(app, monkeypatch, [bad])
    app.process_batch_conversion(str(output_dir), "pdf")

    assert not (output_dir / "bad.pdf").exists()
    assert not list(output_dir.glob("~fcp_*"))


def test_quick_image_merges_in_same_second_get_unique_names(monkeypatch, tmp_path):
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    source = _make_image(output_dir / "image.png")
    existing = output_dir / "merged_images_20240101_120000.pdf"
    existing.write_bytes(b"existing destination")
    monkeypatch.setattr(
        conversion_helpers.time,
        "strftime",
        lambda _format: "20240101_120000",
    )
    monkeypatch.setattr(
        cm_window,
        "_load_quick_config",
        lambda: {"backup_before_conversion": False},
    )

    for _ in range(2):
        cm_window.ConversionThread([str(source)], "images_to_pdf_merged").run()

    outputs = sorted(output_dir.glob("merged_images_20240101_120000*.pdf"))
    assert [path.name for path in outputs] == [
        "merged_images_20240101_120000.pdf",
        "merged_images_20240101_120000_1.pdf",
        "merged_images_20240101_120000_2.pdf",
    ]
    assert existing.read_bytes() == b"existing destination"
    assert _pdf_texts(outputs[1])
    assert _pdf_texts(outputs[2])


def test_concurrent_merges_claim_distinct_destinations(monkeypatch, tmp_path):
    first = _make_pdf(tmp_path / "first.pdf", "first")
    second = _make_pdf(tmp_path / "second.pdf", "second")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    monkeypatch.setattr(
        conversion_helpers.time,
        "strftime",
        lambda _format: "20240101_120000",
    )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(
                conversion_helpers._merge_pdfs,
                [str(source)],
                str(output_dir),
                "none",
            )
            for source in (first, second)
        ]
        outputs = [future.result() for future in futures]

    assert len(set(outputs)) == 2
    assert all(Path(path).is_file() for path in outputs)
    assert all(_pdf_texts(Path(path)) for path in outputs)


def test_failed_merge_releases_reservation_and_preserves_existing(monkeypatch, tmp_path):
    invalid = tmp_path / "invalid.pdf"
    invalid.write_bytes(b"not a PDF")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    existing = output_dir / "merged_20240101_120000.pdf"
    existing.write_bytes(b"existing destination")
    monkeypatch.setattr(
        conversion_helpers.time,
        "strftime",
        lambda _format: "20240101_120000",
    )

    with pytest.raises(RuntimeError, match="PDF merge failed"):
        conversion_helpers._merge_pdfs([str(invalid)], str(output_dir), "none")

    assert existing.read_bytes() == b"existing destination"
    assert sorted(path.name for path in output_dir.glob("merged_*.pdf")) == [
        existing.name
    ]
    assert not list(output_dir.glob("~fcp_*"))
