"""PDF optimization strategy.

Tries Ghostscript first (rebuilds the PDF from rendered content — best general
compression, also recovers files with corrupted xref tables), falls back to PyMuPDF
(garbage-collection + font subsetting, works fully offline), then pikepdf
(QPDF-based repair, also fully offline) if PyMuPDF's save doesn't validate.
A file is never handed back larger than the original — see the final size guard
in optimize_pdf_file."""

from __future__ import annotations

import os


class PdfOptimizerMixin:
    """PDF optimization methods."""

    def optimize_pdf_file(self, pdf_path, output_path, compression_level, remove_metadata, compress_images):
        try:
            original_size = os.path.getsize(pdf_path)

            # Ghostscript first: rebuilds the PDF from rendered content rather
            # than patching the existing object table, so it handles both
            # normal compression AND recovers files with corrupted xrefs in
            # one pass - no need to detect corruption and branch separately.
            print(f"[optimize_pdf] '{pdf_path}': trying Ghostscript first")
            if self._ghostscript_compress(pdf_path, output_path, compression_level):
                if os.path.getsize(output_path) < original_size:
                    print(f"[optimize_pdf] '{pdf_path}': Ghostscript succeeded and reduced size, done")
                    return True
                print(
                    f"[optimize_pdf] '{pdf_path}': Ghostscript succeeded but didn't reduce size, trying PyMuPDF/pikepdf anyway"  # noqa: E501
                )
            else:
                print(f"[optimize_pdf] '{pdf_path}': Ghostscript unavailable or failed, falling back to PyMuPDF")

            import fitz

            images_touched = False
            pdf_document = fitz.open(pdf_path)

            if compress_images:
                dpi_map = {"high": 150, "normal": 120, "very_reduced": 96}
                quality_map = {"high": 85, "normal": 75, "very_reduced": 55}
                target_dpi = dpi_map.get(compression_level, 120)
                jpeg_quality = quality_map.get(compression_level, 75)
                images_touched = self._downsample_pdf_images(pdf_document, target_dpi, jpeg_quality)

            try:
                pdf_document.subset_fonts()
            except Exception as e:
                print(f"[optimize_pdf] '{pdf_path}': subset_fonts skipped: {e}")

            if remove_metadata:
                pdf_document.set_metadata({})

            if images_touched:
                safe_options = {"garbage": 1, "deflate": True, "clean": False, "deflate_fonts": True}
            else:
                safe_options = {"garbage": 4, "deflate": True, "clean": True, "deflate_fonts": True}

            pymupdf_output = output_path + ".pymupdf_tmp.pdf"
            pdf_document.save(pymupdf_output, **safe_options)
            pdf_document.close()

            if self._validate_pdf(pymupdf_output):
                if not os.path.exists(output_path) or os.path.getsize(pymupdf_output) < os.path.getsize(output_path):
                    import shutil

                    shutil.move(pymupdf_output, output_path)
                    print(f"[optimize_pdf] '{pdf_path}': PyMuPDF save is smaller, using it")
                else:
                    os.remove(pymupdf_output)
                    print(f"[optimize_pdf] '{pdf_path}': PyMuPDF save didn't beat current best, discarding")
            else:
                print(f"[optimize_pdf] '{pdf_path}': PyMuPDF save failed validation, trying pikepdf")
                if os.path.exists(pymupdf_output):
                    os.remove(pymupdf_output)
                if not os.path.exists(output_path):
                    if not self._pikepdf_compress(pdf_path, output_path, compression_level):
                        print(f"[optimize_pdf] '{pdf_path}': pikepdf also failed, zero-touch resave")
                        zero_doc = fitz.open(pdf_path)
                        zero_doc.save(output_path, garbage=0, deflate=False, clean=False, incremental=False)
                        zero_doc.close()
                        if not self._validate_pdf(output_path):
                            print(
                                f"[optimize_pdf] '{pdf_path}': source does not survive any re-save — copying original untouched."  # noqa: E501
                            )
                            import shutil

                            shutil.copy2(pdf_path, output_path)
                            return False

            # Final guard: never hand back a file bigger than the input.
            if os.path.exists(output_path) and os.path.getsize(output_path) >= original_size:
                print(f"[optimize_pdf] '{pdf_path}': no method beat the original size, keeping original bytes")
                import shutil

                shutil.copy2(pdf_path, output_path)

            return True
        except Exception as e:
            print(f"PDF optimization error {pdf_path}: {e}")
            return False

    def _pikepdf_compress(self, pdf_path, output_path, compression_level):
        """Offline, pip-only fallback (bundles QPDF statically — no external
        binary, no download, no PATH/admin concerns). QPDF's repair is
        generally more tolerant of damaged xref tables than MuPDF's, and
        object-stream compaction + stream recompression gets real reduction
        on structurally messy 'normal' PDFs that PyMuPDF's save() bounced on.
        """
        try:
            import pikepdf

            with pikepdf.open(pdf_path) as pdf:
                pdf.remove_unreferenced_resources()
                pdf.save(
                    output_path,
                    compress_streams=True,
                    object_stream_mode=pikepdf.ObjectStreamMode.generate,
                    # "high" quality = leave existing stream compression alone;
                    # normal/very_reduced re-run flate compression, which can
                    # shrink streams that were saved uncompressed upstream.
                    recompress_flate=(compression_level != "high"),
                    linearize=False,
                )
            return self._validate_pdf(output_path)
        except ImportError:
            print("[pikepdf_compress] pikepdf not installed — run: pip install pikepdf")
            return False
        except Exception as e:
            print(f"[pikepdf_compress] {pdf_path}: {e}")
            return False

    def _ghostscript_compress(self, pdf_path, output_path, compression_level):
        """Ghostscript's pdfwrite device rebuilds the PDF from rendered content
        instead of patching the existing xref table — recovers files MuPDF's
        repair gives up on, and matches what most online PDF compressors use
        under the hood. Called by absolute path only, resolved by
        _get_ghostscript_bin() (detection only — see that method). Returns
        False if Ghostscript isn't installed; caller falls back to PyMuPDF.
        """
        gs_bin = self._get_ghostscript_bin()
        if not gs_bin:
            print(
                f"[ghostscript_compress] '{pdf_path}': no Ghostscript binary found "
                f"(not on PATH, app-local folder, or common install paths)"
            )
            return False
        print(f"[ghostscript_compress] '{pdf_path}': using binary at {gs_bin}")
        try:
            import subprocess

            settings_map = {"high": "/printer", "normal": "/ebook", "very_reduced": "/screen"}
            pdf_settings = settings_map.get(compression_level, "/ebook")
            tmp_out = output_path + ".gs_tmp.pdf"
            cmd = [
                gs_bin,
                "-o",
                tmp_out,
                "-sDEVICE=pdfwrite",
                f"-dPDFSETTINGS={pdf_settings}",
                "-dNOPAUSE",
                "-dBATCH",
                "-dQUIET",
                pdf_path,
            ]
            # On Windows, subprocess would otherwise briefly flash a console
            # window for each conversion since this app has no console of its
            # own; CREATE_NO_WINDOW suppresses that. The attribute doesn't
            # exist on non-Windows platforms, hence the hasattr guard.
            _no_window = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            result = subprocess.run(cmd, capture_output=True, timeout=180, creationflags=_no_window)
            if result.returncode != 0 or not os.path.exists(tmp_out):
                stderr_tail = result.stderr.decode(errors="replace")[-500:] if result.stderr else "(no stderr)"
                print(
                    f"[ghostscript_compress] '{pdf_path}': gs exited {result.returncode}, tmp file exists={os.path.exists(tmp_out)}\n"  # noqa: E501
                    f"    stderr: {stderr_tail}"
                )
                return False
            if not self._validate_pdf(tmp_out):
                print(f"[ghostscript_compress] '{pdf_path}': gs output failed PDF validation, discarding")
                os.remove(tmp_out)
                return False
            gs_size = os.path.getsize(tmp_out)
            orig_size = os.path.getsize(pdf_path)
            print(
                f"[ghostscript_compress] '{pdf_path}': gs succeeded, output size {gs_size} vs original {orig_size} "
                f"({'smaller' if gs_size < orig_size else 'NOT smaller'})"
            )
            import shutil

            shutil.move(tmp_out, output_path)
            return True
        except subprocess.TimeoutExpired:
            print(f"[ghostscript_compress] '{pdf_path}': gs timed out after 180s")
            return False
        except Exception as e:
            print(f"[ghostscript_compress] {pdf_path}: {e}")
            return False

    def _get_ghostscript_bin(self):
        """Locate a usable Ghostscript binary via the centralized resolver
        (PATH → app-local → common dirs → config file). Detection only — no
        download, no auto-install. Returns an absolute path, or None if
        Ghostscript isn't installed anywhere findable, in which case the
        caller falls back to PyMuPDF/pikepdf.
        """
        cached = getattr(self, "_gs_bin_cache", None)
        if cached and os.path.isfile(cached):
            return cached

        from external_binaries import resolve_binary

        gs = resolve_binary("ghostscript", app_data_dir=os.path.dirname(self._gs_app_dir()))
        if gs:
            self._gs_bin_cache = gs
        return gs

    def check_ghostscript_status(self):
        """Diagnostic helper — call this on its own (e.g. from a settings/about
        screen) to know exactly what this app can and can't do, without
        running an actual PDF through it. Returns a dict rather than printing,
        so the caller can show it in the UI. Detection only, no download.
        """
        import subprocess

        status = {"found": False, "path": None, "version": None, "source": None, "error": None}

        cached = getattr(self, "_gs_bin_cache", None)
        if cached and os.path.isfile(cached):
            status["source"] = "cached"
            candidate = cached
        else:
            from external_binaries import locate_binary

            candidate, status["source"] = locate_binary("ghostscript", app_data_dir=os.path.dirname(self._gs_app_dir()))

        if not candidate:
            status["error"] = "Not found on PATH, in app-local folder, or common install paths."
            return status

        # Presence on disk isn't proof it runs — confirm with a real call.
        try:
            _no_window = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            result = subprocess.run(
                [candidate, "--version"], capture_output=True, timeout=10, text=True, creationflags=_no_window
            )
            if result.returncode == 0:
                status["found"] = True
                status["path"] = candidate
                status["version"] = result.stdout.strip()
            else:
                status["error"] = (
                    f"Found at {candidate} but exited with code {result.returncode}: {result.stderr.strip()}"
                )
        except Exception as e:
            status["error"] = f"Found at {candidate} but failed to execute: {e}"

        return status

    def _gs_app_dir(self):
        """App-local folder Ghostscript may already be installed to (if the
        user installed it there manually, or a previous version of this app
        did). Only ever checked now, never written to automatically."""
        from external_binaries import get_app_data_dir

        base = getattr(self, "app_data_dir", None) or get_app_data_dir()
        return os.path.join(base, "ghostscript")

    def _validate_pdf(self, path):
        """Reopen a saved PDF and confirm it's actually readable before trusting it.

        Checks every page, not just the first — corruption from xref surgery
        tends to cluster in high object numbers (later pages, embedded fonts,
        images), so a page-0-only check gives false positives on exactly the
        documents most at risk here.
        """
        try:
            import fitz

            check = fitz.open(path)
            if check.page_count == 0:
                check.close()
                return False
            for i in range(check.page_count):
                try:
                    check.load_page(i).get_text()
                except Exception as e:
                    print(f"PDF validation failed on page {i} of {path}: {e}")
                    check.close()
                    return False
            check.close()
            return True
        except Exception as e:
            print(f"PDF validation failed for {path}: {e}")
            return False

    def _downsample_pdf_images(self, pdf_document, target_dpi, jpeg_quality):
        """Resample embedded raster images to target_dpi and re-encode as JPEG.

        Effective DPI is based on the image's rendered size on the page, not its
        raw pixel dimensions. Images already at or below target_dpi are left
        unchanged. Vector content, masks (SMask/stencil), and CMYK images are
        skipped to avoid rendering issues.
        """

        import io as _io

        from PIL import Image as PILImage

        seen_xrefs = set()
        any_replaced = False

        for page in pdf_document:
            try:
                img_list = page.get_images(full=True)
            except Exception:
                continue

            for img in img_list:
                xref = img[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)

                # Skip images used as soft/stencil masks elsewhere.
                # img[1] is this image's SMask xref, but this xref may itself be used as a mask.
                try:
                    if pdf_document.xref_get_key(xref, "ImageMask")[1] == "true":
                        continue
                except Exception:
                    pass

                rects = page.get_image_rects(xref)
                if not rects:
                    continue
                rect = rects[0]
                disp_w_in = rect.width / 72.0
                disp_h_in = rect.height / 72.0
                if disp_w_in <= 0 or disp_h_in <= 0:
                    continue

                try:
                    base_image = pdf_document.extract_image(xref)
                except Exception:
                    continue
                if not base_image:
                    continue

                px_w = base_image.get("width")
                px_h = base_image.get("height")
                img_bytes = base_image.get("image")
                if not px_w or not px_h or not img_bytes:
                    continue
                if base_image.get("smask"):
                    # Preserve alpha/soft mask.
                    continue

                if base_image.get("colorspace") == 4:  # CMYK
                    # Skip CMYK images.
                    continue

                current_dpi = px_w / disp_w_in

                # Some PDFs embed images at 1 px = 1 pt, making huge images appear ~72 DPI.
                # DPI-based checks alone would skip them, so also enforce an absolute pixel limit.
                abs_max_px = target_dpi * 20  # Allows up to a 20" side at target DPI
                dpi_over_target = current_dpi > target_dpi * 1.1
                pixel_dims_excessive = max(px_w, px_h) > abs_max_px

                if not dpi_over_target and not pixel_dims_excessive:
                    continue

                if dpi_over_target:
                    scale = target_dpi / current_dpi
                else:
                    scale = abs_max_px / max(px_w, px_h)

                new_w = max(1, int(px_w * scale))
                new_h = max(1, int(px_h * scale))

                try:
                    with PILImage.open(_io.BytesIO(img_bytes)) as pil_img:
                        if pil_img.mode in ("RGBA", "P", "LA"):
                            pil_img = pil_img.convert("RGB")
                        resized = pil_img.resize((new_w, new_h), PILImage.LANCZOS)
                        buf = _io.BytesIO()
                        resized.save(buf, format="JPEG", quality=jpeg_quality, optimize=True)
                        new_bytes = buf.getvalue()

                    if len(new_bytes) < len(img_bytes):
                        page.replace_image(xref, stream=new_bytes)
                        any_replaced = True
                except Exception as e:
                    print(f"[pdf downsample] xref {xref} skipped: {e}")
                    continue

        return any_replaced
