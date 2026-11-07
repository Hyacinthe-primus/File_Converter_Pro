"""Backup policy integration tests for Main, Batch, and engine paths."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest
from PIL import Image
from PySide6.QtWidgets import QDialog

import config as config_module
import context_menu.conversion_helpers as conversion_helpers
import converter.converters as converter_module
import dialogs.merge_order_dialog as merge_dialog_module
from app.mixins import image_to_pdf as image_module
from app.mixins import pdf_operations as pdf_operations_module
from app.mixins import pdf_to_word as pdf_module
from app.mixins import word_to_pdf as word_module
from app.mixins.batch import BatchMixin
from converter.converters import AdvancedConverterEngine
from converter.helpers import BackupError, SourceBackupResult, prepare_operation_backups, prepare_source_backups
from templates import semantic_keys as sk


def _image(path: Path, fmt: str = "PNG") -> Path:
    Image.new("RGB", (16, 12), "blue").save(path, format=fmt)
    return path


def _pdf(path: Path) -> Path:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "backup integration")
    document.save(str(path))
    document.close()
    return path


def _docx(path: Path) -> Path:
    from docx import Document

    Document().save(str(path))
    return path


def _failure(source: Path, reason: str = "backup denied") -> SourceBackupResult:
    return SourceBackupResult(False, {}, {str(source): reason})


def _raise_backup_failure(_sources, **_kwargs):
    raise BackupError("Backup failed: backup denied")


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
        type(self).instances.append(self)

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
                "total_time": 0.01,
            }
        )


class _NoopWorker:
    instances = []

    def __init__(self, *args, **kwargs):
        self.progress = _Signal()
        self.file_done = _Signal()
        self.finished = _Signal()
        type(self).instances.append(self)

    def start(self):
        return None


def _prepare_app(app, tmp_path, monkeypatch, source_paths):
    app.config["backup_before_conversion"] = True
    app.files_list = [str(path) for path in source_paths]
    app.files_list_widget.clear()
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    monkeypatch.setattr(app, "get_output_directory", lambda *_args: str(out_dir))
    monkeypatch.setattr(app, "show_progress", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app, "_set_ui_enabled", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app, "record_config_usage", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app.db_manager, "add_conversion_record", lambda **_kwargs: None)
    monkeypatch.setattr(app.achievement_system, "record_conversion", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app.achievement_system, "record_batch_conversion", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app.achievement_system, "record_ocr_usage", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app.system_notifier, "send", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app.progress_bar, "setValue", lambda *_args, **_kwargs: None)
    return out_dir


def test_engine_direct_uses_global_backup_setting(monkeypatch, tmp_path):
    class FakeConfigManager:
        def load_config(self):
            return {"backup_before_conversion": True}

    monkeypatch.setattr(config_module, "ConfigManager", FakeConfigManager)
    source = _image(tmp_path / "source.png")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    result = AdvancedConverterEngine().convert("image_to_png", str(source), str(out_dir))

    assert result.success is True
    assert Path(f"{source}.bak").read_bytes() == source.read_bytes()


def test_engine_backup_failure_prevents_conversion(monkeypatch, tmp_path):
    source = _image(tmp_path / "source.png")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    calls = []
    engine = AdvancedConverterEngine()
    engine._image_convert = lambda *_args: calls.append(True) or True
    monkeypatch.setattr(converter_module, "prepare_operation_backups", _raise_backup_failure)

    result = engine.convert("image_to_png", str(source), str(out_dir))

    assert result.success is False
    assert "backup denied" in result.error
    assert calls == []


def test_engine_skips_backup_after_delegated_preflight(tmp_path):
    source = _image(tmp_path / "source.png")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    assert prepare_source_backups([source]).success is True
    engine = AdvancedConverterEngine()
    result = engine.convert("image_to_png", str(source), str(out_dir), skip_backup=True)

    assert result.success is True
    assert Path(f"{source}.bak").is_file()
    assert not Path(f"{source}.bak.1").exists()


def test_engine_batch_backs_up_each_unique_source_once(tmp_path, monkeypatch):
    class FakeConfigManager:
        def load_config(self):
            return {"backup_before_conversion": True}

    monkeypatch.setattr(config_module, "ConfigManager", FakeConfigManager)
    first = _image(tmp_path / "first.png")
    second = _image(tmp_path / "second.png")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    engine = AdvancedConverterEngine()

    results = engine.convert_batch("image_to_png", [first, second], str(out_dir))

    assert all(result.success for result in results)
    assert Path(f"{first}.bak").is_file()
    assert Path(f"{second}.bak").is_file()
    assert not Path(f"{first}.bak.1").exists()
    assert not Path(f"{second}.bak.1").exists()


def test_engine_batch_deduplicates_repeated_paths(tmp_path, monkeypatch):
    class FakeConfigManager:
        def load_config(self):
            return {"backup_before_conversion": True}

    monkeypatch.setattr(config_module, "ConfigManager", FakeConfigManager)
    source = _image(tmp_path / "source.png")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    engine = AdvancedConverterEngine()

    results = engine.convert_batch("image_to_png", [source, str(source)], str(out_dir))

    assert all(result.success for result in results)
    assert Path(f"{source}.bak").is_file()
    assert not Path(f"{source}.bak.1").exists()


def test_batch_direct_conversion_backs_up_before_conversion(tmp_path):
    source = _image(tmp_path / "source.png")
    out = tmp_path / "source.pdf"
    observed = []
    batch = BatchMixin.__new__(BatchMixin)
    batch.config = {"backup_before_conversion": True}

    def open_after_backup(path):
        observed.append(Path(f"{path}.bak").is_file())
        return Image.open(path)

    batch._open_image_for_pdf = open_after_backup

    assert batch._batch_to_pdf(str(source), str(out), ".png") is True

    assert observed == [True]
    assert Path(f"{source}.bak").read_bytes() == source.read_bytes()
    assert out.is_file()


def test_batch_backup_failure_prevents_file_conversion(monkeypatch, tmp_path):
    source = _image(tmp_path / "source.png")
    out = tmp_path / "source.pdf"
    batch = BatchMixin.__new__(BatchMixin)
    batch.config = {"backup_before_conversion": True}
    batch._open_image_for_pdf = lambda path: Image.open(path)
    monkeypatch.setattr("app.mixins.batch.prepare_operation_backups", _raise_backup_failure)

    assert batch._convert_batch_file(str(source), str(out), "pdf") is False

    assert batch._last_batch_error.startswith("Backup failed:")
    assert not out.exists()


def test_batch_engine_branch_preflights_before_engine(tmp_path):
    source = tmp_path / "note.txt"
    source.write_text("hello", encoding="utf-8")
    out = tmp_path / "note.pdf"
    batch = BatchMixin.__new__(BatchMixin)
    batch.config = {"backup_before_conversion": True}

    assert batch._batch_to_pdf(str(source), str(out), ".txt") is True

    assert Path(f"{source}.bak").read_text(encoding="utf-8") == "hello"
    assert not Path(f"{source}.bak.1").exists()
    assert out.is_file()


def test_batch_disabled_does_not_back_up_engine_branch(tmp_path):
    source = tmp_path / "note.txt"
    source.write_text("hello", encoding="utf-8")
    out = tmp_path / "note.pdf"
    batch = BatchMixin.__new__(BatchMixin)
    batch.config = {"backup_before_conversion": False}

    assert batch._batch_to_pdf(str(source), str(out), ".txt") is True

    assert not Path(f"{source}.bak").exists()
    assert out.is_file()


@pytest.mark.parametrize(
    ("config", "message"),
    [
        (None, "Batch configuration unavailable"),
        ({}, "Backup policy is missing"),
        ({"backup_before_conversion": "yes"}, "Backup policy is not a boolean"),
        ({"backup_before_conversion": 1}, "Backup policy is not a boolean"),
    ],
)
def test_batch_indeterminate_backup_policy_fails_file(tmp_path, config, message):
    source = _image(tmp_path / "source.png")
    out = tmp_path / "source.pdf"
    batch = BatchMixin.__new__(BatchMixin)
    if config is not None:
        batch.config = config
    batch._open_image_for_pdf = lambda path: Image.open(path)

    assert batch._batch_to_pdf(str(source), str(out), ".png") is False

    assert message in batch._last_batch_error
    assert not out.exists()


def test_batch_backup_failure_continues_other_files(app, monkeypatch, tmp_path):
    missing = tmp_path / "missing.png"
    good = _image(tmp_path / "good.png")
    _prepare_app(app, tmp_path, monkeypatch, [missing, good])
    monkeypatch.setattr(app, "cleanup_temp_files", lambda: None)
    monkeypatch.setattr("app.mixins.batch.QMessageBox.warning", lambda *_args: None)
    monkeypatch.setattr("app.mixins.batch.QMessageBox.information", lambda *_args: None)
    monkeypatch.setattr("conversion_worker.ConversionWorker", _FakeWorker)
    _FakeWorker.instances.clear()

    app.process_batch_conversion(str(tmp_path / "out"), "png")

    assert not (tmp_path / "out" / "missing.png").exists()
    assert (tmp_path / "out" / "good.png").is_file()
    assert Path(f"{good}.bak").is_file()
    assert not Path(f"{missing}.bak").exists()


def test_main_word_to_pdf_backs_up_before_worker(app, monkeypatch, tmp_path):
    source = tmp_path / "source.docx"
    source.write_bytes(b"not really a docx")
    out_dir = _prepare_app(app, tmp_path, monkeypatch, [source])
    app.active_templates = {
        sk.WORD_TO_PDF: {
            "mode": "preserve_all",
            "quality": "",
            "compress_images": True,
            "include_metadata": True,
        }
    }
    monkeypatch.setattr(word_module, "ConversionWorker", _NoopWorker)
    _NoopWorker.instances.clear()

    app.convert_word_to_pdf()

    assert Path(f"{source}.bak").is_file()
    assert len(_NoopWorker.instances) == 1
    assert out_dir.is_dir()


def test_main_word_backup_disabled_creates_no_backup(app, monkeypatch, tmp_path):
    source = tmp_path / "source.docx"
    source.write_bytes(b"not really a docx")
    _prepare_app(app, tmp_path, monkeypatch, [source])
    app.config["backup_before_conversion"] = False
    app.active_templates = {
        sk.WORD_TO_PDF: {
            "mode": "preserve_all",
            "quality": "",
            "compress_images": True,
            "include_metadata": True,
        }
    }
    monkeypatch.setattr(word_module, "ConversionWorker", _NoopWorker)
    _NoopWorker.instances.clear()

    app.convert_word_to_pdf()

    assert not Path(f"{source}.bak").exists()
    assert len(_NoopWorker.instances) == 1


def test_main_word_backup_failure_does_not_start_worker(app, monkeypatch, tmp_path):
    source = tmp_path / "source.docx"
    source.write_bytes(b"not really a docx")
    _prepare_app(app, tmp_path, monkeypatch, [source])
    app.active_templates = {
        sk.WORD_TO_PDF: {
            "mode": "preserve_all",
            "quality": "",
            "compress_images": True,
            "include_metadata": True,
        }
    }
    critical = []
    monkeypatch.setattr(word_module, "ConversionWorker", _NoopWorker)
    monkeypatch.setattr(word_module.QMessageBox, "critical", lambda *_args: critical.append(True))
    monkeypatch.setattr(word_module, "prepare_operation_backups", _raise_backup_failure)
    _NoopWorker.instances.clear()

    app.convert_word_to_pdf()

    assert len(_NoopWorker.instances) == 0
    assert critical
    assert not Path(f"{source}.bak").exists()


def test_main_pdf_to_word_backs_up_before_conversion(app, monkeypatch, tmp_path):
    source = _pdf(tmp_path / "source.pdf")
    _prepare_app(app, tmp_path, monkeypatch, [source])
    app.active_templates = {sk.PDF_TO_WORD: {"mode": "with_images"}}
    converted = []
    monkeypatch.setattr(app, "check_pdf_has_images", lambda _path: False)
    monkeypatch.setattr(app, "convert_pdfs_without_images", lambda files: converted.append(list(files)))

    app.convert_pdf_to_word()

    assert Path(f"{source}.bak").is_file()
    assert converted == [[str(source)]]


def test_main_pdf_backup_failure_prevents_conversion(app, monkeypatch, tmp_path):
    source = _pdf(tmp_path / "source.pdf")
    _prepare_app(app, tmp_path, monkeypatch, [source])
    app.active_templates = {sk.PDF_TO_WORD: {"mode": "with_images"}}
    converted = []
    critical = []
    monkeypatch.setattr(app, "check_pdf_has_images", lambda _path: False)
    monkeypatch.setattr(app, "convert_pdfs_without_images", lambda files: converted.append(list(files)))
    monkeypatch.setattr(pdf_module, "prepare_operation_backups", _raise_backup_failure)
    monkeypatch.setattr(pdf_module.QMessageBox, "critical", lambda *_args: critical.append(True))

    app.convert_pdf_to_word()

    assert not converted
    assert critical
    assert not Path(f"{source}.bak").exists()


def test_main_image_conversion_backs_up_source(app, monkeypatch, tmp_path):
    source = _image(tmp_path / "source.png")
    _prepare_app(app, tmp_path, monkeypatch, [source])
    converted = []
    monkeypatch.setattr(conversion_helpers, "_convert_image_to_pdf", lambda *_args: converted.append(True))
    monkeypatch.setattr(image_module.QMessageBox, "information", lambda *_args: None)

    app.convert_images_to_separate_pdfs([str(source)], [])

    assert Path(f"{source}.bak").is_file()
    assert converted


def test_main_image_backup_failure_prevents_conversion(app, monkeypatch, tmp_path):
    source = _image(tmp_path / "source.png")
    _prepare_app(app, tmp_path, monkeypatch, [source])
    converted = []
    critical = []
    monkeypatch.setattr(conversion_helpers, "_convert_image_to_pdf", lambda *_args: converted.append(True))
    monkeypatch.setattr(image_module, "prepare_operation_backups", _raise_backup_failure)
    monkeypatch.setattr(image_module.QMessageBox, "critical", lambda *_args: critical.append(True))

    app.convert_images_to_separate_pdfs([str(source)], [])

    assert not converted
    assert critical
    assert not Path(f"{source}.bak").exists()


def test_main_image_merge_backs_up_all_inputs(app, monkeypatch, tmp_path):
    first = _image(tmp_path / "first.png")
    second = _image(tmp_path / "second.png")
    out_dir = _prepare_app(app, tmp_path, monkeypatch, [first, second])
    output = out_dir / "merged.pdf"
    monkeypatch.setattr(app, "get_output_directory", lambda *_args: str(output))
    monkeypatch.setattr(image_module.QMessageBox, "information", lambda *_args: None)

    app.convert_images_to_merged_pdf([str(first), str(second)], [])

    assert Path(f"{first}.bak").is_file()
    assert Path(f"{second}.bak").is_file()
    assert output.is_file()


def test_main_pdf_merge_backs_up_all_inputs(app, monkeypatch, tmp_path):
    first = _pdf(tmp_path / "first.pdf")
    second = _pdf(tmp_path / "second.pdf")
    out_dir = _prepare_app(app, tmp_path, monkeypatch, [first, second])
    output = out_dir / "merged.pdf"
    monkeypatch.setattr(app, "get_output_directory", lambda *_args: str(output))
    merges = []

    class FakeMergeDialog:
        def __init__(self, *_args, **_kwargs):
            pass

        def exec(self):
            return QDialog.Accepted

        def get_ordered_files(self):
            return [str(first), str(second)]

        def get_order_key(self):
            return "none"

    def fake_merge(files, _dst_dir, _order, **_kwargs):
        merges.append(list(files))
        _pdf(output)

    monkeypatch.setattr(merge_dialog_module, "MergeOrderDialog", FakeMergeDialog)
    monkeypatch.setattr(conversion_helpers, "_merge_pdfs", fake_merge)
    monkeypatch.setattr(pdf_operations_module.QMessageBox, "information", lambda *_args: None)

    app.merge_pdfs()

    assert Path(f"{first}.bak").is_file()
    assert Path(f"{second}.bak").is_file()
    assert merges == [[str(first), str(second)]]


def test_main_word_merge_backs_up_all_inputs(app, monkeypatch, tmp_path):
    first = _docx(tmp_path / "first.docx")
    second = _docx(tmp_path / "second.docx")
    out_dir = _prepare_app(app, tmp_path, monkeypatch, [first, second])
    output = out_dir / "merged.docx"
    monkeypatch.setattr(app, "get_output_directory", lambda *_args: str(output))
    merges = []

    class FakeMergeDialog:
        def __init__(self, *_args, **_kwargs):
            pass

        def exec(self):
            return QDialog.Accepted

        def get_ordered_files(self):
            return [str(first), str(second)]

        def get_order_key(self):
            return "none"

    def fake_merge(files, _dst_dir, _order, **_kwargs):
        merges.append(list(files))
        _docx(output)

    monkeypatch.setattr(merge_dialog_module, "MergeOrderDialog", FakeMergeDialog)
    monkeypatch.setattr(conversion_helpers, "_merge_docx", fake_merge)
    monkeypatch.setattr(pdf_operations_module.QMessageBox, "information", lambda *_args: None)

    app.merge_word_docs()

    assert Path(f"{first}.bak").is_file()
    assert Path(f"{second}.bak").is_file()
    assert merges == [[str(first), str(second)]]


def test_main_pdf_merge_failure_prevents_merge(app, monkeypatch, tmp_path):
    first = _pdf(tmp_path / "first.pdf")
    second = _pdf(tmp_path / "second.pdf")
    _prepare_app(app, tmp_path, monkeypatch, [first, second])
    output = tmp_path / "out" / "merged.pdf"
    monkeypatch.setattr(app, "get_output_directory", lambda *_args: str(output))
    merges = []
    critical = []

    class FakeMergeDialog:
        def __init__(self, *_args, **_kwargs):
            pass

        def exec(self):
            return QDialog.Accepted

        def get_ordered_files(self):
            return [str(first), str(second)]

        def get_order_key(self):
            return "none"

    monkeypatch.setattr(merge_dialog_module, "MergeOrderDialog", FakeMergeDialog)
    monkeypatch.setattr(conversion_helpers, "_merge_pdfs", lambda *args, **kwargs: merges.append(True))
    monkeypatch.setattr(pdf_operations_module, "prepare_operation_backups", _raise_backup_failure)
    monkeypatch.setattr(pdf_operations_module.QMessageBox, "critical", lambda *_args: critical.append(True))

    app.merge_pdfs()

    assert merges == []
    assert critical
    assert not Path(f"{first}.bak").exists()


def test_operation_backups_disabled_policy_is_a_successful_noop(monkeypatch, tmp_path):
    source = _image(tmp_path / "source.png")

    result = prepare_operation_backups([source], config={"backup_before_conversion": False})

    assert result.success is True
    assert result.enabled is False
    assert result.backups == {}
    assert not Path(f"{source}.bak").exists()


def test_operation_backups_rejects_missing_or_invalid_policy(monkeypatch, tmp_path):
    source = _image(tmp_path / "source.png")

    with pytest.raises(BackupError, match="Backup policy is missing"):
        prepare_operation_backups([source], config={})
    with pytest.raises(BackupError, match="Backup policy is not a boolean"):
        prepare_operation_backups([source], config={"backup_before_conversion": "yes"})


def test_operation_backups_strict_config_load_failure(tmp_path, monkeypatch):
    import config as config_module

    config_file = tmp_path / "config.dat"
    config_file.write_bytes(b"not a valid config")
    manager = config_module.ConfigManager(str(config_file), str(tmp_path / "key.key"))

    with pytest.raises(Exception):
        manager.load_config_strict()


def test_engine_direct_missing_policy_blocks_conversion(tmp_path, monkeypatch):
    class FakeConfigManager:
        def load_config(self):
            return {}

    monkeypatch.setattr(config_module, "ConfigManager", FakeConfigManager)
    source = _image(tmp_path / "source.png")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    result = AdvancedConverterEngine().convert("image_to_png", str(source), str(out_dir))

    assert result.success is False
    assert "Backup policy is missing" in result.error
    assert not (out_dir / "source.png").exists()
    assert not Path(f"{source}.bak").exists()


def test_main_missing_policy_blocks_image_conversion(app, tmp_path, monkeypatch):
    source = _image(tmp_path / "source.png")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    app.config = {}
    monkeypatch.setattr(app, "get_output_directory", lambda *_args: str(out_dir))
    converted = []
    critical = []
    information = []
    monkeypatch.setattr(conversion_helpers, "_convert_image_to_pdf", lambda *_args: converted.append(True))
    monkeypatch.setattr(image_module.QMessageBox, "critical", lambda *_args: critical.append(True))
    monkeypatch.setattr(image_module.QMessageBox, "information", lambda *_args: information.append(True))

    app.convert_images_to_separate_pdfs([str(source)], [])

    assert critical
    assert information == []
    assert converted == []
    assert not (out_dir / "source.pdf").exists()
    assert not Path(f"{source}.bak").exists()
