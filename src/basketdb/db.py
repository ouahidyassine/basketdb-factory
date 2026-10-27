"""Accès à l'entrepôt PostgreSQL : connexion et création du schéma Bronze."""
import logging
from importlib.resources import files

import psycopg

from basketdb.config import Settings

logger = logging.getLogger(__name__)

APPLICATION_NAME = "basketdb"
CONNECT_TIMEOUT_S = 10
BRONZE_DDL = files("basketdb") / "sql" / "bronze" / "create_tables.sql"


def connect(settings: Settings) -> psycopg.Connection:
    """Ouvre une connexion à l'entrepôt.

    L'appelant est responsable de la fermer, de préférence avec un bloc ``with``.
    """
    return psycopg.connect(
        **settings.connection_kwargs(),
        application_name=APPLICATION_NAME,
        connect_timeout=CONNECT_TIMEOUT_S,
    )


def read_bronze_ddl() -> str:
    """Renvoie le script de création du schéma Bronze, embarqué dans le package."""
    return BRONZE_DDL.read_text(encoding="utf-8")


def ensure_bronze_schema(conn: psycopg.Connection) -> None:
    """Crée le schéma et les tables Bronze s'ils n'existent pas (idempotent)."""
    with conn.transaction():
        conn.execute(read_bronze_ddl())
    logger.info("Schéma Bronze prêt")
