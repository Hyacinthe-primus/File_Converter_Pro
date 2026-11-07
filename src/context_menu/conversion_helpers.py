"""Non-UI conversion helpers shared by Quick Convert and automation."""

from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
from pathlib import Path

from utils.conversion_pipeline import ConversionCancelled, run_conversion_pipeline
from utils.pdf_artifacts import validate_docx_artifact, validate_docx_input, validate_pdf_artifact
from utils.pdf_text import build_text_only_engines, convert_pdf_text_to_docx

_PDF_TO_WORD_MODE_DEFAULT = "with_images"
_PDF_TO_WORD_MODES = frozenset({"with_images", "text_only"})

_ConversionCancelled = ConversionCancelled


def _raise_if_cancelled(cancel_event: threading.Event | None) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise _ConversionCancelled()


def _normalise_pdf_to_word_mode(mode: object) -> str:
    if isinstance(mode, str) and mode in _PDF_TO_WORD_MODES:
        return mode
    return _PDF_TO_WORD_MODE_DEFAULT


def _temporary_docx_path(dst_path: str) -> str:
    fd, temp_path = tempfile.mkstemp(
        prefix="~fcp_pdf_word_",
        suffix=".docx",
        dir=os.path.dirname(dst_path),
    )
    os.close(fd)
    return temp_path


def _sort_files(files: list, order: str) -> list:
    """Return merge inputs in the requested order.

    ``none``, ``current``, and ``manual`` preserve the caller-provided order;
    Main uses these for its user-maintained list and manual dialog ordering.
    Quick Convert and automation have no such user sequence, so they normalize
    their ``none`` order to ``alphabetical_asc`` before calling merge helpers.
    Alphabetical orders compare case-insensitive filenames, numeric orders use
    digit-aware natural name tokens, and date orders use modification time.
    All non-preserving orders use the full path string as a deterministic
    tie-breaker.
    """
    aliases = {
        "alpha_az": "alphabetical_asc",
        "alpha_za": "alphabetical_desc",
        "num_asc": "numerical_asc",
        "num_desc": "numerical_desc",
        "manual": "none",
        "current": "none",
    }
    canonical = aliases.get(order, order)
    if canonical == "none" or not canonical:
        return files

    def name_key(path):
        return (Path(path).name.lower(), str(path).lower())

    def number_key(path):
        import re

        parts = re.split(r"(\d+)", Path(path).name)
        return (
            tuple((0, int(part)) if part.isdigit() else (1, part.lower()) for part in parts),
            str(path).lower(),
        )

    def date_key(path):
        return (Path(path).stat().st_mtime, str(path).lower())

    if canonical == "alphabetical_asc":
        return sorted(files, key=name_key)
    if canonical == "alphabetical_desc":
        return sorted(files, key=name_key, reverse=True)
    if canonical == "numerical_asc":
        return sorted(files, key=number_key)
    if canonical == "numerical_desc":
        return sorted(files, key=number_key, reverse=True)
    if canonical == "date_asc":
        return sorted(files, key=date_key)
    if canonical == "date_desc":
        return sorted(files, key=date_key, reverse=True)
    return files


def _embed_images_in_pdf(
    files: list,
    target: str,
    cancel_event: threading.Event | None = None,
) -> None:
    import fitz

    from utils.image_formats import decodable_image_path

    pdf = fitz.open()
    try:
        for src in files:
            _raise_if_cancelled(cancel_event)
            with decodable_image_path(src) as readable:
                img = fitz.open(readable)
                rect = img[0].rect
                page = pdf.new_page(width=rect.width, height=rect.height)
                page.insert_image(rect, filename=readable)
                img.close()
        pdf.save(target)
    finally:
        pdf.close()


def _convert_image_to_pdf(src: str, dst_dir: str) -> None:
    out = os.path.join(dst_dir, f"{Path(src).stem}.pdf")

    def _engine(target):
        _embed_images_in_pdf([src], target)
        return True

    result = run_conversion_pipeline(
        out,
        [("image", _engine)],
        validate_pdf_artifact,
        stage_mode="file",
        staged_prefix="~fcp_image_",
        staged_suffix=".pdf",
        include_engine_labels=False,
    )
    if not result.success:
        raise RuntimeError(f"Image to PDF conversion failed: {result.error}")


def _merge_images_to_pdf(
    files: list, dst_dir: str, cancel_event: threading.Event | None = None
) -> str:
    out = _merge_output_path(dst_dir, None, "merged_images_", "pdf")

    def _engine(target):
        _embed_images_in_pdf(files, target, cancel_event)
        return True

    _commit_merge(
        out,
        _engine,
        validate_pdf_artifact,
        cancel_event,
        "Image",
        reserved=True,
    )
    return out


def _reserve_unique_output_path(dst_dir: str, base_stem: str, suffix: str) -> str:
    """Atomically claim a unique output path, preserving existing files."""
    suffix = suffix.lstrip(".")
    candidate = os.path.join(dst_dir, f"{base_stem}.{suffix}")
    counter = 1
    while True:
        try:
            fd = os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            candidate = os.path.join(dst_dir, f"{base_stem}_{counter}.{suffix}")
            counter += 1
            continue
        os.close(fd)
        return candidate


def _release_reserved_path(path: str) -> None:
    """Remove a reserved destination that was not successfully published."""
    try:
        os.remove(path)
    except OSError:
        pass


def _merge_output_path(
    dst_dir: str,
    dst_path: str | None,
    prefix: str,
    suffix: str,
) -> str:
    if dst_path:
        return os.path.abspath(dst_path)

    stem = f"{prefix}{time.strftime('%Y%m%d_%H%M%S')}"
    return _reserve_unique_output_path(dst_dir, stem, suffix)


def _commit_merge(
    final_path: str,
    engine,
    validator,
    cancel_event: threading.Event | None,
    label: str,
    *,
    reserved: bool = False,
) -> None:
    try:
        result = run_conversion_pipeline(
            final_path,
            [("merge", engine)],
            validator,
            cancel_event=cancel_event,
            stage_mode="file",
            staged_prefix="~fcp_merge_",
            staged_suffix=Path(final_path).suffix or ".tmp",
            include_engine_labels=False,
        )
    except Exception:
        if reserved:
            _release_reserved_path(final_path)
        raise
    if not result.success:
        if reserved:
            _release_reserved_path(final_path)
        if result.cancelled:
            raise _ConversionCancelled()
        raise RuntimeError(f"{label} merge failed: {result.error}")


def _merge_pdfs(
    files: list,
    dst_dir: str,
    order: str,
    cancel_event: threading.Event | None = None,
    *,
    dst_path: str | None = None,
) -> str:
    _raise_if_cancelled(cancel_event)
    ordered_files = _sort_files(files, order)
    if not ordered_files:
        raise RuntimeError("PDF merge requires at least one input file")

    out = _merge_output_path(dst_dir, dst_path, "merged_", "pdf")

    def _engine(target):
        from pypdf import PdfWriter

        writer = PdfWriter()
        try:
            for f in ordered_files:
                _raise_if_cancelled(cancel_event)
                writer.append(f)
            _raise_if_cancelled(cancel_event)
            with open(target, "wb") as handle:
                writer.write(handle)
        finally:
            writer.close()
        return True

    _commit_merge(
        out,
        _engine,
        validate_pdf_artifact,
        cancel_event,
        "PDF",
        reserved=dst_path is None,
    )
    return out


LEGACY_DOC_MERGE_ERROR = (
    "Legacy .doc files are not supported for merging. "
    "Please save them as .docx and try again."
)


def _merge_docx(
    files: list,
    dst_dir: str,
    order: str,
    cancel_event: threading.Event | None = None,
    *,
    dst_path: str | None = None,
) -> str:
    _raise_if_cancelled(cancel_event)
    if any(Path(f).suffix.lower() == ".doc" for f in files):
        raise RuntimeError(LEGACY_DOC_MERGE_ERROR)
    ordered_files = _sort_files(files, order)
    if not ordered_files:
        raise RuntimeError("Word merge requires at least one input file")

    out = _merge_output_path(dst_dir, dst_path, "merged_", "docx")

    def _engine(target):
        from docx import Document
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        from docxcompose.composer import Composer

        merged = Document(ordered_files[0])
        composer = Composer(merged)

        for f in ordered_files[1:]:
            _raise_if_cancelled(cancel_event)
            doc = Document(f)
            p = OxmlElement("w:p")
            r = OxmlElement("w:r")
            br = OxmlElement("w:br")
            br.set(qn("w:type"), "page")
            r.append(br)
            p.append(r)
            doc.element.body.insert(0, p)
            composer.append(doc)

        _raise_if_cancelled(cancel_event)
        composer.save(target)
        return True

    _commit_merge(
        out,
        _engine,
        validate_docx_artifact,
        cancel_event,
        "Word",
        reserved=dst_path is None,
    )
    return out


def _convert_docx_to_pdf(src: str, dst_dir: str, cancel_event: threading.Event | None = None) -> None:
    out = os.path.join(dst_dir, f"{Path(src).stem}.pdf")
    src_abs = os.path.abspath(src)
    out_abs = os.path.abspath(out)

    valid, reason = validate_docx_input(src_abs)
    if not valid:
        raise RuntimeError(f"Invalid Word input: {reason}")

    def _run_docx2pdf(target):
        from docx2pdf import convert

        _raise_if_cancelled(cancel_event)
        try:
            convert(src_abs, target)
        except SystemExit as exc:
            raise RuntimeError(f"docx2pdf exited with status {exc.code}") from exc
        _raise_if_cancelled(cancel_event)

    def _run_com(target):
        import comtypes.client

        _raise_if_cancelled(cancel_event)
        word = None
        document = None
        try:
            word = comtypes.client.CreateObject("Word.Application")
            word.Visible = False
            word.DisplayAlerts = 0
            document = word.Documents.Open(src_abs)
            document.SaveAs(target, FileFormat=17)
            _raise_if_cancelled(cancel_event)
            document.Close(False)
            document = None
        finally:
            if document is not None:
                try:
                    document.Close(False)
                except Exception:
                    pass
            if word is not None:
                try:
                    word.Quit()
                except Exception:
                    pass

    def _run_libreoffice(target):
        import subprocess

        from external_binaries import resolve_binary

        _raise_if_cancelled(cancel_event)
        exe = resolve_binary("libreoffice")
        if not exe:
            raise RuntimeError("LibreOffice not found")
        output_dir = os.path.dirname(target)
        completed = subprocess.run(
            [exe, "--headless", "--convert-to", "pdf", "--outdir", output_dir, src_abs],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        expected = os.path.join(output_dir, f"{Path(src_abs).stem}.pdf")
        if os.path.exists(expected):
            _raise_if_cancelled(cancel_event)
            if os.path.abspath(expected) != os.path.abspath(target):
                os.replace(expected, target)
            return

        detail = (completed.stderr or "").strip()
        if detail:
            raise RuntimeError(f"LibreOffice failed: {detail}")
        raise RuntimeError(f"LibreOffice produced no output (exit code {completed.returncode})")

    def _run_reportlab(target):
        from docx import Document as DocxDoc
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

        _raise_if_cancelled(cancel_event)
        doc = DocxDoc(src_abs)
        styles = getSampleStyleSheet()
        story = []
        for para in doc.paragraphs:
            if para.text.strip():
                story.append(Paragraph(para.text, styles["Normal"]))
                story.append(Spacer(1, 6))
        if not story:
            story.append(Spacer(1, 1))
        SimpleDocTemplate(target, pagesize=A4).build(story)
        _raise_if_cancelled(cancel_event)

    def _run_word(target):
        try:
            _run_com(target)
            return
        except _ConversionCancelled:
            raise
        except Exception as com_exc:
            com_error = com_exc

        try:
            _run_docx2pdf(target)
        except _ConversionCancelled:
            raise
        except Exception as docx_exc:
            raise RuntimeError(f"COM failed: {com_error}; docx2pdf failed: {docx_exc}") from docx_exc

    engines = []
    docx2pdf_supported = src_abs.endswith(".docx")
    if sys.platform == "win32":
        if docx2pdf_supported:
            engines.append(("Word", _run_word))
        else:
            engines.append(("COM", _run_com))
    elif sys.platform == "darwin" and docx2pdf_supported:
        engines.append(("docx2pdf", _run_docx2pdf))
    engines.extend([
        ("LibreOffice", _run_libreoffice),
        ("ReportLab", _run_reportlab),
    ])

    result = run_conversion_pipeline(
        out_abs,
        engines,
        validate_pdf_artifact,
        cancel_event=cancel_event,
        stage_mode="directory",
        stage_dir_prefix="~fcp_pdf_stage_",
        staged_prefix="~fcp_pdf_",
        staged_suffix=".pdf",
    )
    if result.cancelled:
        raise _ConversionCancelled()
    if not result.success:
        detail = result.error
        if detail:
            raise RuntimeError(f"All DOCX→PDF methods failed: {detail}")
        raise RuntimeError("All DOCX→PDF methods failed.")


def _convert_pdf_to_docx(
    src: str,
    dst_dir: str,
    cancel_event: threading.Event | None = None,
    mode: str = _PDF_TO_WORD_MODE_DEFAULT,
) -> None:
    _convert_pdf_to_docx_impl(
        src,
        dst_dir,
        cancel_event,
        mode,
        text_converter=convert_pdf_text_to_docx,
        fallback=_solid_fitz_fallback,
    )


def _pdf_to_docx_word_com(src_abs: str, out_abs: str) -> bool:
    if sys.platform != "win32":
        return False

    try:
        import winreg

        winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "Word.Application")
        word_available = True
    except (OSError, ImportError):
        word_available = False
        print("[pdf→docx] Word not found in registry - skipping COM tier")

    if not word_available:
        return False

    result = {"ok": False}
    stop_event = threading.Event()

    def _dialog_dismisser():
        import ctypes
        import ctypes.wintypes

        user32 = ctypes.windll.user32
        BM_CLICK = 0x00F5

        DialogProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.wintypes.HWND,
            ctypes.wintypes.LPARAM,
        )

        def _find_ok_button(hwnd_dialog):
            found = ctypes.wintypes.HWND(0)

            @DialogProc
            def _enum(hwnd_child, _lp):
                buf = ctypes.create_unicode_buffer(64)
                user32.GetWindowTextW(hwnd_child, buf, 64)
                if buf.value.strip().upper() in ("OK", "O&K"):
                    found.value = hwnd_child
                    return False
                if user32.GetDlgCtrlID(hwnd_child) == 1:
                    found.value = hwnd_child
                    return False
                return True

            user32.EnumChildWindows(hwnd_dialog, _enum, 0)
            return found.value or None

        dialog_classes = ["#32770", "bosa_sdm_msword"]
        target_title = "Microsoft Word"

        while not stop_event.is_set():
            for cls in dialog_classes:
                hwnd = user32.FindWindowW(cls, None)
                if hwnd:
                    ok_btn = _find_ok_button(hwnd)
                    if ok_btn:
                        user32.SendMessageW(ok_btn, BM_CLICK, 0, 0)
                    else:
                        user32.SendMessageW(hwnd, 0x0111, 1, 0)
            hwnd = user32.FindWindowW(None, target_title)
            if hwnd:
                ok_btn = _find_ok_button(hwnd)
                if ok_btn:
                    user32.SendMessageW(ok_btn, BM_CLICK, 0, 0)
                else:
                    user32.SendMessageW(hwnd, 0x0111, 1, 0)
            time.sleep(0.3)

    def _com_worker():
        word = None
        doc = None
        try:
            import comtypes.client
            import pythoncom

            pythoncom.CoInitialize()
            word = comtypes.client.CreateObject("Word.Application")
            word.Visible = False
            word.DisplayAlerts = 0
            word.AutomationSecurity = 3
            doc = word.Documents.Open(
                src_abs,
                ConfirmConversions=False,
                ReadOnly=True,
                AddToRecentFiles=False,
                NoEncodingDialog=True,
            )
            doc.SaveAs2(out_abs, FileFormat=16)
            result["ok"] = True
            print(f"[pdf→docx] Word COM success: {Path(src_abs).name}")
        except Exception as exc:
            print(f"[pdf→docx] COM failed: {exc}")
        finally:
            if doc is not None:
                try:
                    doc.Close(False)
                except Exception:
                    pass
            if word is not None:
                try:
                    word.Quit()
                except Exception:
                    pass
            try:
                import pythoncom as _pc

                _pc.CoUninitialize()
            except Exception:
                pass

    dismisser = threading.Thread(target=_dialog_dismisser, daemon=True)
    dismisser.start()
    worker = threading.Thread(target=_com_worker, daemon=True)
    worker.start()
    worker.join(timeout=60)
    stop_event.set()
    return bool(result["ok"])


def _pdf_to_docx_pdf2docx(src_abs: str, target: str) -> bool:
    from pdf2docx import Converter

    converter = Converter(src_abs)
    try:
        converter.convert(target, parse_drawing=True)
    finally:
        converter.close()
    return True


def _convert_pdf_to_docx_impl(
    src: str,
    dst_dir: str,
    cancel_event: threading.Event | None,
    mode: str,
    *,
    text_converter,
    fallback,
) -> None:
    _raise_if_cancelled(cancel_event)

    out = os.path.join(dst_dir, f"{Path(src).stem}.docx")
    src_abs = os.path.abspath(src)
    out_abs = os.path.abspath(out)
    no_text_errors = []

    if _normalise_pdf_to_word_mode(mode) == "text_only":
        engines, no_text_errors = build_text_only_engines(
            src_abs,
            fallback,
            text_converter=text_converter,
            cancel_check=lambda: _raise_if_cancelled(cancel_event),
        )
    else:
        engines = [
            ("COM", lambda target: _pdf_to_docx_word_com(src_abs, target)),
            ("pdf2docx", lambda target: _pdf_to_docx_pdf2docx(src_abs, target)),
            ("fitz fallback", lambda target: fallback(src_abs, target)),
        ]

    result = run_conversion_pipeline(
        out_abs,
        engines,
        validate_docx_artifact,
        cancel_event=cancel_event,
        stage_mode="file",
        staged_prefix="~fcp_pdf_word_",
        staged_suffix=".docx",
    )

    if result.cancelled:
        raise _ConversionCancelled()

    if not result.success:
        if no_text_errors:
            raise no_text_errors[0]
        raise RuntimeError(f"All PDF→DOCX methods failed. {result.error}")


def _solid_fitz_fallback(pdf_path, docx_path):
    import io as _io

    import fitz
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Inches, Pt

    doc = Document()

    for section in doc.sections:
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    pdf_doc = fitz.open(pdf_path)

    def _flag_to_style(flags, size, median_size):
        is_bold = bool(flags & 16)
        is_italic = bool(flags & 2)
        ratio = size / median_size if median_size else 1.0
        if ratio >= 1.6 and is_bold:
            return "heading1"
        if ratio >= 1.3 and is_bold:
            return "heading2"
        if ratio >= 1.1 and is_bold:
            return "heading3"
        return "bold_body" if is_bold else "italic_body" if is_italic else "body"

    def _apply_run_style(run, flags, size):
        run.bold = bool(flags & 16)
        run.italic = bool(flags & 2)
        if size:
            run.font.size = Pt(round(size, 1))

    def _add_table_to_doc(doc, tab):
        try:
            rows_data = tab.extract()
            if not rows_data or not rows_data[0]:
                return
            n_rows = len(rows_data)
            n_cols = max(len(r) for r in rows_data)
            tbl = doc.add_table(rows=n_rows, cols=n_cols)
            tbl.style = "Table Grid"
            for r_idx, row_data in enumerate(rows_data):
                for c_idx, cell_text in enumerate(row_data):
                    if c_idx < n_cols:
                        cell = tbl.cell(r_idx, c_idx)
                        cell.text = (cell_text or "").strip()
            doc.add_paragraph()
        except Exception as te:
            print(f"[fallback table] {te}")

    for page_num in range(len(pdf_doc)):
        if page_num > 0:
            doc.add_page_break()

        page = pdf_doc.load_page(page_num)
        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

        all_sizes = []
        for blk in text_dict.get("blocks", []):
            if blk["type"] != 0:
                continue
            for line in blk.get("lines", []):
                for span in line.get("spans", []):
                    if span.get("size", 0) > 0:
                        all_sizes.append(span["size"])
        all_sizes.sort()
        median_size = all_sizes[len(all_sizes) // 2] if all_sizes else 11.0

        table_rects = []
        tables_on_page = []
        try:
            finder = page.find_tables()
            tables_on_page = finder.tables if finder else []
            for t in tables_on_page:
                table_rects.append(fitz.Rect(t.bbox))
        except Exception:
            pass

        def _rect_in_table(rect):
            for tr in table_rects:
                inter = fitz.Rect(rect).intersect(tr)
                if not inter.is_empty and inter.get_area() > 100:
                    return True
            return False

        images_on_page = []
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                bbox_list = page.get_image_rects(xref)
                if not bbox_list:
                    continue
                bbox = bbox_list[0]
                if _rect_in_table(bbox):
                    continue
                pix = fitz.Pixmap(pdf_doc, xref)
                if pix.colorspace and pix.colorspace.n > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                if pix.width < 10 or pix.height < 10:
                    continue
                img_bytes = pix.tobytes("png")
                images_on_page.append(
                    {
                        "y0": bbox.y0,
                        "y1": bbox.y1,
                        "bytes": img_bytes,
                        "width_pt": bbox.width,
                    }
                )
                pix = None
            except Exception as ie:
                print(f"[fallback img xref={xref}] {ie}")

        images_on_page.sort(key=lambda x: x["y0"])

        stream = []
        for blk in text_dict.get("blocks", []):
            y0 = blk.get("bbox", [0, 0])[1]
            if blk["type"] == 0:
                if not _rect_in_table(fitz.Rect(blk["bbox"])):
                    stream.append(("text", y0, blk))
        for img in images_on_page:
            stream.append(("image", img["y0"], img))
        for tab in tables_on_page:
            try:
                stream.append(("table", tab.bbox[1], tab))
            except Exception:
                pass

        stream.sort(key=lambda x: x[1])

        img_inserted_xranges = set()

        for item_type, y0, obj in stream:
            if item_type == "image":
                key = round(y0 / 5) * 5
                if key in img_inserted_xranges:
                    continue
                img_inserted_xranges.add(key)
                try:
                    buf = _io.BytesIO(obj["bytes"])
                    w_pt = obj["width_pt"]
                    max_w = Inches(5.5)
                    width = min(Pt(w_pt), max_w)
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = p.add_run()
                    run.add_picture(buf, width=width)
                except Exception as ie:
                    print(f"[fallback img render] {ie}")

            elif item_type == "table":
                _add_table_to_doc(doc, obj)

            elif item_type == "text":
                blk = obj
                for line in blk.get("lines", []):
                    spans = line.get("spans", [])
                    if not spans:
                        continue

                    line_text = "".join(s.get("text", "") for s in spans)
                    if not line_text.strip():
                        continue
                    dom = max(spans, key=lambda s: len(s.get("text", "")))
                    flags = dom.get("flags", 0)
                    size = dom.get("size", median_size)
                    style_label = _flag_to_style(flags, size, median_size)

                    if style_label == "heading1":
                        p = doc.add_heading(line_text.strip(), level=1)
                    elif style_label == "heading2":
                        p = doc.add_heading(line_text.strip(), level=2)
                    elif style_label == "heading3":
                        p = doc.add_heading(line_text.strip(), level=3)
                    else:
                        p = doc.add_paragraph()
                        for span in spans:
                            span_text = span.get("text", "")
                            if not span_text:
                                continue
                            run = p.add_run(span_text)
                            _apply_run_style(run, span.get("flags", 0), span.get("size", None))

    pdf_doc.close()
    doc.save(docx_path)
    print(f"[PDF→DOCX] solid fitz fallback done: {Path(docx_path).name}")
