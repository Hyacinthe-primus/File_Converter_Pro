"""TemplateEditorDialog — dialog for editing an existing template."""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLabel, QLineEdit, QGroupBox, QPushButton)


class TemplateEditorDialog(QDialog):
    """Dialog for editing an existing template"""
    
    def __init__(self, template, parent_dialog):
        super().__init__(parent_dialog)
        self.template = template
        self.parent_dialog = parent_dialog
        
        self.setWindowTitle(self.parent_dialog.translate_text("Modifier le template"))
        self.setMinimumSize(500, 400)
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        info_group = QGroupBox(self.parent_dialog.translate_text("Informations"))
        info_layout = QFormLayout(info_group)
        
        self.name_input = QLineEdit(self.template['name'])
        info_layout.addRow(self.parent_dialog.translate_text("Nom:"), self.name_input)
        
        type_label = QLabel(self.template['type'])
        info_layout.addRow(self.parent_dialog.translate_text("Type:"), type_label)
        
        layout.addWidget(info_group)
        
        config_group = QGroupBox(self.parent_dialog.translate_text("Configuration"))
        config_layout = QVBoxLayout(config_group)
        
        config_text = self.parent_dialog.format_config_for_display(
            self.template['config'], 
            self.template['type']
        )
        config_label = QLabel(config_text)
        config_label.setWordWrap(True)
        
        config_layout.addWidget(config_label)
        
        note_label = QLabel(
            self.parent_dialog.translate_text("Note: L'édition avancée de la configuration sera disponible dans une future version.")
        )
        note_label.setStyleSheet("color: #666; font-style: italic;")
        config_layout.addWidget(note_label)
        
        layout.addWidget(config_group)
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 " + self.parent_dialog.translate_text("Sauvegarder les modifications"))
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton(self.parent_dialog.translate_text("Annuler"))
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)

    def get_updated_config(self):
        return self.template['config']
