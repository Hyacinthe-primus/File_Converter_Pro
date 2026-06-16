# 🗺️ Roadmap for File Converter Pro

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

### Reduced Build Size
Investigate selective PyInstaller bundling and optional module lazy-loading to bring the compiled size below 300 MB without dropping any features.

### Automated Tests
Build a test suite covering the conversion engines and fallback chains. Given the size and complexity of the project, automated regression tests would prevent silent breakage when engines or dependencies are updated.

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

### System Notifications (Extended)
Windows toast notifications are already supported for certain events. The next step is extending them to **long-running conversions** — so users can switch to another app while a heavy batch runs and still get notified the moment it's done.

### Conversion Queue with Priorities
A visible queue panel where users can reorder pending conversions, pause individual items, or cancel specific tasks without killing the whole batch. Useful when converting dozens of files at once and something more urgent comes up.

### Undo Last Conversion
A lightweight undo system that keeps track of the last N output files and allows deleting them with one click, so a mistaken batch conversion doesn't leave the output folder cluttered.

### More Languages
The `.lang` system is already in place. Adding community-contributed translations (German, Spanish, Arabic, etc.) requires no code changes; just more `.lang` files. Native speakers are especially welcome.

---

## Dashboard & Stats

### Achievement Progress Graph
Visualize your achievement unlocks over time, see exactly when each one was earned and track your overall progression curve.

### PDF Dashboard Export
Print or export a full stats report as a PDF, useful for a personal recap or just for fun.

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
Expose conversion functionality via a lightweight local HTTP API, enabling integration with external tools — shell scripts, Zapier workflows, or any automation layer that can make HTTP requests.
Everything stays local: the API binds to `localhost` only and never opens an external port.


### More Format Support
Expand the supported format matrix over time. Candidates include:
- **Markdown → PDF / DOCX** via Pandoc
- **SVG → PNG / PDF** via CairoSVG
- **ODT / ODS / ODP** (LibreOffice native formats)
- **MP4 → GIF** / **GIF → WebP** for quick web-ready exports
### Conversion Engine Versioning
Track which engine version produced a given output (e.g. `ffmpeg 6.1`, `LibreOffice 24.8`). Useful for reproducing or debugging quality differences across machines or after an update.

---

## UI / UX
### Revisit the UI approach
make the UI of the software more intuitive to use

### Output Preview
A quick preview pane showing a thumbnail or first page of the converted output before the user opens it in another app. Particularly useful for image and PDF outputs.

### Custom Themes

File Converter Pro already supports automatic Dark and Light modes driven by the Windows registry. Custom themes would take this further by letting users define their own color schemes through a simple file format — no code changes required, following the same philosophy as the `.lang` translation system.

A `.theme` file (UTF-8 JSON) placed in a `themes/` folder next to the executable would be detected automatically and listed in Settings:

```json
{
  "meta": {
    "name":    "Midnight Blue",
    "author":  "Your Name",
    "version": "1.0",
    "created": "2026-01-01",
    "base":    "dark"
  },
  "colors": {
    "background":        "#0d1117",
    "surface":           "#161b22",
    "surface_alt":       "#21262d",
    "accent":            "#1f6feb",
    "accent_hover":      "#388bfd",
    "text_primary":      "#e6edf3",
    "text_secondary":    "#8b949e",
    "border":            "#30363d",
    "success":           "#3fb950",
    "warning":           "#d29922",
    "error":             "#f85149"
  }
}
```
 
The `base` field tells the app which built-in stylesheet to use as a fallback for any key not defined in the file — so a theme only needs to override what it changes.

A built-in **Theme Editor** in Settings would let users tweak colors visually with a live preview, then export the result as a `.theme` file they can share.

### Pinned Formats
Let users pin their most-used input/output format combinations to the top of the format selector so they don't have to scroll every time.

---

## Have an Idea?

Feel free to open an [Issue](../../issues) with the `enhancement` label.
All suggestions are read and considered.
