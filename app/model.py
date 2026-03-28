from geometry import box_triangles, hollow_rounded_box, rounded_box_triangles

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

        if R > 0:
            tris += hollow_rounded_box(0, 0, 0, W, D, H, T, R)
        else:
            tris += box_triangles(0, 0, 0, W, D, T)        # floor
            tris += box_triangles(0, 0, 0, W, T, H)        # front wall
            tris += box_triangles(0, D-T, 0, W, D, H)      # back wall
            tris += box_triangles(0, 0, 0, T, D, H)        # left wall
            tris += box_triangles(W-T, 0, 0, W, D, H)      # right wall

        for frac in self.x_dividers:
            x = T + frac * (W - 2*T)
            tris += box_triangles(x - T/2, T, T, x + T/2, D-T, H)

        for frac in self.y_dividers:
            y = T + frac * (D - 2*T)
            tris += box_triangles(T, y - T/2, T, W-T, y + T/2, H)

        return tris

