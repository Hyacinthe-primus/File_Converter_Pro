"""ConversionOptionsDialog — Card-based grid for choosing conversion type."""

import os

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton, QVBoxLayout


class ConversionOptionsDialog(QDialog):
    """
    Dialog box allowing the user to choose the type of conversion
    to launch via a keyboard shortcut or a generic button.
    Premium redesign: card-based grid, large icons, dark/light theme-aware.
    """

    conversion_chosen = Signal(str)

    _CARDS = [
        ("PDF → Word/Docx", "launch_pdf_to_word_conversion", "pdf_word.png", "#4dabf7", "#1971c2"),
        ("Word/Docx → PDF", "launch_word_to_pdf_conversion", "word_pdf.png", "#69db7c", "#2f9e44"),
        ("Images → PDF", "launch_image_to_pdf_conversion", "image_pdf.png", "#ffa94d", "#e67700"),
        ("Fusionner PDF", "launch_merge_pdf", "merge_pdf.png", "#f783ac", "#c2255c"),
        ("Fusionner Word", "launch_merge_word", "merge_word.png", "#da77f2", "#9c36b5"),
        ("Optimiser les fichiers", "launch_optimization", "compress_files.png", "#63e6be", "#0ca678"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dark = getattr(parent, "dark_mode", True)
        self.setWindowTitle(parent.translate_text("Lancer la Conversion"))
        self.setFixedWidth(560)

        flags = Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowCloseButtonHint
        self.setWindowFlags(flags | Qt.CustomizeWindowHint)

        if self._dark:
            dlg_bg = "#0d1117"
            dlg_border = "#30363d"
            title_col = "#e6edf3"
            sub_col = "#8b949e"
            cancel_bg = "#21262d"
            cancel_fg = "#c9d1d9"
            cancel_brd = "#30363d"
            cancel_hov = "#30363d"
        else:
            dlg_bg = "#f5f5f5"
            dlg_border = "#d0d7de"
            title_col = "#1f2328"
            sub_col = "#656d76"
            cancel_bg = "#f6f8fa"
            cancel_fg = "#24292f"
            cancel_brd = "#d0d7de"
            cancel_hov = "#e9ecef"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {dlg_bg};
                border: 1px solid {dlg_border};
                border-radius: 12px;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(0)

        title = QLabel(parent.translate_text("Lancer la Conversion"))
        title.setStyleSheet(f"font-size: 17px; font-weight: 700; color: {title_col}; background: transparent;")
        root.addWidget(title)

        sub = QLabel(parent.translate_text("Sélectionnez la catégorie de conversion à lancer :"))
        sub.setStyleSheet(f"font-size: 12px; color: {sub_col}; background: transparent; margin-bottom: 14px;")
        root.addWidget(sub)
        root.addSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        row, col = 0, 0
        for label_key, method_name, icon_file, accent_dark, accent_light in self._CARDS:
            label = parent.translate_text(label_key)
            accent = accent_dark if self._dark else accent_light
            grid.addWidget(self._make_card(label, icon_file, method_name, accent), row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

        root.addLayout(grid)
        root.addSpacing(16)

        cancel = QPushButton(parent.translate_text("Annuler"))
        cancel.setFixedHeight(36)
        cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: {cancel_bg};
                color: {cancel_fg};
                border: 1px solid {cancel_brd};
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover  {{ background-color: {cancel_hov}; }}
            QPushButton:pressed {{ opacity: 0.7; }}
        """)
        cancel.clicked.connect(self.reject)
        root.addWidget(cancel)

    def _make_card(self, label: str, icon_file: str, method_name: str, accent: str) -> QPushButton:
        """Build one conversion card button."""
        if self._dark:
            card_bg = "#161b22"
            card_brd = "#30363d"
            card_fg = "#e6edf3"
            hov_bg = "#1c2333"
        else:
            card_bg = "#ffffff"
            card_brd = "#d0d7de"
            card_fg = "#1f2328"
            hov_bg = "#f0f6fc"

        btn = QPushButton()
        btn.setObjectName(method_name)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(72)

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {card_bg};
                color: {card_fg};
                border: 1.5px solid {card_brd};
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
                text-align: left;
                padding-left: 14px;
            }}
            QPushButton:hover {{
                background-color: {hov_bg};
                border-color: {accent};
                color: {accent};
            }}
            QPushButton:pressed {{
                background-color: {hov_bg};
                border-color: {accent};
            }}
        """)

        icon_path = self.parent().get_resource_path(os.path.join("icons", icon_file))
        if os.path.exists(icon_path):
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(36, 36))

        btn.setText(("  " if os.path.exists(icon_path) else "") + label)

        btn.clicked.connect(lambda _=False, m=method_name: (self.conversion_chosen.emit(m), self.accept()))

        return btn
