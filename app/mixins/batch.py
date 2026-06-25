"""Batch conversion and rename methods."""

import os
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import QFileDialog, QMessageBox, QDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

class BatchMixin:
    """Batch conversion and rename for FileConverterApp."""

    def batch_convert(self) -> None:
        """Show batch conversion dialog and process selected format."""
        if not self.files_list:
            QMessageBox.warning(self, self.translate_text("Avertissement"),
                                self.translate_text("La liste de fichiers est vide"))
            return
        from dialogs import BatchConvertDialog
        dialog = BatchConvertDialog(self, self.current_language)
        if dialog.exec() != QDialog.Accepted:
            return
        target_format = dialog.format_combo.currentText()
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
            QMessageBox.warning(self, self.translate_text("Avertissement"),
                                self.translate_text("La liste de fichiers est vide"))
            return

        self.show_progress(True, self.translate_text("Conversion par Lot"))
        success_count = 0
        start_time = datetime.now()

        def _run_batch_file(task):
            import time as _time
            t0 = _time.perf_counter()
            fp = task["input_path"]
            out = task["output_path"]
            ext = Path(fp).suffix.lower()
            try:
                if ext == '.txt' and 'PDF' in target_format:
                    self.convert_txt_to_pdf(fp, out)
                elif ext in ('.docx', '.doc') and 'PDF' in target_format:
                    self.convert_docx_to_pdf_simple(fp, out)
                elif ext == '.pdf' and 'DOCX' in target_format:
                    self.convert_pdf_to_docx_text_only(fp, out)
                elif ext in ('.jpg', '.jpeg', '.png') and 'PDF' in target_format:
                    self._open_image_for_pdf(fp).save(out, format='PDF')
                fs = os.path.getsize(fp) if os.path.exists(fp) else 0
                return {"success": True, "input_path": fp, "output_path": out, "file_size": fs, "operation_time": _time.perf_counter() - t0}
            except Exception as e:
                return {"success": False, "input_path": fp, "error": str(e)}

        fmt_map = {'PDF': 'pdf', 'DOCX': 'docx', 'Images PNG': 'png'}
        ext = fmt_map.get(target_format, 'pdf')

        tasks = [{"index": i, "total": len(files), "input_path": fp, "output_path": os.path.join(output_dir, f"{Path(fp).stem}.{ext}")} for i, fp in enumerate(files)]

        def _on_file_done(result):
            if result.get("success"):
                self.db_manager.add_conversion_record(source_file=result["input_path"], source_format=Path(result["input_path"]).suffix.upper().replace('.', ''), target_file=result["output_path"], target_format=ext.upper(), operation_type="batch_conversion", file_size=result.get("file_size", 0), conversion_time=result.get("operation_time", 0), success=True)
                nonlocal success_count
                success_count += 1

        def _on_finished(summary):
            self.show_progress(False)
            total_time = (datetime.now() - start_time).total_seconds()
            self.achievement_system.record_batch_conversion(len(files))
            self.achievement_system.record_conversion("batch_conversion", 0, True)
            QMessageBox.information(self, self.translate_text("Succès"),
                                    self.translate_text("pdf_to_word_success_sum").format(success_count, len(files), f"{total_time:.1f}"))

        from conversion_worker import ConversionWorker
        self._worker = ConversionWorker(tasks, _run_batch_file)
        self._worker.progress.connect(self.progress_bar.setValue)
        self._worker.file_done.connect(_on_file_done)
        self._worker.finished.connect(_on_finished)
        self._worker.start()

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
        self.files_list_widget.clear()
        for file_path in self.files_list:
            icon = self.get_file_icon(file_path)
            display_name = Path(file_path).name
            if isinstance(icon, QIcon):
                item = __import__('PySide6.QtWidgets', fromlist=['QListWidgetItem']).QListWidgetItem(display_name)
                item.setIcon(icon)
            else:
                item = __import__('PySide6.QtWidgets', fromlist=['QListWidgetItem']).QListWidgetItem(f"{icon} {display_name}")
            item.setData(Qt.UserRole, file_path)
            item.setData(Qt.UserRole + 1, "file")
            if os.path.isfile(file_path):
                item.setData(Qt.UserRole + 4, self.format_size(os.path.getsize(file_path)))
            item.setToolTip(file_path)
            self.files_list_widget.addItem(item)

        self.update_file_counter()
        QMessageBox.information(self, self.translate_text("Succès"),
                                f"{success_count} {self.translate_text('files renamed')}")

    def get_output_directory(self, filename: str | None = None) -> str:
        default_dir = self.config.get("default_output_folder")
        if filename:
            start_dir = os.path.join(default_dir, filename) if (default_dir and os.path.exists(default_dir)) else filename
            ext = Path(filename).suffix.lower()
            if ext == '.pdf':
                file_filter = self.translate_text("PDF files (*.pdf)")
            elif ext in ('.docx', '.doc'):
                file_filter = "Word Files (*.docx)"
            else:
                file_filter = "All files (*.*)"
            return QFileDialog.getSaveFileName(self, self.translate_text("Save file"), start_dir, file_filter)[0]
        else:
            if default_dir and os.path.exists(default_dir):
                return default_dir
            else:
                return QFileDialog.getExistingDirectory(self, self.translate_text("Select destination folder"))
