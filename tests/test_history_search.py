"""History search must match the localized Type column, not only raw keys."""

import pytest

from history import matching_operation_types


def test_matching_operation_types_uses_localized_labels():
    labels = {
        "pdf_to_word": "PDF vers Word",
        "word_to_pdf": "Word vers PDF",
    }
    assert matching_operation_types(labels, "pdf vers", labels.get) == ["pdf_to_word"]
    assert matching_operation_types(labels, "word vers", labels.get) == ["word_to_pdf"]
    assert matching_operation_types(labels, "", labels.get) == []


@pytest.fixture
def db(tmp_path, monkeypatch):
    import database

    monkeypatch.setattr(database, "SRC_DIR", tmp_path)
    manager = database.DatabaseManager()
    yield manager
    manager.close()


def test_history_query_accepts_localized_operation_keys(db):
    db.add_conversion_record("source.pdf", "PDF", "target.docx", "DOCX", "pdf_to_word", 100, 1.0)
    db.add_conversion_record("source.docx", "DOCX", "target.pdf", "PDF", "word_to_pdf", 100, 1.0)

    rows = db.get_conversion_history(
        limit=10,
        search_query="PDF vers Word",
        operation_types=["pdf_to_word"],
    )
    assert len(rows) == 1
    assert rows[0][6] == "pdf_to_word"
