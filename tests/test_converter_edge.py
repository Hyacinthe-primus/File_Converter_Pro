"""Tests for converter engine dispatch and edge cases."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter.converters import AdvancedConverterEngine, ConversionResult, CATEGORY_MAP


def test_conversion_result_attributes():
    r = ConversionResult(True, "/a.txt", "/b.pdf", 1.5, "", 1024)
    assert r.success is True
    assert r.source == "/a.txt"
    assert r.target == "/b.pdf"
    assert r.elapsed == 1.5
    assert r.file_size == 1024
    assert r.error == ""


def test_conversion_result_repr_ok():
    r = ConversionResult(True, "/a.txt", "/b.pdf")
    assert "OK" in repr(r)


def test_conversion_result_repr_err():
    r = ConversionResult(False, "/a.txt", "", error="not found")
    assert "ERR" in repr(r)
    assert "not found" in repr(r)


def test_category_map_completeness():
    """All dispatch keys should have a category."""
    engine = AdvancedConverterEngine()
    for key in engine._DISPATCH:
        assert key in CATEGORY_MAP, f"{key} has no category"


def test_dispatch_returns_method_and_ext():
    engine = AdvancedConverterEngine()
    method, ext = engine._DISPATCH["txt_to_pdf"]
    assert method == "_txt_to_pdf"
    assert ext == "pdf"


def test_dispatch_image_types():
    engine = AdvancedConverterEngine()
    assert "image_to_png" in engine._DISPATCH
    assert "image_to_jpeg" in engine._DISPATCH
    assert "image_to_ico" in engine._DISPATCH
    assert "image_to_svg" in engine._DISPATCH


def test_dispatch_audio_types():
    engine = AdvancedConverterEngine()
    assert "audio_to_mp3" in engine._DISPATCH
    assert "audio_to_wav" in engine._DISPATCH
    assert "video_to_mp4" in engine._DISPATCH


def test_rtf_parse_colortbl():
    engine = AdvancedConverterEngine()
    raw = r"{\colortbl;\red0\green0\blue0;\red255\green0\blue0;}"
    colors = engine._rtf_parse_colortbl(raw)
    assert len(colors) >= 2
    assert (0, 0, 0) in colors
    assert (255, 0, 0) in colors


def test_rtf_tokenize():
    engine = AdvancedConverterEngine()
    raw = r"{\rtf1\ansi Hello}"
    tokens = engine._rtf_tokenize(raw)
    assert len(tokens) > 0
    token_types = [t[0] for t in tokens]
    assert "{" in token_types
    assert "}" in token_types
