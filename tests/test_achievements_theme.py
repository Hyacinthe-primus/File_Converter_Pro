"""Tests for achievements palette extraction and optional theme loading."""

import textwrap

import pytest

from achievements.theme import (
    DS,
    AchievementsPalette,
    get_achievements_palette,
    load_achievements_qss,
    parse_achievements_palette,
)

CUSTOM_ACHIEVEMENTS_QSS = """
AchievementsPalette {
    background: #101820;
    surface: #182430;
    surface_alt: #1e2c3a;
    input: #223344;
    border: #334455;
    border_light: #445566;
    text: #f0f0f0;
    text_secondary: #9aa7b2;
    muted: #778899;
    gold: #ff8000;
    gold_bright: #ffaa00;
    gold_dim: #663300;
    green: #00cc66;
    red: #ff3355;
    red_dim: #331111;
    blue: #3399ff;
    purple: #aa66ff;
    secret_bg: #120008;
    secret_text: #cc0033;
    progress_text: #ffffff;
    font_family: 'Georgia';
    ring_progress: #abcdef;
    progress_fill: #111213;
    rank_initiate: #123456;
    tier_bronze: #123456;
    tier_bronze_glow: #654321;
    tier_bronze_hover: #abcdef;
    category_progression: #112233;
}
"""


def _install_custom_theme(tmp_path, monkeypatch, name, kind, achievements_qss=None):
    import qss_helpers
    import theme_manager

    themes_dir = tmp_path / "custom_themes"
    theme_dir = themes_dir / name
    theme_dir.mkdir(parents=True)
    metadata = f"[theme]\nname = {name}\nkind = {kind}\n"
    (theme_dir / "metadata.ini").write_text(metadata, encoding="utf-8")
    if achievements_qss is not None:
        (theme_dir / "achievements.qss").write_text(achievements_qss, encoding="utf-8")
    monkeypatch.setattr(theme_manager, "CUSTOM_THEMES_DIR", themes_dir)
    monkeypatch.setattr(qss_helpers, "_CUSTOM_THEMES_DIR", str(themes_dir))
    return name


class TestAchievementsPalette:
    def test_builtin_dark_palette(self):
        palette = get_achievements_palette("dark", True)
        assert palette.background == "#0d1117"
        assert palette.surface == "#161b22"
        assert palette.gold == "#d4af37"
        assert palette.ring_progress == "#d4af37"
        assert palette.font_family == "Segoe UI"
        assert palette.dark is True

    def test_builtin_light_palette(self):
        palette = get_achievements_palette("light", False)
        assert palette.background == "#f5f3ee"
        assert palette.surface == "#ffffff"
        assert palette.gold == "#8a6508"
        assert palette.dark is False

    def test_parse_custom_palette(self):
        palette = parse_achievements_palette(CUSTOM_ACHIEVEMENTS_QSS, True)
        assert palette.background == "#101820"
        assert palette.surface == "#182430"
        assert palette.gold == "#ff8000"
        assert palette.text == "#f0f0f0"
        assert palette.font_family == "Georgia"
        assert palette.ring_progress == "#abcdef"
        assert palette.progress_fill == "#111213"
        assert palette.ranks["initiate"] == "#123456"
        assert palette.tiers["bronze"] == ("#123456", "#654321")
        assert palette.tier_hover["bronze"] == "#abcdef"
        assert palette.categories["progression"] == "#112233"

    def test_rgba_colors_are_normalized(self):
        qss = "AchievementsPalette { surface: rgba(16, 32, 48, 0.5); }"
        palette = parse_achievements_palette(qss, True)
        assert palette.surface == "#102030"

    def test_invalid_colors_fall_back(self):
        fallback = AchievementsPalette.fallback(True)
        qss = "AchievementsPalette { background: #123; gold: not-a-color; }"
        palette = parse_achievements_palette(qss, True)
        assert palette.background == "#112233"
        assert palette.gold == fallback.gold

    def test_custom_theme_without_achievements_qss_falls_back(self, tmp_path, monkeypatch):
        name = _install_custom_theme(tmp_path, monkeypatch, "PlainLight", "light")
        palette = get_achievements_palette(name, False)
        assert palette.dark is False
        assert palette.background == "#f5f3ee"
        assert "AchievementsPalette" in load_achievements_qss(name)

    def test_custom_theme_with_achievements_qss(self, tmp_path, monkeypatch):
        name = _install_custom_theme(
            tmp_path,
            monkeypatch,
            "AmberAchievements",
            "dark",
            textwrap.dedent(CUSTOM_ACHIEVEMENTS_QSS),
        )
        palette = get_achievements_palette(name, True)
        assert palette.dark is True
        assert palette.background == "#101820"
        assert palette.gold == "#ff8000"


class TestAchievementsWidgets:
    def test_card_uses_active_palette(self, qapp):
        palette = AchievementsPalette.fallback(True)
        palette.categories["progression"] = "#112233"
        DS.use_palette(palette)

        from achievements.achievements_ui import AchievementCard

        card = AchievementCard(
            achievement={"tier": "bronze", "category": "progression", "unlocked": True},
            tier_data={"name": "Bronze"},
            category_data={"color": "#00ff00"},
            icon_path="",
        )
        assert card._tier_color.name() == palette.tiers["bronze"][0].lower()
        assert card._cat_color.name() == "#112233"

    def test_stat_bar_and_nav_pill_use_palette(self, qapp):
        palette = AchievementsPalette.fallback(True)
        DS.use_palette(palette)

        from achievements.achievements_ui import NavPill, StatBarWidget

        bar = StatBarWidget("Conversions", "12")
        assert bar.color.name() == palette.blue.lower()
        pill = NavPill("Overview")
        assert pill.objectName() == "AchievementsNavPill"


@pytest.mark.parametrize("dark", [True, False])
def test_palette_has_all_tiers_and_categories(dark):
    palette = AchievementsPalette.fallback(dark)
    assert len(palette.tiers) == 12
    assert len(palette.categories) == 12
