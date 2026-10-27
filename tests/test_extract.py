"""Tests de la logique de reprise, sans appel réseau ni attente réelle."""
import json

import pandas as pd
import pytest
import requests

from basketdb.contract import ContractError
from basketdb.extract import retry_delays, with_retries


class FlakyFetch:
    """Doublure de test : échoue un nombre donné de fois, puis renvoie un DataFrame."""

    def __init__(self, failures: int, error: Exception) -> None:
        self.failures = failures
        self.error = error
        self.calls = 0

    def __call__(self) -> pd.DataFrame:
        self.calls += 1
        if self.calls <= self.failures:
            raise self.error
        return pd.DataFrame({"GAME_ID": ["0021500001"]})


@pytest.fixture
def sleeps() -> list[float]:
    """Collecte les délais demandés au lieu d'attendre réellement."""
    return []


def test_retry_delays_double_each_time() -> None:
    assert retry_delays(4, 5.0) == [5.0, 10.0, 20.0]


def test_success_on_first_attempt_does_not_sleep(sleeps: list[float]) -> None:
    fetch = FlakyFetch(failures=0, error=requests.exceptions.Timeout())

    with_retries(fetch, sleep=sleeps.append)

    assert fetch.calls == 1
    assert sleeps == []


@pytest.mark.parametrize(
    "error",
    [
        requests.exceptions.Timeout(),
        requests.exceptions.ConnectionError(),
        json.JSONDecodeError("Expecting value", "<html>blocked</html>", 0),
    ],
    ids=["timeout", "connection-error", "html-instead-of-json"],
)
def test_transient_errors_are_retried_until_success(
    error: Exception, sleeps: list[float]
) -> None:
    fetch = FlakyFetch(failures=2, error=error)

    df = with_retries(fetch, max_attempts=4, base_delay_s=5.0, sleep=sleeps.append)

    assert len(df) == 1
    assert fetch.calls == 3
    assert sleeps == [5.0, 10.0]


def test_last_error_is_raised_after_max_attempts(sleeps: list[float]) -> None:
    fetch = FlakyFetch(failures=10, error=requests.exceptions.Timeout())

    with pytest.raises(requests.exceptions.Timeout):
        with_retries(fetch, max_attempts=4, sleep=sleeps.append)

    assert fetch.calls == 4
    assert len(sleeps) == 3


def test_permanent_errors_are_not_retried(sleeps: list[float]) -> None:
    fetch = FlakyFetch(failures=1, error=ContractError("colonne absente"))

    with pytest.raises(ContractError):
        with_retries(fetch, sleep=sleeps.append)

    assert fetch.calls == 1
    assert sleeps == []


def test_invalid_max_attempts_is_rejected() -> None:
    with pytest.raises(ValueError):
        with_retries(FlakyFetch(0, requests.exceptions.Timeout()), max_attempts=0)
