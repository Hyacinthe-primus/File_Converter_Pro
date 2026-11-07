# What's New in v1.0.8

## Converter

- **OpenDocument support** – ODT, ODS, and ODP files can now be converted to DOCX, XLSX, PPTX, and PDF, using an Office COM → LibreOffice → native fallback chain. OpenDocument extensions are recognized by the file picker, context menu, notifications, and achievements.
- **OpenDocument previews** – ODT, ODS, and ODP files can be previewed directly in the preview dialog.
- **Markdown to HTML** – Markdown files can be converted to standalone UTF-8 HTML documents with embedded CSS, from the app or the Windows context menu, by @Othman-Benbrahim in https://github.com/Hyacinthe-primus/File_Converter_Pro/pull/31
- **Raster to SVG** – images can now be vectorized to SVG with VTracer.
- **Image format detection** – HEIC/HEIF/AVIF files are detected from their content even when the extension is wrong, and are transparently decoded through a temporary PNG for PyMuPDF, Pillow, and OCR.
- **OCR for image to PDF** – a per-conversion OCR option uses the scanlayer engine to create searchable PDFs. It supports no/auto/manual orientation, falls back to a plain image embed when no text is found, and parallelizes OCR when merging multiple images into one PDF.
- **OCR in watch folders and scheduled tasks** – automation configs accept `ocr = true`, so image → PDF rules and image merges produce searchable PDFs in the background too, with the same orientation setting and plain-embed fallback.
- **OCR output safety** – Main and automation now share non-UI OCR helpers. OCR PDFs are staged and validated before replacing existing files; invalid OCR output falls back to a plain image embed, failed conversions preserve the destination, and merged-OCR achievements are recorded only after validation and commit.
- **Unified, validated conversion pipeline** – PDF ↔ Word, PDF/DOCX merge, DOCX → PDF, and image-to-PDF OCR paths now use shared staged validation and atomic replacement, so failed or cancelled conversions leave the previous destination intact and clean up temporary files.
- **Better PDF-to-Word** – LibreOffice PDF → DOCX now selects `writer_pdf_import`; text-only mode reports PDFs with no extractable text instead of silently producing an empty DOCX, and Quick/Watcher/Scheduler use the richer fitz fallback.
- **Safer DOCX-to-PDF** – DOCX inputs are validated before engines run. Windows tries direct Word COM first, keeps docx2pdf only as a `.docx` fallback after a COM error, and then falls back to LibreOffice or ReportLab. Existing destinations survive failed conversions.
- **Deterministic, safer merges** – Main, Quick Convert, Watcher, and Scheduler share merge helpers with staged validation, stable ordering, pypdf PDF bookmarks, shared DOCX page-break behavior, and collision-safe timestamp names.
- **Backup before conversion** – an optional setting creates a `.bak` copy of each source file before conversion starts.
- **Automatic temp file cleanup** – tracked temporary files are removed when the app closes and at the start of each batch conversion.

## Templates

- **Frequent-configuration templates** – when enabled in Settings, the app tracks how often each conversion configuration is used. A configuration used 3 times is promoted to an `[Auto]` template (up to 3 per conversion type). Duplicates of existing templates are skipped, and deleted auto templates are not recreated.
- **Auto-save frequent configurations** – the tracking that feeds automatic templates can be toggled in Settings.
- **Semantic template configuration** – new templates store language-independent keys such as `text_only`, `alpha_az`, `high`, and `by_pages` instead of French display labels. Legacy database rows and exported templates are normalized automatically, so existing templates keep working.

## Themes

- **QSS-themed settings and dialogs** – Settings, templates, dashboard, and dialogs are now fully styled by `settings.qss` and theme files instead of inline styles.
- **Custom themes in Advanced Conversions** – the dialog re-applies its styles instantly on theme changes, without restarting.
- **Themeable splash screen** – each theme can provide an optional `splash.qss`; themes without one fall back to their dark/light base.
- **Themeable Quick Convert window** – the context-menu window card uses an optional `window_card.qss` per theme, including readable combo-box selection colors in every theme.
- **Themeable automation buttons** – the automation folder and reload buttons in Settings now follow the active theme.
- **Theme gallery shortcut** – the Theme settings tab now has a translated **Get themes** link to the community FCP-themes repository.
- **Theme-aware dashboard** – stat cards, charts, tables, filters, and database controls now derive their palette from the active built-in or custom theme and refresh instantly on theme changes. Custom themes can also define an optional `[dashboard]` palette in `metadata.ini` for precise, readable colors.
- **Theme-aware achievements** – the achievements dialog, cards, XP ring, rank badge, stat bars and unlock/rank popups now use an optional `achievements.qss`. Built-in light and dark styles are included, and custom themes without the file fall back to the matching built-in style. The stylesheet also accepts an `AchievementsPalette` block for the custom-painted widgets, including ring/progress colors, card sheen/shadow, fonts, tier/category colors and per-rank colors.
- **Built-in theme alignment** – dark and light themes now match Obsidian's layout dimensions.
- **Theme switching fixes** – the logo label updates immediately, and tab close / preview button emojis are visible with custom themes.
- **Custom theme names in Settings** – the active custom theme now displays the name from `metadata.ini` instead of its folder name.
- **Readable achievement category highlights** – category hover and selection backgrounds are subtle tints, and category text colors are checked for contrast across all bundled themes.

## i18n

- **Turkish localization** – full Turkish UI translation, installer strings, and legal pages.
- **Achievements translated to English** – achievement names and descriptions are now available in English.
- **Semantic translation keys** – UI text now uses stable semantic keys instead of French literals, making translations consistent across the app.
- **Legacy language-file compatibility** – `legacy_aliases.json` maps old French keys to semantic keys, so existing community `.lang` files and saved values continue to resolve.
- **Bundled language coverage** – new and migrated strings are present in English, French, Italian, Russian, Turkish, Chinese, English-revisited, and the blank language template.
- **Hardcoded UI cleanup** – remaining hardcoded French fallbacks were removed, duplicate labels were consolidated, and file-dialog filters, encryption warnings, and template summaries are now localized.
- **New UI strings** – all new OCR, OpenDocument, template, and theme strings are translated across the existing languages.
- **OCR tooltip re-translation** – the OCR tooltip now updates when switching languages without restarting.

## Licensing

- **GPLv3 only** – the separate commercial license was removed and the README and terms of use now reference GPLv3 exclusively.

## Build & Packaging

- **`src/` layout** – application code, assets, styles, and languages moved under `src/`, with all build and installer files consolidated under `packaging/`.
- **Stable local paths** – configuration, encryption keys, and SQLite databases are anchored to the source directory so they stay alongside the app.
- **QSS recognized as CSS** – added `.gitattributes` entries for `*.qss` files.
- **New dependencies** – scanlayer (OCR), VTracer (SVG), and Markdown.
- **Version 1.0.8** – application, packaging, and metadata version bumped for the release.

## Testing

- **824 tests passed, 8 skipped** – expanded from 193 in v1.0.7, with new suites for PDF → Word fallbacks and cancellation, DOCX → PDF engine ordering and validation, PDF/DOCX merge safety, OCR consolidation and achievement accounting, OpenDocument conversions, ODF previews, image format detection, image-to-SVG, OCR, parallel OCR merge workers, automation OCR, Terms & Privacy enforcement, console suppression, auto-save, backup, temporary-file cleanup, dialog sizing, theme fixes, dashboard theming, achievements theming, semantic template configuration, and translation-key consistency.
- **Real integration coverage** – real Word COM and Tesseract tests run when available; the 8 skipped tests require unavailable LibreOffice/Word integration tools in the current environment.
- **Shared fixtures** – the QApp session fixture, offscreen platform, and isolated app fixture are consolidated in `conftest.py`.

## Fixes

- Config and key files are now stored in the source directory instead of the working directory.
- SQLite database files are anchored to the source directory.
- Refreshed tzdata for Morocco UTC+0 and removed the stale example job.
- Fixed `ModuleNotFoundError` when running `achievements_manager` directly.
- Removed the unimplemented "complete text" PDF-to-Word mode.
- Conversions from the Windows context menu now require Terms & Privacy acceptance, matching the main app.
- The background daemon now refuses to start watch folders and scheduled tasks until Terms & Privacy are accepted.
- No more console window flash at launch: playsound3's import-time backend probe (`ffplay -version`) now runs hidden, and tesseract/ffplay share one console-suppression helper.
- Fixed a crash when opening Settings caused by the console-suppression patch breaking `asyncio` imports.
- Per-file preview buttons are restored after a batch rename.
- Template tests now use an isolated temporary database, so test runs no longer create `Test Template` rows in the real app database.
- Template detail rows use normal bullets instead of leftover `??` placeholders.
- History search now matches the localized Type column shown in the app, not only the internal operation key.
- History conversion types now come from the active language file for every supported language, with readable format-arrow fallbacks for untranslated advanced operations.
- The Word to PDF options dialog now opens at its layout size hint, avoiding the Windows geometry warning.
- Merged PDF/DOCX timestamp collisions now append a unique suffix instead of overwriting an earlier output.
- Invalid or missing DOCX inputs fail with a clear message before opening Word.
- Failed or cancelled PDF/Word, merge, and OCR conversions preserve existing destinations and remove temporary staging files.
- PDF merges preserve bookmarks/outlines through pypdf.
- LibreOffice PDF → DOCX conversions use the Writer PDF import filter.
- Text-only PDF → Word reports image-only/scanned PDFs instead of returning an empty DOCX as success.
- Merged-image OCR achievements count only pages from a successfully validated and committed PDF.
- Dialog buttons now follow the active theme's `QPushButton` rules, including custom themes.
- Cleaned up the Advanced Conversions title and close button, removed emoji prefixes from Word-to-PDF labels and achievement names, and kept Markdown HTML output light-themed with embedded CSS.

**Full Changelog**: https://github.com/Hyacinthe-primus/File_Converter_Pro/compare/v1.0.7...v1.0.8
