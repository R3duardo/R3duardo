"""Pixel-art Pikachu sprite shared by the SVG generators.

The sprite faces right. `pikachu_svg` returns an SVG <g> centred on (0, 0)
with two leg frames (classes `leg-a` / `leg-b`) that callers animate.
"""

COLORS = {
    "K": "#1a1a1a",  # ear tips, eyes, nose
    "Y": "#ffde00",  # body
    "D": "#e0b800",  # body shade
    "R": "#ff3b30",  # cheeks
    "W": "#ffffff",  # eye shine
    "B": "#8b5a2b",  # tail base / back stripes
}

BODY = [
    "....K.......K...",
    "....KY.....YK...",
    ".....Y.....Y....",
    ".....YYYYYYY....",
    "BB..YYYYYYYYY...",
    "YYB.YYKYYYKYY...",
    ".YY.YYKWYYKWY...",
    "..YYYRYYKYYRY...",
    "...YYYYYYYYYY...",
    "....BYYYYYYYB...",
    "....YYYYYYYY....",
    "....DYYYYYYD....",
]

LEGS_A = [
    "....Y.Y..Y.Y....",
    "....Y......Y....",
]

LEGS_B = [
    "...Y..Y...Y..Y..",
    "..Y..........Y..",
]

WIDTH = len(BODY[0])
HEIGHT = len(BODY) + len(LEGS_A)


def _rects(rows, px, ox, oy):
    out = []
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in COLORS:
                out.append(
                    f'<rect x="{ox + x * px:g}" y="{oy + y * px:g}" '
                    f'width="{px:g}" height="{px:g}" fill="{COLORS[ch]}"/>'
                )
    return "".join(out)


def pikachu_svg(px=2.0):
    """Return the sprite as an SVG group centred on the origin."""
    ox = -WIDTH * px / 2
    oy = -HEIGHT * px / 2
    legs_y = oy + len(BODY) * px
    return (
        '<g shape-rendering="crispEdges">'
        f"{_rects(BODY, px, ox, oy)}"
        f'<g class="leg-a">{_rects(LEGS_A, px, ox, legs_y)}</g>'
        f'<g class="leg-b">{_rects(LEGS_B, px, ox, legs_y)}</g>'
        "</g>"
    )


# CSS that makes the legs alternate; include it in the generator's <style>.
RUN_CSS = (
    ".leg-a{animation:legA .3s steps(1) infinite}"
    ".leg-b{animation:legB .3s steps(1) infinite}"
    "@keyframes legA{0%{opacity:1}50%{opacity:0}}"
    "@keyframes legB{0%{opacity:0}50%{opacity:1}}"
)
