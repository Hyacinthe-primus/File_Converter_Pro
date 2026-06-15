"""
Achievements UI
Aesthetic: Luxury game HUD
Every card, ring and bar is custom-drawn with QPainter for a premium feel.

Visual highlights:
  • XPRingWidget
  • AchievementCard
  • StatBarWidget
  • Custom tab row
  • Filter chips

"""

import os
import math
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QGroupBox,
    QTreeWidget, QTreeWidgetItem, QComboBox, QLineEdit, QDialog,
    QSizePolicy, QStackedWidget, QSpacerItem, QApplication,
    QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui import (
    QPixmap, QColor, QPainter, QPainterPath, QBrush, QPen,
    QLinearGradient, QRadialGradient, QFont, QFontMetrics)

import sys
_PKG_DIR  = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_PKG_DIR)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)
from translations import TranslationManager
from utils.translation_mixin import TranslationMixin


class _DSBase:
    TIERS = {
        "starter":       ("#A8DADC", "#4A8A8C"),
        "bronze":        ("#CD7F32", "#80500A"),
        "steel":         ("#71797E", "#3A4044"),
        "silver":        ("#C0C0C0", "#707070"),
        "platinum_tier": ("#C18D30", "#7A5A10"),
        "gold":          ("#FFD700", "#7A6520"),
        "rare":          ("#4169E1", "#1A3A90"),
        "epic":          ("#9370DB", "#4A2080"),
        "legendary":     ("#FF8C00", "#804400"),
        "diamond":       ("#B9F2FF", "#3090C0"),
        "platinum":      ("#E5E4E2", "#808080"),
        "advanced":      ("#22d3ee", "#0A7A90"),
    }

    TIER_HOVER = {
        "starter":       "#C8ECEE",
        "bronze":        "#E8943A",
        "steel":         "#9AAAB0",
        "silver":        "#E0E0E0",
        "platinum_tier": "#E0A840",
        "gold":          "#FFD700",
        "rare":          "#6B8FFF",
        "epic":          "#B090F0",
        "legendary":     "#FFA830",
        "diamond":       "#D8F8FF",
        "platinum":      "#F5F4F2",
        "advanced":      "#50E8FF",
    }

    RADIUS   = 12
    RADIUS_S = 7
    PAD      = 16
    PAD_S    = 10

    GOLD        = "#D4AF37"
    GOLD_BRIGHT = "#FFD700"
    GOLD_DIM    = "#7A6520"

    GREEN   = "#3FB950"
    GREEN_DIM = "#1A4226"
    RED     = "#F85149"
    RED_DIM = "#3D1C1A"
    BLUE    = "#58A6FF"
    PURPLE  = "#BC8CFF"

class _DSDark(_DSBase):
    BG_BASE      = "#0D1117"
    BG_SURFACE   = "#161B22"
    BG_RAISED    = "#1C2333"
    BG_INPUT     = "#21262D"

    BORDER       = "#30363D"
    BORDER_LIGHT = "#3D444D"

    TEXT_PRIMARY   = "#E6EDF3"
    TEXT_SECONDARY = "#8B949E"
    TEXT_MUTED     = "#484F58"

class _DSLight(_DSBase):
    BG_BASE      = "#F5F3EE"
    BG_SURFACE   = "#FFFFFF"
    BG_RAISED    = "#EDE9E0"
    BG_INPUT     = "#F9F7F2"

    BORDER       = "#D6CFC0"
    BORDER_LIGHT = "#C4BBa8"

    TEXT_PRIMARY   = "#1C1A16"
    TEXT_SECONDARY = "#6B6355"
    TEXT_MUTED     = "#A89F8F"

    GREEN_DIM = "#D4EDDA"
    RED_DIM   = "#FADBD8"

class _DSProxy:
    def __init__(self):
        self._theme: _DSBase = _DSDark()

    def use_dark(self):
        self._theme = _DSDark()

    def use_light(self):
        self._theme = _DSLight()

    @property
    def is_dark(self) -> bool:
        return isinstance(self._theme, _DSDark)

    def __getattr__(self, name: str):
        return getattr(self._theme, name)

DS = _DSProxy()


class XPRingWidget(QWidget):
    def __init__(self, total_xp: int = 0, max_xp: int = 1, parent=None):
        super().__init__(parent)
        self.total_xp = total_xp
        self.max_xp   = max(max_xp, 1)
        self.progress = min(total_xp / self.max_xp, 1.0)
        self._shimmer = 0.0
        self._rainbow_hue = 0.0
        self.setFixedSize(190, 190)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(30)

    def _tick(self):
        self._shimmer     = (self._shimmer + 0.025) % (2 * math.pi)
        self._rainbow_hue = (self._rainbow_hue + 1.2) % 360.0
        self.update()

    def set_values(self, total_xp: int, max_xp: int = 0):
        self.total_xp = total_xp
        if max_xp > 0:
            self.max_xp = max_xp
        self.progress = min(total_xp / self.max_xp, 1.0)
        self.update()

    @property
    def _complete(self) -> bool:
        return self.progress >= 1.0

    def _format_xp(self, xp: int) -> str:
        s = str(xp)
        groups = []
        while len(s) > 3:
            groups.insert(0, s[-3:])
            s = s[:-3]
        groups.insert(0, s)
        return "\u202F".join(groups)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        cx, cy  = self.width() / 2, self.height() / 2
        r_outer = min(cx, cy) - 10
        r_inner = r_outer - 18

        rect_outer = QRectF(cx - r_outer, cy - r_outer, r_outer * 2, r_outer * 2)

        p.setPen(QPen(QColor(DS.BORDER), 18, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(rect_outer)

        if self.progress > 0:
            sweep = int(360 * 16 * self.progress)

            if self._complete:
                seg_sweep = 360 * 16 // 12
                for i in range(12):
                    hue = (self._rainbow_hue + i * 30) % 360
                    c   = QColor.fromHsvF(hue / 360.0, 0.85, 1.0)
                    gc = QColor(c); gc.setAlpha(55)
                    p.setPen(QPen(gc, 28, Qt.SolidLine, Qt.RoundCap))
                    p.drawArc(rect_outer, (90 - i * 30) * 16 + int(self._shimmer * 50),
                              -seg_sweep)
                    p.setPen(QPen(c, 18, Qt.SolidLine, Qt.RoundCap))
                    p.drawArc(rect_outer, (90 - i * 30) * 16 + int(self._shimmer * 50),
                              -seg_sweep)
            else:
                p.setPen(QPen(QColor(212, 175, 55, 55), 28, Qt.SolidLine, Qt.RoundCap))
                p.drawArc(rect_outer, 90 * 16, -sweep)
                p.setPen(QPen(QColor(DS.GOLD), 18, Qt.SolidLine, Qt.RoundCap))
                p.drawArc(rect_outer, 90 * 16, -sweep)
                tip_angle = math.radians(90 - 360 * self.progress)
                tip_x = cx + r_outer * math.cos(tip_angle)
                tip_y = cy - r_outer * math.sin(tip_angle)
                alpha = int(170 + 85 * math.sin(self._shimmer))
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(255, 230, 80, alpha))
                p.drawEllipse(QPointF(tip_x, tip_y), 8, 8)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(DS.BG_BASE))
        p.drawEllipse(QRectF(cx - r_inner, cy - r_inner, r_inner * 2, r_inner * 2))

        if self._complete:
            p.setPen(QColor(DS.GOLD_BRIGHT))
            p.setFont(QFont("Segoe UI", 13, QFont.Bold))
            p.drawText(QRectF(cx - r_inner, cy - r_inner * 0.55,
                              r_inner * 2, r_inner * 0.55),
                       Qt.AlignHCenter | Qt.AlignVCenter, "✦  MAX  ✦")

            rainbow_c = QColor.fromHsvF(self._rainbow_hue / 360.0, 0.9, 1.0)
            p.setPen(rainbow_c)
            p.setFont(QFont("Segoe UI", 11, QFont.Bold))
            p.drawText(QRectF(cx - r_inner, cy - r_inner * 0.05,
                              r_inner * 2, r_inner * 0.6),
                       Qt.AlignHCenter | Qt.AlignTop,
                       self._format_xp(self.total_xp))

            p.setPen(QColor(DS.TEXT_MUTED))
            p.setFont(QFont("Segoe UI", 7))
            p.drawText(QRectF(cx - r_inner, cy + r_inner * 0.45,
                              r_inner * 2, r_inner * 0.4),
                       Qt.AlignHCenter | Qt.AlignTop, "TOTAL XP")
        else:
            p.setPen(QColor(DS.GOLD_BRIGHT))
            p.setFont(QFont("Segoe UI", 20, QFont.Bold))
            p.drawText(QRectF(cx - r_inner, cy - r_inner * 0.72,
                              r_inner * 2, r_inner * 1.0),
                       Qt.AlignHCenter | Qt.AlignVCenter,
                       self._format_xp(self.total_xp))

            p.setPen(QColor(DS.TEXT_SECONDARY))
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(QRectF(cx - r_inner, cy + r_inner * 0.12,
                              r_inner * 2, r_inner * 0.45),
                       Qt.AlignHCenter | Qt.AlignTop,
                       f"/ {self._format_xp(self.max_xp)} XP")

            p.setPen(QColor(DS.TEXT_MUTED))
            p.setFont(QFont("Segoe UI", 7))
            p.drawText(QRectF(cx - r_inner, cy + r_inner * 0.48,
                              r_inner * 2, r_inner * 0.35),
                       Qt.AlignHCenter | Qt.AlignTop, "TOTAL XP")

        p.end()


class StatBarWidget(QWidget):
    def __init__(self, label: str, value: str, fraction: float = 1.0,
                 color: str = DS.BLUE, parent=None):
        super().__init__(parent)
        self.label    = label
        self.value    = value
        self.fraction = max(0.0, min(1.0, fraction))
        self.color    = QColor(color)
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(DS.BG_RAISED))
        p.drawRoundedRect(QRectF(0, h * 0.6, w, h * 0.28), 4, 4)

        fill_w = max(8.0, w * self.fraction)
        grad = QLinearGradient(0, 0, fill_w, 0)
        c_dim = QColor(self.color)
        c_dim.setAlpha(120)
        grad.setColorAt(0.0, c_dim)
        grad.setColorAt(1.0, self.color)
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(QRectF(0, h * 0.6, fill_w, h * 0.28), 4, 4)

        p.setPen(QColor(DS.TEXT_SECONDARY))
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(QRectF(0, 0, w * 0.7, h * 0.58), Qt.AlignVCenter | Qt.AlignLeft,
                   self.label)

        p.setPen(self.color)
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.drawText(QRectF(0, 0, w, h * 0.58), Qt.AlignVCenter | Qt.AlignRight,
                   self.value)

        p.end()


class GlobalProgressBar(QWidget):
    """
    Custom progress bar (rounded pill style).
    Height: 22px. Bold text. Gold gradient fill.
    """
    def __init__(self, value: int = 0, maximum: int = 100, parent=None):
        super().__init__(parent)
        self._value   = max(0, min(value, maximum))
        self._maximum = max(maximum, 1)
        self.setFixedHeight(22)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def setValue(self, value: int) -> None:
        """Set value and repaint."""
        self._value = max(0, min(int(value), self._maximum))
        self.update()

    def setMaximum(self, maximum: int) -> None:
        """Set max value."""
        self._maximum = max(int(maximum), 1)
        self._value   = min(self._value, self._maximum)
        self.update()

    def value(self) -> int:
        """Get current value."""
        return self._value

    def maximum(self) -> int:
        """Get max value."""
        return self._maximum

    @property
    def _fraction(self) -> float:
        """Progress ratio (0–1)."""
        return self._value / self._maximum

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h  = self.width(), self.height()
        r     = h / 2
        frac  = self._fraction

        # Track
        p.setPen(QPen(QColor(DS.BORDER), 1))
        p.setBrush(QColor(DS.BG_RAISED))
        p.drawRoundedRect(QRectF(0, 0, w, h), r, r)

        # Fill
        fill_w = w * frac
        if fill_w > 0:
            full_pill = QPainterPath()
            full_pill.addRoundedRect(QRectF(0, 0, w, h), r, r)
            fill_rect = QPainterPath()
            fill_rect.addRect(QRectF(0, 0, fill_w, h))
            fill_path = full_pill.intersected(fill_rect)

            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0.0, QColor(DS.GOLD_DIM))
            grad.setColorAt(1.0, QColor(DS.GOLD))
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(grad))
            p.drawPath(fill_path)

        pct_str = f"{frac * 100:.1f}%"
        txt_c   = QColor("#FFFFFF" if DS.is_dark else "#1C1A16")
        p.setPen(txt_c)
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.drawText(QRectF(0, 0, w, h), Qt.AlignCenter, pct_str)
        p.end()


class AchievementCard(QFrame):
    def __init__(self, achievement: dict, tier_data: dict,
                 category_data: dict, icon_path: str,
                 language: str = "fr", dark_mode: bool = True, parent=None):
        super().__init__(parent)
        self.achievement   = achievement
        self.tier_data     = tier_data or {}
        self.category_data = category_data or {}
        self.icon_path     = icon_path
        self.language      = language
        self.dark_mode     = dark_mode
        from translations import TranslationManager as _TM
        self._tm = _TM(); self._tm.set_language(language)

        self._hover        = False
        self._wave         = 0.0
        self._caustic      = 0.0
        self.setMouseTracking(True)
        self.setCursor(Qt.ArrowCursor)
        self.setFixedHeight(130)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(0)
        self._shadow.setOffset(0, 0)
        self._shadow.setColor(QColor(0, 0, 0, 0))
        self.setGraphicsEffect(self._shadow)

        tier_id = achievement.get("tier", "bronze").lower()
        tdata = DS.TIERS.get(tier_id, DS.TIERS["bronze"])
        self._tier_color = QColor(tdata[0])
        self._tier_glow  = QColor(tdata[1])

        cat_color_str = self.category_data.get("color", "#58A6FF")
        self._cat_color = QColor(cat_color_str)

        hover_hex = DS.TIER_HOVER.get(tier_id, DS.TIER_HOVER["bronze"])
        self._hover_color = QColor(hover_hex)

        self._is_secret = (
            (achievement.get("secret", False) and not achievement.get("unlocked", False))
            or achievement.get("_hide_secret", False)
        )
        if self._is_secret:
            self._cat_color = QColor("#8B0000")

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        self._pixmap: Optional[QPixmap] = None
        if icon_path and os.path.exists(icon_path):
            px = QPixmap(icon_path)
            if not px.isNull():
                self._pixmap = px.scaled(38, 38, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def _tick(self):
        step = 0.06
        if self._hover:
            self._wave    = min(self._wave + step, 1.0)
            self._caustic = (self._caustic + 0.04) % (2 * math.pi)
        else:
            self._wave = max(self._wave - step * 1.4, 0.0)
        self.update()
        if not self._hover and self._wave <= 0.0:
            self._timer.stop()

    def enterEvent(self, _e):
        self._hover = True
        self._timer.start(16)
        blur   = 28 if DS.is_dark else 18
        offset = 4  if DS.is_dark else 3
        alpha  = 120 if DS.is_dark else 60
        self._shadow.setBlurRadius(blur)
        self._shadow.setOffset(0, offset)
        self._shadow.setColor(QColor(0, 0, 0, alpha))

    def leaveEvent(self, _e):
        self._hover = False
        self._shadow.setBlurRadius(0)
        self._shadow.setOffset(0, 0)
        self._shadow.setColor(QColor(0, 0, 0, 0))

    @staticmethod
    def _hex_path(cx: float, cy: float, r: float) -> QPainterPath:
        path = QPainterPath()
        for i in range(6):
            a = math.radians(60 * i - 30)
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
        path.closeSubpath()
        return path

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        ach      = self.achievement
        unlocked = ach.get("unlocked", False)
        secret   = self._is_secret
        w, h     = self.width(), self.height()
        r        = DS.RADIUS
        t        = self._wave
        cat_c    = self._cat_color
        hov_c    = self._hover_color   # tier-based hover tint

        clip = QPainterPath()
        clip.addRoundedRect(QRectF(0, 0, w, h), r, r)
        p.setClipPath(clip)

        if secret:
            base_c = QColor("#0A0608") if DS.is_dark else QColor("#FAE8E8")
            p.fillPath(clip, QBrush(base_c))
        elif unlocked:
            diag = QLinearGradient(0, 0, w, h)
            c_top  = QColor(self._tier_color); c_top.setAlpha(45)
            c_mid  = QColor(self._tier_glow);  c_mid.setAlpha(30)
            c_bot  = QColor(DS.BG_RAISED if DS.is_dark else DS.BG_SURFACE)
            diag.setColorAt(0.0,  c_top)
            diag.setColorAt(0.45, c_mid)
            diag.setColorAt(1.0,  c_bot)
            p.fillPath(clip, QBrush(diag))

            sheen = QLinearGradient(0, 0, 0, h * 0.45)
            sheen_top  = QColor(255, 255, 255, 18 if DS.is_dark else 35)
            sheen_bot  = QColor(255, 255, 255, 0)
            sheen.setColorAt(0, sheen_top)
            sheen.setColorAt(1, sheen_bot)
            p.fillPath(clip, QBrush(sheen))
        else:
            base_c = QColor(DS.BG_SURFACE)
            p.fillPath(clip, QBrush(base_c))

        if t > 0.001:
            if unlocked:
                pulse_r  = max(w, h) * 1.1 * t
                inner_g  = QRadialGradient(w * 0.5, h * 0.5, pulse_r * 0.0001)
                inner_g.setFocalPoint(w * 0.5, h * 0.5)
                core_bright = QColor(self._tier_color); core_bright.setAlpha(int(55 * t))
                core_mid    = QColor(self._tier_color); core_mid.setAlpha(int(22 * t))
                core_edge   = QColor(self._tier_color); core_edge.setAlpha(0)
                inner_g.setColorAt(0.0, core_bright)
                inner_g.setColorAt(0.45, core_mid)
                inner_g.setColorAt(1.0,  core_edge)
                inner_g.setRadius(pulse_r)
                p.fillPath(clip, QBrush(inner_g))

                halo_g = QRadialGradient(w * 0.5, h * 0.5, max(w, h) * 0.9)
                halo_c1 = QColor(hov_c); halo_c1.setAlpha(0)
                halo_c2 = QColor(hov_c); halo_c2.setAlpha(int(30 * t))
                halo_c3 = QColor(hov_c); halo_c3.setAlpha(int(55 * t))
                halo_g.setColorAt(0.0,  halo_c1)
                halo_g.setColorAt(0.55, halo_c2)
                halo_g.setColorAt(1.0,  halo_c3)
                p.fillPath(clip, QBrush(halo_g))

                if t > 0.25:
                    caustic_alpha = int(22 * min((t - 0.25) / 0.75, 1.0))
                    sweep_pos = (math.sin(self._caustic * 0.7) + 1.0) / 2.0
                    cx_pos    = -w * 0.2 + w * 1.4 * sweep_pos
                    cg = QLinearGradient(cx_pos - w * 0.3, 0, cx_pos + w * 0.3, h)
                    cg.setColorAt(0.0, QColor(255, 255, 255, 0))
                    cg.setColorAt(0.45, QColor(255, 255, 255, caustic_alpha))
                    cg.setColorAt(0.55, QColor(255, 255, 255, caustic_alpha))
                    cg.setColorAt(1.0,  QColor(255, 255, 255, 0))
                    p.fillPath(clip, QBrush(cg))
            else:
                flood_h   = h * t
                flood_path = QPainterPath()
                flood_path.addRoundedRect(QRectF(0, h - flood_h, w, flood_h), 0, 0)
                flood_c = QColor(cat_c); flood_c.setAlpha(int(38 * t))
                p.fillPath(flood_path, QBrush(flood_c))

                refract = QRadialGradient(w * 0.5, h * 0.5, max(w, h) * 0.72)
                edge_c = QColor(cat_c); edge_c.setAlpha(int(70 * t))
                mid_c  = QColor(cat_c); mid_c.setAlpha(int(22 * t))
                core_c = QColor(cat_c); core_c.setAlpha(0)
                refract.setColorAt(0.0,  core_c)
                refract.setColorAt(0.55, mid_c)
                refract.setColorAt(1.0,  edge_c)
                p.fillPath(clip, QBrush(refract))

                if t > 0.3:
                    caustic_alpha = int(28 * min((t - 0.3) / 0.7, 1.0))
                    sweep_pos = (math.sin(self._caustic) + 1.0) / 2.0
                    cx_pos    = -w * 0.3 + w * 1.6 * sweep_pos
                    caustic_g = QLinearGradient(cx_pos - w * 0.35, 0,
                                                cx_pos + w * 0.35, h)
                    caustic_g.setColorAt(0.0, QColor(255, 255, 255, 0))
                    caustic_g.setColorAt(0.4, QColor(255, 255, 255, caustic_alpha))
                    caustic_g.setColorAt(0.6, QColor(255, 255, 255, caustic_alpha))
                    caustic_g.setColorAt(1.0, QColor(255, 255, 255, 0))
                    p.fillPath(clip, QBrush(caustic_g))

                if t < 0.95:
                    wl_y     = h - flood_h
                    wl_alpha = int(55 * t * (1 - abs(t - 0.5) * 1.8))
                    if wl_alpha > 0:
                        wave_path = QPainterPath()
                        wave_path.moveTo(0, wl_y)
                        amp  = 3.5 * t
                        freq = 2 * math.pi / w * 3
                        step = max(1, w // 40)
                        for x in range(0, w + step, step):
                            y_off = amp * math.sin(freq * x + self._caustic * 2)
                            wave_path.lineTo(x, wl_y + y_off)
                        wave_path.lineTo(w, h)
                        wave_path.lineTo(0, h)
                        wave_path.closeSubpath()
                        wl_fill = QColor(cat_c); wl_fill.setAlpha(int(18 * t))
                        p.fillPath(wave_path, QBrush(wl_fill))

        p.setClipping(False)

        if secret:
            bc = QColor(DS.RED); bc.setAlpha(int(110 + 90 * t))
            bw = 1.2 + 1.2 * t
            p.setPen(QPen(bc, bw, Qt.DashLine, Qt.RoundCap, Qt.RoundJoin))
        elif unlocked:
            if t > 0.01:
                gc2 = QColor(hov_c); gc2.setAlpha(int(60 * t))
                p.setPen(QPen(gc2, 5.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                p.setBrush(Qt.NoBrush)
                p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)
            tc = QColor(self._tier_color); tc.setAlpha(int(160 + 95 * t))
            p.setPen(QPen(tc, 1.8 + 0.7 * t, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        else:
            locked_bc = QColor(DS.BORDER)
            if t > 0.01:
                r_val = int(locked_bc.red()   * (1 - t) + cat_c.red()   * t)
                g_val = int(locked_bc.green() * (1 - t) + cat_c.green() * t)
                b_val = int(locked_bc.blue()  * (1 - t) + cat_c.blue()  * t)
                locked_bc = QColor(r_val, g_val, b_val)
            locked_bc.setAlpha(int(120 + 110 * t))
            p.setPen(QPen(locked_bc, 1.2 + 0.8 * t, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), r, r)

        stripe_color = hov_c if (t > 0.01 and unlocked) else (
            cat_c if (t > 0.01 and not unlocked) else (
            QColor(DS.RED) if secret else self._tier_color))
        stripe_w  = 5.0 if unlocked else 3.5
        stripe_h2 = h * (0.55 + 0.3 * t)
        stripe_y  = (h - stripe_h2) / 2
        stripe_p  = QPainterPath()
        stripe_p.addRoundedRect(QRectF(1, stripe_y, stripe_w, stripe_h2), 2, 2)
        sg = QLinearGradient(0, stripe_y, 0, stripe_y + stripe_h2)
        sc0 = QColor(stripe_color); sc0.setAlpha(0)
        base_alpha = 0.55 if unlocked else (0.25 if not secret else 0.2)
        sc1 = QColor(stripe_color); sc1.setAlpha(int(220 * max(t, base_alpha)))
        sc2 = QColor(stripe_color); sc2.setAlpha(0)
        sg.setColorAt(0, sc0); sg.setColorAt(0.5, sc1); sg.setColorAt(1, sc2)
        p.fillPath(stripe_p, QBrush(sg))

        ICON_SIZE = 52
        ix, iy = 14, (h - ICON_SIZE) / 2
        hcx, hcy = ix + ICON_SIZE / 2, iy + ICON_SIZE / 2
        hex_path = self._hex_path(hcx, hcy, ICON_SIZE / 2)

        if t > 0.01:
            badge_r = int(self._tier_color.red()   * (1-t*0.6) + hov_c.red()   * t * 0.6)
            badge_g = int(self._tier_color.green() * (1-t*0.6) + hov_c.green() * t * 0.6)
            badge_b = int(self._tier_color.blue()  * (1-t*0.6) + hov_c.blue()  * t * 0.6)
            badge_col = QColor(badge_r, badge_g, badge_b)
        else:
            badge_col = self._tier_color

        if secret:
            badge_bg = QColor(DS.RED); badge_bg.setAlpha(int(18 + 28 * t))
        else:
            badge_bg = QColor(badge_col); badge_bg.setAlpha(int(25 + 45 * (t if unlocked else t * 0.6)))
        p.fillPath(hex_path, QBrush(badge_bg))

        hex_pen_c = QColor(badge_col if not secret else DS.RED)
        hex_pen_c.setAlpha(int((80 if not unlocked else 160) + 60 * t))
        p.setPen(QPen(hex_pen_c, 1.5, Qt.DashLine if secret else Qt.SolidLine))
        p.setBrush(Qt.NoBrush)
        p.drawPath(hex_path)

        if secret:
            p.setOpacity(0.55 + 0.35 * t)
            p.setFont(QFont("Segoe UI Emoji", 20))
            p.setPen(QColor(DS.RED))
            p.drawText(QRectF(ix, iy, ICON_SIZE, ICON_SIZE), Qt.AlignCenter, "🔒")
            p.setOpacity(1.0)
        elif self._pixmap:
            p.setOpacity(1.0 if unlocked else (0.3 + 0.35 * t))
            p.drawPixmap(int(ix + (ICON_SIZE - 38) / 2),
                         int(iy + (ICON_SIZE - 38) / 2), self._pixmap)
            p.setOpacity(1.0)
        else:
            p.setOpacity(1.0 if unlocked else (0.3 + 0.35 * t))
            p.setFont(QFont("Segoe UI Emoji", 20))
            p.setPen(QColor(DS.TEXT_PRIMARY))
            p.drawText(QRectF(ix, iy, ICON_SIZE, ICON_SIZE),
                       Qt.AlignCenter, "🏆" if unlocked else "❓")
            p.setOpacity(1.0)

        tx, tw = ix + ICON_SIZE + 14, w - (ix + ICON_SIZE + 14) - 12

        _raw_name = ach.get("name", "")
        name_text = (self._tm.translate_text(_raw_name)
                     if isinstance(_raw_name, str)
                     else (_raw_name.get(self.language) or _raw_name.get("fr", "?")))
        if secret:
            name_text = "???"

        if secret:
            nr, ng, nb = DS.RED[1:3], DS.RED[3:5], DS.RED[5:7]
            name_c = QColor(int(nr,16), int(ng,16), int(nb,16), int(180 + 75*t))
        elif unlocked:
            nc_r = int(self._tier_color.red()   * (1 - t*0.5) + hov_c.red()   * t * 0.5)
            nc_g = int(self._tier_color.green() * (1 - t*0.5) + hov_c.green() * t * 0.5)
            nc_b = int(self._tier_color.blue()  * (1 - t*0.5) + hov_c.blue()  * t * 0.5)
            name_c = QColor(nc_r, nc_g, nc_b)
            name_c = name_c.lighter(100 + int(15 * t))
        else:
            base = QColor(DS.TEXT_PRIMARY)
            name_c = QColor(
                int(base.red()   * (1 - t*0.3) + cat_c.red()   * t * 0.3),
                int(base.green() * (1 - t*0.3) + cat_c.green() * t * 0.3),
                int(base.blue()  * (1 - t*0.3) + cat_c.blue()  * t * 0.3),
                int(160 + 95 * t))

        p.setPen(name_c)
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.drawText(QRectF(tx, 10, tw - 80, 22), Qt.AlignVCenter | Qt.AlignLeft, name_text)

        xp      = ach.get("reward_xp", 0)
        xp_text = f"+{xp} XP" if not secret else "? XP"
        xp_c    = QColor(DS.RED if secret else (DS.GOLD if unlocked else DS.TEXT_MUTED))
        xp_c.setAlpha(int(130 + 125 * max(t, 0.3 if unlocked else 0)))
        p.setPen(xp_c)
        p.setFont(QFont("Segoe UI", 8, QFont.Bold))
        p.drawText(QRectF(w - 80, 12, 68, 20), Qt.AlignVCenter | Qt.AlignRight, xp_text)

        if not secret and self.tier_data and self.category_data:
            _tn = self.tier_data.get("name", "")
            tier_name = (self._tm.translate_text(_tn) if isinstance(_tn, str)
                         else _tn.get(self.language, ""))
            _cn = self.category_data.get("name", "")
            cat_name  = (self._tm.translate_text(_cn) if isinstance(_cn, str)
                         else _cn.get(self.language, ""))
            pill_text = f"{tier_name}  ·  {cat_name}" if tier_name and cat_name else tier_name
            if unlocked:
                if DS.is_dark:
                    pc = QColor(self._tier_color).lighter(int(110 + 25 * t))
                else:
                    base_pc = QColor(self._tier_color)
                    h2, s2, v2, a2 = base_pc.getHsvF()
                    v2 = min(v2, 0.72 - 0.08 * t)
                    s2 = min(s2 + 0.10 * t, 1.0)
                    pc = QColor.fromHsvF(h2, s2, v2, a2)
            else:
                base_muted = QColor(DS.TEXT_SECONDARY if not DS.is_dark else DS.TEXT_MUTED)
                pc = QColor(
                    int(base_muted.red()   * (1-t) + cat_c.red()   * t),
                    int(base_muted.green() * (1-t) + cat_c.green() * t),
                    int(base_muted.blue()  * (1-t) + cat_c.blue()  * t),
                    int(170 + 85 * t))
            p.setPen(pc)
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(QRectF(tx, 34, tw, 16), Qt.AlignVCenter | Qt.AlignLeft, pill_text)
        elif secret:
            sc3 = QColor(DS.TEXT_MUTED); sc3.setAlpha(int(100 + 80 * t))
            p.setPen(sc3)
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(QRectF(tx, 34, tw, 16), Qt.AlignVCenter | Qt.AlignLeft, "??? · ???")

        _raw_desc = ach.get("description", "")
        desc = (self._tm.translate_text(_raw_desc)
                if isinstance(_raw_desc, str)
                else (_raw_desc.get(self.language) or _raw_desc.get("fr", "")))
        if secret:
            desc = self._tm.translate_text("secret_achievement_desc") if hasattr(self, "_tm") else "Ce succès est encore secret. Continuez à explorer..."

        dc = QColor(DS.TEXT_MUTED if secret else DS.TEXT_SECONDARY)
        if not secret and t > 0:
            dc = QColor(
                int(dc.red()   * (1-t*0.25) + hov_c.red()   * t * 0.25),
                int(dc.green() * (1-t*0.25) + hov_c.green() * t * 0.25),
                int(dc.blue()  * (1-t*0.25) + hov_c.blue()  * t * 0.25))
        p.setPen(dc)
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(QRectF(tx, 53, tw, 32),
                   Qt.AlignTop | Qt.AlignLeft | Qt.TextWordWrap, desc)

        if not unlocked and not secret:
            cur  = ach.get("progress", 0)
            req  = ach.get("requirement", {}).get("value", 1)
            frac = min(cur / max(req, 1), 1.0)
            bar_y, bar_w = h - 22, tw

            track_c = QColor(DS.BG_RAISED)
            if t > 0:
                track_c = QColor(
                    int(track_c.red()   * (1-t*0.4) + cat_c.red()   * t * 0.4),
                    int(track_c.green() * (1-t*0.4) + cat_c.green() * t * 0.4),
                    int(track_c.blue()  * (1-t*0.4) + cat_c.blue()  * t * 0.4))
            p.setPen(Qt.NoPen)
            p.setBrush(track_c)
            p.drawRoundedRect(QRectF(tx, bar_y, bar_w, 5), 2.5, 2.5)

            if frac > 0:
                bar_color = (QColor("#F85149") if frac < 0.33
                             else QColor("#F0A030") if frac < 0.66
                             else QColor("#3FB950"))
                if t > 0:
                    bar_color = QColor(
                        int(bar_color.red()   * (1-t*0.5) + cat_c.red()   * t * 0.5),
                        int(bar_color.green() * (1-t*0.5) + cat_c.green() * t * 0.5),
                        int(bar_color.blue()  * (1-t*0.5) + cat_c.blue()  * t * 0.5))
                p.setBrush(bar_color)
                p.drawRoundedRect(QRectF(tx, bar_y, max(6, bar_w * frac), 5), 2.5, 2.5)

            prog_c = QColor(DS.TEXT_MUTED if t < 0.4 else DS.TEXT_SECONDARY)
            p.setPen(prog_c)
            p.setFont(QFont("Segoe UI", 7))
            p.drawText(QRectF(tx, bar_y - 13, bar_w, 12),
                       Qt.AlignVCenter | Qt.AlignRight,
                       f"{cur:.0f} / {req:.0f}")

        p.setFont(QFont("Segoe UI", 8, QFont.Bold))
        if unlocked:
            badge_text = "✓ Unlocked"
            if ach.get("unlock_date"):
                try:
                    d = datetime.fromisoformat(ach["unlock_date"])
                    badge_text = "✓  " + d.strftime("%d/%m/%Y")
                except Exception:
                    pass
            gc3 = QColor(DS.GREEN); gc3.setAlpha(int(170 + 85 * t))
            p.setPen(gc3)
            p.drawText(QRectF(0, h - 20, w - 12, 14),
                       Qt.AlignVCenter | Qt.AlignRight, badge_text)
        elif secret:
            sc4 = QColor(DS.RED); sc4.setAlpha(int(120 + 90 * t))
            p.setPen(sc4)
            p.drawText(QRectF(0, h - 20, w - 12, 14),
                       Qt.AlignVCenter | Qt.AlignRight, "✦  SECRET  ✦")

        p.end()


class NavPill(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setFixedHeight(34)
        self.setMinimumWidth(120)
        self._update_style()

    def _update_style(self):
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {DS.GOLD_DIM}, stop:1 #5A4A10);
                    color: {DS.GOLD_BRIGHT};
                    border: 1px solid {DS.GOLD};
                    border-radius: 17px;
                    font-weight: bold;
                    font-size: 11px;
                    padding: 0 18px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {DS.BG_RAISED};
                    color: {DS.TEXT_SECONDARY};
                    border: 1px solid {DS.BORDER};
                    border-radius: 17px;
                    font-size: 11px;
                    padding: 0 18px;
                }}
                QPushButton:hover {{
                    background: {DS.BG_INPUT};
                    color: {DS.TEXT_PRIMARY};
                    border-color: {DS.BORDER_LIGHT};
                }}
            """)

    def nextCheckState(self):
        if not self.isChecked():
            self.setChecked(True)

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._update_style()

#  RANK BADGE WIDGET - tier-aware evolving animation

_RANK_ANIM_MAP = {
    # FR names
    "débutant":    0,   # Rookie    — heartbeat
    "initié":      1,   # Initiate  — double-beat
    "adepte":      1,   # Adept     — double-beat
    "vétéran":     2,   # Veteran   — shimmer arc
    "élite":       2,   # Elite     — shimmer arc
    "maître":      3,   # Master    — shimmer + 1 orbit
    "grand maître":4,   # GrandMstr — plasma 3 orbits
    "légendaire":  4,   # Legendary — plasma 3 orbits
    "mythique":    4,   # Mythic    — plasma 3 orbits (max)
    # EN names
    "rookie":      0,
    "initiate":    1,
    "adept":       1,
    "veteran":     2,
    "elite":       2,
    "champion":    3,
    "master":      3,
    "grand master":4,
    "legendary":   4,
    "mythic":      4,
}

class RankBadgeWidget(QWidget):
    """
    Rank badge with tier-aware evolving animation.

    Animation scales with rank tier:
      bronze   — slow heartbeat glow pulse
      silver   — double-beat pulse (lub-dub)
      gold     — sweeping shimmer arc around the badge
      platinum — one orbiting satellite dot + shimmer arc
      diamond  — plasma: three orbiting dots at different speeds + arc
    """

    def __init__(self, rank_name: str, rank_color: str,
                 icon_path: str = "", parent=None):
        super().__init__(parent)
        self.rank_name  = rank_name
        self.rank_color = QColor(rank_color)
        self.icon_path  = icon_path
        self._pixmap: Optional[QPixmap] = None
        self._phase  = 0.0
        self._phase2 = 0.0
        self._phase3 = 0.0
        self._anim_level = self._resolve_anim_level(rank_name)
        self._load_icon(icon_path)
        self.setFixedHeight(36)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._calc_width()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(20)

    def _resolve_anim_level(self, rank_name: str) -> int:
        key = rank_name.lower().strip()
        level = _RANK_ANIM_MAP.get(key, None)
        if level is None:
            for k, lv in _RANK_ANIM_MAP.items():
                if k in key:
                    level = lv
                    break
        return level if level is not None else 0

    def _load_icon(self, icon_path: str):
        self._pixmap = None
        if icon_path and os.path.exists(icon_path):
            px = QPixmap(icon_path)
            if not px.isNull():
                self._pixmap = px.scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def _tick(self):
        speeds = [0.025, 0.04, 0.055, 0.07, 0.09]
        sp = speeds[self._anim_level]
        self._phase  = (self._phase  + sp)            % (2 * math.pi)
        self._phase2 = (self._phase2 + sp * 0.73)     % (2 * math.pi)
        self._phase3 = (self._phase3 + sp * 0.47)     % (2 * math.pi)
        self.update()

    def _calc_width(self):
        fm = QFontMetrics(QFont("Segoe UI", 11, QFont.Bold))
        extra = 20 if self._anim_level >= 3 else 0
        self.setFixedWidth(fm.horizontalAdvance(self.rank_name) + 60 + extra)

    def update_rank(self, rank_name: str, rank_color: str, icon_path: str = ""):
        self.rank_name   = rank_name
        self.rank_color  = QColor(rank_color)
        self._anim_level = self._resolve_anim_level(rank_name)
        self._load_icon(icon_path)
        self._calc_width()
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h   = self.width(), self.height()
        cx, cy = w / 2, h / 2
        lv     = self._anim_level
        rc     = self.rank_color

        # 1. Outer animation layer (behind badge)
        if lv == 0:
            # Bronze: single slow heartbeat
            pulse_a = int(18 + 14 * math.sin(self._phase))
        elif lv == 1:
            # Silver: double beat  (lub-dub: sin + 0.5*sin(2x))
            raw = math.sin(self._phase) + 0.5 * math.sin(2 * self._phase)
            pulse_a = int(20 + 16 * (raw / 1.5))
        elif lv == 2:
            # Gold: faster pulse + shimmer arc (drawn below)
            pulse_a = int(22 + 20 * math.sin(self._phase))
        else:
            # Platinum / Diamond: strong pulse
            pulse_a = int(28 + 24 * math.sin(self._phase))

        pulse_a = max(0, min(255, pulse_a))
        glow_c  = QColor(rc); glow_c.setAlpha(pulse_a)
        p.setPen(QPen(glow_c, 5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), h / 2, h / 2)

        # Shimmer arc
        if lv >= 2:
            arc_rect = QRectF(3, 3, w - 6, h - 6)
            arc_start  = int(self._phase * 180 / math.pi * 16) % (360 * 16)
            arc_span   = int(120 * 16)

            arc_c = QColor(rc).lighter(160)
            arc_c.setAlpha(int(55 + 35 * math.sin(self._phase)))
            p.setPen(QPen(arc_c, 2.5, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(arc_rect, arc_start, arc_span)

            # Second arc offset by 180° for diamond
            if lv >= 4:
                arc_c2 = QColor.fromHsvF(
                    (self.rank_color.hsvHueF() + 0.33) % 1.0, 0.8, 1.0)
                arc_c2.setAlpha(int(45 + 30 * math.sin(self._phase2)))
                p.setPen(QPen(arc_c2, 2.0, Qt.SolidLine, Qt.RoundCap))
                p.drawArc(arc_rect, arc_start + 180 * 16, arc_span)

        # Orbiting satellite dots
        if lv >= 3:
            orbit_r = h * 0.58
            dot_r   = 3.0 if lv == 3 else 2.5

            def _draw_dot(phase_val: float, hue_shift: float, alpha_extra: int):
                dx = cx + orbit_r * math.cos(phase_val)
                dy = cy + orbit_r * math.sin(phase_val)
                # Tail (faded trail)
                for step_back in range(1, 5):
                    tb_phase = phase_val - step_back * 0.18
                    tx_ = cx + orbit_r * math.cos(tb_phase)
                    ty_ = cy + orbit_r * math.sin(tb_phase)
                    trail_c = QColor(rc)
                    trail_c.setAlpha(max(0, int((5 - step_back) * 14) - 10))
                    p.setPen(Qt.NoPen)
                    p.setBrush(trail_c)
                    p.drawEllipse(QPointF(tx_, ty_), dot_r * 0.55, dot_r * 0.55)
                # Dot
                if lv >= 4 and hue_shift != 0:
                    dot_c = QColor.fromHsvF(
                        (rc.hsvHueF() + hue_shift) % 1.0, 0.85, 1.0)
                else:
                    dot_c = QColor(rc).lighter(170)
                dot_c.setAlpha(200 + alpha_extra)
                p.setPen(Qt.NoPen)
                p.setBrush(dot_c)
                p.drawEllipse(QPointF(dx, dy), dot_r, dot_r)

            _draw_dot(self._phase,  0.0,   0)
            if lv >= 4:
                _draw_dot(self._phase2, 0.33, -20)
                _draw_dot(self._phase3, 0.66, -40)

        # 2. Badge background pill
        bg = QColor(rc)
        bg.setAlpha(22)
        p.setPen(QPen(QColor(rc).lighter(140), 1.2))
        p.setBrush(bg)
        p.drawRoundedRect(QRectF(0, 0, w, h), h / 2, h / 2)

        if self._pixmap:
            p.drawPixmap(8, (h - 22) // 2, self._pixmap)
            text_x = 36
        else:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(rc))
            p.drawEllipse(QRectF(8, (h - 10) / 2, 10, 10))
            text_x = 26

        p.setPen(rc)
        p.setFont(QFont("Segoe UI", 11, QFont.Bold))
        p.drawText(QRectF(text_x, 0, w - text_x - 8, h),
                   Qt.AlignVCenter | Qt.AlignLeft, self.rank_name)
        p.end()


class AchievementsUI(TranslationMixin, QDialog):
    """Achievements interface — premium luxury HUD redesign."""

    def __init__(self, achievement_system, parent=None, language="fr"):
        super().__init__(parent)
        self.achievement_system = achievement_system
        self.current_language   = language
        self._tm = TranslationManager(); self._tm.set_language(language)

        dark = getattr(parent, "dark_mode", True) if parent else True
        if dark:
            DS.use_dark()
        else:
            DS.use_light()

        self.setWindowTitle(self.T("🏆 Succès & Trophées"))
        self.setMinimumSize(920, 720)
        self.resize(980, 760)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self._apply_global_style()
        self.setup_ui()

        self.show()
        QApplication.processEvents()
        self.load_achievements()

    def apply_theme(self, dark_mode: bool):
        if dark_mode:
            DS.use_dark()
        else:
            DS.use_light()

        self._apply_global_style()
        self._refresh_header()

        for pill in self._nav_pills:
            pill._update_style()

        self._refresh_footer()

        if hasattr(self, "_xp_ring"):
            self._xp_ring.update()
        if hasattr(self, "_rank_badge"):
            self._rank_badge.update()

        if hasattr(self, "_cards_layout"):
            self.load_achievements_list()

        if hasattr(self, "_global_bar"):
            self._global_bar.update()

        if hasattr(self, "_stat_bars"):
            for bar in self._stat_bars:
                bar.update()

        self._update_secrets_btn_style()
        self.update()

    # Translations
    def T(self, key: str) -> str:
        return self._tm.translate_text(key)

    def _apply_global_style(self):
        self.setStyleSheet(f"""
            QDialog, QWidget {{
                background-color: {DS.BG_BASE};
                color: {DS.TEXT_PRIMARY};
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: {DS.BG_SURFACE};
                width: 6px;
                border-radius: 3px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {DS.BORDER_LIGHT};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar:horizontal {{
                background: {DS.BG_SURFACE};
                height: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:horizontal {{
                background: {DS.BORDER_LIGHT};
                border-radius: 3px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
            QLineEdit {{
                background: {DS.BG_INPUT};
                color: {DS.TEXT_PRIMARY};
                border: 1px solid {DS.BORDER};
                border-radius: 7px;
                padding: 6px 10px;
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border-color: {DS.GOLD_DIM};
            }}
            QComboBox {{
                background: {DS.BG_INPUT};
                color: {DS.TEXT_PRIMARY};
                border: 1px solid {DS.BORDER};
                border-radius: 7px;
                padding: 5px 10px;
                font-size: 11px;
                min-width: 110px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background: {DS.BG_RAISED};
                color: {DS.TEXT_PRIMARY};
                selection-background-color: {DS.GOLD_DIM};
                border: 1px solid {DS.BORDER};
            }}
            QTreeWidget {{
                background: {DS.BG_SURFACE};
                color: {DS.TEXT_PRIMARY};
                border: 1px solid {DS.BORDER};
                border-radius: 8px;
                alternate-background-color: {DS.BG_RAISED};
                outline: none;
                font-size: 11px;
            }}
            QTreeWidget::item {{ padding: 5px 4px; }}
            QTreeWidget::item:hover {{
                background: {"#2A2410" if DS.is_dark else "#F0E8D0"};
                color: {DS.GOLD_BRIGHT if DS.is_dark else "#5A4A10"};
            }}
            QTreeWidget::item:selected {{
                background: {"#3A3010" if DS.is_dark else "#E8D888"};
                color: {DS.GOLD_BRIGHT if DS.is_dark else "#3A2A00"};
            }}
            QHeaderView::section {{
                background: {DS.BG_RAISED};
                color: {DS.TEXT_SECONDARY};
                border: none;
                border-bottom: 1px solid {DS.BORDER};
                padding: 6px 8px;
                font-size: 10px;
                font-weight: bold;
            }}
            QLabel {{ color: {DS.TEXT_PRIMARY}; background: transparent; }}
            QGroupBox {{
                color: {DS.TEXT_SECONDARY};
                border: 1px solid {DS.BORDER};
                border-radius: {DS.RADIUS}px;
                margin-top: 10px;
                padding-top: 10px;
                font-size: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                top: -2px;
                padding: 0 6px;
                background: {DS.BG_BASE};
                color: {DS.TEXT_SECONDARY};
                font-size: 10px;
                letter-spacing: 1px;
            }}
            QFrame {{
                background-color: transparent;
            }}
        """)

    def _global_bar_stylesheet(self) -> str:
        """Kept for legacy compat (get_progress_bar_style uses it)."""
        return f"""
            QProgressBar {{
                border-radius: 6px;
                background: {DS.BG_RAISED};
                border: none;
                text-align: center;
                font-size: 8px;
                color: {DS.TEXT_MUTED};
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {DS.GOLD_DIM}, stop:1 {DS.GOLD});
                border-radius: 6px;
            }}
        """

    def _progress_lbl_html(self, unlocked: int, total: int) -> str:
        return (
            f"<span style='font-size:22px; font-weight:bold; color:{DS.TEXT_PRIMARY}'>"
            f"{unlocked}</span>"
            f"<span style='font-size:14px; color:{DS.TEXT_SECONDARY}'>"
            f" / {total}  {self.T('Succès débloqués')}</span>"
        )

    def _refresh_header(self):
        if not hasattr(self, "_header_frame"):
            return
        self._header_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {DS.BG_SURFACE},
                    stop:0.5 {"#1A2035" if DS.is_dark else "#F0EBE0"},
                    stop:1 {DS.BG_SURFACE});
                border: 1px solid {DS.BORDER};
                border-radius: {DS.RADIUS}px;
            }}
        """)
        if hasattr(self, "_header_title"):
            self._header_title.setStyleSheet(
                f"font-size:20px; font-weight:bold; color:{DS.GOLD}; background:transparent;")
        if hasattr(self, "_header_chips"):
            colors = [DS.GREEN, DS.GOLD]
            for chip, color in zip(self._header_chips, colors):
                chip.setStyleSheet(f"""
                    background: transparent;
                    color: {color};
                    font-size: 11px;
                    font-weight: bold;
                    padding: 4px 12px;
                    border: 1px solid {color};
                    border-radius: 12px;
                """)

    def _refresh_footer(self):
        if hasattr(self, "_close_btn"):
            self._close_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {DS.RED_DIM};
                    color: {DS.RED};
                    border: 1px solid {DS.RED};
                    border-radius: {DS.RADIUS_S}px;
                    font-weight: bold;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background: {DS.RED};
                    color: {"white" if DS.is_dark else "#1C1A16"};
                }}
            """)

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(DS.PAD, DS.PAD, DS.PAD, DS.PAD)
        root.setSpacing(12)

        root.addWidget(self._build_header())

        nav_row = QHBoxLayout()
        nav_row.setSpacing(8)

        self._nav_pills = []
        nav_labels = [
            self.T("Vue d'ensemble"),
            self.T("Liste des succès"),
            self.T("Statistiques"),
        ]
        for i, lbl in enumerate(nav_labels):
            pill = NavPill(lbl)
            pill.setChecked(i == 0)
            idx = i
            pill.clicked.connect(lambda _, ix=idx: self._switch_tab(ix))
            nav_row.addWidget(pill)
            self._nav_pills.append(pill)
        nav_row.addStretch()

        root.addLayout(nav_row)

        self.stack = QStackedWidget()

        self.overview_tab = self._build_overview_tab()
        self.list_tab     = self._build_list_tab()
        self.stats_tab    = self._build_stats_tab()

        self.stack.addWidget(self.overview_tab)
        self.stack.addWidget(self.list_tab)
        self.stack.addWidget(self.stats_tab)

        root.addWidget(self.stack, 1)
        root.addWidget(self._build_footer())

    def _build_header(self) -> QWidget:
        w = QFrame()
        self._header_frame = w
        w.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {DS.BG_SURFACE},
                    stop:0.5 {"#1A2035" if DS.is_dark else "#F0EBE0"},
                    stop:1 {DS.BG_SURFACE});
                border: 1px solid {DS.BORDER};
                border-radius: {DS.RADIUS}px;
            }}
        """)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(DS.PAD, DS.PAD_S, DS.PAD, DS.PAD_S)

        title = QLabel(self.T("🏆 Succès & Trophées"))
        title.setStyleSheet(f"""
            font-size: 20px; font-weight: bold;
            color: {DS.GOLD};
            background: transparent;
        """)
        self._header_title = title
        lay.addWidget(title)
        lay.addStretch()

        ach_sys  = self.achievement_system
        unlocked = ach_sys.get_unlocked_count()
        total    = len(ach_sys.get_all_achievements())
        xp       = ach_sys.get_total_xp()

        self._header_chips = []
        for chip_text, chip_color in [
            (f"{unlocked}/{total}  {self.T('Succès débloqués')}", DS.GREEN),
            (f"{xp}  {self.T('XP')}", DS.GOLD),
        ]:
            chip = QLabel(chip_text)
            chip.setStyleSheet(f"""
                background: transparent;
                color: {chip_color};
                font-size: 11px;
                font-weight: bold;
                padding: 4px 12px;
                border: 1px solid {chip_color};
                border-radius: 12px;
            """)
            lay.addWidget(chip)
            lay.addSpacing(6)
            self._header_chips.append(chip)
        return w

    def _build_footer(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addStretch()

        btn = QPushButton(self.T("Fermer"))
        btn.setFixedSize(110, 36)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {DS.RED_DIM};
                color: {DS.RED};
                border: 1px solid {DS.RED};
                border-radius: {DS.RADIUS_S}px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {DS.RED};
                color: {"white" if DS.is_dark else "#1C1A16"};
            }}
        """)
        btn.clicked.connect(self.close)
        self._close_btn = btn
        lay.addWidget(btn)
        return w

    def _switch_tab(self, index: int):
        for i, pill in enumerate(self._nav_pills):
            pill.setChecked(i == index)
        self.stack.setCurrentIndex(index)

    def _build_overview_tab(self) -> QWidget:
        page = QWidget()
        lay  = QVBoxLayout(page)
        lay.setContentsMargins(0, 8, 0, 0)
        lay.setSpacing(12)

        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        total_xp = self.achievement_system.get_total_xp()
        max_xp   = self.achievement_system.get_max_xp() if hasattr(
            self.achievement_system, "get_max_xp") else sum(
            a.get("reward_xp", 0)
            for a in self.achievement_system.get_all_achievements().values())
        self._max_xp = max(max_xp, 1)
        self._xp_ring = XPRingWidget(total_xp, self._max_xp)
        top_row.addWidget(self._xp_ring)

        info_col = QVBoxLayout()
        info_col.setSpacing(10)

        unlocked = self.achievement_system.get_unlocked_count()
        total = len(self.achievement_system.get_all_achievements())
        pct = self.achievement_system.get_progress_percentage()

        self._progress_lbl = QLabel()
        self._progress_lbl.setTextFormat(Qt.RichText)
        self._progress_lbl.setText(self._progress_lbl_html(unlocked, total))
        info_col.addWidget(self._progress_lbl)

        self._global_bar = GlobalProgressBar(int(pct), 100)
        info_col.addWidget(self._global_bar)

        rank_idx, rank_fr, rank_color = self.achievement_system.get_current_rank()
        rank_name = self.T(rank_fr)
        rank_key  = self.achievement_system.ranks[rank_idx][0].lower().replace(" ", "_")
        icon_path = self.achievement_system.get_achievement_icon_path(f"{rank_key}.png")

        rank_row = QHBoxLayout()
        rank_lbl = QLabel(f"{self.T('Rang')}:")
        rank_lbl.setStyleSheet(f"color:{DS.TEXT_SECONDARY}; font-size:11px; background:transparent;")
        rank_row.addWidget(rank_lbl)

        self._rank_badge = RankBadgeWidget(rank_name, rank_color, icon_path)
        rank_row.addWidget(self._rank_badge)
        rank_row.addStretch()
        info_col.addLayout(rank_row)
        info_col.addStretch()

        top_row.addLayout(info_col, 1)
        lay.addLayout(top_row)

        # Category tree
        cat_group = QGroupBox(self.T("Catégories").upper())
        cat_lay   = QVBoxLayout(cat_group)
        cat_lay.setContentsMargins(DS.PAD_S, DS.PAD_S, DS.PAD_S, DS.PAD_S)

        self._category_tree = QTreeWidget()
        self._category_tree.setHeaderLabels([
            self.T("Catégorie"), self.T("Progression")])
        self._category_tree.setColumnWidth(0, 200)
        self._category_tree.setAlternatingRowColors(True)
        self._category_tree.setRootIsDecorated(False)
        cat_lay.addWidget(self._category_tree)
        lay.addWidget(cat_group, 1)

        return page

    def _build_list_tab(self) -> QWidget:
        page = QWidget()
        lay  = QVBoxLayout(page)
        lay.setContentsMargins(0, 8, 0, 0)
        lay.setSpacing(10)

        lay.addWidget(self._build_filter_bar())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._cards_container = QWidget()
        self._cards_layout = QGridLayout(self._cards_container)
        self._cards_layout.setSpacing(10)
        self._cards_layout.setContentsMargins(2, 2, 2, 2)

        self._skeleton_lbl = QLabel(f"⏳  {self.T('Chargement des succès...')}")
        self._skeleton_lbl.setAlignment(Qt.AlignCenter)
        self._skeleton_lbl.setStyleSheet(
            f"color: {DS.TEXT_MUTED}; font-size: 14px; padding: 40px;")
        self._cards_layout.addWidget(self._skeleton_lbl, 0, 0, 1, 2)

        scroll.setWidget(self._cards_container)
        lay.addWidget(scroll, 1)
        return page

    def _build_filter_bar(self) -> QWidget:
        bar = QFrame()
        bar.setFixedHeight(46)
        bar.setStyleSheet(f"""
            QFrame {{
                background: {DS.BG_SURFACE};
                border: 1px solid {DS.BORDER};
                border-radius: {DS.RADIUS_S}px;
            }}
        """)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(10, 0, 10, 0)
        lay.setSpacing(8)

        self.category_filter = QComboBox()
        self.category_filter.addItem(self.T("Toutes les catégories"))
        self.category_filter.currentIndexChanged.connect(self.filter_achievements)

        self.tier_filter = QComboBox()
        self.tier_filter.addItem(self.T("Tous les tiers"))
        self.tier_filter.currentIndexChanged.connect(self.filter_achievements)

        self.status_filter = QComboBox()
        self.status_filter.addItem(self.T("Tous les statuts"),   "all")
        self.status_filter.addItem(self.T("✅ Débloqués"),        "unlocked")
        self.status_filter.addItem(self.T("🔒 Verrouillés"),     "locked")
        self.status_filter.currentIndexChanged.connect(self.filter_achievements)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.T("Rechercher"))
        self.search_input.setFixedWidth(180)
        self.search_input.textChanged.connect(self.filter_achievements)

        self.show_secrets_check = QPushButton(self.T("Afficher les secrets"))
        self.show_secrets_check.setCheckable(True)
        self.show_secrets_check.setFixedHeight(28)
        self._update_secrets_btn_style()
        self.show_secrets_check.clicked.connect(self.filter_achievements)

        lay.addWidget(self.category_filter)
        lay.addWidget(self.tier_filter)
        lay.addWidget(self.status_filter)
        lay.addWidget(self.search_input)
        lay.addStretch()
        lay.addWidget(self.show_secrets_check)
        return bar

    def _update_secrets_btn_style(self):
        if not hasattr(self, "show_secrets_check"):
            return
        self.show_secrets_check.setStyleSheet(f"""
            QPushButton {{
                background: {DS.BG_INPUT};
                color: {DS.TEXT_SECONDARY};
                border: 1px solid {DS.BORDER};
                border-radius: 14px;
                font-size: 10px;
                padding: 0 12px;
            }}
            QPushButton:checked {{
                background: {DS.RED_DIM};
                color: {DS.RED};
                border-color: {DS.RED};
            }}
            QPushButton:hover:!checked {{
                border-color: {DS.BORDER_LIGHT};
                color: {DS.TEXT_PRIMARY};
            }}
        """)

    def _build_stats_tab(self) -> QWidget:
        page   = QWidget()
        lay    = QVBoxLayout(page)
        lay.setContentsMargins(0, 8, 0, 0)
        lay.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        inner   = QWidget()
        inn_lay = QVBoxLayout(inner)
        inn_lay.setContentsMargins(DS.PAD_S, DS.PAD_S, DS.PAD_S, DS.PAD_S)
        inn_lay.setSpacing(4)

        group = QGroupBox(self.T("Statistiques détaillées").upper())
        g_lay = QVBoxLayout(group)
        g_lay.setSpacing(2)
        g_lay.setContentsMargins(DS.PAD, DS.PAD, DS.PAD, DS.PAD)

        stats = self.achievement_system.stats

        self._stat_defs = [
            (self.T("Conversions totales"),    "total_conversions",    DS.BLUE),
            (self.T("Images converties en PDF"), "images_to_pdf",      DS.PURPLE),
            (self.T("Conversions Word/PDF"),   "word_pdf_conversions", DS.GOLD),
            (self.T("PDF protégés"),           "pdf_protected",        DS.GREEN),
            (self.T("Archives créées"),        "archives_created",     "#FF9F43"),
            (self.T("Aperçus utilisés"),       "previews_used",        DS.BLUE),
            (self.T("Minutes mode sombre"),    "dark_mode_minutes",    "#6C8EBF"),
            (self.T("Pages OCR"),              "ocr_pages",            DS.PURPLE),
            (self.T("Go compressés"),          "compressed_gb",        DS.GREEN),
            (self.T("Succès consécutifs"),     "consecutive_success",  DS.GOLD),
            (self.T("Jours uniques"),          "unique_days",          DS.BLUE),
        ]

        raw_vals = []
        for _, key, _ in self._stat_defs:
            v = stats.get(key, 0)
            try:
                raw_vals.append(float(v))
            except Exception:
                raw_vals.append(0.0)
        max_v = max(raw_vals) if raw_vals else 1.0
        if max_v == 0:
            max_v = 1.0

        self._stat_bars = []
        for i, (label, key, color) in enumerate(self._stat_defs):
            raw = stats.get(key, 0)

            if key == "dark_mode_minutes":
                v = float(raw)
                display = f"{v:.1f} min  ({v/60:.1f} h)"
            elif key == "compressed_gb":
                mb = float(raw)
                if mb < 1024:
                    display = f"{mb:.2f} Go"
                elif mb < 1024 * 1024:
                    display = f"{mb/1024:.2f} Go"
                else:
                    display = f"{mb/(1024*1024):.2f} To"
            else:
                display = str(raw)

            try:
                frac = float(raw) / max_v
            except Exception:
                frac = 0.0

            bar = StatBarWidget(label, display, frac, color)
            g_lay.addWidget(bar)
            self._stat_bars.append(bar)

        inn_lay.addWidget(group)
        inn_lay.addStretch()
        scroll.setWidget(inner)
        lay.addWidget(scroll)
        return page

    # Data loading
    def refresh_stats_tab(self):
        """Refresh the statistics tab with current values without rebuilding it."""
        if not hasattr(self, '_stat_bars') or not hasattr(self, '_stat_defs'):
            return
        stats = self.achievement_system.stats
        raw_vals = [float(stats.get(key, 0)) for _, key, _ in self._stat_defs]
        max_v = max(raw_vals) if raw_vals else 1.0
        if max_v == 0:
            max_v = 1.0
        for bar, (_, key, _) in zip(self._stat_bars, self._stat_defs):
            raw = stats.get(key, 0)
            if key == "dark_mode_minutes":
                v = float(raw)
                display = f"{v:.1f} min  ({v/60:.1f} h)"
            elif key == "compressed_gb":
                mb = float(raw)
                if mb < 1024:
                    display = f"{mb:.2f} Go"
                elif mb < 1024 * 1024:
                    display = f"{mb/1024:.2f} Go"
                else:
                    display = f"{mb/(1024*1024):.2f} To"
            else:
                display = str(raw)
            try:
                frac = float(raw) / max_v
            except Exception:
                frac = 0.0
            bar.value    = display
            bar.fraction = max(0.0, min(1.0, frac))
            bar.update()

    def load_achievements(self):
        self._load_filters()
        self.load_overview()
        self.load_achievements_list()
        self.refresh_stats_tab()

    def _load_filters(self):
        categories = self.achievement_system.achievements_data["categories"]
        for cat_id, cat_data in categories.items():
            _n = cat_data["name"]
            name = (self.T(_n) if isinstance(_n, str)
                    else _n.get(self.current_language, _n.get("fr", "")))
            self.category_filter.addItem(name, cat_id)

        tiers = self.achievement_system.achievements_data["tiers"]
        for tier_id, tier_data in tiers.items():
            _n = tier_data["name"]
            name = (self.T(_n) if isinstance(_n, str)
                    else _n.get(self.current_language, _n.get("fr", "")))
            self.tier_filter.addItem(name, tier_id)

    def load_filters(self):
        self._load_filters()

    def load_overview(self):
        ach_sys  = self.achievement_system
        unlocked = ach_sys.get_unlocked_count()
        total    = len(ach_sys.get_all_achievements())
        pct      = ach_sys.get_progress_percentage()
        total_xp = ach_sys.get_total_xp()

        self._xp_ring.set_values(total_xp, self._max_xp)

        self._progress_lbl.setText(self._progress_lbl_html(unlocked, total))
        self._global_bar.setValue(int(pct))

        # Category tree
        self._category_tree.clear()
        for cat_id, cstats in ach_sys.get_category_stats().items():
            cat_data = ach_sys.get_category(cat_id)
            if cat_data:
                _n = cat_data["name"]
                name = (self.T(_n) if isinstance(_n, str)
                        else _n.get(self.current_language, _n.get("fr", "")))
                item = QTreeWidgetItem(self._category_tree)
                item.setText(0, name)
                item.setText(1, f"{cstats['unlocked']}/{cstats['total']}"
                                f"  ({cstats['percentage']:.0f}%)")
                if "color" in cat_data:
                    item.setForeground(0, QColor(cat_data["color"]))

        rank_idx, rank_fr, rank_color = ach_sys.get_current_rank()
        rank_name = self.T(rank_fr)
        rank_key  = ach_sys.ranks[rank_idx][0].lower().replace(" ", "_")
        icon_path = ach_sys.get_achievement_icon_path(f"{rank_key}.png")
        self._rank_badge.update_rank(rank_name, rank_color, icon_path)

    def load_achievements_list(self):
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if hasattr(self, "_skeleton_lbl") and self._skeleton_lbl is not None:
            self._skeleton_lbl = None
        achievements = self.achievement_system.get_all_achievements()
        filtered     = self._filter_achievements_list(achievements)

        row, col, max_cols = 0, 0, 2
        dark_mode = getattr(self.parent(), "dark_mode", True) if self.parent() else True

        for ach_id, ach in filtered.items():
            tier_data     = self.achievement_system.get_tier(ach["tier"])
            category_data = self.achievement_system.get_category(ach["category"])
            icon_path     = self.achievement_system.get_achievement_icon_path(ach["icon"])

            card = AchievementCard(
                achievement=ach,
                tier_data=tier_data,
                category_data=category_data,
                icon_path=icon_path,
                language=self.current_language,
                dark_mode=dark_mode,
            )
            self._cards_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        self._cards_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding),
            row + 1, 0, 1, max_cols)

    def _filter_achievements_list(self, achievements: dict) -> dict:
        cat_filter    = self.category_filter.currentData()
        tier_filter   = self.tier_filter.currentData()
        status_filter = self.status_filter.currentData() if hasattr(self, 'status_filter') else "all"
        search        = self.search_input.text().lower()
        show_sec      = self.show_secrets_check.isChecked()

        filtered = {}
        for aid, ach in achievements.items():
            if cat_filter and ach["category"] != cat_filter:
                continue
            if tier_filter and ach["tier"] != tier_filter:
                continue
            if status_filter == "unlocked" and not ach.get("unlocked", False):
                continue
            if status_filter == "locked" and ach.get("unlocked", False):
                continue
            if search:
                _rn = ach["name"]
                name = (self.T(_rn) if isinstance(_rn, str)
                        else _rn.get(self.current_language, _rn.get("fr", ""))).lower()
                _rd = ach["description"]
                desc = (self.T(_rd) if isinstance(_rd, str)
                        else _rd.get(self.current_language, _rd.get("fr", ""))).lower()
                if search not in name and search not in desc:
                    continue
            if ach["secret"] and not ach["unlocked"]:
                ach = dict(ach)
                if not show_sec:
                    ach["_hide_secret"] = True
            filtered[aid] = ach
        return filtered

    def filter_achievements(self):
        self.load_achievements_list()

    def filter_achievements_list(self, achievements: dict) -> dict:
        return self._filter_achievements_list(achievements)

    def create_achievement_widget(self, achievement: dict) -> QFrame:
        tier_data     = self.achievement_system.get_tier(achievement["tier"])
        category_data = self.achievement_system.get_category(achievement["category"])
        icon_path     = self.achievement_system.get_achievement_icon_path(achievement["icon"])
        dark_mode     = getattr(self.parent(), "dark_mode", True) if self.parent() else True
        return AchievementCard(
            achievement=achievement,
            tier_data=tier_data,
            category_data=category_data,
            icon_path=icon_path,
            language=self.current_language,
            dark_mode=dark_mode,
        )

    def get_progress_bar_style(self, progress: float, requirement_value: float) -> str:
        pct = (progress / max(requirement_value, 1)) * 100
        color = "#F85149" if pct < 33 else "#F0A030" if pct < 66 else "#3FB950"
        return f"""
            QProgressBar {{
                height: 6px; border-radius: 3px;
                border: 1px solid {DS.BORDER};
                background-color: {DS.BG_RAISED};
            }}
            QProgressBar::chunk {{ background-color: {color}; border-radius: 3px; }}
        """

    def create_overview_tab(self):  return self.overview_tab
    def create_list_tab(self):      return self.list_tab
    def create_stats_tab(self):     return self.stats_tab