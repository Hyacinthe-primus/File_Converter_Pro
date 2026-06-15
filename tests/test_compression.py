"""Tests for compression workflows — create real ZIP files and verify content."""

import os
import sys
import tempfile
import shutil
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _create_test_files(directory, count=3):
    paths = []
    for i in range(count):
        p = os.path.join(directory, f"file_{i}.txt")
        with open(p, "w") as f:
            f.write(f"Content of file {i}\n" * 10)
        paths.append(p)
    return paths


class TestSingleZipArchive:
    def test_creates_valid_zip(self, tmp_dir):
        from app.mixins.compression import CompressionMixin
        mixin = CompressionMixin()
        mixin.translate_text = lambda x: x
        mixin.progress_bar = type('', (), {'setValue': lambda self, v: None})()

        files = _create_test_files(tmp_dir)
        archive = os.path.join(tmp_dir, "test.zip")
        result = mixin.create_single_zip_archive(
            archive, files, zipfile.ZIP_DEFLATED, None
        )
        assert result is True
        assert os.path.exists(archive)
        with zipfile.ZipFile(archive, 'r') as zf:
            names = zf.namelist()
            assert len(names) == 3

    def test_creates_zip_with_subdirs(self, tmp_dir):
        from app.mixins.compression import CompressionMixin
        mixin = CompressionMixin()
        mixin.translate_text = lambda x: x
        mixin.progress_bar = type('', (), {'setValue': lambda self, v: None})()

        sub = os.path.join(tmp_dir, "subdir")
        os.makedirs(sub)
        with open(os.path.join(tmp_dir, "root.txt"), "w") as f:
            f.write("root file")
        with open(os.path.join(sub, "sub.txt"), "w") as f:
            f.write("sub file")

        all_files = []
        for root, dirs, files in os.walk(tmp_dir):
            for f in files:
                all_files.append(os.path.join(root, f))

        archive = os.path.join(tmp_dir, "nested.zip")
        result = mixin.create_single_zip_archive(
            archive, all_files, zipfile.ZIP_DEFLATED, None
        )
        assert result is True
        assert os.path.exists(archive)


class TestArchiveExtension:
    def test_zip_extension(self):
        from app.mixins.compression import CompressionMixin
        m = CompressionMixin()
        m.translate_text = lambda x: x
        assert m.get_archive_extension("ZIP") == "zip"

    def test_rar_extension(self):
        from app.mixins.compression import CompressionMixin
        m = CompressionMixin()
        m.translate_text = lambda x: x
        assert m.get_archive_extension("RAR") == "rar"

    def test_tar_gz_extension(self):
        from app.mixins.compression import CompressionMixin
        m = CompressionMixin()
        m.translate_text = lambda x: x
        assert m.get_archive_extension("TAR.GZ") == "tar.gz"

    def test_tar_extension(self):
        from app.mixins.compression import CompressionMixin
        m = CompressionMixin()
        m.translate_text = lambda x: x
        assert m.get_archive_extension("TAR") == "tar"


class TestFindSplitArchiveParts:
    def test_find_zip_parts(self, tmp_dir):
        from app.mixins.compression import CompressionMixin
        mixin = CompressionMixin()
        mixin.translate_text = lambda x: x

        archive = os.path.join(tmp_dir, "test.zip")
        with open(archive, "w") as f:
            f.write("fake")
        parts = mixin.find_split_archive_parts(archive, "ZIP")
        assert len(parts) >= 1

    def test_find_rar_parts(self, tmp_dir):
        from app.mixins.compression import CompressionMixin
        mixin = CompressionMixin()
        mixin.translate_text = lambda x: x

        archive = os.path.join(tmp_dir, "test.rar")
        with open(archive, "w") as f:
            f.write("fake")
        parts = mixin.find_split_archive_parts(archive, "RAR")
        assert len(parts) >= 1


class TestTarArchive:
    def test_creates_tar(self, tmp_dir):
        from app.mixins.compression import CompressionMixin
        mixin = CompressionMixin()
        mixin.translate_text = lambda x: x
        mixin.progress_bar = type('', (), {'setValue': lambda self, v: None})()

        files = _create_test_files(tmp_dir)
        archive = os.path.join(tmp_dir, "test.tar")
        result = mixin.create_tar_archive(archive, files, "TAR", "Normal")
        assert result is True
        assert os.path.exists(archive)

    def test_creates_tar_gz(self, tmp_dir):
        from app.mixins.compression import CompressionMixin
        mixin = CompressionMixin()
        mixin.translate_text = lambda x: x
        mixin.progress_bar = type('', (), {'setValue': lambda self, v: None})()

        files = _create_test_files(tmp_dir)
        archive = os.path.join(tmp_dir, "test.tar.gz")
        result = mixin.create_tar_archive(archive, files, "TAR.GZ", "Normal")
        assert result is True
        assert os.path.exists(archive)
