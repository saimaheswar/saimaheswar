#!/usr/bin/env python3
"""Generates the SVG images in assets/ and README.md from data/repos.json.

    pip install fonttools brotli
    python3 scripts/build.py

The retro font (Press Start 2P, SIL OFL) is subset to the characters each image
uses and embedded in the SVG, so it shows on GitHub where web fonts can't load.
Everything else is plain vector, so it stays sharp at any size.
"""
import base64
import io
import json
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
FONT_FILE = ROOT / "fonts" / "PressStart2P.woff2"

# palette
BG = "#07090a"
CARD_TOP = "#0e1411"
CARD_BOT = "#090c0a"
BORDER = "#1c2a1f"
NEON = "#39ff14"
NEON_SOFT = "#7dff5c"
TEXT = "#e4f3df"
MUTED = "#8aa585"
PILL_BG = "#12201a"

RETRO = "'PS2P', 'Press Start 2P', ui-monospace, Menlo, Consolas, monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"

GLYPHS = {
    "shield": ["##########", "#........#", "#........#", "#...##...#", "#...##...#", ".#......#.", ".#......#.", "..#....#..", "...#..#...", "....##...."],
    "swap": ["......#...", ".......#..", "##########", ".......#..", "......#...", "...#......", "..#.......", "##########", "..#.......", "...#......"],
    "waves": ["..........", ".#..#..#..", "#.##.##.##", "..........", ".#..#..#..", "#.##.##.##", "..........", ".#..#..#..", "#.##.##.##", ".........."],
    "mail": ["##########", "##......##", "#.#....#.#", "#..#..#..#", "#...##...#", "#........#", "#........#", "#........#", "##########", ".........."],
    "window": ["##########", "#.#......#", "##########", "#........#", "#..####..#", "#........#", "#..####..#", "#........#", "#........#", "##########"],
    "bike": ["..........", "...##.....", "....###...", "..........", ".###..###.", "#...##...#", "#..#..#..#", "#...##...#", ".###..###.", ".........."],
    "hex": ["..######..", ".#......#.", "#........#", "#...##...#", "#...##...#", "#........#", ".#......#.", "..######..", "..........", ".........."],
    "bars": ["..........", ".......#..", ".......#..", "....#..#..", "....#..#..", ".#..#..#..", ".#..#..#..", ".#..#..#..", "##########", ".........."],
    "lock": ["...####...", "..#....#..", "..#....#..", "..#....#..", "##########", "#........#", "#...##...#", "#...##...#", "#........#", "##########"],
    "calendar": [".#......#.", "##########", "#........#", "#.##.##..#", "#........#", "#.##.##.##", "#........#", "#.##.....#", "#........#", "##########"],
    "prompt": ["..........", "##........", ".##.......", "..##......", ".##.......", "##........", "......####", "..........", "..........", ".........."],
    "cap": ["....##....", "..######..", "##########", ".########.", "..######..", "........#.", "........#.", ".......###", "..........", ".........."],
}
for _n, _rows in GLYPHS.items():
    assert len(_rows) == 10 and all(len(r) == 10 for r in _rows), _n


# ---------------------------------------------------------------- helpers

def embedded_font(chars):
    """Base64 woff2 of Press Start 2P limited to `chars`."""
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = []
    opts.name_IDs = []
    opts.notdef_outline = True
    font = TTFont(str(FONT_FILE))
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(sorted(set(chars))) + " ")
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


def svg(width, height, body, title, retro_chars):
    font_css = ""
    if retro_chars:
        font_css = (
            "<style>@font-face{font-family:'PS2P';src:url(data:font/woff2;base64,"
            + embedded_font(retro_chars)
            + ") format('woff2');}</style>"
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">'
        f"<title>{escape(title)}</title>{font_css}{body}</svg>\n"
    )


def t(x, y, s, size, fill, family=SANS, weight="normal", anchor="start", extra=""):
    return (
        f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" fill="{fill}" '
        f'font-weight="{weight}" text-anchor="{anchor}"{extra}>{escape(s)}</text>'
    )


def glyph(name, x, y, px):
    cells = [
        f'<rect x="{x + c * px}" y="{y + r * px}" width="{px}" height="{px}"/>'
        for r, row in enumerate(GLYPHS[name])
        for c, ch in enumerate(row)
        if ch == "#"
    ]
    return f'<g fill="{NEON}" shape-rendering="crispEdges">' + "".join(cells) + "</g>"


def gradients(prefix):
    return (
        "<defs>"
        f'<linearGradient id="{prefix}-bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CARD_TOP}"/><stop offset="1" stop-color="{CARD_BOT}"/></linearGradient>'
        f'<radialGradient id="{prefix}-glow" cx="0" cy="0" r="1" gradientUnits="objectBoundingBox"><stop offset="0" stop-color="{NEON}" stop-opacity=".16"/><stop offset="1" stop-color="{NEON}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="{prefix}-txt" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{NEON_SOFT}"/><stop offset="1" stop-color="{NEON}"/></linearGradient>'
        "</defs>"
    )


def pills(items, x, y, max_x, size=10.5, pad=9, h=20, gap=6, fill=PILL_BG, stroke=BORDER, color=NEON_SOFT, weight="600"):
    out, cx = [], x
    for item in items:
        w = len(item) * size * 0.6 + pad * 2
        if cx + w > max_x:
            break
        out.append(f'<rect x="{cx:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{fill}" stroke="{stroke}"/>')
        out.append(t(f"{cx + w / 2:.1f}", y + h / 2 + size * 0.36, item, size, color, weight=weight, anchor="middle"))
        cx += w + gap
    return "".join(out)


# ---------------------------------------------------------------- banner

def banner(data):
    w, h = 900, 200
    name, role = data["name"], data["role"]
    n = len(data["repos"])
    stats = [(str(n), "public repos"), ("706", "tests across 4 data projects"), ("PY · TS", "main languages")]
    body = [
        gradients("b"),
        f'<rect width="{w}" height="{h}" rx="22" fill="url(#b-bg)"/>',
        f'<rect width="{w}" height="{h}" rx="22" fill="url(#b-glow)"/>',
        '<defs><pattern id="dots" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1" fill="#39ff14" opacity=".10"/></pattern></defs>',
        f'<rect width="{w}" height="{h}" rx="22" fill="url(#dots)"/>',
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="21.5" fill="none" stroke="{BORDER}"/>',
        f'<circle cx="46" cy="40" r="5" fill="{NEON}"><animate attributeName="opacity" values="1;.25;1" dur="2s" repeatCount="indefinite"/></circle>',
        t(60, 44, "PORTFOLIO / ONLINE", 9, MUTED, RETRO),
        t(44, 112, name, 36, "url(#b-txt)", RETRO),
        t(46, 152, role, 20, TEXT, SANS, "500"),
        f'<rect x="{46 + len(role) * 10.3:.0f}" y="136" width="10" height="20" rx="2" fill="{NEON}">'
        '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.1s" repeatCount="indefinite"/></rect>',
    ]
    # right-hand stat column
    x0 = 640
    for i, (big, small) in enumerate(stats):
        y = 62 + i * 48
        body.append(f'<rect x="{x0 - 16}" y="{y - 20}" width="3" height="34" rx="1.5" fill="{NEON}" opacity="{1 - i * 0.25}"/>')
        body.append(t(x0, y, big, 17, NEON, RETRO))
        body.append(t(x0, y + 17, small, 11.5, MUTED, SANS))
    retro = name + "PORTFOLIO / ONLINE" + "".join(b for b, _ in stats)
    return svg(w, h, "".join(body), f"{name}: {role}", retro)


# ---------------------------------------------------------------- repo cards

def card(r, i):
    w, h = 300, 156
    title = r.get("title", r["repo"])
    size = min(10, int(222 / len(title) * 10) / 10)
    body = [
        gradients(f"c{i}"),
        f'<rect width="{w}" height="{h}" rx="16" fill="url(#c{i}-bg)"/>',
        f'<rect width="{w}" height="{h}" rx="16" fill="url(#c{i}-glow)"/>',
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="15.5" fill="none" stroke="{BORDER}"/>',
        t(18, 33, title, size, NEON, RETRO),
        f'<g opacity=".95">{glyph(r["glyph"], 256, 16, 2.6)}</g>',
    ]
    y = 60
    for line in r["desc"]:
        body.append(t(18, y, line, 12.5, TEXT, SANS))
        y += 18
    body.append(pills(r["stack"], 18, 98, w - 14))
    body.append(f'<line x1="18" y1="128" x2="{w - 18}" y2="128" stroke="{BORDER}"/>')
    body.append(f'<circle cx="22" cy="142" r="2.8" fill="{NEON}"/>')
    body.append(t(32, 146, r["stat"], 11, MUTED, SANS))
    m = 6  # transparent margin so neighbouring cards have a gap
    return svg(w + 2 * m, h + 2 * m, f'<g transform="translate({m},{m})">' + "".join(body) + "</g>",
               f"{title}: {' '.join(r['desc'])}", title)


# ---------------------------------------------------------------- toolbox

def toolbox(data):
    w = 900
    rows = data["stack_rows"]
    h = 56 + len(rows) * 34
    body = [
        gradients("t"),
        f'<rect width="{w}" height="{h}" rx="22" fill="url(#t-bg)"/>',
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="21.5" fill="none" stroke="{BORDER}"/>',
        t(30, 38, "TOOLBOX", 10, NEON, RETRO),
    ]
    for ri, row in enumerate(rows):
        body.append(pills(row, 30, 56 + ri * 34, w - 20, size=11, pad=12, h=24, gap=8, color=TEXT, weight="600"))
    body.append(t(w - 30, 38, f"github.com/{data['user']}", 11, MUTED, SANS, anchor="end"))
    return svg(w, h, "".join(body), "Tools: " + ", ".join(", ".join(r) for r in rows), "TOOLBOX")


# ---------------------------------------------------------------- build

def main():
    data = json.loads((ROOT / "data" / "repos.json").read_text())
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    files = {"banner.svg": banner(data), "toolbox.svg": toolbox(data)}
    for i, r in enumerate(data["repos"]):
        files[f"card-{r['repo'].lower()}.svg"] = card(r, i)
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")

    user = data["user"]
    quote = {'"': "&quot;"}
    cards = "\n".join(
        f'<a href="https://github.com/{user}/{r["repo"]}"><img src="assets/card-{r["repo"].lower()}.svg" '
        f'alt="{escape(r.get("title", r["repo"]) + ": " + " ".join(r["desc"]), quote)}" width="32.5%"></a>'
        for r in data["repos"]
    )
    readme = f"""<p align="center">
<img src="assets/banner.svg" alt="{escape(data['name'])}: {escape(data['role'])}" width="100%">
</p>

<p align="center">
{cards}
</p>

<p align="center">
<img src="assets/toolbox.svg" alt="Tools: Python, SQL, TypeScript, PySpark, Kafka, Spark, DuckDB, dbt, Airflow, Postgres, Redis, SQLite, Docker, React, Next.js, Angular, FastAPI" width="100%">
</p>
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    total = sum(len(c) for c in files.values()) // 1024
    print(f"wrote {len(files)} images ({total} KB) and README.md")


if __name__ == "__main__":
    main()
