"""Image-to-PDF conversion methods."""

import os
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

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
        if not (hasattr(self, "active_templates") and "images_to_pdf" in self.active_templates):
            _def_id, _ = (self._ensure_template_manager() or object()).get_default_template("Conversion Images→PDF")
            if _def_id:
                (self._ensure_template_manager() or object()).apply_template(_def_id, self)
        if hasattr(self, "active_templates") and "images_to_pdf" in self.active_templates:
            self.config["separate_image_pdfs"] = self.active_templates["images_to_pdf"].get("separate", False)

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
                self.translate_text("Avertissement"),
                self.translate_text("Aucun fichier image compatible sélectionné ou dans la liste."),
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

    def _configure_scanlayer(self):
        """Resolve Tesseract and configure scanlayer.

        Returns (tesseract_path, orientation) where orientation is None
        (auto), "none", or a float angle in degrees (custom value).
        """
        import scanlayer

        from external_binaries import resolve_binary

        tesseract = resolve_binary("tesseract")
        if tesseract:
            scanlayer.configure(tesseract_cmd=tesseract)

        self._suppress_tesseract_console()

        orientation = self._ocr_orientation_value()
        return tesseract, orientation

    @staticmethod
    def _suppress_tesseract_console():
        """Prevent tesseract.exe console windows from flashing in the GUI app.

        In a console=False PyInstaller app the parent has no console, so any
        spawn of tesseract.exe (a console-subsystem binary) can briefly create
        a visible console window. pytesseract only hides the OCR path via
        STARTUPINFO/SW_HIDE and leaves its one-off probes (get_languages /
        get_tesseract_version) unhidden. This patches subprocess.Popen
        globally so that every spawn of the Tesseract executable is forced to
        run with CREATE_NO_WINDOW, regardless of the caller.
        """
        import os
        import subprocess
        import sys

        if sys.platform != "win32":
            return
        if not hasattr(subprocess, "CREATE_NO_WINDOW"):
            return

        try:
            _orig_popen = subprocess.Popen
            _no_window = subprocess.CREATE_NO_WINDOW

            def _popen_hidden(cmd, *args, **kwargs):
                exe = cmd[0] if isinstance(cmd, (list, tuple)) and cmd else None
                if isinstance(exe, str):
                    base = os.path.basename(exe).lower()
                    if base in ("tesseract", "tesseract.exe", "tesseract.exe.exe"):
                        flags = kwargs.get("creationflags", 0) or 0
                        kwargs["creationflags"] = flags | _no_window
                return _orig_popen(cmd, *args, **kwargs)

            subprocess.Popen = _popen_hidden
        except Exception:
            pass

    def _ocr_orientation_value(self):
        """Map the ocr_orientation config string to the scanlayer orientation.

        "auto" -> None (auto-detect), "none"/empty -> "none" (disabled),
        otherwise -> float angle in degrees.
        """
        raw = self.config.get("ocr_orientation", "auto")
        if isinstance(raw, bool) or raw is None:
            return "none" if raw is False or raw is None else None
        value = str(raw).strip()
        if not value or value == "auto":
            return None
        if value == "none":
            return "none"
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _single_image_to_generic_pdf(self, file_path: str, output_file: str) -> None:
        """Embed a single image into a plain (non-OCR) PDF using PyMuPDF."""
        import fitz

        pdf_document = fitz.open()
        img = fitz.open(file_path)
        rect = img[0].rect
        page = pdf_document.new_page(width=rect.width, height=rect.height)
        page.insert_image(rect, filename=file_path)
        img.close()
        pdf_document.save(output_file)
        pdf_document.close()

    def _image_ocr_able(self, file_path: str, output_file: str, orientation) -> bool:
        """OCR a single image into *output_file*.

        Returns True if the image was OCR-able (text found); otherwise False,
        in which case *output_file* may be left empty or missing and the caller
        should regenerate it with the generic embedder.
        """
        import scanlayer

        try:
            result = scanlayer.convert(
                input_path=file_path,
                output_path=output_file,
                orientation=orientation,
                force=True,
            )
            words = getattr(result, "words_count", 0)
            return bool(words)
        except Exception as e:
            print(f"OCR failed for {file_path}, falling back to plain PDF: {e}")
            return False

    def _image_to_pdf_with_ocr_fallback(self, file_path: str, output_file: str, orientation) -> bool:
        """Convert one image to PDF, using OCR when possible else plain embed.

        Returns True if OCR produced text, False if a plain embed was used.
        """
        if self._image_ocr_able(file_path, output_file, orientation):
            return True
        self._single_image_to_generic_pdf(file_path, output_file)
        return False

    def ocr_convert_images_to_separate_pdfs(self, image_files: list[str], selected_items: list) -> None:
        """Convert each image into a separate searchable PDF using OCR.

        Images that are not OCR-able fall back to a plain image embedding.
        """
        num_images = len(image_files)
        output_dir = self.get_output_directory()
        if not output_dir:
            return

        _, orientation = self._configure_scanlayer()

        self.show_progress(True, self.translate_text("conversion_images_to_separate_pdfs").format(num_images))
        success_count = 0
        ocr_pages = 0
        start_time = datetime.now()

        for i, file_path in enumerate(image_files):
            try:
                output_file = os.path.join(output_dir, f"{Path(file_path).stem}.pdf")
                if not self._image_ocr_able(file_path, output_file, orientation):
                    self._single_image_to_generic_pdf(file_path, output_file)
                else:
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
                print(f"OCR conversion error {file_path}: {e}")

        self.achievement_system.record_ocr_usage(ocr_pages)
        self.show_progress(False)
        if self.config.get("enable_system_notifications", True):
            self.system_notifier.send("image_to_pdf_s")
        QMessageBox.information(
            self,
            self.translate_text("Succès"),
            self.translate_text("images_converted_separate").format(
                success_count=success_count, num_images=num_images, output_dir=output_dir
            ),
        )

    def ocr_convert_images_to_merged_pdf(self, image_files: list[str], selected_items: list) -> None:
        """Merge images into a single searchable PDF using OCR.

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

                self._merge_images_with_ocr_to_pdf(image_files, output_file, orientation)

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
                self.show_progress(False)
                if self.config.get("enable_system_notifications", True):
                    self.system_notifier.send("image_to_pdf")
                QMessageBox.information(
                    self,
                    self.translate_text("Succès"),
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
                    self.translate_text("Succès"),
                    self.translate_text("image_to_pdf_success").format(time=round(conversion_time, 1)),
                )
        except Exception as e:
            self.show_progress(False)
            QMessageBox.critical(
                self, self.translate_text("Erreur"), self.translate_text("error_conversion_fusion").format(error=str(e))
            )

    def _merge_images_with_ocr_to_pdf(self, image_files: list[str], output_file: str, orientation) -> None:
        """Build a multi-page PDF, OCR-ing each image when possible."""
        import shutil
        import tempfile

        import fitz

        self.show_progress(True, self.translate_text(f"Traitement de {len(image_files)} image(s)..."))
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
            self.achievement_system.record_ocr_usage(ocr_pages)
            merged.save(output_file)
        finally:
            merged.close()
            shutil.rmtree(temp_dir, ignore_errors=True)

    def convert_images_to_separate_pdfs(self, image_files: list[str], selected_items: list) -> None:
        """Convert each image into a separate PDF in chosen directory."""
        num_images = len(image_files)
        output_dir = self.get_output_directory()
        if not output_dir:
            return

        self.show_progress(True, self.translate_text("conversion_images_to_separate_pdfs").format(num_images))
        success_count = 0
        start_time = datetime.now()

        import fitz

        for i, file_path in enumerate(image_files):
            try:
                output_file = os.path.join(output_dir, f"{Path(file_path).stem}.pdf")
                pdf_document = fitz.open()
                img = fitz.open(file_path)
                rect = img[0].rect
                page = pdf_document.new_page(width=rect.width, height=rect.height)
                page.insert_image(rect, filename=file_path)
                img.close()
                pdf_document.save(output_file)
                pdf_document.close()
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
                print(f"Image conversion error {file_path}: {e}")

        self.show_progress(False)
        if self.config.get("enable_system_notifications", True):
            self.system_notifier.send("image_to_pdf_s")
        QMessageBox.information(
            self,
            self.translate_text("Succès"),
            self.translate_text("images_converted_separate").format(
                success_count=success_count, num_images=num_images, output_dir=output_dir
            ),
        )

    def convert_images_to_merged_pdf(self, image_files: list[str], selected_items: list) -> None:
        """Merge images into a single PDF (or single image to PDF)."""
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

                images = []
                for i, file_path in enumerate(image_files):
                    try:
                        img = self._open_image_for_pdf(file_path)
                        images.append(img)
                        self.progress_bar.setValue(int((i + 1) / num_images * 50))
                    except Exception as e:
                        print(f"Image loading error {file_path}: {e}")

                if not images:
                    self.show_progress(False)
                    return

                first_image = images[0]
                if len(images) > 1:
                    first_image.save(
                        output_file, format="PDF", save_all=True, append_images=images[1:], resolution=100.0
                    )
                else:
                    first_image.save(output_file, format="PDF", resolution=100.0)

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
                self.show_progress(False)
                if self.config.get("enable_system_notifications", True):
                    self.system_notifier.send("image_to_pdf")
                QMessageBox.information(
                    self,
                    self.translate_text("Succès"),
                    self.translate_text("images_merged_success").format(
                        num_images=num_images, conversion_time=round(conversion_time, 1)
                    ),
                )

            elif num_images == 1:
                file_path = image_files[0]
                output_file = self.get_output_directory(f"{Path(file_path).stem}.pdf")
                if not output_file:
                    self.show_progress(False)
                    return
                img = self._open_image_for_pdf(file_path)
                img.save(output_file, format="PDF")
                file_size = os.path.getsize(file_path)
                self.achievement_system.record_conversion("image_to_pdf", file_size, True)
                self.show_progress(False)
                conversion_time = (datetime.now() - start_time).total_seconds()
                if self.config.get("enable_system_notifications", True):
                    self.system_notifier.send("image_to_pdf")
                QMessageBox.information(
                    self,
                    self.translate_text("Succès"),
                    self.translate_text("image_to_pdf_success").format(time=round(conversion_time, 1)),
                )
        except Exception as e:
            self.show_progress(False)
            QMessageBox.critical(
                self, self.translate_text("Erreur"), self.translate_text("error_conversion_fusion").format(error=str(e))
            )

    def _open_image_for_pdf(self, file_path: str):
        """Open image as PIL Image for PDF conversion."""
        from PIL import Image

        return Image.open(file_path)
