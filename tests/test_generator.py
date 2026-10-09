import pytest

from drawer_organizer import DrawerOrganizerGenerator, DrawerOrganizerParams

def generate(**kw):
    params = DrawerOrganizerParams(**{"width": 120, "depth": 80, "height": 40, **kw})
    return DrawerOrganizerGenerator().generate(params)

@pytest.mark.parametrize("radius", [0, 1, 8])
@pytest.mark.parametrize("dividers", [{}, 
                                      {"dividers_x": [{"position": 40}, 
                                                      {"position": 80}], 
                                       "dividers_y": [{"position": 40}]}])
def test_mesh_is_watertight_and_sized(radius, dividers):
    result = generate(corner_radius=radius, **dividers)
    assert result.is_watertight
    assert result.dimensions_mm == pytest.approx((120, 80, 40), abs=0.01)

def test_dividers_add_material():
    plain = generate().volume_cm3
    with_dividers = generate(dividers_x=[{"position": 60}]).volume_cm3
    # divisória: parede 1.6 × vão interno 76.8 × altura acima do fundo 38.8
    assert with_dividers - plain == pytest.approx(1.6 * 76.8 * 38.8 / 1000, rel=0.01)

def test_rounded_corners_remove_material():
    assert generate(corner_radius=8).volume_cm3 < generate().volume_cm3

def test_divider_does_not_poke_out_of_rounded_corner():
    # divisória a 13 mm da borda, dentro da zona do canto de raio 15
    result = generate(corner_radius=15, dividers_x=[{"position": 13}])
    assert result.dimensions_mm == pytest.approx((120, 80, 40), abs=0.01)
    assert result.is_watertight

def test_stl_is_binary():
    stl = generate().stl_bytes
    assert len(stl) > 84 and not stl.startswith(b"solid")

def test_registered_as_platform_plugin():
    from importlib.metadata import entry_points

    eps = entry_points(group="print_platform.products")
    assert eps["drawer-organizer"].load() is DrawerOrganizerGenerator
    
def test_square_box_with_maximum_corner_radius():
    # raio = metade do lado: o contorno vira um círculo
    result = generate(width=80, depth=80, corner_radius=40, dividers_x=[{"position": 40}])
    assert result.is_watertight
    assert result.dimensions_mm == pytest.approx((80, 80, 40), abs=0.01)

def test_short_divider_uses_its_own_height():
    plain = generate().volume_cm3
    short = generate(dividers_x=[{"position": 60, "height": 20}]).volume_cm3
    # divisória: parede 1.6 × vão interno 76.8 × (20 de altura - 1.2 de fundo)
    assert short - plain == pytest.approx(1.6 * 76.8 * 18.8 / 1000, rel=0.01)


def test_short_divider_keeps_box_height_and_stays_watertight():
    result = generate(
        corner_radius=8,
        dividers_x=[{"position": 60, "height": 20}],
        dividers_y=[{"position": 40}],
    )
    assert result.is_watertight
    assert result.dimensions_mm == pytest.approx((120, 80, 40), abs=0.01)
