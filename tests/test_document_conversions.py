"""Tests for document conversions — using mixin methods directly."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter.mixins.document_converters import DocumentConverters


def _engine():
    return DocumentConverters()


def test_txt_to_pdf(tmp_path):
    src = tmp_path / "test.txt"
    src.write_text("Hello World\nLine 2\nLine 3", encoding="utf-8")
    dst = tmp_path / "test.pdf"
    engine = _engine()
    result = engine._txt_to_pdf(str(src), str(dst))
    assert result is True
    assert dst.exists()
    assert dst.stat().st_size > 0


def test_txt_to_pdf_empty(tmp_path):
    src = tmp_path / "empty.txt"
    src.write_text("", encoding="utf-8")
    dst = tmp_path / "empty.pdf"
    engine = _engine()
    result = engine._txt_to_pdf(str(src), str(dst))
    assert result is True
    assert dst.exists()


def test_csv_to_json(tmp_path):
    src = tmp_path / "test.csv"
    src.write_text("name,age\nAlice,30\nBob,25", encoding="utf-8")
    dst = tmp_path / "test.json"
    engine = _engine()
    result = engine._csv_to_json(str(src), str(dst))
    assert result is True
    data = json.loads(dst.read_text(encoding="utf-8"))
    assert len(data) == 2
    assert data[0]["name"] == "Alice"
    assert data[1]["age"] == "25"


def test_json_to_csv(tmp_path):
    src = tmp_path / "test.json"
    src.write_text(json.dumps([{"a": 1, "b": 2}, {"a": 3, "b": 4}]), encoding="utf-8")
    dst = tmp_path / "test.csv"
    engine = _engine()
    result = engine._json_to_csv(str(src), str(dst))
    assert result is True
    lines = dst.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3  # header + 2 rows
    assert "a,b" in lines[0]


def test_txt_to_docx(tmp_path):
    src = tmp_path / "test.txt"
    src.write_text("Hello\nWorld", encoding="utf-8")
    dst = tmp_path / "test.docx"
    engine = _engine()
    result = engine._txt_to_docx(str(src), str(dst))
    assert result is True
    assert dst.exists()
    assert dst.stat().st_size > 0


def test_json_to_csv_empty(tmp_path):
    src = tmp_path / "empty.json"
    src.write_text("[]", encoding="utf-8")
    dst = tmp_path / "empty.csv"
    engine = _engine()
    result = engine._json_to_csv(str(src), str(dst))
    assert result is False


def test_csv_to_json_special_chars(tmp_path):
    src = tmp_path / "special.csv"
    src.write_text("text,value\n\"hello, world\",42\n\"line1\nline2\",99", encoding="utf-8")
    dst = tmp_path / "special.json"
    engine = _engine()
    result = engine._csv_to_json(str(src), str(dst))
    assert result is True
    data = json.loads(dst.read_text(encoding="utf-8"))
    assert data[0]["text"] == "hello, world"


def test_rtf_to_spans():
    engine = _engine()
    raw = r"{\rtf1\ansi {\b Bold} and normal}"
    spans = engine._rtf_to_spans(raw)
    assert len(spans) > 0
    texts = [s["text"] for s in spans if s.get("text")]
    full = "".join(texts)
    assert "Bold" in full
