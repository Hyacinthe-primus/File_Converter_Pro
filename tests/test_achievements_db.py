"""Tests for achievements format tracking: 7z seeding, rar removal, and
the INSERT OR IGNORE / UPDATE marking flow in mark_format_as_used."""

import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import achievements.achievements_system as mod


@pytest.fixture
def ach(tmp_path):
    """AchievementSystem wired to an isolated temp achievements.db.

    Builds the instance via __new__ to skip the constructor (which would open
    the real achievements.db next to the source), then runs the real DB
    initialization on a temp database.
    """
    instance = mod.AchievementSystem.__new__(mod.AchievementSystem)
    instance.db_path = str(tmp_path / "achievements.db")
    instance.achievements_data = {}
    instance.load_achievements_data()
    instance.init_database()
    instance.initialize_achievements()
    return instance, instance.db_path


def _formats(db_path):
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT format, used FROM used_formats").fetchall()
    finally:
        conn.close()
    return dict(rows)


def _used(db_path, fmt):
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT used FROM used_formats WHERE format = ?", (fmt,)).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


def test_seed_includes_7z_and_drops_rar(ach):
    instance, db_path = ach
    formats = _formats(db_path)
    assert "7z" in formats
    assert "rar" not in formats
    assert formats["7z"] in (0, False)
    assert set(formats) == {"pdf", "docx", "jpg", "png", "zip", "7z", "tar", "gz"}


def test_mark_7z_as_used(ach):
    instance, db_path = ach
    instance.mark_format_as_used("7z")
    assert _used(db_path, "7z") in (1, True)


def test_mark_7z_is_idempotent(ach):
    instance, db_path = ach
    instance.mark_format_as_used("7z")
    instance.mark_format_as_used("7z")
    assert _used(db_path, "7z") in (1, True)


def test_mark_rar_is_ignored(ach):
    instance, db_path = ach
    instance.mark_format_as_used("rar")
    assert _used(db_path, "rar") is None


def test_mark_invalid_format_is_ignored(ach):
    instance, db_path = ach
    instance.mark_format_as_used("exe")
    assert _used(db_path, "exe") is None
