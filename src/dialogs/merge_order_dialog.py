"""MergeOrderDialog - Dialog for choosing merge order."""

import os
import re
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from qss_helpers import _apply_dialog_btn
from utils import make_tm
from utils.translation_mixin import TranslationMixin


class MergeOrderDialog(TranslationMixin, QDialog):
    """Dialog for choosing merge order and optionally reordering files manually."""

    def __init__(self, files, file_type, parent=None, language="fr", pre_select_key=None):
        super().__init__(parent)
        self._tm = make_tm(language)
        self.files = list(files)
        self.file_type = file_type
        self._pre_select_key = pre_select_key
        self.setWindowTitle(self.translate_text("Ordre de fusion"))
        self.setMinimumWidth(480)
        self.setMinimumHeight(400)
        self._setup_ui()
        self.apply_theme_style()
        if pre_select_key and pre_select_key in self._radio_map:
            self._radio_map[pre_select_key].setChecked(True)

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        order_group = QGroupBox(self.translate_text("Choisir l'ordre"))
        order_lay = QVBoxLayout(order_group)

        self.order_buttons = QButtonGroup(self)
        orders = [
            ("alpha_az", "🔤 " + self.translate_text("Alphabétique (A→Z)")),
            ("alpha_za", "🔤 " + self.translate_text("Alphabétique (Z→A)")),
            ("num_asc", "🔢 " + self.translate_text("Numérique (1→9)")),
            ("num_desc", "🔢 " + self.translate_text("Numérique (9→1)")),
            ("date_asc", "📅 " + self.translate_text("Date (ancien→nouveau)")),
            ("date_desc", "📅 " + self.translate_text("Date (nouveau→ancien)")),
            ("manual", "✋ " + self.translate_text("Manuel (glisser-déposer)")),
            ("current", "📋 " + self.translate_text("Ordre actuel (liste principale)")),
        ]
        self._radio_map = {}
        for key, label in orders:
            rb = QRadioButton(label)
            self.order_buttons.addButton(rb)
            order_lay.addWidget(rb)
            self._radio_map[key] = rb
        self._radio_map["current"].setChecked(True)

        lay.addWidget(order_group)

        self._manual_group = QGroupBox(self.translate_text("Réordonner les fichiers"))
        manual_lay = QVBoxLayout(self._manual_group)
        hint = QLabel(self.translate_text("Glissez-déposez pour réordonner, puis cliquez sur Fusionner."))
        hint.setStyleSheet("color: gray; font-size: 11px;")
        manual_lay.addWidget(hint)

        self._manual_list = QListWidget()
        self._manual_list.setDragDropMode(QListWidget.InternalMove)
        self._manual_list.setSelectionMode(QListWidget.SingleSelection)
        for f in self.files:
            self._manual_list.addItem(QListWidgetItem(Path(f).name))
            self._manual_list.item(self._manual_list.count() - 1).setData(Qt.UserRole, f)
        manual_lay.addWidget(self._manual_list)
        self._manual_group.setVisible(False)
        lay.addWidget(self._manual_group)

        self._radio_map["manual"].toggled.connect(self._manual_group.setVisible)

        btn_row = QHBoxLayout()
        merge_btn = QPushButton("🔗 " + self.translate_text("Fusionner"))
        merge_btn.setMinimumHeight(36)
        merge_btn.setStyleSheet("""
            QPushButton { background:#28a745; color:white; border:none;
                          border-radius:6px; font-weight:bold; padding:6px 16px; }
            QPushButton:hover { background:#218838; }
        """)
        cancel_btn = QPushButton(self.translate_text("Annuler"))
        cancel_btn.setMinimumHeight(36)
        _apply_dialog_btn(cancel_btn, "BtnCancelGlassy")
        merge_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(merge_btn)
        lay.addLayout(btn_row)

    def get_ordered_files(self):
        """Return files in the chosen order."""
        files = list(self.files)

        if self._radio_map["alpha_az"].isChecked():
            files.sort(key=lambda f: Path(f).name.lower())
        elif self._radio_map["alpha_za"].isChecked():
            files.sort(key=lambda f: Path(f).name.lower(), reverse=True)
        elif self._radio_map["num_asc"].isChecked():

            def num_key(f):
                nums = re.findall(r"\d+", Path(f).stem)
                return [int(n) for n in nums] if nums else [0]

            files.sort(key=num_key)
        elif self._radio_map["num_desc"].isChecked():

            def num_key_d(f):
                nums = re.findall(r"\d+", Path(f).stem)
                return [int(n) for n in nums] if nums else [0]

            files.sort(key=num_key_d, reverse=True)
        elif self._radio_map["date_asc"].isChecked():
            files.sort(key=lambda f: os.path.getmtime(f))
        elif self._radio_map["date_desc"].isChecked():
            files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        elif self._radio_map["manual"].isChecked():
            files = [self._manual_list.item(i).data(Qt.UserRole) for i in range(self._manual_list.count())]

        return files

    def apply_theme_style(self):
        """Apply white/light or dark theme styling based on the parent window."""
        parent = self.parent()
        dark = bool(getattr(parent, "dark_mode", False))
        if dark:
            self.setStyleSheet(
                """
                QDialog { background-color: #1e2229; }
                QLabel { color: #e9ecef; }
                QRadioButton { color: #e9ecef; spacing: 8px; }
                QRadioButton::indicator {
                    width: 16px; height: 16px;
                    border-radius: 8px;
                    border: 2px solid #4a5568;
                    background: #1e2229;
                }
                QRadioButton::indicator:checked {
                    background-color: #4dabf7;
                    border: 2px solid #4dabf7;
                }
                QGroupBox {
                    color: #adb5bd;
                    border: 1px solid #2c313a;
                    border-radius: 6px;
                    margin-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
                QListWidget {
                    background-color: #2c313a;
                    color: #e9ecef;
                    border: 1px solid #1e2229;
                    border-radius: 4px;
                    padding: 4px;
                }
                """
            )
        else:
            self.setStyleSheet(
                """
                QDialog { background-color: #f8f9fa; }
                QLabel { color: #212529; }
                QRadioButton { color: #212529; spacing: 8px; }
                QRadioButton::indicator {
                    width: 16px; height: 16px;
                    border-radius: 8px;
                    border: 2px solid #adb5bd;
                    background: #ffffff;
                }
                QRadioButton::indicator:checked {
                    background-color: #4dabf7;
                    border: 2px solid #4dabf7;
                }
                QGroupBox {
                    color: #495057;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    margin-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
                QListWidget {
                    background-color: #ffffff;
                    color: #212529;
                    border: 1px solid #ced4da;
                    border-radius: 4px;
                    padding: 4px;
                }
                """
            )
