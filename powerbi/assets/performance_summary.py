"""Résume les exports de l'analyseur de performances de Power BI Desktop.

Usage :
    python powerbi/assets/performance_summary.py docs/performance/vue_saison.json \\
        docs/performance/facteurs.json docs/performance/face_a_face.json \\
        --output docs/performance/README.md

Un export (bouton « Export » du volet Performance analyzer) est un arbre d'événements : un
« Visual Container Lifecycle » par visuel, auquel se rattachent la requête DAX (« Execute DAX
Query ») et le dessin du visuel (« Render »). Le script recalcule pour chaque visuel les durées
du volet (requête DAX, affichage, autre), retrouve sa page et ses champs dans le rapport PBIR,
puis écrit un tableau Markdown par page, du visuel le plus lent au plus rapide.
"""

import argparse
import json
import logging
import sys
from collections import Counter, defaultdict
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from report_positions import PAGES_DIR, visual_fields

logger = logging.getLogger("performance_summary")

LIFECYCLE = "Visual Container Lifecycle"
DAX_QUERY = "Execute DAX Query"
RENDER = "Render"
UNKNOWN_PAGE = "Page inconnue"

Event = dict[str, Any]


@dataclass(frozen=True)
class VisualInfo:
    """Page, type et champs d'un visuel, lus dans le rapport PBIR."""

    page: str
    visual_type: str
    fields: tuple[str, ...]


@dataclass(frozen=True)
class VisualTiming:
    """Durées d'un visuel en millisecondes, découpées comme dans le volet de Power BI."""

    visual_id: str
    visual_type: str
    fields: tuple[str, ...]
    dax_ms: float | None
    display_ms: float
    total_ms: float

    @property
    def other_ms(self) -> float:
        """Le reste du temps du visuel : attente avant le démarrage, préparation des données."""
        return max(self.total_ms - (self.dax_ms or 0.0) - self.display_ms, 0.0)


@dataclass(frozen=True)
class PageTiming:
    """Mesure d'une page : du premier visuel qui démarre au dernier qui se termine."""

    page: str
    started: datetime
    wall_ms: float
    visuals: tuple[VisualTiming, ...]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _duration_ms(event: Event) -> float:
    if "end" not in event:
        return 0.0
    return (_timestamp(event["end"]) - _timestamp(event["start"])) / timedelta(milliseconds=1)


def index_report(pages_dir: Path) -> dict[str, VisualInfo]:
    """Chaque visuel du rapport, indexé par son identifiant (le nom de son dossier PBIR)."""
    index: dict[str, VisualInfo] = {}
    for page_file in sorted(pages_dir.glob("*/page.json")):
        page = _read_json(page_file).get("displayName", page_file.parent.name)
        for visual_file in sorted(page_file.parent.glob("visuals/*/visual.json")):
            visual = _read_json(visual_file)
            index[visual_file.parent.name] = VisualInfo(
                page=page,
                visual_type=visual.get("visual", {}).get("visualType", "inconnu"),
                fields=visual_fields(visual),
            )
    return index


def load_events(path: Path) -> list[Event]:
    """Événements d'un export ; ValueError si le fichier n'est pas un export du volet."""
    data = _read_json(path)
    if not isinstance(data.get("events"), list):
        raise ValueError("pas de liste « events » : ce n'est pas un export de l'analyseur")
    return data["events"]


def _descendants(root_id: str, children: Mapping[str, list[Event]]) -> Iterator[Event]:
    stack = list(children.get(root_id, ()))
    while stack:
        event = stack.pop()
        yield event
        stack.extend(children.get(event["id"], ()))


def summarize(events: Sequence[Event], index: Mapping[str, VisualInfo]) -> PageTiming:
    """Durées de chaque visuel d'un export, du plus lent au plus rapide."""
    lifecycles = [event for event in events if event.get("name") == LIFECYCLE and "end" in event]
    if not lifecycles:
        raise ValueError(f"aucun visuel mesuré : pas d'événement « {LIFECYCLE} » terminé")

    children: dict[str, list[Event]] = defaultdict(list)
    for event in events:
        if "parentId" in event:
            children[event["parentId"]].append(event)

    timings: list[VisualTiming] = []
    attached_queries = 0
    for lifecycle in lifecycles:
        metrics = lifecycle.get("metrics", {})
        visual_id = metrics.get("visualId", lifecycle["id"])
        info = index.get(visual_id) or VisualInfo(
            UNKNOWN_PAGE, metrics.get("visualType", "inconnu"), ()
        )
        durations: dict[str, float] = defaultdict(float)
        counts: Counter[str] = Counter()
        for event in _descendants(lifecycle["id"], children):
            durations[event["name"]] += _duration_ms(event)
            counts[event["name"]] += 1
        attached_queries += counts[DAX_QUERY]
        timings.append(
            VisualTiming(
                visual_id=visual_id,
                visual_type=info.visual_type,
                fields=info.fields,
                dax_ms=durations[DAX_QUERY] if counts[DAX_QUERY] else None,
                display_ms=durations[RENDER],
                total_ms=_duration_ms(lifecycle),
            )
        )

    total_queries = sum(1 for event in events if event.get("name") == DAX_QUERY)
    if attached_queries != total_queries:
        logger.warning(
            "%d requêtes DAX sur %d rattachées à un visuel", attached_queries, total_queries
        )
    repeated = [visual for visual, n in Counter(t.visual_id for t in timings).items() if n > 1]
    if repeated:
        logger.warning("visuels mesurés plusieurs fois (plusieurs actualisations) : %s", repeated)

    pages = Counter(index[t.visual_id].page for t in timings if t.visual_id in index)
    if len(pages) > 1:
        logger.warning("l'export mélange plusieurs pages : %s", dict(pages))
    started = min(_timestamp(event["start"]) for event in lifecycles)
    ended = max(_timestamp(event["end"]) for event in lifecycles)
    return PageTiming(
        page=pages.most_common(1)[0][0] if pages else UNKNOWN_PAGE,
        started=started,
        wall_ms=(ended - started) / timedelta(milliseconds=1),
        visuals=tuple(sorted(timings, key=lambda timing: timing.total_ms, reverse=True)),
    )


def _label(visual: VisualTiming) -> str:
    return " ; ".join(visual.fields) or visual.visual_type


def summary_lines(timing: PageTiming) -> list[str]:
    """Les conclusions chiffrées d'une page : requête la plus lente, part de chaque durée."""
    lines = [f"{len(timing.visuals)} visuels affichés en {timing.wall_ms:,.0f} ms au total."]
    queried = [visual for visual in timing.visuals if visual.dax_ms is not None]
    if queried:
        slowest = max(queried, key=lambda visual: visual.dax_ms or 0.0)
        lines[0] += f" Requête DAX la plus lente : {slowest.dax_ms:,.0f} ms ({_label(slowest)})."
    cumulated = sum(visual.total_ms for visual in timing.visuals)
    if cumulated > 0:
        shares = [
            ("requête DAX", sum(visual.dax_ms or 0.0 for visual in timing.visuals)),
            ("affichage", sum(visual.display_ms for visual in timing.visuals)),
            ("autre", sum(visual.other_ms for visual in timing.visuals)),
        ]
        parts = ", ".join(f"{name} {value / cumulated * 100:.0f} %" for name, value in shares)
        lines.append(f"Temps cumulé des visuels : {parts}.")
    return lines


def to_markdown(timing: PageTiming) -> str:
    """Tableau Markdown d'une page, au format de docs/performance/README.md."""
    rows = [
        f"## {timing.page}",
        "",
        *summary_lines(timing),
        "",
        "| Visuel | Champs | Requête DAX (ms) | Affichage (ms) | Autre (ms) | Total (ms) |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for visual in timing.visuals:
        dax = "—" if visual.dax_ms is None else f"{visual.dax_ms:,.0f}"
        rows.append(
            f"| {visual.visual_type} | {' ; '.join(visual.fields) or '—'} | {dax} "
            f"| {visual.display_ms:,.0f} | {visual.other_ms:,.0f} | {visual.total_ms:,.0f} |"
        )
    return "\n".join(rows)


def to_document(pages: Sequence[PageTiming]) -> str:
    """Document complet : en-tête qui explique les colonnes, puis un tableau par page."""
    measured_on = min(page.started for page in pages)
    header = [
        "# Performances du rapport",
        "",
        "Mesures de l'analyseur de performances de Power BI Desktop, le "
        f"{measured_on:%d/%m/%Y} : une actualisation des visuels par page.",
        "",
        "- **Requête DAX** : calcul des mesures par le moteur ; « — » quand le visuel "
        "n'interroge pas le modèle.",
        "- **Affichage** : dessin du visuel.",
        "- **Autre** : le reste du temps du visuel, surtout l'attente avant son démarrage.",
        "",
        "Fichier généré par `powerbi/assets/performance_summary.py` à partir des exports JSON "
        "de ce dossier.",
    ]
    sections = "\n\n".join(to_markdown(page) for page in pages)
    return "\n".join(header) + "\n\n" + sections + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    """Écrit le résumé des exports ; renvoie 1 si un export est illisible."""
    parser = argparse.ArgumentParser(description="Résumé des exports de l'analyseur.")
    parser.add_argument(
        "exports",
        nargs="+",
        type=Path,
        help="fichiers JSON exportés du volet, dans l'ordre des pages",
    )
    parser.add_argument(
        "--output", type=Path, help="fichier Markdown à écrire (par défaut : la sortie standard)"
    )
    parser.add_argument(
        "--pages-dir",
        type=Path,
        default=PAGES_DIR,
        help="dossier pages/ du rapport (par défaut : celui du dépôt)",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    index = index_report(args.pages_dir)
    pages: list[PageTiming] = []
    for path in args.exports:
        try:
            pages.append(summarize(load_events(path), index))
        except (OSError, ValueError, KeyError) as exc:
            logger.error("%s : %s", path, exc)
            return 1

    document = to_document(pages)
    if args.output is None:
        print(document, end="")
    else:
        args.output.write_text(document, encoding="utf-8")
        logger.info("écrit : %s", args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
