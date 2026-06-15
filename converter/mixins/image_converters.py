"""Image converters: Pillow, rawpy, ImageMagick."""

from __future__ import annotations

import subprocess
from pathlib import Path

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0

class ImageConverters:
    """Image conversion methods for AdvancedConverterEngine."""

    def _open_universal_image(self, src: str):
        """Open any image format using the best available library."""
        ext = Path(src).suffix.lower()
        if ext in ('.heic', '.heif'):
            try:
                from pillow_heif import register_heif_opener
                register_heif_opener()
            except ImportError:
                pass
        if ext in ('.dng', '.cr2', '.cr3', '.nef', '.arw', '.orf', '.rw2', '.raf'):
            try:
                import rawpy
                with rawpy.imread(src) as raw:
                    rgb = raw.postprocess(use_camera_wb=True, output_bps=8)
                from PIL import Image
                return Image.fromarray(rgb)
            except Exception:
                pass
        if ext == '.psd':
            try:
                from psd_tools import PSDImage
                psd = PSDImage.open(src)
                return psd.composite()
            except Exception:
                pass
        from PIL import Image
        return Image.open(src)

    def _image_convert(self, src: str, dst: str, conversion_type: str) -> bool:
        try:
            img = self._open_universal_image(src)
            ext = Path(dst).suffix.lower().lstrip('.')
            fmt_map = {
                'jpg': 'JPEG', 'jpeg': 'JPEG', 'png': 'PNG',
                'bmp': 'BMP', 'tiff': 'TIFF', 'webp': 'WEBP',
                'gif': 'GIF', 'avif': 'AVIF', 'j2k': 'JPEG2000',
            }
            fmt = fmt_map.get(ext, ext.upper())
            save_kwargs = {}
            if fmt == 'JPEG':
                img = img.convert('RGB')
                save_kwargs['quality'] = 95
            elif fmt == 'WEBP':
                save_kwargs['quality'] = 90
            img.save(dst, format=fmt, **save_kwargs)
            return True
        except Exception as e:
            print(f"[image→{conversion_type}] {e}")
            return False

    def _image_to_ico(self, src: str, dst: str, conversion_type: str | None = None) -> bool:
        try:
            img = self._open_universal_image(src)
            img = img.convert('RGBA')
            sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
            img.save(dst, format='ICO', sizes=sizes)
            return True
        except Exception as e:
            print(f"[image→ico] {e}")
            return False

    def _find_imagemagick() -> str | None:
        import shutil
        magick = shutil.which("magick") or shutil.which("convert")
        if magick:
            return magick
        return None

    def _magick_convert(self, src: str, dst: str, conversion_type: str | None = None) -> bool:
        magick = self._find_imagemagick()
        if not magick:
            return False
        try:
            cmd = [magick, src, dst]
            result = subprocess.run(cmd, capture_output=True, timeout=60, creationflags=_NO_WINDOW)
            return result.returncode == 0
        except Exception as e:
            print(f"[magick] {e}")
            return False

    def _image_to_svg(self, src: str, dst: str, conversion_type: str | None = None) -> bool:
        try:
            import cairosvg
            img = self._open_universal_image(src)
            import io
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            cairosvg.svg2png(bytestring=buf.getvalue(), write_to=dst)
            return True
        except Exception as e:
            print(f"[image→svg] {e}")
            return False

    def _image_convert_save(self, img, dst: str, ext: str) -> None:
        fmt_map = {
            '.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG',
            '.bmp': 'BMP', '.tiff': 'TIFF', '.webp': 'WEBP',
            '.gif': 'GIF', '.avif': 'AVIF',
        }
        fmt = fmt_map.get(ext, ext.upper().lstrip('.'))
        save_kwargs = {}
        if fmt == 'JPEG':
            img = img.convert('RGB')
            save_kwargs['quality'] = 95
        img.save(dst, format=fmt, **save_kwargs)

    def _raw_convert(self, src: str, dst: str, conversion_type: str | None = None) -> bool:
        try:
            import rawpy
            with rawpy.imread(src) as raw:
                rgb = raw.postprocess(use_camera_wb=True, output_bps=8)
            from PIL import Image
            img = Image.fromarray(rgb)
            ext = Path(dst).suffix.lower()
            self._image_convert_save(img, dst, ext)
            return True
        except Exception as e:
            print(f"[raw→{conversion_type}] {e}")
            return False

    def _heic_convert(self, src: str, dst: str, conversion_type: str) -> bool:
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
            from PIL import Image
            img = Image.open(src)
            ext = Path(dst).suffix.lower()
            self._image_convert_save(img, dst, ext)
            return True
        except Exception as e:
            print(f"[heic→{conversion_type}] {e}")
            return False
