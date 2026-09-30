# Drawer-Organizer-Builder

> Parametric drawer organizer generator: a Python package that turns dimensions and divider positions into a print-ready STL, plus a desktop editor to design it visually.

It can be used in two ways:

- **As a library / product plugin** — installed by [Print-Platform](https://github.com/guustavomc/Print-Platform), which discovers it automatically and uses it to generate, slice and quote drawer organizers.
- **As a desktop app** — a PyQt editor with a 2D layout canvas and live 3D preview, for designing and exporting organizers locally.

Both use the same generator, so a design made in the desktop app produces exactly the same part the platform would print.

## Features

- **Watertight meshes** — built with boolean operations (trimesh + manifold3d), always manifold and ready for any slicer
- **Parameter validation** — minimum wall, floor and compartment sizes checked before generating
- **Rounded corners** *(in progress)* — configurable outer corner radius
- **STL and GLB export** — STL for slicers, GLB for web previews
- **Desktop editor** — drag dividers on a 2D top-down canvas and see the result in a live 3D preview

## Installation

Requires Python 3.14.

```bash
git clone https://github.com/guustavomc/Drawer-Organizer-Builder
cd Drawer-Organizer-Builder
python -m venv venv
source venv/bin/activate     # Linux/Mac
# venv\Scripts\activate      # Windows
```

Library only (what Print-Platform installs, no GUI dependencies):

```bash
python -m pip install -e .
```

With the desktop app:

```bash
python -m pip install -e ".[desktop]"
```

## Usage

### Desktop app

```bash
python -m drawer_organizer.desktop
```

- **Left panel** — set width, depth, height, wall thickness and corner radius
- **2D layout canvas** (middle) — click to add dividers, drag to move them
- **3D preview** (right) — updates as you design; drag to orbit, scroll to zoom
- **Export STL** — saves a binary STL ready for any slicer (OrcaSlicer, PrusaSlicer, Cura, Bambu Studio...)

Invalid designs (a compartment too narrow to print, a floor thicker than the box...) are flagged in the UI instead of producing a broken STL.

### As a library

```python
from drawer_organizer import DrawerOrganizerGenerator, DrawerOrganizerParams

params = DrawerOrganizerParams(
    width=120, depth=80, height=40,
    wall=1.6, floor=1.2,
    dividers_x=[40, 80],   # divider centers in mm, from the outer left edge
    dividers_y=[40],       # divider centers in mm, from the outer front edge
)

result = DrawerOrganizerGenerator().generate(params)

result.stl_bytes      # binary STL
result.to_dict()      # volume, dimensions, triangle count
```

Invalid parameters raise a Pydantic `ValidationError` explaining what is wrong.

### Parameters

All measurements in millimeters, external dimensions.

| Parameter    | Default | Description |
| ------------ | ------- | ----------- |
| `width`      | —       | External width (X) |
| `depth`      | —       | External depth (Y) |
| `height`     | —       | External height (Z) |
| `wall`       | 1.6     | Wall and divider thickness (min 1.2) |
| `floor`      | 1.2     | Floor thickness (min 0.8) |
| `dividers_x` | `[]`    | Center of each divider parallel to Y, from the outer left edge |
| `dividers_y` | `[]`    | Center of each divider parallel to X, from the outer front edge |

Every compartment must be at least 10 mm wide.

The parameters serialize to JSON (`params.model_dump_json()`). This is the same format Print-Platform's API receives, so a saved design can be sent straight to a quote.

## How it plugs into Print-Platform

This package implements the contract from [print-generator-sdk](https://github.com/guustavomc/print-generator-sdk) and registers itself as a product plugin in `pyproject.toml`:

```toml
[project]
dependencies = ["print-generator-sdk", "trimesh", "manifold3d"]

[project.optional-dependencies]
desktop = ["PyQt6", "PyOpenGL"]

[project.entry-points."print_platform.products"]
drawer-organizer = "drawer_organizer.generator:DrawerOrganizerGenerator"
```

Print-Platform only needs to install this package; it finds the generator through the entry point. The desktop dependencies are optional, so the server never installs PyQt.

## Project structure

```
Drawer-Organizer-Builder/
├── pyproject.toml
├── README.md
├── src/
│   └── drawer_organizer/
│       ├── __init__.py
│       ├── params.py          # DrawerOrganizerParams + validation
│       ├── generator.py       # DrawerOrganizerGenerator (trimesh + manifold3d)
│       └── desktop/           # Optional PyQt app
│           ├── __main__.py    # Entry point (python -m drawer_organizer.desktop)
│           ├── main_window.py # Main window and left panel controls
│           ├── layout_canvas.py # 2D interactive top-down canvas
│           └── gl_preview.py  # 3D OpenGL real-time preview
└── tests/
    ├── test_params.py
    └── test_generator.py
```

The desktop app never builds geometry itself: it keeps the UI state, converts it into `DrawerOrganizerParams` and renders the mesh returned by the generator.

## Running tests

```bash
python -m pytest -v
```

## Roadmap

- [ ] **Package split**
  - [ ] Move the generator from Print-Platform into `src/drawer_organizer/`
  - [ ] Replace the hand-built triangle geometry (`geometry.py`) with the generator
  - [ ] Move the PyQt app into `desktop/` as an optional extra
  - [ ] Register the `print_platform.products` entry point
- [ ] **Geometry**
  - [ ] Rounded outer corners (`corner_radius`)
  - [ ] Divider height override — individual dividers shorter than the box
  - [ ] Compartment labels embossed on the floor
- [ ] **Desktop editor**
  - [ ] Show validation errors inline (compartments too narrow to print)
  - [ ] Compartment dimension display (width × depth inside each cell)
  - [ ] Snap to grid / equal spacing (hold Shift while dragging)
  - [ ] Direct numeric input for divider position (double-click a divider)
  - [ ] Undo / Redo (Ctrl+Z / Ctrl+Y)
  - [ ] Save / Load design as JSON (same format as the platform API)

## Related projects

- [Print-Platform](https://github.com/guustavomc/Print-Platform) — the 3D printing platform that uses this package as a product
- [print-generator-sdk](https://github.com/guustavomc/print-generator-sdk) — the contract every product implements

## Author

**Gustavo Conceição** · [LinkedIn](https://www.linkedin.com/in/gustavo-m-conceição) · [GitHub](https://github.com/guustavomc)