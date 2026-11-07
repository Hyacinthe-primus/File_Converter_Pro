"""Backup behavior for context-menu Quick Convert."""

from pathlib import Path

import pytest

import context_menu.window as cm_window
import converter.converters as converter_module
from converter.helpers import BackupError


def _fake_config(monkeypatch, backup_enabled):
    import config as config_module

    class FakeConfigManager:
        def load_config(self):
            return {"backup_before_conversion": backup_enabled}

    monkeypatch.setattr(config_module, "ConfigManager", FakeConfigManager)


def _run_thread(files, conversion_type):
    thread = cm_window.ConversionThread([str(path) for path in files], conversion_type)
    done = []
    thread.done.connect(lambda *args: done.append(args))
    thread.run()
    return done


class _FakeResult:
    success = True
    error = ""


def _install_fake_engine(monkeypatch, write_output=False):
    instances = []

    class FakeEngine:
        def __init__(self):
            self.allow_local_html_resources = None
            self.skip_backup = None
            instances.append(self)

        def convert(self, conversion_type, src, dst_dir, *, skip_backup=False):
            self.skip_backup = skip_backup
            if write_output:
                output = Path(dst_dir) / f"{Path(src).stem}.pdf"
                output.write_text("converted")
            return _FakeResult()

    monkeypatch.setattr(converter_module, "AdvancedConverterEngine", FakeEngine)
    return instances


def _file(tmp_path, name):
    path = tmp_path / name
    path.write_bytes(b"source data")
    return path


def test_backup_enabled_for_generic_conversion(monkeypatch, tmp_path):
    _fake_config(monkeypatch, True)
    src = _file(tmp_path, "note.txt")
    engines = _install_fake_engine(monkeypatch)

    done = _run_thread([src], "txt_to_pdf")

    assert done and done[0][0] is True
    assert (tmp_path / "note.txt.bak").read_bytes() == b"source data"
    assert engines[0].skip_backup is True


def test_backup_disabled_for_generic_conversion(monkeypatch, tmp_path):
    _fake_config(monkeypatch, False)
    src = _file(tmp_path, "note.txt")
    engines = _install_fake_engine(monkeypatch)

    done = _run_thread([src], "txt_to_pdf")

    assert done and done[0][0] is True
    assert not (tmp_path / "note.txt.bak").exists()
    assert engines[0].skip_backup is True


@pytest.mark.parametrize(
    ("conversion_type", "helper_name", "names"),
    [
        ("image_to_pdf", "_convert_image_to_pdf", ["image.png"]),
        ("docx_to_pdf", "_convert_docx_to_pdf", ["document.docx"]),
        ("pdf_to_docx", "_convert_pdf_to_docx", ["document.pdf"]),
        ("images_to_pdf_merged", "_merge_images_to_pdf", ["one.png", "two.png"]),
        ("merge_pdf_none", "_merge_pdfs", ["one.pdf", "two.pdf"]),
        ("merge_docx_none", "_merge_docx", ["one.docx", "two.docx"]),
    ],
)
def test_backup_enabled_for_special_conversion_families(
    monkeypatch, tmp_path, conversion_type, helper_name, names
):
    _fake_config(monkeypatch, True)
    files = [_file(tmp_path, name) for name in names]
    converted = []
    monkeypatch.setattr(cm_window, helper_name, lambda *a, **k: converted.append((a, k)))

    done = _run_thread(files, conversion_type)

    assert done and done[0][0] is True
    assert len(converted) == 1
    for path in files:
        assert Path(f"{path}.bak").read_bytes() == b"source data"


def test_backup_disabled_for_special_conversion(monkeypatch, tmp_path):
    _fake_config(monkeypatch, False)
    src = _file(tmp_path, "image.png")
    converted = []
    monkeypatch.setattr(cm_window, "_convert_image_to_pdf", lambda *a, **k: converted.append((a, k)))

    done = _run_thread([src], "image_to_pdf")

    assert done and done[0][0] is True
    assert converted
    assert not Path(f"{src}.bak").exists()


def _raw_config(monkeypatch, config):
    import config as config_module

    class FakeConfigManager:
        def load_config(self):
            if isinstance(config, Exception):
                raise config
            return config

    monkeypatch.setattr(config_module, "ConfigManager", FakeConfigManager)


def test_config_load_failure_aborts_before_dispatch(monkeypatch, tmp_path):
    _raw_config(monkeypatch, RuntimeError("config unavailable"))
    src = _file(tmp_path, "image.png")
    converted = []
    monkeypatch.setattr(cm_window, "_convert_image_to_pdf", lambda *args: converted.append(args))

    done = _run_thread([src], "image_to_pdf")

    assert done and done[0][0] is False
    assert "configuration unavailable" in done[0][1]
    assert converted == []


def test_missing_backup_policy_aborts_before_dispatch(monkeypatch, tmp_path):
    _raw_config(monkeypatch, {"pdf_to_word_mode": "with_images"})
    src = _file(tmp_path, "image.png")
    converted = []
    monkeypatch.setattr(cm_window, "_convert_image_to_pdf", lambda *args: converted.append(args))

    done = _run_thread([src], "image_to_pdf")

    assert done and done[0][0] is False
    assert "Backup policy is missing" in done[0][1]
    assert converted == []


@pytest.mark.parametrize("value", ["yes", 1, None])
def test_invalid_backup_policy_aborts_before_dispatch(monkeypatch, tmp_path, value):
    _raw_config(monkeypatch, {"backup_before_conversion": value})
    src = _file(tmp_path, "image.png")
    converted = []
    monkeypatch.setattr(cm_window, "_convert_image_to_pdf", lambda *args: converted.append(args))

    done = _run_thread([src], "image_to_pdf")

    assert done and done[0][0] is False
    assert "Backup policy is not a boolean" in done[0][1]
    assert converted == []


def test_duplicate_sources_create_one_backup(monkeypatch, tmp_path):
    _fake_config(monkeypatch, True)
    src = _file(tmp_path, "image.png")
    monkeypatch.setattr(cm_window, "_convert_image_to_pdf", lambda *a, **k: None)

    done = _run_thread([src, src], "image_to_pdf")

    assert done and done[0][0] is True
    assert Path(f"{src}.bak").is_file()
    assert not Path(f"{src}.bak.1").exists()


def test_existing_backup_is_not_overwritten(monkeypatch, tmp_path):
    _fake_config(monkeypatch, True)
    src = _file(tmp_path, "image.png")
    existing = Path(f"{src}.bak")
    existing.write_bytes(b"old backup")
    monkeypatch.setattr(cm_window, "_convert_image_to_pdf", lambda *a, **k: None)

    done = _run_thread([src], "image_to_pdf")

    assert done and done[0][0] is True
    assert existing.read_bytes() == b"old backup"
    assert Path(f"{src}.bak.1").read_bytes() == b"source data"


def test_backup_failure_prevents_conversion(monkeypatch, tmp_path):
    _fake_config(monkeypatch, True)
    src = _file(tmp_path, "image.png")
    converted = []

    def fail_backup(*_args, **_kwargs):
        raise BackupError("Backup failed: denied")

    monkeypatch.setattr(cm_window, "prepare_operation_backups", fail_backup)
    monkeypatch.setattr(cm_window, "_convert_image_to_pdf", lambda *a, **k: converted.append((a, k)))

    done = _run_thread([src], "image_to_pdf")

    assert done and done[0][0] is False
    assert "Backup failed" in done[0][1]
    assert converted == []


def test_output_file_is_not_backed_up(monkeypatch, tmp_path):
    _fake_config(monkeypatch, True)
    src = _file(tmp_path, "note.txt")
    _install_fake_engine(monkeypatch, write_output=True)

    done = _run_thread([src], "txt_to_pdf")

    assert done and done[0][0] is True
    assert Path(f"{src}.bak").is_file()
    assert not (tmp_path / "note.pdf.bak").exists()


def test_engine_does_not_create_a_second_backup(monkeypatch, tmp_path):
    _fake_config(monkeypatch, True)
    src = _file(tmp_path, "note.txt")
    _install_fake_engine(monkeypatch)
    calls = []
    real_prepare = cm_window.prepare_operation_backups

    def counted_prepare(*args, **kwargs):
        calls.append((args, kwargs))
        return real_prepare(*args, **kwargs)

    monkeypatch.setattr(cm_window, "prepare_operation_backups", counted_prepare)

    done = _run_thread([src], "txt_to_pdf")

    assert done and done[0][0] is True
    assert len(calls) == 1
    assert Path(f"{src}.bak").is_file()
    assert not Path(f"{src}.bak.1").exists()


@pytest.mark.parametrize("module_name", ["watcher", "scheduler"])
def test_automation_paths_do_not_use_quick_backup(monkeypatch, tmp_path, module_name):
    import context_menu.conversion_helpers as conversion_helpers
    from tasks import scheduler, watcher

    runner = watcher._run_conversion if module_name == "watcher" else scheduler._run_conversion
    src = _file(tmp_path, "document.pdf")
    out_dir = tmp_path / "out"
    quick_backups = []
    converted = []
    monkeypatch.setattr(
        cm_window,
        "prepare_operation_backups",
        lambda files, **_kwargs: quick_backups.append(files),
    )
    monkeypatch.setattr(conversion_helpers, "_convert_pdf_to_docx", lambda *a, **k: converted.append((a, k)))

    runner("pdf_to_docx", str(src), str(out_dir))

    assert quick_backups == []
    assert len(converted) == 1
    assert not Path(f"{src}.bak").exists()
