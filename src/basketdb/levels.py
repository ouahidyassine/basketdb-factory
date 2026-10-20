"""Niveaux de détail des journaux de matchs fournis par la source."""
from enum import StrEnum


class Level(StrEnum):
    """Niveau de détail ; la valeur est le code attendu par l'API (paramètre PlayerOrTeam)."""

    TEAM = "T"
    PLAYER = "P"