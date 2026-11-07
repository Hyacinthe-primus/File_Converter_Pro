"""Focused tests for shared source-backup preflight preparation."""

from __future__ import annotations

import os
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

import converter.helpers as backup_helpers
from converter.helpers import prepare_source_backups


def _source(tmp_path: Path, name: str = "source.txt", content: bytes = b"source data") -> Path:
    path = tmp_path / name
    path.write_bytes(content)
    return path


def _existing_backup(path: Path, content: bytes) -> None:
    path.write_bytes(content)


def test_prepare_source_backups_creates_one_backup_per_source(tmp_path):
    first = _source(tmp_path, "first.txt", b"first data")
    second = _source(tmp_path, "second.txt", b"second data")

    result = prepare_source_backups([first, str(second)])

    assert result.success is True
    assert result.errors == {}
    assert result.backups == {
        str(first): f"{first}.bak",
        str(second): f"{second}.bak",
    }
    assert Path(result.backups[str(first)]).read_bytes() == b"first data"
    assert Path(result.backups[str(second)]).read_bytes() == b"second data"


def test_duplicate_sources_create_only_one_backup(tmp_path):
    source = _source(tmp_path)

    result = prepare_source_backups([source, str(source), source])

    assert result.success is True
    assert len(result.backups) == 1
    assert result.backups[str(source)] == f"{source}.bak"
    assert not Path(f"{source}.bak.1").exists()


def test_existing_backups_are_preserved_and_next_suffix_is_used(tmp_path):
    source = _source(tmp_path)
    first_backup = Path(f"{source}.bak")
    second_backup = Path(f"{source}.bak.1")
    _existing_backup(first_backup, b"old backup")
    _existing_backup(second_backup, b"older backup")

    result = prepare_source_backups([source])

    assert result.success is True
    assert result.backups[str(source)] == f"{source}.bak.2"
    assert first_backup.read_bytes() == b"old backup"
    assert second_backup.read_bytes() == b"older backup"
    assert Path(result.backups[str(source)]).read_bytes() == b"source data"


def test_missing_source_is_reported_without_creating_a_backup(tmp_path):
    missing = tmp_path / "missing.txt"

    result = prepare_source_backups([missing])

    assert result.success is False
    assert result.errors[str(missing)] == "source does not exist"
    assert not Path(f"{missing}.bak").exists()


def test_directory_source_is_reported_as_not_a_file(tmp_path):
    directory = tmp_path / "folder"
    directory.mkdir()

    result = prepare_source_backups([directory])

    assert result.success is False
    assert result.errors[str(directory)] == "source is not a file"


def test_inaccessible_source_is_reported_explicitly(tmp_path, monkeypatch):
    source = _source(tmp_path)
    real_stat = os.stat

    def inaccessible_stat(path, *args, **kwargs):
        if os.fspath(path) == str(source):
            raise PermissionError("permission denied")
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(backup_helpers.os, "stat", inaccessible_stat)

    result = prepare_source_backups([source])

    assert result.success is False
    assert "inaccessible" in result.errors[str(source)]
    assert not Path(f"{source}.bak").exists()


def test_partial_failure_still_backs_up_remaining_sources(tmp_path):
    first = _source(tmp_path, "first.txt")
    missing = tmp_path / "missing.txt"
    last = _source(tmp_path, "last.txt")

    result = prepare_source_backups([first, missing, last])

    assert result.success is False
    assert list(result.backups) == [str(first), str(last)]
    assert list(result.errors) == [str(missing)]
    assert Path(f"{first}.bak").read_bytes() == b"source data"
    assert Path(f"{last}.bak").read_bytes() == b"source data"
    assert not Path(f"{missing}.bak").exists()


def test_final_backup_name_is_not_exposed_while_copy_is_in_progress(tmp_path, monkeypatch):
    source = _source(tmp_path)
    final_backup = Path(f"{source}.bak")
    started = threading.Event()
    release = threading.Event()
    real_copy = shutil.copyfileobj

    def blocking_copy(src_file, dst_file):
        started.set()
        release.wait(5)
        real_copy(src_file, dst_file)

    monkeypatch.setattr(shutil, "copyfileobj", blocking_copy)
    result_box = {}

    def run():
        result_box["result"] = prepare_source_backups([source])

    thread = threading.Thread(target=run)
    thread.start()
    try:
        assert started.wait(5)
        assert not final_backup.exists()
    finally:
        release.set()
        thread.join(5)

    assert not thread.is_alive()
    assert result_box["result"].success is True
    assert final_backup.read_bytes() == b"source data"
    assert not list(tmp_path.glob(".fcp_backup_*.tmp"))


def test_failed_copy_removes_partial_backup(tmp_path, monkeypatch):
    source = _source(tmp_path)

    def failing_copy(_src_file, dst_file):
        dst_file.write(b"partial")
        raise OSError("copy failed")

    monkeypatch.setattr(shutil, "copyfileobj", failing_copy)

    result = prepare_source_backups([source])

    assert result.success is False
    assert result.errors[str(source)] == "copy failed"
    assert not Path(f"{source}.bak").exists()
    assert not Path(f"{source}.bak.1").exists()
    assert not list(tmp_path.glob(".fcp_backup_*.tmp"))


def test_relative_and_absolute_paths_are_deduplicated(tmp_path, monkeypatch):
    source = _source(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = prepare_source_backups([source, Path(source.name)])

    assert result.success is True
    assert result.backups == {str(source): f"{source}.bak"}
    assert not Path(f"{source}.bak.1").exists()


def test_symlink_and_target_are_deduplicated(tmp_path):
    target = _source(tmp_path, "target.txt")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    result = prepare_source_backups([link, target])

    assert result.success is True
    assert result.backups == {str(link): f"{link}.bak"}
    assert Path(f"{link}.bak").read_bytes() == b"source data"
    assert not Path(f"{target}.bak").exists()


def test_concurrent_preflights_get_exclusive_backup_names(tmp_path):
    source = _source(tmp_path)
    barrier = threading.Barrier(2)

    def run():
        barrier.wait()
        return prepare_source_backups([source])

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _index: run(), range(2)))

    assert all(result.success for result in results)
    backup_paths = sorted(path for result in results for path in result.backups.values())
    assert backup_paths == [f"{source}.bak", f"{source}.bak.1"]
    assert Path(f"{source}.bak").read_bytes() == b"source data"
    assert Path(f"{source}.bak.1").read_bytes() == b"source data"


def test_failed_replacement_preserves_existing_backup(tmp_path, monkeypatch):
    source = _source(tmp_path)
    existing = Path(f"{source}.bak")
    existing.write_bytes(b"old backup")

    def failing_copy(_src, dst):
        Path(dst).write_bytes(b"partial")
        raise OSError("replacement copy failed")

    monkeypatch.setattr(shutil, "copy2", failing_copy)

    assert backup_helpers.create_backup(str(source), overwrite=True) is None
    assert existing.read_bytes() == b"old backup"
    assert not list(tmp_path.glob(".fcp_backup_*.tmp"))


def test_successful_replacement_is_atomic(tmp_path, monkeypatch):
    source = _source(tmp_path, content=b"new data")
    existing = Path(f"{source}.bak")
    existing.write_bytes(b"old backup")
    started = threading.Event()
    release = threading.Event()
    real_copy = shutil.copy2

    def blocking_copy(src, dst):
        started.set()
        release.wait(5)
        return real_copy(src, dst)

    monkeypatch.setattr(shutil, "copy2", blocking_copy)
    result_box = {}

    def run():
        result_box["path"] = backup_helpers.create_backup(str(source), overwrite=True)

    thread = threading.Thread(target=run)
    thread.start()
    try:
        assert started.wait(5)
        assert existing.read_bytes() == b"old backup"
    finally:
        release.set()
        thread.join(5)

    assert not thread.is_alive()
    assert result_box["path"] == str(existing)
    assert existing.read_bytes() == b"new data"
    assert not list(tmp_path.glob(".fcp_backup_*.tmp"))


def test_cleanup_failure_is_reported_on_failure(tmp_path, monkeypatch):
    source = _source(tmp_path)
    temp_files = []

    def failing_copy(_src, dst):
        temp_files.append(Path(dst))
        Path(dst).write_bytes(b"partial")
        raise OSError("copy failed")

    monkeypatch.setattr(backup_helpers, "_copy_with_metadata", failing_copy)
    monkeypatch.setattr(backup_helpers, "_remove_backup_temp", lambda _path: "cleanup denied")

    try:
        result = prepare_source_backups([source])
        assert result.success is False
        assert "copy failed" in result.errors[str(source)]
        assert "temporary cleanup failed: cleanup denied" in result.errors[str(source)]
    finally:
        for path in temp_files:
            if path.exists():
                path.unlink()


def test_successful_backup_reports_cleanup_failure(tmp_path, monkeypatch):
    source = _source(tmp_path)

    def copy_then_keep_temp(temp_path, final_path):
        shutil.copy2(temp_path, final_path)
        return False

    monkeypatch.setattr(backup_helpers, "_publish_exclusive", copy_then_keep_temp)
    monkeypatch.setattr(backup_helpers, "_remove_backup_temp", lambda _path: "cleanup denied")

    result = prepare_source_backups([source])

    assert result.success is True
    assert result.cleanup_errors[str(source)] == "cleanup denied"
    assert Path(f"{source}.bak").read_bytes() == b"source data"
    for temp_path in tmp_path.glob(".fcp_backup_*.tmp"):
        temp_path.unlink()


def test_custom_pathlike_failure_does_not_abort_other_sources(tmp_path):
    class BrokenPathLike:
        def __fspath__(self):
            raise RuntimeError("broken pathlike")

    source = _source(tmp_path)

    result = prepare_source_backups([BrokenPathLike(), source])

    assert result.success is False
    assert len(result.backups) == 1
    assert str(source) in result.backups
    assert any("broken pathlike" in reason for reason in result.errors.values())


def test_failed_alias_can_be_followed_by_successful_alias(tmp_path, monkeypatch):
    target = _source(tmp_path, "target.txt")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    real_copy = backup_helpers._copy_with_metadata

    def fail_link(src, dst):
        if os.path.abspath(src) == os.path.abspath(link):
            raise OSError("alias copy failed")
        return real_copy(src, dst)

    monkeypatch.setattr(backup_helpers, "_copy_with_metadata", fail_link)

    result = prepare_source_backups([link, target])

    assert result.success is True
    assert result.backups == {str(target): f"{target}.bak"}
    assert result.errors == {}
    assert Path(f"{target}.bak").read_bytes() == b"source data"


@pytest.mark.parametrize("suffix", ["", "bak", "bad/name", "bad\\name", "\0"])
def test_invalid_suffixes_are_rejected(suffix):
    with pytest.raises(ValueError, match="suffix"):
        prepare_source_backups([], suffix=suffix)


def test_empty_source_list_is_a_successful_noop():
    result = prepare_source_backups([])

    assert result.success is True
    assert result.backups == {}
    assert result.errors == {}
