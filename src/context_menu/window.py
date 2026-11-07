"""
context_menu/window.py
Quick Convert popup for Windows Shell Integration for File Converter Pro

Launched via:
    FileConverterPro.exe --context-menu --files "path1" "path2" ...  --conversion-type [type]
"""

import os
import sys
import tempfile
import threading
import time
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from context_menu.conversion_helpers import (
    _PDF_TO_WORD_MODE_DEFAULT,
    _PDF_TO_WORD_MODES,  # noqa: F401
    _ConversionCancelled,
    _convert_docx_to_pdf,
    _convert_image_to_pdf,
    _convert_pdf_to_docx_impl,
    _merge_docx,
    _merge_images_to_pdf,
    _merge_pdfs,
    _normalise_pdf_to_word_mode,
    _raise_if_cancelled,
    _solid_fitz_fallback,
    _sort_files,
    _temporary_docx_path,  # noqa: F401
)
from context_menu.formats import CONVERSION_MAP, LABELS, MERGE_DISPATCH
from converter.helpers import prepare_operation_backups
from qss_helpers import _load_qss
from utils import SRC_DIR
from utils.pdf_text import convert_pdf_text_to_docx

_COLLECT_MIN_SEC = 2.0
_COLLECT_STABLE_SEC = 0.5
_COLLECT_MAX_SEC = 8.0
_COLLECT_POLL_SEC = 0.05
_COLLECT_EPOCH_SEC = 15.0


def _load_quick_config() -> dict | None:
    try:
        from config import ConfigManager

        manager = ConfigManager()
        loader = getattr(manager, "load_config_strict", None)
        config = loader() if loader is not None else manager.load_config()
    except Exception as exc:
        print(f"[QuickConvert] Could not load configuration: {exc}")
        return None
    if not isinstance(config, dict):
        print("[QuickConvert] Configuration is not a mapping")
        return None
    return config


def _load_pdf_to_word_mode(config: dict | None = None) -> str:
    """Read and validate the persisted PDF→Word mode for Quick Convert."""
    if config is None:
        config = _load_quick_config()
    if not isinstance(config, dict):
        return _PDF_TO_WORD_MODE_DEFAULT
    return _normalise_pdf_to_word_mode(config.get("pdf_to_word_mode"))


def _collect_staged_files(conversion_type: str, single_file: str) -> list[str]:
    """
    Windows spawns one process per selected file for context menu commands.
    """
    epoch = int(time.time() / _COLLECT_EPOCH_SEC)
    key = f"fcp_{conversion_type}_{epoch}"
    staging = os.path.join(tempfile.gettempdir(), f"{key}.txt")
    lock = os.path.join(tempfile.gettempdir(), f"{key}.lock")

    with open(staging, "a", encoding="utf-8") as fh:
        fh.write(single_file + "\n")

    time.sleep(_COLLECT_MIN_SEC)

    deadline = time.time() + (_COLLECT_MAX_SEC - _COLLECT_MIN_SEC)
    last_size = -1
    stable_since = time.time()

    while time.time() < deadline:
        time.sleep(_COLLECT_POLL_SEC)
        try:
            size = os.path.getsize(staging)
        except OSError:
            size = last_size
        if size != last_size:
            last_size = size
            stable_since = time.time()
        elif time.time() - stable_since >= _COLLECT_STABLE_SEC:
            break

    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError:
        return []

    time.sleep(0.2)

    try:
        with open(staging, "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and os.path.isfile(line.strip())]
    except Exception:
        return [single_file]


AUTO_CLOSE_DELAY_MS = 1800
CANCEL_GRACE_MS = 5000

_QUICK_OUTPUT_EXTENSIONS = {
    "image_to_pdf": ".pdf",
    "docx_to_pdf": ".pdf",
    "pdf_to_docx": ".docx",
}


def _publish_staged_output(staged_path: str | None, staging_dir: str, dst_dir: str) -> None:
    if not staged_path:
        return
    staged_abs = os.path.abspath(staged_path)
    if os.path.dirname(staged_abs) != os.path.abspath(staging_dir):
        return
    if not os.path.isfile(staged_abs):
        return
    os.replace(staged_abs, os.path.join(dst_dir, os.path.basename(staged_abs)))


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


class ConversionThread(QThread):
    done = Signal(bool, str, str)
    cancelled = Signal()

    def __init__(self, files: list, conversion_type: str):
        super().__init__()
        self.files = files
        self.conversion_type = conversion_type
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        """Request cooperative cancellation of the running conversion."""
        self._cancel_event.set()
        self.requestInterruption()

    def _check_cancelled(self) -> None:
        _raise_if_cancelled(self._cancel_event)

    def run(self):
        try:
            self._check_cancelled()
            base = os.path.dirname(
                sys.executable if getattr(sys, "frozen", False) else str(SRC_DIR)
            )
            if base not in sys.path:
                sys.path.insert(0, base)

            runtime_config = _load_quick_config()
            if runtime_config is None:
                raise RuntimeError("Quick Convert configuration unavailable")
            prepare_operation_backups(self.files, config=runtime_config)
            dst_dir = os.path.dirname(self.files[0])
            pdf_to_word_mode = _PDF_TO_WORD_MODE_DEFAULT
            if self.conversion_type == "pdf_to_docx":
                pdf_to_word_mode = _load_pdf_to_word_mode(runtime_config)

            if self.conversion_type == "images_to_pdf_merged":
                merge_files = _sort_files(self.files, "alphabetical_asc")
                _merge_images_to_pdf(merge_files, dst_dir, self._cancel_event)
                self._check_cancelled()
                self.done.emit(True, "Images merged into PDF", dst_dir)
                return

            if self.conversion_type in MERGE_DISPATCH:
                kind, order = MERGE_DISPATCH[self.conversion_type]
                merge_files = self.files
                if order == "none":
                    merge_files = _sort_files(self.files, "alphabetical_asc")
                if kind == "pdf":
                    _merge_pdfs(merge_files, dst_dir, order, self._cancel_event)
                else:
                    _merge_docx(merge_files, dst_dir, order, self._cancel_event)
                self._check_cancelled()
                self.done.emit(True, "Files merged successfully", dst_dir)
                return

            errors = []
            out_dir = ""
            for f in self.files:
                self._check_cancelled()
                f_dst_dir = os.path.dirname(f)
                try:
                    with tempfile.TemporaryDirectory(
                        prefix="~fcp_quick_", dir=f_dst_dir
                    ) as staging_dir:
                        staged_output = None
                        if self.conversion_type == "image_to_pdf":
                            _convert_image_to_pdf(f, staging_dir)
                        elif self.conversion_type == "docx_to_pdf":
                            _convert_docx_to_pdf(f, staging_dir, self._cancel_event)
                        elif self.conversion_type == "pdf_to_docx":
                            _convert_pdf_to_docx(
                                f,
                                staging_dir,
                                self._cancel_event,
                                mode=pdf_to_word_mode,
                            )
                        else:
                            from converter.converters import AdvancedConverterEngine

                            engine = AdvancedConverterEngine()
                            engine.allow_local_html_resources = runtime_config.get(
                                "allow_local_resources_in_html_to_pdf", False
                            )
                            result = engine.convert(
                                self.conversion_type,
                                f,
                                staging_dir,
                                skip_backup=True,
                            )
                            if not result.success:
                                raise Exception(result.error)
                            staged_output = getattr(result, "target", None)

                        extension = _QUICK_OUTPUT_EXTENSIONS.get(self.conversion_type)
                        if extension:
                            staged_output = os.path.join(
                                staging_dir, f"{Path(f).stem}{extension}"
                            )
                        if not staged_output:
                            staged_files = [
                                entry.path
                                for entry in os.scandir(staging_dir)
                                if entry.is_file()
                            ]
                            if len(staged_files) == 1:
                                staged_output = staged_files[0]
                        self._check_cancelled()
                        _publish_staged_output(staged_output, staging_dir, f_dst_dir)
                    out_dir = f_dst_dir
                except _ConversionCancelled:
                    raise
                except Exception as e:
                    errors.append(f"{os.path.basename(f)}: {e}")

            self._check_cancelled()
            if errors:
                self.done.emit(False, "\n".join(errors), "")
            else:
                n = len(self.files)
                self.done.emit(True, f"{n} file{'s' if n > 1 else ''} converted", out_dir)

        except _ConversionCancelled:
            self.cancelled.emit()
        except Exception as e:
            if self._cancel_event.is_set():
                self.cancelled.emit()
            else:
                self.done.emit(False, str(e), "")


class QuickConvertWindow(QWidget):
    """Floating window launched from the Windows context menu."""

    def __init__(self, files: list, conversion_type: str | None = None):
        super().__init__()
        self.files = [f for f in files if os.path.isfile(f)]

        self.ext = os.path.splitext(self.files[0])[1].lstrip(".").lower() if self.files else ""
        self.forced_conversion = conversion_type
        self.conversion_types = [conversion_type] if conversion_type else CONVERSION_MAP.get(self.ext, [])

        self.setWindowTitle("File Converter Pro")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(310)
        self.setMaximumWidth(310)

        self._set_icon()
        self._build_ui()
        self._center_on_screen()

    def _set_icon(self):
        from utils import get_icon_path

        icon_path = get_icon_path("icon.ico")
        if icon_path and os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    @staticmethod
    def _theme_name() -> str:
        """Resolve the persisted theme for this standalone window."""
        try:
            from config import ConfigManager
            from theme_manager import get_custom_themes

            config = ConfigManager().load_config()
            custom = config.get("custom_theme")
            if custom and custom not in ("dark", "light"):
                if any(theme.folder_name == custom for theme in get_custom_themes()):
                    return custom
            return "dark" if config.get("dark_mode") else "light"
        except Exception:
            return "light"

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame()
        self.card.setObjectName("card")
        self.card.setStyleSheet(_load_qss("window_card.qss", self._theme_name()))

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
        title = QLabel("Quick Convert")
        title.setObjectName("title")
        inner.addWidget(title)

        n = len(self.files)
        if n == 1:
            file_text = os.path.basename(self.files[0])
        elif n <= 4:
            file_text = "\n".join(f"• {os.path.basename(f)}" for f in self.files)
        else:
            previews = "\n".join(f"• {os.path.basename(f)}" for f in self.files[:3])
            file_text = f"{previews}\n• … and {n - 3} more"

        file_label = QLabel(file_text)
        file_label.setObjectName("fileList")
        file_label.setWordWrap(True)
        inner.addWidget(file_label)

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.HLine)
        inner.addWidget(sep)

        self.combo = None

        if not self.conversion_types:
            msg = QLabel(f"No conversion available for .{self.ext or '?'}")
            msg.setObjectName("fileList")
            msg.setWordWrap(True)
            inner.addWidget(msg)
        elif self.forced_conversion:
            label = QLabel(LABELS.get(self.forced_conversion, self.forced_conversion))
            label.setObjectName("conversionLabel")
            inner.addWidget(label)
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
        self.cancel_btn.clicked.connect(self._cancel_conversion)

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
            geo.center().x() - self.width() // 2,
            geo.center().y() - self.height() // 2,
        )

    def _start_conversion(self):
        conversion_type = self.forced_conversion if self.forced_conversion else self.combo.currentData()
        self.convert_btn.setEnabled(False)
        self.cancel_btn.setText("Cancel")
        self.cancel_btn.setEnabled(True)
        self.progress.show()
        self.status_label.hide()

        self._worker_thread = ConversionThread(self.files, conversion_type)
        self._worker_thread.done.connect(self._on_done)
        self._worker_thread.cancelled.connect(self._on_cancelled)
        self._worker_thread.start()

    def _cancel_conversion(self):
        thread = getattr(self, "_worker_thread", None)
        if thread is None or not thread.isRunning():
            self.close()
            return

        thread.cancel()
        self.cancel_btn.setText("Cancelling...")
        self.cancel_btn.setEnabled(False)
        self.status_label.setObjectName("statusOk")
        self.status_label.setText("Cancelling...")
        self.status_label.show()
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self.adjustSize()
        self.setFixedHeight(self.sizeHint().height())
        QTimer.singleShot(CANCEL_GRACE_MS, self._force_cancel_if_running)

    def _force_cancel_if_running(self):
        thread = getattr(self, "_worker_thread", None)
        if thread is not None and thread.isRunning():
            os._exit(0)

    def _on_cancelled(self):
        self.progress.hide()
        self.cancel_btn.setEnabled(False)
        self.status_label.setObjectName("statusOk")
        self.status_label.setText("Conversion cancelled")
        self.status_label.show()
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self.adjustSize()
        self.setFixedHeight(self.sizeHint().height())
        QTimer.singleShot(300, QApplication.quit)

    def _on_done(self, success: bool, message: str, out_dir: str):
        self.progress.hide()
        self.status_label.show()
        self.adjustSize()
        self.setFixedHeight(self.sizeHint().height())

        if success:
            self.cancel_btn.setEnabled(False)
            self.status_label.setObjectName("statusOk")
            self.status_label.setText(f"✓ {message}")
            QTimer.singleShot(AUTO_CLOSE_DELAY_MS, QApplication.quit)
        else:
            self.status_label.setObjectName("statusErr")
            self.status_label.setText(f"✗ {message}")
            self.convert_btn.setText("Retry")
            self.convert_btn.setEnabled(True)
            self.cancel_btn.setText("Cancel")
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
        thread = getattr(self, "_worker_thread", None)
        if thread is not None and thread.isRunning():
            thread.cancel()
            if not thread.wait(3000):
                os._exit(0)
        e.accept()
        QApplication.quit()


def run_context_menu(files: list, conversion_type: str | None = None) -> None:
    """Called from main.py when --context-menu flag is detected."""

    if conversion_type and len(files) == 1:
        collected = _collect_staged_files(conversion_type, files[0])
        if not collected:
            sys.exit(0)
        files = collected

    app = QApplication.instance() or QApplication(sys.argv)
    win = QuickConvertWindow(files, conversion_type=conversion_type)
    win.show()

    if conversion_type:
        QTimer.singleShot(100, win._start_conversion)

    sys.exit(app.exec())
