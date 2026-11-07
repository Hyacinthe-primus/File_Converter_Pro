"""Asset directory layout regressions."""

from pathlib import Path

from utils import SRC_DIR


def test_sfx_and_icons_live_under_assets():
    assets = SRC_DIR / "Assets"

    assert (assets / "icons" / "pdf.ico").is_file()
    assert (assets / "icons" / "template.ico").is_file()
    assert (assets / "SFX" / "notif.mp3").is_file()
    assert (assets / "SFX" / "conversion_done.ogg").is_file()
    assert (assets / "fonts" / "SF-Pro-Display-Medium.ttf").is_file()
    assert not (SRC_DIR / "icons").exists()
    assert not (SRC_DIR / "SFX").exists()
    assert not (SRC_DIR / "fonts").exists()


def test_file_icons_resolve_from_assets_icons():
    from app.mixins.file_management import FileManagementMixin

    class Harness(FileManagementMixin):
        def __init__(self):
            self.loaded = None

        def get_resource_path(self, relative_path):
            return str(SRC_DIR / relative_path)

        def _load_icon(self, icon_path, fallback):
            self.loaded = (Path(icon_path), fallback)
            return icon_path

    harness = Harness()
    harness.get_file_icon("document.pdf")

    assert harness.loaded[0] == SRC_DIR / "Assets" / "icons" / "pdf.ico"
    assert harness.loaded[1] == "📄"


def test_achievement_sounds_resolve_from_assets_sfx():
    from achievements.achievements_system import AchievementSystem

    class Harness:
        def get_resource_path(self, relative_path):
            return str(SRC_DIR / relative_path)

    path = AchievementSystem.get_sound_path(Harness(), "notif.mp3")

    assert Path(path) == SRC_DIR / "Assets" / "SFX" / "notif.mp3"


def test_quick_check_expects_nested_asset_directories():
    from quick_check import CHECKS_RESOURCES

    assert ("Assets/SFX/", "_internal/Assets/SFX", "dir") in CHECKS_RESOURCES
    assert ("Assets/icons/", "_internal/Assets/icons", "dir") in CHECKS_RESOURCES
    assert ("Assets/fonts/", "_internal/Assets/fonts", "dir") in CHECKS_RESOURCES
    assert all(source not in {"SFX/", "icons/", "fonts/"} for source, _target, _kind in CHECKS_RESOURCES)


def test_packaging_collects_only_the_assets_tree():
    spec = (SRC_DIR.parent / "packaging" / "build.spec").read_text(encoding="utf-8")

    assert "('../src/Assets', 'Assets')" in spec
    assert "../src/SFX" not in spec
    assert "../src/icons" not in spec
    assert "../src/fonts" not in spec
