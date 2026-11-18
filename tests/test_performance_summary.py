"""Le résumé des performances découpe les durées comme le volet de Power BI."""

import importlib.util
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ASSETS = Path(__file__).resolve().parents[1] / "powerbi" / "assets"
START = datetime(2026, 11, 18, 18, 4, 39, tzinfo=UTC)


def load_module() -> ModuleType:
    """Charge performance_summary, qui importe report_positions depuis le même dossier."""
    if str(ASSETS) not in sys.path:
        sys.path.insert(0, str(ASSETS))
    spec = importlib.util.spec_from_file_location(
        "performance_summary", ASSETS / "performance_summary.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


performance_summary = load_module()


def event(
    name: str, event_id: str, start_ms: int, end_ms: int, parent: str | None = None, **metrics: Any
) -> dict[str, Any]:
    """Un événement d'export, horodaté en millisecondes après START."""

    def stamp(ms: int) -> str:
        return (
            (START + timedelta(milliseconds=ms))
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )

    item: dict[str, Any] = {
        "name": name,
        "id": event_id,
        "start": stamp(start_ms),
        "end": stamp(end_ms),
    }
    if parent is not None:
        item["parentId"] = parent
    if metrics:
        item["metrics"] = metrics
    return item


EVENTS = [
    {"name": "User Action", "id": "u1", "start": "2026-11-18T18:04:38.407Z"},
    event(
        "Visual Container Lifecycle", "card1-a", 0, 120, visualId="card1", visualType="cardVisual"
    ),
    event("Query", "q1", 0, 80, "card1-a"),
    event("Execute Semantic Query", "s1", 10, 70, "q1"),
    event("Execute DAX Query", "d1", 15, 65, "s1", QueryText="EVALUATE ..."),
    event("Render", "r1", 80, 110, "card1-a"),
    event(
        "Visual Container Lifecycle", "nav1-a", 0, 40, visualId="nav1", visualType="pageNavigator"
    ),
    event("Render", "r2", 5, 35, "nav1-a"),
]


@pytest.fixture
def index(tmp_path: Path) -> dict[str, Any]:
    page = tmp_path / "abc123"
    for name, content in {
        "card1": {
            "visual": {
                "visualType": "cardVisual",
                "query": {
                    "queryState": {"Data": {"projections": [{"queryRef": "_Mesures.Matchs"}]}}
                },
            }
        },
        "nav1": {"visual": {"visualType": "pageNavigator"}},
    }.items():
        folder = page / "visuals" / name
        folder.mkdir(parents=True)
        (folder / "visual.json").write_text(json.dumps(content), encoding="utf-8")
    (page / "page.json").write_text(json.dumps({"displayName": "Vue saison"}), encoding="utf-8")
    return performance_summary.index_report(tmp_path)


def test_durations_are_split_like_the_pane(index: dict[str, Any]) -> None:
    card = performance_summary.summarize(EVENTS, index).visuals[0]
    assert (card.dax_ms, card.display_ms, card.other_ms, card.total_ms) == (50, 30, 40, 120)
    assert card.fields == ("_Mesures.Matchs",)


def test_page_is_found_and_visuals_sorted_slowest_first(index: dict[str, Any]) -> None:
    timing = performance_summary.summarize(EVENTS, index)
    assert timing.page == "Vue saison"
    assert timing.wall_ms == 120
    assert [visual.visual_id for visual in timing.visuals] == ["card1", "nav1"]


def test_visual_without_query_shows_a_dash(index: dict[str, Any]) -> None:
    timing = performance_summary.summarize(EVENTS, index)
    assert timing.visuals[1].dax_ms is None
    assert "| pageNavigator | — | — | 30 | 10 | 40 |" in performance_summary.to_markdown(timing)


def test_summary_names_the_slowest_query_and_the_shares(index: dict[str, Any]) -> None:
    timing = performance_summary.summarize(EVENTS, index)
    assert performance_summary.summary_lines(timing) == [
        "2 visuels affichés en 120 ms au total. "
        "Requête DAX la plus lente : 50 ms (_Mesures.Matchs).",
        "Temps cumulé des visuels : requête DAX 31 %, affichage 38 %, autre 31 %.",
    ]


def test_export_without_visuals_is_rejected(index: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="aucun visuel"):
        performance_summary.summarize(EVENTS[:1], index)


def test_document_states_the_measurement_date(index: dict[str, Any]) -> None:
    document = performance_summary.to_document([performance_summary.summarize(EVENTS, index)])
    assert "le 18/11/2026" in document
    assert document.count("## ") == 1
