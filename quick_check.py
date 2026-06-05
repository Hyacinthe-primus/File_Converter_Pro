"""
Quick Check
Verifies all critical files are present in the onedir build.
Uses tkinter (stdlib) to keep the exe lightweight.

"""

import sys
import os
import time
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

CHECKS_CORE = [
    ("Main executable",               "File Converter Pro.exe",                        "file"),
    ("icon.ico",                      "_internal/icon.ico",                            "file"),
    ("icon.png",                      "_internal/icon.png",                            "file"),
    ("base_library.zip",              "_internal/base_library.zip",                    "file"),
    ("ucrtbase.dll",                  "_internal/ucrtbase.dll",                        "file"),
    ("libffi-8.dll",                  "_internal/libffi-8.dll",                        "file"),
    ("sqlite3.dll",                   "_internal/sqlite3.dll",                         "file"),
    ("libcrypto-3-x64.dll",           "_internal/libcrypto-3-x64.dll",                 "file"),
    ("libssl-3-x64.dll",              "_internal/libssl-3-x64.dll",                    "file"),
    ("python3.dll",                   "_internal/python3.dll",                         "file"),
    ("vcruntime140.dll",              "_internal/vcruntime140.dll",                    "file"),
    ("vcruntime140_1.dll",            "_internal/vcruntime140_1.dll",                  "file"),
]

CHECKS_MODULES = [
    ("_bz2.pyd",                          "_internal/_bz2.pyd",                          "file"),
    ("_ctypes.pyd",                       "_internal/_ctypes.pyd",                       "file"),
    ("_decimal.pyd",                      "_internal/_decimal.pyd",                      "file"),
    ("_elementtree.pyd",                  "_internal/_elementtree.pyd",                  "file"),
    ("_hashlib.pyd",                      "_internal/_hashlib.pyd",                      "file"),
    ("_lzma.pyd",                         "_internal/_lzma.pyd",                         "file"),
    ("_multiprocessing.pyd",              "_internal/_multiprocessing.pyd",              "file"),
    ("_overlapped.pyd",                   "_internal/_overlapped.pyd",                   "file"),
    ("_queue.pyd",                        "_internal/_queue.pyd",                        "file"),
    ("_socket.pyd",                       "_internal/_socket.pyd",                       "file"),
    ("_sqlite3.pyd",                      "_internal/_sqlite3.pyd",                      "file"),
    ("_ssl.pyd",                          "_internal/_ssl.pyd",                          "file"),
    ("_uuid.pyd",                         "_internal/_uuid.pyd",                         "file"),
    ("_wmi.pyd",                          "_internal/_wmi.pyd",                          "file"),
    ("_asyncio.pyd",                      "_internal/_asyncio.pyd",                      "file"),
    ("_cffi_backend.cp313-win_amd64.pyd", "_internal/_cffi_backend.cp313-win_amd64.pyd", "file"),
    ("_brotli.cp313-win_amd64.pyd",       "_internal/_brotli.cp313-win_amd64.pyd",       "file"),
]

CHECKS_RESOURCES = [
    ("Assets/",    "_internal/Assets",  "dir"),
    ("SFX/",       "_internal/SFX",     "dir"),
    ("icons/",     "_internal/icons",   "dir"),
    ("fonts/",     "_internal/fonts",   "dir"),
    ("legal/",     "_internal/legal",   "dir"),
]

CHECKS_QT = [
    ("Qt6Core.dll",                "_internal/PySide6/Qt6Core.dll",                    "file"),
    ("Qt6Gui.dll",                 "_internal/PySide6/Qt6Gui.dll",                     "file"),
    ("Qt6Widgets.dll",             "_internal/PySide6/Qt6Widgets.dll",                 "file"),
    ("Qt6Network.dll",             "_internal/PySide6/Qt6Network.dll",                 "file"),
    ("Shiboken.pyd",               "_internal/shiboken6/Shiboken.pyd",                 "file"),
    ("Qt6Multimedia.dll",          "_internal/PySide6/Qt6Multimedia.dll",              "file"),
    ("Qt6MultimediaWidgets.dll",   "_internal/PySide6/Qt6MultimediaWidgets.dll",       "file"),
    ("Qt6Svg.dll",                 "_internal/PySide6/Qt6Svg.dll",                     "file"),
    ("Qt6OpenGL.dll",              "_internal/PySide6/Qt6OpenGL.dll",                  "file"),
    ("Qt6Quick.dll",               "_internal/PySide6/Qt6Quick.dll",                   "file"),
    ("Qt6Qml.dll",                 "_internal/PySide6/Qt6Qml.dll",                     "file"),
    ("PySide6/QtCore.pyd",         "_internal/PySide6/QtCore.pyd",                     "file"),
    ("PySide6/QtGui.pyd",          "_internal/PySide6/QtGui.pyd",                      "file"),
    ("PySide6/QtWidgets.pyd",      "_internal/PySide6/QtWidgets.pyd",                  "file"),
    ("PySide6/QtNetwork.pyd",      "_internal/PySide6/QtNetwork.pyd",                  "file"),
    ("PySide6/QtMultimedia.pyd",   "_internal/PySide6/QtMultimedia.pyd",               "file"),
    ("platforms/qwindows.dll",     "_internal/PySide6/plugins/platforms/qwindows.dll", "file"),
    ("imageformats/",              "_internal/PySide6/plugins/imageformats",           "dir"),
]

CHECKS_LIBS = [
    ("mupdfcpp64.dll",  "_internal/pymupdf/mupdfcpp64.dll",  "file"),
    ("PIL/",            "_internal/PIL",                      "dir"),
    ("cryptography/",   "_internal/cryptography",             "dir"),
    ("matplotlib/",     "_internal/matplotlib",               "dir"),
]

ALL_GROUPS = {
    "Core":         CHECKS_CORE,
    "Modules":      CHECKS_MODULES,
    "Resources":    CHECKS_RESOURCES,
    "Qt / PySide6": CHECKS_QT,
    "Libraries":    CHECKS_LIBS,
}
ALL_CHECKS = CHECKS_CORE + CHECKS_MODULES + CHECKS_RESOURCES + CHECKS_QT + CHECKS_LIBS


#  THEMES
DARK = {
    "bg":         "#0f1117",
    "surface":    "#1a1d27",
    "border":     "#2e3250",
    "text":       "#e8eaf6",
    "text_dim":   "#6b7280",
    "ok":         "#22c55e",
    "ok_bg":      "#0d2218",
    "fail":       "#ef4444",
    "fail_bg":    "#2a0f0f",
    "accent":     "#6366f1",
    "btn_fg":     "#ffffff",
    "pending_bg": "#1a1d27",
}
LIGHT = {
    "bg":         "#f4f5fb",
    "surface":    "#ffffff",
    "border":     "#d1d5eb",
    "text":       "#1a1d2e",
    "text_dim":   "#6b7280",
    "ok":         "#16a34a",
    "ok_bg":      "#f0fdf4",
    "fail":       "#dc2626",
    "fail_bg":    "#fff5f5",
    "accent":     "#4f46e5",
    "btn_fg":     "#ffffff",
    "pending_bg": "#f9fafb",
}


#  MAIN APP
class QuickCheckApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.dark = True
        self.theme = DARK
        self._running = False

        self.rows: dict[str, dict] = {}

        root.title("File Converter Pro — Quick Check")
        root.geometry("860x700")
        root.minsize(760, 500)
        root.configure(bg=self.theme["bg"])

        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "FileConverterPro.QuickCheck"
            )
        except Exception:
            pass
        try:
            ico = BASE_DIR / "_internal" / "icon.ico"
            if not ico.exists():
                ico = BASE_DIR / "icon.ico"
            if ico.exists():
                root.iconbitmap(str(ico))
                root.wm_iconbitmap(str(ico))
        except Exception:
            pass

        self._build_ui()
        self._apply_theme()
        root.after(300, self._start_check)

    def _build_ui(self):
        t = self.theme

        self._hdr = tk.Frame(self.root, bg=t["bg"])
        self._hdr.pack(fill="x", padx=20, pady=(16, 0))

        self._title_col = tk.Frame(self._hdr, bg=t["bg"])
        self._title_col.pack(side="left")
        self.title_lbl = tk.Label(self._title_col, text="Quick Check",
                                  font=("Segoe UI", 18, "bold"), bg=t["bg"], fg=t["text"])
        self.title_lbl.pack(anchor="w")
        self.sub_lbl = tk.Label(self._title_col, text="Build integrity verification",
                                font=("Segoe UI", 9), bg=t["bg"], fg=t["text_dim"])
        self.sub_lbl.pack(anchor="w")

        self._btn_frame = tk.Frame(self._hdr, bg=t["bg"])
        self._btn_frame.pack(side="right")
        self.rerun_btn = tk.Button(self._btn_frame, text="↺  Re-run",
                                   font=("Segoe UI", 9, "bold"),
                                   bg=t["accent"], fg=t["btn_fg"],
                                   relief="flat", cursor="hand2", padx=14, pady=6,
                                   command=self._start_check)
        self.rerun_btn.pack(side="left", padx=(0, 6))
        self.toggle_btn = tk.Button(self._btn_frame, text="☀",
                                    font=("Segoe UI", 13),
                                    bg=t["surface"], fg=t["text"],
                                    relief="flat", cursor="hand2", width=3,
                                    command=self._toggle_theme)
        self.toggle_btn.pack(side="left")

        self.status_frame = tk.Frame(self.root, bg=t["surface"],
                                     highlightbackground=t["border"], highlightthickness=1)
        self.status_frame.pack(fill="x", padx=20, pady=10)
        self.status_icon_lbl = tk.Label(self.status_frame, text="⏳",
                                        font=("Segoe UI", 15), bg=t["surface"], fg=t["text"])
        self.status_icon_lbl.pack(side="left", padx=(14, 6), pady=8)
        self.status_text_lbl = tk.Label(self.status_frame, text="Running checks...",
                                        font=("Segoe UI", 10, "bold"), bg=t["surface"], fg=t["text"])
        self.status_text_lbl.pack(side="left", pady=8)
        self.status_count_lbl = tk.Label(self.status_frame, text="",
                                         font=("Segoe UI", 9), bg=t["surface"], fg=t["text_dim"])
        self.status_count_lbl.pack(side="right", padx=14, pady=8)

        style = ttk.Style()
        self._style = style
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        self._tab_frames: dict[str, tk.Frame] = {}
        self._canvases: dict[str, tk.Canvas] = {}

        for group_name, checks in ALL_GROUPS.items():
            outer = tk.Frame(self.notebook, bg=t["surface"])
            self.notebook.add(outer, text=f"{group_name}  ({len(checks)})")
            self._tab_frames[group_name] = outer

            canvas = tk.Canvas(outer, bg=t["surface"], highlightthickness=0)
            scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)

            inner = tk.Frame(canvas, bg=t["surface"])
            canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

            def _on_configure(event, c=canvas, cw=canvas_window):
                c.itemconfig(cw, width=c.winfo_width())
                c.configure(scrollregion=c.bbox("all"))

            inner.bind("<Configure>", _on_configure)
            canvas.bind("<Configure>", _on_configure)

            self._canvases[group_name] = canvas

            for label, path, _ in checks:
                row_frame = tk.Frame(inner, bg=t["pending_bg"],
                                     highlightbackground=t["border"], highlightthickness=1)
                row_frame.pack(fill="x", padx=4, pady=2, ipady=5)

                icon_var = tk.StringVar(value="·")
                icon_lbl = tk.Label(row_frame, textvariable=icon_var,
                                    font=("Segoe UI", 12, "bold"), width=2,
                                    bg=t["pending_bg"], fg=t["text_dim"])
                icon_lbl.pack(side="left", padx=(10, 4))

                name_lbl = tk.Label(row_frame, text=label,
                                    font=("Segoe UI", 9), anchor="w",
                                    bg=t["pending_bg"], fg=t["text_dim"])
                name_lbl.pack(side="left", padx=(0, 6))

                path_lbl = tk.Label(row_frame, text=path,
                                    font=("Segoe UI", 7), anchor="w",
                                    bg=t["pending_bg"], fg=t["text_dim"])
                path_lbl.pack(side="left", fill="x", expand=True)

                detail_var = tk.StringVar(value="")
                detail_lbl = tk.Label(row_frame, textvariable=detail_var,
                                      font=("Segoe UI", 8, "bold"), width=12, anchor="e",
                                      bg=t["pending_bg"], fg=t["text_dim"])
                detail_lbl.pack(side="right", padx=(0, 10))

                self.rows[path] = {
                    "frame":      row_frame,
                    "icon_var":   icon_var,
                    "icon_lbl":   icon_lbl,
                    "name_lbl":   name_lbl,
                    "path_lbl":   path_lbl,
                    "detail_var": detail_var,
                    "detail_lbl": detail_lbl,
                    "state":      "pending",
                    "group":      group_name,
                    "canvas":     canvas,
                    "inner":      inner,
                }

        self.close_btn = tk.Button(self.root, text="Close",
                                   font=("Segoe UI", 10, "bold"),
                                   bg=t["surface"], fg=t["text"],
                                   relief="flat", cursor="hand2",
                                   command=self.root.destroy)

        def _on_mousewheel(event):
            tab_idx = self.notebook.index("current")
            group_name = list(ALL_GROUPS.keys())[tab_idx]
            c = self._canvases.get(group_name)
            if c:
                c.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.root.bind_all("<MouseWheel>", _on_mousewheel)

    def _apply_theme(self):
        t = self.theme
        self.root.configure(bg=t["bg"])

        self._hdr.configure(bg=t["bg"])
        self._title_col.configure(bg=t["bg"])
        self._btn_frame.configure(bg=t["bg"])
        self.title_lbl.configure(bg=t["bg"], fg=t["text"])
        self.sub_lbl.configure(bg=t["bg"], fg=t["text_dim"])
        self.rerun_btn.configure(bg=t["accent"], fg=t["btn_fg"])
        self.toggle_btn.configure(bg=t["surface"], fg=t["text"],
                                  text="☀" if self.dark else "☾")

        for w in (self.status_frame, self.status_icon_lbl,
                  self.status_text_lbl, self.status_count_lbl):
            w.configure(bg=t["surface"])
        self.status_frame.configure(highlightbackground=t["border"])
        self.status_text_lbl.configure(fg=t["text"])
        self.status_count_lbl.configure(fg=t["text_dim"])

        s = self._style
        s.theme_use("default")
        s.configure("TNotebook", background=t["bg"], borderwidth=0)
        s.configure("TNotebook.Tab",
                    background=t["surface"], foreground=t["text_dim"],
                    padding=[10, 5], font=("Segoe UI", 9))
        s.map("TNotebook.Tab",
              background=[("selected", t["surface"])],
              foreground=[("selected", t["text"])],
              expand=[("selected", [1, 1, 1, 0])])

        for group_name, outer in self._tab_frames.items():
            outer.configure(bg=t["surface"])
        for group_name, canvas in self._canvases.items():
            canvas.configure(bg=t["surface"])
            for r in self.rows.values():
                if r["group"] == group_name:
                    r["inner"].configure(bg=t["surface"])
                    break

        for path, r in self.rows.items():
            state = r["state"]
            if state == "ok":
                self._color_row(path, True, r["detail_var"].get())
            elif state == "fail":
                self._color_row(path, False, r["detail_var"].get())
            else:
                self._reset_row(path)

        self.close_btn.configure(bg=t["surface"], fg=t["text"])

    def _toggle_theme(self):
        self.dark = not self.dark
        self.theme = DARK if self.dark else LIGHT
        self._apply_theme()

    def _reset_row(self, path: str):
        t = self.theme
        r = self.rows[path]
        r["state"] = "pending"
        r["icon_var"].set("·")
        r["detail_var"].set("")
        r["frame"].configure(bg=t["pending_bg"], highlightbackground=t["border"])
        for w in (r["icon_lbl"], r["name_lbl"], r["path_lbl"], r["detail_lbl"]):
            w.configure(bg=t["pending_bg"], fg=t["text_dim"])

    def _color_row(self, path: str, ok: bool, detail: str):
        t = self.theme
        r = self.rows[path]
        color = t["ok"] if ok else t["fail"]
        bg    = t["ok_bg"] if ok else t["fail_bg"]
        r["state"] = "ok" if ok else "fail"
        r["icon_var"].set("✓" if ok else "✗")
        r["detail_var"].set(detail)
        r["frame"].configure(bg=bg, highlightbackground=color)
        for w in (r["icon_lbl"], r["name_lbl"], r["path_lbl"], r["detail_lbl"]):
            w.configure(bg=bg)
        r["icon_lbl"].configure(fg=color)
        r["name_lbl"].configure(fg=t["text"],
                                font=("Segoe UI", 9, "bold") if not ok else ("Segoe UI", 9))
        r["path_lbl"].configure(fg=t["text_dim"] if ok else color)
        r["detail_lbl"].configure(fg=color)

    def _start_check(self):
        if self._running:
            return
        self._running = True
        self.rerun_btn.configure(state="disabled")
        self.close_btn.pack_forget()

        t = self.theme
        self.status_frame.configure(bg=t["surface"], highlightbackground=t["border"])
        self.status_icon_lbl.configure(text="⏳", bg=t["surface"], fg=t["text"])
        self.status_text_lbl.configure(text="Running checks...", bg=t["surface"], fg=t["text"])
        self.status_count_lbl.configure(text=f"0 / {len(ALL_CHECKS)}", bg=t["surface"])

        for group_name, checks in ALL_GROUPS.items():
            tab_idx = list(ALL_GROUPS.keys()).index(group_name)
            self.notebook.tab(tab_idx, text=f"{group_name}  ({len(checks)})")

        for path in self.rows:
            self._reset_row(path)

        threading.Thread(target=self._run_checks, daemon=True).start()

    def _run_checks(self):
        found = 0
        total = len(ALL_CHECKS)
        for label, rel_path, kind in ALL_CHECKS:
            full = BASE_DIR / rel_path.replace("/", os.sep)
            if kind == "dir":
                ok = full.is_dir()
                detail = (f"{sum(1 for _ in full.rglob('*') if _.is_file())} files"
                          if ok else "missing")
            else:
                ok = full.is_file()
                detail = (f"{full.stat().st_size / 1024:.1f} KB" if ok else "missing")
            if ok:
                found += 1
            self.root.after(0, self._on_result, rel_path, ok, detail, found, total)
            time.sleep(0.02)
        self.root.after(0, self._on_finished, found, total)

    def _on_result(self, path: str, ok: bool, detail: str, found: int, total: int):
        self._color_row(path, ok, detail)
        done = sum(1 for r in self.rows.values() if r["state"] in ("ok", "fail"))
        self.status_count_lbl.configure(text=f"{done} / {total}")

        for i, (group_name, checks) in enumerate(ALL_GROUPS.items()):
            group_rows = [r for p, r in self.rows.items() if r["group"] == group_name]
            has_fail = any(r["state"] == "fail" for r in group_rows)
            done_tab = sum(1 for r in group_rows if r["state"] in ("ok", "fail"))
            badge = " ✗" if has_fail else ""
            self.notebook.tab(i, text=f"{group_name}  ({done_tab}/{len(checks)}){badge}")

    def _on_finished(self, found: int, total: int):
        self._running = False
        self.rerun_btn.configure(state="normal")
        missing = total - found
        t = self.theme

        for i, (group_name, checks) in enumerate(ALL_GROUPS.items()):
            group_rows = [r for r in self.rows.values() if r["group"] == group_name]
            fails = sum(1 for r in group_rows if r["state"] == "fail")
            suffix = f" ✗ {fails}" if fails else " ✓"
            self.notebook.tab(i, text=f"{group_name}  ({len(checks)}){suffix}")

        if missing == 0:
            color = t["ok"]
            bg    = t["ok_bg"]
            self.status_icon_lbl.configure(text="✓", bg=bg, fg=color)
            self.status_text_lbl.configure(
                text=f"All {total} checks passed — build is healthy!",
                bg=bg, fg=color)
            self.status_count_lbl.configure(text=f"{found} / {total}", bg=bg)
            self.status_frame.configure(bg=bg, highlightbackground=color)
            self.root.after(5000, self.root.destroy)
        else:
            color = t["fail"]
            bg    = t["fail_bg"]
            self.status_icon_lbl.configure(text="✗", bg=bg, fg=color)
            self.status_text_lbl.configure(
                text=f"{missing} missing file(s) — rebuild required",
                bg=bg, fg=color)
            self.status_count_lbl.configure(text=f"{found} / {total}", bg=bg)
            self.status_frame.configure(bg=bg, highlightbackground=color)
            self.close_btn.pack(fill="x", padx=20, pady=(0, 12), ipady=6)


if __name__ == "__main__":
    root = tk.Tk()
    app = QuickCheckApp(root)
    root.mainloop()