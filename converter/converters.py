"""
Advanced Converter Engine
converter/converters.py

Routing is driven by a dispatch table (converter/registry.py). Types with
several engines carry an ordered fallback chain — the first engine that
returns success (not False) and writes a non-empty output file wins.

  HTML → PDF  : pdfkit/wkhtmltopdf › weasyprint › reportlab
  EPUB → PDF  : pypandoc › native spine-order engine
  RTF  → PDF  : native RTF renderer › internal parser
  XLSX → PDF  : MS Office COM › openpyxl + reportlab
  PPTX → PDF  : MS Office COM › native renderer › python-pptx + reportlab
  PDF  → HTML : PyMuPDF (fitz) dict-mode
  TXT  → PDF  : reportlab
  Images      : Pillow (HEIC pillow-heif · RAW rawpy · PSD psd_tools · ImageMagick)
  Audio/Video : ffmpeg quality presets per format
"""

from __future__ import annotations

import os
import time

from converter.helpers import ConversionResult, _build_dst
from converter.mixins import (
    DocumentConverters,
    EpubRenderers,
    HtmlRenderers,
    ImageConverters,
    MediaConverters,
    OfficeComConverters,
    PdfRenderers,
    PptxNativeConverters,
    RtfNativeConverters,
)
from converter.registry import CATEGORY_MAP as CATEGORY_MAP
from converter.registry import DISPATCH


class AdvancedConverterEngine(
    DocumentConverters,
    ImageConverters,
    MediaConverters,
    OfficeComConverters,
    RtfNativeConverters,
    PptxNativeConverters,
    HtmlRenderers,
    PdfRenderers,
    EpubRenderers,
):
    """Entry point: dispatch table plus convert/convert_batch routing."""

    _DISPATCH = DISPATCH

    _SIG_WITH_TYPE = ("_image_convert", "_ffmpeg_convert", "_heic_convert", "_raw_convert")

    def convert(self, conversion_type, src, dst_dir):
        if conversion_type not in self._DISPATCH:
            return ConversionResult(False, src, "", error=f"Unknown type: {conversion_type}")
        spec, ext = self._DISPATCH[conversion_type]
        engine_names = spec if isinstance(spec, tuple) else (spec,)
        dst = _build_dst(src, dst_dir, ext)
        file_size = os.path.getsize(src) if os.path.exists(src) else 0
        errors = []
        for index, engine_name in enumerate(engine_names):
            engine = getattr(self, engine_name, None)
            if engine is None:
                errors.append(f"{engine_name}: engine not available")
                continue
            try:
                if engine_name in self._SIG_WITH_TYPE:
                    ok, elapsed = self._run_engine(engine, src, dst, conversion_type)
                else:
                    ok, elapsed = self._run_engine(engine, src, dst)
            except Exception as exc:
                errors.append(f"{engine_name}: {exc}")
                continue
            if ok is False or not self._engine_produced_output(dst):
                errors.append(f"{engine_name}: produced no output")
                continue
            return ConversionResult(
                True,
                src,
                dst,
                elapsed=elapsed,
                file_size=file_size,
                engine_used=engine_name,
                degraded=index > 0,
            )
        detail = "; ".join(errors) if errors else "no engines configured"
        return ConversionResult(False, src, dst, error=f"All engines failed ({detail})", file_size=file_size)

    @staticmethod
    def _run_engine(engine, src, dst, conversion_type=None):
        """Run a single engine, returning (result, elapsed_seconds)."""
        t0 = time.perf_counter()
        if conversion_type is None:
            result = engine(src, dst)
        else:
            result = engine(src, dst, conversion_type)
        return result, time.perf_counter() - t0

    @staticmethod
    def _engine_produced_output(dst):
        """An engine only counts as successful if it wrote a real file."""
        return os.path.isfile(dst) and os.path.getsize(dst) > 0

    def convert_batch(self, conversion_type, sources, dst_dir, progress_cb=None):
        results = []
        for i, src in enumerate(sources, 1):
            result = self.convert(conversion_type, src, dst_dir)
            results.append(result)
            if progress_cb:
                progress_cb(i, len(sources), src)
        return results
