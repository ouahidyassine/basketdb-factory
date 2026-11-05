"""Génère le fond des pages du dashboard Power BI à partir de la grille de mise en page.
"""
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

WIDTH, HEIGHT = 1280, 720
SCALE = 2
GRID = 8
RADIUS = 12

PAGE_COLOR = "#0B0F14"
CARD_COLOR = "#121821"
BORDER_COLOR = "#1F2A37"
ACCENT_COLOR = "#F97316"

OUTPUT = Path(__file__).resolve().parent / "backgrounds" / "page.png"


@dataclass(frozen=True)
class Card:
    """Une carte du fond, en pixels du canevas Power BI (1280 × 720)."""

    name: str
    x: int
    y: int
    width: int
    height: int


LAYOUT: tuple[Card, ...] = (
    Card("header", 24, 24, 1232, 64),
    Card("kpi_1", 24, 104, 296, 104),
    Card("kpi_2", 336, 104, 296, 104),
    Card("kpi_3", 648, 104, 296, 104),
    Card("kpi_4", 960, 104, 296, 104),
    Card("main", 24, 224, 728, 472),
    Card("secondary", 768, 224, 488, 472),
)


def check_layout(cards: tuple[Card, ...]) -> None:
    """Refuse une carte hors de la grille, hors du canevas, ou qui en chevauche une autre."""
    for card in cards:
        if any(value % GRID for value in (card.x, card.y, card.width, card.height)):
            raise ValueError(f"{card.name} : position ou taille hors de la grille de {GRID} px")
        if card.x + card.width > WIDTH or card.y + card.height > HEIGHT:
            raise ValueError(f"{card.name} : la carte dépasse du canevas")
    for index, first in enumerate(cards):
        for second in cards[index + 1:]:
            overlap_x = first.x < second.x + second.width and second.x < first.x + first.width
            overlap_y = first.y < second.y + second.height and second.y < first.y + first.height
            if overlap_x and overlap_y:
                raise ValueError(f"{first.name} et {second.name} se chevauchent")


def draw_background(cards: tuple[Card, ...]) -> Image.Image:
    """Dessine les cartes arrondies et le trait d'accent de l'en-tête, à l'échelle SCALE."""
    image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), PAGE_COLOR)
    draw = ImageDraw.Draw(image)
    for card in cards:
        box = (
            card.x * SCALE,
            card.y * SCALE,
            (card.x + card.width) * SCALE - 1,
            (card.y + card.height) * SCALE - 1,
        )
        draw.rounded_rectangle(
            box, radius=RADIUS * SCALE, fill=CARD_COLOR, outline=BORDER_COLOR, width=SCALE
        )
    header = next(card for card in cards if card.name == "header")
    accent = (
        (header.x + 16) * SCALE,
        (header.y + 16) * SCALE,
        (header.x + 20) * SCALE,
        (header.y + header.height - 16) * SCALE,
    )
    draw.rounded_rectangle(accent, radius=2 * SCALE, fill=ACCENT_COLOR)
    return image


def main() -> None:
    """Vérifie la grille, puis enregistre le fond de page."""
    check_layout(LAYOUT)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    draw_background(LAYOUT).save(OUTPUT)
    print(f"Fond enregistré : {OUTPUT}")


if __name__ == "__main__":
    main()
