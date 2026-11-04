"""HEIC/AVIF support for Quick Convert image-to-PDF helpers."""

import tempfile
import types
from pathlib import Path

import fitz
import pytest
from PIL import Image

import context_menu.window as cm_window
import utils.image_formats as image_formats


def _write_image(path: Path, fmt: str):
    if fmt == "HEIF":
        pytest.importorskip("pillow_heif")
        from pillow_heif import register_heif_opener

        register_heif_opener()
    try:
        Image.new("RGB", (24, 18), (120, 30, 30)).save(path, format=fmt)
    except Exception as exc:
        pytest.skip(f"{fmt} encoding unavailable: {exc}")
    return path


@pytest.mark.parametrize(("suffix", "fmt"), [(".png", "PNG"), (".jpg", "JPEG")])
def test_standard_images_still_convert(tmp_path, suffix, fmt):
    src = _write_image(tmp_path / f"image{suffix}", fmt)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    cm_window._convert_image_to_pdf(str(src), str(out_dir))

    output = out_dir / f"{src.stem}.pdf"
    assert output.is_file()
    with fitz.open(output) as doc:
        assert doc.page_count == 1


@pytest.mark.parametrize(("suffix", "fmt"), [(".heic", "HEIF"), (".avif", "AVIF")])
def test_heic_and_avif_to_pdf(tmp_path, suffix, fmt):
    src = _write_image(tmp_path / f"photo{suffix}", fmt)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    cm_window._convert_image_to_pdf(str(src), str(out_dir))

    output = out_dir / f"{src.stem}.pdf"
    assert output.is_file()
    with fitz.open(output) as doc:
        assert doc.page_count == 1


@pytest.mark.parametrize(("suffix", "fmt"), [(".heic", "HEIF"), (".avif", "AVIF")])
def test_merged_images_support_heic_and_avif(tmp_path, suffix, fmt):
    src = _write_image(tmp_path / f"photo{suffix}", fmt)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    cm_window._merge_images_to_pdf([str(src)], str(out_dir))

    outputs = list(out_dir.glob("merged_images_*.pdf"))
    assert len(outputs) == 1
    with fitz.open(outputs[0]) as doc:
        assert doc.page_count == 1


def test_invalid_image_raises_without_output(tmp_path):
    src = tmp_path / "invalid.png"
    src.write_bytes(b"not an image")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    with pytest.raises(Exception):
        cm_window._convert_image_to_pdf(str(src), str(out_dir))

    assert not list(out_dir.glob("*.pdf"))


def test_decodable_temporary_image_is_cleaned_up(tmp_path, monkeypatch):
    src = _write_image(tmp_path / "photo.heic", "HEIF")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    created = []
    real_mkstemp = tempfile.mkstemp

    def tracking_mkstemp(*args, **kwargs):
        fd, path = real_mkstemp(*args, **kwargs)
        created.append(path)
        return fd, path

    monkeypatch.setattr(
        image_formats,
        "tempfile",
        types.SimpleNamespace(mkstemp=tracking_mkstemp),
    )

    cm_window._convert_image_to_pdf(str(src), str(out_dir))

    assert created
    assert all(not Path(path).exists() for path in created)


@pytest.mark.parametrize("module_name", ["watcher", "scheduler"])
def test_automation_image_to_pdf_supports_heic(tmp_path, module_name):
    from tasks import scheduler, watcher

    src = _write_image(tmp_path / "photo.heic", "HEIF")
    out_dir = tmp_path / "out"
    runner = watcher._run_conversion if module_name == "watcher" else scheduler._run_conversion

    runner("image_to_pdf", str(src), str(out_dir), ocr=False)

    assert (out_dir / f"{src.stem}.pdf").is_file()
