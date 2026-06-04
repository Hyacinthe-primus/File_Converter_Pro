"""
Donate Dialog
A beautiful, animated donation page with Ko-fi support.
Supports dark and light themes automatically.

"""

import sys
import math
import random
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QApplication, QFrame, QLineEdit, QMessageBox
)
from PySide6.QtCore import (Qt, QTimer, QRectF)
from PySide6.QtGui import (QColor, QPainter, QPainterPath, QRadialGradient, QBrush, QCursor)
import os
import webbrowser
import json
from pathlib import Path
import logging

KOFI_LINK = "https://ko-fi.com/hyacinthe_primus/goal?g=0"

def _donor_flag_path(config_dir: str | None = None) -> Path:
    """
    Returns the path to donor_pending.json.
    """
    if config_dir:
        return Path(config_dir) / "donor_pending.json"
    try:
        import sys
        sys._MEIPASS
        return Path(os.environ.get("APPDATA", Path.home())) / "FileConverterPro" / "donor_pending.json"
    except AttributeError:
        return Path(__file__).parent / "donor_pending.json"


def mark_donor_pending(amount: str, config_dir: str | None = None):
    """Reads the existing amount, adds the new one, and saves the total."""
    try:
        path = _donor_flag_path(config_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        current_total = 0.0
        
        if path.exists():
            try:
                old_data = json.loads(path.read_text(encoding="utf-8"))
                current_total = float(old_data.get("amount", 0))
            except (ValueError, json.JSONDecodeError):
                current_total = 0.0

        try:
            new_amount = float(amount.replace(",", "."))
            total = current_total + new_amount
        except ValueError:
            total = current_total

        str_total = f"{total:.2f}".rstrip("0").rstrip(".")

        path.write_text(
            json.dumps({"amount": str_total, "ts": __import__("time").time()}),
            encoding="utf-8"
        )
    except Exception as e:
        print(f"Error while updating donor flag: {e}") 

def pop_donor_flag(config_dir: str | None = None) -> dict | None:
    """Read and delete the donor flag. Returns data dict or None."""
    path = _donor_flag_path(config_dir)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        path.unlink(missing_ok=True)
        return data
    except Exception:
        return None


PILL_COLORS_DARK = [
    ("rgba(255,80,120,0.40)",  "#ff8aaa", "#ff4a7d", "#c0226a"),
    ("rgba(255,140,60,0.40)",  "#ffaa70", "#ff8c28", "#c05010"),
    ("rgba(160,80,255,0.40)",  "#c080ff", "#9040f0", "#5010c0"),
    ("rgba(60,200,120,0.40)",  "#60e090", "#28c060", "#108040"),
    ("rgba(60,160,255,0.40)",  "#70c0ff", "#2880e0", "#0840a0"),
]

PILL_COLORS_LIGHT = [
    ("rgba(220,50,90,0.35)",   "#c02050", "#e0325a", "#a01545"),
    ("rgba(210,110,30,0.35)",  "#b06010", "#d07820", "#904010"),
    ("rgba(130,50,220,0.35)",  "#8030c0", "#7020d0", "#400890"),
    ("rgba(20,160,80,0.35)",   "#109050", "#18b060", "#087040"),
    ("rgba(30,120,210,0.35)",  "#1060c0", "#1870d0", "#0840a0"),
]


class HeartParticle:
    COLORS_DARK = [
        QColor(255, 80, 120), QColor(255, 140, 60),
        QColor(160, 80, 255), QColor(60, 200, 120),
        QColor(255, 200, 60), QColor(255, 60, 200),
    ]
    COLORS_LIGHT = [
        QColor(220, 50, 90),  QColor(210, 110, 30),
        QColor(130, 50, 220), QColor(20, 160, 80),
        QColor(200, 160, 20), QColor(200, 40, 180),
    ]

    def __init__(self, x, y, dark_mode=True):
        self.x = x
        self.y = y
        self.size = random.uniform(10, 26)
        self.speed = random.uniform(0.5, 1.3)
        self.alpha = random.uniform(0.45, 0.9)
        self.drift = random.uniform(-0.5, 0.5)
        self.wobble = random.uniform(0, math.pi * 2)
        self.wobble_speed = random.uniform(0.03, 0.08)
        self.alive = True
        palette = self.COLORS_DARK if dark_mode else self.COLORS_LIGHT
        self.color = QColor(random.choice(palette))

    def update(self):
        self.wobble += self.wobble_speed
        self.x += self.drift + math.sin(self.wobble) * 0.5
        self.y -= self.speed
        self.alpha -= 0.006
        if self.alpha <= 0:
            self.alive = False

    def draw(self, painter: QPainter):
        if not self.alive:
            return
        c = QColor(self.color)
        c.setAlphaF(max(0.0, self.alpha))
        painter.save()
        painter.translate(self.x, self.y)
        painter.setBrush(QBrush(c))
        painter.setPen(Qt.NoPen)
        s = self.size
        path = QPainterPath()
        path.moveTo(0, s * 0.35)
        path.cubicTo(-s * 0.05, s * 0.1, -s * 0.5, -s * 0.15, -s * 0.5, -s * 0.1)
        path.cubicTo(-s * 0.5, -s * 0.45, 0, -s * 0.45, 0, -s * 0.1)
        path.cubicTo(0, -s * 0.45, s * 0.5, -s * 0.45, s * 0.5, -s * 0.1)
        path.cubicTo(s * 0.5, -s * 0.15, s * 0.05, s * 0.1, 0, s * 0.35)
        path.closeSubpath()
        painter.drawPath(path)
        painter.restore()


class HeartCanvas(QWidget):
    def __init__(self, dark_mode=True, parent=None):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self.particles = []
        self._spawn_timer = QTimer(self)
        self._spawn_timer.timeout.connect(self._spawn)
        self._spawn_timer.start(160)
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._tick)
        self._update_timer.start(16)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedHeight(90)

    def _spawn(self):
        if self.width() <= 0:
            return
        x = random.uniform(self.width() * 0.15, self.width() * 0.85)
        y = self.height() - 5
        self.particles.append(HeartParticle(x, y, self.dark_mode))

    def _tick(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        for p in self.particles:
            p.draw(painter)
        painter.end()

    def set_dark_mode(self, dark):
        self.dark_mode = dark


class BigHeartWidget(QWidget):
    def __init__(self, dark_mode=True, parent=None):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)
        self.setFixedSize(120, 110)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def _tick(self):
        self._phase += 0.05
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        scale = 1.0 + 0.07 * math.sin(self._phase)
        cx, cy = self.width() / 2, self.height() / 2
        s = 46 * scale

        for i in range(5, 0, -1):
            alpha = int(18 * i * (0.7 + 0.3 * math.sin(self._phase)))
            painter.setBrush(QBrush(QColor(255, 80, 130, alpha)))
            painter.setPen(Qt.NoPen)
            painter.drawPath(self._heart_path(cx, cy, s + i * 5))

        grad = QRadialGradient(cx - s * 0.1, cy - s * 0.2, s * 1.2)
        if self.dark_mode:
            grad.setColorAt(0.0, QColor(255, 120, 160))
            grad.setColorAt(0.5, QColor(230, 60, 100))
            grad.setColorAt(1.0, QColor(180, 30, 70))
        else:
            grad.setColorAt(0.0, QColor(255, 140, 170))
            grad.setColorAt(0.5, QColor(220, 60, 100))
            grad.setColorAt(1.0, QColor(170, 20, 60))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawPath(self._heart_path(cx, cy, s))

        painter.setBrush(QBrush(QColor(255, 255, 255, 70)))
        hl = QPainterPath()
        hl.addEllipse(QRectF(cx - s * 0.35, cy - s * 0.55, s * 0.38, s * 0.28))
        painter.drawPath(hl)
        painter.end()

    @staticmethod
    def _heart_path(cx, cy, s):
        path = QPainterPath()
        path.moveTo(cx, cy + s * 0.38)
        path.cubicTo(cx - s * 0.05, cy + s * 0.12,
                     cx - s * 0.55, cy - s * 0.18,
                     cx - s * 0.55, cy - s * 0.12)
        path.cubicTo(cx - s * 0.55, cy - s * 0.52,
                     cx, cy - s * 0.52,
                     cx, cy - s * 0.12)
        path.cubicTo(cx, cy - s * 0.52,
                     cx + s * 0.55, cy - s * 0.52,
                     cx + s * 0.55, cy - s * 0.12)
        path.cubicTo(cx + s * 0.55, cy - s * 0.18,
                     cx + s * 0.05, cy + s * 0.12,
                     cx, cy + s * 0.38)
        path.closeSubpath()
        return path

    def set_dark_mode(self, dark):
        self.dark_mode = dark


class AmountPill(QPushButton):
    def __init__(self, label, color_idx, dark_mode=True, parent=None):
        super().__init__(label, parent)
        self.dark_mode = dark_mode
        self.color_idx = color_idx
        self._selected = False
        self.setFixedHeight(40)
        self.setMinimumWidth(72)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self._apply_style()

    def set_selected(self, val):
        self._selected = val
        self._apply_style()

    def _apply_style(self):
        palette = PILL_COLORS_DARK if self.dark_mode else PILL_COLORS_LIGHT
        border, text, sel_start, sel_end = palette[self.color_idx]
        hover_border = border.replace("0.40", "0.65").replace("0.35", "0.55")

        if self._selected:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 {sel_start}, stop:1 {sel_end});
                    color: white;
                    border: none;
                    border-radius: 20px;
                    font-size: 15px;
                    font-weight: 800;
                    padding: 0 18px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {text};
                    border: 1.5px solid {border};
                    border-radius: 20px;
                    font-size: 15px;
                    font-weight: 700;
                    padding: 0 18px;
                }}
                QPushButton:hover {{
                    border-color: {hover_border};
                    color: white;
                }}
            """)

    def set_dark_mode(self, dark):
        self.dark_mode = dark
        self._apply_style()


class DonateDialog(QDialog):
    """Beautiful animated donation dialog with Ko-fi integration."""

    AMOUNTS = [("1 €", "1"), ("3 €", "3"), ("5 €", "5"),
               ("10 €", "10"), ("20 €", "20")]

    def __init__(self, parent=None, dark_mode=True, language="en", config_dir=None):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self.language = language
        self._config_dir = config_dir
        self._selected_amount = "5"
        self._pills = []

        self.setWindowTitle("❤️  Support the Development")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setMinimumWidth(480)
        self.setMaximumWidth(540)
        self.setSizeGripEnabled(False)

        self._build_ui()
        self._apply_theme()

        self.setWindowOpacity(0.0)
        self._opacity = 0.0
        self._fade_timer = QTimer(self)
        self._fade_timer.timeout.connect(self._fade_step)
        QTimer.singleShot(40, self._fade_timer.start)

        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse_kofi)
        self._pulse_timer.start(2000)

    def _fade_step(self):
        self._opacity = min(1.0, self._opacity + 0.06)
        self.setWindowOpacity(self._opacity)
        if self._opacity >= 1.0:
            self._fade_timer.stop()

    def _pulse_kofi(self):
        self._set_kofi_style(bright=False)
        QTimer.singleShot(380, lambda: self._set_kofi_style(bright=True))

    def _set_kofi_style(self, bright=True):
        if self.dark_mode:
            if bright:
                css = """
                    QPushButton {
                        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                            stop:0 #ff4a7d, stop:1 #8020d0);
                        color: white; border: none; border-radius: 12px;
                        font-size: 16px; font-weight: 800;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        letter-spacing: 0.5px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                            stop:0 #ff6a9a, stop:1 #a040f0);
                    }
                    QPushButton:pressed {
                        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                            stop:0 #cc2055, stop:1 #5010a0);
                    }
                """
            else:
                css = """
                    QPushButton {
                        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                            stop:0 #aa2050, stop:1 #4a0890);
                        color: rgba(255,255,255,0.70); border: none; border-radius: 12px;
                        font-size: 16px; font-weight: 800;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        letter-spacing: 0.5px;
                    }
                """
        else:
            if bright:
                css = """
                    QPushButton {
                        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                            stop:0 #e0325a, stop:1 #6010b0);
                        color: white; border: none; border-radius: 12px;
                        font-size: 16px; font-weight: 800;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        letter-spacing: 0.5px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                            stop:0 #f05070, stop:1 #8030d0);
                    }
                    QPushButton:pressed {
                        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                            stop:0 #b01840, stop:1 #400880);
                    }
                """
            else:
                css = """
                    QPushButton {
                        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                            stop:0 #901030, stop:1 #300870);
                        color: rgba(255,255,255,0.65); border: none; border-radius: 12px;
                        font-size: 16px; font-weight: 800;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        letter-spacing: 0.5px;
                    }
                """
        self.kofi_btn.setStyleSheet(css)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.header = QWidget()
        self.header.setFixedHeight(200)
        self.header.setObjectName("DonateHeader")
        header_lay = QVBoxLayout(self.header)
        header_lay.setContentsMargins(0, 0, 0, 0)
        header_lay.setSpacing(0)

        heart_row = QHBoxLayout()
        heart_row.setAlignment(Qt.AlignCenter)
        self.big_heart = BigHeartWidget(self.dark_mode)
        heart_row.addWidget(self.big_heart, alignment=Qt.AlignCenter)
        header_lay.addStretch()
        header_lay.addLayout(heart_row)
        header_lay.addStretch()

        self.heart_canvas = HeartCanvas(self.dark_mode)
        self.heart_canvas.setParent(self.header)
        self.heart_canvas.setGeometry(0, 100, 540, 90)

        root.addWidget(self.header)

        self.body = QWidget()
        self.body.setObjectName("DonateBody")
        body_lay = QVBoxLayout(self.body)
        body_lay.setContentsMargins(32, 24, 32, 28)
        body_lay.setSpacing(18)

        title = QLabel("Support File Converter Pro")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("DonateTitle")
        body_lay.addWidget(title)

        sub = QLabel(
            "This project is completely free and built with passion. "
            "If it helps you every day, a small donation makes all the difference."
        )
        sub.setWordWrap(True)
        sub.setAlignment(Qt.AlignCenter)
        sub.setObjectName("DonateSub")
        body_lay.addWidget(sub)

        body_lay.addWidget(self._divider())

        amt_lbl = QLabel("CHOOSE AN AMOUNT:")
        amt_lbl.setObjectName("DonateAmtLabel")
        amt_lbl.setAlignment(Qt.AlignCenter)
        body_lay.addWidget(amt_lbl)

        pills_row = QHBoxLayout()
        pills_row.setSpacing(10)
        pills_row.setAlignment(Qt.AlignCenter)
        for idx, (label, value) in enumerate(self.AMOUNTS):
            pill = AmountPill(label, color_idx=idx, dark_mode=self.dark_mode)
            pill.set_selected(value == self._selected_amount)
            pill.clicked.connect(lambda checked=False, v=value: self._select_amount(v))
            self._pills.append((value, pill))
            pills_row.addWidget(pill)
        body_lay.addLayout(pills_row)

        custom_row = QHBoxLayout()
        custom_row.setAlignment(Qt.AlignCenter)
        custom_row.setSpacing(0)

        self._custom_container = QWidget()
        self._custom_container.setObjectName("DonateCustomContainer")
        self._custom_container.setFixedSize(180, 38)

        container_lay = QHBoxLayout(self._custom_container)
        container_lay.setContentsMargins(12, 0, 12, 0)
        container_lay.setSpacing(4)

        self._custom_euro = QLabel("€")
        self._custom_euro.setObjectName("DonateCustomEuro")
        self._custom_euro.setFixedWidth(14)
        self._custom_euro.setAlignment(Qt.AlignCenter)

        self._custom_input = QLineEdit()
        self._custom_input.setObjectName("DonateCustomInput")
        self._custom_input.setPlaceholderText("Custom...")
        self._custom_input.setAlignment(Qt.AlignCenter)
        self._custom_input.setFrame(False)

        from PySide6.QtCore import QRegularExpression
        from PySide6.QtGui import QRegularExpressionValidator
        rx = QRegularExpression(r'^\d{0,4}([.,]\d{0,2})?$')
        self._custom_input.setValidator(QRegularExpressionValidator(rx, self._custom_input))

        self._custom_input.textEdited.connect(self._on_custom_edited)
        self._custom_input.focusInEvent  = lambda e: (self._set_container_focus(True),  QLineEdit.focusInEvent(self._custom_input, e))
        self._custom_input.focusOutEvent = lambda e: (self._set_container_focus(False), QLineEdit.focusOutEvent(self._custom_input, e))

        container_lay.addWidget(self._custom_input)
        container_lay.addWidget(self._custom_euro)

        custom_row.addWidget(self._custom_container)
        body_lay.addLayout(custom_row)

        self.kofi_btn = QPushButton("  Donate ❤️  ")
        self.kofi_btn.setFixedHeight(52)
        self.kofi_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.kofi_btn.setObjectName("KofiBtn")
        self.kofi_btn.clicked.connect(self._open_kofi)
        body_lay.addWidget(self.kofi_btn)

        note = QLabel("Secure payment via Ko-fi  •  No account required")
        note.setAlignment(Qt.AlignCenter)
        note.setObjectName("DonateNote")
        body_lay.addWidget(note)

        body_lay.addWidget(self._divider())

        close_btn = QPushButton("Maybe another time")
        close_btn.setObjectName("DonateClose")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.clicked.connect(self.reject)
        body_lay.addWidget(close_btn, alignment=Qt.AlignCenter)

        root.addWidget(self.body)

    def _divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setObjectName("DonateDivider")
        return line

    def _select_amount(self, value):
        self._selected_amount = value
        for v, pill in self._pills:
            pill.set_selected(v == value)
        # Clear custom input when a pill is selected
        if hasattr(self, "_custom_input"):
            self._custom_input.blockSignals(True)
            self._custom_input.clear()
            self._custom_input.blockSignals(False)
            self._set_container_focus(False)

    def _set_container_focus(self, focused: bool):
        """Toggle the focus highlight on the custom input container."""
        if not hasattr(self, "_custom_container"):
            return
        if focused:
            color = "rgba(255,74,125,0.55)" if self.dark_mode else "rgba(220,50,90,0.50)"
            bg    = "rgba(255,74,125,0.07)"  if self.dark_mode else "rgba(220,50,90,0.05)"
        else:
            color = "rgba(255,255,255,0.12)" if self.dark_mode else "rgba(30,30,50,0.14)"
            bg    = "rgba(255,255,255,0.05)" if self.dark_mode else "rgba(30,30,50,0.04)"
        self._custom_container.setStyleSheet(f"""
            QWidget#DonateCustomContainer {{
                background: {bg};
                border: 1.5px solid {color};
                border-radius: 19px;
            }}
        """)

    def _on_custom_edited(self, text: str):
        """Called when the user types in the custom amount field."""
        for _, pill in self._pills:
            pill.set_selected(False)
        try:
            value = float(text.replace(",", "."))
            if value > 0:
                self._selected_amount = f"{value:.2f}".rstrip("0").rstrip(".")
            else:
                self._selected_amount = "5"  # fallback
        except ValueError:
            self._selected_amount = "5"

    def _effective_amount(self) -> str:
        """Return the final amount to use, validating the custom field last."""
        if hasattr(self, "_custom_input") and self._custom_input.text().strip():
            text = self._custom_input.text().strip().replace(",", ".")
            try:
                value = float(text)
                if 0 < value <= 9999:
                    return f"{value:.2f}".rstrip("0").rstrip(".")
            except ValueError:
                pass
        return self._selected_amount

    def _open_kofi(self):
        try:
            amount = self._effective_amount()

            mark_donor_pending(amount, getattr(self, "_config_dir", None))

            if webbrowser.open(KOFI_LINK):
                self.kofi_btn.setText(" Redirection... ")
                self.kofi_btn.setEnabled(False)
                QTimer.singleShot(2500, self._reset_kofi_btn)
                QTimer.singleShot(1250, self.accept)
            else:
                raise RuntimeError("System fails to launch default browser")

        except Exception as e:
            logging.error(f"[Ko-fi Error] {e}", exc_info=True)
            QMessageBox.critical(self, "Redirection Error", f"Unable to open Ko-fi page.\n\nDetail: {e}")
            self._reset_kofi_btn()

    def _reset_kofi_btn(self):
        self.kofi_btn.setText("  Donate ❤️  ")
        self.kofi_btn.setEnabled(True)

    def _apply_theme(self):
        if self.dark_mode:
            self._apply_dark()
        else:
            self._apply_light()
        self.big_heart.set_dark_mode(self.dark_mode)
        self.heart_canvas.set_dark_mode(self.dark_mode)
        for _, pill in self._pills:
            pill.set_dark_mode(self.dark_mode)
        self._set_kofi_style(bright=True)

    def _apply_dark(self):
        self.setStyleSheet("""
            QDialog { background: #0f1117; }
            QWidget#DonateHeader {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #1a0a14, stop:0.5 #1c0d1f, stop:1 #0f1117);
                border-bottom: 1px solid rgba(255,74,125,0.18);
            }
            QWidget#DonateBody { background: #0f1117; }
            QLabel#DonateTitle {
                font-size: 20px; font-weight: 800; color: #ffffff;
                font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
            }
            QLabel#DonateSub {
                font-size: 13px; color: rgba(255,255,255,0.52);
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel#DonateAmtLabel {
                font-size: 11px; font-weight: 600; letter-spacing: 1.2px;
                color: rgba(255,255,255,0.38);
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel#DonateNote {
                font-size: 11px; color: rgba(255,255,255,0.25);
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QWidget#DonateCustomContainer {
                background: rgba(255,255,255,0.05);
                border: 1.5px solid rgba(255,255,255,0.12);
                border-radius: 19px;
            }
            QWidget#DonateCustomContainer:hover {
                border-color: rgba(255,255,255,0.22);
            }
            QLabel#DonateCustomEuro {
                font-size: 14px; font-weight: 700;
                color: rgba(255,255,255,0.40);
                font-family: 'Segoe UI', Arial, sans-serif;
                background: transparent;
            }
            QLineEdit#DonateCustomInput {
                background: transparent;
                color: rgba(255,255,255,0.80);
                border: none;
                font-size: 14px; font-weight: 600;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton#DonateClose {
                background: transparent; color: rgba(255,255,255,0.25);
                border: none; font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif; padding: 4px 12px;
            }
            QPushButton#DonateClose:hover {
                color: rgba(255,255,255,0.55); text-decoration: underline;
            }
            QFrame#DonateDivider { background: rgba(255,255,255,0.07); }
        """)

    def _apply_light(self):
        self.setStyleSheet("""
            QDialog { background: #f7f8fc; }
            QWidget#DonateHeader {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #fce4ec, stop:0.5 #f3e5ff, stop:1 #f7f8fc);
                border-bottom: 1px solid rgba(200,40,80,0.12);
            }
            QWidget#DonateBody { background: #f7f8fc; }
            QLabel#DonateTitle {
                font-size: 20px; font-weight: 800; color: #1a1a2e;
                font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
            }
            QLabel#DonateSub {
                font-size: 13px; color: rgba(30,30,50,0.55);
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel#DonateAmtLabel {
                font-size: 11px; font-weight: 600; letter-spacing: 1.2px;
                color: rgba(30,30,50,0.38);
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel#DonateNote {
                font-size: 11px; color: rgba(30,30,50,0.32);
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QWidget#DonateCustomContainer {
                background: rgba(30,30,50,0.04);
                border: 1.5px solid rgba(30,30,50,0.14);
                border-radius: 19px;
            }
            QWidget#DonateCustomContainer:hover {
                border-color: rgba(30,30,50,0.25);
            }
            QLabel#DonateCustomEuro {
                font-size: 14px; font-weight: 700;
                color: rgba(30,30,50,0.38);
                font-family: 'Segoe UI', Arial, sans-serif;
                background: transparent;
            }
            QLineEdit#DonateCustomInput {
                background: transparent;
                color: rgba(30,30,50,0.80);
                border: none;
                font-size: 14px; font-weight: 600;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton#DonateClose {
                background: transparent; color: rgba(30,30,50,0.32);
                border: none; font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif; padding: 4px 12px;
            }
            QPushButton#DonateClose:hover {
                color: rgba(30,30,50,0.65); text-decoration: underline;
            }
            QFrame#DonateDivider { background: rgba(30,30,50,0.08); }
        """)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'heart_canvas'):
            self.heart_canvas.setGeometry(0, 100, self.header.width(), 90)


class StarParticle:
    """Tiny twinkling star for the thank-you animation."""
    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.size = random.uniform(2, 6)
        self.alpha = random.uniform(0.2, 0.9)
        self.speed_y = random.uniform(-0.6, -0.2)
        self.speed_x = random.uniform(-0.3, 0.3)
        self.twinkle = random.uniform(0, math.pi * 2)
        self.twinkle_speed = random.uniform(0.04, 0.10)
        self.alive = True

    def update(self):
        self.twinkle += self.twinkle_speed
        self.x += self.speed_x
        self.y += self.speed_y
        self.alpha = 0.4 + 0.5 * abs(math.sin(self.twinkle))
        if self.y < -10:
            self.alive = False

    def draw(self, painter: QPainter):
        c = QColor(255, 220, 80, int(self.alpha * 255))
        painter.setBrush(QBrush(c))
        painter.setPen(Qt.NoPen)
        s = self.size
        cx, cy = self.x, self.y
        path = QPainterPath()
        path.moveTo(cx, cy - s)
        path.lineTo(cx + s*0.3, cy - s*0.3)
        path.lineTo(cx + s, cy)
        path.lineTo(cx + s*0.3, cy + s*0.3)
        path.lineTo(cx, cy + s)
        path.lineTo(cx - s*0.3, cy + s*0.3)
        path.lineTo(cx - s, cy)
        path.lineTo(cx - s*0.3, cy - s*0.3)
        path.closeSubpath()
        painter.drawPath(path)


class ThankYouCanvas(QWidget):
    """Animated canvas: hearts + stars floating upward."""
    def __init__(self, dark_mode=True, parent=None):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self.hearts = []
        self.stars = []
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._spawn_t = QTimer(self)
        self._spawn_t.timeout.connect(self._spawn)
        self._spawn_t.start(120)
        self._update_t = QTimer(self)
        self._update_t.timeout.connect(self._tick)
        self._update_t.start(16)

    def _spawn(self):
        w, h = max(self.width(), 1), max(self.height(), 1)
        x = random.uniform(w * 0.1, w * 0.9)
        self.hearts.append(HeartParticle(x, h + 5, self.dark_mode))
        self.stars.append(StarParticle(w, h))

    def _tick(self):
        for p in self.hearts + self.stars:
            p.update()
        self.hearts = [p for p in self.hearts if p.alive]
        self.stars  = [p for p in self.stars  if p.alive]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        for p in self.hearts:
            p.draw(painter)
        for p in self.stars:
            p.draw(painter)
        painter.end()


class ThankYouDialog(QDialog):
    """
    Special 'Thank You' dialog shown on the next app launch
    after the user clicked the Ko-fi donation button.
    """

    def __init__(self, parent=None, dark_mode=True, amount=""):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self.amount = amount

        self.setWindowTitle("💛  Thank You!")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setFixedWidth(460)
        self.setSizeGripEnabled(False)

        self._build_ui()
        self._apply_theme()

        self.setWindowOpacity(0.0)
        self._opacity = 0.0
        self._fade_t = QTimer(self)
        self._fade_t.timeout.connect(self._fade_step)
        QTimer.singleShot(40, self._fade_t.start)

    def _fade_step(self):
        self._opacity = min(1.0, self._opacity + 0.055)
        self.setWindowOpacity(self._opacity)
        if self._opacity >= 1.0:
            self._fade_t.stop()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.header = QWidget()
        self.header.setFixedHeight(160)
        self.header.setObjectName("TYHeader")
        header_lay = QVBoxLayout(self.header)
        header_lay.setContentsMargins(0, 0, 0, 0)

        heart_row = QHBoxLayout()
        heart_row.setAlignment(Qt.AlignCenter)
        self.big_heart = BigHeartWidget(self.dark_mode)
        heart_row.addWidget(self.big_heart, alignment=Qt.AlignCenter)
        header_lay.addStretch()
        header_lay.addLayout(heart_row)
        header_lay.addStretch()

        self.canvas = ThankYouCanvas(self.dark_mode)
        self.canvas.setParent(self.header)
        self.canvas.setGeometry(0, 0, 460, 160)

        root.addWidget(self.header)

        body = QWidget()
        body.setObjectName("TYBody")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(32, 24, 32, 28)
        body_lay.setSpacing(14)

        title = QLabel("Thank you so much! 🌟")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("TYTitle")
        body_lay.addWidget(title)

        if self.amount:
            badge_row = QHBoxLayout()
            badge_row.setAlignment(Qt.AlignCenter)
            badge = QLabel(f"  {self.amount} €  ")
            badge.setObjectName("TYBadge")
            badge.setAlignment(Qt.AlignCenter)
            badge_row.addWidget(badge)
            body_lay.addLayout(badge_row)

        msg_text = (
            "Your generosity truly makes a difference. "
            "Every contribution helps keep File Converter Pro "
            "free, updated, and full of new features.\n\n"
            "You're the reason this project keeps going. "
            "From the bottom of my heart. Thank you! 💙"
        )
        msg = QLabel(msg_text)
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignCenter)
        msg.setObjectName("TYMsg")
        body_lay.addWidget(msg)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setObjectName("TYDivider")
        body_lay.addWidget(line)

        close_btn = QPushButton("Continue  ✨")
        close_btn.setObjectName("TYClose")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setFixedHeight(44)
        close_btn.clicked.connect(self.accept)
        body_lay.addWidget(close_btn)

        root.addWidget(body)

    def _apply_theme(self):
        if self.dark_mode:
            self._apply_dark()
        else:
            self._apply_light()

    def _apply_dark(self):
        self.setStyleSheet("""
            QDialog { background: #0f1117; }
            QWidget#TYHeader {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #12080d, stop:0.5 #15051a, stop:1 #0f1117);
                border-bottom: 1px solid rgba(255,200,60,0.15);
            }
            QWidget#TYBody { background: #0f1117; }
            QLabel#TYTitle {
                font-size: 22px; font-weight: 800; color: #ffffff;
                font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
            }
            QLabel#TYBadge {
                font-size: 18px; font-weight: 800; color: #ffd040;
                font-family: 'Segoe UI', Arial, sans-serif;
                background: rgba(255,200,60,0.12);
                border: 1.5px solid rgba(255,200,60,0.35);
                border-radius: 14px; padding: 4px 16px;
            }
            QLabel#TYMsg {
                font-size: 13px; color: rgba(255,255,255,0.58);
                font-family: 'Segoe UI', Arial, sans-serif;
                line-height: 1.5;
            }
            QFrame#TYDivider { background: rgba(255,255,255,0.07); }
            QPushButton#TYClose {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #f0a000, stop:1 #ff6020);
                color: white; border: none; border-radius: 10px;
                font-size: 15px; font-weight: 800;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton#TYClose:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #ffc020, stop:1 #ff8040);
            }
            QPushButton#TYClose:pressed {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #c07000, stop:1 #cc4010);
            }
        """)

    def _apply_light(self):
        self.setStyleSheet("""
            QDialog { background: #fafbff; }
            QWidget#TYHeader {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #fff8e7, stop:0.5 #fef0fa, stop:1 #fafbff);
                border-bottom: 1px solid rgba(200,140,20,0.15);
            }
            QWidget#TYBody { background: #fafbff; }
            QLabel#TYTitle {
                font-size: 22px; font-weight: 800; color: #1a1a2e;
                font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
            }
            QLabel#TYBadge {
                font-size: 18px; font-weight: 800; color: #c07000;
                font-family: 'Segoe UI', Arial, sans-serif;
                background: rgba(200,140,20,0.10);
                border: 1.5px solid rgba(200,140,20,0.30);
                border-radius: 14px; padding: 4px 16px;
            }
            QLabel#TYMsg {
                font-size: 13px; color: rgba(30,30,50,0.60);
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QFrame#TYDivider { background: rgba(30,30,50,0.08); }
            QPushButton#TYClose {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #d08000, stop:1 #e05010);
                color: white; border: none; border-radius: 10px;
                font-size: 15px; font-weight: 800;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton#TYClose:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #f0a010, stop:1 #f07030);
            }
            QPushButton#TYClose:pressed {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #a06000, stop:1 #b03000);
            }
        """)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "canvas"):
            self.canvas.setGeometry(0, 0, self.header.width(), 160)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = ThankYouDialog(dark_mode=True, amount="5")
    dlg.exec()
    sys.exit(0)