"""
converter/mixins/ package

Modular converter implementations split by domain:
- document_converters: txt, rtf, csv, json, xlsx, pptx
- image_converters: various image format conversions
- media_converters: audio/video via ffmpeg
- office_com: Microsoft Office COM automation
- rtf_native: native RTF → PDF rendering
- pptx_native: native PPTX → PDF rendering
- html_renderers: HTML → PDF rendering strategies
- pdf_renderers: PDF → HTML rendering
- epub_renderers: EPUB → PDF rendering
"""

from .document_converters import DocumentConverters
from .epub_renderers import EpubRenderers
from .html_renderers import HtmlRenderers
from .image_converters import ImageConverters
from .media_converters import MediaConverters
from .office_com import OfficeComConverters
from .pdf_renderers import PdfRenderers
from .pptx_native import PptxNativeConverters
from .rtf_native import RtfNativeConverters

__all__ = [
    "DocumentConverters",
    "EpubRenderers",
    "HtmlRenderers",
    "ImageConverters",
    "MediaConverters",
    "OfficeComConverters",
    "PdfRenderers",
    "PptxNativeConverters",
    "RtfNativeConverters",
]
