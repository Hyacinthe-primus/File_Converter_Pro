"""PdfToWordMixin - PDF to DOCX conversion methods."""

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pdf_text import convert_pdf_text_to_docx
from templates import semantic_keys as sk

try:
    from pdf2docx import Converter as _Converter

    Converter = _Converter
except ImportError as _e:
    Converter = None
    print(f"[IMPORT] pdf2docx not available: {_e}")

try:
    from pypdf import PdfReader
except ImportError as _e:
    PdfReader = None
    print(f"[IMPORT] pypdf not available: {_e}")

try:
    from docx import Document
except ImportError as _e:
    Document = None
    print(f"[IMPORT] python-docx not available: {_e}")

from context_menu.conversion_helpers import _solid_fitz_fallback as _solid_fitz_fallback_impl
from dialogs import PdfToWordDialog
from utils.conversion_pipeline import run_conversion_pipeline
from utils.pdf_artifacts import validate_docx_artifact
from widgets import AnimatedCheckBox


class PdfToWordMixin:
    """Mixin: PDF → Word/DOCX conversion for FileConverterApp."""

    def check_pdf_has_images(self, pdf_path):
        try:
            import fitz

            doc = fitz.open(pdf_path)
            has_images = False
            for page in doc:
                if page.get_images():
                    has_images = True
                    break
            doc.close()
            return has_images
        except Exception:
            return False

    def handle_encrypted_pdfs(self, encrypted_pdfs):
        dialog = QDialog(self)
        dialog.setWindowTitle(self.translate_text("password_protected_pdfs"))
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout(dialog)

        if len(encrypted_pdfs) == 1:
            message = self.translate_text(f"Le fichier '{Path(encrypted_pdfs[0]).name}' est protégé par mot de passe.")
        else:
            message = self.translate_text(f"{len(encrypted_pdfs)} fichiers PDF sont protégés par mot de passe.")

        message += "\n\n" + self.translate_text(
            "to_convert_these_files_to_word_you_must_provide_the_passwords"
        )
        message += self.translate_text("options")

        info_label = QLabel(message)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-weight: bold; color: #d35400; padding: 10px;")
        layout.addWidget(info_label)

        tab_widget = QTabWidget()

        single_tab = QWidget()
        single_layout = QVBoxLayout(single_tab)

        if len(encrypted_pdfs) == 1:
            single_layout.addWidget(QLabel(self.translate_text(f"Fichier : {Path(encrypted_pdfs[0]).name}")))
            single_password_input = QLineEdit()
            single_password_input.setEchoMode(QLineEdit.Password)
            single_password_input.setPlaceholderText(self.translate_text("pdf_password"))

            single_layout.addWidget(QLabel(self.translate_text("password_2")))
            single_layout.addWidget(single_password_input)

            dialog.single_password_input = single_password_input
            dialog.single_pdf = encrypted_pdfs[0]

        multiple_tab = QWidget()
        multiple_layout = QVBoxLayout(multiple_tab)

        if len(encrypted_pdfs) > 1:
            scroll_area = QScrollArea()
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)

            password_inputs = {}

            for pdf_file in encrypted_pdfs:
                group = QGroupBox(Path(pdf_file).name)
                group_layout = QVBoxLayout(group)

                password_input = QLineEdit()
                password_input.setEchoMode(QLineEdit.Password)
                password_input.setPlaceholderText(self.translate_text("password_leave_empty_if_none"))

                group_layout.addWidget(QLabel(self.translate_text("password_2")))
                group_layout.addWidget(password_input)

                password_inputs[pdf_file] = password_input
                scroll_layout.addWidget(group)

            scroll_widget.setLayout(scroll_layout)
            scroll_area.setWidget(scroll_widget)
            scroll_area.setWidgetResizable(True)
            multiple_layout.addWidget(scroll_area)

            dialog.password_inputs = password_inputs

        same_tab = QWidget()
        same_layout = QVBoxLayout(same_tab)

        same_password_input = QLineEdit()
        same_password_input.setEchoMode(QLineEdit.Password)
        same_password_input.setPlaceholderText(self.translate_text("common_password_for_all_pdfs"))

        same_layout.addWidget(QLabel(self.translate_text("this_password_will_be_tried_on_all_encrypted_pdfs")))
        same_layout.addWidget(QLabel(self.translate_text("common_password_2")))
        same_layout.addWidget(same_password_input)

        dialog.same_password_input = same_password_input

        if len(encrypted_pdfs) == 1:
            tab_widget.addTab(single_tab, self.translate_text("single_pdf"))
        else:
            tab_widget.addTab(multiple_tab, self.translate_text("multiple_pdfs"))
            tab_widget.addTab(same_tab, self.translate_text("common_password"))

        layout.addWidget(tab_widget)

        options_group = QGroupBox(self.translate_text("output_options"))
        options_layout = QVBoxLayout(options_group)

        keep_encrypted_check = AnimatedCheckBox(
            self.translate_text("keep_original_encrypted_versions_after_conversion")
        )
        keep_encrypted_check.setChecked(True)

        remove_passwords_check = AnimatedCheckBox(
            self.translate_text("remove_password_protection_from_converted_pdfs_recommended")
        )
        remove_passwords_check.setChecked(True)

        options_layout.addWidget(keep_encrypted_check)
        options_layout.addWidget(remove_passwords_check)

        layout.addWidget(options_group)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        def collect_passwords():
            passwords = {}

            if len(encrypted_pdfs) == 1:
                password = dialog.single_password_input.text()
                if password:
                    passwords[dialog.single_pdf] = password
            else:
                if tab_widget.currentIndex() == 0:
                    for pdf_file, password_input in dialog.password_inputs.items():
                        password = password_input.text()
                        if password:
                            passwords[pdf_file] = password
                else:
                    common_password = dialog.same_password_input.text()
                    if common_password:
                        for pdf_file in encrypted_pdfs:
                            passwords[pdf_file] = common_password

            dialog.passwords = passwords
            dialog.keep_originals = keep_encrypted_check.isChecked()
            dialog.remove_passwords = remove_passwords_check.isChecked()
            dialog.accept()

        button_box.accepted.connect(collect_passwords)
        button_box.rejected.connect(dialog.reject)

        layout.addWidget(button_box)

        if dialog.exec() == QDialog.Accepted:
            if hasattr(dialog, "passwords") and dialog.passwords:
                return {
                    "passwords": dialog.passwords,
                    "keep_originals": dialog.keep_originals,
                    "remove_passwords": dialog.remove_passwords,
                }
            else:
                QMessageBox.warning(
                    self,
                    self.translate_text("warning"),
                    self.translate_text("no_password_provided_the_conversion_will_be_cancelled"),
                )
                return False
        else:
            return False

    def decrypt_pdfs_before_conversion(self, pdf_files, passwords_info):
        temp_files = []
        success_count = 0
        failed_files = []

        passwords = passwords_info.get("passwords", {})
        keep_originals = passwords_info.get("keep_originals", True)
        remove_passwords = passwords_info.get("remove_passwords", True)

        self.show_progress(True, self.translate_text("decrypting_pdfs"))

        for i, pdf_file in enumerate(pdf_files):
            try:
                with open(pdf_file, "rb") as f:
                    pdf_reader = PdfReader(f)

                    if pdf_reader.is_encrypted:
                        password = passwords.get(pdf_file)

                        if not password:
                            try:
                                pdf_reader.decrypt("")
                            except Exception:
                                failed_files.append(
                                    f"{Path(pdf_file).name} - {self.translate_text('password_required')}"
                                )
                                continue
                        else:
                            success = pdf_reader.decrypt(password)

                            if not success:
                                for pwd_variation in [password, password.lower(), password.upper()]:
                                    try:
                                        success = pdf_reader.decrypt(pwd_variation)
                                        if success:
                                            break
                                    except Exception:
                                        continue

                                if not success:
                                    failed_files.append(
                                        f"{Path(pdf_file).name} - {self.translate_text('incorrect_password')}"
                                    )
                                    continue

                        pdf_writer = __import__("pypdf", fromlist=["PdfWriter"]).PdfWriter()

                        for page in pdf_reader.pages:
                            pdf_writer.add_page(page)

                        original_stem = Path(pdf_file).stem
                        temp_file = os.path.join(tempfile.gettempdir(), f"{original_stem}_decrypted.pdf")

                        counter = 1
                        while os.path.exists(temp_file):
                            temp_file = os.path.join(tempfile.gettempdir(), f"{original_stem}_decrypted_{counter}.pdf")
                            counter += 1
                        self.temp_files.append(temp_file)

                        with open(temp_file, "wb") as output_file:
                            if remove_passwords:
                                pdf_writer.write(output_file)
                            else:
                                pdf_writer.encrypt(password)
                                pdf_writer.write(output_file)

                        temp_files.append(temp_file)
                        success_count += 1

                        if not keep_originals:
                            backup_file = pdf_file + ".backup"
                            shutil.copy2(pdf_file, backup_file)
                            shutil.copy2(temp_file, pdf_file)
                            temp_files.append(backup_file)
                    else:
                        temp_files.append(pdf_file)
                        success_count += 1

            except Exception as e:
                error_msg = f"{Path(pdf_file).name} - {str(e)}"
                failed_files.append(error_msg)
                print(f"Decryption error {pdf_file}: {e}")

            self.progress_bar.setValue(int((i + 1) / len(pdf_files) * 100))

        self.show_progress(False)

        if failed_files:
            error_message = self.translate_text(
                f"{success_count}/{len(pdf_files)} PDF(s) déchiffré(s) avec succès.\n\n"
            )
            error_message += self.translate_text(f"Échecs ({len(failed_files)}):\n")
            error_message += "\n".join(failed_files[:3])

            if len(failed_files) > 3:
                error_message += f"\n... et {len(failed_files) - 3} autres"

            QMessageBox.warning(self, self.translate_text("decryption_result"), error_message)

        return temp_files

    def convert_pdfs_without_images(self, pdf_files):
        output_dir = self.get_output_directory()
        if not output_dir:
            return

        message = self.translate_text("conversion_pdf_to_word").format(len(pdf_files))
        self.show_progress(True, message)

        success_count = 0
        failed_files = []
        start_time = datetime.now()

        for i, file_path in enumerate(pdf_files):
            try:
                output_file = os.path.join(output_dir, f"{Path(file_path).stem}.docx")
                file_size = os.path.getsize(file_path)

                operation_start = datetime.now()

                current_mode = self.config.get("pdf_to_word_mode", "with_images")
                if current_mode == "with_images":
                    ok = self.convert_pdf_to_docx_improved(file_path, output_file)
                else:
                    ok = self.convert_pdf_to_docx_text_only(file_path, output_file)
                if ok is False:
                    raise RuntimeError(
                        getattr(self, "_last_pdf_to_word_error", "") or "PDF to Word conversion failed"
                    )

                operation_time = (datetime.now() - operation_start).total_seconds()
                self.achievement_system.record_conversion("pdf_to_word", file_size, True)
                self.achievement_system.mark_format_as_used("pdf")
                self.achievement_system.mark_format_as_used("docx")

                self.db_manager.add_conversion_record(
                    source_file=file_path,
                    source_format="PDF",
                    target_file=output_file,
                    target_format="DOCX",
                    operation_type="pdf_to_word",
                    file_size=file_size,
                    conversion_time=operation_time,
                    success=True,
                    notes=f"Mode: {current_mode}",
                )

                success_count += 1
                self.progress_bar.setValue(int((i + 1) / len(pdf_files) * 100))

            except Exception as e:
                self.db_manager.add_conversion_record(
                    source_file=file_path,
                    source_format="PDF",
                    target_file="",
                    target_format="DOCX",
                    operation_type="pdf_to_word",
                    file_size=0,
                    conversion_time=0,
                    success=False,
                    notes=f"Error: {str(e)}",
                )
                failed_files.append(f"{Path(file_path).name}: {e}")
                QMessageBox.critical(
                    self,
                    self.translate_text("error"),
                    self.translate_text(f"Erreur avec {Path(file_path).name}: {str(e)}"),
                )

        total_time = (datetime.now() - start_time).total_seconds()
        self.show_progress(False)

        if success_count > 0 and 0 <= datetime.now().hour < 6:
            self.achievement_system.increment_stat("night_conversions", success_count)
            self.achievement_system.check_achievement("night_owl")

        if success_count >= 50 and total_time <= 300:
            self.achievement_system.update_stat("recent_batch_files", success_count)
            self.achievement_system.update_stat("recent_batch_time", total_time)
            self.achievement_system.check_speed_conversion(success_count, total_time)

        formatted_time = f"{total_time:.1f}"
        message = self.translate_text("pdf_to_word_success_sum").format(success_count, len(pdf_files), formatted_time)
        if failed_files or success_count < len(pdf_files):
            if failed_files:
                message += "\n\n" + "\n".join(failed_files)
            QMessageBox.warning(self, self.translate_text("warning"), message)
            return
        if self.config.get("enable_system_notifications", True):
            self.system_notifier.send("pdf_to_word")
        QMessageBox.information(self, self.translate_text("success"), message)

    def _get_chart_regions(self, page):
        MIN_PATHS = 8
        MIN_AREA = 8000
        PADDING = 10
        MERGE_GAP = 20

        import fitz

        drawings = page.get_drawings()
        if not drawings:
            return []

        path_rects = [fitz.Rect(d["rect"]) for d in drawings if d.get("rect")]
        if len(path_rects) < MIN_PATHS:
            return []

        path_rects.sort(key=lambda r: (r.y0, r.x0))
        clusters = []
        cur = fitz.Rect(path_rects[0])
        count = 1

        for r in path_rects[1:]:
            expanded = fitz.Rect(cur.x0 - MERGE_GAP, cur.y0 - MERGE_GAP, cur.x1 + MERGE_GAP, cur.y1 + MERGE_GAP)
            if expanded.intersects(r):
                cur = fitz.Rect(min(cur.x0, r.x0), min(cur.y0, r.y0), max(cur.x1, r.x1), max(cur.y1, r.y1))
                count += 1
            else:
                if count >= MIN_PATHS and cur.get_area() >= MIN_AREA:
                    clusters.append(cur)
                cur = fitz.Rect(r)
                count = 1

        if count >= MIN_PATHS and cur.get_area() >= MIN_AREA:
            clusters.append(cur)

        page_rect = page.rect
        result = []
        for c in clusters:
            padded = fitz.Rect(
                max(0, c.x0 - PADDING),
                max(0, c.y0 - PADDING),
                min(page_rect.x1, c.x1 + PADDING),
                min(page_rect.y1, c.y1 + PADDING),
            )
            result.append(padded)

        return result

    def _rasterize_region(self, page, rect, dpi=150):
        import fitz

        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        fitz.IRect(
            int(rect.x0 * zoom),
            int(rect.y0 * zoom),
            int(rect.x1 * zoom),
            int(rect.y1 * zoom),
        )
        pix = page.get_pixmap(matrix=matrix, clip=rect, alpha=False)
        return pix.tobytes("png")

    def _try_word_com_pdf_to_docx(self, pdf_path, docx_path):
        import sys

        if sys.platform != "win32":
            return False

        try:
            import winreg

            winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "Word.Application")
        except (OSError, ImportError):
            print("[PDF→DOCX] Word not found in registry — skipping COM tier")
            return False

        import os
        import threading

        pdf_path = os.path.abspath(pdf_path)
        docx_path = os.path.abspath(docx_path)

        result = {"ok": False}
        stop_event = threading.Event()

        def _dialog_dismisser():
            import ctypes
            import ctypes.wintypes

            user32 = ctypes.windll.user32
            BM_CLICK = 0x00F5

            DialogProc = ctypes.WINFUNCTYPE(
                ctypes.c_bool,
                ctypes.wintypes.HWND,
                ctypes.wintypes.LPARAM,
            )

            def _find_ok_button(hwnd_dialog):
                found = ctypes.wintypes.HWND(0)

                @DialogProc
                def _enum(hwnd_child, _lp):
                    buf = ctypes.create_unicode_buffer(64)
                    user32.GetWindowTextW(hwnd_child, buf, 64)
                    if buf.value.strip().upper() in ("OK", "O&K"):
                        found.value = hwnd_child
                        return False
                    ctrl_id = user32.GetDlgCtrlID(hwnd_child)
                    if ctrl_id == 1:
                        found.value = hwnd_child
                        return False
                    return True

                user32.EnumChildWindows(hwnd_dialog, _enum, 0)
                return found.value or None

            dialog_classes = ["#32770", "bosa_sdm_msword"]
            target_title = "Microsoft Word"

            while not stop_event.is_set():
                for cls in dialog_classes:
                    hwnd = user32.FindWindowW(cls, None)
                    if hwnd:
                        ok_btn = _find_ok_button(hwnd)
                        if ok_btn:
                            user32.SendMessageW(ok_btn, BM_CLICK, 0, 0)
                        else:
                            user32.SendMessageW(hwnd, 0x0111, 1, 0)
                hwnd = user32.FindWindowW(None, target_title)
                if hwnd:
                    ok_btn = _find_ok_button(hwnd)
                    if ok_btn:
                        user32.SendMessageW(ok_btn, BM_CLICK, 0, 0)
                    else:
                        user32.SendMessageW(hwnd, 0x0111, 1, 0)
                import time as _t

                _t.sleep(0.3)

        def _worker():
            word = None
            doc = None
            try:
                import comtypes.client
                import pythoncom

                pythoncom.CoInitialize()
                word = comtypes.client.CreateObject("Word.Application")
                word.Visible = False
                word.DisplayAlerts = 0
                word.AutomationSecurity = 3

                doc = word.Documents.Open(
                    pdf_path,
                    ConfirmConversions=False,
                    ReadOnly=True,
                    AddToRecentFiles=False,
                    NoEncodingDialog=True,
                )
                doc.SaveAs2(docx_path, FileFormat=16)
                result["ok"] = True
                print(f"[PDF→DOCX] Word COM success: {os.path.basename(pdf_path)}")
            except Exception as e:
                print(f"[PDF→DOCX] Word COM failed: {e}")
            finally:
                if doc is not None:
                    try:
                        doc.Close(False)
                    except Exception:
                        pass
                if word is not None:
                    try:
                        word.Quit()
                    except Exception:
                        pass
                try:
                    import pythoncom

                    pythoncom.CoUninitialize()
                except Exception:
                    pass

        dismisser = threading.Thread(target=_dialog_dismisser, daemon=True)
        dismisser.start()

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        t.join(timeout=60)

        stop_event.set()

        if t.is_alive():
            print("[PDF→DOCX] Word COM timed out — falling back to pdf2docx")
            return False

        return result["ok"]

    def _convert_pdf_to_docx_libreoffice(self, pdf_path, docx_path, timeout: int = 120) -> bool:
        """Convert PDF → DOCX via LibreOffice headless. Returns True on success."""
        import subprocess

        from external_binaries import resolve_binary

        soffice = resolve_binary("libreoffice")
        if not soffice:
            print("[PDF→DOCX] LibreOffice not found — skipping tier")
            return False

        output_dir = os.path.dirname(docx_path)
        try:
            result = subprocess.run(
                [soffice, "--headless", "--convert-to", "docx", "--outdir", output_dir, pdf_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            expected_docx = os.path.join(output_dir, os.path.splitext(os.path.basename(pdf_path))[0] + ".docx")
            if os.path.exists(expected_docx):
                if os.path.abspath(expected_docx) != os.path.abspath(docx_path):
                    os.replace(expected_docx, docx_path)
                print(f"[PDF→DOCX] LibreOffice success: {docx_path}")
                return True
            print(f"[PDF→DOCX] LibreOffice failed: {result.stderr}")
            return False
        except subprocess.TimeoutExpired:
            print("[PDF→DOCX] LibreOffice timed out")
            return False
        except Exception as e:
            print(f"[PDF→DOCX] LibreOffice error: {e}")
            return False

    def _try_pdf2docx(self, pdf_path, docx_path):
        if Converter is None:
            print("[PDF→DOCX] pdf2docx not available — skipping Tier 2")
            return False
        try:
            cv = Converter(pdf_path)
            cv.convert(docx_path, start=0, end=None, parse_drawing=True)
            cv.close()
            print(f"[PDF→DOCX] pdf2docx success: {Path(pdf_path).name}")
            return True
        except Exception as e:
            print(f"[PDF→DOCX] pdf2docx failed: {e}")
            return False

    def _solid_fitz_fallback(self, pdf_path, docx_path):
        _solid_fitz_fallback_impl(pdf_path, docx_path)

    def _convert_pdf_to_docx_pdf2docx_with_charts(self, pdf_path, docx_path):
        import io as _io

        import fitz

        if not self._try_pdf2docx(pdf_path, docx_path):
            return False

        try:
            pdf_doc = fitz.open(pdf_path)
            docx = Document(docx_path)

            charts_per_page = {}
            for page_num in range(len(pdf_doc)):
                page = pdf_doc.load_page(page_num)
                rects = self._get_chart_regions(page)
                if not rects:
                    continue
                imgs = []
                for rect in rects:
                    png_bytes = self._rasterize_region(page, rect, dpi=150)
                    imgs.append(_io.BytesIO(png_bytes))
                charts_per_page[page_num] = imgs

            pdf_doc.close()

            if charts_per_page:
                import copy

                from docx.shared import Inches as _Inches

                def _add_picture_paragraph(docx_doc, img_buf, max_width_inches=5.5):
                    p = docx_doc.add_paragraph()
                    p.alignment = 1
                    run = p.add_run()
                    run.add_picture(img_buf, width=_Inches(max_width_inches))
                    return p

                def _insert_para_after(ref_para, new_para_xml):
                    ref_para._element.addnext(new_para_xml)

                body_paras = docx.paragraphs
                page_break_indices = []
                for idx, para in enumerate(body_paras):
                    for run in para.runs:
                        if (
                            run._element.xml.find("w:lastRenderedPageBreak") != -1
                            or run._element.xml.find("w:br") != -1
                        ):
                            page_break_indices.append(idx)
                            break

                for page_num in sorted(charts_per_page.keys()):
                    imgs = charts_per_page[page_num]
                    if page_num == 0 or page_num - 1 >= len(page_break_indices):
                        for img_buf in imgs:
                            _add_picture_paragraph(docx, img_buf)
                    else:
                        ref_idx = page_break_indices[page_num - 1]
                        ref_para = body_paras[ref_idx]
                        for img_buf in reversed(imgs):
                            tmp_doc = Document()
                            pic_para = _add_picture_paragraph(tmp_doc, img_buf)
                            _insert_para_after(ref_para, copy.deepcopy(pic_para._element))

                docx.save(docx_path)
        except Exception as e:
            print(f"[chart injection] {e}")

        return True

    def convert_pdf_to_docx_with_charts(self, pdf_path, docx_path):
        engines = [
            ("COM", lambda target: self._try_word_com_pdf_to_docx(pdf_path, target)),
            (
                "pdf2docx",
                lambda target: self._convert_pdf_to_docx_pdf2docx_with_charts(pdf_path, target),
            ),
            ("fitz fallback", lambda target: self._solid_fitz_fallback(pdf_path, target)),
        ]
        result = run_conversion_pipeline(
            os.path.abspath(docx_path),
            engines,
            validate_docx_artifact,
            stage_mode="file",
            staged_prefix="~fcp_pdf_word_",
            staged_suffix=".docx",
        )
        self._last_pdf_to_word_error = result.error
        return result.success

    def convert_pdf_to_docx_improved(self, pdf_path, docx_path):
        return self.convert_pdf_to_docx_with_charts(pdf_path, docx_path)

    def convert_pdf_to_docx_text_only(self, pdf_path, docx_path):
        engines = [
            ("text extraction", lambda target: convert_pdf_text_to_docx(pdf_path, target)),
            ("fitz fallback", lambda target: self._solid_fitz_fallback(pdf_path, target)),
        ]
        result = run_conversion_pipeline(
            os.path.abspath(docx_path),
            engines,
            validate_docx_artifact,
            stage_mode="file",
            staged_prefix="~fcp_pdf_word_",
            staged_suffix=".docx",
        )
        self._last_pdf_to_word_error = result.error
        return result.success

    def convert_pdf_to_word(self):
        if not (hasattr(self, "active_templates") and sk.PDF_TO_WORD in self.active_templates):
            _def_id, _ = (self._ensure_template_manager() or object()).get_default_template(sk.PDF_TO_WORD)
            if _def_id:
                (self._ensure_template_manager() or object()).apply_template(_def_id, self)

        selected_items = self.files_list_widget.selectedItems()
        files_to_process = []
        if selected_items:
            for i in range(self.files_list_widget.count()):
                item = self.files_list_widget.item(i)
                if item.isSelected():
                    files_to_process.append(item.data(Qt.UserRole))
        else:
            files_to_process = [f for f in self.files_list if f.lower().endswith(".pdf")]

        pdf_files = [f for f in files_to_process if f.lower().endswith(".pdf")]
        if not pdf_files:
            msg = (
                self.translate_text("please_select_at_least_one_pdf_file")
                if selected_items
                else self.translate_text("the_list_must_contain_at_least_one_pdf_file")
            )
            QMessageBox.warning(self, self.translate_text("warning"), msg)
            return

        encrypted_pdfs = []
        for pdf_file in pdf_files:
            try:
                with open(pdf_file, "rb") as f:
                    pdf_reader = PdfReader(f)
                    if pdf_reader.is_encrypted:
                        encrypted_pdfs.append(pdf_file)
            except Exception as e:
                print(f"PDF verification error {pdf_file}: {e}")

        if encrypted_pdfs:
            response = self.handle_encrypted_pdfs(encrypted_pdfs)
            if response is False:
                return
            elif response is not None:
                passwords = response
                pdf_files = self.decrypt_pdfs_before_conversion(pdf_files, passwords)
                print(f"[DEBUG] {len(encrypted_pdfs)} password-protected PDF files successfully converted.")
                self.achievement_system.record_protected_file_conversion(len(encrypted_pdfs), "pdf")
                if not pdf_files:
                    return

        pdfs_with_images = []
        for pdf_file in pdf_files:
            if self.check_pdf_has_images(pdf_file):
                pdfs_with_images.append(pdf_file)

        if not pdfs_with_images:
            self.convert_pdfs_without_images(pdf_files)
            return

        if hasattr(self, "active_templates") and sk.PDF_TO_WORD in self.active_templates:
            conversion_mode = self.active_templates[sk.PDF_TO_WORD].get("mode", "with_images")
        else:
            current_mode = self.config.get("pdf_to_word_mode", "with_images")
            dialog = PdfToWordDialog(self, self.current_language, current_mode)
            if dialog.exec() != QDialog.Accepted:
                return
            conversion_mode = dialog.get_conversion_mode()

        output_dir = self.get_output_directory()
        if not output_dir:
            return

        message = self.translate_text("conversion_pdf_to_word").format(len(pdf_files))
        self.show_progress(True, message)
        self._set_ui_enabled(False)

        _mode = conversion_mode
        _outdir = output_dir

        def _run_pdf_to_word(task):
            import os
            import time as _time

            t0 = _time.perf_counter()
            fp = task["input_path"]
            out = task["output_path"]
            fs = os.path.getsize(fp) if os.path.exists(fp) else 0
            if _mode == "with_images":
                ok = self.convert_pdf_to_docx_improved(fp, out)
            else:
                ok = self.convert_pdf_to_docx_text_only(fp, out)
            if ok is False:
                return {
                    "success": False,
                    "error": getattr(self, "_last_pdf_to_word_error", "")
                    or "PDF to Word conversion failed",
                    "file_size": fs,
                    "operation_time": _time.perf_counter() - t0,
                }
            return {
                "success": True,
                "error": "",
                "output_path": out,
                "file_size": fs,
                "operation_time": _time.perf_counter() - t0,
            }

        tasks = [
            {
                "index": i,
                "total": len(pdf_files),
                "input_path": fp,
                "output_path": os.path.join(_outdir, f"{Path(fp).stem}.docx"),
            }
            for i, fp in enumerate(pdf_files)
        ]
        from conversion_worker import ConversionWorker

        self._pdf_to_word_worker = ConversionWorker(tasks, _run_pdf_to_word)
        self._pdf_to_word_worker.file_done.connect(self._on_pdf_to_word_file_done)

        def _on_pdf_to_word_finished(s):
            self.show_progress(False)
            self._set_ui_enabled(True)
            if s["success_count"] > 0:
                self.record_config_usage(sk.PDF_TO_WORD, {"mode": _mode})
            msg = self.translate_text("pdf_to_word_success_sum").format(
                s["success_count"], s["total"], f"{s['total_time']:.1f}"
            )
            failed = s.get("failed", [])
            if failed or s["success_count"] < s["total"]:
                failure_lines = [
                    self.translate_text("error_with_file").format(
                        filename=Path(item.get("name", "?")).name,
                        error=item.get("error", ""),
                    )
                    for item in failed
                ]
                if failure_lines:
                    msg = f"{msg}\n\n" + "\n".join(failure_lines)
                QMessageBox.warning(self, self.translate_text("warning"), msg)
                return
            if self.config.get("enable_system_notifications", True):
                self.system_notifier.send("pdf_to_word")
            QMessageBox.information(self, self.translate_text("success"), msg)

        self._pdf_to_word_worker.finished.connect(_on_pdf_to_word_finished)
        self._pdf_to_word_worker.error.connect(
            lambda e: (
                self.show_progress(False),
                self._set_ui_enabled(True),
                QMessageBox.critical(self, self.translate_text("error"), str(e)),
            )
        )
        self._pdf_to_word_worker.start()

    def _on_pdf_to_word_file_done(self, result):
        fp = result.get("input_path", "?")
        fs = result.get("file_size", 0)
        if result.get("success"):
            self.achievement_system.record_conversion("pdf_to_word", fs, True)
            self.achievement_system.mark_format_as_used("pdf")
            self.achievement_system.mark_format_as_used("docx")
            self.db_manager.add_conversion_record(
                source_file=fp,
                source_format="PDF",
                target_file=result.get("output_path", ""),
                target_format="DOCX",
                operation_type="pdf_to_word",
                file_size=fs,
                conversion_time=result.get("operation_time", 0),
                success=True,
            )
        else:
            self.db_manager.add_conversion_record(
                source_file=fp,
                source_format="PDF",
                target_file="",
                target_format="DOCX",
                operation_type="pdf_to_word",
                file_size=0,
                conversion_time=0,
                success=False,
                notes=f"Error: {result.get('error', '')}",
            )
