"""SplitDialog - PDF splitting options (pages, ranges)."""

from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QSpinBox

from qss_helpers import _apply_dialog_btn
from templates import semantic_keys as sk
from utils import make_tm
from utils.translation_mixin import TranslationMixin


class SplitDialog(TranslationMixin, QDialog):
    def __init__(self, total_pages, parent=None, language="fr", pre_select_key=None, pages_per_file=None):
        super().__init__(parent)
        self.total_pages = total_pages
        self.language = language
        self._tm = make_tm(language)
        self.setWindowTitle(self.translate_text("split_pdf"))
        self.setup_ui()
        self._apply_template_values(pre_select_key, pages_per_file)

    def setup_ui(self):
        layout = QFormLayout(self)

        self.split_method = QComboBox()
        self.split_method.addItem(self.translate_text("by_pages"), sk.SPLIT_BY_PAGES)
        self.split_method.addItem(self.translate_text("all_pages"), sk.SPLIT_ALL_PAGES)
        self.split_method.addItem(self.translate_text("page_range"), sk.SPLIT_PAGE_RANGE)

        self.page_interval = QSpinBox()
        self.page_interval.setMinimum(1)
        self.page_interval.setMaximum(self.total_pages)
        self.page_interval.setValue(1)

        self.start_page = QSpinBox()
        self.start_page.setMinimum(1)
        self.start_page.setMaximum(self.total_pages)
        self.start_page.setValue(1)

        self.end_page = QSpinBox()
        self.end_page.setMinimum(1)
        self.end_page.setMaximum(self.total_pages)
        self.end_page.setValue(self.total_pages)

        layout.addRow(self.translate_text("split_method"), self.split_method)
        layout.addRow(self.translate_text("interval_pages"), self.page_interval)
        layout.addRow(self.translate_text("start_page"), self.start_page)
        layout.addRow(self.translate_text("end_page"), self.end_page)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_button = buttons.button(QDialogButtonBox.Ok)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        _apply_dialog_btn(ok_button, "BtnOK")
        _apply_dialog_btn(cancel_button, "BtnCancel")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def _apply_template_values(self, pre_select_key, pages_per_file):
        if isinstance(pre_select_key, str):
            index = self.split_method.findData(pre_select_key)
            if index >= 0:
                self.split_method.setCurrentIndex(index)

        try:
            pages = int(pages_per_file)
        except (TypeError, ValueError):
            pages = 1
        if pages < 1 or pages > self.total_pages:
            pages = 1
        self.page_interval.setValue(pages)
