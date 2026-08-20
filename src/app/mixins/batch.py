"""Batch conversion and rename methods."""

import os
import tempfile
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

_BATCH_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"}
_ENGINE_TO_PDF = {
    ".txt": "txt_to_pdf",
    ".rtf": "rtf_to_pdf",
    ".xlsx": "xlsx_to_pdf",
    ".pptx": "pptx_to_pdf",
    ".html": "html_to_pdf",
    ".htm": "html_to_pdf",
    ".epub": "epub_to_pdf",
}
_ENGINE_TO_DOCX = {".txt": "txt_to_docx", ".rtf": "rtf_to_docx"}


class BatchMixin:
    """Batch conversion and rename for FileConverterApp."""

    def batch_convert(self) -> None:
        """Show batch conversion dialog and process selected format."""
        if not self.files_list:
            QMessageBox.warning(
                self, self.translate_text("Avertissement"), self.translate_text("La liste de fichiers est vide")
            )
            return
        from dialogs import BatchConvertDialog

        dialog = BatchConvertDialog(self, self.current_language)
        if dialog.exec() != QDialog.Accepted:
            return
        target_format = dialog.selected_format()
        output_dir = QFileDialog.getExistingDirectory(self, self.translate_text("Sélectionner le dossier de sortie"))
        if not output_dir:
            return
        self.process_batch_conversion(output_dir, target_format)

    def process_batch_conversion(self, output_dir: str, target_format: str) -> None:
        """Run conversion on all files using worker thread."""
        selected_items = self.files_list_widget.selectedItems()
        files = []
        if selected_items:
            for i in range(self.files_list_widget.count()):
                item = self.files_list_widget.item(i)
                if item.isSelected():
                    files.append(item.data(Qt.UserRole))
        else:
            files = list(self.files_list)

        if not files:
            QMessageBox.warning(
                self, self.translate_text("Avertissement"), self.translate_text("La liste de fichiers est vide")
            )
            return

        self.show_progress(True, self.translate_text("Conversion par Lot"))
        success_count = 0
        start_time = datetime.now()

        def _run_batch_file(task):
            import time as _time

            t0 = _time.perf_counter()
            fp = task["input_path"]
            out = task["output_path"]
            ok = self._convert_batch_file(fp, out, target_format)
            if not ok:
                return {"success": False, "input_path": fp, "error": "Unsupported conversion"}
            fs = os.path.getsize(fp) if os.path.exists(fp) else 0
            return {
                "success": True,
                "input_path": fp,
                "output_path": out,
                "file_size": fs,
                "operation_time": _time.perf_counter() - t0,
            }

        ext = {"pdf": "pdf", "docx": "docx", "png": "png"}.get(target_format, target_format)

        tasks = [
            {
                "index": i,
                "total": len(files),
                "input_path": fp,
                "output_path": os.path.join(output_dir, f"{Path(fp).stem}.{ext}"),
            }
            for i, fp in enumerate(files)
        ]

        def _on_file_done(result):
            if result.get("success"):
                self.db_manager.add_conversion_record(
                    source_file=result["input_path"],
                    source_format=Path(result["input_path"]).suffix.upper().replace(".", ""),
                    target_file=result["output_path"],
                    target_format=ext.upper(),
                    operation_type="batch_conversion",
                    file_size=result.get("file_size", 0),
                    conversion_time=result.get("operation_time", 0),
                    success=True,
                )
                nonlocal success_count
                success_count += 1

        def _on_finished(summary):
            self.show_progress(False)
            total_time = (datetime.now() - start_time).total_seconds()
            self.achievement_system.record_batch_conversion(len(files))
            target_label = {"pdf": "PDF", "docx": "DOCX", "png": "Images PNG"}.get(target_format, target_format.upper())
            if success_count:
                QMessageBox.information(
                    self,
                    self.translate_text("Batch Conversion Result"),
                    f"{success_count}/{len(files)} {self.translate_text('files converted to')} "
                    f"{self.translate_text(target_label)} ({total_time:.1f}s)",
                )
            else:
                QMessageBox.warning(
                    self,
                    self.translate_text("Batch Conversion Result"),
                    self.translate_text("No files converted. Check supported formats."),
                )

        from conversion_worker import ConversionWorker

        self._worker = ConversionWorker(tasks, _run_batch_file)
        self._worker.progress.connect(self.progress_bar.setValue)
        self._worker.file_done.connect(_on_file_done)
        self._worker.finished.connect(_on_finished)
        self._worker.start()

    def _convert_batch_file(self, fp: str, out: str, target_format: str) -> bool:
        """Convert one file to the requested target ('pdf' | 'docx' | 'png')."""
        ext = Path(fp).suffix.lower()
        try:
            if target_format == "pdf":
                return self._batch_to_pdf(fp, out, ext)
            if target_format == "docx":
                return self._batch_to_docx(fp, out, ext)
            if target_format == "png":
                return self._batch_to_png(fp, out, ext)
        except Exception as e:
            print(f"[BATCH] {Path(fp).name} → {target_format}: {e}")
            return False
        return False

    def _batch_to_pdf(self, fp: str, out: str, ext: str) -> bool:
        """Route a single file to PDF."""
        if ext in (".docx", ".doc"):
            try:
                if self.convert_word_to_pdf_com(fp, out):
                    return True
            except Exception:
                pass
            try:
                if self._convert_docx_to_pdf_libreoffice(fp, out):
                    return True
            except Exception:
                pass
            return bool(self.convert_docx_to_pdf_simple(fp, out))
        if ext == ".pdf":
            return self._batch_copy(fp, out)
        if ext in _BATCH_IMAGE_EXTS:
            self._open_image_for_pdf(fp).save(out, format="PDF", resolution=100.0)
            return os.path.exists(out)
        conv = _ENGINE_TO_PDF.get(ext)
        if conv:
            from converter.converters import AdvancedConverterEngine

            return AdvancedConverterEngine().convert(conv, fp, str(Path(out).parent)).success
        return False

    def _batch_to_docx(self, fp: str, out: str, ext: str) -> bool:
        """Route a single file to DOCX."""
        if ext == ".pdf":
            return self._batch_pdf_to_docx(fp, out)
        if ext in (".docx", ".doc"):
            return self._batch_copy(fp, out)
        if ext in _BATCH_IMAGE_EXTS:
            return self._batch_image_to_docx(fp, out)
        conv = _ENGINE_TO_DOCX.get(ext)
        if conv:
            from converter.converters import AdvancedConverterEngine

            return AdvancedConverterEngine().convert(conv, fp, str(Path(out).parent)).success
        return False

    def _batch_pdf_to_docx(self, fp: str, out: str) -> bool:
        """Convert a PDF to DOCX using COM → LibreOffice → native fallback."""
        try:
            if self._try_word_com_pdf_to_docx(fp, out):
                return True
        except Exception:
            pass
        try:
            if self._convert_pdf_to_docx_libreoffice(fp, out):
                return True
        except Exception:
            pass
        self._solid_fitz_fallback(fp, out)
        return os.path.exists(out)

    def _batch_to_png(self, fp: str, out: str, ext: str) -> bool:
        """Route a single file to PNG (one PNG per page for PDFs)."""
        if ext in _BATCH_IMAGE_EXTS:
            try:
                from PIL import Image

                Image.open(fp).save(out, format="PNG")
                return os.path.exists(out)
            except Exception:
                return self._batch_copy(fp, out)
        if ext == ".pdf":
            return self._pdf_to_png(fp, out)
        if ext in (".docx", ".doc"):
            tmp_pdf = self._batch_temp_file()
            try:
                if not self._batch_to_pdf(fp, tmp_pdf, ".docx"):
                    return False
                return self._pdf_to_png(tmp_pdf, out)
            finally:
                self._batch_remove_temp(tmp_pdf)
        conv = _ENGINE_TO_PDF.get(ext)
        if conv:
            tmp_dir = tempfile.mkdtemp()
            try:
                from converter.converters import AdvancedConverterEngine

                if not AdvancedConverterEngine().convert(conv, fp, tmp_dir).success:
                    return False
                tmp_pdf = os.path.join(tmp_dir, f"{Path(fp).stem}.pdf")
                if not os.path.exists(tmp_pdf):
                    return False
                return self._pdf_to_png(tmp_pdf, out)
            finally:
                self._batch_remove_temp(tmp_dir)
        return False

    @staticmethod
    def _batch_copy(src: str, dst: str) -> bool:
        import shutil

        try:
            shutil.copy2(src, dst)
            return os.path.exists(dst)
        except Exception:
            return False

    def _batch_image_to_docx(self, fp: str, out: str) -> bool:
        try:
            from docx import Document
            from docx.shared import Inches

            doc = Document()
            doc.add_picture(fp, width=Inches(6.0))
            doc.save(out)
            return os.path.exists(out)
        except Exception as e:
            print(f"[BATCH] image→docx {e}")
            return False

    @staticmethod
    def _batch_temp_file() -> str:
        import tempfile as _tempfile

        fd, path = _tempfile.mkstemp(suffix=".pdf")
        import os as _os

        _os.close(fd)
        return path

    @staticmethod
    def _batch_remove_temp(path: str) -> None:
        import os as _os

        try:
            if _os.path.isdir(path):
                import shutil

                shutil.rmtree(path, ignore_errors=True)
            elif _os.path.exists(path):
                _os.remove(path)
        except Exception:
            pass

    @staticmethod
    def _pdf_to_png(pdf_path: str, base_out: str) -> bool:
        """Render each PDF page to PNG. First page → base_out, rest → stem_page_N.png."""
        import fitz

        doc = fitz.open(pdf_path)
        base = Path(base_out)
        written = 0
        try:
            for i, page in enumerate(doc, 1):
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                target = str(base) if i == 1 else str(base.with_name(f"{base.stem}_page_{i}.png"))
                pix.save(target)
                written += 1
        finally:
            doc.close()
        return written > 0

    def process_batch_rename(self, rename_plan: list[tuple[str, str]]) -> None:
        """Execute rename plan: list of (old_path, new_name) tuples."""
        success_count = 0
        new_files_list = []
        for old_path, new_name in rename_plan:
            try:
                new_path = os.path.join(Path(old_path).parent, new_name)
                counter = 1
                base_stem, ext = os.path.splitext(new_path)
                while os.path.exists(new_path) and new_path != old_path:
                    new_path = f"{base_stem}_{counter}{ext}"
                    counter += 1
                if new_path != old_path:
                    os.rename(old_path, new_path)
                new_files_list.append(new_path)
                success_count += 1
            except Exception as e:
                print(f"Error renaming {old_path}: {e}")
                new_files_list.append(old_path)

        self.files_list = new_files_list
        self._sync_active_tab_state()
        self.files_list_widget.clear()
        for idx, file_path in enumerate(self.files_list, 1):
            icon = self.get_file_icon(file_path)
            display_name = Path(file_path).name
            if isinstance(icon, QIcon):
                item = __import__("PySide6.QtWidgets", fromlist=["QListWidgetItem"]).QListWidgetItem(
                    f"{idx}. {display_name}"
                )
                item.setIcon(icon)
            else:
                item = __import__("PySide6.QtWidgets", fromlist=["QListWidgetItem"]).QListWidgetItem(
                    f"{idx}. {icon} {display_name}"
                )
            item.setData(Qt.UserRole, file_path)
            item.setData(Qt.UserRole + 1, "file")
            if os.path.isfile(file_path):
                item.setData(Qt.UserRole + 4, self.format_size(os.path.getsize(file_path)))
            item.setToolTip(file_path)
            self.files_list_widget.addItem(item)

        self.update_file_counter()
        QMessageBox.information(
            self, self.translate_text("Succès"), f"{success_count} {self.translate_text('files renamed')}"
        )

    def get_output_directory(self, filename: str | None = None) -> str:
        default_dir = self.config.get("default_output_folder")
        if filename:
            start_dir = (
                os.path.join(default_dir, filename) if (default_dir and os.path.exists(default_dir)) else filename
            )
            ext = Path(filename).suffix.lower()
            if ext == ".pdf":
                file_filter = self.translate_text("PDF files (*.pdf)")
            elif ext in (".docx", ".doc"):
                file_filter = "Word Files (*.docx)"
            else:
                file_filter = "All files (*.*)"
            return QFileDialog.getSaveFileName(self, self.translate_text("Save file"), start_dir, file_filter)[0]
        else:
            if default_dir and os.path.exists(default_dir):
                return default_dir
            else:
                return QFileDialog.getExistingDirectory(self, self.translate_text("Select destination folder"))
