"""Architecture / structural tests.

These guard invariants that have repeatedly broken in this codebase:

- Translation keys: every key in the source language (fr.json) must exist in
  every other language file, and every translate_text("...") literal that
  looks like a named key must exist in fr.json.
- Mixin composition: every mixin class in app/mixins (plus AppUIMixin /
  AppLogicMixin) must be part of the FileConverterApp MRO.
- Theme styling: every widget object name set in Python must have a matching
  #selector in both the dark and light stylesheets.
"""

import ast
import importlib
import json
import os
import pkgutil
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")

EXCLUDED_DIRS = {
    ".git",
    ".github",
    ".pytest_cache",
    ".ruff_cache",
    ".venv-wsl",
    ".vscode",
    "__pycache__",
    "dist",
    "tests",
    "Wiki",
}

LANG_FILES = [
    "languages/fr.json",
    "languages/en.json",
    "languages/zh.lang",
    "languages/ru.lang",
    "languages/it.lang",
    "languages/en-revisited.lang",
    "languages/blank.lang",
]

QSS_FILES = ["styles/themes/dark/style.qss", "styles/themes/light/style.qss"]

# Object names intentionally without a #selector in any stylesheet (styled via
# a base-class selector in inline stylesheets, via dynamic stylesheets in code,
# or not styled at all).
QSS_ALLOWLIST = {
    "BtnCancel",
    "BtnOK",
    "ContactGroup",
    "ContactLinks",
    "KofiBtn",
    "TemplateApplyBtn",
    "TemplateCloseBtn",
    "TemplateDeleteBtn",
    "TemplateEditBtn",
    "TermsCheckBox",
    "TermsTextBrowser",
    "container",
}


def iter_python_files():
    for entry in sorted(os.listdir(SRC)):
        path = os.path.join(SRC, entry)
        if os.path.isdir(path):
            if entry in EXCLUDED_DIRS:
                continue
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
                for f in files:
                    if f.endswith(".py"):
                        yield os.path.join(root, f)
        elif entry.endswith(".py"):
            yield path


def translate_text_literals():
    """All constant string literals passed to translate_text(...) in code."""
    keys = set()
    for path in iter_python_files():
        with open(path, encoding="utf-8") as fh:
            try:
                tree = ast.parse(fh.read())
            except SyntaxError:
                continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "translate_text" and node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        keys.add(arg.value)
    return keys


def load_lang_keys():
    keys = {}
    for f in LANG_FILES:
        with open(os.path.join(SRC, f), encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict) and isinstance(data.get("strings"), dict):
            data = data["strings"]
        keys[f] = set(data.keys())
    return keys


def collect_object_names():
    names = set()
    for path in iter_python_files():
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        for m in re.finditer(r"setObjectName\(\s*[\"']([^\"']+)[\"']", text):
            names.add(m.group(1))
    return names


def inline_stylesheet_text():
    """Concatenated text of every setStyleSheet(...) string literal in code."""
    pattern = re.compile(
        r'setStyleSheet\(\s*('
        r'"""(?:[^"\\]|\\.)*?"""'
        r"|'''(?:[^'\\]|\\.)*?'''"
        r'|"(?:[^"\\\n]|\\.)*"'
        r"|'(?:[^'\\\n]|\\.)*'"
        r")",
        re.DOTALL,
    )
    parts = []
    for path in iter_python_files():
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        for m in pattern.finditer(text):
            raw = m.group(1)
            parts.append(raw[3:-3] if raw[:3] in ('"""', "'''") else raw[1:-1])
    return "\n".join(parts)


def all_styling_text():
    """All text that can carry a #selector for a widget: theme QSS files,
    any other .qss file, inline setStyleSheet strings, and full Python sources
    (which also contain f-string / variable stylesheets)."""
    parts = []
    for qss_file in QSS_FILES:
        parts.append(open(os.path.join(SRC, qss_file), encoding="utf-8").read())
    for root, dirs, files in os.walk(os.path.join(SRC, "styles")):
        dirs[:] = [d for d in dirs if d not in ("__pycache__",)]
        for f in files:
            if f.endswith(".qss"):
                parts.append(open(os.path.join(root, f), encoding="utf-8").read())
    parts.append(inline_stylesheet_text())
    for path in iter_python_files():
        parts.append(open(path, encoding="utf-8").read())
    return "\n".join(parts)


class TestTranslationConsistency:
    def test_fr_keys_present_in_all_language_files(self):
        fr = json.load(open(os.path.join(SRC, "languages/fr.json"), encoding="utf-8"))
        if isinstance(fr, dict) and isinstance(fr.get("strings"), dict):
            fr = fr["strings"]
        others = {f for f in LANG_FILES if f != "languages/fr.json"}
        for f in sorted(others):
            keys = load_lang_keys()[f]
            missing = sorted(set(fr) - keys)
            assert not missing, f"{f} is missing {len(missing)} key(s): {missing[:10]}"

    def test_named_code_keys_exist_in_fr(self):
        fr = load_lang_keys()["languages/fr.json"]
        missing = sorted(k for k in translate_text_literals() if re.fullmatch(r"[a-z_][a-z0-9_]*", k) and k not in fr)
        assert not missing, f"named translation keys missing from fr.json: {missing}"


class TestMixinComposition:
    def test_all_mixins_in_app_mro(self):
        from app import FileConverterApp

        mixins = set()
        import app.mixins as mixins_pkg

        for _, name, _ in pkgutil.iter_modules(mixins_pkg.__path__):
            module = importlib.import_module(f"app.mixins.{name}")
            for attr in vars(module).values():
                if isinstance(attr, type) and attr.__name__.endswith("Mixin") and attr.__module__ == module.__name__:
                    mixins.add(attr)

        from app.logic import AppLogicMixin
        from app.ui import AppUIMixin

        mixins.update({AppLogicMixin, AppUIMixin})

        missing = [
            cls.__name__
            for cls in sorted(mixins, key=lambda c: c.__name__)
            if not issubclass(FileConverterApp, cls)
        ]
        assert not missing, f"mixins not composed into FileConverterApp: {missing}"

    def test_mixin_methods_resolvable(self):
        from app import FileConverterApp
        from app.mixins import project_management, theme_language

        for mod, names in (
            (project_management, ["open_project_file", "_close_project_tab", "MAX_PROJECT_TABS"]),
            (theme_language, ["toggle_language", "update_texts"]),
        ):
            for name in names:
                assert hasattr(FileConverterApp, name), f"{mod.__name__}.{name} not reachable on FileConverterApp"


class TestQssObjectNames:
    def test_every_objectname_has_a_selector(self):
        names = collect_object_names() - QSS_ALLOWLIST
        styling = all_styling_text()
        unstyled = sorted(n for n in names if f"#{n}" not in styling)
        assert not unstyled, f"no #selector found anywhere for: {unstyled}"
