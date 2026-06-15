"""
Custom Widgets

Contains customized Qt widgets with advanced animations and behaviors.

Classes:
    AnimatedCheckBox:
        - Smooth check/uncheck animations using QPropertyAnimation
        - Custom painting with glow, ripple, and progress effects
        - Theme-aware colors (Dark/Light mode support)
    
    DraggableListWidget:
        - Supports drag-and-drop files from Windows Explorer
        - Intelligent parent detection via duck typing
        - Emits signals or calls parent methods on file drop

"""

from PySide6.QtWidgets import QCheckBox, QListWidget, QStyledItemDelegate, QStyle
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QSize, QPointF, QRect, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QLinearGradient, QDragEnterEvent, QDropEvent
import os

class AnimatedCheckBox(QCheckBox):
    """
    Custom CheckBox with:
    - Smooth check/uncheck animation
    - Progressively drawn check mark
    - Glow effect on hover
    - Ripple effect on click
    - Dark/light theme support
    """
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._check_progress = 0.0
        self._hover_glow = 0.0
        self._ripple_progress = 0.0
        self._ripple_active = False
        self._is_dark = False
        self.setFixedHeight(32)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.setStyleSheet("QCheckBox::indicator { width: 0; height: 0; }")
        
        self._anim = QPropertyAnimation(self, b"checkProgress")
        self._anim.setDuration(350)
        self._anim.setEasingCurve(QEasingCurve.OutBack)
        
        self._hover_anim = QPropertyAnimation(self, b"hoverGlow")
        self._hover_anim.setDuration(180)
        self._hover_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self._ripple_anim = QPropertyAnimation(self, b"rippleProgress")
        self._ripple_anim.setDuration(480)
        self._ripple_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._ripple_anim.finished.connect(self._on_ripple_done)
        
        self.toggled.connect(self._on_toggled)
    
    def _get_check(self):
        return self._check_progress
    
    def _set_check(self, v):
        self._check_progress = v
        self.update()
    
    checkProgress = Property(float, _get_check, _set_check)
    
    def _get_hover(self):
        return self._hover_glow
    
    def _set_hover(self, v):
        self._hover_glow = v
        self.update()
    
    hoverGlow = Property(float, _get_hover, _set_hover)
    
    def _get_ripple(self):
        return self._ripple_progress
    
    def _set_ripple(self, v):
        self._ripple_progress = v
        self.update()
    
    rippleProgress = Property(float, _get_ripple, _set_ripple)
    
    def setDarkTheme(self, dark: bool):
        self._is_dark = dark
        self.update()
    
    def _on_toggled(self, checked):
        self._anim.stop()
        self._anim.setStartValue(self._check_progress)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()
    
    def _on_ripple_done(self):
        self._ripple_active = False
        self.update()
    
    def mousePressEvent(self, event):
        if not self.isEnabled():
            event.ignore()
            return
        try:
            if event.button() == Qt.LeftButton:
                self._ripple_active = True
                self._ripple_anim.stop()
                self._ripple_anim.setStartValue(0.0)
                self._ripple_anim.setEndValue(1.0)
                self._ripple_anim.start()
            super().mousePressEvent(event)
        except RuntimeError:
            pass
    
    def enterEvent(self, event):
        try:
            self._hover_anim.stop()
            self._hover_anim.setStartValue(self._hover_glow)
            self._hover_anim.setEndValue(1.0)
            self._hover_anim.start()
            super().enterEvent(event)
        except RuntimeError:
            pass
    
    def leaveEvent(self, event):
        try:
            self._hover_anim.stop()
            self._hover_anim.setStartValue(self._hover_glow)
            self._hover_anim.setEndValue(0.0)
            self._hover_anim.start()
            super().leaveEvent(event)
        except RuntimeError:
            pass
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bs = 20
        bx = 2
        by = (self.height() - bs) // 2
        self._draw_ripple(painter, bx, by, bs)
        self._draw_box(painter, bx, by, bs)
        self._draw_checkmark(painter, bx, by, bs)
        self._draw_label(painter, bx + bs + 10)
    
    def _draw_ripple(self, painter, bx, by, bs):
        if not self._ripple_active and self._ripple_progress == 0:
            return
        cx, cy = bx + bs / 2, by + bs / 2
        r = bs * 1.5 * self._ripple_progress
        alpha = int(55 * (1 - self._ripple_progress))
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(99, 102, 241, alpha))
        painter.drawEllipse(QPointF(cx, cy), r, r)
        painter.restore()
    
    def _draw_box(self, painter, bx, by, bs):
        from PySide6.QtCore import QRectF
        rect = QRectF(bx, by, bs, bs)
        p = self._check_progress
        
        # Theme-aware colors
        if self._is_dark:
            unchecked_bg = QColor(45, 51, 59)
            unchecked_bg2 = QColor(38, 43, 50)
        else:
            unchecked_bg = QColor(250, 250, 252)
            unchecked_bg2 = QColor(240, 240, 245)
        
        grad = QLinearGradient(bx, by, bx + bs, by + bs)
        if p > 0:
            r1 = int(unchecked_bg.red() + (99 - unchecked_bg.red()) * min(p * 2, 1))
            g1 = int(unchecked_bg.green() + (102 - unchecked_bg.green()) * min(p * 2, 1))
            b1 = int(unchecked_bg.blue() + (241 - unchecked_bg.blue()) * min(p * 2, 1))
            c1 = QColor(r1, g1, b1)
            c2 = QColor(int(r1 * 0.78), int(g1 * 0.68), min(255, int(b1 * 1.08)))
            grad.setColorAt(0, c1)
            grad.setColorAt(1, c2)
        else:
            grad.setColorAt(0, unchecked_bg)
            grad.setColorAt(1, unchecked_bg2)
        
        painter.save()
        
        if p > 0:
            for i in range(3, 0, -1):
                painter.setPen(QPen(QColor(99, 102, 241, int(50 * p)), i * 2.0))
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(
                    QRectF(bx - i, by - i, bs + i * 2, bs + i * 2), 7 + i, 7 + i
                )
        
        if self._hover_glow > 0 and p == 0:
            painter.setPen(QPen(QColor(99, 102, 241, int(22 * self._hover_glow)), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(QRectF(bx - 2, by - 2, bs + 4, bs + 4), 8, 8)
        
        painter.setBrush(grad)
        if p < 1.0:
            border_alpha = int(255 * (1 - p * 0.9))
            if self._is_dark:
                border_col = QColor(80, 90, 110, border_alpha)
            else:
                border_col = QColor(180, 180, 200, border_alpha)
            painter.setPen(QPen(border_col, 1.5))
        else:
            painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 6, 6)
        painter.restore()
    
    def _draw_checkmark(self, painter, bx, by, bs):
        from PySide6.QtCore import QPointF
        from PySide6.QtGui import QPainterPath
        if self._check_progress <= 0:
            return
        painter.save()
        p1 = QPointF(bx + bs * 0.22, by + bs * 0.52)
        p2 = QPointF(bx + bs * 0.44, by + bs * 0.72)
        p3 = QPointF(bx + bs * 0.78, by + bs * 0.30)
        len1 = ((p2.x()-p1.x())**2 + (p2.y()-p1.y())**2) ** 0.5
        len2 = ((p3.x()-p2.x())**2 + (p3.y()-p2.y())**2) ** 0.5
        total = len1 + len2
        draw_len = self._check_progress * total
        pen = QPen(QColor(255, 255, 255), 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        path = QPainterPath()
        if draw_len <= len1:
            t = draw_len / len1
            path.moveTo(p1)
            path.lineTo(QPointF(p1.x() + (p2.x()-p1.x())*t, p1.y() + (p2.y()-p1.y())*t))
        else:
            t = (draw_len - len1) / len2
            path.moveTo(p1)
            path.lineTo(p2)
            path.lineTo(QPointF(p2.x() + (p3.x()-p2.x())*t, p2.y() + (p3.y()-p2.y())*t))
        painter.drawPath(path)
        painter.restore()
    
    def _draw_label(self, painter, x):
        text = self.text()
        if not text:
            return
        painter.save()
        p = self._check_progress
        font = self.font()
        font.setPointSize(10)
        painter.setFont(font)
        if self._is_dark:
            r = int(180 + (160 - 180) * p)
            g = int(180 + (155 - 180) * p)
            b = int(200 + (220 - 200) * p)
        else:
            r = int(80 + (59 - 80) * p)
            g = int(80 + (55 - 80) * p)
            b = int(100 + (130 - 100) * p)
        painter.setPen(QColor(r, g, b))
        fm = painter.fontMetrics()
        painter.drawText(x, (self.height() + fm.ascent() - fm.descent()) // 2, text)
        painter.restore()
    
    def sizeHint(self):
        fm = self.fontMetrics()
        w = 2 + 20 + 10 + fm.horizontalAdvance(self.text()) + 4
        return QSize(max(w, 120), 32)


class FileSizeDelegate(QStyledItemDelegate):
    """
    Lets Qt draw everything normally, then paints the size string
    (stored in UserRole+4) on top, right-aligned.
    Selected: green (dark mode) / blue (light mode).
    Unselected: muted grey.
    """
    RIGHT_MARGIN = 10

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        size_str = index.data(Qt.UserRole + 4)
        if not size_str:
            return

        painter.save()

        font = painter.font()
        font.setPointSizeF(max(font.pointSizeF() - 1.0, 7.5))
        painter.setFont(font)
        fm = painter.fontMetrics()

        size_w = fm.horizontalAdvance(size_str)
        size_rect = QRect(
            option.rect.right() - size_w - self.RIGHT_MARGIN,
            option.rect.top(),
            size_w + self.RIGHT_MARGIN,
            option.rect.height(),
        )

        if option.state & QStyle.State_Selected:
            bg = option.palette.window().color()
            is_dark = (bg.red() * 0.299 + bg.green() * 0.587 + bg.blue() * 0.114) < 128
            if is_dark:
                color = QColor(80, 220, 140, 230)
            else:
                color = QColor(50, 130, 240, 230)
        else:
            color = QColor(110, 125, 150, 210)

        painter.setPen(color)
        painter.drawText(size_rect, Qt.AlignVCenter | Qt.AlignRight, size_str)
        painter.restore()

    def sizeHint(self, option, index):
        sh = super().sizeHint(option, index)
        return QSize(sh.width(), max(sh.height(), 28))

class DraggableListWidget(QListWidget):
    """
    ListWidget with drag & drop file support.
    - Accepts files from Windows Explorer
    - Calls the parent's add_files_to_list method
    - Supports internal reordering by drag & drop (single or multiple items)
    - Visual highlight on drag hover via viewport event filter (no timer)
    - ASCII art glitch animation when empty.
    """

    # Glitch character pool
    _GLITCH_CHARS = "█▓▒░╔╗╚╝║═╠╣╦╩╬▄▀■□▪▫◆◇○●"

    _GLITCH_RGB_PALETTES = [
        (255,  20, 147),
        ( 57, 255,  20),
        (255,  69,   0),
        (  0, 255, 255),
        (255, 255,   0),
        (148,   0, 211),
        (255, 165,   0),
        (  0, 191, 255),
    ]

    def __init__(self, parent=None, translation_manager=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragEnabled(True)
        self.setItemDelegate(FileSizeDelegate(self))
        self.viewport().setAcceptDrops(True)
        self.viewport().installEventFilter(self)
        self.viewport().setMouseTracking(True)
        self.setMouseTracking(True)

        self._tm = translation_manager

        import random
        self._rng = random.Random()
        self._glitch_frame        = 0
        self._glitch_active       = False
        self._glitch_ticks        = 0
        self._glitch_lines        = {}
        self._glitch_offset       = QPointF(0, 0)
        self._scanline_y          = 0
        self._glitch_palette_idx  = 0
        self._glitch_rgb_override = {}

        self._glitch_enabled      = True
        self._glitch_stop_timer   = QTimer(self)
        self._glitch_stop_timer.setSingleShot(True)
        self._glitch_stop_timer.setInterval(10_000)
        self._glitch_stop_timer.timeout.connect(self._stop_glitch_effects)
        self._glitch_stop_timer.start()

        self._glitch_timer = QTimer(self)
        self._glitch_timer.setInterval(80)
        self._glitch_timer.timeout.connect(self._tick_glitch)
        self._glitch_timer.start()

    def set_translation_manager(self, tm):
        """Inject or replace the TranslationManager (called from app)."""
        self._tm = tm
        self.viewport().update()

    def set_language(self, _lang: str = None):
        """Called by the app when language changes.
        The actual language state lives in the TranslationManager; we just
        need to repaint so the new strings are picked up immediately."""
        self.viewport().update()

    def _tr(self, key: str) -> str:
        """Translate *key* through the injected TM, or return key as fallback."""
        if self._tm is not None:
            return self._tm.translate_text(key)
        app = self._find_app()
        if app and hasattr(app, 'translation_manager'):
            self._tm = app.translation_manager
            return self._tm.translate_text(key)
        return key

    @property
    def _ASCII_ART(self):
        """Return the full art list: block1 rows + [''] gap + block2 rows.

        Each block comes from a translation key that holds newline-separated
        rows — so .lang files can override them freely.
        """
        raw1 = self._tr("dropzone_line1")
        raw2 = self._tr("dropzone_line2")
        block1 = raw1.split("\n") if raw1 else []
        block2 = raw2.split("\n") if raw2 else []
        return block1 + [""] + block2

    def _stop_glitch_effects(self):
        """Freeze glitch effects: no new bursts until hover."""
        self._glitch_enabled      = False
        self._glitch_active       = False
        self._glitch_lines        = {}
        self._glitch_rgb_override = {}
        self._glitch_offset       = QPointF(0, 0)
        self.viewport().update()

    def _start_glitch_effects(self):
        """Re-enable glitch effects for 10 s (called on hover)."""
        if not self._glitch_enabled:
            self._glitch_enabled = True
            self._glitch_stop_timer.start(10_000)

    def _tick_glitch(self):
        """Called every 80 ms. Drives all glitch state."""
        if self.count() > 0:
            self._glitch_timer.setInterval(500)
            self.viewport().update()
            return

        self._glitch_timer.setInterval(80)
        self._glitch_frame += 1
        art = self._ASCII_ART
        total = len(art)

        self._scanline_y = (self._scanline_y + 2) % max(total * 14, 1)

        if not self._glitch_active and self._glitch_enabled and self._rng.random() < 0.06:
            self._glitch_active = True
            self._glitch_ticks  = self._rng.randint(3, 8)
            self._glitch_palette_idx = (self._glitch_palette_idx + 1) % len(self._GLITCH_RGB_PALETTES)

        if self._glitch_active:
            self._glitch_ticks -= 1
            if self._glitch_ticks <= 0:
                self._glitch_active      = False
                self._glitch_lines       = {}
                self._glitch_rgb_override = {}
                self._glitch_offset      = QPointF(0, 0)
            else:
                n_corrupt = self._rng.randint(1, 3)
                self._glitch_lines       = {}
                self._glitch_rgb_override = {}

                base_rgb = self._GLITCH_RGB_PALETTES[self._glitch_palette_idx]
                sec_idx  = (self._glitch_palette_idx + self._rng.randint(1, 3)) % len(self._GLITCH_RGB_PALETTES)
                sec_rgb  = self._GLITCH_RGB_PALETTES[sec_idx]

                for k in range(n_corrupt):
                    li = self._rng.randint(0, total - 1)
                    orig = art[li]
                    if not orig:
                        continue
                    corrupted = list(orig)
                    n_swaps = self._rng.randint(2, max(3, len(orig) // 8))
                    for _ in range(n_swaps):
                        pos = self._rng.randint(0, len(corrupted) - 1)
                        corrupted[pos] = self._rng.choice(self._GLITCH_CHARS)
                    self._glitch_lines[li] = "".join(corrupted)
                    self._glitch_rgb_override[li] = base_rgb if k % 2 == 0 else sec_rgb

                dx = self._rng.uniform(-5, 5)
                self._glitch_offset = QPointF(dx, 0)
        else:
            self._glitch_lines       = {}
            self._glitch_rgb_override = {}
            self._glitch_offset      = QPointF(0, 0)

        self.viewport().update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.count() > 0:
            return

        import math
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing, False)

        w = self.viewport().width()
        h = self.viewport().height()

        art = self._ASCII_ART

        app = self._find_app()
        dark = getattr(app, 'dark_mode', True) if app else True
        if dark:
            bg = QColor(18, 18, 24)
        else:
            bg = QColor(245, 245, 252)
        painter.fillRect(0, 0, w, h, bg)

        longest = max(len(l) for l in art) if art else 1
        font = painter.font()
        font.setFamily("Courier New")
        font.setBold(True)
        for pt in range(8, 3, -1):
            font.setPointSize(pt)
            painter.setFont(font)
            fm = painter.fontMetrics()
            if fm.horizontalAdvance("█" * longest) <= w - 20:
                break
        painter.setFont(font)
        fm = painter.fontMetrics()

        try:
            gap_idx = art.index("")
        except ValueError:
            gap_idx = len(art)
        n1 = gap_idx
        n2 = len(art) - gap_idx - 1

        line_h  = fm.height() + 2
        gap_h   = line_h * 2
        total_h = n1 * line_h + gap_h + n2 * line_h
        start_y = max(10, (h - total_h) // 2)

        scan_y = start_y + (self._scanline_y % max(total_h, 1))
        painter.save()
        painter.setOpacity(0.06)
        painter.fillRect(0, scan_y, w, 3, QColor(120, 200, 255))
        painter.restore()

        if self._glitch_active:
            painter.save()
            painter.setOpacity(0.22)
            for i, line in enumerate(art):
                if not line:
                    continue
                txt = self._glitch_lines.get(i, line)
                tw  = fm.horizontalAdvance(txt)
                if i < n1:
                    y = start_y + i * line_h + fm.ascent()
                else:
                    y = start_y + n1 * line_h + gap_h + (i - n1 - 1) * line_h + fm.ascent()
                x = (w - tw) // 2 + 3
                painter.setPen(QColor(255, 50, 50))
                painter.drawText(int(x), int(y), txt)
            for i, line in enumerate(art):
                if not line:
                    continue
                txt = self._glitch_lines.get(i, line)
                tw  = fm.horizontalAdvance(txt)
                if i < n1:
                    y = start_y + i * line_h + fm.ascent()
                else:
                    y = start_y + n1 * line_h + gap_h + (i - n1 - 1) * line_h + fm.ascent()
                x = (w - tw) // 2 - 3
                painter.setPen(QColor(50, 50, 255))
                painter.drawText(int(x), int(y), txt)
            painter.restore()

        shake_x = int(self._glitch_offset.x())
        t = self._glitch_frame * 0.05   # slow pulse

        for i, line in enumerate(art):
            if not line:
                continue

            txt = self._glitch_lines.get(i, line)
            tw  = fm.horizontalAdvance(txt)
            x   = (w - tw) // 2 + shake_x

            if i < n1:
                y = start_y + i * line_h + fm.ascent()
                r = int(140 + 40 * math.sin(t + i * 0.3))
                g = int(80  + 20 * math.sin(t + i * 0.2 + 1))
                b = 255
                color = QColor(min(r, 255), min(g, 255), b)
            else:
                row_in_block2 = i - n1 - 1
                if row_in_block2 < 0:
                    continue
                y = start_y + n1 * line_h + gap_h + row_in_block2 * line_h + fm.ascent()
                r = 0
                g = int(200 + 40 * math.sin(t + i * 0.4))
                b = int(220 + 35 * math.sin(t + i * 0.25 + 2))
                color = QColor(r, min(g, 255), min(b, 255))

            if i in self._glitch_rgb_override:
                rgb = self._glitch_rgb_override[i]
                flicker = 0.75 + 0.25 * math.sin(t * 7 + i)
                color = QColor(
                    min(255, int(rgb[0] * flicker)),
                    min(255, int(rgb[1] * flicker)),
                    min(255, int(rgb[2] * flicker)),
                )

            painter.setPen(color)
            painter.drawText(int(x), int(y), txt)

        if self._glitch_active and self._rng.random() < 0.4:
            sl_y  = self._rng.randint(start_y, start_y + total_h)
            sl_h  = self._rng.randint(2, 5)
            painter.save()
            painter.setOpacity(0.7)
            painter.fillRect(0, sl_y, w, sl_h, bg)
            painter.restore()

        painter.end()

    def _find_app(self):
        node = self.parent()
        while node is not None:
            if hasattr(node, 'add_files_to_list'):
                return node
            node = node.parent() if hasattr(node, 'parent') else None
        return None

    def _highlight_on(self):
        app = self._find_app()
        dark = getattr(app, 'dark_mode', False) if app else False
        if dark:
            self.setStyleSheet(
                "QListWidget { border: 2px solid rgba(110,190,255,0.70);"
                " background: rgba(110,190,255,0.08); border-radius: 10px; }"
            )
        else:
            self.setStyleSheet(
                "QListWidget { border: 2px solid rgba(59,130,246,0.60);"
                " background: rgba(59,130,246,0.07); border-radius: 10px; }"
            )

    def _highlight_off(self):
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self.setStyleSheet("QListWidget {}"))
        QTimer.singleShot(50, lambda: self.setStyleSheet(""))

    def eventFilter(self, source, event):
        from PySide6.QtCore import QEvent
        if source is self.viewport():
            if event.type() == QEvent.HoverEnter or event.type() == QEvent.Enter:
                self._start_glitch_effects()
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    event.acceptProposedAction()
                    self._highlight_on()
                    return True
            elif event.type() == QEvent.DragMove:
                if event.mimeData().hasUrls():
                    event.acceptProposedAction()
                    return True
            elif event.type() == QEvent.DragLeave:
                self._highlight_off()
                return True
            elif event.type() == QEvent.Drop:
                if event.mimeData().hasUrls():
                    self._highlight_off()
                    all_paths = [
                        url.toLocalFile()
                        for url in event.mimeData().urls()
                        if url.toLocalFile() and os.path.exists(url.toLocalFile())
                    ]
                    app = self._find_app()
                    if app:
                        proj_files  = [p for p in all_paths if p.lower().endswith('.fcproj')]
                        other_files = [p for p in all_paths if not p.lower().endswith('.fcproj')]
                        for proj in proj_files:
                            app.open_project_file(proj)
                        if other_files:
                            app.add_files_to_list(other_files)
                    event.acceptProposedAction()
                    return True
                else:
                    result = super().eventFilter(source, event)
                    app = self._find_app()
                    if app and hasattr(app, 'update_file_order'):
                        app.update_file_order()
                    return result
        return super().eventFilter(source, event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._highlight_on()
        else:
            super().dragEnterEvent(event)

    def dragLeaveEvent(self, event):
        self._highlight_off()
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            self._highlight_off()
            all_paths = [
                url.toLocalFile()
                for url in event.mimeData().urls()
                if url.toLocalFile() and os.path.exists(url.toLocalFile())
            ]
            app = self._find_app()
            if app:
                proj_files  = [p for p in all_paths if p.lower().endswith('.fcproj')]
                other_files = [p for p in all_paths if not p.lower().endswith('.fcproj')]
                for proj in proj_files:
                    app.open_project_file(proj)
                if other_files:
                    app.add_files_to_list(other_files)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
            app = self._find_app()
            if app and hasattr(app, 'update_file_order'):
                app.update_file_order()