"""Point d'entrée de l'ingestion : charge une plage de saisons dans la couche Bronze."""
import argparse
import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from basketdb.config import load_settings
from basketdb.db import connect, ensure_bronze_schema
from basketdb.extract import SOURCE, extract_season
from basketdb.levels import Level
from basketdb.load import load_season, to_records
from basketdb.seasons import SeasonError, parse_season, season_range

logger = logging.getLogger(__name__)

DEFAULT_PAUSE_S = 2.0
LEVEL_CHOICES: dict[str, Level] = {"team": Level.TEAM, "player": Level.PLAYER}


@dataclass(frozen=True)
class UnitResult:
    """Résultat du chargement d'une saison à un niveau."""

    season: str
    level: Level
    rows: int
    error: str | None = None

    @property
    def ok(self) -> bool:
        """Vrai si l'unité s'est chargée sans erreur."""
        return self.error is None


def season_arg(value: str) -> str:
    """Type argparse : accepte un libellé de saison valide, sinon erreur d'usage."""
    try:
        parse_season(value)
    except SeasonError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return value


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Lit et valide les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        prog="basketdb-ingest",
        description="Charge les journaux de matchs NBA d'une plage de saisons dans Bronze.",
    )
    parser.add_argument(
        "--from", dest="first", required=True, type=season_arg,
        help="première saison, par exemple 2015-16",
    )
    parser.add_argument(
        "--to", dest="last", required=True, type=season_arg,
        help="dernière saison incluse, par exemple 2025-26",
    )
    parser.add_argument(
        "--levels", nargs="+", choices=list(LEVEL_CHOICES), default=list(LEVEL_CHOICES),
        help="niveaux à charger (par défaut : les deux)",
    )
    parser.add_argument(
        "--pause", type=float, default=DEFAULT_PAUSE_S,
        help="pause entre deux appels à l'API, en secondes",
    )
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser.parse_args(argv)


def run(
    seasons: Sequence[str],
    levels: Sequence[Level],
    *,
    pause_s: float = DEFAULT_PAUSE_S,
    sleep: Callable[[float], None] = time.sleep,
) -> list[UnitResult]:
    """Charge chaque saison à chaque niveau ; une unité en échec n'arrête pas les autres."""
    results: list[UnitResult] = []
    with connect(load_settings()) as conn:
        ensure_bronze_schema(conn)
        for season in seasons:
            for level in levels:
                if results:
                    sleep(pause_s)
                try:
                    records = to_records(extract_season(season, level))
                    rows = load_season(conn, records, season=season, level=level, source=SOURCE)
                    results.append(UnitResult(season, level, rows))
                except Exception as exc:  # frontière du lot : on journalise et on continue
                    logger.exception("Saison %s, niveau %s : échec", season, level.name)
                    error = f"{type(exc).__name__}: {exc}"
                    results.append(UnitResult(season, level, 0, error=error))
    return results


def summarize(results: Sequence[UnitResult]) -> None:
    """Journalise le bilan du lot, puis chaque unité en échec."""
    failed = [result for result in results if not result.ok]
    total_rows = sum(result.rows for result in results)
    logger.info(
        "Terminé : %d unités, %d lignes chargées, %d en échec",
        len(results), total_rows, len(failed),
    )
    for result in failed:
        logger.error(
            "En échec : saison %s, niveau %s (%s)",
            result.season, result.level.name, result.error,
        )


def main(argv: Sequence[str] | None = None) -> int:
    """Renvoie 0 si tout a réussi, 1 si au moins une unité a échoué, 2 si mal appelée."""
    args = parse_args(argv)
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    try:
        seasons = season_range(args.first, args.last)
    except SeasonError as exc:
        logger.error("%s", exc)
        return 2

    levels = [LEVEL_CHOICES[name] for name in args.levels]
    logger.info(
        "Ingestion de %d saison(s), de %s à %s, niveaux : %s",
        len(seasons), seasons[0], seasons[-1], ", ".join(args.levels),
    )
    results = run(seasons, levels, pause_s=args.pause)
    summarize(results)
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
