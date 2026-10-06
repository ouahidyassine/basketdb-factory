import os
from collections.abc import Mapping
from dataclasses import dataclass, field

from dotenv import find_dotenv, load_dotenv

REQUIRED_VARS: tuple[str, ...] = (
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
)


class ConfigError(Exception):
    """Configuration absente ou invalide."""


@dataclass(frozen=True)
class Settings:
    """Paramètres de connexion à l'entrepôt PostgreSQL."""

    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str = field(repr=False) 
    def connection_kwargs(self) -> dict[str, str | int]:
        """Arguments nommés attendus par psycopg.connect()."""
        return {
            "host": self.postgres_host,
            "port": self.postgres_port,
            "dbname": self.postgres_db,
            "user": self.postgres_user,
            "password": self.postgres_password,
        }


def _parse_port(raw: str) -> int:
    """Convertit le port en entier et vérifie qu'il est dans la plage valide."""
    try:
        port = int(raw)
    except ValueError as exc:
        raise ConfigError(f"POSTGRES_PORT doit être un entier, reçu : {raw!r}") from exc
    if not 1 <= port <= 65535:
        raise ConfigError(f"POSTGRES_PORT hors plage (1-65535) : {port}")
    return port


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Construit les paramètres à partir de l'environnement.

    Sans argument, charge d'abord .env (s'il existe), puis lit os.environ.
    Les tests passent un dictionnaire, pour ne dépendre d'aucun fichier ni d'aucune
    variable réelle.
    """
    if env is None:
        load_dotenv(find_dotenv(usecwd=True))
        env = os.environ

    missing = [name for name in REQUIRED_VARS if not env.get(name, "").strip()]
    if missing:
        raise ConfigError(
            "Variables d'environnement manquantes : "
            + ", ".join(missing)
            + ". Copiez .env.example en .env et renseignez-les."
        )

    return Settings(
        postgres_host=env["POSTGRES_HOST"].strip(),
        postgres_port=_parse_port(env["POSTGRES_PORT"].strip()),
        postgres_db=env["POSTGRES_DB"].strip(),
        postgres_user=env["POSTGRES_USER"].strip(),
        postgres_password=env["POSTGRES_PASSWORD"],
    )