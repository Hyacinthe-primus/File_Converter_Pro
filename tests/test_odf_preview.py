"""Native OpenDocument preview (no LibreOffice subprocess)."""

import io
import os
import zipfile

import pytest

pytest.importorskip("odf")
from odf.draw import Frame, Page, TextBox
from odf.opendocument import OpenDocumentPresentation, OpenDocumentSpreadsheet, OpenDocumentText
from odf.style import Style, TextProperties
from odf.table import Table, TableCell, TableRow
from odf.text import H, List, ListItem, P, Span

from utils import odf_preview


def _png_bytes(color=(40, 90, 200)):
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (16, 16), color).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def odt(tmp_path):
    doc = OpenDocumentText()
    bold = Style(name="B", family="text")
    bold.addElement(TextProperties(fontweight="bold"))
    doc.automaticstyles.addElement(bold)

    doc.text.addElement(H(outlinelevel=1, text="Rapport"))
    p = P(text="Bonjour <monde> & ")
    p.addElement(Span(stylename=bold, text="gras"))
    doc.text.addElement(p)
    lst = List()
    for label in ("un", "deux"):
        item = ListItem()
        item.addElement(P(text=label))
        lst.addElement(item)
    doc.text.addElement(lst)
    table = Table(name="t")
    row = TableRow()
    for value in ("A1", "B1"):
        cell = TableCell()
        cell.addElement(P(text=value))
        row.addElement(cell)
    table.addElement(row)
    doc.text.addElement(table)
    path = tmp_path / "doc.odt"
    doc.save(str(path))
    return str(path)


@pytest.fixture
def ods(tmp_path):
    doc = OpenDocumentSpreadsheet()
    table = Table(name="Ventes")
    for values in (("Produit", "Prix"), ("Stylo", "1,50 €")):
        row = TableRow()
        for v in values:
            cell = TableCell(valuetype="string")
            cell.addElement(P(text=v))
            row.addElement(cell)
        table.addElement(row)
    # a row repeated a million times must not blow up
    empty = TableRow(numberrowsrepeated=1048000)
    empty.addElement(TableCell(numbercolumnsrepeated=16000))
    table.addElement(empty)
    doc.spreadsheet.addElement(table)
    path = tmp_path / "sheet.ods"
    doc.save(str(path))
    return str(path)


@pytest.fixture
def odp(tmp_path):
    doc = OpenDocumentPresentation()
    for i, title in enumerate(("Intro", "Conclusion"), 1):
        page = Page(name=f"page{i}", masterpagename="Default")
        frame = Frame(width="10cm", height="2cm", x="1cm", y="1cm")
        box = TextBox()
        box.addElement(P(text=title))
        frame.addElement(box)
        page.addElement(frame)
        doc.presentation.addElement(page)
    path = tmp_path / "slides.odp"
    doc.save(str(path))
    return str(path)


def _add_thumbnail(path):
    with zipfile.ZipFile(path, "a") as zf:
        zf.writestr("Thumbnails/thumbnail.png", _png_bytes())


class TestOdt:
    def test_headings_paragraphs_and_escaping(self, odt):
        html = odf_preview.odt_to_html(odt).html
        assert "<h1>Rapport</h1>" in html
        assert "Bonjour &lt;monde&gt; &amp; " in html  # user text can never inject markup

    def test_bold_style_is_applied(self, odt):
        assert "<b>gras</b>" in odf_preview.odt_to_html(odt).html

    def test_list_and_table(self, odt):
        html = odf_preview.odt_to_html(odt).html
        assert "<li>" in html and "un" in html and "deux" in html
        assert "<td><p" in html and "A1" in html and "B1" in html

    def test_empty_document_is_reported_empty(self, tmp_path):
        path = tmp_path / "empty.odt"
        OpenDocumentText().save(str(path))
        assert odf_preview.odt_to_html(str(path)).is_empty

    def test_embedded_image_is_extracted(self, tmp_path):
        doc = OpenDocumentText()
        href = doc.addPicture(str(_write(tmp_path / "pic.png", _png_bytes())))
        frame = Frame(width="2cm", height="2cm")
        from odf.draw import Image as DrawImage

        frame.addElement(DrawImage(href=href))
        p = P()
        p.addElement(frame)
        doc.text.addElement(p)
        path = tmp_path / "img.odt"
        doc.save(str(path))
        result = odf_preview.odt_to_html(str(path))
        assert len(result.images) == 1
        assert "odfimg://0" in result.html


class TestOds:
    def test_values_as_displayed(self, ods):
        (name, rows), = odf_preview.ods_sheets(ods)
        assert name == "Ventes"
        assert rows == [["Produit", "Prix"], ["Stylo", "1,50 €"]]

    def test_huge_repeated_rows_are_trimmed_not_expanded(self, ods):
        (_, rows), = odf_preview.ods_sheets(ods)
        assert len(rows) == 2

    def test_empty_workbook_has_no_sheets(self, tmp_path):
        path = tmp_path / "empty.ods"
        OpenDocumentSpreadsheet().save(str(path))
        assert odf_preview.ods_sheets(str(path)) == []


class TestOdp:
    def test_slide_text_in_order(self, odp):
        assert odf_preview.odp_slides(odp) == [["Intro"], ["Conclusion"]]


class TestThumbnail:
    def test_thumbnail_is_read_when_present(self, odt):
        assert odf_preview.read_thumbnail(odt) is None
        _add_thumbnail(odt)
        assert odf_preview.read_thumbnail(odt)[:4] == b"\x89PNG"

    def test_non_zip_file_returns_none(self, tmp_path):
        bad = tmp_path / "x.odt"
        bad.write_bytes(b"not a zip")
        assert odf_preview.read_thumbnail(str(bad)) is None


class TestSizeLimit:
    def test_oversized_file_is_refused(self, odt, monkeypatch):
        monkeypatch.setattr(odf_preview, "MAX_FILE_BYTES", 10)
        with pytest.raises(odf_preview.OdfTooLarge):
            odf_preview.odt_to_html(odt)


def _write(path, data):
    path.write_bytes(data)
    return path


@pytest.fixture
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


class TestPreviewDialog:
    @pytest.fixture(autouse=True)
    def no_libreoffice(self, monkeypatch):
        """The native path must never reach for soffice."""
        import external_binaries

        def boom(*_a, **_k):
            raise AssertionError("LibreOffice must not be used when native preview works")

        monkeypatch.setattr(external_binaries, "resolve_binary", boom)

    def _widgets(self, dlg):
        from PySide6.QtWidgets import QTableWidget, QTabWidget, QTextEdit

        return (
            dlg.findChildren(QTextEdit),
            dlg.findChildren(QTabWidget),
            dlg.findChildren(QTableWidget),
        )

    def test_odt_renders_in_text_view(self, qapp, odt):
        from dialogs.preview_dialog import PreviewDialog

        dlg = PreviewDialog(odt, None, "en")
        edits, _, _ = self._widgets(dlg)
        assert edits and "Rapport" in edits[0].toPlainText()

    def test_ods_renders_in_tabs(self, qapp, ods):
        from dialogs.preview_dialog import PreviewDialog

        dlg = PreviewDialog(ods, None, "en")
        _, tabs, tables = self._widgets(dlg)
        assert tabs and tabs[0].tabText(0) == "Ventes"
        assert tables[0].item(1, 1).text() == "1,50 €"

    def test_odp_shows_slide_text_and_thumbnail(self, qapp, odp):
        from PySide6.QtWidgets import QLabel

        from dialogs.preview_dialog import PreviewDialog

        _add_thumbnail(odp)
        dlg = PreviewDialog(odp, None, "en")
        edits, _, _ = self._widgets(dlg)
        assert "Intro" in edits[0].toPlainText() and "Conclusion" in edits[0].toPlainText()
        assert any(w.pixmap() is not None and not w.pixmap().isNull() for w in dlg.findChildren(QLabel))

    def test_empty_odt_falls_back_to_thumbnail(self, qapp, tmp_path):
        from PySide6.QtWidgets import QLabel

        from dialogs.preview_dialog import PreviewDialog

        path = tmp_path / "empty.odt"
        OpenDocumentText().save(str(path))
        _add_thumbnail(str(path))
        dlg = PreviewDialog(str(path), None, "en")
        assert any(w.pixmap() is not None and not w.pixmap().isNull() for w in dlg.findChildren(QLabel))

    def test_broken_file_uses_libreoffice_as_last_resort(self, qapp, tmp_path, monkeypatch):
        import external_binaries
        from dialogs.preview_dialog import PreviewDialog

        called = []
        monkeypatch.setattr(external_binaries, "resolve_binary", lambda *_: called.append(1) or None)
        bad = tmp_path / "broken.odt"
        bad.write_bytes(b"not a zip")
        PreviewDialog(str(bad), None, "en")
        assert called
