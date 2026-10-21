"""Fixtures partagées par tous les tests."""
from collections.abc import Iterator

import psycopg
import pytest

from basketdb.config import ConfigError, load_settings
from basketdb.db import connect, ensure_bronze_schema


@pytest.fixture
def conn() -> Iterator[psycopg.Connection]:
    """Connexion à la base locale, dans une transaction toujours annulée à la fin du test.

    Le test est ignoré si la base n'est pas configurée ou pas joignable, comme en CI.
    """
    try:
        connection = connect(load_settings())
    except (ConfigError, psycopg.OperationalError) as exc:
        pytest.skip(f"PostgreSQL indisponible : {exc}")

    with connection:
        with connection.transaction(force_rollback=True):
            ensure_bronze_schema(connection)
            yield connection