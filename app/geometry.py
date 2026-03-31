import struct
import numpy as np


# ─────────────────────────────────────────────
#  Geometry helpers
# ─────────────────────────────────────────────

def box_triangles(x0, y0, z0, x1, y1, z1):
    """Return list of triangles (each = 3×3 array) for a solid box."""
    tris = []
    corners = [
        (x0, y0, z0), 
        (x1, y0, z0), 
        (x1, y1, z0), 
        (x0, y1, z0),
        (x0, y0, z1), 
        (x1, y0, z1), 
        (x1, y1, z1), 
        (x0, y1, z1),
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

def rounded_rect_profile(x0, y0, x1, y1, radius, segments=8):
    """2D polygon for a rounded rectangle. r = corner radius."""
    pts = []
    
    # Each corner: (center_x, center_y, angle_start, angle_end)
    corners = [
        (x1 - radius, y1 - radius,  0.0,          np.pi / 2),   # top-right
        (x0 + radius, y1 - radius,  np.pi / 2,    np.pi),        # top-left
        (x0 + radius, y0 + radius,  np.pi,        3 * np.pi / 2),# bottom-left
        (x1 - radius, y0 + radius,  3 * np.pi / 2, 2 * np.pi),  # bottom-right
    ]

    for center_x, center_y, angle_start, angle_end in corners:
        for i in range(segments + 1):
            angle = angle_start + (angle_end - angle_start) * i / segments
            pts.append((center_x + radius * np.cos(angle), center_y + radius * np.sin(angle)))
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

def ring_cap_triangles(outer_points, inner_points, z):
    """Triangulate an annular ring between two profiles at height z."""
    tris = []
    n = len(outer_points)
    for i in range(n):
        op0 = np.array([outer_points[i][0],        outer_points[i][1],        z])
        op1 = np.array([outer_points[(i+1)%n][0],  outer_points[(i+1)%n][1],  z])
        ip0 = np.array([inner_points[i][0],         inner_points[i][1],        z])
        ip1 = np.array([inner_points[(i+1)%n][0],  inner_points[(i+1)%n][1],  z])
        if np.flip:
            tris.append((op0, ip0, ip1))
            tris.append((op0, ip1, op1))
        else:
            tris.append((op0, op1, ip1))
            tris.append((op0, ip1, ip0))
    return tris

def hollow_rounded_box(x0, y0, z0, x1, y1, z_top, wall, r, segments=8):
    """
    Hollow open-top box with rounded vertical corners.
    x0/y0/z0: outer origin, x1/y1: outer far corner, z_top: total height.
    wall: wall/floor thickness. r: outer corner radius.
    """
    r_outer = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
    r_inner = max(r_outer - wall, 0.0)
    z_floor = z0 + wall

    outer_points = rounded_rect_profile(x0, y0, x1, y1, r_outer, segments)
    inner_points = rounded_rect_profile(x0 + wall, y0 + wall,
                                     x1 - wall, y1 - wall, r_inner, segments)
    tris = []
    # Outer walls (normals face outward)
    tris += extrude_profile(outer_points, z0, z_top)
    # Exterior bottom face
    tris += cap_triangles(outer_points, z0, flip=True)
    # Inner walls (reversed → normals face inward)
    tris += extrude_profile(list(reversed(inner_points)), z_floor, z_top)
    # Interior floor face (faces up)
    tris += cap_triangles(inner_points, z_floor)
    # Top rim (annular ring, faces up)
    tris += ring_cap_triangles(outer_points, inner_points, z_top)
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

