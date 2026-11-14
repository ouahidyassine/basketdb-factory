"""La grille du dashboard reste valide : sur 8 px, dans le canevas, sans chevauchement."""
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

LAYOUT_PATH = Path(__file__).resolve().parents[1] / "powerbi" / "assets" / "dashboard_layout.py"


def load_layout() -> ModuleType:
    """Charge dashboard_layout depuis son fichier : powerbi/assets n'est pas un paquet."""
    spec = importlib.util.spec_from_file_location("dashboard_layout", LAYOUT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


layout = load_layout()


@pytest.mark.parametrize("page", layout.PAGES, ids=lambda page: page.slug)
def test_every_page_has_a_valid_grid(page) -> None:
    layout.check_layout(page.zones)


@pytest.mark.parametrize("page", layout.PAGES, ids=lambda page: page.slug)
def test_every_visual_fits_inside_its_zone(page) -> None:
    for zone in layout.iter_zones(page.zones):
        x, y, width, height = zone.visual_box()
        assert width > 0 and height > 0, zone.name
        assert zone.x <= x and x + width <= zone.right, zone.name
        assert zone.y <= y and y + height <= zone.bottom, zone.name


def test_page_slugs_are_unique() -> None:
    slugs = [page.slug for page in layout.PAGES]
    assert len(slugs) == len(set(slugs))


def test_overlapping_zones_are_rejected() -> None:
    content = layout.Content("Test")
    zones = (
        layout.Zone("a", 0, 0, 64, 64, layout.Style.CARD, content),
        layout.Zone("b", 32, 32, 64, 64, layout.Style.CARD, content),
    )
    with pytest.raises(ValueError, match="se chevauchent"):
        layout.check_layout(zones)


def test_off_grid_zone_is_rejected() -> None:
    zone = layout.Zone("a", 4, 0, 64, 64, layout.Style.CARD, layout.Content("Test"))
    with pytest.raises(ValueError, match="grille"):
        layout.check_layout((zone,))


def test_child_outside_its_parent_is_rejected() -> None:
    content = layout.Content("Test")
    child = layout.Zone("enfant", 96, 0, 64, 64, layout.Style.MINI, content)
    parent = layout.Zone("parent", 0, 0, 128, 64, layout.Style.HERO, content, children=(child,))
    with pytest.raises(ValueError, match="dépasse"):
        layout.check_layout((parent,))
