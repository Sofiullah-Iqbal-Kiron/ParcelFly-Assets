"""Graphic devices and layout helpers derived from the symbol (all outputs are SVG fragments)."""
import math

import segno

from . import logo as L
from . import symbol as S
from . import text as T
from .brand import AQUA, CYAN, COBALT, FLIGHT, MINT, NAVY, SKY, WHITE
from .text import fmt

R_GAP = S.GAP / S.HEIGHT            # channel / symbol height
R_FEATHER = S.FEATHER_H / S.HEIGHT  # feather height / symbol height
R_TAIL = S.TAIL_W / S.FEATHER_H     # tail width / feather height (118 / 107.35)


# ------------------------------------------------------------------ gradients

def flight_gradient(gid="flight", angle=0, stops=None):
    """Logo colours from tail to nose. angle in degrees (0 = left -> right)."""
    stops = stops or list(zip([0, 0.3, 0.58, 0.82, 1.0], FLIGHT))
    a = math.radians(angle)
    x1, y1 = 0.5 - 0.5 * math.cos(a), 0.5 - 0.5 * math.sin(a)
    x2, y2 = 0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a)
    s = "".join(f'<stop offset="{fmt(o)}" stop-color="{c}"/>' for o, c in stops)
    return f'<linearGradient id="{gid}" x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y2)}">{s}</linearGradient>'


def glow(gid, colour, opacity=0.5):
    return (f'<radialGradient id="{gid}" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="{colour}" '
            f'stop-opacity="{opacity}"/><stop offset="1" stop-color="{colour}" stop-opacity="0"/></radialGradient>')


# ------------------------------------------------------------------ devices

def feather_bar(x_tip, y_top, h, length, cut="left", fill=SKY, opacity=None):
    """One feather: quarter-ellipse tail at the left tip, 45 deg cut at the right end.
    cut: 'left' (edge leans like the top feather, x+y=c), 'right' (like the bottom feather), 'square'."""
    tw = R_TAIL * h
    x_end_top = x_tip + length
    if cut == "left":
        x_end_bot = x_end_top - h
    elif cut == "right":
        x_end_bot = x_end_top + h
    else:
        x_end_bot = x_end_top
    d = (f"M{fmt(x_tip)} {fmt(y_top)}L{fmt(x_end_top)} {fmt(y_top)}L{fmt(x_end_bot)} {fmt(y_top + h)}"
         f"L{fmt(x_tip + tw)} {fmt(y_top + h)}A{fmt(tw)} {fmt(h)} 0 0 1 {fmt(x_tip)} {fmt(y_top)}Z")
    op = f' fill-opacity="{opacity}"' if opacity is not None else ""
    return f'<path fill="{fill}"{op} d="{d}"/>'


def speed_lines(x, y, height, length, fills=(SKY, COBALT, NAVY), cut="left", stagger=True, opacity=None):
    """Three feathers stacked like the wing (same height/gap ratios), tips stepping down at 45 deg."""
    h = R_FEATHER * height
    g = R_GAP * height
    step = h + g
    out = []
    for i in range(3):
        dx = i * step if stagger else 0
        out.append(feather_bar(x + dx, y + i * step, h, length - dx, cut, fills[i % len(fills)], opacity))
    return "".join(out)


def chevron(x, y, height, fills=(MINT, AQUA), opacity=None):
    """The two facets as an arrow head, (x, y) = top-left of its box, height = symbol height."""
    k = height / S.HEIGHT
    p = S.part_paths()
    x0 = S.C1  # facet box starts at the top facet's left corner
    op = f' fill-opacity="{opacity}"' if opacity is not None else ""
    return (f'<g transform="translate({fmt(x - x0 * k)} {fmt(y)}) scale({k:.6f})">'
            f'<path fill="{fills[0]}"{op} d="{p["facet_top"]}"/><path fill="{fills[1]}"{op} d="{p["facet_bot"]}"/></g>')


def chevron_width(height):
    return (S.WIDTH - S.C1) * height / S.HEIGHT


def parcel(cx, cy, half_diag, fill=CYAN, opacity=None, stroke=None, sw=0):
    op = f' fill-opacity="{opacity}"' if opacity is not None else ""
    st = f' stroke="{stroke}" stroke-width="{fmt(sw)}"' if stroke else ""
    return (f'<path fill="{fill}"{op}{st} d="M{fmt(cx)} {fmt(cy - half_diag)}L{fmt(cx + half_diag)} {fmt(cy)}'
            f'L{fmt(cx)} {fmt(cy + half_diag)}L{fmt(cx - half_diag)} {fmt(cy)}Z"/>')


def diamond_path(cx, cy, hd, r=0.0):
    """Diamond (square at 45 deg) with optional corner radius r."""
    if r <= 0:
        return f"M{fmt(cx)} {fmt(cy - hd)}L{fmt(cx + hd)} {fmt(cy)}L{fmt(cx)} {fmt(cy + hd)}L{fmt(cx - hd)} {fmt(cy)}Z"
    t = r * math.sqrt(2)  # tangent offset along each edge projected on axes
    o = r * (math.sqrt(2) - 1) * math.sqrt(2) / 2
    pts = [(cx, cy - hd), (cx + hd, cy), (cx, cy + hd), (cx - hd, cy)]
    d = ""
    for i, (px, py) in enumerate(pts):
        prv, nxt = pts[i - 1], pts[(i + 1) % 4]
        def towards(a, b, dist):
            L_ = math.hypot(b[0] - a[0], b[1] - a[1])
            return a[0] + (b[0] - a[0]) * dist / L_, a[1] + (b[1] - a[1]) * dist / L_
        a = towards((px, py), prv, r)
        b = towards((px, py), nxt, r)
        d += ("M" if i == 0 else "L") + f"{fmt(a[0])} {fmt(a[1])}"
        d += f"Q{fmt(px)} {fmt(py)} {fmt(b[0])} {fmt(b[1])}"
    return d + "Z"


# ------------------------------------------------------------------ logo placement

LOCKUP_BUILDERS = {
    "stacked": lambda way, **kw: L.stacked(way, **kw),
    "horizontal": lambda way, **kw: L.horizontal(way, **kw),
    "symbol": lambda way, **kw: L.symbol_only(way),
    "wordmark": lambda way, **kw: L.wordmark_only(way, **kw),
}


def place_logo(kind, way, x, y, w=None, h=None, align="left", valign="top", **kw):
    """Fit a lockup into the box (x, y, w, h); either w or h may be None. Returns (fragment, placed bbox)."""
    frag, (x0, y0, x1, y1) = LOCKUP_BUILDERS[kind](way, **kw)
    bw, bh = x1 - x0, y1 - y0
    s = min(w / bw if w else 1e9, h / bh if h else 1e9)
    pw, ph = bw * s, bh * s
    px = x if align == "left" else (x + (w - pw) / 2 if align == "center" else x + w - pw)
    py = y if valign == "top" else (y + ((h or ph) - ph) / 2 if valign == "middle" else y + (h or ph) - ph)
    return (f'<g transform="translate({fmt(px - x0 * s)} {fmt(py - y0 * s)}) scale({s:.6f})">{frag}</g>',
            (px, py, px + pw, py + ph))


def symbol_at(way, cx, cy, width):
    k = width / S.WIDTH
    return f'<g transform="translate({fmt(cx - width / 2)} {fmt(cy - S.HEIGHT * k / 2)}) scale({k:.6f})">{S.svg_group(way)}</g>'


def flight_crop(way, size, nose=0.89, span=0.62, clip_id=None, rx=0.0):
    """The app-icon crop: parcel+facets fill `span` of the square, nose at `nose`, wings bleed off the left."""
    k = size * span / (S.WIDTH - (S.CX - S.D))
    x = size * nose - S.WIDTH * k
    y = (size - S.HEIGHT * k) / 2
    g = f'<g transform="translate({fmt(x)} {fmt(y)}) scale({k:.6f})">{S.svg_group(way)}</g>'
    if clip_id:
        return (f'<clipPath id="{clip_id}"><rect width="{fmt(size)}" height="{fmt(size)}" rx="{fmt(rx)}"/></clipPath>',
                f'<g clip-path="url(#{clip_id})">{g}</g>')
    return "", g


# ------------------------------------------------------------------ text helpers

def heading(s, x, y, size, fill=NAVY, anchor="start", weight=800, key="montserrat", tracking=-0.01, max_width=None,
            leading=1.1):
    """Multi-line heading (wraps at max_width). y = first baseline. Returns (fragment, last baseline)."""
    lines = T.wrap(s, key, size, max_width, weight, tracking=tracking) if max_width else s.split("\n")
    out = []
    for i, line in enumerate(lines):
        out.append(T.text(line, key, size, x, y + i * size * leading, fill, anchor, weight, tracking=tracking))
    return "".join(out), y + (len(lines) - 1) * size * leading


def para(s, x, y, size, fill=NAVY, max_width=None, weight=500, key="montserrat", leading=1.45, anchor="start",
         opacity=None):
    lines = []
    for block in s.split("\n"):
        lines.extend(T.wrap(block, key, size, max_width, weight) if max_width else [block])
    out = [T.text(line, key, size, x, y + i * size * leading, fill, anchor, weight, opacity=opacity)
           for i, line in enumerate(lines)]
    return "".join(out), y + (len(lines) - 1) * size * leading


def label(s, x, y, size, fill=SKY, anchor="start", weight=700, tracking=0.16):
    """Tracked caps label (Montserrat), y = baseline."""
    return T.text(s.upper(), "montserrat", size, x, y, fill, anchor, weight, tracking=tracking)


def chip(x, y, s, size, fill=CYAN, text_fill=NAVY, pad_x=None, pad_y=None, weight=700, key="montserrat",
         tracking=0.0, anchor="start", icon=None):
    """Rounded pill with text. (x, y) = top-left (anchor start) or top-centre (anchor middle)."""
    pad_x = pad_x if pad_x is not None else size * 0.9
    pad_y = pad_y if pad_y is not None else size * 0.55
    adv = T.advance(s, key, size, weight, tracking=tracking)
    w = adv + 2 * pad_x
    h = size * 0.72 + 2 * pad_y
    if anchor == "middle":
        x -= w / 2
    out = f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" rx="{fmt(h / 2)}" fill="{fill}"/>'
    out += T.text(s, key, size, x + pad_x, y + pad_y + size * 0.72, text_fill, "start", weight, tracking=tracking)
    return out, (x, y, x + w, y + h)


# ------------------------------------------------------------------ codes

def qr(data, x, y, size, fill=NAVY, bg=None, quiet=2, error="m"):
    """QR code as one path (module squares merged per row run)."""
    q = segno.make(data, error=error, micro=False)
    m = [list(r) for r in q.matrix]
    n = len(m)
    total = n + 2 * quiet
    u = size / total
    parts = []
    for r, row in enumerate(m):
        c = 0
        while c < n:
            if row[c]:
                s = c
                while c < n and row[c]:
                    c += 1
                parts.append(f"M{fmt(x + (s + quiet) * u)} {fmt(y + (r + quiet) * u)}h{fmt((c - s) * u)}v{fmt(u)}h{fmt(-(c - s) * u)}Z")
            else:
                c += 1
    b = f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(size)}" height="{fmt(size)}" fill="{bg}"/>' if bg else ""
    return b + f'<path fill="{fill}" d="{"".join(parts)}"/>'


_C128 = ["212222", "222122", "222221", "121223", "121322", "131222", "122213", "122312", "132212", "221213",
         "221312", "231212", "112232", "122132", "122231", "113222", "123122", "123221", "223211", "221132",
         "221231", "213212", "223112", "312131", "311222", "321122", "321221", "312212", "322112", "322211",
         "212123", "212321", "232121", "111323", "131123", "131321", "112313", "132113", "132311", "211313",
         "231113", "231311", "112133", "112331", "132131", "113123", "113321", "133121", "313121", "211331",
         "231131", "213113", "213311", "213131", "311123", "311321", "331121", "312113", "312311", "332111",
         "314111", "221411", "431111", "111224", "111422", "121124", "121421", "141122", "141221", "112214",
         "112412", "122114", "122411", "142112", "142211", "241211", "221114", "413111", "241112", "134111",
         "111242", "121142", "121241", "114212", "124112", "124211", "411212", "421112", "421211", "212141",
         "214121", "412121", "111143", "111341", "131141", "114113", "114311", "411113", "411311", "113141",
         "114131", "311141", "411131", "211412", "211214", "211232", "2331112"]


def code128(data, x, y, w, h, fill="#000000"):
    """Code 128-B barcode as rects fitted into width w."""
    codes = [104] + [ord(ch) - 32 for ch in data]
    check = (104 + sum((i + 1) * c for i, c in enumerate(codes[1:]))) % 103
    codes += [check, 106]
    pattern = "".join(_C128[c] for c in codes)
    modules = sum(int(v) for v in pattern) + 20  # quiet zones
    u = w / modules
    cx = x + 10 * u
    out = []
    for i, v in enumerate(pattern):
        wv = int(v) * u
        if i % 2 == 0:
            out.append(f'<rect x="{fmt(cx)}" y="{fmt(y)}" width="{fmt(wv)}" height="{fmt(h)}" fill="{fill}"/>')
        cx += wv
    return "".join(out)
