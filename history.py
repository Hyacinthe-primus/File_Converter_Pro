"""
Conversion History

Interface for viewing, filtering, and managing conversion logs.

Features:
    - Detailed table view (Date, Type, Source, Target, Size, Time, Status)
    - Advanced filtering (Search text, Date range, Result limit)
    - Row actions (Reconvert, Open File, Delete Record)
    - Bulk actions (Delete selected, Export all)
    - Keyboard shortcuts (Ctrl+F for search, Esc to close)

Classes:
    HistoryDialog: Modal window for history management.

Integration:
    - Direct connection to DatabaseManager for live queries
    - Context menu support for quick actions
    - Tooltip display for full file paths

"""

import sys
import os
import subprocess
from pathlib import Path

def _resource_path(relative_path):
    """Resolve path for both dev and PyInstaller exe."""
    from utils import resource_path
    return resource_path(relative_path).replace("\\", "/")
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFileDialog, QMessageBox, QComboBox,
                               QLineEdit, QDialog, QMenu, QTableWidget, QTableWidgetItem, QDateEdit)
from PySide6.QtCore import Qt, QDate, QThread, Signal, QObject
from PySide6.QtGui import QKeySequence, QShortcut
from utils.translation_mixin import TranslationMixin

from qss_helpers import _load_qss, _apply_dialog_btn

class HistoryLoader(QObject):
    """Worker that runs the DB query in a separate thread."""
    finished = Signal(list)

    def __init__(self, db_manager, limit, search_query, start_date, end_date):
        super().__init__()
        self.db_manager   = db_manager
        self.limit        = limit
        self.search_query = search_query
        self.start_date   = start_date
        self.end_date     = end_date

    def run(self):
        try:
            results = self.db_manager.get_conversion_history(
                limit=self.limit,
                search_query=self.search_query,
                start_date=self.start_date,
                end_date=self.end_date
            )
        except Exception:
            results = []
        self.finished.emit(results)


from datetime import datetime
import sqlite3

def _make_tm(language):
    from utils import make_tm
    return make_tm(language)

class HistoryDialog(TranslationMixin, QDialog):
    def __init__(self, db_manager, parent=None, language="fr", adv_db_manager=None):
        super().__init__(parent)
        self.db_manager     = db_manager
        self.adv_db_manager = adv_db_manager
        self._use_adv_db    = False
        self.language       = language
        self._tm            = _make_tm(language)
        self.parent_window  = parent
        self._loader_thread = None
        self.setWindowTitle(self.translate_text("📋 Historique des Conversions"))
        self.setModal(False)
        self.setMinimumSize(1000, 700)
        self.setup_ui()
        self.load_history()

    def apply_scrollbar_style(self):
        dark = hasattr(self.parent_window, 'dark_mode') and self.parent_window.dark_mode
        self.setStyleSheet(self.styleSheet() + _load_qss("scrollbar.qss", "dark" if dark else "light"))

    def setup_shortcuts(self):
        """Keyboard shortcuts for the history window"""
        # Ctrl+F: Search
        shortcut_search = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_search.activated.connect(lambda: self.search_input.setFocus())
        
        # Esc: Close
        shortcut_close = QShortcut(QKeySequence("Esc"), self)
        shortcut_close.activated.connect(self.close)

    def setup_ui(self):

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        source_layout = QHBoxLayout()
        source_layout.setSpacing(8)

        self.btn_main_db = QPushButton("🗂️ " + self.translate_text("Conversions principales"))
        self.btn_adv_db  = QPushButton("⚙️ " + self.translate_text("Conversions avancées"))
        self.btn_main_db.setFixedHeight(30)
        self.btn_adv_db.setFixedHeight(30)

        _sel   = "background-color:#4F46E5;color:white;border:none;padding:4px 14px;border-radius:6px;font-weight:bold;"
        _unsel = "background-color:transparent;color:#4F46E5;border:2px solid #4F46E5;padding:4px 14px;border-radius:6px;font-weight:bold;"

        self.btn_main_db.setStyleSheet(_sel)
        self.btn_adv_db.setStyleSheet(_unsel)

        def _switch_main():
            self._use_adv_db = False
            self.btn_main_db.setStyleSheet(_sel)
            self.btn_adv_db.setStyleSheet(_unsel)
            self.load_history()

        def _switch_adv():
            if not self.adv_db_manager:
                return
            self._use_adv_db = True
            self.btn_main_db.setStyleSheet(_unsel)
            self.btn_adv_db.setStyleSheet(_sel)
            self.load_history()

        self.btn_main_db.clicked.connect(_switch_main)
        self.btn_adv_db.clicked.connect(_switch_adv)

        if not self.adv_db_manager:
            self.btn_adv_db.setEnabled(False)
            self.btn_adv_db.setToolTip("Module de conversions avancées non chargé")

        source_layout.addWidget(self.btn_main_db)
        source_layout.addWidget(self.btn_adv_db)
        source_layout.addStretch()
        layout.addLayout(source_layout)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translate_text("Rechercher par nom de fichier ou type d'opération..."))
        self.search_input.textChanged.connect(self.load_history)

        arrow_path = _resource_path("Assets/down-arrow.svg")
        date_style = _load_qss("history_date.qss").replace("{arrow_path}", arrow_path)

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        first_date = self.db_manager.get_first_conversion_date()
        if first_date:
            min_qdate = QDate.fromString(first_date, "yyyy-MM-dd")
            self.start_date_edit.setMinimumDate(min_qdate)
            self.start_date_edit.setDate(min_qdate)
        else:
            self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.start_date_edit.dateChanged.connect(self.load_history)
        self.start_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.start_date_edit.setFixedWidth(140)
        self.start_date_edit.setStyleSheet(date_style)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.dateChanged.connect(self.load_history)
        self.end_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.end_date_edit.setFixedWidth(140)
        self.end_date_edit.setStyleSheet(date_style)
        self.start_date_edit.calendarWidget().setStyleSheet(_load_qss("history_calendar.qss"))
        self.end_date_edit.calendarWidget().setStyleSheet(_load_qss("history_calendar.qss"))

        self.limit_combo = QComboBox()
        self.limit_combo.addItems(["50", "100", "200", "500", "1000", "2000", "5000", "7500", "10000"])
        self.limit_combo.setCurrentText("100")
        self.limit_combo.currentIndexChanged.connect(self.load_history)
        self.limit_combo.setFixedWidth(75)

        filter_layout.addWidget(QLabel(self.translate_text("Recherche:")))
        filter_layout.addWidget(self.search_input, 1)  # stretch
        filter_layout.addWidget(QLabel(self.translate_text("Du:")))
        filter_layout.addWidget(self.start_date_edit)
        filter_layout.addWidget(QLabel(self.translate_text("Au:")))
        filter_layout.addWidget(self.end_date_edit)
        filter_layout.addWidget(QLabel(self.translate_text("Nombre:")))
        filter_layout.addWidget(self.limit_combo)

        layout.addLayout(filter_layout)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            self.translate_text("Date/Heure"),
            self.translate_text("Type"),
            self.translate_text("Fichier Source"),
            self.translate_text("Format Source"),
            self.translate_text("Fichier Cible"),
            self.translate_text("Format Cible"),
            self.translate_text("Statut"),
            self.translate_text("Actions")
        ])
        self.history_table.horizontalHeader().setStretchLastSection(False)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_table.customContextMenuRequested.connect(self.show_context_menu)
        self.history_table.verticalHeader().setDefaultSectionSize(36)
        self.history_table.verticalHeader().setMinimumSectionSize(36)
        from PySide6.QtWidgets import QHeaderView
        hh = self.history_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed);   self.history_table.setColumnWidth(0, 130)  # Date
        hh.setSectionResizeMode(1, QHeaderView.Fixed);   self.history_table.setColumnWidth(1, 130)  # Type
        hh.setSectionResizeMode(2, QHeaderView.Fixed);   self.history_table.setColumnWidth(2, 160)  # Source file
        hh.setSectionResizeMode(3, QHeaderView.Fixed);   self.history_table.setColumnWidth(3, 110)  # Src format
        hh.setSectionResizeMode(4, QHeaderView.Fixed);   self.history_table.setColumnWidth(4, 160)  # Target file
        hh.setSectionResizeMode(5, QHeaderView.Fixed);   self.history_table.setColumnWidth(5, 110)  # Tgt format
        hh.setSectionResizeMode(6, QHeaderView.Fixed);   self.history_table.setColumnWidth(6, 60)   # Status
        hh.setSectionResizeMode(7, QHeaderView.Fixed);   self.history_table.setColumnWidth(7, 110)  # Actions
        
        layout.addWidget(self.history_table)
        
        button_layout = QHBoxLayout()
        
        self.reconvert_btn = QPushButton("🔄 " + self.translate_text("Reconvertir la sélection"))
        _apply_dialog_btn(self.reconvert_btn, "BtnReconvert")
        self.reconvert_btn.clicked.connect(self.reconvert_selected)
        self.reconvert_btn.setEnabled(False)
        
        self.delete_btn = QPushButton("🗑️ " + self.translate_text("Supprimer la sélection"))
        _apply_dialog_btn(self.delete_btn, "BtnDeleteSelection")
        self.delete_btn.clicked.connect(self.delete_selected)
        self.delete_btn.setEnabled(False)
        
        self.clear_all_btn = QPushButton("🧹 " + self.translate_text("Effacer tout l'historique"))
        _apply_dialog_btn(self.clear_all_btn, "BtnClearAll")
        self.clear_all_btn.clicked.connect(self.clear_all_history)
        
        print_pdf_btn = QPushButton("🖨️ " + self.translate_text("Imprimer en PDF"))
        _apply_dialog_btn(print_pdf_btn, "BtnPrintPdf")
        print_pdf_btn.clicked.connect(self.print_pdf)
        
        export_json_btn = QPushButton("📋 " + self.translate_text("Exporter en JSON"))
        _apply_dialog_btn(export_json_btn, "BtnExportJson")
        export_json_btn.clicked.connect(self.export_json)
        
        close_btn = QPushButton(self.translate_text("Fermer"))
        _apply_dialog_btn(close_btn, "BtnHistoryClose")
        close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(self.reconvert_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.clear_all_btn)
        button_layout.addStretch()
        button_layout.addWidget(print_pdf_btn)
        button_layout.addWidget(export_json_btn)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.history_table.itemSelectionChanged.connect(self.update_button_states)
        self.setup_shortcuts()
        self.apply_scrollbar_style()

    def load_history(self):
        search_query = self.search_input.text() if self.search_input.text() else None
        start_date   = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date     = self.end_date_edit.date().toString("yyyy-MM-dd")
        limit        = int(self.limit_combo.currentText())

        active_db = self.adv_db_manager if self._use_adv_db else self.db_manager

        if self._loader_thread is not None:
            try:
                if self._loader_thread.isRunning():
                    self._loader_thread.quit()
                    self._loader_thread.wait()
            except RuntimeError:
                pass
            self._loader_thread = None

        self._loader_thread = QThread(self)
        self._worker = HistoryLoader(active_db, limit, search_query, start_date, end_date)
        self._worker.moveToThread(self._loader_thread)

        self._loader_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_history_loaded)
        self._worker.finished.connect(self._loader_thread.quit)

        self._loader_thread.start()

    def _on_history_loaded(self, history):
        """Called in the main thread once the data is ready."""
        self.history_table.setRowCount(0)

        for i, row in enumerate(history):
            self.history_table.insertRow(i)
            
            dt = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
            date_item = QTableWidgetItem(dt.strftime('%d/%m/%Y %H:%M'))
            date_item.setData(Qt.UserRole, row[0])  # Store the ID
            self.history_table.setItem(i, 0, date_item)
            
            op_key = row[6]
            display_text = self.translate_operation_type(op_key)
            self.history_table.setItem(i, 1, QTableWidgetItem(display_text))
            
            source_name = Path(row[2]).name if row[2] else ""
            source_item = QTableWidgetItem(source_name)
            source_item.setToolTip(row[2])
            self.history_table.setItem(i, 2, source_item)
            
            self.history_table.setItem(i, 3, QTableWidgetItem(row[3]))
            
            target_name = Path(row[4]).name if row[4] else ""
            target_item = QTableWidgetItem(target_name)
            target_item.setToolTip(row[4])
            self.history_table.setItem(i, 4, target_item)
            
            self.history_table.setItem(i, 5, QTableWidgetItem(row[5]))
            
            status = "✅" if row[9] else "❌"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(i, 6, status_item)

            action_widget = QWidget()
            action_widget.setAttribute(Qt.WA_TranslucentBackground)
            action_widget.setStyleSheet("background: transparent;")
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setSpacing(4)
            action_layout.setAlignment(Qt.AlignCenter)

            small_btn_style = """
                QPushButton {
                    background-color: transparent;
                    border: none;
                    padding: 2px;
                    font-size: 14px;
                    text-align: center;
                    qproperty-iconSize: 0px;
                }
                QPushButton:hover {
                    background-color: rgba(77, 171, 247, 0.3);
                    border-radius: 4px;
                }
            """

            reconvert_action = QPushButton("🔄")
            reconvert_action.setFixedSize(26, 26)
            reconvert_action.setToolTip(self.translate_text("Reconvertir ce fichier"))
            reconvert_action.setStyleSheet(small_btn_style)
            reconvert_action.clicked.connect(lambda checked, idx=i: self.reconvert_single(idx))
            
            open_action = QPushButton("📂")
            open_action.setFixedSize(26, 26)
            open_action.setToolTip(self.translate_text("Ouvrir le fichier"))
            open_action.setStyleSheet(small_btn_style)
            open_action.clicked.connect(lambda checked, idx=i: self.open_file(idx))
            
            delete_action = QPushButton("🗑️")
            delete_action.setFixedSize(26, 26)
            delete_action.setToolTip(self.translate_text("Supprimer cet enregistrement"))
            delete_action.setStyleSheet(small_btn_style)
            delete_action.clicked.connect(lambda checked, idx=i: self.delete_single(idx))
            
            action_layout.addWidget(reconvert_action)
            action_layout.addWidget(open_action)
            action_layout.addWidget(delete_action)
            
            self.history_table.setCellWidget(i, 7, action_widget)

        for i in range(self.history_table.rowCount()):
            self.history_table.setRowHeight(i, 36)

    def update_button_states(self):
        selected_count = len(self.history_table.selectedItems()) > 0
        self.reconvert_btn.setEnabled(selected_count)
        self.delete_btn.setEnabled(selected_count)

    def show_context_menu(self, position):
        menu = QMenu()
        
        reconvert_action = menu.addAction("🔄 " + self.translate_text("Reconvertir la sélection"))
        delete_action = menu.addAction("🗑️ " + self.translate_text("Supprimer la sélection"))
        open_source_action = menu.addAction("📂 " + self.translate_text("Ouvrir le fichier source"))
        open_target_action = menu.addAction("📂 " + self.translate_text("Ouvrir le fichier cible"))
        
        action = menu.exec(self.history_table.mapToGlobal(position))
        
        selected_rows = set(item.row() for item in self.history_table.selectedItems())
        
        if action == reconvert_action:
            self.reconvert_selected_rows(list(selected_rows))
        elif action == delete_action:
            self.delete_selected_rows(list(selected_rows))
        elif action == open_source_action:
            self.open_source_files(list(selected_rows))
        elif action == open_target_action:
            self.open_target_files(list(selected_rows))

    def reconvert_selected(self):
        selected_rows = set(item.row() for item in self.history_table.selectedItems())
        self.reconvert_selected_rows(list(selected_rows))

    def reconvert_selected_rows(self, rows):
        if not rows:
            return
        
        for row in rows:
            source_file = self.history_table.item(row, 2).toolTip()
            operation_type = self.history_table.item(row, 1).text()
            
            if os.path.exists(source_file):
                if self.parent_window:
                    self.parent_window.add_files_to_list([source_file])
                    
                    if "PDF vers Word" in operation_type:
                        self.parent_window.convert_pdf_to_word()
                    elif "Word vers PDF" in operation_type:
                        self.parent_window.convert_word_to_pdf()
                    elif "Images vers PDF" in operation_type:
                        self.parent_window.convert_images_to_pdf()
                    elif "fusion" in operation_type.lower():
                        if "PDF" in operation_type:
                            self.parent_window.merge_pdfs()
                        else:
                            self.parent_window.merge_word_docs()
            else:
                QMessageBox.warning(
                    self, 
                    self.translate_text("Fichier introuvable"), 
                    self.translate_text(f"Le fichier source n'existe plus: {source_file}")
                )

    def reconvert_single(self, row):
        self.reconvert_selected_rows([row])

    def delete_selected(self):
        selected_rows = set(item.row() for item in self.history_table.selectedItems())
        self.delete_selected_rows(list(selected_rows))

    def delete_selected_rows(self, rows):
        if not rows:
            return
        
        reply = QMessageBox.question(
            self, 
            self.translate_text("Confirmation"), 
            self.translate_text("history_delete").format(len(rows)),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            active_db = self.adv_db_manager if self._use_adv_db else self.db_manager
            table     = "adv_conversion_history" if self._use_adv_db else "conversion_history"
            conn   = sqlite3.connect(active_db.db_path)
            cursor = conn.cursor()
            
            for row in sorted(rows, reverse=True):
                record_id = self.history_table.item(row, 0).data(Qt.UserRole)
                cursor.execute(f'DELETE FROM {table} WHERE id = ?', (record_id,))
                self.history_table.removeRow(row)
            
            conn.commit()
            conn.close()

    def delete_single(self, row):
        self.delete_selected_rows([row])

    def clear_all_history(self):
        reply = QMessageBox.question(
            self, 
            self.translate_text("Confirmation"), 
            self.translate_text("Voulez-vous vraiment supprimer TOUT l'historique ? Cette action est irréversible."),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            active_db = self.adv_db_manager if self._use_adv_db else self.db_manager
            conn   = sqlite3.connect(active_db.db_path)
            cursor = conn.cursor()
            if self._use_adv_db:
                cursor.execute('DELETE FROM adv_conversion_history')
                cursor.execute('DELETE FROM adv_daily_stats')
            else:
                cursor.execute('DELETE FROM conversion_history')
                cursor.execute('DELETE FROM daily_stats')
            conn.commit()
            conn.close()
            self.history_table.setRowCount(0)

    def open_file(self, row):
        target_file = self.history_table.item(row, 4).toolTip()
        
        if os.path.exists(target_file):
            try:
                if sys.platform == "win32":
                    os.startfile(target_file)
                elif sys.platform == "darwin":
                    subprocess.run(["open", target_file])
                else:
                    subprocess.run(["xdg-open", target_file])
            except Exception as e:
                QMessageBox.warning(
                    self, 
                    self.translate_text("Erreur"), 
                    self.translate_text(f"Impossible d'ouvrir le fichier: {str(e)}")
                )
        else:
            QMessageBox.warning(
                self, 
                self.translate_text("Fichier introuvable"), 
                self.translate_text("Le fichier cible n'existe plus.")
            )

    def open_source_files(self, rows):
        for row in rows:
            source_file = self.history_table.item(row, 2).toolTip()
            if os.path.exists(source_file):
                try:
                    if sys.platform == "win32":
                        os.startfile(source_file)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", source_file])
                    else:
                        subprocess.run(["xdg-open", source_file])
                except Exception:
                    pass

    def open_target_files(self, rows):
        for row in rows:
            target_file = self.history_table.item(row, 4).toolTip()
            if os.path.exists(target_file):
                try:
                    if sys.platform == "win32":
                        os.startfile(target_file)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", target_file])
                    else:
                        subprocess.run(["xdg-open", target_file])
                except Exception:
                    pass

    def print_pdf(self):
        """Generate a colored PDF report of the conversion history, grouped by operation type."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            self.translate_text("Imprimer en PDF"),
            "historique_conversions.pdf",
            "PDF (*.pdf)"
        )
        if not filepath:
            return

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                            Paragraph, Spacer, HRFlowable)
            from collections import defaultdict

            # Palette
            COLOR_HEADER_BG    = colors.HexColor("#4F46E5")
            COLOR_HEADER_TEXT  = colors.white
            COLOR_ROW_ODD      = colors.HexColor("#F5F3FF")
            COLOR_ROW_EVEN     = colors.white
            COLOR_SUCCESS      = colors.HexColor("#10B981")
            COLOR_FAIL         = colors.HexColor("#EF4444")
            COLOR_GRID         = colors.HexColor("#C7D2FE")

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                "Title", parent=styles["Title"],
                fontSize=18, textColor=COLOR_HEADER_BG,
                spaceAfter=4
            )
            subtitle_style = ParagraphStyle(
                "Sub", parent=styles["Normal"],
                fontSize=9, textColor=colors.HexColor("#6B7280"),
                spaceAfter=12
            )
            section_style = ParagraphStyle(
                "Section", parent=styles["Normal"],
                fontSize=11, fontName="Helvetica-Bold",
                textColor=COLOR_HEADER_BG, spaceBefore=14, spaceAfter=4
            )
            cell_style = ParagraphStyle(
                "Cell", parent=styles["Normal"],
                fontSize=7, leading=9
            )

            rows_by_type = defaultdict(list)
            for r in range(self.history_table.rowCount()):
                date    = self.history_table.item(r, 0).text() if self.history_table.item(r, 0) else ""
                op_type = self.history_table.item(r, 1).text() if self.history_table.item(r, 1) else ""
                src     = self.history_table.item(r, 2).toolTip() if self.history_table.item(r, 2) else ""
                src_fmt = self.history_table.item(r, 3).text() if self.history_table.item(r, 3) else ""
                tgt     = self.history_table.item(r, 4).toolTip() if self.history_table.item(r, 4) else ""
                tgt_fmt = self.history_table.item(r, 5).text() if self.history_table.item(r, 5) else ""
                status  = self.history_table.item(r, 6).text() if self.history_table.item(r, 6) else ""
                rows_by_type[op_type].append((date, src, src_fmt, tgt, tgt_fmt, status))

            doc = SimpleDocTemplate(
                filepath, pagesize=A4,
                leftMargin=1.5*cm, rightMargin=1.5*cm,
                topMargin=1.5*cm, bottomMargin=1.5*cm
            )
            story = []

            from datetime import datetime as _dt
            story.append(Paragraph("📋 " + self.translate_text("Historique des Conversions"), title_style))
            story.append(Paragraph(
                self.translate_text("Généré le") + " " + _dt.now().strftime("%d/%m/%Y") +
                " " + self.translate_text("à") + " " + _dt.now().strftime("%H:%M") +
                "  —  " + str(self.history_table.rowCount()) + " " + self.translate_text("entrée(s)"),
                subtitle_style
            ))
            story.append(HRFlowable(width="100%", thickness=1, color=COLOR_HEADER_BG, spaceAfter=10))

            col_headers = [
                self.translate_text("Date/Heure"),
                self.translate_text("Fichier Source"),
                self.translate_text("Fmt src"),
                self.translate_text("Fichier Cible"),
                self.translate_text("Fmt cible"),
                self.translate_text("Statut"),
            ]
            col_widths = [3.2*cm, 4.8*cm, 1.6*cm, 4.8*cm, 1.6*cm, 1.4*cm]

            for op_type, data_rows in sorted(rows_by_type.items()):
                story.append(Paragraph(f"▸  {op_type}  ({len(data_rows)})", section_style))

                table_data = [[Paragraph(f"<b>{h}</b>", cell_style) for h in col_headers]]
                for idx, (date, src, src_fmt, tgt, tgt_fmt, status) in enumerate(data_rows):
                    src_name = Path(src).name
                    tgt_name = Path(tgt).name
                    row = [
                        Paragraph(date, cell_style),
                        Paragraph(src_name, cell_style),
                        Paragraph(src_fmt, cell_style),
                        Paragraph(tgt_name, cell_style),
                        Paragraph(tgt_fmt, cell_style),
                        Paragraph(status, cell_style),
                    ]
                    table_data.append(row)

                t = Table(table_data, colWidths=col_widths, repeatRows=1)

                style_cmds = [
                    ("BACKGROUND",  (0, 0), (-1, 0), COLOR_HEADER_BG),
                    ("TEXTCOLOR",   (0, 0), (-1, 0), COLOR_HEADER_TEXT),
                    ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE",    (0, 0), (-1, 0), 7),
                    ("ALIGN",       (0, 0), (-1, 0), "CENTER"),
                    ("TOPPADDING",  (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING",(0, 0), (-1, -1), 4),
                    ("GRID",        (0, 0), (-1, -1), 0.4, COLOR_GRID),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_ROW_ODD, COLOR_ROW_EVEN]),
                    ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
                ]

                for row_idx, (_, _, _, _, _, status) in enumerate(data_rows, start=1):
                    clr = COLOR_SUCCESS if "✅" in status else COLOR_FAIL
                    style_cmds.append(("TEXTCOLOR", (5, row_idx), (5, row_idx), clr))
                    style_cmds.append(("FONTNAME",  (5, row_idx), (5, row_idx), "Helvetica-Bold"))
                    style_cmds.append(("ALIGN",     (5, row_idx), (5, row_idx), "CENTER"))

                t.setStyle(TableStyle(style_cmds))
                story.append(t)
                story.append(Spacer(1, 0.4*cm))

            doc.build(story)

            QMessageBox.information(
                self,
                self.translate_text("Succès"),
                self.translate_text("Historique exporté avec succès vers") + f"\n{filepath}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                self.translate_text("Erreur"),
                self.translate_text("Erreur lors de l'export:") + f"\n{str(e)}"
            )

    def export_json(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, 
            self.translate_text("Exporter l'historique en JSON"), 
            "", 
            "JSON (*.json)"
        )
        
        if filepath:
            try:
                self.db_manager.export_history(filepath, 'json')
                QMessageBox.information(
                    self, 
                    self.translate_text("Succès"), 
                    self.translate_text(f"Historique exporté avec succès vers {filepath}")
                )
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    self.translate_text("Erreur"), 
                    self.translate_text(f"Erreur lors de l'export: {str(e)}")
                )


    def translate_operation_type(self, operation_key):
        """Translate a technical key into readable text according to the language"""
        return self._tm.translate_operation_type(operation_key)