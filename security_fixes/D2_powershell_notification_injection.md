# D2: PowerShell injection through imported translation packs

**Status:** Implemented and verified in the working tree. Not committed.

**Source finding:** `SECURITY_AUDIT_DEEP_DIVE.md` - D2 (High, confirmed injection path).

## Root cause

The notification path used `winotify 1.1.0`'s `Notification.show()`:

- `winotify` embeds `title`, `msg`, action label/link, tag, group, app id, icon,
  and duration into a PowerShell here-string template with `str.format()`.
- Translation values were treated as trusted text. An imported `.lang` file
  could override built-in `fr`/`en` keys, including `notif_task_done_fr` and
  `open_github_repository`.
- `translate_text()` deliberately converts literal `\\n` and `\\t` sequences to
  real newlines and tabs.
- A translation containing a newline followed by `"@` could terminate the
  here-string; the rest of the translation could become top-level PowerShell
  source. The original audit parsed a benign marker command without executing
  it.

Filtering quotes or newlines would not be sufficient because the content was
interpolated into executable source.

## Chosen solution

The unsafe `winotify.Notification.show()` path is no longer used.

1. **Notification XML is built as data in Python.** `_build_toast_xml()` uses
   `xml.etree.ElementTree`; title, message, action label, action URL, icon, and
   duration are escaped as XML text/attributes. XML safety is independent of
   PowerShell syntax.
2. **The PowerShell script is fixed.** `_TOAST_PS_SCRIPT` contains no
   here-strings and no interpolation of notification values. It reads a JSON
   payload from an environment variable, parses it with `ConvertFrom-Json`,
   loads the XML with `XmlDocument.LoadXml()`, and sets Tag/Group and the app id
   as data properties.
3. **The fixed script is passed with `-EncodedCommand`.** The command line
   contains no notification text. No `-Command` concatenation and no
   `-ExecutionPolicy Bypass` are used.
4. **Notification values are supplied separately.** `_build_ps_invocation()`
   places the JSON payload in `FCP_TOAST_PAYLOAD` in the child environment. The
   payload contains the XML plus app id, tag, and group. The PowerShell process
   never treats any of those values as source.
5. **Qt remains the fallback.** If `winotify` is not installed or the platform
   is not Windows, the existing Qt tray path is used unchanged.

The Windows toast still supports the existing title, message, icon, duration,
and protocol action. The app id, tag, and group behavior match the previous
winotify setup.

## Translation handling

- `_translate_message()` substitutes only the exact `{task}` and `{app}`
  placeholders with a regex callback. Other braces, quotes, backticks,
  semicolons, newlines, and Unicode are preserved as text instead of being
  interpreted by `str.format()`.
- Non-string translation values fall back to the built-in notification text.
- `_repo_button_label()` and `_get_task_display_name()` also guard against
  non-string values.
- Literal `\\n` and `\\t` conversion in `translate_text()` is preserved. The
  resulting newline/tab characters are data in the XML/JSON payload.
- Imported packs can still override built-in `fr`/`en` keys. This behavior was
  reviewed and left unchanged because it may be used by existing custom packs;
  the security fix does not depend on the values being trusted. It remains an
  integrity/translation-quality boundary, not a code-execution path.

## Tests

`tests/test_system_notifier_security.py` covers:

- here-string terminator plus newline in title, message, and action label;
- attempted additional PowerShell commands (`Write-Output 'D2_MARKER'`);
- quotes, apostrophes, braces, backticks, semicolons, XML-sensitive characters,
  and Unicode/accented French;
- XML round-trip equality for all notification fields;
- data separation: malicious markers are absent from the fixed script and
  command line, but present only in the JSON environment payload;
- mocked `Popen` inspection of the fixed command and environment;
- PowerShell AST parsing of the fixed script without executing the toast;
- malicious `.lang` overrides of `notif_task_done_fr` and
  `open_github_repository`;
- literal `\\n` and `\\t` handling;
- normal French and English notifications.

## Verification

- Focused D2 suite: `python -m pytest tests/test_system_notifier_security.py -q`
  - 12 passed.
- Translation suite: `python -m pytest tests/test_translations.py -q`
  - 12 passed.
- Full suite: `python -m pytest -q`
  - 534 passed.
- Ruff on modified Python files: `All checks passed`.
- Real Windows path: a benign toast payload was passed to the fixed encoded
  PowerShell script; the process returned `0`. The visual toast content was not
  inspected programmatically.
- No malicious payload was executed. Script inspection, mocked process
  execution, and PowerShell parser-only validation were used for hostile
  content.

## Remaining limitations

- Imported packs can still change built-in UI/notification text. This is an
  integrity issue, not PowerShell execution, because notification values are
  now data.
- XML 1.0-invalid control characters in a translation could make
  `XmlDocument.LoadXml()` fail; the notification is then skipped by the existing
  error handler. No arbitrary text filtering is applied.
- The fixed script relies on Windows PowerShell and the Windows Runtime toast
  APIs, matching the previous winotify requirement.
- The Qt fallback displays the same text through Qt and does not use PowerShell.
- The real toast was started successfully but its rendered pixels/text were not
  visually or OCR-verified.

## Files changed

- `src/system_notifier.py`
- `tests/test_system_notifier_security.py` (new)
- `security_fixes/D2_powershell_notification_injection.md` (this file)

No commit was created.
