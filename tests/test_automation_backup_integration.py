"""Backup policy integration tests for Watcher and Scheduler."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest
from PIL import Image

import config as config_module
import context_menu.conversion_helpers as conversion_helpers
from tasks import scheduler, watcher


def _use_config(monkeypatch, config):
    class FakeConfigManager:
        def load_config(self):
            return config

    monkeypatch.setattr(config_module, "ConfigManager", FakeConfigManager)


def _enable_backups(monkeypatch, enabled: bool = True) -> None:
    _use_config(monkeypatch, {"backup_before_conversion": enabled})


def _image(path: Path) -> Path:
    Image.new("RGB", (16, 12), "blue").save(path, format="PNG")
    return path


def _pdf(path: Path) -> Path:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "backup")
    document.save(str(path))
    document.close()
    return path


def _failure(source: Path):
    from converter.helpers import SourceBackupResult

    return SourceBackupResult(False, {}, {str(source): "backup denied"})


def _raise_backup_failure(_sources, **_kwargs):
    from converter.helpers import BackupError

    raise BackupError("Source backup failed: backup denied")


def test_watcher_special_conversion_backs_up_before_conversion(monkeypatch, tmp_path):
    _enable_backups(monkeypatch)
    source = _image(tmp_path / "image.png")
    out_dir = tmp_path / "out"
    calls = []

    def convert(src, dst):
        calls.append(Path(f"{src}.bak").is_file())

    monkeypatch.setattr(conversion_helpers, "_convert_image_to_pdf", convert)

    watcher._run_conversion("image_to_pdf", str(source), str(out_dir), ocr=False)

    assert calls == [True]
    assert Path(f"{source}.bak").is_file()


def test_watcher_generic_conversion_does_not_duplicate_backup(monkeypatch, tmp_path):
    _enable_backups(monkeypatch)
    source = tmp_path / "note.txt"
    source.write_text("hello", encoding="utf-8")
    out_dir = tmp_path / "out"

    watcher._run_conversion("txt_to_pdf", str(source), str(out_dir))

    assert Path(f"{source}.bak").read_text(encoding="utf-8") == "hello"
    assert not Path(f"{source}.bak.1").exists()
    assert (out_dir / "note.pdf").is_file()


def test_watcher_special_conversion_with_backups_disabled(monkeypatch, tmp_path):
    _enable_backups(monkeypatch, enabled=False)
    source = _image(tmp_path / "image.png")
    out_dir = tmp_path / "out"
    calls = []
    monkeypatch.setattr(conversion_helpers, "_convert_image_to_pdf", lambda *args: calls.append(True))

    watcher._run_conversion("image_to_pdf", str(source), str(out_dir), ocr=False)

    assert calls == [True]
    assert not Path(f"{source}.bak").exists()


def test_watcher_configuration_failure_blocks_special_conversion(monkeypatch, tmp_path):
    class BrokenConfigManager:
        def load_config(self):
            raise RuntimeError("config unavailable")

    monkeypatch.setattr(config_module, "ConfigManager", BrokenConfigManager)
    source = _image(tmp_path / "image.png")
    out_dir = tmp_path / "out"
    calls = []
    monkeypatch.setattr(conversion_helpers, "_convert_image_to_pdf", lambda *args: calls.append(True))

    try:
        watcher._run_conversion("image_to_pdf", str(source), str(out_dir), ocr=False)
    except RuntimeError as exc:
        assert "configuration unavailable" in str(exc)
    else:
        raise AssertionError("expected configuration failure")

    assert calls == []
    assert not out_dir.exists()


def test_watcher_missing_backup_policy_blocks_special_conversion(monkeypatch, tmp_path):
    _use_config(monkeypatch, {"pdf_to_word_mode": "with_images"})
    source = _image(tmp_path / "image.png")
    out_dir = tmp_path / "out"
    calls = []
    monkeypatch.setattr(conversion_helpers, "_convert_image_to_pdf", lambda *args: calls.append(True))

    try:
        watcher._run_conversion("image_to_pdf", str(source), str(out_dir), ocr=False)
    except RuntimeError as exc:
        assert "Backup policy is missing" in str(exc)
    else:
        raise AssertionError("expected missing backup policy failure")

    assert calls == []
    assert not out_dir.exists()


@pytest.mark.parametrize("value", ["yes", 1, None])
def test_watcher_invalid_backup_policy_blocks_special_conversion(monkeypatch, tmp_path, value):
    _use_config(monkeypatch, {"backup_before_conversion": value})
    source = _image(tmp_path / "image.png")
    out_dir = tmp_path / "out"
    calls = []
    monkeypatch.setattr(conversion_helpers, "_convert_image_to_pdf", lambda *args: calls.append(True))

    try:
        watcher._run_conversion("image_to_pdf", str(source), str(out_dir), ocr=False)
    except RuntimeError as exc:
        assert "Backup policy is not a boolean" in str(exc)
    else:
        raise AssertionError("expected invalid backup policy failure")

    assert calls == []


def test_watcher_configuration_failure_blocks_merge(monkeypatch, tmp_path):
    class BrokenConfigManager:
        def load_config(self):
            raise RuntimeError("config unavailable")

    monkeypatch.setattr(config_module, "ConfigManager", BrokenConfigManager)
    first = _pdf(tmp_path / "first.pdf")
    second = _pdf(tmp_path / "second.pdf")
    out_dir = tmp_path / "out"
    calls = []
    monkeypatch.setattr(
        conversion_helpers,
        "_merge_pdfs",
        lambda files, dst, order, **kwargs: calls.append(list(files)),
    )

    try:
        watcher._run_merge("merge_pdf_none", [str(first), str(second)], str(out_dir))
    except RuntimeError as exc:
        assert "configuration unavailable" in str(exc)
    else:
        raise AssertionError("expected configuration failure")

    assert calls == []
    assert not out_dir.exists()


def test_watcher_backup_failure_prevents_special_conversion(monkeypatch, tmp_path):
    _enable_backups(monkeypatch)
    source = _image(tmp_path / "image.png")
    out_dir = tmp_path / "out"
    calls = []
    monkeypatch.setattr(watcher, "prepare_operation_backups", _raise_backup_failure)
    monkeypatch.setattr(conversion_helpers, "_convert_image_to_pdf", lambda *args: calls.append(True))

    try:
        watcher._run_conversion("image_to_pdf", str(source), str(out_dir), ocr=False)
    except RuntimeError as exc:
        assert "backup denied" in str(exc)
    else:
        raise AssertionError("expected backup failure")

    assert calls == []
    assert not (out_dir / "image.pdf").exists()


def test_watcher_merge_backs_up_every_input(monkeypatch, tmp_path):
    _enable_backups(monkeypatch)
    first = _pdf(tmp_path / "first.pdf")
    second = _pdf(tmp_path / "second.pdf")
    out_dir = tmp_path / "out"
    calls = []
    monkeypatch.setattr(
        conversion_helpers,
        "_merge_pdfs",
        lambda files, dst, order, **kwargs: calls.append(list(files)),
    )

    watcher._run_merge("merge_pdf_none", [str(first), str(second)], str(out_dir))

    assert Path(f"{first}.bak").is_file()
    assert Path(f"{second}.bak").is_file()
    assert calls


def test_watcher_merge_backup_failure_prevents_merge(monkeypatch, tmp_path):
    _enable_backups(monkeypatch)
    first = _pdf(tmp_path / "first.pdf")
    second = _pdf(tmp_path / "second.pdf")
    out_dir = tmp_path / "out"
    calls = []
    monkeypatch.setattr(watcher, "prepare_operation_backups", _raise_backup_failure)
    monkeypatch.setattr(
        conversion_helpers,
        "_merge_pdfs",
        lambda files, dst, order, **kwargs: calls.append(list(files)),
    )

    try:
        watcher._run_merge("merge_pdf_none", [str(first), str(second)], str(out_dir))
    except RuntimeError as exc:
        assert "backup denied" in str(exc)
    else:
        raise AssertionError("expected backup failure")

    assert calls == []


def test_scheduler_configuration_failure_blocks_special_conversion(monkeypatch, tmp_path):
    class BrokenConfigManager:
        def load_config(self):
            raise RuntimeError("config unavailable")

    monkeypatch.setattr(config_module, "ConfigManager", BrokenConfigManager)
    source = _image(tmp_path / "image.png")
    out_dir = tmp_path / "out"
    calls = []
    monkeypatch.setattr(conversion_helpers, "_convert_image_to_pdf", lambda *args: calls.append(True))

    try:
        scheduler._run_conversion("image_to_pdf", str(source), str(out_dir), ocr=False)
    except RuntimeError as exc:
        assert "configuration unavailable" in str(exc)
    else:
        raise AssertionError("expected configuration failure")

    assert calls == []


def test_scheduler_task_retries_configuration_for_other_files(monkeypatch, tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    _image(input_dir / "first.png")
    _image(input_dir / "second.png")
    output_dir = tmp_path / "out"
    calls = []

    class RecoveringConfigManager:
        calls = 0

        def load_config(self):
            type(self).calls += 1
            if self.calls == 1:
                raise RuntimeError("temporary config failure")
            return {"backup_before_conversion": False}

    monkeypatch.setattr(config_module, "ConfigManager", RecoveringConfigManager)
    monkeypatch.setattr(conversion_helpers, "_convert_image_to_pdf", lambda *args: calls.append(True))

    scheduler._run_task(
        {
            "name": "backup-recovery",
            "path": str(input_dir),
            "output_dir": str(output_dir),
            "recursive": False,
            "rules": {"png": [{"kind": "convert", "fmt": "pdf"}]},
            "trigger": {"type": "interval"},
        }
    )

    assert len(calls) == 1


def test_scheduler_generic_conversion_does_not_duplicate_backup(monkeypatch, tmp_path):
    _enable_backups(monkeypatch)
    source = tmp_path / "note.txt"
    source.write_text("hello", encoding="utf-8")
    out_dir = tmp_path / "out"

    scheduler._run_conversion("txt_to_pdf", str(source), str(out_dir))

    assert Path(f"{source}.bak").read_text(encoding="utf-8") == "hello"
    assert not Path(f"{source}.bak.1").exists()
    assert (out_dir / "note.pdf").is_file()


def test_scheduler_special_conversion_backs_up(monkeypatch, tmp_path):
    _enable_backups(monkeypatch)
    source = _image(tmp_path / "image.png")
    out_dir = tmp_path / "out"
    calls = []
    monkeypatch.setattr(conversion_helpers, "_convert_image_to_pdf", lambda *args: calls.append(True))

    scheduler._run_conversion("image_to_pdf", str(source), str(out_dir), ocr=False)

    assert Path(f"{source}.bak").is_file()
    assert calls


def test_scheduler_task_continues_after_one_failed_conversion(monkeypatch, tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    first = input_dir / "first.txt"
    second = input_dir / "second.txt"
    first.write_text("first", encoding="utf-8")
    second.write_text("second", encoding="utf-8")
    output_dir = tmp_path / "out"
    calls = []

    def run_conversion(_conversion_type, source, _output_dir, **_kwargs):
        calls.append(Path(source).name)
        if Path(source).name == "first.txt":
            raise RuntimeError("Source backup failed: backup denied")

    monkeypatch.setattr(scheduler, "_run_conversion", run_conversion)

    scheduler._run_task(
        {
            "name": "backup-test",
            "path": str(input_dir),
            "output_dir": str(output_dir),
            "recursive": False,
            "rules": {"txt": [{"kind": "convert", "fmt": "pdf"}]},
            "trigger": {"type": "interval"},
        }
    )

    assert calls == ["first.txt", "second.txt"]


def test_scheduler_merge_backs_up_every_input(monkeypatch, tmp_path):
    _enable_backups(monkeypatch)
    first = _pdf(tmp_path / "first.pdf")
    second = _pdf(tmp_path / "second.pdf")
    out_dir = tmp_path / "out"
    calls = []
    monkeypatch.setattr(
        conversion_helpers,
        "_merge_pdfs",
        lambda files, dst, order, **kwargs: calls.append(list(files)),
    )

    scheduler._run_merge("merge_pdf_none", [str(first), str(second)], str(out_dir))

    assert Path(f"{first}.bak").is_file()
    assert Path(f"{second}.bak").is_file()
    assert calls
