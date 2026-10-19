"""Image → SVG (VTracer vectorisation) and SVG → raster (PyMuPDF)."""

import xml.etree.ElementTree as ET

import pytest
from PIL import Image

from converter.converters import AdvancedConverterEngine

SVG_NS = "http://www.w3.org/2000/svg"
RED = (200, 40, 40)


@pytest.fixture
def engine():
    return AdvancedConverterEngine()


def _png_with_rect(path, size=(60, 40), color=RED):
    """White image with a solid coloured rectangle, which VTracer turns into a path."""
    img = Image.new("RGB", size, "white")
    w, h = size
    for x in range(w // 5, w * 4 // 5):
        for y in range(h // 5, h * 4 // 5):
            img.putpixel((x, y), color)
    img.save(path)
    return str(path)


def _svg(path, size=(120, 80)):
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size[0]}" height="{size[1]}">'
        f'<rect width="{size[0]}" height="{size[1]}" fill="white"/>'
        '<circle cx="60" cy="40" r="20" fill="#e01010"/></svg>',
        encoding="utf-8",
    )
    return str(path)


def _root(path):
    return ET.parse(path).getroot()


def _fills(root):
    colors = []
    for el in root.iter():
        fill = el.get("fill")
        if fill and fill.startswith("#") and len(fill) == 7:
            colors.append(tuple(int(fill[i : i + 2], 16) for i in (1, 3, 5)))
    return colors


def _near(color, target, tolerance=16):
    return all(abs(a - b) <= tolerance for a, b in zip(color, target))


class TestImageToSvgVectorises:
    def test_output_is_well_formed_svg(self, engine, tmp_path):
        src = _png_with_rect(tmp_path / "photo.png")
        dst = tmp_path / "photo.svg"
        assert engine._image_to_svg(src, str(dst)) is True
        assert _root(dst).tag == f"{{{SVG_NS}}}svg"

    def test_output_is_vector_not_an_embedded_raster(self, engine, tmp_path):
        src = _png_with_rect(tmp_path / "photo.png")
        dst = tmp_path / "photo.svg"
        engine._image_to_svg(src, str(dst))

        raw = dst.read_text(encoding="utf-8")
        root = _root(dst)
        tags = [el.tag.split("}")[-1] for el in root.iter()]
        assert "path" in tags
        assert "image" not in tags
        assert "data:image" not in raw

    def test_dimensions_match_the_source(self, engine, tmp_path):
        src = _png_with_rect(tmp_path / "photo.png", size=(90, 60))
        dst = tmp_path / "photo.svg"
        engine._image_to_svg(src, str(dst))

        root = _root(dst)
        assert root.get("width") == "90"
        assert root.get("height") == "60"

    def test_colours_are_preserved(self, engine, tmp_path):
        src = _png_with_rect(tmp_path / "photo.png", color=RED)
        dst = tmp_path / "photo.svg"
        engine._image_to_svg(src, str(dst))
        assert any(_near(c, RED) for c in _fills(_root(dst)))

    def test_accepts_jpeg_input(self, engine, tmp_path):
        src = tmp_path / "photo.jpg"
        Image.new("RGB", (40, 30), (12, 130, 220)).save(src, format="JPEG")
        dst = tmp_path / "photo.svg"
        assert engine._image_to_svg(str(src), str(dst)) is True
        assert _root(dst).tag == f"{{{SVG_NS}}}svg"

    def test_accepts_rgba_input(self, engine, tmp_path):
        src = tmp_path / "icon.png"
        img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        img.putpixel((16, 16), (220, 20, 20, 255))
        img.save(src)
        dst = tmp_path / "icon.svg"
        assert engine._image_to_svg(str(src), str(dst)) is True

    def test_heic_input_uses_the_pillow_fallback(self, engine, tmp_path):
        pillow_heif = pytest.importorskip("pillow_heif")
        pillow_heif.register_heif_opener()
        src = tmp_path / "photo.heic"
        Image.new("RGB", (50, 30), (30, 200, 60)).save(src, format="HEIF")
        dst = tmp_path / "photo.svg"
        assert engine._image_to_svg(str(src), str(dst)) is True
        assert _root(dst).tag == f"{{{SVG_NS}}}svg"

    def test_svg_input_is_rendered_then_traced(self, engine, tmp_path):
        src = _svg(tmp_path / "in.svg")
        dst = tmp_path / "out.svg"
        assert engine._image_to_svg(src, str(dst)) is True
        assert _root(dst).get("width") == "120"

    def test_unreadable_input_returns_false_without_crashing(self, engine, tmp_path):
        # VTracer panics with PanicException (a BaseException), which must be caught
        bad = tmp_path / "bad.png"
        bad.write_bytes(b"not an image")
        dst = tmp_path / "bad.svg"
        assert engine._image_to_svg(str(bad), str(dst)) is False
        assert not (dst.exists() and dst.stat().st_size == 0)


class TestSvgToRaster:
    def test_svg_to_png(self, engine, tmp_path):
        src = _svg(tmp_path / "in.svg")
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        result = engine.convert("image_to_png", src, str(out_dir))
        assert result.success is True
        assert Image.open(result.target).size == (120, 80)

    def test_svg_to_jpeg_has_a_white_background(self, engine, tmp_path):
        src = tmp_path / "t.svg"
        src.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40">'
            '<circle cx="20" cy="20" r="10" fill="red"/></svg>',
            encoding="utf-8",
        )
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        result = engine.convert("image_to_jpeg", str(src), str(out_dir))
        assert result.success is True
        corner = Image.open(result.target).getpixel((1, 1))
        assert all(channel > 240 for channel in corner)  # transparent area flattened to white

    def test_open_universal_image_renders_svg(self, engine, tmp_path):
        img = engine._open_universal_image(_svg(tmp_path / "in.svg"))
        assert img.size == (120, 80)

    def test_open_image_for_pdf_handles_svg(self, tmp_path):
        from app.mixins.image_to_pdf import ImageToPdfMixin

        img = ImageToPdfMixin()._open_image_for_pdf(_svg(tmp_path / "in.svg"))
        assert img.size == (120, 80)


class TestConvertDispatch:
    def test_engine_convert_reports_success(self, engine, tmp_path):
        src = _png_with_rect(tmp_path / "logo.png")
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        result = engine.convert("image_to_svg", src, str(out_dir))
        assert result.success is True
        assert result.target.endswith(".svg")
        assert _root(result.target).tag == f"{{{SVG_NS}}}svg"
