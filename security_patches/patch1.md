# Patch 1: HTML-to-PDF local resource handling

- **Affected component:** HTML-to-PDF conversion, including local images,
  stylesheets, CSS resources, and fallback renderers.
- **Affected versions:** Releases predating the 1.0.8 development line,
  including v1.0.7.
- **Root cause:** Local resource references were not sufficiently contained, and
  renderers were allowed to access local files and active content.
- **Remediation:** Local resources are now disabled by default and require an
  explicit opt-in. Approved resources must remain inside the HTML file's folder.
  Local-file access and JavaScript are disabled in the pdfkit path; WeasyPrint
  uses a restricted URL policy with redirects disabled; the ReportLab fallback
  accepts only `data:` images. Resource reads use an open-once containment
  check.
- **Verification:** Focused regression tests, the full automated suite, real
  wkhtmltopdf checks, and WeasyPrint 70.0 runtime checks. The full suite reported
  550 passing tests in the current development line.
- **Limitations:** Local resources remain opt-in. Filesystem-level alias and
  race conditions remain documented limitations. Remote HTTP(S) resources are
  still allowed by the renderers. WeasyPrint 70.0 compatibility is verified with
  the restricted URL fetcher.
