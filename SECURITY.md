# Security Policy

## Supported Versions

Only the latest release of File Converter Pro is supported with security updates. Previous versions receive no patches.

| Version | Supported |
|---------|-----------|
| 1.0.7+  | Yes       |
| < 1.0.7 | No        |

At the time of writing, **v1.0.7 is the latest tagged release**. The security
fixes described below are present in the **1.0.8 development line** on `main`
and are expected in the next release; they are not included in the tagged
v1.0.7 build.

## Recent Security Fixes

### HTML-to-PDF local resource handling

- **Affected component:** HTML-to-PDF conversion, including local images,
  stylesheets, CSS resources, and fallback renderers.
- **Affected versions:** Releases predating the 1.0.8 development line,
  including the latest tagged v1.0.7.
- **Root cause:** Local resource references were not sufficiently contained, and
  renderers were allowed to access local files and active content.
- **Remediation:** Local resources are now disabled by default and require an
  explicit opt-in. Approved resources must remain inside the HTML file's folder.
  Local-file access and JavaScript are disabled in the pdfkit path; WeasyPrint
  uses a restricted URL policy; the ReportLab fallback accepts only `data:`
  images. Resource reads use an open-once containment check.
- **Verification:** Focused regression tests, the full automated suite, and
  real wkhtmltopdf checks. The full suite reported 541 passing tests at the time
  of the fix.
- **Limitations:** Local resources remain opt-in. Filesystem-level alias and
  race conditions remain documented limitations. Remote HTTP(S) resources are
  still allowed by the renderers. Newer WeasyPrint versions may hit a
  compatibility limitation in the custom fetcher and fall back to the safer
  ReportLab path; approved local resources may not render through that path.

### Notification PowerShell handling

- **Affected components:** Windows notifications and imported translation packs.
- **Affected versions:** Releases predating the 1.0.8 development line,
  including the latest tagged v1.0.7.
- **Root cause:** Notification text from translation packs was interpolated into
  generated PowerShell source.
- **Remediation:** Notifications no longer use the unsafe winotify template.
  A fixed PowerShell script receives notification values as structured XML and
  JSON data; no untrusted value is interpolated into PowerShell source or the
  command line. Imported translation values are treated as untrusted data.
- **Verification:** Focused regression tests, PowerShell parser validation,
  mocked process checks, and the full automated suite (541 passing tests at the
  time of the fix). A benign real Windows toast invocation completed
  successfully; visual rendering was not programmatically inspected.
- **Limitations:** Imported language packs can still change displayed UI and
  notification text; this is an integrity boundary, not code execution.
  Notification process hardening, including executable resolution and
  environment handling, remains tracked separately.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security reports.**

Email: **prime.enterprises.dev@gmail.com**

Include in your report:
- A description of the vulnerability and its impact.
- Steps to reproduce or a proof of concept.
- The version you tested against.

You should receive an initial acknowledgment within 72 hours. A solo developer maintains this project, so full analysis and patching may take longer depending on severity and complexity.

## What Qualifies

A security issue is anything that allows an attacker to execute arbitrary code, access data outside the app's intended scope, or cause unexpected behavior through crafted input without the user's informed consent.

Realistic attack surfaces in this project:

- **File parsing**: The app reads untrusted PDFs, Office documents, images, audio, and video through third-party libraries (MuPDF/fitz, pdf2docx, Pillow, lxml, openpyxl, python-pptx, etc.). Heap overflows, type confusion, or path traversal in any of these parsers are in scope.
- **COM automation**: When Microsoft Office is installed, the app calls Word, Excel, and PowerPoint through pywin32 COM automation. Injection through crafted Office documents or abuse of the COM interface is in scope.
- **External tool downloads**: The app can fetch third-party binaries (7-Zip, etc.) from URLs configured in `external_binaries.json`. MITM during download, path traversal in the tool path, or command injection when launching these tools is in scope.
- **Archive handling**: The app creates and extracts ZIP files (pyzipper with AES encryption). Zip-slip path traversal or weaknesses in the encryption implementation are in scope.
- **Local data**: Settings and history are stored as JSON files; achievements in SQLite. SQL injection, path traversal, or unsafe deserialization is in scope.

## What Is Not in Scope

- Vulnerabilities in third-party applications the app delegates to (Microsoft Office, LibreOffice, 7-Zip itself).
- Social engineering or phishing that tricks a user into running a malicious file.
- Issues requiring physical access to the machine.
- Bugs in the app's UI, sound system, or achievements feature that do not lead to code execution or data exposure.
- Denial of service through excessively large files (the app processes locally; the user controls what they open).

## Disclosure Policy

1. **Report received** – acknowledgment within 72 hours.
2. **Triage** – the maintainer validates the issue and assesses severity.
3. **Fix** – a patch is prepared and tested.
4. **Release** – a new version is published on GitHub.
5. **Credit** – the reporter is credited in the release notes unless they prefer otherwise.

If a fix requires coordination with an upstream library (e.g., a MuPDF or lxml vulnerability), the maintainer will file an issue with that project and work around it where possible while waiting for an upstream patch.

## Safe Harbor

The maintainer will not pursue legal action against researchers who:
- Make a good-faith effort to report privately.
- Do not exploit the vulnerability beyond what is necessary to demonstrate it.
- Do not access or modify data belonging to other users.
- Do not disrupt the service for other users.

## Code Signing

File Converter Pro is not currently code-signed. The executable is built with PyInstaller and distributed as a standalone archive. Users should verify downloads against official release channels. This is a known limitation and something the project aims to address as resources allow.

## Acknowledgments

Security research improves this project. Responsible disclosure is appreciated and credited.
