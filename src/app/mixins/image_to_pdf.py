"""Image-to-PDF conversion methods."""

import os
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from converter.helpers import BackupError, prepare_operation_backups
from templates import semantic_keys as sk
from utils.pdf_artifacts import run_pdf_engine_with_artifact_validation

IMAGE_EXTENSIONS = (
    ".png",
    ".jpeg",
    ".jpg",
    ".bmp",
    ".heic",
    ".heif",
    ".gif",
    ".jpx",
    ".webp",
    ".tiff",
    ".tif",
    ".psd",
    ".svg",
    ".avif",
    ".j2k",
    ".jp2",
    ".dng",
    ".cr2",
    ".cr3",
    ".nef",
    ".arw",
    ".orf",
    ".rw2",
    ".raf",
    ".jfif",
)


class ImageToPdfMixin:
    """Image-to-PDF conversion for FileConverterApp."""

    def convert_images_to_pdf(self) -> None:
        """Route to separate or merged PDF based on config."""
        if not (hasattr(self, "active_templates") and sk.IMAGES_TO_PDF in self.active_templates):
            _def_id, _ = (self._ensure_template_manager() or object()).get_default_template(sk.IMAGES_TO_PDF)
            if _def_id:
                (self._ensure_template_manager() or object()).apply_template(_def_id, self)
        if hasattr(self, "active_templates") and sk.IMAGES_TO_PDF in self.active_templates:
            self.config["separate_image_pdfs"] = self.active_templates[sk.IMAGES_TO_PDF].get("separate", False)

        selected_items = self.files_list_widget.selectedItems()
        files_to_process = []
        if selected_items:
            for i in range(self.files_list_widget.count()):
                item = self.files_list_widget.item(i)
                if item.isSelected():
                    files_to_process.append(item.data(Qt.UserRole))
        else:
            files_to_process = self.files_list

        image_files = [f for f in files_to_process if f.lower().endswith(IMAGE_EXTENSIONS)]
        if not image_files:
            QMessageBox.warning(
                self,
                self.translate_text("warning"),
                self.translate_text("no_compatible_image_file_selected_or_in_the_list"),
            )
            return

        for file_path in image_files:
            ext = Path(file_path).suffix.lower().lstrip(".")
            if ext == "jpeg":
                ext = "jpg"
            if ext in ["jpg", "png"]:
                self.achievement_system.mark_format_as_used(ext)
        self.achievement_system.mark_format_as_used("pdf")

        separate_mode = self.config.get("separate_image_pdfs", False)
        if separate_mode:
            if self._ocr_active():
                self.ocr_convert_images_to_separate_pdfs(image_files, selected_items)
            else:
                self.convert_images_to_separate_pdfs(image_files, selected_items)
        else:
            if self._ocr_active():
                self.ocr_convert_images_to_merged_pdf(image_files, selected_items)
            else:
                self.convert_images_to_merged_pdf(image_files, selected_items)

    def _ocr_active(self) -> bool:
        """Whether OCR should be attempted for the current image->PDF conversion.

        OCR runs only when the per-conversion OCR checkbox is checked. Images
        that fail OCR (no text found or an error) fall back to a plain
        image embedding.
        """
        return getattr(self, "ocr_checkbox", None) is not None and self.ocr_checkbox.isChecked()

    def _prepare_image_source_backups(self, image_files: list[str]) -> bool:
        try:
            prepare_operation_backups(image_files, config=getattr(self, "config", None))
        except BackupError as exc:
            QMessageBox.critical(self, self.translate_text("error"), str(exc))
            return False
        return True

    def _configure_scanlayer(self):
        """Resolve Tesseract and configure scanlayer.

        Returns (tesseract_path, orientation) where orientation is None
        (auto), "none", or a float angle in degrees (custom value).
        """
        from tasks.ocr_helpers import configure_scanlayer

        return configure_scanlayer(
            self.config.get("ocr_orientation", "auto"),
            include_tesseract=True,
        )

    def _single_image_to_generic_pdf(self, file_path: str, output_file: str) -> None:
        """Embed a single image into a plain (non-OCR) PDF using PyMuPDF."""
        from tasks.ocr_helpers import embed_image_in_pdf

        embed_image_in_pdf(file_path, output_file)

    def _image_ocr_able(self, file_path: str, output_file: str, orientation) -> bool:
        """OCR a single image into *output_file*.

        Returns True if the image was OCR-able (text found); otherwise False,
        in which case *output_file* may be left empty or missing and the caller
        should regenerate it with the generic embedder.
        """
        from tasks.ocr_helpers import image_ocr_able

        return image_ocr_able(file_path, output_file, orientation)

    def _image_to_pdf_with_ocr_fallback(self, file_path: str, output_file: str, orientation) -> bool:
        """Convert one image to PDF, using OCR when possible else plain embed.

        Returns True if OCR produced text, False if a plain embed was used.
        """
        from tasks.ocr_helpers import image_to_pdf

        return image_to_pdf(file_path, output_file, orientation)

    def ocr_convert_images_to_separate_pdfs(self, image_files: list[str], selected_items: list) -> None:
        """Convert each image into a separate searchable PDF using OCR.

        Images that are not OCR-able fall back to a plain image embedding.
        """
        num_images = len(image_files)
        output_dir = self.get_output_directory()
        if not output_dir:
            return
        if not self._prepare_image_source_backups(image_files):
            return

        _, orientation = self._configure_scanlayer()

        self.show_progress(True, self.translate_text("conversion_images_to_separate_pdfs").format(num_images))
        success_count = 0
        ocr_pages = 0
        failures = []
        start_time = datetime.now()

        for i, file_path in enumerate(image_files):
            try:
                output_file = os.path.join(output_dir, f"{Path(file_path).stem}.pdf")
                if self._image_to_pdf_with_ocr_fallback(file_path, output_file, orientation):
                    ocr_pages += 1
                file_size = os.path.getsize(file_path)
                self.db_manager.add_conversion_record(
                    source_file=file_path,
                    source_format=Path(file_path).suffix.upper().replace(".", ""),
                    target_file=output_file,
                    target_format="PDF",
                    operation_type="image_to_pdf_s",
                    file_size=file_size,
                    conversion_time=(datetime.now() - start_time).total_seconds(),
                    success=True,
                )
                self.achievement_system.record_conversion("image_to_pdf", file_size, True)
                success_count += 1
                self.progress_bar.setValue(int((i + 1) / num_images * 100))
            except Exception as e:
                failures.append((Path(file_path).name, str(e)))
                print(f"OCR conversion error {file_path}: {e}")

        self.achievement_system.record_ocr_usage(ocr_pages)
        self.show_progress(False)
        if success_count > 0:
            self.record_config_usage(sk.IMAGES_TO_PDF, {"separate": True})
            if self.config.get("enable_system_notifications", True):
                self.system_notifier.send("image_to_pdf_s")
        message = self.translate_text("images_converted_separate").format(
            success_count=success_count, num_images=num_images, output_dir=output_dir
        )
        if failures:
            failure_lines = [
                self.translate_text("error_with_file").format(filename=name, error=error)
                for name, error in failures
            ]
            failure_text = message + "\n\n" + "\n".join(failure_lines)
            if success_count:
                QMessageBox.warning(self, self.translate_text("warning"), failure_text)
            else:
                QMessageBox.critical(self, self.translate_text("error"), failure_text)
            return
        QMessageBox.information(self, self.translate_text("success"), message)

    def ocr_convert_images_to_merged_pdf(self, image_files: list[str], selected_items: list) -> None:
        """Merge images into a single searchable PDF using OCR.

        Page order follows ``image_files`` (the user-maintained main-list order).

        Images that are not OCR-able are embedded as plain pages in the merged
        PDF instead.
        """
        num_images = len(image_files)
        start_time = datetime.now()

        _, orientation = self._configure_scanlayer()

        try:
            if num_images >= 2:
                default_filename = f"fusion_images_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                output_file = self.get_output_directory(default_filename)
                if not output_file:
                    self.show_progress(False)
                    return
                if not self._prepare_image_source_backups(image_files):
                    self.show_progress(False)
                    return

                from utils.conversion_pipeline import run_conversion_pipeline
                from utils.pdf_artifacts import validate_pdf_artifact

                ocr_pages = 0

                def _run_ocr_merge(target):
                    nonlocal ocr_pages
                    ocr_pages = self._merge_images_with_ocr_to_pdf(image_files, target, orientation) or 0
                    return True

                result = run_conversion_pipeline(
                    output_file,
                    [("OCR", _run_ocr_merge)],
                    validate_pdf_artifact,
                    stage_mode="file",
                    staged_prefix="~fcp_ocr_",
                    staged_suffix=".pdf",
                    include_engine_labels=False,
                )
                if not result.success:
                    raise RuntimeError(f"OCR merge failed: {result.error}")
                self.achievement_system.record_ocr_usage(ocr_pages)

                conversion_time = (datetime.now() - start_time).total_seconds()
                total_size = sum(os.path.getsize(f) for f in image_files if os.path.exists(f))
                self.db_manager.add_conversion_record(
                    source_file=", ".join([Path(f).name for f in image_files]),
                    source_format="Image",
                    target_file=output_file,
                    target_format="PDF",
                    operation_type="image_to_pdf",
                    file_size=total_size,
                    conversion_time=conversion_time,
                    success=True,
                )
                self.achievement_system.record_conversion("image_to_pdf", total_size, True)
                self.record_config_usage(sk.IMAGES_TO_PDF, {"separate": False})
                self.show_progress(False)
                if self.config.get("enable_system_notifications", True):
                    self.system_notifier.send("image_to_pdf")
                QMessageBox.information(
                    self,
                    self.translate_text("success"),
                    self.translate_text("images_merged_success").format(
                        num_images=num_images, conversion_time=round(conversion_time, 1)
                    ),
                )

            elif num_images == 1:
                self.show_progress(True, self.translate_text(f"Traitement de {num_images} image(s)..."))
                file_path = image_files[0]
                output_file = self.get_output_directory(f"{Path(file_path).stem}.pdf")
                if not output_file:
                    self.show_progress(False)
                    return
                if not self._prepare_image_source_backups([file_path]):
                    self.show_progress(False)
                    return
                ocr_pages = 1 if self._image_to_pdf_with_ocr_fallback(file_path, output_file, orientation) else 0
                file_size = os.path.getsize(file_path)
                self.achievement_system.record_conversion("image_to_pdf", file_size, True)
                self.achievement_system.record_ocr_usage(ocr_pages)
                self.show_progress(False)
                conversion_time = (datetime.now() - start_time).total_seconds()
                if self.config.get("enable_system_notifications", True):
                    self.system_notifier.send("image_to_pdf")
                QMessageBox.information(
                    self,
                    self.translate_text("success"),
                    self.translate_text("image_to_pdf_success").format(time=round(conversion_time, 1)),
                )
        except Exception as e:
            self.show_progress(False)
            QMessageBox.critical(
                self, self.translate_text("error"), self.translate_text("error_conversion_fusion").format(error=str(e))
            )

    # scanlayer's maximum for parallel pages in a merge (it also caps by CPU count and page count)
    OCR_MERGE_WORKERS = 4

    def _merge_images_with_ocr_to_pdf(self, image_files: list[str], output_file: str, orientation) -> int | None:
        """Build a multi-page PDF, OCR-ing each image when possible.

        Fast path: scanlayer's own merge, which OCRs up to OCR_MERGE_WORKERS pages
        at the same time (typically 15-35% faster; the output is identical). If it
        cannot handle the batch, for example one page is in a format scanlayer
        cannot read, fall back to one-page-at-a-time, where such a page is
        embedded as a plain image without OCR.

        Returns the number of pages that received OCR text. The caller records
        achievement usage only after the final PDF is validated and committed.
        """
        self.show_progress(True, self.translate_text(f"Traitement de {len(image_files)} image(s)..."))
        ocr_pages = self._merge_images_with_ocr_parallel(image_files, output_file, orientation)
        if ocr_pages is not None:
            return ocr_pages
        return self._merge_images_with_ocr_sequential(image_files, output_file, orientation)

    @staticmethod
    def _run_off_ui_thread(fn):
        """Run a blocking call in a worker thread while the UI keeps repainting."""
        from concurrent.futures import ThreadPoolExecutor

        from PySide6.QtCore import QEventLoop, QTimer

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(fn)
            loop = QEventLoop()
            timer = QTimer()
            timer.setInterval(50)
            timer.timeout.connect(lambda: loop.quit() if future.done() else None)
            timer.start()
            if not future.done():
                loop.exec()
            timer.stop()
            return future.result()

    def _merge_images_with_ocr_parallel(self, image_files: list[str], output_file: str, orientation) -> int | None:
        """Merge with scanlayer.convert_merge(workers=...). Returns page count or None to fall back."""
        import contextlib

        import fitz
        import scanlayer

        from utils.image_formats import decodable_image_path

        try:
            with contextlib.ExitStack() as stack:
                # PyMuPDF/Tesseract cannot read HEIC/AVIF, so those go in as temporary PNGs
                readable = [stack.enter_context(decodable_image_path(f)) for f in image_files]
                self.progress_bar.setRange(0, 0)  # busy: scanlayer reports no per-page progress
                self._set_ui_enabled(False)
                try:
                    self._run_off_ui_thread(
                        lambda: scanlayer.convert_merge(
                            readable,
                            output_file,
                            orientation=orientation,
                            force=True,  # blank/no-text pages are kept, as in the sequential path
                            workers=self.OCR_MERGE_WORKERS,
                        )
                    )
                finally:
                    self._set_ui_enabled(True)
                    self.progress_bar.setRange(0, 100)
            # pages that received a text layer are the pages OCR actually read
            with fitz.open(output_file) as merged:
                ocr_pages = sum(1 for page in merged if page.get_text().strip())
        except Exception as e:
            print(f"Parallel OCR merge failed, falling back to page-by-page: {e}")
            with contextlib.suppress(OSError):
                os.remove(output_file)
            return None

        self.progress_bar.setValue(100)
        return ocr_pages

    def _merge_images_with_ocr_sequential(self, image_files: list[str], output_file: str, orientation) -> int:
        """One page at a time; pages OCR cannot handle are embedded as plain images."""
        import shutil
        import tempfile

        import fitz

        merged = fitz.open()
        temp_dir = tempfile.mkdtemp(prefix="fcp_ocr_merge_")
        ocr_pages = 0
        try:
            for i, file_path in enumerate(image_files):
                page_pdf = os.path.join(temp_dir, f"page_{i}.pdf")
                if self._image_ocr_able(file_path, page_pdf, orientation):
                    ocr_pages += 1
                else:
                    self._single_image_to_generic_pdf(file_path, page_pdf)
                src = fitz.open(page_pdf)
                merged.insert_pdf(src)
                src.close()
                self.progress_bar.setValue(int((i + 1) / len(image_files) * 100))
            merged.save(output_file)
        finally:
            merged.close()
            shutil.rmtree(temp_dir, ignore_errors=True)
        return ocr_pages

    def convert_images_to_separate_pdfs(self, image_files: list[str], selected_items: list) -> None:
        """Convert each image into a separate PDF in chosen directory."""
        num_images = len(image_files)
        output_dir = self.get_output_directory()
        if not output_dir:
            return
        if not self._prepare_image_source_backups(image_files):
            return

        self.show_progress(True, self.translate_text("conversion_images_to_separate_pdfs").format(num_images))
        success_count = 0
        failures = []
        start_time = datetime.now()

        from context_menu.conversion_helpers import _convert_image_to_pdf

        for i, file_path in enumerate(image_files):
            try:
                output_file = os.path.join(output_dir, f"{Path(file_path).stem}.pdf")
                _convert_image_to_pdf(file_path, output_dir)
                file_size = os.path.getsize(file_path)
                self.db_manager.add_conversion_record(
                    source_file=file_path,
                    source_format=Path(file_path).suffix.upper().replace(".", ""),
                    target_file=output_file,
                    target_format="PDF",
                    operation_type="image_to_pdf_s",
                    file_size=file_size,
                    conversion_time=(datetime.now() - start_time).total_seconds(),
                    success=True,
                )
                self.achievement_system.record_conversion("image_to_pdf", file_size, True)
                success_count += 1
                self.progress_bar.setValue(int((i + 1) / num_images * 100))
            except Exception as e:
                failures.append((Path(file_path).name, str(e)))
                print(f"Image conversion error {file_path}: {e}")

        self.show_progress(False)
        if success_count > 0:
            self.record_config_usage(sk.IMAGES_TO_PDF, {"separate": True})
            if self.config.get("enable_system_notifications", True):
                self.system_notifier.send("image_to_pdf_s")

        message = self.translate_text("images_converted_separate").format(
            success_count=success_count, num_images=num_images, output_dir=output_dir
        )
        if failures:
            failure_lines = [
                self.translate_text("error_with_file").format(filename=name, error=error)
                for name, error in failures
            ]
            failure_text = message + "\n\n" + "\n".join(failure_lines)
            if success_count:
                QMessageBox.warning(self, self.translate_text("warning"), failure_text)
            else:
                QMessageBox.critical(self, self.translate_text("error"), failure_text)
            return
        QMessageBox.information(self, self.translate_text("success"), message)

    def convert_images_to_merged_pdf(self, image_files: list[str], selected_items: list) -> None:
        """Merge images into a single PDF (or single image to PDF).

        Page order follows ``image_files`` (the user-maintained main-list order).
        """
        num_images = len(image_files)
        is_merge = num_images >= 2
        start_time = datetime.now()

        try:
            self.show_progress(True, self.translate_text(f"Traitement de {num_images} image(s)..."))

            if is_merge:
                default_filename = f"fusion_images_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                output_file = self.get_output_directory(default_filename)
                if not output_file:
                    self.show_progress(False)
                    return
                if not self._prepare_image_source_backups(image_files):
                    self.show_progress(False)
                    return

                images = []
                loaded_files = []
                failures = []
                for i, file_path in enumerate(image_files):
                    try:
                        img = self._open_image_for_pdf(file_path)
                        images.append(img)
                        loaded_files.append(file_path)
                        self.progress_bar.setValue(int((i + 1) / num_images * 50))
                    except Exception as e:
                        failures.append((Path(file_path).name, str(e)))
                        print(f"Image loading error {file_path}: {e}")

                if not images:
                    failure_lines = [
                        self.translate_text("error_with_file").format(
                            filename=name, error=error
                        )
                        for name, error in failures
                    ]
                    raise RuntimeError(
                        "\n".join(failure_lines) or "No images could be loaded"
                    )

                def _save_merged(target):
                    first_image = images[0]
                    if len(images) > 1:
                        first_image.save(
                            target, format="PDF", save_all=True, append_images=images[1:], resolution=100.0
                        )
                    else:
                        first_image.save(target, format="PDF", resolution=100.0)
                    return True

                success, error = run_pdf_engine_with_artifact_validation(output_file, _save_merged)
                if not success:
                    raise RuntimeError(f"Image to PDF conversion failed: {error}")

                conversion_time = (datetime.now() - start_time).total_seconds()
                total_size = sum(
                    os.path.getsize(f) for f in loaded_files if os.path.exists(f)
                )
                self.db_manager.add_conversion_record(
                    source_file=", ".join([Path(f).name for f in loaded_files]),
                    source_format="Image",
                    target_file=output_file,
                    target_format="PDF",
                    operation_type="image_to_pdf",
                    file_size=total_size,
                    conversion_time=conversion_time,
                    success=True,
                )
                self.achievement_system.record_conversion("image_to_pdf", total_size, True)
                self.record_config_usage(sk.IMAGES_TO_PDF, {"separate": False})
                self.show_progress(False)
                if self.config.get("enable_system_notifications", True):
                    self.system_notifier.send("image_to_pdf")
                success_message = self.translate_text("images_merged_success").format(
                    num_images=len(images),
                    conversion_time=round(conversion_time, 1),
                )
                if failures:
                    failure_lines = [
                        self.translate_text("error_with_file").format(
                            filename=name, error=error
                        )
                        for name, error in failures
                    ]
                    QMessageBox.warning(
                        self,
                        self.translate_text("warning"),
                        success_message + "\n\n" + "\n".join(failure_lines),
                    )
                else:
                    QMessageBox.information(
                        self,
                        self.translate_text("success"),
                        success_message,
                    )

            elif num_images == 1:
                file_path = image_files[0]
                output_file = self.get_output_directory(f"{Path(file_path).stem}.pdf")
                if not output_file:
                    self.show_progress(False)
                    return
                if not self._prepare_image_source_backups([file_path]):
                    self.show_progress(False)
                    return
                img = self._open_image_for_pdf(file_path)

                def _save_single(target):
                    img.save(target, format="PDF")
                    return True

                success, error = run_pdf_engine_with_artifact_validation(output_file, _save_single)
                if not success:
                    raise RuntimeError(f"Image to PDF conversion failed: {error}")
                file_size = os.path.getsize(file_path)
                self.achievement_system.record_conversion("image_to_pdf", file_size, True)
                self.show_progress(False)
                conversion_time = (datetime.now() - start_time).total_seconds()
                if self.config.get("enable_system_notifications", True):
                    self.system_notifier.send("image_to_pdf")
                QMessageBox.information(
                    self,
                    self.translate_text("success"),
                    self.translate_text("image_to_pdf_success").format(time=round(conversion_time, 1)),
                )
        except Exception as e:
            self.show_progress(False)
            QMessageBox.critical(
                self, self.translate_text("error"), self.translate_text("error_conversion_fusion").format(error=str(e))
            )

    def _open_image_for_pdf(self, file_path: str):
        """Open image as PIL Image for PDF conversion."""
        from PIL import Image

        from utils.image_formats import register_heif

        if Path(file_path).suffix.lower() == ".svg":
            import io

            import fitz

            with fitz.open(file_path) as doc:
                png = doc[0].get_pixmap(alpha=True).tobytes("png")
            return Image.open(io.BytesIO(png))

        register_heif()  # Pillow reads by content, so this also covers HEIC saved as .png
        return Image.open(file_path)
