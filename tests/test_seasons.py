"""Tests des libellés et des plages de saisons."""
from datetime import date

import pytest

from basketdb.seasons import SeasonError, parse_season, season_for_date, season_label, season_range


@pytest.mark.parametrize(
    ("label", "start"),
    [("2015-16", 2015), ("1999-00", 1999), ("2025-26", 2025)],
)
def test_valid_season_is_parsed(label: str, start: int) -> None:
    assert parse_season(label) == start


@pytest.mark.parametrize("label", ["2015-2016", "15-16", "2015/16", "2015-17", "abcd-ef", ""])
def test_invalid_season_is_rejected(label: str) -> None:
    with pytest.raises(SeasonError):
        parse_season(label)


def test_label_handles_century_change() -> None:
    assert season_label(1999) == "1999-00"


def test_range_is_inclusive_and_ordered() -> None:
    seasons = season_range("2015-16", "2025-26")

    assert len(seasons) == 11
    assert seasons[0] == "2015-16"
    assert seasons[-1] == "2025-26"


def test_single_season_range() -> None:
    assert season_range("2019-20", "2019-20") == ["2019-20"]


def test_reversed_range_is_rejected() -> None:
    with pytest.raises(SeasonError, match="inversée"):
        season_range("2025-26", "2015-16")


@pytest.mark.parametrize(
    ("day", "season"),
    [
        (date(2026, 1, 15), "2025-26"),
        (date(2026, 6, 20), "2025-26"),
        (date(2026, 9, 30), "2025-26"),
        (date(2026, 10, 1), "2026-27"),
        (date(1999, 12, 25), "1999-00"),
    ],
    ids=["en-saison", "intersaison", "veille-bascule", "bascule", "passage-siecle"],
)
def test_season_for_date(day: date, season: str) -> None:
    assert season_for_date(day) == season
