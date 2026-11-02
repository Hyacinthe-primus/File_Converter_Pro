"""Word merge template order consumption tests."""

from pathlib import Path

import docx
import docxcompose.composer
from PySide6.QtWidgets import QDialog, QMessageBox

from app.mixins.pdf_operations import PdfOperationsMixin
from dialogs.merge_order_dialog import MergeOrderDialog
from templates import semantic_keys as sk


def _files(tmp_path):
    first = tmp_path / "b.docx"
    second = tmp_path / "a.docx"
    first.write_bytes(b"docx")
    second.write_bytes(b"docx")
    return first, second


class _FakeWidget:
    def selectedItems(self):
        return []


class _FakeAchievements:
    def record_conversion(self, *args, **kwargs):
        pass


class _FakeDb:
    def add_conversion_record(self, *args, **kwargs):
        pass


class _FakeNotifier:
    def send(self, *args, **kwargs):
        pass


def _fake_self(tmp_path, active_templates):
    obj = PdfOperationsMixin.__new__(PdfOperationsMixin)
    first, second = _files(tmp_path)
    obj.files_list_widget = _FakeWidget()
    obj.files_list = [str(first), str(second)]
    obj.current_language = "en"
    obj.active_templates = active_templates
    obj.config = {"enable_system_notifications": False}
    obj.translate_text = lambda key: key
    obj.get_output_directory = lambda _name: str(tmp_path / "merged.docx")
    obj.show_progress = lambda *args, **kwargs: None
    obj.achievement_system = _FakeAchievements()
    obj.db_manager = _FakeDb()
    obj.system_notifier = _FakeNotifier()
    obj.record_config_usage = lambda *args: None
    return obj, first, second


def test_word_merge_dialog_preselects_and_manual_choice_wins(qapp, tmp_path):
    first, second = _files(tmp_path)
    dialog = MergeOrderDialog(
        [str(first), str(second)],
        ".docx",
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


def test_word_merge_no_template_keeps_default(qapp, tmp_path):
    first, second = _files(tmp_path)
    dialog = MergeOrderDialog([str(first), str(second)], ".docx", language="en")
    try:
        assert dialog.get_order_key() == sk.ORDER_CURRENT
    finally:
        dialog.deleteLater()
        qapp.processEvents()


def test_word_merge_invalid_template_order_falls_back(qapp, tmp_path):
    first, second = _files(tmp_path)
    dialog = MergeOrderDialog(
        [str(first), str(second)],
        ".docx",
        language="en",
        pre_select_key="not_a_real_order",
    )
    try:
        assert dialog.get_order_key() == sk.ORDER_CURRENT
    finally:
        dialog.deleteLater()
        qapp.processEvents()


def test_word_merge_receives_preselect_and_uses_dialog_order(monkeypatch, tmp_path):
    obj, first, second = _fake_self(
        tmp_path,
        {sk.WORD_MERGE: {"merge_order_key": sk.ORDER_ALPHA_AZ}},
    )
    captured = {}
    composers = []
    documents = []

    class FakeDocument:
        def __init__(self, path):
            self.path = path
            self.page_breaks = 0
            documents.append(path)

        def add_page_break(self):
            self.page_breaks += 1

    class FakeComposer:
        def __init__(self, document):
            self.doc = document
            self.appended = []
            composers.append(self)

        def append(self, document):
            self.appended.append(document)

        def save(self, path):
            Path(path).write_bytes(b"docx")

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

    monkeypatch.setattr("dialogs.merge_order_dialog.MergeOrderDialog", FakeDialog)
    monkeypatch.setattr(docx, "Document", FakeDocument)
    monkeypatch.setattr(docxcompose.composer, "Composer", FakeComposer)
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: None))
    monkeypatch.setattr(QMessageBox, "critical", staticmethod(lambda *a, **k: None))
    obj.record_config_usage = lambda *args: captured.setdefault("recorded", args)

    obj.merge_word_docs()

    assert captured["pre_select_key"] == sk.ORDER_ALPHA_AZ
    assert captured["recorded"] == (sk.WORD_MERGE, {"merge_order": sk.ORDER_ALPHA_ZA})
    assert documents[0] == str(second)
    assert [doc.path for doc in composers[0].appended] == [str(first)]


def test_word_merge_no_active_template_passes_no_preselect(monkeypatch, tmp_path):
    obj, _first, _second = _fake_self(tmp_path, {})
    captured = {}

    class FakeDialog:
        def __init__(self, files, file_type, parent=None, language="fr", pre_select_key=None):
            captured["pre_select_key"] = pre_select_key

        def exec(self):
            return QDialog.Rejected

    monkeypatch.setattr("dialogs.merge_order_dialog.MergeOrderDialog", FakeDialog)
    obj.merge_word_docs()

    assert captured["pre_select_key"] is None
