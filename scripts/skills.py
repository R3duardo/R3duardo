"""Generate an animated "tech skills" grid SVG for the profile README.

Run from the repo root:  python scripts/skills.py
Reads devicon SVGs from assets/icons/ and writes assets/skills.svg.

Each icon sits in a dark, brand-tinted circle with a neon glow that
"breathes" (staggered so a wave travels diagonally across the grid) and a
subtle float. Animation is pure CSS so it runs inside GitHub's <img> tags;
without animation the SVG still looks complete (glow at a resting level).
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICON_DIR = ROOT / "assets" / "icons"
OUT = ROOT / "assets" / "skills.svg"

BG = (13, 17, 23)  # GitHub dark canvas, used to tint circle fills
LIGHT_FILL = "#d5dae1"  # for black logos so they stay readable
LIGHT_GLOW = "#e6edf3"
LIGHT_RING = "#9da7b3"  # darker rim so light circles keep an edge on white pages

# (icon file stem, label, glow colour, light circle?)
SKILLS = [
    ("html5", "HTML5", "#e34f26", False),
    ("css3", "CSS3", "#1572b6", False),
    ("javascript", "JavaScript", "#f7df1e", False),
    ("typescript", "TypeScript", "#3178c6", False),
    ("react", "React", "#61dafb", False),
    ("angular", "Angular", "#f0306a", False),
    ("nextjs", "Next.js", LIGHT_GLOW, True),
    ("tailwindcss", "Tailwind", "#38bdf8", False),
    ("astro", "Astro", "#bc52ee", False),
    ("dot-net", ".NET", "#512bd4", False),
    ("nodejs", "Node.js", "#5fa04e", False),
    ("express", "Express", LIGHT_GLOW, True),
    ("mysql", "SQL", "#00a0c6", False),
    ("mongodb", "MongoDB", "#47a248", False),
    ("csharp", "C#", "#9b4f96", False),
    ("python", "Python", "#ffd43b", False),
    ("php", "PHP", "#777bb4", False),
    ("bash", "Bash", LIGHT_GLOW, True),
    ("git", "Git", "#f05032", False),
    ("github", "GitHub", LIGHT_GLOW, True),
    ("docker", "Docker", "#2496ed", False),
]

# Per-icon colour tweaks applied to the raw markup: (old, new) pairs.
# Astro's default logo body is near-black, which vanishes on a dark circle;
# swap it for the white body Astro uses on dark backgrounds.
RECOLOR = {
    "astro": [('stop-color="#000014"', 'stop-color="#ffffff"'),
              ('stop-color="#150426"', 'stop-color="#e9ddff"')],
    # MySQL's deep-blue dolphin is too dark on a dark circle; lift it.
    "mysql": [('fill="#00618A"', 'fill="#4fb3d9"')],
}

COLS = 7
PITCH_X = 120          # horizontal distance between circle centres
PITCH_Y = 150          # vertical distance between rows
RADIUS = 55            # circle radius (110px diameter)
ICON = 62              # icon box size inside the circle
LABEL_GAP = 24         # circle bottom -> label baseline
PILL_H = 20            # label pill height (keeps text legible on light + dark)
PAD_X = 30             # outer padding so the glow is never clipped
PAD_TOP = 36

BREATH_S = 3.0         # glow cycle
FLOAT_S = 4.0          # float cycle
WAVE_STEP = 0.22       # delay between diagonals


def tint(hex_colour, amount):
    """Mix a brand colour into the dark background (amount = brand share)."""
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    mix = [round(c * amount + bg * (1 - amount)) for c, bg in zip((r, g, b), BG)]
    return "#{:02x}{:02x}{:02x}".format(*mix)


def load_icon(stem, prefix):
    """Return an icon's inner markup with every id/reference namespaced."""
    raw = (ICON_DIR / f"{stem}-original.svg").read_text(encoding="utf-8")
    raw = re.sub(r"<\?xml[^>]*\?>", "", raw)
    raw = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    inner = re.search(r"<svg\b[^>]*>(.*)</svg>", raw, flags=re.S)
    if not inner:
        raise ValueError(f"no <svg> root in {stem}")
    body = inner.group(1)

    for old, new in RECOLOR.get(stem, []):
        body = body.replace(old, new)

    ids = set(re.findall(r'\bid="([^"]+)"', body))
    for ident in sorted(ids, key=len, reverse=True):
        new = f"{prefix}-{ident}"
        esc = re.escape(ident)
        body = re.sub(rf'\bid="{esc}"', f'id="{new}"', body)
        body = re.sub(rf"url\(\s*['\"]?#{esc}['\"]?\s*\)", f"url(#{new})", body)
        body = re.sub(rf'((?:xlink:)?href)="#{esc}"', rf'\1="#{new}"', body)

    body = re.sub(r">\s+<", "><", body).strip()
    return body


def build():
    rows = -(-len(SKILLS) // COLS)
    width = PAD_X * 2 + PITCH_X * COLS
    height = PAD_TOP + PITCH_Y * (rows - 1) + 2 * RADIUS + LABEL_GAP + PILL_H

    css = f"""
.cell{{animation:float {FLOAT_S}s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}
.halo{{opacity:.6;animation:breathe {BREATH_S}s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}
.ring{{stroke-opacity:.85}}
.lbl{{font:600 12.5px -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;fill:#e6edf3;letter-spacing:.2px}}
.pill{{fill:#161b22;fill-opacity:.92;stroke-width:1;stroke-opacity:.55}}
@keyframes breathe{{0%,100%{{opacity:.3;transform:scale(.97)}}50%{{opacity:1;transform:scale(1.03)}}}}
@keyframes float{{0%,100%{{transform:translateY(2px)}}50%{{transform:translateY(-3px)}}}}
@media (prefers-reduced-motion:reduce){{.cell,.halo{{animation:none}}}}
""".strip()

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Tech skills: {", ".join(s[1] for s in SKILLS)}">',
        f"<title>Tech skills</title>",
        f"<style>{css}</style>",
        "<defs>"
        '<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">'
        '<feGaussianBlur stdDeviation="6"/></filter>'
        '<filter id="glow-tight" x="-50%" y="-50%" width="200%" height="200%">'
        '<feGaussianBlur stdDeviation="2"/></filter>'
        "</defs>",
    ]

    for i, (stem, label, glow, light) in enumerate(SKILLS):
        col, row = i % COLS, i // COLS
        cx = PAD_X + PITCH_X * col + PITCH_X / 2
        cy = PAD_TOP + RADIUS + PITCH_Y * row
        fill = LIGHT_FILL if light else tint(glow, 0.14)
        ring = LIGHT_RING if light else glow
        # Negative delays: the wave is already mid-flight at first paint.
        wave = (col + row) * WAVE_STEP
        breathe_delay = f"-{wave:.2f}s"
        float_delay = f"-{wave * 1.3:.2f}s"
        icon = load_icon(stem, f"i{i}")
        ix, iy = cx - ICON / 2, cy - ICON / 2
        # Label sits on a dark pill so it reads on GitHub's light and dark themes.
        pill_w = round(len(label) * 7.6 + 22)
        pill_y = cy + RADIUS + LABEL_GAP - PILL_H / 2 - 6

        parts.append(
            f'<g class="cell" style="animation-delay:{float_delay}">'
            f'<g class="halo" opacity=".6" style="animation-delay:{breathe_delay}">'
            f'<circle cx="{cx:g}" cy="{cy:g}" r="{RADIUS}" fill="none" stroke="{glow}" '
            f'stroke-width="6" filter="url(#glow)"/>'
            f'<circle cx="{cx:g}" cy="{cy:g}" r="{RADIUS}" fill="none" stroke="{glow}" '
            f'stroke-width="2.5" filter="url(#glow-tight)"/>'
            "</g>"
            f'<circle class="ring" cx="{cx:g}" cy="{cy:g}" r="{RADIUS}" fill="{fill}" '
            f'stroke="{ring}" stroke-width="1.5"/>'
            f'<svg x="{ix:g}" y="{iy:g}" width="{ICON}" height="{ICON}" viewBox="0 0 128 128">'
            f"{icon}</svg>"
            "</g>"
            f'<rect class="pill" x="{cx - pill_w / 2:g}" y="{pill_y:g}" width="{pill_w:g}" '
            f'height="{PILL_H}" rx="{PILL_H / 2:g}" stroke="{glow}"/>'
            f'<text class="lbl" x="{cx:g}" y="{pill_y + PILL_H / 2 + 4.5:g}" '
            f'text-anchor="middle">{label}</text>'
        )

    parts.append("</svg>")
    return "".join(parts) + "\n", width, height


def main():
    svg, width, height = build()
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({width}x{height}, {len(svg.encode()) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
