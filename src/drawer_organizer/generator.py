import trimesh
from manifold3d import CrossSection, JoinType

from print_generator_sdk import BaseProductGenerator, GenerationResult, build_result

from .params import DrawerOrganizerParams

CORNER_SEGMENTS = 32  # pontos por volta completa nos cantos arredondados


def _box(size: tuple[float, float, float], min_corner: tuple[float, float, float]) -> trimesh.Trimesh:
    """Caixa com o canto mínimo em min_corner (trimesh cria centrado na origem)."""
    box = trimesh.creation.box(extents=size)
    box.apply_translation([m + s / 2 for m, s in zip(min_corner, size)])
    return box


def _rounded_prism(
    size: tuple[float, float, float], min_corner: tuple[float, float, float], radius: float
) -> trimesh.Trimesh:
    """Caixa com os cantos verticais arredondados; com radius 0 vira uma caixa comum."""
    w, d, h = size
    if radius <= 0:
        return _box(size, min_corner)
    # Retângulo encolhido pelo raio e depois expandido com junta redonda
    profile = CrossSection.square((w - 2 * radius, d - 2 * radius)).offset(
        radius, JoinType.Round, circular_segments=CORNER_SEGMENTS
    )
    mesh = profile.extrude(h).to_mesh()
    prism = trimesh.Trimesh(vertices=mesh.vert_properties[:, :3], faces=mesh.tri_verts)
    prism.apply_translation([min_corner[0] + radius, min_corner[1] + radius, min_corner[2]])
    return prism


class DrawerOrganizerGenerator(BaseProductGenerator):
    """Bandeja aberta no topo com divisórias internas em X e Y."""

    def generate(self, params: DrawerOrganizerParams) -> GenerationResult:
        w, d, h, t, f = params.width, params.depth, params.height, params.wall, params.floor
        r = params.corner_radius

        outer = _rounded_prism((w, d, h), (0, 0, 0), r)
        # Cavidade começa no fundo e passa do topo, deixando a bandeja aberta.
        # O raio interno acompanha o externo para a parede ter espessura constante.
        cavity = _rounded_prism((w - 2 * t, d - 2 * t, h), (t, t, f), max(r - t, 0.0))
        tray = outer.difference(cavity)

        # Divisórias ocupam a altura e a profundidade/largura totais: sobrepõem
        # paredes e fundo, então a união funde tudo em um sólido só. A interseção
        # com o contorno externo corta o que sairia pelos cantos arredondados.
        dividers = [_box((t, d, h), (x - t / 2, 0, 0)) for x in params.dividers_x]
        dividers += [_box((w, t, h), (0, y - t / 2, 0)) for y in params.dividers_y]
        if dividers:
            inside = trimesh.boolean.union(dividers).intersection(outer)
            tray = tray.union(inside)

        return build_result(tray)