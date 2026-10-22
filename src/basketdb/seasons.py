"""Libellés de saisons NBA (« 2015-16 ») : validation et génération de plages."""
import re

_SEASON_PATTERN = re.compile(r"(\d{4})-(\d{2})")


class SeasonError(ValueError):
    """Libellé de saison invalide, ou plage de saisons incohérente."""


def parse_season(label: str) -> int:
    """Renvoie l'année de début d'un libellé « AAAA-AA », après en avoir vérifié la cohérence.

    « 2015-16 » donne 2015. « 2015-17 » est refusé : la seconde partie doit être
    l'année suivante, sur deux chiffres.
    """
    match = _SEASON_PATTERN.fullmatch(label)
    if match is None:
        raise SeasonError(f"Format de saison invalide : {label!r} (attendu : AAAA-AA)")

    start, end = int(match.group(1)), int(match.group(2))
    expected = f"{(start + 1) % 100:02d}"
    if end != (start + 1) % 100:
        raise SeasonError(f"Saison incohérente : {label!r} (attendu : {start}-{expected})")
    return start


def season_label(start_year: int) -> str:
    """Libellé d'une saison à partir de son année de début : 2015 donne « 2015-16 »."""
    return f"{start_year}-{(start_year + 1) % 100:02d}"


def season_range(first: str, last: str) -> list[str]:
    """Liste les saisons de ``first`` à ``last`` incluses, dans l'ordre chronologique."""
    start, end = parse_season(first), parse_season(last)
    if start > end:
        raise SeasonError(f"Plage inversée : {first} est après {last}")
    return [season_label(year) for year in range(start, end + 1)]
    