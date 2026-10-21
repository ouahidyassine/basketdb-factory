"""Tests du chargement Bronze : sérialisation des lignes."""
import json

import pandas as pd

from basketdb.load import to_records


def test_nan_becomes_none() -> None:
    df = pd.DataFrame({"GAME_ID": ["0021500001"], "FG3_PCT": [float("nan")]})

    assert to_records(df) == [{"GAME_ID": "0021500001", "FG3_PCT": None}]


def test_integers_become_python_ints() -> None:
    df = pd.DataFrame({"PTS": pd.Series([106], dtype="int64")})

    records = to_records(df)

    assert records == [{"PTS": 106}]
    assert type(records[0]["PTS"]) is int


def test_records_produce_strict_json() -> None:
    df = pd.DataFrame({"WL": ["W", "L"], "FG3_PCT": [0.5, float("nan")]})

    text = json.dumps(to_records(df), allow_nan=False)

    assert "NaN" not in text


def test_empty_dataframe_gives_no_records() -> None:
    assert to_records(pd.DataFrame(columns=["GAME_ID"])) == []