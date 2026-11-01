# D1: HTML-to-PDF local resource access

**Status:** Implemented, independently reviewed, and hardened in the working tree. Not committed.

**Source finding:** `SECURITY_AUDIT_DEEP_DIVE.md` - D1 (High, confirmed).

## Vulnerability

Before this fix, every HTML-to-PDF conversion was treated as trusted:

- `src/converter/mixins/html_renderers.py` resolved `src`, `href`, and CSS
  `url(...)` values with `base_dir / value` and read matching files without any
  containment check.
- Absolute paths, `file://` URLs, UNC paths, and `../` traversal could all read
  files outside the HTML file's folder.
- pdfkit was invoked with `enable-local-file-access`, and wkhtmltopdf
  JavaScript was not disabled.
- WeasyPrint was given the source folder as `base_url`, allowing local fetches.
- The ReportLab fallback parsed local `<img src>` values directly.

The audit reproduced disclosure of an arbitrary local sentinel file in the
generated PDF through both the application's inliner and wkhtmltopdf
JavaScript/iframe access.

## Fix

### Setting and UI

- New persistent setting: `allow_local_resources_in_html_to_pdf`.
- Default: `False` in `DEFAULT_CONFIG` (`src/config.py`).
- Settings dialog: checkbox with an explanatory tooltip, restored by
  `restore_defaults()`, and returned by `get_settings()`
  (`src/dialogs/settings_dialog.py`).
- English/French strings added, plus matching keys in every bundled `.lang`
  file so translation-consistency tests pass.

### Two-layer enforcement

Layer 1 - application resource handling:

- `_inline_all_resources()` classifies every resource reference before reading.
- Local resources are read only when the setting is enabled **and** the resolved
  path is inside the HTML file's folder.
- Disabled, outside-root, missing, directory, and symlink-escape paths are
  removed from the HTML rather than left for a renderer to fetch later.
- Allowed local images, stylesheets, CSS `url()` resources, and `@import`ed CSS
  are converted to data URIs before rendering.
- `@import` recursion is capped at four levels.

Layer 2 - renderer hardening, independent of the setting:

- pdfkit always uses `disable-local-file-access` and `disable-javascript`.
  `enable-local-file-access` is never passed.
- WeasyPrint receives no `base_url` and uses
  `_safe_weasyprint_fetcher`, which permits only `http`, `https`, and `data`
  schemes. Evidence: `src/converter/mixins/html_renderers.py:128`.
- The ReportLab fallback only passes `data:` image sources to
  `add_image_flowable`; the helper now rejects non-`data:` values, EPS/PostScript
  MIME types, and EPS magic bytes.
- Active content is removed in both modes: `<script>`, `<iframe>`, `<object>`,
  `<embed>`, `<applet>`, `<base>`, and meta refresh, including entity-encoded
  `http-equiv` names and values.

This means even if a new HTML/CSS edge case escapes the sanitizer, the backends
still cannot read local files.

### Path validation

`_resolve_local_path()` and `_resource_target()` enforce:

- HTML entities are decoded before classification (`&#58;` cannot turn a
  blocked URL into an allowed one).
- `file://` URLs are parsed with `urlsplit`/`url2pathname`; Windows drive and UNC
  forms are recognised explicitly.
- Relative references resolve from the HTML folder (or the importing CSS
  folder), then `Path.resolve()` canonicalises them.
- Containment uses `os.path.normcase()` plus `os.path.commonpath()` against the
  HTML folder, so traversal and symlink escapes are rejected.
- The resolved target must be an existing regular file.
- The file is opened once, its handle is checked as a regular file, its path is
  resolved again after opening, and the opened handle's `st_dev`/`st_ino` must
  match the current path before data is read. This closes the ordinary
  validation/read TOCTOU window without adding a filesystem abstraction.
- `Path.resolve()` does **not** detect hardlinks. A hardlink inside the HTML
  folder can still expose the contents of a file outside it when the setting is
  enabled; see the residual-risk section.
- CSS files in subfolders may reference resources higher in the HTML folder,
  but never outside it; the original HTML folder remains the root.

### Propagation

`AdvancedConverterEngine(allow_local_html_resources=False)` exposes the policy.
The value is loaded from config and applied at every engine creation point:

- `src/advanced_conversions.py` (worker and dialog)
- `src/app/mixins/batch.py` (three sites)
- `src/context_menu/window.py`
- `src/tasks/watcher.py`

The advanced-conversion worker now applies config only when one is supplied;
previously it overwrote `backup_enabled` with `False` when no config was given.

## Follow-up hardening (independent D1 review)

### Classification

- **Original confirmed vulnerability:** fixed by the default-off setting and the
  two enforcement layers above.
- **Confirmed limitation:** hardlinks inside the HTML folder can reference files
  outside it when local resources are enabled.
- **Potential risk:** a TOCTOU race remains possible on filesystems or paths
  where the identity check cannot provide a stable guarantee.
- **Hardening improvements:** quote-aware tag extraction, `HTMLParser`-based
  meta-refresh detection, Windows UNC classification, CSS data-URI import
  preservation, and ReportLab image restrictions.
- **False positive:** EPS data URIs do not provide a local-file read bypass in
  the installed Pillow/Ghostscript combination because Pillow passes
  `-dSAFER`. This does not eliminate Ghostscript parser risk.
- **Unresolved:** remote HTTP(S) fetching, real WeasyPrint runtime verification,
  and residual limitations of regex-based HTML/CSS handling.

### Hardlink limitation

`Path.resolve()` canonicalises paths, but a hardlink is a directory entry that
shares an inode with a file elsewhere. It therefore resolves to a path inside
the HTML folder while its data also belongs to the outside file. The inliner
reads that path when local resources are enabled.

This is **not reachable through HTML alone**. A local actor must already be able
to create a hardlink inside the HTML folder (or the folder must contain such a
link), on the same volume as the target. No reliable cross-platform hardlink
restriction was introduced; the limitation and its prerequisites are documented
here rather than hidden behind an incomplete detector.

### TOCTOU mitigation

Local file reads now use a single opened handle:

1. open the resolved path read-only;
2. require the handle to be a regular file;
3. resolve the path again and require it to remain inside the HTML root;
4. compare the handle's `st_dev`/`st_ino` with the current path;
5. read from the already-open handle.

This rejects the practical symlink/junction/path-swap race tested by the
regression suite. It is a best-effort mitigation, not an absolute guarantee on
filesystems without stable file identity, and it does not detect hardlinks or
other filesystem aliases that still resolve inside the root.

### HTML parsing and UNC handling

- Tag extraction is quote-aware, so a quoted attribute containing `>` is
  captured as one tag instead of being truncated.
- Meta tags are evaluated with the standard-library `HTMLParser`; attribute
  names and values are entity-decoded before the `http-equiv=refresh` check.
  Encoded names/values and casing no longer bypass removal.
- Legitimate markup and non-local resource references are left intact.
- On Windows, `//server/share` is classified as a local UNC reference. It is
  blocked when local resources are disabled and remains subject to the HTML-root
  containment check when enabled. Explicit `http://` and `https://` references
  remain remote.
- Compatibility note: protocol-relative remote URLs (`//host/path`) on Windows
  are indistinguishable from UNC paths and are therefore treated as local and
  blocked. Use an explicit `https://` URL for remote resources.
- Renderer-level local-access and JavaScript restrictions remain independent of
  the sanitizer.

### CSS data-URI imports

The import parser now treats a quoted or `url(...)` data URI as a single import
token, including semicolons inside the URI. Valid `data:` imports are preserved
unchanged, following rules and imports remain intact, and the existing four-level
local-import recursion limit is retained. Local imports are still inlined only
inside the allowed root.

### ReportLab and Ghostscript

`add_image_flowable()` now accepts only `data:` sources. EPS/PostScript MIME
types and `%!PS` magic bytes are rejected before writing a temporary image or
constructing `RLImage`, so the ReportLab fallback does not invoke Ghostscript for
an EPS data URI. The removed local-path branch also previously appended the
source path to the temporary-file cleanup list, which could have deleted a local
file. Supported raster formats (and SVG where ReportLab/Pillow can handle it)
continue through the existing path.

Pillow's EPS plugin does pass `-dSAFER` to Ghostscript, and a harmless sentinel
test confirmed that `-dSAFER` blocks arbitrary file reads. That is not a claim
that Ghostscript parser vulnerabilities are eliminated; excluding EPS from this
fallback removes the external-process exposure instead.

## Behaviour matrix

| Reference | Disabled (default) | Enabled |
| --- | --- | --- |
| Local image/stylesheet/font inside HTML folder | Blocked and removed | Validated, read, embedded as data URI |
| Local path outside HTML folder | Blocked | Blocked |
| `file://`, UNC, absolute path outside root | Blocked | Blocked |
| Traversal or symlink escape | Blocked | Blocked |
| Hardlink inside HTML folder pointing outside | Blocked | **Read** (documented limitation) |
| Malformed quoted attribute containing `>` | Removed/blocked | Removed/blocked unless inside root |
| Encoded meta refresh | Removed | Removed |
| Windows `//server/share` | Blocked as local | Blocked outside root |
| Remote `http(s)` resource | Left for renderer | Left for renderer |
| `data:` resource | Left as-is | Left as-is |
| Data-URI CSS `@import` | Preserved | Preserved |
| JavaScript, iframe, object/embed/applet | Removed | Removed |
| Local `srcset` candidate | Removed | Removed (not inlined) |

## Verification

- Focused suite: `python -m pytest tests/test_html_local_resources_security.py -q`
  - 51 passed.
- Full suite: `python -m pytest -q`
  - 522 passed.
- Lint: `python -m ruff check ...`
  - All checks passed.
- Real wkhtmltopdf proof outside the repository:
  - A local SVG containing `LOCAL_SENTINEL`, a file iframe, and a JavaScript
    sentinel were placed in a temporary HTML file.
  - With the setting disabled, PyMuPDF extracted only `SAFE`; neither the local
    image nor the active content appeared.
  - With the setting enabled, it extracted `SAFE` and `LOCAL_SENTINEL`, proving
    approved local inlining still works; the iframe and JavaScript content were
    still absent.
- Follow-up real-wkhtmltopdf probes (Qt 4.8.7 producer) with harmless outside
  sentinels:
  - malformed quoted `>` attribute: sanitized, no outside sentinel, conversion
    completed;
  - entity-encoded meta refresh: removed, no outside sentinel, conversion
    completed;
  - data-SVG nested outside file: outer SVG rendered, nested file blocked in
    both modes;
  - approved local SVG inside the HTML folder: still inlined when enabled.

WeasyPrint could not render in this environment because its native Pango
dependency is unavailable. Its fetcher policy is covered by unit tests and the
conversion path was exercised with a fake module; the pdfkit path was exercised
with real wkhtmltopdf.

## Residual risks and limitations

- **Hardlinks (confirmed limitation).** A hardlink inside the HTML folder can
  expose outside-file contents when local resources are enabled. This requires a
  local actor able to create the link (or a folder already containing one) on
  the same volume; it is not reachable through HTML alone. No reliable
  cross-platform hardlink restriction was introduced.
- **TOCTOU (potential, mitigated).** The open-once/identity-check read rejects
  the tested path-swap race, but filesystems without stable `st_dev`/`st_ino`
  identity, or aliases such as hardlinks, can retain residual risk.
- Remote `http(s)` resources are still fetched by the backends. This is not
  local-file disclosure, but it can contact attacker-controlled servers or leak
  the user's IP address. Blocking remote resources would be a separate policy
  decision.
- Protocol-relative `//host/path` references on Windows are treated as local
  UNC paths and are blocked; use explicit `https://` URLs for remote resources.
- `srcset` local candidates are stripped rather than inlined. Standard `src`
  images and CSS resources are supported.
- Local references in SVG presentation attributes (for example `fill="url(...)"`)
  are not inlined by the application sanitizer. They remain protected by
  renderer-level denial of local access, but may not render when the setting is
  enabled.
- Files inside the HTML folder are intentionally allowed when the setting is on.
  That includes sibling files such as private keys placed next to the HTML
  document.
- HTML tag extraction remains quote-aware regex rather than a full document
  parser; meta refresh uses `HTMLParser`. The renderer-level controls above
  remain the defense-in-depth mechanism for malformed markup.
- WeasyPrint could not be run in this environment because native Pango
  dependencies are unavailable; its fetcher path is source-reviewed and
  unit-tested, but not runtime-verified here.

## Tests

`tests/test_html_local_resources_security.py` covers:

- default-off config and settings round-trip;
- settings checkbox state and persisted value;
- engine and advanced-worker propagation;
- no local file reads while disabled;
- allowed local images, stylesheets, CSS URLs, and CSS subdirectory references;
- blocking of outside-root, `file://`, UNC, traversal, non-file, and symlink
  targets;
- CSS `@import` handling and depth limits;
- JavaScript/iframe removal;
- HTML-entity bypass attempts;
- malformed quoted attributes containing `>`;
- entity-encoded and case-varied meta refresh removal;
- Windows forward-slash UNC classification and blocking;
- data-URI CSS imports followed by rules and local imports;
- hardlink limitation and open-once TOCTOU revalidation;
- ReportLab local-path and EPS data-URI rejection, plus PNG acceptance;
- WeasyPrint fetcher denial for local paths;
- pdfkit `disable-local-file-access`/`disable-javascript` options;
- ReportLab fallback ignoring local image paths.

## Files changed

- `src/config.py`
- `src/dialogs/settings_dialog.py`
- `src/converter/mixins/html_renderers.py`
- `src/converter/html_inline.py`
- `src/converter/converters.py`
- `src/advanced_conversions.py`
- `src/app/mixins/batch.py`
- `src/context_menu/window.py`
- `src/tasks/watcher.py`
- `src/languages/en.json`
- `src/languages/fr.json`
- `src/languages/blank.lang`
- `src/languages/en-revisited.lang`
- `src/languages/it.lang`
- `src/languages/ru.lang`
- `src/languages/tr.lang`
- `src/languages/zh.lang`
- `tests/test_html_local_resources_security.py` (new)

No commit was created. The existing unrelated working-tree changes were left
untouched.
