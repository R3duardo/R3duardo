"""Pixel-art Pikachu sprite shared by the SVG generators.

Pikachu runs to the right in a side / three-quarter view. The sprite is built
from layered parts (tail, limbs, torso, head) stacked back-to-front into four
run frames. Each part gets its own 1px dark outline as it is stacked, which
gives the clean silhouette plus the inner lines (chin, legs, arm) that make
the pixel art read on both dark and light backgrounds.

`pikachu_svg(px)` returns an SVG <g> centred on (0, 0). Pixels shared by every
frame are drawn once; the rest live in frame groups (classes `leg-a` ..
`leg-d`) that `RUN_CSS` flips through.
"""

COLORS = {
    "O": "#2a1c00",  # outline
    "N": "#2a1c00",  # nose / mouth
    "K": "#1c1c1c",  # ear tips, eye
    "W": "#ffffff",  # eye shine
    "Y": "#f8d030",  # body
    "y": "#d9a514",  # body shade / far limbs
    "h": "#fff3a8",  # highlight
    "R": "#e8402c",  # cheek
    "B": "#a0601c",  # tail base / back stripes
}

# Art area (the outline adds a 1px margin on every side).
_ART_W, _ART_H = 29, 23

# Parts are (top_row, rows). '.' is transparent; rows may be short.
HEAD = (0, [  # ears, head and face
    ".........KK..........K",
    ".........KKKK........KK",
    "..........KKYYY......KKK",
    "............YYYYY....YYY",
    "..............YYYYY.YYYYY",
    "................YYYYYYYYY",
    "................YYhhYYYYYYY",
    "...............YYhYYYYYYYYYY",
    "...............YYYYYYYYYWKYY",
    "...............YYYYYYYYYKKYYY",
    "...............YYYYYYYYYKKYYN",
    "...............YYYYYYRRRYYYYY",
    "...............YYYYYYRRRYYNN",
    "................yyYYYYYYYYY",
    "..................yyYYYYY",
])

TORSO = (13, [  # body with brown back stripes
    ".............YYYYYYY",
    "............YYYYYYYYY",
    "...........BBBYYYYYYYY",
    "...........YYYYYYYYYYY",
    "...........BBBYYYYYYYY",
    "...........YYYYYYYYYYY",
    "............yyYYYYYYY",
    ".............yyyYYYY",
])

TAIL = (5, [  # lightning bolt, brown at the base
    ".YYY",
    "YYYYYY",
    ".YYYYYYY",
    "..YYYYYYY",
    "....YYYYY",
    ".....YYYY",
    "......YYYY",
    "....YYYY",
    "....YYY",
    ".....YYY",
    "......YYY",
    ".......BBB",
    "........BBB",
])

# Run cycle: near limbs in body yellow, far limbs in shade.
FRAME_PARTS = [
    {  # a: stride, near leg forward / far leg back, far paw reaching out
        "tail_dy": 0,
        "far_leg": (20, ["...........yyy", ".........yyy", ".......yyyy"]),
        "far_arm": (15, ["......................yyy", ".......................yyy"]),
        "near_leg": (20, ["...................YYY", "....................YYY",
                          "......................YYYY"]),
        "near_arm": None,
    },
    {  # b: passing, legs gathered, near foot lifted
        "tail_dy": 1,
        "far_leg": (20, [".............yyy", ".............yyy", "............yyyy"]),
        "far_arm": None,
        "near_leg": (20, [".................YYY", ".................YYYY"]),
        "near_arm": (16, ["......................YYY", ".......................YY"]),
    },
    {  # c: stride, near leg back / far leg forward, near paw reaching out
        "tail_dy": 0,
        "far_leg": (20, ["..................yyy", "....................yyy",
                         ".....................yyyy"]),
        "far_arm": None,
        "near_leg": (20, ["............YYY", "..........YYY", ".......YYYY"]),
        "near_arm": (15, [".......................YYY", "........................YY"]),
    },
    {  # d: passing, near foot planted
        "tail_dy": 1,
        "far_leg": (20, ["..............yyy", "..............yyy", ".............yyyy"]),
        "far_arm": None,
        "near_leg": (20, [".................YYY", ".................YYY",
                          ".................YYYY"]),
        "near_arm": (16, ["......................YYY", ".......................YY"]),
    },
]

WIDTH = _ART_W + 2   # grid size in pixels, outline margin included
HEIGHT = _ART_H + 2


def _cells(part, dy=0):
    if part is None:
        return {}
    top, rows = part
    return {
        (x + 1, top + y + dy + 1): ch
        for y, row in enumerate(rows)
        for x, ch in enumerate(row)
        if ch != "."
    }


def _compose(spec):
    """Stack the parts back-to-front, outlining each one as it lands."""
    layers = [
        _cells(TAIL, spec["tail_dy"]),
        _cells(spec["far_leg"]),
        _cells(spec["far_arm"]),
        _cells(spec["near_leg"]),
        _cells(TORSO),
        _cells(HEAD),
        _cells(spec["near_arm"]),
    ]
    canvas = {}
    for cells in layers:
        for (x, y) in cells:
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) not in cells:
                    canvas[(nx, ny)] = "O"
        canvas.update(cells)
    return canvas


FRAMES = [_compose(spec) for spec in FRAME_PARTS]


def _rects(cells, px, ox, oy):
    """Draw cells, merging horizontal runs of one colour into a single rect."""
    out = []
    for y in range(HEIGHT):
        x = 0
        while x < WIDTH:
            ch = cells.get((x, y))
            if ch is None:
                x += 1
                continue
            x0 = x
            while x < WIDTH and cells.get((x, y)) == ch:
                x += 1
            out.append(
                f'<rect x="{ox + x0 * px:g}" y="{oy + y * px:g}" '
                f'width="{(x - x0) * px:g}" height="{px:g}" fill="{COLORS[ch]}"/>'
            )
    return "".join(out)


def _split():
    """Cells identical in every frame, and what is left of each frame."""
    common = {
        pos: ch for pos, ch in FRAMES[0].items()
        if all(f.get(pos) == ch for f in FRAMES[1:])
    }
    per = [{p: c for p, c in f.items() if p not in common} for f in FRAMES]
    return common, per


FRAME_CLASSES = ["leg-a", "leg-b", "leg-c", "leg-d"]
CYCLE = 0.36  # seconds for one full run cycle


def pikachu_svg(px=2.0):
    """Return the sprite as an SVG group centred on the origin."""
    ox = -WIDTH * px / 2
    oy = -HEIGHT * px / 2
    common, per = _split()
    frames = "".join(
        f'<g class="{cls}">{_rects(cells, px, ox, oy)}</g>'
        for cls, cells in zip(FRAME_CLASSES, per)
    )
    return f'<g shape-rendering="crispEdges">{_rects(common, px, ox, oy)}{frames}</g>'


def _run_css():
    n = len(FRAME_CLASSES)
    rules = [
        f".{cls}{{animation:pkf {CYCLE:g}s steps(1) {-((n - i) % n) * CYCLE / n:.2f}s infinite}}"
        for i, cls in enumerate(FRAME_CLASSES)
    ]
    rules.append(f"@keyframes pkf{{0%{{opacity:1}}{100 / n:g}%,100%{{opacity:0}}}}")
    return "".join(rules)


# CSS that flips through the run frames; include it in the generator's <style>.
RUN_CSS = _run_css()
