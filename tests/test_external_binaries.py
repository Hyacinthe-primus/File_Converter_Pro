"""Tests for external_binaries config fallback resolution."""

import os
import tempfile

import pytest

import external_binaries as eb


@pytest.fixture(autouse=True)
def _clean_config_cache(monkeypatch):
    """Point at a scratch config file and reset the module cache."""
    monkeypatch.setenv("FCP_EXTERNAL_BINARIES_CONF", str(TEST_CONF))
    eb._reset_cache()
    yield
    eb._reset_cache()


def _write_conf(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".conf")
    os.write(fd, content.encode("utf-8"))
    os.close(fd)
    return path


def _make_file(path) -> str:
    os.makedirs(os.path.dirname(str(path)), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"MZ")
    return str(path)


def _norm(path) -> str:
    return os.path.normpath(str(path))


class _FakeWhich:
    """Stand-in for shutil with a name -> path map (missing => None)."""

    def __init__(self, results: dict):
        self._results = results

    def which(self, name: str):
        return self._results.get(name)


class _FakeGlob:
    """Stand-in for glob with a pattern -> matches map."""

    def __init__(self, results: dict):
        self._results = results

    def glob(self, pattern: str):
        return self._results.get(pattern, [])


TEST_CONF = _write_conf("")


def test_config_file_exists_in_repo():
    """The shipped config file exists next to the app."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "external_binaries.conf")
    assert os.path.isfile(path)


def test_empty_values_return_none():
    """Empty config values must keep automatic detection (return None)."""
    assert eb.get_config_path() is not None
    for key in ("ffmpeg", "ffprobe", "ghostscript", "imagemagick", "libreoffice", "wkhtmltopdf", "pandoc"):
        assert eb.get_configured_binary(key) is None


def test_missing_config_file_returns_none(monkeypatch):
    monkeypatch.setenv("FCP_EXTERNAL_BINARIES_CONF", os.path.join(tempfile.gettempdir(), "does_not_exist.conf"))
    eb._reset_cache()
    assert eb.get_config_path() is None
    assert eb.load_config() == {}
    assert eb.get_configured_binary("ffmpeg") is None


def test_configured_existing_path_is_returned(tmp_path):
    fake = tmp_path / "ffmpeg.exe"
    fake.write_bytes(b"MZ")
    conf = _write_conf(f"[binaries]\nffmpeg = {fake}\n")
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("FCP_EXTERNAL_BINARIES_CONF", conf)
    eb._reset_cache()
    try:
        assert eb.get_configured_binary("ffmpeg") == str(fake)
    finally:
        monkeypatch.undo()
        os.remove(conf)
        eb._reset_cache()


def test_configured_missing_path_returns_none(tmp_path):
    conf = _write_conf(f"[binaries]\nffmpeg = {tmp_path / 'nope.exe'}\n")
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("FCP_EXTERNAL_BINARIES_CONF", conf)
    eb._reset_cache()
    try:
        assert eb.get_configured_binary("ffmpeg") is None
    finally:
        monkeypatch.undo()
        os.remove(conf)
        eb._reset_cache()


@pytest.mark.skipif(os.name != "nt", reason="config uses Windows backslash relative paths")
def test_relative_path_resolved_against_app_root(tmp_path):
    app_root = tmp_path / "app_root"
    fake = app_root / "fake_dir" / "gs.exe"
    fake.parent.mkdir(parents=True)
    fake.write_bytes(b"MZ")
    # Place the config inside a "config" subfolder of the app root.
    conf_dir = app_root / "config"
    conf_dir.mkdir(parents=True)
    conf = conf_dir / "external_binaries.conf"
    conf.write_text("[binaries]\nghostscript = fake_dir\\gs.exe\n", encoding="utf-8")
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("FCP_EXTERNAL_BINARIES_CONF", str(conf))
    eb._reset_cache()
    try:
        assert eb.get_configured_binary("ghostscript") == str(fake)
    finally:
        monkeypatch.undo()
        eb._reset_cache()


def test_env_var_expansion_in_path(tmp_path):
    fake = tmp_path / "bin" / "ffmpeg.exe"
    fake.parent.mkdir()
    fake.write_bytes(b"MZ")
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("FCP_TEST_EB", str(tmp_path))
    conf = _write_conf(f"[binaries]\nffmpeg = %FCP_TEST_EB%{os.sep}bin{os.sep}ffmpeg.exe\n")
    monkeypatch.setenv("FCP_EXTERNAL_BINARIES_CONF", conf)
    eb._reset_cache()
    try:
        assert eb.get_configured_binary("ffmpeg") == str(fake)
    finally:
        monkeypatch.delenv("FCP_TEST_EB")
        monkeypatch.undo()
        os.remove(conf)
        eb._reset_cache()


def test_resolve_nothing_found_returns_none(monkeypatch):
    """With no PATH match, no common dirs hit, and no config, resolve returns None."""
    monkeypatch.setattr(eb, "shutil", _FakeWhich({}))
    monkeypatch.setattr(eb, "glob", _FakeGlob({}))
    assert eb.resolve_binary("ffmpeg") is None
    assert eb.locate_binary("ffmpeg") == (None, None)


def test_resolve_prefers_path(monkeypatch, tmp_path):
    """A PATH hit beats a valid config entry."""
    on_path = _make_file(tmp_path / "ffmpeg.exe")
    conf = _write_conf(f"[binaries]\nffmpeg = {tmp_path / 'configured.exe'}\n")
    monkeypatch.setenv("FCP_EXTERNAL_BINARIES_CONF", conf)
    monkeypatch.setattr(eb, "shutil", _FakeWhich({"ffmpeg": on_path}))
    monkeypatch.setattr(eb, "glob", _FakeGlob({}))
    eb._reset_cache()
    try:
        assert _norm(eb.resolve_binary("ffmpeg")) == _norm(on_path)
        assert _norm(eb.locate_binary("ffmpeg")[0]) == _norm(on_path)
        assert eb.locate_binary("ffmpeg")[1] == "system PATH"
    finally:
        monkeypatch.undo()
        os.remove(conf)
        eb._reset_cache()


def test_resolve_checks_app_local(monkeypatch, tmp_path):
    """Ghostscript app-local install dir is found when PATH has nothing."""
    app_data = tmp_path / "app_data"
    fake = _make_file(app_data / "ghostscript" / "bin" / "gswin64c.exe")
    monkeypatch.setattr(eb, "shutil", _FakeWhich({}))
    monkeypatch.setattr(eb, "glob", _FakeGlob({}))
    result = eb.resolve_binary("ghostscript", app_data_dir=str(app_data))
    assert _norm(result) == _norm(fake)
    assert _norm(eb.locate_binary("ghostscript", app_data_dir=str(app_data))[0]) == _norm(fake)


def test_resolve_checks_common_dirs(monkeypatch, tmp_path):
    """Common system dirs (with glob patterns) are consulted after app-local."""
    fake = _make_file(tmp_path / "gswin64c.exe")
    pattern = r"C:\Program Files\gs\gs*\bin\gswin64c.exe"
    monkeypatch.setattr(eb, "shutil", _FakeWhich({}))
    monkeypatch.setattr(eb, "glob", _FakeGlob({pattern: [fake]}))
    assert _norm(eb.resolve_binary("ghostscript")) == _norm(fake)
    assert _norm(eb.locate_binary("ghostscript")[0]) == _norm(fake)
    assert eb.locate_binary("ghostscript")[1] == "common dirs"


def test_resolve_falls_back_to_config(monkeypatch, tmp_path):
    """Config file path is the final fallback when all detection fails."""
    configured = _make_file(tmp_path / "soffice.exe")
    conf = _write_conf(f"[binaries]\nlibreoffice = {configured}\n")
    monkeypatch.setenv("FCP_EXTERNAL_BINARIES_CONF", conf)
    monkeypatch.setattr(eb, "shutil", _FakeWhich({}))
    monkeypatch.setattr(eb, "glob", _FakeGlob({}))
    eb._reset_cache()
    try:
        assert _norm(eb.resolve_binary("libreoffice")) == _norm(configured)
        assert _norm(eb.locate_binary("libreoffice")[0]) == _norm(configured)
        assert eb.locate_binary("libreoffice")[1] == "config file"
    finally:
        monkeypatch.undo()
        os.remove(conf)
        eb._reset_cache()


def test_resolve_unknown_tool_uses_config_only(monkeypatch, tmp_path):
    """Tools not in TOOLS can still be resolved through the config file."""
    fake = _make_file(tmp_path / "custom_tool.exe")
    conf = _write_conf(f"[binaries]\ncustom_tool = {fake}\n")
    monkeypatch.setenv("FCP_EXTERNAL_BINARIES_CONF", conf)
    monkeypatch.setattr(eb, "shutil", _FakeWhich({"custom_tool": str(tmp_path / "other.exe")}))
    monkeypatch.setattr(eb, "glob", _FakeGlob({}))
    eb._reset_cache()
    try:
        assert _norm(eb.resolve_binary("custom_tool")) == _norm(fake)
        assert _norm(eb.locate_binary("custom_tool")[0]) == _norm(fake)
        assert eb.locate_binary("custom_tool")[1] == "config file"
    finally:
        monkeypatch.undo()
        os.remove(conf)
        eb._reset_cache()
