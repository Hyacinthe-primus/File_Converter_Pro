"""PasswordDialog — Secure password input for PDF protection."""

from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox
from qss_helpers import _apply_dialog_btn

from utils import make_tm
from utils.translation_mixin import TranslationMixin


class PasswordDialog(TranslationMixin, QDialog):
    def __init__(self, parent=None, language="fr"):
        super().__init__(parent)
        self.language = language
        self._tm = make_tm(language)
        self.setWindowTitle(self.translate_text("Protéger PDF avec mot de passe"))
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)

        layout.addRow(self.translate_text("Mot de passe:"), self.password_input)
        layout.addRow(self.translate_text("Confirmer mot de passe:"), self.confirm_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_button = buttons.button(QDialogButtonBox.Ok)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        _apply_dialog_btn(ok_button, "BtnOK")
        _apply_dialog_btn(cancel_button, "BtnCancel")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def get_password(self):
        return self.password_input.text()
