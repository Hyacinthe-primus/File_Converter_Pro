"""Theme palette extraction for the statistics dashboard."""

from __future__ import annotations

import colorsys
import re
from dataclasses import dataclass

from qss_helpers import _load_qss
from theme_manager import get_custom_theme_kind, get_dashboard_overrides

_COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]+\)")
_BLOCK_RE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.DOTALL)
_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


@dataclass(frozen=True)
class _Color:
    hex: str
    alpha: float = 1.0


@dataclass(frozen=True)
class DashboardPalette:
    background: str
    surface: str
    surface_alt: str
    border: str
    text: str
    muted: str
    accent: str
    accent_text: str
    on_accent: str
    dark: bool

    @classmethod
    def fallback(
        cls,
        dark: bool,
        accent: str | None = None,
        accent_text: str | None = None,
    ) -> "DashboardPalette":
        if dark:
            background = "#0d1117"
            surface = "#161b27"
            surface_alt = "#1a2236"
            border = "#2d3748"
            text = "#ffffff"
            muted = "#c8d0dc"
            accent = accent or "#4dabf7"
        else:
            background = "#f0f2f7"
            surface = "#ffffff"
            surface_alt = "#f7faff"
            border = "#dde3ec"
            text = "#1a202c"
            muted = "#4a5568"
            accent = accent or "#2b6cb0"
        return cls(
            background=background,
            surface=surface,
            surface_alt=surface_alt,
            border=border,
            text=text,
            muted=muted,
            accent=accent,
            accent_text=accent_text or accent,
            on_accent=contrast_text(accent),
            dark=dark,
        )


def get_dashboard_palette(theme: str | None, dark: bool) -> DashboardPalette:
    name = theme or ("dark" if dark else "light")
    is_dark = dark
    if name not in ("dark", "light"):
        try:
            is_dark = get_custom_theme_kind(name) == "dark"
        except Exception:
            pass
    fallback = DashboardPalette.fallback(is_dark)
    qss = _load_qss("dashboard.qss", name)
    palette = parse_dashboard_palette(qss, is_dark, fallback)
    if name not in ("dark", "light"):
        try:
            overrides = get_dashboard_overrides(name)
        except Exception:
            overrides = {}
        if overrides:
            palette = apply_dashboard_overrides(palette, overrides)
    return palette


_OVERRIDE_FIELDS = (
    "background",
    "surface",
    "surface_alt",
    "border",
    "text",
    "muted",
    "accent",
    "accent_text",
)


def apply_dashboard_overrides(
    palette: DashboardPalette,
    overrides: dict[str, str],
) -> DashboardPalette:
    values = {}
    for key in _OVERRIDE_FIELDS:
        parsed = _parse_color(str(overrides.get(key, "")).strip())
        if parsed is not None and parsed.alpha >= 0.999:
            values[key] = parsed.hex
    if not values:
        return palette

    accent = values.get("accent", palette.accent)
    accent_text = values.get("accent_text")
    if accent_text is None:
        accent_text = accent if "accent" in values else palette.accent_text
    return DashboardPalette(
        background=values.get("background", palette.background),
        surface=values.get("surface", palette.surface),
        surface_alt=values.get("surface_alt", palette.surface_alt),
        border=values.get("border", palette.border),
        text=values.get("text", palette.text),
        muted=values.get("muted", palette.muted),
        accent=accent,
        accent_text=accent_text,
        on_accent=contrast_text(accent),
        dark=palette.dark,
    )


def parse_dashboard_palette(
    qss: str,
    dark: bool,
    fallback: DashboardPalette | None = None,
) -> DashboardPalette:
    base = fallback or DashboardPalette.fallback(dark)
    if not qss.strip():
        return base

    widget_body = _rule_body(qss, "QWidget")
    background = _body_color(
        widget_body,
        ("background-color", "background"),
        base.background,
        base.background,
    )
    text = _body_color(widget_body, ("color",), base.text, background)

    pane_body = _rule_body(qss, "QTabWidget::pane")
    surface = _body_color(pane_body, ("background", "background-color"), base.surface, background)
    border = _body_color(pane_body, ("border", "border-color", "border-top", "border-bottom"), base.border, surface)

    table_body = _rule_body(qss, "QTableWidget")
    if _prop(table_body, "alternate-background-color"):
        surface_alt = _body_color(
            table_body,
            ("alternate-background-color",),
            base.surface_alt,
            surface,
        )
    elif table_body:
        surface_alt = mix_colors(surface, background, 0.5)
    else:
        surface_alt = base.surface_alt
    table_border = _body_color(table_body, ("border", "border-color"), border, surface)
    if border == base.border and table_border != border:
        border = table_border

    tab_body = _rule_body(qss, "QTabBar::tab")
    muted = _body_color(tab_body, ("color",), base.muted, background)

    accent = _accent_from_qss(qss, surface, base.accent)

    return DashboardPalette(
        background=background,
        surface=surface,
        surface_alt=surface_alt,
        border=border,
        text=text,
        muted=muted,
        accent=accent,
        accent_text=accent,
        on_accent=contrast_text(accent),
        dark=dark,
    )


def accent_variants(accent: str, count: int) -> list[str]:
    if count <= 0:
        return []
    if count == 1:
        return [accent]
    r, g, b = _rgb(accent)
    hue, lightness, saturation = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    saturation = max(saturation, 0.35)
    variants = [accent]
    for index in range(1, count):
        offset = index - (count - 1) / 2.0
        variant_hue = (hue + offset * 0.035) % 1.0
        variant_lightness = min(0.74, max(0.30, lightness + (0.07 if index % 2 else -0.05)))
        red, green, blue = colorsys.hls_to_rgb(variant_hue, variant_lightness, saturation)
        variants.append(_hex_from_rgb(red * 255.0, green * 255.0, blue * 255.0))
    return variants


def mix_colors(color1: str, color2: str, amount: float) -> str:
    amount = min(1.0, max(0.0, amount))
    r1, g1, b1 = _rgb(color1)
    r2, g2, b2 = _rgb(color2)
    return _hex_from_rgb(
        r1 + (r2 - r1) * amount,
        g1 + (g2 - g1) * amount,
        b1 + (b2 - b1) * amount,
    )


def shade_color(color: str, amount: float) -> str:
    target = "#ffffff" if amount > 0 else "#000000"
    return mix_colors(color, target, abs(amount))


def contrast_text(color: str) -> str:
    r, g, b = _rgb(color)
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return "#111111" if luminance > 150 else "#ffffff"


def _rule_body(qss: str, selector: str) -> str:
    for match in _BLOCK_RE.finditer(qss):
        selectors = _selectors(match.group(1))
        if selector in selectors:
            return match.group(2)
    return ""


def _selectors(selector_text: str) -> list[str]:
    cleaned = _COMMENT_RE.sub("", selector_text)
    return [part.strip() for part in cleaned.split(",")]


def _prop(body: str, name: str) -> str:
    match = re.search(r"(?:^|;)\s*" + re.escape(name) + r"\s*:\s*([^;]+)", body)
    return match.group(1).strip() if match else ""


def _body_color(body: str, props: tuple[str, ...], default: str, backdrop: str) -> str:
    for prop in props:
        value = _prop(body, prop)
        for color in _colors(value):
            return _blend(color, backdrop)
    return default


def _accent_from_qss(qss: str, surface: str, default: str) -> str:
    candidates = []
    for selector in ("QTabBar::tab:selected", "QGroupBox::title"):
        body = _rule_body(qss, selector)
        for prop in (
            "border-bottom",
            "border-top",
            "border",
            "border-color",
            "background",
            "background-color",
            "color",
        ):
            for color in _colors(_prop(body, prop)):
                blended = _blend(color, surface)
                if _saturation(blended) >= 0.12:
                    candidates.append(blended)
    if not candidates:
        return default
    return max(candidates, key=_color_score)


def _colors(value: str) -> list[_Color]:
    colors = []
    for token in _COLOR_RE.findall(value):
        parsed = _parse_color(token)
        if parsed is not None:
            colors.append(parsed)
    return colors


def _parse_color(token: str) -> _Color | None:
    token = token.strip()
    if token.startswith("#"):
        raw = token[1:]
        alpha = 1.0
        if len(raw) in (3, 4):
            alpha = int(raw[3] * 2, 16) / 255.0 if len(raw) == 4 else 1.0
            raw = "".join(char * 2 for char in raw[:3])
        elif len(raw) == 8:
            alpha = int(raw[6:8], 16) / 255.0
            raw = raw[:6]
        if len(raw) != 6:
            return None
        return _Color("#" + raw.lower(), alpha)

    if token.startswith("rgb"):
        match = re.match(r"rgba?\(([^)]+)\)", token)
        if not match:
            return None
        parts = [part.strip() for part in match.group(1).split(",")]
        if len(parts) < 3:
            return None
        try:
            red, green, blue = (max(0, min(255, int(float(part)))) for part in parts[:3])
            alpha = max(0.0, min(1.0, float(parts[3]))) if len(parts) > 3 else 1.0
        except ValueError:
            return None
        return _Color(_hex_from_rgb(red, green, blue), alpha)

    return None


def _blend(color: _Color, backdrop: str) -> str:
    if color.alpha >= 0.999:
        return color.hex
    if color.alpha <= 0:
        return backdrop
    return mix_colors(backdrop, color.hex, color.alpha)


def _rgb(color: str) -> tuple[int, int, int]:
    try:
        return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    except (ValueError, IndexError):
        return 0, 0, 0


def _hex_from_rgb(red: float, green: float, blue: float) -> str:
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, int(round(red)))),
        max(0, min(255, int(round(green)))),
        max(0, min(255, int(round(blue)))),
    )


def _saturation(color: str) -> float:
    red, green, blue = _rgb(color)
    high = max(red, green, blue)
    low = min(red, green, blue)
    return 0.0 if high == 0 else (high - low) / high


def _color_score(color: str) -> float:
    red, green, blue = _rgb(color)
    value = max(red, green, blue) / 255.0
    return _saturation(color) * (0.35 + 0.65 * value)
