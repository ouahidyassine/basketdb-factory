"""Contrat de schéma de la source : colonnes attendues pour chaque niveau de détail."""
import logging
from collections.abc import Iterable

from basketdb.levels import Level

logger = logging.getLogger(__name__)

# Colonnes indispensables aux deux niveaux : identifiants, contexte du match, statistiques.
_COMMON_REQUIRED: frozenset[str] = frozenset({
    "SEASON_ID", "TEAM_ID", "TEAM_ABBREVIATION", "TEAM_NAME",
    "GAME_ID", "GAME_DATE", "MATCHUP", "WL", "MIN",
    "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT",
    "FTM", "FTA", "FT_PCT", "OREB", "DREB", "REB",
    "AST", "STL", "BLK", "TOV", "PF", "PTS", "PLUS_MINUS",
})

REQUIRED_COLUMNS: dict[Level, frozenset[str]] = {
    Level.TEAM: _COMMON_REQUIRED,
    Level.PLAYER: _COMMON_REQUIRED | {"PLAYER_ID", "PLAYER_NAME"},
}

# Colonnes connues mais inutiles à l'analyse : leur disparition ne doit pas bloquer.
OPTIONAL_COLUMNS: dict[Level, frozenset[str]] = {
    Level.TEAM: frozenset({"VIDEO_AVAILABLE"}),
    Level.PLAYER: frozenset({"VIDEO_AVAILABLE", "FANTASY_PTS"}),
}


class ContractError(Exception):
    """La source ne fournit plus une colonne indispensable."""


def check_columns(columns: Iterable[str], level: Level) -> set[str]:
    """Vérifie les colonnes reçues pour un niveau donné.

    Lève ContractError si une colonne requise manque. Renvoie les colonnes inconnues
    (ni requises ni optionnelles), après les avoir signalées dans les logs.
    """
    received = set(columns)

    missing = REQUIRED_COLUMNS[level] - received
    if missing:
        raise ContractError(
            f"Niveau {level.name} : colonnes requises absentes : {sorted(missing)}"
        )

    unexpected = received - REQUIRED_COLUMNS[level] - OPTIONAL_COLUMNS[level]
    if unexpected:
        logger.warning("Niveau %s : colonnes inattendues : %s", level.name, sorted(unexpected))
    return unexpected
