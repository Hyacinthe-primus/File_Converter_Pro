"""Tests for this session's compression fixes:
archive size summing for split archives, multivolume target detection,
and process_compression returning the real archive path.
"""

import os
import shutil
import tempfile

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


def _make_mixin():
    from app.mixins.compression import CompressionMixin

    mixin = CompressionMixin()
    mixin.translate_text = lambda x: x
    mixin.progress_bar = type("", (), {"setValue": lambda self, v: None})()
    mixin.status_bar = type("", (), {"showMessage": lambda self, m: None})()
    return mixin


class TestArchiveTotalSize:
    def test_sums_split_parts(self, tmp_dir):
        m = _make_mixin()
        with open(os.path.join(tmp_dir, "arch.7z.001"), "wb") as f:
            f.write(b"a" * 100)
        with open(os.path.join(tmp_dir, "arch.7z.002"), "wb") as f:
            f.write(b"b" * 200)
        archive = os.path.join(tmp_dir, "arch.7z")
        assert m._archive_total_size(archive, 5) == 300

    def test_single_file_no_split(self, tmp_dir):
        m = _make_mixin()
        archive = os.path.join(tmp_dir, "arch.7z")
        with open(archive, "wb") as f:
            f.write(b"a" * 150)
        assert m._archive_total_size(archive, 0) == 150

    def test_missing_returns_zero(self, tmp_dir):
        m = _make_mixin()
        archive = os.path.join(tmp_dir, "arch.7z")
        assert m._archive_total_size(archive, 0) == 0
        assert m._archive_total_size(archive, 5) == 0

    def test_unrelated_files_ignored(self, tmp_dir):
        m = _make_mixin()
        with open(os.path.join(tmp_dir, "arch.7z.001"), "wb") as f:
            f.write(b"a" * 100)
        with open(os.path.join(tmp_dir, "other.log"), "wb") as f:
            f.write(b"x" * 999)
        archive = os.path.join(tmp_dir, "arch.7z")
        assert m._archive_total_size(archive, 5) == 100


class TestCompressionTargetExists:
    def test_split_parts_exist(self, tmp_dir):
        m = _make_mixin()
        with open(os.path.join(tmp_dir, "arch.7z.001"), "wb") as f:
            f.write(b"x")
        archive = os.path.join(tmp_dir, "arch.7z")
        assert m._compression_target_exists(archive, 5) is True

    def test_base_file_exist_no_split(self, tmp_dir):
        m = _make_mixin()
        archive = os.path.join(tmp_dir, "arch.7z")
        with open(archive, "wb") as f:
            f.write(b"x")
        assert m._compression_target_exists(archive, 0) is True

    def test_nothing_exists(self, tmp_dir):
        m = _make_mixin()
        archive = os.path.join(tmp_dir, "arch.7z")
        assert m._compression_target_exists(archive, 0) is False
        assert m._compression_target_exists(archive, 5) is False


class TestProcessCompressionReturn:
    def test_tar_returns_archive_path(self, tmp_dir):
        m = _make_mixin()
        files = _create_test_files(tmp_dir)
        out = os.path.join(tmp_dir, "out")
        os.makedirs(out)
        result = m.process_compression(files, out, "arch", "TAR", "Normal", None, False, 0)
        expected = os.path.join(out, "arch.tar")
        assert result == expected
        assert os.path.exists(expected)

    def test_tar_dedups_existing_archive(self, tmp_dir):
        m = _make_mixin()
        files = _create_test_files(tmp_dir)
        out = os.path.join(tmp_dir, "out")
        os.makedirs(out)
        with open(os.path.join(out, "arch.tar"), "wb") as f:
            f.write(b"existing")
        result = m.process_compression(files, out, "arch", "TAR", "Normal", None, False, 0)
        expected = os.path.join(out, "arch_1.tar")
        assert result == expected
        assert os.path.exists(expected)

    def test_returns_false_on_failure(self, tmp_dir):
        m = _make_mixin()
        files = _create_test_files(tmp_dir)
        out = os.path.join(tmp_dir, "no_such_dir")
        result = m.process_compression(files, out, "arch", "TAR", "Normal", None, False, 0)
        assert result is False

    def test_7z_returns_archive_path(self, tmp_dir):
        from external_binaries import resolve_binary

        if not resolve_binary("7z"):
            pytest.skip("7-Zip not available")
        m = _make_mixin()
        files = _create_test_files(tmp_dir)
        out = os.path.join(tmp_dir, "out")
        os.makedirs(out)
        result = m.process_compression(files, out, "arch", "7Z", "Normal", None, False, 0)
        assert isinstance(result, str)
        assert result.endswith("arch.7z")
        assert os.path.exists(result)
