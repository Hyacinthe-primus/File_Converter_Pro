"""DOCX-to-PDF consolidation, fallback, and real-artifact regressions."""

import os
import subprocess
import sys
import threading
from pathlib import Path

import fitz
import pytest
from docx import Document
from docx.shared import Inches
from PIL import Image

from context_menu import conversion_helpers
from external_binaries import resolve_binary
from utils.pdf_artifacts import validate_docx_input, validate_pdf_artifact

LIBREOFFICE = resolve_binary("libreoffice")


def _make_docx(path: Path, paragraphs: list[str]) -> Path:
    document = Document()
    for text in paragraphs:
        document.add_paragraph(text)
    document.save(str(path))
    return path


def _make_complex_docx(path: Path) -> Path:
    document = Document()
    document.add_heading("Real conversion document", level=1)
    for index in range(30):
        document.add_paragraph(f"Paragraph {index + 1}: " + "text " * 20)
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Table A"
    table.cell(0, 1).text = "Table B"
    table.cell(1, 0).text = "Table C"
    table.cell(1, 1).text = "Table D"
    image_path = path.parent / "image.png"
    Image.new("RGB", (120, 80), (20, 120, 220)).save(image_path)
    document.add_picture(str(image_path), width=Inches(1.0))
    document.save(str(path))
    return path


def _make_pdf(path: Path, text: str) -> Path:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    document.save(str(path))
    document.close()
    return path


def _pdf_text(path: Path) -> str:
    with fitz.open(str(path)) as pdf:
        return "\n".join(page.get_text() for page in pdf)


def _word_registered() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "Word.Application"):
            return True
    except OSError:
        return False


WORD_AVAILABLE = _word_registered()


def test_validate_docx_input_handles_missing_invalid_and_legacy_files(tmp_path):
    assert validate_docx_input(str(tmp_path / "missing.docx")) == (False, "missing input")

    empty = tmp_path / "empty.docx"
    empty.write_bytes(b"")
    assert validate_docx_input(str(empty)) == (False, "empty input")

    invalid = tmp_path / "invalid.docx"
    invalid.write_bytes(b"not a docx")
    assert validate_docx_input(str(invalid)) == (False, "not a DOCX")

    valid = _make_docx(tmp_path / "valid.docx", ["valid"])
    assert validate_docx_input(str(valid)) == (True, "")

    legacy = tmp_path / "legacy.doc"
    legacy.write_bytes(b"legacy binary word document")
    assert validate_docx_input(str(legacy)) == (True, "")


def test_docx_to_pdf_reportlab_fallback_without_word_or_libreoffice(monkeypatch, tmp_path):
    import external_binaries

    monkeypatch.setattr(conversion_helpers.sys, "platform", "linux")
    monkeypatch.setattr(external_binaries, "resolve_binary", lambda _name: None)
    paragraphs = [f"Paragraph {index + 1}: " + "text " * 20 for index in range(40)]
    source = _make_docx(tmp_path / "input.docx", paragraphs)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    conversion_helpers._convert_docx_to_pdf(str(source), str(out_dir))

    output = out_dir / "input.pdf"
    assert validate_pdf_artifact(str(output)) == (True, "")
    with fitz.open(str(output)) as pdf:
        assert pdf.page_count >= 2
        assert "Paragraph 1" in "\n".join(page.get_text() for page in pdf)
    assert not list(out_dir.glob("~fcp_pdf_*"))


def test_docx_to_pdf_libreoffice_timeout_falls_back_to_reportlab(monkeypatch, tmp_path):
    import external_binaries

    monkeypatch.setattr(conversion_helpers.sys, "platform", "linux")
    monkeypatch.setattr(external_binaries, "resolve_binary", lambda _name: "soffice")

    def timed_out(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("soffice", 120)

    monkeypatch.setattr("subprocess.run", timed_out)
    source = _make_docx(tmp_path / "input.docx", ["Timeout fallback text"])
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    conversion_helpers._convert_docx_to_pdf(str(source), str(out_dir))

    output = out_dir / "input.pdf"
    assert "Timeout fallback text" in _pdf_text(output)
    assert not list(out_dir.glob("~fcp_pdf_*"))


def test_docx_to_pdf_libreoffice_accepts_valid_output_on_nonzero_exit(monkeypatch, tmp_path):
    import external_binaries

    monkeypatch.setattr(conversion_helpers.sys, "platform", "linux")
    monkeypatch.setattr(external_binaries, "resolve_binary", lambda _name: "soffice")
    source = _make_docx(tmp_path / "input.docx", ["input"])
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    def run(args, **_kwargs):
        target_dir = Path(args[args.index("--outdir") + 1])
        _make_pdf(target_dir / f"{source.stem}.pdf", "libreoffice")
        return type("Result", (), {"returncode": 1, "stderr": "non-fatal warning"})()

    monkeypatch.setattr("subprocess.run", run)

    conversion_helpers._convert_docx_to_pdf(str(source), str(out_dir))

    assert _pdf_text(out_dir / "input.pdf").strip() == "libreoffice"


def test_docx_to_pdf_cancellation_preserves_destination_and_cleans_staging(tmp_path):
    source = _make_docx(tmp_path / "input.docx", ["input"])
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    output = _make_pdf(out_dir / "input.pdf", "stale")
    original = output.read_bytes()
    cancel_event = threading.Event()
    cancel_event.set()

    with pytest.raises(conversion_helpers._ConversionCancelled):
        conversion_helpers._convert_docx_to_pdf(str(source), str(out_dir), cancel_event)

    assert output.read_bytes() == original
    assert not list(out_dir.glob("~fcp_pdf_*"))


@pytest.mark.parametrize("module_name", ["watcher", "scheduler"])
def test_automation_rejects_invalid_docx_before_pipeline(monkeypatch, tmp_path, module_name):
    from tasks import scheduler, watcher

    calls = []
    monkeypatch.setattr(
        conversion_helpers,
        "run_conversion_pipeline",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    source = tmp_path / "invalid.docx"
    source.write_bytes(b"not a docx")
    out_dir = tmp_path / "out"
    module = watcher if module_name == "watcher" else scheduler

    with pytest.raises(RuntimeError, match="Invalid Word input: not a DOCX"):
        module._run_conversion("docx_to_pdf", str(source), str(out_dir))

    assert calls == []


@pytest.mark.integration
@pytest.mark.skipif(
    not LIBREOFFICE,
    reason="LibreOffice is not installed; real integration test skipped",
)
def test_real_libreoffice_docx_to_pdf(monkeypatch, tmp_path):
    monkeypatch.setattr(conversion_helpers.sys, "platform", "linux")
    source = _make_complex_docx(tmp_path / "input.docx")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    conversion_helpers._convert_docx_to_pdf(str(source), str(out_dir))

    output = out_dir / "input.pdf"
    assert validate_pdf_artifact(str(output)) == (True, "")
    with fitz.open(str(output)) as pdf:
        assert pdf.page_count >= 2
        text = "\n".join(page.get_text() for page in pdf)
    assert "Real conversion document" in text
    assert "Table A" in text


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("FCP_REAL_WORD_TESTS") != "1" or not WORD_AVAILABLE,
    reason="Set FCP_REAL_WORD_TESTS=1 with Microsoft Word installed to run the real COM test",
)
def test_real_word_com_docx_to_pdf(tmp_path):
    source = _make_complex_docx(tmp_path / "input.docx")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    conversion_helpers._convert_docx_to_pdf(str(source), str(out_dir))

    output = out_dir / "input.pdf"
    assert validate_pdf_artifact(str(output)) == (True, "")
    with fitz.open(str(output)) as pdf:
        assert pdf.page_count >= 2
        text = "\n".join(page.get_text() for page in pdf)
    assert "Real conversion document" in text
    assert "Table A" in text
