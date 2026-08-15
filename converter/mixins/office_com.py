"""Microsoft Office COM automation conversion (PowerPoint/Excel/Word -> PDF)."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0


class OfficeComConverters:
    """Microsoft Office COM automation conversions."""

    @staticmethod
    def _office_to_pdf_com(src: str, dst: str, app_name: str) -> bool:
        """
        Convert src → dst PDF via Microsoft Office COM automation.
        app_name: "PowerPoint.Application" | "Excel.Application" | "Word.Application"
        Returns True on success, False if Office/comtypes not available.
        Works only on Windows with Office installed.
        """
        try:
            import comtypes
            import comtypes.client

            src_abs = str(Path(src).resolve())
            dst_abs = str(Path(dst).resolve())

            # Excel constants
            XL_PORTRAIT = 1
            XL_LANDSCAPE = 2
            XL_PDF = 0

            # Word constants
            WD_PDF = 17

            if "Excel" in app_name:
                app = comtypes.client.CreateObject(app_name)
                try:
                    app.Visible = False
                except Exception:
                    pass
                app.DisplayAlerts = False
                try:
                    wb = app.Workbooks.Open(src_abs)
                    try:
                        for sheet in wb.Worksheets:
                            try:
                                used = sheet.UsedRange
                                ps = sheet.PageSetup

                                # Measure real column width in points via .Width property
                                # A4 portrait printable ~510 pt, landscape ~750 pt
                                total_width_pts = sum(
                                    sheet.Columns(used.Column + i).Width for i in range(used.Columns.Count)
                                )
                                ps.Orientation = XL_LANDSCAPE if total_width_pts > 510 else XL_PORTRAIT
                                # Zoom=100, no FitTo — Excel paginates naturally
                                ps.Zoom = 100
                                ps.FitToPagesWide = False
                                ps.FitToPagesTall = False
                                ps.PrintArea = used.Address
                            except Exception:
                                pass
                        wb.ExportAsFixedFormat(XL_PDF, dst_abs)
                    finally:
                        wb.Close(False)
                finally:
                    app.Quit()

            elif "PowerPoint" in app_name:
                import shutil

                tmp_dst = str(Path(tempfile.gettempdir()) / "pptx_com_out.pdf")
                _ps_env = os.environ.copy()
                _ps_env["FCP_SRC"] = src_abs
                _ps_env["FCP_DST"] = tmp_dst

                ps_a = """
                $app = New-Object -ComObject PowerPoint.Application
                $app.Visible = -1
                try {
                    $prs = $app.Presentations.Open($env:FCP_SRC, 0, 0, -1)
                    $prs.SaveAs($env:FCP_DST, 32)
                    $prs.Close()
                } finally { $app.Quit() }
                """
                subprocess.run(
                    ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps_a],
                    capture_output=True,
                    timeout=120,
                    creationflags=_NO_WINDOW,
                    env=_ps_env,
                )
                if Path(tmp_dst).exists():
                    shutil.move(tmp_dst, dst_abs)
                    return Path(dst_abs).exists()

                ps_b = """
                $app = New-Object -ComObject PowerPoint.Application
                $app.Visible = -1
                try {
                    $prs = $app.Presentations.Open($env:FCP_SRC, 0, 0, -1)
                    $prs.PrintOut(1, $prs.Slides.Count, $env:FCP_DST, 0, 2)
                    $prs.Close()
                } finally { $app.Quit() }
                """
                r2 = subprocess.run(
                    ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps_b],
                    capture_output=True,
                    timeout=120,
                    creationflags=_NO_WINDOW,
                    env=_ps_env,
                )
                if Path(tmp_dst).exists():
                    shutil.move(tmp_dst, dst_abs)
                    return Path(dst_abs).exists()

                print(f"[COM-PS] stderr: {r2.stderr.decode('utf-8', 'replace')[:400]}")

            elif "Word" in app_name:
                app = comtypes.client.CreateObject(app_name)
                try:
                    app.Visible = False
                except Exception:
                    pass
                try:
                    doc = app.Documents.Open(src_abs)
                    try:
                        doc.SaveAs2(dst_abs, WD_PDF)
                    finally:
                        doc.Close(False)
                finally:
                    app.Quit()

            return Path(dst).exists()

        except Exception as _com_exc:
            print(f"[COM] {app_name} failed: {_com_exc}")
            return False

    def _xlsx_to_pdf_com(self, src: str, dst: str) -> bool:
        """Excel → PDF via Microsoft Office COM automation (Windows + Office)."""
        return self._office_to_pdf_com(src, dst, "Excel.Application")

    def _pptx_to_pdf_com(self, src: str, dst: str) -> bool:
        """PowerPoint → PDF via Microsoft Office COM automation (Windows + Office)."""
        return self._office_to_pdf_com(src, dst, "PowerPoint.Application")
