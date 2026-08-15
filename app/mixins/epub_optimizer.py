"""EPUB optimization (image re-compression + deflate)."""

from __future__ import annotations

import os
from pathlib import Path


class EpubOptimizerMixin:
    """EPUB optimization methods."""

    def optimize_epub_file(self, src_path, output_path, compress_images, quality_level):
        try:
            import io as _io
            import zipfile

            quality_map = {0: 85, 1: 75, 2: 55}
            img_quality = quality_map.get(quality_level, 75)
            IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
            buf_out = _io.BytesIO()
            with (
                zipfile.ZipFile(src_path, "r") as zin,
                zipfile.ZipFile(buf_out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zout,
            ):
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    ext = Path(item.filename).suffix.lower()
                    if compress_images and ext in IMAGE_EXTS and len(data) > 2048:
                        try:
                            from PIL import Image as PILImage

                            buf_img = _io.BytesIO(data)
                            buf_new = _io.BytesIO()
                            with PILImage.open(buf_img) as img:
                                if ext in (".jpg", ".jpeg"):
                                    img.convert("RGB").save(buf_new, format="JPEG", quality=img_quality, optimize=True)
                                elif ext == ".png":
                                    compress_lvl = max(1, min(9, int(quality_level * 3) + 1))
                                    img.save(buf_new, format="PNG", optimize=True, compress_level=compress_lvl)
                                else:
                                    img.convert("RGB").save(buf_new, format="JPEG", quality=img_quality, optimize=True)
                            new_data = buf_new.getvalue()
                            if len(new_data) < len(data):
                                data = new_data
                        except Exception:
                            pass
                    if item.filename == "mimetype":
                        zout.writestr(item, data, compress_type=zipfile.ZIP_STORED)
                    else:
                        zout.writestr(item, data)
            new_bytes = buf_out.getvalue()
            orig_bytes = os.path.getsize(src_path)
            if len(new_bytes) < orig_bytes:
                with open(output_path, "wb") as f:
                    f.write(new_bytes)
            else:
                import shutil as _sh

                _sh.copy2(src_path, output_path)
            return True
        except Exception as e:
            print(f"EPUB optimization error {src_path}: {e}")
            return False
