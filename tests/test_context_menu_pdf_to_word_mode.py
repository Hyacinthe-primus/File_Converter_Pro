"""PDF→Word mode propagation for context-menu Quick Convert."""

import sys
import types
from pathlib import Path

import pytest

import context_menu.conversion_helpers as conversion_helpers
import context_menu.window as cm_window


def _fake_pdf2docx(monkeypatch):
    calls = []
    module = types.ModuleType("pdf2docx")

    class FakeConverter:
        def __init__(self, path):
            calls.append(("init", path))

        def convert(self, path, **kwargs):
            calls.append(("convert", path, kwargs))
            from docx import Document

            document = Document()
            document.add_paragraph("fake pdf2docx output")
            document.save(path)

        def close(self):
            calls.append(("close",))

    module.Converter = FakeConverter
    monkeypatch.setitem(sys.modules, "pdf2docx", module)
    return calls


def _fake_winreg(monkeypatch):
    calls = []
    module = types.ModuleType("winreg")
    module.HKEY_CLASSES_ROOT = object()

    def _open_key(*args):
        calls.append(args)
        raise OSError("Word not installed")

    module.OpenKey = _open_key
    monkeypatch.setitem(sys.modules, "winreg", module)
    return calls


def _fake_config(monkeypatch, config):
    import config as config_module

    class FakeConfigManager:
        def load_config(self):
            return config

    monkeypatch.setattr(config_module, "ConfigManager", FakeConfigManager)


def test_with_images_uses_pdf2docx_route(monkeypatch, tmp_path):
    src = tmp_path / "input.pdf"
    src.write_bytes(b"%PDF")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    pdf2docx_calls = _fake_pdf2docx(monkeypatch)
    winreg_calls = _fake_winreg(monkeypatch)
    text_calls = []
    monkeypatch.setattr(cm_window, "convert_pdf_text_to_docx", lambda *a, **k: text_calls.append((a, k)))
    monkeypatch.setattr(cm_window.sys, "platform", "win32")

    cm_window._convert_pdf_to_docx(str(src), str(out_dir), mode="with_images")

    assert winreg_calls
    assert [call[0] for call in pdf2docx_calls] == ["init", "convert", "close"]
    assert text_calls == []


def test_text_only_skips_com_and_pdf2docx(monkeypatch, tmp_path):
    src = tmp_path / "input.pdf"
    src.write_bytes(b"%PDF")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    text_calls = []

    def fake_text(pdf_path, docx_path, **kwargs):
        text_calls.append((pdf_path, docx_path, kwargs))
        from docx import Document

        document = Document()
        document.add_paragraph("fake text output")
        document.save(docx_path)

    monkeypatch.setattr(cm_window, "convert_pdf_text_to_docx", fake_text)
    pdf2docx_calls = _fake_pdf2docx(monkeypatch)
    winreg_calls = _fake_winreg(monkeypatch)
    monkeypatch.setattr(cm_window.sys, "platform", "win32")

    cm_window._convert_pdf_to_docx(str(src), str(out_dir), mode="text_only")

    assert len(text_calls) == 1
    assert text_calls[0][0] == str(src.resolve())
    temporary_path = Path(text_calls[0][1])
    assert temporary_path.parent == out_dir.resolve()
    assert temporary_path.suffix == ".docx"
    assert not _temp_files(out_dir)
    assert pdf2docx_calls == []
    assert winreg_calls == []


def _write_text_pdf(path, text="Quick Convert text"):
    import fitz

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), text)
    pdf.save(str(path))
    pdf.close()


def _temp_files(directory):
    return list(Path(directory).glob("~fcp_pdf_word_*"))


def test_temporary_output_is_ignored_by_watcher(tmp_path):
    from tasks.watcher import _is_temp_file

    temp_path = Path(cm_window._temporary_docx_path(str(tmp_path / "input.docx")))
    try:
        assert _is_temp_file(temp_path)
    finally:
        temp_path.unlink()


def test_text_only_extracts_text_without_images(tmp_path):
    import io

    import fitz
    from docx import Document
    from PIL import Image

    src = tmp_path / "input.pdf"
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Quick Convert text")
    image_bytes = io.BytesIO()
    Image.new("RGB", (20, 20), (255, 0, 0)).save(image_bytes, "PNG")
    page.insert_image(fitz.Rect(72, 100, 120, 148), stream=image_bytes.getvalue())
    pdf.save(str(src))
    pdf.close()

    cm_window._convert_pdf_to_docx(str(src), str(tmp_path), mode="text_only")

    output = tmp_path / "input.docx"
    assert output.is_file()
    converted = Document(str(output))
    assert any("Quick Convert text" in paragraph.text for paragraph in converted.paragraphs)
    assert len(converted.inline_shapes) == 0


def test_load_pdf_to_word_mode_reads_persisted_value(monkeypatch):
    _fake_config(monkeypatch, {"pdf_to_word_mode": "text_only"})

    assert cm_window._load_pdf_to_word_mode() == "text_only"


@pytest.mark.parametrize(
    "config",
    [
        {},
        {"pdf_to_word_mode": None},
        {"pdf_to_word_mode": "unsupported"},
        None,
    ],
)
def test_missing_or_invalid_mode_falls_back_to_with_images(monkeypatch, config):
    _fake_config(monkeypatch, config)

    assert cm_window._load_pdf_to_word_mode() == "with_images"


def test_conversion_thread_uses_persisted_mode(monkeypatch, tmp_path):
    src = tmp_path / "input.pdf"
    src.write_bytes(b"%PDF")
    _fake_config(monkeypatch, {"pdf_to_word_mode": "text_only"})
    seen = []
    monkeypatch.setattr(cm_window, "_convert_pdf_to_docx", lambda *a, **k: seen.append((a, k)))
    thread = cm_window.ConversionThread([str(src)], "pdf_to_docx")
    done = []
    thread.done.connect(lambda *args: done.append(args))

    thread.run()

    assert len(seen) == 1
    args, kwargs = seen[0]
    assert args[0] == str(src)
    assert kwargs == {"mode": "text_only"}
    assert done and done[0][0] is True


def _assert_legacy_pdf_call(runner, monkeypatch, tmp_path):
    src = tmp_path / "input.pdf"
    src.write_bytes(b"%PDF")
    out_dir = tmp_path / "out"
    seen = []
    _fake_config(monkeypatch, {"pdf_to_word_mode": "with_images"})
    monkeypatch.setattr(conversion_helpers, "_convert_pdf_to_docx", lambda *a, **k: seen.append((a, k)))

    runner("pdf_to_docx", str(src), str(out_dir))

    assert seen == [((str(src), str(out_dir)), {"mode": "with_images"})]


def test_watcher_pdf_route_remains_compatible(monkeypatch, tmp_path):
    from tasks import watcher

    _assert_legacy_pdf_call(watcher._run_conversion, monkeypatch, tmp_path)


def test_scheduler_pdf_route_remains_compatible(monkeypatch, tmp_path):
    from tasks import scheduler

    _assert_legacy_pdf_call(scheduler._run_conversion, monkeypatch, tmp_path)


def test_main_text_only_uses_shared_extractor(monkeypatch, tmp_path):
    import app.mixins.pdf_to_word as pdf_to_word_module

    calls = []

    def fake_extractor(pdf_path, docx_path):
        calls.append((pdf_path, docx_path))
        from docx import Document

        document = Document()
        document.add_paragraph("fake text output")
        document.save(docx_path)

    monkeypatch.setattr(pdf_to_word_module, "convert_pdf_text_to_docx", fake_extractor)
    mixin = pdf_to_word_module.PdfToWordMixin.__new__(pdf_to_word_module.PdfToWordMixin)
    output = tmp_path / "output.docx"

    assert mixin.convert_pdf_to_docx_text_only("input.pdf", str(output)) is True
    assert calls[0][0] == "input.pdf"
    assert Path(calls[0][1]).suffix == ".docx"
    assert output.is_file()


def test_main_text_only_preserves_layout_fallback(monkeypatch, tmp_path):
    import app.mixins.pdf_to_word as pdf_to_word_module

    def fail_extraction(_pdf_path, _docx_path):
        raise RuntimeError("text extraction failed")

    monkeypatch.setattr(pdf_to_word_module, "convert_pdf_text_to_docx", fail_extraction)
    mixin = pdf_to_word_module.PdfToWordMixin.__new__(pdf_to_word_module.PdfToWordMixin)
    fallback = []

    def fake_fallback(_pdf_path, docx_path):
        fallback.append(docx_path)
        from docx import Document

        document = Document()
        document.add_paragraph("fallback output")
        document.save(docx_path)

    mixin._solid_fitz_fallback = fake_fallback
    output = tmp_path / "output.docx"

    assert mixin.convert_pdf_to_docx_text_only("input.pdf", str(output)) is True
    assert len(fallback) == 1
    assert output.is_file()


def test_text_only_success_replaces_existing_destination(monkeypatch, tmp_path):
    src = tmp_path / "input.pdf"
    _write_text_pdf(src)
    output = tmp_path / "input.docx"
    output.write_bytes(b"old destination")
    fallback_calls = []
    monkeypatch.setattr(
        cm_window,
        "_solid_fitz_fallback",
        lambda pdf_path, docx_path: fallback_calls.append((pdf_path, docx_path)),
    )

    cm_window._convert_pdf_to_docx(str(src), str(tmp_path), mode="text_only")

    from docx import Document

    assert output.is_file()
    assert any("Quick Convert text" in paragraph.text for paragraph in Document(output).paragraphs)
    assert fallback_calls == []
    assert not _temp_files(tmp_path)


def test_text_only_fallback_replaces_existing_destination(monkeypatch, tmp_path):
    src = tmp_path / "input.pdf"
    _write_text_pdf(src, "Fallback text")
    output = tmp_path / "input.docx"
    output.write_bytes(b"old destination")

    def fail_extraction(*args, **kwargs):
        raise RuntimeError("primary extraction failed")

    monkeypatch.setattr(cm_window, "convert_pdf_text_to_docx", fail_extraction)

    cm_window._convert_pdf_to_docx(str(src), str(tmp_path), mode="text_only")

    from docx import Document

    assert output.is_file()
    assert any("Fallback text" in paragraph.text for paragraph in Document(output).paragraphs)
    assert not _temp_files(tmp_path)


def test_text_only_cancellation_does_not_use_fallback(monkeypatch, tmp_path):
    src = tmp_path / "input.pdf"
    src.write_bytes(b"%PDF")
    output = tmp_path / "input.docx"
    output.write_bytes(b"old destination")
    fallback_calls = []

    def cancel_extraction(*args, **kwargs):
        raise cm_window._ConversionCancelled()

    monkeypatch.setattr(cm_window, "convert_pdf_text_to_docx", cancel_extraction)
    monkeypatch.setattr(
        cm_window,
        "_solid_fitz_fallback",
        lambda pdf_path, docx_path: fallback_calls.append((pdf_path, docx_path)),
    )

    with pytest.raises(cm_window._ConversionCancelled):
        cm_window._convert_pdf_to_docx(str(src), str(tmp_path), mode="text_only")

    assert fallback_calls == []
    assert output.read_bytes() == b"old destination"
    assert not _temp_files(tmp_path)


def test_text_only_total_failure_removes_partial_output(monkeypatch, tmp_path):
    src = tmp_path / "input.pdf"
    src.write_bytes(b"%PDF")

    def fail_extraction(pdf_path, docx_path, **kwargs):
        Path(docx_path).write_bytes(b"partial primary")
        raise RuntimeError("primary extraction failed")

    def fail_fallback(pdf_path, docx_path):
        Path(docx_path).write_bytes(b"partial fallback")
        raise RuntimeError("fallback failed")

    monkeypatch.setattr(cm_window, "convert_pdf_text_to_docx", fail_extraction)
    monkeypatch.setattr(cm_window, "_solid_fitz_fallback", fail_fallback)

    with pytest.raises(RuntimeError):
        cm_window._convert_pdf_to_docx(str(src), str(tmp_path), mode="text_only")

    assert not (tmp_path / "input.docx").exists()
    assert not _temp_files(tmp_path)


def test_text_only_total_failure_preserves_existing_destination(monkeypatch, tmp_path):
    src = tmp_path / "input.pdf"
    src.write_bytes(b"%PDF")
    output = tmp_path / "input.docx"
    output.write_bytes(b"old destination")

    def fail_extraction(pdf_path, docx_path, **kwargs):
        Path(docx_path).write_bytes(b"partial primary")
        raise RuntimeError("primary extraction failed")

    def fail_fallback(pdf_path, docx_path):
        Path(docx_path).write_bytes(b"partial fallback")
        raise RuntimeError("fallback failed")

    monkeypatch.setattr(cm_window, "convert_pdf_text_to_docx", fail_extraction)
    monkeypatch.setattr(cm_window, "_solid_fitz_fallback", fail_fallback)

    with pytest.raises(RuntimeError):
        cm_window._convert_pdf_to_docx(str(src), str(tmp_path), mode="text_only")

    assert output.read_bytes() == b"old destination"
    assert not _temp_files(tmp_path)
