from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QDoubleSpinBox, QSpinBox, QPushButton, QGroupBox,
    QFileDialog, QMessageBox, QStatusBar)
from PyQt6.QtCore import Qt

from geometry import write_stl
from model import OrganizerModel
from ui.gl_preview import GLPreview
from ui.layout_canvas import LayoutCanvas

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
        mid.addWidget(QLabel("Layout View  (Left-click: add X divider   Right-click: add Y divider   Drag to move   Del to remove)"))
        self.canvas = LayoutCanvas(self.model)
        self.canvas.modelChanged.connect(self._on_layout_changed)
        self.canvas.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        mid.addWidget(self.canvas)
        root.addLayout(mid, 1)

        # ── Right: 3D preview ────────────────
        right = QVBoxLayout()
        right.addWidget(QLabel("3D Preview  (Drag to rotate · Scroll to zoom)"))
        self.gl = GLPreview(self.model)
        right.addWidget(self.gl)
        root.addLayout(right, 1)

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
            QMainWindow, QWidget { background: #1b1b1b; color: #cdd6f4; font-size: 13px; }
            QGroupBox { border: 1px solid #45475a; border-radius: 6px;
                        margin-top: 8px; padding: 6px; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; color: #89b4fa; }
            QDoubleSpinBox, QSpinBox { background: #121212; border: 1px solid #45475a;
                                       border-radius: 4px; padding: 2px 4px; color: #cdd6f4; }
            QPushButton { background: #121212; border: 1px solid #45475a; border-radius: 5px;
                          padding: 5px 12px; color: #cdd6f4; }
            QPushButton:hover { background: #121212; }
            QPushButton:pressed { background: #121212; color: #1e1e2e; }
            QLabel { color: #cdd6f4; }
            QStatusBar { background: #1b1b1b; color: #6c7086; }
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
