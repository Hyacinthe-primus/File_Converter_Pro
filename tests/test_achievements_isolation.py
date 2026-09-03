"""Enforcement tests for Task 3.3 - Achievements Isolation.

The gamification layer (achievements/) must stay strictly isolated from the
conversion engine:

  * converter/  and tasks/  never reference achievements.
  * Conversion workers (advanced_conversions.py, conversion_worker.py) use
    constructor injection and guards, never a direct import.
  * The achievements package never imports converter/, app/ or tasks/.
  * Only the app layer (main.py, app/logic.py, app/ui.py) may import the
    achievements package.

These tests fail on regression so coupling can be caught at CI time.
"""

import os
import re

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")

_ACH_REF = re.compile(r"achievement", re.IGNORECASE)
_ACH_IMPORT = re.compile(r"^\s*(?:import achievements|from achievements\b)", re.MULTILINE)
_ISOLATED_IMPORT = re.compile(
    r"^\s*(?:import (?:converter|app|tasks)\b|from (?:converter|app|tasks)\b)",
    re.MULTILINE,
)

_APP_IMPORT_WHITELIST = {os.path.join("main.py")}
_APP_IMPORT_WHITELIST.add(os.path.join("app", "logic.py"))
_APP_IMPORT_WHITELIST.add(os.path.join("app", "ui.py"))

_EXCLUDED_DIRS = {"__pycache__", "build", "dist", "achievements", "tests", "Wiki"}


def _iter_py_files(root, subdir=None):
    base = root if subdir is None else os.path.join(root, subdir)
    if not os.path.isdir(base):
        return
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in _EXCLUDED_DIRS)
        for name in sorted(filenames):
            if name.endswith(".py"):
                yield os.path.relpath(os.path.join(dirpath, name), root)


def _read(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as f:
        return f.read()


def test_converter_has_no_achievement_references():
    offending = [
        rel for rel in _iter_py_files(SRC_DIR, "converter") if _ACH_REF.search(_read(SRC_DIR, rel))
    ]
    assert not offending, (
        "converter/ must stay isolated from the gamification layer, "
        "but references 'achievement' in: {}".format(offending)
    )


def test_tasks_has_no_achievement_references():
    offending = [
        rel for rel in _iter_py_files(SRC_DIR, "tasks") if _ACH_REF.search(_read(SRC_DIR, rel))
    ]
    assert not offending, (
        "tasks/ must stay isolated from the gamification layer, "
        "but references 'achievement' in: {}".format(offending)
    )


def test_conversion_workers_do_not_import_achievements():
    for rel in ("advanced_conversions.py", "conversion_worker.py"):
        assert _ACH_IMPORT.search(_read(SRC_DIR, rel)) is None, (
            "{} must not import the achievements package (use injection)".format(rel)
        )


def test_achievements_package_has_no_reverse_coupling():
    offending = [
        rel for rel in _iter_py_files(SRC_DIR, "achievements")
        if _ISOLATED_IMPORT.search(_read(SRC_DIR, rel))
    ]
    assert not offending, (
        "achievements/ must not import converter/, app/ or tasks/: {}".format(offending)
    )


def test_achievements_imports_confined_to_app_layer():
    importers = [
        rel for rel in _iter_py_files(SRC_DIR)
        if _ACH_IMPORT.search(_read(SRC_DIR, rel))
    ]
    extra = sorted(set(importers) - _APP_IMPORT_WHITELIST)
    assert not extra, (
        "only the app layer may import the achievements package, "
        "but found it in: {}".format(extra)
    )
