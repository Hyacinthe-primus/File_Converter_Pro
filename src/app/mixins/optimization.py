"""OptimizationMixin - office file optimization methods.

Routes files to the right per-format strategy (see optimize_office_files).
Format-specific logic lives in:
- pdf_optimizer: PDF (Ghostscript › PyMuPDF › pikepdf)
- office_optimizer: Word/PowerPoint/Excel
- media_optimizer: audio/video via ffmpeg
- web_optimizer: json/html
- epub_optimizer: EPUB
- image_optimizer: images via Pillow
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from app.mixins.epub_optimizer import EpubOptimizerMixin
from app.mixins.image_optimizer import ImageOptimizerMixin
from app.mixins.media_optimizer import MediaOptimizerMixin
from app.mixins.office_optimizer import OfficeDocOptimizerMixin
from app.mixins.pdf_optimizer import PdfOptimizerMixin
from app.mixins.web_optimizer import WebOptimizerMixin


class OptimizationMixin(
    PdfOptimizerMixin,
    OfficeDocOptimizerMixin,
    MediaOptimizerMixin,
    WebOptimizerMixin,
    EpubOptimizerMixin,
    ImageOptimizerMixin,
):
    """Mixin: office file optimization methods for FileConverterApp."""

    def optimize_office_files(
        self, office_files, optimization_type, quality_level, remove_metadata, compress_images, keep_backup
    ):
        if hasattr(self, "active_templates") and "office_optimization" in self.active_templates:
            del self.active_templates["office_optimization"]
        """Optimize office and image files"""
        output_dir = self.get_output_directory()
        if not output_dir:
            return

        IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp", ".gif"}
        EXCEL_EXTS = {".xlsx", ".xls"}
        AUDIO_EXTS = {".mp3", ".wav", ".aac", ".flac", ".ogg"}
        VIDEO_EXTS = {".mp4", ".avi", ".mkv", ".mov", ".webm"}
        WEB_EXTS = {".json", ".html", ".htm"}
        EPUB_EXTS = {".epub"}

        self.show_progress(True, self.translate_text("len_off").format(len(office_files)))

        success_count = 0
        total_original_size = 0
        total_compressed_size = 0
        start_time = datetime.now()

        for i, file_path in enumerate(office_files):
            try:
                file_ext = Path(file_path).suffix.lower()
                original_size = os.path.getsize(file_path)
                total_original_size += original_size

                if keep_backup:
                    output_file = os.path.join(output_dir, f"optimized_{Path(file_path).name}")
                else:
                    output_file = file_path

                operation_start = datetime.now()

                if quality_level == 0:
                    compression_level = "high"
                elif quality_level == 1:
                    compression_level = "normal"
                elif quality_level == 2:
                    compression_level = "very_reduced"

                if file_ext == ".pdf":
                    success = self.optimize_pdf_file(
                        file_path, output_file, compression_level, remove_metadata, compress_images
                    )
                elif file_ext in [".docx", ".doc"]:
                    success = self.optimize_word_file(
                        file_path, output_file, compression_level, remove_metadata, compress_images
                    )
                elif file_ext in [".pptx", ".ppt"]:
                    success = self.optimize_powerpoint_file(
                        file_path, output_file, compression_level, remove_metadata, compress_images
                    )
                elif file_ext in EXCEL_EXTS:
                    success = self.optimize_excel_file(file_path, output_file, compression_level, remove_metadata)
                elif file_ext in IMAGE_EXTS:
                    success = self.optimize_image_file(file_path, output_file, quality_level)
                elif file_ext in AUDIO_EXTS:
                    success = self.optimize_av_file(file_path, output_file, quality_level, "audio")
                elif file_ext in VIDEO_EXTS:
                    success = self.optimize_av_file(file_path, output_file, quality_level, "video")
                elif file_ext in WEB_EXTS:
                    success = self.optimize_web_file(file_path, output_file, file_ext)
                elif file_ext in EPUB_EXTS:
                    success = self.optimize_epub_file(file_path, output_file, compress_images, quality_level)
                else:
                    success = False

                if success:
                    compressed_size = os.path.getsize(output_file) if os.path.exists(output_file) else original_size
                    total_compressed_size += compressed_size
                    operation_time = (datetime.now() - operation_start).total_seconds()
                    self.db_manager.add_conversion_record(
                        source_file=file_path,
                        source_format=file_ext.upper().replace(".", ""),
                        target_file=output_file,
                        target_format=file_ext.upper().replace(".", ""),
                        operation_type="office_optimization",
                        file_size=original_size,
                        conversion_time=operation_time,
                        success=True,
                        notes=f"Type: {optimization_type}, Quality: {quality_level}",
                    )
                    success_count += 1
                self.progress_bar.setValue(int((i + 1) / len(office_files) * 100))
            except Exception as e:
                self.db_manager.add_conversion_record(
                    source_file=file_path,
                    source_format=Path(file_path).suffix.upper().replace(".", ""),
                    target_file="",
                    target_format="",
                    operation_type="office_optimization",
                    file_size=0,
                    conversion_time=0,
                    success=False,
                    notes=f"Error: {str(e)}",
                )
                print(f"Optimization error {file_path}: {e}")

        total_time = (datetime.now() - start_time).total_seconds()
        self.show_progress(False)

        if total_original_size > 0:
            compression_rate = (total_original_size - total_compressed_size) / total_original_size * 100
            savings_mb = (total_original_size - total_compressed_size) / (1024 * 1024)
            message = self.translate_text("msg_1").format(success_count, len(office_files), f"{total_time:.1f}")
            message += self.translate_text("msg_2").format(f"{savings_mb:.2f}", f"{compression_rate:.1f}")
            message += self.translate_text("msg_3").format(output_dir)
        else:
            message = self.translate_text("msg_4").format(success_count, len(office_files))
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(self, self.translate_text("Succès"), self.translate_text(message))
