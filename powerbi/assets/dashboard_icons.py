"""Icônes vectorielles originales du dashboard, dessinées au trait avec Pillow.

Chaque icône se dessine dans une boîte carrée (x, y, côté) ; les coordonnées internes
sont exprimées entre 0 et 1, puis mises à l'échelle.
"""
from collections.abc import Callable

from PIL import ImageDraw

Box = tuple[float, float, float]
Color = tuple[int, int, int, int]


def _p(box: Box, u: float, v: float) -> tuple[float, float]:
    x, y, side = box
    return x + u * side, y + v * side


def _rect(box: Box, u0: float, v0: float, u1: float, v1: float) -> list[tuple[float, float]]:
    return [_p(box, u0, v0), _p(box, u1, v1)]


def _ball(draw: ImageDraw.ImageDraw, box: Box, color: Color, width: int) -> None:
    draw.ellipse(_rect(box, 0.08, 0.08, 0.92, 0.92), outline=color, width=width)
    draw.line([_p(box, 0.5, 0.08), _p(box, 0.5, 0.92)], fill=color, width=width)
    draw.line([_p(box, 0.08, 0.5), _p(box, 0.92, 0.5)], fill=color, width=width)
    draw.arc(_rect(box, -0.30, 0.15, 0.42, 0.85), -62, 62, fill=color, width=width)
    draw.arc(_rect(box, 0.58, 0.15, 1.30, 0.85), 118, 242, fill=color, width=width)


def _house(draw: ImageDraw.ImageDraw, box: Box, color: Color, width: int) -> None:
    draw.line([_p(box, 0.08, 0.50), _p(box, 0.50, 0.12), _p(box, 0.92, 0.50)],
              fill=color, width=width, joint="curve")
    draw.line([_p(box, 0.22, 0.42), _p(box, 0.22, 0.90), _p(box, 0.78, 0.90),
               _p(box, 0.78, 0.42)], fill=color, width=width, joint="curve")
    draw.line([_p(box, 0.42, 0.90), _p(box, 0.42, 0.64), _p(box, 0.58, 0.64),
               _p(box, 0.58, 0.90)], fill=color, width=width, joint="curve")


def _calendar(draw: ImageDraw.ImageDraw, box: Box, color: Color, width: int) -> None:
    draw.rounded_rectangle(_rect(box, 0.10, 0.20, 0.90, 0.90), radius=box[2] * 0.1,
                           outline=color, width=width)
    draw.line([_p(box, 0.10, 0.42), _p(box, 0.90, 0.42)], fill=color, width=width)
    for u in (0.32, 0.68):
        draw.line([_p(box, u, 0.08), _p(box, u, 0.30)], fill=color, width=width)
    for u in (0.30, 0.50, 0.70):
        draw.rectangle(_rect(box, u - 0.05, 0.60, u + 0.05, 0.70), fill=color)


def _route(draw: ImageDraw.ImageDraw, box: Box, color: Color, width: int) -> None:
    draw.line([_p(box, 0.16, 0.84), _p(box, 0.82, 0.18)], fill=color, width=width)
    draw.line([_p(box, 0.44, 0.18), _p(box, 0.82, 0.18), _p(box, 0.82, 0.56)],
              fill=color, width=width, joint="curve")
    draw.ellipse(_rect(box, 0.08, 0.76, 0.24, 0.92), fill=color)


def _trophy(draw: ImageDraw.ImageDraw, box: Box, color: Color, width: int) -> None:
    draw.line([_p(box, 0.26, 0.14), _p(box, 0.74, 0.14)], fill=color, width=width)
    draw.arc(_rect(box, 0.26, -0.16, 0.74, 0.62), 0, 180, fill=color, width=width)
    draw.arc(_rect(box, 0.08, 0.16, 0.34, 0.42), 90, 270, fill=color, width=width)
    draw.arc(_rect(box, 0.66, 0.16, 0.92, 0.42), 270, 450, fill=color, width=width)
    draw.line([_p(box, 0.50, 0.62), _p(box, 0.50, 0.80)], fill=color, width=width)
    draw.line([_p(box, 0.30, 0.88), _p(box, 0.70, 0.88)], fill=color, width=width)


def _trend_down(draw: ImageDraw.ImageDraw, box: Box, color: Color, width: int) -> None:
    draw.line([_p(box, 0.08, 0.24), _p(box, 0.38, 0.54), _p(box, 0.56, 0.38),
               _p(box, 0.90, 0.76)], fill=color, width=width, joint="curve")
    draw.line([_p(box, 0.62, 0.78), _p(box, 0.90, 0.78), _p(box, 0.90, 0.50)],
              fill=color, width=width, joint="curve")


def _grid(draw: ImageDraw.ImageDraw, box: Box, color: Color, width: int) -> None:
    faint = (*color[:3], color[3] // 3)
    filled = {(0, 0), (1, 1), (2, 0), (2, 2)}
    for column in range(3):
        for row in range(3):
            u, v = 0.08 + column * 0.30, 0.08 + row * 0.30
            area = _rect(box, u, v, u + 0.24, v + 0.24)
            draw.rectangle(area, fill=color if (column, row) in filled else faint)


def _donut(draw: ImageDraw.ImageDraw, box: Box, color: Color, width: int) -> None:
    faint = (*color[:3], color[3] // 3)
    area = _rect(box, 0.10, 0.10, 0.90, 0.90)
    draw.arc(area, 0, 360, fill=faint, width=width * 2)
    draw.arc(area, -90, 115, fill=color, width=width * 2)


def _bars(draw: ImageDraw.ImageDraw, box: Box, color: Color, width: int) -> None:
    for v, length in ((0.14, 0.86), (0.42, 0.64), (0.70, 0.42)):
        draw.rounded_rectangle(_rect(box, 0.10, v, length, v + 0.16), radius=box[2] * 0.04,
                               fill=color)


def _line(draw: ImageDraw.ImageDraw, box: Box, color: Color, width: int) -> None:
    faint = (*color[:3], color[3] // 2)
    draw.line([_p(box, 0.10, 0.10), _p(box, 0.10, 0.90), _p(box, 0.92, 0.90)],
              fill=faint, width=width, joint="curve")
    draw.line([_p(box, 0.20, 0.70), _p(box, 0.42, 0.44), _p(box, 0.62, 0.58),
               _p(box, 0.88, 0.24)], fill=color, width=width, joint="curve")


def _shield(draw: ImageDraw.ImageDraw, box: Box, color: Color, width: int) -> None:
    points = [(0.50, 0.06), (0.88, 0.20), (0.82, 0.60), (0.50, 0.94), (0.18, 0.60),
              (0.12, 0.20), (0.50, 0.06)]
    draw.line([_p(box, u, v) for u, v in points], fill=color, width=width, joint="curve")


def _pin(draw: ImageDraw.ImageDraw, box: Box, color: Color, width: int) -> None:
    draw.arc(_rect(box, 0.20, 0.06, 0.80, 0.66), 150, 390, fill=color, width=width)
    draw.line([_p(box, 0.24, 0.52), _p(box, 0.50, 0.94), _p(box, 0.76, 0.52)],
              fill=color, width=width, joint="curve")
    draw.ellipse(_rect(box, 0.40, 0.26, 0.60, 0.46), fill=color)


def _flame(draw: ImageDraw.ImageDraw, box: Box, color: Color, width: int) -> None:
    points = [(0.50, 0.06), (0.70, 0.34), (0.82, 0.58), (0.74, 0.82), (0.50, 0.94),
              (0.26, 0.82), (0.18, 0.58), (0.34, 0.40), (0.42, 0.58), (0.50, 0.06)]
    draw.line([_p(box, u, v) for u, v in points], fill=color, width=width, joint="curve")


def _clock(draw: ImageDraw.ImageDraw, box: Box, color: Color, width: int) -> None:
    draw.ellipse(_rect(box, 0.08, 0.08, 0.92, 0.92), outline=color, width=width)
    draw.line([_p(box, 0.50, 0.24), _p(box, 0.50, 0.50), _p(box, 0.70, 0.62)],
              fill=color, width=width, joint="curve")


def _battery(draw: ImageDraw.ImageDraw, box: Box, color: Color, width: int) -> None:
    draw.rounded_rectangle(_rect(box, 0.06, 0.28, 0.82, 0.72), radius=box[2] * 0.08,
                           outline=color, width=width)
    draw.rectangle(_rect(box, 0.86, 0.40, 0.94, 0.60), fill=color)
    draw.rectangle(_rect(box, 0.16, 0.38, 0.30, 0.62), fill=color)


def _star(draw: ImageDraw.ImageDraw, box: Box, color: Color, width: int) -> None:
    points = [(0.50, 0.06), (0.62, 0.36), (0.94, 0.38), (0.69, 0.58), (0.78, 0.90),
              (0.50, 0.72), (0.22, 0.90), (0.31, 0.58), (0.06, 0.38), (0.38, 0.36),
              (0.50, 0.06)]
    draw.line([_p(box, u, v) for u, v in points], fill=color, width=width, joint="curve")


def _versus(draw: ImageDraw.ImageDraw, box: Box, color: Color, width: int) -> None:
    draw.line([_p(box, 0.10, 0.34), _p(box, 0.88, 0.34)], fill=color, width=width)
    draw.line([_p(box, 0.70, 0.18), _p(box, 0.88, 0.34), _p(box, 0.70, 0.50)],
              fill=color, width=width, joint="curve")
    draw.line([_p(box, 0.90, 0.68), _p(box, 0.12, 0.68)], fill=color, width=width)
    draw.line([_p(box, 0.30, 0.52), _p(box, 0.12, 0.68), _p(box, 0.30, 0.84)],
              fill=color, width=width, joint="curve")


def _cross(draw: ImageDraw.ImageDraw, box: Box, color: Color, width: int) -> None:
    draw.ellipse(_rect(box, 0.08, 0.08, 0.92, 0.92), outline=color, width=width)
    draw.line([_p(box, 0.34, 0.34), _p(box, 0.66, 0.66)], fill=color, width=width)
    draw.line([_p(box, 0.66, 0.34), _p(box, 0.34, 0.66)], fill=color, width=width)


ICONS: dict[str, Callable[[ImageDraw.ImageDraw, Box, Color, int], None]] = {
    "ball": _ball,
    "bars": _bars,
    "battery": _battery,
    "calendar": _calendar,
    "clock": _clock,
    "cross": _cross,
    "donut": _donut,
    "flame": _flame,
    "grid": _grid,
    "house": _house,
    "line": _line,
    "pin": _pin,
    "route": _route,
    "shield": _shield,
    "star": _star,
    "trend_down": _trend_down,
    "trophy": _trophy,
    "versus": _versus,
}


def draw_icon(
    draw: ImageDraw.ImageDraw, name: str, box: Box, color: Color, width: int
) -> None:
    """Dessine l'icône `name` dans la boîte ; une icône inconnue lève KeyError avec la liste."""
    icon = ICONS.get(name)
    if icon is None:
        raise KeyError(f"Icône inconnue : {name!r} (disponibles : {sorted(ICONS)})")
    icon(draw, box, color, width)
