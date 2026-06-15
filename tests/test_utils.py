"""Tests for shared utility functions."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_resource_path():
    """resource_path should return a valid path."""
    from utils import resource_path
    result = resource_path("icon.ico")
    assert isinstance(result, str)
    assert "icon.ico" in result


def test_get_icon_path():
    """get_icon_path should return a string path."""
    from utils import get_icon_path
    result = get_icon_path()
    assert isinstance(result, str)
    assert "icon.ico" in result


def test_make_tm():
    """make_tm should return a TranslationManager with correct language."""
    from utils import make_tm
    tm = make_tm("fr")
    assert tm.current_language == "fr"
    tm_en = make_tm("en")
    assert tm_en.current_language == "en"
