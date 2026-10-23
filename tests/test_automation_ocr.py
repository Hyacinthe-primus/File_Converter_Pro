"""Automation OCR option: TOML plumbing, watcher/scheduler routing and fallbacks."""

import os
import sys
import types

import fitz
import pytest

import tasks.ocr_helpers as ocr_helpers
from tasks import scheduler, watcher


def _pngs(tmp_path, count=2):
    from PIL import Image

    paths = []
    for i in range(count):
        p = tmp_path / f"img{i}.png"
        Image.new("RGB", (32, 32), "white").save(p)
        paths.append(str(p))
    return paths


def _pdf_with(path, texts):
    doc = fitz.open()
    for has_text in texts:
        page = doc.new_page()
        if has_text:
            page.insert_text((72, 72), "recognised text")
    doc.save(path)
    doc.close()


def _install_scanlayer(monkeypatch, words=1, merge_raises=False, convert_raises=False):
    calls = {"convert": [], "merge": [], "configure": []}

    class _Result:
        def __init__(self, w):
            self.words_count = w

    def convert(input_path=None, output_path=None, orientation=None, force=False):
        calls["convert"].append(
            {"input": input_path, "output": output_path, "orientation": orientation, "force": force}
        )
        if convert_raises:
            raise RuntimeError("unreadable image")
        _pdf_with(output_path, [bool(words)])
        return _Result(words)

    def convert_merge(paths, output_path, **kwargs):
        calls["merge"].append({"paths": list(paths), **kwargs})
        if merge_raises:
            with open(output_path, "wb") as fh:
                fh.write(b"partial")
            raise RuntimeError("batch cannot be read")
        _pdf_with(output_path, [True] * len(paths))

    def configure(**kwargs):
        calls["configure"].append(kwargs)

    monkeypatch.setitem(
        sys.modules,
        "scanlayer",
        types.SimpleNamespace(convert=convert, convert_merge=convert_merge, configure=configure),
    )
    monkeypatch.setattr("external_binaries.resolve_binary", lambda name: None)
    return calls


class TestTomlFlag:
    def test_watch_folder_ocr_flag(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            watcher,
            "_load_all_toml",
            lambda: {
                "watch_folders": {
                    "plain": {"path": str(tmp_path), "rules": {"png": "pdf"}},
                    "scans": {"path": str(tmp_path), "rules": {"png": "pdf"}, "ocr": True},
                }
            },
        )
        enabled = {c["name"]: c["ocr"] for c in watcher.get_watch_folder_configs()}
        assert enabled == {"plain": False, "scans": True}

        all_configs = {c["name"]: c["ocr"] for c in watcher.get_all_watch_folder_configs()}
        assert all_configs == {"plain": False, "scans": True}

    def test_scheduled_task_ocr_flag(self, monkeypatch, tmp_path):
        task = {"path": str(tmp_path), "rules": {"png": "pdf"}, "trigger": {"type": "interval", "hours": 1}}
        monkeypatch.setattr(
            scheduler,
            "_load_all_toml",
            lambda: {"scheduled_tasks": {"plain": dict(task), "scans": dict(task, ocr=True)}},
        )
        monkeypatch.setattr(scheduler, "_find_toml_for_task", lambda name: None)

        enabled = {c["name"]: c["ocr"] for c in scheduler.get_scheduled_task_configs()}
        assert enabled == {"plain": False, "scans": True}

        all_configs = {c["name"]: c["ocr"] for c in scheduler.get_all_scheduled_task_configs()}
        assert all_configs == {"plain": False, "scans": True}

    def test_example_toml_documents_ocr(self):
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src",
            "automation",
            "example_automation.toml",
        )
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        assert "ocr" in content


class TestOrientation:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("auto", None),
            ("", None),
            ("junk", None),
            ("none", "none"),
            ("90", 90.0),
            ("-12.5", -12.5),
            (False, "none"),
            (True, None),
        ],
    )
    def test_explicit_values(self, raw, expected):
        assert ocr_helpers.resolve_orientation(raw) == expected

    def test_reads_config_when_raw_is_none(self, monkeypatch):
        class _ConfigManager:
            def load_config(self):
                return {"ocr_orientation": "45"}

        monkeypatch.setattr("config.ConfigManager", _ConfigManager)
        assert ocr_helpers.resolve_orientation() == 45.0

    def test_config_read_failure_is_auto(self, monkeypatch):
        class _ConfigManager:
            def load_config(self):
                raise RuntimeError("no config")

        monkeypatch.setattr("config.ConfigManager", _ConfigManager)
        assert ocr_helpers.resolve_orientation() is None


class TestConfigureScanlayer:
    def test_tesseract_is_configured(self, monkeypatch):
        calls = _install_scanlayer(monkeypatch)
        monkeypatch.setattr("external_binaries.resolve_binary", lambda name: r"C:\tess\tesseract.exe")
        monkeypatch.setattr(ocr_helpers, "resolve_orientation", lambda raw=None: 42.0)

        assert ocr_helpers.configure_scanlayer() == 42.0
        assert calls["configure"] == [{"tesseract_cmd": r"C:\tess\tesseract.exe"}]

    def test_missing_tesseract_skips_configure(self, monkeypatch):
        calls = _install_scanlayer(monkeypatch)
        monkeypatch.setattr(ocr_helpers, "resolve_orientation", lambda raw=None: None)

        assert ocr_helpers.configure_scanlayer() is None
        assert calls["configure"] == []


class TestImageHelpers:
    def test_ocr_success_returns_true(self, monkeypatch, tmp_path):
        calls = _install_scanlayer(monkeypatch, words=3)
        src = _pngs(tmp_path, 1)[0]
        out = str(tmp_path / "o.pdf")

        assert ocr_helpers.image_to_pdf(src, out, 90.0) is True
        assert calls["convert"][0]["orientation"] == 90.0
        assert calls["convert"][0]["force"] is True
        assert os.path.isfile(out)

    def test_failed_ocr_falls_back_to_plain_embed(self, monkeypatch, tmp_path):
        _install_scanlayer(monkeypatch, convert_raises=True)
        src = _pngs(tmp_path, 1)[0]
        out = str(tmp_path / "o.pdf")

        assert ocr_helpers.image_to_pdf(src, out, None) is False
        with fitz.open(out) as doc:
            assert doc.page_count == 1
            assert doc[0].get_text().strip() == ""

    def test_no_text_falls_back_to_plain_embed(self, monkeypatch, tmp_path):
        _install_scanlayer(monkeypatch, words=0)
        src = _pngs(tmp_path, 1)[0]
        out = str(tmp_path / "o.pdf")

        assert ocr_helpers.image_to_pdf(src, out, None) is False
        with fitz.open(out) as doc:
            assert doc.page_count == 1


class TestMergeHelpers:
    def test_parallel_merge_uses_workers(self, monkeypatch, tmp_path):
        calls = _install_scanlayer(monkeypatch)
        images = _pngs(tmp_path, 3)
        out = str(tmp_path / "merged.pdf")

        assert ocr_helpers.merge_images_with_ocr(images, out, None) is True
        assert calls["merge"][0]["workers"] == ocr_helpers.OCR_MERGE_WORKERS == 4
        assert calls["merge"][0]["force"] is True
        assert calls["merge"][0]["paths"] == images

    def test_parallel_failure_falls_back_sequentially(self, monkeypatch, tmp_path):
        calls = _install_scanlayer(monkeypatch, merge_raises=True)
        images = _pngs(tmp_path, 2)
        out = str(tmp_path / "merged.pdf")

        assert ocr_helpers.merge_images_with_ocr(images, out, None) is True
        assert len(calls["convert"]) == 2
        with fitz.open(out) as doc:
            assert doc.page_count == 2


class TestRunConversionRouting:
    def test_ocr_flag_uses_ocr_path(self, monkeypatch, tmp_path):
        calls = _install_scanlayer(monkeypatch)
        monkeypatch.setattr(ocr_helpers, "configure_scanlayer", lambda: 90.0)
        src = _pngs(tmp_path, 1)[0]
        out_dir = tmp_path / "out"

        watcher._run_conversion("image_to_pdf", src, str(out_dir), ocr=True)

        assert calls["convert"] and calls["convert"][0]["orientation"] == 90.0
        assert (out_dir / "img0.pdf").is_file()

    def test_without_ocr_uses_context_menu_path(self, monkeypatch, tmp_path):
        import context_menu.window as cm_window

        seen = []
        monkeypatch.setattr(cm_window, "_convert_image_to_pdf", lambda src, out: seen.append(src))
        src = _pngs(tmp_path, 1)[0]

        watcher._run_conversion("image_to_pdf", src, str(tmp_path / "out"), ocr=False)

        assert seen == [src]


class TestRunMergeRouting:
    def test_merge_with_ocr(self, monkeypatch, tmp_path):
        calls = _install_scanlayer(monkeypatch)
        monkeypatch.setattr(ocr_helpers, "configure_scanlayer", lambda: None)
        images = _pngs(tmp_path, 2)
        out_dir = tmp_path / "out"

        watcher._run_merge("images_to_pdf_merged", images, str(out_dir), ocr=True)

        merged = [f for f in os.listdir(out_dir) if f.startswith("merged_images_") and f.endswith(".pdf")]
        assert len(merged) == 1
        assert calls["merge"]

    def test_merge_without_ocr_uses_context_menu_path(self, monkeypatch, tmp_path):
        import context_menu.window as cm_window

        seen = []
        monkeypatch.setattr(cm_window, "_merge_images_to_pdf", lambda files, out: seen.append(list(files)))
        images = _pngs(tmp_path, 2)

        watcher._run_merge("images_to_pdf_merged", images, str(tmp_path / "out"), ocr=False)

        assert seen == [images]


class TestPlumbing:
    def test_handler_reads_ocr_flag(self, tmp_path):
        handler = watcher._FolderEventHandler(
            {"path": str(tmp_path), "output_dir": "", "rules": {}, "recursive": False, "ocr": True}
        )
        assert handler._ocr is True

    def test_process_existing_passes_ocr(self, monkeypatch, tmp_path):
        src_dir = tmp_path / "in"
        src_dir.mkdir()
        (src_dir / "a.png").write_bytes(b"\x89PNG")
        seen = []
        monkeypatch.setattr(watcher, "_run_conversion", lambda *a, **k: seen.append((a, k)))

        watcher.WatcherManager()._process_existing(
            {
                "name": "t",
                "path": str(src_dir),
                "output_dir": str(tmp_path / "out"),
                "rules": {"png": [{"kind": "convert", "fmt": "pdf"}]},
                "recursive": False,
                "ocr": True,
            }
        )

        assert seen and seen[0][1]["ocr"] is True

    def test_scheduler_passes_ocr(self, monkeypatch, tmp_path):
        src_dir = tmp_path / "in"
        src_dir.mkdir()
        (src_dir / "a.png").write_bytes(b"\x89PNG")
        seen = []
        monkeypatch.setattr(scheduler, "_run_conversion", lambda *a, **k: seen.append((a, k)))

        scheduler._run_task(
            {
                "name": "t",
                "path": str(src_dir),
                "output_dir": str(tmp_path / "out"),
                "rules": {"png": [{"kind": "convert", "fmt": "pdf"}]},
                "recursive": False,
                "trigger": {"type": "cron"},
                "toml_file": None,
                "ocr": True,
            }
        )

        assert seen and seen[0][1]["ocr"] is True


class TestConversionMapResolvable:
    def test_every_convert_entry_is_reachable_by_rules(self):
        from context_menu.formats import CONVERSION_MAP, MERGE_DISPATCH

        unresolvable = []
        for ext, entries in CONVERSION_MAP.items():
            for entry in entries:
                if entry in MERGE_DISPATCH or entry == "images_to_pdf_merged":
                    continue
                fmt = entry.rsplit("_", 1)[-1]
                if watcher._build_conversion_type(ext, fmt) is None:
                    unresolvable.append((ext, entry))

        assert unresolvable == []
