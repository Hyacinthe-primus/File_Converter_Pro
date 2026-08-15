"""Native RTF parsing and full-fidelity RTF -> PDF rendering."""

from __future__ import annotations

import io
import re

from converter.helpers import _safe_html


class RtfNativeConverters:
    """Native RTF -> PDF conversions (no Office or pandoc needed)."""

    @staticmethod
    def _rtf_read_raw(src: str) -> str:
        """Read RTF bytes and decode robustly (utf-8 → cp1252 → latin-1)."""
        with open(src, "rb") as fh:
            raw_bytes = fh.read()
        for enc in ("utf-8", "cp1252", "latin-1"):
            try:
                return raw_bytes.decode(enc)
            except Exception:
                pass
        return raw_bytes.decode("utf-8", errors="replace")

    @staticmethod
    def _rtf_extract_images(raw: str) -> list:
        """
        Extract embedded PNG/JPEG images from \\pict blocks (hex-encoded).
        Returns list of (image_bytes, 'png'|'jpg').
        WMF/EMF bitmaps are skipped (not portably renderable).
        """
        images = []
        for m in re.finditer(r"\{\\pict((?:[^{}]|\{[^{}]*\})*)\}", raw, re.S):
            block = m.group(1)
            if re.search(r"\\pngblip\b", block):
                fmt = "png"
            elif re.search(r"\\jpegblip\b", block):
                fmt = "jpg"
            else:
                continue
            hex_data = re.sub(r"\\[a-zA-Z]+[-0-9]*\s?", "", block)
            hex_data = re.sub(r"[^0-9a-fA-F]", "", hex_data)
            if len(hex_data) < 8:
                continue
            try:
                images.append((bytes.fromhex(hex_data), fmt))
            except Exception:
                pass
        return images

    @staticmethod
    def _rtf_spans_to_paragraphs(spans: list) -> list:
        """
        Assemble spans into a document structure:
          { 'type': 'para',      'para': { runs, text_content } }
          { 'type': 'table_row', 'cells': [ [para, ...], ... ] }

        Adjacent runs with identical formatting are merged.
        """
        items = []
        cur_runs = []
        cur_cell_paras = []
        cur_row_cells = []

        def _flush(is_cell=False):
            merged = []
            for run in cur_runs:
                if (
                    merged
                    and merged[-1]["bold"] == run["bold"]
                    and merged[-1]["italic"] == run["italic"]
                    and merged[-1]["underline"] == run["underline"]
                    and merged[-1]["fontsize"] == run["fontsize"]
                    and merged[-1]["color"] == run["color"]
                ):
                    merged[-1]["text"] += run["text"]
                else:
                    merged.append(dict(run))
            cur_runs.clear()
            return {
                "runs": merged,
                "text_content": "".join(r["text"] for r in merged).strip(),
                "is_table_cell": is_cell,
            }

        for sp in spans:
            if sp["cell_end"]:
                cur_cell_paras.append(_flush(is_cell=True))
                cur_row_cells.append(list(cur_cell_paras))
                cur_cell_paras.clear()
                continue
            if sp["row_end"]:
                leftover = _flush(is_cell=True)
                if leftover["text_content"] or leftover["runs"]:
                    cur_cell_paras.append(leftover)
                    cur_row_cells.append(list(cur_cell_paras))
                    cur_cell_paras.clear()
                items.append({"type": "table_row", "cells": list(cur_row_cells)})
                cur_row_cells.clear()
                continue
            if sp["par"]:
                para = _flush()
                if sp["in_table"]:
                    cur_cell_paras.append(para)
                else:
                    items.append({"type": "para", "para": para})
                continue
            if sp["text"]:
                cur_runs.append({k: sp[k] for k in ("text", "bold", "italic", "underline", "fontsize", "color")})

        if cur_runs:
            items.append({"type": "para", "para": _flush()})
        return items

    def _rtf_to_pdf_native(self, src, dst):
        """
        Full-fidelity native RTF → PDF (no Office, no pandoc needed).
        Preserves bold · italic · underline · font sizes · RGB colors ·
        tables · embedded PNG/JPEG images.
        """
        from reportlab.lib import colors as rl_colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Image as RLImage
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        raw = self._rtf_read_raw(src)
        color_table = self._rtf_parse_colortbl(raw)
        img_data = self._rtf_extract_images(raw)
        tokens = self._rtf_tokenize(raw)
        spans = self._rtf_parse_spans(tokens, color_table)
        paras = self._rtf_spans_to_paragraphs(spans)

        sty = getSampleStyleSheet()
        base = ParagraphStyle(
            "RTFBase", parent=sty["Normal"], fontSize=11, leading=15, spaceAfter=3, fontName="Helvetica"
        )
        td_s = ParagraphStyle("RTFTd", parent=sty["Normal"], fontSize=9, leading=12, fontName="Helvetica")

        def _runs_to_xml(runs, base_fs=11):
            parts = []
            for r in runs:
                txt = _safe_html(r["text"])
                if not txt:
                    continue
                fs = max(6, r["fontsize"] // 2)
                o, c = [], []
                if r["bold"]:
                    o.append("<b>")
                    c.insert(0, "</b>")
                if r["italic"]:
                    o.append("<i>")
                    c.insert(0, "</i>")
                if r["underline"]:
                    o.append("<u>")
                    c.insert(0, "</u>")
                if r["color"]:
                    rv, gv, bv = r["color"]
                    o.append(f'<font color="#{rv:02x}{gv:02x}{bv:02x}">')
                    c.insert(0, "</font>")
                if fs != base_fs:
                    o.append(f'<font size="{fs}">')
                    c.insert(0, "</font>")
                parts.append("".join(o) + txt + "".join(c))
            return "".join(parts)

        story = []

        def _build_rl_table(rows_data):
            """Convert list of table_row items into a single ReportLab Table."""
            max_cols = max(len(r["cells"]) for r in rows_data)
            tbl_rows = []
            for row_item in rows_data:
                tbl_row = []
                for ci in range(max_cols):
                    cell_paras = row_item["cells"][ci] if ci < len(row_item["cells"]) else []
                    cell_content = []
                    for cp in cell_paras:
                        x = _runs_to_xml(cp["runs"], base_fs=9)
                        if x.strip():
                            cell_content.append(Paragraph(x, td_s))
                    tbl_row.append(cell_content or [Paragraph("", td_s)])
                tbl_rows.append(tbl_row)
            tbl = Table(tbl_rows, hAlign="LEFT", colWidths=[None] * max_cols)
            tbl.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.4, rl_colors.HexColor("#bbbbbb")),
                        ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor("#f5f5f5")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )
            return tbl

        idx = 0
        while idx < len(paras):
            item = paras[idx]

            if item["type"] == "table_row":
                rows_data = []
                while idx < len(paras) and paras[idx]["type"] == "table_row":
                    rows_data.append(paras[idx])
                    idx += 1
                story.append(_build_rl_table(rows_data))
                continue

            para = item["para"]
            xml = _runs_to_xml(para["runs"])
            idx += 1
            if not xml.strip():
                story.append(Spacer(1, 4))
                continue
            plain = para["text_content"]
            if (
                plain.isupper()
                and 0 < len(plain) < 80
                and all(r["bold"] or r["fontsize"] >= 28 for r in para["runs"] if r["text"].strip())
            ):
                hs = ParagraphStyle(
                    "RTFHead",
                    parent=base,
                    fontSize=13,
                    leading=17,
                    spaceBefore=6,
                    spaceAfter=4,
                    fontName="Helvetica-Bold",
                )
                story.append(Paragraph(xml, hs))
            else:
                sizes = [r["fontsize"] for r in para["runs"] if r["text"].strip()]
                dom = max(6, (max(sizes) // 2)) if sizes else 11
                ps = ParagraphStyle("RTFPar", parent=base, fontSize=dom, leading=max(dom + 3, 13))
                story.append(Paragraph(xml, ps))

        for img_bytes, fmt in img_data:
            try:
                from PIL import Image as PILImg

                buf = io.BytesIO(img_bytes)
                pil = PILImg.open(buf)
                w, h = pil.size
                max_w = 120 * mm
                scale = min(1.0, max_w / max(w, 1))
                buf.seek(0)
                story.append(Spacer(1, 6))
                story.append(RLImage(buf, width=w * scale, height=h * scale))
                story.append(Spacer(1, 6))
            except Exception:
                pass

        if not story:
            story.append(Paragraph("(empty document)", base))

        SimpleDocTemplate(
            dst,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        ).build(story)
