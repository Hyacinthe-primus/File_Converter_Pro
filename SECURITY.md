# Security Policy

## Supported Versions

Only the latest release of File Converter Pro is supported with security updates. Previous versions receive no patches.

| Version | Supported |
|---------|-----------|
| 1.0.7+  | Yes       |
| < 1.0.7 | No        |

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
