# Contributing to File Converter Pro

Thanks for taking the time to contribute! This project is maintained solo alongside studies, so every bit of help matters.

---

## What you can contribute

### 🌐 Translations *(easiest entry point)*

No coding required. Create a `.lang` file (UTF-8 JSON) and place it in `languages/`. The app auto-detects it on next launch.

en-revisited.lang is an example file for reference. Use blank.lang as your starting point for new translations.

**Format:**

```json
{
  "meta": {
    "code":        "DE",
    "name":        "Deutsch",
    "author":      "Your Name",
    "version":     "1.0",
    "created":     "2026-01-01",
    "description": "German translation"
  },
  "strings": {
    "Paramètres": "Einstellungen",
    "Fermer":     "Schließen"
  }
}
```

Open an issue with your `.lang` file attached, or submit a pull request directly.

---

### Bug Reports

Use the [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) template. Please include:

- Windows version (10 / 11, build number if possible)
- Input format → Output format attempted
- Whether Office, LibreOffice, Pandoc, or MiKTeX are installed
- Error message or screenshot if applicable

---

### 💡 Feature Requests

Check [ROADMAP.md](ROADMAP.md) first, the feature may already be planned. If not, open an issue using the [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) template.

---

###  Simple Code Contributions

Small bug fixes, typo corrections, minor UI tweaks, adding a missing format to an existing pipeline  these are welcome as direct PRs.

1. Fork the repo
2. Make your changes (creating a branch is optional but recommended: `git checkout -b fix/my-fix`)
3. Test on a **clean machine** if possible
4. Open a pull request with a clear description of what changed and why

**A few things to keep in mind:**

- Comments and docstrings must be in **English**
- Keep changes focused, one PR per fix
- If you're touching a conversion pipeline, mention which fallback chain is affected
- The project uses `PySide6` (Qt6) not PyQt5

---

### Complex Contributions *(open an issue first)*

Some contributions involve significant architectural changes. **Before writing any code**, open an issue to discuss scope and feasibility. This avoids wasted effort on both sides.

This applies to things like:

- **Linux / macOS port** - several parts of the codebase are Windows-specific by design:
  - COM automation (`comtypes`) for Word, Excel, PowerPoint → PDF - no equivalent on Linux without Office
  - Dark mode detection reads directly from the Windows registry
  - PyInstaller packaging and Inno Setup installer are Windows-first
  - A Linux port would need platform guards throughout `config.py`, `app/ui.py`, `app/logic.py`, and all COM-dependent pipelines in `converter/converters.py`

- **New conversion formats:**  make sure the engine chain fits the existing multi-fallback pattern used in `converter/converters.py`. Discuss which libraries are involved and what happens on a clean machine with no optional tools.

- **New major features:** achievements system extensions, new dashboard charts, plugin system, etc. Check ROADMAP.md first; if it's already planned, coordinate to avoid overlap.

- **Build system changes:** PyInstaller spec, Inno Setup script, UPX config, PowerShell build scripts.

For these, **open an issue describing what you want to build and how** before writing code. I'll give feedback on whether/how it fits the project.

---

## Running from source

```bash
git clone https://github.com/Hyacinthe-primus/File_Converter_Pro.git
cd File_Converter_Pro
pip install -r requirements.txt
python main.py
```

See the [Developer section in README](README.md#-for-developers) for build instructions and all CLI flags.

---

## License

By contributing, you agree that your contributions will be licensed under the same [GPLv3 license](LICENSE.md) that covers the project.
