"""Test de faisabilité de la source stats.nba.com via nba_api.

Pour chaque saison passée en argument, vérifie que l'API répond depuis cette
machine, puis contrôle le volume, le grain et la plage de dates des journaux de
matchs, au niveau équipe et au niveau joueur.

Usage : python spikes/nba_api_source.py 2015-16 2019-20 2024-25
"""
import logging
import sys
import time

import pandas as pd
import requests
from nba_api.stats.endpoints import leaguegamelog

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("spike_nba_api")

# Niveau de détail -> colonnes qui doivent identifier chaque ligne de façon unique (le grain).
GRAIN_KEYS: dict[str, list[str]] = {
    "T": ["GAME_ID", "TEAM_ID"],    # une ligne par équipe et par match
    "P": ["GAME_ID", "PLAYER_ID"],  # une ligne par joueur et par match
}
PAUSE_BETWEEN_CALLS_S = 2.0  # pause entre deux appels, pour ne pas être bloqué
REQUEST_TIMEOUT_S = 60       # délai maximal d'attente d'une réponse


def fetch_game_log(season: str, level: str) -> pd.DataFrame:
    """Télécharge le journal des matchs de saison régulière d'une saison.

    level vaut "T" (équipes) ou "P" (joueurs).
    """
    endpoint = leaguegamelog.LeagueGameLog(
        season=season,
        season_type_all_star="Regular Season",
        player_or_team_abbreviation=level,
        timeout=REQUEST_TIMEOUT_S,
    )
    return endpoint.get_data_frames()[0]


def check_grain(df: pd.DataFrame, keys: list[str]) -> bool:
    """Renvoie True si aucune combinaison de clés n'apparaît plus d'une fois."""
    duplicates = int(df.duplicated(subset=keys).sum())
    if duplicates:
        logger.error("Grain violé : %d doublons sur %s", duplicates, keys)
        return False
    return True


def profile_season(season: str, level: str) -> bool:
    """Télécharge une saison, journalise son profil, et renvoie True si tous les contrôles passent."""
    start = time.perf_counter()
    try:
        df = fetch_game_log(season, level)
    except (requests.exceptions.RequestException, ValueError) as exc:
        logger.error("[%s/%s] appel échoué : %s", season, level, exc)
        return False
    duration = time.perf_counter() - start

    if df.empty:
        logger.error("[%s/%s] aucune ligne renvoyée", season, level)
        return False

    logger.info(
        "[%s/%s] %d lignes | %d matchs | du %s au %s | %.1f s",
        season, level, len(df), df["GAME_ID"].nunique(),
        df["GAME_DATE"].min(), df["GAME_DATE"].max(), duration,
    )
    logger.info("[%s/%s] colonnes : %s", season, level, list(df.columns))

    ok = check_grain(df, GRAIN_KEYS[level])
    if level == "T":
        rows_per_game = df.groupby("GAME_ID").size()
        bad_games = int((rows_per_game != 2).sum())
        if bad_games:
            logger.error("[%s/T] %d matchs sans exactement 2 lignes", season, bad_games)
            ok = False
    return ok


def main(seasons: list[str]) -> int:
    """Profile chaque saison aux deux niveaux ; renvoie 0 si tout passe, 1 sinon, 2 si mal appelé."""
    if not seasons:
        logger.error("Usage : python spikes/nba_api_source.py 2015-16 [2019-20 ...]")
        return 2

    results: list[bool] = []
    for season in seasons:
        for level in GRAIN_KEYS:
            results.append(profile_season(season, level))
            time.sleep(PAUSE_BETWEEN_CALLS_S)

    logger.info("Contrôles réussis : %d/%d", sum(results), len(results))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))