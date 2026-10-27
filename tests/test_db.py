"""Tests du module d'accès à la base, sans connexion réelle."""
import re

from basketdb.db import read_bronze_ddl


def test_bronze_ddl_is_packaged() -> None:
    assert "CREATE SCHEMA IF NOT EXISTS bronze" in read_bronze_ddl()


def test_every_create_statement_is_idempotent() -> None:
    creates = re.findall(r"CREATE\s+(?:SCHEMA|TABLE|INDEX)\b[^;]*", read_bronze_ddl())

    assert creates, "aucune instruction CREATE trouvée"
    for statement in creates:
        assert "IF NOT EXISTS" in statement, statement
