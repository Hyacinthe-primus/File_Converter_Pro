"""
qss_helpers.py
Helper functions for loading and applying QSS stylesheets.
    _load_qss(filename, theme=None)  — load from styles/themes/[theme/]filename
    _apply_dialog_btn(btn, id)       — setObjectName + apply buttons.qss inline

Expected structure:
    styles/
    └── themes/
        ├── dark/
        ├── light/
        └── *.qss   (theme-independent files)
"""

import os

_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

__all__ = ["_load_qss", "_apply_dialog_btn", "_ROOT_DIR"]

_THEMES_DIR = os.path.join(_ROOT_DIR, "styles", "themes")


def _load_qss(filename: str, theme: str | None = None) -> str:
    """Load a QSS/CSS file from styles/themes/[theme/]filename.

    Args:
        filename : file name (e.g. "buttons.qss")
        theme    : optional sub-folder ("dark", "light", or None for common files)

    Returns an empty string silently when the file is absent so that callers
    can always do ``widget.setStyleSheet(_load_qss(...))`` without guarding.
    """
    parts = [_THEMES_DIR, theme, filename] if theme else [_THEMES_DIR, filename]
    path = os.path.join(*[p for p in parts if p])
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


_BUTTONS_QSS: str | None = None
_CURRENT_THEME: str | None = None


def set_theme(theme: str | None) -> None:
    """Set the active theme ("dark", "light", or None).

    Resets the button stylesheet cache so that the next call to
    _apply_dialog_btn reloads buttons.qss from the new theme folder.
    """
    global _CURRENT_THEME, _BUTTONS_QSS
    _CURRENT_THEME = theme
    _BUTTONS_QSS = None


def _apply_dialog_btn(btn, object_name: str) -> None:
    """Assign object_name and apply buttons.qss directly on btn.

    QDialog instances are top-level windows: the main-window stylesheet does
    not cascade into them, so objectName alone is not sufficient — the
    stylesheet must be set explicitly on each button.

    Supported object names (defined in styles/themes/[theme/]buttons.qss):
        BtnOK        — green confirm button
        BtnCancel    — neutral cancel button
        BtnCancelRed — red/destructive cancel button
    """
    global _BUTTONS_QSS
    if btn is None:
        return
    btn.setObjectName(object_name)
    if _BUTTONS_QSS is None:
        _BUTTONS_QSS = _load_qss("buttons.qss", _CURRENT_THEME)
    if _BUTTONS_QSS:
        btn.setStyleSheet(_BUTTONS_QSS)