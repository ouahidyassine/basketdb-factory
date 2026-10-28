"""Contrôles de qualité de Bronze : exécution, bilan et commande basketdb-check."""
import argparse
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from importlib.resources import files

import psycopg

from basketdb.config import load_settings
from basketdb.db import connect

logger = logging.getLogger(__name__)

BRONZE_CHECKS = files("basketdb") / "sql" / "checks" / "bronze_quality.sql"


@dataclass(frozen=True)
class CheckResult:
    """Résultat d'un contrôle : son libellé et son nombre de violations."""

    name: str
    violations: int

    @property
    def ok(self) -> bool:
        """Vrai si le contrôle n'a trouvé aucune violation."""
        return self.violations == 0


def run_checks(conn: psycopg.Connection) -> list[CheckResult]:
    """Exécute les contrôles de Bronze et renvoie un résultat par contrôle."""
    query = BRONZE_CHECKS.read_text(encoding="utf-8")
    rows = conn.execute(query).fetchall()
    return [CheckResult(name, violations) for name, violations in rows]


def failed_checks(results: Sequence[CheckResult]) -> list[CheckResult]:
    """Les contrôles qui ont trouvé au moins une violation."""
    return [result for result in results if not result.ok]


def main(argv: Sequence[str] | None = None) -> int:
    """Renvoie 0 si tous les contrôles passent, 1 sinon."""
    parser = argparse.ArgumentParser(
        prog="basketdb-check",
        description="Exécute les contrôles de qualité de la couche Bronze.",
    )
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    with connect(load_settings()) as conn:
        results = run_checks(conn)

    if not results:
        logger.error("Aucun contrôle exécuté : le fichier de contrôles est vide ou illisible")
        return 1

    for result in results:
        log = logger.info if result.ok else logger.error
        log("%s : %d violation(s)", result.name, result.violations)

    failed = failed_checks(results)
    logger.info("Bilan : %d contrôles, %d en échec", len(results), len(failed))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
