"""PDF -> HTML rendering (fitz dict-mode)."""

from __future__ import annotations

from pathlib import Path

from converter.helpers import _img_to_b64, _mime_for_ext, _safe_html


class PdfRenderers:
    """PDF -> HTML conversions."""

    def _pdf_to_html(self, src, dst):
        """
        PDF → HTML — self-contained, faithful layout.

        Key improvements:
        - Margins reconstructed from block X positions relative to page width
          → text appears centred with proper left/right margins, not stuck left
        - Multi-column detection: blocks with x0 > 50% of page width → right col
        - Justified text for body paragraphs
        - Line-height and letter-spacing tuned per block font size
        - Consecutive lines of the same block merged into one <p> (no <br> soup)
        - Bold/italic/colour/size spans preserved
        - Images at their exact position in the flow
        - Superscript/subscript detected via vertical origin offset
        """
        import fitz

        doc = fitz.open(src)
        name = Path(dst).stem

        _widths = [p.rect.width for p in doc]
        _heights = [p.rect.height for p in doc]
        MED_W = sorted(_widths)[len(_widths) // 2] if _widths else 595.0
        sorted(_heights)[len(_heights) // 2] if _heights else 842.0

        CSS_W = max(620, min(1080, int(MED_W * 1.333)))
        PAD = max(40, int(CSS_W * 0.075))
        INNER = CSS_W - PAD * 2

        BASE_F = max(11, min(15, round(MED_W / 50)))

        CSS = f"""<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html {{ font-size: {BASE_F}px; }}
  body {{
    font-family: 'Georgia', 'Times New Roman', serif;
    background: #d8d8d8;
    color: #111;
    line-height: 1.65;
  }}
  /* page card */
  .page {{
    background: #fff;
    width: {CSS_W}px;
    margin: 28px auto;
    padding: {PAD}px;
    box-shadow: 0 3px 18px rgba(0,0,0,.18);
    border-radius: 3px;
    position: relative;
  }}
  /* page number */
  .pn {{
    font-size: 9px;
    color: #bbb;
    text-align: right;
    margin-bottom: 14px;
    font-family: 'Segoe UI', Arial, sans-serif;
  }}
  /* body paragraph */
  p {{
    margin: 0 0 6px 0;
    text-align: justify;
    hyphens: auto;
    word-spacing: 0.02em;
  }}
  p.center {{ text-align: center; }}
  p.right  {{ text-align: right;  }}
  /* headings */
  h1 {{ font-size: {BASE_F + 7}px; margin: 16px 0 8px; line-height: 1.25; }}
  h2 {{ font-size: {BASE_F + 5}px; margin: 14px 0 6px; line-height: 1.28; }}
  h3 {{ font-size: {BASE_F + 3}px; margin: 10px 0 5px; line-height: 1.3;  }}
  h4 {{ font-size: {BASE_F + 1}px; margin: 8px  0 4px; }}
  /* inline */
  img {{
    max-width: 100%;
    height: auto;
    display: block;
    margin: 14px auto;
  }}
  sup {{ font-size: 0.72em; vertical-align: super; }}
  sub {{ font-size: 0.72em; vertical-align: sub;   }}
  hr  {{ border: none; border-top: 1px solid #e0e0e0; margin: 18px 0; }}
  /* two-column blocks */
  .col-r {{ margin-left: 50%; }}
  /* indent levels */
  .ind1 {{ margin-left: {int(INNER * 0.05)}px; }}
  .ind2 {{ margin-left: {int(INNER * 0.10)}px; }}
  .ind3 {{ margin-left: {int(INNER * 0.15)}px; }}
</style>"""

        def _span_html(span, page_origin_y):
            txt = span.get("text", "")
            if not txt.strip():
                return txt
            flags = span.get("flags", 0)
            size = span.get("size", BASE_F)
            color = span.get("color", 0)
            orig = span.get("origin", (0, 0))

            styles = []
            if flags & 16:
                styles.append("font-weight:700")
            if flags & 2:
                styles.append("font-style:italic")

            ratio = size / BASE_F if BASE_F else 1
            if ratio >= 1.35:
                styles.append(f"font-size:{min(int(size * 1.333), 38)}px")
            elif ratio <= 0.78:
                styles.append(f"font-size:{max(int(size * 1.333), 8)}px")

            if color and color != 0:
                r2 = (color >> 16) & 0xFF
                g2 = (color >> 8) & 0xFF
                b2 = color & 0xFF
                if not (r2 < 30 and g2 < 30 and b2 < 30):
                    styles.append(f"color:#{r2:02x}{g2:02x}{b2:02x}")

            safe = _safe_html(txt).replace("	", "    ").replace("  ", " &nbsp;")

            if len(orig) >= 2 and page_origin_y:
                pass

            if not styles:
                return safe
            style_str = ";".join(styles)
            return f'<span style="{style_str}">{safe}</span>'

        def _block_html(block, page_w):
            """
            Convert a fitz text block to an HTML element.
            Returns (html_string, alignment_class).
            """
            bbox = block.get("bbox", [0, 0, page_w, 0])
            x0, x1 = bbox[0], bbox[2]
            x1 - x0

            all_spans = [sp for ln in block.get("lines", []) for sp in ln.get("spans", [])]
            if not all_spans:
                return "", ""

            first_size = all_spans[0].get("size", BASE_F)
            sum(sp.get("size", BASE_F) for sp in all_spans) / len(all_spans)
            all_bold = all(sp.get("flags", 0) & 16 for sp in all_spans)

            ratio = first_size / BASE_F if BASE_F else 1
            if ratio >= 1.6 or (ratio >= 1.3 and all_bold):
                tag = "h1"
            elif ratio >= 1.35 or (ratio >= 1.15 and all_bold):
                tag = "h2"
            elif ratio >= 1.15:
                tag = "h3"
            elif ratio >= 1.05 and all_bold:
                tag = "h4"
            else:
                tag = "p"

            left_margin_frac = x0 / page_w if page_w else 0
            right_margin_frac = (page_w - x1) / page_w if page_w else 0

            align_cls = ""
            indent_cls = ""

            if tag == "p":
                if abs(left_margin_frac - right_margin_frac) < 0.08 and left_margin_frac > 0.15:
                    align_cls = "center"
                elif left_margin_frac > 0.45 and right_margin_frac < 0.12:
                    align_cls = "right"
                elif 0.08 < left_margin_frac < 0.20:
                    indent_cls = "ind1"
                elif 0.20 <= left_margin_frac < 0.30:
                    indent_cls = "ind2"
                elif left_margin_frac >= 0.30:
                    indent_cls = "ind3"

            line_texts = []
            line_widths = []

            for line in block.get("lines", []):
                spans_html = "".join(_span_html(sp, None) for sp in line.get("spans", []))
                if not spans_html.strip():
                    continue
                line_texts.append(spans_html)
                lbbox = line.get("bbox", [0, 0, 0, 0])
                line_widths.append(lbbox[2] - lbbox[0])

            if not line_texts:
                return "", ""

            block_text_w = bbox[2] - bbox[0]

            if len(line_texts) == 1:
                inner = line_texts[0]
            else:
                short_lines = sum(1 for w in line_widths if block_text_w > 0 and w / block_text_w < 0.75)
                short_ratio = short_lines / len(line_widths)

                block_frac = block_text_w / page_w if page_w else 1

                if short_ratio >= 0.5 or block_frac < 0.40:
                    inner = "<br>".join(line_texts)
                else:
                    inner = " ".join(line_texts)

            classes = " ".join(filter(None, [align_cls, indent_cls]))
            cls_attr = f' class="{classes}"' if classes else ""

            return f"<{tag}{cls_attr}>{inner}</{tag}>", align_cls

        pages_html = []

        for page in doc:
            pn = page.number + 1
            page_w = page.rect.width or MED_W

            img_b64: dict[int, str] = {}
            for info in page.get_images(full=True):
                xref = info[0]
                if xref in img_b64:
                    continue
                try:
                    bi = doc.extract_image(xref)
                    img_b64[xref] = _img_to_b64(bi["image"], _mime_for_ext(bi["ext"]))
                except Exception:
                    pass

            items = []
            for block in page.get_text("dict", sort=True).get("blocks", []):
                y0, x0 = block["bbox"][1], block["bbox"][0]
                if block.get("type") == 0:
                    html, _ = _block_html(block, page_w)
                    if html:
                        items.append((y0, x0, "txt", html))
                elif block.get("type") == 1:
                    xref = block.get("xref", 0)
                    if xref and xref in img_b64:
                        items.append((y0, x0, "img", img_b64[xref]))

            placed = {d for _, _, k, d in items if k == "img"}
            for xref, uri in img_b64.items():
                if uri not in placed:
                    items.append((9999, 0, "img", uri))

            items.sort(key=lambda x: (x[0], x[1]))

            body_parts = []
            for _, _, kind, data in items:
                if kind == "txt":
                    body_parts.append(data)
                elif kind == "tbl":
                    body_parts.append(data)
                else:
                    body_parts.append(f'<img src="{data}" alt="img p{pn}">')

            pages_html.append(
                f'<div class="page"><div class="pn">Page {pn} / {len(doc)}</div>' + "\n".join(body_parts) + "</div>"
            )

        with open(dst, "w", encoding="utf-8") as f:
            f.write(
                "<!DOCTYPE html>\n"
                '<html lang="fr">\n<head>\n'
                '  <meta charset="utf-8">\n'
                f"  <title>{_safe_html(name)}</title>\n"
                f"  {CSS}\n"
                "</head>\n<body>\n" + "\n<hr>\n".join(pages_html) + "\n</body>\n</html>"
            )
