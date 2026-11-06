"""LibreOffice PDF→DOCX importer configuration regressions.

Command-construction and failure tests mock ``subprocess.run`` so they run
everywhere. The ``TestRealLibreOffice...`` class contains real-file
integration tests that are skipped when LibreOffice is not installed.
"""

from __future__ import annotations

import io
import subprocess
import types
import zipfile
from contextlib import contextmanager
from pathlib import Path

import fitz
import pytest
from docx import Document
from PIL import Image

import external_binaries
from app.mixins.batch import BatchMixin
from app.mixins.pdf_to_word import PdfToWordMixin


def _make_mixin():
    return PdfToWordMixin.__new__(PdfToWordMixin)


def _write_text_pdf(path: Path, labels: list[str]) -> str:
    with fitz.open() as pdf:
        for label in labels:
            page = pdf.new_page()
            page.insert_text((72, 72), label, fontsize=12)
        pdf.save(str(path))
    return str(path)


def _write_text_heavy_pdf(path: Path) -> str:
    return _write_text_pdf(
        path,
        ["Text heavy document", "Second line of selectable text", "Third line of selectable text"],
    )


def _write_table_pdf(path: Path) -> str:
    rows = [["R0C0", "R0C1", "R0C2"], ["R1C0", "R1C1", "R1C2"], ["R2C0", "R2C1", "R2C2"]]
    column_widths = [90, 90, 90]
    row_height = 24
    x0, y0 = 72, 72

    with fitz.open() as pdf:
        page = pdf.new_page()
        x_positions = [x0]
        for width in column_widths:
            x_positions.append(x_positions[-1] + width)
        y_positions = [y0 + index * row_height for index in range(len(rows) + 1)]

        for x in x_positions:
            page.draw_line((x, y_positions[0]), (x, y_positions[-1]), color=(0, 0, 0), width=1)
        for y in y_positions:
            page.draw_line((x_positions[0], y), (x_positions[-1], y), color=(0, 0, 0), width=1)
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                page.insert_text(
                    (x_positions[column_index] + 4, y_positions[row_index] + 16),
                    value,
                    fontsize=10,
                )
        pdf.save(str(path))
    return str(path)


def _write_multicolumn_pdf(path: Path) -> str:
    with fitz.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), "Left column heading", fontsize=12)
        page.insert_text((72, 96), "Left column body text", fontsize=10)
        page.insert_text((330, 72), "Right column heading", fontsize=12)
        page.insert_text((330, 96), "Right column body text", fontsize=10)
        pdf.save(str(path))
    return str(path)


def _write_image_pdf(path: Path) -> str:
    buffer = io.BytesIO()
    Image.new("RGB", (100, 100), (40, 90, 190)).save(buffer, "PNG")
    with fitz.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), "Document with an image", fontsize=12)
        page.insert_image(fitz.Rect(72, 100, 172, 200), stream=buffer.getvalue())
        pdf.save(str(path))
    return str(path)


def _write_multipage_pdf(path: Path) -> str:
    return _write_text_pdf(path, ["Page one", "Page two", "Page three"])


def _write_invalid_pdf(path: Path) -> str:
    path.write_bytes(b"this is not a pdf")
    return str(path)


def _document_text(document) -> str:
    parts = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return "\n".join(parts)


@contextmanager
def _assert_valid_docx_archive(path: Path):
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        assert "[Content_Types].xml" in names
        assert "word/document.xml" in names
        assert "_rels/.rels" in names
        yield archive


def _fake_successful_soffice(source: Path, calls: list):
    def run(args, **kwargs):
        calls.append((args, kwargs))
        output_dir = Path(args[args.index("--outdir") + 1])
        document = Document()
        document.add_paragraph("LibreOffice output")
        document.save(str(output_dir / f"{source.stem}.docx"))
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    return run


def test_libreoffice_pdf_to_docx_uses_writer_pdf_import(monkeypatch, tmp_path):
    src = Path(_write_text_pdf(tmp_path / "input.pdf", ["LibreOffice text"]))
    output = tmp_path / "converted.docx"
    calls = []
    monkeypatch.setattr(external_binaries, "resolve_binary", lambda _name: "soffice")
    monkeypatch.setattr("subprocess.run", _fake_successful_soffice(src, calls))

    assert _make_mixin()._convert_pdf_to_docx_libreoffice(str(src), str(output)) is True

    args, kwargs = calls[0]
    assert args[0] == "soffice"
    assert "--headless" in args
    assert "--infilter=writer_pdf_import" in args
    assert args[args.index("--convert-to") + 1] == "docx"
    assert args[args.index("--outdir") + 1] == str(tmp_path)
    assert args[-1] == str(src)
    assert kwargs["capture_output"] is True
    assert kwargs["timeout"] == 120
    assert Document(output).paragraphs[0].text == "LibreOffice output"


def test_libreoffice_pdf_to_docx_missing_binary_returns_false(monkeypatch, tmp_path):
    src = _write_text_pdf(tmp_path / "input.pdf", ["No LibreOffice"])
    output = tmp_path / "output.docx"
    monkeypatch.setattr(external_binaries, "resolve_binary", lambda _name: None)

    def unexpected_run(*_args, **_kwargs):
        raise AssertionError("subprocess.run must not be called without LibreOffice")

    monkeypatch.setattr("subprocess.run", unexpected_run)

    assert _make_mixin()._convert_pdf_to_docx_libreoffice(src, str(output)) is False
    assert not output.exists()


def test_libreoffice_pdf_to_docx_timeout_returns_false(monkeypatch, tmp_path):
    src = _write_text_pdf(tmp_path / "input.pdf", ["Timeout"])
    output = tmp_path / "output.docx"
    monkeypatch.setattr(external_binaries, "resolve_binary", lambda _name: "soffice")

    def timeout_run(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("soffice", 120)

    monkeypatch.setattr("subprocess.run", timeout_run)

    assert _make_mixin()._convert_pdf_to_docx_libreoffice(src, str(output)) is False
    assert not output.exists()


def test_libreoffice_pdf_to_docx_missing_output_returns_false(monkeypatch, tmp_path):
    src = _write_text_pdf(tmp_path / "input.pdf", ["No output"])
    output = tmp_path / "output.docx"
    monkeypatch.setattr(external_binaries, "resolve_binary", lambda _name: "soffice")
    monkeypatch.setattr(
        "subprocess.run",
        lambda *_args, **_kwargs: types.SimpleNamespace(returncode=0, stdout="", stderr=""),
    )

    assert _make_mixin()._convert_pdf_to_docx_libreoffice(src, str(output)) is False
    assert not output.exists()


def test_batch_falls_through_libreoffice_failure_to_native_fallback(monkeypatch, tmp_path):
    class CombinedMixin(BatchMixin, PdfToWordMixin):
        pass

    src = _write_text_pdf(tmp_path / "input.pdf", ["Native fallback text"])
    output = tmp_path / "output.docx"
    mixin = CombinedMixin.__new__(CombinedMixin)
    mixin._try_word_com_pdf_to_docx = lambda _pdf, _docx: False
    monkeypatch.setattr(external_binaries, "resolve_binary", lambda _name: "soffice")
    monkeypatch.setattr(
        "subprocess.run",
        lambda *_args, **_kwargs: types.SimpleNamespace(
            returncode=1, stdout="", stderr="LibreOffice import failed"
        ),
    )

    assert mixin._batch_pdf_to_docx(src, str(output)) is True

    document = Document(output)
    assert any("Native fallback text" in paragraph.text for paragraph in document.paragraphs)


def _libreoffice_available() -> bool:
    return external_binaries.resolve_binary("libreoffice") is not None


requires_libreoffice = pytest.mark.skipif(
    not _libreoffice_available(),
    reason="LibreOffice is not installed; real integration tests require it",
)


@pytest.mark.integration
@requires_libreoffice
class TestRealLibreOfficePDFToDOCX:
    def test_text_heavy_pdf(self, tmp_path):
        src = _write_text_heavy_pdf(tmp_path / "text.pdf")
        output = tmp_path / "text.docx"

        assert _make_mixin()._convert_pdf_to_docx_libreoffice(src, str(output)) is True

        with _assert_valid_docx_archive(output):
            pass
        document = Document(output)
        assert "Text heavy document" in _document_text(document)

    def test_table_pdf_preserves_cell_text(self, tmp_path):
        src = _write_table_pdf(tmp_path / "table.pdf")
        output = tmp_path / "table.docx"

        assert _make_mixin()._convert_pdf_to_docx_libreoffice(src, str(output)) is True

        with _assert_valid_docx_archive(output):
            pass
        text = _document_text(Document(output))
        for value in ("R0C0", "R1C1", "R2C2"):
            assert value in text

    def test_multicolumn_pdf_preserves_column_text(self, tmp_path):
        src = _write_multicolumn_pdf(tmp_path / "columns.pdf")
        output = tmp_path / "columns.docx"

        assert _make_mixin()._convert_pdf_to_docx_libreoffice(src, str(output)) is True

        with _assert_valid_docx_archive(output):
            pass
        text = _document_text(Document(output))
        assert "Left column heading" in text
        assert "Right column heading" in text

    def test_image_pdf_preserves_image(self, tmp_path):
        src = _write_image_pdf(tmp_path / "image.pdf")
        output = tmp_path / "image.docx"

        assert _make_mixin()._convert_pdf_to_docx_libreoffice(src, str(output)) is True

        with _assert_valid_docx_archive(output) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/")]
        assert media

    def test_multipage_pdf_preserves_page_text(self, tmp_path):
        src = _write_multipage_pdf(tmp_path / "pages.pdf")
        output = tmp_path / "pages.docx"

        assert _make_mixin()._convert_pdf_to_docx_libreoffice(src, str(output)) is True

        with _assert_valid_docx_archive(output):
            pass
        document = Document(output)
        text = _document_text(document)
        for label in ("Page one", "Page two", "Page three"):
            assert label in text
        assert len(document.sections) >= 1

    def test_invalid_pdf_returns_false(self, tmp_path):
        src = _write_invalid_pdf(tmp_path / "broken.pdf")
        output = tmp_path / "broken.docx"

        assert _make_mixin()._convert_pdf_to_docx_libreoffice(src, str(output)) is False
        assert not output.exists()
