"""MergeOrderDialog - Dialog for choosing merge order."""

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
    QVBoxLayout,
)

from context_menu.conversion_helpers import _sort_files
from qss_helpers import _apply_dialog_btn
from utils import make_tm
from utils.translation_mixin import TranslationMixin
from widgets import AnimatedCheckBox


class MergeOrderDialog(TranslationMixin, QDialog):
    """Dialog for choosing merge order and optionally reordering files manually."""

    def __init__(self, files, file_type, parent=None, language="fr", pre_select_key=None):
        super().__init__(parent)
        self._tm = make_tm(language)
        self.files = list(files)
        self.file_type = file_type
        self.setWindowTitle(self.translate_text("merge_order"))
        self.setMinimumWidth(480)
        self.setMinimumHeight(400)
        self._setup_ui()
        self.apply_theme_style()
        self.resize(self.layout().sizeHint().expandedTo(self.layout().minimumSize()))
        if pre_select_key and pre_select_key in self._radio_map:
            self._radio_map[pre_select_key].setChecked(True)

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        order_group = QGroupBox(self.translate_text("choose_order"))
        order_lay = QVBoxLayout(order_group)

        self.order_buttons = QButtonGroup(self)
        self.order_buttons.setExclusive(True)
        parent_dark = bool(getattr(self.parent(), "dark_mode", False))
        orders = [
            ("alpha_az", "🔤 " + self.translate_text("alphabetical_a_to_z")),
            ("alpha_za", "🔤 " + self.translate_text("alphabetical_z_to_a")),
            ("num_asc", "🔢 " + self.translate_text("numeric_1_to_9")),
            ("num_desc", "🔢 " + self.translate_text("numeric_9_to_1")),
            ("date_asc", "📅 " + self.translate_text("date_oldest_to_newest")),
            ("date_desc", "📅 " + self.translate_text("date_newest_to_oldest")),
            ("manual", "✋ " + self.translate_text("manual_drag_and_drop")),
            ("current", "📋 " + self.translate_text("current_order_main_list")),
        ]
        self._radio_map = {}
        for key, label in orders:
            cb = AnimatedCheckBox(label)
            cb.set_dark_mode(parent_dark)
            self.order_buttons.addButton(cb)
            order_lay.addWidget(cb)
            self._radio_map[key] = cb
        self._radio_map["current"].setChecked(True)

        lay.addWidget(order_group)

        self._manual_group = QGroupBox(self.translate_text("reorder_files"))
        manual_lay = QVBoxLayout(self._manual_group)
        hint = QLabel(self.translate_text("drag_and_drop_to_reorder_then_click_merge"))
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
        merge_btn = QPushButton(self.translate_text("merge"))
        merge_btn.setMinimumHeight(36)
        _apply_dialog_btn(merge_btn, "BtnOK")
        cancel_btn = QPushButton(self.translate_text("cancel"))
        cancel_btn.setMinimumHeight(36)
        _apply_dialog_btn(cancel_btn, "BtnCancelGlassy")
        merge_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(merge_btn)
        lay.addLayout(btn_row)

    def get_order_key(self):
        """Return the key of the chosen merge order (e.g. "alpha_az", "current")."""
        for key, radio in self._radio_map.items():
            if radio.isChecked():
                return key
        return "current"

    def get_ordered_files(self):
        """Return files in the chosen order using the shared merge ordering rules."""
        order_key = self.get_order_key()
        if order_key == "manual":
            return [
                self._manual_list.item(i).data(Qt.UserRole)
                for i in range(self._manual_list.count())
            ]
        return _sort_files(list(self.files), order_key)

    def apply_theme_style(self):
        """Apply white/light or dark theme styling based on the parent window."""
        parent = self.parent()
        dark = bool(getattr(parent, "dark_mode", False))
        if dark:
            self.setStyleSheet(
                """
                QDialog { background-color: #1e2229; }
                QLabel { color: #e9ecef; }
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
