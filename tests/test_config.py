import pytest

from basketdb.config import REQUIRED_VARS, ConfigError, Settings, load_settings


@pytest.fixture
def valid_env() -> dict[str, str]:
    """Environnement complet et valide, indépendant de la machine."""
    return {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5433",
        "POSTGRES_DB": "basketdb",
        "POSTGRES_USER": "basketdb_user",
        "POSTGRES_PASSWORD": "secret-de-test",
    }


def test_valid_env_builds_settings(valid_env: dict[str, str]) -> None:
    settings = load_settings(valid_env)

    assert settings == Settings(
        postgres_host="localhost",
        postgres_port=5433,
        postgres_db="basketdb",
        postgres_user="basketdb_user",
        postgres_password="secret-de-test",
    )


def test_all_missing_vars_are_reported_at_once() -> None:
    with pytest.raises(ConfigError) as exc_info:
        load_settings({})

    message = str(exc_info.value)
    for name in REQUIRED_VARS:
        assert name in message


def test_blank_value_counts_as_missing(valid_env: dict[str, str]) -> None:
    valid_env["POSTGRES_HOST"] = "   "

    with pytest.raises(ConfigError, match="POSTGRES_HOST"):
        load_settings(valid_env)


@pytest.mark.parametrize("raw_port", ["abc", "54.3", "0", "70000"])
def test_invalid_port_is_rejected(valid_env: dict[str, str], raw_port: str) -> None:
    valid_env["POSTGRES_PORT"] = raw_port

    with pytest.raises(ConfigError, match="POSTGRES_PORT"):
        load_settings(valid_env)


def test_password_is_hidden_from_repr(valid_env: dict[str, str]) -> None:
    settings = load_settings(valid_env)

    assert "secret-de-test" not in repr(settings)


def test_connection_kwargs_use_psycopg_names(valid_env: dict[str, str]) -> None:
    kwargs = load_settings(valid_env).connection_kwargs()

    assert kwargs == {
        "host": "localhost",
        "port": 5433,
        "dbname": "basketdb",
        "user": "basketdb_user",
        "password": "secret-de-test",
    }