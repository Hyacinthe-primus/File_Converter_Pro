"""Batch conversion and rename methods."""

import os
import tempfile
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from context_menu.conversion_helpers import (
    _release_reserved_path,
    _reserve_unique_output_path,
)
from context_menu.formats import CONVERSION_MAP
from converter.helpers import BackupError, prepare_operation_backups
from converter.registry import DISPATCH
from utils.conversion_pipeline import run_conversion_pipeline
from utils.pdf_artifacts import validate_docx_artifact, validate_docx_input, validate_pdf_artifact

_BATCH_RECOGNIZED_IMAGE_EXTS = frozenset(
    f".{ext}"
    for ext, actions in CONVERSION_MAP.items()
    if "image_to_pdf" in actions
)
_BATCH_UNSUPPORTED_IMAGE_FORMATS = frozenset(
    {"psd", "dng", "raw", "cr2", "cr3", "nef", "arw", "orf", "rw2", "raf"}
)
_BATCH_IMAGE_EXTS = frozenset(
    ext
    for ext in _BATCH_RECOGNIZED_IMAGE_EXTS
    if ext.lstrip(".") not in _BATCH_UNSUPPORTED_IMAGE_FORMATS
)
_BATCH_EXTENSION_ALIASES = {"htm": "html"}


def _batch_conversion_type(ext: str, target: str) -> str | None:
    """Resolve a Batch conversion from the shared format/action mapping."""
    source = ext.lstrip(".").lower()
    source = _BATCH_EXTENSION_ALIASES.get(source, source)
    suffix = f"_{target}"
    for action in CONVERSION_MAP.get(source, ()):
        if action.endswith(suffix) and action in DISPATCH:
            return action
    return None


class BatchMixin:
    """Batch conversion and rename for FileConverterApp."""

    def _open_batch_image(self, fp: str):
        opener = getattr(self, "_open_image_for_pdf", None)
        if callable(opener):
            return opener(fp)

        from PIL import Image

        from utils.image_formats import register_heif

        if Path(fp).suffix.lower() == ".svg":
            import io

            import fitz

            with fitz.open(fp) as document:
                png = document[0].get_pixmap(alpha=True).tobytes("png")
            return Image.open(io.BytesIO(png))
        register_heif()
        return Image.open(fp)

    def _batch_engine_convert(self, conversion_type: str, fp: str, out: str) -> bool:
        from converter.converters import AdvancedConverterEngine

        engine = AdvancedConverterEngine()
        engine.allow_local_html_resources = getattr(self, "config", {}).get(
            "allow_local_resources_in_html_to_pdf", False
        )
        result = engine.convert(conversion_type, fp, str(Path(out).parent), skip_backup=True)
        if result.success:
            return True
        self._last_batch_error = (
            result.error or f"Batch conversion failed for {Path(fp).name}"
        )
        return False

    def _batch_unsupported(self, ext: str, target: str) -> bool:
        supported_input = f"{ext} input" if ext else "this input"
        self._last_batch_error = (
            f"Batch {target.upper()} conversion does not support {supported_input}"
        )
        print(f"[BATCH] {self._last_batch_error}")
        return False

    def _prepare_batch_backup(self, fp: str) -> tuple[bool, str]:
        config = getattr(self, "config", None)
        if not isinstance(config, dict):
            return False, "Batch configuration unavailable"
        try:
            prepare_operation_backups([fp], config=config)
        except BackupError as exc:
            return False, str(exc)
        return True, ""

    def batch_convert(self) -> None:
        """Show batch conversion dialog and process selected format."""
        if not self.files_list:
            QMessageBox.warning(
                self, self.translate_text("warning"), self.translate_text("the_file_list_is_empty")
            )
            return
        from dialogs import BatchConvertDialog

        dialog = BatchConvertDialog(self, self.current_language)
        if dialog.exec() != QDialog.Accepted:
            return
        target_format = dialog.selected_format()
        output_dir = QFileDialog.getExistingDirectory(
            self, self.translate_text("choose_output_folder")
        )
        if not output_dir:
            return
        self.process_batch_conversion(output_dir, target_format)

    def process_batch_conversion(self, output_dir: str, target_format: str) -> None:
        """Run conversion on all files using worker thread."""
        if getattr(self, "config", {}).get("auto_clean_temp_files", True):
            self.cleanup_temp_files()
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
                self, self.translate_text("warning"), self.translate_text("the_file_list_is_empty")
            )
            return

        self.show_progress(True, self.translate_text("batch_conversion"))
        success_count = 0
        start_time = datetime.now()
        backed_up_keys = set()

        def _run_batch_file(task):
            import time as _time

            t0 = _time.perf_counter()
            fp = task["input_path"]
            out = task["output_path"]
            self._last_batch_error = ""
            backup_prepared = False
            try:
                try:
                    backup_key = os.path.normcase(os.path.realpath(fp))
                except Exception:
                    backup_key = fp
                if backup_key in backed_up_keys:
                    backup_prepared = True
                else:
                    backup_ok, backup_error = self._prepare_batch_backup(fp)
                    if not backup_ok:
                        _release_reserved_path(out)
                        return {"success": False, "input_path": fp, "error": backup_error}
                    backed_up_keys.add(backup_key)
                    backup_prepared = True
                ok = self._convert_batch_file(
                    fp, out, target_format, backup_prepared=backup_prepared
                )
                if not ok:
                    error = (
                        self._last_batch_error
                        or "Batch conversion failed without an error reason"
                    )
                    _release_reserved_path(out)
                    return {"success": False, "input_path": fp, "error": error}
            except Exception as exc:
                _release_reserved_path(out)
                return {"success": False, "input_path": fp, "error": str(exc)}
            fs = os.path.getsize(fp) if os.path.exists(fp) else 0
            return {
                "success": True,
                "input_path": fp,
                "output_path": out,
                "file_size": fs,
                "operation_time": _time.perf_counter() - t0,
            }

        ext = {"pdf": "pdf", "docx": "docx", "png": "png"}.get(target_format, target_format)

        tasks = []
        for i, fp in enumerate(files):
            tasks.append(
                {
                    "index": i,
                    "total": len(files),
                    "input_path": fp,
                    "output_path": _reserve_unique_output_path(
                        output_dir, Path(fp).stem, ext
                    ),
                }
            )

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
            else:
                self.db_manager.add_conversion_record(
                    source_file=result.get("input_path", "?"),
                    source_format=Path(result.get("input_path", "?")).suffix.upper().replace(".", ""),
                    target_file="",
                    target_format=ext.upper(),
                    operation_type="batch_conversion",
                    file_size=0,
                    conversion_time=0,
                    success=False,
                    notes=f"Error: {result.get('error', '')}",
                )

        def _on_finished(summary):
            self.show_progress(False)
            total_time = (datetime.now() - start_time).total_seconds()
            self.achievement_system.record_batch_conversion(len(files))
            target_label = {"pdf": "PDF", "docx": "DOCX", "png": "png_images"}.get(target_format, target_format.upper())
            completed = summary.get("success_count", success_count)
            failed = summary.get("failed", [])
            result_text = (
                f"{completed}/{len(files)} {self.translate_text('files_converted_to')} "
                f"{self.translate_text(target_label)} ({total_time:.1f}s)"
            )
            if failed or completed < len(files):
                failure_lines = [
                    self.translate_text("error_with_file").format(
                        filename=Path(item.get("name", "?")).name,
                        error=item.get("error", ""),
                    )
                    for item in failed
                ]
                if failure_lines:
                    result_text += "\n\n" + "\n".join(failure_lines)
                QMessageBox.warning(
                    self,
                    self.translate_text("batch_conversion_result"),
                    result_text,
                )
                return
            QMessageBox.information(
                self,
                self.translate_text("batch_conversion_result"),
                result_text,
            )

        from conversion_worker import ConversionWorker

        self._worker = ConversionWorker(tasks, _run_batch_file)
        self._worker.progress.connect(self.progress_bar.setValue)
        self._worker.file_done.connect(_on_file_done)
        self._worker.finished.connect(_on_finished)
        self._worker.start()

    def _convert_batch_file(
        self,
        fp: str,
        out: str,
        target_format: str,
        *,
        backup_prepared: bool = False,
    ) -> bool:
        """Convert one file to the requested target ('pdf' | 'docx' | 'png')."""
        ext = Path(fp).suffix.lower()
        self._last_batch_error = ""
        try:
            if target_format == "pdf":
                return self._batch_to_pdf(fp, out, ext, backup_prepared=backup_prepared)
            if target_format == "docx":
                return self._batch_to_docx(fp, out, ext, backup_prepared=backup_prepared)
            if target_format == "png":
                return self._batch_to_png(fp, out, ext, backup_prepared=backup_prepared)
        except Exception as e:
            self._last_batch_error = f"Batch {target_format.upper()} conversion failed: {e}"
            print(f"[BATCH] {Path(fp).name} → {target_format}: {e}")
            return False
        return self._batch_unsupported(ext, target_format)

    def _batch_to_pdf(self, fp: str, out: str, ext: str, *, backup_prepared: bool = False) -> bool:
        """Route a single file to PDF."""
        self._last_batch_error = ""
        if not backup_prepared:
            backup_ok, backup_error = self._prepare_batch_backup(fp)
            if not backup_ok:
                self._last_batch_error = backup_error
                print(f"[BATCH] Backup failed for {Path(fp).name}: {backup_error}")
                return False
            backup_prepared = True
        if ext in (".docx", ".doc"):
            valid, reason = validate_docx_input(fp)
            if not valid:
                self._last_batch_error = f"Word to PDF conversion failed: {reason}"
                print(f"[BATCH] Word->PDF input rejected for {Path(fp).name}: {reason}")
                return False
            engines = [
                ("COM", lambda target: self.convert_word_to_pdf_com(fp, target)),
                ("LibreOffice", lambda target: self._convert_docx_to_pdf_libreoffice(fp, target)),
                ("ReportLab", lambda target: self.convert_docx_to_pdf_simple(fp, target)),
            ]
            result = run_conversion_pipeline(
                out,
                engines,
                validate_pdf_artifact,
                stage_mode="directory",
                stage_dir_prefix="~fcp_pdf_stage_",
                staged_prefix="~fcp_pdf_",
                staged_suffix=".pdf",
            )
            if result.success:
                return True
            self._last_batch_error = "Word to PDF conversion failed: " + result.error
            print(f"[BATCH] Word->PDF failed for {Path(fp).name}: {result.error}")
            return False
        if ext == ".pdf":
            return self._batch_copy_checked(fp, out)
        if ext in _BATCH_IMAGE_EXTS:
            def _save_image(target):
                with self._open_batch_image(fp) as image:
                    image.save(target, format="PDF", resolution=100.0)
                return True

            result = run_conversion_pipeline(
                out,
                [("Pillow", _save_image)],
                validate_pdf_artifact,
                stage_mode="directory",
                stage_dir_prefix="~fcp_pdf_stage_",
                staged_prefix="~fcp_pdf_image_",
                staged_suffix=".pdf",
            )
            if result.success:
                return True
            self._last_batch_error = "Image to PDF conversion failed: " + result.error
            print(f"[BATCH] Image->PDF failed for {Path(fp).name}: {result.error}")
            return False
        if ext in _BATCH_RECOGNIZED_IMAGE_EXTS:
            return self._batch_unsupported(ext, "pdf")
        conv = _batch_conversion_type(ext, "pdf")
        if conv:
            return self._batch_engine_convert(conv, fp, out)
        return self._batch_unsupported(ext, "pdf")

    def _batch_to_docx(self, fp: str, out: str, ext: str, *, backup_prepared: bool = False) -> bool:
        """Route a single file to DOCX."""
        self._last_batch_error = ""
        if not backup_prepared:
            backup_ok, backup_error = self._prepare_batch_backup(fp)
            if not backup_ok:
                self._last_batch_error = backup_error
                print(f"[BATCH] Backup failed for {Path(fp).name}: {backup_error}")
                return False
        if ext == ".pdf":
            return self._batch_pdf_to_docx(fp, out)
        if ext == ".docx":
            return self._batch_copy_checked(fp, out)
        if ext == ".doc":
            self._last_batch_error = (
                "Batch DOCX conversion does not support legacy .doc input"
            )
            return False
        if ext in _BATCH_IMAGE_EXTS:
            return self._batch_image_to_docx(fp, out)
        if ext in _BATCH_RECOGNIZED_IMAGE_EXTS:
            return self._batch_unsupported(ext, "docx")
        conv = _batch_conversion_type(ext, "docx")
        if conv:
            return self._batch_engine_convert(conv, fp, out)
        return self._batch_unsupported(ext, "docx")

    def _batch_pdf_to_docx(self, fp: str, out: str) -> bool:
        """Convert a PDF to DOCX using the configured PDF-to-Word mode."""
        self._last_batch_error = ""
        from context_menu.conversion_helpers import _normalise_pdf_to_word_mode

        config = getattr(self, "config", None)
        mode = _normalise_pdf_to_word_mode(
            config.get("pdf_to_word_mode") if isinstance(config, dict) else None
        )
        if mode == "text_only":
            if self.convert_pdf_to_docx_text_only(fp, out):
                return True
            detail = getattr(self, "_last_pdf_to_word_error", "") or "text-only conversion failed"
            self._last_batch_error = "PDF to Word conversion failed: " + detail
            return False

        engines = [
            ("COM", lambda target: self._try_word_com_pdf_to_docx(fp, target)),
            ("LibreOffice", lambda target: self._convert_pdf_to_docx_libreoffice(fp, target)),
            ("fitz fallback", lambda target: self._solid_fitz_fallback(fp, target)),
        ]
        result = run_conversion_pipeline(
            out,
            engines,
            validate_docx_artifact,
            stage_mode="directory",
            stage_dir_prefix="~fcp_pdf_stage_",
            staged_prefix="~fcp_pdf_word_",
            staged_suffix=".docx",
        )
        if result.success:
            return True
        self._last_batch_error = "PDF to Word conversion failed: " + result.error
        return False

    def _batch_to_png(self, fp: str, out: str, ext: str, *, backup_prepared: bool = False) -> bool:
        """Route a single file to PNG (one PNG per page for PDFs)."""
        self._last_batch_error = ""
        if not backup_prepared:
            backup_ok, backup_error = self._prepare_batch_backup(fp)
            if not backup_ok:
                self._last_batch_error = backup_error
                print(f"[BATCH] Backup failed for {Path(fp).name}: {backup_error}")
                return False
        if ext in _BATCH_IMAGE_EXTS:
            from converter.artifact_validators import validator_for_extension

            def _save_png(target):
                with self._open_batch_image(fp) as image:
                    image.save(target, format="PNG")
                return True

            result = run_conversion_pipeline(
                out,
                [("Pillow", _save_png)],
                validator_for_extension("png"),
                stage_mode="file",
                staged_prefix="~fcp_png_",
                staged_suffix=".png",
                include_engine_labels=False,
            )
            if result.success:
                return True
            self._last_batch_error = "Image to PNG conversion failed: " + result.error
            print(f"[BATCH] Image->PNG failed for {Path(fp).name}: {result.error}")
            return False
        if ext == ".pdf":
            try:
                if self._pdf_to_png(fp, out):
                    return True
            except Exception as e:
                self._last_batch_error = f"PDF to PNG conversion failed: {e}"
                return False
            self._last_batch_error = "PDF to PNG conversion failed"
            return False
        if ext in (".docx", ".doc"):
            tmp_pdf = self._batch_temp_file()
            try:
                if not self._batch_to_pdf(fp, tmp_pdf, ext, backup_prepared=True):
                    return False
                try:
                    if self._pdf_to_png(tmp_pdf, out):
                        return True
                except Exception as e:
                    self._last_batch_error = f"PDF to PNG conversion failed: {e}"
                    return False
                self._last_batch_error = "PDF to PNG conversion failed"
                return False
            finally:
                self._batch_remove_temp(tmp_pdf)
        if ext in _BATCH_RECOGNIZED_IMAGE_EXTS:
            return self._batch_unsupported(ext, "png")
        conv = _batch_conversion_type(ext, "pdf")
        if conv:
            tmp_dir = tempfile.mkdtemp()
            try:
                from converter.converters import AdvancedConverterEngine

                engine = AdvancedConverterEngine()
                engine.allow_local_html_resources = getattr(self, "config", {}).get(
                    "allow_local_resources_in_html_to_pdf", False
                )
                result = engine.convert(conv, fp, tmp_dir, skip_backup=True)
                if not result.success:
                    self._last_batch_error = (
                        result.error or f"Batch conversion failed for {Path(fp).name}"
                    )
                    return False
                tmp_pdf = os.path.join(tmp_dir, f"{Path(fp).stem}.pdf")
                if not os.path.exists(tmp_pdf):
                    self._last_batch_error = "Intermediate PDF was not produced"
                    return False
                try:
                    if self._pdf_to_png(tmp_pdf, out):
                        return True
                except Exception as e:
                    self._last_batch_error = f"PDF to PNG conversion failed: {e}"
                    return False
                self._last_batch_error = "PDF to PNG conversion failed"
                return False
            finally:
                self._batch_remove_temp(tmp_dir)
        return self._batch_unsupported(ext, "png")

    @staticmethod
    def _batch_copy_result(src: str, dst: str) -> tuple[bool, str]:
        import shutil

        try:
            shutil.copy2(src, dst)
        except Exception as e:
            return False, str(e) or type(e).__name__
        if not os.path.exists(dst):
            return False, "destination file was not created"
        return True, ""

    @staticmethod
    def _batch_copy(src: str, dst: str) -> bool:
        return BatchMixin._batch_copy_result(src, dst)[0]

    def _batch_copy_checked(self, src: str, dst: str) -> bool:
        self._last_batch_error = ""
        copied, error = self._batch_copy_result(src, dst)
        if copied:
            return True
        self._last_batch_error = f"File copy failed for {Path(src).name}: {error}"
        return False

    def _batch_image_to_docx(self, fp: str, out: str) -> bool:
        self._last_batch_error = ""
        try:
            from docx import Document
            from docx.shared import Inches

            with tempfile.TemporaryDirectory(prefix="~fcp_batch_image_") as temp_dir:
                normalized = os.path.join(temp_dir, "image.png")
                with self._open_batch_image(fp) as image:
                    image.save(normalized, format="PNG")
                doc = Document()
                doc.add_picture(normalized, width=Inches(6.0))
            doc.save(out)
            return os.path.exists(out)
        except Exception as e:
            self._last_batch_error = f"Image to DOCX conversion failed: {e}"
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
            item.setData(Qt.UserRole + 1, "folder" if os.path.isdir(file_path) else "file")
            if os.path.isfile(file_path):
                item.setData(Qt.UserRole + 4, self.format_size(os.path.getsize(file_path)))
            item.setToolTip(file_path)
            self.files_list_widget.addItem(item)
            self._attach_preview_btn(item, file_path)

        self.update_file_counter()
        QMessageBox.information(
            self, self.translate_text("success"), f"{success_count} {self.translate_text('files_renamed')}"
        )

    def get_output_directory(self, filename: str | None = None) -> str:
        default_dir = self.config.get("default_output_folder")
        if filename:
            start_dir = (
                os.path.join(default_dir, filename) if (default_dir and os.path.exists(default_dir)) else filename
            )
            ext = Path(filename).suffix.lower()
            if ext == ".pdf":
                file_filter = self.translate_text("pdf_files_pdf_2")
            elif ext in (".docx", ".doc"):
                file_filter = "Word Files (*.docx)"
            else:
                file_filter = "All files (*.*)"
            return QFileDialog.getSaveFileName(self, self.translate_text("save_file"), start_dir, file_filter)[0]
        else:
            if default_dir and os.path.exists(default_dir):
                return default_dir
            else:
                return QFileDialog.getExistingDirectory(self, self.translate_text("select_destination_folder_2"))
