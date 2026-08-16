"""Tests for multi-project tabs — opening a project adds a tab to the top bar
(next to "File Converter Pro"), each tab keeps its own file list / project state,
and at most MAX_PROJECT_TABS (5) projects can be open."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app
    app.processEvents()


@pytest.fixture()
def app(qapp, tmp_path):
    """Build a real FileConverterApp offscreen with isolated config and
    non-modal message boxes, so the test never blocks on dialogs."""
    cfg = {
        "accepted_terms": True,
        "accepted_privacy": True,
        "language": "fr",
        "use_system_theme": False,
        "dark_mode": False,
        "last_project": None,
        "auto_open_last_project": False,
        "show_dashboard_on_startup": False,
    }
    cfg_file = tmp_path / "config.dat"
    cfg_file.write_text(json.dumps(cfg), encoding="utf-8")

    from config import ConfigManager

    cm = ConfigManager(str(cfg_file), str(tmp_path / "key.key"))

    QMessageBox.critical = staticmethod(lambda *a, **k: None)
    QMessageBox.warning = staticmethod(lambda *a, **k: None)

    from app import FileConverterApp

    window = FileConverterApp(cm)
    window.hide()
    qapp.processEvents()
    return window


def _make_project(tmp_path, name, paths):
    p = tmp_path / f"{name}.fcproj"
    data = {
        "version": 1,
        "name": name,
        "notes": "",
        "files": [{"path": str(f), "added_at": "2026-01-01T00:00:00", "size": 1} for f in paths],
    }
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def _titles(app):
    return [
        st["widget"].findChild(QPushButton, "ProjectTabBtn").text().removeprefix("🗁  ")
        for st in app._project_tabs
    ]


def _norm(path):
    return os.path.normpath(str(path))


class TestProjectTabs:
    def test_startup_no_tabs_and_empty_list(self, app):
        assert app._project_tabs == []
        assert app.project_tab_bar.isVisible() is False
        assert app.current_project is None
        assert app.files_list == []

    def test_first_open_creates_tab_near_title(self, app, tmp_path):
        f1 = tmp_path / "a.txt"
        f1.write_text("a")
        proj = _make_project(tmp_path, "Alpha", [f1])

        app.open_project_file(proj)

        assert len(app._project_tabs) == 1
        assert app.project_tab_bar.isHidden() is False
        assert app.current_project == proj
        assert [_norm(f1)] == [_norm(p) for p in app.files_list]
        assert _titles(app) == ["Alpha"]
        assert app.project_name_lbl.isVisible() is False

    def test_second_open_adds_tab_with_independent_state(self, app, tmp_path):
        f1 = tmp_path / "a.txt"
        f1.write_text("a")
        proj1 = _make_project(tmp_path, "Alpha", [f1])
        proj2 = _make_project(tmp_path, "Beta", [f1])

        app.open_project_file(proj1)
        app.open_project_file(proj2)

        assert len(app._project_tabs) == 2
        assert app.current_project == proj2
        assert len(app.files_list) == 1
        assert _titles(app) == ["Alpha", "Beta"]

    def test_switch_tab_restores_its_own_state(self, app, tmp_path):
        f1 = tmp_path / "a.txt"
        f1.write_text("a")
        f2 = tmp_path / "b.txt"
        f2.write_text("b")
        proj1 = _make_project(tmp_path, "Alpha", [f1, f2])
        proj2 = _make_project(tmp_path, "Beta", [f1])

        app.open_project_file(proj1)
        app.open_project_file(proj2)

        app._switch_project_tab(app._project_tabs[0])
        assert app.current_project == proj1
        assert len(app.files_list) == 2

        app.files_list.append(str(f1))
        app._sync_active_tab_state()
        app._switch_project_tab(app._project_tabs[1])
        assert len(app.files_list) == 1, "tab1 must not see tab0 edits"

        app._switch_project_tab(app._project_tabs[0])
        assert len(app.files_list) == 3, "tab0 edits preserved after switching back"

    def test_close_tab_and_last_tab_returns_to_blank(self, app, tmp_path):
        f1 = tmp_path / "a.txt"
        f1.write_text("a")
        proj1 = _make_project(tmp_path, "Alpha", [f1])
        proj2 = _make_project(tmp_path, "Beta", [f1])

        app.open_project_file(proj1)
        app.open_project_file(proj2)

        app._close_project_tab(app._project_tabs[1])
        assert len(app._project_tabs) == 1
        assert app.current_project == proj1

        app._close_project_tab(app._project_tabs[0])
        assert app._project_tabs == []
        assert app.project_tab_bar.isHidden() is True
        assert app.current_project is None
        assert app.files_list == []

    def test_save_syncs_state_and_title_to_active_tab_only(self, app, tmp_path):
        f1 = tmp_path / "a.txt"
        f1.write_text("a")
        proj1 = _make_project(tmp_path, "Alpha", [f1])

        app.open_project_file(proj1)
        app._add_project_tab(files_list=[], current_project=None, project_data={"name": "Gamma"})

        out = tmp_path / "out.fcproj"
        app.files_list = [str(f1)]
        app._project_data = {"name": "Gamma", "notes": "", "files": []}
        app._save_project_to(str(out))

        assert app.current_project == str(out)
        assert _titles(app) == ["Alpha", "Gamma"]

        app._switch_project_tab(app._project_tabs[0])
        assert app.current_project == proj1, "saving one tab must not touch the other"
        assert _titles(app) == ["Alpha", "Gamma"]

    def test_add_project_tab_title_from_project_data(self, app):
        app._add_project_tab(files_list=[], current_project=None, project_data={"name": "Gamma"})
        assert len(app._project_tabs) == 1
        assert _titles(app) == ["Gamma"]
        assert app.current_project is None
        assert app.files_list == []

    def test_reopening_same_file_switches_to_existing_tab(self, app, tmp_path):
        f1 = tmp_path / "a.txt"
        f1.write_text("a")
        proj1 = _make_project(tmp_path, "Alpha", [f1])
        proj2 = _make_project(tmp_path, "Beta", [f1])

        app.open_project_file(proj1)
        app.open_project_file(proj2)
        assert len(app._project_tabs) == 2

        infos = []
        QMessageBox.information = staticmethod(lambda *a, **k: infos.append(a[1:]))

        app.open_project_file(proj1)
        assert len(app._project_tabs) == 2, "no duplicate tab for the same file"
        assert app.current_project == proj1
        assert app._active_tab is app._project_tabs[0]
        assert len(infos) == 1, "already-open dialog shown once"
        assert infos[0][1] == app.translate_text("project_already_open")
        assert infos[0][1] != "project_already_open"


class TestProjectTabLimit:
    def test_max_5_tabs_rejects_the_6th_with_message(self, app, tmp_path):
        f1 = tmp_path / "a.txt"
        f1.write_text("a")
        projects = [_make_project(tmp_path, f"P{i}", [f1]) for i in range(1, 7)]

        warned = []
        QMessageBox.warning = staticmethod(
            lambda *a, **k: warned.append(a[1:])
        )

        for proj in projects:
            app.open_project_file(proj)

        assert len(app._project_tabs) == 5
        assert app.project_tab_bar.isHidden() is False
        assert app.current_project == projects[4]
        assert len(warned) == 1, "only the 6th open should warn"
        assert app.translate_text("project_tabs_limit") != "project_tabs_limit"

    def test_new_project_respects_limit(self, app):
        for i in range(5):
            tab = app._add_project_tab(project_data={"name": f"T{i}"})
            assert tab is not None
        blocked = app._add_project_tab(project_data={"name": "TooMany"})
        assert blocked is None
        assert len(app._project_tabs) == 5

    def test_close_frees_a_slot(self, app, tmp_path):
        f1 = tmp_path / "a.txt"
        f1.write_text("a")
        projects = [_make_project(tmp_path, f"P{i}", [f1]) for i in range(1, 6)]
        for proj in projects:
            app.open_project_file(proj)
        assert len(app._project_tabs) == 5

        app._close_project_tab(app._project_tabs[0])
        assert len(app._project_tabs) == 4

        extra = _make_project(tmp_path, "Extra", [f1])
        app.open_project_file(extra)
        assert len(app._project_tabs) == 5
        assert app.current_project == extra
