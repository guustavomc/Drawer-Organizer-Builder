from PyQt6.QtWidgets import (
   QWidget, QSizePolicy)
from PyQt6.QtCore import Qt, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

from model import OrganizerModel
# ─────────────────────────────────────────────
#  2-D layout canvas
# ─────────────────────────────────────────────

class LayoutCanvas(QWidget):
    """Top-down 2D view. Click to add/remove dividers."""

    modelChanged = pyqtSignal()

    MARGIN = 20
    DIVIDER_HIT = 6   # pixels

    def __init__(self, model: OrganizerModel):
        super().__init__()
        self.model = model
        self.setMinimumSize(300, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self._drag = None       # ('x'|'y', index)
        self._hover = None
        self._mode = 'add'      # 'add' | 'remove'

    def set_mode(self, mode):
        self._mode = mode
        self.update()

    # ── coordinate helpers ──────────────────

    def _box_rect(self):
        """Pixel rect for the organizer footprint."""
        w, h = self.width() - 2*self.MARGIN, self.height() - 2*self.MARGIN
        m = self.model
        aspect = m.width / m.depth
        if w / h > aspect:
            bh = h; bw = int(h * aspect)
        else:
            bw = w; bh = int(w / aspect)
        ox = self.MARGIN + (w - bw) // 2
        oy = self.MARGIN + (h - bh) // 2
        return QRect(ox, oy, bw, bh)

    def _frac_to_px(self, frac, axis, r):
        T = self.model.wall
        if axis == 'x':
            inner = r.width() * (1 - 2*T/self.model.width)
            return r.left() + int(r.width() * T/self.model.width + frac * inner)
        else:
            inner = r.height() * (1 - 2*T/self.model.depth)
            return r.top() + int(r.height() * T/self.model.depth + frac * inner)

    def _px_to_frac(self, px, axis, r):
        T = self.model.wall
        if axis == 'x':
            inner_px = r.width() * (1 - 2*T/self.model.width)
            offset_px = r.width() * T/self.model.width
            return (px - r.left() - offset_px) / inner_px
        else:
            inner_px = r.height() * (1 - 2*T/self.model.depth)
            offset_px = r.height() * T/self.model.depth
            return (px - r.top() - offset_px) / inner_px

    # ── painting ────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self._box_rect()

        # background
        p.fillRect(self.rect(), QColor('#1e1e2e'))

        # box fill
        p.fillRect(r, QColor('#313244'))

        # wall inset shade
        T = self.model.wall
        tx = int(r.width()  * T / self.model.width)
        ty = int(r.height() * T / self.model.depth)
        inner = r.adjusted(tx, ty, -tx, -ty)
        p.fillRect(inner, QColor('#45475a'))

        # dividers
        pen_div = QPen(QColor('#89b4fa'), 2)
        p.setPen(pen_div)
        for frac in self.model.x_dividers:
            px = self._frac_to_px(frac, 'x', r)
            p.drawLine(px, inner.top(), px, inner.bottom())

        for frac in self.model.y_dividers:
            py = self._frac_to_px(frac, 'y', r)
            p.drawLine(inner.left(), py, inner.right(), py)

        # hover highlight
        if self._hover:
            axis, idx = self._hover
            pen_h = QPen(QColor('#f38ba8'), 2, Qt.PenStyle.DashLine)
            p.setPen(pen_h)
            if axis == 'x':
                px = self._frac_to_px(self.model.x_dividers[idx], 'x', r)
                p.drawLine(px, inner.top(), px, inner.bottom())
            else:
                py = self._frac_to_px(self.model.y_dividers[idx], 'y', r)
                p.drawLine(inner.left(), py, inner.right(), py)

        # border
        p.setPen(QPen(QColor('#cdd6f4'), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(r)

        # labels
        p.setPen(QColor('#a6adc8'))
        p.setFont(QFont('Arial', 8))
        p.drawText(r.left(), r.bottom() + 14,
                   f"W: {self.model.width:.0f}mm  D: {self.model.depth:.0f}mm")

        # instructions
        p.setFont(QFont('Arial', 9))
        p.setPen(QColor('#6c7086'))
        p.drawText(self.MARGIN, self.height() - 4,
                   "Left-click: add X divider   Right-click: add Y divider   Drag to move   Del to remove")

    # ── mouse interaction ────────────────────

    def _hit_divider(self, pos):
        r = self._box_rect()
        for i, frac in enumerate(self.model.x_dividers):
            px = self._frac_to_px(frac, 'x', r)
            if abs(pos.x() - px) <= self.DIVIDER_HIT:
                return ('x', i)
        for i, frac in enumerate(self.model.y_dividers):
            py = self._frac_to_px(frac, 'y', r)
            if abs(pos.y() - py) <= self.DIVIDER_HIT:
                return ('y', i)
        return None

    def mousePressEvent(self, event):
        r = self._box_rect()
        pos = event.pos()
        hit = self._hit_divider(pos)
        if hit:
            if event.button() == Qt.MouseButton.LeftButton:
                self._drag = hit
            return
        if not r.contains(pos):
            return
        if event.button() == Qt.MouseButton.LeftButton:
            frac = max(0.01, min(0.99, self._px_to_frac(pos.x(), 'x', r)))
            self.model.x_dividers.append(frac)
            self.model.x_dividers.sort()
        elif event.button() == Qt.MouseButton.RightButton:
            frac = max(0.01, min(0.99, self._px_to_frac(pos.y(), 'y', r)))
            self.model.y_dividers.append(frac)
            self.model.y_dividers.sort()
        self.modelChanged.emit()
        self.update()

    def mouseMoveEvent(self, event):
        r = self._box_rect()
        pos = event.pos()
        if self._drag:
            axis, idx = self._drag
            if axis == 'x':
                frac = max(0.01, min(0.99, self._px_to_frac(pos.x(), 'x', r)))
                self.model.x_dividers[idx] = frac
            else:
                frac = max(0.01, min(0.99, self._px_to_frac(pos.y(), 'y', r)))
                self.model.y_dividers[idx] = frac
            self.modelChanged.emit()
            self.update()
        else:
            self._hover = self._hit_divider(pos)
            self.update()

    def mouseReleaseEvent(self, event):
        if self._drag:
            self.model.x_dividers.sort()
            self.model.y_dividers.sort()
            self._drag = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete and self._hover:
            axis, idx = self._hover
            if axis == 'x':
                del self.model.x_dividers[idx]
            else:
                del self.model.y_dividers[idx]
            self._hover = None
            self.modelChanged.emit()
            self.update()

    def focusOutEvent(self, event):
        self._hover = None
        self.update()
