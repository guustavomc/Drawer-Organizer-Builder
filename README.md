# Drawer-Organizer-Builder

## Overview

This is a Python project for a tool for automatic STL file generation. Designed for creation of 3d printing models.

- Left panel — set box width/depth/height/wall thickness via spinboxes.

- 2D Layout Canvas (middle) — interactive top-down view.

- 3D Preview (right) — live OpenGL render that updates instantly as you design. Drag to orbit, scroll to zoom.

- Export — click Export STL to save a binary STL ready for any slicer (PrusaSlicer, Cura, Bambu Studio, etc.).

## Installation

1. Clone the project
```bash
git clone https://github.com/guustavomc/Drawer-Organizer-Builder
cd Drawer-Organizer-Builder
```

2. Create virtual environment (optional)
```bash
python -m venv venv
source venv/bin/activate     # Linux/Mac
# venv\Scripts\activate      # Windows
```

3. Install dependencies
```bash
pip install PyQt6 PyOpenGL PyOpenGL_accelerate numpy numpy-stl
```

4. Run the project
```bash
cd .\app\
python main.py
```

## Future Features

- **Compartment dimension display** — show width × depth (in mm) inside each cell on the 2D canvas, plus X/Y coordinates for each divider vertex on hover
- **Snap to grid / equal spacing** — hold Shift while dragging a divider to snap it to evenly-spaced positions
- **Undo / Redo (Ctrl+Z / Ctrl+Y)** — history stack for divider additions, deletions, and moves
- **Direct numeric input for divider position** — double-click a divider to type its exact mm position
- **Minimum compartment size warning** — highlight compartments that are too narrow to print (below `2 × wall thickness`)
- **Save / Load design (JSON)** — export and reload full designs including dimensions and divider positions
- **Compartment labels** — type short labels per compartment shown in the 2D canvas and optionally embossed on the STL floor
- **Divider height override** — set individual dividers shorter than the full box height

## Project Structure

```
Drawer-Organizer-Builder/
├── README.md
└── app/
    ├── main.py            # Entry point
    ├── model.py           # Data model (box/compartment state)
    ├── geometry.py        # STL geometry generation
    └── ui/
        ├── __init__.py
        ├── main_window.py # Main application window and left panel controls
        ├── layout_canvas.py # 2D interactive top-down canvas
        └── gl_preview.py  # 3D OpenGL real-time preview
```