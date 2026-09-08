# Roadmap for File Converter Pro

This roadmap outlines planned features and improvements for future versions of File Converter Pro.
Items are grouped by category and are not listed in order of priority or release date.
This is a solo project developed alongside studies, so timelines are intentionally left open.

> **Note:** This roadmap is aspirational. Features may be added, removed, or reprioritized at any time.
> Contributions, suggestions, and feedback are welcome via [Issues](../../issues).

---

## ✅ Completed

These features have been implemented and shipped.

### Disable Achievements
Users can now disable the achievements system entirely from Settings, for a more minimal experience.

### Windows Context Menu Support
Convert files directly from File Explorer -- right-click any supported file, hover **Convert with FCP**, and pick the conversion. A lightweight window opens, converts, and closes automatically. No need to open the app at all.

### Expanded Image Conversion Support
Image converters previously limited to PNG and JPG outputs now support 13 output formats:
PNG, JPEG, JPG, BMP, HEIC, WebP, TIFF, PSD, SVG, AVIF, J2K, DNG, ICO.
Input format support has also been extended to cover most common image extensions.

> **Note:** When selecting multiple files, each file must be the same type.

### Advanced Batch Scheduling
Schedule conversion tasks to run at a specific time or on a recurring basis.
Example: *"Convert everything in this folder every Monday at 9:00 AM."*

### Watch Folder
Monitor a folder and automatically convert any file dropped into it, using a predefined output format and template. Zero interaction required once configured.

### System Notifications
Windows toast notifications are fully supported for long-running conversions. Users can switch to another app while a batch is running and receive a notification as soon as it completes.

### Reduced Build Size
Investigative PyInstaller bundling brought the compiled size from 269 MB to ~219 MB. Orphaned Qt6 DLLs, Pythonwin/MFC, unused crypto libraries, and legacy binaries were removed. SFX sounds were compressed from WAV (16.3 MB) to OGG (2.9 MB), and Qt translations were trimmed to the top 10 world languages.

### Automated Tests
193 tests covering the conversion engine, fallback chains, architecture invariants (translations, mixins, QSS styling), external binary resolution, and achievements isolation. Shared fixtures are consolidated in `conftest.py`.

### Converter Engine Refactor
The monolithic converter was split into an engine-based mixin architecture with a centralized dispatch table. Each format (RTF, PPTX, EPUB, HTML, PDF, Office COM) has its own renderer mixin, and a multi-engine fallback chain tries native, LibreOffice, and COM in sequence.

### Markdown to HTML
Markdown files can be converted to standalone UTF-8 HTML documents from the application or the Windows context menu.

### 7-Zip Replaces WinRAR
File compression now uses 7-Zip for ZIP splitting and 7Z format support, removing the WinRAR dependency.

### External Binary Resolver
A centralized lookup chain (system PATH, app-local, common directories, config file) resolves ffmpeg, 7-Zip, and LibreOffice. Users can manually point the app to tool locations via `config/external_binaries.conf`.

### Multi-Project Tabs
Files can be organized into separate project workspaces within the app, each with its own info dialog. Up to 5 tabs are supported.

### Custom Themes
A theme manager handles user-created QSS themes. Themes are detected automatically from a `themes/custom_themes/` folder and listed in Settings. The merge order dialog now respects dark/light theme.

### Flagged Language Names
Language names in the selector now display their country flag, re-translate when switching languages without restarting, and include all missing translation keys across English, French, Italian, Russian, and Chinese.

### Word to PDF Options
Image compression and metadata stripping are now available when converting Word documents to PDF.

### PDF Optimization for Scanned PDFs
Scanned PDFs are now supported by the optimizer with Ghostscript and native fallbacks.

### Security Policy
A `SECURITY.md` was added with responsible disclosure guidelines, scope definitions tied to the actual codebase (file parsing, COM automation, external tools), and safe harbor terms.

---

## User Features

### Linux Support
Revisit the main code to add linux support such as: 
- Appimage
- Flatpack
- Specific Linux Distributions support (may come really late)
### User Profiles
Support for multiple independent profiles on the same machine, each with their own:
- Achievement progress and stats
- Saved templates
- Conversion history

### Conversion Queue with Priorities
A visible queue panel where users can reorder pending conversions, pause individual items, or cancel specific tasks without killing the whole batch. Useful when converting dozens of files at once and something more urgent comes up.

### Undo Last Conversion
A lightweight undo system that keeps track of the last N output files and allows deleting them with one click, so a mistaken batch conversion doesn't leave the output folder cluttered.

### More Languages
The `.lang` system is already in place. Adding community-contributed translations (German, Spanish, Arabic, etc.) requires no code changes; just more `.lang` files. Native speakers are especially welcome.

---

## Dashboard & Stats

### Period Comparison
Compare your activity between two time ranges directly in the dashboard.
Example: *"This week vs. last week"* - conversion count, file volume, formats used.

### Format Popularity Heatmap
A calendar-style heatmap (similar to GitHub's contribution graph) showing which days you converted the most files. A nice visual complement to the existing bar charts.

### Achievement Rarity Labels
Contextual labels on achievements showing how far along most users get. e.g. *"Most users reach this around 50 conversions"*. Encourages continued use without requiring any server or leaderboard.

---

## Technical

### Plugin System
Allow users to add custom converters via external Python scripts, without modifying the core codebase. A defined plugin interface would let the community (or power users) extend File Converter Pro with new formats or conversion pipelines.

### Local REST API
Expose conversion functionality via a lightweight local HTTP API, enabling integration with external tools like shell scripts, Zapier workflows, or any automation layer that can make HTTP requests.
Everything stays local: the API binds to `localhost` only and never opens an external port.


### More Format Support
Expand the supported format matrix over time. Candidates include:
- **Markdown → PDF / DOCX** via Pandoc
- **HTML → Markdown**
- **ODT / ODS / ODP → Word**
- **Word → ODT / ODS / ODP** (LibreOffice native formats)
- **MP4 → GIF** / **GIF → WebP** for quick web-ready exports
### Conversion Engine Versioning
Track which engine version produced a given output (e.g. `ffmpeg 6.1`, `LibreOffice 24.8`). Useful for reproducing or debugging quality differences across machines or after an update.

---

## UI / UX
### Revisit the UI approach
make the UI of the software more intuitive to use

### Output Preview
A quick preview pane showing a thumbnail or first page of the converted output before the user opens it in another app. Particularly useful for image and PDF outputs.

### Pinned Formats
Let users pin their most-used input/output format combinations to the top of the format selector so they don't have to scroll every time.

---

## Have an Idea?

Feel free to open an [Issue](../../issues) with the `enhancement` label.
All suggestions are read and considered.
