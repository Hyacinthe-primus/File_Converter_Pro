"""
qss_helpers.py
Helper functions for loading and applying QSS stylesheets.
    _load_qss(filename, theme=None)  - load from styles/themes/[theme/]filename
    _apply_dialog_btn(btn, id)       - setObjectName + apply buttons.qss inline

Expected structure:
    styles/
    └── themes/
        ├── dark/
        ├── light/
        └── *.qss   (theme-independent files)
"""

import os
import re

from utils import SRC_DIR, resource_path

_ROOT_DIR = str(SRC_DIR)

__all__ = ["_load_qss", "_apply_dialog_btn", "_dialog_buttons_qss", "_ROOT_DIR"]

_THEMES_DIR = resource_path(os.path.join("styles", "themes"))
_CUSTOM_THEMES_DIR = resource_path(os.path.join("styles", "custom_themes"))


def _load_qss(filename: str, theme: str | None = None) -> str:
    """Load a QSS/CSS file from styles/themes/[theme/] or custom_themes/[theme/]filename.

    Fallback chain for custom themes:
      1. custom_themes/{theme}/{filename}
      2. custom_themes/{theme}/{theme}/{filename}
      3. themes/{base_kind}/{filename}  (light or dark)
      4. themes/{filename}              (root)

    For builtin themes:
      1. themes/{theme}/{filename}
      2. themes/{filename}              (root)
    """
    if theme:
        custom_path = os.path.join(_CUSTOM_THEMES_DIR, theme, filename)
        try:
            with open(custom_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            pass
        custom_inner = os.path.join(_CUSTOM_THEMES_DIR, theme, theme, filename)
        try:
            with open(custom_inner, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            pass
        if theme not in ("dark", "light"):
            from theme_manager import get_custom_theme_kind

            base = get_custom_theme_kind(theme)
            base_path = os.path.join(_THEMES_DIR, base, filename)
            try:
                with open(base_path, "r", encoding="utf-8") as f:
                    return f.read()
            except FileNotFoundError:
                pass
        else:
            builtin_path = os.path.join(_THEMES_DIR, theme, filename)
            try:
                with open(builtin_path, "r", encoding="utf-8") as f:
                    return f.read()
            except FileNotFoundError:
                pass
        root_path = os.path.join(_THEMES_DIR, filename)
        try:
            with open(root_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            pass
        return ""
    parts = [_THEMES_DIR, filename]
    path = os.path.join(*[p for p in parts if p])
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


_QSS_BLOCK_RE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.DOTALL)


def _extract_qss_blocks(qss: str, selector_token: str) -> str:
    """Return top-level QSS blocks whose selector contains selector_token."""
    blocks = []
    for match in _QSS_BLOCK_RE.finditer(qss):
        if selector_token in match.group(1):
            blocks.append(match.group(0).strip())
    return "\n\n".join(blocks)


def _dialog_buttons_qss(theme: str | None) -> str:
    """Return dialog-button rules for the active theme.

    A theme-specific buttons.qss wins when it differs from the stock fallback.
    Otherwise the theme's style.qss is the source of truth, which prevents
    custom themes that ship a stale copy of buttons.qss from losing their look.
    """
    buttons_qss = _load_qss("buttons.qss", theme)
    default_buttons_qss = _load_qss("buttons.qss", None)
    if buttons_qss and buttons_qss != default_buttons_qss:
        return buttons_qss
    button_rules = _extract_qss_blocks(_load_qss("style.qss", theme), "QPushButton")
    if button_rules:
        return button_rules
    return buttons_qss or default_buttons_qss


_BUTTONS_QSS: str | None = None
_CURRENT_THEME: str | None = None


def set_theme(theme: str | None) -> None:
    """Set the active theme ("dark", "light", or custom name).

    Resets the button stylesheet cache so that the next call to
    _apply_dialog_btn reloads button rules from the new theme's style.qss.
    """
    global _CURRENT_THEME, _BUTTONS_QSS
    _CURRENT_THEME = theme
    _BUTTONS_QSS = None


def get_current_theme(dark: bool) -> str:
    """Return the active theme name, respecting custom themes."""
    if _CURRENT_THEME and _CURRENT_THEME not in ("dark", "light"):
        return _CURRENT_THEME
    return "dark" if dark else "light"


def _apply_dialog_btn(btn, object_name: str) -> None:
    """Assign object_name and apply the active theme's button rules to btn.

    Dialog buttons are styled explicitly so they keep the active theme even
    when their parent does not propagate its stylesheet. The rules come from
    the theme's style.qss; buttons.qss is only a legacy fallback.

    Supported object names (defined in styles/themes/[theme/]style.qss):
        BtnOK        - green confirm button
        BtnCancel    - neutral cancel button
        BtnCancelRed - red/destructive cancel button
    """
    global _BUTTONS_QSS
    if btn is None:
        return
    btn.setObjectName(object_name)
    if _BUTTONS_QSS is None:
        _BUTTONS_QSS = _dialog_buttons_qss(_CURRENT_THEME)
    if _BUTTONS_QSS:
        btn.setStyleSheet(_BUTTONS_QSS)
