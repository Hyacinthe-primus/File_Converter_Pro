"""PanelsMixin — Left and right panel creation methods."""

from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QScrollArea, QFrame, QWidget, QCheckBox,
                               QListWidget)
from PySide6.QtCore import Qt, QSize

from widgets import DraggableListWidget


class PanelsMixin:
    """Mixin: left and right panel creation for FileConverterApp."""

    def create_left_panel(self, parent_layout):
        left_panel = QGroupBox(self.translate_text("Gestion des Fichiers"))
        left_panel.setProperty("i18n_key", "Gestion des Fichiers")
        left_panel.setObjectName("FilePanel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 18, 10, 10)
        left_layout.setSpacing(10)

        hint_lbl = QLabel(self.translate_text("Fichiers sélectionnés (glissez-déposez depuis l'explorateur):"))
        hint_lbl.setProperty("i18n_key", "Fichiers sélectionnés (glissez-déposez depuis l'explorateur):")
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

        self.add_files_btn   = _file_btn("📁 " + self.translate_text("Ajouter Fichiers"), "BtnFileAdd")
        self.add_folder_btn  = _file_btn("📂 " + self.translate_text("Ajouter Dossier"), "BtnFileFolder")
        self.remove_file_btn = _file_btn("🗑 "  + self.translate_text("Supprimer"), "BtnFileDel")
        self.clear_all_btn   = _file_btn("🧹 " + self.translate_text("Tout Effacer"), "BtnFileClear")
        self.add_files_btn.setProperty("i18n_key", "Ajouter Fichiers")
        self.add_folder_btn.setProperty("i18n_key", "Ajouter Dossier")
        self.remove_file_btn.setProperty("i18n_key", "Supprimer")
        self.clear_all_btn.setProperty("i18n_key", "Tout Effacer")

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

        conv_card, conv_lay = _card(self.translate_text("Conversion de Fichiers"))
        conv_card.setProperty("i18n_key", "Conversion de Fichiers")

        ocr_row = QHBoxLayout()
        self.ocr_checkbox = QCheckBox(self.translate_text("Utiliser OCR pour les images dans les PDF"))
        self.ocr_checkbox.setProperty("i18n_key", "Utiliser OCR pour les images dans les PDF")
        self.ocr_checkbox.setChecked(False)
        self.ocr_checkbox.setEnabled(False)
        self.ocr_checkbox.setToolTip(self.translate_text("Cette fonctionnalité est en cours de développement"))
        self.ocr_checkbox.setObjectName("OcrCheckbox")
        ocr_row.addWidget(self.ocr_checkbox)
        ocr_row.addStretch()
        conv_lay.addLayout(ocr_row)

        conv_grid = QHBoxLayout()
        conv_grid.setSpacing(7)
        self.pdf_to_word_btn   = _btn("📄→📝 " + self.translate_text("PDF → Word"), "BtnBlue")
        self.word_to_pdf_btn   = _btn("📝→📄 " + self.translate_text("Word → PDF"), "BtnBlue")
        self.image_to_pdf_btn  = _btn("🖼→📄 "  + self.translate_text("Images → PDF"), "BtnBlue")
        self.pdf_to_word_btn.setProperty("i18n_key", "PDF → Word")
        self.word_to_pdf_btn.setProperty("i18n_key", "Word → PDF")
        self.image_to_pdf_btn.setProperty("i18n_key", "Images → PDF")
        for b in [self.pdf_to_word_btn, self.word_to_pdf_btn, self.image_to_pdf_btn]:
            conv_grid.addWidget(b)
        conv_lay.addLayout(conv_grid)

        self.more_conversions_btn = QPushButton("✦  " + self.translate_text("Plus de conversions"))
        self.more_conversions_btn.setProperty("i18n_key", "Plus de conversions")
        self.more_conversions_btn.setMinimumHeight(32)
        self.more_conversions_btn.setObjectName("BtnMoreConv")
        self.more_conversions_btn.clicked.connect(self.show_advanced_conversions)
        conv_lay.addWidget(self.more_conversions_btn)
        right_layout.addWidget(conv_card)

        merge_card, merge_lay = _card(self.translate_text("Fusion de Fichiers"))
        merge_card.setProperty("i18n_key", "Fusion de Fichiers")
        merge_row = QHBoxLayout()
        merge_row.setSpacing(7)
        self.merge_pdf_btn  = _btn("🔗 " + self.translate_text("Fusionner PDF"), "BtnTeal")
        self.merge_word_btn = _btn("🔗 " + self.translate_text("Fusionner Word"), "BtnTeal")
        self.merge_pdf_btn.setProperty("i18n_key", "Fusionner PDF")
        self.merge_word_btn.setProperty("i18n_key", "Fusionner Word")
        merge_row.addWidget(self.merge_pdf_btn)
        merge_row.addWidget(self.merge_word_btn)
        merge_lay.addLayout(merge_row)
        right_layout.addWidget(merge_card)

        adv_card, adv_lay = _card(self.translate_text("Fonctionnalités Avancées"))
        adv_card.setProperty("i18n_key", "Fonctionnalités Avancées")
        adv_row = QHBoxLayout()
        adv_row.setSpacing(7)
        self.split_pdf_btn      = _btn("✂️ " + self.translate_text("Diviser PDF"), "BtnOrange")
        self.protect_pdf_btn    = _btn("🔒 " + self.translate_text("Protéger PDF"), "BtnOrange")
        self.compress_files_btn = _btn("🗜 "  + self.translate_text("Compresser Fichiers"), "BtnOrange")
        self.split_pdf_btn.setProperty("i18n_key", "Diviser PDF")
        self.protect_pdf_btn.setProperty("i18n_key", "Protéger PDF")
        self.compress_files_btn.setProperty("i18n_key", "Compresser Fichiers")
        for b in [self.split_pdf_btn, self.protect_pdf_btn, self.compress_files_btn]:
            adv_row.addWidget(b)
        adv_lay.addLayout(adv_row)
        right_layout.addWidget(adv_card)

        batch_card, batch_lay = _card(self.translate_text("Opérations par Lots"))
        batch_card.setProperty("i18n_key", "Opérations par Lots")
        batch_row = QHBoxLayout()
        batch_row.setSpacing(7)
        self.batch_convert_btn = _btn("🔄 " + self.translate_text("Conversion par Lot"), "BtnViolet")
        self.batch_rename_btn  = _btn("📝 " + self.translate_text("Renommer par Lot"), "BtnViolet")
        self.batch_convert_btn.setProperty("i18n_key", "Conversion par Lot")
        self.batch_rename_btn.setProperty("i18n_key", "Renommer par Lot")
        batch_row.addWidget(self.batch_convert_btn)
        batch_row.addWidget(self.batch_rename_btn)
        batch_lay.addLayout(batch_row)
        right_layout.addWidget(batch_card)
        right_layout.addStretch()

        self.settings_btn = QPushButton("⚙  " + self.translate_text("Paramètres"))
        self.settings_btn.setProperty("i18n_key", "Paramètres")
        self.settings_btn.setMinimumHeight(38)
        self.settings_btn.setObjectName("BtnSettings")
        right_layout.addWidget(self.settings_btn)

        self.dashboard_btn    = self.nav_dashboard_btn
        self.history_btn      = self.nav_history_btn
        self.templates_btn    = self.nav_templates_btn
        self.achievements_btn = self.nav_achievements_btn
        self._apply_achievements_btn_state()

        parent_layout.addWidget(right_panel, 0)