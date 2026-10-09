import pytest
from pydantic import ValidationError

from drawer_organizer import DrawerOrganizerParams

BASE = dict(width=120, depth=80, height=40)


def test_defaults():
    p = DrawerOrganizerParams(**BASE)
    assert p.wall == 1.6 and p.floor == 1.2 and p.corner_radius == 0


def test_unknown_field_rejected():
    with pytest.raises(ValidationError):
        DrawerOrganizerParams(**BASE, colour="red")


def test_wall_below_minimum():
    with pytest.raises(ValidationError):
        DrawerOrganizerParams(**BASE, wall=0.8)


def test_floor_must_be_below_height():
    with pytest.raises(ValidationError, match="floor"):
        DrawerOrganizerParams(width=50, depth=50, height=5, floor=5)


def test_compartment_too_narrow():
    with pytest.raises(ValidationError, match="dividers_x"):
        DrawerOrganizerParams(**BASE, dividers_x=[{"position": 40}, {"position": 45}])


def test_divider_too_close_to_wall():
    with pytest.raises(ValidationError, match="dividers_y"):
        DrawerOrganizerParams(**BASE, dividers_y=[{"position": 5}])


def test_corner_radius_too_big():
    with pytest.raises(ValidationError, match="corner_radius"):
        DrawerOrganizerParams(**BASE, corner_radius=41)


def test_json_roundtrip():
    p = DrawerOrganizerParams(**BASE, dividers_x=[{"position": 40}, {"position": 80, "height": 20}], corner_radius=5)
    assert DrawerOrganizerParams.model_validate_json(p.model_dump_json()) == p


def test_divider_height_defaults_to_full():
    p = DrawerOrganizerParams(**BASE, dividers_x=[{"position": 60}])
    assert p.dividers_x[0].height is None


def test_bare_number_divider_rejected():
    with pytest.raises(ValidationError):
        DrawerOrganizerParams(**BASE, dividers_x=[60])


@pytest.mark.parametrize("height", [1.2, 3.1, 40.1])
def test_divider_height_out_of_range(height):
    # válido de floor + 2 (3.2) até a altura da caixa (40)
    with pytest.raises(ValidationError, match=r"dividers_x\[0\]"):
        DrawerOrganizerParams(**BASE, dividers_x=[{"position": 60, "height": height}])


@pytest.mark.parametrize("height", [3.2, 40])
def test_divider_height_at_limits(height):
    DrawerOrganizerParams(**BASE, dividers_x=[{"position": 60, "height": height}])


def test_unknown_divider_field_rejected():
    with pytest.raises(ValidationError):
        DrawerOrganizerParams(**BASE, dividers_x=[{"position": 60, "colour": "red"}])
