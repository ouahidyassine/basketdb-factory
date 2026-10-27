"""Tests d'intégration du chargement Bronze, contre un vrai PostgreSQL.

Chaque test s'exécute dans une transaction annulée à la fin : la base n'est jamais modifiée.
"""
import psycopg
import pytest

from basketdb.levels import Level
from basketdb.load import load_season

pytestmark = pytest.mark.integration

SEASON = "1999-00"  # saison fictive, hors du périmètre réel
SOURCE = "test"
RECORDS = [
    {"GAME_ID": "0029900001", "TEAM_ID": 1},
    {"GAME_ID": "0029900001", "TEAM_ID": 2},
]


def count_rows(conn: psycopg.Connection, season: str) -> int:
    """Nombre de lignes de la saison dans la table Bronze équipe."""
    query = "SELECT count(*) FROM bronze.team_game_log WHERE season = %s"
    return conn.execute(query, (season,)).fetchone()[0]


def test_loading_twice_gives_the_same_rows(conn: psycopg.Connection) -> None:
    load_season(conn, RECORDS, season=SEASON, level=Level.TEAM, source=SOURCE)
    loaded = load_season(conn, RECORDS, season=SEASON, level=Level.TEAM, source=SOURCE)

    assert loaded == 2
    assert count_rows(conn, SEASON) == 2


def test_empty_extraction_keeps_existing_rows(conn: psycopg.Connection) -> None:
    load_season(conn, RECORDS, season=SEASON, level=Level.TEAM, source=SOURCE)

    loaded = load_season(conn, [], season=SEASON, level=Level.TEAM, source=SOURCE)

    assert loaded == 0
    assert count_rows(conn, SEASON) == 2


def test_payload_round_trips_unchanged(conn: psycopg.Connection) -> None:
    records = [{"GAME_ID": "0029900001", "TEAM_ID": 1, "FG3_PCT": None}]
    load_season(conn, records, season=SEASON, level=Level.TEAM, source=SOURCE)

    query = "SELECT payload FROM bronze.team_game_log WHERE season = %s"
    payload = conn.execute(query, (SEASON,)).fetchone()[0]

    assert payload == records[0]


def test_invalid_season_is_rejected_and_nothing_is_written(conn: psycopg.Connection) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        load_season(conn, RECORDS, season="1999-2000", level=Level.TEAM, source=SOURCE)

    assert count_rows(conn, "1999-2000") == 0
