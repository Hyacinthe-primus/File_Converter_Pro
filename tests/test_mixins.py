"""Tests for mixin utility functions."""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_format_size_bytes():
    from app.mixins.file_management import FileManagementMixin
    m = FileManagementMixin()
    assert m.format_size(0) == "0.00 B"
    assert m.format_size(500) == "500.00 B"


def test_format_size_kb():
    from app.mixins.file_management import FileManagementMixin
    m = FileManagementMixin()
    assert m.format_size(1024) == "1.00 KB"
    assert m.format_size(1536) == "1.50 KB"


def test_format_size_mb():
    from app.mixins.file_management import FileManagementMixin
    m = FileManagementMixin()
    assert m.format_size(1024 * 1024) == "1.00 MB"
    assert m.format_size(1024 * 1024 * 5.5) == "5.50 MB"


def test_format_size_gb():
    from app.mixins.file_management import FileManagementMixin
    m = FileManagementMixin()
    assert m.format_size(1024 ** 3) == "1.00 GB"


def test_format_size_tb():
    from app.mixins.file_management import FileManagementMixin
    m = FileManagementMixin()
    assert m.format_size(1024 ** 4) == "1.00 TB"


def test_format_size_pb():
    from app.mixins.file_management import FileManagementMixin
    m = FileManagementMixin()
    assert m.format_size(1024 ** 5) == "1.00 PB"


def test_calculate_folder_size_empty():
    from app.mixins.file_management import FileManagementMixin
    m = FileManagementMixin()
    d = tempfile.mkdtemp()
    try:
        assert m.calculate_folder_size(d) == 0
    finally:
        shutil.rmtree(d)


def test_calculate_folder_size_with_files():
    from app.mixins.file_management import FileManagementMixin
    m = FileManagementMixin()
    d = tempfile.mkdtemp()
    try:
        f1 = os.path.join(d, "a.txt")
        f2 = os.path.join(d, "b.txt")
        with open(f1, "w") as f:
            f.write("hello")
        with open(f2, "w") as f:
            f.write("world!")
        assert m.calculate_folder_size(d) == 11
    finally:
        shutil.rmtree(d)


def test_calculate_folder_size_nested():
    from app.mixins.file_management import FileManagementMixin
    m = FileManagementMixin()
    d = tempfile.mkdtemp()
    try:
        sub = os.path.join(d, "sub")
        os.makedirs(sub)
        with open(os.path.join(d, "a.txt"), "w") as f:
            f.write("abc")
        with open(os.path.join(sub, "b.txt"), "w") as f:
            f.write("de")
        assert m.calculate_folder_size(d) == 5
    finally:
        shutil.rmtree(d)


def test_sanitize_xml_clean():
    from app.mixins.word_to_pdf import _sanitize_xml
    assert _sanitize_xml("hello world") == "hello world"
    assert _sanitize_xml("test 123") == "test 123"


def test_sanitize_xml_control_chars():
    from app.mixins.word_to_pdf import _sanitize_xml
    assert _sanitize_xml("a\x00b") == "ab"
    assert _sanitize_xml("a\x08b") == "ab"
    assert _sanitize_xml("a\x0Bb") == "ab"
    assert _sanitize_xml("a\x0Cb") == "ab"
    assert _sanitize_xml("a\x0Eb") == "ab"
    assert _sanitize_xml("a\x1Fb") == "ab"
    assert _sanitize_xml("a\x7Fb") == "ab"


def test_sanitize_xml_preserves_normal():
    from app.mixins.word_to_pdf import _sanitize_xml
    assert _sanitize_xml("Hello\tWorld") == "Hello\tWorld"
    assert _sanitize_xml("Line1\nLine2") == "Line1\nLine2"


def test_sanitize_xml_none():
    from app.mixins.word_to_pdf import _sanitize_xml
    assert _sanitize_xml(None) == ""


def test_sanitize_xml_empty():
    from app.mixins.word_to_pdf import _sanitize_xml
    assert _sanitize_xml("") == ""


def test_get_archive_extension_zip():
    from app.mixins.compression import CompressionMixin
    m = CompressionMixin()
    m.translate_text = lambda x: x
    assert m.get_archive_extension("ZIP") == "zip"


def test_get_archive_extension_rar():
    from app.mixins.compression import CompressionMixin
    m = CompressionMixin()
    m.translate_text = lambda x: x
    assert m.get_archive_extension("RAR") == "rar"


def test_get_archive_extension_tar_gz():
    from app.mixins.compression import CompressionMixin
    m = CompressionMixin()
    m.translate_text = lambda x: x
    assert m.get_archive_extension("TAR.GZ") == "tar.gz"


def test_get_archive_extension_tar():
    from app.mixins.compression import CompressionMixin
    m = CompressionMixin()
    m.translate_text = lambda x: x
    assert m.get_archive_extension("TAR") == "tar"


def test_get_archive_extension_unknown():
    from app.mixins.compression import CompressionMixin
    m = CompressionMixin()
    m.translate_text = lambda x: x
    assert m.get_archive_extension("UNKNOWN") == "zip"


def test_get_archive_extension_translated():
    from app.mixins.compression import CompressionMixin
    m = CompressionMixin()
    translations = {"ZIP": "ZIP", "RAR": "RAR", "TAR.GZ": "TAR.GZ", "TAR": "TAR"}
    m.translate_text = lambda x: translations.get(x, x)
    assert m.get_archive_extension("ZIP") == "zip"
    assert m.get_archive_extension("RAR") == "rar"
