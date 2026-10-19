"""Native (no LibreOffice) previews of OpenDocument files: ODT, ODS and ODP.

Pure parsing helpers, with no Qt dependency except the small data containers:
    - read_thumbnail(path)  -> PNG bytes embedded by the authoring app (first page)
    - odt_to_html(path)     -> OdtPreview(html, images)   (text, lists, tables, images)
    - ods_sheets(path)      -> [(sheet name, rows)]       (values as displayed)
    - odp_slides(path)      -> [[text line, ...], ...]    (text of each slide)

This is a simplified view: no page layout, headers/footers, charts or exact
fonts. Everything is size-capped so a huge document cannot freeze the UI.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from html import escape

from odf import teletype
from odf.namespaces import DRAWNS, FONS, OFFICENS, STYLENS, TABLENS, TEXTNS, XLINKNS
from odf.opendocument import load

MAX_FILE_BYTES = 60 * 1024 * 1024
MAX_BLOCKS = 1500
MAX_ROWS = 200
MAX_COLS = 60
MAX_SHEETS = 8
MAX_SLIDES = 100
MAX_IMAGES = 30
MAX_IMAGE_BYTES = 6 * 1024 * 1024
THUMBNAIL_PATH = "Thumbnails/thumbnail.png"
MAX_THUMBNAIL_BYTES = 3 * 1024 * 1024

_TEXT_NODE = 3


class OdfTooLarge(Exception):
    """The file is too big to preview natively."""


@dataclass
class OdtPreview:
    html: str = ""
    images: dict[str, bytes] = field(default_factory=dict)  # resource name -> raw image bytes

    @property
    def is_empty(self) -> bool:
        return not self.html.strip()


def _check_size(path: str) -> None:
    import os

    if os.path.getsize(path) > MAX_FILE_BYTES:
        raise OdfTooLarge(path)


def read_thumbnail(path: str) -> bytes | None:
    """The first-page thumbnail LibreOffice/OpenOffice store in the file, if any."""
    try:
        with zipfile.ZipFile(path) as zf:
            info = zf.getinfo(THUMBNAIL_PATH)
            if info.file_size > MAX_THUMBNAIL_BYTES:
                return None
            return zf.read(THUMBNAIL_PATH)
    except (KeyError, zipfile.BadZipFile, OSError):
        return None


def _attr(el, ns: str, name: str):
    return el.getAttrNS(ns, name)


def _is(node, ns: str, name: str) -> bool:
    return getattr(node, "qname", None) == (ns, name)


# ---------------------------------------------------------------------------
# ODT
# ---------------------------------------------------------------------------


def _text_styles(doc) -> dict[str, tuple[bool, bool, bool]]:
    """style name -> (bold, italic, underline) from the document's styles."""
    result: dict[str, tuple[bool, bool, bool]] = {}
    for container in (doc.automaticstyles, doc.styles):
        for st in container.childNodes:
            if not _is(st, STYLENS, "style"):
                continue
            name = _attr(st, STYLENS, "name")
            for props in st.childNodes:
                if _is(props, STYLENS, "text-properties"):
                    bold = _attr(props, FONS, "font-weight") in ("bold", "700", "800", "900")
                    italic = _attr(props, FONS, "font-style") in ("italic", "oblique")
                    underline = _attr(props, STYLENS, "text-underline-style") not in (None, "none")
                    result[name] = (bold, italic, underline)
    return result


class _OdtRenderer:
    def __init__(self, doc):
        self.doc = doc
        self.styles = _text_styles(doc)
        self.images: dict[str, bytes] = {}
        self.blocks = 0

    # -- inline ------------------------------------------------------------

    def inline(self, node) -> str:
        out = []
        for ch in node.childNodes:
            if ch.nodeType == _TEXT_NODE:
                out.append(escape(ch.data))
                continue
            if _is(ch, TEXTNS, "span"):
                out.append(self._styled(ch))
            elif _is(ch, TEXTNS, "a"):
                href = _attr(ch, XLINKNS, "href") or ""
                inner = self.inline(ch)
                out.append(f'<a href="{escape(href, quote=True)}">{inner}</a>' if href else inner)
            elif _is(ch, TEXTNS, "s"):
                out.append("&nbsp;" * int(_attr(ch, TEXTNS, "c") or 1))
            elif _is(ch, TEXTNS, "tab"):
                out.append("&nbsp;" * 4)
            elif _is(ch, TEXTNS, "line-break"):
                out.append("<br>")
            elif _is(ch, DRAWNS, "frame") or _is(ch, DRAWNS, "image"):
                out.append(self._image(ch))
            elif _is(ch, TEXTNS, "note") or _is(ch, TEXTNS, "bookmark") or _is(ch, TEXTNS, "bookmark-start"):
                continue
            else:
                out.append(self.inline(ch))
        return "".join(out)

    def _styled(self, span) -> str:
        inner = self.inline(span)
        bold, italic, underline = self.styles.get(_attr(span, TEXTNS, "style-name"), (False, False, False))
        if bold:
            inner = f"<b>{inner}</b>"
        if italic:
            inner = f"<i>{inner}</i>"
        if underline:
            inner = f"<u>{inner}</u>"
        return inner

    def _image(self, node) -> str:
        image = node if _is(node, DRAWNS, "image") else next(
            (c for c in node.childNodes if _is(c, DRAWNS, "image")), None
        )
        if image is None or len(self.images) >= MAX_IMAGES:
            return ""
        href = _attr(image, XLINKNS, "href")
        entry = self.doc.Pictures.get(href) if href else None
        if not entry:
            return ""
        data = entry[1] if isinstance(entry, tuple) else entry
        if not isinstance(data, (bytes, bytearray)) or len(data) > MAX_IMAGE_BYTES:
            return ""
        name = f"odfimg://{len(self.images)}"
        self.images[name] = bytes(data)
        return f'<img src="{name}" style="max-width:100%">'

    # -- blocks ------------------------------------------------------------

    def blocks_html(self, parent) -> str:
        out = []
        for ch in parent.childNodes:
            if self.blocks >= MAX_BLOCKS:
                out.append("<p style='color:gray;font-style:italic'>[...]</p>")
                break
            piece = self._block(ch)
            if piece:
                out.append(piece)
        return "".join(out)

    def _block(self, node) -> str:
        if _is(node, TEXTNS, "h"):
            self.blocks += 1
            level = min(max(int(_attr(node, TEXTNS, "outline-level") or 1), 1), 6)
            return f"<h{level}>{self.inline(node)}</h{level}>"
        if _is(node, TEXTNS, "p"):
            self.blocks += 1
            inner = self.inline(node)
            return f"<p style='margin:3px 0'>{inner}</p>" if inner.strip() else "<br>"
        if _is(node, TEXTNS, "list"):
            return self._list(node)
        if _is(node, TABLENS, "table"):
            return self._table(node)
        if _is(node, TEXTNS, "section") or _is(node, TEXTNS, "list-item") or _is(node, TEXTNS, "list-header"):
            return self.blocks_html(node)
        return ""

    def _list(self, node) -> str:
        items = []
        for item in node.childNodes:
            if _is(item, TEXTNS, "list-item") or _is(item, TEXTNS, "list-header"):
                items.append(f"<li>{self.blocks_html(item)}</li>")
        return f"<ul>{''.join(items)}</ul>" if items else ""

    def _table(self, table) -> str:
        self.blocks += 1
        rows_html = []

        def collect(parent):
            for ch in parent.childNodes:
                if _is(ch, TABLENS, "table-row"):
                    cells = []
                    for cell in ch.childNodes:
                        if _is(cell, TABLENS, "table-cell"):
                            span = int(_attr(cell, TABLENS, "number-columns-spanned") or 1)
                            rspan = int(_attr(cell, TABLENS, "number-rows-spanned") or 1)
                            attrs = f" colspan={span}" if span > 1 else ""
                            attrs += f" rowspan={rspan}" if rspan > 1 else ""
                            cells.append(f"<td{attrs}>{self.blocks_html(cell)}</td>")
                    rows_html.append(f"<tr>{''.join(cells)}</tr>")
                elif _is(ch, TABLENS, "table-header-rows") or _is(ch, TABLENS, "table-row-group"):
                    collect(ch)

        collect(table)
        if not rows_html:
            return ""
        style = "border-collapse:collapse"
        return f"<table border='1' cellspacing='0' cellpadding='4' style='{style}'>{''.join(rows_html)}</table><br>"


def odt_to_html(path: str) -> OdtPreview:
    _check_size(path)
    doc = load(path)
    renderer = _OdtRenderer(doc)
    html = renderer.blocks_html(doc.text)
    return OdtPreview(html=html, images=renderer.images)


# ---------------------------------------------------------------------------
# ODS
# ---------------------------------------------------------------------------


def _cell_text(cell) -> str:
    """Value as the spreadsheet displays it (formatting is stored in the text:p)."""
    paragraphs = [teletype.extractText(p) for p in cell.childNodes if _is(p, TEXTNS, "p")]
    shown = "\n".join(p for p in paragraphs if p)
    if shown:
        return shown
    for name in ("value", "date-value", "time-value", "boolean-value", "string-value"):
        raw = _attr(cell, OFFICENS, name)
        if raw is not None:
            return str(raw)
    return ""


def _sheet_rows(table) -> list[list[str]]:
    rows: list[list[str]] = []

    def collect(parent):
        for ch in parent.childNodes:
            if len(rows) >= MAX_ROWS:
                return
            if _is(ch, TABLENS, "table-row"):
                row: list[str] = []
                for cell in ch.childNodes:
                    if _is(cell, TABLENS, "table-cell") or _is(cell, TABLENS, "covered-table-cell"):
                        repeat = int(_attr(cell, TABLENS, "number-columns-repeated") or 1)
                        text = _cell_text(cell)
                        row.extend([text] * min(repeat, MAX_COLS - len(row)))
                    if len(row) >= MAX_COLS:
                        break
                repeat_rows = int(_attr(ch, TABLENS, "number-rows-repeated") or 1)
                for _ in range(min(repeat_rows, MAX_ROWS - len(rows))):
                    rows.append(list(row))
            elif _is(ch, TABLENS, "table-header-rows") or _is(ch, TABLENS, "table-row-group"):
                collect(ch)

    collect(table)
    while rows and not any(rows[-1]):
        rows.pop()
    width = 0
    for r in rows:
        while r and not r[-1]:
            r.pop()
        width = max(width, len(r))
    return [r + [""] * (width - len(r)) for r in rows]


def ods_sheets(path: str) -> list[tuple[str, list[list[str]]]]:
    _check_size(path)
    doc = load(path)
    sheets = []
    for table in doc.spreadsheet.childNodes:
        if not _is(table, TABLENS, "table"):
            continue
        rows = _sheet_rows(table)
        if rows:
            sheets.append((_attr(table, TABLENS, "name") or str(len(sheets) + 1), rows))
        if len(sheets) >= MAX_SHEETS:
            break
    return sheets


# ---------------------------------------------------------------------------
# ODP
# ---------------------------------------------------------------------------


def _paragraph_texts(node) -> list[str]:
    """Text of every paragraph/heading under ``node``, in document order."""
    found: list[str] = []
    for ch in node.childNodes:
        if _is(ch, TEXTNS, "p") or _is(ch, TEXTNS, "h"):
            line = teletype.extractText(ch).strip()
            if line:
                found.append(line)
        elif getattr(ch, "childNodes", None):
            found.extend(_paragraph_texts(ch))
    return found


def odp_slides(path: str) -> list[list[str]]:
    _check_size(path)
    doc = load(path)
    slides = []
    for page in doc.presentation.childNodes:
        if _is(page, DRAWNS, "page"):
            slides.append(_paragraph_texts(page))
            if len(slides) >= MAX_SLIDES:
                break
    return slides
