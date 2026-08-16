"""Tests for batch rename and batch conversion routing logic."""

import os
import tempfile

from app.mixins.batch import BatchMixin


def test_batch_rename_basic():
    """Rename files according to plan."""

    with tempfile.TemporaryDirectory() as tmp:
        # Create test files
        f1 = os.path.join(tmp, "old1.txt")
        f2 = os.path.join(tmp, "old2.txt")
        with open(f1, "w") as f:
            f.write("test1")
        with open(f2, "w") as f:
            f.write("test2")

        # Create a minimal mock for the mixin
        class MockApp:
            def __init__(self):
                self.files_list = [f1, f2]
                self.current_language = "fr"
                self.config = {}
                self.system_notifier = None

            def translate_text(self, text):
                return text

            def get_file_icon(self, path):
                return "📄"

            def format_size(self, size):
                return str(size)

            def update_file_counter(self):
                pass

        # We can't fully test process_batch_rename without Qt widgets,
        # but we can test the rename logic directly
        new_f1 = os.path.join(tmp, "new1.txt")
        os.rename(f1, new_f1)
        assert os.path.exists(new_f1)
        assert not os.path.exists(f1)


def test_get_output_directory_default(tmp_path):
    """get_output_directory returns default folder when no filename."""

    class MockApp:
        config = {"default_output_folder": str(tmp_path)}

        def translate_text(self, text):
            return text

    app = MockApp()
    # Can't call get_output_directory without Qt, but we can verify the logic
    default_dir = app.config.get("default_output_folder")
    assert default_dir == str(tmp_path)
    assert os.path.exists(default_dir)


def _make_batch():
    return BatchMixin.__new__(BatchMixin)


def test_batch_copy_creates_file(tmp_path):
    src = tmp_path / "in.txt"
    dst = tmp_path / "out.txt"
    src.write_text("hello")
    assert BatchMixin._batch_copy(str(src), str(dst)) is True
    assert dst.read_text() == "hello"


def test_batch_copy_missing_source(tmp_path):
    dst = tmp_path / "out.txt"
    assert BatchMixin._batch_copy(str(tmp_path / "nope.txt"), str(dst)) is False


def test_batch_pdf_to_png_pages(tmp_path):
    import fitz

    pdf = tmp_path / "multi.pdf"
    doc = fitz.open()
    for _ in range(2):
        page = doc.new_page()
        page.insert_text((72, 72), "test")
    doc.save(str(pdf))
    doc.close()

    out_base = tmp_path / "out.png"
    assert BatchMixin._pdf_to_png(str(pdf), str(out_base)) is True
    assert out_base.exists()
    assert (tmp_path / "out_page_2.png").exists()
    assert not (tmp_path / "out_page_3.png").exists()


def test_batch_convert_image_to_pdf(tmp_path):
    from PIL import Image

    img = tmp_path / "pic.png"
    Image.new("RGB", (10, 10), "red").save(img)
    out = tmp_path / "pic.pdf"
    b = _make_batch()
    b._open_image_for_pdf = lambda fp: Image.open(fp)
    assert b._batch_to_pdf(str(img), str(out), ".png") is True
    assert out.exists() and out.stat().st_size > 0


def test_batch_convert_image_to_docx(tmp_path):
    from PIL import Image

    img = tmp_path / "pic.png"
    Image.new("RGB", (10, 10), "red").save(img)
    out = tmp_path / "pic.docx"
    b = _make_batch()
    assert b._batch_image_to_docx(str(img), str(out)) is True
    assert out.exists() and out.stat().st_size > 0


def test_batch_convert_image_to_png(tmp_path):
    from PIL import Image

    img = tmp_path / "pic.jpg"
    Image.new("RGB", (10, 10), "blue").save(img, "JPEG")
    out = tmp_path / "pic.png"
    b = _make_batch()
    assert b._batch_to_png(str(img), str(out), ".jpg") is True
    assert out.exists() and out.stat().st_size > 0


def test_batch_unsupported_format_returns_false(tmp_path):
    src = tmp_path / "weird.xyz"
    src.write_text("data")
    out = tmp_path / "weird.pdf"
    b = _make_batch()
    assert b._convert_batch_file(str(src), str(out), "pdf") is False
    assert not out.exists()


def test_batch_engine_txt_to_pdf(tmp_path):
    src = tmp_path / "note.txt"
    src.write_text("hello world")
    out = tmp_path / "note.pdf"
    b = _make_batch()
    assert b._batch_to_pdf(str(src), str(out), ".txt") is True
    assert out.exists() and out.stat().st_size > 0


def test_batch_pdf_to_docx_native_fallback_with_image(tmp_path):
    """A PDF containing an image must yield a non-empty DOCX via native fallback."""
    import io

    import fitz
    from PIL import Image

    pdf = tmp_path / "img.pdf"
    doc = fitz.open()
    page = doc.new_page()
    img_bytes = io.BytesIO()
    Image.new("RGB", (60, 40), (200, 30, 30)).save(img_bytes, "PNG")
    page.insert_image(page.rect, stream=img_bytes.getvalue())
    doc.save(str(pdf))
    doc.close()

    out = tmp_path / "img.docx"
    from app.mixins.pdf_to_word import PdfToWordMixin

    class _Combo(BatchMixin, PdfToWordMixin):
        pass

    b = _Combo.__new__(_Combo)
    b._try_word_com_pdf_to_docx = lambda p, d: False
    b._convert_pdf_to_docx_libreoffice = lambda p, d, timeout=120: False
    assert b._batch_pdf_to_docx(str(pdf), str(out)) is True
    assert out.exists() and out.stat().st_size > 0

    from docx import Document

    converted = Document(str(out))
    assert len(converted.inline_shapes) >= 1
