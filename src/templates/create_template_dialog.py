"""CreateTemplateDialog - dialog for creating a new template."""

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
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from widgets import AnimatedCheckBox

from .template_manager import TemplateManager


class CreateTemplateDialog(QDialog):
    """Dialog for creating a new template"""

    def __init__(self, template_manager, parent_app, parent_dialog):
        super().__init__(parent_dialog)
        self.template_manager = template_manager
        self.parent_app = parent_app
        self.parent_dialog = parent_dialog

        self.setWindowTitle(self.parent_dialog.translate_text("create_new_template"))
        self.setMinimumSize(600, 520)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(self.parent_dialog.translate_text("e_g_high_quality_conversion"))

        self.type_combo = QComboBox()
        self.type_combo.addItems(
            [
                self.parent_dialog.translate_text("pdf_to_word_conversion"),
                self.parent_dialog.translate_text("word_to_pdf_conversion"),
                self.parent_dialog.translate_text("images_to_pdf_conversion"),
                self.parent_dialog.translate_text("pdf_merge"),
                self.parent_dialog.translate_text("word_merge"),
                self.parent_dialog.translate_text("pdf_split"),
                self.parent_dialog.translate_text("pdf_protection"),
                self.parent_dialog.translate_text("Compression"),
                self.parent_dialog.translate_text("file_optimization"),
            ]
        )
        self.type_combo.currentIndexChanged.connect(self.update_config_form)

        form_layout.addRow(self.parent_dialog.translate_text("template_name"), self.name_input)
        form_layout.addRow(self.parent_dialog.translate_text("template_type"), self.type_combo)

        self.config_widget = QWidget()
        self.config_layout = QVBoxLayout(self.config_widget)

        form_layout.addRow(self.parent_dialog.translate_text("configuration"), self.config_widget)

        layout.addLayout(form_layout)

        self.advanced_group = QGroupBox(self.parent_dialog.translate_text("advanced_options"))
        advanced_layout = QVBoxLayout(self.advanced_group)

        self.memorize_check = AnimatedCheckBox(self.parent_dialog.translate_text("remember_for_next_time"))
        self.memorize_check.setToolTip(
            self.parent_dialog.translate_text("remember_creation_params_tooltip")
        )
        _mem = getattr(self.parent_app, "config", {}).get("last_template_creation_params", {})
        self.memorize_check.setChecked(_mem.get("memorize", False))

        self.set_as_default_check = AnimatedCheckBox(
            self.parent_dialog.translate_text("set_as_default_template")
        )
        self.set_as_default_check.setToolTip(
            self.parent_dialog.translate_text(
                "if_checked_this_template_will_be_applied_silently_every_time_thi"  # noqa: E501
            )
        )
        self.set_as_default_check.setChecked(False)

        advanced_layout.addWidget(self.memorize_check)
        advanced_layout.addWidget(self.set_as_default_check)

        layout.addWidget(self.advanced_group)
        layout.addStretch()

        button_layout = QHBoxLayout()

        create_btn = QPushButton("💾 " + self.parent_dialog.translate_text("create_template"))
        create_btn.clicked.connect(self.create_template)

        cancel_btn = QPushButton(self.parent_dialog.translate_text("cancel"))
        cancel_btn.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(create_btn)

        layout.addLayout(button_layout)

        self.update_config_form()

    def create_images_to_pdf_config(self):
        self.separate_images_check = AnimatedCheckBox(
            self.parent_dialog.translate_text("create_separate_pdf_per_image_instead_of_merging")
        )
        self.separate_images_check.setChecked(False)
        self.config_layout.addWidget(self.separate_images_check)

    def create_word_merge_config(self):
        order_label = QLabel(self.parent_dialog.translate_text("merge_order_2"))
        self.word_merge_order_combo = QComboBox()
        self.word_merge_order_combo.addItems(
            [
                self.parent_dialog.translate_text("current_order_main_list"),
                self.parent_dialog.translate_text("alphabetical_a_to_z"),
                self.parent_dialog.translate_text("alphabetical_z_to_a"),
                self.parent_dialog.translate_text("numeric_1_to_9"),
                self.parent_dialog.translate_text("numeric_9_to_1"),
                self.parent_dialog.translate_text("date_oldest_to_newest"),
                self.parent_dialog.translate_text("date_newest_to_oldest"),
                self.parent_dialog.translate_text("manual_drag_and_drop"),
            ]
        )
        name_label = QLabel(self.parent_dialog.translate_text("filename_template"))
        self.word_merge_name_input = QLineEdit()
        self.word_merge_name_input.setText("fusion_word_{date}_{heure}")
        self.config_layout.addWidget(order_label)
        self.config_layout.addWidget(self.word_merge_order_combo)
        self.config_layout.addWidget(name_label)
        self.config_layout.addWidget(self.word_merge_name_input)

    def create_compression_config(self):
        self.config_layout.setContentsMargins(0, 4, 0, 4)
        self.config_layout.setSpacing(4)

        format_label = QLabel(self.parent_dialog.translate_text("archive_format"))

        self.compression_format_combo = QComboBox()
        self.compression_format_combo.addItems(
            [
                self.parent_dialog.translate_text("ZIP"),
                self.parent_dialog.translate_text("7Z"),
                self.parent_dialog.translate_text("tar_gz"),
                self.parent_dialog.translate_text("TAR"),
            ]
        )
        self.compression_format_combo.setMinimumHeight(30)
        self.compression_format_combo.setMaximumHeight(35)

        level_label = QLabel(self.parent_dialog.translate_text("compression_level"))
        self.compression_level_combo = QComboBox()
        self.compression_level_combo.addItems(
            [
                self.parent_dialog.translate_text("Normal"),
                self.parent_dialog.translate_text("high_compression"),
                self.parent_dialog.translate_text("maximum_compression"),
            ]
        )
        self.compression_level_combo.setMinimumHeight(28)
        self.compression_level_combo.setMaximumHeight(32)

        self.encrypt_check = AnimatedCheckBox(self.parent_dialog.translate_text("protect_with_password"))
        self.encrypt_check.setChecked(False)

        self.delete_originals_check = AnimatedCheckBox(
            self.parent_dialog.translate_text("delete_original_files_after_compression")
        )
        self.delete_originals_check.setChecked(False)

        self.split_check = AnimatedCheckBox(
            self.parent_dialog.translate_text("split_archive_into_multiple_parts")
        )
        self.split_check.setChecked(False)

        split_size_label = QLabel(self.parent_dialog.translate_text("part_size_mb"))
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

        if template_type == self.parent_dialog.translate_text("pdf_to_word_conversion"):
            self.create_pdf_to_word_config()
        elif template_type == self.parent_dialog.translate_text("word_to_pdf_conversion"):
            self.create_word_to_pdf_config()
        elif template_type == self.parent_dialog.translate_text("images_to_pdf_conversion"):
            self.create_images_to_pdf_config()
        elif template_type == self.parent_dialog.translate_text("pdf_merge"):
            self.create_pdf_merge_config()
        elif template_type == self.parent_dialog.translate_text("word_merge"):
            self.create_word_merge_config()
        elif template_type == self.parent_dialog.translate_text("pdf_split"):
            self.create_pdf_split_config()
        elif template_type == self.parent_dialog.translate_text("pdf_protection"):
            self.create_pdf_protection_config()
        elif template_type == self.parent_dialog.translate_text("Compression"):
            self.create_compression_config()
        elif template_type == self.parent_dialog.translate_text("file_optimization"):
            self.create_optimization_config()

    def create_pdf_split_config(self):
        method_label = QLabel(self.parent_dialog.translate_text("split_method"))
        self.split_method_combo = QComboBox()
        self.split_method_combo.addItems(
            [
                self.parent_dialog.translate_text("by_pages"),
                self.parent_dialog.translate_text("all_pages"),
                self.parent_dialog.translate_text("page_range"),
            ]
        )

        pages_label = QLabel(self.parent_dialog.translate_text("pages_per_file"))
        self.pages_per_file_spin = QSpinBox()
        self.pages_per_file_spin.setRange(1, 500)
        self.pages_per_file_spin.setValue(1)
        self.pages_per_file_spin.setMinimumHeight(28)

        self.config_layout.addWidget(method_label)
        self.config_layout.addWidget(self.split_method_combo)
        self.config_layout.addWidget(pages_label)
        self.config_layout.addWidget(self.pages_per_file_spin)

    def create_pdf_protection_config(self):
        level_label = QLabel(self.parent_dialog.translate_text("mode"))
        self.protection_level_combo = QComboBox()
        self.protection_level_combo.addItems(
            [
                self.parent_dialog.translate_text("basic_only_restrictions"),
                self.parent_dialog.translate_text("advanced_password_restrictions"),
            ]
        )

        permissions_group = QGroupBox(self.parent_dialog.translate_text("Permissions"))
        permissions_layout = QVBoxLayout(permissions_group)

        self.allow_printing_check = AnimatedCheckBox(self.parent_dialog.translate_text("allow_printing"))
        self.allow_printing_check.setChecked(True)

        self.allow_copying_check = AnimatedCheckBox(self.parent_dialog.translate_text("allow_text_copying"))
        self.allow_copying_check.setChecked(True)

        self.allow_modifications_check = AnimatedCheckBox(
            self.parent_dialog.translate_text("allow_modifications")
        )
        self.allow_modifications_check.setChecked(False)

        permissions_layout.addWidget(self.allow_printing_check)
        permissions_layout.addWidget(self.allow_copying_check)
        permissions_layout.addWidget(self.allow_modifications_check)

        self.config_layout.addWidget(level_label)
        self.config_layout.addWidget(self.protection_level_combo)
        self.config_layout.addWidget(permissions_group)

    def create_pdf_to_word_config(self):
        mode_label = QLabel(self.parent_dialog.translate_text("conversion_mode_2"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(
            [
                self.parent_dialog.translate_text("keep_images_and_layout"),
                self.parent_dialog.translate_text("text_only_2"),
            ]
        )
        self.config_layout.addWidget(mode_label)
        self.config_layout.addWidget(self.mode_combo)

    def create_word_to_pdf_config(self):
        mode_label = QLabel(self.parent_dialog.translate_text("conversion_mode_2"))
        self.word_mode_combo = QComboBox()
        self.word_mode_combo.addItems(
            [
                self.parent_dialog.translate_text("preserve_all_layout"),
                self.parent_dialog.translate_text("text_only"),
            ]
        )

        quality_label = QLabel(self.parent_dialog.translate_text("image_quality"))
        self.image_quality_combo = QComboBox()
        self.image_quality_combo.addItems(
            [
                self.parent_dialog.translate_text("high_300_dpi"),
                self.parent_dialog.translate_text("standard_150_dpi"),
                self.parent_dialog.translate_text("low_72_dpi"),
            ]
        )

        self.include_metadata_check = AnimatedCheckBox(self.parent_dialog.translate_text("include_metadata"))
        self.include_metadata_check.setChecked(True)

        self.compress_images_check = AnimatedCheckBox(self.parent_dialog.translate_text("compress_images"))
        self.compress_images_check.setChecked(True)

        self.config_layout.addWidget(mode_label)
        self.config_layout.addWidget(self.word_mode_combo)
        self.config_layout.addWidget(quality_label)
        self.config_layout.addWidget(self.image_quality_combo)
        self.config_layout.addWidget(self.include_metadata_check)
        self.config_layout.addWidget(self.compress_images_check)

    def create_pdf_merge_config(self):
        order_label = QLabel(self.parent_dialog.translate_text("merge_order_2"))
        self.merge_order_combo = QComboBox()
        self.merge_order_combo.addItems(
            [
                self.parent_dialog.translate_text("current_order_main_list"),
                self.parent_dialog.translate_text("alphabetical_a_to_z"),
                self.parent_dialog.translate_text("alphabetical_z_to_a"),
                self.parent_dialog.translate_text("numeric_1_to_9"),
                self.parent_dialog.translate_text("numeric_9_to_1"),
                self.parent_dialog.translate_text("date_oldest_to_newest"),
                self.parent_dialog.translate_text("date_newest_to_oldest"),
                self.parent_dialog.translate_text("manual_drag_and_drop"),
            ]
        )
        name_label = QLabel(self.parent_dialog.translate_text("filename_template"))
        self.name_template_input = QLineEdit()
        self.name_template_input.setText("fusion_{date}_{heure}")
        self.config_layout.addWidget(order_label)
        self.config_layout.addWidget(self.merge_order_combo)
        self.config_layout.addWidget(name_label)
        self.config_layout.addWidget(self.name_template_input)

    def create_optimization_config(self):
        tr = self.parent_dialog.translate_text

        self.config_layout.addWidget(QLabel(tr("optimization_mode")))
        self.optim_mode_combo = QComboBox()
        self.optim_mode_combo.addItems(
            [
                tr("compression_reduces_file_size"),
                tr("cleaning_removes_metadata_only"),
                tr("compression_cleaning_recommended"),
            ]
        )
        self.optim_mode_combo.setCurrentIndex(2)
        self.config_layout.addWidget(self.optim_mode_combo)

        self.config_layout.addWidget(QLabel(tr("compression_level_2")))
        self.optim_quality_combo = QComboBox()
        self.optim_quality_combo.addItems(
            [
                "I  —  " + tr("high_quality_moderate_gain"),
                "II  —  " + tr("balanced_recommended"),
                "III  —  " + tr("maximum_reduced_quality"),
            ]
        )
        self.optim_quality_combo.setCurrentIndex(1)
        self.config_layout.addWidget(self.optim_quality_combo)

        self.config_layout.addWidget(QLabel(tr("Options")))
        from PySide6.QtWidgets import QCheckBox as _QCB

        self.optim_metadata_check = _QCB(tr("remove_personal_metadata"))
        self.optim_metadata_check.setChecked(True)
        self.optim_images_check = _QCB(tr("recompress_embedded_images"))
        self.optim_images_check.setChecked(True)
        self.optim_backup_check = _QCB(tr("keep_a_copy_of_the_originals_2"))
        self.optim_backup_check.setChecked(True)
        self.config_layout.addWidget(self.optim_metadata_check)
        self.config_layout.addWidget(self.optim_images_check)
        self.config_layout.addWidget(self.optim_backup_check)

    def create_template(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                self.parent_dialog.translate_text("error"),
                self.parent_dialog.translate_text("please_enter_a_name_for_the_template"),
            )
            return

        template_type = self.type_combo.currentText()

        config_data = {}

        if template_type == self.parent_dialog.translate_text("pdf_to_word_conversion"):
            config_data = {"mode": self.mode_combo.currentText()}
        elif template_type == self.parent_dialog.translate_text("word_to_pdf_conversion"):
            config_data = {
                "mode": self.word_mode_combo.currentText(),
                "quality": self.image_quality_combo.currentText(),
                "include_metadata": self.include_metadata_check.isChecked(),
                "compress_images": self.compress_images_check.isChecked(),
            }
        elif template_type == self.parent_dialog.translate_text("images_to_pdf_conversion"):
            config_data = {
                "separate": self.separate_images_check.isChecked(),
            }
        elif template_type == self.parent_dialog.translate_text("pdf_merge"):
            config_data = {
                "merge_order": self.merge_order_combo.currentText(),
                "name_template": self.name_template_input.text(),
            }
        elif template_type == self.parent_dialog.translate_text("word_merge"):
            config_data = {
                "merge_order": self.word_merge_order_combo.currentText(),
                "name_template": self.word_merge_name_input.text(),
            }
        elif template_type == self.parent_dialog.translate_text("pdf_split"):
            config_data = {
                "split_method": self.split_method_combo.currentText(),
                "pages_per_file": self.pages_per_file_spin.value(),
            }
        elif template_type == self.parent_dialog.translate_text("pdf_protection"):
            config_data = {
                "mode": self.protection_level_combo.currentText(),
                "allow_printing": self.allow_printing_check.isChecked(),
                "allow_copying": self.allow_copying_check.isChecked(),
                "allow_modifications": self.allow_modifications_check.isChecked(),
            }
        elif template_type == self.parent_dialog.translate_text("Compression"):
            config_data = {
                "format": self.compression_format_combo.currentText(),
                "compression_level": self.compression_level_combo.currentText(),
                "encrypt": self.encrypt_check.isChecked(),
                "delete_originals": self.delete_originals_check.isChecked(),
                "split_archive": self.split_check.isChecked(),
                "split_size": self.split_size_spin.value() if self.split_check.isChecked() else 0,
            }
        elif template_type == self.parent_dialog.translate_text("file_optimization"):
            _mode_map = {
                self.parent_dialog.translate_text("compression_reduces_file_size"): 0,
                self.parent_dialog.translate_text("cleaning_removes_metadata_only"): 1,
                self.parent_dialog.translate_text("compression_cleaning_recommended"): 2,
            }
            config_data = {
                "optimization_type": _mode_map.get(self.optim_mode_combo.currentText(), 2),
                "quality_level": self.optim_quality_combo.currentIndex(),
                "remove_metadata": self.optim_metadata_check.isChecked(),
                "compress_images": self.optim_images_check.isChecked(),
                "keep_backup": self.optim_backup_check.isChecked(),
            }

        if self.memorize_check.isChecked() and hasattr(self.parent_app, "config"):
            self.parent_app.config["last_template_creation_params"] = {
                "memorize": True,
                "type": template_type,
            }
            try:
                self.parent_app.config_manager.save_config(self.parent_app.config)
            except Exception:
                pass
        elif hasattr(self.parent_app, "config"):
            self.parent_app.config.pop("last_template_creation_params", None)
            try:
                self.parent_app.config_manager.save_config(self.parent_app.config)
            except Exception:
                pass

        if self.set_as_default_check.isChecked():
            config_data["is_default"] = True

        self.template_manager.db_manager.save_template(name, template_type, config_data)
        self.template_manager.load_templates()

        if self.set_as_default_check.isChecked():
            new_id = None
            for tid, tpl in self.template_manager.current_templates.items():
                if tpl["name"] == name and TemplateManager.normalize_type(
                    tpl["type"]
                ) == TemplateManager.normalize_type(template_type):
                    new_id = tid
                    break
            if new_id is not None:
                self.template_manager.set_default_template(new_id, template_type)

        QMessageBox.information(
            self,
            self.parent_dialog.translate_text("success"),
            self.parent_dialog.translate_text("template_created").format(name),
        )

        _cfg = getattr(self.parent_app, "config", {})
        ach = getattr(self.parent_app, "achievement_system", None) if _cfg.get("achievements_enabled", True) else None
        if ach:
            try:
                ach.record_template_created(template_type)
            except Exception:
                pass

        self.accept()
