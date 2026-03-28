import struct
import numpy as np


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

def rounded_rect_profile(x0, y0, x1, y1, r, segments=8):
    """2D polygon for a rounded rectangle. r = corner radius."""
    pts = []
    
    # Each corner: (center_x, center_y, angle_start, angle_end)
    corners = [
        (x1 - r, y1 - r,  0.0,          np.pi / 2),   # top-right
        (x0 + r, y1 - r,  np.pi / 2,    np.pi),        # top-left
        (x0 + r, y0 + r,  np.pi,        3 * np.pi / 2),# bottom-left
        (x1 - r, y0 + r,  3 * np.pi / 2, 2 * np.pi),  # bottom-right
    ]

    for cx, cy, a_start, a_end in corners:
        for i in range(segments + 1):
            a = a_start + (a_end - a_start) * i / segments
            pts.append((cx + r * np.cos(a), cy + r * np.sin(a)))
    return pts

def extrude_profile(pts, z0, z1):
    """Extrude a 2D polygon (list of (x,y)) from z0 to z1. Returns triangles."""
    triangles = []
    n = len(pts)
    for i in range(n):
        # Current and next point (wraps around at the end)
        first_point = np.array([pts[i][0], pts[i][1], z0])
        second_point = np.array([pts[(i+1) % n][0], pts[(i+1) % n][1], z0])
        third_point = np.array([pts[(i+1) % n][0], pts[(i+1) % n][1], z1])
        fourth_point = np.array([pts[i][0], pts[i][1], z1])

        # Each side edge becomes 2 triangles (a quad)
        triangles.append((first_point, second_point, third_point))
        triangles.append((first_point, third_point, fourth_point))
    return triangles

def cap_triangles(pts, z, flip=False):
    """Fan-triangulate a flat polygon cap at height z."""
    triangles = []
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    center = np.array([cx, cy, z])
    n = len(pts)
    for i in range(n):
        a = np.array([pts[i][0],           pts[i][1],           z])
        b = np.array([pts[(i+1) % n][0],   pts[(i+1) % n][1],   z])
        # flip=True for the bottom cap so normals point downward
        triangles.append((center, b, a) if flip else (center, a, b))
    return triangles

def rounded_box_triangles(x0, y0, z0, x1, y1, z1, r, segments=8):
    """Solid box with rounded vertical edges. r = corner radius."""
    # Clamp radius so it never exceeds half the shorter side
    r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
    pts = rounded_rect_profile(x0, y0, x1, y1, r, segments)
    tris = []
    tris += extrude_profile(pts, z0, z1)   # side walls
    tris += cap_triangles(pts, z1)          # top cap
    tris += cap_triangles(pts, z0, flip=True)  # bottom cap
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

