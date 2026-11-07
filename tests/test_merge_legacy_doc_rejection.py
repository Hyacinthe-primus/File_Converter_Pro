"""Legacy .doc files are rejected by the document merge workflow."""

from pathlib import Path

import pytest
from docx import Document

from app.mixins import pdf_operations as pdf_operations_module
from app.mixins.pdf_operations import PdfOperationsMixin
from context_menu import conversion_helpers
from context_menu.conversion_helpers import LEGACY_DOC_MERGE_ERROR
from context_menu.formats import CONVERSION_MAP
from tasks import watcher


def _make_docx(path: Path, text: str) -> Path:
    document = Document()
    document.add_paragraph(text)
    document.save(str(path))
    return path


def test_docx_merge_remains_supported(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    first = _make_docx(tmp_path / "first.docx", "First")
    second = _make_docx(tmp_path / "second.docx", "Second")

    output = conversion_helpers._merge_docx(
        [str(first), str(second)], str(out_dir), "none"
    )

    merged = Document(output)
    texts = [paragraph.text for paragraph in merged.paragraphs if paragraph.text]
    assert texts == ["First", "Second"]


def test_legacy_doc_merge_is_rejected_before_output(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    first = _make_docx(tmp_path / "first.docx", "First")
    legacy = tmp_path / "legacy.doc"
    legacy.write_bytes(b"legacy binary Word document")

    with pytest.raises(RuntimeError, match=r"Legacy \.doc files are not supported for merging"):
        conversion_helpers._merge_docx(
            [str(first), str(legacy)], str(out_dir), "none"
        )

    assert list(out_dir.glob("merged_*.docx")) == []


def test_main_merge_rejects_legacy_doc_with_explicit_message(monkeypatch, tmp_path):
    class _NoSelection:
        @staticmethod
        def selectedItems():
            return []

    legacy = tmp_path / "legacy.doc"
    legacy.write_bytes(b"legacy binary Word document")
    obj = PdfOperationsMixin.__new__(PdfOperationsMixin)
    obj.files_list_widget = _NoSelection()
    obj.files_list = [str(legacy)]
    obj.current_language = "en"
    obj.translate_text = lambda key: key
    messages = []
    monkeypatch.setattr(
        pdf_operations_module.QMessageBox,
        "critical",
        staticmethod(lambda *args: messages.append(args[2])),
    )

    obj.merge_word_docs()

    assert messages == [LEGACY_DOC_MERGE_ERROR]


def test_doc_format_no_longer_offers_merge_actions():
    actions = CONVERSION_MAP["doc"]

    assert "docx_to_pdf" in actions
    assert not [action for action in actions if action.startswith("merge_docx_")]


def test_watcher_word_merge_collection_excludes_legacy_doc(tmp_path):
    docx = _make_docx(tmp_path / "source.docx", "Source")
    (tmp_path / "legacy.doc").write_bytes(b"legacy binary Word document")

    files = watcher._collect_merge_files(
        str(tmp_path), watcher.MERGE_DOCX_ACTION, recursive=False
    )

    assert files == [str(docx)]
