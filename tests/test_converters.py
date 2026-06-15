"""Tests for the converter engine."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_conversion_result():
    """ConversionResult should store success, source, target."""
    from converter.converters import ConversionResult
    r = ConversionResult(success=True, source="/a.txt", target="/b.pdf", elapsed=1.0)
    assert r.success is True
    assert r.source == "/a.txt"
    assert r.target == "/b.pdf"
    assert r.elapsed == 1.0
    assert "OK" in repr(r)


def test_conversion_result_failure():
    """ConversionResult failure should show error."""
    from converter.converters import ConversionResult
    r = ConversionResult(success=False, source="/a.txt", target="", error="not found")
    assert r.success is False
    assert "ERR" in repr(r)


def test_category_map():
    """CATEGORY_MAP should categorize conversion types."""
    from converter.converters import CATEGORY_MAP
    assert CATEGORY_MAP.get("txt_to_pdf") == "document"
    assert CATEGORY_MAP.get("image_to_png") == "image"
    assert CATEGORY_MAP.get("video_to_mp4") == "video"
    assert CATEGORY_MAP.get("audio_to_mp3") == "audio"


def test_engine_has_dispatch():
    """AdvancedConverterEngine should have _DISPATCH mapping."""
    from converter.converters import AdvancedConverterEngine
    assert hasattr(AdvancedConverterEngine, "_DISPATCH")
    assert "txt_to_pdf" in AdvancedConverterEngine._DISPATCH


def test_engine_has_document_converters():
    """AdvancedConverterEngine should inherit DocumentConverters."""
    from converter.converters import AdvancedConverterEngine
    from converter.mixins import DocumentConverters
    assert issubclass(AdvancedConverterEngine, DocumentConverters)


def test_engine_has_image_converters():
    """AdvancedConverterEngine should inherit ImageConverters."""
    from converter.converters import AdvancedConverterEngine
    from converter.mixins import ImageConverters
    assert issubclass(AdvancedConverterEngine, ImageConverters)


def test_engine_has_media_converters():
    """AdvancedConverterEngine should inherit MediaConverters."""
    from converter.converters import AdvancedConverterEngine
    from converter.mixins import MediaConverters
    assert issubclass(AdvancedConverterEngine, MediaConverters)
