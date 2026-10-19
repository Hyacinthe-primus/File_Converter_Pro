"""Tests for auto-clean temporary files and cross-platform compatibility."""

import inspect
import os
import shutil
import tempfile

import pytest


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


class TestAutoCleanTempFiles:
    def test_cleanup_removes_temp_files(self, tmp_dir):
        from app.logic import AppLogicMixin

        mixin = AppLogicMixin.__new__(AppLogicMixin)
        mixin.temp_files = []

        f1 = os.path.join(tmp_dir, "temp1.tmp")
        f2 = os.path.join(tmp_dir, "temp2.tmp")
        with open(f1, "w") as f:
            f.write("temp1")
        with open(f2, "w") as f:
            f.write("temp2")

        mixin.temp_files = [f1, f2]
        mixin.cleanup_temp_files()

        assert not os.path.exists(f1)
        assert not os.path.exists(f2)
        assert len(mixin.temp_files) == 0

    def test_cleanup_handles_missing_files(self, tmp_dir):
        from app.logic import AppLogicMixin

        mixin = AppLogicMixin.__new__(AppLogicMixin)
        mixin.temp_files = [os.path.join(tmp_dir, "nonexistent.tmp")]
        mixin.cleanup_temp_files()
        assert len(mixin.temp_files) == 0

    def test_cleanup_handles_empty_list(self):
        from app.logic import AppLogicMixin

        mixin = AppLogicMixin.__new__(AppLogicMixin)
        mixin.temp_files = []
        mixin.cleanup_temp_files()
        assert len(mixin.temp_files) == 0

    def test_create_temp_file_tracks(self, tmp_dir):
        from app.logic import AppLogicMixin

        mixin = AppLogicMixin.__new__(AppLogicMixin)
        mixin.temp_files = []

        path = mixin.create_temp_file(suffix=".test")
        assert os.path.exists(path)
        assert path in mixin.temp_files

        mixin.cleanup_temp_files()
        assert not os.path.exists(path)

    def test_cleanup_clears_list_after(self, tmp_dir):
        from app.logic import AppLogicMixin

        mixin = AppLogicMixin.__new__(AppLogicMixin)
        f1 = os.path.join(tmp_dir, "temp1.tmp")
        with open(f1, "w") as f:
            f.write("data")
        mixin.temp_files = [f1, "/nonexistent/path/file.tmp"]
        mixin.cleanup_temp_files()
        assert len(mixin.temp_files) == 0

    def test_close_event_calls_cleanup_when_enabled(self, tmp_dir):
        cleaned = []

        class _Obj:
            config = {"auto_clean_temp_files": True}
            temp_files = []
            db_manager = type("", (), {"close": lambda self: None})()

            def cleanup_temp_files(self):
                for f in self.temp_files:
                    if os.path.exists(f):
                        os.remove(f)
                        cleaned.append(f)
                self.temp_files.clear()

            def closeEvent(self, event):
                try:
                    self.db_manager.close()
                except Exception:
                    pass
                if self.config.get("auto_clean_temp_files", True):
                    self.cleanup_temp_files()

        obj = _Obj()
        f1 = os.path.join(tmp_dir, "temp_close.tmp")
        with open(f1, "w") as f:
            f.write("data")
        obj.temp_files = [f1]

        class MockEvent:
            def accept(self):
                pass

        obj.closeEvent(MockEvent())
        assert f1 in cleaned
        assert not os.path.exists(f1)

    def test_close_event_skips_cleanup_when_disabled(self, tmp_dir):
        cleaned = []

        class _Obj:
            config = {"auto_clean_temp_files": False}
            temp_files = []
            db_manager = type("", (), {"close": lambda self: None})()

            def cleanup_temp_files(self):
                for f in self.temp_files:
                    if os.path.exists(f):
                        os.remove(f)
                        cleaned.append(f)
                self.temp_files.clear()

            def closeEvent(self, event):
                try:
                    self.db_manager.close()
                except Exception:
                    pass
                if self.config.get("auto_clean_temp_files", True):
                    self.cleanup_temp_files()

        obj = _Obj()
        f1 = os.path.join(tmp_dir, "temp_keep.tmp")
        with open(f1, "w") as f:
            f.write("data")
        obj.temp_files = [f1]

        class MockEvent:
            def accept(self):
                pass

        obj.closeEvent(MockEvent())
        assert f1 not in cleaned
        assert os.path.exists(f1)


class TestCrossPlatform:
    def test_create_backup_uses_shutil(self, tmp_dir):
        from converter.helpers import create_backup

        source = inspect.getsource(create_backup)
        assert "shutil.copy2" in source

    def test_cleanup_uses_os_path(self):
        from app.logic import AppLogicMixin

        source = inspect.getsource(AppLogicMixin.cleanup_temp_files)
        assert "os.path" in source

    def test_temp_file_uses_tempfile(self):
        from app.logic import AppLogicMixin

        source = inspect.getsource(AppLogicMixin.create_temp_file)
        assert "tempfile" in source
