"""CreateTemplateDialog — dialog for creating a new template."""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLabel, QLineEdit, QComboBox, QGroupBox, QPushButton, QWidget, QSpinBox,
                               QMessageBox)
from widgets import AnimatedCheckBox
from .template_manager import TemplateManager


class CreateTemplateDialog(QDialog):
    """Dialog for creating a new template"""

    def __init__(self, template_manager, parent_app, parent_dialog):
        super().__init__(parent_dialog)
        self.template_manager = template_manager
        self.parent_app = parent_app
        self.parent_dialog = parent_dialog
        
        self.setWindowTitle(self.parent_dialog.translate_text("Créer un nouveau template"))
        self.setMinimumSize(600, 520)
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(self.parent_dialog.translate_text("ex: Conversion Haute Qualité"))
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            self.parent_dialog.translate_text("Conversion PDF→Word"),
            self.parent_dialog.translate_text("Conversion Word→PDF"),
            self.parent_dialog.translate_text("Conversion Images→PDF"),  
            self.parent_dialog.translate_text("Fusion PDF"),
            self.parent_dialog.translate_text("Fusion Word"),
            self.parent_dialog.translate_text("Division PDF"), 
            self.parent_dialog.translate_text("Protection PDF"),  
            self.parent_dialog.translate_text("Compression"), 
            self.parent_dialog.translate_text("Optimisation de fichiers")
        ])
        self.type_combo.currentIndexChanged.connect(self.update_config_form)
        
        form_layout.addRow(self.parent_dialog.translate_text("Nom du template:"), self.name_input)
        form_layout.addRow(self.parent_dialog.translate_text("Type de template:"), self.type_combo)
        
        self.config_widget = QWidget()
        self.config_layout = QVBoxLayout(self.config_widget)
        
        form_layout.addRow(self.parent_dialog.translate_text("Configuration:"), self.config_widget)
        
        layout.addLayout(form_layout)
        
        self.advanced_group = QGroupBox(self.parent_dialog.translate_text("Options avancées"))
        advanced_layout = QVBoxLayout(self.advanced_group)
        
        self.memorize_check = AnimatedCheckBox(self.parent_dialog.translate_text("Mémoriser pour la prochaine fois"))
        self.memorize_check.setToolTip(self.parent_dialog.translate_text(
            "Si coché, les paramètres saisis ici seront pré-remplis à la prochaine ouverture de ce dialog."))
        _mem = getattr(self.parent_app, 'config', {}).get('last_template_creation_params', {})
        self.memorize_check.setChecked(_mem.get('memorize', False))

        self.set_as_default_check = AnimatedCheckBox(self.parent_dialog.translate_text("Définir comme template par défaut"))
        self.set_as_default_check.setToolTip(self.parent_dialog.translate_text(
            "Si coché, ce template s'applique silencieusement à chaque utilisation de cette opération, sans passer par le panel Templates."))
        self.set_as_default_check.setChecked(False)

        advanced_layout.addWidget(self.memorize_check)
        advanced_layout.addWidget(self.set_as_default_check)
        
        layout.addWidget(self.advanced_group)
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        
        create_btn = QPushButton("💾 " + self.parent_dialog.translate_text("Créer le template"))
        create_btn.clicked.connect(self.create_template)
        
        cancel_btn = QPushButton(self.parent_dialog.translate_text("Annuler"))
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
        
        self.update_config_form()
    
    def create_images_to_pdf_config(self):
        self.separate_images_check = AnimatedCheckBox(
            self.parent_dialog.translate_text("Un PDF par image (au lieu de tout fusionner)"))
        self.separate_images_check.setChecked(False)
        self.config_layout.addWidget(self.separate_images_check)

    def create_word_merge_config(self):
        order_label = QLabel(self.parent_dialog.translate_text("Ordre de fusion:"))
        self.word_merge_order_combo = QComboBox()
        self.word_merge_order_combo.addItems([
            self.parent_dialog.translate_text("Ordre actuel (liste principale)"),
            self.parent_dialog.translate_text("Alphabétique (A→Z)"),
            self.parent_dialog.translate_text("Alphabétique (Z→A)"),
            self.parent_dialog.translate_text("Numérique (1→9)"),
            self.parent_dialog.translate_text("Numérique (9→1)"),
            self.parent_dialog.translate_text("Date (ancien→nouveau)"),
            self.parent_dialog.translate_text("Date (nouveau→ancien)"),
            self.parent_dialog.translate_text("Manuel (glisser-déposer)"),
        ])
        name_label = QLabel(self.parent_dialog.translate_text("Template de nom de fichier:"))
        self.word_merge_name_input = QLineEdit()
        self.word_merge_name_input.setText("fusion_word_{date}_{heure}")
        self.config_layout.addWidget(order_label)
        self.config_layout.addWidget(self.word_merge_order_combo)
        self.config_layout.addWidget(name_label)
        self.config_layout.addWidget(self.word_merge_name_input)

    def create_compression_config(self):
        self.config_layout.setContentsMargins(0, 4, 0, 4)
        self.config_layout.setSpacing(4)

        format_label = QLabel(self.parent_dialog.translate_text("Format d'archive:"))

        self.compression_format_combo = QComboBox()
        self.compression_format_combo.addItems([
            self.parent_dialog.translate_text("ZIP"),
            self.parent_dialog.translate_text("TAR.GZ"),
            self.parent_dialog.translate_text("TAR"),
            self.parent_dialog.translate_text("RAR")
        ])
        self.compression_format_combo.setMinimumHeight(30)
        self.compression_format_combo.setMaximumHeight(35)

        level_label = QLabel(self.parent_dialog.translate_text("Niveau de compression:"))
        self.compression_level_combo = QComboBox()
        self.compression_level_combo.addItems([
            self.parent_dialog.translate_text("Normal"),
            self.parent_dialog.translate_text("Haute compression"),
            self.parent_dialog.translate_text("Compression maximale")
        ])
        self.compression_level_combo.setMinimumHeight(28)
        self.compression_level_combo.setMaximumHeight(32)

        self.encrypt_check = AnimatedCheckBox(self.parent_dialog.translate_text("Protéger par mot de passe"))
        self.encrypt_check.setChecked(False)

        self.delete_originals_check = AnimatedCheckBox(self.parent_dialog.translate_text("Supprimer les fichiers originaux après compression"))
        self.delete_originals_check.setChecked(False)

        self.split_check = AnimatedCheckBox(self.parent_dialog.translate_text("Fractionner l'archive en plusieurs parties"))
        self.split_check.setChecked(False)

        split_size_label = QLabel(self.parent_dialog.translate_text("Taille par partie (Mo):"))
        self.split_size_spin = QSpinBox()
        self.split_size_spin.setRange(1, 1000)
        self.split_size_spin.setValue(100)
        self.split_size_spin.setMinimumHeight(28)
        self.split_size_spin.setEnabled(False)

        self.split_check.stateChanged.connect(lambda state: self.split_size_spin.setEnabled(state))

        self.config_layout.addWidget(format_label)
        self.config_layout.addWidget(self.compression_format_combo)
        self.config_layout.addSpacing(8)

        self.config_layout.addWidget(level_label)
        self.config_layout.addWidget(self.compression_level_combo)
        self.config_layout.addSpacing(8)

        self.config_layout.addWidget(self.encrypt_check)
        self.config_layout.addWidget(self.delete_originals_check)
        self.config_layout.addWidget(self.split_check)
        self.config_layout.addSpacing(8)

        self.config_layout.addWidget(split_size_label)
        self.config_layout.addWidget(self.split_size_spin)

    def update_config_form(self):
        while self.config_layout.count():
            item = self.config_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        template_type = self.type_combo.currentText()
        
        if template_type == self.parent_dialog.translate_text("Conversion PDF→Word"):
            self.create_pdf_to_word_config()
        elif template_type == self.parent_dialog.translate_text("Conversion Word→PDF"):
            self.create_word_to_pdf_config()
        elif template_type == self.parent_dialog.translate_text("Conversion Images→PDF"):
            self.create_images_to_pdf_config()  
        elif template_type == self.parent_dialog.translate_text("Fusion PDF"):
            self.create_pdf_merge_config()
        elif template_type == self.parent_dialog.translate_text("Fusion Word"):
            self.create_word_merge_config()  
        elif template_type == self.parent_dialog.translate_text("Division PDF"):
            self.create_pdf_split_config()  
        elif template_type == self.parent_dialog.translate_text("Protection PDF"):
            self.create_pdf_protection_config()
        elif template_type == self.parent_dialog.translate_text("Compression"):
            self.create_compression_config()
        elif template_type == self.parent_dialog.translate_text("Optimisation de fichiers"):
            self.create_optimization_config()

    def create_pdf_split_config(self):
        method_label = QLabel(self.parent_dialog.translate_text("Méthode de division:"))
        self.split_method_combo = QComboBox()
        self.split_method_combo.addItems([
            self.parent_dialog.translate_text("Par pages"),
            self.parent_dialog.translate_text("Toutes les pages"),
            self.parent_dialog.translate_text("Plage de pages"),
        ])

        pages_label = QLabel(self.parent_dialog.translate_text("Pages par fichier:"))
        self.pages_per_file_spin = QSpinBox()
        self.pages_per_file_spin.setRange(1, 500)
        self.pages_per_file_spin.setValue(1)
        self.pages_per_file_spin.setMinimumHeight(28)

        self.config_layout.addWidget(method_label)
        self.config_layout.addWidget(self.split_method_combo)
        self.config_layout.addWidget(pages_label)
        self.config_layout.addWidget(self.pages_per_file_spin)

    def create_pdf_protection_config(self):
        level_label = QLabel(self.parent_dialog.translate_text("Mode:"))
        self.protection_level_combo = QComboBox()
        self.protection_level_combo.addItems([
            self.parent_dialog.translate_text("Basique (restrictions uniquement)"),
            self.parent_dialog.translate_text("Avancé (mot de passe + restrictions)"),
        ])

        permissions_group = QGroupBox(self.parent_dialog.translate_text("Permissions"))
        permissions_layout = QVBoxLayout(permissions_group)

        self.allow_printing_check = AnimatedCheckBox(self.parent_dialog.translate_text("Autoriser l'impression"))
        self.allow_printing_check.setChecked(True)

        self.allow_copying_check = AnimatedCheckBox(self.parent_dialog.translate_text("Autoriser la copie de texte"))
        self.allow_copying_check.setChecked(True)

        self.allow_modifications_check = AnimatedCheckBox(self.parent_dialog.translate_text("Autoriser les modifications"))
        self.allow_modifications_check.setChecked(False)

        permissions_layout.addWidget(self.allow_printing_check)
        permissions_layout.addWidget(self.allow_copying_check)
        permissions_layout.addWidget(self.allow_modifications_check)

        self.config_layout.addWidget(level_label)
        self.config_layout.addWidget(self.protection_level_combo)
        self.config_layout.addWidget(permissions_group)

    def create_pdf_to_word_config(self):
        mode_label = QLabel(self.parent_dialog.translate_text("Mode de conversion:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            self.parent_dialog.translate_text("Conserver les images et la mise en page"),
            self.parent_dialog.translate_text("Texte brut uniquement"),
            self.parent_dialog.translate_text("Texte complet (texte + texte des images)"),
        ])
        self.config_layout.addWidget(mode_label)
        self.config_layout.addWidget(self.mode_combo)

    def create_word_to_pdf_config(self):
        mode_label = QLabel(self.parent_dialog.translate_text("Mode de conversion:"))
        self.word_mode_combo = QComboBox()
        self.word_mode_combo.addItems([
            self.parent_dialog.translate_text("Conserver toute la mise en page"),
            self.parent_dialog.translate_text("Texte uniquement"),
        ])

        quality_label = QLabel(self.parent_dialog.translate_text("Qualité d'image:"))
        self.image_quality_combo = QComboBox()
        self.image_quality_combo.addItems([
            self.parent_dialog.translate_text("Haute (300 DPI)"),
            self.parent_dialog.translate_text("Standard (150 DPI)"),
            self.parent_dialog.translate_text("Basse (72 DPI)"),
        ])

        self.include_metadata_check = AnimatedCheckBox(
            self.parent_dialog.translate_text("Inclure les métadonnées"))
        self.include_metadata_check.setChecked(True)

        self.compress_images_check = AnimatedCheckBox(
            self.parent_dialog.translate_text("Compresser les images"))
        self.compress_images_check.setChecked(True)

        self.config_layout.addWidget(mode_label)
        self.config_layout.addWidget(self.word_mode_combo)
        self.config_layout.addWidget(quality_label)
        self.config_layout.addWidget(self.image_quality_combo)
        self.config_layout.addWidget(self.include_metadata_check)
        self.config_layout.addWidget(self.compress_images_check)
    
    def create_pdf_merge_config(self):
        order_label = QLabel(self.parent_dialog.translate_text("Ordre de fusion:"))
        self.merge_order_combo = QComboBox()
        self.merge_order_combo.addItems([
            self.parent_dialog.translate_text("Ordre actuel (liste principale)"),
            self.parent_dialog.translate_text("Alphabétique (A→Z)"),
            self.parent_dialog.translate_text("Alphabétique (Z→A)"),
            self.parent_dialog.translate_text("Numérique (1→9)"),
            self.parent_dialog.translate_text("Numérique (9→1)"),
            self.parent_dialog.translate_text("Date (ancien→nouveau)"),
            self.parent_dialog.translate_text("Date (nouveau→ancien)"),
            self.parent_dialog.translate_text("Manuel (glisser-déposer)"),
        ])
        name_label = QLabel(self.parent_dialog.translate_text("Template de nom de fichier:"))
        self.name_template_input = QLineEdit()
        self.name_template_input.setText("fusion_{date}_{heure}")
        self.config_layout.addWidget(order_label)
        self.config_layout.addWidget(self.merge_order_combo)
        self.config_layout.addWidget(name_label)
        self.config_layout.addWidget(self.name_template_input)

    def create_optimization_config(self):
        tr = self.parent_dialog.translate_text

        self.config_layout.addWidget(QLabel(tr("Mode d'optimisation")))
        self.optim_mode_combo = QComboBox()
        self.optim_mode_combo.addItems([
            tr("Compression  –  réduit la taille du fichier"),
            tr("Nettoyage  –  supprime uniquement les métadonnées"),
            tr("Compression + Nettoyage  –  recommandé"),
        ])
        self.optim_mode_combo.setCurrentIndex(2)
        self.config_layout.addWidget(self.optim_mode_combo)

        self.config_layout.addWidget(QLabel(tr("Niveau de compression")))
        self.optim_quality_combo = QComboBox()
        self.optim_quality_combo.addItems([
            "I  —  " + tr("Haute qualité  (gain modéré)"),
            "II  —  " + tr("Équilibré  (recommandé)"),
            "III  —  " + tr("Maximum  (qualité réduite)"),
        ])
        self.optim_quality_combo.setCurrentIndex(1)
        self.config_layout.addWidget(self.optim_quality_combo)

        self.config_layout.addWidget(QLabel(tr("Options")))
        from PySide6.QtWidgets import QCheckBox as _QCB
        self.optim_metadata_check = _QCB(tr("Supprimer les métadonnées personnelles"))
        self.optim_metadata_check.setChecked(True)
        self.optim_images_check = _QCB(tr("Recompresser les images intégrées"))
        self.optim_images_check.setChecked(True)
        self.optim_backup_check = _QCB(tr("Garder une copie des originaux"))
        self.optim_backup_check.setChecked(True)
        self.config_layout.addWidget(self.optim_metadata_check)
        self.config_layout.addWidget(self.optim_images_check)
        self.config_layout.addWidget(self.optim_backup_check)

    def create_template(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                self.parent_dialog.translate_text("Erreur"),
                self.parent_dialog.translate_text("Veuillez entrer un nom pour le template.")
            )
            return
        
        template_type = self.type_combo.currentText()
        
        config_data = {}
        
        if template_type == self.parent_dialog.translate_text("Conversion PDF→Word"):
            config_data = {
                'mode': self.mode_combo.currentText()
            }
        elif template_type == self.parent_dialog.translate_text("Conversion Word→PDF"):
            config_data = {
                'mode':             self.word_mode_combo.currentText(),
                'quality':          self.image_quality_combo.currentText(),
                'include_metadata': self.include_metadata_check.isChecked(),
                'compress_images':  self.compress_images_check.isChecked(),
            }
        elif template_type == self.parent_dialog.translate_text("Conversion Images→PDF"):
            config_data = {
                'separate': self.separate_images_check.isChecked(),
            }
        elif template_type == self.parent_dialog.translate_text("Fusion PDF"):
            config_data = {
                'merge_order':  self.merge_order_combo.currentText(),
                'name_template': self.name_template_input.text(),
            }
        elif template_type == self.parent_dialog.translate_text("Fusion Word"):
            config_data = {
                'merge_order':  self.word_merge_order_combo.currentText(),
                'name_template': self.word_merge_name_input.text(),
            }
        elif template_type == self.parent_dialog.translate_text("Division PDF"):
            config_data = {
                'split_method':   self.split_method_combo.currentText(),
                'pages_per_file': self.pages_per_file_spin.value(),
            }
        elif template_type == self.parent_dialog.translate_text("Protection PDF"):
            config_data = {
                'mode':               self.protection_level_combo.currentText(),
                'allow_printing':     self.allow_printing_check.isChecked(),
                'allow_copying':      self.allow_copying_check.isChecked(),
                'allow_modifications': self.allow_modifications_check.isChecked(),
            }
        elif template_type == self.parent_dialog.translate_text("Compression"):
            config_data = {
                'format':            self.compression_format_combo.currentText(),
                'compression_level': self.compression_level_combo.currentText(),
                'encrypt':           self.encrypt_check.isChecked(),
                'delete_originals':  self.delete_originals_check.isChecked(),
                'split_archive':     self.split_check.isChecked(),
                'split_size':        self.split_size_spin.value() if self.split_check.isChecked() else 0,
            }
        elif template_type == self.parent_dialog.translate_text("Optimisation de fichiers"):
            _mode_map = {
                self.parent_dialog.translate_text("Compression  –  réduit la taille du fichier"): 0,
                self.parent_dialog.translate_text("Nettoyage  –  supprime uniquement les métadonnées"): 1,
                self.parent_dialog.translate_text("Compression + Nettoyage  –  recommandé"): 2,
            }
            config_data = {
                'optimization_type': _mode_map.get(self.optim_mode_combo.currentText(), 2),
                'quality_level':     self.optim_quality_combo.currentIndex(),
                'remove_metadata':   self.optim_metadata_check.isChecked(),
                'compress_images':   self.optim_images_check.isChecked(),
                'keep_backup':       self.optim_backup_check.isChecked(),
            }
        
        if self.memorize_check.isChecked() and hasattr(self.parent_app, 'config'):
            self.parent_app.config['last_template_creation_params'] = {
                'memorize': True, 'type': template_type,
            }
            try:
                self.parent_app.config_manager.save_config(self.parent_app.config)
            except Exception:
                pass
        elif hasattr(self.parent_app, 'config'):
            self.parent_app.config.pop('last_template_creation_params', None)
            try:
                self.parent_app.config_manager.save_config(self.parent_app.config)
            except Exception:
                pass

        if self.set_as_default_check.isChecked():
            config_data['is_default'] = True

        self.template_manager.db_manager.save_template(name, template_type, config_data)
        self.template_manager.load_templates()

        if self.set_as_default_check.isChecked():
            new_id = None
            for tid, tpl in self.template_manager.current_templates.items():
                if (tpl['name'] == name and
                        TemplateManager.normalize_type(tpl['type']) ==
                        TemplateManager.normalize_type(template_type)):
                    new_id = tid
                    break
            if new_id is not None:
                self.template_manager.set_default_template(new_id, template_type)

        QMessageBox.information(
            self,
            self.parent_dialog.translate_text("Succès"),
            self.parent_dialog.translate_text("template_created").format(name)
        )

        _cfg = getattr(self.parent_app, 'config', {})
        ach = getattr(self.parent_app, 'achievement_system', None) if _cfg.get("achievements_enabled", True) else None
        if ach:
            try: ach.record_template_created(template_type)
            except Exception: pass

        self.accept()
