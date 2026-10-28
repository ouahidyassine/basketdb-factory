"""Tests des contrôles de qualité de Bronze."""
import psycopg
import pytest
from psycopg.types.json import Jsonb

from basketdb.checks import CheckResult, failed_checks, run_checks


def test_check_without_violation_is_ok() -> None:
    assert CheckResult("contrôle", 0).ok
    assert not CheckResult("contrôle", 3).ok


def test_failed_checks_keeps_only_violations() -> None:
    results = [CheckResult("a", 0), CheckResult("b", 2), CheckResult("c", 0)]

    assert failed_checks(results) == [CheckResult("b", 2)]


@pytest.mark.integration
def test_clean_bronze_passes_all_checks(conn: psycopg.Connection) -> None:
    results = run_checks(conn)

    assert len(results) == 7
    assert failed_checks(results) == []


@pytest.mark.integration
def test_duplicated_row_is_detected(conn: psycopg.Connection) -> None:
    row = {"GAME_ID": "0029900001", "TEAM_ID": 1, "WL": "W", "PTS": 100}
    query = "INSERT INTO bronze.team_game_log (season, payload, _source) VALUES (%s, %s, %s)"
    for _ in range(2):
        conn.execute(query, ("1999-00", Jsonb(row), "test"))

    failed = failed_checks(run_checks(conn))

    assert any("doublons" in result.name for result in failed)
