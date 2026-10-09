from pydantic import Field, model_validator

from print_generator_sdk import BED_SIZE_MM, BaseProductParams

MIN_WALL_MM = 1.2          # parede mínima imprimível (3 linhas de 0.4 mm)
MIN_FLOOR_MM = 0.8         # fundo mínimo (4 camadas de 0.2 mm)
MIN_COMPARTMENT_MM = 10.0  # vão livre mínimo entre paredes/divisórias
MIN_DIVIDER_RISE_MM = 2.0  # quanto uma divisória baixa precisa subir acima do fundo


class Divider(BaseProductParams):
    """Uma divisória interna."""

    position: float = Field(description="Centro da divisória, a partir da borda externa")
    height: float | None = Field(
        default=None,
        description="Altura a partir da base externa; None usa a altura total da caixa",
    )


class DrawerOrganizerParams(BaseProductParams):
    """Parâmetros do organizador de gaveta. Todas as medidas em mm, externas."""

    width: float = Field(gt=0, le=BED_SIZE_MM[0], description="Largura externa (X)")
    depth: float = Field(gt=0, le=BED_SIZE_MM[1], description="Profundidade externa (Y)")
    height: float = Field(gt=0, le=BED_SIZE_MM[2], description="Altura externa (Z)")
    wall: float = Field(default=1.6, ge=MIN_WALL_MM, le=10, description="Espessura das paredes e divisórias")
    floor: float = Field(default=1.2, ge=MIN_FLOOR_MM, le=10, description="Espessura do fundo")
    corner_radius: float = Field(default=0.0, ge=0, description="Raio dos cantos verticais externos")

    dividers_x: list[Divider] = Field(
        default_factory=list,
        description="Divisórias paralelas ao eixo Y; position é o X a partir da borda externa esquerda",
    )
    dividers_y: list[Divider] = Field(
        default_factory=list,
        description="Divisórias paralelas ao eixo X; position é o Y a partir da borda externa frontal",
    )

    @model_validator(mode="after")
    def check_geometry(self) -> "DrawerOrganizerParams":
        if self.floor >= self.height:
            raise ValueError("floor deve ser menor que height")
        if self.corner_radius > min(self.width, self.depth) / 2:
            raise ValueError("corner_radius não pode passar da metade do menor lado")
        for name, dividers, length in (
            ("dividers_x", self.dividers_x, self.width),
            ("dividers_y", self.dividers_y, self.depth),
        ):
            _check_compartments(name, [d.position for d in dividers], length, self.wall)
            _check_heights(name, dividers, self.floor + MIN_DIVIDER_RISE_MM, self.height)
        return self


def _check_compartments(name: str, positions: list[float], length: float, wall: float) -> None:
    """Garante que todo vão entre paredes e divisórias tem pelo menos MIN_COMPARTMENT_MM."""
    centers = sorted(positions)
    starts = [wall] + [c + wall / 2 for c in centers]          # face onde cada vão começa
    ends = [c - wall / 2 for c in centers] + [length - wall]   # face onde cada vão termina
    for start, end in zip(starts, ends):
        if end - start < MIN_COMPARTMENT_MM:
            raise ValueError(
                f"{name}: vão de {end - start:.1f} mm entre {start:.1f} e {end:.1f} "
                f"(mínimo {MIN_COMPARTMENT_MM} mm)"
            )


def _check_heights(name: str, dividers: list[Divider], lowest: float, highest: float) -> None:
    """Garante que toda divisória baixa sobe acima do fundo e não passa da caixa."""
    for i, divider in enumerate(dividers):
        if divider.height is not None and not lowest <= divider.height <= highest:
            raise ValueError(
                f"{name}[{i}]: height de {divider.height:.1f} mm fora do intervalo "
                f"{lowest:.1f} a {highest:.1f} mm"
            )
