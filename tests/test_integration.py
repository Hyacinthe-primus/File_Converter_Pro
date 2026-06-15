"""Integration tests for file conversions — create real temp files and verify output."""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _write_text(path, content="Hello world, this is a test file.\nLine two of the text."):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _write_json(path, data='{"key": "value", "number": 42}'):
    with open(path, "w", encoding="utf-8") as f:
        f.write(data)


def _write_csv(path, content="name,age\nAlice,30\nBob,25\n"):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _write_html(path, content="<html><body><h1>Test</h1><p>Hello</p></body></html>"):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


class TestTxtToPdf:
    def test_txt_to_pdf_creates_file(self, tmp_dir):
        from converter.converters import AdvancedConverterEngine
        src = os.path.join(tmp_dir, "test.txt")
        dst = os.path.join(tmp_dir, "test.pdf")
        _write_text(src)
        engine = AdvancedConverterEngine()
        result = engine.convert("txt_to_pdf", src, tmp_dir)
        assert result.success or os.path.exists(dst)

    def test_txt_to_pdf_with_long_text(self, tmp_dir):
        from converter.converters import AdvancedConverterEngine
        src = os.path.join(tmp_dir, "long.txt")
        dst = os.path.join(tmp_dir, "long.pdf")
        _write_text(src, "Line {}\n".format("test " * 50) * 100)
        engine = AdvancedConverterEngine()
        result = engine.convert("txt_to_pdf", src, tmp_dir)
        assert result.success or os.path.exists(dst)


class TestCsvJson:
    def test_csv_to_json(self, tmp_dir):
        from converter.converters import AdvancedConverterEngine
        src = os.path.join(tmp_dir, "data.csv")
        dst = os.path.join(tmp_dir, "data.json")
        _write_csv(src)
        engine = AdvancedConverterEngine()
        result = engine.convert("csv_to_json", src, tmp_dir)
        assert result.success
        assert os.path.exists(dst)
        import json
        with open(dst) as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 2

    def test_json_to_csv(self, tmp_dir):
        from converter.converters import AdvancedConverterEngine
        src = os.path.join(tmp_dir, "data.json")
        dst = os.path.join(tmp_dir, "data.csv")
        _write_json(src, '[{"name":"Alice","age":30},{"name":"Bob","age":25}]')
        engine = AdvancedConverterEngine()
        result = engine.convert("json_to_csv", src, tmp_dir)
        assert result.success
        assert os.path.exists(dst)
        with open(dst) as f:
            lines = f.readlines()
        assert len(lines) >= 3  # header + 2 rows

    def test_csv_to_json_special_chars(self, tmp_dir):
        from converter.converters import AdvancedConverterEngine
        src = os.path.join(tmp_dir, "special.csv")
        dst = os.path.join(tmp_dir, "special.json")
        _write_csv(src, 'name,description\n"Hello, World","A test"\n')
        engine = AdvancedConverterEngine()
        result = engine.convert("csv_to_json", src, tmp_dir)
        assert result.success
        assert os.path.exists(dst)


class TestHtmlToPdf:
    def test_html_to_pdf_creates_file(self, tmp_dir):
        from converter.converters import AdvancedConverterEngine
        src = os.path.join(tmp_dir, "test.html")
        dst = os.path.join(tmp_dir, "test.pdf")
        _write_html(src)
        engine = AdvancedConverterEngine()
        result = engine.convert("html_to_pdf", src, tmp_dir)
        assert result.success or os.path.exists(dst)


class TestPdfToHtml:
    def test_import(self):
        from converter.converters import AdvancedConverterEngine
        engine = AdvancedConverterEngine()
        assert hasattr(engine, '_pdf_to_html')


class TestBatchConversion:
    def test_batch_returns_results(self, tmp_dir):
        from converter.converters import AdvancedConverterEngine
        src1 = os.path.join(tmp_dir, "a.txt")
        src2 = os.path.join(tmp_dir, "b.txt")
        _write_text(src1, "File A")
        _write_text(src2, "File B")
        engine = AdvancedConverterEngine()
        results = engine.convert_batch("txt_to_pdf", [src1, src2], tmp_dir)
        assert len(results) == 2
        assert all(hasattr(r, "success") for r in results)


class TestConversionResult:
    def test_result_success(self):
        from converter.converters import ConversionResult
        r = ConversionResult(True, "input.pdf", "output.docx", elapsed=1.5)
        assert r.success is True
        assert r.source == "input.pdf"
        assert r.elapsed == 1.5
        assert "OK" in repr(r)

    def test_result_failure(self):
        from converter.converters import ConversionResult
        r = ConversionResult(False, "input.pdf", "", error="File not found")
        assert r.success is False
        assert "ERR" in repr(r)


class TestDispatcher:
    def test_dispatch_txt_to_pdf(self):
        from converter.converters import AdvancedConverterEngine
        engine = AdvancedConverterEngine()
        method, ext = engine._DISPATCH["txt_to_pdf"]
        assert method == "_txt_to_pdf"
        assert ext == "pdf"

    def test_dispatch_image_to_png(self):
        from converter.converters import AdvancedConverterEngine
        engine = AdvancedConverterEngine()
        method, ext = engine._DISPATCH["image_to_png"]
        assert ext == "png"

    def test_dispatch_audio_to_mp3(self):
        from converter.converters import AdvancedConverterEngine
        engine = AdvancedConverterEngine()
        method, ext = engine._DISPATCH["audio_to_mp3"]
        assert ext == "mp3"
