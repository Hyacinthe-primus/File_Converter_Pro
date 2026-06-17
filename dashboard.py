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

from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QFileDialog, QMessageBox, QComboBox,
                               QLineEdit, QTabWidget, QTableWidget, QDialog,
                               QTableWidgetItem, QDateEdit, QFrame,
                               QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QSizePolicy)
from PySide6.QtCore import (QDate, QTimer, QPropertyAnimation, QEasingCurve,
                            Qt )
from PySide6.QtGui import QColor
from datetime import datetime

from qss_helpers import _load_qss
from converter import AdvancedDatabaseManager
from utils.translation_mixin import TranslationMixin


FigureCanvas = None
Figure       = None
plt          = None
mdates       = None
animation    = None

def _ensure_matplotlib():
    """Import matplotlib on first use and populate module-level references."""
    global FigureCanvas, Figure, plt, mdates, animation
    if FigureCanvas is not None:
        return
    import matplotlib
    matplotlib.use('QtAgg')
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as _FigureCanvas
    from matplotlib.figure import Figure as _Figure
    import matplotlib.pyplot as _plt
    import matplotlib.dates as _mdates
    import matplotlib.animation as _animation
    FigureCanvas = _FigureCanvas
    Figure       = _Figure
    plt          = _plt
    mdates       = _mdates
    animation    = _animation

def _get_asset_path(relative: str) -> str:
    """Resolve an asset path — dev mode AND PyInstaller (onedir + onefile)."""
    from utils import resource_path
    return resource_path(relative).replace('\\', '/')

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

    def get_conversion_history(self, limit=200, search_query=None,
                               start_date=None, end_date=None):
        return self._db.get_conversion_history(
            limit=limit, search_query=search_query,
            start_date=start_date, end_date=end_date)

    def export_history(self, filepath, format_type):
        self._db.export_history(filepath, fmt=format_type)

    def __getattr__(self, name):
        return getattr(self._db, name)


class _FillBar(QWidget):
    """A thin bar that fills left-to-right with a shimmer sweep on hover."""

    def __init__(self, color: str, dark_mode: bool, parent=None):
        super().__init__(parent)
        self.accent_color = color
        self.dark_mode = dark_mode
        self._fill = 0.0
        self._shimmer = 0.0
        self.setFixedHeight(4)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._fill_timer = QTimer(self)
        self._fill_timer.setInterval(12)
        self._fill_timer.timeout.connect(self._fill_tick)
        self._fill_target = 0.0
        self._fill_speed  = 0.055

        self._shimmer_timer = QTimer(self)
        self._shimmer_timer.setInterval(14)
        self._shimmer_timer.timeout.connect(self._shimmer_tick)

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
        from PySide6.QtGui import QPainter, QLinearGradient, QBrush, QColor
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        r = h // 2

        track_color = QColor("#2d3748" if self.dark_mode else "#e2e8f0")
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(track_color))
        p.drawRoundedRect(0, 0, w, h, r, r)

        fill_w = int(w * self._fill)
        if fill_w > 0:
            try:
                ar = int(self.accent_color[1:3], 16)
                ag = int(self.accent_color[3:5], 16)
                ab = int(self.accent_color[5:7], 16)
            except Exception:
                ar, ag, ab = 77, 171, 247

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

    def __init__(self, icon: str, title: str, color: str, dark_mode: bool = False, parent=None):
        super().__init__(parent)
        self.icon = icon
        self.title = title
        self.accent_color = color
        self.dark_mode = dark_mode

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
            f"color: {'#8b9ab0' if not self.dark_mode else '#7c8fa3'}; background: transparent;"
        )
        self._title_lbl.setWordWrap(True)
        header.addWidget(self._icon_lbl)
        header.addWidget(self._title_lbl, 1)
        layout.addLayout(header)

        self._value_lbl = QLabel("—")
        self._value_lbl.setStyleSheet(
            f"font-size: 32px; font-weight: 800; color: {self.accent_color}; "
            f"letter-spacing: -1px; background: transparent;"
        )
        layout.addWidget(self._value_lbl)

        self._fill_bar = _FillBar(self.accent_color, self.dark_mode, self)
        layout.addStretch()
        layout.addWidget(self._fill_bar)

    def _lerp_color(self, c1: str, c2: str, t: float) -> str:
        r1,g1,b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
        r2,g2,b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
        return f"#{int(r1+(r2-r1)*t):02x}{int(g1+(g2-g1)*t):02x}{int(b1+(b2-b1)*t):02x}"

    def _apply_card_style(self, t: float):
        if self.dark_mode:
            bg0, bg1 = "#1e2535", "#252f42"
            border0  = "#2d3748"
        else:
            bg0, bg1 = "#ffffff", "#f0f5ff"
            border0  = "#e8ecf0"

        bg     = self._lerp_color(bg0, bg1, t)
        border = self._lerp_color(border0, self.accent_color, t)

        self.setStyleSheet(f"""
            AnimatedStatCard {{
                background-color: {bg};
                border: 1.5px solid {border};
                border-radius: 14px;
            }}
        """)

        effect = QGraphicsDropShadowEffect(self)
        try:
            r = int(self.accent_color[1:3], 16)
            g = int(self.accent_color[3:5], 16)
            b = int(self.accent_color[5:7], 16)
            effect.setColor(QColor(r, g, b, int(20 + 110 * t)))
        except Exception:
            effect.setColor(QColor(0, 0, 0, int(20 + 60*t)))
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

    def set_dark_mode(self, dark: bool):
        self.dark_mode = dark
        self._fill_bar.dark_mode = dark
        self._title_lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 600; letter-spacing: 0.5px; "
            f"color: {'#8b9ab0' if not dark else '#7c8fa3'}; background: transparent;"
        )
        self._apply_card_style(t=0.0)


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
        self.setWindowTitle(self.translate_text("📊 Tableau de Bord & Statistiques"))
        self.setMinimumSize(1100, 700)
        self.setWindowFlag(Qt.FramelessWindowHint, False)
        self._dark = self._get_dark_mode()
        # DB selector state
        self._main_db   = db_manager
        self._adv_db    = None
        self._using_adv = False

        self.setup_ui()
        self.load_statistics()
        self._apply_global_style()

    def _get_dark_mode(self):
        return hasattr(self.parent(), 'dark_mode') and self.parent().dark_mode

    def _apply_global_style(self):
        arrow_svg = _get_asset_path("Assets/down-arrow.svg")
        qss = _load_qss("dashboard.qss", "dark" if self._dark else "light")
        self.setStyleSheet(qss.replace("{arrow_svg}", arrow_svg))

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(14)

        layout.addWidget(self._build_db_selector_bar())

        top_bar = QHBoxLayout()

        title_lbl = QLabel(self.translate_text("📊 Tableau de Bord & Statistiques"))
        title_lbl.setStyleSheet(
            "font-size: 20px; font-weight: 800; letter-spacing: -0.5px; background: transparent;"
        )
        top_bar.addWidget(title_lbl, 1)

        self.refresh_btn = QPushButton("🔄  " + self.translate_text("Rafraîchir les statistiques"))
        self.refresh_btn.clicked.connect(self._animate_refresh)
        self.refresh_btn.setStyleSheet(self._btn_style("#28a745", "#218838", "#1a6e2e"))
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setFixedHeight(36)

        top_bar.addWidget(self.refresh_btn)
        top_bar.addSpacing(8)
        layout.addLayout(top_bar)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #2d3748; background: #2d3748; max-height: 1px;")
        layout.addWidget(divider)

        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        self.overview_tab = self.create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "  " + self.translate_text("Vue d'ensemble") + "  ")

        self.charts_tab = self.create_charts_tab()
        self.tab_widget.addTab(self.charts_tab, "  " + self.translate_text("Graphiques") + "  ")

        self.details_tab = self.create_details_tab()
        self.tab_widget.addTab(self.details_tab, "  " + self.translate_text("Détails") + "  ")

        layout.addWidget(self.tab_widget, 1)

    def _btn_style(self, bg, hover, pressed):
        return f"""
            QPushButton {{
                background-color: {bg};
                color: white;
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

    def create_overview_tab(self):
        dm = self._dark
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(14)

        self.card_conversions = AnimatedStatCard("🔄", self.translate_text("Conversions totales:"), "#4dabf7", dm)
        self.card_size        = AnimatedStatCard("💾", self.translate_text("Taille totale traitée:"), "#28a745", dm)
        self.card_time_saved  = AnimatedStatCard("⏱️", self.translate_text("Temps économisé:"), "#ff6b6b", dm)
        self.card_avg_time    = AnimatedStatCard("⚡", self.translate_text("Temps moyen par conversion:"), "#ffd166", dm)

        for card in [self.card_conversions, self.card_size, self.card_time_saved, self.card_avg_time]:
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            cards_layout.addWidget(card)

        layout.addLayout(cards_layout)

        hlayout = QHBoxLayout()
        hlayout.setSpacing(14)

        def make_section(title, table_attr, headers):
            container = QFrame()
            container.setStyleSheet(f"""
                QFrame {{
                    background: {'#161b27' if dm else '#ffffff'};
                    border: 1px solid {'#2d3748' if dm else '#dde3ec'};
                    border-radius: 12px;
                }}
            """)
            vbox = QVBoxLayout(container)
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.setSpacing(0)

            header_lbl = QLabel(title)
            header_lbl.setStyleSheet(f"""
                QLabel {{
                    background: {'#1a2236' if dm else '#eef2fa'};
                    color: {'#90caf9' if dm else '#2b6cb0'};
                    font-size: 13px;
                    font-weight: 700;
                    padding: 10px 14px;
                    border-top-left-radius: 12px;
                    border-top-right-radius: 12px;
                    border-bottom: 1px solid {'#2d3748' if dm else '#dde3ec'};
                }}
            """)
            vbox.addWidget(header_lbl)

            tbl = self._make_table(headers, max_h=220)
            tbl.setStyleSheet("border: none; border-radius: 0;")
            vbox.addWidget(tbl)
            setattr(self, table_attr, tbl)
            return container

        formats_section = make_section(
            self.translate_text("📁 Formats les plus utilisés"),
            "formats_table",
            [self.translate_text("Format"), self.translate_text("Utilisations")]
        )
        operations_section = make_section(
            self.translate_text("⚡ Opérations les plus fréquentes"),
            "operations_table",
            [self.translate_text("Opération"), self.translate_text("Nombre")]
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
        t.horizontalHeader().setStretchLastSection(True)
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

        period_lbl = QLabel(self.translate_text("Période:"))
        period_lbl.setStyleSheet("font-weight: 600; font-size: 12px; background: transparent;")

        self.period_combo = QComboBox()
        self.period_combo.addItems([
            self.translate_text("7 derniers jours"),
            self.translate_text("30 derniers jours"),
            self.translate_text("3 derniers mois"),
            self.translate_text("6 derniers mois")
        ])
        self.period_combo.currentIndexChanged.connect(self._smooth_update_charts)

        chart_lbl = QLabel(self.translate_text("Type de graphique:"))
        chart_lbl.setStyleSheet("font-weight: 600; font-size: 12px; background: transparent;")

        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems([
            self.translate_text("Conversions par jour"),
            self.translate_text("Taille traitée par jour"),
            self.translate_text("Types d'opérations"),
            self.translate_text("Évolution des formats")
        ])
        self.chart_type_combo.currentIndexChanged.connect(self._smooth_update_charts)

        controls_layout.addWidget(period_lbl)
        controls_layout.addWidget(self.period_combo)
        controls_layout.addSpacing(16)
        controls_layout.addWidget(chart_lbl)
        controls_layout.addWidget(self.chart_type_combo)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        canvas_frame = QFrame()
        canvas_frame.setStyleSheet(f"""
            QFrame {{
                background: {'#161b27' if self._dark else '#ffffff'};
                border: 1px solid {'#2d3748' if self._dark else '#dde3ec'};
                border-radius: 14px;
            }}
        """)
        canvas_layout = QVBoxLayout(canvas_frame)
        canvas_layout.setContentsMargins(8, 8, 8, 8)

        self.chart_canvas = FigureCanvas(Figure(figsize=(10, 6)))
        self.chart_canvas.setStyleSheet("background: transparent; border: none;")
        canvas_layout.addWidget(self.chart_canvas)

        layout.addWidget(canvas_frame, 1)
        return widget

    def create_details_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        filters_frame = QFrame()
        filters_frame.setStyleSheet(f"""
            QFrame {{
                background: {'#161b27' if self._dark else '#f8faff'};
                border: 1px solid {'#2d3748' if self._dark else '#dde3ec'};
                border-radius: 10px;
                padding: 4px;
            }}
        """)
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setContentsMargins(12, 8, 12, 8)
        filters_layout.setSpacing(10)

        def flbl(text):
            l = QLabel(text)
            l.setStyleSheet("font-weight: 600; font-size: 12px; background: transparent;")
            return l

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

        self.start_date_edit.calendarWidget().setStyleSheet(_load_qss("history_calendar.qss"))
        self.end_date_edit.calendarWidget().setStyleSheet(_load_qss("history_calendar.qss"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translate_text("Rechercher dans l'historique..."))

        self.apply_filters_btn = QPushButton("🔍  " + self.translate_text("Appliquer les filtres"))
        self.apply_filters_btn.setStyleSheet(self._btn_style("#4361ee", "#3451d1", "#2a3fbf"))
        self.apply_filters_btn.setCursor(Qt.PointingHandCursor)
        self.apply_filters_btn.setFixedHeight(34)
        self.apply_filters_btn.clicked.connect(self.load_statistics)

        filters_layout.addWidget(flbl(self.translate_text("Du:")))
        filters_layout.addWidget(self.start_date_edit)
        filters_layout.addWidget(flbl(self.translate_text("Au:")))
        filters_layout.addWidget(self.end_date_edit)
        filters_layout.addWidget(self.search_input, 1)
        filters_layout.addWidget(self.apply_filters_btn)
        layout.addWidget(filters_frame)

        self.detailed_table = self._make_table([
            self.translate_text("Date/Heure"),
            self.translate_text("Opération"),
            self.translate_text("Source"),
            self.translate_text("Cible"),
            self.translate_text("Taille"),
            self.translate_text("Temps"),
            self.translate_text("Statut")
        ])
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

        export_csv_btn = QPushButton("📊  " + self.translate_text("Exporter en CSV"))
        export_csv_btn.setStyleSheet(self._btn_style("#4361ee", "#3451d1", "#2a3fbf"))
        export_csv_btn.setCursor(Qt.PointingHandCursor)
        export_csv_btn.setFixedHeight(34)
        export_csv_btn.clicked.connect(lambda: self.export_history('csv'))

        export_json_btn = QPushButton("📋  " + self.translate_text("Exporter en JSON"))
        export_json_btn.setStyleSheet(self._btn_style("#7c3aed", "#6d28d9", "#5b21b6"))
        export_json_btn.setCursor(Qt.PointingHandCursor)
        export_json_btn.setFixedHeight(34)
        export_json_btn.clicked.connect(lambda: self.export_history('json'))

        export_layout.addWidget(export_csv_btn)
        export_layout.addWidget(export_json_btn)
        export_layout.addStretch()
        layout.addLayout(export_layout)

        return widget

    def _on_tab_changed(self, index):
        """Fade the canvas out, redraw, fade back in when entering Charts tab.
        On the very first visit the chart is already rendered — skip the blink."""
        if index == 1:
            if not getattr(self, '_charts_tab_visited', False):
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
        self.refresh_btn.setText("⏳  " + self.translate_text("Rafraîchir les statistiques"))
        QTimer.singleShot(300, self._do_refresh)

    def _do_refresh(self):
        self.load_statistics()
        self.refresh_btn.setText("🔄  " + self.translate_text("Rafraîchir les statistiques"))
        self.refresh_btn.setEnabled(True)

    def load_statistics(self):
        days_map = {
            self.translate_text("7 derniers jours"): 7,
            self.translate_text("30 derniers jours"): 30,
            self.translate_text("3 derniers mois"): 90,
            self.translate_text("6 derniers mois"): 180
        }
        days = days_map.get(self.period_combo.currentText(), 30)
        stats = self.db_manager.get_statistics(days)

        if stats['general']:
            total_conversions = stats['general'][0] or 0
            total_size        = stats['general'][1] or 0
            total_time        = stats['general'][2] or 0
            avg_time          = stats['general'][3] or 0

            self.card_conversions.set_value(str(total_conversions), float(total_conversions))
            size_str = self.format_size(total_size)
            self.card_size.set_value(size_str, total_size / (1024 * 1024), " Mo", is_float=True)
            self.card_time_saved.set_value(f"{int(total_time)}s", float(total_time), "s")
            self.card_avg_time.set_value(f"{avg_time:.1f}s", avg_time, "s", is_float=True)

        self.formats_table.setRowCount(0)
        for i, (fmt, count) in enumerate(stats['top_formats']):
            self.formats_table.insertRow(i)
            self.formats_table.setItem(i, 0, QTableWidgetItem(fmt))
            item = QTableWidgetItem(str(count))
            item.setTextAlignment(Qt.AlignCenter)
            self.formats_table.setItem(i, 1, item)

        self.operations_table.setRowCount(0)
        for i, (op, count) in enumerate(stats['top_operations']):
            self.operations_table.insertRow(i)
            self.operations_table.setItem(i, 0, QTableWidgetItem(self.translate_operation_type(op)))
            item = QTableWidgetItem(str(count))
            item.setTextAlignment(Qt.AlignCenter)
            self.operations_table.setItem(i, 1, item)

        start_date   = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date     = self.end_date_edit.date().toString("yyyy-MM-dd")
        search_query = self.search_input.text() or None

        history = self.db_manager.get_conversion_history(
            limit=2500,
            search_query=search_query,
            start_date=start_date,
            end_date=end_date
        )

        self.detailed_table.setRowCount(0)
        for i, row in enumerate(history):
            self.detailed_table.insertRow(i)

            dt = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
            self.detailed_table.setItem(i, 0, QTableWidgetItem(dt.strftime('%d/%m/%Y %H:%M')))
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
        dm = self._get_dark_mode()

        bg_color      = '#0d1117' if dm else '#ffffff'
        plot_bg_color = '#161b27' if dm else '#f8f9fa'
        grid_color    = '#2d3748' if dm else '#e2e8f0'
        axis_color    = '#8899aa' if dm else '#64748b'
        text_color    = '#e2e8f0' if dm else '#1a202c'
        label_color   = '#cbd5e0' if dm else '#374151'

        days_map = {
            self.translate_text("7 derniers jours"): 7,
            self.translate_text("30 derniers jours"): 30,
            self.translate_text("3 derniers mois"): 90,
            self.translate_text("6 derniers mois"): 180
        }
        days  = days_map.get(self.period_combo.currentText(), 30)
        stats = self.db_manager.get_statistics(days)

        self.chart_canvas.figure.clear()
        ax = self.chart_canvas.figure.add_subplot(111)

        self.chart_canvas.figure.patch.set_facecolor(bg_color)
        ax.set_facecolor(plot_bg_color)
        for spine in ax.spines.values():
            spine.set_color(axis_color)
            spine.set_linewidth(0.8)
        ax.tick_params(colors=axis_color, length=3)
        ax.grid(True, alpha=0.25, color=grid_color, linestyle='--', linewidth=0.7)

        chart_type = self.chart_type_combo.currentText()

        if chart_type == self.translate_text("Conversions par jour") and stats['daily_stats']:
            dates       = [datetime.strptime(r[0], '%Y-%m-%d') for r in stats['daily_stats']]
            conversions = [r[1] for r in stats['daily_stats']]
            x_pos       = range(len(dates))

            bar_color  = '#640986' if dm else '#1e3a8a'
            edge_color = '#1e2535' if dm else '#ffffff'
            ax.bar(x_pos, conversions, width=0.6, color=bar_color, alpha=0.88,
                   edgecolor=edge_color, linewidth=1.2, zorder=3)

            max_conv = max(conversions) if conversions else 1
            for i, v in enumerate(conversions):
                ax.text(i, v + max_conv * 0.02, str(v),
                        ha='center', va='bottom', fontsize=9, fontweight='bold', color=text_color)

            max_labels = 15
            step = max(1, len(dates) // max_labels)
            labels = [dates[i].strftime('%d/%m/%Y') if i % step == 0 else '' for i in range(len(dates))]
            ax.set_xticks(list(x_pos))
            ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9, color=text_color)
            ax.yaxis.set_tick_params(labelcolor=text_color)

            ax.set_xlabel(self.translate_text("Date"), color=label_color, fontsize=11)
            ax.set_ylabel(self.translate_text("Nombre de conversions"), color=label_color, fontsize=11)
            ax.set_title(self.translate_text("Conversions par jour"), color=text_color,
                         fontsize=14, fontweight='bold', pad=14)
            ax.margins(x=0.01)
            self.chart_canvas.figure.tight_layout()

        elif chart_type == self.translate_text("Taille traitée par jour") and stats['daily_stats']:
            dates    = [datetime.strptime(r[0], '%Y-%m-%d') for r in stats['daily_stats']]
            sizes_mb = [r[2] / (1024 * 1024) for r in stats['daily_stats']]

            line_color = '#0891B2' if dm else '#28a745'
            ax.plot(dates, sizes_mb, marker='o', color=line_color, linewidth=2.2,
                    markersize=6, markerfacecolor=line_color, markeredgewidth=1.5,
                    markeredgecolor=bg_color, zorder=4)
            ax.fill_between(dates, sizes_mb, alpha=0.18, color=line_color)

            max_size = max(sizes_mb) if sizes_mb else 1
            min_size = min(sizes_mb) if sizes_mb else 0
            y_margin = max_size * 0.1
            ax.set_ylim(max(0, min_size - y_margin * 0.2), max_size + y_margin)

            for i, size in enumerate(sizes_mb):
                if size == 0:
                    continue
                label = f"{size / 1024:.1f} Go" if size >= 1024 else f"{size:.1f} Mo"
                ax.text(dates[i], size + y_margin * 0.25, label,
                        ha='center', va='bottom', fontsize=9, fontweight='bold', color=text_color)

            ax.set_xlabel(self.translate_text("Date"), color=label_color, fontsize=11)
            ax.set_ylabel(self.translate_text("Taille (Mo)"), color=label_color, fontsize=11)
            ax.set_title(self.translate_text("Taille de fichiers traitée par jour"), color=text_color,
                         fontsize=14, fontweight='bold', pad=14)
            ax.tick_params(axis='x', rotation=45, colors=text_color)
            ax.tick_params(axis='y', colors=text_color)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
            self.chart_canvas.figure.autofmt_xdate()
            self.chart_canvas.figure.tight_layout()

        elif chart_type == self.translate_text("Types d'opérations") and stats['top_operations']:
            operations  = [self.translate_operation_type(r[0]) for r in stats['top_operations']]
            counts      = [r[1] for r in stats['top_operations']]
            total       = sum(counts)
            percentages = [c / float(total) * 100 for c in counts]

            color_map = {
                "PDF vers Word": "#1e3a8a", "PDF to Word": "#1e3a8a",
                "Word vers PDF": "#3b82f6", "Word to PDF": "#3b82f6",
                "Images vers PDF": "#10b981", "Images to PDF": "#10b981",
                "Images vers PDF séparés": "#059669", "Images to Separate PDFs": "#059669",
                "Fusion PDF": "#8b5cf6", "Merge PDF": "#8b5cf6",
                "Fusion Word": "#2a0a74", "Merge Word": "#2a0a74",
                "Division PDF": "#f59e0b", "Split PDF": "#f59e0b",
                "Protection PDF": "#ef4444", "Protect PDF": "#ef4444",
                "Compression de fichiers": "#6366f1", "File Compression": "#6366f1",
                "Optimisation bureautique": "#06b6d4", "Office Optimization": "#06b6d4",
                "Conversion par Lot": "#ec4899", "Batch Conversion": "#ec4899",
                "Renommage par Lot": "#8b5cf6", "Batch Rename": "#8b5cf6"
            }
            colors = [color_map.get(op, plt.cm.Set3(i / max(len(operations), 1)))
                      for i, op in enumerate(operations)]

            def custom_autopct(pct):
                return f'{pct:.1f}%' if pct >= 10 else ''

            wedges, texts, autotexts = ax.pie(
                counts, labels=None, autopct=custom_autopct,
                startangle=90, colors=colors,
                wedgeprops=dict(width=0.42, edgecolor=bg_color, linewidth=1.5),
                pctdistance=0.82
            )
            for at in autotexts:
                if at.get_text():
                    at.set_color('white')
                    at.set_fontweight('bold')
                    at.set_fontsize(9)

            ax.set_title(self.translate_text("Répartition des types d'opérations"),
                         fontsize=14, fontweight='bold', pad=20, color=label_color)

            legend_labels = [
                f"{op}: {count} ({pct:.1f}%)"
                for op, count, pct in zip(operations, counts, percentages)
            ]
            legend = ax.legend(wedges, legend_labels,
                               title=self.translate_text("Types d'opérations"),
                               loc="center left", bbox_to_anchor=(1, 0, 0.5, 1),
                               fontsize=9, title_fontsize=10,
                               frameon=True, framealpha=0.92,
                               facecolor=plot_bg_color, edgecolor=grid_color,
                               labelcolor=label_color)
            plt.setp(legend.get_title(), color=text_color)

            self.chart_canvas.figure.tight_layout(rect=[0.18, 0, 0.8, 1])

            ops_label   = self.translate_text("\nOpérations")
            center_text = f"Total: {total}{ops_label}"
            ax.text(0, 0, center_text, ha='center', va='center',
                    fontsize=12, fontweight='bold', color=text_color)

            if any(p < 10 for p in percentages):
                note = self.translate_text(
                    "•Les pourcentages < 10% ne sont affichés\nque dans la légende"
                )
                ax.text(-1.9, 0, note, ha='center', va='center', fontsize=8,
                        color='#6b7280' if not dm else '#8b94a1', style='italic')

        elif chart_type == self.translate_text("Évolution des formats") and stats['top_formats']:
            formats = [r[0] for r in stats['top_formats']]
            counts  = [r[1] for r in stats['top_formats']]
            n       = len(formats)

            ax.barh(formats, counts,
                    color=[plt.cm.Pastel1(i / max(n, 1)) for i in range(n)],
                    edgecolor=grid_color, linewidth=0.8, height=0.65)
            ax.set_xlabel(self.translate_text("Nombre d'utilisations"), color=label_color, fontsize=11)
            ax.set_title(self.translate_text("Formats les plus utilisés"), color=label_color,
                         fontsize=14, fontweight='bold', pad=14)
            ax.grid(True, alpha=0.25, axis='x', color=grid_color, linestyle='--')
            ax.tick_params(axis='y', colors=label_color)
            ax.tick_params(axis='x', colors=axis_color)

            for bar, count in zip(ax.patches, counts):
                w = bar.get_width()
                ax.text(w + 0.15, bar.get_y() + bar.get_height() / 2, str(count),
                        va='center', ha='left', color=text_color, fontweight='bold', fontsize=9)

            self.chart_canvas.figure.tight_layout()

        self.chart_canvas.draw()

    def export_history(self, format_type):
        file_filter = "CSV (*.csv)" if format_type == 'csv' else "JSON (*.json)"
        filepath, _ = QFileDialog.getSaveFileName(
            self, self.translate_text("Exporter l'historique"), "", file_filter
        )
        if filepath:
            try:
                self.db_manager.export_history(filepath, format_type)
                QMessageBox.information(
                    self, self.translate_text("Succès"),
                    self.translate_text(f"Historique exporté avec succès vers {filepath}")
                )
            except Exception as e:
                QMessageBox.critical(
                    self, self.translate_text("Erreur"),
                    self.translate_text(f"Erreur lors de l'export: {str(e)}")
                )

    def _build_db_selector_bar(self) -> QWidget:
        dm = self._dark
        bar = QWidget()
        row = QHBoxLayout(bar)
        row.setContentsMargins(8, 6, 8, 6)
        row.setSpacing(8)

        btn_base   = "border-radius:7px; font-size:11px; font-weight:700; padding:5px 14px; border: none;"
        btn_active = f"background:#4dabf7; color:#fff; {btn_base}"
        btn_normal = (
            f"background:#1e2535; color:#8b9ab0; {btn_base}" if dm
            else f"background:#e2e8f0; color:#4a5568; {btn_base}"
        )

        lbl = QLabel(self.translate_text("Base de données :"))
        lbl.setStyleSheet(
            f"color:{'#8b9ab0' if dm else '#6b7280'}; font-size:11px; font-weight:600;"
            " background: transparent;"
        )
        row.addWidget(lbl)

        self._btn_main_db = QPushButton(self.translate_text("📁 Base principale"))
        self._btn_main_db.setStyleSheet(btn_active)
        self._btn_main_db.setCursor(Qt.PointingHandCursor)
        self._btn_main_db.setFixedHeight(28)
        self._btn_main_db.clicked.connect(lambda: self._switch_db("main"))
        row.addWidget(self._btn_main_db)

        self._btn_adv_db = QPushButton(self.translate_text("🔄 Conversions avancées"))
        self._btn_adv_db.setStyleSheet(btn_normal)
        self._btn_adv_db.setCursor(Qt.PointingHandCursor)
        self._btn_adv_db.setFixedHeight(28)
        self._btn_adv_db.clicked.connect(lambda: self._switch_db("advanced"))
        row.addWidget(self._btn_adv_db)

        btn_custom = QPushButton(self.translate_text("📂 Charger une DB…"))
        btn_custom.setStyleSheet(btn_normal)
        btn_custom.setCursor(Qt.PointingHandCursor)
        btn_custom.setFixedHeight(28)
        btn_custom.clicked.connect(lambda: self._switch_db("custom"))
        row.addWidget(btn_custom)

        row.addStretch()

        self._db_path_lbl = QLabel("")
        self._db_path_lbl.setStyleSheet(
            "color:#6366f1; font-size:10px; font-style:italic; background: transparent;"
        )
        row.addWidget(self._db_path_lbl)

        bar.setStyleSheet(
            f"background:{'#161b27' if dm else '#eef2fa'};"
            "border-radius:9px;"
        )
        bar.setFixedHeight(44)
        return bar

    def _switch_db(self, mode: str) -> None:
        dm = self._dark
        btn_base   = "border-radius:7px; font-size:11px; font-weight:700; padding:5px 14px; border: none;"
        btn_active = f"background:#4dabf7; color:#fff; {btn_base}"
        btn_normal = (
            f"background:#1e2535; color:#8b9ab0; {btn_base}" if dm
            else f"background:#e2e8f0; color:#4a5568; {btn_base}"
        )

        self._btn_main_db.setStyleSheet(btn_normal)
        self._btn_adv_db.setStyleSheet(btn_normal)

        if mode == "main":
            self.db_manager = self._main_db
            self._db_path_lbl.setText("")
            self._btn_main_db.setStyleSheet(btn_active)

        elif mode == "advanced":
            if self._adv_db is None:
                self._adv_db = AdvancedDatabaseManager()
            self.db_manager = _AdvDbProxy(self._adv_db)
            self._db_path_lbl.setText(f"({self._adv_db.db_path})")
            self._btn_adv_db.setStyleSheet(btn_active)

        elif mode == "custom":
            path, _ = QFileDialog.getOpenFileName(
                self,
                self.translate_text("Choisir une base de données"),
                "",
                "SQLite databases (*.db *.sqlite *.sqlite3);;All files (*)"
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
                        self.translate_text("Erreur"),
                        self.translate_text(f"Impossible d'ouvrir la base : {exc2}")
                    )
                    return

        self.load_statistics()

    def format_size(self, size_bytes):
        if size_bytes is None:
            return "0 octets"
        for unit in ['octets', 'Ko', 'Mo', 'Go', 'To']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} Po"


    def translate_operation_type(self, operation_key):
        return self._translation_manager.translate_operation_type(operation_key)

    def apply_scrollbar_style(self):
        pass