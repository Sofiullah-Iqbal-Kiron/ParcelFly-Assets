"""Brand guidelines: an A4 landscape vector PDF (one SVG per page, merged), page previews, and a Markdown summary."""
import io
import re
import sys
from pathlib import Path

import cairosvg
from pypdf import PdfWriter, PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pfbrand import ROOT, layout as LY, scenes as SC, symbol as S, text as T, logo as L  # noqa: E402
from pfbrand import pictograms as P  # noqa: E402
from pfbrand import maps as MP  # noqa: E402
from pfbrand.brand import (AMBER, AQUA, CLOUD, CONTACT, COBALT, CYAN, GREEN, INK, MINT, MIST, NAVY, NEUTRALS,  # noqa: E402
                           PALETTE, RED, SKY, SLATE, STATUS, TAGLINE, TAGLINE_BN, WHITE, ICON_SCHEMES)
from pfbrand.svg import Doc, render_png  # noqa: E402
from pfbrand.text import fmt  # noqa: E402

OUT = ROOT / "guidelines"
PW, PH, M = 297.0, 210.0, 16.0
VERSION = "Version 1.0 · November 2026"
_n = [0]


def embed(path, x, y, w=None, h=None, align="xMidYMid"):
    """Inline an asset SVG as a nested <svg> (vector) with namespaced ids."""
    _n[0] += 1
    src = Path(path).read_text(encoding="utf-8")
    vb = re.search(r'viewBox="([^"]+)"', src).group(1)
    vx, vy, vw, vh = (float(v) for v in vb.split())
    inner = re.search(r"<svg[^>]*>(.*)</svg>", src, re.S).group(1)
    inner = re.sub(r"<title>.*?</title>", "", inner, flags=re.S)
    p = f"e{_n[0]}-"
    inner = inner.replace('id="', f'id="{p}').replace("url(#", f"url(#{p}")
    if w is None:
        w = h * vw / vh
    if h is None:
        h = w * vh / vw
    k = min(w / vw, h / vh) if "slice" not in align else max(w / vw, h / vh)
    fw, fh = vw * k, vh * k
    fx = x + (w - fw) / 2 if "xMid" in align else (x if "xMin" in align else x + w - fw)
    fy = y + (h - fh) / 2 if "YMid" in align else (y if "YMin" in align else y + h - fh)
    mode = "slice" if "slice" in align else "meet"
    a = align.replace(" slice", "")
    return (f'<svg x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" viewBox="{vb}" '
            f'preserveAspectRatio="{a} {mode}">{inner}</svg>'), (fx, fy, fx + fw, fy + fh)


def border(bb, colour=MIST, sw=0.3):
    x0, y0, x1, y1 = bb
    return (f'<rect x="{fmt(x0)}" y="{fmt(y0)}" width="{fmt(x1 - x0)}" height="{fmt(y1 - y0)}" fill="none" '
            f'stroke="{colour}" stroke-width="{sw}"/>')


class Page:
    def __init__(self, title, section, dark=False):
        self.title, self.section, self.dark = title, section, dark
        self.d = Doc(PW, PH, unit="mm", title=f"Parcel Fly brand guidelines: {title}")
        self.d.rect(0, 0, PW, PH, NAVY if dark else WHITE)

    def head(self, intro=None, title_size=11.0):
        fg, acc = (WHITE, CYAN) if self.dark else (NAVY, SKY)
        self.d.add(LY.label(self.section, M, M + 3, 2.6, acc, tracking=0.2))
        self.d.add(T.text(self.title, "montserrat", title_size, M, M + 15, fg, "start", 800, tracking=-0.01))
        y = M + 15
        if intro:
            frag, y = LY.para(intro, M, M + 24, 3.4, WHITE if self.dark else SLATE, max_width=150, weight=500)
            self.d.add(frag)
        return y

    def foot(self, num):
        fg = WHITE if self.dark else NAVY
        frag, _ = LY.place_logo("horizontal", "ondark" if self.dark else "color", M, PH - M + 3.2, h=6)
        self.d.add(frag)
        self.d.add(T.text(f"Brand guidelines  ·  {num:02d}", "montserrat", 2.4, PW - M, PH - M + 7.6,
                          fg, "end", 600, opacity=0.7))

    def add(self, *a):
        self.d.add(*a)


def text_block(page, x, y, w, items, size=3.2, colour=None, head_colour=None, gap=6.0):
    colour = colour or (WHITE if page.dark else INK)
    head_colour = head_colour or (CYAN if page.dark else NAVY)
    for title, body in items:
        page.add(T.text(title, "montserrat", size * 1.12, x, y, head_colour, "start", 800))
        frag, last = LY.para(body, x, y + size * 1.75, size, colour, max_width=w, weight=500, leading=1.42)
        page.add(frag)
        y = last + gap
    return y


# ------------------------------------------------------------------ pages

def p_cover():
    pg = Page("Brand guidelines", "", dark=True)
    d = pg.d
    SC.glow(d, PW * 0.85, 0, 230, COBALT, 0.85)
    hh = PH * 1.2
    d.add(SC.watermark(COBALT, PW - S.WIDTH * hh / S.HEIGHT * 0.62, (PH - hh) / 2, hh, 0.65))
    frag, bb = LY.place_logo("stacked", "ondark", M + 4, 46, w=118, tagline="en")
    d.add(frag)
    d.add(T.text("Brand guidelines", "montserrat", 13, M + 4, 158, WHITE, "start", 800))
    d.add(T.text(VERSION, "montserrat", 3.6, M + 4, 167, CYAN, "start", 600))
    b0, b1, b2, b3 = T.ink_bounds(TAGLINE_BN, "mina-bold", 6)
    d.add(T.text(TAGLINE_BN, "mina-bold", 6, M + 4 - b0, 180 - b1, WHITE))
    return pg


def p_contents():
    pg = Page("Contents", "Parcel Fly")
    pg.head()
    items = ["The brand", "The logo", "Construction", "Logo family", "Bangla and tagline lockups", "Clear space and size",
             "Colour versions", "Logo misuse", "Colour palette", "Typography", "Graphic devices and patterns",
             "Hub network and maps", "Pictograms", "Apps and sub-brands", "Social media", "Stationery", "Stamps and seals",
             "Stickers and packaging", "Bags and carry bags", "Apparel and signage", "Merchandise", "Mockups",
             "Web and wallpapers", "Motion", "Files and contacts"]
    for i, it in enumerate(items):
        col, row = divmod(i, 13)
        x, y = M + col * 135, 50 + row * 10.2
        pg.add(T.text(f"{i + 3:02d}", "geist-mono", 3.6, x, y, SKY, "start", 600))
        pg.add(T.text(it, "montserrat", 4.4, x + 12, y, NAVY, "start", 700))
        pg.add(f'<rect x="{x}" y="{y + 3.6}" width="120" height="0.2" fill="{MIST}"/>')
    return pg


def p_brand():
    pg = Page("The brand", "01 · The brand", dark=True)
    pg.head("Parcel Fly is a Dhaka-focused courier and logistics company for online sellers, food businesses and growing "
            "local brands. We pick up from the merchant's store and deliver to the customer's door, with tracking, "
            "cash on delivery and careful handling built in.")
    y = text_block(pg, M, 74, 120, [
        ("Promise", "Fast, careful and trackable delivery. Always, Everywhere. সবসময়, সবখানে।"),
        ("Personality", "Fast but never careless. Dependable and local. Modern, clear and friendly. We speak like a "
                        "helpful dispatcher: short sentences, real numbers, no hype."),
        ("Voice", "Say what happens next (\"Your parcel is out for delivery\"). Prefer plain words to jargon. Write "
                  "Bangla and English with equal care, never machine-translated."),
    ])
    frag, _ = LY.place_logo("symbol", "ondark", 170, 70, w=110)
    pg.add(frag)
    pg.add(T.text("A parcel given wings.", "montserrat", 7.4, 170 + 55, 140, WHITE, "middle", 800))
    frag2, _ = LY.para("Three feathers carry the parcel forward; its two facets form the arrow that points to the "
                       "doorstep. The colours climb from deep navy to bright mint, from pickup to delivery.",
                       170, 150, 3.2, CYAN, max_width=112, weight=600)
    pg.add(frag2)
    return pg


def p_logo():
    pg = Page("The logo", "02 · The logo")
    pg.head("The stacked logo is the primary signature. It is final and in production: always use the master files, "
            "never redraw, retype or recolour it.")
    e, bb = embed(ROOT / "logo/primary-stacked/parcelfly-stacked-color.svg", 20, 60, w=120)
    pg.add(e)
    text_block(pg, 160, 66, 118, [
        ("Symbol", "A diamond parcel with two facets that make an arrow, carried by three feathers. Six flat colours, "
                   "no gradients or shadows. (The drop shadow on the old production PNG is retired.)"),
        ("Wordmark", "Parcel Fly set in Nasalization with -0.05 em tracking, outlined as fixed artwork. Never type the "
                     "wordmark: use the files."),
        ("Bangla", "পার্সেল ফ্লাই is set in Mina Bold, sized so its stems match the English wordmark."),
        ("Masters", "logo/ holds SVG (screens), PDF and EPS (print) and PNG (office), in every colour version."),
    ])
    return pg


def p_construction():
    pg = Page("Construction", "03 · Construction")
    pg.head("Measured from the production artwork and rebuilt on exact geometry. Units are logo units; every white "
            "channel is the same 26 units, every edge runs at 0 or 45 degrees.")
    k = 0.21
    ox, oy = 22, 74
    cw = S.colourway("color")
    paths = S.part_paths()
    g = "".join(f'<path fill="{cw[p]}" fill-opacity="0.35" d="{paths[p]}"/>' for p in S.PARTS)
    guide = f'stroke="{NAVY}" stroke-width="{0.25 / k:.3f}" fill="none"'
    lines = [
        f'<path {guide} stroke-dasharray="6 4" d="M{fmt(S.CX)} -40V{fmt(S.HEIGHT + 40)}M-30 {fmt(S.CY)}H{fmt(S.WIDTH + 30)}"/>',
        f'<path {guide} d="{LY.diamond_path(S.CX, S.CY, S.D)}"/>',
        f'<path {guide} stroke-dasharray="3 3" d="M0 0L{fmt(2 * S.STEP + 60)} {fmt(2 * S.STEP + 60)}"/>',
    ]
    pg.add(f'<g transform="translate({ox} {oy}) scale({k})">{g}{"".join(lines)}</g>')

    def at(x, y):
        return ox + x * k, oy + y * k

    def callout(x, y, label, anchor="middle"):
        px_, py_ = at(x, y)
        pg.add(f'<circle cx="{fmt(px_)}" cy="{fmt(py_)}" r="0.7" fill="{RED}"/>')
        pg.add(T.text(label, "montserrat", 2.6, px_ + (2 if anchor == "start" else 0), py_ - 1.6, RED, anchor, 800))

    callout((S.CX + S.CX + S.D) / 2 + 10, (S.CY - S.D + S.CY) / 2 - 10, "256")
    callout(S.C1 - S.GX / 2 + 4, 40, "26")
    callout(S.STEP + 30, S.STEP + 30, "45°", "start")
    callout(S.C1 + S.FACET_W / 2, -6, "118")
    callout(-4, S.FEATHER_H / 2 + 6, "107.35", "end" if False else "middle")
    notes = [
        ("Parcel", "Square of side 256 turned 45 degrees (half-diagonal 181.02). The horizontal axis is the mirror line."),
        ("Channel", "26 units between every pair of shapes, measured at right angles."),
        ("Feathers", "Three bars 107.35 tall with 26 gaps; tips step down a 45 degree line; tails are quarter-ellipses 118 x 107.35."),
        ("Facets", "Parallelograms 118 wide with 45 degree sides, mirrored about the axis: the arrow head."),
        ("Overall", "835.79 x 374.04 (2.23 : 1). The wordmark cap height is 168; the stacked lockup keeps the production spacing."),
    ]
    text_block(pg, 210, 62, 70, notes, size=2.9, gap=4.2)
    return pg


def p_family():
    pg = Page("Logo family", "04 · Logo family")
    pg.head()
    cells = [("logo/primary-stacked/parcelfly-stacked-color.svg", "Stacked (primary)", "Square and portrait spaces, social, packaging"),
             ("logo/horizontal/parcelfly-horizontal-color.svg", "Horizontal", "Website and app headers, letterheads, signage"),
             ("logo/symbol/parcelfly-symbol-color.svg", "Symbol", "Avatars, icons, small spaces, patterns"),
             ("logo/wordmark/parcelfly-wordmark-color.svg", "Wordmark", "Where the symbol is already present")]
    for i, (f, name, use) in enumerate(cells):
        col, row = i % 2, i // 2
        x, y = M + col * 136, 44 + row * 72
        pg.add(f'<rect x="{x}" y="{y}" width="130" height="60" rx="3" fill="{CLOUD}"/>')
        e, _ = embed(ROOT / f, x + 15, y + 8, w=100, h=34)
        pg.add(e)
        pg.add(T.text(name, "montserrat", 3.6, x + 6, y + 50, NAVY, "start", 800))
        pg.add(T.text(use, "montserrat", 2.6, x + 6, y + 55, SLATE, "start", 500))
    return pg


def p_bangla():
    pg = Page("Bangla and tagline lockups", "05 · Lockups")
    pg.head()
    cells = [("logo/bangla/parcelfly-bn-stacked-color.svg", "Bangla stacked"),
             ("logo/bangla/parcelfly-bn-horizontal-color.svg", "Bangla horizontal"),
             ("logo/tagline/parcelfly-stacked-tagline-en-color.svg", "Stacked + tagline"),
             ("logo/tagline/parcelfly-horizontal-tagline-en-color.svg", "Horizontal + tagline"),
             ("logo/tagline/parcelfly-stacked-tagline-bn-color.svg", "Stacked + Bangla tagline"),
             ("logo/bangla/parcelfly-bn-horizontal-tagline-color.svg", "Bangla horizontal + tagline")]
    for i, (f, name) in enumerate(cells):
        col, row = i % 3, i // 3
        x, y = M + col * 90, 42 + row * 66
        pg.add(f'<rect x="{x}" y="{y}" width="85" height="58" rx="3" fill="{CLOUD}"/>')
        e, _ = embed(ROOT / f, x + 8, y + 7, w=69, h=36)
        pg.add(e)
        pg.add(T.text(name, "montserrat", 3.0, x + 5, y + 53, NAVY, "start", 800))
    pg.add(T.text("Taglines: \"Always, Everywhere\" in Montserrat SemiBold caps, +0.2 em; \"সবসময়, সবখানে\" in Mina Bold. "
                  "Drop the tagline below 160 px / 40 mm wide.", "noto-bengali", 2.7, M, 182, SLATE, "start", 500))
    return pg


def p_clearspace():
    pg = Page("Clear space and size", "06 · Clear space")
    pg.head("Keep clear space of X on every side, where X is the height of one feather. It scales with the logo. "
            "Nothing else (text, edges, other logos) enters this zone.")
    frag, bb = L.stacked("color")
    k = 0.088
    X = S.FEATHER_H * k
    w, h = (bb[2] - bb[0]) * k, (bb[3] - bb[1]) * k
    x0, y0 = 34, 68
    pg.add(f'<rect x="{fmt(x0 - X)}" y="{fmt(y0 - X)}" width="{fmt(w + 2 * X)}" height="{fmt(h + 2 * X)}" fill="{CLOUD}" '
           f'stroke="{SKY}" stroke-width="0.3" stroke-dasharray="1.5 1"/>')
    pg.add(f'<g transform="translate({fmt(x0 - bb[0] * k)} {fmt(y0 - bb[1] * k)}) scale({k})">{frag}</g>')
    for (cx, cy) in [(x0 - X / 2, y0 + h / 2), (x0 + w + X / 2, y0 + h / 2), (x0 + w / 2, y0 - X / 2), (x0 + w / 2, y0 + h + X / 2)]:
        pg.add(T.text("X", "montserrat", 3.2, cx, cy + 1.1, SKY, "middle", 800))
    rows = [("Symbol", "24 px", "8 mm", "Use the app-icon crop below 32 px (favicons)."),
            ("Stacked", "72 px wide", "20 mm wide", "Tagline version: 160 px / 40 mm."),
            ("Horizontal", "120 px wide", "30 mm wide", "Tagline version: 200 px / 50 mm."),
            ("Wordmark", "80 px wide", "22 mm wide", "")]
    y = 70
    tx = 188
    pg.add(T.text("MINIMUM SIZE", "montserrat", 2.6, tx, y - 8, SKY, "start", 800, tracking=0.16))
    for name, scr, prn, note in rows:
        pg.add(T.text(name, "montserrat", 3.4, tx, y, NAVY, "start", 800))
        pg.add(T.text(f"Screen {scr}  ·  Print {prn}", "montserrat", 2.9, tx, y + 5, INK, "start", 600))
        if note:
            pg.add(T.text(note, "montserrat", 2.5, tx, y + 9.6, SLATE, "start", 500))
        y += 17
    return pg


def p_colourways():
    pg = Page("Colour versions", "07 · Colour versions")
    pg.head("Full colour on white is the default. On dark backgrounds the feathers turn white and the parcel keeps its "
            "colours. Use one-colour versions where colour printing is not possible.")
    cells = [("color", WHITE, "Full colour"), ("ondark", NAVY, "On dark"), ("navy", WHITE, "One colour navy"),
             ("white", SKY, "White on brand colour"), ("black", WHITE, "Black"), ("grey", WHITE, "Greyscale")]
    for i, (way, bg, name) in enumerate(cells):
        col, row = i % 3, i // 3
        x, y = M + col * 90, 52 + row * 64
        pg.add(f'<rect x="{x}" y="{y}" width="85" height="56" rx="3" fill="{bg}" stroke="{MIST}" stroke-width="0.3"/>')
        e, _ = embed(ROOT / f"logo/horizontal/parcelfly-horizontal-{way}.svg", x + 8, y + 14, w=69, h=18)
        pg.add(e)
        pg.add(T.text(name, "montserrat", 2.9, x + 5, y + 51, WHITE if bg in (NAVY, SKY) else NAVY, "start", 800))
    return pg


def p_misuse():
    pg = Page("Logo misuse", "08 · Misuse")
    pg.head("The logo only works when it is reproduced exactly. These are the most common mistakes.")
    frag, bb = L.horizontal("color")
    k = 60 / (bb[2] - bb[0])
    base = lambda t: f'<g transform="{t}"><g transform="translate({fmt(-bb[0] * k)} {fmt(-bb[1] * k)}) scale({k:.5f})">{frag}</g></g>'
    lh = (bb[3] - bb[1]) * k
    items = [
        ("Do not stretch or squash", lambda x, y: base(f"translate({x + 1} {y + 2}) scale(0.95 1.45)")),
        ("Do not rotate", lambda x, y: base(f"translate({x + 6} {y + 9}) rotate(-12) scale(0.85)")),
        ("Do not recolour", lambda x, y: f'<g transform="translate({x} {y})">' + LY.place_logo("horizontal", "#E0303A", 0, 0, w=60)[0] + "</g>"),
        ("Do not add shadows or effects", lambda x, y: f'<g transform="translate({x + 1.2} {y + 1.2})" opacity="0.35">' + LY.place_logo("horizontal", "black", 0, 0, w=60)[0] + "</g>" + base(f"translate({x} {y})")),
        ("Do not rearrange the parts", lambda x, y: f'<g transform="translate({x} {y})">' + LY.place_logo("wordmark", NAVY, 0, 0, w=40)[0]
         + f'<g transform="translate(44 -2)">' + LY.place_logo("symbol", "color", 0, 0, w=18)[0] + "</g></g>"),
        ("Do not place on busy backgrounds", lambda x, y: f'<rect x="{x - 3}" y="{y - 4}" width="66" height="{lh + 8}" fill="{SKY}"/>'
         + "".join(f'<circle cx="{x - 3 + i * 6}" cy="{y + (i % 3) * 4}" r="3" fill="{MINT}"/>' for i in range(12)) + base(f"translate({x} {y})")),
        ("Do not outline", lambda x, y: f'<g transform="translate({x} {y})" fill="none">' + LY.place_logo("horizontal", "white", 0, 0, w=60)[0].replace('fill="#FFFFFF"', f'fill="none" stroke="{NAVY}" stroke-width="7"') + "</g>"),
        ("Do not retype the wordmark", lambda x, y: f'<g transform="translate({x} {y})">' + LY.place_logo("symbol", "color", 0, 0, w=22)[0]
         + T.text("Parcel Fly", "montserrat", 6.5, 25, 8, NAVY, "start", 700) + "</g>"),
    ]
    for i, (lab, draw) in enumerate(items):
        col, row = i % 4, i // 4
        x, y = M + col * 67, 52 + row * 66
        pg.add(f'<rect x="{x}" y="{y}" width="63" height="56" rx="3" fill="{CLOUD}"/>')
        pg.add(f'<svg x="{x}" y="{y}" width="63" height="40" viewBox="{x} {y} 63 40">{draw(x + 1.5, y + 14)}</svg>')
        pg.add(f'<path d="M{x + 4} {y + 44}l3 3m0-3l-3 3" stroke="{RED}" stroke-width="0.7" stroke-linecap="round"/>')
        frag2, _ = LY.para(lab, x + 9, y + 47, 2.6, NAVY, max_width=50, weight=700)
        pg.add(frag2)
    return pg


def p_colour():
    pg = Page("Colour palette", "09 · Colour")
    pg.head()
    keys = list(PALETTE)
    for i, k in enumerate(keys):
        v = PALETTE[k]
        x = M + i * 44.5
        pg.d.rect(x, 36, 41, 62, v["hex"], rx=2.5)
        light = k in ("cyan", "aqua", "mint")
        tc = NAVY if light else WHITE
        pg.add(T.text(v["name"], "montserrat", 3.3, x + 3, 82, tc, "start", 800))
        pg.add(T.text(v["hex"], "geist-mono", 2.7, x + 3, 87, tc, "start", 600))
        r, g, b = (int(v["hex"][j:j + 2], 16) for j in (1, 3, 5))
        c = v["cmyk"]
        for j, line in enumerate([f"RGB {r} {g} {b}", f"CMYK {c[0]} {c[1]} {c[2]} {c[3]}", f"Pantone {v['pantone']}"]):
            pg.add(T.text(line, "geist-mono", 2.3, x + 3, 104 + j * 4.2, INK, "start", 500))
    allc = list(NEUTRALS.items()) + list(STATUS.items())
    for i, (k, v) in enumerate(allc):
        x = M + i * 33.4
        pg.d.rect(x, 124, 31, 22, v["hex"], rx=2, extra=f' stroke="{MIST}" stroke-width="0.3"')
        pg.add(T.text(v["name"], "montserrat", 2.5, x, 151, NAVY, "start", 800))
        pg.add(T.text(v["hex"], "geist-mono", 2.3, x, 155, SLATE, "start", 500))
    pg.add(T.text("Neutrals (left) carry text and surfaces. Status colours (right) are only for states: delivered, pending, "
                  "fragile. Proportion: navy and white lead (about 85 %), the bright logo colours accent (about 10 %).",
                  "montserrat", 2.6, M, 166, SLATE, "start", 500))
    gid = "flight-g"
    pg.d.defs_add(LY.flight_gradient(gid))
    pg.d.rect(M, 172, PW - 2 * M, 8, f"url(#{gid})", rx=2)
    pg.add(T.text("Flight gradient: for backgrounds and graphics only, never inside the logo.", "montserrat", 2.6, M, 185,
                  SLATE, "start", 600))
    return pg


def p_type():
    pg = Page("Typography", "10 · Typography")
    pg.head()
    pg.add(T.text("Montserrat", "montserrat", 15, M, 52, NAVY, "start", 800))
    pg.add(T.text("Headlines ExtraBold, body Medium, labels SemiBold in tracked caps. English everywhere.", "montserrat",
                  3, M, 59, SLATE, "start", 500))
    hs = T.fit_size("Delivery that keeps up with your business.", "montserrat", 132, 7.4, 800, tracking=-0.01)
    pg.add(T.text("Delivery that keeps up with your business.", "montserrat", hs, M, 74, NAVY, "start", 800, tracking=-0.01))
    frag, _ = LY.para("Fast, careful and trackable parcel delivery across Dhaka for online sellers, food businesses and "
                      "growing local brands.", M, 82, 3.4, INK, max_width=125)
    pg.add(frag)
    pg.add(LY.label("Label · Always, Everywhere", M, 98, 2.8, SKY))
    b0, b1, b2, b3 = T.ink_bounds("সবসময়, সবখানে", "mina-bold", 14)
    pg.add(T.text("সবসময়, সবখানে", "mina-bold", 14, 160, 52 - 0, NAVY))
    pg.add(T.text("Mina Bold: Bangla display, the Bangla wordmark and taglines.", "montserrat", 3, 160, 59, SLATE, "start", 500))
    bfrag, _ = LY.para("দ্রুত, যত্নশীল ও ট্র্যাকযোগ্য পার্সেল ডেলিভারি, পুরো ঢাকা জুড়ে।", 160, 72, 4.4, NAVY, max_width=120,
                       weight=700, key="noto-bengali", leading=1.5)
    pg.add(bfrag)
    frag, _ = LY.para("Noto Sans Bengali: Bangla body text and UI. Never stretch Bangla with letter-spacing: the headline "
                      "(matra) must stay connected.", 160, 88, 3.0, SLATE, max_width=120)
    pg.add(frag)
    pg.add(T.text("PF 2511 2100 01", "geist-mono", 6, M, 122, NAVY, "start", 700))
    pg.add(T.text("Geist Mono: tracking numbers, waybills, codes and numbers in tables.", "montserrat", 3, M, 129, SLATE, "start", 500))
    rows = [("Nasalization", "Logo wordmark only, outlined fixed artwork. Typodermic desktop licence: never install it on "
                             "servers, ship it in apps or websites, or use it for text."),
            ("Fonts folder", "source/fonts holds the open-licence fonts (SIL OFL) with their licences: Montserrat, Mina, "
                             "Noto Sans Bengali, Geist Mono. Install them before editing any template."),
            ("Web stack", "Montserrat, \"Noto Sans Bengali\", system-ui, sans-serif.")]
    text_block(pg, 160, 116, 120, rows, size=2.9, gap=4)
    return pg


def p_devices():
    pg = Page("Graphic devices and patterns", "11 · Devices")
    pg.head("Everything is cut from the symbol: the feathers become speed lines, the facets an arrow, the parcel a frame. "
            "Keep the 45 degree angles and the channel proportions.")
    pg.d.rect(M, 64, 80, 52, NAVY, rx=3)
    pg.add(LY.speed_lines(M + 6, 74, 32, 66, (SKY, COBALT, CYAN)))
    pg.add(T.text("Speed lines", "montserrat", 3.2, M, 122, NAVY, "start", 800))
    pg.d.rect(M + 86, 64, 80, 52, CLOUD, rx=3)
    pg.add(SC.chevron_trail(M + 98, 74, 32, 3))
    pg.add(T.text("Arrow (facets)", "montserrat", 3.2, M + 86, 122, NAVY, "start", 800))
    pg.d.rect(M + 172, 64, 93, 52, SKY, rx=3)
    pg.add(f'<path d="{LY.diamond_path(M + 218.5, 90, 22, 2)}" fill="{WHITE}"/>')
    pg.add(P.icon("parcel", M + 210, 81.5, 17, NAVY, 3.4))
    pg.add(T.text("Parcel frame", "montserrat", 3.2, M + 172, 122, NAVY, "start", 800))
    for i, f in enumerate(["patterns/lattice/parcelfly-pattern-lattice-mist-on-cloud-1920x1080.svg",
                           "patterns/monogram/parcelfly-pattern-monogram-cobalt-on-navy-1920x1080.svg",
                           "patterns/chevrons/parcelfly-pattern-chevrons-cobalt-on-navy-1920x1080.svg",
                           "patterns/wings/parcelfly-pattern-wings-mist-on-white-1920x1080.svg"]):
        e, _ = embed(ROOT / f, M + i * 66.5, 132, w=63, h=35.4, align="xMidYMid slice")
        pg.add(f'<g>{e}</g>')
    pg.add(T.text("Patterns: lattice, monogram, chevrons, wings (patterns/ has tiles and 1920 x 1080 files).", "montserrat",
                  2.7, M, 174, SLATE, "start", 500))
    return pg


def p_hubs():
    pg = Page("Hub network and maps", "12 · Hub network")
    pg.head()
    e, bb = embed(ROOT / "maps/hub-network/parcelfly-hub-map-square-dark.svg", M, 34, w=136, h=136)
    pg.add(e)
    x = M + 146
    pg.add(LY.label("Five hubs", x, 40, 2.6, SKY))
    for i, h_ in enumerate(MP.hubs()):
        y = 49 + i * 9.2
        pg.add(LY.parcel(x + 2.2, y - 1.3, 2.1, NAVY))
        pg.add(LY.parcel(x + 2.2, y - 1.3, 0.9, CYAN))
        pg.add(T.text(f"{h_['name']} Hub", "montserrat", 3.4, x + 6.5, y, NAVY, "start", 800))
        pg.add(T.text(f"{h_['name_bn']} হাব", "mina-bold", 3.0, x + 6.5, y + 3.9, SKY))
    text_block(pg, x, 103, 118, [
        ("Real geography", "Rivers, water and roads come from OpenStreetMap; the Bangladesh outline and rivers from "
                           "Natural Earth. Rebuild maps with source/build/build_maps.py, never redraw them by hand."),
        ("Credit", "Keep \"© OpenStreetMap contributors\" visible on every map (the files include it)."),
        ("Pins", "Hub pins mark the neighbourhood, not the street address. Update source/geo/hubs.json when the "
                 "exact addresses are confirmed."),
        ("Styles", "Dark map on navy surfaces and social media; light map on white, in print and on the website."),
    ], size=2.75, gap=3.4)
    e2, bb2 = embed(ROOT / "maps/hub-network/parcelfly-hub-map-square-light.svg", PW - M - 40, 150, w=19, h=19)
    pg.add(e2 + border(bb2))
    e3, bb3 = embed(ROOT / "maps/bangladesh/parcelfly-bangladesh-map-dark.svg", PW - M - 18, 150, w=18, h=22.5)
    pg.add(e3)
    return pg


def p_icons():
    pg = Page("Pictograms", "13 · Pictograms")
    pg.head("48-unit grid, 3.5 stroke, round caps and joins, 45 degree geometry. One colour: navy on light, white on dark.")
    names = list(P.ICONS)
    cols = 13
    for i, n in enumerate(names):
        col, row = i % cols, i // cols
        x, y = M + col * 20.5, 62 + row * 30
        pg.add(P.icon(n, x + 2, y, 14, NAVY))
        frag, _ = LY.para(P.LABELS[n], x + 9, y + 20, 2.1, SLATE, max_width=19, weight=600, anchor="middle")
        pg.add(frag)
    pg.d.rect(M, 128, PW - 2 * M, 40, NAVY, rx=3)
    for i, n in enumerate(["track", "pricing", "coverage", "merchant", "rider", "offers", "reviews", "faq", "phone", "info"]):
        cx = M + 13 + i * 26.3
        pg.add(f'<circle cx="{cx}" cy="148" r="10" fill="none" stroke="{CYAN}" stroke-width="0.6"/>')
        pg.add(P.icon(n, cx - 6, 142, 12, WHITE))
    return pg


def p_apps():
    pg = Page("Apps and sub-brands", "14 · Apps")
    pg.head("One master brand. Each app keeps the symbol and changes only the tile colour; the descriptor names the app.")
    apps = [("parcelfly", "Parcel Fly / Merchant", "Navy tile"), ("rider", "Rider", "White tile"), ("hub", "Hub", "Parcel Cyan tile"),
            ("admin", "Admin", "Ink tile, amber parcel")]
    for i, (a, name, note) in enumerate(apps):
        x = M + i * 66.5
        e, _ = embed(ROOT / f"icons/app/{a}/{a}-icon-rounded.svg", x + 14, 56, w=34)
        pg.add(e)
        pg.add(f'<rect x="{x + 14}" y="56" width="34" height="34" rx="{34 * 0.2237:.2f}" fill="none" stroke="{MIST}" stroke-width="0.35"/>')
        pg.add(T.text(name, "montserrat", 3.3, x + 31, 98, NAVY, "middle", 800))
        pg.add(T.text(note, "montserrat", 2.5, x + 31, 103, SLATE, "middle", 500))
    for i, sb in enumerate(["merchant", "rider", "hub", "admin"]):
        x = M + (i % 2) * 133
        y = 116 + (i // 2) * 30
        pg.add(f'<rect x="{x}" y="{y}" width="128" height="25" rx="3" fill="{CLOUD}"/>')
        e, _ = embed(ROOT / f"logo/sub-brands/{sb}/parcelfly-{sb}-inline-color.svg", x + 8, y + 5, w=112, h=15)
        pg.add(e)
    pg.add(T.text("App icons use the flight crop: the parcel and arrow fill the tile, the wings run off the left edge. "
                  "icons/app/<app> has iOS, Android (adaptive, monochrome, legacy), Expo and web/PWA sets.",
                  "montserrat", 2.6, M, 182, SLATE, "start", 500))
    return pg


def grid_embed(pg, files, x0, y0, cols, cw, ch, gap=4, align="xMidYMid", labels=None, borders=True):
    for i, f in enumerate(files):
        col, row = i % cols, i // cols
        x, y = x0 + col * (cw + gap), y0 + row * (ch + gap + (5 if labels else 0))
        e, bb = embed(ROOT / f, x, y, w=cw, h=ch, align=align)
        pg.add(e)
        if borders:
            pg.add(border(bb))
        if labels:
            pg.add(T.text(labels[i], "montserrat", 2.4, x, y + ch + 3.6, SLATE, "start", 600))


def p_social():
    pg = Page("Social media", "15 · Social")
    pg.head()
    grid_embed(pg, ["social/facebook/parcelfly-cover-signature.svg", "social/facebook/parcelfly-cover-bangla.svg",
                    "social/facebook/parcelfly-cover-merchant.svg", "social/facebook/parcelfly-cover-coverage.svg"],
               M, 36, 2, 118, 45, labels=["Signature", "Bangla", "Merchant", "Coverage"])
    grid_embed(pg, ["social/posts/square/parcelfly-post-service-01.svg", "social/posts/square/parcelfly-post-tagline-bn.svg",
                    "social/posts/square/parcelfly-post-how-it-works.svg"], 262 - 0, 36, 1, 23, 23)
    pg.add(T.text("Covers adapt to every platform's safe zone (Facebook, LinkedIn, X, YouTube, Google Business, email, "
                  "Open Graph). Profiles are circle-safe; posts come square, portrait and landscape; stories keep "
                  "clear of the app UI.", "montserrat", 2.6, M, 150, SLATE, "start", 500))
    for i, f in enumerate(["social/facebook/parcelfly-profile-navy.svg", "social/facebook/parcelfly-profile-white.svg",
                           "social/facebook/parcelfly-profile-gradient.svg", "social/facebook/parcelfly-profile-bold.svg"]):
        pg.add(f'<clipPath id="pc{i}"><circle cx="{M + 12 + i * 28}" cy="{170}" r="12"/></clipPath>')
        e, _ = embed(ROOT / f, M + i * 28, 158, w=24, h=24)
        pg.add(f'<g clip-path="url(#pc{i})">{e}</g>')
        pg.add(f'<circle cx="{M + 12 + i * 28}" cy="170" r="12" fill="none" stroke="{MIST}" stroke-width="0.35"/>')
    return pg


def p_stationery():
    pg = Page("Stationery", "16 · Stationery")
    pg.head()
    grid_embed(pg, ["stationery/business-card/parcelfly-business-card-a-front-navy.svg",
                    "stationery/business-card/parcelfly-business-card-a-back-white.svg",
                    "stationery/business-card/parcelfly-business-card-b-front-white.svg",
                    "stationery/business-card/parcelfly-business-card-b-back-navy.svg"], M, 36, 2, 70, 42)
    e, _ = embed(ROOT / "stationery/letterhead/parcelfly-letterhead-a4.svg", 168, 36, h=110)
    pg.add(f'<rect x="168" y="36" width="{fmt(110 * 210 / 297)}" height="110" fill="none" stroke="{MIST}" stroke-width="0.3"/>' + e)
    grid_embed(pg, ["stationery/id-card/parcelfly-id-card-rider-front.svg", "stationery/id-card/parcelfly-id-card-back.svg",
                    "stationery/shipping-label/parcelfly-shipping-label-4x6.svg"], 252, 36, 1, 24, 36, gap=2)
    frag, _ = LY.para("Business cards 89 x 51 mm with 3 mm bleed. Letterhead A4 (PDF and Word). Envelope DL, compliment "
                      "slip, ID cards (CR80) and a 4 x 6 in thermal shipping label.", M, 136, 2.6, SLATE, max_width=140)
    pg.add(frag)
    return pg


def p_marks():
    pg = Page("Stamps and seals", "17 · Stamps and seals")
    pg.head()
    grid_embed(pg, ["stamps/rubber-stamp-vector/parcelfly-stamp-delivered-navy.svg",
                    "stamps/rubber-stamp-vector/parcelfly-stamp-returned-black.svg",
                    "stamps/rubber-stamp-vector/parcelfly-stamp-cash-on-delivery-navy.svg",
                    "stamps/rubber-stamp-vector/parcelfly-company-seal-navy.svg"], M, 38, 4, 60, 30)
    grid_embed(pg, ["seals/color/parcelfly-seal-official-partner-color.svg", "seals/light/parcelfly-seal-verified-merchant-light.svg",
                    "seals/color/parcelfly-seal-heritage-color.svg", "seals/color/parcelfly-seal-bn-official-partner-color.svg",
                    "seals/light/parcelfly-seal-cash-on-delivery-light.svg"], M, 92, 5, 48, 48)
    pg.add(T.text("Rubber stamps are one colour (send the black PDF/EPS to the stamp maker); every hub has its own round "
                  "stamp. Inked PNGs are for digital documents. Seals are for merchant pages, receipts and packaging.", "montserrat", 2.6, M, 176, SLATE, "start", 500))
    return pg


def p_stickers():
    pg = Page("Stickers and packaging", "18 · Stickers and packaging")
    pg.head()
    grid_embed(pg, ["stickers/die-cut/parcelfly-sticker-symbol-diecut.svg", "stickers/round/parcelfly-sticker-round-logo.svg",
                    "stickers/handling/parcelfly-sticker-fragile.svg", "stickers/handling/parcelfly-sticker-keep-frozen.svg",
                    "stickers/round/parcelfly-sticker-thank-you.svg", "stickers/brand/parcelfly-sticker-scan-to-track.svg"],
               M, 36, 6, 40, 34)
    grid_embed(pg, ["packaging/tape/parcelfly-tape-48mm-repeat-navy.svg", "packaging/tape/parcelfly-tape-48mm-repeat-white.svg"],
               M, 80, 1, 130, 21, gap=3)
    grid_embed(pg, ["packaging/mailer/parcelfly-poly-mailer-front.svg", "packaging/delivery-box/parcelfly-delivery-box-decal-square-400x400.svg",
                    "packaging/box/parcelfly-box-top-panel.svg"], 152, 80, 3, 40, 52)
    pg.add(T.text("Every sticker has artwork with 1 mm bleed and a separate magenta cut line (CutContour). "
                  "stickers/sheet has ready-to-print A4 sheets.", "montserrat", 2.6, M, 150, SLATE, "start", 500))
    return pg


def raster(path, x, y, w, h=None, quality=82):
    """Embed a raster (JPG/PNG) scaled to width w (mm)."""
    import base64
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    flat = Image.new("RGBA", im.size, (255, 255, 255, 255))     # transparent corners (cards) sit on the page white
    flat.alpha_composite(im)
    im = flat.convert("RGB")
    if h is None:
        h = w * im.height / im.width
    target = int(w / 25.4 * 220)
    if im.width > target:
        im = im.resize((target, int(target * im.height / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality)
    uri = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    return f'<image x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" xlink:href="{uri}" preserveAspectRatio="xMidYMid slice"/>', h


def p_bags():
    pg = Page("Bags and carry bags", "19 · Bags")
    pg.head()
    img, h = raster(ROOT / "mockups/bags/parcelfly-bag-family.jpg", M, 34, PW - 2 * M, 84)
    pg.add(img)
    for i, f in enumerate(["parcelfly-paper-bags.jpg", "parcelfly-carry-bags.jpg", "parcelfly-rider-backpack.jpg"]):
        im, _ = raster(ROOT / "mockups/bags" / f, M + i * 89.5, 122, 86, 53.75)
        pg.add(im)
    text_block(pg, M, 186, 265, [
        ("Suggested production", "Paper bags 320 x 120 x 410 mm and 200 x 80 x 250 mm: 157 gsm art paper with matt lamination "
                                 "and twisted paper handles; kraft 120 gsm printed one colour navy. Totes 380 x 420 mm, 10 oz "
                                 "cotton canvas, screen print. Non-woven carry bags 80 gsm PP, D-cut or loop handles. Rider "
                                 "backpack 420 x 330 x 420 mm, 600D polyester, insulated, reflective strip."),
    ], size=2.5, gap=2)
    return pg


def p_apparel():
    pg = Page("Apparel and signage", "20 · Apparel and signage")
    pg.head()
    pg.d.rect(M, 36, 60, 70, NAVY, rx=3)
    e, _ = embed(ROOT / "apparel/tshirt/parcelfly-tshirt-back-rider-ondark.svg", M + 5, 40, w=50, h=62)
    pg.add(e)
    grid_embed(pg, ["signage/signboard/parcelfly-signboard-mirpur-hub.svg"], M + 66, 36, 1, 132, 44)
    grid_embed(pg, ["signage/roll-up/parcelfly-rollup-850x2000.svg", "signage/flyer/parcelfly-flyer-a5-front.svg",
                    "signage/flyer/parcelfly-flyer-a5-back.svg"], 220, 36, 3, 18, 42, gap=2)
    pg.add(T.text("Signboards 2400 x 800 mm (generic and one for each of the five hubs), roll-up 850 x 2000 mm, A5 flyer, "
                  "T-shirt chest and back prints, cap embroidery.", "montserrat", 2.6, M, 118, SLATE, "start", 500))
    return pg


def p_merch():
    pg = Page("Merchandise", "21 · Merchandise")
    pg.head()
    img, h = raster(ROOT / "mockups/merch/parcelfly-merch-family.jpg", M, 34, PW - 2 * M, 70)
    pg.add(img)
    for i, f in enumerate(["parcelfly-mugs.jpg", "parcelfly-paper-cups.jpg", "parcelfly-desk-flatlay.jpg"]):
        im, _ = raster(ROOT / "mockups/merch" / f, M + i * 89.5, 108, 86, 53.75)
        pg.add(im)
    text_block(pg, M, 172, 265, [
        ("Print files (merch/print/)", "Mugs: 11 oz sublimation wraps 216 x 89 mm; each half is designed for the side that "
                                       "shows with the handle left or right. Paper cups: 12 oz wraps plus the printable fan "
                                       "at 300 dpi and its die line. Diary: A5 hardcover case wraps (15 mm turn-in) and the "
                                       "ruled page. Pens: 50 x 8 mm barrel prints. Laptop stickers: A5 kiss-cut sheet."),
    ], size=2.5, gap=2)
    return pg


def p_mockups():
    pg = Page("Mockups", "22 · Mockups")
    pg.head("Every physical item, rendered from its real print file.")
    shots = ["mockups/stationery/parcelfly-stationery-flatlay.jpg", "mockups/packaging/parcelfly-packaging-family.jpg",
             "mockups/signage/parcelfly-storefront-mirpur-hub.jpg", "mockups/apparel/parcelfly-tshirt-front-back.jpg",
             "mockups/stationery/parcelfly-id-cards-lanyards.jpg", "mockups/apparel/parcelfly-caps.jpg"]
    for i, f in enumerate(shots):
        col, row = i % 3, i // 3
        im, _ = raster(ROOT / f, M + col * 89.5, 48 + row * 59, 86, 55)
        pg.add(im)
    pg.add(T.text("mockups/: bags, merch, stationery, packaging, stamps, stickers, apparel, signage. JPG scenes with "
                  "half-size previews; cutouts/ holds transparent product renders for your own layouts.",
                  "montserrat", 2.6, M, 172, SLATE, "start", 500))
    return pg


def p_digital():
    pg = Page("Web and wallpapers", "23 · Web and wallpapers")
    pg.head()
    im, _ = raster(ROOT / "web/banners/parcelfly-banner-hub-network-desktop-1920x640.jpg", M, 34, 130, 43.3)
    pg.add(im)
    im, _ = raster(ROOT / "web/cards/services/parcelfly-card-service-01-light.png", M, 81, 41, 30.75)
    pg.add(im)
    im, _ = raster(ROOT / "web/cards/services/parcelfly-card-service-02-dark.png", M + 44.5, 81, 41, 30.75)
    pg.add(im)
    im, _ = raster(ROOT / "web/cards/features/parcelfly-card-feature-01-dark.png", M + 89, 81, 41, 41)
    pg.add(im)
    im, _ = raster(ROOT / "wallpapers/parcelfly-wallpapers-overview.jpg", 160, 34, PW - 160 - M)
    pg.add(im)
    text_block(pg, M, 136, 128, [
        ("Website (web/)", "Promo banners 1920 x 640 (desktop) and 1080 x 1080 (mobile) for the client panel home page, "
                           "text-free hero backgrounds for live HTML text, service and feature cards in light and dark."),
    ], size=2.5, gap=2)
    text_block(pg, 160, 136, 120, [
        ("Wallpapers (wallpapers/)", "Generic, merchant, client, rider, hub manager, staff and admin designs for phones "
                                     "(1290 x 2796, 1440 x 3200), tablets (2732 square, 2560 x 1600), laptops "
                                     "(2880 x 1800, 1920 x 1080) and desktops (4K, 21:9). Keep the map credit."),
    ], size=2.5, gap=2)
    return pg


def p_motion():
    import build_motion as BM
    from pfbrand import motion as MO
    pg = Page("Motion", "24 · Motion")
    pg.head("Nineteen animations built from one timeline engine: the sign, the wordmark and the lockups. Every one "
            "resolves exactly to the static master.")
    heroes = [("sign-build", "Sign: build"), ("sign-unfold", "Sign: unfold"), ("horizontal-build", "Horizontal: build"),
              ("stacked-drop", "Stacked: drop")]
    y = 53
    for name, label in heroes:
        A = BM.CATALOGUE[name]("color")[0]
        pg.add(T.text(label, "montserrat", 2.9, M, y + 2.5, NAVY, "start", 800))
        fr_w = 24.0
        for j, f in enumerate((0.12, 0.3, 0.5, 0.72, 1.0)):
            fit = MO.Fit(A.extent, 400, None, pad=0.22)
            fh = fr_w * fit.h / fit.w
            fh = min(fh, 21.0)
            src = MO.frame_svg(A, A.duration * f, fit, "#F3F8FC")
            src = src.replace('<svg xmlns="http://www.w3.org/2000/svg" ',
                              f'<svg x="{M + j * (fr_w + 2.2)}" y="{y + 5}" preserveAspectRatio="xMidYMid meet" ', 1)
            src = re.sub(r'width="[^"]+" height="[^"]+"', f'width="{fr_w}" height="{fh}"', src, count=1)
            src = re.sub(r'id="c(\d+)_(\d+)"', lambda m_: f'id="g{name}{j}c{m_.group(1)}_{m_.group(2)}"', src)
            src = re.sub(r'url\(#c(\d+)_(\d+)\)', lambda m_: f'url(#g{name}{j}c{m_.group(1)}_{m_.group(2)})', src)
            pg.add(src)
        y += 28
    x = 152
    yy = 53
    groups = [("sign", "Sign"), ("loader", "Loaders"), ("wordmark", "Wordmark"), ("combined", "Combined")]
    for g, gl in groups:
        pg.add(LY.label(gl, x, yy, 2.3, SKY))
        yy += 4.6
        for name, fac in BM.CATALOGUE.items():
            A = fac("color")[0]
            if A.group != g:
                continue
            pg.add(T.text(name, "geist-mono", 2.45, x, yy, NAVY, "start", 600))
            pg.add(T.text(("loop " if A.loop else "") + f"{A.duration:.1f} s", "montserrat", 2.3, x + 48, yy, SLATE,
                          "start", 600))
            pg.add(T.text(BM.USE.get(name, ""), "montserrat", 2.3, x + 62, yy, SLATE, "start", 500))
            yy += 4.15
        yy += 1.6
    text_block(pg, M, 168, 128, [
        ("Formats", "SVG (web, CSS, honours reduced motion), Lottie JSON (apps), MP4 (social, video), WebM and WebP "
                    "with transparency, GIF (email, chat). Colour and on-dark versions of each."),
    ], size=2.6, gap=2.5)
    text_block(pg, 150, 168, 130, [
        ("Rules", "Keep stings short (1 to 3 s) with ease-out motion. Never stretch, spin freely or recolour the logo in "
                  "motion; only the speed lines may scale. Use the loaders for waiting states, not as decoration."),
    ], size=2.6, gap=2.5)
    return pg


def p_files():
    pg = Page("Files and contacts", "25 · Files", dark=True)
    pg.head()
    rows = [("logo/", "Every lockup x 6 colour versions: SVG, PDF, EPS, PNG 600/1200/2400, JPG"),
            ("icons/", "App icons (iOS, Android, Expo, web/PWA) for 5 apps, favicons, pictograms"),
            ("social/", "Covers, profiles, highlights, posts, stories for 8 platforms"),
            ("stationery/", "Cards, letterhead (PDF + Word), envelope, slip, ID cards, label"),
            ("stamps/ seals/ stickers/", "Rubber stamps, inked PNGs, seals, stickers with cut lines"),
            ("packaging/ apparel/ signage/", "Tape, mailer, box, decals, T-shirts, cap, signboards, roll-up, flyer"),
            ("maps/", "Hub network maps on real geography, per-hub maps, Bangladesh map, A3 poster"),
            ("bags/ merch/", "Bag dielines and artwork; mugs, cups, diary, pens, laptop sticker sheet"),
            ("mockups/", "Realistic mockups of every physical item, with transparent cut-outs"),
            ("web/ wallpapers/", "Website banners and cards; device wallpapers for every audience"),
            ("motion/", "19 logo animations: SVG, Lottie, MP4, WebM, WebP and GIF, colour and on-dark"),
            ("colors/ patterns/ email/", "Tokens (CSS, Tailwind, JSON, ASE, GPL), patterns, email signature"),
            ("source/", "Build scripts, outlined wordmark master, open-licence fonts")]
    y = 52
    for a, b in rows:
        pg.add(T.text(a, "geist-mono", 3.2, M, y, CYAN, "start", 700))
        pg.add(T.text(b, "montserrat", 3.0, M + 80, y, WHITE, "start", 500))
        y += 9
    text_block(pg, M, 132, 160, [
        ("Which file?", "Screens and web: SVG or PNG. Office documents: PNG or JPG. Printers and sign makers: PDF or EPS, "
                        "plus the CMYK values on the colour page. Never send a screenshot."),
        ("Contact", f"{CONTACT['email']}  ·  {CONTACT['phone_intl']}  ·  {CONTACT['web']}  ·  {CONTACT['address']}"),
    ], size=3.0)
    return pg


PAGES = [p_cover, p_contents, p_brand, p_logo, p_construction, p_family, p_bangla, p_clearspace, p_colourways, p_misuse,
         p_colour, p_type, p_devices, p_hubs, p_icons, p_apps, p_social, p_stationery, p_marks, p_stickers, p_bags, p_apparel,
         p_merch, p_mockups, p_digital, p_motion, p_files]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pages_dir = OUT / "pages"
    pages_dir.mkdir(exist_ok=True)
    writer = PdfWriter()
    for i, fn in enumerate(PAGES, start=1):
        pg = fn()
        if i > 1:
            pg.foot(i)
        svg = pg.d.svg()
        pdf = cairosvg.svg2pdf(bytestring=svg.encode())
        for p in PdfReader(io.BytesIO(pdf)).pages:
            writer.add_page(p)
        render_png(svg, pages_dir / f"page-{i:02d}.png", 1600, PW, PH)
    writer.add_metadata({"/Title": "Parcel Fly brand guidelines", "/Author": "Parcel Fly", "/Subject": VERSION})
    with open(OUT / "parcelfly-brand-guidelines.pdf", "wb") as fh:
        writer.write(fh)
    print(f"guidelines: {len(PAGES)} pages")


if __name__ == "__main__":
    main()
