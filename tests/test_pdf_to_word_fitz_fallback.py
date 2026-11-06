"""PDF→DOCX ``with_images`` fallback regressions.

The integration tests build real PDFs and execute the real rich fitz
fallback. Only the external Word COM and pdf2docx tiers are stubbed so the
pipeline is forced into the fallback; the fallback output itself is genuine
and inspected with python-docx.

The mocked tests isolate cancellation and partial-output cleanup, where a
real failure cannot be produced deterministically.
"""

from __future__ import annotations

import io
import threading
from pathlib import Path

import fitz
import pytest
from docx import Document
from docx.oxml.ns import qn
from PIL import Image

import context_menu.conversion_helpers as conversion_helpers


def _write_text_pdf(path: Path, labels: list[str]) -> str:
    with fitz.open() as pdf:
        for label in labels:
            page = pdf.new_page()
            page.insert_text((72, 72), label, fontsize=12)
        pdf.save(str(path))
    return str(path)


def _image_stream(size: tuple[int, int] = (64, 64)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, (190, 40, 40)).save(buffer, "PNG")
    return buffer.getvalue()


def _write_image_pdf(path: Path, text: str | None = None) -> str:
    with fitz.open() as pdf:
        page = pdf.new_page()
        if text:
            page.insert_text((72, 72), text, fontsize=12)
            rect = fitz.Rect(72, 110, 172, 210)
        else:
            rect = fitz.Rect(72, 72, 172, 172)
        page.insert_image(rect, stream=_image_stream())
        pdf.save(str(path))
    return str(path)


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


def _fail_external_engines(monkeypatch):
    calls = {"com": 0, "pdf2docx": 0}

    def fail_com(*_args, **_kwargs):
        calls["com"] += 1
        return False

    def fail_pdf2docx(*_args, **_kwargs):
        calls["pdf2docx"] += 1
        raise RuntimeError("pdf2docx unavailable in test")

    monkeypatch.setattr(conversion_helpers, "_pdf_to_docx_word_com", fail_com)
    monkeypatch.setattr(conversion_helpers, "_pdf_to_docx_pdf2docx", fail_pdf2docx)
    return calls


def _spy_rich_fallback(monkeypatch, module=None):
    target = module or conversion_helpers
    calls = []
    real_fallback = target._solid_fitz_fallback

    def fallback(*args, **kwargs):
        calls.append(args)
        return real_fallback(*args, **kwargs)

    monkeypatch.setattr(target, "_solid_fitz_fallback", fallback)
    return calls


def _convert_with_images(src: str, dst_dir: Path):
    conversion_helpers._convert_pdf_to_docx(src, str(dst_dir), mode="with_images")


def _paragraph_texts(document) -> list[str]:
    return [paragraph.text for paragraph in document.paragraphs]


def _page_breaks(document) -> int:
    return sum(
        1
        for br in document.element.body.iter(qn("w:br"))
        if br.get(qn("w:type")) == "page"
    )


def _staging_artifacts(directory: Path) -> list[Path]:
    return list(directory.glob("~fcp_pdf_word_*")) + list(directory.glob("~fcp_pdf_stage_*"))


@pytest.mark.integration
def test_quick_convert_with_images_reaches_real_rich_fallback(monkeypatch, tmp_path):
    import context_menu.window as cm_window

    src = _write_text_pdf(tmp_path / "quick.pdf", ["Quick Convert selectable text"])
    calls = _fail_external_engines(monkeypatch)
    fallback_calls = _spy_rich_fallback(monkeypatch, cm_window)

    cm_window._convert_pdf_to_docx(src, str(tmp_path), mode="with_images")

    output = tmp_path / "quick.docx"
    assert output.is_file()
    assert calls == {"com": 1, "pdf2docx": 1}
    assert len(fallback_calls) == 1
    assert any("Quick Convert selectable text" in text for text in _paragraph_texts(Document(output)))


@pytest.mark.integration
def test_real_fallback_preserves_selectable_text(monkeypatch, tmp_path):
    src = _write_text_pdf(tmp_path / "text.pdf", ["Selectable fallback text"])
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    calls = _fail_external_engines(monkeypatch)
    fallback_calls = _spy_rich_fallback(monkeypatch)

    _convert_with_images(src, out_dir)

    output = out_dir / "text.docx"
    assert output.is_file()
    assert calls == {"com": 1, "pdf2docx": 1}
    assert len(fallback_calls) == 1
    assert any("Selectable fallback text" in text for text in _paragraph_texts(Document(output)))
    assert _staging_artifacts(out_dir) == []


@pytest.mark.integration
def test_real_fallback_preserves_embedded_image(monkeypatch, tmp_path):
    src = _write_image_pdf(tmp_path / "image.pdf")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _fail_external_engines(monkeypatch)

    _convert_with_images(src, out_dir)

    document = Document(out_dir / "image.docx")
    assert len(document.inline_shapes) >= 1
    assert all(not text.strip() for text in _paragraph_texts(document))


@pytest.mark.integration
def test_real_fallback_preserves_text_and_image(monkeypatch, tmp_path):
    src = _write_image_pdf(tmp_path / "mixed.pdf", text="Mixed page text")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _fail_external_engines(monkeypatch)

    _convert_with_images(src, out_dir)

    document = Document(out_dir / "mixed.docx")
    assert any("Mixed page text" in text for text in _paragraph_texts(document))
    assert len(document.inline_shapes) >= 1


@pytest.mark.integration
def test_real_fallback_preserves_detected_table(monkeypatch, tmp_path):
    src = _write_table_pdf(tmp_path / "table.pdf")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _fail_external_engines(monkeypatch)

    _convert_with_images(src, out_dir)

    document = Document(out_dir / "table.docx")
    assert len(document.tables) == 1
    cells = [cell.text for row in document.tables[0].rows for cell in row.cells]
    assert cells == ["R0C0", "R0C1", "R0C2", "R1C0", "R1C1", "R1C2", "R2C0", "R2C1", "R2C2"]


@pytest.mark.integration
def test_real_fallback_preserves_multipage_structure(monkeypatch, tmp_path):
    src = _write_text_pdf(tmp_path / "pages.pdf", ["Page one", "Page two", "Page three"])
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _fail_external_engines(monkeypatch)

    _convert_with_images(src, out_dir)

    document = Document(out_dir / "pages.docx")
    texts = _paragraph_texts(document)
    assert [text for text in texts if text] == ["Page one", "Page two", "Page three"]
    assert _page_breaks(document) == 2


@pytest.mark.integration
def test_real_fallback_preserves_scanned_page_image_without_ocr(monkeypatch, tmp_path):
    src = _write_image_pdf(tmp_path / "scan.pdf", text=None)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _fail_external_engines(monkeypatch)

    _convert_with_images(src, out_dir)

    document = Document(out_dir / "scan.docx")
    assert len(document.inline_shapes) == 1
    assert all(not text.strip() for text in _paragraph_texts(document))


@pytest.mark.integration
def test_real_fitz_failure_preserves_existing_destination(monkeypatch, tmp_path):
    src = tmp_path / "broken.pdf"
    src.write_bytes(b"this is not a pdf")
    output = tmp_path / "broken.docx"
    output.write_bytes(b"existing destination")
    _fail_external_engines(monkeypatch)

    with pytest.raises(RuntimeError, match="All PDF→DOCX methods failed"):
        _convert_with_images(str(src), tmp_path)

    assert output.read_bytes() == b"existing destination"
    assert _staging_artifacts(tmp_path) == []


def test_mocked_fitz_failure_cleans_partial_output_and_preserves_destination(monkeypatch, tmp_path):
    src = _write_text_pdf(tmp_path / "input.pdf", ["Partial fallback"])
    output = tmp_path / "input.docx"
    output.write_bytes(b"existing destination")
    _fail_external_engines(monkeypatch)

    def fail_fallback(_pdf_path, docx_path):
        Path(docx_path).write_bytes(b"partial fallback output")
        raise RuntimeError("fitz fallback failed")

    monkeypatch.setattr(conversion_helpers, "_solid_fitz_fallback", fail_fallback)

    with pytest.raises(RuntimeError, match="All PDF→DOCX methods failed"):
        _convert_with_images(src, tmp_path)

    assert output.read_bytes() == b"existing destination"
    assert _staging_artifacts(tmp_path) == []


def test_cancellation_before_conversion_preserves_existing_destination(monkeypatch, tmp_path):
    src = _write_text_pdf(tmp_path / "input.pdf", ["Cancelled"])
    output = tmp_path / "input.docx"
    output.write_bytes(b"existing destination")
    cancel_event = threading.Event()
    cancel_event.set()
    calls = _fail_external_engines(monkeypatch)
    fallback_calls = _spy_rich_fallback(monkeypatch)

    with pytest.raises(conversion_helpers._ConversionCancelled):
        conversion_helpers._convert_pdf_to_docx(
            src,
            str(tmp_path),
            cancel_event=cancel_event,
            mode="with_images",
        )

    assert calls == {"com": 0, "pdf2docx": 0}
    assert fallback_calls == []
    assert output.read_bytes() == b"existing destination"
    assert _staging_artifacts(tmp_path) == []


def test_cancellation_during_conversion_skips_remaining_fallbacks(monkeypatch, tmp_path):
    src = _write_text_pdf(tmp_path / "input.pdf", ["Cancelled"])
    output = tmp_path / "input.docx"
    output.write_bytes(b"existing destination")
    cancel_event = threading.Event()
    pdf2docx_calls = []
    fallback_calls = _spy_rich_fallback(monkeypatch)

    def cancel_com(*_args, **_kwargs):
        cancel_event.set()
        return False

    monkeypatch.setattr(conversion_helpers, "_pdf_to_docx_word_com", cancel_com)
    monkeypatch.setattr(
        conversion_helpers,
        "_pdf_to_docx_pdf2docx",
        lambda *args, **kwargs: pdf2docx_calls.append((args, kwargs)),
    )

    with pytest.raises(conversion_helpers._ConversionCancelled):
        conversion_helpers._convert_pdf_to_docx(
            src,
            str(tmp_path),
            cancel_event=cancel_event,
            mode="with_images",
        )

    assert pdf2docx_calls == []
    assert fallback_calls == []
    assert output.read_bytes() == b"existing destination"
    assert _staging_artifacts(tmp_path) == []


def _patch_config(monkeypatch, config):
    import config as config_module

    class FakeConfigManager:
        def load_config(self):
            return config

    monkeypatch.setattr(config_module, "ConfigManager", FakeConfigManager)


@pytest.mark.integration
@pytest.mark.parametrize("module_name", ["watcher", "scheduler"])
def test_automation_with_images_reaches_real_rich_fallback(monkeypatch, tmp_path, module_name):
    from tasks import scheduler, watcher

    src = _write_image_pdf(tmp_path / "automation.pdf", text="Automation mixed text")
    out_dir = tmp_path / "out"
    _patch_config(monkeypatch, {"pdf_to_word_mode": "with_images"})
    calls = _fail_external_engines(monkeypatch)
    fallback_calls = _spy_rich_fallback(monkeypatch)
    runner = watcher._run_conversion if module_name == "watcher" else scheduler._run_conversion

    runner("pdf_to_docx", src, str(out_dir))

    output = out_dir / "automation.docx"
    assert output.is_file()
    assert calls == {"com": 1, "pdf2docx": 1}
    assert len(fallback_calls) == 1
    document = Document(output)
    assert any("Automation mixed text" in text for text in _paragraph_texts(document))
    assert len(document.inline_shapes) >= 1
