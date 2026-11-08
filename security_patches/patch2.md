# Patch 2: Notification PowerShell handling

- **Affected components:** Windows notifications and imported translation packs.
- **Affected versions:** Releases predating the 1.0.8 development line,
  including v1.0.7.
- **Root cause:** Notification text from translation packs was interpolated into
  generated PowerShell source.
- **Remediation:** Notifications no longer use the unsafe winotify template.
  A fixed PowerShell script receives notification values as structured XML and
  JSON data; no untrusted value is interpolated into PowerShell source or the
  command line. Imported translation values are treated as untrusted data.
- **Verification:** Focused regression tests, PowerShell parser validation,
  mocked process checks, and the full automated suite (550 passing tests in the
  current development line). A benign real Windows toast invocation completed
  successfully; visual rendering was not programmatically inspected.
- **Limitations:** Imported language packs can still change displayed UI and
  notification text; this is an integrity boundary, not code execution.
  Notification process hardening, including executable resolution and
  environment handling, remains tracked separately.
