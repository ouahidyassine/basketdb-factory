"""Relève la position réelle des visuels d'une page du rapport Power BI (format PBIR).

Usage :
    python powerbi/assets/report_positions.py "Vue saison"

Chaque visuel est décrit dans pages/<id>/visuals/<id>/visual.json ; la sortie est un tableau
Markdown, trié de haut en bas puis de gauche à droite, à reporter dans docs/design/dashboard.md.
"""
import argparse
import json
import logging
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("report_positions")

PAGES_DIR = (
    Path(__file__).resolve().parents[1] / "basketdb.Report" / "definition" / "pages"
)


@dataclass(frozen=True)
class VisualPosition:
    """Type, champs et rectangle d'un visuel, en pixels du canevas."""

    visual_type: str
    fields: tuple[str, ...]
    x: int
    y: int
    width: int
    height: int


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def find_page(pages_dir: Path, display_name: str) -> Path:
    """Dossier de la page nommée `display_name` ; ValueError avec la liste sinon."""
    names: dict[str, Path] = {}
    for page_file in sorted(pages_dir.glob("*/page.json")):
        names[_read_json(page_file).get("displayName", "")] = page_file.parent
    if display_name not in names:
        raise ValueError(f"Page introuvable : {display_name!r} (pages : {sorted(names)})")
    return names[display_name]


def _fields(visual: dict[str, Any]) -> tuple[str, ...]:
    """Champs projetés par le visuel, dans l'ordre de ses zones (axes, valeurs…)."""
    query_state = visual.get("visual", {}).get("query", {}).get("queryState", {})
    fields: list[str] = []
    for role in query_state.values():
        for projection in role.get("projections", []):
            name = projection.get("nativeQueryRef") or projection.get("queryRef")
            if name:
                fields.append(name)
    return tuple(fields)


def read_positions(page_dir: Path) -> list[VisualPosition]:
    """Positions de tous les visuels de la page, triées de haut en bas et de gauche à droite."""
    positions: list[VisualPosition] = []
    for visual_file in page_dir.glob("visuals/*/visual.json"):
        visual = _read_json(visual_file)
        box = visual.get("position")
        if box is None:
            logger.warning("%s : pas de position, ignoré", visual_file)
            continue
        positions.append(
            VisualPosition(
                visual_type=visual.get("visual", {}).get("visualType", "inconnu"),
                fields=_fields(visual),
                x=round(box["x"]),
                y=round(box["y"]),
                width=round(box["width"]),
                height=round(box["height"]),
            )
        )
    return sorted(positions, key=lambda item: (item.y, item.x))


def to_markdown(display_name: str, positions: Sequence[VisualPosition]) -> str:
    """Tableau Markdown des positions, au format de docs/design/dashboard.md."""
    rows = [
        f"### {display_name}",
        "",
        "| Visuel | Champs | x | y | Largeur | Hauteur |",
        "|---|---|---|---|---|---|",
    ]
    for item in positions:
        fields = " ; ".join(item.fields) or "—"
        rows.append(
            f"| {item.visual_type} | {fields} | {item.x} | {item.y} "
            f"| {item.width} | {item.height} |"
        )
    return "\n".join(rows)


def main(argv: Sequence[str] | None = None) -> int:
    """Affiche le tableau des positions ; renvoie 1 si la page n'existe pas."""
    parser = argparse.ArgumentParser(description="Positions réelles des visuels d'une page.")
    parser.add_argument("page", help="nom affiché de la page, par exemple « Vue saison »")
    parser.add_argument("--pages-dir", type=Path, default=PAGES_DIR,
                        help="dossier pages/ du rapport (par défaut : celui du dépôt)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        page_dir = find_page(args.pages_dir, args.page)
    except ValueError as exc:
        logger.error("%s", exc)
        return 1
    print(to_markdown(args.page, read_positions(page_dir)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
