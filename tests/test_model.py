import pytest

from drawer_organizer import DrawerOrganizerParams
from drawer_organizer.desktop.model import DividerState, OrganizerModel


def test_to_params_converts_fractions_to_mm():
    model = OrganizerModel()  # 120 × 80, parede 1.6
    model.x_dividers = [DividerState(0.5)]
    model.y_dividers = [DividerState(0.25)]
    params = model.to_params()
    assert params.dividers_x[0].position == pytest.approx(60)
    # 1.6 de parede + 25% do vão interno de 76.8
    assert params.dividers_y[0].position == pytest.approx(1.6 + 0.25 * 76.8)


def test_to_params_keeps_divider_height():
    model = OrganizerModel()
    model.x_dividers = [DividerState(0.5, height=20)]
    assert model.to_params().dividers_x[0].height == 20


def test_load_params_roundtrip():
    params = DrawerOrganizerParams(
        width=200, depth=150, height=60, wall=2.4, floor=1.6, corner_radius=8,
        dividers_x=[{"position": 50}, {"position": 120, "height": 25}],
        dividers_y=[{"position": 75}],
    )
    model = OrganizerModel()
    model.load_params(params)
    loaded = model.to_params()

    assert loaded.model_dump(exclude={"dividers_x", "dividers_y"}) == params.model_dump(
        exclude={"dividers_x", "dividers_y"}
    )
    for axis in ("dividers_x", "dividers_y"):
        before, after = getattr(params, axis), getattr(loaded, axis)
        assert [d.position for d in after] == pytest.approx([d.position for d in before])
        assert [d.height for d in after] == [d.height for d in before]


def test_load_params_replaces_existing_dividers():
    model = OrganizerModel()
    model.x_dividers = [DividerState(0.3), DividerState(0.6)]
    model.load_params(DrawerOrganizerParams(width=120, depth=80, height=40))
    assert model.x_dividers == [] and model.y_dividers == []


def test_load_params_sorts_dividers():
    params = DrawerOrganizerParams(
        width=120, depth=80, height=40,
        dividers_x=[{"position": 80, "height": 20}, {"position": 40}],
    )
    model = OrganizerModel()
    model.load_params(params)
    assert [d.height for d in model.x_dividers] == [None, 20]


def test_compartment_sizes_without_dividers_is_inner_space():
    model = OrganizerModel()  # 120 × 80, parede 1.6
    assert model.compartment_sizes('x') == pytest.approx([116.8])
    assert model.compartment_sizes('y') == pytest.approx([76.8])


def test_compartment_sizes_subtracts_half_wall_per_divider_side():
    model = OrganizerModel()
    model.x_dividers = [DividerState(0.5)]
    # centro em 60; cada lado vai da parede (1.6) até a face da divisória (60 - 0.8)
    assert model.compartment_sizes('x') == pytest.approx([57.6, 57.6])


def test_compartment_sizes_sum_is_inner_space_minus_dividers():
    model = OrganizerModel()
    model.wall = 2.4
    model.x_dividers = [DividerState(0.2), DividerState(0.45), DividerState(0.8)]
    inner = 120 - 2 * 2.4
    assert sum(model.compartment_sizes('x')) == pytest.approx(inner - 3 * 2.4)


def test_compartment_sizes_ignores_divider_order():
    model = OrganizerModel()
    model.x_dividers = [DividerState(0.66), DividerState(0.33)]  # fora de ordem, como durante um drag
    unsorted = model.compartment_sizes('x')
    model.sort_dividers()
    assert unsorted == pytest.approx(model.compartment_sizes('x'))


def test_compartment_sizes_y_uses_depth_and_y_dividers():
    model = OrganizerModel()
    model.x_dividers = [DividerState(0.25)]
    model.y_dividers = [DividerState(0.5)]
    # (80 - 2·1.6 - 1.6) / 2
    assert model.compartment_sizes('y') == pytest.approx([37.6, 37.6])


def test_compartment_sizes_negative_when_dividers_overlap():
    model = OrganizerModel()
    model.x_dividers = [DividerState(0.5), DividerState(0.5)]
    # duas divisórias no mesmo centro: o vão entre elas é -parede
    assert model.compartment_sizes('x')[1] == pytest.approx(-1.6)
