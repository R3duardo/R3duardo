"""Pixel-art Pikachu sprite shared by the SVG generators.

The pixel data was extracted once from a two-frame running-Pikachu GIF
(30x30 grid of upscaled pixels): each cell was sampled, the background and
watermark dropped, the colours snapped to the small palette below, both frames
cropped to a common box and mirrored so the sprite faces right.

`pikachu_svg` returns an SVG <g> centred on (0, 0). Pixels shared by both
frames are drawn once; the pixels that differ live in two frame groups
(classes `leg-a` / `leg-b`) that `RUN_CSS` alternates.
"""

COLORS = {
    "K": "#0c0401",  # outline
    "Y": "#f8f202",  # body yellow
    "L": "#ebec48",  # light yellow (edge highlight)
    "O": "#fee434",  # orange-yellow shade
    "C": "#eedc7b",  # cream
    "N": "#8e6c00",  # nose
    "B": "#754801",  # back stripes
    "D": "#593f24",  # tail base
}

# "." is transparent. Both frames share the same grid and anchor.
FRAME_A = [
    ".....KK.........",
    ".KKKKKKKKK......",
    ".KLYLKKLLLKKK...",
    "..KYYKCLYYYYLK..",
    "...KLKKKLYYYYLK.",
    "....KLLKYYYYYYK.",
    "..KKKLKOOYYOKYLK",
    "..KCCKKOOONOYYLK",
    "...KBKDBBOOYYYK.",
    "..KDDKCOOYOCKCK.",
    "...KDKDBBYYKKLK.",
    "...KKKKCLYYYLKK.",
    "....KCKKLLLLKLLK",
    ".....KLLKKKK.KK.",
    "......KK........",
]

FRAME_B = [
    ".....KK.........",
    "KKKKKKKKKK......",
    "KLLYLKKLLLKKK...",
    ".KYYYKCLYYYYLK..",
    "..KLLKKKLYYYYLK.",
    "...KYLLKYYYYYYK.",
    ".KKKYLKOOYYOKYLK",
    ".KCCCKKOOONOYYLK",
    "..KBKKDBBOOYYYK.",
    ".KDDKKCOOYOCKCK.",
    "..KDDKDBBYYKKLK.",
    "...KKKKCLYYYLLK.",
    "......KKLLLLLK..",
    "......KLKKKKKLK.",
    "......KKKK.KKKK.",
]

WIDTH = len(FRAME_A[0])
HEIGHT = len(FRAME_A)


def _layers():
    """Split the frames into (shared, only-A, only-B) pixel grids."""
    shared, only_a, only_b = [], [], []
    for row_a, row_b in zip(FRAME_A, FRAME_B):
        s, a, b = [], [], []
        for ca, cb in zip(row_a, row_b):
            same = ca == cb
            s.append(ca if same else ".")
            a.append("." if same else ca)
            b.append("." if same else cb)
        shared.append("".join(s))
        only_a.append("".join(a))
        only_b.append("".join(b))
    return shared, only_a, only_b


def _rects(rows, px, ox, oy):
    """One <rect> per horizontal run of same-coloured pixels."""
    out = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            ch = row[x]
            end = x + 1
            while end < len(row) and row[end] == ch:
                end += 1
            if ch in COLORS:
                out.append(
                    f'<rect x="{ox + x * px:g}" y="{oy + y * px:g}" '
                    f'width="{(end - x) * px:g}" height="{px:g}" fill="{COLORS[ch]}"/>'
                )
            x = end
    return "".join(out)


def pikachu_svg(px=2.0):
    """Return the sprite as an SVG group centred on the origin.

    A thin light rim (an SVG filter) keeps the near-black outline readable
    on dark backgrounds such as GitHub's dark theme.
    """
    ox = -WIDTH * px / 2
    oy = -HEIGHT * px / 2
    rim = px * 0.5
    shared, only_a, only_b = _layers()
    return (
        "<defs>"
        '<filter id="pika-rim" x="-20%" y="-20%" width="140%" height="140%">'
        f'<feMorphology in="SourceAlpha" operator="dilate" radius="{rim:g}" result="grow"/>'
        '<feFlood flood-color="#fef3c7" flood-opacity=".85"/>'
        '<feComposite in2="grow" operator="in" result="rim"/>'
        '<feMerge><feMergeNode in="rim"/><feMergeNode in="SourceGraphic"/></feMerge>'
        "</filter>"
        "</defs>"
        '<g shape-rendering="crispEdges" filter="url(#pika-rim)">'
        f"{_rects(shared, px, ox, oy)}"
        f'<g class="leg-a">{_rects(only_a, px, ox, oy)}</g>'
        f'<g class="leg-b">{_rects(only_b, px, ox, oy)}</g>'
        "</g>"
    )


# CSS that alternates the two run frames (0.2s each); include it in the
# generator's <style>.
RUN_CSS = (
    ".leg-a{animation:legA .4s steps(1) infinite}"
    ".leg-b{animation:legB .4s steps(1) infinite}"
    "@keyframes legA{0%{opacity:1}50%{opacity:0}}"
    "@keyframes legB{0%{opacity:0}50%{opacity:1}}"
)
