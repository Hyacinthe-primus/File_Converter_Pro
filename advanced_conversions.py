"""
Advanced Conversions Dialog — File Converter Pro

What does it do?
    - Provides a dedicated interface for advanced conversion formats
    - Conversions are REAL (not placeholders).
    - File source: items selected in the main window's file list
      (or ALL files if nothing is selected).
    - Output folder: prompted once, then remembered per session.
    - Every result is recorded in the dedicated AdvancedDatabaseManager
      (file_converter_advanced.db) — separate from the main DB.
    - Progress is shown inline in the dialog (progress bar + log).
    - Worker thread keeps the UI responsive.

Author: Hyacinthe
Version: 1.0
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from PySide6.QtCore    import Qt, Signal, QThread, QObject
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTabWidget, QWidget, QScrollArea,
    QGridLayout, QGroupBox, QProgressBar, QTextEdit,
    QFileDialog, QMessageBox )

from converter import AdvancedDatabaseManager, AdvancedConverterEngine
from translations import TranslationManager


class _ConversionWorker(QObject):
    """
    Runs conversions off the main thread.
    """
    progress = Signal(int, int, str)
    log      = Signal(str)
    finished = Signal(int, int)

    def __init__(
        self,
        engine: AdvancedConverterEngine,
        db: AdvancedDatabaseManager,
        conversion_type: str,
        sources: list[str],
        dst_dir: str,
        achievement_system=None,
        tm=None,
        config=None
    ) -> None:
        super().__init__()
        self.engine              = engine
        self.db                  = db
        self.conversion_type     = conversion_type
        self.sources             = sources
        self.dst_dir             = dst_dir
        self._cancelled          = False
        self.achievement_system  = achievement_system
        self._tm                 = tm
        self._config = config or {}

    def cancel(self) -> None:
        self._cancelled = True

    def _t(self, key: str, **kwargs) -> str:
        """Translate a key via the TranslationManager if available."""
        if self._tm is not None:
            tpl = self._tm.translate_text(key)
        else:
            tpl = key
        return tpl.format(**kwargs) if kwargs else tpl

    def run(self) -> None:
        _achievements_on = self._config.get("achievements_enabled", True)
        ok = fail = 0
        total = len(self.sources)
        _batch_start = time.time()

        if self.achievement_system is not None and _achievements_on:
            try:
                self.achievement_system.update_stat("recent_batch_files", 0)
            except Exception:
                pass

        for i, src in enumerate(self.sources, 1):
            if self._cancelled:
                self.log.emit(self._t("adv_log_cancelled"))
                break

            filename = Path(src).name
            self.log.emit(self._t("adv_log_converting", i=i, total=total, filename=filename))
            self.progress.emit(i - 1, total, filename)

            result = self.engine.convert(self.conversion_type, src, self.dst_dir)

            from converter.converters import CATEGORY_MAP
            category = CATEGORY_MAP.get(self.conversion_type, "document")

            self.db.add_record(
                source_file     = result.source,
                source_format   = Path(result.source).suffix.lstrip(".").upper(),
                target_file     = result.target,
                target_format   = Path(result.target).suffix.lstrip(".").upper()
                                  if result.success else "",
                conversion_type = self.conversion_type,
                category        = category,
                file_size       = result.file_size,
                conversion_time = result.elapsed,
                success         = result.success,
                error_message   = result.error,
            )

            if result.success:
                ok += 1
                self.log.emit(self._t("adv_log_success",
                                      target=Path(result.target).name,
                                      elapsed=result.elapsed))
                if self.achievement_system is not None and _achievements_on:
                    try:
                        self.achievement_system.record_advanced_conversion(
                            self.conversion_type, success=True
                        )
                    except Exception as _e:
                        print(f"[ADV ACH] Error: {_e}")
            else:
                fail += 1
                err_msg = result.error
                if "ne contient pas de piste audio" in err_msg:
                    self.log.emit(self._t("adv_log_no_audio", error=err_msg))
                else:
                    self.log.emit(self._t("adv_log_error", error=err_msg))
                if self.achievement_system is not None and _achievements_on:
                    try:
                        self.achievement_system.record_advanced_conversion(
                            self.conversion_type, success=False
                        )
                    except Exception as _e:
                        print(f"[ADV ACH] Error (fail): {_e}")

            self.progress.emit(i, total, filename)

        # Flash Gordon: check if the entire batch qualifies (>=50 files in <=5 min)
        if self.achievement_system is not None and ok > 0:
            try:
                _batch_time = time.time() - _batch_start
                self.achievement_system.update_stat("recent_batch_time", _batch_time)
                self.achievement_system.check_speed_conversion(ok, _batch_time)
            except Exception as _e:
                print(f"[ADV ACH] Flash Gordon check error: {_e}")

        self.finished.emit(ok, fail)


class AdvancedConversionsDialog(QDialog):
    """
    Dialog for advanced conversion formats.

    Reads files from the parent window's `files_list` attribute
    (or from selected items in `file_list_widget` if any are selected).
    Results are stored in the separate AdvancedDatabaseManager.
    """

    conversion_requested = Signal(str)

    def __init__(
        self,
        parent=None,
        language: str = "fr",
        advanced_db: AdvancedDatabaseManager | None = None,
    ) -> None:
        super().__init__(parent)
        self.parent_window = parent
        self.language      = language
        self._tm = TranslationManager(); self._tm.set_language(language)

        self.adv_db = advanced_db or AdvancedDatabaseManager()
        self.engine = AdvancedConverterEngine()

        self._last_dst_dir: str | None = None

        self._thread: QThread | None = None
        self._worker: _ConversionWorker | None = None

        self.setWindowTitle(self.tr_("🔄 Plus de Conversions"))
        self.setMinimumSize(900, 720)
        self.setModal(False)

        self._setup_ui()
        self._apply_theme_style()

    def _get_source_files(self, accepted_exts: list[str]) -> list[str]:
        """
        Returns the files to convert.

        Priority:
        1. Items *selected* in the parent's file_list_widget.
        2. All items in parent's files_list (if nothing selected).
        3. Empty list (user will be warned).

        Files are filtered by *accepted_exts* (e.g. ['.txt', '.rtf']).
        """
        files: list[str] = []

        if self.parent_window is not None:
            widget = getattr(self.parent_window, "files_list_widget", None)
            if widget is not None:
                selected = []
                for i in range(widget.count()):
                    item = widget.item(i)
                    if item.isSelected():
                        from PySide6.QtCore import Qt as _Qt
                        path = item.data(_Qt.UserRole) or item.text()
                        selected.append(path)
                if selected:
                    files = selected

            if not files:
                files = list(getattr(self.parent_window, "files_list", []))

        if accepted_exts:
            exts = {e.lower() for e in accepted_exts}
            files = [f for f in files if Path(f).suffix.lower() in exts]

        return files

    def _choose_dst_dir(self) -> str | None:
        """Return the output folder — uses the app default if configured, else asks the user."""
        if self.parent_window is not None:
            cfg = getattr(self.parent_window, "config", {})
            candidate = cfg.get("default_output_folder", "")
            if candidate and os.path.exists(candidate):
                return candidate

        folder = QFileDialog.getExistingDirectory(
            self,
            self.tr_("Choisir le dossier de sortie"),
            self._last_dst_dir or str(Path.home()),
        )
        if folder:
            self._last_dst_dir = folder
        return folder or None

    def _run_conversion(
        self,
        conversion_type: str,
        accepted_exts: list[str],
    ) -> None:
        """Resolve files, pick output folder, then start the worker thread."""

        try:
            running = self._thread is not None and self._thread.isRunning()
        except RuntimeError:
            running = False
            self._thread = None
            self._worker = None
        if running:
            QMessageBox.warning(
                self, self.tr_("En cours"),
                self.tr_("Une conversion est déjà en cours.")
            )
            return

        self.conversion_requested.emit(conversion_type)

        sources = self._get_source_files(accepted_exts)
        if not sources:
            QMessageBox.information(
                self, self.tr_("Aucun fichier"),
                self.tr_(
                    "Aucun fichier compatible trouvé dans la liste.\n"
                    "Ajoutez des fichiers dans la fenêtre principale d'abord."
                )
            )
            return

        dst_dir = self._choose_dst_dir()
        if not dst_dir:
            return
        self._log_area.clear()
        self._progress_bar.setValue(0)
        self._progress_bar.setMaximum(len(sources))
        self._progress_widget.setVisible(True)
        self._cancel_btn.setEnabled(True)

        _ach_sys = getattr(self.parent_window, 'achievement_system', None)
        worker = _ConversionWorker(
            self.engine, self.adv_db, conversion_type, sources, dst_dir,
            achievement_system=_ach_sys,
            tm=self._tm,
        )
        thread = QThread(self)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.log.connect(self._on_log)
        worker.progress.connect(self._on_progress)
        worker.finished.connect(self._on_finished)
        worker.finished.connect(thread.quit)
        def _cleanup():
            self._thread = None
            self._worker = None
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(_cleanup)

        self._worker = worker
        self._thread = thread
        thread.start()

    def _cancel_conversion(self) -> None:
        if self._worker:
            self._worker.cancel()
        self._cancel_btn.setEnabled(False)

    def _on_log(self, msg: str) -> None:
        self._log_area.append(msg)

    def _on_progress(self, done: int, total: int, filename: str) -> None:
        self._progress_bar.setValue(done)
        self._progress_bar.setFormat(f"{done}/{total}  —  {filename}")

    def _on_finished(self, ok: int, fail: int) -> None:
        self._cancel_btn.setEnabled(False)
        self._log_area.append("")
        if fail == 0:
            self._log_area.append(self.tr_("adv_log_all_ok").format(ok=ok))
        else:
            self._log_area.append(self.tr_("adv_log_partial").format(ok=ok, fail=fail))
        self._progress_bar.setValue(self._progress_bar.maximum())

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        title = QLabel(self.tr_("🔄 Conversions Avancées"))
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 4px;")
        layout.addWidget(title)

        subtitle = QLabel(self.tr_("Sélectionnez un format de conversion ci-dessous"))
        subtitle.setStyleSheet("font-size: 12px; color: #888; margin-bottom: 10px;")
        layout.addWidget(subtitle)

        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.tab_widget.setStyleSheet(self._tab_style(0))

        self.tab_widget.addTab(self._build_documents_tab(), self.tr_("📄 Documents"))
        self.tab_widget.addTab(self._build_images_tab(),    self.tr_("🖼️ Images"))
        self.tab_widget.addTab(self._build_av_tab(),        self.tr_("🎵 Audio/Vidéo"))

        layout.addWidget(self.tab_widget)

        self._progress_widget = QWidget()
        prog_layout = QVBoxLayout(self._progress_widget)
        prog_layout.setContentsMargins(0, 0, 0, 0)
        prog_layout.setSpacing(6)

        self._progress_bar = QProgressBar()
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFixedHeight(22)
        prog_layout.addWidget(self._progress_bar)

        self._log_area = QTextEdit()
        self._log_area.setReadOnly(True)
        self._log_area.setFixedHeight(120)
        self._log_area.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 11px;"
        )
        prog_layout.addWidget(self._log_area)

        self._progress_widget.setVisible(False)
        layout.addWidget(self._progress_widget)

        btn_row = QHBoxLayout()
        self._cancel_btn = QPushButton(self.tr_("⛔ Annuler la conversion"))
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.setStyleSheet(self._btn_style("cancel"))
        self._cancel_btn.clicked.connect(self._cancel_conversion)
        btn_row.addWidget(self._cancel_btn)

        btn_row.addStretch()

        close_btn = QPushButton(self.tr_("Fermer"))
        close_btn.setMinimumHeight(38)
        close_btn.setStyleSheet(self._btn_style("close"))
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _build_documents_tab(self) -> QWidget:
        groups = [
            (self.tr_("TXT / RTF"), [
                ("📄 TXT → PDF",  "txt_to_pdf",  [".txt"]),
                ("📄 RTF → PDF",  "rtf_to_pdf",  [".rtf"]),
                ("📄 TXT → DOCX", "txt_to_docx", [".txt"]),
                ("📄 RTF → DOCX", "rtf_to_docx", [".rtf"]),
            ]),
            (self.tr_("CSV / JSON"), [
                ("📊 CSV → JSON", "csv_to_json", [".csv"]),
                ("📊 JSON → CSV", "json_to_csv", [".json"]),
            ]),
            (self.tr_("XLSX (Excel)"), [
                ("📊 XLSX → PDF",  "xlsx_to_pdf",  [".xlsx", ".xls"]),
                ("📊 XLSX → JSON", "xlsx_to_json", [".xlsx", ".xls"]),
                ("📊 XLSX → CSV",  "xlsx_to_csv",  [".xlsx", ".xls"]),
            ]),
            (self.tr_("PPTX (PowerPoint)"), [
                ("📽️ PPTX → PDF", "pptx_to_pdf", [".pptx", ".ppt"]),
            ]),
            (self.tr_("HTML"), [
                ("🌐 HTML → PDF", "html_to_pdf", [".html", ".htm"]),
                ("🌐 PDF → HTML", "pdf_to_html", [".pdf"]),
            ]),
            (self.tr_("EPUB (E-book)"), [
                ("📚 EPUB → PDF", "epub_to_pdf", [".epub"]),
            ]),
        ]
        return self._build_tab_from_groups(groups, "documents")

    def _build_images_tab(self) -> QWidget:
        groups = [
            (self.tr_("JPEG / PNG"), [
                ("🖼️ JPEG → PNG", "jpeg_to_png", [".jpeg", ".jpg"]),
                ("🖼️ PNG → JPG",  "png_to_jpg",  [".png"]),
                ("🖼️ JPG → PNG",  "jpg_to_png",  [".jpg", ".jpeg"]),
                ("🖼️ WEBP → PNG", "webp_to_png", [".webp"]),
                ("🖼️ BMP → PNG",  "bmp_to_png",  [".bmp"]),
                ("🖼️ TIFF → PNG", "tiff_to_png", [".tiff", ".tif"]),
                ("🖼️ HEIC → PNG", "heic_to_png", [".heic", ".heif"]),
                ("🖼️ GIF → PNG",  "gif_to_png",  [".gif"]),
            ]),
            (self.tr_("ICO (Icône)"), [
                ("🎨 Image → ICO", "image_to_ico",
                 [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif",
                  ".webp", ".gif"]),
            ]),
        ]
        return self._build_tab_from_groups(groups, "images")

    def _build_av_tab(self) -> QWidget:
        groups = [
            (self.tr_("Vidéo → Vidéo"), [
                ("🎬 AVI → MP4",  "avi_to_mp4",  [".avi"]),
                ("🎬 WEBM → MP4", "webm_to_mp4", [".webm"]),
                ("🎬 MKV → MP4",  "mkv_to_mp4",  [".mkv"]),
                ("🎬 MOV → MP4",  "mov_to_mp4",  [".mov"]),
            ]),
            (self.tr_("Vidéo → Audio"), [
                ("🎬 MP4 → MP3",  "mp4_to_mp3",  [".mp4"]),
                ("🎬 AVI → MP3",  "avi_to_mp3",  [".avi"]),
                ("🎬 WEBM → MP3", "webm_to_mp3", [".webm"]),
                ("🎬 MKV → MP3",  "mkv_to_mp3",  [".mkv"]),
            ]),
            (self.tr_("Audio → Audio"), [
                ("🎵 WAV → MP3",  "wav_to_mp3",  [".wav"]),
                ("🎵 MP3 → WAV",  "mp3_to_wav",  [".mp3"]),
                ("🎵 AAC → MP3",  "acc_to_mp3",  [".aac", ".m4a"]),
                ("🎵 MP3 → AAC",  "mp3_to_acc",  [".mp3"]),
                ("🎵 FLAC → MP3", "flac_to_mp3", [".flac"]),
                ("🎵 OGG → MP3",  "ogg_to_mp3",  [".ogg"]),
            ]),
        ]
        return self._build_tab_from_groups(groups, "audio_video")

    def _build_tab_from_groups(
        self,
        groups: list[tuple[str, list]],
        tab_type: str,
    ) -> QWidget:
        tab = QWidget()
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(18)

        for group_title, buttons in groups:
            group = QGroupBox(group_title)
            grid  = QGridLayout(group)
            grid.setHorizontalSpacing(10)
            grid.setVerticalSpacing(10)

            for i, entry in enumerate(buttons):
                label, conv_type, exts = entry
                btn = self._make_btn(label, conv_type, exts, tab_type)
                grid.addWidget(btn, i // 2, i % 2)

            content_layout.addWidget(group)

        content_layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)
        return tab

    def _make_btn(
        self,
        label: str,
        conversion_type: str,
        accepted_exts: list[str],
        tab_type: str,
    ) -> QPushButton:
        btn = QPushButton(label)
        btn.setMinimumHeight(45)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self._btn_style("conversion", tab_type))
        btn.clicked.connect(
            lambda _checked, ct=conversion_type, exts=accepted_exts:
                self._run_conversion(ct, exts)
        )
        return btn

    # Theme / styling
    def _apply_theme_style(self) -> None:
        dark = getattr(self.parent_window, "dark_mode", False)
        if dark:
            self.setStyleSheet("""
                QDialog { background-color: #1a1d23; }
                QLabel  { color: #e9ecef; }
                QGroupBox {
                    color: #adb5bd; border: 2px solid #495057;
                    border-radius: 8px; margin-top: 10px; padding-top: 10px;
                    background-color: #2d333b;
                }
                QGroupBox::title { subcontrol-origin: margin; left: 10px;
                    padding: 0 5px; color: #adb5bd; }
                QScrollArea { border: none; background-color: transparent; }
                QProgressBar {
                    border: 1px solid #495057; border-radius: 6px;
                    background: #2d333b; color: #e9ecef; text-align: center;
                }
                QProgressBar::chunk { background: #6366f1; border-radius: 5px; }
                QTextEdit {
                    background: #2d333b; color: #d1d5db;
                    border: 1px solid #495057; border-radius: 6px;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background-color: #f8f9fa; }
                QLabel  { color: #212529; }
                QGroupBox {
                    color: #495057; border: 2px solid #dee2e6;
                    border-radius: 8px; margin-top: 10px; padding-top: 10px;
                    background-color: #ffffff;
                }
                QGroupBox::title { subcontrol-origin: margin; left: 10px;
                    padding: 0 5px; color: #495057; }
                QScrollArea { border: none; background-color: transparent; }
                QProgressBar {
                    border: 1px solid #dee2e6; border-radius: 6px;
                    background: #f1f3f5; color: #212529; text-align: center;
                }
                QProgressBar::chunk { background: #6366f1; border-radius: 5px; }
                QTextEdit {
                    background: #ffffff; color: #212529;
                    border: 1px solid #dee2e6; border-radius: 6px;
                }
            """)

    def _tab_style(self, active_index: int = 0) -> str:
        colors = ["#6366f1", "#10b981", "#f59e0b"]
        ac = colors[active_index % len(colors)]
        return f"""
            QTabWidget::pane  {{ border: 2px solid #495057; border-radius: 8px;
                                 background-color: #2d333b; }}
            QTabBar::tab      {{ background-color: #374151; color: #e9ecef;
                                 padding: 12px 24px; margin-right: 4px;
                                 border-top-left-radius: 6px;
                                 border-top-right-radius: 6px;
                                 font-weight: bold; font-size: 13px; }}
            QTabBar::tab:selected      {{ background-color: {ac}; color: white; }}
            QTabBar::tab:hover:!selected {{ background-color: #4b5563; }}
        """

    def _btn_style(self, kind: str, tab_type: str = "documents") -> str:
        palettes = {
            "documents" : ("#6366f1", "#4f46e5", "#4338ca"),
            "images"    : ("#10b981", "#059669", "#047857"),
            "audio_video": ("#f59e0b", "#d97706", "#b45309"),
        }
        s, h, p = palettes.get(tab_type, palettes["documents"])

        if kind == "conversion":
            return f"""
                QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                                stop:0 {s}, stop:1 {h});
                    color: white; border: none; padding: 10px 16px;
                    border-radius: 8px; font-weight: bold; font-size: 13px; }}
                QPushButton:hover   {{ background: {h}; }}
                QPushButton:pressed {{ background: {p}; }}
            """
        elif kind == "close":
            return """
                QPushButton { background: #6b7280; color: white; border: none;
                    padding: 10px 20px; border-radius: 8px;
                    font-weight: bold; font-size: 13px; }
                QPushButton:hover   { background: #4b5563; }
                QPushButton:pressed { background: #374151; }
            """
        elif kind == "cancel":
            return """
                QPushButton { background: #ef4444; color: white; border: none;
                    padding: 8px 16px; border-radius: 8px;
                    font-weight: bold; font-size: 12px; }
                QPushButton:hover   { background: #dc2626; }
                QPushButton:pressed { background: #b91c1c; }
                QPushButton:disabled { background: #6b7280; color: #9ca3af; }
            """
        return ""

    def _on_tab_changed(self, index: int) -> None:
        self.tab_widget.setStyleSheet(self._tab_style(index))

    def tr_(self, text: str) -> str:
        return self._tm.translate_text(text)

    def translate_text(self, text: str) -> str:
        return self._tm.translate_text(text)