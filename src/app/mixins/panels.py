"""PanelsMixin - Left and right panel creation methods."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from widgets import AnimatedCheckBox, DraggableListWidget


class PanelsMixin:
    """Mixin: left and right panel creation for FileConverterApp."""

    def create_left_panel(self, parent_layout):
        left_panel = QGroupBox(self.translate_text("file_management"))
        left_panel.setProperty("i18n_key", "file_management")
        left_panel.setObjectName("FilePanel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 18, 10, 10)
        left_layout.setSpacing(10)

        hint_lbl = QLabel(self.translate_text("files_selected_drag_and_drop_from_file_explorer"))
        hint_lbl.setProperty("i18n_key", "files_selected_drag_and_drop_from_file_explorer")
        hint_lbl.setObjectName("HintLabel")
        hint_lbl.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(hint_lbl)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)
        scroll_area.setWidget(scroll_widget)

        self.files_list_widget = DraggableListWidget(translation_manager=self.translation_manager)
        self.files_list_widget.setMinimumHeight(200)
        self.files_list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.files_list_widget.setIconSize(QSize(18, 18))
        scroll_layout.addWidget(self.files_list_widget)

        left_layout.addWidget(scroll_area, 1)

        def _file_btn(label, name):
            b = QPushButton(label)
            b.setMinimumHeight(34)
            b.setObjectName(name)
            return b

        self.add_files_btn = _file_btn("➕📄 " + self.translate_text("add_files"), "BtnFileAdd")
        self.add_folder_btn = _file_btn("➕📂 " + self.translate_text("add_folder"), "BtnFileFolder")
        self.remove_file_btn = _file_btn("❌ " + self.translate_text("remove"), "BtnFileDel")
        self.clear_all_btn = _file_btn("🧹 " + self.translate_text("clear_all"), "BtnFileClear")
        self.add_files_btn.setProperty("i18n_key", "add_files")
        self.add_folder_btn.setProperty("i18n_key", "add_folder")
        self.remove_file_btn.setProperty("i18n_key", "remove")
        self.clear_all_btn.setProperty("i18n_key", "clear_all")

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        for b in [self.add_files_btn, self.add_folder_btn, self.remove_file_btn, self.clear_all_btn]:
            btn_row.addWidget(b)
        left_layout.addLayout(btn_row)

        parent_layout.addWidget(left_panel, 1)

    def create_right_panel(self, parent_layout):
        right_panel = QWidget()
        right_panel.setMinimumWidth(320)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(0, 0, 0, 0)

        def _card(title):
            g = QGroupBox(title.upper())
            g.setObjectName("ActionCard")
            lay = QVBoxLayout(g)
            lay.setContentsMargins(8, 16, 8, 10)
            lay.setSpacing(8)
            return g, lay

        def _btn(label, name, h=36):
            b = QPushButton(label)
            b.setMinimumHeight(h)
            b.setObjectName(name)
            return b

        conv_card, conv_lay = _card(self.translate_text("file_conversion"))
        conv_card.setProperty("i18n_key", "file_conversion")
        conv_lay.setContentsMargins(8, 2, 8, 10)

        ocr_row = QHBoxLayout()
        self.ocr_checkbox = AnimatedCheckBox(self.translate_text("use_ocr_for_images_in_pdfs"))
        self.ocr_checkbox.setWordWrap(True)
        self.ocr_checkbox.setProperty("i18n_key", "use_ocr_for_images_in_pdfs")
        self.ocr_checkbox.setChecked(bool(self.config.get("ocr_enabled", False)))
        self.ocr_checkbox.setToolTip(self.translate_text("generates_a_selectable_text_layer_in_the_pdf"))
        self.ocr_checkbox.setProperty("i18n_tip", "generates_a_selectable_text_layer_in_the_pdf")
        self.ocr_checkbox.setObjectName("OcrCheckbox")
        self.ocr_checkbox.stateChanged.connect(self._on_ocr_checkbox_toggled)
        ocr_row.addWidget(self.ocr_checkbox)
        ocr_row.addStretch()
        conv_lay.addLayout(ocr_row)

        conv_grid = QHBoxLayout()
        conv_grid.setSpacing(7)
        self.pdf_to_word_btn = _btn("📄→📝 " + self.translate_text("pdf_to_word_2"), "BtnBlue")
        self.word_to_pdf_btn = _btn("📝→📄 " + self.translate_text("word_to_pdf_2"), "BtnBlue")
        self.image_to_pdf_btn = _btn("🖼️​→📄 " + self.translate_text("images_to_pdf_3"), "BtnBlue")
        self.pdf_to_word_btn.setProperty("i18n_key", "pdf_to_word_2")
        self.word_to_pdf_btn.setProperty("i18n_key", "word_to_pdf_2")
        self.image_to_pdf_btn.setProperty("i18n_key", "images_to_pdf_3")
        for b in [self.pdf_to_word_btn, self.word_to_pdf_btn, self.image_to_pdf_btn]:
            conv_grid.addWidget(b, 1)
        conv_lay.addLayout(conv_grid)

        self.more_conversions_btn = QPushButton("➕​  " + self.translate_text("more_conversions"))
        self.more_conversions_btn.setProperty("i18n_key", "more_conversions")
        self.more_conversions_btn.setMinimumHeight(32)
        self.more_conversions_btn.setObjectName("BtnMoreConv")
        self.more_conversions_btn.clicked.connect(self.show_advanced_conversions)
        conv_lay.addWidget(self.more_conversions_btn)
        right_layout.addWidget(conv_card)

        merge_card, merge_lay = _card(self.translate_text("file_merge"))
        merge_card.setProperty("i18n_key", "file_merge")
        merge_row = QHBoxLayout()
        merge_row.setSpacing(7)
        self.merge_pdf_btn = _btn("🔗 " + self.translate_text("merge_pdf"), "BtnTeal")
        self.merge_word_btn = _btn("🔗 " + self.translate_text("merge_word"), "BtnTeal")
        self.merge_pdf_btn.setProperty("i18n_key", "merge_pdf")
        self.merge_word_btn.setProperty("i18n_key", "merge_word")
        merge_row.addWidget(self.merge_pdf_btn, 1)
        merge_row.addWidget(self.merge_word_btn, 1)
        merge_lay.addLayout(merge_row)
        right_layout.addWidget(merge_card)

        adv_card, adv_lay = _card(self.translate_text("advanced_features"))
        adv_card.setProperty("i18n_key", "advanced_features")
        adv_row = QHBoxLayout()
        adv_row.setSpacing(7)
        self.split_pdf_btn = _btn("✂️ " + self.translate_text("split_pdf"), "BtnOrange")
        self.protect_pdf_btn = _btn("🔒 " + self.translate_text("protect_pdf"), "BtnOrange")
        self.compress_files_btn = _btn("📦 " + self.translate_text("compress_files"), "BtnOrange")
        self.split_pdf_btn.setProperty("i18n_key", "split_pdf")
        self.protect_pdf_btn.setProperty("i18n_key", "protect_pdf")
        self.compress_files_btn.setProperty("i18n_key", "compress_files")
        for b in [self.split_pdf_btn, self.protect_pdf_btn, self.compress_files_btn]:
            adv_row.addWidget(b, 1)
        adv_lay.addLayout(adv_row)
        right_layout.addWidget(adv_card)

        batch_card, batch_lay = _card(self.translate_text("batch_operations"))
        batch_card.setProperty("i18n_key", "batch_operations")
        batch_row = QHBoxLayout()
        batch_row.setSpacing(7)
        self.batch_convert_btn = _btn("🔁 " + self.translate_text("batch_conversion"), "BtnViolet")
        self.batch_rename_btn = _btn("✏️ " + self.translate_text("batch_rename"), "BtnViolet")
        self.batch_convert_btn.setProperty("i18n_key", "batch_conversion")
        self.batch_rename_btn.setProperty("i18n_key", "batch_rename")
        batch_row.addWidget(self.batch_convert_btn, 1)
        batch_row.addWidget(self.batch_rename_btn, 1)
        batch_lay.addLayout(batch_row)
        right_layout.addWidget(batch_card)
        right_layout.addStretch()

        self.settings_btn = QPushButton("⚙  " + self.translate_text("settings"))
        self.settings_btn.setProperty("i18n_key", "settings")
        self.settings_btn.setMinimumHeight(38)
        self.settings_btn.setObjectName("BtnSettings")
        right_layout.addWidget(self.settings_btn)

        self.dashboard_btn = self.nav_dashboard_btn
        self.history_btn = self.nav_history_btn
        self.templates_btn = self.nav_templates_btn
        self.achievements_btn = self.nav_achievements_btn
        self._apply_achievements_btn_state()

        parent_layout.addWidget(right_panel, 0)

    def _on_ocr_checkbox_toggled(self, state: int) -> None:
        """Persist the per-conversion OCR checkbox state to the config."""
        if not hasattr(self, "config"):
            return
        self.config["ocr_enabled"] = bool(state)
