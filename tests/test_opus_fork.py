"""
NAVI-KIND: TOOL
NAVI-PURPOSE: Propose audio_to_opus for File Converter Pro (fork) by patching registry,
             formats, labels, installer registry, optimizer, in-app dialog.
"""
import sys, os, subprocess
from pathlib import Path

ROOT = Path("/root/.hermes/cache/scratch/fcp")
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

fails = []


def check(name, fn):
    try:
        fn()
        print(f"  ok   {name}")
    except AssertionError as e:
        print(f"  FAIL {name}: {e}")
        fails.append(name)
    except Exception as e:
        print(f"  ERR  {name}: {type(e).__name__}: {e}")
        fails.append(name)


def test_registry_has_opus():
    """registry.py has no heavy imports, so load it standalone."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "fcp_registry_standalone", SRC / "converter" / "registry.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.CATEGORY_MAP["audio_to_opus"] == "audio", mod.CATEGORY_MAP.get("audio_to_opus")
    assert mod.DISPATCH["audio_to_opus"] == ("_ffmpeg_convert", "opus"), mod.DISPATCH.get("audio_to_opus")


def test_context_menu_map_offers_opus_from_mp3():
    from context_menu.formats import CONVERSION_MAP, LABELS
    assert "audio_to_opus" in CONVERSION_MAP["mp3"], CONVERSION_MAP["mp3"]
    assert LABELS["audio_to_opus"] == "Audio → OPUS", LABELS.get("audio_to_opus")


def test_context_menu_map_round_trip():
    """opus -> mp3 and mp3 -> opus both offered."""
    from context_menu.formats import CONVERSION_MAP
    assert "audio_to_opus" in CONVERSION_MAP["mp3"]
    assert "audio_to_mp3" in CONVERSION_MAP["opus"], CONVERSION_MAP.get("opus")


def test_dispatch_engine_accepts_opus():
    """Import the registry tables directly; converters.py pulls heavy deps."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "fcp_registry_under_test", SRC / "converter" / "registry.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert "audio_to_opus" in mod.DISPATCH, "audio_to_opus not in DISPATCH"
    assert mod.DISPATCH["audio_to_opus"][1] == "opus", mod.DISPATCH["audio_to_opus"]
    assert mod.CATEGORY_MAP["audio_to_opus"] == "audio"


def test_ffmpeg_has_opus_encoder():
    """Locate ffmpeg without importing the app (avoids heavy deps)."""
    import shutil

    ff = shutil.which("ffmpeg")
    assert ff, "ffmpeg not on PATH on this host"
    out = subprocess.run([ff, "-hide_banner", "-encoders"], capture_output=True, text=True)
    assert "libopus" in out.stdout, "libopus encoder missing from ffmpeg build"


def test_installer_registers_mp3_subcommand():
    iss = (ROOT / "packaging" / "setup.iss").read_text(encoding="utf-8", errors="replace")
    block = iss.split("Ext = 'mp3' then begin", 1)[1].split("end else if Ext = 'mp4'", 1)[0]
    assert "audio_to_opus" in block, "mp3 block has no opus subcommand"
    assert "OPUS" in block.upper(), "no OPUS menu label in mp3 block"


def test_opus_input_registered_for_cleanup():
    iss = (ROOT / "packaging" / "setup.iss").read_text(encoding="utf-8", errors="replace")
    assert "DeleteContextMenuForExtension('opus')" in iss


def test_opus_preset_present():
    src = (SRC / "converter" / "mixins" / "media_converters.py").read_text(encoding="utf-8")
    assert '"opus"' in src, "no opus entry in AUDIO_PRESETS"


def test_opus_in_app_audio_extension_lists():
    hits = []
    for rel in [
        "app/ui.py",
        "app/mixins/file_management.py",
        "app/mixins/optimization.py",
        "advanced_conversions.py",
    ]:
        txt = (SRC / rel).read_text(encoding="utf-8")
        if ".opus" in txt:
            hits.append(rel)
    assert hits, ".opus missing from every in-app audio extension list"


def test_opus_not_a_conversion_label_collision():
    """Load formats.py standalone (imports PySide6-free module only)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "fcp_formats_standalone", SRC / "context_menu" / "formats.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.LABELS["audio_to_ogg"] == "Audio → OGG"
    assert mod.LABELS["audio_to_opus"] != mod.LABELS["audio_to_ogg"]
    assert "audio_to_opus" in mod.CONVERSION_MAP["mp3"]
    assert "audio_to_mp3" in mod.CONVERSION_MAP["opus"]


if __name__ == "__main__":
    print("File Converter Pro -- audio_to_opus fork checks")
    check("registry: CATEGORY_MAP + DISPATCH", test_registry_has_opus)
    check("context menu: mp3 -> opus offered", test_context_menu_map_offers_opus_from_mp3)
    check("context menu: opus -> mp3 round trip", test_context_menu_map_round_trip)
    check("engine dispatch accepts audio_to_opus", test_dispatch_engine_accepts_opus)
    check("ffmpeg exposes libopus encoder", test_ffmpeg_has_opus_encoder)
    check("installer: mp3 subcommand registered", test_installer_registers_mp3_subcommand)
    check("installer: opus cleanup registered", test_opus_input_registered_for_cleanup)
    check("media_converters: opus preset", test_opus_preset_present)
    check("app: .opus in audio extension lists", test_opus_in_app_audio_extension_lists)
    check("labels: no collision with ogg", test_opus_not_a_conversion_label_collision)
    print()
    if fails:
        print(f"FAILED ({len(fails)}): {fails}")
        sys.exit(1)
    print("ALL CHECKS PASSED")
