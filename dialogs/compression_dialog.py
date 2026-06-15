"""CompressionDialog — Archive settings (ZIP/RAR/TAR, split, encrypt)."""

import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QComboBox, QLineEdit, QSpinBox, QGroupBox,
                               QDialogButtonBox, QMessageBox)
from PySide6.QtCore import Qt
from qss_helpers import _apply_dialog_btn
from widgets import AnimatedCheckBox

from utils import make_tm
from utils.translation_mixin import TranslationMixin


class CompressionDialog(TranslationMixin, QDialog):
    def __init__(self, parent=None, language="fr"):
        super().__init__(parent)
        self.language = language
        self._tm = make_tm(language)
        self.setWindowTitle(self.translate_text("Compresser des Fichiers"))
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        selection_info = QLabel()
        selection_info.setStyleSheet("font-weight: bold; color: #4dabf7;")
        selection_info.setWordWrap(True)
        layout.addWidget(selection_info)

        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel(self.translate_text("Format d'archive:")))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["ZIP", "RAR", "TAR.GZ", "TAR"])
        self.format_combo.currentIndexChanged.connect(self.update_format_info)
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)

        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel(self.translate_text("Niveau de compression:")))
        self.compression_level = QComboBox()
        self.compression_level.addItems([
            self.translate_text("Normal"),
            self.translate_text("Haute compression"),
            self.translate_text("Compression maximale")
        ])
        level_layout.addWidget(self.compression_level)
        layout.addLayout(level_layout)

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel(self.translate_text("Nom de l'archive:")))
        self.filename_input = QLineEdit()
        self.filename_input.setText("archive_compressee")
        name_layout.addWidget(self.filename_input)
        layout.addLayout(name_layout)

        options_group = QGroupBox(self.translate_text("Options"))
        options_layout = QVBoxLayout(options_group)

        self.encryption_checkbox = AnimatedCheckBox(self.translate_text("Protéger par mot de passe"))
        self.encryption_checkbox.stateChanged.connect(self.on_encryption_changed)

        self.split_checkbox = AnimatedCheckBox(self.translate_text("Fractionner l'archive en plusieurs parties"))
        self.split_checkbox.setChecked(False)
        self.split_checkbox.stateChanged.connect(self.on_split_changed)

        self.delete_original_checkbox = AnimatedCheckBox(self.translate_text("Supprimer les fichiers originaux après compression"))

        QLabel(self.translate_text("Taille par partie:"))

        self.split_size_spin = QSpinBox()
        self.split_size_spin.setRange(1, 10000)
        self.split_size_spin.setValue(100)
        self.split_size_spin.setSuffix(" MB")
        self.split_size_spin.setEnabled(False)
        self.split_size_spin.valueChanged.connect(self.on_split_size_changed)

        self.split_preset_combo = QComboBox()
        self.split_preset_combo.addItems([
            "10 MB (Email)",
            "25 MB (Email)",
            self.translate_text("100 MB (Partage web)"),
            "700 MB (CD)",
            "4.7 GB (DVD)",
            self.translate_text("8.5 GB (Double couche DVD)"),
            self.translate_text("Personnalisé")
        ])
        self.split_preset_combo.setEnabled(False)
        self.split_preset_combo.setCurrentIndex(2)

        split_size_layout = QHBoxLayout()
        split_size_layout.addWidget(QLabel(self.translate_text("Taille par partie:")))
        split_size_layout.addWidget(self.split_size_spin)
        split_size_layout.addWidget(self.split_preset_combo)
        split_size_layout.addStretch()

        self.split_info_label = QLabel()
        self.split_info_label.setStyleSheet("font-size: 10px; color: #1e2229; font-style: italic;")
        self.split_info_label.setWordWrap(True)
        self.split_info_label.setVisible(False)

        options_layout.addWidget(self.encryption_checkbox)
        options_layout.addWidget(self.split_checkbox)
        options_layout.addWidget(self.delete_original_checkbox)
        options_layout.addLayout(split_size_layout)
        options_layout.addWidget(self.split_info_label)

        layout.addWidget(options_group)

        self.format_info = QLabel()
        self.format_info.setStyleSheet("font-size: 11px; color: #1e2229; font-style: italic;")
        self.format_info.setWordWrap(True)
        layout.addWidget(self.format_info)

        self.split_note_label = QLabel()
        self.split_note_label.setStyleSheet("font-size: 10px; color: #dc3545; font-style: italic;")
        self.split_note_label.setWordWrap(True)
        self.split_note_label.setText(self.translate_text(
            "Note: Le fractionnement n'est disponible que pour les formats ZIP et RAR. "
            "Les archives TAR/TAR.GZ ne peuvent pas être fractionnées."
        ))
        self.split_note_label.setVisible(False)
        layout.addWidget(self.split_note_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_button = buttons.button(QDialogButtonBox.Ok)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        _apply_dialog_btn(ok_button, "BtnOK")
        _apply_dialog_btn(cancel_button, "BtnCancelGlassy")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.split_checkbox.stateChanged.connect(self.on_split_changed)
        self.format_combo.currentIndexChanged.connect(self.on_format_changed)
        self.split_preset_combo.currentIndexChanged.connect(self.on_split_preset_changed)
        self.split_size_spin.valueChanged.connect(lambda: self.on_split_preset_changed(0))
        self.update_split_controls_state()

        self.update_format_info()
        self.on_format_changed()

        self.apply_theme_style()

    def update_split_controls_state(self):
        is_split_enabled = self.split_checkbox.isChecked()
        is_custom = self.split_preset_combo.currentText() == self.translate_text("Personnalisé")

        self.split_preset_combo.setEnabled(is_split_enabled)
        self.split_size_spin.setEnabled(is_split_enabled and is_custom)

        if is_split_enabled:
            self.update_split_info_message()

    def apply_theme_style(self):
        parent = self.parent()
        if hasattr(parent, 'dark_mode'):
            if parent.dark_mode:
                self.setStyleSheet("""
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
                    QComboBox, QLineEdit, QSpinBox {
                        background-color: #2c313a;;
                        color: #e9ecef;
                        border: 1px solid #1e2229;
                        border-radius: 4px;
                        padding: 5px;
                    }
                    QCheckBox { color: #e9ecef; spacing: 8px; }
                    QCheckBox::indicator {
                        width: 16px; height: 16px;
                        border-radius: 3px;
                        border: 2px solid #1e2229;
                    }
                    QCheckBox::indicator:checked {
                        background-color: #4dabf7;
                        border: 2px solid #4dabf7;
                    }
                """)
            else:
                self.setStyleSheet("""
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
                    QComboBox, QLineEdit, QSpinBox {
                        background-color: #ffffff;
                        color: #212529;
                        border: 1px solid #ced4da;
                        border-radius: 4px;
                        padding: 5px;
                    }
                    QCheckBox { color: #212529; spacing: 8px; }
                    QCheckBox::indicator {
                        width: 16px; height: 16px;
                        border-radius: 3px;
                        border: 2px solid #adb5bd;
                    }
                    QCheckBox::indicator:checked {
                        background-color: #4dabf7;
                        border: 2px solid #4dabf7;
                    }
                """)

    def on_split_size_changed(self, value):
        if self.split_checkbox.isChecked() and self.split_preset_combo.currentText() == self.translate_text("Personnalisé"):
            template = self.translate_text("split_info_custom")
            message = template.format(value)
            self.split_info_label.setText(message)
            self.split_info_label.setVisible(True)

    def on_split_changed(self, state):
        self.update_split_controls_state()

    def on_split_preset_changed(self, index):
        preset_text = self.split_preset_combo.currentText()

        if preset_text == self.translate_text("Personnalisé"):
            self.split_size_spin.setEnabled(True)
        else:
            self.split_size_spin.setEnabled(False)

            preset_sizes = {
                "10 MB (Email)": 10,
                "25 MB (Email)": 25,
                "100 MB (Partage web)": 100,
                "700 MB (CD)": 700,
                "4.7 GB (DVD)": 4700,
                "8.5 GB (Double couche DVD)": 8500
            }

            if preset_text in preset_sizes:
                self.split_size_spin.setValue(preset_sizes[preset_text])

        self.update_split_info_message()

    def update_split_info_message(self):
        if self.split_checkbox.isChecked():
            preset_text = self.split_preset_combo.currentText()
            size_value = self.split_size_spin.value()

            if preset_text == self.translate_text("Personnalisé"):
                template = self.translate_text("split_info_custom")
                message = template.format(size_value)
            else:
                size_name = preset_text.split(' ')[0]
                template = self.translate_text("split_info_preset")
                message = template.format(size_value, size_name)

            self.split_info_label.setText(message)
            self.split_info_label.setVisible(True)
        else:
            self.split_info_label.setVisible(False)

    def on_format_changed(self):
        current_format = self.format_combo.currentText()

        if current_format in ["TAR", "TAR.GZ"]:
            self.split_checkbox.setEnabled(False)
            self.split_checkbox.setChecked(False)
            self.split_note_label.setVisible(True)
            self.split_size_spin.setEnabled(False)
            self.split_preset_combo.setEnabled(False)
        else:
            self.split_checkbox.setEnabled(True)
            self.split_note_label.setVisible(False)

            if self.split_checkbox.isChecked():
                self.split_preset_combo.setEnabled(True)
                if self.split_preset_combo.currentText() == self.translate_text("Personnalisé"):
                    self.split_size_spin.setEnabled(True)
                else:
                    self.split_size_spin.setEnabled(False)

                if self.split_preset_combo.currentIndex() > 0:
                    preset_text = self.split_preset_combo.currentText()
                    size_name = preset_text.split(' ')[0]
                    size_value = self.split_size_spin.value()
                    template = self.translate_text("split_info_preset")
                    self.split_info_label.setText(template.format(size_value, size_name))

    def on_encryption_changed(self, state):
        if state == Qt.Checked:
            parent = self.parent()
            if hasattr(parent, 'files_list'):
                total_size = sum(os.path.getsize(f) for f in parent.files_list if os.path.exists(f))
                total_size_mb = total_size / (1024 * 1024)

                if total_size_mb > 100:
                    message = self.translate_text(
                        f"⚠️ Attention: Vous allez chiffrer {total_size_mb:.1f} Mo de données.\n"
                        "Le chiffrement peut ralentir la compression."
                    )
                else:
                    message = self.translate_text(
                        "Le chiffrement ZIP utilise le standard AES-256 avec pyzipper (si installé).\n\n"
                        "Pour une meilleure sécurité, assurez-vous d'avoir installé pyzipper:\n"
                        "pip install pyzipper"
                    )
            else:
                message = self.translate_text(
                    "Le chiffrement ZIP utilise le standard AES-256 avec pyzipper (si installé).\n\n"
                    "Pour une meilleure sécurité, assurez-vous d'avoir installé pyzipper:\n"
                    "pip install pyzipper"
                )

            QMessageBox.information(self,
                                    self.translate_text("Information sur le chiffrement"),
                                    message)

    def update_format_info(self):
        format_info = {
            "ZIP": self.translate_text("Format universel, compatible avec tous les systèmes. Supporte le chiffrement et le fractionnement."),
            "RAR": self.translate_text("Meilleure compression mais nécessite WinRAR/7-Zip pour décompresser. Supporte le fractionnement."),
            "TAR.GZ": self.translate_text("Standard Unix/Linux, bonne compression. Ne supporte PAS le fractionnement."),
            "TAR": self.translate_text("Archive non compressée, préférable pour sauvegarde rapide. Ne supporte PAS le fractionnement.")
        }

        current_format = self.format_combo.currentText()
        self.format_info.setText(format_info.get(current_format, ""))

        if current_format in ["TAR", "TAR.GZ"]:
            self.split_note_label.setVisible(True)
        else:
            self.split_note_label.setVisible(False)

    def get_compression_settings(self):
        is_split_enabled = self.split_checkbox.isChecked()
        current_format = self.format_combo.currentText()
        is_split_supported = current_format in ["ZIP", "RAR",
                                                self.translate_text("ZIP"),
                                                self.translate_text("RAR")]

        split_size = 0
        if is_split_enabled and is_split_supported:
            split_size = self.split_size_spin.value()
            if split_size < 1:
                split_size = 100

        settings = {
            'format': current_format,
            'level': self.compression_level.currentText(),
            'name': self.filename_input.text().strip() or "archive_compressee",
            'password': self.encryption_checkbox.isChecked(),
            'split': is_split_enabled and is_split_supported,
            'split_size': split_size,
            'delete_originals': self.delete_original_checkbox.isChecked()
        }

        return settings
