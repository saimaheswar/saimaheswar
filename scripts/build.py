#!/usr/bin/env python3
"""Generates the SVG images in assets/ from data/repos.json.

    python3 scripts/build.py

Edit data/repos.json (names, descriptions, stack, stats) and rerun. No dependencies.
"""
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

NEON = "#39ff14"
BRIGHT = "#c4ffb3"
DIM = "#2a8f12"
FAINT = "#0f3d08"
BG = "#030703"
FONT = "ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"

# 10x10 pixel icons, one per repo.
GLYPHS = {
    "shield": [
        "##########", "#........#", "#........#", "#...##...#", "#...##...#",
        ".#......#.", ".#......#.", "..#....#..", "...#..#...", "....##....",
    ],
    "swap": [
        "......#...", ".......#..", "##########", ".......#..", "......#...",
        "...#......", "..#.......", "##########", "..#.......", "...#......",
    ],
    "waves": [
        "..........", ".#..#..#..", "#.##.##.##", "..........", ".#..#..#..",
        "#.##.##.##", "..........", ".#..#..#..", "#.##.##.##", "..........",
    ],
    "mail": [
        "##########", "##......##", "#.#....#.#", "#..#..#..#", "#...##...#",
        "#........#", "#........#", "#........#", "##########", "..........",
    ],
    "window": [
        "##########", "#.#......#", "##########", "#........#", "#..####..#",
        "#........#", "#..####..#", "#........#", "#........#", "##########",
    ],
    "bike": [
        "..........", "...##.....", "....###...", "..........", ".###..###.",
        "#...##...#", "#..#..#..#", "#...##...#", ".###..###.", "..........",
    ],
    "hex": [
        "..######..", ".#......#.", "#........#", "#...##...#", "#...##...#",
        "#........#", ".#......#.", "..######..", "..........", "..........",
    ],
    "bars": [
        "..........", ".......#..", ".......#..", "....#..#..", "....#..#..",
        ".#..#..#..", ".#..#..#..", ".#..#..#..", "##########", "..........",
    ],
    "lock": [
        "...####...", "..#....#..", "..#....#..", "..#....#..", "##########",
        "#........#", "#...##...#", "#...##...#", "#........#", "##########",
    ],
    "calendar": [
        ".#......#.", "##########", "#........#", "#.##.##..#", "#........#",
        "#.##.##.##", "#........#", "#.##.....#", "#........#", "##########",
    ],
    "prompt": [
        "..........", "##........", ".##.......", "..##......", ".##.......",
        "##........", "......####", "..........", "..........", "..........",
    ],
    "cap": [
        "....##....", "..######..", "##########", ".########.", "..######..",
        "........#.", "........#.", ".......###", "..........", "..........",
    ],
}
for name, rows in GLYPHS.items():
    assert len(rows) == 10 and all(len(r) == 10 for r in rows), name

DEFS = f"""<defs>
  <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
    <feGaussianBlur stdDeviation="2.2" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="glow-s" x="-20%" y="-20%" width="140%" height="140%">
    <feGaussianBlur stdDeviation="1" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
    <rect width="4" height="1.4" fill="#000" opacity=".28"/>
  </pattern>
</defs>"""


def svg(width, height, body, title):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">\n'
        f"<title>{escape(title)}</title>\n{DEFS}\n"
        f'<rect width="{width}" height="{height}" fill="{BG}"/>\n{body}\n'
        f'<rect width="{width}" height="{height}" fill="url(#scan)" pointer-events="none"/>\n'
        "</svg>\n"
    )


def text(x, y, s, size=13, fill=NEON, weight="normal", anchor="start", extra="", glow=False):
    f = ' filter="url(#glow-s)"' if glow else ""
    return (
        f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{fill}" '
        f'font-weight="{weight}" text-anchor="{anchor}" xml:space="preserve"{f}{extra}>{escape(s)}</text>'
    )


def glyph(name, x, y, px=4, fill=NEON):
    cells = []
    for r, row in enumerate(GLYPHS[name]):
        for c, ch in enumerate(row):
            if ch == "#":
                cells.append(f'<rect x="{x + c * px}" y="{y + r * px}" width="{px - 0.6}" height="{px - 0.6}"/>')
    return f'<g fill="{fill}" filter="url(#glow-s)">' + "".join(cells) + "</g>"


def frame(w, h, inset=1.5, color=NEON, opacity=0.75, corner=10):
    x0, y0, x1, y1 = inset, inset, w - inset, h - inset
    c = corner
    brackets = (
        f"M{x0},{y0 + c} V{y0} H{x0 + c} "
        f"M{x1 - c},{y0} H{x1} V{y0 + c} "
        f"M{x1},{y1 - c} V{y1} H{x1 - c} "
        f"M{x0 + c},{y1} H{x0} V{y1 - c}"
    )
    return (
        f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="none" '
        f'stroke="{DIM}" stroke-width="1" opacity="{opacity}"/>'
        f'<path d="{brackets}" fill="none" stroke="{color}" stroke-width="2.5" filter="url(#glow-s)"/>'
    )


def reveal(delay, dur=0.35):
    """Opacity 0 -> 1 after `delay` seconds. The element stays visible if animation is unsupported."""
    total = delay + dur
    return (
        f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{delay / total:.4f};1" '
        f'dur="{total}s" begin="0s" fill="freeze"/>'
    )


# ---------------------------------------------------------------- banner

def banner(data):
    w, h = 900, 250
    name, role = data["name"], data["role"]
    n_pub = len(data["repos"])
    lines = [
        (34, 62, f"$ whoami", 15, DIM, "normal", 0.2),
        (34, 138, name, 56, NEON, "bold", 0.9),
        (36, 172, f"> {role}", 18, BRIGHT, "normal", 1.9),
        (36, 202, f"> {n_pub} public repos · data pipelines · web apps · ML", 15, DIM, "normal", 2.6),
    ]
    body = [frame(w, h, corner=18)]
    body.append(f'<rect x="0" y="0" width="{w}" height="26" fill="{FAINT}"/>')
    body.append(text(14, 18, "saimaheswar@github:~", 12, NEON))
    for i, col in enumerate((NEON, DIM, FAINT)):
        body.append(f'<rect x="{w - 62 + i * 18}" y="8" width="10" height="10" fill="{col}"/>')
    for x, y, s, size, fill, weight, delay in lines:
        glow = size >= 50
        g = f'<g>{text(x, y, s, size, fill, weight, glow=glow, extra=(" letter-spacing=\"3\"" if size >= 50 else ""))}'
        g += reveal(delay) + "</g>"
        body.append(g)
    # prompt line with blinking block cursor
    body.append(text(36, 232, "> ", 15, NEON))
    body.append(
        f'<rect x="56" y="219" width="10" height="16" fill="{NEON}" filter="url(#glow-s)">'
        '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/>'
        "</rect>"
    )
    # decorative pixel glyphs on the right
    body.append(f'<g opacity=".9">{glyph("hex", 700, 60, 9)}</g>')
    body.append(f'<g opacity=".35">{glyph("waves", 640, 150, 5)}{glyph("bars", 800, 150, 5)}</g>')
    return svg(w, h, "\n".join(body), f"{name} — {role}")


# ---------------------------------------------------------------- stats strip

def stats(data):
    w, h = 900, 96
    n = len(data["repos"])
    tiles = [
        (str(n), "PUBLIC REPOS", None),
        ("706", "TESTS ACROSS 4 DATA PROJECTS", None),
        ("PY + TS", "MAIN LANGUAGES", None),
        ("ONLINE", "STATUS", "dot"),
    ]
    tw = (w - 20 - 12 * (len(tiles) - 1)) / len(tiles)
    body = []
    for i, (big, small, kind) in enumerate(tiles):
        x = 10 + i * (tw + 12)
        body.append(f'<rect x="{x}" y="10" width="{tw}" height="{h - 20}" fill="none" stroke="{DIM}" stroke-width="1"/>')
        body.append(f'<rect x="{x}" y="10" width="4" height="{h - 20}" fill="{NEON}" filter="url(#glow-s)"/>')
        body.append(text(x + 18, 52, big, 26, NEON, "bold", glow=True))
        if kind == "dot":
            cx = x + 18 + len(big) * 15.8 + 14
            body.append(
                f'<circle cx="{cx}" cy="44" r="5" fill="{NEON}" filter="url(#glow)">'
                '<animate attributeName="opacity" values="1;0.2;1" dur="1.6s" repeatCount="indefinite"/></circle>'
            )
        body.append(text(x + 18, 74, small, 10.5, DIM))
    return svg(w, h, "\n".join(body), f"{n} public repos, 706 tests across 4 data projects, Python and TypeScript")


# ---------------------------------------------------------------- section headers

def header(label, subtitle=""):
    w, h = 900, 46
    body = [
        text(10, 30, "//", 22, DIM, "bold"),
        text(44, 30, label, 22, NEON, "bold", glow=True, extra=' letter-spacing="2"'),
        f'<line x1="{44 + len(label) * 15 + 18}" y1="24" x2="{w - 10}" y2="24" stroke="{DIM}" stroke-dasharray="3 4"/>',
    ]
    if subtitle:
        body.append(text(w - 10, 14, subtitle, 10, DIM, anchor="end"))
    return svg(w, h, "\n".join(body), label)


# ---------------------------------------------------------------- repo cards

def card(r, index):
    w, h = 440, 200
    title = r.get("title", r["repo"])
    body = [frame(w, h)]
    body.append(f'<rect x="3" y="3" width="{w - 6}" height="26" fill="{FAINT}"/>')
    body.append(
        f'<circle cx="18" cy="16" r="4" fill="{NEON}" filter="url(#glow-s)">'
        f'<animate attributeName="opacity" values="1;0.25;1" dur="{2 + (index % 4) * 0.4:.1f}s" repeatCount="indefinite"/></circle>'
    )
    body.append(text(32, 20, f"[ {title} ]", 13, NEON, "bold", glow=True))
    body.append(text(w - 14, 20, f"{index + 1:02d}", 12, DIM, anchor="end"))
    body.append(glyph(r["glyph"], w - 62, 42, 4))
    y = 58
    for line in r["desc"]:
        body.append(text(18, y, line, 12.5, BRIGHT))
        y += 19
    body.append(f'<line x1="18" y1="118" x2="{w - 18}" y2="118" stroke="{DIM}" stroke-dasharray="3 4"/>')
    body.append(text(18, 142, "stack>", 12, DIM))
    body.append(text(78, 142, r["stack"], 12, NEON))
    body.append(text(18, 164, "stat>", 12, DIM))
    body.append(text(78, 164, r["stat"], 12, NEON))
    body.append(text(w - 18, 187, "[ OPEN REPO >> ]", 11, NEON, "bold", anchor="end", glow=True))
    return svg(w, h, "\n".join(body), f"{title}: {' '.join(r['desc'])}")


# ---------------------------------------------------------------- stack chips

def stack(data):
    w = 900
    rows = data["stack_rows"]
    row_h = 40
    h = 20 + len(rows) * row_h
    body = []
    for ri, row in enumerate(rows):
        x = 12
        y = 14 + ri * row_h
        for label in row:
            cw = len(label) * 9.2 + 26
            body.append(f'<rect x="{x}" y="{y}" width="{cw:.1f}" height="28" fill="none" stroke="{NEON}" stroke-width="1.2" opacity=".85"/>')
            body.append(text(x + cw / 2, y + 19, label, 12.5, NEON, "bold", anchor="middle", glow=True))
            x += cw + 12
    return svg(w, h, "\n".join(body), "Tools: " + ", ".join(", ".join(r) for r in rows))


# ---------------------------------------------------------------- footer

def footer(data):
    w, h = 900, 78
    body = [
        frame(w, h, corner=12),
        text(30, 36, f"> thanks for stopping by.", 16, BRIGHT),
        text(30, 58, f"> github.com/{data['user']}", 13, DIM),
        f'<rect x="{30 + 26 * 9.6:.0f}" y="21" width="9" height="16" fill="{NEON}" filter="url(#glow-s)">'
        '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/></rect>',
        text(w - 24, 44, "EOF", 22, DIM, "bold", anchor="end"),
    ]
    return svg(w, h, "\n".join(body), "end of file")


def main():
    data = json.loads((ROOT / "data" / "repos.json").read_text())
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    files = {
        "banner.svg": banner(data),
        "stats.svg": stats(data),
        "h-repos.svg": header("REPOSITORIES", f"{len(data['repos'])} public"),
        "h-stack.svg": header("TOOLBOX"),
        "stack.svg": stack(data),
        "footer.svg": footer(data),
    }
    for i, r in enumerate(data["repos"]):
        files[f"card-{r['repo'].lower()}.svg"] = card(r, i)
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")

    # README
    cards = []
    repos = data["repos"]
    for i in range(0, len(repos), 2):
        cells = []
        for r in repos[i:i + 2]:
            alt = f"{r.get('title', r['repo'])}: {' '.join(r['desc'])}"
            cells.append(
                f'<td width="50%" align="center"><a href="https://github.com/{data["user"]}/{r["repo"]}">'
                f'<img src="assets/card-{r["repo"].lower()}.svg" alt="{escape(alt, {chr(34): "&quot;"})}" width="100%"></a></td>'
            )
        cards.append("<tr>" + "".join(cells) + "</tr>")
    readme = f"""<div align="center">

<img src="assets/banner.svg" alt="{escape(data['name'])} — {escape(data['role'])}" width="100%">

<img src="assets/stats.svg" alt="{len(repos)} public repos, 706 tests across 4 data projects, Python and TypeScript" width="100%">

<img src="assets/h-repos.svg" alt="Repositories" width="100%">

<table>
{chr(10).join(cards)}
</table>

<img src="assets/h-stack.svg" alt="Toolbox" width="100%">

<img src="assets/stack.svg" alt="Python, SQL, TypeScript, PySpark, Kafka, Spark, DuckDB, dbt, Airflow, Postgres, Redis, SQLite, Docker, React, Next.js, Angular, FastAPI" width="100%">

<a href="https://github.com/{data['user']}?tab=repositories"><img src="assets/footer.svg" alt="github.com/{data['user']}" width="100%"></a>

</div>
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print(f"wrote {len(files)} images and README.md")


if __name__ == "__main__":
    main()
