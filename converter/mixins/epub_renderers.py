"""EPUB -> PDF rendering (pypandoc > native engine)."""

from __future__ import annotations

import base64
import os
import re
import tempfile
import zipfile
from pathlib import Path

from converter.html_inline import build_table_flowable, inline_markup


class EpubRenderers:
    """EPUB -> PDF conversions."""

    def _epub_to_pdf(self, src, dst):
        """
        EPUB → PDF strategies:
        1. pypandoc (pandoc binary) — best typographic output
        2. Native engine             — fully self-contained, no binary needed
           Handles: spine order, cover image, metadata title, h1-h6,
           p, li (ul/ol), blockquote, br, strong/em/b/i, inline images
           at correct position in text flow.
        """
        try:
            import pypandoc

            from external_binaries import resolve_binary

            _pandoc = resolve_binary("pandoc")
            if _pandoc:
                os.environ["PANDOC"] = _pandoc
            pypandoc.convert_file(src, "pdf", outputfile=dst)
            return
        except Exception:
            pass
        self._epub_to_pdf_native(src, dst)

    def _epub_to_pdf_native(self, src, dst):
        """
        Native EPUB → PDF — peak quality.
        Improvements over previous version:
        - Tables rendered as reportlab Table objects
        - <ol> with real numbering (1. 2. 3.)
        - <pre>/<code> in monospace box
        - <figure>/<figcaption> with caption
        - <span style="..."> inline CSS (font-size, font-weight, color)
        - Image path resolution handles ../../../ deep relative paths
        - CSS font-size extracted from embedded <style> blocks
        """
        from xml.etree import ElementTree as ET

        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            HRFlowable,
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
        )
        from reportlab.platypus import (
            Image as RLImage,
        )

        base = getSampleStyleSheet()

        def _sty(name, **kw):
            parent = kw.pop("parent", base["Normal"])
            return ParagraphStyle(name, parent=parent, **kw)

        sty = {
            "title": _sty(
                "ET",
                parent=base["Title"],
                fontSize=22,
                leading=28,
                spaceAfter=16,
                textColor=colors.HexColor("#1a1a2e"),
                alignment=TA_CENTER,
            ),
            "author": _sty(
                "EA", fontSize=13, leading=18, spaceAfter=6, textColor=colors.HexColor("#555"), alignment=TA_CENTER
            ),
            "h1": _sty(
                "EH1",
                parent=base["Heading1"],
                fontSize=18,
                leading=22,
                spaceBefore=14,
                spaceAfter=8,
                textColor=colors.HexColor("#1a1a2e"),
            ),
            "h2": _sty(
                "EH2",
                parent=base["Heading2"],
                fontSize=15,
                leading=19,
                spaceBefore=10,
                spaceAfter=6,
                textColor=colors.HexColor("#1e3a5f"),
            ),
            "h3": _sty(
                "EH3",
                parent=base["Heading3"],
                fontSize=13,
                leading=17,
                spaceBefore=8,
                spaceAfter=4,
                textColor=colors.HexColor("#1e3a5f"),
            ),
            "h4": _sty(
                "EH4",
                fontSize=11,
                leading=15,
                spaceBefore=6,
                spaceAfter=3,
                fontName="Helvetica-Bold",
                textColor=colors.HexColor("#333"),
            ),
            "h5": _sty("EH5", fontSize=10.5, leading=14, spaceBefore=4, spaceAfter=2, fontName="Helvetica-Bold"),
            "h6": _sty("EH6", fontSize=10, leading=13, spaceBefore=4, spaceAfter=2, fontName="Helvetica-BoldOblique"),
            "body": _sty("EB", fontSize=10.5, leading=16, spaceAfter=5, alignment=TA_JUSTIFY),
            "bq": _sty(
                "EBQ",
                fontSize=10,
                leading=15,
                spaceAfter=5,
                leftIndent=24,
                rightIndent=12,
                textColor=colors.HexColor("#555"),
            ),
            "li_ul": _sty("ELU", fontSize=10.5, leading=15, spaceAfter=3, leftIndent=16),
            "li_ol": _sty("ELO", fontSize=10.5, leading=15, spaceAfter=3, leftIndent=20),
            "pre": _sty(
                "EPR",
                fontName="Courier",
                fontSize=9,
                leading=13,
                spaceAfter=8,
                spaceBefore=4,
                leftIndent=12,
                rightIndent=12,
                backColor=colors.HexColor("#f5f5f5"),
                borderColor=colors.HexColor("#ddd"),
                borderWidth=0.5,
                borderPad=6,
            ),
            "caption": _sty(
                "EC", fontSize=9, leading=12, spaceAfter=8, textColor=colors.HexColor("#777"), alignment=TA_CENTER
            ),
            "td": _sty("ETd", fontSize=9, leading=12, spaceAfter=0),
            "th": _sty("ETh", fontSize=9, leading=12, spaceAfter=0, fontName="Helvetica-Bold"),
        }

        H_STYS = {"h1": "h1", "h2": "h2", "h3": "h3", "h4": "h4", "h5": "h5", "h6": "h6"}

        story = []
        tmp_imgs = []
        PAGE_W = A4[0] - 40 * mm

        def _decode(text):
            return (
                text.replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&quot;", '"')
                .replace("&apos;", "'")
                .replace("&nbsp;", "\xa0")
            )

        def _rl_safe(text):
            d = _decode(text)
            return d.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        def _css_to_inline(style_str):
            """Parse a CSS style attribute into reportlab-compatible markup hints."""
            bold = False
            italic = False
            color = None
            size = None
            for decl in style_str.split(";"):
                decl = decl.strip()
                if not decl or ":" not in decl:
                    continue
                prop, _, val = decl.partition(":")
                prop = prop.strip().lower()
                val = val.strip()
                if prop == "font-weight" and val in ("bold", "700", "800", "900"):
                    bold = True
                elif prop == "font-style" and val == "italic":
                    italic = True
                elif prop == "color":
                    color = val
                elif prop == "font-size":
                    try:
                        size = float(re.sub(r"[^0-9.]", "", val))
                    except Exception:
                        pass
            return bold, italic, color, size

        def _inline_markup(frag):
            return inline_markup(frag, decode_fn=_decode, preserve_font_tags=True)

        def _add_img(raw_bytes, ext, alt=""):
            try:
                tf = tempfile.NamedTemporaryFile(suffix=f".{ext or 'png'}", delete=False)
                tf.write(raw_bytes)
                tf.close()
                tmp_imgs.append(tf.name)
                rl = RLImage(tf.name)
                scale = min(PAGE_W / rl.imageWidth, (A4[1] * 0.5) / rl.imageHeight, 1.0)
                rl.drawWidth = rl.imageWidth * scale
                rl.drawHeight = rl.imageHeight * scale
                rl.hAlign = "CENTER"
                story.append(Spacer(1, 6))
                story.append(rl)
                if alt and alt.lower() not in ("", "image", "cover"):
                    story.append(Paragraph(_rl_safe(alt), sty["caption"]))
                story.append(Spacer(1, 6))
                return True
            except Exception:
                return False

        def _resolve_img(src_attr, chap_dir, img_data):
            """Resolve image src with robust path normalisation."""
            if not src_attr:
                return None
            if src_attr.startswith("data:"):
                try:
                    b64 = src_attr.split(",", 1)[1]
                    raw = base64.b64decode(b64)
                    ext = re.search(r"data:image/(\w+)", src_attr)
                    return raw, (ext.group(1) if ext else "png")
                except Exception:
                    return None

            raw_p = src_attr.split("?")[0].split("#")[0]
            try:
                from pathlib import PurePosixPath

                resolved = str(PurePosixPath(chap_dir) / raw_p)
            except Exception:
                resolved = f"{chap_dir}/{raw_p}"

            candidates = set()
            for c in [raw_p, resolved, raw_p.lstrip("/"), resolved.lstrip("/")]:
                c_norm = c.replace("\\", "/")
                while c_norm.startswith("./"):
                    c_norm = c_norm[2:]
                candidates.add(c_norm)
                parts = c_norm.split("/")
                if len(parts) > 1:
                    candidates.add(parts[-1])

            for c in candidates:
                b = img_data.get(c)
                if b:
                    return b, Path(c).suffix.lstrip(".")
                fname = c.split("/")[-1]
                for k in img_data:
                    if k.split("/")[-1] == fname:
                        return img_data[k], Path(fname).suffix.lstrip(".")
            return None

        def _parse_table(table_html, chap_dir, img_data):
            return build_table_flowable(table_html, _inline_markup, sty["td"], sty["th"], header_bg="#e8edf5")

        def _parse_chapter(html_raw, chap_dir, img_data):
            html = re.sub(r'\s+xmlns(?::\w+)?=["\'][^"\']*["\']', "", html_raw)
            bm = re.search(r"<body[^>]*>(.*?)</body>", html, re.I | re.S)
            body = bm.group(1) if bm else html
            body = re.sub(r"<head[^>]*>.*?</head>", "", body, flags=re.I | re.S)
            body = re.sub(r"<script[^>]*>.*?</script>", "", body, flags=re.I | re.S)
            body = re.sub(r"<style[^>]*>.*?</style>", "", body, flags=re.I | re.S)

            TAG_RE = re.compile(r"<(/?)(\w+)((?:\s[^>]*)?)/?>", re.I)
            pos = 0
            buf = ""
            ol_count = [0]

            def flush_buf():
                nonlocal buf
                text = _inline_markup(buf)
                buf = ""
                if text.strip():
                    story.append(Paragraph(text, sty["body"]))

            for m in TAG_RE.finditer(body):
                buf += body[pos : m.start()]
                pos = m.end()
                closing, tag, attrs_str = m.group(1), m.group(2).lower(), m.group(3) or ""

                block_tags = {
                    "p",
                    "div",
                    "h1",
                    "h2",
                    "h3",
                    "h4",
                    "h5",
                    "h6",
                    "br",
                    "hr",
                    "li",
                    "img",
                    "figure",
                    "figcaption",
                    "table",
                    "ul",
                    "ol",
                    "pre",
                    "blockquote",
                    "section",
                    "article",
                    "header",
                    "footer",
                    "aside",
                    "nav",
                }
                if tag in block_tags:
                    flush_buf()

                if tag == "br" and not closing:
                    story.append(Spacer(1, 4))

                elif tag == "hr" and not closing:
                    story.append(
                        HRFlowable(
                            width="100%", thickness=0.5, color=colors.HexColor("#ccc"), spaceAfter=6, spaceBefore=6
                        )
                    )

                elif tag in H_STYS and not closing:
                    end_m = re.search(rf"</{tag}\s*>", body[pos:], re.I)
                    if end_m:
                        inner = _inline_markup(body[pos : pos + end_m.start()])
                        pos += end_m.end()
                        if inner:
                            story.append(Spacer(1, 4))
                            story.append(Paragraph(inner, sty[H_STYS[tag]]))

                elif tag == "p" and not closing:
                    end_m = re.search(r"</p\s*>", body[pos:], re.I)
                    if end_m:
                        inner_html = body[pos : pos + end_m.start()]
                        pos += end_m.end()
                        for img_m in re.finditer(r"<img[^>]+>", inner_html, re.I):
                            sm = re.search(r"""src=(['"])([^'"]+)\1""", img_m.group(0), re.I)
                            if sm:
                                res = _resolve_img(sm.group(2), chap_dir, img_data)
                                if res:
                                    alt_m = re.search(r"""alt=(['"])([^'"]*)\1""", img_m.group(0), re.I)
                                    _add_img(res[0], res[1], alt_m.group(2) if alt_m else "")
                        text = _inline_markup(inner_html)
                        if text.strip():
                            story.append(Paragraph(text, sty["body"]))

                elif tag in ("div", "section", "article", "header", "footer", "aside", "nav") and not closing:
                    pass

                elif tag == "blockquote" and not closing:
                    end_m = re.search(r"</blockquote\s*>", body[pos:], re.I)
                    if end_m:
                        inner = _inline_markup(body[pos : pos + end_m.start()])
                        pos += end_m.end()
                        if inner:
                            story.append(Paragraph(inner, sty["bq"]))

                elif tag == "pre" and not closing:
                    end_m = re.search(r"</pre\s*>", body[pos:], re.I)
                    if end_m:
                        raw_pre = body[pos : pos + end_m.start()]
                        pos += end_m.end()
                        text = re.sub(r"<[^>]+>", "", raw_pre)
                        text = _decode(text)
                        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        story.append(Paragraph(safe.replace("\n", "<br/>"), sty["pre"]))

                elif tag == "ol" and not closing:
                    ol_count[0] = 0
                elif tag == "ul" and not closing:
                    ol_count[0] = -1

                elif tag == "li" and not closing:
                    end_m = re.search(r"</li\s*>", body[pos:], re.I)
                    if end_m:
                        inner = _inline_markup(body[pos : pos + end_m.start()])
                        pos += end_m.end()
                        if inner.strip():
                            if ol_count[0] >= 0:
                                ol_count[0] += 1
                                prefix = f"{ol_count[0]}. "
                                ps = sty["li_ol"]
                            else:
                                prefix = "• "
                                ps = sty["li_ul"]
                            story.append(Paragraph(prefix + inner, ps))

                elif tag == "img" and not closing:
                    sm = re.search(r"""src=(['"])([^'"]+)\1""", attrs_str, re.I)
                    if sm:
                        res = _resolve_img(sm.group(2), chap_dir, img_data)
                        if res:
                            alt_m = re.search(r"""alt=(['"])([^'"]*)\1""", attrs_str, re.I)
                            _add_img(res[0], res[1], alt_m.group(2) if alt_m else "")

                elif tag == "figure" and not closing:
                    pass

                elif tag == "figcaption" and not closing:
                    end_m = re.search(r"</figcaption\s*>", body[pos:], re.I)
                    if end_m:
                        inner = _inline_markup(body[pos : pos + end_m.start()])
                        pos += end_m.end()
                        if inner:
                            story.append(Paragraph(inner, sty["caption"]))

                elif tag == "table" and not closing:
                    end_m = re.search(r"</table\s*>", body[pos:], re.I)
                    if end_m:
                        tbl = _parse_table(body[pos : pos + end_m.start()], chap_dir, img_data)
                        pos += end_m.end()
                        if tbl:
                            story.append(Spacer(1, 8))
                            story.append(tbl)
                            story.append(Spacer(1, 8))

            buf += body[pos:]
            flush_buf()

        with zipfile.ZipFile(src) as zf:
            names = zf.namelist()
            spine_order = []
            book_title = Path(src).stem
            book_authors = []
            cover_data = None
            opf_dir = ""

            try:
                container = zf.read("META-INF/container.xml").decode("utf-8", "replace")
                opf_m = re.search(r"full-path=[\"']([^\"']+\.opf)[\"']", container, re.I)
                if opf_m:
                    opf_path = opf_m.group(1)
                    opf_dir = str(Path(opf_path).parent)
                    opf_xml = zf.read(opf_path).decode("utf-8", "replace")
                    root = ET.fromstring(opf_xml)
                    ns_opf = {"o": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/"}
                    t_el = root.find(".//dc:title", ns_opf)
                    if t_el is not None and t_el.text:
                        book_title = t_el.text.strip()
                    for cr in root.findall(".//dc:creator", ns_opf):
                        if cr.text:
                            book_authors.append(cr.text.strip())
                    manifest = {}
                    for item in root.findall(".//o:item", ns_opf):
                        iid = item.get("id", "")
                        href = item.get("href", "")
                        mtype = item.get("media-type", "")
                        full = f"{opf_dir}/{href}".lstrip("/")
                        manifest[iid] = {"href": href, "full": full, "type": mtype}
                    cover_id = None
                    mc = root.find(".//o:meta[@name='cover']", ns_opf)
                    if mc is not None:
                        cover_id = mc.get("content", "")
                    if not cover_id:
                        for iid, v in manifest.items():
                            if "cover" in iid.lower() and "image" in v["type"]:
                                cover_id = iid
                                break
                    if cover_id and cover_id in manifest:
                        cpath = manifest[cover_id]["full"]
                        try:
                            cover_data = (zf.read(cpath), Path(cpath).suffix.lstrip("."))
                        except Exception:
                            pass
                    for ref in root.findall(".//o:itemref", ns_opf):
                        iid = ref.get("idref", "")
                        if iid in manifest:
                            full = manifest[iid]["full"]
                            if full in names:
                                spine_order.append(full)
            except Exception:
                pass

            if not spine_order:
                spine_order = sorted(n for n in names if n.endswith((".xhtml", ".html", ".htm")))

            img_data = {}
            for n in names:
                ext = Path(n).suffix.lower().lstrip(".")
                if ext in ("png", "jpg", "jpeg", "gif", "webp", "bmp", "svg"):
                    try:
                        key = n.replace("\\", "/").lstrip("/")
                        img_data[key] = zf.read(n)
                    except Exception:
                        pass

            if cover_data:
                _add_img(cover_data[0], cover_data[1], "cover")
                story.append(PageBreak())

            story.append(Spacer(1, 30 * mm))
            story.append(Paragraph(_rl_safe(book_title), sty["title"]))
            if book_authors:
                story.append(Spacer(1, 6))
                for auth in book_authors:
                    story.append(Paragraph(_rl_safe(auth), sty["author"]))
            story.append(PageBreak())

            for chap in spine_order:
                try:
                    raw = zf.read(chap).decode("utf-8", "replace")
                    chap_dir = str(Path(chap).parent).replace("\\", "/")
                    _parse_chapter(raw, chap_dir, img_data)
                    story.append(PageBreak())
                except Exception:
                    continue

        if len(story) <= 2:
            raise RuntimeError("No content could be extracted from this EPUB.")

        def _safe_str(s):
            return s if isinstance(s, str) else ""

        SimpleDocTemplate(
            dst,
            pagesize=A4,
            leftMargin=22 * mm,
            rightMargin=22 * mm,
            topMargin=22 * mm,
            bottomMargin=22 * mm,
            title=_safe_str(book_title),
            author=", ".join(book_authors) if book_authors else "",
        ).build(story)

        for f in tmp_imgs:
            try:
                os.remove(f)
            except Exception:
                pass
