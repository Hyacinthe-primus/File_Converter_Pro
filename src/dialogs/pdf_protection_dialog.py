"""PdfProtectionDialog - Dialog for PDF protection options."""

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from qss_helpers import _apply_dialog_btn
from translations import TranslationManager
from widgets import AnimatedCheckBox


class PdfProtectionDialog(QDialog):
    """Dialog for PDF protection options — Basic or Advanced."""

    def __init__(self, parent=None, language="fr"):
        super().__init__(parent)
        self._tm = TranslationManager()
        self._tm.set_language(language)
        self.setWindowTitle(self.tr_("protect_pdf_with_password"))
        self.setMinimumWidth(400)
        self._setup_ui()

    def tr_(self, text):
        return self._tm.translate_text(text)

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        mode_lay = QHBoxLayout()
        mode_lay.addWidget(QLabel(self.tr_("mode")))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(
            [
                self.tr_("basic_only_restrictions"),
                self.tr_("advanced_password_restrictions"),
            ]
        )
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_lay.addWidget(self.mode_combo)
        lay.addLayout(mode_lay)

        self._pwd_group = QGroupBox(self.tr_("password"))
        pwd_lay = QFormLayout(self._pwd_group)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        pwd_lay.addRow(self.tr_("password"), self.password_input)
        pwd_lay.addRow(self.tr_("confirm"), self.confirm_input)
        self._pwd_group.setVisible(False)
        lay.addWidget(self._pwd_group)

        perm_group = QGroupBox(self.tr_("Permissions"))
        perm_lay = QVBoxLayout(perm_group)

        self.allow_print_check = AnimatedCheckBox(self.tr_("allow_printing"))
        self.allow_print_check.setChecked(True)
        self.allow_copy_check = AnimatedCheckBox(self.tr_("allow_text_copying"))
        self.allow_copy_check.setChecked(True)
        self.allow_copy_accessibility_check = AnimatedCheckBox(self.tr_("allow_copying_for_accessibility"))
        self.allow_copy_accessibility_check.setChecked(True)
        self.allow_modify_check = AnimatedCheckBox(self.tr_("allow_content_modifications"))
        self.allow_modify_check.setChecked(False)
        self.allow_annotations_check = AnimatedCheckBox(self.tr_("allow_comments_annotations"))
        self.allow_annotations_check.setChecked(False)
        self.allow_forms_check = AnimatedCheckBox(self.tr_("allow_form_filling"))
        self.allow_forms_check.setChecked(False)
        self.allow_assemble_check = AnimatedCheckBox(self.tr_("allow_document_assembly_signing"))
        self.allow_assemble_check.setChecked(False)

        perm_lay.addWidget(self.allow_print_check)
        perm_lay.addWidget(self.allow_copy_check)
        perm_lay.addWidget(self.allow_copy_accessibility_check)
        perm_lay.addWidget(self.allow_modify_check)
        perm_lay.addWidget(self.allow_annotations_check)
        perm_lay.addWidget(self.allow_forms_check)
        perm_lay.addWidget(self.allow_assemble_check)
        lay.addWidget(perm_group)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton(self.tr_("apply"))
        ok_btn.setMinimumHeight(36)
        ok_btn.setStyleSheet("""
            QPushButton { background:#28a745; color:white; border:none;
                          border-radius:6px; font-weight:bold; padding:6px 16px; }
            QPushButton:hover { background:#218838; }
        """)
        cancel_btn = QPushButton(self.tr_("cancel"))
        cancel_btn.setMinimumHeight(36)
        _apply_dialog_btn(cancel_btn, "BtnCancelGlassy")
        ok_btn.clicked.connect(self._validate)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        lay.addLayout(btn_row)

    def _on_mode_changed(self, idx):
        self._pwd_group.setVisible(idx == 1)
        self.adjustSize()

    def is_advanced(self):
        return self.mode_combo.currentIndex() == 1

    def get_password(self):
        return self.password_input.text() if self.is_advanced() else None

    def _validate(self):
        if self.is_advanced():
            pwd = self.password_input.text()
            if not pwd:
                QMessageBox.warning(self, self.tr_("error"), self.tr_("please_enter_a_password"))
                return
            if self.password_input.text() != self.confirm_input.text():
                QMessageBox.warning(self, self.tr_("error"), self.tr_("passwords_do_not_match"))
                return
        self.accept()
