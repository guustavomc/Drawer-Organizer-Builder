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
