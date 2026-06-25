"""PdfOperationsMixin — PDF merge, split, protect methods."""

import os
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtCore import Qt

class PdfOperationsMixin:
    """Mixin: PDF merge, split, protect for FileConverterApp."""

    def merge_pdfs(self):
        from app.ui import MergeOrderDialog
        selected_items = self.files_list_widget.selectedItems()
        pdf_files = []
        if selected_items:
            for i in range(self.files_list_widget.count()):
                item = self.files_list_widget.item(i)
                if item.isSelected():
                    f = item.data(Qt.UserRole)
                    if f and f.lower().endswith('.pdf'):
                        pdf_files.append(f)
        else:
            pdf_files = [f for f in self.files_list if f.lower().endswith('.pdf')]

        if len(pdf_files) < 2:
            msg = self.translate_text("Veuillez sélectionner au moins 2 fichiers PDF") if selected_items else self.translate_text("La liste doit contenir au moins 2 fichiers PDF")
            QMessageBox.warning(self, self.translate_text("Avertissement"), msg)
            return

        dialog = MergeOrderDialog(pdf_files, self, self.current_language)
        if dialog.exec() != QDialog.Accepted:
            return
        ordered_files = dialog.get_ordered_files()

        default_filename = f"fusion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_file = self.get_output_directory(default_filename)
        if not output_file:
            return

        self.show_progress(True, self.translate_text("Fusion PDF"))
        start_time = datetime.now()
        total_size = sum(os.path.getsize(f) for f in ordered_files)

        try:
            from pypdf import PdfMerger
            merger = PdfMerger()
            for file_path in ordered_files:
                merger.append(file_path)
            merger.write(output_file)
            merger.close()

            conversion_time = (datetime.now() - start_time).total_seconds()
            self.db_manager.add_conversion_record(source_file=", ".join([Path(f).name for f in ordered_files]), source_format="PDF", target_file=output_file, target_format="PDF", operation_type="merge_pdf", file_size=total_size, conversion_time=conversion_time, success=True)
            self.achievement_system.record_conversion("merge_pdf", total_size, True)
            import fitz
            merged_doc = fitz.open(output_file)
            self.achievement_system.record_pdf_merge(len(merged_doc))
            merged_doc.close()
            self.show_progress(False)
            if self.config.get("enable_system_notifications", True):
                self.system_notifier.send("merge_pdf")
            QMessageBox.information(self, self.translate_text("Succès"),
                                    self.translate_text("pdf_merge_success").format(count=len(ordered_files), time=f"{conversion_time:.1f}"))
        except Exception as e:
            self.show_progress(False)
            QMessageBox.critical(self, self.translate_text("Erreur"),
                                 self.translate_text("error_merge").format(error=str(e)))

    def merge_word_docs(self):
        from docxcompose import Composer
        selected_items = self.files_list_widget.selectedItems()
        word_files = []
        if selected_items:
            for i in range(self.files_list_widget.count()):
                item = self.files_list_widget.item(i)
                if item.isSelected():
                    f = item.data(Qt.UserRole)
                    if f and f.lower().endswith(('.docx', '.doc')):
                        word_files.append(f)
        else:
            word_files = [f for f in self.files_list if f.lower().endswith(('.docx', '.doc'))]

        if len(word_files) < 2:
            QMessageBox.warning(self, self.translate_text("Avertissement"),
                                self.translate_text("Veuillez sélectionner au moins 2 fichiers Word"))
            return

        default_filename = f"fusion_word_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        output_file = self.get_output_directory(default_filename)
        if not output_file:
            return

        self.show_progress(True, self.translate_text("Fusion Word"))
        try:
            from docx import Document
            composer = Composer(Document(word_files[0]))
            for wf in word_files[1:]:
                composer.append(Document(wf))
            composer.save(output_file)
            self.show_progress(False)
            if self.config.get("enable_system_notifications", True):
                self.system_notifier.send("merge_word")
            QMessageBox.information(self, self.translate_text("Succès"),
                                    self.translate_text("word_merge_success").format(count=len(word_files), time="0"))
        except Exception as e:
            self.show_progress(False)
            QMessageBox.critical(self, self.translate_text("Erreur"),
                                 self.translate_text("error_merge").format(error=str(e)))

    def split_pdf(self):
        selected_items = self.files_list_widget.selectedItems()
        pdf_files = []
        if selected_items:
            for i in range(self.files_list_widget.count()):
                item = self.files_list_widget.item(i)
                if item.isSelected():
                    f = item.data(Qt.UserRole)
                    if f and f.lower().endswith('.pdf'):
                        pdf_files.append(f)
        else:
            pdf_files = [f for f in self.files_list if f.lower().endswith('.pdf')]

        if not pdf_files:
            QMessageBox.warning(self, self.translate_text("Avertissement"),
                                self.translate_text("Veuillez sélectionner au moins un fichier PDF"))
            return

        for pdf_file in pdf_files:
            self.split_pdf_file(pdf_file)

    def split_pdf_file(self, pdf_path, output_dir=None, dialog=None, silent=False):
        import fitz
        try:
            pdf_document = fitz.open(pdf_path)
            total_pages = len(pdf_document)
            pdf_document.close()
        except Exception as e:
            QMessageBox.critical(self, self.translate_text("Erreur"), str(e))
            return

        if dialog is None:
            from dialogs import SplitDialog
            dialog = SplitDialog(total_pages, self, self.current_language)
            if dialog.exec() != QDialog.Accepted:
                return

        if not output_dir:
            output_dir = self.get_output_directory()
            if not output_dir:
                return

        method = dialog.split_method.currentIndex()
        pdf_document = fitz.open(pdf_path)
        base_name = Path(pdf_path).stem
        success_count = 0

        try:
            if method == 0:
                interval = dialog.page_interval.value()
                for start in range(0, total_pages, interval):
                    end = min(start + interval, total_pages)
                    output_file = os.path.join(output_dir, f"{base_name}_pages_{start+1}-{end}.pdf")
                    new_pdf = fitz.open()
                    new_pdf.insert_pdf(pdf_document, from_page=start, to_page=end-1)
                    new_pdf.save(output_file)
                    new_pdf.close()
                    success_count += 1
            elif method == 1:
                for i in range(total_pages):
                    output_file = os.path.join(output_dir, f"{base_name}_page_{i+1}.pdf")
                    new_pdf = fitz.open()
                    new_pdf.insert_pdf(pdf_document, from_page=i, to_page=i)
                    new_pdf.save(output_file)
                    new_pdf.close()
                    success_count += 1
            elif method == 2:
                start_page = dialog.start_page.value() - 1
                end_page = dialog.end_page.value()
                output_file = os.path.join(output_dir, f"{base_name}_pages_{start_page+1}-{end_page}.pdf")
                new_pdf = fitz.open()
                new_pdf.insert_pdf(pdf_document, from_page=start_page, to_page=end_page-1)
                new_pdf.save(output_file)
                new_pdf.close()
                success_count = 1

            pdf_document.close()
            self.achievement_system.record_pdf_split(total_pages)
            self.achievement_system.record_conversion("split_pdf", 0, True)
            if not silent:
                if self.config.get("enable_system_notifications", True):
                    self.system_notifier.send("split_pdf")
                QMessageBox.information(self, self.translate_text("Succès"),
                                        self.translate_text("pdf_split_into_files").format(total_pages=success_count))
        except Exception as e:
            QMessageBox.critical(self, self.translate_text("Erreur"),
                                 self.translate_text("split_error").format(error=str(e)))

    def protect_pdf(self):
        selected_items = self.files_list_widget.selectedItems()
        pdf_files = []
        if selected_items:
            for i in range(self.files_list_widget.count()):
                item = self.files_list_widget.item(i)
                if item.isSelected():
                    f = item.data(Qt.UserRole)
                    if f and f.lower().endswith('.pdf'):
                        pdf_files.append(f)
        else:
            pdf_files = [f for f in self.files_list if f.lower().endswith('.pdf')]

        if not pdf_files:
            QMessageBox.warning(self, self.translate_text("Avertissement"),
                                self.translate_text("Veuillez sélectionner au moins un fichier PDF"))
            return

        from dialogs import PasswordDialog
        dialog = PasswordDialog(self, self.current_language)
        if dialog.exec() != QDialog.Accepted:
            return

        password = dialog.get_password()
        if not password:
            QMessageBox.warning(self, self.translate_text("Avertissement"),
                                self.translate_text("Mot de passe requis"))
            return

        output_dir = self.get_output_directory()
        if not output_dir:
            return

        self.show_progress(True, self.translate_text("Protection PDF"))
        success_count = 0

        import fitz
        for i, pdf_file in enumerate(pdf_files):
            try:
                output_file = os.path.join(output_dir, f"protected_{Path(pdf_file).name}")
                pdf_doc = fitz.open(pdf_file)
                pdf_doc.save(output_file, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw=password)
                pdf_doc.close()
                success_count += 1
                self.progress_bar.setValue(int((i + 1) / len(pdf_files) * 100))
            except Exception as e:
                print(f"Protection error {pdf_file}: {e}")

        self.show_progress(False)
        if success_count > 0:
            self.achievement_system.record_pdf_protection(success_count, len(password))
        QMessageBox.information(self, self.translate_text("Succès"),
                                self.translate_text("all_pdfs_protected").format(success_count=success_count, total_time="0"))
