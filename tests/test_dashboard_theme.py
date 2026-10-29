"""Tests for dashboard palette extraction and theme refresh."""

import re

from dashboard_theme import (
    DashboardPalette,
    accent_variants,
    get_dashboard_palette,
    parse_dashboard_palette,
)

CUSTOM_DASHBOARD_QSS = """
QWidget {
    background-color: #101820;
    color: #f0f0f0;
}
QTabWidget::pane {
    background: #182430;
    border: 1px solid rgba(255, 128, 0, 0.40);
}
QTabBar::tab {
    color: #9aa7b2;
}
QTabBar::tab:selected {
    background: #ff8000;
    color: #101820;
    border-bottom: 2px solid #ff8000;
}
QGroupBox::title {
    color: #ff8000;
}
QTableWidget {
    alternate-background-color: #1e2c3a;
}
"""


class _FakeDb:
    def get_statistics(self, days=30):
        return {
            "general": (12, 5 * 1024 * 1024, 30, 2.5),
            "daily_stats": [
                ("2026-10-01", 3, 1024 * 1024),
                ("2026-10-02", 5, 2 * 1024 * 1024),
            ],
            "top_formats": [("PDF", 8), ("DOCX", 4)],
            "top_operations": [("PDF to Word", 8), ("Merge PDF", 4)],
        }

    def get_first_conversion_date(self):
        return "2026-10-01"

    def get_conversion_history(self, **kwargs):
        return []

    def export_history(self, *args, **kwargs):
        return None


def _install_custom_theme(tmp_path, monkeypatch, name, qss, dashboard=""):
    import qss_helpers
    import theme_manager

    themes_dir = tmp_path / "custom_themes"
    theme_dir = themes_dir / name
    theme_dir.mkdir(parents=True)
    metadata = f"[theme]\nname = {name}\nkind = dark\n"
    if dashboard:
        metadata += f"\n[dashboard]\n{dashboard}\n"
    (theme_dir / "metadata.ini").write_text(metadata, encoding="utf-8")
    (theme_dir / "dashboard.qss").write_text(qss, encoding="utf-8")
    monkeypatch.setattr(theme_manager, "CUSTOM_THEMES_DIR", themes_dir)
    monkeypatch.setattr(qss_helpers, "_CUSTOM_THEMES_DIR", str(themes_dir))
    return name


class TestDashboardPalette:
    def test_builtin_dark_palette(self):
        palette = get_dashboard_palette("dark", True)
        assert palette.background == "#0d1117"
        assert palette.surface == "#161b27"
        assert palette.border == "#2d3748"
        assert palette.accent == "#4dabf7"

    def test_builtin_light_palette(self):
        palette = get_dashboard_palette("light", False)
        assert palette.background == "#f0f2f7"
        assert palette.surface == "#ffffff"
        assert palette.accent == "#2b6cb0"
        assert palette.accent_text == "#2b6cb0"

    def test_parse_custom_qss(self):
        palette = parse_dashboard_palette(CUSTOM_DASHBOARD_QSS, True)
        assert palette.background == "#101820"
        assert palette.surface == "#182430"
        assert palette.text == "#f0f0f0"
        assert palette.muted == "#9aa7b2"
        assert palette.accent == "#ff8000"
        assert palette.border != palette.surface

    def test_rgba_border_is_blended_over_surface(self):
        palette = parse_dashboard_palette(CUSTOM_DASHBOARD_QSS, True)
        assert re.fullmatch(r"#[0-9a-f]{6}", palette.border)
        assert palette.border != "#182430"

    def test_custom_theme_palette(self, tmp_path, monkeypatch):
        name = _install_custom_theme(tmp_path, monkeypatch, "AmberNight", CUSTOM_DASHBOARD_QSS)
        palette = get_dashboard_palette(name, True)
        assert palette.dark is True
        assert palette.background == "#101820"
        assert palette.accent == "#ff8000"

    def test_custom_dashboard_overrides(self, tmp_path, monkeypatch):
        name = _install_custom_theme(
            tmp_path,
            monkeypatch,
            "AmberNight",
            CUSTOM_DASHBOARD_QSS,
            "accent = #0066cc\naccent_text = #003366\nmuted = #445566\n",
        )
        palette = get_dashboard_palette(name, True)
        assert palette.accent == "#0066cc"
        assert palette.accent_text == "#003366"
        assert palette.muted == "#445566"
        assert palette.on_accent == "#ffffff"

    def test_invalid_dashboard_override_is_ignored(self, tmp_path, monkeypatch):
        name = _install_custom_theme(
            tmp_path,
            monkeypatch,
            "AmberNight",
            CUSTOM_DASHBOARD_QSS,
            "accent = not-a-color\nmuted = #445566\n",
        )
        palette = get_dashboard_palette(name, True)
        assert palette.accent == "#ff8000"
        assert palette.accent_text == "#ff8000"
        assert palette.muted == "#445566"

    def test_empty_qss_uses_fallback(self):
        palette = parse_dashboard_palette("", True)
        assert palette == DashboardPalette.fallback(True)

    def test_accent_variants_are_hex_colors(self):
        variants = accent_variants("#ff8000", 4)
        assert len(variants) == 4
        assert variants[0] == "#ff8000"
        assert all(re.fullmatch(r"#[0-9a-f]{6}", color) for color in variants)


class TestDashboardThemeRefresh:
    def test_stat_card_accepts_palette(self, qapp):
        from dashboard import AnimatedStatCard

        palette = DashboardPalette.fallback(True, "#ff8000", "#ffb347")
        card = AnimatedStatCard("x", "Conversions", palette=palette)
        assert card.accent_color == "#ff8000"
        assert palette.muted in card._title_lbl.styleSheet()
        assert "#ffb347" in card._value_lbl.styleSheet()
        assert card._fill_bar.track_color == palette.surface_alt

        light = DashboardPalette.fallback(False, "#0066cc")
        card.set_palette(light)
        assert card.accent_color == "#0066cc"
        assert "#0066cc" in card._value_lbl.styleSheet()
        assert card._fill_bar.track_color == light.surface_alt
        card.deleteLater()

    def test_dashboard_refreshes_on_theme_changed(self, qapp):
        from PySide6.QtCore import Signal
        from PySide6.QtWidgets import QWidget

        from dashboard import StatisticsDashboard

        class _Parent(QWidget):
            theme_changed = Signal(str)

            def __init__(self):
                super().__init__()
                self.dark_mode = True
                self.current_theme = "dark"

        parent = _Parent()
        dashboard = StatisticsDashboard(_FakeDb(), language="en", parent=parent)
        assert dashboard._palette.dark is True
        assert dashboard.card_conversions.accent_color == dashboard._palette.accent

        parent.dark_mode = False
        parent.current_theme = "light"
        parent.theme_changed.emit("light")
        qapp.processEvents()

        assert dashboard._palette.dark is False
        assert dashboard._palette.background == "#f0f2f7"
        assert dashboard.card_conversions.accent_color == dashboard._palette.accent
        assert dashboard._chart_frame.styleSheet().find(dashboard._palette.surface) != -1

        dashboard.deleteLater()
        parent.deleteLater()
