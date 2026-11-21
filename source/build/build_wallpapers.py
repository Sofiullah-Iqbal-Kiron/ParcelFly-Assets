"""Device wallpapers for every audience: mobile, tablet, laptop and desktop.

wallpapers/<audience>/<device>/parcelfly-wallpaper-<audience>-<design>-<W>x<H>.jpg
wallpapers/parcelfly-wallpapers-overview.jpg   every design on a phone and a desktop screen

Safe zones: phones keep the lock-screen clock (top) and dock (bottom) calm, iPad art sits in the centre square
(the only part visible in both orientations), desktop lockups stay above the taskbar / dock. Map wallpapers carry
the OpenStreetMap credit next to the lockup, where no taskbar or dock covers it.
"""
import argparse
import math
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pfbrand import ROOT, layout as LY, logo as L, maps as MP, pictograms as P, scenes as SC, symbol as S  # noqa: E402
from pfbrand import text as T  # noqa: E402
from pfbrand.brand import (AMBER, AQUA, CLOUD, COBALT, CONTACT, CYAN, INK, MINT, MIST, NAVY, SKY, SLATE,  # noqa: E402
                           TAGLINE, WHITE)
from pfbrand.svg import Doc, png_image  # noqa: E402
from pfbrand.text import fmt  # noqa: E402

OUT = ROOT / "wallpapers"

DEVICES = [  # (device, width, height, note)
    ("mobile", 1290, 2796, "iPhone Pro Max class, 19.5:9"),
    ("mobile", 1440, 3200, "Android QHD+, 20:9"),
    ("tablet", 2732, 2732, "iPad: square, rotates; art stays in the centre 2048 square"),
    ("tablet", 2560, 1600, "Android and Windows tablets, 16:10 landscape"),
    ("laptop", 2880, 1800, "16:10 (MacBook class)"),
    ("laptop", 1920, 1080, "16:9 Full HD"),
    ("desktop", 3840, 2160, "4K UHD, 16:9"),
    ("desktop", 3440, 1440, "Ultrawide, 21:9"),
]

AUDIENCES = {
    "generic": ["signature", "light", "bangla", "map"],
    "merchant": ["dark", "light"],
    "client": ["dark", "light"],
    "rider": ["dark", "light"],
    "hub-manager": ["map", "cyan"],
    "staff": ["dark", "light"],
    "admin": ["console", "network"],
}

HUB_NAMES = [h["name"] for h in sorted(MP.hubs(), key=lambda h: h["name"])]
HUB_NAMES_BN = [h["name_bn"] for h in sorted(MP.hubs(), key=lambda h: h["name"])]
CREDIT = MP.ATTRIBUTION


# ------------------------------------------------------------------ frame

class G:
    """Layout frame for one canvas: orientation, visible area, hero centre and lockup width."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        r = w / h
        if r < 0.8:
            self.kind = "portrait"
            self.vis = (0.0, 0.0, w, h)
            self.cx, self.cy, self.lw = w / 2, h * 0.555, w * 0.54
        elif r < 1.25:
            self.kind = "square"
            s = min(w, h) * 0.75
            self.vis = ((w - s) / 2, (h - s) / 2, (w + s) / 2, (h + s) / 2)
            self.cx, self.cy, self.lw = w / 2, h / 2, s * 0.40
        else:
            self.kind = "ultra" if r > 2.0 else "landscape"
            self.vis = (0.0, 0.0, w, h)
            self.cx, self.cy, self.lw = w / 2, h * 0.455, h * 0.40
        vx0, vy0, vx1, vy1 = self.vis
        self.u = min(vx1 - vx0, vy1 - vy0)

    @property
    def portrait(self):
        return self.kind == "portrait"


# ------------------------------------------------------------------ hero block

def stacked(way, lang, tagline):
    return L.stacked(way, lang=lang, tagline=tagline)


def hero(g, way, lang="en", tagline="en", pill=None, pill_cols=(CYAN, NAVY), subs=(), scale=1.0, cy=None):
    """Centred stacked lockup + optional audience pill + small lines.
    subs: [(text, font key, size as a share of the lockup width, colour, weight, tracking)].
    Returns (fragment, block bbox, symbol bbox)."""
    lw = g.lw * scale
    frag, (x0, y0, x1, y1) = stacked(way, lang, tagline)
    s = lw / (x1 - x0)
    lh = (y1 - y0) * s
    gap = lw * 0.085
    ps = lw * 0.058
    ph = ps * 0.72 + 2 * ps * 0.55 if pill else 0
    total = lh + (gap + ph if pill else 0) + sum(gap * 0.55 + lw * sz for _, _, sz, _, _, _ in subs)
    top = (cy if cy is not None else g.cy) - total / 2
    tx, ty = g.cx - lw / 2 - x0 * s, top - y0 * s
    out = [f'<g transform="translate({fmt(tx)} {fmt(ty)}) scale({s:.6f})">{frag}</g>']
    sym = (tx, ty, tx + S.WIDTH * s, ty + S.HEIGHT * s)
    y = top + lh
    if pill:
        y += gap
        f, pb = LY.chip(g.cx, y, pill, ps, pill_cols[0], pill_cols[1], anchor="middle", weight=800, tracking=0.14,
                        pad_x=ps * 1.1)
        out.append(f)
        y = pb[3]
    for text, key, sz, col, weight, tracking in subs:
        size = lw * sz
        b = T.ink_bounds(text, key, size, weight, tracking=tracking)
        y += gap * 0.55
        out.append(T.text(text, key, size, g.cx, y - b[1], col, "middle", weight, tracking=tracking))
        y += b[3] - b[1]
    return "".join(out), (g.cx - lw / 2, top, g.cx + lw / 2, y), sym


def corner_lockup(g, way, label=None, credit=None, dark=True, width=None):
    """Small horizontal (or sub-brand) lockup placed where taskbars, docks and clocks do not reach."""
    if g.portrait:
        w = width or g.w * 0.46
        x, y, align = g.cx - w / 2, g.h * 0.83, "center"
    elif g.kind == "square":
        w = width or g.u * 0.34
        x, y, align = g.cx - w / 2, g.vis[3] - g.u * 0.15, "center"
    else:
        w = width or g.h * 0.36
        x, y, align = g.w * 0.955 - w, g.h * 0.80, "right"
    if label:
        frag, bb = L.subbrand_horizontal(label, way)
        s = w / (bb[2] - bb[0])
        frag = f'<g transform="translate({fmt(x - bb[0] * s)} {fmt(y - bb[1] * s)}) scale({s:.6f})">{frag}</g>'
        bb = (x, y, x + w, y + (bb[3] - bb[1]) * s)
    else:
        frag, bb = LY.place_logo("horizontal", way, x, y, w=w, align="left")
    out = [frag]
    if credit:
        cs = max(g.u * 0.0125, 11)
        ax = {"center": g.cx, "right": bb[2]}[align]
        out.append(T.text(credit, "montserrat", cs, ax, bb[3] + cs * 2.4, "#8FA3E8" if dark else SLATE,
                          "middle" if align == "center" else "end", 500))
    return "".join(out), bb


# ------------------------------------------------------------------ backgrounds and devices

def base(g, stops, angle=90, title=""):
    d = Doc(g.w, g.h, title=title, bg=stops[0][1])
    SC.gradient_bg(d, stops, angle=angle)
    return d


def trails(g, sym, fills, opacity, reach=None):
    """Speed lines from the left edge towards the symbol, aligned with its feathers (kept clear of the logo)."""
    if g.portrait:
        return ""          # too little room beside the logo on a phone: the trail would read as a stub
    sx0, sy0, sx1, sy1 = sym
    hgt = sy1 - sy0
    end = sx0 - hgt * 0.42
    start = -hgt * 1.2 if reach is None else end - reach
    return LY.speed_lines(start, sy0, hgt, end - start, fills, opacity=opacity)


def icon_field(g, names, colour, opacity, avoid, seed=3):
    size, step = g.u * 0.052, g.u * 0.15
    rng = random.Random(seed)
    out = []
    pad = step * 0.35
    for r in range(int(g.h / step) + 2):
        for c in range(int(g.w / step) + 2):
            x = c * step + (step / 2 if r % 2 else 0) - step * 0.3
            y = r * step + step * 0.35
            if avoid[0] - pad < x < avoid[2] + pad and avoid[1] - pad < y < avoid[3] + pad:
                continue
            dist = math.hypot((x - g.cx) / g.w, (y - g.cy) / g.h)
            op = opacity * min(1.0, 0.35 + dist * 1.6)
            out.append(f'<g opacity="{op:.3f}">{P.icon(rng.choice(names), x - size / 2, y - size / 2, size, colour, 3.2)}</g>')
    return "".join(out)


def streaks(g, colours, n, opacity, avoid, seed=5):
    """Horizontal motion streaks fading in from the left."""
    rng = random.Random(seed)
    defs, out = [], []
    for i, col in enumerate(colours):
        defs.append(f'<linearGradient id="sk{i}"><stop offset="0" stop-color="{col}" stop-opacity="0"/>'
                    f'<stop offset="1" stop-color="{col}"/></linearGradient>')
    for _ in range(n):
        y = rng.uniform(0, g.h)
        length = rng.uniform(0.12, 0.45) * g.w
        x = rng.uniform(-0.25, 0.95) * g.w
        th = rng.uniform(0.0025, 0.007) * g.u
        if avoid[1] - th * 4 < y < avoid[3] + th * 4 and x < avoid[2] and x + length > avoid[0]:
            continue
        i = rng.randrange(len(colours))
        op = rng.uniform(0.2, 0.75) * opacity
        out.append(f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(length)}" height="{fmt(th)}" rx="{fmt(th / 2)}" '
                   f'fill="url(#sk{i})" opacity="{op:.3f}"/>')
    return f'<defs>{"".join(defs)}</defs>' + "".join(out)


def dot_grid(g, colour, opacity, step=None):
    step = step or g.u * 0.028
    pid = SC.uid("dg")
    r = step * 0.06
    return (f'<defs><pattern id="{pid}" width="{fmt(step)}" height="{fmt(step)}" patternUnits="userSpaceOnUse">'
            f'<circle cx="{fmt(step / 2)}" cy="{fmt(step / 2)}" r="{fmt(r)}" fill="{colour}"/></pattern></defs>'
            f'<rect width="{fmt(g.w)}" height="{fmt(g.h)}" fill="url(#{pid})" opacity="{opacity}"/>')


def route(g, y0, amp, line_col, node_bg, icon_col, text_col, dark):
    """A delivery route with four milestones (pickup, hub, on the way, delivered)."""
    w = g.w
    p = [(-0.04 * w, y0 + amp * 0.2), (0.3 * w, y0 - amp), (0.62 * w, y0 + amp), (1.04 * w, y0 - amp * 0.4)]

    def bez(t):
        a = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
        return sum(k * q[0] for k, q in zip(a, p)), sum(k * q[1] for k, q in zip(a, p))

    sw = max(g.u * 0.006, 3)
    out = [f'<path d="M{fmt(p[0][0])} {fmt(p[0][1])}C{fmt(p[1][0])} {fmt(p[1][1])} {fmt(p[2][0])} {fmt(p[2][1])} '
           f'{fmt(p[3][0])} {fmt(p[3][1])}" fill="none" stroke="{line_col}" stroke-width="{fmt(sw)}" '
           f'stroke-linecap="round" stroke-dasharray="{fmt(sw * 0.1)} {fmt(sw * 2.4)}"/>']
    r = g.u * (0.042 if g.portrait else 0.034)
    ls = g.u * (0.02 if g.portrait else 0.017)
    stops = [("pickup", "Picked up"), ("network", "At the hub"), ("fast", "On the way"), ("thanks", "Delivered")]
    ts = [0.14, 0.38, 0.62, 0.86] if not g.portrait else [0.12, 0.37, 0.63, 0.88]
    for i, ((ic, lab), t) in enumerate(zip(stops, ts)):
        x, y = bez(t)
        last = i == len(stops) - 1
        out.append(f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r * 1.25)}" fill="{line_col}" opacity="0.18"/>')
        out.append(f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="{CYAN if last else node_bg}"/>')
        out.append(P.icon(ic, x - r * 0.62, y - r * 0.62, r * 1.24, NAVY if last else icon_col, 3.4))
        out.append(LY.label(lab, x, y + r * 1.25 + ls * 1.6, ls, text_col, "middle", 700, 0.12))
    return "".join(out)


def fit_extent(g, box, labels, ls, ns, suffix=" Hub"):
    """Extent with the canvas aspect that puts every hub node and label inside box (px), centred in it."""
    kx = math.cos(math.radians(23.72))
    hs = MP.hubs()
    lon0, lat1 = min(h["lon"] for h in hs), max(h["lat"] for h in hs)
    widths = []
    for h in hs:
        wl = 0.0
        if labels in ("en", "both"):
            wl = T.advance(h["name"] + suffix, "montserrat", ls, 800)
        if labels in ("bn", "both"):
            wl = max(wl, T.advance(h["name_bn"] + " হাব", "mina-bold", ls * 0.86))
        widths.append(wl)

    def content(sc):
        bx = []
        for h, wl in zip(hs, widths):
            x, y = (h["lon"] - lon0) * kx * sc, (lat1 - h["lat"]) * sc
            r = ns * 1.4
            if h.get("label", "right") == "right":
                x0, x1 = x - r, x + ns * 1.9 + wl
            else:
                x0, x1 = x - ns * 1.9 - wl, x + r
            bx.append((x0, y - max(r, ls * 0.8), x1, y + max(r, ls * (1.5 if labels == "both" else 0.45))))
        return min(b[0] for b in bx), min(b[1] for b in bx), max(b[2] for b in bx), max(b[3] for b in bx)

    bw, bh = box[2] - box[0], box[3] - box[1]
    lo, hi = 10.0, 1e7
    for _ in range(80):
        sc = math.sqrt(lo * hi)
        c = content(sc)
        if c[2] - c[0] <= bw and c[3] - c[1] <= bh:
            lo = sc
        else:
            hi = sc
    sc = lo
    c = content(sc)
    glon = lon0 + (c[0] + c[2]) / 2 / (kx * sc)
    glat = lat1 - (c[1] + c[3]) / 2 / sc
    clon = glon + (g.w / 2 - (box[0] + box[2]) / 2) / (kx * sc)
    clat = glat - (g.h / 2 - (box[1] + box[3]) / 2) / sc
    hw, hh = g.w / 2 / (kx * sc), g.h / 2 / sc
    return (clon - hw, clat - hh, clon + hw, clat + hh)


def data_edges(g, ext, bg):
    """Hide the edges of the OSM extract when the canvas reaches past it (opaque ground + soft fade)."""
    kx = math.cos(math.radians(23.72))
    b0, b1, b2, b3 = MP.region()["bbox"]
    sc = g.h / (ext[3] - ext[1])
    f = g.u * 0.14
    out = []
    gid = SC.uid("de")
    out.append(f'<linearGradient id="{gid}"><stop offset="0" stop-color="{bg}"/>'
               f'<stop offset="1" stop-color="{bg}" stop-opacity="0"/></linearGradient>')
    xl = (b0 - ext[0]) * kx * sc
    xr = (b2 - ext[0]) * kx * sc
    yt = (ext[3] - b3) * sc
    yb = (ext[3] - b1) * sc
    if xl > -f:
        out.append(f'<rect x="0" y="0" width="{fmt(max(xl, 0))}" height="{fmt(g.h)}" fill="{bg}"/>'
                   f'<rect x="{fmt(xl)}" y="0" width="{fmt(f)}" height="{fmt(g.h)}" fill="url(#{gid})"/>')
    if xr < g.w + f:
        out.append(f'<rect x="{fmt(xr)}" y="0" width="{fmt(max(g.w - xr, 0))}" height="{fmt(g.h)}" fill="{bg}"/>'
                   f'<rect x="{fmt(xr - f)}" y="0" width="{fmt(f)}" height="{fmt(g.h)}" fill="url(#{gid})" '
                   f'transform="rotate(180 {fmt(xr - f / 2)} {fmt(g.h / 2)})"/>')
    if yt > -f:
        out.append(f'<rect x="0" y="0" width="{fmt(g.w)}" height="{fmt(max(yt, 0))}" fill="{bg}"/>'
                   f'<rect x="0" y="{fmt(yt)}" width="{fmt(f)}" height="{fmt(g.w)}" fill="url(#{gid})" '
                   f'transform="rotate(90 0 {fmt(yt)}) translate(0 {fmt(-g.w)})"/>')
    if yb < g.h + f:
        out.append(f'<rect x="0" y="{fmt(yb)}" width="{fmt(g.w)}" height="{fmt(max(g.h - yb, 0))}" fill="{bg}"/>')
    return "".join(out)


def map_wallpaper(g, style, bg, labels, way, sub_label, cid, title):
    dark = style != "light"
    d = Doc(g.w, g.h, title=title, bg=bg)
    ls, ns = g.u * 0.024, g.u * 0.013
    if g.portrait:
        box = (g.w * 0.07, g.h * 0.29, g.w * 0.93, g.h * 0.73)
    elif g.kind == "square":
        vx0, vy0, vx1, vy1 = g.vis
        box = (vx0 + g.u * 0.07, vy0 + g.u * 0.07, vx1 - g.u * 0.07, vy1 - g.u * 0.27)
    else:
        box = (g.w * 0.5 - g.h * 0.62, g.h * 0.09, g.w * 0.5 + g.h * 0.5, g.h * 0.9)
    ext = fit_extent(g, box, labels, ls, ns)
    d.add(MP.hub_map(0, 0, g.w, g.h, style, extent=ext, labels=labels, label_size=ls, node_size=ns, inset=False,
                     attribution=False, fade=False, clip_id=cid))
    d.add(data_edges(g, ext, bg))
    # calm the lockup zone
    gid = SC.uid("mz")
    if g.portrait or g.kind == "square":
        d.defs_add(f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{bg}" '
                   f'stop-opacity="0"/><stop offset="0.5" stop-color="{bg}" stop-opacity="0.92"/>'
                   f'<stop offset="1" stop-color="{bg}"/></linearGradient>')
        y0 = g.h * 0.74 if g.portrait else g.vis[3] - g.u * 0.27
        d.rect(0, y0, g.w, g.h - y0, f"url(#{gid})")
    else:
        d.defs_add(f'<radialGradient id="{gid}" cx="1" cy="1" r="1"><stop offset="0" stop-color="{bg}"/>'
                   f'<stop offset="0.45" stop-color="{bg}" stop-opacity="0.9"/>'
                   f'<stop offset="1" stop-color="{bg}" stop-opacity="0"/></radialGradient>')
        d.rect(g.w * 0.55, g.h * 0.5, g.w * 0.45, g.h * 0.5, f"url(#{gid})")
    frag, _ = corner_lockup(g, way, sub_label, CREDIT, dark=dark)
    d.add(frag)
    return d


def radar(g, cx, cy, r_max, seed=11):
    """Concentric rings, ticks and amber arcs around the symbol (admin oversight)."""
    rng = random.Random(seed)
    sw = max(g.u * 0.0013, 1.2)
    out = []
    n = 6
    for i in range(1, n + 1):
        r = r_max * i / n
        out.append(f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r)}" fill="none" stroke="#2B3A6E" '
                   f'stroke-width="{fmt(sw)}" opacity="{0.95 - i * 0.07:.2f}"/>')
        if i in (2, 3, 5, 6):
            a0 = math.radians(rng.uniform(0, 360))
            a1 = a0 + math.radians(rng.uniform(18, 55))
            x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
            x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
            col = AMBER if i != 3 else CYAN
            out.append(f'<path d="M{fmt(x0)} {fmt(y0)}A{fmt(r)} {fmt(r)} 0 0 1 {fmt(x1)} {fmt(y1)}" fill="none" '
                       f'stroke="{col}" stroke-width="{fmt(sw * 2.6)}" stroke-linecap="round" opacity="0.85"/>')
            out.append(LY.parcel(x1, y1, sw * 4.5, col, 0.95))
    for k in range(120):
        a = math.radians(k * 3)
        ln = r_max * (0.045 if k % 10 == 0 else 0.018)
        x0, y0 = cx + r_max * math.cos(a), cy + r_max * math.sin(a)
        x1, y1 = cx + (r_max + ln) * math.cos(a), cy + (r_max + ln) * math.sin(a)
        out.append(f'<path d="M{fmt(x0)} {fmt(y0)}L{fmt(x1)} {fmt(y1)}" stroke="#3A4A80" stroke-width="{fmt(sw)}"/>')
    for a in (0, 90, 180, 270):
        t = math.radians(a)
        out.append(f'<path d="M{fmt(cx + r_max * 1.08 * math.cos(t))} {fmt(cy + r_max * 1.08 * math.sin(t))}'
                   f'L{fmt(cx + r_max * 1.22 * math.cos(t))} {fmt(cy + r_max * 1.22 * math.sin(t))}" stroke="#3A4A80" '
                   f'stroke-width="{fmt(sw)}"/>')
    return "".join(out)


# ------------------------------------------------------------------ designs

def generic_signature(g):
    d = base(g, [(0, "#00004A"), (0.55, NAVY), (1, "#06199A")], 90, "Parcel Fly wallpaper: signature")
    frag, bb, sym = hero(g, "ondark", tagline="en")
    SC.glow(d, (sym[0] + sym[2]) / 2, (sym[1] + sym[3]) / 2, g.lw * 1.25, COBALT, 0.95)
    SC.glow(d, g.w * 0.92, g.h * 0.06, g.u * 0.8, SKY, 0.35)
    d.add(trails(g, sym, (SKY, COBALT, CYAN), 0.45))
    d.add(frag)
    return d


def generic_light(g):
    d = base(g, [(0, WHITE), (0.6, CLOUD), (1, "#E4EEF8")], 90, "Parcel Fly wallpaper: light")
    SC.lattice(d, MIST, cell=g.u * 0.07, opacity=0.9)
    frag, bb, sym = hero(g, "color", tagline="en")
    SC.glow(d, g.cx, (bb[1] + bb[3]) / 2, g.lw * 1.1, WHITE, 1.0)
    d.add(trails(g, sym, (SKY, COBALT, NAVY), 0.16))
    d.add(frag)
    return d


def generic_bangla(g):
    d = base(g, [(0, "#00004A"), (0.6, NAVY), (1, "#001E8C")], 90, "Parcel Fly wallpaper: Bangla")
    SC.lattice(d, COBALT, cell=g.u * 0.09, opacity=0.55, outline=True)
    frag, bb, sym = hero(g, "ondark", lang="bn", tagline="bn")
    SC.glow(d, g.cx, (bb[1] + bb[3]) / 2, g.lw * 1.2, NAVY, 1.0)
    SC.glow(d, (sym[0] + sym[2]) / 2, (sym[1] + sym[3]) / 2, g.lw * 0.9, COBALT, 0.8)
    d.add(frag)
    return d


def generic_map(g):
    return map_wallpaper(g, "dark", NAVY, "en", "ondark", None, "gm", "Parcel Fly wallpaper: hub map")


def merchant(g, dark):
    fg = "ondark" if dark else "color"
    d = (base(g, [(0, "#00004A"), (0.55, NAVY), (1, "#0A2BA8")], 90, "Parcel Fly wallpaper: merchant") if dark else
         base(g, [(0, WHITE), (1, CLOUD)], 90, "Parcel Fly wallpaper: merchant (light)"))
    frag, bb, sym = hero(g, fg, tagline="en", pill="MERCHANT", pill_cols=(CYAN, NAVY) if dark else (NAVY, WHITE),
                         subs=[("Delivery that keeps up with your business.", "montserrat", 0.044,
                                WHITE if dark else SLATE, 600, 0)])
    d.add(icon_field(g, ["merchant", "parcel", "cash", "track", "fast", "secure", "pickup", "scan", "offers"],
                     "#2C4BD0" if dark else "#BFD2E6", 0.55 if dark else 0.9, bb))
    SC.glow(d, g.cx, (bb[1] + bb[3]) / 2, g.lw * 1.15, NAVY if dark else WHITE, 1.0)
    d.add(frag)
    return d


def client(g, dark):
    fg = "ondark" if dark else "color"
    d = (base(g, [(0, "#00004A"), (0.5, NAVY), (1, "#003C9E")], 90, "Parcel Fly wallpaper: client") if dark else
         base(g, [(0, WHITE), (0.55, CLOUD), (1, "#DDEBF7")], 90, "Parcel Fly wallpaper: client (light)"))
    cy = g.h * 0.47 if g.portrait else (g.cy - g.u * 0.06 if g.kind == "square" else g.h * 0.40)
    frag, bb, sym = hero(g, fg, tagline="en", cy=cy,
                         subs=[("Track every parcel at " + CONTACT["web"], "montserrat", 0.042,
                                WHITE if dark else SLATE, 600, 0)])
    SC.glow(d, g.cx, (bb[1] + bb[3]) / 2, g.lw * 1.2, COBALT if dark else WHITE, 0.7 if dark else 1.0)
    if g.portrait:
        ry, amp = g.h * 0.80, g.h * 0.025
    elif g.kind == "square":
        ry, amp = g.vis[3] - g.u * 0.2, g.u * 0.035
    else:
        ry, amp = g.h * 0.765, g.h * 0.05
    d.add(route(g, ry, amp, SKY if dark else SKY, "#1A2FA0" if dark else WHITE, WHITE if dark else NAVY,
                "#AFC3F0" if dark else SLATE, dark))
    d.add(frag)
    return d


def rider(g, dark):
    fg = "ondark" if dark else "color"
    d = (base(g, [(0, "#00004A"), (0.6, NAVY), (1, "#00136E")], 90, "Parcel Fly wallpaper: rider") if dark else
         base(g, [(0, WHITE), (1, "#EAF2FA")], 90, "Parcel Fly wallpaper: rider (light)"))
    frag, bb, sym = hero(g, fg, tagline="bn", pill="RIDER", pill_cols=(CYAN, NAVY) if dark else (NAVY, WHITE),
                         subs=[("রাইডার টিম", "mina-bold", 0.064, CYAN if dark else SKY, None, 0)])
    d.add(streaks(g, (SKY, CYAN, COBALT) if dark else (SKY, CYAN, "#9DB7E0"), 70 if not g.portrait else 55,
                  0.8 if dark else 0.6, bb))
    SC.glow(d, g.cx, (bb[1] + bb[3]) / 2, g.lw * 1.05, NAVY if dark else WHITE, 1.0)
    d.add(trails(g, sym, (SKY, COBALT, CYAN) if dark else (SKY, COBALT, NAVY), 0.5 if dark else 0.22))
    d.add(frag)
    return d


def hub_manager_map(g):
    return map_wallpaper(g, "light", CLOUD, "both", "color", "Hub", "hm", "Parcel Fly wallpaper: hub manager map")


def hub_manager_cyan(g):
    d = base(g, [(0, "#00C4DE"), (0.6, CYAN), (1, "#009FC7")], 90, "Parcel Fly wallpaper: hub manager")
    SC.lattice(d, WHITE, cell=g.u * 0.08, opacity=0.18)
    names = "  ·  ".join(HUB_NAMES).upper()
    frag, bb, sym = hero(g, "hub", tagline="en", pill="HUB MANAGER", pill_cols=(NAVY, WHITE),
                         subs=[(names, "montserrat", 0.03 if g.portrait else 0.032, NAVY, 700, 0.1)],
                         scale=0.92 if g.portrait else 1.0)
    SC.glow(d, g.cx, (bb[1] + bb[3]) / 2, g.lw * 1.15, "#00D2E6", 0.9)
    d.add(frag)
    return d


def staff(g, dark):
    fg = "ondark" if dark else "color"
    d = (base(g, [(0, "#00004A"), (0.55, NAVY), (1, COBALT)], 70, "Parcel Fly wallpaper: staff") if dark else
         base(g, [(0, WHITE), (1, CLOUD)], 70, "Parcel Fly wallpaper: staff (light)"))
    SC.lattice(d, COBALT if dark else MIST, cell=g.u * 0.06, opacity=0.55 if dark else 0.9)
    names = "  ·  ".join(HUB_NAMES).upper()
    frag, bb, sym = hero(g, fg, tagline="en", pill="TEAM PARCEL FLY", pill_cols=(CYAN, NAVY) if dark else (NAVY, WHITE),
                         subs=[("টিম পার্সেল ফ্লাই", "mina-bold", 0.06, CYAN if dark else SKY, None, 0),
                               (names, "montserrat", 0.03 if g.portrait else 0.032, WHITE if dark else SLATE, 700, 0.1)],
                         scale=0.92 if g.portrait else 1.0)
    SC.glow(d, g.cx, (bb[1] + bb[3]) / 2, g.lw * 1.2, NAVY if dark else WHITE, 1.0)
    d.add(frag)
    return d


def admin_console(g):
    d = base(g, [(0, "#070C26"), (0.6, INK), (1, "#141E4D")], 90, "Parcel Fly wallpaper: admin console")
    d.add(dot_grid(g, "#8E9AC0", 0.22))
    frag, bb, sym = hero(g, "admin", tagline="en", pill="ADMIN", pill_cols=(AMBER, INK))
    scx, scy = (sym[0] + sym[2]) / 2, (sym[1] + sym[3]) / 2
    d.add(radar(g, scx, scy, (g.w * 0.40 if g.portrait else g.u * 0.40)))
    SC.glow(d, scx, scy, g.lw * 0.9, AMBER, 0.16)
    SC.glow(d, g.cx, (bb[1] + bb[3]) / 2, g.lw * 1.1, INK, 0.9)
    d.add(frag)
    return d


def admin_network(g):
    return map_wallpaper(g, "ink", INK, "en", "admin", "Admin", "an", "Parcel Fly wallpaper: admin network")


DESIGNS = {
    ("generic", "signature"): generic_signature,
    ("generic", "light"): generic_light,
    ("generic", "bangla"): generic_bangla,
    ("generic", "map"): generic_map,
    ("merchant", "dark"): lambda g: merchant(g, True),
    ("merchant", "light"): lambda g: merchant(g, False),
    ("client", "dark"): lambda g: client(g, True),
    ("client", "light"): lambda g: client(g, False),
    ("rider", "dark"): lambda g: rider(g, True),
    ("rider", "light"): lambda g: rider(g, False),
    ("hub-manager", "map"): hub_manager_map,
    ("hub-manager", "cyan"): hub_manager_cyan,
    ("staff", "dark"): lambda g: staff(g, True),
    ("staff", "light"): lambda g: staff(g, False),
    ("admin", "console"): admin_console,
    ("admin", "network"): admin_network,
}


# ------------------------------------------------------------------ render

def path_for(aud, design, device, w, h):
    return OUT / aud / device / f"parcelfly-wallpaper-{aud}-{design}-{w}x{h}.jpg"


def render(job):
    aud, design, device, w, h = job
    doc = DESIGNS[(aud, design)](G(w, h))
    im = png_image(doc.svg(), w, w, h).convert("RGB")
    a = np.asarray(im, np.float32)
    rng = np.random.default_rng(w * 7 + h)
    a = a + rng.normal(0, 0.9, a.shape[:2])[..., None]        # dither: no banding in the long gradients
    im = Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8))
    p = path_for(aud, design, device, w, h)
    p.parent.mkdir(parents=True, exist_ok=True)
    im.save(p, quality=90, optimize=True, progressive=True)
    return str(p.relative_to(ROOT))


# ------------------------------------------------------------------ overview

def _round_mask(size, r):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), r, fill=255)
    return m


def phone(img, h=560):
    w = int(h * img.width / img.height)
    bez = int(h * 0.028)
    body = Image.new("RGBA", (w + 2 * bez, h + 2 * bez), (0, 0, 0, 0))
    ImageDraw.Draw(body).rounded_rectangle((0, 0, body.width - 1, body.height - 1), int(h * 0.075), fill="#0E1220")
    scr = img.resize((w, h), Image.LANCZOS).convert("RGBA")
    scr.putalpha(_round_mask((w, h), int(h * 0.062)))
    body.alpha_composite(scr, (bez, bez))
    isl = (body.width // 2 - int(w * 0.16), bez + int(h * 0.018), body.width // 2 + int(w * 0.16), bez + int(h * 0.05))
    ImageDraw.Draw(body).rounded_rectangle(isl, int(h * 0.016), fill="#05070D")
    return body


def monitor(img, w=900):
    h = int(w * img.height / img.width)
    bez = int(w * 0.018)
    stand_h = int(w * 0.16)
    out = Image.new("RGBA", (w + 2 * bez, h + 2 * bez + stand_h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(out)
    cx = out.width // 2
    dr.polygon([(cx - w * 0.05, h + 2 * bez), (cx + w * 0.05, h + 2 * bez), (cx + w * 0.07, h + 2 * bez + stand_h * 0.85),
                (cx - w * 0.07, h + 2 * bez + stand_h * 0.85)], fill="#B9C3CF")
    dr.rounded_rectangle((cx - w * 0.17, h + 2 * bez + stand_h * 0.82, cx + w * 0.17, h + 2 * bez + stand_h), 8, fill="#A5B0BE")
    dr.rounded_rectangle((0, 0, w + 2 * bez - 1, h + 2 * bez - 1), int(w * 0.014), fill="#0E1220")
    out.alpha_composite(img.resize((w, h), Image.LANCZOS).convert("RGBA"), (bez, bez))
    return out


def shadowed(sheet, item, x, y):
    a = item.getchannel("A")
    pad = 40
    sh = Image.new("L", (item.width + 2 * pad, item.height + 2 * pad), 0)
    sh.paste(a, (pad, pad))
    sh = sh.filter(ImageFilter.GaussianBlur(14)).point(lambda v: v * 0.35)
    layer = Image.new("RGBA", sh.size, (10, 16, 50, 0))
    layer.putalpha(sh)
    sheet.alpha_composite(layer, (x - pad + 6, y - pad + 14))
    sheet.alpha_composite(item, (x, y))


def overview():
    designs = [(a, d) for a, ds in AUDIENCES.items() for d in ds]
    cols = 4
    cell_w, cell_h = 1260, 760
    head = 260
    rows = math.ceil(len(designs) / cols)
    sheet = Image.new("RGBA", (cols * cell_w + 120, head + rows * cell_h + 60), CLOUD)
    dr = ImageDraw.Draw(sheet)
    title = Doc(2400, 200, title="t")
    title.add(T.text("Parcel Fly wallpapers", "montserrat", 84, 0, 90, NAVY, "start", 800))
    title.add(T.text("Mobile, tablet, laptop and desktop for every audience: generic, merchant, client, rider, hub manager, "
                     "staff and admin", "montserrat", 34, 0, 160, SLATE, "start", 600))
    sheet.alpha_composite(png_image(title.svg(), 2400, 2400, 200), (60, 40))
    for i, (aud, design) in enumerate(designs):
        cx = 60 + (i % cols) * cell_w
        cy = head + (i // cols) * cell_h
        mob = Image.open(path_for(aud, design, "mobile", 1290, 2796))
        desk = Image.open(path_for(aud, design, "desktop", 3840, 2160))
        m = monitor(desk, 820)
        p = phone(mob, 540)
        shadowed(sheet, m, cx, cy + 30)
        shadowed(sheet, p, cx + 820 + 80, cy + 20)
        lab = Doc(1200, 60, title="l")
        lab.add(T.text(f"{aud.replace('-', ' ').title()}: {design}", "montserrat", 36, 0, 44, NAVY, "start", 700))
        sheet.alpha_composite(png_image(lab.svg(), 1200, 1200, 60), (cx, cy + 640))
    sheet.convert("RGB").save(OUT / "parcelfly-wallpapers-overview.jpg", quality=86, optimize=True, progressive=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="audience or audience:design")
    ap.add_argument("--sizes", help="comma list of WxH to render (default: all)")
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    jobs = []
    for aud, designs in AUDIENCES.items():
        for design in designs:
            if args.only and args.only not in (aud, f"{aud}:{design}"):
                continue
            for device, w, h, _ in DEVICES:
                if args.sizes and f"{w}x{h}" not in args.sizes.split(","):
                    continue
                jobs.append((aud, design, device, w, h))
    with ProcessPoolExecutor(args.workers) as ex:
        done = list(ex.map(render, jobs))
    if not args.only and not args.sizes:
        overview()
    print(f"wallpapers: {len(done)} files")


if __name__ == "__main__":
    main()
