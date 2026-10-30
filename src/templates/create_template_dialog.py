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

from . import semantic_keys as sk
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

    @staticmethod
    def _add_choices(combo, choices):
        for label, value in choices:
            combo.addItem(label, value)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(self.parent_dialog.translate_text("e_g_high_quality_conversion"))

        self.type_combo = QComboBox()
        self._add_choices(
            self.type_combo,
            [
                (self.parent_dialog.translate_text("pdf_to_word_conversion"), sk.PDF_TO_WORD),
                (self.parent_dialog.translate_text("word_to_pdf_conversion"), sk.WORD_TO_PDF),
                (self.parent_dialog.translate_text("images_to_pdf_conversion"), sk.IMAGES_TO_PDF),
                (self.parent_dialog.translate_text("pdf_merge"), sk.PDF_MERGE),
                (self.parent_dialog.translate_text("word_merge"), sk.WORD_MERGE),
                (self.parent_dialog.translate_text("pdf_split"), sk.PDF_SPLIT),
                (self.parent_dialog.translate_text("pdf_protection"), sk.PDF_PROTECTION),
                (self.parent_dialog.translate_text("Compression"), sk.COMPRESSION),
                (self.parent_dialog.translate_text("file_optimization"), sk.FILE_OPTIMIZATION),
            ],
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
        self._add_choices(
            self.word_merge_order_combo,
            [
                (self.parent_dialog.translate_text("current_order_main_list"), sk.ORDER_CURRENT),
                (self.parent_dialog.translate_text("alphabetical_a_to_z"), sk.ORDER_ALPHA_AZ),
                (self.parent_dialog.translate_text("alphabetical_z_to_a"), sk.ORDER_ALPHA_ZA),
                (self.parent_dialog.translate_text("numeric_1_to_9"), sk.ORDER_NUM_ASC),
                (self.parent_dialog.translate_text("numeric_9_to_1"), sk.ORDER_NUM_DESC),
                (self.parent_dialog.translate_text("date_oldest_to_newest"), sk.ORDER_DATE_ASC),
                (self.parent_dialog.translate_text("date_newest_to_oldest"), sk.ORDER_DATE_DESC),
                (self.parent_dialog.translate_text("manual_drag_and_drop"), sk.ORDER_MANUAL),
            ],
        )
        name_label = QLabel(self.parent_dialog.translate_text("filename_template"))
        self.word_merge_name_input = QLineEdit()
        self.word_merge_name_input.setText("fusion_word_{date}_{hour}")
        self.config_layout.addWidget(order_label)
        self.config_layout.addWidget(self.word_merge_order_combo)
        self.config_layout.addWidget(name_label)
        self.config_layout.addWidget(self.word_merge_name_input)

    def create_compression_config(self):
        self.config_layout.setContentsMargins(0, 4, 0, 4)
        self.config_layout.setSpacing(4)

        format_label = QLabel(self.parent_dialog.translate_text("archive_format"))

        self.compression_format_combo = QComboBox()
        self._add_choices(
            self.compression_format_combo,
            [
                (self.parent_dialog.translate_text("ZIP"), sk.FORMAT_ZIP),
                (self.parent_dialog.translate_text("7Z"), sk.FORMAT_7Z),
                (self.parent_dialog.translate_text("tar_gz"), sk.FORMAT_TAR_GZ),
                (self.parent_dialog.translate_text("TAR"), sk.FORMAT_TAR),
            ],
        )
        self.compression_format_combo.setMinimumHeight(30)
        self.compression_format_combo.setMaximumHeight(35)

        level_label = QLabel(self.parent_dialog.translate_text("compression_level"))
        self.compression_level_combo = QComboBox()
        self._add_choices(
            self.compression_level_combo,
            [
                (self.parent_dialog.translate_text("Normal"), sk.LEVEL_NORMAL),
                (self.parent_dialog.translate_text("high_compression"), sk.LEVEL_HIGH),
                (self.parent_dialog.translate_text("maximum_compression"), sk.LEVEL_MAXIMUM),
            ],
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

        template_type = self.type_combo.currentData() or sk.normalize_type(self.type_combo.currentText())

        if template_type == sk.PDF_TO_WORD:
            self.create_pdf_to_word_config()
        elif template_type == sk.WORD_TO_PDF:
            self.create_word_to_pdf_config()
        elif template_type == sk.IMAGES_TO_PDF:
            self.create_images_to_pdf_config()
        elif template_type == sk.PDF_MERGE:
            self.create_pdf_merge_config()
        elif template_type == sk.WORD_MERGE:
            self.create_word_merge_config()
        elif template_type == sk.PDF_SPLIT:
            self.create_pdf_split_config()
        elif template_type == sk.PDF_PROTECTION:
            self.create_pdf_protection_config()
        elif template_type == sk.COMPRESSION:
            self.create_compression_config()
        elif template_type == sk.FILE_OPTIMIZATION:
            self.create_optimization_config()

    def create_pdf_split_config(self):
        method_label = QLabel(self.parent_dialog.translate_text("split_method"))
        self.split_method_combo = QComboBox()
        self._add_choices(
            self.split_method_combo,
            [
                (self.parent_dialog.translate_text("by_pages"), sk.SPLIT_BY_PAGES),
                (self.parent_dialog.translate_text("all_pages"), sk.SPLIT_ALL_PAGES),
                (self.parent_dialog.translate_text("page_range"), sk.SPLIT_PAGE_RANGE),
            ],
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
        self._add_choices(
            self.protection_level_combo,
            [
                (self.parent_dialog.translate_text("basic_only_restrictions"), sk.PROTECTION_BASIC),
                (self.parent_dialog.translate_text("advanced_password_restrictions"), sk.PROTECTION_ADVANCED),
            ],
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
        self._add_choices(
            self.mode_combo,
            [
                (self.parent_dialog.translate_text("keep_images_and_layout"), sk.MODE_WITH_IMAGES),
                (self.parent_dialog.translate_text("text_only_2"), sk.MODE_TEXT_ONLY),
            ],
        )
        self.config_layout.addWidget(mode_label)
        self.config_layout.addWidget(self.mode_combo)

    def create_word_to_pdf_config(self):
        mode_label = QLabel(self.parent_dialog.translate_text("conversion_mode_2"))
        self.word_mode_combo = QComboBox()
        self._add_choices(
            self.word_mode_combo,
            [
                (self.parent_dialog.translate_text("preserve_all_layout"), sk.MODE_PRESERVE_ALL),
                (self.parent_dialog.translate_text("text_only"), sk.MODE_TEXT_ONLY),
            ],
        )

        quality_label = QLabel(self.parent_dialog.translate_text("image_quality"))
        self.image_quality_combo = QComboBox()
        self._add_choices(
            self.image_quality_combo,
            [
                (self.parent_dialog.translate_text("high_300_dpi"), sk.QUALITY_HIGH),
                (self.parent_dialog.translate_text("standard_150_dpi"), sk.QUALITY_STANDARD),
                (self.parent_dialog.translate_text("low_72_dpi"), sk.QUALITY_LOW),
            ],
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
        self._add_choices(
            self.merge_order_combo,
            [
                (self.parent_dialog.translate_text("current_order_main_list"), sk.ORDER_CURRENT),
                (self.parent_dialog.translate_text("alphabetical_a_to_z"), sk.ORDER_ALPHA_AZ),
                (self.parent_dialog.translate_text("alphabetical_z_to_a"), sk.ORDER_ALPHA_ZA),
                (self.parent_dialog.translate_text("numeric_1_to_9"), sk.ORDER_NUM_ASC),
                (self.parent_dialog.translate_text("numeric_9_to_1"), sk.ORDER_NUM_DESC),
                (self.parent_dialog.translate_text("date_oldest_to_newest"), sk.ORDER_DATE_ASC),
                (self.parent_dialog.translate_text("date_newest_to_oldest"), sk.ORDER_DATE_DESC),
                (self.parent_dialog.translate_text("manual_drag_and_drop"), sk.ORDER_MANUAL),
            ],
        )
        name_label = QLabel(self.parent_dialog.translate_text("filename_template"))
        self.name_template_input = QLineEdit()
        self.name_template_input.setText("fusion_{date}_{hour}")
        self.config_layout.addWidget(order_label)
        self.config_layout.addWidget(self.merge_order_combo)
        self.config_layout.addWidget(name_label)
        self.config_layout.addWidget(self.name_template_input)

    def create_optimization_config(self):
        tr = self.parent_dialog.translate_text

        self.config_layout.addWidget(QLabel(tr("optimization_mode")))
        self.optim_mode_combo = QComboBox()
        self._add_choices(
            self.optim_mode_combo,
            [
                (tr("compression_reduces_file_size"), sk.OPTIMIZATION_COMPRESSION),
                (tr("cleaning_removes_metadata_only"), sk.OPTIMIZATION_CLEANING),
                (tr("compression_cleaning_recommended"), sk.OPTIMIZATION_BOTH),
            ],
        )
        self.optim_mode_combo.setCurrentIndex(2)
        self.config_layout.addWidget(self.optim_mode_combo)

        self.config_layout.addWidget(QLabel(tr("compression_level_2")))
        self.optim_quality_combo = QComboBox()
        self._add_choices(
            self.optim_quality_combo,
            [
                ("I  -  " + tr("high_quality_moderate_gain"), 0),
                ("II  -  " + tr("balanced_recommended"), 1),
                ("III  -  " + tr("maximum_reduced_quality"), 2),
            ],
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

        template_type = self.type_combo.currentData() or sk.normalize_type(self.type_combo.currentText())

        config_data = {}

        if template_type == sk.PDF_TO_WORD:
            config_data = {"mode": self.mode_combo.currentData()}
        elif template_type == sk.WORD_TO_PDF:
            config_data = {
                "mode": self.word_mode_combo.currentData(),
                "quality": self.image_quality_combo.currentData(),
                "include_metadata": self.include_metadata_check.isChecked(),
                "compress_images": self.compress_images_check.isChecked(),
            }
        elif template_type == sk.IMAGES_TO_PDF:
            config_data = {
                "separate": self.separate_images_check.isChecked(),
            }
        elif template_type == sk.PDF_MERGE:
            config_data = {
                "merge_order": self.merge_order_combo.currentData(),
                "name_template": self.name_template_input.text(),
            }
        elif template_type == sk.WORD_MERGE:
            config_data = {
                "merge_order": self.word_merge_order_combo.currentData(),
                "name_template": self.word_merge_name_input.text(),
            }
        elif template_type == sk.PDF_SPLIT:
            config_data = {
                "split_method": self.split_method_combo.currentData(),
                "pages_per_file": self.pages_per_file_spin.value(),
            }
        elif template_type == sk.PDF_PROTECTION:
            config_data = {
                "protection_level": self.protection_level_combo.currentData(),
                "allow_printing": self.allow_printing_check.isChecked(),
                "allow_copying": self.allow_copying_check.isChecked(),
                "allow_modifications": self.allow_modifications_check.isChecked(),
            }
        elif template_type == sk.COMPRESSION:
            config_data = {
                "format": self.compression_format_combo.currentData(),
                "compression_level": self.compression_level_combo.currentData(),
                "encrypt": self.encrypt_check.isChecked(),
                "delete_originals": self.delete_originals_check.isChecked(),
                "split_archive": self.split_check.isChecked(),
                "split_size": self.split_size_spin.value() if self.split_check.isChecked() else 0,
            }
        elif template_type == sk.FILE_OPTIMIZATION:
            config_data = {
                "optimization_type": self.optim_mode_combo.currentData(),
                "quality_level": self.optim_quality_combo.currentData(),
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

        self.template_manager.db_manager.save_template(
            name,
            self.template_manager.normalize_type(template_type),
            config_data,
        )
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
