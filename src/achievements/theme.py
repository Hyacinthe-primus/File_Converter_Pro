"""Theme loading and painted-widget palette for the achievements UI."""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace

from qss_helpers import _load_qss
from theme_manager import get_custom_theme_kind

_PALETTE_SELECTOR = "AchievementsPalette"
_BLOCK_RE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.DOTALL)
_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_PROP_RE = re.compile(r"(?:^|;)\s*([A-Za-z0-9_-]+)\s*:\s*([^;]+)")
_HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_RGB_RE = re.compile(r"^rgba?\(([^)]+)\)$")

_PALETTE_FIELDS = (
    "background",
    "surface",
    "surface_alt",
    "input",
    "border",
    "border_light",
    "text",
    "text_secondary",
    "muted",
    "gold",
    "gold_bright",
    "gold_dim",
    "green",
    "red",
    "red_dim",
    "blue",
    "purple",
    "secret_bg",
    "secret_text",
    "progress_text",
    "ring_track",
    "ring_progress",
    "ring_glow",
    "ring_tip",
    "ring_complete",
    "progress_track",
    "progress_fill",
    "progress_fill_end",
    "stat_track",
    "card_sheen",
    "card_shadow",
)

_DEFAULT_TIERS = {
    "starter": ("#A8DADC", "#4A8A8C"),
    "bronze": ("#CD7F32", "#80500A"),
    "steel": ("#71797E", "#3A4044"),
    "silver": ("#C0C0C0", "#707070"),
    "platinum_tier": ("#C18D30", "#7A5A10"),
    "gold": ("#FFD700", "#7A6520"),
    "rare": ("#4169E1", "#1A3A90"),
    "epic": ("#9370DB", "#4A2080"),
    "legendary": ("#FF8C00", "#804400"),
    "diamond": ("#B9F2FF", "#3090C0"),
    "platinum": ("#E5E4E2", "#808080"),
    "advanced": ("#22d3ee", "#0A7A90"),
}

_DEFAULT_TIER_HOVER = {
    "starter": "#C8ECEE",
    "bronze": "#E8943A",
    "steel": "#9AAAB0",
    "silver": "#E0E0E0",
    "platinum_tier": "#E0A840",
    "gold": "#FFD700",
    "rare": "#6B8FFF",
    "epic": "#B090F0",
    "legendary": "#FFA830",
    "diamond": "#D8F8FF",
    "platinum": "#F5F4F2",
    "advanced": "#50E8FF",
}

_DEFAULT_CATEGORIES = {
    "progression": "#FFD700",
    "conversion": "#4dabf7",
    "pdf_tools": "#FF6B6B",
    "compression": "#51CF66",
    "security": "#FFA94D",
    "technical": "#CC5DE8",
    "usage": "#339AF0",
    "completion": "#20C997",
    "ultimate": "#9775FA",
    "fun": "#FF8787",
    "advanced_conversions": "#22d3ee",
    "templates": "#a78bfa",
}


@dataclass(frozen=True)
class AchievementsPalette:
    background: str
    surface: str
    surface_alt: str
    input: str
    border: str
    border_light: str
    text: str
    text_secondary: str
    muted: str
    gold: str
    gold_bright: str
    gold_dim: str
    green: str
    red: str
    red_dim: str
    blue: str
    purple: str
    secret_bg: str
    secret_text: str
    progress_text: str
    ring_track: str
    ring_progress: str
    ring_glow: str
    ring_tip: str
    ring_complete: str
    progress_track: str
    progress_fill: str
    progress_fill_end: str
    stat_track: str
    card_sheen: str
    card_shadow: str
    dark: bool
    font_family: str = "Segoe UI"
    tiers: dict[str, tuple[str, str]] = field(default_factory=dict)
    tier_hover: dict[str, str] = field(default_factory=dict)
    categories: dict[str, str] = field(default_factory=dict)
    ranks: dict[str, str] = field(default_factory=dict)

    @classmethod
    def fallback(cls, dark: bool) -> "AchievementsPalette":
        if dark:
            background = "#0D1117"
            surface = "#161B22"
            surface_alt = "#1C2333"
            input_color = "#21262D"
            border = "#30363D"
            border_light = "#3D444D"
            text = "#E6EDF3"
            text_secondary = "#8B949E"
            muted = "#484F58"
            red_dim = "#3D1C1A"
            secret_bg = "#0A0608"
            progress_text = "#FFFFFF"
        else:
            background = "#F5F3EE"
            surface = "#FFFFFF"
            surface_alt = "#EDE9E0"
            input_color = "#F9F7F2"
            border = "#D6CFC0"
            border_light = "#C4BBA8"
            text = "#1C1A16"
            text_secondary = "#6B6355"
            muted = "#A89F8F"
            red_dim = "#FADBD8"
            secret_bg = "#FAE8E8"
            progress_text = "#1C1A16"
        if dark:
            gold = "#D4AF37"
            gold_bright = "#FFD700"
            green = "#3FB950"
            red = "#F85149"
            blue = "#58A6FF"
            purple = "#BC8CFF"
            categories = dict(_DEFAULT_CATEGORIES)
        else:
            gold = "#8A6508"
            gold_bright = "#8A6508"
            green = "#2E7D32"
            red = "#D32F2F"
            blue = "#1976D2"
            purple = "#7B1FA2"
            categories = {
                "progression": "#8A6508",
                "conversion": "#1976D2",
                "pdf_tools": "#D32F2F",
                "compression": "#2E7D32",
                "security": "#E65100",
                "technical": "#7B1FA2",
                "usage": "#1565C0",
                "completion": "#00897B",
                "ultimate": "#5E35B1",
                "fun": "#C62828",
                "advanced_conversions": "#00838F",
                "templates": "#6A1B9A",
            }
        return cls(
            background=background,
            surface=surface,
            surface_alt=surface_alt,
            input=input_color,
            border=border,
            border_light=border_light,
            text=text,
            text_secondary=text_secondary,
            muted=muted,
            gold=gold,
            gold_bright=gold_bright,
            gold_dim="#7A6520",
            green=green,
            red=red,
            red_dim=red_dim,
            blue=blue,
            purple=purple,
            secret_bg=secret_bg,
            secret_text="#8B0000",
            progress_text=progress_text,
            ring_track=border,
            ring_progress=gold,
            ring_glow=gold,
            ring_tip=gold_bright,
            ring_complete=gold_bright,
            progress_track=surface_alt,
            progress_fill="#7A6520",
            progress_fill_end=gold,
            stat_track=surface_alt,
            card_sheen="#FFFFFF",
            card_shadow="#000000",
            dark=dark,
            tiers=dict(_DEFAULT_TIERS),
            tier_hover=dict(_DEFAULT_TIER_HOVER),
            categories=categories,
        )


def resolve_theme_name(parent, dark: bool | None = None) -> str:
    custom_theme = getattr(parent, "current_theme", None) if parent else None
    if custom_theme and custom_theme not in ("dark", "light"):
        return custom_theme
    if dark is None:
        dark = bool(getattr(parent, "dark_mode", False)) if parent else False
    return "dark" if dark else "light"


def load_achievements_qss(theme: str | None) -> str:
    return _load_qss("achievements.qss", theme)


def get_achievements_palette(theme: str | None, dark: bool) -> AchievementsPalette:
    name = theme or ("dark" if dark else "light")
    if name == "dark":
        is_dark = True
    elif name == "light":
        is_dark = False
    else:
        is_dark = dark
        try:
            is_dark = get_custom_theme_kind(name) == "dark"
        except Exception:
            pass
    fallback = AchievementsPalette.fallback(is_dark)
    return parse_achievements_palette(load_achievements_qss(name), is_dark, fallback)


def parse_achievements_palette(
    qss: str,
    dark: bool,
    fallback: AchievementsPalette | None = None,
) -> AchievementsPalette:
    base = fallback or AchievementsPalette.fallback(dark)
    body = _rule_body(qss, _PALETTE_SELECTOR)
    if not body:
        return base

    values = {}
    for key in _PALETTE_FIELDS:
        parsed = _parse_color(_prop(body, key))
        if parsed is not None:
            values[key] = parsed

    font_family = _parse_font(_prop(body, "font_family"))
    if font_family:
        values["font_family"] = font_family

    tiers = dict(base.tiers)
    tier_hover = dict(base.tier_hover)
    categories = dict(base.categories)
    ranks = dict(base.ranks)
    for key, value in _all_props(body).items():
        parsed = _parse_color(value)
        if parsed is None:
            continue
        if key.startswith("tier_"):
            tier_key = key[5:]
            if tier_key.endswith("_glow"):
                tier_id = tier_key[:-5]
                current = tiers.get(tier_id)
                if current:
                    tiers[tier_id] = (current[0], parsed)
            elif tier_key.endswith("_hover"):
                tier_hover[tier_key[:-6]] = parsed
            else:
                current = tiers.get(tier_key, ("#CD7F32", "#80500A"))
                tiers[tier_key] = (parsed, current[1])
        elif key.startswith("category_"):
            categories[key[9:]] = parsed
        elif key.startswith("rank_"):
            ranks[key[5:]] = parsed

    return replace(
        base,
        **values,
        tiers=tiers,
        tier_hover=tier_hover,
        categories=categories,
        ranks=ranks,
    )


def _rule_body(qss: str, selector: str) -> str:
    for match in _BLOCK_RE.finditer(qss):
        selectors = [part.strip() for part in _COMMENT_RE.sub("", match.group(1)).split(",")]
        if selector in selectors:
            return _COMMENT_RE.sub("", match.group(2))
    return ""


def _prop(body: str, name: str) -> str:
    match = re.search(r"(?:^|;)\s*" + re.escape(name) + r"\s*:\s*([^;]+)", body)
    return match.group(1).strip() if match else ""


def _all_props(body: str) -> dict[str, str]:
    return {match.group(1).lower(): match.group(2).strip() for match in _PROP_RE.finditer(body)}


def _parse_font(value: str) -> str:
    value = value.strip().strip("\"'")
    if not value:
        return ""
    return value.split(",")[0].strip().strip("\"'")


def _parse_color(value: str) -> str | None:
    value = value.strip().strip("\"'")
    match = _HEX_RE.match(value)
    if match:
        raw = match.group(1)
        if len(raw) == 3:
            raw = "".join(char * 2 for char in raw)
        elif len(raw) == 8:
            raw = raw[:6]
        return "#" + raw.lower()

    match = _RGB_RE.match(value)
    if match:
        parts = [part.strip() for part in match.group(1).split(",")]
        if len(parts) < 3:
            return None
        try:
            red, green, blue = (max(0, min(255, int(float(part)))) for part in parts[:3])
        except ValueError:
            return None
        return f"#{red:02x}{green:02x}{blue:02x}"
    return None


class _ThemeProxy:
    RADIUS = 12
    RADIUS_S = 7
    PAD = 16
    PAD_S = 10

    _ALIASES = {
        "BG_BASE": "background",
        "BG_SURFACE": "surface",
        "BG_RAISED": "surface_alt",
        "BG_INPUT": "input",
        "BORDER": "border",
        "BORDER_LIGHT": "border_light",
        "TEXT_PRIMARY": "text",
        "TEXT_SECONDARY": "text_secondary",
        "TEXT_MUTED": "muted",
        "GOLD": "gold",
        "GOLD_BRIGHT": "gold_bright",
        "GOLD_DIM": "gold_dim",
        "GREEN": "green",
        "RED": "red",
        "RED_DIM": "red_dim",
        "BLUE": "blue",
        "PURPLE": "purple",
        "SECRET_BG": "secret_bg",
        "SECRET_TEXT": "secret_text",
        "PROGRESS_TEXT": "progress_text",
        "RING_TRACK": "ring_track",
        "RING_PROGRESS": "ring_progress",
        "RING_GLOW": "ring_glow",
        "RING_TIP": "ring_tip",
        "RING_COMPLETE": "ring_complete",
        "PROGRESS_TRACK": "progress_track",
        "PROGRESS_FILL": "progress_fill",
        "PROGRESS_FILL_END": "progress_fill_end",
        "STAT_TRACK": "stat_track",
        "CARD_SHEEN": "card_sheen",
        "CARD_SHADOW": "card_shadow",
        "FONT_FAMILY": "font_family",
        "TIERS": "tiers",
        "TIER_HOVER": "tier_hover",
        "CATEGORIES": "categories",
        "RANKS": "ranks",
    }

    def __init__(self):
        self._palette = AchievementsPalette.fallback(True)

    def use_palette(self, palette: AchievementsPalette) -> None:
        self._palette = palette

    @property
    def is_dark(self) -> bool:
        return self._palette.dark

    def __getattr__(self, name: str):
        return getattr(self._palette, self._ALIASES.get(name, name))


DS = _ThemeProxy()
