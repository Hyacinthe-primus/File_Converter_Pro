import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
HELPER_NAMES = [
    "_ConversionCancelled",
    "_PDF_TO_WORD_MODE_DEFAULT",
    "_PDF_TO_WORD_MODES",
    "_convert_docx_to_pdf",
    "_convert_image_to_pdf",
    "_convert_pdf_to_docx",
    "_merge_docx",
    "_merge_images_to_pdf",
    "_merge_pdfs",
    "_normalise_pdf_to_word_mode",
    "_raise_if_cancelled",
    "_solid_fitz_fallback",
    "_sort_files",
    "_temporary_docx_path",
]


def _run_probe(import_name: str, forbidden: set[str]) -> None:
    code = "\n".join(
        [
            "import sys",
            f"sys.path.insert(0, {str(SRC)!r})",
            f"import {import_name}",
            f"forbidden = {forbidden!r}",
            "loaded = sorted(",
            "    name for name in sys.modules",
            "    if name in forbidden or name.startswith('PySide6')",
            ")",
            "assert not loaded, loaded",
        ]
    )
    subprocess.run([sys.executable, "-c", code], cwd=ROOT, check=True, capture_output=True, text=True)


def _is_forbidden(name: str) -> bool:
    if name == "context_menu.window" or name.startswith("context_menu.window."):
        return True
    if name == "app.mixins" or name.startswith("app.mixins."):
        return True
    return name.split(".", 1)[0] in {"PySide6", "config", "dialogs", "widgets", "tasks", "converter"}


def test_conversion_helpers_import_does_not_load_ui_or_application_modules():
    _run_probe(
        "context_menu.conversion_helpers",
        {"config", "dialogs", "widgets", "context_menu.window", "app.mixins.pdf_to_word", "tasks", "converter"},
    )


def test_watcher_import_does_not_load_window_or_pyside6():
    _run_probe(
        "tasks.watcher",
        {"config", "dialogs", "widgets", "context_menu.window", "app.mixins.pdf_to_word", "converter"},
    )


def test_conversion_helpers_has_no_forbidden_imports():
    tree = ast.parse((SRC / "context_menu" / "conversion_helpers.py").read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names = [node.module]
        else:
            continue
        found.extend(name for name in names if _is_forbidden(name))

    assert found == []


def test_window_exposes_compatibility_helpers_and_identity():
    import context_menu.conversion_helpers as conversion_helpers
    import context_menu.window as window

    for name in HELPER_NAMES:
        assert hasattr(window, name), name
        if name != "_convert_pdf_to_docx":
            assert getattr(window, name) is getattr(conversion_helpers, name), name

    assert window._ConversionCancelled is conversion_helpers._ConversionCancelled
    assert window._convert_image_to_pdf is conversion_helpers._convert_image_to_pdf
    assert window._convert_pdf_to_docx is not conversion_helpers._convert_pdf_to_docx


def test_window_wildcard_import_restores_public_api():
    import context_menu.window as window

    namespace = {}
    exec("from context_menu.window import *", namespace)

    for name in ("AUTO_CLOSE_DELAY_MS", "ConversionThread", "QuickConvertWindow", "run_context_menu"):
        assert namespace[name] is getattr(window, name)


def test_quick_convert_thread_uses_window_compatibility_helpers(monkeypatch, tmp_path):
    import context_menu.window as window

    src = tmp_path / "image.png"
    src.write_bytes(b"image")
    calls = []
    monkeypatch.setattr(window, "_load_quick_config", lambda: {})
    monkeypatch.setattr(window, "_convert_image_to_pdf", lambda *args: calls.append(args))
    thread = window.ConversionThread([str(src)], "image_to_pdf")

    thread.run()

    assert calls == [(str(src), str(tmp_path))]


def test_watcher_resolves_conversion_helpers_from_non_ui_module(monkeypatch, tmp_path):
    import context_menu.conversion_helpers as conversion_helpers
    from tasks import watcher

    src = tmp_path / "image.png"
    src.write_bytes(b"image")
    out_dir = tmp_path / "out"
    calls = []
    monkeypatch.setattr(conversion_helpers, "_convert_image_to_pdf", lambda *args: calls.append(args))

    watcher._run_conversion("image_to_pdf", str(src), str(out_dir), ocr=False)

    assert calls == [(str(src), str(out_dir))]
