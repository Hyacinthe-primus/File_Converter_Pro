"""Tests for images whose real format differs from their extension (e.g. HEIC saved as .png)."""

import os

import pytest

from utils.image_formats import decodable_image_path, sniff_image_ext

pytest.importorskip("pillow_heif")
from PIL import Image  # noqa: E402


@pytest.fixture
def heic_named_png(tmp_path):
    """A genuine HEIC file that carries a .png extension."""
    from pillow_heif import register_heif_opener

    register_heif_opener()
    path = tmp_path / "photo.png"
    Image.new("RGB", (64, 48), (200, 60, 90)).save(path, format="HEIF")
    return str(path)


@pytest.fixture
def real_png(tmp_path):
    path = tmp_path / "real.png"
    Image.new("RGB", (32, 32), (10, 20, 30)).save(path, format="PNG")
    return str(path)


class TestSniff:
    def test_heic_content_wins_over_png_extension(self, heic_named_png):
        assert sniff_image_ext(heic_named_png, ".png") == ".heic"

    def test_real_png_keeps_its_extension(self, real_png):
        assert sniff_image_ext(real_png, ".png") == ".png"

    def test_avif_brand_is_detected(self, tmp_path):
        f = tmp_path / "x.png"
        f.write_bytes(b"\x00\x00\x00\x1cftypavif\x00\x00\x00\x00mif1avif")
        assert sniff_image_ext(str(f), ".png") == ".avif"

    def test_missing_file_falls_back(self, tmp_path):
        assert sniff_image_ext(str(tmp_path / "nope.png"), ".png") == ".png"


class TestDecodablePath:
    def test_regular_image_is_passed_through(self, real_png):
        with decodable_image_path(real_png) as p:
            assert p == real_png

    def test_heic_is_converted_to_a_readable_png(self, heic_named_png):
        import fitz

        with decodable_image_path(heic_named_png) as p:
            assert p != heic_named_png
            assert os.path.exists(p)
            pix = fitz.Pixmap(p)  # PyMuPDF cannot read HEIC, so this proves a real PNG was produced
            assert (pix.width, pix.height) == (64, 48)
            produced = p
        assert not os.path.exists(produced)  # temp file cleaned up
        assert os.path.exists(heic_named_png)  # original untouched

    def test_unreadable_heic_yields_original_path(self, tmp_path):
        broken = tmp_path / "broken.heic"
        broken.write_bytes(b"\x00\x00\x00\x1cftypheic\x00\x00\x00\x00 not really an image")
        with decodable_image_path(str(broken)) as p:
            assert p == str(broken)

    def test_temp_file_removed_even_when_caller_fails(self, heic_named_png):
        produced = None
        with pytest.raises(RuntimeError):
            with decodable_image_path(heic_named_png) as p:
                produced = p
                raise RuntimeError("decoder blew up")
        assert not os.path.exists(produced)


class TestImageToPdfPipeline:
    def test_generic_embedder_handles_heic_named_png(self, heic_named_png, tmp_path):
        import fitz

        from app.mixins.image_to_pdf import ImageToPdfMixin

        out = str(tmp_path / "out.pdf")
        ImageToPdfMixin._single_image_to_generic_pdf(None, heic_named_png, out)
        doc = fitz.open(out)
        assert len(doc) == 1
        doc.close()

    def test_open_image_for_pdf_handles_heic_named_png(self, heic_named_png):
        from app.mixins.image_to_pdf import ImageToPdfMixin

        img = ImageToPdfMixin._open_image_for_pdf(None, heic_named_png)
        assert img.size == (64, 48)
