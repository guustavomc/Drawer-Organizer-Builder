from geometry import box_triangles, rounded_box_triangles

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
        self.corner_radius = 0.0 #mm

        # dividers as fractions [0..1] along each axis
        self.x_dividers: list[float] = []   # vertical dividers (along X)
        self.y_dividers: list[float] = []   # horizontal dividers (along Y)

    def build_triangles(self):
        W, D, H, T = self.width, self.depth, self.height, self.wall
        R = self.corner_radius
        tris = []

        def _box(x0, y0, z0, x1, y1, z1):
            if R > 0:
                return rounded_box_triangles(x0, y0, z0, x1, y1, z1, R)
            return box_triangles(x0, y0, z0, x1, y1, z1)

        tris += _box(0, 0, 0, W, D, T)        # floor
        tris += _box(0, 0, 0, W, T, H)        # front wall
        tris += _box(0, D-T, 0, W, D, H)      # back wall
        tris += _box(0, 0, 0, T, D, H)        # left wall
        tris += _box(W-T, 0, 0, W, D, H)      # right wall

        for frac in self.x_dividers:
            x = T + frac * (W - 2*T)
            tris += box_triangles(x - T/2, T, T, x + T/2, D-T, H)  # dividers stay sharp

        for frac in self.y_dividers:
            y = T + frac * (D - 2*T)
            tris += box_triangles(T, y - T/2, T, W-T, y + T/2, H)

        return tris

