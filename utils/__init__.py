"""
Shared utility functions for File Converter Pro.

Provides centralized implementations for:
    - resource_path()  : resolve paths for dev mode and PyInstaller
    - get_icon_path()  : locate icon.ico robustly
    - make_tm()        : create a TranslationManager for a given language
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from translations import TranslationManager

import os
import sys


def resource_path(relative_path: str) -> str:
    """Resolve a relative path for both dev mode and PyInstaller onefile.

    In PyInstaller mode, data files are extracted to ``sys._MEIPASS``.
    In dev mode, the project root directory is used as base.
    """
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


def get_icon_path(icon_name: str = "icon.ico") -> str:
    """Locate an icon file robustly (dev + PyInstaller).

    Search order:
        1. PyInstaller extraction dir (sys._MEIPASS)
        2. Project root directory (two levels up from utils/)
        3. Current working directory
        4. Fallback: return icon_name as-is
    """
    if getattr(sys, "frozen", False):
        path = os.path.join(sys._MEIPASS, icon_name)
        if os.path.exists(path):
            return path

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root_dir, icon_name)
    if os.path.exists(path):
        return path

    path = os.path.join(os.getcwd(), icon_name)
    if os.path.exists(path):
        return path

    return icon_name


def make_tm(language: str) -> "TranslationManager":
    """Create a TranslationManager set to the given language.

    This avoids duplicating the same 3-line factory in every file that
    needs translation support.
    """
    from translations import TranslationManager
    tm = TranslationManager()
    tm.set_language(language)
    return tm


__all__ = ["resource_path", "get_icon_path", "make_tm"]
