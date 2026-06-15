"""BatchRenameDialog — Advanced batch rename with template, numbering, case, find/replace."""

import os
import re
from datetime import datetime

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QLabel, QLineEdit, QPushButton, QComboBox,
                               QSpinBox, QTableWidget, QTableWidgetItem,
                               QHeaderView, QGridLayout)
from qss_helpers import _apply_dialog_btn
from widgets import AnimatedCheckBox


def _make_tm(language):
    from utils import make_tm
    return make_tm(language)


class BatchRenameDialog(QDialog):
    """
    Advanced batch rename dialog.
    Features: flexible template, numbering options, case/cleanup, find/replace, live preview.
    """

    def __init__(self, files, parent=None, language="fr"):
        super().__init__(parent)
        self.files = list(files)
        self._tm = _make_tm(language)
        self.setWindowTitle(self.tr_("Renommage par Lot"))
        self.setMinimumSize(740, 600)
        self._setup_ui()
        self._refresh_preview()

    def tr_(self, text):
        return self._tm.translate_text(text)

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(14, 14, 14, 14)

        tpl_box = QGroupBox(self.tr_("br_template_title"))
        tpl_lay = QVBoxLayout(tpl_box)

        hint = QLabel(self.tr_("br_template_hint"))
        hint.setStyleSheet("color: rgba(160,160,160,0.85); font-size: 11px;")
        hint.setWordWrap(True)
        tpl_lay.addWidget(hint)

        tpl_row = QHBoxLayout()
        self.tpl_input = QLineEdit("{original}")
        self.tpl_input.setPlaceholderText("{original}_{num}")
        self.tpl_input.textChanged.connect(self._refresh_preview)
        tpl_row.addWidget(self.tpl_input)

        for var in ["{original}", "{num}", "{date}", "{ext}"]:
            btn = QPushButton(var)
            btn.setFixedHeight(28)
            btn.setStyleSheet("""
                QPushButton { background: rgba(170,100,255,0.15); color: rgb(170,100,255);
                              border: 1px solid rgba(170,100,255,0.35); border-radius:5px;
                              font-size:11px; padding: 0 6px; }
                QPushButton:hover { background: rgba(170,100,255,0.28); }
            """)
            btn.clicked.connect(lambda _, v=var: self._insert_var(v))
            tpl_row.addWidget(btn)
        tpl_lay.addLayout(tpl_row)
        root.addWidget(tpl_box)
        num_box = QGroupBox(self.tr_("br_numbering_title"))
        num_grid = QGridLayout(num_box)
        num_grid.setColumnStretch(1, 1)
        num_grid.setColumnStretch(3, 1)

        num_grid.addWidget(QLabel(self.tr_("br_start")), 0, 0)
        self.start_spin = QSpinBox()
        self.start_spin.setRange(0, 99999)
        self.start_spin.setValue(1)
        self.start_spin.valueChanged.connect(self._refresh_preview)
        num_grid.addWidget(self.start_spin, 0, 1)

        num_grid.addWidget(QLabel(self.tr_("br_step")), 0, 2)
        self.step_spin = QSpinBox()
        self.step_spin.setRange(1, 100)
        self.step_spin.setValue(1)
        self.step_spin.valueChanged.connect(self._refresh_preview)
        num_grid.addWidget(self.step_spin, 0, 3)

        num_grid.addWidget(QLabel(self.tr_("br_padding")), 1, 0)
        self.pad_spin = QSpinBox()
        self.pad_spin.setRange(1, 6)
        self.pad_spin.setValue(3)
        self.pad_spin.valueChanged.connect(self._refresh_preview)
        num_grid.addWidget(self.pad_spin, 1, 1)

        num_grid.addWidget(QLabel(self.tr_("br_order")), 1, 2)
        self.order_combo = QComboBox()
        self.order_combo.addItems([
            self.tr_("br_order_current"),
            self.tr_("Alphabétique (A→Z)"),
            self.tr_("Alphabétique (Z→A)"),
            self.tr_("Numérique (1→9)"),
            self.tr_("Numérique (9→1)"),
            self.tr_("Date (ancien→nouveau)"),
            self.tr_("Date (nouveau→ancien)"),
        ])
        self.order_combo.currentIndexChanged.connect(self._refresh_preview)
        num_grid.addWidget(self.order_combo, 1, 3)
        root.addWidget(num_box)

        case_box = QGroupBox(self.tr_("br_case_title"))
        case_lay = QHBoxLayout(case_box)

        case_lay.addWidget(QLabel(self.tr_("br_case_label")))
        self.case_combo = QComboBox()
        self.case_combo.addItems([
            self.tr_("br_case_unchanged"),
            self.tr_("br_case_upper"),
            self.tr_("br_case_lower"),
            self.tr_("br_case_title"),
        ])
        self.case_combo.currentIndexChanged.connect(self._refresh_preview)
        case_lay.addWidget(self.case_combo)
        case_lay.addSpacing(16)

        self.spaces_check = AnimatedCheckBox(self.tr_("br_spaces"))
        self.spaces_check.stateChanged.connect(self._refresh_preview)
        case_lay.addWidget(self.spaces_check)

        self.trim_check = AnimatedCheckBox(self.tr_("br_trim"))
        self.trim_check.stateChanged.connect(self._refresh_preview)
        case_lay.addWidget(self.trim_check)

        self.special_check = AnimatedCheckBox(self.tr_("br_special"))
        self.special_check.stateChanged.connect(self._refresh_preview)
        case_lay.addWidget(self.special_check)
        case_lay.addStretch()
        root.addWidget(case_box)

        fr_box = QGroupBox(self.tr_("br_findreplace_title"))
        fr_lay = QHBoxLayout(fr_box)
        fr_lay.addWidget(QLabel(self.tr_("br_find")))
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText(self.tr_("br_find_placeholder"))
        self.find_input.textChanged.connect(self._refresh_preview)
        fr_lay.addWidget(self.find_input)
        fr_lay.addWidget(QLabel(self.tr_("br_replace")))
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText(self.tr_("br_replace_placeholder"))
        self.replace_input.textChanged.connect(self._refresh_preview)
        fr_lay.addWidget(self.replace_input)
        root.addWidget(fr_box)

        prev_box = QGroupBox(self.tr_("br_preview_title"))
        prev_lay = QVBoxLayout(prev_box)

        self.preview_table = QTableWidget(0, 2)
        self.preview_table.setHorizontalHeaderLabels([
            self.tr_("br_col_before"), self.tr_("br_col_after")
        ])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.preview_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setMinimumHeight(160)
        self.preview_table.setStyleSheet(
            "QTableWidget { border: none; font-size: 12px; }"
            "QHeaderView::section { font-weight: 700; padding: 4px; font-size: 12px; }"
        )
        prev_lay.addWidget(self.preview_table)
        root.addWidget(prev_box)
        root.setStretchFactor(prev_box, 1)

        btn_row = QHBoxLayout()
        self.rename_btn = QPushButton("✅ " + self.tr_("br_apply"))
        self.rename_btn.setMinimumHeight(36)
        _apply_dialog_btn(self.rename_btn, "BtnOK")
        cancel_btn = QPushButton(self.tr_("Annuler"))
        cancel_btn.setMinimumHeight(36)
        _apply_dialog_btn(cancel_btn, "BtnDecline")
        self.rename_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self.rename_btn)
        root.addLayout(btn_row)

    def _insert_var(self, var):
        pos = self.tpl_input.cursorPosition()
        txt = self.tpl_input.text()
        self.tpl_input.setText(txt[:pos] + var + txt[pos:])
        self.tpl_input.setCursorPosition(pos + len(var))

    def _sorted_files(self):
        files = list(self.files)
        idx = self.order_combo.currentIndex()
        if idx == 1:
            files.sort(key=lambda f: os.path.basename(f).lower())
        elif idx == 2:
            files.sort(key=lambda f: os.path.basename(f).lower(), reverse=True)
        elif idx == 3:
            def _nk(f):
                nums = re.findall(r'\d+', os.path.splitext(os.path.basename(f))[0])
                return [int(n) for n in nums] if nums else [0]
            files.sort(key=_nk)
        elif idx == 4:
            def _nkd(f):
                nums = re.findall(r'\d+', os.path.splitext(os.path.basename(f))[0])
                return [int(n) for n in nums] if nums else [0]
            files.sort(key=_nkd, reverse=True)
        elif idx == 5:
            files.sort(key=lambda f: os.path.getmtime(f) if os.path.exists(f) else 0)
        elif idx == 6:
            files.sort(key=lambda f: os.path.getmtime(f) if os.path.exists(f) else 0, reverse=True)
        return files

    def _apply_transforms(self, stem):
        if self.trim_check.isChecked():
            stem = stem.strip()
        if self.spaces_check.isChecked():
            stem = stem.replace(" ", "_")
        if self.special_check.isChecked():
            stem = re.sub(r'[^\w\-\.]', '', stem)
        find = self.find_input.text()
        if find:
            stem = stem.replace(find, self.replace_input.text())
        case_idx = self.case_combo.currentIndex()
        if case_idx == 1:
            stem = stem.upper()
        elif case_idx == 2:
            stem = stem.lower()
        elif case_idx == 3:
            stem = stem.title()
        return stem

    def _compute_new_name(self, file_path, index):
        stem = os.path.splitext(os.path.basename(file_path))[0]
        ext  = os.path.splitext(file_path)[1]
        num  = self.start_spin.value() + index * self.step_spin.value()
        pad  = self.pad_spin.value()
        date = datetime.now().strftime("%Y-%m-%d")

        tpl = self.tpl_input.text() or "{original}"
        new_stem = (tpl
                    .replace("{original}", stem)
                    .replace("{num}",      str(num).zfill(pad))
                    .replace("{date}",     date)
                    .replace("{ext}",      ext.lstrip(".")))
        new_stem = self._apply_transforms(new_stem)
        return new_stem + ext

    def _refresh_preview(self):
        from PySide6.QtGui import QColor
        files = self._sorted_files()
        self.preview_table.setRowCount(len(files))
        for i, fp in enumerate(files):
            old_name = os.path.basename(fp)
            new_name = self._compute_new_name(fp, i)
            old_item = QTableWidgetItem(old_name)
            new_item = QTableWidgetItem(new_name)
            if old_name != new_name:
                new_item.setForeground(QColor("#4ade80"))
            self.preview_table.setItem(i, 0, old_item)
            self.preview_table.setItem(i, 1, new_item)

    def get_rename_plan(self):
        """Return list of (old_path, new_name) in chosen order."""
        files = self._sorted_files()
        return [(fp, self._compute_new_name(fp, i)) for i, fp in enumerate(files)]
