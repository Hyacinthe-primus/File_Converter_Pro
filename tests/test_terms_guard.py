"""Tests for Terms & Privacy enforcement, including the context-menu entry point."""

import sys

import pytest


def test_already_accepted_requires_both_flags():
    import main

    accepted = main.TermsGuard({"accepted_terms": True, "accepted_privacy": True}, None)
    assert accepted._already_accepted()

    partial = main.TermsGuard({"accepted_terms": True, "accepted_privacy": False}, None)
    assert not partial._already_accepted()

    missing = main.TermsGuard({}, None)
    assert not missing._already_accepted()


def test_enforce_records_acceptance(monkeypatch):
    from PySide6.QtWidgets import QDialog

    import main

    class FakeDialog:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def exec(self):
            return QDialog.Accepted

    saved = {}

    class FakeConfigManager:
        def save_config(self, config):
            saved.update(config)

    config = {"accepted_terms": False, "accepted_privacy": False, "language": "fr", "dark_mode": False}
    monkeypatch.setattr(main, "TermsAndPrivacyDialog", FakeDialog)

    main.TermsGuard(config, FakeConfigManager()).enforce()

    assert config["accepted_terms"] is True
    assert config["accepted_privacy"] is True
    assert "terms_acceptance_timestamp" in config
    assert "terms_reacceptance_timestamp" not in config
    assert saved["accepted_terms"] is True
    assert saved["accepted_privacy"] is True


def test_enforce_records_reacceptance_timestamp(monkeypatch):
    from PySide6.QtWidgets import QDialog

    import main

    class FakeDialog:
        def __init__(self, **kwargs):
            pass

        def exec(self):
            return QDialog.Accepted

    class FakeConfigManager:
        def save_config(self, config):
            pass

    config = {
        "accepted_terms": False,
        "accepted_privacy": False,
        "terms_acceptance_timestamp": "2026-01-01T00:00:00",
    }
    monkeypatch.setattr(main, "TermsAndPrivacyDialog", FakeDialog)

    main.TermsGuard(config, FakeConfigManager()).enforce()

    assert config["terms_acceptance_timestamp"] == "2026-01-01T00:00:00"
    assert "terms_reacceptance_timestamp" in config


def test_enforce_exits_when_refused(monkeypatch):
    from PySide6.QtWidgets import QDialog

    import main

    class FakeDialog:
        def __init__(self, **kwargs):
            pass

        def exec(self):
            return QDialog.Rejected

    saved = []

    class FakeConfigManager:
        def save_config(self, config):
            saved.append(config)

    config = {"accepted_terms": False, "accepted_privacy": False}
    monkeypatch.setattr(main, "TermsAndPrivacyDialog", FakeDialog)

    with pytest.raises(SystemExit):
        main.TermsGuard(config, FakeConfigManager()).enforce()

    assert not saved
    assert config["accepted_terms"] is False


def test_enforce_skips_dialog_when_already_accepted(monkeypatch):
    import main

    class ExplodingDialog:
        def __init__(self, **kwargs):
            raise AssertionError("dialog must not be shown when terms are already accepted")

    monkeypatch.setattr(main, "TermsAndPrivacyDialog", ExplodingDialog)

    main.TermsGuard({"accepted_terms": True, "accepted_privacy": True}, None).enforce()


def _fake_config_manager(config):
    class FakeConfigManager:
        def load_config(self):
            return dict(config)

    return FakeConfigManager()


def test_context_menu_blocked_when_terms_not_accepted(monkeypatch, tmp_path, qapp):
    import main

    source = tmp_path / "photo.png"
    source.write_bytes(b"png")

    calls = []

    class FakeGuard:
        def __init__(self, config, config_manager):
            calls.append("guard")
            assert config.get("accepted_terms", False) is False

        def enforce(self):
            calls.append("enforce")
            raise SystemExit(0)

    import context_menu.window as cm_window

    monkeypatch.setattr(main, "ConfigManager", lambda: _fake_config_manager({"use_system_theme": False}))
    monkeypatch.setattr(main, "TermsGuard", FakeGuard)
    monkeypatch.setattr(cm_window, "run_context_menu", lambda *a, **k: calls.append("convert"))
    monkeypatch.setattr(sys, "argv", ["main.py", "--context-menu", "--files", str(source)])

    with pytest.raises(SystemExit):
        main.main()

    assert calls == ["guard", "enforce"]
    assert "convert" not in calls


def test_context_menu_converts_after_acceptance(monkeypatch, tmp_path, qapp):
    import main

    source = tmp_path / "photo.png"
    source.write_bytes(b"png")

    calls = []

    class FakeGuard:
        def __init__(self, config, config_manager):
            calls.append("guard")

        def enforce(self):
            calls.append("enforce")

    import context_menu.window as cm_window

    monkeypatch.setattr(main, "ConfigManager", lambda: _fake_config_manager({"use_system_theme": False}))
    monkeypatch.setattr(main, "TermsGuard", FakeGuard)
    monkeypatch.setattr(
        cm_window,
        "run_context_menu",
        lambda files, conversion_type=None: calls.append(("convert", files, conversion_type)),
    )
    monkeypatch.setattr(sys, "argv", ["main.py", "--context-menu", "--files", str(source)])

    main.main()

    assert calls[0:2] == ["guard", "enforce"]
    assert calls[2] == ("convert", [str(source)], None)
