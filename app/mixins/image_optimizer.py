"""Image optimization (Pillow re-encode + resize)."""

from __future__ import annotations

import os
from pathlib import Path


class ImageOptimizerMixin:
    """Image optimization methods."""

    def optimize_image_file(self, img_path, output_path, quality_level):
        try:
            import shutil

            from PIL import Image as PILImage

            quality_map = {0: 85, 1: 75, 2: 55}
            quality = quality_map.get(quality_level, 75)
            # Long-edge cap per tier. This is the main size lever for photos
            # straight off a phone/camera — quality/compress_level alone
            # barely move the needle if the pixel dimensions stay huge.
            max_dim_map = {0: 3840, 1: 2560, 2: 1600}
            max_dim = max_dim_map.get(quality_level, 2560)
            try:
                RESAMPLE = PILImage.Resampling.LANCZOS
            except AttributeError:
                RESAMPLE = PILImage.LANCZOS

            # .bmp used to be remapped to "PNG" here while output_path kept
            # its .bmp extension, so a "compressed" bmp actually contained
            # PNG bytes under the wrong extension. Keeping bmp -> BMP is
            # correct (if not much smaller); a real bmp->png size win needs
            # the caller to hand this function a .png output path instead.
            ext_map = {
                ".jpg": "JPEG",
                ".jpeg": "JPEG",
                ".png": "PNG",
                ".bmp": "BMP",
                ".tiff": "TIFF",
                ".webp": "WEBP",
                ".gif": "GIF",
            }
            src_ext = Path(img_path).suffix.lower()
            dst_ext = Path(output_path).suffix.lower()
            fmt_out = ext_map.get(dst_ext, ext_map.get(src_ext, "JPEG"))

            original_size = os.path.getsize(img_path)
            tmp_output = output_path + ".opt_tmp"

            with PILImage.open(img_path) as img:
                exif_data = None
                try:
                    exif_data = img.info.get("exif")
                except Exception:
                    pass

                is_animated = getattr(img, "is_animated", False) and fmt_out in ("GIF", "WEBP")

                if is_animated:
                    self._save_animated_image(img, tmp_output, fmt_out, quality, RESAMPLE, max_dim)
                else:
                    frame = img.copy()
                    if frame.width > max_dim or frame.height > max_dim:
                        frame.thumbnail((max_dim, max_dim), RESAMPLE)

                    if fmt_out == "JPEG":
                        rgb = frame.convert("RGB")
                        save_kwargs = {"quality": quality, "optimize": True}
                        if exif_data:
                            save_kwargs["exif"] = exif_data
                        rgb.save(tmp_output, format="JPEG", **save_kwargs)
                    elif fmt_out == "PNG":
                        # PNG has no "quality" concept — quality_level (0/1/2) is
                        # remapped onto PIL's compress_level range (0-9, lossless
                        # either way; higher just spends more CPU for a smaller
                        # file). 0->0(min,clamped to 1), 1->3, 2->6.
                        compress = max(1, min(9, int(quality_level * 3)))
                        frame.save(tmp_output, format="PNG", optimize=True, compress_level=compress)
                    elif fmt_out == "WEBP":
                        # method=6 = slowest/best compression PIL's WEBP encoder
                        # offers; fine here since this runs once per file, not
                        # in a hot loop.
                        frame.save(tmp_output, format="WEBP", quality=quality, method=6)
                    else:
                        frame.save(tmp_output, format=fmt_out)

            # Never hand back a file that isn't actually smaller — mirrors
            # the size guard every other optimizer in this file already has.
            if os.path.exists(tmp_output) and os.path.getsize(tmp_output) < original_size:
                shutil.move(tmp_output, output_path)
            else:
                if os.path.exists(tmp_output):
                    os.remove(tmp_output)
                if os.path.abspath(output_path) != os.path.abspath(img_path):
                    shutil.copy2(img_path, output_path)
                # else: in-place mode — original bytes at output_path were
                # never touched, nothing to do.
            return True
        except Exception as e:
            print(f"Image optimization error {img_path}: {e}")
            return False

    def _save_animated_image(self, img, tmp_output, fmt_out, quality, resample, max_dim):
        """Resize + re-save every frame of an animated GIF/WEBP with save_all.
        Plain img.save() only writes the current frame, which silently
        truncates animations to a single still image."""
        from PIL import ImageSequence

        frames = []
        for frame in ImageSequence.Iterator(img):
            f = frame.convert(frame.mode)
            if f.width > max_dim or f.height > max_dim:
                f.thumbnail((max_dim, max_dim), resample)
            frames.append(f)

        duration = img.info.get("duration", 100)
        loop = img.info.get("loop", 0)
        save_kwargs = {
            "format": fmt_out,
            "save_all": True,
            "append_images": frames[1:],
            "duration": duration,
            "loop": loop,
            "disposal": img.info.get("disposal", 2),
        }
        if fmt_out == "WEBP":
            save_kwargs["quality"] = quality
            save_kwargs["method"] = 6
        elif fmt_out == "GIF":
            save_kwargs["optimize"] = True

        frames[0].save(tmp_output, **save_kwargs)
