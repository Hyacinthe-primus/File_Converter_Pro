"""Transactional output regressions for AdvancedConverterEngine."""

from pathlib import Path

import fitz
from docx import Document
from PIL import Image

from converter.converters import AdvancedConverterEngine


def _make_pdf(path: Path, text: str = "new") -> Path:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    document.save(str(path))
    document.close()
    return path


def _make_docx(path: Path, text: str = "new") -> Path:
    document = Document()
    document.add_paragraph(text)
    document.save(str(path))
    return path


def _make_png(path: Path) -> Path:
    Image.new("RGB", (16, 16), (10, 120, 200)).save(path, format="PNG")
    return path


def _pdf_text(path: Path) -> str:
    with fitz.open(str(path)) as document:
        return "\n".join(page.get_text().strip() for page in document)


def _no_stage_dirs(parent: Path) -> bool:
    return not list(parent.glob("~fcp_adv_stage_*")) and not list(parent.glob("~fcp_adv_*"))


def test_convert_stages_valid_output_with_final_basename_and_atomic_commit(tmp_path):
    src = tmp_path / "custom-name.txt"
    src.write_text("hello", encoding="utf-8")
    destination = tmp_path / "custom-name.pdf"
    engine = AdvancedConverterEngine()
    seen = []

    def _write(s, d):
        seen.append(Path(d))
        _make_pdf(Path(d), "staged")
        return True

    engine._txt_to_pdf = _write
    result = engine.convert("txt_to_pdf", str(src), str(tmp_path))

    assert result.success is True
    assert result.target == str(destination)
    assert len(seen) == 1
    assert seen[0].name == destination.name
    assert seen[0].parent != tmp_path
    assert seen[0].suffix == ".pdf"
    assert _pdf_text(destination) == "staged"
    assert _no_stage_dirs(tmp_path)


def test_convert_rejects_invalid_output_and_preserves_existing_destination(tmp_path):
    src = tmp_path / "note.txt"
    src.write_text("hello", encoding="utf-8")
    destination = tmp_path / "note.pdf"
    original = b"existing destination must survive"
    destination.write_bytes(original)
    engine = AdvancedConverterEngine()

    engine._txt_to_pdf = lambda s, d: Path(d).write_bytes(b"not a pdf") or True
    result = engine.convert("txt_to_pdf", str(src), str(tmp_path))

    assert result.success is False
    assert "_txt_to_pdf" in result.error
    assert destination.read_bytes() == original
    assert _no_stage_dirs(tmp_path)


def test_convert_replaces_existing_destination_only_after_validation(tmp_path):
    src = tmp_path / "note.txt"
    src.write_text("hello", encoding="utf-8")
    destination = _make_pdf(tmp_path / "note.pdf", "old")
    engine = AdvancedConverterEngine()

    engine._txt_to_pdf = lambda s, d: _make_pdf(Path(d), "new") and True
    result = engine.convert("txt_to_pdf", str(src), str(tmp_path))

    assert result.success is True
    assert _pdf_text(destination) == "new"
    assert _no_stage_dirs(tmp_path)


def test_convert_rejects_empty_output_and_preserves_existing_destination(tmp_path):
    src = tmp_path / "note.txt"
    src.write_text("hello", encoding="utf-8")
    destination = _make_pdf(tmp_path / "note.pdf", "old")
    original = destination.read_bytes()
    engine = AdvancedConverterEngine()

    engine._txt_to_pdf = lambda s, d: True
    result = engine.convert("txt_to_pdf", str(src), str(tmp_path))

    assert result.success is False
    assert "produced no output" in result.error
    assert destination.read_bytes() == original
    assert _no_stage_dirs(tmp_path)


def test_convert_rejects_invalid_docx_output_and_preserves_existing_destination(tmp_path):
    src = tmp_path / "note.txt"
    src.write_text("hello", encoding="utf-8")
    destination = _make_docx(tmp_path / "note.docx", "old")
    original = destination.read_bytes()
    engine = AdvancedConverterEngine()

    engine._txt_to_docx = lambda s, d: Path(d).write_bytes(b"not a docx") or True
    result = engine.convert("txt_to_docx", str(src), str(tmp_path))

    assert result.success is False
    assert "not a DOCX" in result.error
    assert destination.read_bytes() == original
    assert _no_stage_dirs(tmp_path)


def test_convert_rejects_invalid_json_output_and_preserves_existing_destination(tmp_path):
    src = tmp_path / "rows.csv"
    src.write_text("name,age\nAlice,30\n", encoding="utf-8")
    destination = tmp_path / "rows.json"
    original = b'{"old": true}'
    destination.write_bytes(original)
    engine = AdvancedConverterEngine()

    engine._csv_to_json = lambda s, d: Path(d).write_text("{bad", encoding="utf-8") or True
    result = engine.convert("csv_to_json", str(src), str(tmp_path))

    assert result.success is False
    assert "invalid JSON" in result.error
    assert destination.read_bytes() == original
    assert _no_stage_dirs(tmp_path)


def test_convert_rejects_invalid_image_output_and_preserves_existing_destination(tmp_path):
    src = tmp_path / "photo.jpg"
    _make_png(src)
    destination = _make_png(tmp_path / "photo.png")
    original = destination.read_bytes()
    engine = AdvancedConverterEngine()

    def _write(s, d, conversion_type):
        Path(d).write_bytes(b"not a png")
        return True

    engine._image_convert = _write
    result = engine.convert("image_to_png", str(src), str(tmp_path))

    assert result.success is False
    assert "not a PNG" in result.error
    assert destination.read_bytes() == original
    assert _no_stage_dirs(tmp_path)


def test_convert_cleans_temporary_output_when_engine_raises(tmp_path):
    src = tmp_path / "note.txt"
    src.write_text("hello", encoding="utf-8")
    destination = _make_pdf(tmp_path / "note.pdf", "old")
    original = destination.read_bytes()
    engine = AdvancedConverterEngine()

    def _boom(s, d):
        Path(d).write_bytes(b"partial")
        raise RuntimeError("engine crashed")

    engine._txt_to_pdf = _boom
    result = engine.convert("txt_to_pdf", str(src), str(tmp_path))

    assert result.success is False
    assert destination.read_bytes() == original
    assert _no_stage_dirs(tmp_path)


def test_convert_fallback_still_uses_transactional_output(tmp_path):
    src = tmp_path / "doc.rtf"
    src.write_text(r"{\rtf1\ansi hello}", encoding="utf-8")
    destination = tmp_path / "doc.pdf"
    engine = AdvancedConverterEngine()
    seen = []

    engine._rtf_to_pdf_native = lambda s, d: False

    def _fallback(s, d):
        seen.append(Path(d))
        _make_pdf(Path(d), "fallback")
        return True

    engine._rtf_to_pdf = _fallback
    result = engine.convert("rtf_to_pdf", str(src), str(tmp_path))

    assert result.success is True
    assert result.engine_used == "_rtf_to_pdf"
    assert result.degraded is True
    assert seen[0].name == destination.name
    assert seen[0].suffix == ".pdf"
    assert _pdf_text(destination) == "fallback"
    assert _no_stage_dirs(tmp_path)


def test_convert_valid_image_uses_staged_png_extension(tmp_path):
    src = tmp_path / "photo.jpg"
    _make_png(src)
    destination = tmp_path / "photo.png"
    engine = AdvancedConverterEngine()
    seen = []

    def _write(s, d, conversion_type):
        seen.append(Path(d))
        _make_png(Path(d))
        return True

    engine._image_convert = _write
    result = engine.convert("image_to_png", str(src), str(tmp_path))

    assert result.success is True
    assert seen[0].name == destination.name
    assert seen[0].suffix == ".png"
    assert destination.exists()
    assert _no_stage_dirs(tmp_path)


def test_convert_valid_docx_commit_preserves_document_content(tmp_path):
    src = tmp_path / "note.txt"
    src.write_text("hello", encoding="utf-8")
    destination = tmp_path / "note.docx"
    engine = AdvancedConverterEngine()

    engine._txt_to_docx = lambda s, d: _make_docx(Path(d), "transactional") and True
    result = engine.convert("txt_to_docx", str(src), str(tmp_path))

    assert result.success is True
    assert [p.text for p in Document(str(destination)).paragraphs] == ["transactional"]
    assert _no_stage_dirs(tmp_path)


def test_convert_failure_keeps_engine_name_and_fallback_attempts(tmp_path):
    src = tmp_path / "doc.rtf"
    src.write_text(r"{\rtf1\ansi hello}", encoding="utf-8")
    engine = AdvancedConverterEngine()
    calls = []

    def _primary(s, d):
        calls.append("primary")
        Path(d).write_bytes(b"not a pdf")
        return True

    def _fallback(s, d):
        calls.append("fallback")
        return False

    engine._rtf_to_pdf_native = _primary
    engine._rtf_to_pdf = _fallback
    result = engine.convert("rtf_to_pdf", str(src), str(tmp_path))

    assert result.success is False
    assert calls == ["primary", "fallback"]
    assert "_rtf_to_pdf_native" in result.error
    assert "_rtf_to_pdf" in result.error
    assert not (tmp_path / "doc.pdf").exists()
    assert _no_stage_dirs(tmp_path)
