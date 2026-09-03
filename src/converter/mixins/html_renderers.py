"""HTML -> PDF rendering (pdfkit > weasyprint > reportlab fallback)."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from converter.helpers import _img_to_b64, _mime_for_ext
from converter.html_inline import add_image_flowable, build_table_flowable, inline_markup


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

        with open(src, "r", encoding="utf-8", errors="replace") as f:
            html_raw = f.read()

        html = self._inline_all_resources(html_raw, base_dir)

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
                        "enable-local-file-access": "",
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

            import weasyprint

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                weasyprint.HTML(string=html, base_url=base_dir.as_uri()).write_pdf(dst)
            return
        except Exception:
            pass

        # Strategy 3: reportlab
        self._reportlab_html_to_pdf(html, dst)

    def _inline_all_resources(self, html, base_dir):
        """Inline all local img/css/url resources as base64 data-URIs."""
        SRC_RE = re.compile(r"""src=(['"])([^'"]+)\1""", re.I)
        HREF_RE = re.compile(r"""href=(['"])([^'"]+)\1""", re.I)

        def _link_to_style(m):
            tag = m.group(0)
            if "stylesheet" not in tag.lower():
                return tag
            hm = HREF_RE.search(tag)
            if not hm:
                return tag
            href = hm.group(2)
            if href.startswith(("http://", "https://", "data:", "//")):
                return tag
            css_path = base_dir / href
            if not css_path.exists():
                return tag
            try:
                css = css_path.read_text(encoding="utf-8", errors="replace")
                css = self._inline_css_urls(css, css_path.parent)
                return "<style>" + css + "</style>"
            except Exception:
                return tag

        html = re.sub(r"<link[^>]+>", _link_to_style, html, flags=re.I | re.S)

        def _style_block(m):
            return "<style>" + self._inline_css_urls(m.group(1), base_dir) + "</style>"

        html = re.sub(r"<style[^>]*>(.*?)</style>", _style_block, html, flags=re.I | re.S)

        def _img_src(m):
            tag = m.group(0)
            sm = SRC_RE.search(tag)
            if not sm:
                return tag
            val = sm.group(2)
            if val.startswith(("http://", "https://", "data:")):
                return tag
            p = base_dir / val
            if not p.exists():
                return tag
            try:
                b64 = _img_to_b64(p.read_bytes(), _mime_for_ext(p.suffix.lstrip(".")))
                return SRC_RE.sub('src="' + b64 + '"', tag, count=1)
            except Exception:
                return tag

        html = re.sub(r"<img[^>]+>", _img_src, html, flags=re.I | re.S)
        return html

    def _inline_css_urls(self, css, base_dir):
        """Replace url(path) in CSS with base64 data URIs."""
        URL_RE = re.compile(r"url\\(\\s*([\"']?)([^)'\"]+)\\1\\s*\\)", re.I)

        def repl(m):
            raw = m.group(2).strip()
            if raw.startswith(("http://", "https://", "data:")):
                return m.group(0)
            p = base_dir / raw
            if not p.exists():
                return m.group(0)
            try:
                b64 = _img_to_b64(p.read_bytes(), _mime_for_ext(p.suffix.lstrip(".")))
                return "url('" + b64 + "')"
            except Exception:
                return m.group(0)

        return URL_RE.sub(repl, css)

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
