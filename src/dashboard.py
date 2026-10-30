"""
Statistics Dashboard

Visual analytics panel using Matplotlib for data visualization.

Features:
    - Real-time counters with animated counting effect (Total conversions, Size, Time saved)
    - Interactive Charts with smooth transitions:
        • Conversions per day (Animated Bar chart)
        • Processed size per day (Animated Line chart with fill)
        • Operation type distribution (Animated Donut chart)
        • Format evolution (Animated Horizontal bar chart)
    - Detailed history table with filtering and export
    - Hover effects on stat cards
    - Smooth tab switching transitions
    - Theme-aware design (Dark/Light mode)

Classes:
    StatisticsDashboard: Main widget containing tabs for Overview, Charts, and Details.

"""

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QDate, QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from converter import AdvancedDatabaseManager
from dashboard_theme import (
    DashboardPalette,
    accent_variants,
    contrast_text,
    get_dashboard_palette,
    shade_color,
)
from qss_helpers import _load_qss
from utils.translation_mixin import TranslationMixin

FigureCanvas = None
Figure = None
plt = None
mdates = None
animation = None


def _ensure_matplotlib():
    """Import matplotlib on first use and populate module-level references."""
    global FigureCanvas, Figure, plt, mdates, animation
    if FigureCanvas is not None:
        return
    import matplotlib

    matplotlib.use("QtAgg")
    import matplotlib.animation as _animation
    import matplotlib.dates as _mdates
    import matplotlib.pyplot as _plt
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as _FigureCanvas
    from matplotlib.figure import Figure as _Figure

    FigureCanvas = _FigureCanvas
    Figure = _Figure
    plt = _plt
    mdates = _mdates
    animation = _animation


def _get_asset_path(relative: str) -> str:
    """Resolve an asset path dev mode AND PyInstaller (onedir + onefile)."""
    from utils import resource_path

    return resource_path(relative).replace("\\", "/")


class _AdvDbProxy:
    """
    Thin proxy around AdvancedDatabaseManager.
    Routes get_statistics() → get_statistics_compat() WITHOUT monkey-patching,
    which caused infinite recursion because the monkey-patch replaced the method
    that compat itself was trying to call.
    All other methods are forwarded transparently.
    """

    def __init__(self, db: AdvancedDatabaseManager):
        self._db = db

    def get_statistics(self, days=30):
        return self._db.get_statistics_compat(days)

    def get_conversion_history(
        self, limit=200, search_query=None, start_date=None, end_date=None, operation_types=None
    ):
        return self._db.get_conversion_history(
            limit=limit,
            search_query=search_query,
            start_date=start_date,
            end_date=end_date,
            operation_types=operation_types,
        )

    def export_history(self, filepath, format_type):
        self._db.export_history(filepath, fmt=format_type)

    def __getattr__(self, name):
        return getattr(self._db, name)


class _FillBar(QWidget):
    """A thin bar that fills left-to-right with a shimmer sweep on hover."""

    def __init__(self, color: str, track_color: str = "#2d3748", parent=None):
        super().__init__(parent)
        self.accent_color = color
        self.track_color = track_color
        self._fill = 0.0
        self._shimmer = 0.0
        self.setFixedHeight(4)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._fill_timer = QTimer(self)
        self._fill_timer.setInterval(12)
        self._fill_timer.timeout.connect(self._fill_tick)
        self._fill_target = 0.0

        self._shimmer_timer = QTimer(self)
        self._shimmer_timer.setInterval(14)
        self._shimmer_timer.timeout.connect(self._shimmer_tick)

    def set_palette(self, palette: DashboardPalette):
        self.accent_color = palette.accent
        self.track_color = palette.surface_alt
        self.update()

    def animate_in(self):
        self._fill_target = 1.0
        if not self._fill_timer.isActive():
            self._fill_timer.start()
        self._shimmer = 0.0
        self._shimmer_timer.start()

    def animate_out(self):
        self._fill_target = 0.0
        self._shimmer_timer.stop()
        if not self._fill_timer.isActive():
            self._fill_timer.start()

    def _fill_tick(self):
        diff = self._fill_target - self._fill
        if abs(diff) < 0.005:
            self._fill = self._fill_target
            self._fill_timer.stop()
        else:
            self._fill += diff * 0.14
        self.update()

    def _shimmer_tick(self):
        self._shimmer = (self._shimmer + 0.022) % 1.2
        self.update()

    def paintEvent(self, event):
        from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        r = h // 2

        track_color = QColor(self.track_color)
        if not track_color.isValid():
            track_color = QColor("#2d3748")
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(track_color))
        p.drawRoundedRect(0, 0, w, h, r, r)

        fill_w = int(w * self._fill)
        if fill_w > 0:
            accent = QColor(self.accent_color)
            if not accent.isValid():
                accent = QColor("#4dabf7")
            ar, ag, ab = accent.red(), accent.green(), accent.blue()

            grad = QLinearGradient(0, 0, fill_w, 0)
            grad.setColorAt(0.0, QColor(ar, ag, ab, 180))
            grad.setColorAt(1.0, QColor(ar, ag, ab, 255))
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(0, 0, fill_w, h, r, r)

            if self._shimmer_timer.isActive():
                sx = int((self._shimmer - 0.15) * w)
                sw = int(0.18 * w)
                shimmer_grad = QLinearGradient(sx, 0, sx + sw, 0)
                shimmer_grad.setColorAt(0.0, QColor(255, 255, 255, 0))
                shimmer_grad.setColorAt(0.5, QColor(255, 255, 255, 90))
                shimmer_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
                p.setBrush(QBrush(shimmer_grad))
                p.setClipRect(0, 0, fill_w, h)
                p.drawRoundedRect(sx, 0, sw, h, r, r)
                p.setClipping(False)

        p.end()


class AnimatedStatCard(QFrame):
    """Stat card with count-up, smooth hover glow, and fill-bar animation."""

    def __init__(
        self,
        icon: str,
        title: str,
        color: str | None = None,
        dark_mode: bool = False,
        parent=None,
        palette: DashboardPalette | None = None,
    ):
        super().__init__(parent)
        self.icon = icon
        self.title = title
        self.palette = palette or DashboardPalette.fallback(dark_mode, color)
        self.accent_color = self.palette.accent
        self.dark_mode = self.palette.dark

        self._start_value = 0.0
        self._target_value = 0.0
        self._full_display = "—"
        self._suffix = ""
        self._float_value = False
        self._steps = 0
        self._step_count = 40
        self._step_delay = 14
        self._count_timer = QTimer(self)
        self._count_timer.timeout.connect(self._tick)

        self._hover_step = 0
        self._hover_total = 14
        self._hover_in = False
        self._hover_timer = QTimer(self)
        self._hover_timer.setInterval(16)
        self._hover_timer.timeout.connect(self._hover_tick)

        self.setMinimumHeight(120)
        self.setMinimumWidth(190)
        self.setCursor(Qt.PointingHandCursor)
        self._build_ui()
        self._apply_card_style(t=0.0)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 10)
        layout.setSpacing(4)

        header = QHBoxLayout()
        self._icon_lbl = QLabel(self.icon)
        self._icon_lbl.setStyleSheet("font-size: 24px; background: transparent;")
        self._title_lbl = QLabel(self.title)
        self._title_lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 600; letter-spacing: 0.5px; "
            f"color: {self.palette.muted}; background: transparent;"
        )
        self._title_lbl.setWordWrap(True)
        header.addWidget(self._icon_lbl)
        header.addWidget(self._title_lbl, 1)
        layout.addLayout(header)

        self._value_lbl = QLabel("—")
        self._value_lbl.setStyleSheet(
            f"font-size: 32px; font-weight: 800; color: {self.palette.accent_text}; "
            f"letter-spacing: -1px; background: transparent;"
        )
        layout.addWidget(self._value_lbl)

        self._fill_bar = _FillBar(self.palette.accent, self.palette.surface_alt, self)
        layout.addStretch()
        layout.addWidget(self._fill_bar)

    def _lerp_color(self, c1: str, c2: str, t: float) -> str:
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        return f"#{int(r1 + (r2 - r1) * t):02x}{int(g1 + (g2 - g1) * t):02x}{int(b1 + (b2 - b1) * t):02x}"

    def _apply_card_style(self, t: float):
        bg = self._lerp_color(self.palette.surface, self.palette.surface_alt, t)
        border = self._lerp_color(self.palette.border, self.palette.accent, t)

        self.setStyleSheet(f"""
            AnimatedStatCard {{
                background-color: {bg};
                border: 1.5px solid {border};
                border-radius: 14px;
            }}
        """)

        effect = QGraphicsDropShadowEffect(self)
        accent = QColor(self.palette.accent)
        if not accent.isValid():
            accent = QColor("#4dabf7")
        effect.setColor(QColor(accent.red(), accent.green(), accent.blue(), int(20 + 110 * t)))
        effect.setBlurRadius(int(10 + 32 * t))
        effect.setOffset(0, int(2 + 6 * t))
        self.setGraphicsEffect(effect)

    def _ease_in_out(self, t: float) -> float:
        return t * t * (3 - 2 * t)

    def enterEvent(self, event):
        self._hover_in = True
        if not self._hover_timer.isActive():
            self._hover_timer.start()
        self._fill_bar.animate_in()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover_in = False
        if not self._hover_timer.isActive():
            self._hover_timer.start()
        self._fill_bar.animate_out()
        super().leaveEvent(event)

    def _hover_tick(self):
        if self._hover_in:
            self._hover_step = min(self._hover_step + 1, self._hover_total)
        else:
            self._hover_step = max(self._hover_step - 1, 0)
        t = self._ease_in_out(self._hover_step / self._hover_total)
        self._apply_card_style(t)
        if self._hover_step in (0, self._hover_total):
            self._hover_timer.stop()

    def set_value(self, display_str: str, numeric_end: float, suffix: str = "", is_float: bool = False):
        self._suffix = suffix
        self._float_value = is_float
        self._start_value = 0.0
        self._target_value = numeric_end
        self._full_display = display_str
        self._steps = 0
        self._count_timer.start(self._step_delay)

    def _tick(self):
        self._steps += 1
        progress = self._steps / self._step_count
        eased = 1 - (1 - progress) ** 3
        current = self._start_value + (self._target_value - self._start_value) * eased
        if self._float_value:
            self._value_lbl.setText(f"{current:.1f}{self._suffix}")
        else:
            self._value_lbl.setText(f"{int(current)}{self._suffix}")
        if self._steps >= self._step_count:
            self._count_timer.stop()
            self._value_lbl.setText(self._full_display)

    def set_palette(self, palette: DashboardPalette):
        self.palette = palette
        self.accent_color = palette.accent
        self.dark_mode = palette.dark
        self._title_lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 600; letter-spacing: 0.5px; "
            f"color: {palette.muted}; background: transparent;"
        )
        self._value_lbl.setStyleSheet(
            f"font-size: 32px; font-weight: 800; color: {palette.accent_text}; "
            f"letter-spacing: -1px; background: transparent;"
        )
        self._fill_bar.set_palette(palette)
        self._apply_card_style(t=0.0)

    def set_dark_mode(self, dark: bool):
        self.set_palette(
            DashboardPalette.fallback(
                dark,
                self.palette.accent,
                self.palette.accent_text,
            )
        )


class StatisticsDashboard(TranslationMixin, QDialog):
    def __init__(self, db_manager, language="fr", parent=None, translation_manager=None):
        super().__init__(parent)
        self.setModal(False)
        _ensure_matplotlib()
        self.db_manager = db_manager
        self.language = language
        self.parent_window = parent

        if translation_manager is not None:
            self._translation_manager = translation_manager
        else:
            from translations import TranslationManager

            self._translation_manager = TranslationManager()
            self._translation_manager.set_language(language)
        self.setWindowTitle(self.translate_text("dashboard_statistics"))
        self.setMinimumSize(1100, 700)
        self.setWindowFlag(Qt.FramelessWindowHint, False)
        self._dark = self._get_dark_mode()
        self._palette = get_dashboard_palette(self._resolve_theme_name(), self._dark)
        self._section_widgets = []
        self._db_mode = "main"
        # DB selector state
        self._main_db = db_manager
        self._adv_db = None

        self.setup_ui()
        self.load_statistics()
        self._apply_global_style()
        parent = self.parent()
        if parent is not None and hasattr(parent, "theme_changed"):
            parent.theme_changed.connect(self._apply_global_style)

    def _get_dark_mode(self):
        parent = self.parent()
        return bool(getattr(parent, "dark_mode", False)) if parent else False

    def _resolve_theme_name(self) -> str:
        parent = self.parent()
        custom_theme = getattr(parent, "current_theme", None) if parent else None
        if custom_theme and custom_theme not in ("dark", "light"):
            return custom_theme
        return "dark" if self._dark else "light"

    def _apply_global_style(self, *args):
        self._dark = self._get_dark_mode()
        theme = self._resolve_theme_name()
        self._palette = get_dashboard_palette(theme, self._dark)
        arrow_svg = _get_asset_path("Assets/down-arrow.svg")
        qss = _load_qss("dashboard.qss", theme)
        self.setStyleSheet(qss.replace("{arrow_svg}", arrow_svg))
        self._refresh_theme_widgets()

    def _refresh_theme_widgets(self):
        for card in (
            getattr(self, "card_conversions", None),
            getattr(self, "card_size", None),
            getattr(self, "card_time_saved", None),
            getattr(self, "card_avg_time", None),
        ):
            if card is not None:
                card.set_palette(self._palette)
        for frame, header in self._section_widgets:
            self._style_section(frame, header)
        if hasattr(self, "_chart_frame"):
            self._style_chart_frame()
        if hasattr(self, "_filters_frame"):
            self._style_filters_frame()
        if hasattr(self, "_db_bar"):
            self._style_db_bar()
        self._style_action_buttons()
        self._style_calendars()
        if hasattr(self, "_divider"):
            self._style_divider()
        if hasattr(self, "chart_canvas") and self.chart_canvas.figure.axes:
            self.update_charts()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(14)

        layout.addWidget(self._build_db_selector_bar())

        top_bar = QHBoxLayout()

        title_lbl = QLabel(self.translate_text("dashboard_statistics"))
        title_lbl.setStyleSheet("font-size: 20px; font-weight: 800; letter-spacing: -0.5px; background: transparent;")
        top_bar.addWidget(title_lbl, 1)

        self.refresh_btn = QPushButton("🔄  " + self.translate_text("refresh_statistics"))
        self.refresh_btn.clicked.connect(self._animate_refresh)
        self.refresh_btn.setStyleSheet(self._accent_btn_style())
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setFixedHeight(36)

        top_bar.addWidget(self.refresh_btn)
        top_bar.addSpacing(8)
        layout.addLayout(top_bar)

        self._divider = QFrame()
        self._divider.setFrameShape(QFrame.HLine)
        self._style_divider()
        layout.addWidget(self._divider)

        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        self.overview_tab = self.create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "  " + self.translate_text("overview") + "  ")

        self.charts_tab = self.create_charts_tab()
        self.tab_widget.addTab(self.charts_tab, "  " + self.translate_text("charts") + "  ")

        self.details_tab = self.create_details_tab()
        self.tab_widget.addTab(self.details_tab, "  " + self.translate_text("details") + "  ")

        layout.addWidget(self.tab_widget, 1)

    def _btn_style(self, bg, hover, pressed, color=None):
        color = color or self._palette.on_accent
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {color};
                border: none;
                padding: 0 18px;
                border-radius: 9px;
                font-weight: 700;
                font-size: 12px;
                letter-spacing: 0.2px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {pressed};
            }}
        """

    def _accent_btn_style(self, accent=None):
        accent = accent or self._palette.accent
        return self._btn_style(accent, shade_color(accent, -0.14), shade_color(accent, -0.28))

    def _style_divider(self):
        self._divider.setStyleSheet(
            f"color: {self._palette.border}; background: {self._palette.border}; max-height: 1px;"
        )

    def _style_section(self, frame, header):
        palette = self._palette
        frame.setStyleSheet(f"""
            QFrame {{
                background: {palette.surface};
                border: 1px solid {palette.border};
                border-radius: 12px;
            }}
        """)
        header.setStyleSheet(f"""
            QLabel {{
                background: {palette.surface_alt};
                color: {palette.accent_text};
                font-size: 13px;
                font-weight: 700;
                padding: 10px 14px;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 1px solid {palette.border};
            }}
        """)

    def _style_chart_frame(self):
        palette = self._palette
        self._chart_frame.setStyleSheet(f"""
            QFrame {{
                background: {palette.surface};
                border: 1px solid {palette.border};
                border-radius: 14px;
            }}
        """)

    def _style_filters_frame(self):
        palette = self._palette
        self._filters_frame.setStyleSheet(f"""
            QFrame {{
                background: {palette.surface};
                border: 1px solid {palette.border};
                border-radius: 10px;
                padding: 4px;
            }}
        """)

    def _style_action_buttons(self):
        for name in ("refresh_btn", "apply_filters_btn", "_export_csv_btn", "_export_json_btn"):
            button = getattr(self, name, None)
            if button is not None:
                button.setStyleSheet(self._accent_btn_style())

    def _style_calendars(self):
        qss = _load_qss("history_calendar.qss", self._resolve_theme_name())
        for name in ("start_date_edit", "end_date_edit"):
            editor = getattr(self, name, None)
            if editor is not None:
                editor.calendarWidget().setStyleSheet(qss)

    def create_overview_tab(self):
        palette = self._palette
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(14)

        self.card_conversions = AnimatedStatCard("🔄", self.translate_text("total_conversions"), palette=palette)
        self.card_size = AnimatedStatCard("💾", self.translate_text("total_size_processed"), palette=palette)
        self.card_time_saved = AnimatedStatCard("⏱️", self.translate_text("time_saved"), palette=palette)
        self.card_avg_time = AnimatedStatCard("⚡", self.translate_text("average_conversion_time"), palette=palette)

        for card in [self.card_conversions, self.card_size, self.card_time_saved, self.card_avg_time]:
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            cards_layout.addWidget(card)

        layout.addLayout(cards_layout)

        hlayout = QHBoxLayout()
        hlayout.setSpacing(14)

        def make_section(title, table_attr, headers):
            container = QFrame()
            vbox = QVBoxLayout(container)
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.setSpacing(0)

            header_lbl = QLabel(title)
            vbox.addWidget(header_lbl)

            tbl = self._make_table(headers, max_h=220)
            tbl.setStyleSheet("border: none; border-radius: 0;")
            vbox.addWidget(tbl)
            setattr(self, table_attr, tbl)
            self._section_widgets.append((container, header_lbl))
            self._style_section(container, header_lbl)
            return container

        formats_section = make_section(
            self.translate_text("most_used_formats"),
            "formats_table",
            [self.translate_text("Format"), self.translate_text("uses")],
        )
        operations_section = make_section(
            self.translate_text("most_frequent_operations"),
            "operations_table",
            [self.translate_text("operation"), self.translate_text("count")],
        )

        hlayout.addWidget(formats_section, 1)
        hlayout.addWidget(operations_section, 1)
        layout.addLayout(hlayout)
        layout.addStretch()

        return widget

    def _make_table(self, headers, max_h=None):
        t = QTableWidget()
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t.setAlternatingRowColors(True)
        t.setShowGrid(False)
        t.verticalHeader().setVisible(False)
        t.setSelectionBehavior(QTableWidget.SelectRows)
        if max_h:
            t.setMaximumHeight(max_h)
        return t

    def create_charts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        period_lbl = QLabel(self.translate_text("period"))
        period_lbl.setStyleSheet("font-weight: 600; font-size: 12px; background: transparent;")

        self.period_combo = QComboBox()
        self.period_combo.addItems(
            [
                self.translate_text("last_7_days"),
                self.translate_text("last_30_days"),
                self.translate_text("last_3_months"),
                self.translate_text("last_6_months"),
            ]
        )
        self.period_combo.currentIndexChanged.connect(self._smooth_update_charts)

        chart_lbl = QLabel(self.translate_text("chart_type"))
        chart_lbl.setStyleSheet("font-weight: 600; font-size: 12px; background: transparent;")

        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(
            [
                self.translate_text("conversions_per_day"),
                self.translate_text("size_processed_per_day"),
                self.translate_text("operation_types"),
                self.translate_text("format_evolution"),
            ]
        )
        self.chart_type_combo.currentIndexChanged.connect(self._smooth_update_charts)

        controls_layout.addWidget(period_lbl)
        controls_layout.addWidget(self.period_combo)
        controls_layout.addSpacing(16)
        controls_layout.addWidget(chart_lbl)
        controls_layout.addWidget(self.chart_type_combo)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        self._chart_frame = QFrame()
        self._style_chart_frame()
        canvas_layout = QVBoxLayout(self._chart_frame)
        canvas_layout.setContentsMargins(8, 8, 8, 8)

        self.chart_canvas = FigureCanvas(Figure(figsize=(10, 6)))
        self.chart_canvas.setStyleSheet("background: transparent; border: none;")
        canvas_layout.addWidget(self.chart_canvas)

        layout.addWidget(self._chart_frame, 1)
        return widget

    def create_details_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        self._filters_frame = QFrame()
        self._style_filters_frame()
        filters_layout = QHBoxLayout(self._filters_frame)
        filters_layout.setContentsMargins(12, 8, 12, 8)
        filters_layout.setSpacing(10)

        def flbl(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("font-weight: 600; font-size: 12px; background: transparent;")
            return lbl

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        first_date = self._main_db.get_first_conversion_date()
        if first_date:
            min_qdate = QDate.fromString(first_date, "yyyy-MM-dd")
            self.start_date_edit.setMinimumDate(min_qdate)
            self.start_date_edit.setDate(min_qdate)
        else:
            self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.start_date_edit.setMinimumWidth(160)
        self.start_date_edit.setDisplayFormat("dd/MM/yyyy")

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setMinimumWidth(160)
        self.end_date_edit.setDisplayFormat("dd/MM/yyyy")

        self._style_calendars()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translate_text("search_in_history"))

        self.apply_filters_btn = QPushButton("🔍  " + self.translate_text("apply_filters"))
        self.apply_filters_btn.setStyleSheet(self._accent_btn_style())
        self.apply_filters_btn.setCursor(Qt.PointingHandCursor)
        self.apply_filters_btn.setFixedHeight(34)
        self.apply_filters_btn.clicked.connect(self.load_statistics)

        filters_layout.addWidget(flbl(self.translate_text("from")))
        filters_layout.addWidget(self.start_date_edit)
        filters_layout.addWidget(flbl(self.translate_text("to")))
        filters_layout.addWidget(self.end_date_edit)
        filters_layout.addWidget(self.search_input, 1)
        filters_layout.addWidget(self.apply_filters_btn)
        layout.addWidget(self._filters_frame)

        self.detailed_table = self._make_table(
            [
                self.translate_text("date_time"),
                self.translate_text("operation"),
                self.translate_text("Source"),
                self.translate_text("target"),
                self.translate_text("size"),
                self.translate_text("time"),
                self.translate_text("status"),
            ]
        )
        from PySide6.QtWidgets import QHeaderView as _HV

        _hh = self.detailed_table.horizontalHeader()
        _hh.setStretchLastSection(False)
        _hh.setSectionResizeMode(_HV.Fixed)
        for _col, _w in enumerate([155, 130, 130, 130, 90, 70, 60]):
            self.detailed_table.setColumnWidth(_col, _w)
        _hh.setSectionResizeMode(2, _HV.Stretch)
        _hh.setSectionResizeMode(3, _HV.Stretch)
        layout.addWidget(self.detailed_table, 1)

        # Export row
        export_layout = QHBoxLayout()
        export_layout.setSpacing(10)

        self._export_csv_btn = QPushButton("📊  " + self.translate_text("export_to_csv"))
        self._export_csv_btn.setStyleSheet(self._accent_btn_style())
        self._export_csv_btn.setCursor(Qt.PointingHandCursor)
        self._export_csv_btn.setFixedHeight(34)
        self._export_csv_btn.clicked.connect(lambda: self.export_history("csv"))

        self._export_json_btn = QPushButton("📋  " + self.translate_text("export_to_json"))
        self._export_json_btn.setStyleSheet(self._accent_btn_style())
        self._export_json_btn.setCursor(Qt.PointingHandCursor)
        self._export_json_btn.setFixedHeight(34)
        self._export_json_btn.clicked.connect(lambda: self.export_history("json"))

        export_layout.addWidget(self._export_csv_btn)
        export_layout.addWidget(self._export_json_btn)
        export_layout.addStretch()
        layout.addLayout(export_layout)

        return widget

    def _on_tab_changed(self, index):
        """Fade the canvas out, redraw, fade back in when entering Charts tab.
        On the very first visit the chart is already rendered."""
        if index == 1:
            if not getattr(self, "_charts_tab_visited", False):
                self._charts_tab_visited = True
            else:
                self._fade_chart(fade_in=False, callback=self._redraw_and_fadein)
        tab = self.tab_widget.widget(index)
        if tab is None:
            return

    def _fade_chart(self, fade_in: bool, callback=None):
        """Animate canvas opacity 1→0 (fade_in=False) or 0→1 (fade_in=True)."""
        effect = QGraphicsOpacityEffect(self.chart_canvas)
        self.chart_canvas.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(220)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        if fade_in:
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
        else:
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)
        if callback:
            anim.finished.connect(callback)
        self._chart_anim = anim
        anim.start()

    def _redraw_and_fadein(self):
        self.update_charts()
        self._fade_chart(fade_in=True)

    def _animate_refresh(self):
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("⏳  " + self.translate_text("refresh_statistics"))
        QTimer.singleShot(300, self._do_refresh)

    def _do_refresh(self):
        self.load_statistics()
        self.refresh_btn.setText("🔄  " + self.translate_text("refresh_statistics"))
        self.refresh_btn.setEnabled(True)

    def load_statistics(self):
        days_map = {
            self.translate_text("last_7_days"): 7,
            self.translate_text("last_30_days"): 30,
            self.translate_text("last_3_months"): 90,
            self.translate_text("last_6_months"): 180,
        }
        days = days_map.get(self.period_combo.currentText(), 30)
        stats = self.db_manager.get_statistics(days)

        if stats["general"]:
            total_conversions = stats["general"][0] or 0
            total_size = stats["general"][1] or 0
            total_time = stats["general"][2] or 0
            avg_time = stats["general"][3] or 0

            self.card_conversions.set_value(str(total_conversions), float(total_conversions))
            size_str = self.format_size(total_size)
            self.card_size.set_value(size_str, total_size / (1024 * 1024), " Mo", is_float=True)
            self.card_time_saved.set_value(f"{int(total_time)}s", float(total_time), "s")
            self.card_avg_time.set_value(f"{avg_time:.1f}s", avg_time, "s", is_float=True)

        self.formats_table.setRowCount(0)
        for i, (fmt, count) in enumerate(stats["top_formats"]):
            self.formats_table.insertRow(i)
            self.formats_table.setItem(i, 0, QTableWidgetItem(fmt))
            item = QTableWidgetItem(str(count))
            item.setTextAlignment(Qt.AlignCenter)
            self.formats_table.setItem(i, 1, item)

        self.operations_table.setRowCount(0)
        for i, (op, count) in enumerate(stats["top_operations"]):
            self.operations_table.insertRow(i)
            self.operations_table.setItem(i, 0, QTableWidgetItem(self.translate_operation_type(op)))
            item = QTableWidgetItem(str(count))
            item.setTextAlignment(Qt.AlignCenter)
            self.operations_table.setItem(i, 1, item)

        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        search_query = self.search_input.text() or None

        history = self.db_manager.get_conversion_history(
            limit=2500, search_query=search_query, start_date=start_date, end_date=end_date
        )

        self.detailed_table.setRowCount(0)
        for i, row in enumerate(history):
            self.detailed_table.insertRow(i)

            dt = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
            self.detailed_table.setItem(i, 0, QTableWidgetItem(dt.strftime("%d/%m/%Y %H:%M")))
            self.detailed_table.setItem(i, 1, QTableWidgetItem(self.translate_operation_type(row[6])))

            source_name = Path(row[2]).name if row[2] else ""
            self.detailed_table.setItem(i, 2, QTableWidgetItem(source_name))

            target_name = Path(row[4]).name if row[4] else ""
            self.detailed_table.setItem(i, 3, QTableWidgetItem(target_name))

            size_str = self.format_size(row[7]) if row[7] else "0"
            self.detailed_table.setItem(i, 4, QTableWidgetItem(size_str))

            time_str = f"{row[8]:.1f}s" if row[8] else "0s"
            self.detailed_table.setItem(i, 5, QTableWidgetItem(time_str))

            status = "✅" if row[9] else "❌"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.detailed_table.setItem(i, 6, status_item)

        self.update_charts()

    def _smooth_update_charts(self):
        """Fade out → redraw → fade in when user changes chart type/period."""
        self._fade_chart(fade_in=False, callback=self._redraw_and_fadein)

    def update_charts(self):
        palette = self._palette

        bg_color = palette.surface
        plot_bg_color = palette.surface_alt
        grid_color = palette.border
        axis_color = palette.muted
        text_color = palette.text
        label_color = palette.text
        accent = palette.accent

        days_map = {
            self.translate_text("last_7_days"): 7,
            self.translate_text("last_30_days"): 30,
            self.translate_text("last_3_months"): 90,
            self.translate_text("last_6_months"): 180,
        }
        days = days_map.get(self.period_combo.currentText(), 30)
        stats = self.db_manager.get_statistics(days)

        self.chart_canvas.figure.clear()
        ax = self.chart_canvas.figure.add_subplot(111)

        self.chart_canvas.figure.patch.set_facecolor(bg_color)
        ax.set_facecolor(plot_bg_color)
        for spine in ax.spines.values():
            spine.set_color(axis_color)
            spine.set_linewidth(0.8)
        ax.tick_params(colors=axis_color, length=3)
        ax.grid(True, alpha=0.25, color=grid_color, linestyle="--", linewidth=0.7)

        chart_type = self.chart_type_combo.currentText()

        if chart_type == self.translate_text("conversions_per_day") and stats["daily_stats"]:
            dates = [datetime.strptime(r[0], "%Y-%m-%d") for r in stats["daily_stats"]]
            conversions = [r[1] for r in stats["daily_stats"]]
            x_pos = range(len(dates))

            bar_color = accent
            edge_color = palette.surface
            ax.bar(
                x_pos,
                conversions,
                width=0.6,
                color=bar_color,
                alpha=0.88,
                edgecolor=edge_color,
                linewidth=1.2,
                zorder=3,
            )

            max_conv = max(conversions) if conversions else 1
            for i, v in enumerate(conversions):
                ax.text(
                    i,
                    v + max_conv * 0.02,
                    str(v),
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    fontweight="bold",
                    color=text_color,
                )

            max_labels = 15
            step = max(1, len(dates) // max_labels)
            labels = [dates[i].strftime("%d/%m/%Y") if i % step == 0 else "" for i in range(len(dates))]
            ax.set_xticks(list(x_pos))
            ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9, color=text_color)
            ax.yaxis.set_tick_params(labelcolor=text_color)

            ax.set_xlabel(self.translate_text("Date"), color=label_color, fontsize=11)
            ax.set_ylabel(self.translate_text("number_of_conversions"), color=label_color, fontsize=11)
            ax.set_title(
                self.translate_text("conversions_per_day"), color=text_color, fontsize=14, fontweight="bold", pad=14
            )
            ax.margins(x=0.01)
            self.chart_canvas.figure.tight_layout()

        elif chart_type == self.translate_text("size_processed_per_day") and stats["daily_stats"]:
            dates = [datetime.strptime(r[0], "%Y-%m-%d") for r in stats["daily_stats"]]
            sizes_mb = [r[2] / (1024 * 1024) for r in stats["daily_stats"]]

            line_color = accent
            ax.plot(
                dates,
                sizes_mb,
                marker="o",
                color=line_color,
                linewidth=2.2,
                markersize=6,
                markerfacecolor=line_color,
                markeredgewidth=1.5,
                markeredgecolor=bg_color,
                zorder=4,
            )
            ax.fill_between(dates, sizes_mb, alpha=0.18, color=line_color)

            max_size = max(sizes_mb) if sizes_mb else 1
            min_size = min(sizes_mb) if sizes_mb else 0
            y_margin = max_size * 0.1
            ax.set_ylim(max(0, min_size - y_margin * 0.2), max_size + y_margin)

            for i, size in enumerate(sizes_mb):
                if size == 0:
                    continue
                label = f"{size / 1024:.1f} Go" if size >= 1024 else f"{size:.1f} Mo"
                ax.text(
                    dates[i],
                    size + y_margin * 0.25,
                    label,
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    fontweight="bold",
                    color=text_color,
                )

            ax.set_xlabel(self.translate_text("Date"), color=label_color, fontsize=11)
            ax.set_ylabel(self.translate_text("size_mb"), color=label_color, fontsize=11)
            ax.set_title(
                self.translate_text("size_of_files_processed_per_day"),
                color=text_color,
                fontsize=14,
                fontweight="bold",
                pad=14,
            )
            ax.tick_params(axis="x", rotation=45, colors=text_color)
            ax.tick_params(axis="y", colors=text_color)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m-%Y"))
            self.chart_canvas.figure.autofmt_xdate()
            self.chart_canvas.figure.tight_layout()

        elif chart_type == self.translate_text("operation_types") and stats["top_operations"]:
            operations = [self.translate_operation_type(r[0]) for r in stats["top_operations"]]
            counts = [r[1] for r in stats["top_operations"]]
            total = sum(counts)
            percentages = [c / float(total) * 100 for c in counts]

            colors = accent_variants(accent, len(operations))

            def custom_autopct(pct):
                return f"{pct:.1f}%" if pct >= 10 else ""

            wedges, texts, autotexts = ax.pie(
                counts,
                labels=None,
                autopct=custom_autopct,
                startangle=90,
                colors=colors,
                wedgeprops=dict(width=0.42, edgecolor=bg_color, linewidth=1.5),
                pctdistance=0.82,
            )
            for at, color in zip(autotexts, colors):
                if at.get_text():
                    at.set_color(contrast_text(color))
                    at.set_fontweight("bold")
                    at.set_fontsize(9)

            ax.set_title(
                self.translate_text("distribution_of_operation_types"),
                fontsize=14,
                fontweight="bold",
                pad=20,
                color=label_color,
            )

            legend_labels = [f"{op}: {count} ({pct:.1f}%)" for op, count, pct in zip(operations, counts, percentages)]
            legend = ax.legend(
                wedges,
                legend_labels,
                title=self.translate_text("operation_types"),
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1),
                fontsize=9,
                title_fontsize=10,
                frameon=True,
                framealpha=0.92,
                facecolor=plot_bg_color,
                edgecolor=grid_color,
                labelcolor=label_color,
            )
            plt.setp(legend.get_title(), color=text_color)

            self.chart_canvas.figure.tight_layout(rect=[0.18, 0, 0.8, 1])

            ops_label = self.translate_text("operations")
            center_text = f"Total: {total}{ops_label}"
            ax.text(0, 0, center_text, ha="center", va="center", fontsize=12, fontweight="bold", color=text_color)

            if any(p < 10 for p in percentages):
                note = self.translate_text("percentages_10_are_only_shown_in_the_legend")
                ax.text(
                    -1.9,
                    0,
                    note,
                    ha="center",
                    va="center",
                    fontsize=8,
                    color=palette.muted,
                    style="italic",
                )

        elif chart_type == self.translate_text("format_evolution") and stats["top_formats"]:
            formats = [r[0] for r in stats["top_formats"]]
            counts = [r[1] for r in stats["top_formats"]]
            n = len(formats)

            ax.barh(
                formats,
                counts,
                color=accent_variants(accent, n),
                edgecolor=palette.border,
                linewidth=0.8,
                height=0.65,
            )
            ax.set_xlabel(self.translate_text("number_of_uses"), color=label_color, fontsize=11)
            ax.set_title(
                self.translate_text("most_used_formats_2"),
                color=label_color,
                fontsize=14,
                fontweight="bold",
                pad=14,
            )
            ax.grid(True, alpha=0.25, axis="x", color=grid_color, linestyle="--")
            ax.tick_params(axis="y", colors=label_color)
            ax.tick_params(axis="x", colors=axis_color)

            for bar, count in zip(ax.patches, counts):
                w = bar.get_width()
                ax.text(
                    w + 0.15,
                    bar.get_y() + bar.get_height() / 2,
                    str(count),
                    va="center",
                    ha="left",
                    color=text_color,
                    fontweight="bold",
                    fontsize=9,
                )

            self.chart_canvas.figure.tight_layout()

        self.chart_canvas.draw()

    def export_history(self, format_type):
        file_filter = "CSV (*.csv)" if format_type == "csv" else "JSON (*.json)"
        filepath, _ = QFileDialog.getSaveFileName(self, self.translate_text("export_history"), "", file_filter)
        if filepath:
            try:
                self.db_manager.export_history(filepath, format_type)
                QMessageBox.information(
                    self,
                    self.translate_text("success"),
                    self.translate_text(f"Historique exporté avec succès vers {filepath}"),
                )
            except Exception as e:
                QMessageBox.critical(
                    self, self.translate_text("error"), self.translate_text(f"Erreur lors de l'export: {str(e)}")
                )

    def _style_db_bar(self):
        palette = self._palette
        self._db_bar.setStyleSheet(f"background:{palette.surface_alt};border-radius:9px;")
        self._db_label.setStyleSheet(
            f"color:{palette.muted}; font-size:11px; font-weight:600; background: transparent;"
        )
        self._db_path_lbl.setStyleSheet(
            f"color:{palette.accent_text}; font-size:10px; font-style:italic; background: transparent;"
        )
        self._apply_db_button_styles()

    def _apply_db_button_styles(self):
        palette = self._palette
        btn_base = "border-radius:7px; font-size:11px; font-weight:700; padding:5px 14px; border: none;"
        btn_active = f"background:{palette.accent}; color:{palette.on_accent}; {btn_base}"
        btn_normal = f"background:{palette.surface}; color:{palette.muted}; {btn_base}"
        for name, mode in (
            ("_btn_main_db", "main"),
            ("_btn_adv_db", "advanced"),
            ("_btn_custom", "custom"),
        ):
            button = getattr(self, name, None)
            if button is not None:
                button.setStyleSheet(btn_active if self._db_mode == mode else btn_normal)

    def _build_db_selector_bar(self) -> QWidget:
        self._db_bar = QWidget()
        row = QHBoxLayout(self._db_bar)
        row.setContentsMargins(8, 6, 8, 6)
        row.setSpacing(8)

        self._db_label = QLabel(self.translate_text("database"))
        row.addWidget(self._db_label)

        self._btn_main_db = QPushButton(self.translate_text("main_database"))
        self._btn_main_db.setCursor(Qt.PointingHandCursor)
        self._btn_main_db.setFixedHeight(28)
        self._btn_main_db.clicked.connect(lambda: self._switch_db("main"))
        row.addWidget(self._btn_main_db)

        self._btn_adv_db = QPushButton(self.translate_text("advanced_conversions"))
        self._btn_adv_db.setCursor(Qt.PointingHandCursor)
        self._btn_adv_db.setFixedHeight(28)
        self._btn_adv_db.clicked.connect(lambda: self._switch_db("advanced"))
        row.addWidget(self._btn_adv_db)

        self._btn_custom = QPushButton(self.translate_text("load_a_db"))
        self._btn_custom.setCursor(Qt.PointingHandCursor)
        self._btn_custom.setFixedHeight(28)
        self._btn_custom.clicked.connect(lambda: self._switch_db("custom"))
        row.addWidget(self._btn_custom)

        row.addStretch()

        self._db_path_lbl = QLabel("")
        row.addWidget(self._db_path_lbl)

        self._style_db_bar()
        self._db_bar.setFixedHeight(44)
        return self._db_bar

    def _switch_db(self, mode: str) -> None:
        if mode == "main":
            self.db_manager = self._main_db
            self._db_mode = "main"
            self._db_path_lbl.setText("")

        elif mode == "advanced":
            if self._adv_db is None:
                self._adv_db = AdvancedDatabaseManager()
            self.db_manager = _AdvDbProxy(self._adv_db)
            self._db_mode = "advanced"
            self._db_path_lbl.setText(f"({self._adv_db.db_path})")

        elif mode == "custom":
            path, _ = QFileDialog.getOpenFileName(
                self,
                self.translate_text("choose_a_database"),
                "",
                "SQLite databases (*.db *.sqlite *.sqlite3);;All files (*)",
            )
            if not path:
                return
            try:
                custom_db = AdvancedDatabaseManager(db_path=path)
                self.db_manager = _AdvDbProxy(custom_db)
                self._db_path_lbl.setText(f"({path})")
            except Exception:
                try:
                    import sqlite3 as _sql

                    conn = _sql.connect(path)
                    conn.execute("SELECT 1 FROM conversion_history LIMIT 1")
                    conn.close()
                    from database import DatabaseManager as _DM

                    class _CustomMain(_DM):
                        def __init__(self, p):
                            self.db_path = p
                            self.init_database()

                    self.db_manager = _CustomMain(path)
                    self._db_path_lbl.setText(f"({path})")
                except Exception as exc2:
                    QMessageBox.critical(
                        self,
                        self.translate_text("error"),
                        self.translate_text(f"Impossible d'ouvrir la base : {exc2}"),
                    )
                    return
            self._db_mode = "custom"

        self._apply_db_button_styles()
        self.load_statistics()

    def format_size(self, size_bytes):
        if size_bytes is None:
            return "0 octets"
        for unit in ["octets", "Ko", "Mo", "Go", "To"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} Po"

    def translate_operation_type(self, operation_key):
        return self._translation_manager.translate_operation_type(operation_key)

    def apply_scrollbar_style(self):
        pass
