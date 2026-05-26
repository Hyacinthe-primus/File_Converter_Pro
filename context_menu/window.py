"""
context_menu/window.py
Quick Convert popup for Windows Shell Integration for File Converter Pro

Launched via:
    FileConverterPro.exe --context-menu --files "path1" "path2" ...
"""

import os
import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QProgressBar, QFrame, QApplication
)
from PySide6.QtGui  import QIcon
from PySide6.QtCore import Qt, QThread, Signal, QTimer

CONVERSION_MAP: dict[str, list[str]] = {
    # Images
    "jpg":  ["image_to_pdf", "image_to_png", "image_to_jpeg", "image_to_webp",
             "image_to_bmp", "image_to_tiff", "image_to_avif", "image_to_j2k",
             "image_to_svg", "image_to_ico", "image_to_heic", "image_to_psd",
             "image_to_dng", "image_to_jpg"],
    "jpeg": ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_webp",
             "image_to_bmp", "image_to_tiff", "image_to_avif", "image_to_j2k",
             "image_to_svg", "image_to_ico", "image_to_heic", "image_to_psd",
             "image_to_dng", "image_to_jpeg"],
    "png":  ["image_to_pdf", "image_to_jpg", "image_to_jpeg", "image_to_webp",
             "image_to_bmp", "image_to_tiff", "image_to_avif", "image_to_j2k",
             "image_to_svg", "image_to_ico", "image_to_heic", "image_to_psd",
             "image_to_dng", "image_to_png"],
    "webp": ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_bmp", "image_to_tiff", "image_to_avif", "image_to_j2k",
             "image_to_svg", "image_to_ico", "image_to_heic", "image_to_psd",
             "image_to_dng", "image_to_webp"],
    "bmp":  ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_tiff", "image_to_avif", "image_to_j2k",
             "image_to_svg", "image_to_ico", "image_to_heic", "image_to_psd",
             "image_to_dng", "image_to_bmp"],
    "tiff": ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_avif", "image_to_j2k",
             "image_to_svg", "image_to_ico", "image_to_heic", "image_to_psd",
             "image_to_dng", "image_to_tiff"],
    "tif":  ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_avif", "image_to_j2k",
             "image_to_svg", "image_to_ico", "image_to_heic", "image_to_psd",
             "image_to_dng", "image_to_tif"],
    "heic": ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_tiff", "image_to_avif",
             "image_to_j2k", "image_to_svg", "image_to_ico", "image_to_psd",
             "image_to_dng", "image_to_heic"],
    "jfif": ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_tiff", "image_to_avif",
             "image_to_j2k", "image_to_svg", "image_to_ico", "image_to_psd",
             "image_to_dng", "image_to_heic"],
    "heif": ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_tiff", "image_to_avif",
             "image_to_j2k", "image_to_svg", "image_to_ico", "image_to_psd",
             "image_to_dng", "image_to_heic"],
    "avif": ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_tiff", "image_to_j2k",
             "image_to_svg", "image_to_ico", "image_to_heic", "image_to_psd",
             "image_to_dng", "image_to_avif"],
    "gif":  ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_tiff", "image_to_avif",
             "image_to_j2k", "image_to_svg", "image_to_ico", "image_to_heic",
             "image_to_psd", "image_to_dng"],
    "psd":  ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_tiff", "image_to_avif",
             "image_to_j2k", "image_to_svg", "image_to_ico", "image_to_heic",
             "image_to_dng", "image_to_psd"],
    "svg":  ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_tiff", "image_to_avif",
             "image_to_j2k", "image_to_ico", "image_to_heic", "image_to_psd",
             "image_to_dng", "image_to_psd"],
    "j2k":  ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_tiff", "image_to_avif",
             "image_to_svg", "image_to_ico", "image_to_heic", "image_to_psd",
             "image_to_dng", "image_to_j2k"],
    "jp2":  ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_tiff", "image_to_avif",
             "image_to_svg", "image_to_ico", "image_to_heic", "image_to_psd",
             "image_to_dng", "image_to_j2k"],
    "jpx":  ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_tiff", "image_to_avif",
             "image_to_svg", "image_to_ico", "image_to_heic", "image_to_psd",
             "image_to_dng", "image_to_j2k"],
    "dng":  ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_tiff", "image_to_avif",
             "image_to_j2k", "image_to_svg", "image_to_ico", "image_to_heic",
             "image_to_psd", "image_to_dng"],
    "raw":  ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_tiff", "image_to_avif",
             "image_to_j2k", "image_to_svg", "image_to_ico", "image_to_heic",
             "image_to_psd", "image_to_dng"],
    "cr2":  ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_tiff", "image_to_avif",
             "image_to_j2k", "image_to_svg", "image_to_ico", "image_to_heic",
             "image_to_psd", "image_to_dng"],
    "cr3":  ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_tiff", "image_to_avif",
             "image_to_j2k", "image_to_svg", "image_to_ico", "image_to_heic",
             "image_to_psd", "image_to_dng"],
    "nef":  ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_tiff", "image_to_avif",
             "image_to_j2k", "image_to_svg", "image_to_ico", "image_to_heic",
             "image_to_psd", "image_to_dng"],
    "arw":  ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_tiff", "image_to_avif",
             "image_to_j2k", "image_to_svg", "image_to_ico", "image_to_heic",
             "image_to_psd", "image_to_dng"],
    "orf":  ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_tiff", "image_to_avif",
             "image_to_j2k", "image_to_svg", "image_to_ico", "image_to_heic",
             "image_to_psd", "image_to_dng"],
    "rw2":  ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_tiff", "image_to_avif",
             "image_to_j2k", "image_to_svg", "image_to_ico", "image_to_heic",
             "image_to_psd", "image_to_dng"],
    "raf":  ["image_to_pdf", "image_to_png", "image_to_jpg", "image_to_jpeg",
             "image_to_webp", "image_to_bmp", "image_to_tiff", "image_to_avif",
             "image_to_j2k", "image_to_svg", "image_to_ico", "image_to_heic",
             "image_to_psd", "image_to_dng"],
    # Documents
    "docx": ["docx_to_pdf"],
    "doc":  ["docx_to_pdf"],
    "pdf":  ["pdf_to_docx", "pdf_to_html"],
    "txt":  ["txt_to_pdf",  "txt_to_docx"],
    "rtf":  ["rtf_to_pdf",  "rtf_to_docx"],
    "xlsx": ["xlsx_to_pdf", "xlsx_to_csv",  "xlsx_to_json"],
    "pptx": ["pptx_to_pdf"],
    "html": ["html_to_pdf"],
    "epub": ["epub_to_pdf"],
    "csv":  ["csv_to_json"],
    "json": ["json_to_csv"],
    # Audio
    "wav":  ["audio_to_mp3", "audio_to_aac", "audio_to_flac", "audio_to_ogg",  "audio_to_m4a", "audio_to_wav"],
    "mp3":  ["audio_to_wav", "audio_to_aac", "audio_to_flac", "audio_to_ogg",  "audio_to_m4a", "audio_to_mp3"],
    "aac":  ["audio_to_mp3", "audio_to_wav", "audio_to_flac", "audio_to_ogg",  "audio_to_m4a", "audio_to_aac"],
    "flac": ["audio_to_mp3", "audio_to_wav", "audio_to_aac",  "audio_to_ogg",  "audio_to_m4a", "audio_to_flac"],
    "ogg":  ["audio_to_mp3", "audio_to_wav", "audio_to_aac",  "audio_to_flac", "audio_to_m4a", "audio_to_ogg"],
    "m4a":  ["audio_to_mp3", "audio_to_wav", "audio_to_aac",  "audio_to_flac", "audio_to_ogg", "audio_to_m4a"],
    # Video
    "avi":  ["video_to_mp4", "video_to_mkv", "video_to_webm", "video_to_mov", "video_to_avi",
             "video_to_mp3", "video_to_wav", "video_to_aac",  "video_to_flac"],
    "webm": ["video_to_mp4", "video_to_mkv", "video_to_avi",  "video_to_mov", "video_to_webm",
             "video_to_mp3", "video_to_wav", "video_to_aac",  "video_to_flac"],
    "mkv":  ["video_to_mp4", "video_to_avi", "video_to_webm", "video_to_mov", "video_to_mkv",
             "video_to_mp3", "video_to_wav", "video_to_aac",  "video_to_flac"],
    "mov":  ["video_to_mp4", "video_to_mkv", "video_to_avi",  "video_to_webm", "video_to_mov",
             "video_to_mp3", "video_to_wav", "video_to_aac",  "video_to_flac"],
    "mp4":  ["video_to_mkv", "video_to_avi", "video_to_webm", "video_to_mov", "video_to_mp4",
             "video_to_mp3", "video_to_wav", "video_to_aac",  "video_to_flac"],
}

LABELS: dict[str, str] = {
    "image_to_pdf":  "Image → PDF",
    "image_to_png":  "Image → PNG",  "image_to_jpg":  "Image → JPG",
    "image_to_jpeg": "Image → JPEG", "image_to_bmp":  "Image → BMP",
    "image_to_webp": "Image → WEBP", "image_to_tiff": "Image → TIFF",
    "image_to_heic": "Image → HEIC", "image_to_avif": "Image → AVIF",
    "image_to_psd":  "Image → PSD",  "image_to_svg":  "Image → SVG",
    "image_to_dng":  "Image → DNG",  "image_to_ico":  "Image → ICO",
    "image_to_j2k":  "Image → J2K",
    "docx_to_pdf":   "Word → PDF",   "pdf_to_docx":   "PDF → Word",
    "txt_to_pdf":    "TXT → PDF",    "txt_to_docx":   "TXT → DOCX",
    "rtf_to_pdf":    "RTF → PDF",    "rtf_to_docx":   "RTF → DOCX",
    "xlsx_to_pdf":   "XLSX → PDF",   "xlsx_to_csv":   "XLSX → CSV",
    "xlsx_to_json":  "XLSX → JSON",  "pptx_to_pdf":   "PPTX → PDF",
    "html_to_pdf":   "HTML → PDF",   "pdf_to_html":   "PDF → HTML",
    "epub_to_pdf":   "EPUB → PDF",   "csv_to_json":   "CSV → JSON",
    "json_to_csv":   "JSON → CSV",
    "audio_to_mp3":  "Audio → MP3",  "audio_to_wav":  "Audio → WAV",
    "audio_to_aac":  "Audio → AAC",  "audio_to_ogg":  "Audio → OGG",
    "audio_to_flac": "Audio → FLAC", "audio_to_m4a":  "Audio → M4A",
    "video_to_mp4":  "Video → MP4",  "video_to_mkv":  "Video → MKV",
    "video_to_avi":  "Video → AVI",  "video_to_webm": "Video → WEBM",
    "video_to_mov":  "Video → MOV",  "video_to_mp3":  "Video → MP3",
    "video_to_wav":  "Video → WAV",  "video_to_aac":  "Video → AAC",
    "video_to_flac": "Video → FLAC",
}

STYLE = """
#card {
    background: rgba(20, 22, 35, 0.92);
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.08);
}
QLabel { color: rgba(255,255,255,0.85); font-family: 'Segoe UI'; }
#title    { font-size: 13px; font-weight: 700; color: rgba(255,255,255,0.92); }
#fileList { font-size: 11px; color: rgba(255,255,255,0.45); }
QComboBox {
    background: rgba(255,255,255,0.06);
    color: rgba(255,255,255,0.85);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 7px;
    padding: 7px 10px; font-size: 12px; font-family: 'Segoe UI';
    min-height: 16px;
}
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background: #1a1d2e; color: rgba(255,255,255,0.85);
    selection-background-color: rgba(110,190,255,0.20);
    border: 1px solid rgba(255,255,255,0.08); outline: none;
}
QPushButton#convertBtn {
    background: rgba(110,190,255,0.18);
    color: rgb(110,190,255);
    border: 1px solid rgba(110,190,255,0.35);
    border-radius: 8px;
    padding: 9px 0; font-weight: 700;
    font-size: 12px; font-family: 'Segoe UI';
}
QPushButton#convertBtn:hover    { background: rgba(110,190,255,0.28); }
QPushButton#convertBtn:disabled {
    background: rgba(255,255,255,0.05);
    color: rgba(255,255,255,0.20);
    border-color: rgba(255,255,255,0.07);
}
QPushButton#cancelBtn {
    background: rgba(255,255,255,0.05);
    color: rgba(255,255,255,0.40);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 8px;
    padding: 9px 0; font-size: 12px; font-family: 'Segoe UI';
}
QPushButton#cancelBtn:hover {
    background: rgba(255,255,255,0.10);
    color: rgba(255,255,255,0.75);
    border-color: rgba(255,255,255,0.20);
}
QProgressBar {
    background: rgba(255,255,255,0.06);
    border-radius: 3px;
    min-height: 5px; max-height: 5px; border: none;
}
QProgressBar::chunk { background: rgba(110,190,255,0.70); border-radius: 3px; }
#statusOk  { font-size: 11px; color: rgb(32,200,170); font-family: 'Segoe UI'; }
#statusErr { font-size: 11px; color: rgb(255,100,100); font-family: 'Segoe UI'; }
#conversionLabel {
    font-size: 12px; font-weight: 600;
    color: rgb(110,190,255);
    font-family: 'Segoe UI';
}
"""

AUTO_CLOSE_DELAY_MS = 1800


def _convert_image_to_pdf(src: str, dst_dir: str) -> None:
    """Image → PDF via fitz (mirrors logic.py convert_images_to_separate_pdfs)."""
    import fitz
    from pathlib import Path
    out = os.path.join(dst_dir, f"{Path(src).stem}.pdf")
    pdf = fitz.open()
    img = fitz.open(src)
    rect = img[0].rect
    page = pdf.new_page(width=rect.width, height=rect.height)
    page.insert_image(rect, filename=src)
    img.close()
    pdf.save(out)
    pdf.close()


def _convert_docx_to_pdf(src: str, dst_dir: str) -> None:
    """DOCX → PDF with full fallback chain."""
    from pathlib import Path
    out = os.path.join(dst_dir, f"{Path(src).stem}.pdf")
    src_abs = os.path.abspath(src)
    out_abs = os.path.abspath(out)

    try:
        from docx2pdf import convert
        convert(src_abs, out_abs)
        return
    except Exception as e:
        print(f"[docx→pdf] docx2pdf failed: {e}")

    try:
        import comtypes.client
        word = comtypes.client.CreateObject("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(src_abs)
        doc.SaveAs(out_abs, FileFormat=17)
        doc.Close(False)
        word.Quit()
        return
    except Exception as e:
        print(f"[docx→pdf] COM failed: {e}")

    try:
        import subprocess, shutil
        candidates = [
            "soffice", "libreoffice",
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        exe = next((c for c in candidates if shutil.which(c) or os.path.exists(c)), None)
        if exe:
            subprocess.run(
                [exe, "--headless", "--convert-to", "pdf", "--outdir", dst_dir, src_abs],
                check=True, capture_output=True, timeout=60
            )
            return
    except Exception as e:
        print(f"[docx→pdf] LibreOffice failed: {e}")

    try:
        from docx import Document as DocxDoc
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        doc    = DocxDoc(src_abs)
        styles = getSampleStyleSheet()
        story  = []
        for para in doc.paragraphs:
            if para.text.strip():
                story.append(Paragraph(para.text, styles["Normal"]))
                story.append(Spacer(1, 6))
        SimpleDocTemplate(out_abs, pagesize=A4).build(story)
        return
    except Exception as e:
        print(f"[docx→pdf] reportlab failed: {e}")

    raise RuntimeError("All DOCX→PDF methods failed.")


def _convert_pdf_to_docx(src: str, dst_dir: str) -> None:
    """PDF → DOCX with full fallback chain."""
    from pathlib import Path
    out = os.path.join(dst_dir, f"{Path(src).stem}.docx")
    src_abs = os.path.abspath(src)
    out_abs = os.path.abspath(out)

    try:
        from pdf2docx import Converter
        cv = Converter(src_abs)
        cv.convert(out_abs)
        cv.close()
        return
    except Exception as e:
        print(f"[pdf→docx] pdf2docx failed: {e}")

    try:
        import comtypes.client
        word = comtypes.client.CreateObject("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(src_abs)
        doc.SaveAs(out_abs, FileFormat=16)
        doc.Close(False)
        word.Quit()
        return
    except Exception as e:
        print(f"[pdf→docx] COM failed: {e}")

    try:
        import fitz
        from docx import Document as DocxDoc
        pdf_doc  = fitz.open(src_abs)
        word_doc = DocxDoc()
        for page_num in range(len(pdf_doc)):
            text = pdf_doc.load_page(page_num).get_text("text")
            for line in text.split("\n"):
                if line.strip():
                    word_doc.add_paragraph(line.strip())
            if page_num < len(pdf_doc) - 1:
                word_doc.add_page_break()
        pdf_doc.close()
        word_doc.save(out_abs)
        return
    except Exception as e:
        print(f"[pdf→docx] fitz failed: {e}")

    raise RuntimeError("All PDF→DOCX methods failed.")


class ConversionThread(QThread):
    done = Signal(bool, str, str)

    def __init__(self, files: list[str], conversion_type: str):
        super().__init__()
        self.files           = files
        self.conversion_type = conversion_type

    def run(self):
        try:
            base = os.path.dirname(
                sys.executable if getattr(sys, "frozen", False)
                else os.path.abspath(os.path.join(__file__, "..", ".."))
            )
            if base not in sys.path:
                sys.path.insert(0, base)

            errors  = []
            out_dir = ""

            for f in self.files:
                dst_dir = os.path.dirname(f)
                try:
                    if self.conversion_type == "image_to_pdf":
                        _convert_image_to_pdf(f, dst_dir)
                    elif self.conversion_type == "docx_to_pdf":
                        _convert_docx_to_pdf(f, dst_dir)
                    elif self.conversion_type == "pdf_to_docx":
                        _convert_pdf_to_docx(f, dst_dir)
                    else:
                        from converter.converters import AdvancedConverterEngine
                        result = AdvancedConverterEngine().convert(
                            self.conversion_type, f, dst_dir
                        )
                        if not result.success:
                            raise Exception(result.error)
                    out_dir = dst_dir
                except Exception as e:
                    errors.append(f"{os.path.basename(f)}: {e}")

            if errors:
                self.done.emit(False, "\n".join(errors), "")
            else:
                n = len(self.files)
                self.done.emit(True, f"{n} file{'s' if n > 1 else ''} converted", out_dir)

        except Exception as e:
            self.done.emit(False, str(e), "")


class QuickConvertWindow(QWidget):
    """Floating window launched from the Windows context menu."""

    def __init__(self, files: list[str], conversion_type: str | None = None):
        super().__init__()
        self.files = [f for f in files if os.path.isfile(f)]
        self._converting = False

        self.ext = (
            os.path.splitext(self.files[0])[1].lstrip(".").lower()
            if self.files else ""
        )
        self.forced_conversion = conversion_type
        self.conversion_types  = (
            [conversion_type] if conversion_type
            else CONVERSION_MAP.get(self.ext, [])
        )

        self.setWindowTitle("File Converter Pro")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(310)
        self.setMaximumWidth(310)

        self._set_icon()
        self._build_ui()
        self._center_on_screen()

    def _set_icon(self):
        candidates = [
            os.path.join(os.path.dirname(sys.executable), "icon.ico"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "icon.ico"),
            "icon.ico",
        ]
        for p in candidates:
            if os.path.exists(p):
                self.setWindowIcon(QIcon(p))
                break

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame()
        self.card.setObjectName("card")
        self.card.setStyleSheet(STYLE)

        inner = QVBoxLayout(self.card)
        inner.setSpacing(10)
        inner.setContentsMargins(18, 16, 18, 16)
        self._build_ui_inner(inner)

        root.addWidget(self.card)
        self.progress.show()
        self.adjustSize()
        self.setFixedHeight(self.sizeHint().height())
        self.progress.hide()

    def _build_ui_inner(self, inner: QVBoxLayout):
        """Populates the card's inner layout (shared by init and reload)."""
        title = QLabel("Quick Convert")
        title.setObjectName("title")
        inner.addWidget(title)

        n = len(self.files)
        if n == 1:
            file_text = os.path.basename(self.files[0])
        elif n <= 4:
            file_text = "\n".join(f"• {os.path.basename(f)}" for f in self.files)
        else:
            previews  = "\n".join(f"• {os.path.basename(f)}" for f in self.files[:3])
            file_text = f"{previews}\n• … and {n - 3} more"

        file_label = QLabel(file_text)
        file_label.setObjectName("fileList")
        file_label.setWordWrap(True)
        inner.addWidget(file_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #313244; max-height: 1px;")
        inner.addWidget(sep)

        if not self.conversion_types:
            msg = QLabel(f"No conversion available for .{self.ext or '?'}")
            msg.setObjectName("fileList")
            msg.setWordWrap(True)
            inner.addWidget(msg)
        elif self.forced_conversion:
            label = QLabel(LABELS.get(self.forced_conversion, self.forced_conversion))
            label.setObjectName("conversionLabel")
            inner.addWidget(label)
            self.combo = None
        else:
            self.combo = QComboBox()
            for ct in self.conversion_types:
                self.combo.addItem(LABELS.get(ct, ct), ct)
            inner.addWidget(self.combo)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        inner.addWidget(self.progress)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusOk")
        self.status_label.setWordWrap(True)
        self.status_label.hide()
        inner.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.close)

        self.convert_btn = QPushButton("Convert")
        self.convert_btn.setObjectName("convertBtn")
        self.convert_btn.setEnabled(bool(self.conversion_types))
        self.convert_btn.clicked.connect(self._start_conversion)

        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.convert_btn)
        inner.addLayout(btn_row)

    def _center_on_screen(self):
        geo = QApplication.primaryScreen().availableGeometry()
        self.move(
            geo.center().x() - self.width()  // 2,
            geo.center().y() - self.height() // 2,
        )

    def _start_conversion(self):
        conversion_type = (
            self.forced_conversion
            if self.forced_conversion
            else self.combo.currentData()
        )
        self._converting = True
        self.convert_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.progress.show()
        self.status_label.hide()

        self._worker_thread = ConversionThread(self.files, conversion_type)
        self._worker_thread.done.connect(self._on_done)
        self._worker_thread.start()

    def _on_done(self, success: bool, message: str, out_dir: str):
        self._converting = False
        self.progress.hide()
        self.status_label.show()
        self.adjustSize()
        self.setFixedHeight(self.sizeHint().height())

        if success:
            self.status_label.setObjectName("statusOk")
            self.status_label.setText(f"✓ {message}")
            QTimer.singleShot(AUTO_CLOSE_DELAY_MS, QApplication.quit)
        else:
            self.status_label.setObjectName("statusErr")
            self.status_label.setText(f"✗ {message}")
            self.convert_btn.setText("Retry")
            self.convert_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
            self.convert_btn.clicked.disconnect()
            self.convert_btn.clicked.connect(self._start_conversion)

        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton and hasattr(self, "_drag_pos"):
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def closeEvent(self, e):
        e.accept()
        if hasattr(self, "_worker_thread") and self._worker_thread.isRunning():
            self._worker_thread.quit()
            self._worker_thread.wait(2000)
            os._exit(0)
        else:
            QApplication.quit()


def run_context_menu(files: list[str], conversion_type: str | None = None) -> None:
    """Called from main.py when --context-menu flag is detected."""
    app = QApplication.instance() or QApplication(sys.argv)
    win = QuickConvertWindow(files, conversion_type=conversion_type)
    win.show()

    if conversion_type:
        QTimer.singleShot(100, win._start_conversion)

    sys.exit(app.exec())