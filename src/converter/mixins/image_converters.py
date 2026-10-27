"""Image converters: Pillow, rawpy, ImageMagick."""

from __future__ import annotations

import subprocess
from pathlib import Path

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0


class ImageConverters:
    """Image conversion methods for AdvancedConverterEngine."""

    def _open_universal_image(self, src: str):
        """Open any image format using the best available library."""
        ext = Path(src).suffix.lower()
        if ext == ".svg":
            import io

            import fitz
            from PIL import Image

            with fitz.open(src) as doc:
                png = doc[0].get_pixmap(alpha=True).tobytes("png")
            return Image.open(io.BytesIO(png))
        if ext in (".heic", ".heif"):
            try:
                from pillow_heif import register_heif_opener

                register_heif_opener()
            except ImportError:
                pass
        if ext in (".dng", ".cr2", ".cr3", ".nef", ".arw", ".orf", ".rw2", ".raf"):
            try:
                import rawpy

                with rawpy.imread(src) as raw:
                    rgb = raw.postprocess(use_camera_wb=True, output_bps=8)
                from PIL import Image

                return Image.fromarray(rgb)
            except Exception:
                pass
        if ext == ".psd":
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
            ext = Path(dst).suffix.lower().lstrip(".")
            fmt_map = {
                "jpg": "JPEG",
                "jpeg": "JPEG",
                "png": "PNG",
                "bmp": "BMP",
                "tiff": "TIFF",
                "webp": "WEBP",
                "gif": "GIF",
                "avif": "AVIF",
                "j2k": "JPEG2000",
            }
            fmt = fmt_map.get(ext, ext.upper())
            save_kwargs = {}
            if fmt == "JPEG":
                img = self._flatten_jpeg(img)
                save_kwargs["quality"] = 95
            elif fmt == "WEBP":
                save_kwargs["quality"] = 90
            img.save(dst, format=fmt, **save_kwargs)
            return True
        except Exception as e:
            print(f"[image→{conversion_type}] {e}")
            return False

    def _image_to_ico(self, src: str, dst: str, conversion_type: str | None = None) -> bool:
        try:
            img = self._open_universal_image(src)
            img = img.convert("RGBA")
            layer = self._icon_layer_setting()
            if layer == "multi":
                sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
            else:
                try:
                    n = int(layer)
                except (TypeError, ValueError):
                    n = 256
                sizes = [(n, n)]
            img.save(dst, format="ICO", sizes=sizes)
            return True
        except Exception as e:
            print(f"[image→ico] {e}")
            return False

    @staticmethod
    def _icon_layer_setting() -> str:
        """Read the user's icon-layer preference from saved config."""
        try:
            from config import ConfigManager

            config = ConfigManager().load_config()
            return str(config.get("image_to_icon_layer", "multi"))
        except Exception:
            return "multi"

    @staticmethod
    def _find_imagemagick() -> str | None:
        from external_binaries import resolve_binary

        return resolve_binary("imagemagick")

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
        """Vectorise the image into an SVG with VTracer.

        PNG/JPEG/TIFF/... go straight to VTracer. HEIC/AVIF (even when misnamed)
        are decoded to a temporary PNG by decodable_image_path ; anything else
        VTracer cannot read is decoded by Pillow via _open_universal_image.
        """
        try:
            import vtracer

            from utils.image_formats import decodable_image_path

            try:
                with decodable_image_path(src) as readable:
                    vtracer.convert_image_to_svg_py(readable, dst)
            except (KeyboardInterrupt, SystemExit):
                raise
            except BaseException:
                # VTracer panics on formats it cannot decode, and PanicException
                # derives from BaseException rather than Exception.
                self._vtracer_from_pillow(vtracer, src, dst)
            if Path(dst).is_file() and Path(dst).stat().st_size > 0:
                return True
            raise RuntimeError("VTracer produced no output")
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException as e:
            print(f"[image→svg] {e}")
            try:
                if Path(dst).is_file() and Path(dst).stat().st_size == 0:
                    Path(dst).unlink()
            except OSError:
                pass
            return False

    def _vtracer_from_pillow(self, vtracer, src: str, dst: str) -> None:
        """Decode an image VTracer cannot read directly, then trace the temporary PNG."""
        import os
        import tempfile

        img = self._open_universal_image(src)
        if img.mode not in ("RGB", "RGBA"):
            has_alpha = "A" in img.getbands() or "transparency" in img.info
            img = img.convert("RGBA" if has_alpha else "RGB")
        fd, tmp_png = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        try:
            img.save(tmp_png, format="PNG")
            vtracer.convert_image_to_svg_py(tmp_png, dst)
        finally:
            try:
                os.remove(tmp_png)
            except OSError:
                pass

    def _image_convert_save(self, img, dst: str, ext: str) -> None:
        fmt_map = {
            ".jpg": "JPEG",
            ".jpeg": "JPEG",
            ".png": "PNG",
            ".bmp": "BMP",
            ".tiff": "TIFF",
            ".webp": "WEBP",
            ".gif": "GIF",
            ".avif": "AVIF",
        }
        fmt = fmt_map.get(ext, ext.upper().lstrip("."))
        save_kwargs = {}
        if fmt == "JPEG":
            img = self._flatten_jpeg(img)
            save_kwargs["quality"] = 95
        img.save(dst, format=fmt, **save_kwargs)

    @staticmethod
    def _flatten_jpeg(img):
        """Composite transparent pixels onto white so JPEGs do not turn black."""
        if img.mode in ("RGBA", "LA") or "transparency" in img.info:
            from PIL import Image

            rgba = img.convert("RGBA")
            flat = Image.new("RGB", rgba.size, "white")
            flat.paste(rgba, mask=rgba.split()[3])
            return flat
        return img.convert("RGB")

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
