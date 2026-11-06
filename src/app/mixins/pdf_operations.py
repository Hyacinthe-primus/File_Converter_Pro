"""PdfOperationsMixin - PDF merge, split, protect methods."""

import os
import secrets
import tempfile
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QMessageBox

from templates import semantic_keys as sk


def _protection_permission_flags(allow_printing, allow_copying, allow_modifications):
    """Build pypdf permissions.

    allow_printing controls PRINT and PRINT_TO_REPRESENTATION.
    allow_copying controls EXTRACT; EXTRACT_TEXT_AND_GRAPHICS stays enabled.
    allow_modifications controls MODIFY, ADD_OR_MODIFY, FILL_FORM_FIELDS,
    and ASSEMBLE_DOC.
    """
    from pypdf.constants import UserAccessPermissions

    flags = UserAccessPermissions(0xFFFFFFFF)
    if not allow_printing:
        flags &= ~(
            UserAccessPermissions.PRINT
            | UserAccessPermissions.PRINT_TO_REPRESENTATION
        )
    if not allow_copying:
        flags &= ~UserAccessPermissions.EXTRACT
    if not allow_modifications:
        flags &= ~(
            UserAccessPermissions.MODIFY
            | UserAccessPermissions.ADD_OR_MODIFY
            | UserAccessPermissions.FILL_FORM_FIELDS
            | UserAccessPermissions.ASSEMBLE_DOC
        )
    return flags


def _protect_pdf_file(
    source_file,
    output_file,
    user_password,
    allow_printing,
    allow_copying,
    allow_modifications,
):
    """Write an AES-256 protected copy without leaving a partial output."""
    from pypdf import PdfReader, PdfWriter

    permissions = _protection_permission_flags(
        allow_printing,
        allow_copying,
        allow_modifications,
    )
    owner_password = secrets.token_urlsafe(32)

    fd, temp_path = tempfile.mkstemp(
        prefix=".fcp_protect_",
        suffix=".pdf",
        dir=os.path.dirname(output_file) or ".",
    )
    os.close(fd)
    try:
        with open(source_file, "rb") as source_stream:
            reader = PdfReader(source_stream)
            writer = PdfWriter()
            writer.append(reader)
            writer.encrypt(
                user_password=user_password,
                owner_password=owner_password,
                permissions_flag=permissions,
                algorithm="AES-256",
            )
            with open(temp_path, "wb") as temp_file:
                writer.write(temp_file)
        os.replace(temp_path, output_file)
    except Exception:
        try:
            os.remove(temp_path)
        except OSError:
            pass
        raise


class PdfOperationsMixin:
    """Mixin: PDF merge, split, protect for FileConverterApp."""

    def merge_pdfs(self):
        from dialogs.merge_order_dialog import MergeOrderDialog
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
            msg = (
                self.translate_text("please_select_at_least_2_pdf_files")
                if selected_items
                else self.translate_text("the_list_must_contain_at_least_2_pdf_files")
            )
            QMessageBox.warning(self, self.translate_text("warning"), msg)
            return

        active_templates = getattr(self, "active_templates", None)
        template = active_templates.get(sk.PDF_MERGE) if isinstance(active_templates, dict) else None
        pre_select_key = template.get("merge_order_key") if isinstance(template, dict) else None
        if not isinstance(pre_select_key, str):
            pre_select_key = None

        dialog = MergeOrderDialog(
            pdf_files,
            ".pdf",
            parent=self,
            language=self.current_language,
            pre_select_key=pre_select_key,
        )
        if dialog.exec() != QDialog.Accepted:
            return
        ordered_files = dialog.get_ordered_files()
        order_key = dialog.get_order_key()

        default_filename = f"fusion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_file = self.get_output_directory(default_filename)
        if not output_file:
            return

        self.show_progress(True, self.translate_text("pdf_merge"))
        start_time = datetime.now()

        try:
            total_size = sum(os.path.getsize(f) for f in ordered_files)
            from context_menu.conversion_helpers import _merge_pdfs

            _merge_pdfs(
                ordered_files,
                os.path.dirname(output_file),
                "none",
                dst_path=output_file,
            )

            conversion_time = (datetime.now() - start_time).total_seconds()
            self.db_manager.add_conversion_record(
                source_file=", ".join([Path(f).name for f in ordered_files]),
                source_format="PDF",
                target_file=output_file,
                target_format="PDF",
                operation_type="merge_pdf",
                file_size=total_size,
                conversion_time=conversion_time,
                success=True,
            )
            self.achievement_system.record_conversion("merge_pdf", total_size, True)
            import fitz
            with fitz.open(output_file) as merged_doc:
                self.achievement_system.record_pdf_merge(len(merged_doc))
            self.record_config_usage(sk.PDF_MERGE, {"merge_order": order_key})
            self.show_progress(False)
            if self.config.get("enable_system_notifications", True):
                self.system_notifier.send("merge_pdf")
            QMessageBox.information(
                self,
                self.translate_text("success"),
                self.translate_text("pdf_merge_success").format(
                    count=len(ordered_files), time=f"{conversion_time:.1f}"
                ),
            )
        except Exception as e:
            self.show_progress(False)
            QMessageBox.critical(self, self.translate_text("error"),
                                 self.translate_text("error_merge").format(error=str(e)))

    def merge_word_docs(self):
        from dialogs.merge_order_dialog import MergeOrderDialog
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
            QMessageBox.warning(self, self.translate_text("warning"),
                                self.translate_text("please_select_at_least_2_word_files"))
            return

        active_templates = getattr(self, "active_templates", None)
        template = active_templates.get(sk.WORD_MERGE) if isinstance(active_templates, dict) else None
        pre_select_key = template.get("merge_order_key") if isinstance(template, dict) else None
        if not isinstance(pre_select_key, str):
            pre_select_key = None

        dialog = MergeOrderDialog(
            word_files,
            ".docx",
            parent=self,
            language=self.current_language,
            pre_select_key=pre_select_key,
        )
        if dialog.exec() != QDialog.Accepted:
            return
        ordered_files = dialog.get_ordered_files()
        order_key = dialog.get_order_key()

        default_filename = f"fusion_word_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        output_file = self.get_output_directory(default_filename)
        if not output_file:
            return

        self.show_progress(True, self.translate_text("word_merge"))
        start_time = datetime.now()

        try:
            total_size = sum(os.path.getsize(f) for f in ordered_files)
            from context_menu.conversion_helpers import _merge_docx

            _merge_docx(
                ordered_files,
                os.path.dirname(output_file),
                "none",
                dst_path=output_file,
            )
            self.show_progress(False)
            if self.config.get("enable_system_notifications", True):
                self.system_notifier.send("merge_word")
            conversion_time = (datetime.now() - start_time).total_seconds()
            self.db_manager.add_conversion_record(
                source_file=", ".join([Path(f).name for f in ordered_files]),
                source_format="Word",
                target_file=output_file,
                target_format="Word",
                operation_type="merge_word",
                file_size=total_size,
                conversion_time=conversion_time,
                success=True,
            )
            self.achievement_system.record_conversion("merge_word", total_size, True)
            self.record_config_usage(sk.WORD_MERGE, {"merge_order": order_key})
            QMessageBox.information(
                self,
                self.translate_text("success"),
                self.translate_text("word_merge_success").format(
                    count=len(ordered_files), time=f"{conversion_time:.1f}"
                ),
            )
        except Exception as e:
            self.show_progress(False)
            QMessageBox.critical(self, self.translate_text("error"),
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
            QMessageBox.warning(self, self.translate_text("warning"),
                                self.translate_text("please_select_at_least_one_pdf_file"))
            return

        for pdf_file in pdf_files:
            if self.split_pdf_file(pdf_file) is False:
                break

    def split_pdf_file(self, pdf_path, output_dir=None, dialog=None, silent=False):
        import fitz
        try:
            pdf_document = fitz.open(pdf_path)
            total_pages = len(pdf_document)
            pdf_document.close()
        except Exception as e:
            QMessageBox.critical(self, self.translate_text("error"), str(e))
            return

        if dialog is None:
            from dialogs import SplitDialog

            active_templates = getattr(self, "active_templates", None)
            template = active_templates.get(sk.PDF_SPLIT) if isinstance(active_templates, dict) else None
            pre_select_key = template.get("split_method_key") if isinstance(template, dict) else None
            if not isinstance(pre_select_key, str):
                pre_select_key = None
            pages_per_file = template.get("pages_per_file") if isinstance(template, dict) else None

            dialog = SplitDialog(
                total_pages,
                self,
                self.current_language,
                pre_select_key=pre_select_key,
                pages_per_file=pages_per_file,
            )
            if dialog.exec() != QDialog.Accepted:
                return False

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
            if method == 0:
                self.record_config_usage(
                    sk.PDF_SPLIT,
                    {"split_method": sk.SPLIT_BY_PAGES, "pages_per_file": dialog.page_interval.value()},
                )
            elif method == 1:
                self.record_config_usage(sk.PDF_SPLIT, {"split_method": sk.SPLIT_ALL_PAGES})
            if not silent:
                if self.config.get("enable_system_notifications", True):
                    self.system_notifier.send("split_pdf")
                QMessageBox.information(self, self.translate_text("success"),
                                        self.translate_text("pdf_split_into_files").format(total_pages=success_count))
        except Exception as e:
            QMessageBox.critical(self, self.translate_text("error"),
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
            QMessageBox.warning(self, self.translate_text("warning"),
                                self.translate_text("please_select_at_least_one_pdf_file"))
            return

        active_templates = getattr(self, "active_templates", None)
        template = (
            active_templates.get(sk.PDF_PROTECTION)
            if isinstance(active_templates, dict)
            else None
        )
        if isinstance(template, dict):
            pre_select_mode = template.get("protection_level")
            allow_printing = template.get("allow_printing")
            allow_copying = template.get("allow_copying")
            allow_modifications = template.get("allow_modifications")
            allow_printing = allow_printing if isinstance(allow_printing, bool) else None
            allow_copying = allow_copying if isinstance(allow_copying, bool) else None
            allow_modifications = (
                allow_modifications if isinstance(allow_modifications, bool) else None
            )
        else:
            pre_select_mode = sk.PROTECTION_ADVANCED
            allow_printing = True
            allow_copying = True
            allow_modifications = True

        from dialogs import PdfProtectionDialog

        dialog = PdfProtectionDialog(
            self,
            self.current_language,
            pre_select_mode=pre_select_mode,
            allow_printing=allow_printing,
            allow_copying=allow_copying,
            allow_modifications=allow_modifications,
        )
        if dialog.exec() != QDialog.Accepted:
            return

        mode = dialog.get_mode()
        password = dialog.get_password()
        if mode == sk.PROTECTION_ADVANCED and not password:
            QMessageBox.warning(self, self.translate_text("warning"),
                                self.translate_text("password_required"))
            return
        user_password = password if mode == sk.PROTECTION_ADVANCED else ""
        permissions = dialog.get_permissions()

        output_dir = self.get_output_directory()
        if not output_dir:
            return

        self.show_progress(True, self.translate_text("pdf_protection"))
        success_count = 0

        for i, pdf_file in enumerate(pdf_files):
            try:
                output_file = os.path.join(output_dir, f"protected_{Path(pdf_file).name}")
                _protect_pdf_file(
                    pdf_file,
                    output_file,
                    user_password,
                    permissions["allow_printing"],
                    permissions["allow_copying"],
                    permissions["allow_modifications"],
                )
                success_count += 1
                self.progress_bar.setValue(int((i + 1) / len(pdf_files) * 100))
            except Exception as e:
                print(f"Protection error {pdf_file}: {e}")

        self.show_progress(False)
        if success_count > 0:
            self.achievement_system.record_pdf_protection(
                success_count, len(user_password)
            )
        QMessageBox.information(
            self,
            self.translate_text("success"),
            self.translate_text("all_pdfs_protected").format(
                success_count=success_count, total_time=0.0
            ),
        )
