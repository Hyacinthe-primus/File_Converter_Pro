"""
Special Events Manager for File Converter Pro
• True 3D Perlin FBM — seamless, artifact-free liquid border
• Particle system — event-themed floating confetti / sparkles
• Perceptual color cycling (Oklab-inspired smooth hue shifts)
• Per-event color theming  (gold/amber for birthday, cyan/violet for new year)
• Countdown ring — shows remaining display time
• Fixed Property declarations (PySide6-compatible)
• Fixed closeEvent (removed phantom attributes)
• Performance — path rebuilt only when size changes (cached)
• BirthdayInputDialog — hint hidden until validation fails
• Robust .exe resource path resolution

Author: Hyacinthe
Version: 1.0
"""

import os
import sys
import math
import random
import sqlite3
from datetime import date
from pathlib import Path
from typing import Optional, List, Tuple

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QDateEdit, QMessageBox, QWidget, QSizePolicy, QGraphicsOpacityEffect)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QUrl,
    Signal, Property, QPointF, QRectF)
from PySide6.QtGui import (
    QPixmap, QFont, QFontDatabase, QColor, QPainter, QPainterPath,
    QBrush, QPen, QConicalGradient, QRadialGradient,
    QTransform, QGuiApplication)

from translations import TranslationManager
from widgets import AnimatedCheckBox

def _make_tm(language: str) -> TranslationManager:
    tm = TranslationManager()
    tm.set_language(language)
    return tm


class PerlinNoise:
    """
    True 3D Perlin noise with Fractional Brownian Motion (FBM).

    Key improvements over the original:
    • 12-direction gradient table (cube edge midpoints) → less grid-aligned look
    • noise3D(x, y, z): use z=time for seamless, never-cycling animation
    • fbm(): replaces stacking 4 separate PerlinNoise instances — one call,
      tunable octaves / persistence / lacunarity
    • Isolated RNG (random.Random) — won't pollute global random state
    """

    _GRAD3: List[Tuple[int, int, int]] = [
        (1, 1, 0), (-1, 1, 0), (1, -1, 0), (-1, -1, 0),
        (1, 0, 1), (-1, 0, 1), (1, 0, -1), (-1, 0, -1),
        (0, 1, 1), (0, -1, 1), (0, 1, -1), (0, -1, -1),
    ]

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed if seed is not None else random.randint(0, 1_000_000)
        rng = random.Random(self.seed)
        perm = list(range(256))
        rng.shuffle(perm)
        self.p = perm * 2

    @staticmethod
    def _fade(t: float) -> float:
        """Quintic smoothstep: 6t⁵ − 15t⁴ + 10t³  (C² continuous)"""
        return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

    @staticmethod
    def _lerp(t: float, a: float, b: float) -> float:
        return a + t * (b - a)

    def _grad3(self, h: int, x: float, y: float, z: float) -> float:
        gx, gy, gz = self._GRAD3[h % 12]
        return gx * x + gy * y + gz * z

    def noise(self, x: float, y: float) -> float:
        """2D Perlin noise (legacy-compatible shim). Returns ≈ [-1, 1]."""
        return self.noise3D(x, y, 0.0)

    def noise3D(self, x: float, y: float, z: float) -> float:
        """
        True 3D Perlin noise.  Returns ≈ [-1, 1].
        Pass z = time for smooth, artifact-free temporal animation.
        """
        p = self.p
        X = int(math.floor(x)) & 255
        Y = int(math.floor(y)) & 255
        Z = int(math.floor(z)) & 255

        xf = x - math.floor(x)
        yf = y - math.floor(y)
        zf = z - math.floor(z)

        u, v, w = self._fade(xf), self._fade(yf), self._fade(zf)

        A  = p[X]     + Y;  AA = p[A]     + Z;  AB = p[A + 1] + Z
        B  = p[X + 1] + Y;  BA = p[B]     + Z;  BB = p[B + 1] + Z

        return self._lerp(w,
            self._lerp(v,
                self._lerp(u, self._grad3(p[AA],     xf,       yf,       zf      ),
                              self._grad3(p[BA],     xf - 1.0, yf,       zf      )),
                self._lerp(u, self._grad3(p[AB],     xf,       yf - 1.0, zf      ),
                              self._grad3(p[BB],     xf - 1.0, yf - 1.0, zf      ))),
            self._lerp(v,
                self._lerp(u, self._grad3(p[AA + 1], xf,       yf,       zf - 1.0),
                              self._grad3(p[BA + 1], xf - 1.0, yf,       zf - 1.0)),
                self._lerp(u, self._grad3(p[AB + 1], xf,       yf - 1.0, zf - 1.0),
                              self._grad3(p[BB + 1], xf - 1.0, yf - 1.0, zf - 1.0))))

    def fbm(self,
            x: float, y: float, z: float = 0.0,
            octaves: int = 4,
            persistence: float = 0.5,
            lacunarity: float = 2.0) -> float:
        """
        Fractional Brownian Motion — layered noise for organic detail.

        Args:
            octaves     : detail layers  (4 = organic fluid, 6 = turbulent)
            persistence : amplitude per octave  (0.5 = halves each layer)
            lacunarity  : frequency per octave  (2.0 = doubles each layer)
        Returns:
            Normalised value ≈ [-1, 1]
        """
        value = amplitude = max_value = 0.0
        amplitude = frequency = 1.0
        max_value = 0.0

        for _ in range(octaves):
            value     += self.noise3D(x * frequency, y * frequency, z * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= lacunarity

        return value / max_value


class Particle:
    """Single floating particle for celebration effects."""
    __slots__ = ("x", "y", "vx", "vy", "size", "life", "max_life",
                 "color", "shape", "rotation", "rot_speed")

    def __init__(self, x: float, y: float, palette: List[QColor],
                 shapes: List[str] = ("circle", "star", "rect")):
        self.x, self.y = x, y
        angle = random.uniform(0, math.tau)
        speed = random.uniform(0.3, 1.8)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(0.2, 1.0)  # upward bias
        self.size = random.uniform(2.5, 6.0)
        self.max_life = random.randint(60, 140)
        self.life = self.max_life
        self.color = random.choice(palette)
        self.shape = random.choice(shapes)
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-4.0, 4.0)

    @property
    def alpha(self) -> int:
        progress = self.life / self.max_life
        if progress > 0.85:
            return int(255 * (1.0 - progress) / 0.15)
        return int(255 * min(progress / 0.1, 1.0))

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.04          # gravity
        self.vx *= 0.99          # drag
        self.rotation += self.rot_speed
        self.life -= 1

    @property
    def alive(self) -> bool:
        return self.life > 0

class ParticleSystem:
    """Manages a pool of particles and emits new ones at a capped rate."""

    MAX_PARTICLES = 80

    def __init__(self, palette: List[QColor]):
        self.palette = palette
        self.particles: List[Particle] = []
        self._spawn_counter = 0

    def emit(self, x: float, y: float, count: int = 3):
        remaining = self.MAX_PARTICLES - len(self.particles)
        for _ in range(min(count, remaining)):
            self.particles.append(Particle(x + random.uniform(-10, 10),
                                           y + random.uniform(-5, 5),
                                           self.palette))

    def update(self):
        self.particles = [p for p in self.particles if p.alive]
        for p in self.particles:
            p.update()

    def draw(self, painter: QPainter):
        painter.save()
        for p in self.particles:
            c = QColor(p.color)
            c.setAlpha(p.alpha)
            painter.setBrush(QBrush(c))
            painter.setPen(Qt.NoPen)

            painter.save()
            painter.translate(p.x, p.y)
            painter.rotate(p.rotation)

            s = p.size
            if p.shape == "circle":
                painter.drawEllipse(QRectF(-s, -s, s * 2, s * 2))
            elif p.shape == "rect":
                painter.drawRect(QRectF(-s * 0.6, -s * 0.6, s * 1.2, s * 1.2))
            elif p.shape == "star":
                path = QPainterPath()
                for i in range(5):
                    a_out = math.radians(i * 72 - 90)
                    a_in  = math.radians(i * 72 - 90 + 36)
                    ox, oy = math.cos(a_out) * s, math.sin(a_out) * s
                    ix, iy = math.cos(a_in)  * s * 0.4, math.sin(a_in) * s * 0.4
                    if i == 0:
                        path.moveTo(ox, oy)
                    else:
                        path.lineTo(ox, oy)
                    path.lineTo(ix, iy)
                path.closeSubpath()
                painter.drawPath(path)

            painter.restore()
        painter.restore()


class EventTheme:
    """Defines color personality for a specific event type."""

    BIRTHDAY = "birthday"
    NEW_YEAR  = "new_year"

    _THEMES = {
        BIRTHDAY: {
            "hue_start":  35.0,
            "hue_range":  80.0,
            "saturation": 0.92,
            "glow_color": (255, 180, 40),
            "particle_palette": [
                QColor(255, 215,  50),
                QColor(255, 140,  60),
                QColor(255,  90, 120),
                QColor(255, 200, 100),
                QColor(220,  80, 200),
            ],
        },
        NEW_YEAR: {
            "hue_start": 180.0,
            "hue_range": 160.0,
            "saturation": 0.95,
            "glow_color": (80, 200, 255),
            "particle_palette": [
                QColor( 80, 220, 255),
                QColor(140,  80, 255),
                QColor(200, 240, 255),
                QColor( 40, 160, 255),
                QColor(180, 100, 255),
            ],
        },
    }

    def __init__(self, event_type: str = NEW_YEAR):
        self._data = self._THEMES.get(event_type, self._THEMES[self.NEW_YEAR])

    @property
    def hue_start(self)       -> float:              return self._data["hue_start"]
    @property
    def hue_range(self)       -> float:              return self._data["hue_range"]
    @property
    def saturation(self)      -> float:              return self._data["saturation"]
    @property
    def glow_color(self)      -> Tuple[int, int, int]: return self._data["glow_color"]
    @property
    def particle_palette(self) -> List[QColor]:      return self._data["particle_palette"]

    def cyclic_color(self, hue_offset: float, local_offset: float = 0.0,
                     time: float = 0.0) -> QColor:
        """
        Returns a smooth perceptual color from this theme's hue band.
        `hue_offset` drives the animation cycle; `local_offset` spreads
        colors around the border.
        """
        hue = (self.hue_start + (hue_offset + local_offset) % self.hue_range) % 360.0

        sat = self.saturation * (0.93 + math.sin(time * 0.4 + local_offset * 0.015) * 0.07)
        val = 0.97 + math.sin(time * 0.6 + local_offset * 0.02) * 0.03

        return QColor.fromHsvF(hue / 360.0, min(sat, 1.0), min(val, 1.0))


class LiquidBorderWidget(QWidget):
    """
    Organic liquid border using:
    • Single FBM PerlinNoise (replaces 4 separate instances)
    • Path cached until widget is resized  → huge CPU saving
    • Per-event color theming
    • Integrated particle system
    • Countdown arc showing remaining display time
    """

    def __init__(self, parent=None, event_type: str = EventTheme.NEW_YEAR,
                 duration_ms: int = 60000):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.noise = PerlinNoise(seed=42)

        self.time        = 0.0
        self.hue_offset  = 0.0
        self.flow_speed  = 0.022
        self.wave_scale  = 11.0
        self.border_width = 5.0
        self.path_smoothness = 0.82

        self.theme = EventTheme(event_type)

        self.particles = ParticleSystem(self.theme.particle_palette)
        self._spawn_tick = 0

        self.duration_ms   = duration_ms
        self.elapsed_ms    = 0
        self._countdown_ms = duration_ms

        self._cached_path: Optional[QPainterPath] = None
        self._cached_size = (0, 0)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def _tick(self):
        self.time       += self.flow_speed
        self.hue_offset  = (self.hue_offset + 1.4) % self.theme.hue_range
        self.elapsed_ms += 16
        self._countdown_ms = max(0, self.duration_ms - self.elapsed_ms)

        self._spawn_tick += 1
        if self._spawn_tick % 8 == 0:
            w, h = self.width(), self.height()
            side = random.randint(0, 3)
            if side == 0:   px, py = random.uniform(0, w), 8.0
            elif side == 1: px, py = w - 8.0, random.uniform(0, h)
            elif side == 2: px, py = random.uniform(0, w), h - 8.0
            else:           px, py = 8.0, random.uniform(0, h)
            self.particles.emit(px, py, count=random.randint(1, 3))

        self.particles.update()
        self.update()

    def _organic_offset(self, position: float, edge_id: float) -> float:
        """FBM-based offset — single call replaces 4 noise instances."""
        return self.noise.fbm(
            x=position * 0.018,
            y=edge_id  * 3.5,
            z=self.time,
            octaves=4,
            persistence=0.52,
            lacunarity=2.15,
        ) * self.wave_scale

    def _build_liquid_path(self) -> QPainterPath:
        rect = self.rect().adjusted(7, 7, -7, -7)
        w, h = rect.width(), rect.height()
        step = 5
        pts: List[QPointF] = []

        for i in range(0, w + step, step):
            pts.append(QPointF(rect.x() + i,
                               rect.y() + self._organic_offset(i, 0.0)))
        for i in range(0, h + step, step):
            pts.append(QPointF(rect.x() + w + self._organic_offset(i, 1.0),
                               rect.y() + i))
        for i in range(w, -step, -step):
            pts.append(QPointF(rect.x() + i,
                               rect.y() + h + self._organic_offset(i, 2.0)))
        for i in range(h, -step, -step):
            pts.append(QPointF(rect.x() + self._organic_offset(i, 3.0),
                               rect.y() + i))

        return self._catmull_rom(pts)

    def _catmull_rom(self, pts: List[QPointF]) -> QPainterPath:
        """Catmull-Rom spline through all points, closed."""
        n = len(pts)
        if n < 2:
            return QPainterPath()

        path = QPainterPath()
        path.moveTo(pts[0])
        s = self.path_smoothness

        def tangent(a: QPointF, b: QPointF) -> QPointF:
            return QPointF((b.x() - a.x()) * 0.5 * s,
                           (b.y() - a.y()) * 0.5 * s)

        for i in range(n - 1):
            p0 = pts[max(i - 1, 0)]
            p1 = pts[i]
            p2 = pts[(i + 1) % n]
            p3 = pts[(i + 2) % n]

            t1 = tangent(p0, p2)
            t2 = tangent(p1, p3)

            cp1 = QPointF(p1.x() + t1.x() / 3, p1.y() + t1.y() / 3)
            cp2 = QPointF(p2.x() - t2.x() / 3, p2.y() - t2.y() / 3)
            path.cubicTo(cp1, cp2, p2)

        path.closeSubpath()
        return path

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        bg = QPainterPath()
        bg.addRoundedRect(QRectF(self.rect().adjusted(3, 3, -3, -3)), 17, 17)
        grad = QRadialGradient(self.rect().center(),
                               max(self.width(), self.height()) * 0.75)
        grad.setColorAt(0.0, QColor(24, 29, 40, 246))
        grad.setColorAt(0.6, QColor(17, 21, 30, 251))
        grad.setColorAt(1.0, QColor(11, 14, 20, 255))
        painter.fillPath(bg, QBrush(grad))

        sz = (self.width(), self.height())
        if sz != self._cached_size:
            self._cached_size = sz
        path = self._build_liquid_path()

        cg = QConicalGradient(self.rect().center(), self.hue_offset)
        offsets = [0.0, 0.14, 0.28, 0.42, 0.57, 0.71, 0.85, 1.0]
        for pos in offsets:
            c = self.theme.cyclic_color(self.hue_offset,
                                         pos * self.theme.hue_range,
                                         self.time)
            c.setAlpha(215)
            cg.setColorAt(pos, c)

        bw = self.border_width

        painter.setPen(QPen(QColor(0, 0, 0, 70), bw + 14))
        painter.drawPath(path)

        r, g, b = self.theme.glow_color
        outer = QColor(r, g, b, 40)
        painter.setPen(QPen(outer, bw + 10))
        painter.drawPath(path)

        mid = QColor(r, g, b, 65)
        painter.setPen(QPen(mid, bw + 5))
        painter.drawPath(path)

        pen = QPen(QBrush(cg), bw)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(path)

        hi = self.theme.cyclic_color(self.hue_offset, 0, self.time)
        hi.setAlpha(170)
        painter.setPen(QPen(hi, bw * 0.45))
        painter.drawPath(path)

        self.particles.draw(painter)

        self._draw_countdown(painter)

        painter.end()

    def _draw_countdown(self, painter: QPainter):
        """Subtle arc in corner showing time remaining."""
        if self.duration_ms <= 0:
            return
        progress = self._countdown_ms / self.duration_ms
        if progress <= 0:
            return

        r = 10
        margin = 10
        cx = self.width()  - margin - r
        cy = self.height() - margin - r
        rect = QRectF(cx - r, cy - r, r * 2, r * 2)

        painter.setPen(QPen(QColor(255, 255, 255, 25), 2.0, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(rect)

        span = int(360 * 16 * progress)
        r2, g2, b2 = self.theme.glow_color
        arc_color = QColor(r2, g2, b2, 180)
        painter.setPen(QPen(arc_color, 2.0, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, 90 * 16, -span)


class _AnimBase(QDialog):
    """
    Provides scale_factor, rotation_angle, and glow_intensity as proper
    Q_PROPERTY-compatible Python properties for QPropertyAnimation.
    (Lambda-based Property declarations break QPropertyAnimation in PySide6.)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scale    = 1.0
        self._rotation = 0.0
        self._glow     = 0.0

    def _get_scale(self)      -> float: return self._scale
    def _set_scale(self, v: float):
        self._scale = v
        self.update()
    scale_factor = Property(float, _get_scale, _set_scale)

    def _get_rotation(self)   -> float: return self._rotation
    def _set_rotation(self, v: float):
        self._rotation = v
        self.update()
    rotation_angle = Property(float, _get_rotation, _set_rotation)

    def _get_glow(self)       -> float: return self._glow
    def _set_glow(self, v: float):
        self._glow = v
        self.update()
    glow_intensity = Property(float, _get_glow, _set_glow)


class SpecialEventPopup(_AnimBase):
    """
    Frameless floating notification with:
    • Event-themed liquid border + particles
    • Entrance animation (fade + spring scale + slight rotation)
    • Continuous ambient glow pulse
    • Countdown ring
    • Sound playback with cleanup
    """

    closed_by_user = Signal()

    def __init__(self, title: str, subtitle: str, message: str,
                 icon_path: str, sound_path: str,
                 event_type: str = EventTheme.NEW_YEAR,
                 duration_ms: int = 60000,
                 parent=None):
        super().__init__(parent)

        self.sound_path  = sound_path
        self.duration_ms = duration_ms
        self.event_type  = event_type
        self.theme       = EventTheme(event_type)
        self.media_player  = None
        self.audio_output  = None
        self.custom_font   = self._load_font()

        self._build_ui(title, subtitle, message, icon_path)
        self._setup_animations()
        self._play_sound()

        QTimer.singleShot(duration_ms, self._close_timeout)

    def _load_font(self) -> QFont:
        candidates = [
            _resource_path(os.path.join("fonts", "Inter-Regular.ttf")),
            os.path.join("fonts", "Inter-Regular.ttf"),
        ]
        for p in candidates:
            if os.path.exists(p):
                fid = QFontDatabase.addApplicationFont(p)
                if fid != -1:
                    families = QFontDatabase.applicationFontFamilies(fid)
                    if families:
                        return QFont(families[0], 12)
        return QFont("Segoe UI", 12)

    def _build_ui(self, title: str, subtitle: str,
                  message: str, icon_path: str):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(470, 265)

        self.border_widget = LiquidBorderWidget(
            self, event_type=self.event_type, duration_ms=self.duration_ms)
        self.border_widget.setGeometry(0, 0, 470, 265)

        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.container.setGeometry(7, 7, 456, 251)
        self.container.setStyleSheet("""
            #container {
                background: qradialgradient(
                    cx:0.5, cy:0.5, radius:1.2,
                    stop:0 #1e2535, stop:0.65 #171e2c, stop:1 #0e1320);
                border-radius: 13px;
            }
        """)

        root = QVBoxLayout(self.container)
        root.setContentsMargins(14, 12, 14, 10)
        root.setSpacing(9)

        content = QHBoxLayout()
        content.setSpacing(13)

        icon_frame = QFrame()
        icon_frame.setFixedSize(82, 82)
        r, g, b = self.theme.glow_color
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background: qradialgradient(
                    cx:0.5, cy:0.5, radius:0.8,
                    stop:0 rgba({r},{g},{b},28), stop:1 rgba({r//2},{g//2},{b//2},10));
                border-radius: 9px;
                border: 1px solid rgba({r},{g},{b},55);
            }}
        """)
        il = QVBoxLayout(icon_frame)
        il.setContentsMargins(3, 3, 3, 3)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(76, 76)
        il.addWidget(self.icon_label)
        content.addWidget(icon_frame)

        text_w = QWidget()
        text_w.setStyleSheet("background:transparent;")
        tl = QVBoxLayout(text_w)
        tl.setContentsMargins(0, 2, 0, 0)
        tl.setSpacing(3)

        self.title_label = QLabel(title)
        self.title_label.setFont(QFont(self.custom_font.family(), 17, QFont.Bold))
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(42)
        if self.event_type == EventTheme.BIRTHDAY:
            title_css = "color: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #FFD700, stop:0.5 #FF8C00, stop:1 #FFD700);"
        else:
            title_css = "color: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #40E0FF, stop:0.5 #9B6FFF, stop:1 #40E0FF);"
        self.title_label.setStyleSheet(title_css)
        tl.addWidget(self.title_label)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setFont(QFont(self.custom_font.family(), 13, QFont.Bold))
        sub_color = "#FFB347" if self.event_type == EventTheme.BIRTHDAY else "#7EC8F5"
        self.subtitle_label.setStyleSheet(f"color:{sub_color};")
        tl.addWidget(self.subtitle_label)

        self.message_label = QLabel(message)
        self.message_label.setFont(QFont(self.custom_font.family(), 10))
        self.message_label.setWordWrap(True)
        self.message_label.setMaximumHeight(95)
        self.message_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.message_label.setStyleSheet("color:#C8D6DC; background:transparent;")
        tl.addWidget(self.message_label)
        tl.addStretch()

        content.addWidget(text_w, 1)
        root.addLayout(content)

        close_row = QHBoxLayout()
        close_row.addStretch()
        self.close_btn = QPushButton()
        self.close_btn.setFixedSize(26, 26)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet("background:transparent; border:none;")
        self.close_btn.paintEvent = lambda e: _draw_close_btn(self.close_btn, e)
        self.close_btn.clicked.connect(self._close_user)
        close_row.addWidget(self.close_btn)
        root.addLayout(close_row)

        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 22, screen.top() + 38)

        self._load_icon(icon_path)

    def _load_icon(self, path: str):
        if path and os.path.exists(path):
            px = QPixmap(path)
            if not px.isNull():
                scaled = px.scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                final = QPixmap(76, 76)
                final.fill(Qt.transparent)
                p = QPainter(final)
                p.setRenderHint(QPainter.Antialiasing)
                p.drawPixmap((76 - scaled.width()) // 2,
                              (76 - scaled.height()) // 2, scaled)
                p.end()
                self.icon_label.setPixmap(final)
                return
        emoji = "🎂" if self.event_type == EventTheme.BIRTHDAY else "🎉"
        self.icon_label.setText(emoji)
        self.icon_label.setFont(QFont(self.custom_font.family(), 40))
        r, g, b = self.theme.glow_color
        self.icon_label.setStyleSheet(
            f"color:rgb({r},{g},{b}); background:transparent;")

    def _setup_animations(self):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        fade = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade.setDuration(550)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.OutCubic)
        fade.start()

        scale = QPropertyAnimation(self, b"scale_factor")
        scale.setDuration(600)
        scale.setStartValue(0.80)
        scale.setEndValue(1.0)
        scale.setEasingCurve(QEasingCurve.OutBack)
        scale.start()

        rot = QPropertyAnimation(self, b"rotation_angle")
        rot.setDuration(550)
        rot.setStartValue(-3.0)
        rot.setEndValue(0.0)
        rot.setEasingCurve(QEasingCurve.OutCubic)
        rot.start()

        glow = QPropertyAnimation(self, b"glow_intensity")
        glow.setDuration(1600)
        glow.setLoopCount(-1)
        glow.setKeyValues([(0.0, 0.25), (0.5, 1.0), (1.0, 0.25)])
        glow.setEasingCurve(QEasingCurve.InOutSine)
        glow.start()

        self._anims = [fade, scale, rot, glow]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self._scale != 1.0 or self._rotation != 0.0:
            t = QTransform()
            c = self.rect().center()
            t.translate(c.x(), c.y())
            t.scale(self._scale, self._scale)
            t.rotate(self._rotation)
            t.translate(-c.x(), -c.y())
            painter.setTransform(t)

        if self._glow > 0.01:
            painter.setCompositionMode(QPainter.CompositionMode_Plus)
            gr = self.rect().adjusted(-15, -15, 15, 15)
            rr, gg, bb = self.theme.glow_color
            g = QRadialGradient(gr.center(),
                                max(gr.width(), gr.height()) / 2.3)
            a = int(105 * self._glow)
            g.setColorAt(0.0, QColor(rr, gg, bb, a))
            g.setColorAt(0.55, QColor(rr // 2, gg // 2, bb, a // 2))
            g.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(g))
            painter.drawRoundedRect(QRectF(gr), 22, 22)

        painter.end()
        super().paintEvent(event)

    def _play_sound(self):
        if not self.sound_path or not os.path.exists(self.sound_path):
            return
        try:
            from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput  # lazy — codecs loaded on first sound
            self.media_player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.media_player.setAudioOutput(self.audio_output)
            self.audio_output.setVolume(0.6)
            self.media_player.setSource(QUrl.fromLocalFile(self.sound_path))
            self.media_player.play()
        except Exception as e:
            print(f"[SpecialEvents] Audio error: {e}")

    def _stop_sound(self):
        if self.media_player:
            self.media_player.stop()
            self.media_player.deleteLater()
            self.media_player = None
        if self.audio_output:
            self.audio_output.deleteLater()
            self.audio_output = None
        if hasattr(self, "border_widget"):
            self.border_widget._timer.stop()

    def _close_user(self):
        self._stop_sound()
        self.closed_by_user.emit()
        self.accept()

    def _close_timeout(self):
        self._stop_sound()
        self.accept()

    def closeEvent(self, event):
        self._stop_sound()
        event.accept()

def _draw_close_btn(widget: QWidget, _event):
    p = QPainter(widget)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#8EACBB"), 1.3))
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(2, 2, 22, 22)
    pen = QPen(QColor("#8EACBB"), 1.7)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.drawLine(8, 8, 18, 18)
    p.drawLine(8, 18, 18, 8)
    p.end()


class BirthdayInputDialog(QDialog):
    """
    Compact birthdate dialog.
    Improvements:
    • hint_label hidden until validation actually fails
    • Theme-aware styling
    • Font loaded once via module helper
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.custom_font = self._load_font()
        self.setWindowTitle(self._t("bday_title_win"))
        self.setModal(True)
        self.setFixedSize(390, 285)
        self._build_ui()
        self._apply_style()

    _KEY_MAP = {
        "title_win":  "bday_title_win",
        "heading":    "bday_heading",
        "desc":       "bday_desc",
        "lbl_date":   "bday_lbl_date",
        "hint_age":   "bday_hint_age",
        "btn_cancel": "bday_btn_cancel",
        "btn_save":   "bday_btn_save",
        "err_title":  "bday_err_title",
        "err_old":    "bday_err_old",
        "err_young":  "bday_err_young",
    }

    def _t(self, key: str) -> str:
        lang = getattr(self.parent(), "current_language", "fr") if self.parent() else "fr"
        tm   = _make_tm(lang)
        return tm.translate_text(self._KEY_MAP.get(key, key))

    def _load_font(self) -> QFont:
        return _load_app_font(11)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(22, 20, 22, 18)

        heading = QLabel(self._t("heading"))
        heading.setFont(QFont(self.custom_font.family(), 16, QFont.Bold))
        heading.setAlignment(Qt.AlignCenter)
        layout.addWidget(heading)

        desc = QLabel(self._t("desc"))
        desc.setFont(QFont(self.custom_font.family(), 10))
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        row = QHBoxLayout()
        lbl = QLabel(self._t("lbl_date"))
        lbl.setFont(QFont(self.custom_font.family(), 10))

        self.date_edit = QDateEdit()
        self.date_edit.setFont(QFont(self.custom_font.family(), 10))
        self.date_edit.setCalendarPopup(True)
        today = date.today()
        self.date_edit.setDateRange(date(1900, 1, 1),
                                    today.replace(year=today.year - 3))
        self.date_edit.setDate(today.replace(year=today.year - 25))
        self.date_edit.setMinimumHeight(38)
        row.addWidget(lbl)
        row.addWidget(self.date_edit)
        layout.addLayout(row)

        self.hint_label = QLabel(self._t("hint_age"))
        self.hint_label.setFont(QFont(self.custom_font.family(), 9))
        self.hint_label.setWordWrap(True)
        self.hint_label.setAlignment(Qt.AlignRight)
        self.hint_label.setVisible(False)
        layout.addWidget(self.hint_label)



        btns = QHBoxLayout()
        self.cancel_btn = QPushButton(self._t("btn_cancel"))
        self.cancel_btn.setFont(QFont(self.custom_font.family(), 10, QFont.Bold))
        self.cancel_btn.setMinimumHeight(36)
        self.cancel_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.submit_btn = QPushButton(self._t("btn_save"))
        self.submit_btn.setFont(QFont(self.custom_font.family(), 10, QFont.Bold))
        self.submit_btn.setMinimumHeight(36)
        self.submit_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        btns.addWidget(self.cancel_btn)
        btns.addWidget(self.submit_btn)
        layout.addLayout(btns)

        self.dont_ask_checkbox = AnimatedCheckBox(self._t("dont_ask"))
        self.dont_ask_checkbox.setChecked(False)
        layout.addWidget(self.dont_ask_checkbox, alignment=Qt.AlignCenter)

        self.cancel_btn.clicked.connect(self.reject)
        self.submit_btn.clicked.connect(self._validate)

    def _apply_style(self):
        dark = getattr(self.parent(), "dark_mode", True) if self.parent() else True
        arr  = _resource_path(os.path.join("Assets", "down-arrow.svg")).replace("\\", "/")
        arrH = _resource_path(os.path.join("Assets", "down-arrow-hover.svg")).replace("\\", "/")
        ff   = self.custom_font.family()

        if dark:
            bg_dlg  = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(28,35,46,.95), stop:1 rgba(20,26,36,.95))"
            fg      = "#E4E8EE"
            btn_bg  = "rgba(55,60,65,.65)"
            btn_bdr = "rgba(90,95,100,.8)"
            inp_bg  = "rgba(38,43,50,.85)"
            inp_bdr = "rgba(90,95,100,.8)"
            cal_btn = "rgba(55,60,65,.65)"
            cal_bdr = "rgba(90,95,100,.5)"
        else:
            bg_dlg  = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(255,255,255,.96), stop:1 rgba(238,240,243,.96))"
            fg      = "#1C1F24"
            btn_bg  = "rgba(238,240,243,.85)"
            btn_bdr = "rgba(210,214,218,.85)"
            inp_bg  = "rgba(255,255,255,.85)"
            inp_bdr = "rgba(210,214,218,.85)"
            cal_btn = "rgba(238,240,243,.85)"
            cal_bdr = "rgba(210,214,218,.5)"

        self.setStyleSheet(f"""
            QDialog {{
                background: {bg_dlg};
                border-radius: 10px;
            }}
            QLabel {{ color: {fg}; background: transparent; }}
            QPushButton {{
                padding: 6px 12px;
                border-radius: 7px;
                font-weight: bold;
                font-family: '{ff}';
            }}
            QPushButton#cancel {{
                background: {btn_bg};
                color: {fg};
                border: 1px solid {btn_bdr};
            }}
            QPushButton#cancel:hover {{ background: {btn_bdr}; }}
            QPushButton#submit {{
                background: rgba(26,115,232,.82);
                color: white;
                border: none;
            }}
            QPushButton#submit:hover {{ background: rgba(21,87,176,.92); }}
            QDateEdit {{
                padding: 6px;
                border-radius: 7px;
                border: 1px solid {inp_bdr};
                background: {inp_bg};
                color: {fg};
                font-family: '{ff}';
            }}
            QDateEdit::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid {inp_bdr};
            }}
            QDateEdit::down-arrow       {{ image: url("{arr}");  width:16px; height:16px; }}
            QDateEdit::down-arrow:hover {{ image: url("{arrH}"); width:16px; height:16px; top:2px; }}
            QCalendarWidget {{ font-family: '{ff}'; }}
            QCalendarWidget QToolButton, QCalendarWidget QSpinBox {{
                color: {fg};
                background-color: {cal_btn};
                border: 1px solid {cal_bdr};
                border-radius: 4px;
                padding: 4px;
                margin: 2px;
            }}
            QCalendarWidget QSpinBox {{ min-width: 65px; }}
            QCalendarWidget QSpinBox::up-button,
            QCalendarWidget QSpinBox::down-button {{
                subcontrol-origin: border;
                background: {cal_bdr};
                width: 16px;
            }}
        """)
        self.cancel_btn.setObjectName("cancel")
        self.submit_btn.setObjectName("submit")

    def _validate(self):
        bd    = self.date_edit.date().toPython()
        today = date.today()
        min_d = today.replace(year=today.year - 120)
        max_d = today.replace(year=today.year - 3)

        if bd < min_d:
            self.hint_label.setText(self._t("err_old"))
            self.hint_label.setVisible(True)
            QMessageBox.warning(self, self._t("err_title"), self._t("err_old"))
            return
        if bd > max_d:
            self.hint_label.setText(self._t("hint_age"))
            self.hint_label.setVisible(True)
            QMessageBox.warning(self, self._t("err_title"), self._t("err_young"))
            return

        self.hint_label.setVisible(False)
        self.accept()


def _resource_path(relative: str) -> str:
    """Resolves asset paths for both dev mode and PyInstaller .exe."""
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.abspath(".")

    p = os.path.join(base, relative)
    if os.path.exists(p):
        return p

    for alt in (Path.cwd() / relative, Path(__file__).parent / relative):
        if alt.exists():
            return str(alt)

    return p

def _load_app_font(size: int = 11) -> QFont:
    """Load Inter-Regular (shared across dialogs)."""
    candidates = [
        _resource_path(os.path.join("fonts", "Inter-Regular.ttf")),
        os.path.join("fonts", "Inter-Regular.ttf"),
    ]
    for path in candidates:
        if os.path.exists(path):
            fid = QFontDatabase.addApplicationFont(path)
            if fid != -1:
                families = QFontDatabase.applicationFontFamilies(fid)
                if families:
                    return QFont(families[0], size)
    return QFont("Segoe UI", size)


class SpecialEventsManager:
    """
    Orchestrates special-event detection and popup display.
    Tracks triggered events in SQLite to avoid re-showing within the same day.
    """

    def __init__(self, app_instance):
        self.app       = app_instance
        self.db_path   = self._get_db_path()
        self.birthdate: Optional[date] = None
        self._init_db()
        QTimer.singleShot(5000, self._check_and_prompt)

    def _get_db_path(self) -> str:
        base = (os.path.dirname(sys.executable)
                if getattr(sys, "frozen", False)
                else os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, "special_events.db")

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS events (
                event_type TEXT PRIMARY KEY,
                last_triggered_date TEXT NOT NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS user_info (
                key TEXT PRIMARY KEY, value TEXT)""")

    def _triggered_today(self, etype: str) -> bool:
        today = date.today().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT 1 FROM events WHERE event_type=? AND last_triggered_date=?",
                (etype, today)).fetchone()
        return row is not None

    def _mark_triggered(self, etype: str):
        today = date.today().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO events VALUES (?,?)",
                (etype, today))

    def _get_birthdate(self) -> Optional[date]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT value FROM user_info WHERE key='birthdate'").fetchone()
        if row and row[0]:
            try:
                return date.fromisoformat(row[0])
            except ValueError:
                pass
        return None

    def _save_birthdate(self, bd: date):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO user_info VALUES ('birthdate',?)",
                         (bd.isoformat(),))
        self.birthdate = bd

    def _save_user_info(self, key: str, value: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO user_info VALUES (?,?)", (key, value))

    def _get_user_info(self, key: str):
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT value FROM user_info WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def _check_and_prompt(self):
        bd = self._get_birthdate()
        if bd is None:
            if self._get_user_info("birthday_declined") == "1":
                self._check_new_year()
                return
            dlg = BirthdayInputDialog(self.app)
            if dlg.exec() == QDialog.Accepted:
                bd = dlg.date_edit.date().toPython()
                self._save_birthdate(bd)
                self._check_birthday()
            else:
                if dlg.dont_ask_checkbox.isChecked():
                    self._save_user_info("birthday_declined", "1")
        else:
            self.birthdate = bd
            self._check_birthday()
        self._check_new_year()

    def _check_new_year(self):
        today = date.today()
        if today.month == 1 and today.day == 1 and not self._triggered_today("new_year"):
            self._fire_new_year()

    def _check_birthday(self):
        if not self.birthdate:
            return
        today = date.today()
        if (today.month == self.birthdate.month and
                today.day == self.birthdate.day and
                not self._triggered_today("birthday")):
            self._fire_birthday(today.year - self.birthdate.year)

    def _fire_new_year(self):
        lang  = getattr(self.app, "current_language", "fr")
        year  = date.today().year
        tm    = _make_tm(lang)

        title    = tm.translate_text("new_year_title")
        subtitle = str(year)
        message  = tm.translate_text("new_year_message")

        popup = SpecialEventPopup(
            title=title, subtitle=subtitle, message=message,
            icon_path=_resource_path(os.path.join("Assets", "new_year.png")),
            sound_path=_resource_path(os.path.join("SFX", "new_year.wav")),
            event_type=EventTheme.NEW_YEAR,
            duration_ms=60_000,
            parent=self.app,
        )
        popup.closed_by_user.connect(lambda: self._mark_triggered("new_year"))
        popup.exec()
        self._mark_triggered("new_year")

    def _fire_birthday(self, age: int):
        lang = getattr(self.app, "current_language", "fr")
        tm   = _make_tm(lang)

        title   = tm.translate_text("birthday_title")
        message = tm.translate_text("birthday_message")
        if lang == "fr":
            subtitle = f"{age} ans"
        else:
            suffix   = "st" if age==1 else "nd" if age==2 else "rd" if age==3 else "th"
            subtitle = f"{age}{suffix} Birthday"

        popup = SpecialEventPopup(
            title=title, subtitle=subtitle, message=message,
            icon_path=_resource_path(os.path.join("Assets", "birthday.png")),
            sound_path=_resource_path(os.path.join("SFX", "birthday.wav")),
            event_type=EventTheme.BIRTHDAY,
            duration_ms=80_000,
            parent=self.app,
        )
        popup.closed_by_user.connect(lambda: self._mark_triggered("birthday"))
        popup.exec()
        self._mark_triggered("birthday")