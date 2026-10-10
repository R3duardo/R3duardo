"""Generate the animated Pokemon-themed footer SVGs for the profile README.

Writes:
  assets/pikachu-run.svg  - Pac-Man style strip: Pikachu eats dots, chased
                            by a rolling Poke Ball.
  assets/thanks.svg       - Scrolling "thanks for visiting" marquee.

Only CSS @keyframes are used (no JS, no external resources) so both files
animate when embedded with <img> on GitHub.

Run from the repo root:  python scripts/footer.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pikachu import HEIGHT as PIKA_H, WIDTH as PIKA_W, RUN_CSS, pikachu_svg  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

# ---------------------------------------------------------------- run strip
W, H = 880, 90
DUR = 9.0                 # seconds per loop
PX = 3                    # Pikachu pixel size
PIKA_HALF_W = PIKA_W * PX / 2
PIKA_HALF_H = PIKA_H * PX / 2
CY = H / 2                # Pikachu centre line
GROUND = CY + PIKA_HALF_H  # feet rest here
BALL_R = 14
GAP = 80                  # Poke Ball centre trails Pikachu centre by this
START = -PIKA_HALF_W - 10  # Pikachu centre at t=0 (just off-screen left)
END = W + GAP + BALL_R + 20  # Pikachu centre at t=1 (ball fully off right)
TRAVEL = END - START
DOT_Y = CY + 5            # roughly mouth height
MOUTH = PIKA_HALF_W - 6   # dot is eaten when it reaches this far ahead


def _pct(v):
    return f"{max(0.0, min(100.0, v)):.2f}%"


def _dots():
    """Yellow dots across the bar plus per-dot 'eaten' keyframes."""
    shapes, css = [], []
    xs = list(range(40, W - 20, 30))
    for i, x in enumerate(xs):
        # fraction of the loop at which Pikachu's mouth reaches this dot
        t = (x - MOUTH - START) / TRAVEL * 100
        big = i % 7 == 3
        if big:  # Pac-Man style "power pellet": a larger, pulsing yellow dot
            shapes.append(
                f'<g class="d{i}"><circle class="pp" cx="{x}" cy="{DOT_Y}" r="6" fill="#ffde00"/></g>'
            )
        else:
            shapes.append(
                f'<circle class="d{i}" cx="{x}" cy="{DOT_Y}" r="3.5" fill="#ffde00"/>'
            )
        css.append(
            f".d{i}{{animation:e{i} {DUR}s linear infinite}}"
            f"@keyframes e{i}{{0%,{_pct(t)}{{opacity:1}}"
            f"{_pct(t + 0.2)},100%{{opacity:0}}}}"
        )
    return "".join(shapes), "".join(css)


def _pokeball(r):
    """Poke Ball centred on the origin."""
    band = r * 0.16
    return (
        f'<circle r="{r}" fill="#ffffff"/>'
        f'<path d="M{-r} 0A{r} {r} 0 0 1 {r} 0Z" fill="#ee1515"/>'
        f'<rect x="{-r}" y="{-band}" width="{2 * r}" height="{2 * band}" fill="#111"/>'
        f'<circle r="{r * 0.36}" fill="#111"/>'
        f'<circle r="{r * 0.22}" fill="#ffffff"/>'
        f'<path d="M{-r * 0.55} {-r * 0.55}A{r * 0.75} {r * 0.75} 0 0 1 {-r * 0.1} {-r * 0.78}" '
        f'stroke="#ff8a80" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
        f'<circle r="{r - 0.6}" fill="none" stroke="#111" stroke-width="1.2"/>'
    )


def _spark(x, y, s, cls):
    """Tiny lightning bolt polygon."""
    pts = [(0, 0), (4, 0), (2, 4), (5, 4), (-1, 11), (1, 6), (-2, 6)]
    p = " ".join(f"{x + a * s:g},{y + b * s:g}" for a, b in pts)
    return f'<polygon class="{cls}" points="{p}" fill="#fff35c" stroke="#ffb300" stroke-width="0.6"/>'


def build_run():
    dots, dot_css = _dots()
    rolls_per_sec = (TRAVEL / DUR) / (2 * 3.14159 * BALL_R)
    spin = 1 / rolls_per_sec

    css = (
        RUN_CSS
        + f".pika{{animation:run {DUR}s linear infinite}}"
        f"@keyframes run{{from{{transform:translateX({START:g}px)}}"
        f"to{{transform:translateX({END:g}px)}}}}"
        ".hop{animation:hop .3s ease-in-out infinite alternate}"
        "@keyframes hop{from{transform:translateY(0)}to{transform:translateY(-3px)}}"
        f".ball{{animation:chase {DUR}s linear infinite}}"
        f"@keyframes chase{{from{{transform:translateX({START - GAP:g}px)}}"
        f"to{{transform:translateX({END - GAP:g}px)}}}}"
        f".spin{{transform-box:fill-box;transform-origin:center;"
        f"animation:spin {spin:.3f}s linear infinite}}"
        "@keyframes spin{to{transform:rotate(360deg)}}"
        ".s1{animation:zap 1.1s steps(1) infinite}"
        ".s2{animation:zap 1.1s steps(1) -.55s infinite}"
        ".s3{animation:zap 1.7s steps(1) -.3s infinite}"
        "@keyframes zap{0%{opacity:1}18%{opacity:0}}"
        ".glow{animation:glow 2.4s ease-in-out infinite alternate}"
        "@keyframes glow{from{opacity:.35}to{opacity:.8}}"
        ".pp{transform-box:fill-box;transform-origin:center;"
        "animation:pp .6s ease-in-out infinite alternate}"
        "@keyframes pp{from{transform:scale(.75)}to{transform:scale(1)}}"
        + dot_css
    )

    sparks = (
        _spark(PIKA_HALF_W - 2, -PIKA_HALF_H - 2, 0.9, "s1")
        + _spark(-PIKA_HALF_W - 6, -PIKA_HALF_H + 6, 0.8, "s2")
        + _spark(PIKA_HALF_W + 4, -4, 0.7, "s3")
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Pikachu running and eating dots, chased by a rolling Poke Ball">
<title>Pikachu run</title>
<style>{css}</style>
<defs><clipPath id="bar"><rect width="{W}" height="{H}" rx="14"/></clipPath></defs>
<rect width="{W}" height="{H}" rx="14" fill="#0b0b0f"/>
<g clip-path="url(#bar)">
<line class="glow" x1="0" y1="{GROUND + 1}" x2="{W}" y2="{GROUND + 1}" stroke="#ffde00" stroke-width="1" stroke-dasharray="2 6"/>
{dots}
<g class="ball"><g transform="translate(0 {GROUND - BALL_R})"><g class="spin">{_pokeball(BALL_R)}</g></g></g>
<g class="pika"><g transform="translate(0 {CY})"><g class="hop">{pikachu_svg(PX)}{sparks}</g></g></g>
</g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="13.5" fill="none" stroke="#ffde00" stroke-opacity=".25"/>
</svg>
"""
    return svg


# ---------------------------------------------------------------- marquee
TW, TH = 880, 70
# Two identical copies of the message sit PERIOD px apart and the pair slides
# left by exactly PERIOD each loop, so the scroll is seamless (no blank gap).
# With the first copy at X0 = PERIOD - TW, the second copy starts just off the
# right edge and the first has fully left the bar by the end of each loop, as
# long as the text is narrower than TW (~680px in Comic Sans MS bold 28px,
# ~650px in Trebuchet/Segoe/sans-serif).
PERIOD = 1000
X0 = PERIOD - TW
MARQUEE_DUR = 12  # seconds per PERIOD (~83 px/s)
MSG = "Thanks for visiting my profile, see you next time!"
TAG = "Gotta code 'em all!"


def _message(x):
    return (
        f'<text class="t" x="{x}" y="34">{MSG}</text>'
        f'<text class="g" x="{x + 4}" y="60"><tspan class="z">⚡</tspan> {TAG} '
        f'<tspan class="z">⚡</tspan></text>'
    )


def build_thanks():
    font = "'Comic Sans MS','Comic Neue','Trebuchet MS','Segoe UI',sans-serif"
    # Thin, semi-transparent dark outline: invisible on GitHub dark, but keeps
    # the bright green / yellow legible on the light theme.
    outline = "paint-order:stroke;stroke:#0d1117;stroke-opacity:.55;stroke-linejoin:round"
    css = (
        f".m{{animation:marquee {MARQUEE_DUR}s linear infinite}}"
        f"@keyframes marquee{{from{{transform:translateX(0)}}"
        f"to{{transform:translateX(-{PERIOD}px)}}}}"
        f"text{{font-family:{font};font-weight:700}}"
        f".t{{font-size:28px;fill:#39d353;stroke-width:2.5px;{outline}}}"
        f".g{{font-size:16px;fill:#ffde00;stroke-width:2.5px;{outline}}}"
        ".z{animation:blink 1s steps(1) infinite}"
        "@keyframes blink{50%{opacity:.3}}"
    )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{TW}" height="{TH}" viewBox="0 0 {TW} {TH}" role="img" aria-label="{MSG} {TAG.replace("'", "&#39;")}">
<title>Thanks for visiting</title>
<style>{css}</style>
<g class="m">{_message(X0)}{_message(X0 + PERIOD)}</g>
</svg>
"""
    return svg


def main():
    os.makedirs(ASSETS, exist_ok=True)
    for name, content in (("pikachu-run.svg", build_run()), ("thanks.svg", build_thanks())):
        path = os.path.join(ASSETS, name)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"wrote {os.path.relpath(path, ROOT)}")


if __name__ == "__main__":
    main()
