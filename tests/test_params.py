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
        DrawerOrganizerParams(**BASE, dividers_x=[40, 45])


def test_divider_too_close_to_wall():
    with pytest.raises(ValidationError, match="dividers_y"):
        DrawerOrganizerParams(**BASE, dividers_y=[5])


def test_corner_radius_too_big():
    with pytest.raises(ValidationError, match="corner_radius"):
        DrawerOrganizerParams(**BASE, corner_radius=41)


def test_json_roundtrip():
    p = DrawerOrganizerParams(**BASE, dividers_x=[40, 80], corner_radius=5)
    assert DrawerOrganizerParams.model_validate_json(p.model_dump_json()) == p