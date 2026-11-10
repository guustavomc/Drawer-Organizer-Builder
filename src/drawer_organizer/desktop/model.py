from dataclasses import dataclass
from .. import Divider, DrawerOrganizerGenerator, DrawerOrganizerParams
from ..params import MIN_COMPARTMENT_MM

@dataclass
class DividerState:
    """Uma divisória como a interface a guarda."""

    frac: float                  # fração [0..1] do vão interno
    height: float | None = None  # mm a partir da base externa; None = altura total

class OrganizerModel:
    """Estado da interface. Não gera geometria: delega ao gerador."""

    def __init__(self):
        self.width = 120.0
        self.depth = 80.0
        self.height = 40.0
        self.wall = 1.6
        self.floor = 1.2
        self.corner_radius = 0.0
        self.x_dividers: list[DividerState] = []
        self.y_dividers: list[DividerState] = []

    def sort_dividers(self) -> None:
        self.x_dividers.sort(key=lambda d: d.frac)
        self.y_dividers.sort(key=lambda d: d.frac)

    def to_params(self) -> DrawerOrganizerParams:
        T = self.wall
        return DrawerOrganizerParams(
            width=self.width, depth=self.depth, height=self.height,
            wall=T, floor=self.floor, corner_radius=self.corner_radius,
            dividers_x=[
                Divider(position=round(T + d.frac * (self.width - 2 * T), 3), height=d.height)
                for d in self.x_dividers
            ],
            dividers_y=[
                Divider(position=round(T + d.frac * (self.depth - 2 * T), 3), height=d.height)
                for d in self.y_dividers
            ],
        )

    def load_params(self, params: DrawerOrganizerParams) -> None:
        """Substitui o estado pelo de um design salvo (inverso de to_params)."""
        T = params.wall
        self.width, self.depth, self.height = params.width, params.depth, params.height
        self.wall, self.floor, self.corner_radius = T, params.floor, params.corner_radius
        self.x_dividers = [
            DividerState((d.position - T) / (params.width - 2 * T), d.height)
            for d in params.dividers_x
        ]
        self.y_dividers = [
            DividerState((d.position - T) / (params.depth - 2 * T), d.height)
            for d in params.dividers_y
        ]
        self.sort_dividers()

    def compartment_sizes(self, axis: str) -> list[float]:
        """Vão livre (mm) de cada compartimento num eixo, de face a face."""
        T = self.wall
        length = self.width if axis == 'x' else self.depth
        divs = self.x_dividers if axis == 'x' else self.y_dividers
        centers = sorted(T + d.frac * (length - 2 * T) for d in divs)
        starts = [T] + [c + T / 2 for c in centers]
        ends = [c - T / 2 for c in centers] + [length - T]
        return [e - s for s, e in zip(starts, ends)]

    def compartment_size_range(self, axis: str, idx: int) -> tuple[float, float]:
        """Tamanhos válidos (mm) do compartimento antes da divisória idx.

        A divisória só divide o espaço entre os dois vizinhos, então a soma
        deles é fixa: o da esquerda vai de MIN até (soma - MIN).
        Supõe as divisórias ordenadas.
        """
        sizes = self.compartment_sizes(axis)
        return MIN_COMPARTMENT_MM, sizes[idx] + sizes[idx + 1] - MIN_COMPARTMENT_MM

    def set_compartment_size(self, axis: str, idx: int, size: float) -> None:
        """Move a divisória idx para que o compartimento antes dela tenha size mm.

        Inverso de compartment_sizes; o compartimento depois dela absorve a
        diferença. Supõe as divisórias ordenadas.
        """
        T = self.wall
        length = self.width if axis == 'x' else self.depth
        divs = self.x_dividers if axis == 'x' else self.y_dividers
        inner = length - 2 * T
        start = T if idx == 0 else T + divs[idx - 1].frac * inner + T / 2
        center = start + size + T / 2
        divs[idx].frac = (center - T) / inner

    def build(self):
        """Gera a peça. Levanta ValidationError se o design não é imprimível."""
        return DrawerOrganizerGenerator().generate(self.to_params())
