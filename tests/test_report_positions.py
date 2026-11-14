"""Le relevé des positions lit correctement les fichiers visual.json du format PBIR."""
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "powerbi" / "assets" / "report_positions.py"


def load_module() -> ModuleType:
    """Charge report_positions depuis son fichier : powerbi/assets n'est pas un paquet."""
    spec = importlib.util.spec_from_file_location("report_positions", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


report_positions = load_module()


def write_visual(page: Path, name: str, content: dict) -> None:
    folder = page / "visuals" / name
    folder.mkdir(parents=True)
    (folder / "visual.json").write_text(json.dumps(content), encoding="utf-8")


@pytest.fixture
def pages_dir(tmp_path: Path) -> Path:
    page = tmp_path / "abc123"
    page.mkdir()
    (page / "page.json").write_text(json.dumps({"displayName": "Vue saison"}), encoding="utf-8")
    write_visual(page, "card", {
        "position": {"x": 32.4, "y": 152, "z": 1000, "width": 272, "height": 104},
        "visual": {
            "visualType": "cardVisual",
            "query": {"queryState": {"Data": {"projections": [
                {"queryRef": "_Mesures.Avantage du terrain (pts)",
                 "nativeQueryRef": "Avantage du terrain (pts)"},
            ]}}},
        },
    })
    write_visual(page, "slicer", {
        "position": {"x": 472, "y": 42, "width": 120, "height": 32},
        "visual": {"visualType": "slicer", "query": {"queryState": {"Values": {"projections": [
            {"queryRef": "dim_season.season"},
        ]}}}},
    })
    write_visual(page, "textbox", {
        "position": {"x": 0, "y": 600, "width": 10, "height": 10},
        "visual": {"visualType": "textbox"},
    })
    return tmp_path


def test_positions_are_sorted_top_to_bottom(pages_dir: Path) -> None:
    page = report_positions.find_page(pages_dir, "Vue saison")
    positions = report_positions.read_positions(page)
    assert [item.visual_type for item in positions] == ["slicer", "cardVisual", "textbox"]


def test_coordinates_are_rounded_and_fields_named(pages_dir: Path) -> None:
    page = report_positions.find_page(pages_dir, "Vue saison")
    card = report_positions.read_positions(page)[1]
    assert (card.x, card.y, card.width, card.height) == (32, 152, 272, 104)
    assert card.fields == ("Avantage du terrain (pts)",)


def test_unknown_page_lists_existing_pages(pages_dir: Path) -> None:
    with pytest.raises(ValueError, match="Vue saison"):
        report_positions.find_page(pages_dir, "Inconnue")


def test_markdown_table_has_one_row_per_visual(pages_dir: Path) -> None:
    page = report_positions.find_page(pages_dir, "Vue saison")
    table = report_positions.to_markdown("Vue saison", report_positions.read_positions(page))
    assert table.count("\n| ") == 4
    assert "| textbox | — |" in table
