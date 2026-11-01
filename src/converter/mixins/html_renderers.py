"""HTML -> PDF rendering (pdfkit > weasyprint > reportlab fallback)."""

from __future__ import annotations

import html as html_stdlib
import ntpath
import os
import re
import stat
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import url2pathname

from converter.helpers import _img_to_b64, _mime_for_ext
from converter.html_inline import add_image_flowable, build_table_flowable, inline_markup

_WEASYPRINT_DLL_COOKIES = []


def _import_weasyprint():
    """Import WeasyPrint with the native MSYS2/GTK DLLs taking priority.

    WeasyPrint resolves its libraries through ctypes.util.find_library(), which
    walks PATH. Other applications bundle their own GTK stack (Tesseract-OCR
    ships pango/harfbuzz/fontconfig), so if such a directory comes first on
    PATH, an incompatible mix of DLLs is loaded and the process crashes.
    Prioritize the real native DLL directories for the import only.
    """
    if os.name != "nt":
        import weasyprint

        return weasyprint

    configured = os.environ.get("WEASYPRINT_DLL_DIRECTORIES", "")
    candidates = [part for part in configured.split(";") if part]
    candidates.extend(
        (
            r"C:\msys64\ucrt64\bin",
            r"C:\msys64\mingw64\bin",
            r"C:\Program Files\GTK3-Runtime Win64\bin",
        )
    )

    dll_dirs = []
    seen = set()
    for path in candidates:
        key = os.path.normcase(os.path.abspath(path))
        if key in seen or not os.path.isdir(path):
            continue
        seen.add(key)
        dll_dirs.append(path)

    for path in dll_dirs:
        try:
            _WEASYPRINT_DLL_COOKIES.append(os.add_dll_directory(path))
        except OSError:
            pass

    old_path = os.environ.get("PATH", "")
    if dll_dirs:
        dropped = {os.path.normcase(os.path.abspath(path)) for path in dll_dirs}
        remaining = []
        for path in old_path.split(os.pathsep):
            if path and os.path.normcase(os.path.abspath(path)) not in dropped:
                remaining.append(path)
        os.environ["PATH"] = os.pathsep.join(dll_dirs + remaining)
    try:
        import weasyprint
    finally:
        os.environ["PATH"] = old_path
    return weasyprint


class _SingleTagParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tag = None
        self.attrs = []

    def handle_starttag(self, tag, attrs):
        self.tag = tag.lower()
        self.attrs = attrs

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)


def _parse_start_tag(raw_tag):
    parser = _SingleTagParser()
    try:
        parser.feed(raw_tag)
        parser.close()
    except Exception:
        return None, []
    return parser.tag, parser.attrs


def _is_meta_refresh_tag(raw_tag):
    tag, attrs = _parse_start_tag(raw_tag)
    if tag != "meta":
        return False
    values = {}
    for name, value in attrs:
        key = html_stdlib.unescape(name or "").strip().lower()
        values.setdefault(key, html_stdlib.unescape(value or ""))
    return values.get("http-equiv", "").strip().lower() == "refresh"


class HtmlRenderers:
    """HTML -> PDF rendering strategies and resource inlining."""

    def _html_to_pdf(self, src, dst):
        """
        HTML → PDF - lightweight strategy stack, PyInstaller-compatible.

        1. pdfkit    (wkhtmltopdf separate binary, optional)
        2. weasyprint (pip install weasyprint)
        3. reportlab  - parses HTML manually, never fails, no duplicate content
           (fitz insert_htmlbox removed - duplicates content on some HTML inputs)
        """
        src_path = Path(src)
        base_dir = src_path.parent
        allow_local_resources = self._allow_local_resources(None)

        with open(src, "r", encoding="utf-8", errors="replace") as f:
            html_raw = f.read()

        html = self._inline_all_resources(html_raw, base_dir, allow_local_resources)

        # Strategy 1: pdfkit (wkhtmltopdf)
        try:
            import pdfkit

            from external_binaries import resolve_binary

            _wkhtmltopdf = resolve_binary("wkhtmltopdf")
            _pdfkit_cfg = pdfkit.configuration(wkhtmltopdf=_wkhtmltopdf) if _wkhtmltopdf else None
            tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
            tmp.write(html)
            tmp.close()
            try:
                pdfkit.from_file(
                    tmp.name,
                    dst,
                    options={
                        "disable-local-file-access": "",
                        "disable-javascript": "",
                        "load-error-handling": "ignore",
                        "load-media-error-handling": "ignore",
                        "print-media-type": "",
                        "quiet": "",
                        "margin-top": "15mm",
                        "margin-bottom": "15mm",
                        "margin-left": "15mm",
                        "margin-right": "15mm",
                    },
                    configuration=_pdfkit_cfg,
                )
                return
            finally:
                try:
                    os.remove(tmp.name)
                except Exception:
                    pass
        except Exception:
            pass

        # Strategy 2: weasyprint
        try:
            import warnings

            weasyprint = _import_weasyprint()

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                weasyprint.HTML(string=html, url_fetcher=self._safe_weasyprint_fetcher).write_pdf(dst)
            return
        except Exception:
            pass

        # Strategy 3: reportlab
        self._reportlab_html_to_pdf(html, dst)

    _REMOTE_PREFIXES = ("http://", "https://", "ftp://", "ftps://", "mailto:", "tel:")
    _URL_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
    _WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")
    _TAG_BODY = r"""(?:"[^"]*"|'[^']*'|[^>"'])*"""
    _TAG_RE = re.compile(r"<" + _TAG_BODY + r">", re.S)
    _META_TAG_RE = re.compile(r"<meta\b" + _TAG_BODY + r">", re.I | re.S)
    _CSS_URL_RE = re.compile(r"""url\(\s*(?P<quote>['"]?)(?P<url>.*?)(?P=quote)\s*\)""", re.I | re.S)
    _CSS_IMPORT_RE = re.compile(
        r"""@import\s+(?:url\(\s*(?P<url_quote>['"]?)(?P<url_quoted>.*?)(?P=url_quote)\s*\)
        |(?P<bare_quote>['"])(?P<url_bare>.*?)(?P=bare_quote))\s*[^;]*;""",
        re.I | re.S | re.X,
    )
    _SRC_RE = re.compile(r"""\bsrc\s*=\s*(['"])([^'"]+)\1""", re.I)
    _HREF_RE = re.compile(r"""\bhref\s*=\s*(['"])([^'"]+)\1""", re.I)
    _STYLE_ATTR_RE = re.compile(
        r"""(?P<prefix>\bstyle\s*=\s*)(?P<quote>['"])(?P<css>.*?)(?P=quote)""",
        re.I | re.S,
    )
    _SRCSET_RE = re.compile(
        r"""(?P<prefix>\bsrcset\s*=\s*)(?P<quote>['"])(?P<value>.*?)(?P=quote)""",
        re.I | re.S,
    )
    _URL_ATTR_RE = re.compile(
        r"""(?P<prefix>\b(?:src|href|poster|data|xlink:href|background)\s*=\s*)"""
        r"""(?P<quote>['"])(?P<value>[^'"]*)(?P=quote)""",
        re.I | re.S,
    )
    _URL_ATTR_UNQUOTED_RE = re.compile(
        r"""(?P<prefix>\b(?:src|href|poster|data|xlink:href|background)\s*=\s*)(?P<value>[^\s>"']+)""",
        re.I,
    )

    def _allow_local_resources(self, allow_local_resources):
        if allow_local_resources is None:
            return bool(getattr(self, "allow_local_html_resources", False))
        return bool(allow_local_resources)

    @staticmethod
    def _safe_weasyprint_fetcher(url, *args, **kwargs):
        """Allow only remote/data fetches; applied local files are inlined."""
        scheme = urlsplit(url).scheme.lower()
        if scheme not in ("http", "https", "data"):
            raise ValueError("Local file access is disabled")
        from weasyprint.urls import default_url_fetcher

        return default_url_fetcher(url, *args, **kwargs)

    @staticmethod
    def _clean_resource_ref(raw):
        value = html_stdlib.unescape(str(raw).strip())
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1].strip()
        return value

    def _resource_kind(self, raw):
        ref = self._clean_resource_ref(raw)
        if not ref:
            return "empty", None
        lower = ref.lower()
        if lower.startswith("data:"):
            return "data", None
        if ref.startswith("#"):
            return "fragment", None
        if lower.startswith(self._REMOTE_PREFIXES):
            return "remote", None
        if lower.startswith("//"):
            if os.name == "nt":
                return "local", ref
            return "remote", None
        if lower.startswith("file:"):
            return "local", ref
        if self._WINDOWS_DRIVE_RE.match(ref) or ref.startswith("\\\\"):
            return "local", ref
        if self._URL_SCHEME_RE.match(ref):
            return "other", None
        return "local", ref

    @staticmethod
    def _path_within_root(path, root):
        try:
            root_key = os.path.normcase(str(root))
            path_key = os.path.normcase(str(path))
            return os.path.commonpath([root_key, path_key]) == root_key
        except ValueError:
            return False

    @classmethod
    def _read_local_file(cls, path, root_dir):
        root = Path(root_dir).resolve()
        fd = None
        try:
            fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0))
            opened = os.fstat(fd)
            if not stat.S_ISREG(opened.st_mode):
                raise OSError("local resource is not a regular file")
            current = Path(path).resolve()
            if not cls._path_within_root(current, root):
                raise OSError("local resource escaped the HTML root")
            current_stat = current.stat()
            if (current_stat.st_dev, current_stat.st_ino) != (opened.st_dev, opened.st_ino):
                raise OSError("local resource changed during validation")
            with os.fdopen(fd, "rb") as handle:
                fd = None
                return handle.read()
        finally:
            if fd is not None:
                os.close(fd)

    @classmethod
    def _read_local_text(cls, path, root_dir):
        return cls._read_local_file(path, root_dir).decode("utf-8", errors="replace")

    def _resolve_local_path(self, ref, base_dir, root_dir=None):
        try:
            if ref.lower().startswith("file:"):
                split = urlsplit(ref)
                path_text = unquote(split.path)
                if split.netloc:
                    path_text = f"//{split.netloc}{path_text}"
                if os.name == "nt":
                    path_text = url2pathname(path_text)
            else:
                path_text = unquote(ref.split("?", 1)[0].split("#", 1)[0])

            if not path_text:
                return None
            if self._WINDOWS_DRIVE_RE.match(path_text) or path_text.startswith("\\\\"):
                if os.name != "nt":
                    return None
                drive, _ = ntpath.splitdrive(path_text)
                if drive and not ntpath.isabs(path_text):
                    return None

            path = Path(path_text)
            if not path.is_absolute():
                path = Path(base_dir) / path
            resolved = path.resolve()
            root = Path(root_dir if root_dir is not None else base_dir).resolve()
            if not self._path_within_root(resolved, root):
                return None
            if not resolved.is_file():
                return None
            return resolved
        except (OSError, ValueError):
            return None

    def _resource_target(self, raw, base_dir, allow_local_resources, root_dir=None):
        kind, ref = self._resource_kind(raw)
        if kind != "local":
            return kind, None
        if not allow_local_resources or ref is None:
            return "blocked", None
        path = self._resolve_local_path(ref, base_dir, root_dir)
        if path is None:
            return "blocked", None
        return "local", path

    @classmethod
    def _file_data_uri(cls, path, root_dir):
        return _img_to_b64(cls._read_local_file(path, root_dir), _mime_for_ext(path.suffix.lstrip(".")))

    def _inline_css_urls(self, css, base_dir, allow_local_resources=None, _depth=0, _root_dir=None):
        """Inline or block local CSS url()/@import references."""
        allow_local_resources = self._allow_local_resources(allow_local_resources)
        base_dir = Path(base_dir).resolve()
        root_dir = Path(_root_dir).resolve() if _root_dir is not None else base_dir

        def _import_url(m):
            return m.group("url_quoted") if m.group("url_quoted") is not None else m.group("url_bare")

        def _import_repl(m):
            kind, path = self._resource_target(_import_url(m), base_dir, allow_local_resources, root_dir)
            if kind in ("remote", "data", "fragment", "empty", "other"):
                return m.group(0)
            if kind != "local" or path is None:
                return ""
            try:
                imported = self._read_local_text(path, root_dir)
                imported = self._inline_css_urls(
                    imported, path.parent, allow_local_resources, _depth + 1, root_dir
                )
                data_uri = _img_to_b64(imported.encode("utf-8"), "text/css")
                return f"@import url('{data_uri}');"
            except Exception:
                return ""

        if _depth <= 4:
            css = self._CSS_IMPORT_RE.sub(_import_repl, css)
        else:
            css = self._CSS_IMPORT_RE.sub(
                lambda m: "" if self._resource_kind(_import_url(m))[0] == "local" else m.group(0),
                css,
            )

        def _url_repl(m):
            kind, path = self._resource_target(m.group("url"), base_dir, allow_local_resources, root_dir)
            if kind in ("remote", "data", "fragment", "empty", "other"):
                return m.group(0)
            if kind == "local" and path is not None:
                try:
                    return "url('" + self._file_data_uri(path, root_dir) + "')"
                except Exception:
                    return "url('')"
            return "url('')"

        return self._CSS_URL_RE.sub(_url_repl, css)

    def _inline_all_resources(self, html, base_dir, allow_local_resources=None):
        """Inline allowed local resources and strip all other local references."""
        allow_local_resources = self._allow_local_resources(allow_local_resources)
        base_dir = Path(base_dir).resolve()

        tag_body = self._TAG_BODY
        html = re.sub(rf"<(script|iframe|object|embed|applet)\b{tag_body}>.*?</\1\s*>", "", html, flags=re.I | re.S)
        html = re.sub(rf"<(script|iframe|object|embed|applet)\b{tag_body}>", "", html, flags=re.I | re.S)
        html = re.sub(rf"<base\b{tag_body}>", "", html, flags=re.I | re.S)
        html = self._META_TAG_RE.sub(
            lambda m: "" if _is_meta_refresh_tag(m.group(0)) else m.group(0),
            html,
        )

        def _link_to_style(m):
            tag = m.group(0)
            hm = self._HREF_RE.search(tag)
            if not hm:
                return tag
            kind, path = self._resource_target(hm.group(2), base_dir, allow_local_resources)
            if kind in ("remote", "data", "empty", "fragment", "other"):
                return tag
            if kind != "local" or path is None or "stylesheet" not in tag.lower():
                return ""
            try:
                css = self._read_local_text(path, base_dir)
                css = self._inline_css_urls(css, path.parent, allow_local_resources, _root_dir=base_dir)
                return "<style>" + css + "</style>"
            except Exception:
                return ""

        html = re.sub(rf"<link\b{tag_body}>", _link_to_style, html, flags=re.I | re.S)

        def _style_block(m):
            return "<style>" + self._inline_css_urls(m.group(1), base_dir, allow_local_resources) + "</style>"

        html = re.sub(rf"<style\b{tag_body}>(.*?)</style\s*>", _style_block, html, flags=re.I | re.S)

        def _img_src(m):
            tag = m.group(0)
            sm = self._SRC_RE.search(tag)
            if not sm:
                return tag
            kind, path = self._resource_target(sm.group(2), base_dir, allow_local_resources)
            if kind in ("remote", "data", "empty", "fragment", "other"):
                return tag
            if kind == "local" and path is not None:
                try:
                    return self._SRC_RE.sub('src="' + self._file_data_uri(path, base_dir) + '"', tag, count=1)
                except Exception:
                    pass
            return self._SRC_RE.sub('src=""', tag, count=1)

        html = re.sub(rf"<img\b{tag_body}>", _img_src, html, flags=re.I | re.S)

        def _sanitize_srcset(m):
            for candidate in m.group("value").split(","):
                raw = candidate.strip().split()[0] if candidate.strip() else ""
                kind, _ = self._resource_target(raw, base_dir, allow_local_resources)
                if kind in ("local", "blocked"):
                    return m.group("prefix") + '""'
            return m.group(0)

        def _sanitize_url_attr(m):
            kind, _ = self._resource_target(m.group("value"), base_dir, allow_local_resources)
            if kind in ("local", "blocked"):
                return m.group("prefix") + m.group("quote") + m.group("quote")
            return m.group(0)

        def _sanitize_url_attr_unquoted(m):
            kind, _ = self._resource_target(m.group("value"), base_dir, allow_local_resources)
            if kind in ("local", "blocked"):
                return m.group("prefix") + '""'
            return m.group(0)

        def _sanitize_tag(tag):
            tag = self._STYLE_ATTR_RE.sub(
                lambda m: (
                    m.group("prefix")
                    + m.group("quote")
                    + self._inline_css_urls(m.group("css"), base_dir, allow_local_resources)
                    + m.group("quote")
                ),
                tag,
            )
            tag = self._SRCSET_RE.sub(_sanitize_srcset, tag)
            tag = self._URL_ATTR_RE.sub(_sanitize_url_attr, tag)
            tag = self._URL_ATTR_UNQUOTED_RE.sub(_sanitize_url_attr_unquoted, tag)
            return tag

        return self._TAG_RE.sub(lambda m: _sanitize_tag(m.group(0)), html)

    def _reportlab_html_to_pdf(self, html, dst):
        """
        Reportlab HTML fallback — faithful CSS class + inline style support.
        Parses <style> blocks to extract .class rules (text-align, margin-left).
        Applies class + inline style to every <p>/<div>.
        <br> inside <p> becomes a real line break inside the paragraph.
        .pn (page number) divs are skipped.
        """
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

        MAX_W = A4[0] - 40 * mm
        base = getSampleStyleSheet()

        class_rules = {}
        for sb in re.finditer(r"<style[^>]*>(.*?)</style>", html, re.I | re.S):
            css = sb.group(1)
            for rule in re.finditer(r"\.([\w-]+)\s*\{([^}]*)\}", css):
                cls = rule.group(1)
                decls = {}
                for d in rule.group(2).split(";"):
                    d = d.strip()
                    if ":" not in d:
                        continue
                    p, _, v = d.partition(":")
                    decls[p.strip().lower()] = v.strip()
                class_rules[cls] = decls

        ALIGN_MAP = {
            "right": TA_RIGHT,
            "center": TA_CENTER,
            "left": TA_LEFT,
            "justify": TA_JUSTIFY,
        }

        def _decls_to_align(decls):
            return ALIGN_MAP.get(decls.get("text-align", "").lower())

        def _decls_to_indent(decls):
            ml = decls.get("margin-left", "")
            m = re.search(r"([\d.]+)px", ml)
            return float(m.group(1)) * 0.75 if m else 0.0

        _cache = {}

        def _sty(align=TA_LEFT, indent=0.0, size=10.5, bold=False):
            key = (align, round(indent), size, bold)
            if key not in _cache:
                _cache[key] = ParagraphStyle(
                    "RS%d" % len(_cache),
                    parent=base["Normal"],
                    fontName="Helvetica-Bold" if bold else "Helvetica",
                    fontSize=size,
                    leading=size * 1.55,
                    spaceAfter=5,
                    alignment=align,
                    leftIndent=indent,
                )
            return _cache[key]

        H_STYS = {
            "h1": _sty(size=16, bold=True),
            "h2": _sty(size=14, bold=True),
            "h3": _sty(size=12, bold=True),
            "h4": _sty(size=11, bold=True),
            "h5": _sty(size=10, bold=True),
            "h6": _sty(size=10, bold=True),
        }
        TD_S = _sty(size=9)
        TH_S = _sty(size=9, bold=True)
        PRE_S = ParagraphStyle(
            "RPRE",
            parent=base["Code"],
            fontName="Courier",
            fontSize=9,
            leading=13,
            spaceAfter=6,
            backColor=colors.HexColor("#f5f5f5"),
        )

        _CLS_RE = re.compile(r"""class=['"]([^'"]+)['"]""", re.I)
        _STY_RE = re.compile(r"""style=['"]([^'"]*?)['"]""", re.I)
        _SRC_RE = re.compile(r"""src=['"]([^'"]+)['"]""", re.I)

        def _resolve(attrs):
            align = None
            indent = 0.0
            cm = _CLS_RE.search(attrs)
            if cm:
                for c in cm.group(1).split():
                    rd = class_rules.get(c, {})
                    a = _decls_to_align(rd)
                    if a is not None:
                        align = a
                    i = _decls_to_indent(rd)
                    if i:
                        indent = i
            sm = _STY_RE.search(attrs)
            if sm:
                decl_str = sm.group(1)
                rd2 = {}
                for d in decl_str.split(";"):
                    d = d.strip()
                    if ":" not in d:
                        continue
                    p, _, v = d.partition(":")
                    rd2[p.strip().lower()] = v.strip()
                a2 = _decls_to_align(rd2)
                if a2 is not None:
                    align = a2
                i2 = _decls_to_indent(rd2)
                if i2:
                    indent = i2
            return (align or TA_LEFT), indent

        def _decode(t):
            return (
                t.replace("&nbsp;", "\xa0")
                .replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&quot;", '"')
                .replace("&#39;", "'")
            )

        def _inline(frag):
            return inline_markup(frag, decode_fn=_decode, preserve_font_tags=False)

        tmp_imgs = []

        def _add_img(src_val):
            if not src_val.startswith("data:"):
                return
            add_image_flowable(story, src_val, MAX_W, tmp_imgs)

        def _parse_tbl(tbl_html):
            return build_table_flowable(tbl_html, _inline, TD_S, TH_S)

        h2 = re.sub(r"<head[^>]*>.*?</head>", "", html, flags=re.I | re.S)
        h2 = re.sub(r"<script[^>]*>.*?</script>", "", h2, flags=re.I | re.S)
        bm = re.search(r"<body[^>]*>(.*?)</body>", h2, re.I | re.S)
        body = bm.group(1) if bm else h2

        story = []

        TAG_RE = re.compile(r"<(/?)(\w+)((?:\s[^>]*)?)/?>", re.I)
        pos = 0

        for m in TAG_RE.finditer(body):
            pos = m.end()
            closing = m.group(1)
            tag = m.group(2).lower()
            attrs = m.group(3) or ""

            if tag == "hr" and not closing:
                story.append(
                    HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#ccc"), spaceAfter=5, spaceBefore=5)
                )

            elif tag in ("h1", "h2", "h3", "h4", "h5", "h6") and not closing:
                em = re.search(r"</" + tag + r"\s*>", body[pos:], re.I)
                if em:
                    txt = _inline(body[pos : pos + em.start()])
                    pos += em.end()
                    if txt:
                        story.append(Paragraph(txt, H_STYS.get(tag, H_STYS["h4"])))

            elif tag == "p" and not closing:
                align, indent = _resolve(attrs)
                em = re.search(r"</p\s*>", body[pos:], re.I)
                if em:
                    inner = body[pos : pos + em.start()]
                    pos += em.end()
                    for im in re.finditer(r"<img[^>]+>", inner, re.I):
                        sm = _SRC_RE.search(im.group(0))
                        if sm:
                            _add_img(sm.group(1))
                    txt = _inline(inner)
                    if txt.strip():
                        story.append(Paragraph(txt, _sty(align, indent)))

            elif tag == "div" and not closing:
                cm2 = _CLS_RE.search(attrs)
                if cm2 and "pn" in cm2.group(1).split():
                    em = re.search(r"</div\s*>", body[pos:], re.I)
                    if em:
                        pos += em.end()

            elif tag == "li" and not closing:
                em = re.search(r"</li\s*>", body[pos:], re.I)
                if em:
                    txt = _inline(body[pos : pos + em.start()])
                    pos += em.end()
                    if txt.strip():
                        story.append(Paragraph("• " + txt, _sty()))

            elif tag == "blockquote" and not closing:
                em = re.search(r"</blockquote\s*>", body[pos:], re.I)
                if em:
                    txt = _inline(body[pos : pos + em.start()])
                    pos += em.end()
                    if txt:
                        story.append(Paragraph(txt, _sty(indent=18)))

            elif tag == "pre" and not closing:
                em = re.search(r"</pre\s*>", body[pos:], re.I)
                if em:
                    raw = re.sub(r"<[^>]+>", "", body[pos : pos + em.start()])
                    pos += em.end()
                    safe = (
                        _decode(raw)
                        .replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                        .replace("\n", "<br/>")
                    )
                    story.append(Paragraph(safe, PRE_S))

            elif tag == "img" and not closing:
                sm = _SRC_RE.search(attrs)
                if sm:
                    _add_img(sm.group(1))

            elif tag == "table" and not closing:
                em = re.search(r"</table\s*>", body[pos:], re.I)
                if em:
                    tbl = _parse_tbl(body[pos : pos + em.start()])
                    pos += em.end()
                    if tbl:
                        story.append(Spacer(1, 6))
                        story.append(tbl)
                        story.append(Spacer(1, 6))

        if not story:
            story.append(Paragraph("(empty)", _sty()))

        SimpleDocTemplate(
            dst, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=20 * mm, bottomMargin=20 * mm
        ).build(story)
        for f in tmp_imgs:
            try:
                os.remove(f)
            except Exception:
                pass
