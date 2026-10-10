"""Generate a Pikachu-turns-your-contributions-red animated SVG (dark + light).

Pikachu runs the contribution grid boustrophedon (row 0 left->right, row 1
right->left, ...). The graph starts in GitHub's green palette. Every non-empty
cell Pikachu passes is charged: it flashes electric yellow and then turns red
at the same intensity level (empty cells stay empty). Once the run is done the
fully red graph is held for a couple of seconds, then the cells fade back to
green (via the empty colour) and the loop starts again. Only CSS animations are
used, so the SVG keeps animating inside an <img> on GitHub (no JS, no external
resources).

Usage:
    python scripts/pokemon_contrib.py --user R3duardo --out-dir dist
    python scripts/pokemon_contrib.py --from-file contributions.html --out-dir /tmp/out

Python 3 standard library only.
"""

import argparse
import datetime as _dt
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pikachu import HEIGHT as PIKA_H  # noqa: E402
from pikachu import RUN_CSS, pikachu_svg  # noqa: E402
from pikachu import WIDTH as PIKA_W  # noqa: E402

# --------------------------------------------------------------------------
# Layout / timing
# --------------------------------------------------------------------------
CELL = 11
GAP = 3
STEP = CELL + GAP
RADIUS = 2
ROWS = 7

PX = 1.8                      # Pikachu pixel size (sprite size = WIDTH/HEIGHT * PX)
SPRITE_W = PIKA_W * PX
SPRITE_H = PIKA_H * PX
FEET_OVERLAP = 3              # how far the feet dip into the current row

PAD_X = 30
PAD_TOP = int(SPRITE_H - FEET_OVERLAP) + 6
PAD_BOTTOM = 8

DURATION = 30.0               # seconds per loop
RUN_END = 84.0                # % of the loop spent running the grid (~25s)
FLASH = 0.9                   # % a charged cell stays electric yellow
FADE = 0.7                    # % to fade from yellow to red
RESET_START = 92.0            # % red graph starts fading back to green
RESET_MID = 94.0              # % cells pass through the empty colour (no muddy red/green mix)
RESET_END = 96.0              # % grid fully green again (red held ~2s before)

ELECTRIC = "#facc15"
GLOW = "#fb923c"              # orange rim on the brightest red level
GLOW_OPACITY = 0.6

# index 0 = empty colour, 1..4 = contribution level
PALETTES = {
    "dark": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
    "light": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
}
RED_PALETTES = {
    "dark": ["#161b22", "#5c1010", "#991b1b", "#dc2626", "#f87171"],
    "light": ["#ebedf0", "#fecaca", "#f87171", "#dc2626", "#991b1b"],
}
SPARK_STROKE = {"dark": "#fff6a8", "light": "#9a7b00"}

# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------
_TD_RE = re.compile(r"<td\b[^>]*>", re.I)
_ATTR_RE = {
    "date": re.compile(r'data-date="(\d{4}-\d{2}-\d{2})"'),
    "level": re.compile(r'data-level="(\d)"'),
    "id": re.compile(r'id="contribution-day-component-(\d+)-(\d+)"'),
}


def fetch_html(user):
    url = f"https://github.com/users/{user}/contributions"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (pokemon-contrib generator)",
            "Accept": "text/html",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def parse_cells(html):
    """Return {(row, col): level} from GitHub's contributions HTML."""
    by_id = {}
    by_date = {}
    for tag in _TD_RE.findall(html):
        date_m = _ATTR_RE["date"].search(tag)
        level_m = _ATTR_RE["level"].search(tag)
        if not date_m:
            continue
        level = max(0, min(4, int(level_m.group(1)))) if level_m else 0
        id_m = _ATTR_RE["id"].search(tag)
        if id_m:
            row, col = int(id_m.group(1)), int(id_m.group(2))
            if 0 <= row < ROWS:
                by_id[(row, col)] = level
        by_date[date_m.group(1)] = level

    if by_id:
        return by_id

    # Fallback: derive the position from the date (weeks start on Sunday).
    cells = {}
    if not by_date:
        return cells
    dates = sorted(_dt.date.fromisoformat(d) for d in by_date)
    first = dates[0]
    first_sunday = first - _dt.timedelta(days=(first.weekday() + 1) % 7)
    for d in dates:
        row = (d.weekday() + 1) % 7
        col = (d - first_sunday).days // 7
        cells[(row, col)] = by_date[d.isoformat()]
    return cells


# --------------------------------------------------------------------------
# Path of Pikachu
# --------------------------------------------------------------------------
def _cell_x(col):
    return PAD_X + col * STEP


def _cell_y(row):
    return PAD_TOP + row * STEP


def _cx(col):
    return _cell_x(col) + CELL / 2


def _pika_y(row):
    """Sprite centre y so its feet stand on top of `row`."""
    return _cell_y(row) + FEET_OVERLAP - SPRITE_H / 2


def build_path(ncols):
    """Waypoints (x, y, facing) of the run, start to finish."""
    left = _cx(-2)
    right = _cx(ncols + 1)
    pts = []
    for row in range(ROWS):
        y = _pika_y(row)
        if row % 2 == 0:
            a, b, facing = left, right, 1
        else:
            a, b, facing = right, left, -1
        if not pts:
            pts.append((a, y, facing))
        else:
            # Step down from the previous row, still facing the old way,
            # then turn around.
            px_, _, pf = pts[-1]
            pts.append((px_, y, pf))
            pts.append((a, y, facing))
        pts.append((b, y, facing))
    return pts


def path_times(pts):
    """Percent of the loop at which each waypoint is reached."""
    dist = [0.0]
    for (x0, y0, _), (x1, y1, _) in zip(pts, pts[1:]):
        dist.append(dist[-1] + abs(x1 - x0) + abs(y1 - y0))
    total = dist[-1] or 1.0
    return [d / total * RUN_END for d in dist], total


def hit_percent(row, col, pts, times):
    """Loop % when Pikachu's centre passes over the centre of (row, col)."""
    x = _cx(col)
    y = _pika_y(row)
    for (x0, y0, _), (x1, y1, _), t0, t1 in zip(pts, pts[1:], times, times[1:]):
        if y0 == y1 == y and min(x0, x1) <= x <= max(x0, x1) and x0 != x1:
            return t0 + (t1 - t0) * (x - x0) / (x1 - x0)
    return None


# --------------------------------------------------------------------------
# SVG
# --------------------------------------------------------------------------
def _pct(v):
    return f"{v:.3f}".rstrip("0").rstrip(".") + "%"


def _num(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


SPARK = (
    "M0,-4 L-2.5,0.5 L-0.4,0.5 L-1.8,5 L2.6,-1 L0.4,-1 L1.6,-4 Z"
)


def render(cells, theme, user):
    palette = PALETTES[theme]
    reds = RED_PALETTES[theme]
    empty = palette[0]
    ncols = (max(c for _, c in cells) + 1) if cells else 53

    width = PAD_X * 2 + ncols * STEP - GAP
    height = PAD_TOP + ROWS * STEP - GAP + PAD_BOTTOM

    pts = build_path(ncols)
    times, _ = path_times(pts)

    css = [
        RUN_CSS,
        f".c{{animation-duration:{DURATION:g}s;animation-timing-function:linear;"
        "animation-iteration-count:infinite}",
    ]
    rects = []
    n = 0
    for (row, col), level in sorted(cells.items()):
        x, y = _cell_x(col), _cell_y(row)
        fill = palette[level]
        red = reds[level]
        attrs = (
            f'x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'rx="{RADIUS}" ry="{RADIUS}" fill="{fill}"'
        )
        p = hit_percent(row, col, pts, times) if level > 0 else None
        if p is None:
            rects.append(f"<rect {attrs}/>")
            continue
        n += 1
        name = f"k{n}"
        glow = level == 4
        off = ";stroke-opacity:0" if glow else ""
        on = f";stroke-opacity:{GLOW_OPACITY}" if glow else ""
        css.append(
            f"@keyframes {name}{{"
            f"0%,{_pct(p)}{{fill:{fill}{off}}}"
            f"{_pct(p + 0.05)},{_pct(p + FLASH)}{{fill:{ELECTRIC}{off}}}"
            f"{_pct(p + FLASH + FADE)},{_pct(RESET_START)}{{fill:{red}{on}}}"
            f"{_pct(RESET_MID)}{{fill:{empty}{off}}}"
            f"{_pct(RESET_END)},100%{{fill:{fill}{off}}}}}"
        )
        if glow:
            attrs += f' stroke="{GLOW}" stroke-width="1.2" stroke-opacity="0"'
        rects.append(f'<rect class="c" style="animation-name:{name}" {attrs}/>')

    # Pikachu movement (outer group) and facing (inner group).
    move = []
    flip = []
    last_facing = None
    for (x, y, facing), t in zip(pts, times):
        move.append(f"{_pct(t)}{{transform:translate({_num(x)}px,{_num(y)}px)}}")
        if facing != last_facing:
            flip.append(f"{_pct(t)}{{transform:scale({facing},1)}}")
            last_facing = facing
    sx, sy, _ = pts[0]
    ex, ey, _ = pts[-1]
    move.append(f"98%{{transform:translate({_num(ex)}px,{_num(ey)}px)}}")
    move.append(f"98.01%,100%{{transform:translate({_num(sx)}px,{_num(sy)}px)}}")
    flip.append("98.01%,100%{transform:scale(1,1)}")

    css.append("@keyframes pmove{" + "".join(move) + "}")
    css.append("@keyframes pflip{" + "".join(flip) + "}")
    css.append(
        "@keyframes pfade{0%,"
        + _pct(RUN_END + 0.5)
        + "{opacity:1}"
        + _pct(RUN_END + 2)
        + ",98.5%{opacity:0}100%{opacity:1}}"
    )
    css.append(
        f".pmove{{animation:pmove {DURATION:g}s linear infinite,"
        f"pfade {DURATION:g}s linear infinite}}"
        f".pflip{{transform-origin:0 0;animation:pflip {DURATION:g}s steps(1,end) infinite}}"
        ".spark{animation:spark .45s steps(1,end) infinite}"
        "@keyframes spark{0%{opacity:1;transform:translate(0,0)}"
        "33%{opacity:0}66%{opacity:1;transform:translate(1px,-1.5px)}}"
        ".hop{animation:hop .3s ease-in-out infinite}"
        "@keyframes hop{0%,100%{transform:translateY(0)}50%{transform:translateY(-1px)}}"
    )

    spark_x = SPRITE_W / 2 + 3
    spark_y = SPRITE_H / 2 - 7
    pika = (
        f'<g class="pmove" style="transform:translate({_num(sx)}px,{_num(sy)}px)">'
        '<g class="pflip">'
        f'<g class="hop">{pikachu_svg(PX)}</g>'
        f'<g transform="translate({_num(spark_x)},{_num(spark_y)})">'
        f'<path class="spark" d="{SPARK}" fill="{ELECTRIC}" '
        f'stroke="{SPARK_STROKE[theme]}" stroke-width="0.6" stroke-linejoin="round"/>'
        "</g>"
        "</g></g>"
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f"<title>{user}'s contributions turned red by Pikachu</title>"
        f"<desc>Animated contribution graph: Pikachu runs over the grid and "
        f"charges every day with contributions, turning it from green to red.</desc>"
        f"<style>{''.join(css)}</style>"
        f'<g shape-rendering="geometricPrecision">{"".join(rects)}</g>'
        f"{pika}"
        "</svg>"
    )


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--user", default="R3duardo", help="GitHub username")
    ap.add_argument("--out-dir", default="dist", help="output directory")
    ap.add_argument(
        "--from-file", help="read contributions HTML from a file instead of GitHub"
    )
    args = ap.parse_args(argv)

    if args.from_file:
        with open(args.from_file, encoding="utf-8") as fh:
            html = fh.read()
    else:
        html = fetch_html(args.user)

    cells = parse_cells(html)
    if not cells:
        sys.exit("error: no contribution cells found in the HTML")

    os.makedirs(args.out_dir, exist_ok=True)
    nonzero = sum(1 for v in cells.values() if v > 0)
    for theme in ("dark", "light"):
        path = os.path.join(args.out_dir, f"pokemon-contributions-{theme}.svg")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render(cells, theme, args.user))
        print(f"wrote {path} ({len(cells)} days, {nonzero} with contributions)")


if __name__ == "__main__":
    main()
