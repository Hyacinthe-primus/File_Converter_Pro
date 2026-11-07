"""Merge ordering regressions across Main, Quick Convert, and automation."""

from pathlib import Path

import fitz
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QListWidgetItem, QMessageBox, QWidget

import context_menu.window as cm_window
import dialogs.merge_order_dialog as merge_dialog_module
from app.mixins.pdf_operations import PdfOperationsMixin
from tasks import scheduler, watcher
from templates import semantic_keys as sk


def _make_pdf(path: Path, label: str) -> Path:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), label)
    document.save(str(path))
    document.close()
    return path


def _page_texts(path: str | Path) -> list[str]:
    with fitz.open(str(path)) as document:
        return [page.get_text().strip() for page in document]


def _merge_sources(tmp_path: Path) -> list[Path]:
    return [
        _make_pdf(tmp_path / "file10.pdf", "10"),
        _make_pdf(tmp_path / "file2.pdf", "2"),
        _make_pdf(tmp_path / "file1.pdf", "1"),
    ]


class _NoSelection:
    @staticmethod
    def selectedItems():
        return []


class _MainMerger(PdfOperationsMixin, QWidget):
    pass


class _Achievements:
    def record_conversion(self, *_args, **_kwargs):
        pass

    def record_pdf_merge(self, *_args, **_kwargs):
        pass


class _Database:
    def add_conversion_record(self, **_kwargs):
        pass


class _Notifier:
    def send(self, *_args, **_kwargs):
        pass


def _main_merger(tmp_path: Path, files: list[Path]):
    obj = _MainMerger()
    obj.files_list_widget = _NoSelection()
    obj.files_list = [str(path) for path in files]
    obj.current_language = "en"
    obj.active_templates = {}
    obj.config = {
        "enable_system_notifications": False,
        "backup_before_conversion": False,
    }
    obj.translate_text = lambda key: key
    obj.get_output_directory = lambda _name: str(tmp_path / "merged.pdf")
    obj.show_progress = lambda *_args, **_kwargs: None
    obj.achievement_system = _Achievements()
    obj.db_manager = _Database()
    obj.system_notifier = _Notifier()
    obj.record_config_usage = lambda *_args, **_kwargs: None
    return obj


@pytest.mark.parametrize(
    ("order_key", "expected"),
    [
        (sk.ORDER_ALPHA_AZ, ["1", "10", "2"]),
        (sk.ORDER_NUM_ASC, ["1", "2", "10"]),
        (sk.ORDER_CURRENT, ["10", "2", "1"]),
    ],
)
def test_main_merges_in_dialog_order(qapp, monkeypatch, tmp_path, order_key, expected):
    sources = _merge_sources(tmp_path)
    obj = _main_merger(tmp_path, sources)

    def auto_accept(self):
        self._radio_map[order_key].setChecked(True)
        return QDialog.Accepted

    monkeypatch.setattr(merge_dialog_module.MergeOrderDialog, "exec", auto_accept)
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: None))

    obj.merge_pdfs()

    assert _page_texts(tmp_path / "merged.pdf") == expected


def test_main_merges_in_explicit_manual_order(qapp, monkeypatch, tmp_path):
    sources = _merge_sources(tmp_path)
    manual = [sources[1], sources[2], sources[0]]
    obj = _main_merger(tmp_path, sources)

    def auto_accept(self):
        self._radio_map[sk.ORDER_MANUAL].setChecked(True)
        self._manual_list.clear()
        for path in manual:
            item = QListWidgetItem(Path(path).name)
            item.setData(Qt.UserRole, str(path))
            self._manual_list.addItem(item)
        return QDialog.Accepted

    monkeypatch.setattr(merge_dialog_module.MergeOrderDialog, "exec", auto_accept)
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: None))

    obj.merge_pdfs()

    assert _page_texts(tmp_path / "merged.pdf") == ["2", "1", "10"]


@pytest.mark.parametrize(
    ("conversion_type", "expected"),
    [
        ("merge_pdf_none", ["1", "10", "2"]),
        ("merge_pdf_num_asc", ["1", "2", "10"]),
    ],
)
def test_quick_convert_merges_in_configured_order(
    monkeypatch, tmp_path, conversion_type, expected
):
    sources = _merge_sources(tmp_path)
    monkeypatch.setattr(
        cm_window,
        "_load_quick_config",
        lambda: {"backup_before_conversion": False},
    )
    thread = cm_window.ConversionThread(
        [str(path) for path in reversed(sources)], conversion_type
    )

    thread.run()

    outputs = list(tmp_path.glob("merged_*.pdf"))
    assert len(outputs) == 1
    assert _page_texts(outputs[0]) == expected


def test_quick_convert_image_merge_uses_stable_order(monkeypatch, tmp_path):
    one = str(tmp_path / "one.png")
    two = str(tmp_path / "two.png")
    for path in (one, two):
        Path(path).write_bytes(b"image")
    seen = []
    monkeypatch.setattr(
        cm_window,
        "_load_quick_config",
        lambda: {"backup_before_conversion": False},
    )
    monkeypatch.setattr(
        cm_window,
        "_merge_images_to_pdf",
        lambda files, *_args, **_kwargs: seen.append(list(files)),
    )

    cm_window.ConversionThread([two, one], "images_to_pdf_merged").run()

    assert seen == [[one, two]]


def test_automation_image_merge_uses_stable_order(monkeypatch, tmp_path):
    one = str(tmp_path / "one.png")
    two = str(tmp_path / "two.png")
    for path in (one, two):
        Path(path).write_bytes(b"image")
    seen = []
    monkeypatch.setattr(
        watcher,
        "_load_runtime_config",
        lambda: {"backup_before_conversion": False},
    )
    monkeypatch.setattr(
        "context_menu.conversion_helpers._merge_images_to_pdf",
        lambda files, *_args, **_kwargs: seen.append(list(files)),
    )

    watcher._run_merge("images_to_pdf_merged", [two, one], str(tmp_path / "out"))

    assert seen == [[one, two]]


def test_quick_convert_none_order_is_deterministic(monkeypatch, tmp_path):
    sources = _merge_sources(tmp_path)
    monkeypatch.setattr(
        cm_window,
        "_load_quick_config",
        lambda: {"backup_before_conversion": False},
    )
    paths = [str(path) for path in sources]

    cm_window.ConversionThread(list(reversed(paths)), "merge_pdf_none").run()
    cm_window.ConversionThread([paths[1], paths[2], paths[0]], "merge_pdf_none").run()

    outputs = sorted(tmp_path.glob("merged_*.pdf"))
    assert len(outputs) == 2
    assert [_page_texts(path) for path in outputs] == [
        ["1", "10", "2"],
        ["1", "10", "2"],
    ]


@pytest.mark.parametrize("module", [watcher, scheduler])
@pytest.mark.parametrize(
    ("conversion_type", "expected"),
    [
        ("merge_pdf_none", ["1", "10", "2"]),
        ("merge_pdf_num_asc", ["1", "2", "10"]),
    ],
)
def test_automation_merges_in_configured_order(
    monkeypatch, tmp_path, module, conversion_type, expected
):
    sources = _merge_sources(tmp_path)
    out_dir = tmp_path / "out"
    monkeypatch.setattr(
        watcher,
        "_load_runtime_config",
        lambda: {"backup_before_conversion": False},
    )

    output = module._run_merge(
        conversion_type,
        [str(path) for path in reversed(sources)],
        str(out_dir),
    )

    assert output is not None
    assert _page_texts(output) == expected
