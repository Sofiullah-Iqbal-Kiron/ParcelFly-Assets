"""Realistic brand maps: the five Parcel Fly hubs on real Dhaka to Narayanganj geography (OpenStreetMap), and a
Bangladesh map (Natural Earth). Everything is drawn as SVG paths in the brand palette."""
import json
import math
from functools import lru_cache

from . import SOURCE
from . import layout as LY
from . import text as T
from .brand import AMBER, CLOUD, CYAN, INK, MINT, MIST, NAVY, SKY, SLATE, WHITE, COBALT
from .text import fmt

GEO = SOURCE / "geo"
ATTRIBUTION = "© OpenStreetMap contributors"

STYLES = {
    "dark": {"bg": NAVY, "water": "#00004E", "river": "#00004E", "canal": "#000F6A",
             "secondary": ("#1B3BB0", 0.55), "primary": ("#2C55C8", 0.75), "motorway": ("#3D7BE0", 0.9),
             "rail": ("#FFFFFF", 0.22), "net": CYAN, "node": WHITE, "ring": CYAN, "label": WHITE, "label_bn": CYAN,
             "halo": NAVY, "river_label": "#6E8BE0", "muted": "#8FA3E8", "inset_land": COBALT, "inset_line": CYAN},
    "light": {"bg": CLOUD, "water": "#CBE2F4", "river": "#BCD9F0", "canal": "#D3E6F5",
              "secondary": ("#DCE6F0", 1.0), "primary": ("#C7D6E6", 1.0), "motorway": ("#AFC3DA", 1.0),
              "rail": ("#55607A", 0.35), "net": SKY, "node": NAVY, "ring": CYAN, "label": NAVY, "label_bn": SKY,
              "halo": CLOUD, "river_label": "#6C9CC8", "muted": SLATE, "inset_land": MIST, "inset_line": SKY},
    # admin sub-brand: ink ground, amber network (wallpapers)
    "ink": {"bg": INK, "water": "#050A24", "river": "#050A24", "canal": "#101A45",
            "secondary": ("#243055", 0.6), "primary": ("#33426E", 0.8), "motorway": ("#4A5B8C", 0.9),
            "rail": ("#FFFFFF", 0.16), "net": AMBER, "node": WHITE, "ring": AMBER, "label": WHITE, "label_bn": AMBER,
            "halo": INK, "river_label": "#5A6A99", "muted": "#8E9AC0", "inset_land": "#1A2552", "inset_line": AMBER},
}

# a loop through the four city hubs plus the Narayanganj spur
EDGES = [("mirpur", "rampura"), ("rampura", "jatrabari"), ("jatrabari", "bakshibazar"), ("bakshibazar", "mirpur"),
         ("jatrabari", "narayanganj")]

RIVER_LABELS = {"Buriganga River": "Buriganga", "Turag River": "Turag", "Balu River": "Balu",
                "Meghna River": "Meghna", "Dhaleshwari River": "Dhaleshwari"}
# Shitalakshya is mapped as a water area without a named centre line: label it at a known point on the river.
POINT_LABELS = [("Shitalakshya", 90.5262, 23.652, -80)]


@lru_cache(maxsize=None)
def region():
    return json.loads((GEO / "dhaka-region.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def hubs():
    return json.loads((GEO / "hubs.json").read_text(encoding="utf-8"))["hubs"]


@lru_cache(maxsize=None)
def country():
    return json.loads((GEO / "bangladesh.json").read_text(encoding="utf-8"))


def hub(key):
    return next(h for h in hubs() if h["key"] == key)


class Proj:
    """Local equirectangular projection fitted to a box."""

    def __init__(self, x, y, w, h, extent, lat0=23.72):
        self.kx = math.cos(math.radians(lat0))
        minlon, minlat, maxlon, maxlat = extent
        gw, gh = (maxlon - minlon) * self.kx, maxlat - minlat
        self.s = min(w / gw, h / gh)
        cx, cy = (minlon + maxlon) / 2, (minlat + maxlat) / 2
        self.cx, self.cy, self.bx, self.by = cx, cy, x + w / 2, y + h / 2
        self.x, self.y, self.w, self.h = x, y, w, h

    def __call__(self, lon, lat):
        return self.bx + (lon - self.cx) * self.kx * self.s, self.by - (lat - self.cy) * self.s

    def km(self, km):
        return km / 110.574 * self.s


def _ring(p, pts):
    return "M" + "L".join(f"{fmt(a)} {fmt(b)}" for a, b in (p(lon, lat) for lon, lat in pts)) + "Z"


def _line(p, pts):
    return "M" + "L".join(f"{fmt(a)} {fmt(b)}" for a, b in (p(lon, lat) for lon, lat in pts))


def hub_extent(keys=None, pad=0.22):
    hs = [h for h in hubs() if keys is None or h["key"] in keys]
    lons = [h["lon"] for h in hs]
    lats = [h["lat"] for h in hs]
    dl = max(max(lats) - min(lats), 0.04)
    dn = max(max(lons) - min(lons), 0.04)
    return (min(lons) - dn * pad, min(lats) - dl * pad, max(lons) + dn * pad, max(lats) + dl * pad)


def halo_text(s, key, size, x, y, fill, halo, anchor="start", weight=None, sw=None, tracking=0.0):
    d, adv = T.path_d(s, key, size, x, y, anchor, weight, tracking=tracking)
    sw = sw if sw is not None else size * 0.32
    return (f'<path d="{d}" fill="none" stroke="{halo}" stroke-width="{fmt(sw)}" stroke-linejoin="round" '
            f'stroke-opacity="0.92"/><path d="{d}" fill="{fill}"/>')


def hub_map(x, y, w, h, style="dark", extent=None, highlight=None, labels="both", label_size=None, network=True,
            inset=True, scalebar=False, attribution=True, rivers=True, fade=True, clip_id="mapclip", node_size=None,
            hub_suffix=" Hub", only=None):
    """The hub network map inside the box (x, y, w, h). Returns an SVG fragment (defs included)."""
    st = STYLES[style]
    extent = extent or hub_extent()
    p = Proj(x, y, w, h, extent)
    reg = region()
    unit = min(w, h)
    ls = label_size or max(unit * 0.034, 2.0)
    out = [f'<clipPath id="{clip_id}"><rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}"/></clipPath>',
           f'<g clip-path="url(#{clip_id})">',
           f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" fill="{st["bg"]}"/>']
    # water areas
    d = "".join(_ring(p, ring) for poly in reg["water"] for ring in poly)
    out.append(f'<path d="{d}" fill="{st["water"]}" fill-rule="evenodd"/>')
    lw = max(unit * 0.0016, 0.15)
    for k, col in [("canal", st["canal"]), ("river", st["river"])]:
        d = "".join(_line(p, ln) for ln in reg["lines"][k])
        out.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{fmt(lw * (1.0 if k == "canal" else 2.2))}" '
                   f'stroke-linecap="round" stroke-linejoin="round"/>')
    # transport
    for k, mul in [("secondary", 0.9), ("primary", 1.35), ("motorway", 2.0)]:
        col, op = st[k]
        d = "".join(_line(p, ln) for ln in reg["lines"][k])
        out.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-opacity="{op}" stroke-width="{fmt(lw * mul)}" '
                   f'stroke-linecap="round" stroke-linejoin="round"/>')
    col, op = st["rail"]
    d = "".join(_line(p, ln) for ln in reg["lines"]["rail"])
    out.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-opacity="{op}" stroke-width="{fmt(lw * 1.1)}" '
               f'stroke-dasharray="{fmt(lw * 5)} {fmt(lw * 3)}"/>')
    # hub label boxes (obstacles for river names)
    hs_all = [h_ for h_ in hubs() if only is None or h_["key"] in only]
    ns0 = node_size or unit * 0.022
    obstacles = []
    for h_ in hs_all:
        px, py = p(h_["lon"], h_["lat"])
        r = ns0 * 1.6
        obstacles.append((px - r, py - r, px + r, py + r))
        if labels:
            size = ls * (1.15 if highlight == h_["key"] else 1.0)
            wlab = max(T.advance(h_["name"] + hub_suffix, "montserrat", size, 800) if labels in ("en", "both") else 0,
                       T.advance(h_["name_bn"] + " হাব", "mina-bold", size * 0.86) if labels in ("bn", "both") else 0)
            y0b, y1b = py - size * 0.75, py + size * (1.45 if labels == "both" else 0.4)
            if h_.get("label", "right") == "right":
                obstacles.append((px + ns0 * 1.6, y0b, px + ns0 * 1.9 + wlab, y1b))
            else:
                obstacles.append((px - ns0 * 1.9 - wlab, y0b, px - ns0 * 1.6, y1b))
    if inset:
        isz = unit * 0.24
        obstacles.append((x + w - isz - unit * 0.03, y + unit * 0.03, x + w - unit * 0.03, y + unit * 0.03 + isz * 1.18))
    # river names along their courses
    if rivers:
        out.append(_river_labels(p, reg, st, max(ls * 0.62, 1.2), obstacles))
    if fade:
        out.append(_edge_fade(x, y, w, h, st["bg"], clip_id))
    # network
    hs = [h_ for h_ in hubs() if only is None or h_["key"] in only]
    pos = {h_["key"]: p(h_["lon"], h_["lat"]) for h_ in hs}
    if network:
        nw = max(unit * 0.0045, 0.35)
        for a, b in EDGES:
            if a not in pos or b not in pos:
                continue
            (x1, y1), (x2, y2) = pos[a], pos[b]
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            dx, dy = x2 - x1, y2 - y1
            L = math.hypot(dx, dy) or 1
            bend = 0.12 * L
            cxp, cyp = mx - dy / L * bend, my + dx / L * bend
            dim = highlight and highlight not in (a, b)
            out.append(f'<path d="M{fmt(x1)} {fmt(y1)}Q{fmt(cxp)} {fmt(cyp)} {fmt(x2)} {fmt(y2)}" fill="none" '
                       f'stroke="{st["net"]}" stroke-opacity="{0.35 if dim else 0.95}" stroke-width="{fmt(nw)}" '
                       f'stroke-linecap="round" stroke-dasharray="{fmt(nw * 0.1)} {fmt(nw * 2.6)}"/>' if dim else
                       f'<path d="M{fmt(x1)} {fmt(y1)}Q{fmt(cxp)} {fmt(cyp)} {fmt(x2)} {fmt(y2)}" fill="none" '
                       f'stroke="{st["net"]}" stroke-opacity="0.9" stroke-width="{fmt(nw)}" stroke-linecap="round"/>')
    # nodes and labels
    ns = node_size or unit * 0.022
    for h_ in hs:
        px, py = pos[h_["key"]]
        hi = highlight == h_["key"]
        dim = highlight and not hi
        r = ns * (1.45 if hi else 1.0)
        if hi:
            gid = f"{clip_id}-glow"
            out.append(f'<radialGradient id="{gid}"><stop offset="0" stop-color="{CYAN}" stop-opacity="0.55"/>'
                       f'<stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>'
                       f'<circle cx="{fmt(px)}" cy="{fmt(py)}" r="{fmt(r * 4.2)}" fill="url(#{gid})"/>')
        out.append(LY.parcel(px, py, r * 1.38, st["ring"], 0.5 if dim else 1.0))
        out.append(LY.parcel(px, py, r, st["node"], 0.6 if dim else 1.0))
        if labels:
            side = h_.get("label", "right")
            anchor = "start" if side == "right" else "end"
            tx = px + (r * 1.9 if side == "right" else -r * 1.9)
            size = ls * (1.15 if hi else 1.0)
            op_fill = st["label"] if not dim else st["muted"]
            if labels in ("en", "both"):
                out.append(halo_text(h_["name"] + hub_suffix, "montserrat", size, tx, py + size * 0.18, op_fill,
                                     st["halo"], anchor, 800))
            if labels in ("bn", "both"):
                bs = size * (0.86 if labels == "both" else 1.05)
                by = py + size * (1.2 if labels == "both" else 0.3)
                out.append(halo_text(h_["name_bn"] + (" হাব" if hub_suffix else ""), "mina-bold", bs, tx, by,
                                     st["label_bn"] if not dim else st["muted"], st["halo"], anchor))
    if inset:
        out.append(country_inset(x + w - unit * 0.24 - unit * 0.03, y + unit * 0.03, unit * 0.24, style, extent))
    if scalebar:
        out.append(_scalebar(p, x + unit * 0.04, y + h - unit * 0.05, st))
    if attribution:
        out.append(T.text(ATTRIBUTION, "montserrat", max(unit * 0.016, 1.1), x + w - unit * 0.015, y + h - unit * 0.015,
                          st["muted"], "end", 500))
    out.append("</g>")
    return "".join(out)


def _edge_fade(x, y, w, h, bg, cid):
    f = min(w, h) * 0.12
    g = (f'<linearGradient id="{cid}-fh"><stop offset="0" stop-color="{bg}"/><stop offset="1" stop-color="{bg}" stop-opacity="0"/></linearGradient>'
         f'<linearGradient id="{cid}-fv" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{bg}"/><stop offset="1" stop-color="{bg}" stop-opacity="0"/></linearGradient>')
    return (g + f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(f)}" height="{fmt(h)}" fill="url(#{cid}-fh)"/>'
            f'<rect x="{fmt(x + w - f)}" y="{fmt(y)}" width="{fmt(f)}" height="{fmt(h)}" fill="url(#{cid}-fh)" '
            f'transform="rotate(180 {fmt(x + w - f / 2)} {fmt(y + h / 2)})"/>'
            f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(f)}" fill="url(#{cid}-fv)"/>'
            f'<rect x="{fmt(x)}" y="{fmt(y + h - f)}" width="{fmt(w)}" height="{fmt(f)}" fill="url(#{cid}-fv)" '
            f'transform="rotate(180 {fmt(x + w / 2)} {fmt(y + h - f / 2)})"/>')


def _hits(box_, obstacles):
    x0, y0, x1, y1 = box_
    return any(not (x1 < a or x0 > c or y1 < b or y0 > d) for a, b, c, d in obstacles)


def _rot_box(mx, my, tw, th, ang):
    a = math.radians(ang)
    hw, hh = tw / 2, th / 2
    ex = abs(hw * math.cos(a)) + abs(hh * math.sin(a))
    ey = abs(hw * math.sin(a)) + abs(hh * math.cos(a))
    return mx - ex, my - ey, mx + ex, my + ey


def _river_labels(p, reg, st, size, obstacles=()):
    out = []
    for name, label in RIVER_LABELS.items():
        best = None
        for ln in reg["rivers_named"].get(name, []):
            pts = [p(lon, lat) for lon, lat in ln]
            inside = [(a, b) for a, b in pts if p.x + p.w * 0.08 < a < p.x + p.w * 0.92 and p.y + p.h * 0.08 < b < p.y + p.h * 0.92]
            if len(inside) < 2:
                continue
            length = sum(math.hypot(inside[i + 1][0] - inside[i][0], inside[i + 1][1] - inside[i][1]) for i in range(len(inside) - 1))
            if not best or length > best[0]:
                best = (length, inside)
        if not best:
            continue
        length, pts = best
        tw = T.advance(label, "montserrat-italic", size, 600, tracking=0.08)
        if length < tw * 1.6:
            continue
        for frac in (0.5, 0.38, 0.62, 0.27, 0.73, 0.18, 0.82):
            target, acc, placed = length * frac, 0.0, False
            for i in range(len(pts) - 1):
                seg = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
                if acc + seg >= target:
                    t = (target - acc) / (seg or 1)
                    mx = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t
                    my = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t
                    j0, j1 = max(0, i - 3), min(len(pts) - 1, i + 4)
                    ang = math.degrees(math.atan2(pts[j1][1] - pts[j0][1], pts[j1][0] - pts[j0][0]))
                    if ang > 90:
                        ang -= 180
                    elif ang < -90:
                        ang += 180
                    if not _hits(_rot_box(mx, my, tw, size * 1.2, ang), obstacles):
                        d, _ = T.path_d(label, "montserrat-italic", size, 0, size * 0.35, "middle", 600, tracking=0.08)
                        out.append(f'<path transform="translate({fmt(mx)} {fmt(my)}) rotate({ang:.1f})" d="{d}" '
                                   f'fill="{st["river_label"]}"/>')
                        placed = True
                    break
                acc += seg
            if placed:
                break
    for label, lon, lat, ang in POINT_LABELS:
        mx, my = p(lon, lat)
        tw = T.advance(label, "montserrat-italic", size, 600, tracking=0.08)
        if (p.x + p.w * 0.08 < mx < p.x + p.w * 0.92 and p.y + p.h * 0.08 < my < p.y + p.h * 0.92
                and not _hits(_rot_box(mx, my, tw, size * 1.2, ang), obstacles)):
            d, _ = T.path_d(label, "montserrat-italic", size, 0, size * 0.35, "middle", 600, tracking=0.08)
            out.append(f'<path transform="translate({fmt(mx)} {fmt(my)}) rotate({ang})" d="{d}" fill="{st["river_label"]}"/>')
    return "".join(out)


def _scalebar(p, x, y, st):
    km = 5
    L = p.km(km)
    if L > p.w * 0.3:
        km = 2
        L = p.km(km)
    hgt = max(p.h * 0.008, 0.4)
    size = max(min(p.w, p.h) * 0.022, 1.2)
    return (f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(L / 2)}" height="{fmt(hgt)}" fill="{st["label"]}"/>'
            f'<rect x="{fmt(x + L / 2)}" y="{fmt(y)}" width="{fmt(L / 2)}" height="{fmt(hgt)}" fill="{st["muted"]}"/>'
            + T.text(f"{km} km", "montserrat", size, x + L + size * 0.6, y + hgt, st["label"], "start", 700))


def country_inset(x, y, size, style="dark", extent=None, label=True):
    """Bangladesh locator with the detail extent marked."""
    st = STYLES[style]
    c = country()
    minx, miny, maxx, maxy = c["bounds"]
    p = Proj(x, y, size, size * 1.18, (minx, miny, maxx, maxy), lat0=23.7)
    out = [f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(size)}" height="{fmt(size * 1.18)}" rx="{fmt(size * 0.06)}" '
           f'fill="{st["bg"]}" fill-opacity="0.85" stroke="{st["inset_line"]}" stroke-opacity="0.35" stroke-width="{fmt(size * 0.006)}"/>']
    pad = Proj(x + size * 0.08, y + size * 0.1, size * 0.84, size * 0.92, (minx, miny, maxx, maxy), lat0=23.7)
    d = "".join(_ring(pad, ring) for poly in c["outline"] for ring in poly)
    out.append(f'<path d="{d}" fill="{st["inset_land"]}" fill-rule="evenodd"/>')
    d = "".join(_line(pad, ln) for r in c["rivers"] for ln in r["lines"])
    out.append(f'<path d="{d}" fill="none" stroke="{st["inset_line"]}" stroke-opacity="0.55" stroke-width="{fmt(size * 0.006)}"/>')
    if extent:
        (ax, ay), (bx, by) = pad(extent[0], extent[3]), pad(extent[2], extent[1])
        out.append(f'<rect x="{fmt(ax)}" y="{fmt(ay)}" width="{fmt(max(bx - ax, size * 0.03))}" '
                   f'height="{fmt(max(by - ay, size * 0.03))}" fill="none" stroke="{MINT}" stroke-width="{fmt(size * 0.012)}"/>')
    if label:
        out.append(T.text("BANGLADESH", "montserrat", size * 0.06, x + size / 2, y + size * 1.12, st["muted"], "middle", 800,
                          tracking=0.16))
    return "".join(out)


def bangladesh_map(x, y, w, h, style="dark", highlight_dhaka=True, rivers=True, labels=True, clip_id="bdclip"):
    """Bangladesh with its major rivers, Dhaka and Narayanganj highlighted (for 'based in Bangladesh' contexts)."""
    st = STYLES[style]
    c = country()
    minx, miny, maxx, maxy = c["bounds"]
    p = Proj(x, y, w, h, (minx - 0.15, miny - 0.1, maxx + 0.15, maxy + 0.1), lat0=23.7)
    unit = min(w, h)
    out = [f'<clipPath id="{clip_id}"><rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}"/></clipPath>',
           f'<g clip-path="url(#{clip_id})">']
    d = "".join(_ring(p, ring) for poly in c["outline"] for ring in poly)
    land = "#0A1B9A" if style == "dark" else WHITE
    out.append(f'<path d="{d}" fill="{land}" fill-rule="evenodd" stroke="{st["inset_line"]}" stroke-opacity="0.6" '
               f'stroke-width="{fmt(unit * 0.003)}" stroke-linejoin="round"/>')
    if rivers:
        for r in c["rivers"]:
            d = "".join(_line(p, ln) for ln in r["lines"])
            out.append(f'<path d="{d}" fill="none" stroke="{st["net"] if style == "light" else SKY}" stroke-opacity="0.75" '
                       f'stroke-width="{fmt(unit * 0.004)}" stroke-linecap="round" stroke-linejoin="round"/>')
    if highlight_dhaka:
        dx, dy = p(90.4125, 23.8103)
        nx, ny = p(90.4988, 23.6237)
        gid = f"{clip_id}-g"
        out.append(f'<radialGradient id="{gid}"><stop offset="0" stop-color="{CYAN}" stop-opacity="0.6"/>'
                   f'<stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>'
                   f'<circle cx="{fmt((dx + nx) / 2)}" cy="{fmt((dy + ny) / 2)}" r="{fmt(unit * 0.09)}" fill="url(#{gid})"/>')
        out.append(LY.parcel(dx, dy, unit * 0.014, st["node"]))
        out.append(LY.parcel(nx, ny, unit * 0.011, st["node"]))
        if labels:
            ls = unit * 0.032
            out.append(halo_text("Dhaka", "montserrat", ls, dx + unit * 0.025, dy - unit * 0.004, st["label"], st["halo"],
                                 "start", 800))
            out.append(halo_text("Narayanganj", "montserrat", ls * 0.8, nx + unit * 0.022, ny + unit * 0.02, st["label"],
                                 st["halo"], "start", 700))
    if labels:
        out.append(T.text("BANGLADESH", "montserrat", unit * 0.03, x + w * 0.5, y + h * 0.97, st["muted"], "middle", 800,
                          tracking=0.2))
    out.append("</g>")
    return "".join(out)
