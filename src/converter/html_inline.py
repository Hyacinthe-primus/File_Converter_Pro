"""Shared HTML→ReportLab helpers used by _reportlab_html_to_pdf and _epub_to_pdf_native."""

from __future__ import annotations

import base64
import re
import tempfile

from reportlab.lib import colors
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle


def decode_entities(text: str) -> str:
    """Decode common HTML entities to unicode."""
    replacements = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&apos;": "'",
        "&nbsp;": " ",
        "&#8211;": "–",
        "&#8212;": "—",
        "&#8216;": "‘",
        "&#8217;": "’",
        "&#8220;": "“",
        "&#8221;": "”",
        "&hellip;": "…",
        "&mdash;": "—",
        "&ndash;": "–",
        "&laquo;": "«",
        "&raquo;": "»",
        "&eacute;": "é",
        "&egrave;": "è",
        "&agrave;": "à",
        "&ccedil;": "ç",
        "&ocirc;": "ô",
        "&ucirc;": "û",
    }
    for entity, char in replacements.items():
        text = text.replace(entity, char)
    text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
    text = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), text)
    return text


def inline_markup(frag: str, *, decode_fn=None, preserve_font_tags: bool = False) -> str:
    """Convert inline HTML to ReportLab XML markup.

    Handles <b>, <i>, <strong>, <em>, <span style="...">, <code>, <a>, <br>.

    Args:
        frag: HTML fragment with inline tags.
        decode_fn: Optional callable to decode entities (default: decode_entities).
        preserve_font_tags: If True, keep <font> tags for Courier (for EPUB).
                            If False, strip <code> tags (for HTML→PDF).
    """
    if decode_fn is None:
        decode_fn = decode_entities

    h = frag

    def _span_style(m):
        style_attr = re.search(r'style=["\']([^"\']*)["\']', m.group(1) or "", re.I)
        bold, italic, color, size = False, False, None, None
        if style_attr:
            s = style_attr.group(1)
            fw = re.search(r"font-weight\s*:\s*(\w+)", s, re.I)
            fi = re.search(r"font-style\s*:\s*(\w+)", s, re.I)
            fc = re.search(r"color\s*:\s*(#[\da-fA-F]{3,8}|\w+)", s, re.I)
            fs = re.search(r"font-size\s*:\s*([\d.]+)px", s, re.I)
            if fw and fw.group(1).lower() in ("bold", "700", "800", "900"):
                bold = True
            if fi and fi.group(1).lower() == "italic":
                italic = True
            if fc:
                color = fc.group(1)
            if fs:
                size = fs.group(1)
        inner = m.group(2)
        if bold:
            inner = f"<b>{inner}</b>"
        if italic:
            inner = f"<i>{inner}</i>"
        if color:
            inner = f'<font color="{color}">{inner}</font>'
        if size:
            inner = f'<font size="{size}">{inner}</font>'
        return inner

    h = re.sub(r"<span([^>]*)>(.*?)</span>", _span_style, h, flags=re.I | re.S)
    h = re.sub(r"<strong[^>]*>(.*?)</strong>", r"<b>\1</b>", h, flags=re.I | re.S)
    h = re.sub(r"<b[^>]*>(.*?)</b>", r"<b>\1</b>", h, flags=re.I | re.S)
    h = re.sub(r"<em[^>]*>(.*?)</em>", r"<i>\1</i>", h, flags=re.I | re.S)
    h = re.sub(r"<i[^>]*>(.*?)</i>", r"<i>\1</i>", h, flags=re.I | re.S)
    h = re.sub(r"<br\s*/?>", " ", h, flags=re.I)
    h = re.sub(r"<a[^>]*>(.*?)</a>", r"\1", h, flags=re.I | re.S)

    if preserve_font_tags:
        h = re.sub(r"<code[^>]*>(.*?)</code>", r"<font name='Courier'>\1</font>", h, flags=re.I | re.S)
    else:
        h = re.sub(r"<code[^>]*>(.*?)</code>", r"\1", h, flags=re.I | re.S)

    h = re.sub(r"<[^>]+>", "", h)
    h = decode_fn(h)

    h = h.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    for tag in ("b", "i"):
        h = h.replace(f"&lt;{tag}&gt;", f"<{tag}>").replace(f"&lt;/{tag}&gt;", f"</{tag}>")
    h = h.replace("&lt;font name='Courier'&gt;", "<font name='Courier'>").replace("&lt;/font&gt;", "</font>")

    return re.sub(r"\s{2,}", " ", h).strip()


def build_table_flowable(
    tbl_html: str,
    inline_fn,
    td_style,
    th_style,
    *,
    header_bg: str = "#f0f0f0",
) -> Table | None:
    """Parse <table> HTML and return a reportlab Table flowable.

    Args:
        tbl_html: HTML table content (between <table> and </table>).
        inline_fn: Function to convert inline HTML to reportlab XML.
        td_style: ParagraphStyle for body cells.
        th_style: ParagraphStyle for header cells.
        header_bg: Background color for header rows.
    """
    rows = []
    for rm in re.finditer(r"<tr[^>]*>(.*?)</tr>", tbl_html, re.I | re.S):
        cells = []
        hdr = False
        for cm in re.finditer(r"<(td|th)[^>]*>(.*?)</(td|th)>", rm.group(1), re.I | re.S):
            t = cm.group(1).lower()
            cells.append(Paragraph(inline_fn(cm.group(2)) or " ", th_style if t == "th" else td_style))
            if t == "th":
                hdr = True
        if cells:
            rows.append((cells, hdr))

    if not rows:
        return None

    n = max(len(r) for r, _ in rows)
    data = []
    cmds = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for ri, (row, hdr) in enumerate(rows):
        while len(row) < n:
            row.append(Paragraph(" ", td_style))
        data.append(row)
        if hdr:
            cmds.append(("BACKGROUND", (0, ri), (-1, ri), colors.HexColor(header_bg)))

    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle(cmds))
    return t


_EPS_MIME_TYPES = {
    "application/eps",
    "application/postscript",
    "image/eps",
    "image/postscript",
    "image/x-eps",
}
_EPS_MAGIC_PREFIXES = (b"%!PS",)
_IMAGE_EXTENSIONS = {"bmp", "gif", "jpeg", "jpg", "png", "svg", "tif", "tiff", "webp"}


def add_image_flowable(
    story: list,
    src_val: str,
    max_width: float,
    tmp_imgs_list: list,
    *,
    caption: str | None = None,
    caption_style=None,
) -> bool:
    """Add an image from a data URI to the story.

    Args:
        story: Reportlab story list to append to.
        src_val: Data URI (data:image/png;base64,...).
        max_width: Maximum width in points.
        tmp_imgs_list: List to track temp files for cleanup.
        caption: Optional caption text.
        caption_style: ParagraphStyle for caption.
    """
    try:
        if not src_val.startswith("data:"):
            return False
        header, separator, payload = src_val[5:].partition(",")
        if not separator:
            return False
        mime = header.split(";", 1)[0].strip().lower()
        if mime in _EPS_MIME_TYPES:
            return False
        raw = base64.b64decode(payload)
        if raw.lstrip().startswith(_EPS_MAGIC_PREFIXES):
            return False
        ext = mime.split("/")[-1].split("+", 1)[0].lower()
        if ext not in _IMAGE_EXTENSIONS:
            ext = "png"
        tf = tempfile.NamedTemporaryFile(suffix="." + ext, delete=False)
        tf.write(raw)
        tf.close()
        tmp_imgs_list.append(tf.name)
        rl = RLImage(tf.name)

        if rl.imageWidth > max_width:
            s = max_width / rl.imageWidth
            rl.drawWidth = rl.imageWidth * s
            rl.drawHeight = rl.imageHeight * s
        rl.hAlign = "CENTER"
        story.append(Spacer(1, 6))
        story.append(rl)
        if caption and caption_style:
            story.append(Paragraph(caption, caption_style))
        story.append(Spacer(1, 6))
        return True
    except Exception:
        return False
