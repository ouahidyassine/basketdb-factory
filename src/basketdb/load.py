"""Chargement idempotent des journaux de matchs dans la couche Bronze."""
import json
import logging
from typing import Any

import pandas as pd
import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from basketdb.levels import Level

logger = logging.getLogger(__name__)

# Une table Bronze par niveau de détail : (schéma, table).
BRONZE_TABLES: dict[Level, tuple[str, str]] = {
    Level.TEAM: ("bronze", "team_game_log"),
    Level.PLAYER: ("bronze", "player_game_log"),
}


class LoadError(Exception):
    """Le chargement n'a pas produit l'état attendu ; la transaction est annulée."""


def to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convertit chaque ligne en dictionnaire compatible JSON.

    Les valeurs manquantes (NaN) deviennent None, et les types numériques de
    pandas deviennent des types Python natifs : chaque dictionnaire peut être
    écrit tel quel dans une colonne JSONB.
    """
    return json.loads(df.to_json(orient="records"))


def load_season(
    conn: psycopg.Connection,
    records: list[dict[str, Any]],
    *,
    season: str,
    level: Level,
    source: str,
) -> int:
    """Remplace une saison dans la table Bronze du niveau, en une seule transaction.

    Renvoie le nombre de lignes chargées. Une liste vide ne modifie rien : une
    réponse vide de la source ne doit jamais effacer une saison existante.
    """
    if not records:
        logger.warning(
            "Saison %s, niveau %s : aucune ligne extraite, rien n'est modifié",
            season, level.name,
        )
        return 0

    table = sql.Identifier(*BRONZE_TABLES[level])

    with conn.transaction():
        with conn.cursor() as cur:
            delete_query = sql.SQL("DELETE FROM {} WHERE season = %s").format(table)
            cur.execute(delete_query, (season,))
            deleted = cur.rowcount

            copy_query = sql.SQL("COPY {} (season, payload, _source) FROM STDIN").format(table)
            with cur.copy(copy_query) as copy:
                for record in records:
                    copy.write_row((season, Jsonb(record), source))

            count_query = sql.SQL("SELECT count(*) FROM {} WHERE season = %s").format(table)
            cur.execute(count_query, (season,))
            loaded = cur.fetchone()[0]

        if loaded != len(records):
            raise LoadError(
                f"Saison {season}, niveau {level.name} : "
                f"{loaded} lignes en base pour {len(records)} extraites"
            )

    logger.info(
        "Saison %s, niveau %s : %d lignes remplacées par %d",
        season, level.name, deleted, loaded,
    )
    return loaded