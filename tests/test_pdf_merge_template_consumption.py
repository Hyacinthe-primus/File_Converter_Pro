"""PDF merge template order consumption tests."""

from pathlib import Path

import fitz
import pypdf
from PySide6.QtWidgets import QDialog, QMessageBox

from app.mixins.pdf_operations import PdfOperationsMixin
from dialogs.merge_order_dialog import MergeOrderDialog
from templates import semantic_keys as sk


def _files(tmp_path):
    first = tmp_path / "b.pdf"
    second = tmp_path / "a.pdf"
    first.write_bytes(b"%PDF-1.4\n")
    second.write_bytes(b"%PDF-1.4\n")
    return first, second


class _FakeWidget:
    def selectedItems(self):
        return []


class _FakeAchievements:
    def record_conversion(self, *args, **kwargs):
        pass

    def record_pdf_merge(self, *args, **kwargs):
        pass


class _FakeDb:
    def add_conversion_record(self, *args, **kwargs):
        pass


class _FakeNotifier:
    def send(self, *args, **kwargs):
        pass


class _FakeWriter:
    instances = []

    def __init__(self):
        self.files = []
        self.__class__.instances.append(self)

    def append(self, path):
        self.files.append(path)

    def write(self, path):
        Path(path).write_bytes(b"%PDF-1.4\n")

    def close(self):
        pass


class _FakeDoc:
    def __len__(self):
        return 2

    def close(self):
        pass


def _fake_self(tmp_path, active_templates):
    obj = PdfOperationsMixin.__new__(PdfOperationsMixin)
    first, second = _files(tmp_path)
    obj.files_list_widget = _FakeWidget()
    obj.files_list = [str(first), str(second)]
    obj.current_language = "en"
    obj.active_templates = active_templates
    obj.translate_text = lambda key: key
    obj.get_output_directory = lambda _name: str(tmp_path / "merged.pdf")
    obj.show_progress = lambda *args, **kwargs: None
    obj.achievement_system = _FakeAchievements()
    obj.db_manager = _FakeDb()
    obj.system_notifier = _FakeNotifier()
    obj.record_config_usage = lambda *args: None
    return obj, first, second


def test_active_template_preselects_and_manual_choice_wins(qapp, tmp_path):
    first, second = _files(tmp_path)
    dialog = MergeOrderDialog(
        [str(first), str(second)],
        ".pdf",
        language="en",
        pre_select_key=sk.ORDER_ALPHA_AZ,
    )
    try:
        assert dialog.get_order_key() == sk.ORDER_ALPHA_AZ

        dialog._radio_map[sk.ORDER_ALPHA_ZA].setChecked(True)
        assert dialog.get_order_key() == sk.ORDER_ALPHA_ZA
        assert dialog.get_ordered_files() == [str(first), str(second)]
    finally:
        dialog.deleteLater()
        qapp.processEvents()


def test_no_template_keeps_default_order(qapp, tmp_path):
    first, second = _files(tmp_path)
    dialog = MergeOrderDialog([str(first), str(second)], ".pdf", language="en")
    try:
        assert dialog.get_order_key() == sk.ORDER_CURRENT
    finally:
        dialog.deleteLater()
        qapp.processEvents()


def test_merge_order_choice_cannot_be_unchecked(qapp, tmp_path):
    first, second = _files(tmp_path)
    dialog = MergeOrderDialog([str(first), str(second)], ".pdf", language="en")
    try:
        dialog._radio_map[sk.ORDER_CURRENT].click()
        assert dialog.get_order_key() == sk.ORDER_CURRENT

        dialog._radio_map[sk.ORDER_ALPHA_AZ].click()
        assert dialog.get_order_key() == sk.ORDER_ALPHA_AZ

        dialog._radio_map[sk.ORDER_ALPHA_AZ].click()
        assert dialog.get_order_key() == sk.ORDER_ALPHA_AZ
    finally:
        dialog.deleteLater()
        qapp.processEvents()


def test_invalid_template_order_falls_back_to_default(qapp, tmp_path):
    first, second = _files(tmp_path)
    dialog = MergeOrderDialog(
        [str(first), str(second)],
        ".pdf",
        language="en",
        pre_select_key="not_a_real_order",
    )
    try:
        assert dialog.get_order_key() == sk.ORDER_CURRENT
    finally:
        dialog.deleteLater()
        qapp.processEvents()


def test_merge_receives_template_preselect_and_uses_dialog_order(monkeypatch, tmp_path):
    obj, first, second = _fake_self(
        tmp_path,
        {sk.PDF_MERGE: {"merge_order_key": sk.ORDER_ALPHA_AZ}},
    )
    captured = {}
    writer_instances = []

    class FakeDialog:
        def __init__(self, files, file_type, parent=None, language="fr", pre_select_key=None):
            captured["pre_select_key"] = pre_select_key
            self.files = list(files)

        def exec(self):
            return QDialog.Accepted

        def get_ordered_files(self):
            return [self.files[1], self.files[0]]

        def get_order_key(self):
            return sk.ORDER_ALPHA_ZA

    class FakeWriter(_FakeWriter):
        def __init__(self):
            super().__init__()
            writer_instances.append(self)

    monkeypatch.setattr("dialogs.merge_order_dialog.MergeOrderDialog", FakeDialog)
    monkeypatch.setattr(pypdf, "PdfWriter", FakeWriter)
    monkeypatch.setattr(fitz, "open", lambda _path: _FakeDoc())
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: None))
    monkeypatch.setattr(QMessageBox, "critical", staticmethod(lambda *a, **k: None))
    obj.record_config_usage = lambda *args: captured.setdefault("recorded", args)

    obj.merge_pdfs()

    assert captured["pre_select_key"] == sk.ORDER_ALPHA_AZ
    assert captured["recorded"] == (sk.PDF_MERGE, {"merge_order": sk.ORDER_ALPHA_ZA})
    assert writer_instances[0].files == [str(second), str(first)]


def test_no_active_template_passes_no_preselect(monkeypatch, tmp_path):
    obj, _first, _second = _fake_self(tmp_path, {})
    captured = {}

    class FakeDialog:
        def __init__(self, files, file_type, parent=None, language="fr", pre_select_key=None):
            captured["pre_select_key"] = pre_select_key

        def exec(self):
            return QDialog.Rejected

    monkeypatch.setattr("dialogs.merge_order_dialog.MergeOrderDialog", FakeDialog)
    obj.merge_pdfs()

    assert captured["pre_select_key"] is None
