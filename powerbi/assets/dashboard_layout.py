"""Grille et contenu des trois pages du dashboard BasketDB.

Toutes les mesures sont en pixels du canevas Power BI (1280 × 720). Une seule description sert
à dessiner les fonds de page et à donner la position exacte de chaque visuel à poser dessus.
"""
from dataclasses import dataclass
from enum import StrEnum

WIDTH, HEIGHT = 1280, 720
GRID = 8


class Style(StrEnum):
    """Rendu d'une zone du fond."""

    HERO = "hero"
    CARD = "card"
    MINI = "mini"
    SLOT = "slot"
    NAV = "nav"


@dataclass(frozen=True)
class Content:
    """Ce que montre une zone : titre, explication, icône, et visuel Power BI à y poser."""

    title: str
    subtitle: str = ""
    icon: str | None = None
    visual: str = ""
    field: str = ""


@dataclass(frozen=True)
class Zone:
    """Un rectangle du fond : carte, mini-carte, emplacement de segment ou de navigation."""

    name: str
    x: int
    y: int
    width: int
    height: int
    style: Style
    content: Content
    note: str = ""
    legend: bool = False
    illustration: bool = False
    children: tuple["Zone", ...] = ()

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    def visual_box(self) -> tuple[int, int, int, int]:
        """Position et taille du visuel Power BI de la zone : (x, y, largeur, hauteur)."""
        match self.style:
            case Style.HERO:
                return self.x + 16, self.y + 56, self.width // 2 - 24, 104
            case Style.MINI:
                return self.x + 44, self.y + 6, self.width - 48, 44
            case Style.SLOT:
                return self.x + 8, self.y + 26, self.width - 16, 32
            case Style.NAV:
                return self.x + 4, self.y + 4, self.width - 8, self.height - 8
            case _:
                reserved = 48 if self.legend else 120 if self.illustration else 0
                return self.x + 16, self.y + 52, self.width - 32 - reserved, self.height - 60


@dataclass(frozen=True)
class Page:
    """Une page du rapport et les zones de son fond."""

    slug: str
    name: str
    zones: tuple[Zone, ...]


def _slicer(title: str, icon: str, field: str) -> Content:
    return Content(title, icon=icon, visual="Slicer (Dropdown)", field=field)


def _card(title: str, subtitle: str, icon: str, field: str) -> Content:
    return Content(title, subtitle, icon, "Card (new)", field)


def build_page(
    slug: str,
    name: str,
    *,
    slots: tuple[Content, Content, Content],
    hero: Content,
    note: str,
    minis: tuple[Content, Content, Content, Content],
    kpi: Content,
    featured: Content,
    heatmap: Content,
    gauge: Content,
    bars: Content,
    trend: Content,
) -> Page:
    """Assemble une page sur la grille commune : en-tête, carte principale, six cartes."""
    header = tuple(
        Zone(f"segment_{index + 1}", 464 + index * 152, 16, 136, 64, Style.SLOT, content)
        for index, content in enumerate(slots)
    )
    navigation = Zone(
        "navigation", 920, 24, 344, 48, Style.NAV,
        Content("Pages", visual="Page navigator", field="Pages visibles du rapport"),
    )
    mini_zones = tuple(
        Zone(f"mini_{index + 1}", 32 + index * 144, 264, 128, 80, Style.MINI, content)
        for index, content in enumerate(minis)
    )
    return Page(
        slug,
        name,
        (
            *header,
            navigation,
            Zone("principal", 16, 96, 592, 264, Style.HERO, hero, note=note, children=mini_zones),
            Zone("kpi", 624, 96, 304, 120, Style.CARD, kpi),
            Zone("a_la_une", 944, 96, 320, 120, Style.CARD, featured, illustration=True),
            Zone("chaleur", 624, 232, 400, 200, Style.CARD, heatmap, legend=True),
            Zone("anneau", 1040, 232, 224, 200, Style.CARD, gauge),
            Zone("barres", 16, 376, 592, 328, Style.CARD, bars),
            Zone("courbes", 624, 448, 640, 256, Style.CARD, trend),
        ),
    )


SEASON = _slicer("Saison", "calendar", "dim_season[season]")
TEAM = _slicer("Équipe", "shield", "dim_team[team_name]")
VENUE = _slicer("Lieu", "pin", "fact_team_game[venue]")
OPPONENT = _slicer("Adversaire", "versus", "dim_opponent[opponent_name]")

PAGES: tuple[Page, ...] = (
    build_page(
        "vue_saison",
        "Vue saison",
        slots=(SEASON, TEAM, VENUE),
        hero=_card(
            "Avantage du terrain", "Écart domicile − extérieur, saisons terminées",
            "house", "[Avantage du terrain (pts)]",
        ),
        note=(
            "Un match équilibré se gagne une fois sur deux. L'écart entre le taux de victoire "
            "à domicile et à l'extérieur mesure, en points, l'avantage de jouer chez soi."
        ),
        minis=(
            _card("Matchs joués", "", "calendar", "[Matchs]"),
            _card("Domicile", "", "house", "[Taux de victoire à domicile]"),
            _card("Extérieur", "", "route", "[Taux de victoire à l'extérieur]"),
            _card("Saisons", "", "ball", "[Saisons analysées]"),
        ),
        kpi=_card(
            "Meilleure saison à domicile", "Taux de la saison la plus forte", "trophy",
            "[Meilleur taux à domicile] ; référence [Meilleure saison à domicile]",
        ),
        featured=_card(
            "Saison la plus faible", "Le creux de l'avantage", "trend_down",
            "[Plus faible taux à domicile] ; référence [Saison la plus faible à domicile]",
        ),
        heatmap=Content(
            "Victoires par lieu et par saison", "Plus la case est orange, plus le taux est élevé",
            "grid", "Matrix", "Lignes venue ; colonnes season_short ; [Taux de victoire]",
        ),
        gauge=Content(
            "Lieu des victoires", "Part gagnée à domicile", "donut", "Donut chart",
            "Légende venue ; [Victoires]",
        ),
        bars=Content(
            "Classement des équipes", "Taux de victoire, du plus haut au plus bas", "bars",
            "Clustered bar chart", "team_name ; [Taux de victoire]",
        ),
        trend=Content(
            "L'avantage du terrain, saison par saison",
            "La chute de 2019-21 coïncide avec la bulle et les salles vides", "line",
            "Line chart",
            "season_short ; [Taux de victoire à domicile], [Taux de victoire à l'extérieur]",
        ),
    ),
    build_page(
        "facteurs",
        "Facteurs d'avant-match",
        slots=(SEASON, TEAM, VENUE),
        hero=_card(
            "Le facteur le plus fort", "Taux de victoire en meilleure forme que l'adversaire",
            "flame", "[Taux de victoire en meilleure forme]",
        ),
        note=(
            "La forme compte les victoires sur les 10 derniers matchs avant le coup d'envoi. "
            "Elle mesure l'élan du moment, mais aussi le niveau général de l'équipe."
        ),
        minis=(
            _card("Domicile", "", "house", "[Taux de victoire à domicile]"),
            _card("+ de repos", "", "clock", "[Taux de victoire avec plus de repos]"),
            _card("Back-to-back", "", "battery", "[Taux de victoire en back-to-back]"),
            _card("Extérieur", "", "route", "[Taux de victoire à l'extérieur]"),
        ),
        kpi=_card(
            "Écart avec un match équilibré", "Meilleure forme, comparée à 50 %", "star",
            "[Écart forme vs 50 %]",
        ),
        featured=_card(
            "Pire scénario", "Back-to-back à l'extérieur", "battery",
            "[Taux en back-to-back à l'extérieur]",
        ),
        heatmap=Content(
            "Repos et lieu", "Taux de victoire selon les jours de repos", "grid", "Matrix",
            "Lignes rest_bucket ; colonnes venue ; [Taux de victoire]",
        ),
        gauge=Content(
            "Bilan en back-to-back", "Victoires et défaites", "donut", "Donut chart",
            "Légende result ; [Matchs (équipe)] ; filtre is_back_to_back = True",
        ),
        bars=Content(
            "Les facteurs comparés", "Au-dessus de la ligne des 50 %, le facteur aide", "bars",
            "Clustered bar chart", "Facteurs[Facteur] ; [Taux du facteur]",
        ),
        trend=Content(
            "Le back-to-back, saison par saison", "Taux de victoire avec et sans back-to-back",
            "line", "Line chart",
            "season ; [Taux de victoire en back-to-back], [Taux de victoire hors back-to-back]",
        ),
    ),
    build_page(
        "face_a_face",
        "Face-à-face",
        slots=(TEAM, OPPONENT, SEASON),
        hero=_card(
            "Bilan du face-à-face", "Victoires – défaites de l'équipe contre l'adversaire",
            "versus", "[Bilan]",
        ),
        note=(
            "Choisissez une équipe et un adversaire dans l'en-tête : le bilan, les écarts et la "
            "forme se recalculent pour leurs seules confrontations."
        ),
        minis=(
            _card("Matchs", "", "calendar", "[Matchs (équipe)]"),
            _card("Victoires", "", "trophy", "[Victoires]"),
            _card("Défaites", "", "cross", "[Défaites]"),
            _card("Écart moyen", "", "line", "[Écart moyen]"),
        ),
        kpi=_card(
            "Taux de victoire", "Sur les confrontations choisies", "donut", "[Taux de victoire]",
        ),
        featured=_card(
            "Plus large victoire", "Écart de points maximal", "star", "[Plus large victoire]",
        ),
        heatmap=Content(
            "Résultats par saison", "Taux de victoire, à domicile et à l'extérieur", "grid",
            "Matrix", "Lignes venue ; colonnes season_short ; [Taux de victoire]",
        ),
        gauge=Content(
            "Répartition", "Victoires et défaites", "donut", "Donut chart",
            "Légende result ; [Matchs (équipe)]",
        ),
        bars=Content(
            "Écart de points par saison", "Positif : l'équipe a dominé la saison", "bars",
            "Clustered column chart", "season ; [Écart moyen]",
        ),
        trend=Content(
            "La forme avant chaque match",
            "Victoires sur les 10 derniers matchs, équipe et adversaire", "line", "Line chart",
            "game_date ; [Forme de l'équipe], [Forme de l'adversaire]",
        ),
    ),
)


def check_layout(
    zones: tuple[Zone, ...], bounds: tuple[int, int, int, int] = (0, 0, WIDTH, HEIGHT)
) -> None:
    """Refuse une zone hors grille, hors de son parent, ou qui en chevauche une autre."""
    left, top, right, bottom = bounds
    for zone in zones:
        if any(value % GRID for value in (zone.x, zone.y, zone.width, zone.height)):
            raise ValueError(f"{zone.name} : position ou taille hors de la grille de {GRID} px")
        if zone.x < left or zone.y < top or zone.right > right or zone.bottom > bottom:
            raise ValueError(f"{zone.name} : la zone dépasse de son conteneur")
        check_layout(zone.children, (zone.x, zone.y, zone.right, zone.bottom))
    for index, first in enumerate(zones):
        for second in zones[index + 1:]:
            overlap_x = first.x < second.right and second.x < first.right
            overlap_y = first.y < second.bottom and second.y < first.bottom
            if overlap_x and overlap_y:
                raise ValueError(f"{first.name} et {second.name} se chevauchent")


def iter_zones(zones: tuple[Zone, ...]) -> list[Zone]:
    """Toutes les zones, enfants compris, dans l'ordre de lecture."""
    flat: list[Zone] = []
    for zone in zones:
        flat.append(zone)
        flat.extend(iter_zones(zone.children))
    return flat
