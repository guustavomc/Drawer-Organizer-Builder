
import sys
import math
import struct
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QDoubleSpinBox, QSpinBox, QPushButton, QGroupBox,
    QScrollArea, QSizePolicy, QFileDialog, QMessageBox, QFrame,
    QToolBar, QStatusBar
)
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QAction, QIcon
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *


# ─────────────────────────────────────────────
#  Geometry helpers
# ─────────────────────────────────────────────

def box_triangles(x0, y0, z0, x1, y1, z1):
    """Return list of triangles (each = 3×3 array) for a solid box."""
    tris = []
    corners = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]
    faces = [
        (0,1,2,3),  # bottom
        (4,7,6,5),  # top
        (0,4,5,1),  # front
        (2,6,7,3),  # back
        (0,3,7,4),  # left
        (1,5,6,2),  # right
    ]
    for f in faces:
        a, b, c, d = [np.array(corners[i]) for i in f]
        tris.append((a, b, c))
        tris.append((a, c, d))
    return tris


def write_stl(triangles, filepath):
    """Write binary STL from a list of (v0,v1,v2) triangle tuples."""
    with open(filepath, 'wb') as f:
        f.write(b'\x00' * 80)          # header
        f.write(struct.pack('<I', len(triangles)))
        for v0, v1, v2 in triangles:
            n = np.cross(v1 - v0, v2 - v0)
            ln = np.linalg.norm(n)
            if ln > 0:
                n = n / ln
            f.write(struct.pack('<fff', *n))
            f.write(struct.pack('<fff', *v0))
            f.write(struct.pack('<fff', *v1))
            f.write(struct.pack('<fff', *v2))
            f.write(struct.pack('<H', 0))


# ─────────────────────────────────────────────
#  Organizer model
# ─────────────────────────────────────────────

class OrganizerModel:
    """Holds dimensions + divider positions and builds geometry."""

    def __init__(self):
        self.width = 120.0    # mm  X
        self.depth = 80.0     # mm  Y
        self.height = 40.0    # mm  Z
        self.wall = 2.0       # mm

        # dividers as fractions [0..1] along each axis
        self.x_dividers: list[float] = []   # vertical dividers (along X)
        self.y_dividers: list[float] = []   # horizontal dividers (along Y)

    def build_triangles(self):
        W, D, H, T = self.width, self.depth, self.height, self.wall
        tris = []

        # Outer shell (bottom + 4 walls)
        # Bottom floor
        tris += box_triangles(0, 0, 0, W, D, T)
        # Front wall
        tris += box_triangles(0, 0, 0, W, T, H)
        # Back wall
        tris += box_triangles(0, D-T, 0, W, D, H)
        # Left wall
        tris += box_triangles(0, 0, 0, T, D, H)
        # Right wall
        tris += box_triangles(W-T, 0, 0, W, D, H)

        # X dividers (run along Y, perpendicular to X axis)
        for frac in self.x_dividers:
            x = T + frac * (W - 2*T)
            tris += box_triangles(x - T/2, T, T, x + T/2, D-T, H)

        # Y dividers (run along X, perpendicular to Y axis)
        for frac in self.y_dividers:
            y = T + frac * (D - 2*T)
            tris += box_triangles(T, y - T/2, T, W-T, y + T/2, H)

        return tris


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


# ─────────────────────────────────────────────
#  3-D OpenGL preview
# ─────────────────────────────────────────────

class GLPreview(QOpenGLWidget):
    def __init__(self, model: OrganizerModel):
        super().__init__()
        self.model = model
        self._triangles = []
        self._rot_x = 30.0
        self._rot_z = -45.0
        self._zoom = 1.0
        self._last_pos = None
        self.setMinimumSize(300, 300)

    def refresh(self):
        self._triangles = self.model.build_triangles()
        self.update()

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLightfv(GL_LIGHT0, GL_POSITION, [1, 2, 3, 0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1, 1, 1, 1])
        glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.25, 0.25, 0.25, 1])
        glClearColor(0.12, 0.12, 0.18, 1)
        self._triangles = self.model.build_triangles()

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        w, h = self.width(), self.height()
        aspect = w / h if h else 1
        diag = math.sqrt(self.model.width**2 + self.model.depth**2 + self.model.height**2)
        gluPerspective(45, aspect, 1, diag * 10)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        dist = diag * 1.5 / self._zoom
        gluLookAt(0, 0, dist, 0, 0, 0, 0, 1, 0)

        cx = self.model.width / 2
        cy = self.model.depth / 2
        cz = self.model.height / 2
        glTranslatef(-cx, -cy, -cz)
        # rotate around centre
        glTranslatef(cx, cy, cz)
        glRotatef(self._rot_x, 1, 0, 0)
        glRotatef(self._rot_z, 0, 0, 1)
        glTranslatef(-cx, -cy, -cz)

        glColor3f(0.36, 0.58, 0.87)
        glBegin(GL_TRIANGLES)
        for v0, v1, v2 in self._triangles:
            n = np.cross(v1 - v0, v2 - v0)
            ln = np.linalg.norm(n)
            if ln > 0:
                n = n / ln
            glNormal3f(*n)
            glVertex3f(*v0)
            glVertex3f(*v1)
            glVertex3f(*v2)
        glEnd()

    def mousePressEvent(self, event):
        self._last_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self._last_pos:
            dx = event.pos().x() - self._last_pos.x()
            dy = event.pos().y() - self._last_pos.y()
            self._rot_z += dx * 0.5
            self._rot_x += dy * 0.5
            self._last_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        self._last_pos = None

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self._zoom *= (1.1 if delta > 0 else 0.9)
        self._zoom = max(0.2, min(10.0, self._zoom))
        self.update()


# ─────────────────────────────────────────────
#  Main Window
# ─────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.model = OrganizerModel()
        self.setWindowTitle("Organizer Creator — STL Generator")
        self.resize(1100, 700)
        self._build_ui()
        self._apply_stylesheet()

    # ── UI construction ──────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setSpacing(8)
        root.setContentsMargins(8, 8, 8, 8)

        # ── Left panel ──────────────────────
        left = QVBoxLayout()
        left.setSpacing(6)

        # Dimensions group
        dim_group = QGroupBox("Box Dimensions (mm)")
        dim_layout = QVBoxLayout(dim_group)

        self.spin_w = self._spin(10, 500, self.model.width,  "Width (X)")
        self.spin_d = self._spin(10, 500, self.model.depth,  "Depth (Y)")
        self.spin_h = self._spin(5,  300, self.model.height, "Height (Z)")
        self.spin_t = self._spin(0.5, 10, self.model.wall,   "Wall thickness")

        for label, spin in [("Width (X):", self.spin_w),
                             ("Depth (Y):", self.spin_d),
                             ("Height (Z):", self.spin_h),
                             ("Wall (mm):", self.spin_t)]:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            row.addWidget(spin)
            dim_layout.addLayout(row)

        for spin in [self.spin_w, self.spin_d, self.spin_h, self.spin_t]:
            spin.valueChanged.connect(self._on_dim_changed)

        left.addWidget(dim_group)

        # Divider count shortcuts
        div_group = QGroupBox("Quick Dividers")
        div_layout = QVBoxLayout(div_group)

        row_x = QHBoxLayout()
        row_x.addWidget(QLabel("X dividers:"))
        self.spin_nx = QSpinBox(); self.spin_nx.setRange(0, 20); self.spin_nx.setValue(0)
        self.spin_nx.valueChanged.connect(self._on_nx_changed)
        row_x.addWidget(self.spin_nx)
        div_layout.addLayout(row_x)

        row_y = QHBoxLayout()
        row_y.addWidget(QLabel("Y dividers:"))
        self.spin_ny = QSpinBox(); self.spin_ny.setRange(0, 20); self.spin_ny.setValue(0)
        self.spin_ny.valueChanged.connect(self._on_ny_changed)
        row_y.addWidget(self.spin_ny)
        div_layout.addLayout(row_y)

        left.addWidget(div_group)

        # Clear button
        btn_clear = QPushButton("🗑  Clear all dividers")
        btn_clear.clicked.connect(self._clear_dividers)
        left.addWidget(btn_clear)

        # Info box
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        left.addWidget(self.info_label)
        self._update_info()

        left.addStretch()

        # Export button
        btn_export = QPushButton("💾  Export STL…")
        btn_export.setFixedHeight(40)
        btn_export.clicked.connect(self._export_stl)
        left.addWidget(btn_export)

        left_widget = QWidget(); left_widget.setLayout(left)
        left_widget.setFixedWidth(220)
        root.addWidget(left_widget)

        # ── Middle: 2D canvas ────────────────
        mid = QVBoxLayout()
        mid.addWidget(QLabel("Layout View  (Left-click → X divider · Right-click → Y divider · Drag · Del)"))
        self.canvas = LayoutCanvas(self.model)
        self.canvas.modelChanged.connect(self._on_layout_changed)
        self.canvas.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        mid.addWidget(self.canvas)
        root.addLayout(mid, 2)

        # ── Right: 3D preview ────────────────
        right = QVBoxLayout()
        right.addWidget(QLabel("3D Preview  (Drag to rotate · Scroll to zoom)"))
        self.gl = GLPreview(self.model)
        right.addWidget(self.gl)
        root.addLayout(right, 2)

        # Status bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready — design your organizer and export to STL.")

    def _spin(self, lo, hi, val, tip):
        s = QDoubleSpinBox()
        s.setRange(lo, hi)
        s.setValue(val)
        s.setSingleStep(1.0)
        s.setToolTip(tip)
        return s

    # ── Stylesheet ───────────────────────────

    def _apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #1e1e2e; color: #cdd6f4; font-size: 13px; }
            QGroupBox { border: 1px solid #45475a; border-radius: 6px;
                        margin-top: 8px; padding: 6px; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; color: #89b4fa; }
            QDoubleSpinBox, QSpinBox { background: #313244; border: 1px solid #45475a;
                                       border-radius: 4px; padding: 2px 4px; color: #cdd6f4; }
            QPushButton { background: #313244; border: 1px solid #45475a; border-radius: 6px;
                          padding: 6px 12px; color: #cdd6f4; }
            QPushButton:hover { background: #45475a; }
            QPushButton:pressed { background: #89b4fa; color: #1e1e2e; }
            QLabel { color: #cdd6f4; }
            QStatusBar { background: #181825; color: #6c7086; }
        """)

    # ── Slots ────────────────────────────────

    def _on_dim_changed(self):
        self.model.width  = self.spin_w.value()
        self.model.depth  = self.spin_d.value()
        self.model.height = self.spin_h.value()
        self.model.wall   = self.spin_t.value()
        self.canvas.update()
        self.gl.refresh()
        self._update_info()

    def _on_layout_changed(self):
        self.gl.refresh()
        self.spin_nx.blockSignals(True)
        self.spin_ny.blockSignals(True)
        self.spin_nx.setValue(len(self.model.x_dividers))
        self.spin_ny.setValue(len(self.model.y_dividers))
        self.spin_nx.blockSignals(False)
        self.spin_ny.blockSignals(False)
        self._update_info()

    def _on_nx_changed(self, n):
        current = len(self.model.x_dividers)
        if n > current:
            for _ in range(n - current):
                self.model.x_dividers.append(
                    (len(self.model.x_dividers) + 1) / (n + 1))
        elif n < current:
            self.model.x_dividers = self.model.x_dividers[:n]
        self.model.x_dividers = [
            (i + 1) / (n + 1) for i in range(n)]
        self.canvas.update()
        self.gl.refresh()
        self._update_info()

    def _on_ny_changed(self, n):
        self.model.y_dividers = [
            (i + 1) / (n + 1) for i in range(n)]
        self.canvas.update()
        self.gl.refresh()
        self._update_info()

    def _clear_dividers(self):
        self.model.x_dividers.clear()
        self.model.y_dividers.clear()
        self.spin_nx.setValue(0)
        self.spin_ny.setValue(0)
        self.canvas.update()
        self.gl.refresh()
        self._update_info()

    def _update_info(self):
        nx = len(self.model.x_dividers)
        ny = self.model.y_dividers.__len__()
        compartments = (nx + 1) * (ny + 1)
        self.info_label.setText(
            f"<b>Compartments:</b> {compartments}<br>"
            f"X dividers: {nx}<br>"
            f"Y dividers: {ny}<br>"
            f"Triangles: ~{len(self.model.build_triangles())}"
        )

    def _export_stl(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save STL", "organizer.stl", "STL files (*.stl)")
        if not path:
            return
        try:
            tris = self.model.build_triangles()
            write_stl(tris, path)
            QMessageBox.information(self, "Exported",
                f"STL saved to:\n{path}\n\n{len(tris)} triangles")
            self.statusBar().showMessage(f"Exported {len(tris)} triangles → {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("Organizer Creator")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
