from drawer_organizer import DrawerOrganizerGenerator, DrawerOrganizerParams


class OrganizerModel:
    """Estado da interface. Não gera geometria: delega ao gerador."""

    def __init__(self):
        self.width = 120.0
        self.depth = 80.0
        self.height = 40.0
        self.wall = 2.0
        self.floor = 1.2
        self.corner_radius = 0.0
        # frações [0..1] do vão interno; a interface trabalha assim
        self.x_dividers: list[float] = []
        self.y_dividers: list[float] = []

    def to_params(self) -> DrawerOrganizerParams:
        T = self.wall
        return DrawerOrganizerParams(
            width=self.width, depth=self.depth, height=self.height,
            wall=T, floor=self.floor, corner_radius=self.corner_radius,
            dividers_x=[T + f * (self.width - 2 * T) for f in self.x_dividers],
            dividers_y=[T + f * (self.depth - 2 * T) for f in self.y_dividers],
        )

    def build(self):
        """Gera a peça. Levanta ValidationError se o design não é imprimível."""
        return DrawerOrganizerGenerator().generate(self.to_params())