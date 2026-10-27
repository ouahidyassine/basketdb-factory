"""Tests du contrat de schéma de la source."""
import logging

import pytest

from basketdb.contract import (
    OPTIONAL_COLUMNS,
    REQUIRED_COLUMNS,
    ContractError,
    check_columns,
)
from basketdb.levels import Level


@pytest.mark.parametrize("level", list(Level))
def test_expected_columns_pass(level: Level) -> None:
    columns = REQUIRED_COLUMNS[level] | OPTIONAL_COLUMNS[level]

    assert check_columns(columns, level) == set()


@pytest.mark.parametrize("level", list(Level))
def test_optional_columns_may_disappear(level: Level) -> None:
    assert check_columns(REQUIRED_COLUMNS[level], level) == set()


@pytest.mark.parametrize("level", list(Level))
def test_missing_required_column_fails(level: Level) -> None:
    columns = REQUIRED_COLUMNS[level] - {"GAME_ID"}

    with pytest.raises(ContractError, match="GAME_ID"):
        check_columns(columns, level)


def test_unexpected_column_is_reported(caplog: pytest.LogCaptureFixture) -> None:
    columns = REQUIRED_COLUMNS[Level.TEAM] | {"PIE"}

    with caplog.at_level(logging.WARNING, logger="basketdb.contract"):
        unexpected = check_columns(columns, Level.TEAM)

    assert unexpected == {"PIE"}
    assert "PIE" in caplog.text


def test_player_level_requires_player_id() -> None:
    with pytest.raises(ContractError, match="PLAYER_ID"):
        check_columns(REQUIRED_COLUMNS[Level.TEAM], Level.PLAYER)
