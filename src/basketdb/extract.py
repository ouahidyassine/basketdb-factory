"""Extraction des journaux de matchs depuis stats.nba.com, avec reprises."""
import json
import logging
import time
from collections.abc import Callable
from functools import partial

import pandas as pd
import requests
from nba_api.stats.endpoints import leaguegamelog

from basketdb.contract import check_columns
from basketdb.levels import Level

logger = logging.getLogger(__name__)

SOURCE = "stats.nba.com/leaguegamelog"
REQUEST_TIMEOUT_S = 60
MAX_ATTEMPTS = 4
BASE_DELAY_S = 5.0

# Erreurs passagères : réseau, délai dépassé, réponse illisible (page de blocage HTML).
TRANSIENT_ERRORS: tuple[type[Exception], ...] = (
    requests.exceptions.RequestException,
    json.JSONDecodeError,
)


def fetch_game_log(season: str, level: Level) -> pd.DataFrame:
    """Appelle l'API une seule fois et renvoie le journal de saison régulière, brut."""
    endpoint = leaguegamelog.LeagueGameLog(
        season=season,
        season_type_all_star="Regular Season",
        player_or_team_abbreviation=level.value,
        timeout=REQUEST_TIMEOUT_S,
    )
    return endpoint.get_data_frames()[0]


def retry_delays(max_attempts: int, base_delay_s: float) -> list[float]:
    """Délais d'attente entre tentatives successives (attente exponentielle)."""
    return [base_delay_s * 2**i for i in range(max_attempts - 1)]


def with_retries(
    fetch: Callable[[], pd.DataFrame],
    *,
    max_attempts: int = MAX_ATTEMPTS,
    base_delay_s: float = BASE_DELAY_S,
    sleep: Callable[[float], None] = time.sleep,
) -> pd.DataFrame:
    """Exécute ``fetch`` en réessayant uniquement sur les erreurs passagères.

    Après ``max_attempts`` échecs, la dernière erreur est relevée telle quelle.
    """
    if max_attempts < 1:
        raise ValueError(f"max_attempts doit valoir au moins 1, reçu : {max_attempts}")

    delays = retry_delays(max_attempts, base_delay_s)
    for attempt in range(1, max_attempts + 1):
        try:
            return fetch()
        except TRANSIENT_ERRORS as exc:
            if attempt == max_attempts:
                logger.error("Échec définitif après %d tentatives : %r", max_attempts, exc)
                raise
            delay = delays[attempt - 1]
            logger.warning(
                "Tentative %d/%d échouée (%s) ; nouvel essai dans %.0f s",
                attempt, max_attempts, type(exc).__name__, delay,
            )
            sleep(delay)


def extract_season(season: str, level: Level) -> pd.DataFrame:
    """Extrait une saison à un niveau donné, avec reprises, puis vérifie le contrat."""
    df = with_retries(partial(fetch_game_log, season, level))
    check_columns(df.columns, level)
    logger.info("Saison %s, niveau %s : %d lignes extraites", season, level.name, len(df))
    return df