import trimesh
from pydantic import Field, model_validator

from core.base import BaseProductGenerator, GenerationResult
from core.mesh_utils import BED_SIZE_MM, build_result
from src.drawer_organizer.params import DrawerOrganizerParams

MIN_WALL_MM = 1.2         # parede mínima imprimível (3 linhas de 0.4 mm)
MIN_FLOOR_MM = 0.8        # fundo mínimo (4 camadas de 0.2 mm)
MIN_COMPARTMENT_MM = 10.0  # vão livre mínimo entre paredes/divisórias

def _box(size: tuple[float, float, float], min_corner: tuple[float, float, float]) -> trimesh.Trimesh:
    """Caixa com o canto mínimo em min_corner (trimesh cria centrado na origem)."""
    box = trimesh.creation.box(extents=size)
    box.apply_translation([m + s / 2 for m, s in zip(min_corner, size)])
    return box


class DrawerOrganizerGenerator(BaseProductGenerator):
    """Bandeja aberta no topo com divisórias internas em X e Y."""

    def generate(self, params: DrawerOrganizerParams) -> GenerationResult:
        w, d, h, t, f = params.width, params.depth, params.height, params.wall, params.floor

        outer = _box((w, d, h), (0, 0, 0))
        # Cavidade começa no fundo e passa do topo, deixando a bandeja aberta
        cavity = _box((w - 2 * t, d - 2 * t, h), (t, t, f))
        tray = outer.difference(cavity)

        # Divisórias ocupam a altura e a profundidade/largura totais: sobrepõem
        # paredes e fundo, então a união funde tudo em um sólido só
        dividers = [_box((t, d, h), (x - t / 2, 0, 0)) for x in params.dividers_x]
        dividers += [_box((w, t, h), (0, y - t / 2, 0)) for y in params.dividers_y]
        if dividers:
            tray = trimesh.boolean.union([tray, *dividers])

        return build_result(tray)