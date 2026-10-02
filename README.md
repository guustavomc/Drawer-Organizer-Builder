# Drawer-Organizer-Builder

> Parametric drawer organizer generator: turns dimensions and divider positions into a print-ready STL, with a desktop editor to design it visually.

It can be used in two ways:

- **As a desktop app**: a PyQt editor with a 2D layout canvas and a live 3D preview, for designing and exporting organizers locally.
- **As a library / product plugin**: installed by [Print-Platform](https://github.com/guustavomc/Print-Platform), which discovers it automatically and uses it to generate, slice and quote drawer organizers.

Both use the same generator, so a design made in the desktop app produces exactly the same part the platform would print.

## Features

- **Watertight meshes**: built with boolean operations (trimesh + manifold3d), always manifold and ready for any slicer
- **Parameter validation**: minimum wall, floor and compartment sizes are checked before generating
- **Rounded corners**: configurable outer corner radius, with walls of constant thickness
- **STL and GLB export**: STL for slicers, GLB for web previews
- **Desktop editor**: drag dividers on a 2D top-down canvas and see the result in a live 3D preview

## Requirements

- Python 3.12 or newer
- Git (the SDK is installed from GitHub)
- For the desktop app: a machine with OpenGL support

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/guustavomc/Drawer-Organizer-Builder
cd Drawer-Organizer-Builder
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
```

```bash
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows (cmd / PowerShell)
```

### 3. Install

Choose what you need. The parts in brackets are optional extras:

```bash
python -m pip install -e ".[desktop]"       # library + desktop app
python -m pip install -e ".[desktop,dev]"   # library + desktop app + test tools
python -m pip install -e .                  # library only (what Print-Platform installs)
```

`-e` (editable) links the installed package to this folder, so code changes take effect without reinstalling. The [Print-Generator-SDK](https://github.com/guustavomc/Print-Generator-SDK) is downloaded from GitHub automatically.

### 4. Run the desktop app

```bash
python -m drawer_organizer.desktop
```

Installing the package also creates a shortcut command, so this works too:

```bash
drawer-organizer
```

### 5. Run the tests

Requires the `dev` extra:

```bash
python -m pytest -v
```

## Using the desktop app

- **Left panel**: set width, depth, height, wall thickness, floor thickness and corner radius; add evenly spaced dividers with the X/Y counters
- **2D layout canvas** (middle):
  - Left-click: add an X divider
  - Right-click: add a Y divider
  - Drag: move a divider
  - Hover + `Delete`: remove a divider
- **3D preview** (right): updates as you design; drag to orbit, scroll to zoom
- **Info box**: number of compartments, volume and triangle count
- **Export STL**: saves a binary STL ready for any slicer (OrcaSlicer, PrusaSlicer, Cura, Bambu Studio...)

Invalid designs (a compartment too narrow to print, a floor thicker than the box...) are shown in red in the status bar. The preview keeps the last valid part, and export is blocked until the design is fixed.

## Using it as a library

```python
from drawer_organizer import DrawerOrganizerGenerator, DrawerOrganizerParams

params = DrawerOrganizerParams(
    width=120, depth=80, height=40,
    wall=1.6, floor=1.2,
    corner_radius=5,
    dividers_x=[40, 80],   # divider centers in mm, from the outer left edge
    dividers_y=[40],       # divider centers in mm, from the outer front edge
)

result = DrawerOrganizerGenerator().generate(params)

with open("organizer.stl", "wb") as f:
    f.write(result.stl_bytes)

print(result.to_dict())   # volume, dimensions, watertight flag, triangle count
```

Invalid parameters raise a Pydantic `ValidationError` explaining what is wrong:

```python
DrawerOrganizerParams(width=120, depth=80, height=40, dividers_x=[40, 45])
# ValidationError: dividers_x: vão de 3.4 mm entre 40.8 e 44.2 (mínimo 10.0 mm)
```

### Parameters

All measurements in millimeters, external dimensions.

| Parameter       | Default | Description |
| --------------- | ------- | ----------- |
| `width`         | —       | External width (X), up to 256 |
| `depth`         | —       | External depth (Y), up to 256 |
| `height`        | —       | External height (Z), up to 256 |
| `wall`          | 1.6     | Wall and divider thickness (1.2 to 10) |
| `floor`         | 1.2     | Floor thickness (0.8 to 10, less than `height`) |
| `corner_radius` | 0       | Outer vertical corner radius (up to half of the smaller side) |
| `dividers_x`    | `[]`    | Center of each divider parallel to Y, from the outer left edge |
| `dividers_y`    | `[]`    | Center of each divider parallel to X, from the outer front edge |

Every compartment must be at least 10 mm wide.

The parameters serialize to JSON (`params.model_dump_json()`), the same format Print-Platform's API receives, so a saved design can be sent straight to a quote.

## How it plugs into Print-Platform

This package implements the contract from [Print-Generator-SDK](https://github.com/guustavomc/Print-Generator-SDK) and registers itself as a product plugin in `pyproject.toml`:

```toml
[project.entry-points."print_platform.products"]
drawer-organizer = "drawer_organizer.generator:DrawerOrganizerGenerator"
```

Print-Platform only needs to install this package; it finds the generator through that entry point. The desktop dependencies are an optional extra, so the server never installs PyQt.

## Development

### Working on the SDK at the same time

Clone both repositories side by side:

```
workspace/
├── Print-Generator-SDK/
└── Drawer-Organizer-Builder/
```

Then, inside this project's virtual environment, install the SDK from your local copy **before** installing this package:

```bash
python -m pip install -e ../Print-Generator-SDK
python -m pip install -e ".[desktop,dev]"
```

pip sees the SDK is already installed and keeps your local copy, so changes to the SDK show up here immediately.

### What the tests cover

- `tests/test_params.py`: parameter validation (minimums, compartment sizes, corner radius, unknown fields, JSON round trip)
- `tests/test_generator.py`: generated meshes are watertight with the right dimensions (with and without dividers and rounded corners), dividers add the expected volume, dividers don't stick out of rounded corners, STL is binary, and the plugin is registered for Print-Platform

## Project structure

```
Drawer-Organizer-Builder/
├── pyproject.toml               # Package metadata, dependencies, extras and entry points
├── README.md
├── src/
│   └── drawer_organizer/
│       ├── __init__.py          # Public API: DrawerOrganizerParams, DrawerOrganizerGenerator
│       ├── params.py            # Parameters and validation
│       ├── generator.py         # Mesh generation (trimesh + manifold3d)
│       └── desktop/             # Optional PyQt app
│           ├── __main__.py      # Entry point (python -m drawer_organizer.desktop)
│           ├── model.py         # UI state → DrawerOrganizerParams
│           ├── main_window.py   # Main window and left panel controls
│           ├── layout_canvas.py # 2D interactive top-down canvas
│           └── gl_preview.py    # 3D OpenGL real-time preview
└── tests/
    ├── test_params.py
    └── test_generator.py
```

The desktop app never builds geometry itself: `model.py` keeps the UI state (dividers as fractions of the inner space), converts it into `DrawerOrganizerParams` and the preview renders the mesh returned by the generator.

## Roadmap

- [x] **Package split**
  - [x] Move the generator from Print-Platform into `src/drawer_organizer/`
  - [x] Replace the hand-built triangle geometry (`geometry.py`) with the generator
  - [x] Move the PyQt app into `desktop/` as an optional extra
  - [x] Register the `print_platform.products` entry point
- [ ] **Geometry**
  - [x] Rounded outer corners (`corner_radius`)
  - [ ] Divider height override: individual dividers shorter than the box
  - [ ] Compartment labels embossed on the floor
- [ ] **Desktop editor**
  - [x] Show validation errors inline
  - [ ] Compartment dimension display (width × depth inside each cell)
  - [ ] Snap to grid / equal spacing (hold Shift while dragging)
  - [ ] Direct numeric input for divider position (double-click a divider)
  - [ ] Undo / Redo (Ctrl+Z / Ctrl+Y)
  - [ ] Save / Load design as JSON (same format as the platform API)

## Related projects

- [Print-Platform](https://github.com/guustavomc/Print-Platform): the 3D printing platform that uses this package as a product
- [Print-Generator-SDK](https://github.com/guustavomc/Print-Generator-SDK): the contract every product implements

## Author

**Gustavo Conceição** · [LinkedIn](https://www.linkedin.com/in/gustavo-m-conceição) · [GitHub](https://github.com/guustavomc)