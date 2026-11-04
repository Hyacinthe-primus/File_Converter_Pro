"""Focused tests for collision-safe backup creation."""

import os
import shutil
import stat
from pathlib import Path

import pytest

import converter.helpers as backup_helpers


def _source(tmp_path, content=b"source data"):
    src = tmp_path / "document.txt"
    src.write_bytes(content)
    return src


def test_existing_backups_are_preserved(tmp_path):
    src = _source(tmp_path)
    existing = {
        f"{src}.bak": b"old backup",
        f"{src}.bak.1": b"older backup",
        f"{src}.bak.2": b"oldest backup",
    }
    for path, content in existing.items():
        Path(path).write_bytes(content)

    backup_path = backup_helpers.create_backup(str(src), overwrite=False)

    assert backup_path == f"{src}.bak.3"
    assert Path(backup_path).read_bytes() == b"source data"
    for path, content in existing.items():
        assert Path(path).read_bytes() == content


def test_competing_creation_selects_next_suffix(tmp_path, monkeypatch):
    src = _source(tmp_path)
    candidate = f"{src}.bak"
    competing_content = b"created by another process"
    real_open = os.open

    def racing_open(path, flags, mode=0o777):
        if os.path.abspath(path) == os.path.abspath(candidate) and not os.path.exists(candidate):
            Path(candidate).write_bytes(competing_content)
        return real_open(path, flags, mode)

    monkeypatch.setattr(backup_helpers.os, "open", racing_open)

    backup_path = backup_helpers.create_backup(str(src), overwrite=False)

    assert backup_path == f"{candidate}.1"
    assert Path(candidate).read_bytes() == competing_content
    assert Path(backup_path).read_bytes() == b"source data"


def test_symlink_candidate_is_not_followed(tmp_path):
    src = _source(tmp_path)
    victim = tmp_path / "victim.txt"
    victim.write_bytes(b"must not change")
    candidate = Path(f"{src}.bak")
    try:
        candidate.symlink_to(victim)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    backup_path = backup_helpers.create_backup(str(src), overwrite=False)

    assert backup_path == f"{src}.bak.1"
    assert candidate.is_symlink()
    assert candidate.resolve() == victim.resolve()
    assert victim.read_bytes() == b"must not change"
    assert Path(backup_path).read_bytes() == b"source data"


def test_copy_failure_removes_only_new_backup(tmp_path, monkeypatch):
    src = _source(tmp_path)
    existing = Path(f"{src}.bak")
    existing.write_bytes(b"old backup")

    def failing_copy(src_file, dst_file):
        dst_file.write(b"partial")
        raise OSError("copy failed")

    monkeypatch.setattr(shutil, "copyfileobj", failing_copy)

    assert backup_helpers.create_backup(str(src), overwrite=False) is None
    assert existing.read_bytes() == b"old backup"
    assert not Path(f"{src}.bak.1").exists()


def test_metadata_failure_removes_only_new_backup(tmp_path, monkeypatch):
    src = _source(tmp_path)
    existing = Path(f"{src}.bak")
    existing.write_bytes(b"old backup")

    def failing_copystat(*args, **kwargs):
        raise OSError("metadata failed")

    monkeypatch.setattr(shutil, "copystat", failing_copystat)

    assert backup_helpers.create_backup(str(src), overwrite=False) is None
    assert existing.read_bytes() == b"old backup"
    assert not Path(f"{src}.bak.1").exists()


def test_metadata_is_preserved(tmp_path):
    src = _source(tmp_path)
    os.chmod(src, 0o640)
    os.utime(src, (1_600_000_000, 1_600_000_000))

    backup_path = backup_helpers.create_backup(str(src), overwrite=False)

    source_stat = os.stat(src)
    backup_stat = os.stat(backup_path)
    assert stat.S_IMODE(backup_stat.st_mode) == stat.S_IMODE(source_stat.st_mode)
    assert int(backup_stat.st_mtime) == int(source_stat.st_mtime)


def test_overwrite_true_still_overwrites(tmp_path):
    src = _source(tmp_path)
    existing = Path(f"{src}.bak")
    existing.write_bytes(b"old backup")

    backup_path = backup_helpers.create_backup(str(src), overwrite=True)

    assert backup_path == str(existing)
    assert existing.read_bytes() == b"source data"
