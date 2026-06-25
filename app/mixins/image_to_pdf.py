"""Image-to-PDF conversion methods."""

import os
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt

IMAGE_EXTENSIONS = (
    '.png', '.jpeg', '.jpg', '.bmp', '.heic', '.heif', '.gif', '.jpx',
    '.webp', '.tiff', '.tif', '.psd', '.svg', '.avif', '.j2k', '.jp2',
    '.dng', '.cr2', '.cr3', '.nef', '.arw', '.orf', '.rw2', '.raf', '.jfif'
)

class ImageToPdfMixin:
    """Image-to-PDF conversion for FileConverterApp."""

    def convert_images_to_pdf(self) -> None:
        """Route to separate or merged PDF based on config."""
        if not (hasattr(self, 'active_templates') and 'images_to_pdf' in self.active_templates):
            _def_id, _ = (self._ensure_template_manager() or object()).get_default_template('Conversion Images→PDF')
            if _def_id:
                (self._ensure_template_manager() or object()).apply_template(_def_id, self)
        if hasattr(self, 'active_templates') and 'images_to_pdf' in self.active_templates:
            self.config['separate_image_pdfs'] = self.active_templates['images_to_pdf'].get('separate', False)

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
            QMessageBox.warning(self, self.translate_text("Avertissement"),
                                self.translate_text("Aucun fichier image compatible sélectionné ou dans la liste."))
            return

        for file_path in image_files:
            ext = Path(file_path).suffix.lower().lstrip('.')
            if ext == 'jpeg':
                ext = 'jpg'
            if ext in ['jpg', 'png']:
                self.achievement_system.mark_format_as_used(ext)
        self.achievement_system.mark_format_as_used("pdf")

        separate_mode = self.config.get("separate_image_pdfs", False)
        if separate_mode:
            self.convert_images_to_separate_pdfs(image_files, selected_items)
        else:
            self.convert_images_to_merged_pdf(image_files, selected_items)

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
                self.db_manager.add_conversion_record(source_file=file_path, source_format=Path(file_path).suffix.upper().replace('.', ''), target_file=output_file, target_format="PDF", operation_type="image_to_pdf_s", file_size=file_size, conversion_time=(datetime.now() - start_time).total_seconds(), success=True)
                self.achievement_system.record_conversion("image_to_pdf", file_size, True)
                success_count += 1
                self.progress_bar.setValue(int((i + 1) / num_images * 100))
            except Exception as e:
                print(f"Image conversion error {file_path}: {e}")

        self.show_progress(False)
        if self.config.get("enable_system_notifications", True):
            self.system_notifier.send("image_to_pdf_s")
        QMessageBox.information(self, self.translate_text("Succès"),
                                self.translate_text("images_converted_separate").format(success_count=success_count, num_images=num_images, output_dir=output_dir))

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
                    first_image.save(output_file, format='PDF', save_all=True, append_images=images[1:], resolution=100.0)
                else:
                    first_image.save(output_file, format='PDF', resolution=100.0)

                conversion_time = (datetime.now() - start_time).total_seconds()
                total_size = sum(os.path.getsize(f) for f in image_files if os.path.exists(f))
                self.db_manager.add_conversion_record(source_file=", ".join([Path(f).name for f in image_files]), source_format="Image", target_file=output_file, target_format="PDF", operation_type="image_to_pdf", file_size=total_size, conversion_time=conversion_time, success=True)
                self.achievement_system.record_conversion("image_to_pdf", total_size, True)
                self.show_progress(False)
                if self.config.get("enable_system_notifications", True):
                    self.system_notifier.send("image_to_pdf")
                QMessageBox.information(self, self.translate_text("Succès"),
                                        self.translate_text("images_merged_success").format(num_images=num_images, conversion_time=conversion_time))

            elif num_images == 1:
                file_path = image_files[0]
                output_file = self.get_output_directory(f"{Path(file_path).stem}.pdf")
                if not output_file:
                    self.show_progress(False)
                    return
                img = self._open_image_for_pdf(file_path)
                img.save(output_file, format='PDF')
                file_size = os.path.getsize(file_path)
                self.achievement_system.record_conversion("image_to_pdf", file_size, True)
                self.show_progress(False)
                if self.config.get("enable_system_notifications", True):
                    self.system_notifier.send("image_to_pdf")
                QMessageBox.information(self, self.translate_text("Succès"),
                                        self.translate_text("image_to_pdf_success").format(time=0))
        except Exception as e:
            self.show_progress(False)
            QMessageBox.critical(self, self.translate_text("Erreur"),
                                 self.translate_text("error_conversion_fusion").format(error=str(e)))

    def _open_image_for_pdf(self, file_path: str):
        """Open image as PIL Image for PDF conversion."""
        from PIL import Image
        return Image.open(file_path)
