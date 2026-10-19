"""Tests for backup before conversion."""

import os
import shutil
import tempfile

import pytest


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


class TestBackupBeforeConversion:
    def test_create_backup_basic(self, tmp_dir):
        from converter.helpers import create_backup

        src = os.path.join(tmp_dir, "document.txt")
        with open(src, "w") as f:
            f.write("important content")

        backup_path = create_backup(src)
        assert backup_path is not None
        assert backup_path == src + ".bak"
        assert os.path.exists(backup_path)
        with open(backup_path, "r") as f:
            assert f.read() == "important content"

    def test_create_backup_custom_suffix(self, tmp_dir):
        from converter.helpers import create_backup

        src = os.path.join(tmp_dir, "photo.jpg")
        with open(src, "wb") as f:
            f.write(b"\xff\xd8\xff")

        backup_path = create_backup(src, suffix=".backup")
        assert backup_path == src + ".backup"
        assert os.path.exists(backup_path)

    def test_create_backup_nonexistent_source(self, tmp_dir):
        from converter.helpers import create_backup

        result = create_backup(os.path.join(tmp_dir, "nonexistent.txt"))
        assert result is None

    def test_create_backup_preserves_content(self, tmp_dir):
        from converter.helpers import create_backup

        src = os.path.join(tmp_dir, "data.bin")
        content = bytes(range(256))
        with open(src, "wb") as f:
            f.write(content)

        backup_path = create_backup(src)
        with open(backup_path, "rb") as f:
            assert f.read() == content

    def test_engine_backup_enabled(self, tmp_dir):
        from converter.converters import AdvancedConverterEngine

        engine = AdvancedConverterEngine()
        engine.backup_enabled = True

        src = os.path.join(tmp_dir, "test.txt")
        with open(src, "w") as f:
            f.write("test content")

        dst_dir = os.path.join(tmp_dir, "output")
        os.makedirs(dst_dir, exist_ok=True)

        backup_path = src + ".bak"
        if os.path.exists(backup_path):
            os.remove(backup_path)

        engine.convert("txt_to_pdf", src, dst_dir)

        assert os.path.exists(backup_path)
        with open(backup_path, "r") as f:
            assert f.read() == "test content"

    def test_engine_backup_disabled(self, tmp_dir):
        from converter.converters import AdvancedConverterEngine

        engine = AdvancedConverterEngine()
        engine.backup_enabled = False

        src = os.path.join(tmp_dir, "test.txt")
        with open(src, "w") as f:
            f.write("test content")

        dst_dir = os.path.join(tmp_dir, "output")
        os.makedirs(dst_dir, exist_ok=True)

        backup_path = src + ".bak"
        if os.path.exists(backup_path):
            os.remove(backup_path)

        engine.convert("txt_to_pdf", src, dst_dir)

        assert not os.path.exists(backup_path)

    def test_engine_backup_default_disabled(self, tmp_dir):
        from converter.converters import AdvancedConverterEngine

        engine = AdvancedConverterEngine()
        assert engine.backup_enabled is False

    def test_backup_overwrites_existing(self, tmp_dir):
        from converter.helpers import create_backup

        src = os.path.join(tmp_dir, "file.txt")
        with open(src, "w") as f:
            f.write("new content")

        backup_path = src + ".bak"
        with open(backup_path, "w") as f:
            f.write("old content")

        create_backup(src)
        with open(backup_path, "r") as f:
            assert f.read() == "new content"
