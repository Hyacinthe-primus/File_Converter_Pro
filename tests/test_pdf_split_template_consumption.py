"""PDF split template prefill and splitting behavior tests."""

from pathlib import Path

import fitz
import pytest
from PySide6.QtWidgets import QDialog

import dialogs
from app.mixins.pdf_operations import PdfOperationsMixin
from dialogs.split_dialog import SplitDialog
from templates import semantic_keys as sk


def _pdf(tmp_path):
    path = tmp_path / "source.pdf"
    path.write_bytes(b"%PDF-1.4\n")
    return path


class _FakeWidget:
    def selectedItems(self):
        return []


class _FakeAchievements:
    def record_pdf_split(self, *args, **kwargs):
        pass


class _FakeNotifier:
    def send(self, *args, **kwargs):
        pass


class _FakeDoc:
    instances = []

    def __init__(self, pages=5):
        self.pages = pages
        self.inserts = []
        self.__class__.instances.append(self)

    def __len__(self):
        return self.pages

    def insert_pdf(self, document, from_page, to_page):
        self.inserts.append((from_page, to_page))

    def save(self, path):
        Path(path).write_bytes(b"%PDF-1.4\n")

    def close(self):
        pass


class _FakeMethod:
    def __init__(self, index):
        self.index = index

    def currentIndex(self):
        return self.index


class _FakeSpin:
    def __init__(self, value):
        self._value = value

    def value(self):
        return self._value


class _FakeDialog:
    def __init__(self, method=0, interval=3, start=2, end=4, accepted=True):
        self.split_method = _FakeMethod(method)
        self.page_interval = _FakeSpin(interval)
        self.start_page = _FakeSpin(start)
        self.end_page = _FakeSpin(end)
        self.accepted = accepted

    def exec(self):
        return QDialog.Accepted if self.accepted else QDialog.Rejected


def _fake_self(tmp_path):
    obj = PdfOperationsMixin.__new__(PdfOperationsMixin)
    obj.current_language = "en"
    obj.config = {"enable_system_notifications": False}
    obj.translate_text = lambda key: key
    obj.show_progress = lambda *args, **kwargs: None
    obj.achievement_system = _FakeAchievements()
    obj.system_notifier = _FakeNotifier()
    obj.record_config_usage = lambda *args: None
    return obj


def _patch_fitz(monkeypatch):
    _FakeDoc.instances = []
    monkeypatch.setattr(fitz, "open", lambda *args: _FakeDoc())


def test_split_dialog_prefills_method_and_page_count(qapp):
    dialog = SplitDialog(10, language="en", pre_select_key=sk.SPLIT_BY_PAGES, pages_per_file=3)
    try:
        assert dialog.split_method.currentData() == sk.SPLIT_BY_PAGES
        assert dialog.page_interval.value() == 3
    finally:
        dialog.deleteLater()
        qapp.processEvents()


def test_split_dialog_defaults_without_template(qapp):
    dialog = SplitDialog(10, language="en")
    try:
        assert dialog.split_method.currentData() == sk.SPLIT_BY_PAGES
        assert dialog.page_interval.value() == 1
    finally:
        dialog.deleteLater()
        qapp.processEvents()


@pytest.mark.parametrize("pages_per_file", [0, -3, 99])
def test_split_dialog_invalid_method_and_page_count_fall_back(qapp, pages_per_file):
    dialog = SplitDialog(
        10,
        language="en",
        pre_select_key="not_a_split_method",
        pages_per_file=pages_per_file,
    )
    try:
        assert dialog.split_method.currentData() == sk.SPLIT_BY_PAGES
        assert dialog.page_interval.value() == 1
    finally:
        dialog.deleteLater()
        qapp.processEvents()


def test_split_dialog_manual_choices_override_template(qapp):
    dialog = SplitDialog(10, language="en", pre_select_key=sk.SPLIT_BY_PAGES, pages_per_file=3)
    try:
        dialog.split_method.setCurrentIndex(2)
        dialog.page_interval.setValue(5)
        assert dialog.split_method.currentData() == sk.SPLIT_PAGE_RANGE
        assert dialog.page_interval.value() == 5
    finally:
        dialog.deleteLater()
        qapp.processEvents()


def test_split_pdf_file_receives_template_values_and_uses_interval(monkeypatch, tmp_path):
    obj = _fake_self(tmp_path)
    obj.active_templates = {sk.PDF_SPLIT: {"split_method_key": sk.SPLIT_BY_PAGES, "pages_per_file": 3}}
    source = _pdf(tmp_path)
    captured = {}
    _patch_fitz(monkeypatch)

    class FakeSplitDialog:
        def __init__(self, total_pages, parent=None, language="fr", pre_select_key=None, pages_per_file=None):
            captured["pre_select_key"] = pre_select_key
            captured["pages_per_file"] = pages_per_file

        def exec(self):
            return QDialog.Accepted

        @property
        def split_method(self):
            return _FakeMethod(0)

        @property
        def page_interval(self):
            return _FakeSpin(3)

    monkeypatch.setattr(dialogs, "SplitDialog", FakeSplitDialog)

    obj.split_pdf_file(str(source), output_dir=str(tmp_path), silent=True)

    assert captured == {"pre_select_key": sk.SPLIT_BY_PAGES, "pages_per_file": 3}
    assert [doc.inserts for doc in _FakeDoc.instances[2:]] == [[(0, 2)], [(3, 4)]]


def test_split_pdf_file_no_template_keeps_defaults(monkeypatch, tmp_path):
    obj = _fake_self(tmp_path)
    obj.active_templates = {}
    source = _pdf(tmp_path)
    captured = {}
    _patch_fitz(monkeypatch)

    class FakeSplitDialog:
        def __init__(self, total_pages, parent=None, language="fr", pre_select_key=None, pages_per_file=None):
            captured["pre_select_key"] = pre_select_key
            captured["pages_per_file"] = pages_per_file

        def exec(self):
            return QDialog.Rejected

    monkeypatch.setattr(dialogs, "SplitDialog", FakeSplitDialog)
    obj.split_pdf_file(str(source), output_dir=str(tmp_path), silent=True)

    assert captured == {"pre_select_key": None, "pages_per_file": None}


def test_split_pdf_file_page_range_remains_unchanged(monkeypatch, tmp_path):
    obj = _fake_self(tmp_path)
    source = _pdf(tmp_path)
    _patch_fitz(monkeypatch)
    dialog = _FakeDialog(method=2, start=2, end=4)

    obj.split_pdf_file(str(source), output_dir=str(tmp_path), dialog=dialog, silent=True)

    assert _FakeDoc.instances[-1].inserts == [(1, 3)]


def test_split_pdf_cancel_stops_remaining_files(monkeypatch, tmp_path):
    obj = _fake_self(tmp_path)
    obj.files_list_widget = _FakeWidget()
    first = _pdf(tmp_path)
    second = tmp_path / "second.pdf"
    second.write_bytes(b"%PDF-1.4\n")
    obj.files_list = [str(first), str(second)]
    _patch_fitz(monkeypatch)
    created = []

    class CancelSplitDialog:
        def __init__(self, total_pages, parent=None, language="fr", **kwargs):
            created.append(total_pages)

        def exec(self):
            return QDialog.Rejected

    monkeypatch.setattr(dialogs, "SplitDialog", CancelSplitDialog)

    obj.split_pdf()

    assert created == [5]
