"""Global PDF-to-Word mode propagation into Watcher and Scheduler."""

import pytest

import context_menu.window as cm_window
from tasks import scheduler, watcher


def _patch_config(monkeypatch, config):
    import config as config_module

    class FakeConfigManager:
        def load_config(self):
            return config

    monkeypatch.setattr(config_module, "ConfigManager", FakeConfigManager)


def _source(tmp_path):
    src = tmp_path / "input.pdf"
    src.write_bytes(b"%PDF")
    return src


def _run_and_capture(monkeypatch, tmp_path, runner, config):
    src = _source(tmp_path)
    out_dir = tmp_path / "out"
    seen = []
    _patch_config(monkeypatch, config)
    monkeypatch.setattr(cm_window, "_convert_pdf_to_docx", lambda *a, **k: seen.append((a, k)))

    runner("pdf_to_docx", str(src), str(out_dir))

    return src, out_dir, seen


@pytest.mark.parametrize("mode", ["with_images", "text_only"])
def test_watcher_uses_configured_mode(monkeypatch, tmp_path, mode):
    _src, _out_dir, seen = _run_and_capture(
        monkeypatch,
        tmp_path,
        watcher._run_conversion,
        {"pdf_to_word_mode": mode},
    )

    assert seen == [((str(_src), str(_out_dir)), {"mode": mode})]


@pytest.mark.parametrize(
    "config",
    [
        {},
        {"pdf_to_word_mode": None},
        {"pdf_to_word_mode": ""},
        {"pdf_to_word_mode": "unsupported"},
    ],
)
def test_watcher_invalid_or_missing_mode_defaults_to_with_images(monkeypatch, tmp_path, config):
    _src, _out_dir, seen = _run_and_capture(
        monkeypatch,
        tmp_path,
        watcher._run_conversion,
        config,
    )

    assert seen == [((str(_src), str(_out_dir)), {"mode": "with_images"})]


def test_watcher_reads_configuration_for_each_conversion(monkeypatch, tmp_path):
    import config as config_module

    class ChangingConfigManager:
        calls = 0

        def load_config(self):
            type(self).calls += 1
            return {"pdf_to_word_mode": "text_only" if self.calls == 1 else "with_images"}

    monkeypatch.setattr(config_module, "ConfigManager", ChangingConfigManager)
    src = _source(tmp_path)
    out_dir = tmp_path / "out"
    seen = []
    monkeypatch.setattr(cm_window, "_convert_pdf_to_docx", lambda *a, **k: seen.append((a, k)))

    watcher._run_conversion("pdf_to_docx", str(src), str(out_dir))
    watcher._run_conversion("pdf_to_docx", str(src), str(out_dir))

    assert [call[1]["mode"] for call in seen] == ["text_only", "with_images"]


def test_watcher_configuration_failure_defaults_to_with_images(monkeypatch, tmp_path):
    import config as config_module

    class BrokenConfigManager:
        def load_config(self):
            raise RuntimeError("config unavailable")

    monkeypatch.setattr(config_module, "ConfigManager", BrokenConfigManager)
    src = _source(tmp_path)
    out_dir = tmp_path / "out"
    seen = []
    monkeypatch.setattr(cm_window, "_convert_pdf_to_docx", lambda *a, **k: seen.append((a, k)))

    watcher._run_conversion("pdf_to_docx", str(src), str(out_dir))

    assert seen == [((str(src), str(out_dir)), {"mode": "with_images"})]


@pytest.mark.parametrize("mode", ["text_only", "with_images"])
def test_scheduler_inherits_watcher_mode_behavior(monkeypatch, tmp_path, mode):
    _src, _out_dir, seen = _run_and_capture(
        monkeypatch,
        tmp_path,
        scheduler._run_conversion,
        {"pdf_to_word_mode": mode},
    )

    assert seen == [((str(_src), str(_out_dir)), {"mode": mode})]


def test_scheduler_defaults_to_with_images(monkeypatch, tmp_path):
    _src, _out_dir, seen = _run_and_capture(
        monkeypatch,
        tmp_path,
        scheduler._run_conversion,
        {},
    )

    assert seen == [((str(_src), str(_out_dir)), {"mode": "with_images"})]


def test_watcher_text_only_mode_reaches_real_conversion(monkeypatch, tmp_path):
    import fitz
    from docx import Document

    src = tmp_path / "input.pdf"
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Automation text")
    pdf.save(str(src))
    pdf.close()
    out_dir = tmp_path / "out"
    _patch_config(monkeypatch, {"pdf_to_word_mode": "text_only"})

    watcher._run_conversion("pdf_to_docx", str(src), str(out_dir))

    output = out_dir / "input.docx"
    assert output.is_file()
    assert any("Automation text" in paragraph.text for paragraph in Document(output).paragraphs)
