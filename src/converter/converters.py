"""
Advanced Converter Engine
converter/converters.py

Routing is driven by a dispatch table (converter/registry.py). Types with
several engines carry an ordered fallback chain - the first engine that
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
from pathlib import Path

from converter.artifact_validators import validator_for_extension
from converter.helpers import BackupError, ConversionResult, _build_dst, prepare_operation_backups
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
from utils.conversion_pipeline import run_conversion_pipeline


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

    def __init__(self, allow_local_html_resources=False):
        self.allow_local_html_resources = bool(allow_local_html_resources)

    @staticmethod
    def _source_key(src):
        try:
            return os.path.normcase(os.path.realpath(src))
        except Exception:
            return ""

    def convert(self, conversion_type, src, dst_dir, *, skip_backup=False):
        if conversion_type not in self._DISPATCH:
            return ConversionResult(False, src, "", error=f"Unknown type: {conversion_type}")
        spec, ext = self._DISPATCH[conversion_type]
        engine_names = spec if isinstance(spec, tuple) else (spec,)
        dst = _build_dst(src, dst_dir, ext)
        file_size = os.path.getsize(src) if os.path.exists(src) else 0
        if not skip_backup:
            try:
                prepare_operation_backups([src])
            except BackupError as exc:
                return ConversionResult(False, src, dst, error=str(exc), file_size=file_size)
        validator = validator_for_extension(ext)
        staged_name = Path(dst).name
        errors = []
        for index, engine_name in enumerate(engine_names):
            engine = getattr(self, engine_name, None)
            if engine is None:
                errors.append(f"{engine_name}: engine not available")
                continue

            elapsed = 0.0

            def _attempt(target, _engine=engine, _name=engine_name):
                nonlocal elapsed
                if _name in self._SIG_WITH_TYPE:
                    ok, elapsed = self._run_engine(_engine, src, target, conversion_type)
                else:
                    ok, elapsed = self._run_engine(_engine, src, target)
                return ok

            result = run_conversion_pipeline(
                dst,
                [(engine_name, _attempt)],
                validator,
                stage_mode="directory",
                stage_dir_prefix="~fcp_adv_stage_",
                staged_prefix="~fcp_adv_",
                staged_suffix=f".{ext}",
                staged_name=staged_name,
            )
            if result.success:
                return ConversionResult(
                    True,
                    src,
                    dst,
                    elapsed=elapsed,
                    file_size=file_size,
                    engine_used=engine_name,
                    degraded=index > 0,
                )

            detail = result.error or "produced no output"
            if not detail.startswith(f"{engine_name}:"):
                detail = f"{engine_name}: {detail}"
            errors.append(detail)
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

    def convert_batch(self, conversion_type, sources, dst_dir, progress_cb=None):
        source_list = list(sources)
        backup_result = None
        backup_error = ""
        if conversion_type in self._DISPATCH:
            try:
                backup_result = prepare_operation_backups(source_list)
            except BackupError as exc:
                backup_result = exc.result
                backup_error = str(exc)

        backed_keys = set()
        backup_errors = {}
        if backup_result is not None:
            for source in backup_result.backups:
                key = self._source_key(source)
                if key:
                    backed_keys.add(key)
            for source, reason in backup_result.errors.items():
                backup_errors[self._source_key(source)] = f"{source}: {reason}"

        results = []
        for i, src in enumerate(source_list, 1):
            key = self._source_key(src)
            if backup_result is None and backup_error:
                result = ConversionResult(
                    False,
                    src,
                    _build_dst(src, dst_dir, self._DISPATCH[conversion_type][1]),
                    error=backup_error,
                    file_size=os.path.getsize(src) if os.path.exists(src) else 0,
                )
            elif backup_result is not None and backup_result.enabled and key not in backed_keys:
                dst = _build_dst(src, dst_dir, self._DISPATCH[conversion_type][1])
                result = ConversionResult(
                    False,
                    src,
                    dst,
                    error=f"Source backup failed: {backup_errors.get(key, 'source was not backed up')}",
                    file_size=os.path.getsize(src) if os.path.exists(src) else 0,
                )
            else:
                result = self.convert(conversion_type, src, dst_dir, skip_backup=True)
            results.append(result)
            if progress_cb:
                progress_cb(i, len(source_list), src)
        return results
