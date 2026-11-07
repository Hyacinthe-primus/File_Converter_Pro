"""TIFF/TIF identifier and workflow dispatch regressions."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

import context_menu.window as cm_window
from context_menu.formats import CONVERSION_MAP, LABELS
from converter.converters import CATEGORY_MAP, AdvancedConverterEngine
from converter.registry import DISPATCH
from tasks import scheduler, watcher


def _make_image(path: Path, fmt: str = "JPEG") -> Path:
    Image.new("RGB", (18, 12), "blue").save(path, format=fmt)
    return path


def _assert_tiff(path: Path) -> None:
    assert path.is_file()
    with Image.open(path) as image:
        assert image.format == "TIFF"
        image.verify()


@pytest.mark.parametrize(
    ("conversion_type", "extension"),
    [("image_to_tif", "tif"), ("image_to_tiff", "tiff")],
)
def test_registry_dispatches_both_tiff_identifiers(conversion_type, extension):
    assert DISPATCH[conversion_type] == ("_image_convert", extension)
    assert CATEGORY_MAP[conversion_type] == "image"


@pytest.mark.parametrize(
    ("conversion_type", "extension"),
    [("image_to_tif", "tif"), ("image_to_tiff", "tiff")],
)
def test_engine_converts_to_tif_and_tiff_identifiers(tmp_path, conversion_type, extension):
    src = _make_image(tmp_path / "source.jpg")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    result = AdvancedConverterEngine().convert(conversion_type, str(src), str(out_dir))

    assert result.success is True
    assert Path(result.target).name == f"source.{extension}"
    _assert_tiff(Path(result.target))


@pytest.mark.parametrize(
    ("source_suffix", "conversion_type", "output_suffix"),
    [(".tif", "image_to_tif", ".tif"), (".tiff", "image_to_tiff", ".tiff")],
)
def test_tif_and_tiff_inputs_and_outputs(tmp_path, source_suffix, conversion_type, output_suffix):
    input_dir = tmp_path / "input"
    out_dir = tmp_path / "out"
    input_dir.mkdir()
    out_dir.mkdir()
    src = _make_image(input_dir / f"source{source_suffix}", fmt="TIFF")

    result = AdvancedConverterEngine().convert(conversion_type, str(src), str(out_dir))

    assert result.success is True
    assert Path(result.target).name == f"source{output_suffix}"
    _assert_tiff(Path(result.target))


@pytest.mark.parametrize(
    ("conversion_type", "extension"),
    [("image_to_tif", "tif"), ("image_to_tiff", "tiff")],
)
def test_quick_convert_routes_tiff_identifiers(qapp, tmp_path, monkeypatch, conversion_type, extension):
    src = _make_image(tmp_path / "source.jpg")
    monkeypatch.setattr(cm_window, "_load_quick_config", lambda: {"backup_before_conversion": False})

    thread = cm_window.ConversionThread([str(src)], conversion_type)
    thread.run()

    output = tmp_path / f"source.{extension}"
    _assert_tiff(output)


@pytest.mark.parametrize("runner", [watcher._run_conversion, scheduler._run_conversion])
@pytest.mark.parametrize(
    ("conversion_type", "extension"),
    [("image_to_tif", "tif"), ("image_to_tiff", "tiff")],
)
def test_watcher_and_scheduler_route_tiff_identifiers(tmp_path, runner, conversion_type, extension):
    src = _make_image(tmp_path / "source.jpg")
    out_dir = tmp_path / "out"

    runner(conversion_type, str(src), str(out_dir))

    _assert_tiff(out_dir / f"source.{extension}")


@pytest.mark.parametrize(
    ("source_ext", "target_fmt", "expected"),
    [
        ("tif", "tif", "image_to_tif"),
        ("tif", "tiff", "image_to_tiff"),
        ("tiff", "tif", "image_to_tif"),
        ("tiff", "tiff", "image_to_tiff"),
    ],
)
def test_watcher_builds_tiff_conversion_types_for_both_extensions(source_ext, target_fmt, expected):
    assert watcher._build_conversion_type(source_ext, target_fmt) == expected


def test_persisted_tif_identifiers_and_labels_remain_available():
    assert "image_to_tif" in CONVERSION_MAP["tif"]
    assert "image_to_tiff" in CONVERSION_MAP["tiff"]
    assert "image_to_tif" in CONVERSION_MAP["tiff"]
    assert "image_to_tiff" in CONVERSION_MAP["tif"]
    assert LABELS["image_to_tif"] == "Image → TIF"
    assert LABELS["image_to_tiff"] == "Image → TIFF"


def test_unsupported_tiff_identifier_is_not_redirected(tmp_path):
    src = _make_image(tmp_path / "source.jpg")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    result = AdvancedConverterEngine().convert("image_to_tif_alias", str(src), str(out_dir))

    assert result.success is False
    assert "Unknown type" in result.error
    assert list(out_dir.iterdir()) == []


def test_unrelated_image_identifiers_remain_unchanged(tmp_path):
    src = _make_image(tmp_path / "source.jpg")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    assert DISPATCH["image_to_jpg"] == ("_image_convert", "jpg")
    assert DISPATCH["image_to_jpeg"] == ("_image_convert", "jpeg")
    result = AdvancedConverterEngine().convert("image_to_png", str(src), str(out_dir))

    assert result.success is True
    assert (out_dir / "source.png").is_file()
