# File Converter Pro - Session Handoff

Last updated: 2026-11-06

## Repositories

- App: `C:\Users\hyaci\Documents\My Visual Studio Codes\All_Projects\File_Converter_App`
  - Remote: `https://github.com/Hyacinthe-primus/File_Converter_Pro.git`
  - Branch: `main`
  - Latest commit: `38aa724` (`feat: add custom image-to-ICO size setting`)
  - Recent security commits: `5175efd`, `fd4f650`, `b0fa220`, `da61d93`
- Themes: `C:\Users\hyaci\Documents\My Visual Studio Codes\All_Projects\FCP-themes`
  - Remote: `https://github.com/Hyacinthe-primus/FCP-themes.git`
  - Branch: `main`
  - Latest local commit: `e5fc75d` (`fix: keep category highlights readable`)
  - The GitHub Actions bot may add `chore: update themes index [skip ci]` commits after pushes.

## Current Git State

The app working tree has a large, intentionally uncommitted batch on top of `38aa724`. Do not commit any of it unless the user explicitly asks.

Modified tracked files:

- Docs/build: `README.md`, `packaging/build.ps1`, `packaging/build.spec`
- App/UI: `src/app/logic.py`, `src/dialogs/settings_dialog.py`, `src/dialogs/terms_dialog.py`, `src/main.py`, `src/qss_helpers.py`, `tests/test_terms_guard.py`
- Quick Convert/conversion: `src/context_menu/window.py`, `src/converter/helpers.py`, `src/app/mixins/pdf_to_word.py`
- Automation: `src/tasks/watcher.py`

Untracked files:

- `HANDOFF.md` (this file)
- `releases.md`
- `src/pdf_text.py`
- `tests/test_automation_pdf_to_word_mode.py`
- `tests/test_backup_exclusive.py`
- `tests/test_context_menu_backup.py`
- `tests/test_context_menu_image_pdf.py`
- `tests/test_context_menu_pdf_to_word_mode.py`
- `tests/test_terms_dialog_theme.py`

`src/styles/custom_themes/` is gitignored. The local `Kintsugi` theme has been updated but cannot be committed without changing `.gitignore`.

FCP-themes working tree is clean.

## Verification

Run from the app repo:

```powershell
python -m pytest -q
python -m ruff check src tests
python -m compileall -q src tests
```

This shell does not expose `python` on `PATH`; the Windows interpreter used for verification was:

```powershell
& "C:\Users\hyaci\AppData\Local\Programs\Python\Python313\python.exe" -m pytest -q
```

Last verified state (2026-11-06):

- **689 tests passed**
- Ruff clean
- `compileall` clean
- `git diff --check`: no whitespace errors; only pre-existing LF/CRLF warnings in the working tree

From FCP-themes:

```powershell
python scripts/build_themes.py --check
```

Last verified: **12 themes valid**.

## What Was Completed

### Quick Convert, PDF-to-Word, and automation hardening (2026-11-06)

- Backup creation was made collision-safe for Quick Convert:
  - `create_backup(..., overwrite=False)` now reserves paths with `os.open(..., O_CREAT | O_EXCL)`.
  - Quick Convert centralizes source backups before dispatch, deduplicates sources by canonical path, and disables the engine's duplicate backup.
  - `create_backup(..., overwrite=True)` retains the old overwrite behavior for existing engine/advanced callers.
  - Added `tests/test_backup_exclusive.py` and `tests/test_context_menu_backup.py`.
- Quick Convert image-to-PDF now supports HEIC/HEIF/AVIF through the existing `utils.image_formats.decodable_image_path()`:
  - Both single-image and merged-image Quick paths use the decodable path.
  - Watcher/Scheduler inherit the behavior when they call Quick helpers.
  - Added `tests/test_context_menu_image_pdf.py` with real generated HEIC/AVIF fixtures and temp-cleanup coverage.
- PDF-to-Word text-only fallback now mirrors the main app:
  - Reuses `PdfToWordMixin._solid_fitz_fallback()` through a lazy wrapper in `src/context_menu/window.py`.
  - Cancellation never triggers fallback.
- PDF-to-Word text-only output is transactional:
  - Primary extraction and fallback write to a temp `.docx` in the destination directory.
  - `os.replace()` commits only after success.
  - Existing destinations are preserved byte-for-byte when both attempts fail.
  - Temp names use `~fcp_pdf_word_` so Watcher ignores them.
  - Added/expanded coverage in `tests/test_context_menu_pdf_to_word_mode.py`.
- Watcher and Scheduler now honor the global `pdf_to_word_mode`:
  - Watcher reads `ConfigManager().load_config()` on every PDF-to-Word conversion; no startup cache.
  - Missing, invalid, empty, or unavailable config defaults to `with_images`.
  - Scheduler inherits through its existing Watcher `_run_conversion` import.
  - Added `tests/test_automation_pdf_to_word_mode.py`.

### Architecture audit findings (2026-11-06)

- The generic `AdvancedConverterEngine` and `converter.registry.DISPATCH` are genuinely shared across Main, Quick, Watcher, and Advanced.
- Special pipelines remain duplicated:
  - Quick and Watcher reuse Quick image/PDF/Word/merge helpers.
  - Main direct, Main batch, and Quick use different Word→PDF and PDF→Word fallback chains.
  - Main uses different merge implementations and output names (`fusion_*`) from Quick/Watcher (`merged_*`).
  - Main and automation have separate OCR implementations (`app.mixins.image_to_pdf` vs `tasks.ocr_helpers`).
- Watcher/Scheduler still import Quick helper functions from the Qt-containing `context_menu.window` module. Preserve this compatibility until a non-UI helper extraction is done.
- A P2 audit of `default_output_folder` was completed but not implemented: Quick Convert still always writes beside sources and does not honor the configured default folder.

### Security hardening and disclosure

- HTML-to-PDF local resources remain opt-in; approved resources must stay inside the HTML file's folder. pdfkit disables local-file access and JavaScript; ReportLab accepts only `data:` images; resource reads use an open-once containment check.
- WeasyPrint now uses `weasyprint.urls.URLFetcher` with only `http`, `https`, and `data` protocols and redirects disabled. Compatibility is verified against WeasyPrint 70.
- Notification PowerShell uses a fixed script with structured XML/JSON input, so untrusted notification text is never interpolated into PowerShell source or the command line.
- Legacy excluded notification operation labels map to canonical IDs (`protect_pdf`, `office_optimization`).
- Detailed patch notes moved out of `SECURITY.md` into:
  - `security_patches/patch1.md` - HTML-to-PDF local resource handling
  - `security_patches/patch2.md` - Notification PowerShell handling
- `SECURITY.md` now links to those patch notes and keeps the standard vulnerability-disclosure policy structure.

### External tools / WeasyPrint DLL directories

- Added `[directories]` support to `config/external_binaries.conf`, currently for `weasyprint_dll`.
- `external_binaries.resolve_directories()` applies this precedence:
  1. `WEASYPRINT_DLL_DIRECTORIES`
  2. non-empty INI `[directories] weasyprint_dll` (replaces built-in defaults)
  3. `DIRECTORY_DEFAULTS`: `C:\msys64\ucrt64\bin`, `C:\msys64\mingw64\bin`, `C:\Program Files\GTK3-Runtime Win64\bin`
- Directory values accept `%VAR%`, `~`, and relative paths (resolved against the app root); missing directories are ignored.
- `_import_weasyprint()` registers configured directories with `os.add_dll_directory()`, keeps the DLL directory cookies alive, prepends those directories to `PATH` for the import, then restores `PATH`.
- Added tests for INI override, env-var priority, and built-in defaults in `tests/test_external_binaries.py`.
- `packaging/build.spec` also bundles `DLLs/libffi*.dll` from the build interpreter (`libffi-8.dll` is present in `packaging/dist/FCP/_internal/`).

### Context-menu cancellation and HTML-to-PDF guard

- Quick Convert cancellation is cooperative via `threading.Event`:
  - `ConversionThread.cancel()` sets the event and calls `requestInterruption()`.
  - Checks run before each file, inside image/PDF/Word merge loops, and between PDF→DOCX fallback tiers.
  - Cancellation raises `_ConversionCancelled`; the thread emits `cancelled`.
- UI behavior: `Cancelling...` status, cancel button disabled, `_force_cancel_if_running()` calls `os._exit(0)` after `CANCEL_GRACE_MS = 5000` if the thread is still alive.
- `closeEvent` cancels a running worker and waits up to 3 seconds before forcing exit.
- Success auto-closes after 1.8 seconds; errors stay open with `Retry`/`Cancel`.
- Added `tests/test_context_menu_cancel.py` covering pre-start cancellation, remaining-file cancellation, and the Cancel button.
- `_html_to_pdf()` now rejects non-HTML sources before rendering:
  - Accepted: `.html`, `.htm`, `.xhtml`
  - Error: `HTML to PDF requires an HTML source (.html, .htm, .xhtml), not <ext>`
  - Regression test: `tests/test_converter_edge.py::test_html_to_pdf_rejects_non_html_source`.
- Frozen-mode correction: `resolve_binary("wkhtmltopdf")` uses the same `TOOLS["wkhtmltopdf"]` ToolSpec in source and frozen builds. Frozen finds and uses system-installed `C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe`; it does not bundle the tool. The earlier “frozen falls back to WeasyPrint” explanation was wrong.
- Correct command for PDF→HTML is `--conversion-type pdf_to_html` (single PyMuPDF/fitz engine), not `html_to_pdf`.

### PDF operations, templates, and protection

- PDF merge, Word merge, split, and protection now consume active template values:
  - merge order for PDF and Word
  - split method and pages-per-file
  - protection mode and permission checkboxes
- Word merge now composes files in the order returned by the merge-order dialog, not the original list order.
- Canceling the split dialog now returns `False` and stops the multi-file split loop.
- PDF protection now uses pypdf with AES-256 encryption, a generated owner password, configurable print/copy/modify permissions, and atomic temporary output.
- Protection dialog supports Basic and Advanced modes and exposes only the print/copy/modify permissions.
- Added template-consumption tests for PDF merge, Word merge, PDF split, and PDF protection.

### Office COM / temporary-file isolation

- PowerPoint COM conversion uses a per-conversion `TemporaryDirectory` instead of a shared temp filename.
- Concurrent PPTX/ODP conversions cannot overwrite or delete each other's intermediate files.
- Added concurrency and cleanup tests in `tests/test_pptx_temp_isolation.py`.

### UI polish

- Word-to-PDF Advanced Options now uses `AnimatedCheckBox`; the old custom QGroupBox indicator is hidden and the animated checkbox drives the group state.
- Merge-order choices now use `AnimatedCheckBox` widgets in an exclusive `QButtonGroup`, so one choice always stays selected.
- The protection Apply and merge buttons now use the shared `BtnOK` QSS style instead of inline green styles.
- `AnimatedCheckBox` gained `set_dark_mode()` for correct hand-painted colors and now sizes labels with the same 10pt font metrics used for painting, avoiding clipping in translated labels.

### Template semantic-key follow-ups

- App mixins, achievements, and template application now use canonical semantic keys such as `file_optimization` instead of legacy French labels.
- Default-template lookup accepts both canonical and legacy type names.
- Achievement template-category statistics continue to use the legacy storage keys for backward compatibility.
- Added tests for canonical/legacy template lookup, active-template keys, and achievement stat keys.
- Removed the obsolete `.fctheme` import-hint translation key and alias; multiline HTML-resource tooltips are preserved across languages.

### Dashboard theming

- Added `src/dashboard_theme.py`.
- Refactored `src/dashboard.py` to use theme palettes for cards, charts, tables, filters and controls.
- Added optional `[dashboard]` overrides in custom theme `metadata.ini`.
- Updated dark/light `dashboard.qss`.
- Added `tests/test_dashboard_theme.py`.

### Achievements theming

- Added `src/achievements/theme.py`.
- Added optional `src/styles/themes/dark/achievements.qss` and `light/achievements.qss`.
- Refactored:
  - `src/achievements/achievements_ui.py`
  - `src/achievements/achievements_popup.py`
  - `src/achievements/rank_popup.py`
- Added optional `achievements.qss` support for custom themes without requiring an app rebuild.
- Added `AchievementsPalette` keys for:
  - core colors
  - `font_family`
  - ring/progress/stat/card paint colors
  - tier, category and per-rank overrides
- Added `tests/test_achievements_theme.py`.

### FCP themes

- All 12 published themes include `achievements.qss`.
- All themes are version `1.0.2`.
- `.fctheme` archives and `themes.json` are rebuilt.
- Template theme docs updated:
  - `themes/theme_template/achievements.qss`
  - `themes/theme_template/README.md`
  - `CONTRIBUTING.md`
- Category hover/selection contrast fixed in all themes.
- Custom theme display name in Settings comes from `metadata.ini`, not the folder name.

### Template semantics

- Added `src/templates/semantic_keys.py`.
- New template configs use semantic values such as:
  - `mode: text_only`
  - `merge_order: alpha_az`
  - `compression_level: high`
  - `split_method: by_pages`
  - `optimization_type: compression_cleaning`
- Legacy French/English labels and old DB rows are normalized automatically.
- Template type storage remains the legacy French canonical form for compatibility. `TemplateManager.normalize_type()` returns that legacy value; `semantic_keys.normalize_type()` returns the semantic key.
- Updated:
  - `src/templates/template_manager.py`
  - `src/templates/frequent_configs.py`
  - `src/templates/create_template_dialog.py`
  - `src/templates/templates.py`
  - `src/templates/template_editor_dialog.py`
  - `src/app/ui.py`
- Added `tests/test_semantic_keys.py` and expanded template tests.

### History fixes

- History search matches the localized Type column, not only raw operation keys.
- Added `operation_types` filtering to main and advanced databases.
- Added `matching_operation_types()` in `src/history.py`.
- `translate_operation_type()` uses language files for all languages (IT/RU/TR/ZH/etc.).
- Added aliases/fallbacks for:
  - `image_to_pdf`
  - `image_to_pdf_s`
  - compression selection/all
  - advanced `*_to_*` operations
- Added `tests/test_history_search.py` and translation tests.

### Test/database isolation

- `tests/test_templates.py` uses a temporary database.
- Current app DB contains four templates:
  - `protections` (Protection PDF)
  - `bug_fixed` (Division PDF)
  - `Bug_template` (Fusion PDF)
  - `[Auto] PDF to Word Conversion #1`
- DB integrity check: `ok`.
- Backup of the DB before the earlier cleanup:
  - `C:\Users\hyaci\AppData\Local\Temp\opencode\file_converter_stats.db.before_template_cleanup`

### Build spec

- `packaging/build.spec` explicitly includes:
  - `templates.semantic_keys`
  - `achievements.theme`
  - `dashboard_theme`
  - `DLLs/libffi*.dll` from the build interpreter

### UI cleanup

- Removed leftover `??` / `???` placeholders in template detail rows; replaced with bullets.
- Removed unused `TemplateManager.semantic_type` helper.

## Dead-code check performed

Checked changed areas for stale references and duplicates:

- No remaining `_DSBase` / `_DSDark` / `_DSLight` classes.
- No remaining `_TYPE_NORMALIZE` in `TemplateManager`.
- No duplicate old French canonical maps in `frequent_configs.py`.
- No old hardcoded FR/EN operation dictionaries in `translations.py`.
- No `_progress_lbl_html`, `_update_secrets_btn_style`, `_refresh_header`, `_refresh_footer`.
- No `??` placeholders in `src/templates/templates.py`.
- No `QRadioButton` usage left in `MergeOrderDialog`.
- No inline green styles left on the protection Apply button or the merge dialog button.
- Ruff reports no unused imports/locals.
- Old French label mappings that remain in `semantic_keys.py` are intentional backward-compatibility aliases.

## Build/Release Status

The source has changed after both release artifacts. Only `packaging/dist` was rebuilt on 2026-11-02; the installer and ZIP are stale and must be rebuilt before release.

Rebuilt dist:

- `packaging\dist\FCP\FCP.exe`
  - Size: 24,620,057 bytes
  - Built: 2026-11-02 12:54:20
  - Verified from the frozen build: valid HTML→PDF uses system wkhtmltopdf, `pdf_to_html` works, and `html_to_pdf` rejects a PDF source with a clear error.

Stale artifacts (for reference only):

- `Output\FileConverterPro_Setup_v1.0.8.exe`
  - Run 29, built 2026-11-01 17:36:04 (before the WeasyPrint DLL, cancellation, and HTML guard changes)
  - Size: 130,539,813 bytes
  - SHA256: `FA48567808B30C6BC5A6CABBBD164C17654608FDBC2E77D3A6F47E08438EAEED`
- `Output\File_Converter_Pro_v1.0.8.zip`
  - Built 2026-10-29 21:57:17
  - Size: 152,712,317 bytes
  - SHA256: `1DB97F8A55F84E60593328E548A4A44988B81C1A96D643E09CEB59D160539868`
- `Output\checksums.txt` also predates the rebuild.

Working-tree release notes:

- `README.md` now advertises v1.0.8.
- `releases.md` is untracked and still says **471 tests**; the current count is **689**.
- Rebuilding `packaging/dist` resets the frozen app's Terms acceptance; context-menu tests may need to accept the Terms dialog again.

Rebuild commands from `packaging/`:

```powershell
pwsh -File build.ps1      # dist only; took ~10.2 minutes in this session
pwsh -File build_all.ps1  # dist + installer
```

Then rebuild the ZIP and checksums as previously done.

Release blockers:

- No `v1.0.8` git tag or GitHub release exists.
- Installer and ZIP must be rebuilt from the current source. The last dist rebuild predates the 2026-11-06 Quick Convert, PDF-to-Word, automation, and backup changes.
- Website deployment waits on that release.
- Website changes remain uncommitted in `C:\Users\hyaci\Documents\My Visual Studio Codes\All_Projects\fcp-website`.
- Wiki link bump remains uncommitted in `Wiki/For-End-Users.md` nested repo.

## Important Design Notes for Next Session

1. `TemplateManager.normalize_type()` intentionally returns the legacy French storage type.
2. `semantic_keys.normalize_type()` returns the semantic type (`pdf_to_word`, `file_optimization`, etc.).
3. New template configs are semantic; old configs are normalized on read/apply/export/import.
4. `frequent_configs.canonical_config()` returns semantic configs.
5. History type labels come from language files via `TranslationManager.translate_operation_type()`.
6. Custom theme display names come from `metadata.ini`, via `theme_manager.get_theme_display_name()`.
7. `achievements.qss` is optional; custom themes fall back to built-in light/dark if absent.
8. The local `Kintsugi` app theme has `achievements.qss` version `1.0.2` but is gitignored.
9. Do not add `achievements.qss` to required theme file lists; it is optional.
10. Test files should always override `database.SRC_DIR` or patch the DB manager to a temp path.
11. Security patch details live in `security_patches/`; keep `SECURITY.md` focused on policy and link to patch files.
12. PDF protection uses pypdf (not fitz) for AES-256 encryption and permission flags.
13. Merge-order selections use `AnimatedCheckBox` in an exclusive group; clicking the current selection must not clear it.
14. `AnimatedCheckBox` does not auto-detect theme; call `set_dark_mode(True/False)` after creating it in themed dialogs.
15. Frozen mode uses the same external-tool ToolSpec lookup as source; it does not bundle `wkhtmltopdf`. Missing-tool fallbacks are not a frozen-only behavior.
16. `html_to_pdf` requires `.html`/`.htm`/`.xhtml`; use `pdf_to_html` for PDFs. The engine guard lives in `src/converter/mixins/html_renderers.py`.
17. Context-menu cancellation is cooperative; do not terminate `QThread`s directly. The 5-second UI safety net uses `os._exit(0)`.
18. WeasyPrint DLL directories resolve env → INI → defaults; `_import_weasyprint()` must keep `os.add_dll_directory()` cookies alive for the process lifetime.
19. Quick Convert PDF-to-Word text-only output is transactional: primary/fallback write to `~fcp_pdf_word_*.docx` in the destination directory, then `os.replace()` commits. Watcher ignores the `~` prefix.
20. Watcher reads `pdf_to_word_mode` from `ConfigManager` on every PDF-to-Word conversion; do not cache it at Watcher startup. Scheduler inherits through `tasks.watcher._run_conversion`.
21. Quick image-to-PDF (single and merged) uses `utils.image_formats.decodable_image_path()`; do not bypass it for HEIC/HEIF/AVIF support.
22. `create_backup(..., overwrite=False)` is the collision-safe Quick path; `overwrite=True` remains the default for existing engine/advanced callers.
23. Quick Convert still ignores `default_output_folder`; the P2 audit is complete but the implementation is pending a product decision.
24. Remaining P4 architecture risks are the duplicated special pipelines, separate OCR implementations, and Watcher/Scheduler depending on helper imports from the Qt-containing `context_menu.window` module.

## Useful Commands

```powershell
# App tests
python -m pytest -q

# App lint/compile
python -m ruff check src tests
python -m compileall -q src tests

# FCP themes validation
cd "C:\Users\hyaci\Documents\My Visual Studio Codes\All_Projects\FCP-themes"
python scripts/build_themes.py --check

# Rebuild FCP archives + index
python scripts/build_themes.py

# Rebuild app installer
cd "C:\Users\hyaci\Documents\My Visual Studio Codes\All_Projects\File_Converter_App\packaging"
pwsh -File build_all.ps1
```
