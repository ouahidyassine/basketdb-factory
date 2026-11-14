"""Génère les fonds des pages du dashboard Power BI à partir de dashboard_layout.

Usage :
    python powerbi/assets/generate_background.py              # un PNG par page
    python powerbi/assets/generate_background.py --positions  # positions des visuels

Les textes sont rendus en Segoe UI, la police de Power BI, lue par défaut dans le dossier
des polices de Windows (/mnt/c/Windows/Fonts depuis WSL). La variable BASKETDB_FONT_DIR
permet d'en choisir un autre ; à défaut, DejaVu Sans est utilisée, avec un avertissement.
"""
import argparse
import logging
import os
import sys
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path

from dashboard_icons import draw_icon
from dashboard_layout import (
    HEIGHT,
    PAGES,
    WIDTH,
    Page,
    Style,
    Zone,
    check_layout,
    iter_zones,
)
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

logger = logging.getLogger("generate_background")

SCALE = 2
OUTPUT_DIR = Path(__file__).resolve().parent / "backgrounds"
FONT_DIR = Path(os.environ.get("BASKETDB_FONT_DIR", "/mnt/c/Windows/Fonts"))
FONT_FILES = {"regular": "segoeui.ttf", "semibold": "seguisb.ttf", "bold": "segoeuib.ttf"}
FALLBACK_FONTS = {
    "regular": "DejaVuSans.ttf",
    "semibold": "DejaVuSans-Bold.ttf",
    "bold": "DejaVuSans-Bold.ttf",
}

RGBA = tuple[int, int, int, int]
PAGE = (9, 12, 17, 255)            # #090C11, à reprendre pour le wallpaper de Power BI
CARD_TOP = (20, 27, 38, 255)
CARD_BOTTOM = (13, 18, 25, 255)
HERO_FROM = (79, 33, 12, 255)
HERO_TO = (17, 24, 35, 255)
ACCENT = (249, 115, 22, 255)       # #F97316
SLATE = (51, 65, 85, 255)
TEXT = (241, 245, 249, 255)
MUTED = (128, 144, 166, 255)
NOTE = (183, 192, 205, 255)

BORDER_ALPHA = {Style.HERO: 170, Style.CARD: 60, Style.MINI: 90, Style.SLOT: 110,
                Style.NAV: 110}
GLOW_ALPHA = {Style.HERO: 150, Style.CARD: 45, Style.SLOT: 35, Style.NAV: 35}
RADIUS = {Style.HERO: 14, Style.CARD: 14, Style.MINI: 10, Style.SLOT: 10, Style.NAV: 24}


def s(value: float) -> int:
    """Convertit des pixels du canevas en pixels de l'image, à l'échelle SCALE."""
    return round(value * SCALE)


def with_alpha(color: RGBA, alpha: int) -> RGBA:
    return color[0], color[1], color[2], alpha


@lru_cache
def _warn_missing_fonts(directory: Path) -> None:
    logger.warning("Segoe UI introuvable dans %s : rendu en DejaVu Sans", directory)


@lru_cache
def font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    """Police Segoe UI à la taille `size` (en pixels du canevas), ou DejaVu Sans à défaut."""
    path = FONT_DIR / FONT_FILES[weight]
    if path.is_file():
        return ImageFont.truetype(str(path), s(size))
    _warn_missing_fonts(FONT_DIR)
    return ImageFont.truetype(FALLBACK_FONTS[weight], s(size))


def _box(zone: Zone) -> tuple[int, int, int, int]:
    return s(zone.x), s(zone.y), s(zone.right) - 1, s(zone.bottom) - 1


def _composite(canvas: Image.Image, layer: Image.Image, x: int, y: int) -> None:
    """Superpose `layer` en (x, y), en le rognant s'il dépasse du canevas."""
    left, top = max(0, -x), max(0, -y)
    right = min(layer.width, canvas.width - x)
    bottom = min(layer.height, canvas.height - y)
    if right > left and bottom > top:
        canvas.alpha_composite(layer.crop((left, top, right, bottom)), (x + left, y + top))


def _radial_glow(canvas: Image.Image, center: tuple[int, int], radius: int, color: RGBA,
                 strength: int) -> None:
    """Halo circulaire, doux sur ses bords, centré sur `center` (pixels du canevas)."""
    size = s(radius) * 2
    falloff = ImageOps.invert(Image.radial_gradient("L")).resize((size, size))
    falloff = falloff.point(lambda value: value * value * strength // (255 * 255))
    layer = Image.new("RGBA", (size, size), with_alpha(color, 0))
    layer.putalpha(falloff)
    _composite(canvas, layer, s(center[0]) - size // 2, s(center[1]) - size // 2)


def _gradient(size: tuple[int, int], start: RGBA, end: RGBA, *, diagonal: bool) -> Image.Image:
    """Dégradé de `start` vers `end`, vertical ou en diagonale depuis le coin haut gauche."""
    mask = Image.linear_gradient("L").resize(size)
    if diagonal:
        across = Image.linear_gradient("L").rotate(90)
        mask = ImageChops.add(mask, across.resize(size), scale=2.0)
    return Image.composite(Image.new("RGBA", size, end), Image.new("RGBA", size, start), mask)


def _fill(canvas: Image.Image, zone: Zone) -> None:
    """Remplit la zone selon son style, avec des coins arrondis."""
    size = (s(zone.width), s(zone.height))
    match zone.style:
        case Style.HERO:
            fill = _gradient(size, HERO_FROM, HERO_TO, diagonal=True)
        case Style.MINI:
            fill = Image.new("RGBA", size, (8, 11, 16, 170))
        case Style.SLOT | Style.NAV:
            fill = Image.new("RGBA", size, (15, 20, 28, 255))
        case _:
            fill = _gradient(size, CARD_TOP, CARD_BOTTOM, diagonal=False)
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1),
                                           radius=s(RADIUS[zone.style]), fill=255)
    fill.putalpha(ImageChops.multiply(fill.getchannel("A"), mask))
    canvas.alpha_composite(fill, (s(zone.x), s(zone.y)))
    ImageDraw.Draw(canvas, "RGBA").rounded_rectangle(
        _box(zone), radius=s(RADIUS[zone.style]),
        outline=with_alpha(ACCENT, BORDER_ALPHA[zone.style]), width=s(1),
    )


def _glows(canvas: Image.Image, zones: Sequence[Zone]) -> None:
    """Halo orange autour des cartes, dessiné sur un calque flouté en une seule passe."""
    layer = Image.new("RGBA", canvas.size, with_alpha(ACCENT, 0))
    draw = ImageDraw.Draw(layer)
    for zone in zones:
        alpha = GLOW_ALPHA.get(zone.style)
        if alpha:
            draw.rounded_rectangle(_box(zone), radius=s(RADIUS[zone.style]),
                                   outline=with_alpha(ACCENT, alpha), width=s(4))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(s(9))))


def _title(draw: ImageDraw.ImageDraw, zone: Zone) -> None:
    """Icône, titre et sous-titre explicatif en haut d'une carte."""
    content = zone.content
    if content.icon:
        draw_icon(draw, content.icon, (s(zone.x + 16), s(zone.y + 15), s(20)), ACCENT, s(1.6))
    draw.text((s(zone.x + 44), s(zone.y + 13)), content.title, font=font("semibold", 13),
              fill=TEXT, anchor="la")
    if content.subtitle:
        draw.text((s(zone.x + 44), s(zone.y + 32)), content.subtitle, font=font("regular", 10),
                  fill=MUTED, anchor="la")


def _wrap(text: str, typeface: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Coupe `text` en lignes qui tiennent dans `max_width` pixels de l'image."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if typeface.getlength(candidate) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _hero_note(draw: ImageDraw.ImageDraw, zone: Zone) -> None:
    """Encadré « Comment lire » à droite de la valeur principale."""
    left = zone.x + zone.width // 2 + 16
    draw.line([(s(left - 16), s(zone.y + 60)), (s(left - 16), s(zone.y + 152))],
              fill=(255, 255, 255, 28), width=s(1))
    draw.text((s(left), s(zone.y + 60)), "COMMENT LIRE", font=font("semibold", 9),
              fill=ACCENT, anchor="la")
    typeface = font("regular", 11)
    for index, line in enumerate(_wrap(zone.note, typeface, s(zone.width // 2 - 40))):
        draw.text((s(left), s(zone.y + 80 + index * 17)), line, font=typeface, fill=NOTE,
                  anchor="la")


def _legend(canvas: Image.Image, zone: Zone) -> None:
    """Barre de dégradé « Élevé / Faible » à droite d'une carte de chaleur."""
    center = zone.right - 24
    top, bottom = zone.y + 76, zone.bottom - 28
    bar = _gradient((s(8), s(bottom - top)), ACCENT, (31, 42, 55, 255), diagonal=False)
    mask = Image.new("L", bar.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bar.width - 1, bar.height - 1),
                                           radius=s(4), fill=255)
    bar.putalpha(mask)
    canvas.alpha_composite(bar, (s(center - 4), s(top)))
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.text((s(center), s(top - 6)), "Élevé", font=font("regular", 9), fill=MUTED,
              anchor="ms")
    draw.text((s(center), s(bottom + 6)), "Faible", font=font("regular", 9), fill=MUTED,
              anchor="mt")


def _court(canvas: Image.Image, zone: Zone) -> None:
    """Demi-terrain au trait, original, fondu vers la gauche, dans la droite de la carte."""
    width, height = s(120), s(zone.height - 16)
    layer = Image.new("RGBA", (width, height), with_alpha(ACCENT, 0))
    draw = ImageDraw.Draw(layer)
    line, stroke = with_alpha(ACCENT, 150), s(1.5)
    pad = s(6)
    left, top, right, bottom = pad, pad, width - pad, height - pad
    middle = (top + bottom) / 2
    key_half, key_length = (bottom - top) * 0.18, (right - left) * 0.32
    draw.rectangle((left, top, right, bottom), outline=line, width=stroke)
    draw.rectangle((right - key_length, middle - key_half, right, middle + key_half),
                   outline=line, width=stroke)
    draw.ellipse((right - key_length - key_half, middle - key_half,
                  right - key_length + key_half, middle + key_half), outline=line, width=stroke)
    hoop_x, arc_radius = right - s(9), (bottom - top) * 0.5
    draw.arc((hoop_x - arc_radius, middle - arc_radius, hoop_x + arc_radius,
              middle + arc_radius), 90, 270, fill=line, width=stroke)
    draw.ellipse((hoop_x - s(3), middle - s(3), hoop_x + s(3), middle + s(3)),
                 outline=line, width=stroke)
    draw.arc((left - key_half * 1.4, middle - key_half * 1.4, left + key_half * 1.4,
              middle + key_half * 1.4), -90, 90, fill=line, width=stroke)
    fade = Image.linear_gradient("L").rotate(90)
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), fade.resize(layer.size)))
    _radial_glow(canvas, (zone.right - 50, zone.y + zone.height // 2), 70, ACCENT, 60)
    canvas.alpha_composite(layer, (s(zone.right - 128), s(zone.y + 8)))


def _paint_zone(canvas: Image.Image, zone: Zone) -> None:
    """Dessine une zone et ses enfants : fond, bordure, puis textes et décors."""
    _fill(canvas, zone)
    draw = ImageDraw.Draw(canvas, "RGBA")
    match zone.style:
        case Style.HERO | Style.CARD:
            _title(draw, zone)
        case Style.MINI:
            draw_icon(draw, zone.content.icon or "ball", (s(zone.x + 14), s(zone.y + 26), s(26)),
                      ACCENT, s(1.8))
            draw.text((s(zone.x + 52), s(zone.y + 54)), zone.content.title,
                      font=font("regular", 10), fill=NOTE, anchor="la")
        case Style.SLOT:
            draw_icon(draw, zone.content.icon or "calendar", (s(zone.x + 10), s(zone.y + 8),
                      s(14)), ACCENT, s(1.4))
            draw.text((s(zone.x + 30), s(zone.y + 8)), zone.content.title,
                      font=font("semibold", 10), fill=TEXT, anchor="la")
        case Style.NAV:
            pass
    if zone.note:
        _hero_note(draw, zone)
    if zone.legend:
        _legend(canvas, zone)
    if zone.illustration:
        _court(canvas, zone)
    for child in zone.children:
        _paint_zone(canvas, child)


def _brand(canvas: Image.Image, page: Page) -> None:
    """Logo, nom et accroche à gauche de l'en-tête."""
    _radial_glow(canvas, (38, 46), 60, ACCENT, 90)
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.ellipse((s(16), s(24), s(60), s(68)), fill=ACCENT)
    draw_icon(draw, "ball", (s(16), s(24), s(44)), PAGE, s(2.2))
    name_font = font("bold", 24)
    draw.text((s(72), s(26)), "BasketDB", font=name_font, fill=TEXT, anchor="la")
    divider = 72 + name_font.getlength("BasketDB") / SCALE + 16
    draw.line([(s(divider), s(26)), (s(divider), s(64))], fill=(255, 255, 255, 40), width=s(1))
    title_font = font("semibold", 15)
    draw.text((s(divider + 16), s(25)), "Analyses d'avant-match NBA", font=title_font,
              fill=TEXT, anchor="la")
    draw.text((s(divider + 16), s(49)), f"Explorer · Analyser · Anticiper   |   {page.name}",
              font=font("regular", 10), fill=MUTED, anchor="la")
    end = divider + 16 + title_font.getlength("Analyses d'avant-match NBA") / SCALE
    if end > 456:
        logger.warning("%s : le titre de l'en-tête déborde sur les segments", page.slug)


def render(page: Page) -> Image.Image:
    """Image du fond de `page`, en WIDTH × HEIGHT × SCALE pixels."""
    check_layout(page.zones)
    canvas = Image.new("RGBA", (s(WIDTH), s(HEIGHT)), PAGE)
    _radial_glow(canvas, (280, 230), 560, ACCENT, 34)
    _radial_glow(canvas, (1120, 640), 520, SLATE, 60)
    _glows(canvas, page.zones)
    for zone in page.zones:
        _paint_zone(canvas, zone)
    _brand(canvas, page)
    return canvas.convert("RGB")


def positions_markdown(pages: Sequence[Page]) -> str:
    """Tableau des positions des visuels, page par page, à reporter dans Power BI."""
    blocks: list[str] = []
    for page in pages:
        rows = [
            f"### {page.name}",
            "",
            "| Zone | Visuel | Champs | x | y | Largeur | Hauteur |",
            "|---|---|---|---|---|---|---|",
        ]
        for zone in iter_zones(page.zones):
            x, y, width, height = zone.visual_box()
            rows.append(
                f"| {zone.name} | {zone.content.visual} | {zone.content.field} "
                f"| {x} | {y} | {width} | {height} |"
            )
        blocks.append("\n".join(rows))
    return "\n\n".join(blocks)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fonds de page du dashboard BasketDB.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR,
                        help="dossier des PNG (par défaut : powerbi/assets/backgrounds)")
    parser.add_argument("--positions", action="store_true",
                        help="affiche les positions des visuels au lieu de générer les fonds")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Génère un fond par page ; renvoie 1 si la grille est invalide."""
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if args.positions:
        print(positions_markdown(PAGES))
        return 0
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for page in PAGES:
        try:
            image = render(page)
        except ValueError as exc:
            logger.error("%s : grille invalide : %s", page.slug, exc)
            return 1
        path = args.output_dir / f"{page.slug}.png"
        image.save(path, optimize=True)
        logger.info("Fond enregistré : %s (%d × %d)", path, image.width, image.height)
    return 0


if __name__ == "__main__":
    sys.exit(main())
