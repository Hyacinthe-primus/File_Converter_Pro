"""Quick Launch dialog for finding and starting a conversion."""

import os

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QKeyEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QVBoxLayout,
)

from qss_helpers import _load_qss


class _QuickLaunchSearch(QLineEdit):
    """Search field that moves focus to the result list with the arrow keys."""

    navigation_requested = Signal(int)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.modifiers() == Qt.KeyboardModifier.NoModifier and event.key() in (
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
        ):
            self.navigation_requested.emit(-1 if event.key() == Qt.Key.Key_Up else 1)
            event.accept()
            return
        super().keyPressEvent(event)


class ConversionOptionsDialog(QDialog):
    """Searchable, keyboard-first picker for the available conversion actions."""

    conversion_chosen = Signal(str)

    _ACTIONS = [
        ("pdf_to_word_2", "launch_pdf_to_word_conversion", "pdf_word.png"),
        ("word_to_pdf_2", "launch_word_to_pdf_conversion", "word_pdf.png"),
        ("images_to_pdf_3", "launch_image_to_pdf_conversion", "image_pdf.png"),
        ("merge_pdf", "launch_merge_pdf", "merge_pdf.png"),
        ("merge_word", "launch_merge_word", "merge_word.png"),
        ("optimize_files", "launch_optimization", "compress_files.png"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dark = getattr(parent, "dark_mode", True)
        self._theme_name = getattr(parent, "current_theme", None) or ("dark" if self._dark else "light")
        self.setObjectName("QuickLaunchDialog")
        self.setWindowTitle(parent.translate_text("quick_launch"))
        self.setFixedWidth(460)

        flags = Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowCloseButtonHint
        self.setWindowFlags(flags | Qt.CustomizeWindowHint)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 14)
        root.setSpacing(8)

        title = QLabel(parent.translate_text("quick_launch"))
        title.setObjectName("QuickLaunchTitle")
        root.addWidget(title)

        self.search_input = _QuickLaunchSearch()
        self.search_input.setObjectName("QuickLaunchSearch")
        self.search_input.setPlaceholderText(parent.translate_text("search_2"))
        self.search_input.setClearButtonEnabled(True)
        self.search_input.navigation_requested.connect(self._navigate_results)
        self.search_input.textChanged.connect(self._filter_results)
        self.search_input.returnPressed.connect(self._activate_current)
        root.addWidget(self.search_input)

        self.results = QListWidget()
        self.results.setObjectName("QuickLaunchResults")
        self.results.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.results.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.results.setUniformItemSizes(True)
        self.results.setIconSize(QSize(20, 20))
        self.results.setMinimumHeight(210)
        self.results.itemActivated.connect(self._activate_item)

        icon_dir = os.path.join("Assets", "icons")
        for label_key, method_name, icon_file in self._ACTIONS:
            label = parent.translate_text(label_key)
            icon_path = parent.get_resource_path(os.path.join(icon_dir, icon_file))
            item = QListWidgetItem(QIcon(icon_path) if os.path.exists(icon_path) else QIcon(), label)
            item.setData(Qt.ItemDataRole.UserRole, method_name)
            self.results.addItem(item)

        self.empty_label = QLabel(parent.translate_text("no_matching_conversions"))
        self.empty_label.setObjectName("QuickLaunchEmpty")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.result_stack = QStackedWidget()
        self.result_stack.setObjectName("QuickLaunchResultStack")
        self.result_stack.addWidget(self.results)
        self.result_stack.addWidget(self.empty_label)
        root.addWidget(self.result_stack, 1)

        hint = QLabel(parent.translate_text("quick_launch_keyboard_hint"))
        hint.setObjectName("QuickLaunchHint")
        root.addWidget(hint)

        self._filter_results("")
        self.search_input.setFocus(Qt.OtherFocusReason)
        self._apply_theme(self._theme_name)

        theme_changed = getattr(parent, "theme_changed", None)
        if theme_changed is not None and hasattr(theme_changed, "connect"):
            theme_changed.connect(self._apply_theme)

    def _apply_theme(self, theme_name: str | None = None) -> None:
        if theme_name:
            self._theme_name = theme_name
        self.setStyleSheet(_load_qss("quick_launch.qss", self._theme_name))

    def _filter_results(self, query: str) -> None:
        normalized_query = query.strip().casefold()
        visible_rows = []
        for row in range(self.results.count()):
            item = self.results.item(row)
            matches = normalized_query in item.text().casefold()
            item.setHidden(not matches)
            if matches:
                visible_rows.append(row)

        if visible_rows:
            self.results.setCurrentRow(visible_rows[0])
            self.result_stack.setCurrentWidget(self.results)
        else:
            self.results.setCurrentRow(-1)
            self.result_stack.setCurrentWidget(self.empty_label)

    def _navigate_results(self, direction: int) -> None:
        visible_rows = [row for row in range(self.results.count()) if not self.results.item(row).isHidden()]
        if not visible_rows:
            return

        current_row = self.results.currentRow()
        if self.search_input.hasFocus() or current_row not in visible_rows:
            target_row = visible_rows[0] if direction > 0 else visible_rows[-1]
        else:
            position = visible_rows.index(current_row)
            target_position = max(0, min(position + direction, len(visible_rows) - 1))
            target_row = visible_rows[target_position]

        self.results.setCurrentRow(target_row)
        self.results.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def _activate_current(self) -> None:
        self._activate_item(self.results.currentItem())

    def _activate_item(self, item: QListWidgetItem | None = None) -> None:
        if item is None or item.isHidden():
            item = self.results.currentItem()
        if item is None or item.isHidden():
            return

        method_name = item.data(Qt.ItemDataRole.UserRole)
        if method_name:
            self.conversion_chosen.emit(method_name)
            self.accept()
