# D2 Residual Security Risks

**Status:** Documentation only. No code changes in this task.

**Context:** The original D2 vulnerability — PowerShell injection through imported
`.lang` translation packs via `winotify 1.1.0` here-string interpolation — has
been fixed and independently reviewed. The review verdict was
**PASS WITH LIMITATIONS**: no exploitable translation-to-PowerShell path was
found, but the residual concerns below remain.

These items are separated from D2 because they are pre-existing local hardening
issues, translation-integrity behavior, notification availability concerns, or
test-coverage gaps. None restores the original translation-to-PowerShell
injection.

## Summary

| ID | Severity | Area | D2 impact |
| --- | --- | --- | --- |
| R1 | Low | PowerShell executable resolution | Pre-existing local risk; not introduced by D2 |
| R2 | Low | Built-in translation override | Integrity issue; notification values remain data |
| R3 | Low / Informational | Invalid XML / oversized fields | Notification availability only |
| R4 | Informational | Action URL scheme | No current untrusted caller |
| R5 | Informational | Environment inheritance / silent child failure | Pre-existing process-hardening concern |
| R6 | Informational | Console/log output | Log spoofing/disruption only |

## R1 — PowerShell executable resolution through PATH

**Severity:** Low

**Location:** `src/system_notifier.py` (`_run_windows_toast` and
`_build_ps_invocation`)

**Finding:** PowerShell is invoked as `powershell.exe` rather than through a
validated absolute path. Windows executable resolution can search locations
such as the application directory, current directory, system directories, and
`PATH`.

**Preconditions:** A local attacker can write to one of those executable search
locations and place a malicious `powershell.exe`.

**Impact:** Potential local code execution as the user when a notification is
sent.

**D2 relationship:** This is pre-existing. The previous winotify implementation
also invoked `powershell.exe` by name. Imported translations cannot control
`PATH`, the current directory, or executable placement.

**Recommended improvement:** Resolve PowerShell through a validated absolute
path, preferably under
`%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe`, and reject
unexpected resolution results.

## R2 — Imported language packs can override built-in translations

**Severity:** Low

**Location:** `src/translations.py` (`_load_lang_file_internal`)

**Finding:** Imported `.lang` packs can set `meta.code` to `fr` or `en` and
update built-in translation dictionaries. This can change UI text, notification
messages, and action labels.

**Impact:** Translation-integrity and UI/notification-spoofing risk. It does not
restore the original PowerShell injection because notification values are now
handled as structured XML/JSON data and never become PowerShell source.

**Recommended improvement:** Consider a separate namespace for custom languages,
or prevent imported packs from replacing built-in `fr`/`en` entries while
preserving legitimate custom language packs.

## R3 — Invalid XML characters and oversized notification fields

**Severity:** Low / Informational

**Location:** `src/system_notifier.py` (`_build_toast_xml`,
`_build_ps_invocation`, `_run_windows_toast`)

**Finding:** XML 1.0-invalid control characters can make toast XML construction
or `XmlDocument.LoadXml()` fail. Extremely large notification fields increase
the XML/JSON payload size and may exceed process or environment-variable limits.

**Impact:** Notification availability only. A malformed or oversized
notification may be skipped or fail inside the child PowerShell process; no
PowerShell code execution was identified.

**Recommended improvement:** Validate XML-compatible characters and impose
reasonable notification field-size limits without unnecessarily modifying
legitimate text.

## R4 — Action URL scheme is not restricted

**Severity:** Informational

**Location:** `src/system_notifier.py` (`_build_toast_xml`, `send`,
`check_and_notify_update`)

**Finding:** The XML builder accepts arbitrary action URLs and marks them as
protocol actions. Current callers use trusted constant HTTPS URLs, so no current
exploitable path was identified.

**Impact:** If a future caller passes an untrusted action URL, a user click could
invoke an unintended protocol handler. This is not a PowerShell injection path.

**Recommended improvement:** Enforce an HTTPS allowlist if untrusted callers are
ever introduced.

## R5 — Child process inherits the parent environment and failures are silent

**Severity:** Informational

**Location:** `src/system_notifier.py` (`_build_ps_invocation`,
`_run_windows_toast`)

**Finding:** The PowerShell process inherits the parent environment through
`os.environ.copy()`. Its stdout and stderr are redirected to `DEVNULL`, and the
process is started without checking its exit status.

**Impact:** Sensitive parent environment values are available to the trusted
child, and toast/API failures are not surfaced to the application. This is a
pre-existing process-hardening and diagnostics concern, not a D2 injection path.

**Recommended improvement:** Provide a minimal environment, consider bounded
process monitoring or a timeout, and log relevant failures without exposing
sensitive values.

## R6 — Untrusted notification text appears in console output

**Severity:** Informational

**Location:** `src/system_notifier.py` (`send`)

**Finding:** Translated notification content is printed to the console without
escaping control characters.

**Impact:** A malicious translation could inject newlines, ANSI escapes, or
other control characters into console/log output, causing log spoofing or visual
disruption. It does not execute PowerShell.

**Recommended improvement:** Escape control characters in log output or avoid
logging the full notification message.

## Additional test coverage recommendations

The existing D2 tests establish the core command/environment separation and XML
escaping. The following additional tests would strengthen regression coverage:

1. **PowerShell AST command allowlist:** Parse `_TOAST_PS_SCRIPT` and assert the
   AST contains no dangerous constructs such as `Invoke-Expression`, `Add-Type`,
   `Start-Process`, or unexpected command invocation. The current AST test only
   checks for parse errors.
2. **Exact subprocess contract:** Assert that `Popen` receives a list argv, no
   `shell=True`, the expected fixed `-EncodedCommand`, and no untrusted values in
   the command line.
3. **Environment override:** Set a hostile inherited `FCP_TOAST_PAYLOAD` value
   and verify `_build_ps_invocation` replaces it with the generated payload.
4. **Invalid and oversized content:** Cover NUL bytes, XML 1.0-invalid control
   characters, very long titles/messages/action labels, and oversized payloads;
   assert the result is a controlled notification failure, not execution.
5. **Malformed JSON/environment payloads:** Verify that malformed child payload
   data cannot become executable PowerShell and that failures are handled.
6. **Full import path:** Exercise `load_lang_file()` through its copy-and-load
   path, not only `_load_lang_file_internal()`.
7. **Action URL handling:** Test scheme/protocol validation independently from
   message and action-label escaping.
8. **Executable resolution:** If R1 is addressed, test that PowerShell is
   resolved through the intended absolute path and that lookup failure is
   handled.
9. **Child failure behavior:** Cover PowerShell unavailable, toast API failure,
   nonzero exit status, and timeout behavior.
10. **Log output:** Test that control characters in translated messages are
    escaped or omitted from console/log output.
11. **Real notification rendering:** Where practical, verify the displayed toast
    text and action label, not only process startup success. This remains a
    compatibility check rather than a security proof.

## Unresolved limitations

- The real Windows toast path was not visually verified in the review.
- Windows PowerShell and Windows Runtime toast APIs remain required for the
  native Windows path.
- App ID registration and protocol-action behavior remain as before.
- Imported language packs remain an integrity boundary, not a code-execution
  boundary, after the D2 fix.
- These residual items should be handled as separate hardening work if the
  project's threat model includes local binary planting, untrusted language
  packs, or strict notification reliability.
