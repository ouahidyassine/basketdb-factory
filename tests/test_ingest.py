"""Tests de la ligne de commande d'ingestion, sans réseau ni base."""
import pytest

from basketdb.ingest import main, parse_args


def test_defaults_load_both_levels() -> None:
    args = parse_args(["--from", "2015-16", "--to", "2016-17"])

    assert args.levels == ["team", "player"]
    assert args.pause == 2.0


def test_invalid_season_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--from", "2015-2016", "--to", "2016-17"])

    assert exc_info.value.code == 2


def test_unknown_level_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--from", "2015-16", "--to", "2016-17", "--levels", "coach"])

    assert exc_info.value.code == 2


def test_reversed_range_returns_usage_code() -> None:
    assert main(["--from", "2025-26", "--to", "2015-16"]) == 2