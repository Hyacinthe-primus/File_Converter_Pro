"""Tests for OpenDocument conversions (ODT/ODS/ODP)."""

import os
import shutil
import tempfile
import zipfile

import pytest


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


class TestOpenDocumentConversions:
    def test_odt_to_docx_dispatch(self):
        from converter.registry import DISPATCH

        assert "odt_to_docx" in DISPATCH
        assert DISPATCH["odt_to_docx"] == (("_odt_to_docx_com", "_odt_to_docx"), "docx")

    def test_ods_to_xlsx_dispatch(self):
        from converter.registry import DISPATCH

        assert "ods_to_xlsx" in DISPATCH
        assert DISPATCH["ods_to_xlsx"] == (("_ods_to_xlsx_com", "_ods_to_xlsx"), "xlsx")

    def test_odp_to_pptx_dispatch(self):
        from converter.registry import DISPATCH

        assert "odp_to_pptx" in DISPATCH
        assert DISPATCH["odp_to_pptx"] == (("_odp_to_pptx_com", "_odp_to_pptx"), "pptx")

    def test_odt_to_pdf_dispatch(self):
        from converter.registry import DISPATCH

        assert "odt_to_pdf" in DISPATCH
        assert DISPATCH["odt_to_pdf"] == (("_odt_to_pdf_com", "_odt_to_pdf"), "pdf")

    def test_ods_to_pdf_dispatch(self):
        from converter.registry import DISPATCH

        assert "ods_to_pdf" in DISPATCH
        assert DISPATCH["ods_to_pdf"] == (("_ods_to_pdf_com", "_ods_to_pdf"), "pdf")

    def test_odp_to_pdf_dispatch(self):
        from converter.registry import DISPATCH

        assert "odp_to_pdf" in DISPATCH
        assert DISPATCH["odp_to_pdf"] == (("_odp_to_pdf_com", "_odp_to_pdf"), "pdf")

    def test_odt_native_fallback(self, tmp_dir):
        from converter.converters import AdvancedConverterEngine

        src = os.path.join(tmp_dir, "test.odt")
        dst = os.path.join(tmp_dir, "test.docx")

        with zipfile.ZipFile(src, "w") as zf:
            zf.writestr("content.xml", "<text>hello world</text>")

        engine = AdvancedConverterEngine()
        assert engine._odt_to_docx(src, dst) is True
        assert os.path.exists(dst)

    def test_ods_native_fallback(self, tmp_dir):
        from converter.converters import AdvancedConverterEngine

        src = os.path.join(tmp_dir, "test.ods")
        dst = os.path.join(tmp_dir, "test.xlsx")

        with zipfile.ZipFile(src, "w") as zf:
            zf.writestr(
                "content.xml",
                "<table:table-row><table:table-cell>A1</table:table-cell></table:table-row>",
            )

        engine = AdvancedConverterEngine()
        assert engine._ods_to_xlsx(src, dst) is True
        assert os.path.exists(dst)

    def test_odp_native_fallback(self, tmp_dir):
        from converter.converters import AdvancedConverterEngine

        src = os.path.join(tmp_dir, "test.odp")
        dst = os.path.join(tmp_dir, "test.pptx")

        with zipfile.ZipFile(src, "w") as zf:
            zf.writestr(
                "content.xml",
                '<draw:page><text:p>Slide Title</text:p></draw:page>',
            )

        engine = AdvancedConverterEngine()
        assert engine._odp_to_pptx(src, dst) is True
        assert os.path.exists(dst)
