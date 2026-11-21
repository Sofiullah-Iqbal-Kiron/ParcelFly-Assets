"""Realistic brand maps: the Parcel Fly hubs on real Dhaka to Narayanganj geography (OpenStreetMap), and a
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
         ("jatrabari", "narayanganj"), ("bakshibazar", "keraniganj")]
NUMBER_WORDS = {3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten"}
AREAS = "Dhaka and Narayanganj"      # the two districts the hubs are in (Keraniganj is inside Dhaka District)

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


def hub_count_word():
    return NUMBER_WORDS[len(hubs())]


def headline():
    """'Six hubs across Dhaka and Narayanganj.' (count from hubs.json)."""
    return f"{hub_count_word()} hubs across {AREAS}."


def hub_line():
    """Every hub, north to south: '..., Keraniganj and Narayanganj hubs keep us close to your customers.'"""
    ns = [h["name"] for h in sorted(hubs(), key=lambda h: -h["lat"])]
    return f"{', '.join(ns[:-1])} and {ns[-1]} hubs keep us close to your customers."


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


def _label_layout(h_, px, py, r, size, labels, suffix):
    """Where a hub label goes. Sides: 'left', 'right' (beside the node) or 'below' (centred under it); an optional
    'label_dy' in hubs.json moves it up (negative) or down in label sizes, for pins that sit close together.
    Returns (anchor, x, English baseline, Bangla baseline, Bangla size, box incl. halo)."""
    side = h_.get("label", "right")
    py = py + h_.get("label_dy", 0.0) * size          # optional nudge from hubs.json (in label sizes)
    bs = size * (0.86 if labels == "both" else 1.05)
    wl = 0.0
    if labels in ("en", "both"):
        wl = T.advance(h_["name"] + suffix, "montserrat", size, 800)
    if labels in ("bn", "both"):
        wl = max(wl, T.advance(h_["name_bn"] + (" হাব" if suffix else ""), "mina-bold", bs))
    halo = size * 0.18
    if side == "below":
        anchor, tx = "middle", px
        top = py + r * 1.75
        ty = top + size * 0.74
        by = ty + size * 1.05 if labels == "both" else top + bs * 0.78
        box = (tx - wl / 2, top, tx + wl / 2, (ty if labels == "en" else by) + size * 0.35)
    else:
        anchor = "start" if side == "right" else "end"
        tx = px + (r * 1.9 if side == "right" else -r * 1.9)
        ty = py + size * 0.18
        by = py + size * (1.2 if labels == "both" else 0.3)
        x0, x1 = (tx, tx + wl) if side == "right" else (tx - wl, tx)
        box = (x0, py - size * 0.7, x1, py + size * {"en": 0.35, "both": 1.55, "bn": 0.75}[labels])
    return anchor, tx, ty, by, bs, (box[0] - halo, box[1] - halo, box[2] + halo, box[3] + halo)


def _label_boxes(sc, hs, labels, ls, ns, suffix, highlight, lon0, lat1):
    """[(hub index, box)] for every node and label at sc px per degree, relative to (lon0, lat1)."""
    kx = math.cos(math.radians(23.72))
    out = []
    for i, h_ in enumerate(hs):
        hi = highlight == h_["key"]
        px, py = (h_["lon"] - lon0) * kx * sc, (lat1 - h_["lat"]) * sc
        r = ns * (1.45 if hi else 1.0)
        node = r * 1.38                                  # the pin's outer diamond (the soft glow may overlap)
        out.append((i, (px - node, py - node, px + node, py + node)))
        if labels:
            out.append((i, _label_layout(h_, px, py, r, ls * (1.15 if hi else 1.0), labels, suffix)[5]))
    return out


def _clashes(bx, hs):
    """Pairs of hubs whose labels overlap another hub's label or pin (pins tested by the square inside the diamond)."""
    out = set()
    for a, (i, p_) in enumerate(bx):
        for b_, (j, q) in enumerate(bx):
            if i == j or b_ <= a:
                continue
            pn, qn = a % 2 == 0, b_ % 2 == 0           # even entries are pins when labels are on
            if pn and qn:
                continue
            if pn:
                c, hlf = ((p_[0] + p_[2]) / 2, (p_[1] + p_[3]) / 2), (p_[2] - p_[0]) / 4
                p_ = (c[0] - hlf, c[1] - hlf, c[0] + hlf, c[1] + hlf)
            if qn:
                c, hlf = ((q[0] + q[2]) / 2, (q[1] + q[3]) / 2), (q[2] - q[0]) / 4
                q = (c[0] - hlf, c[1] - hlf, c[0] + hlf, c[1] + hlf)
            if _overlap(p_, q):
                out.add(tuple(sorted((hs[i]["key"], hs[j]["key"]))))
    return sorted(out)


def _overlap(p, q):
    return p[0] < q[2] and p[2] > q[0] and p[1] < q[3] and p[3] > q[1]


def fit_extent(x, y, w, h, labels="both", label_size=None, node_size=None, suffix=" Hub", highlight=None, keys=None,
               avoid=(), margin=None, pad=0.22):
    """Extent (with the box's aspect) that keeps every hub node and label inside the box and clear of `avoid` boxes
    (inset, scale bar, credit). Never zooms in past the classic hub_extent framing: first slides the network within
    the box, then zooms out only as far as the labels need. Prints a warning if labels of two hubs still collide."""
    hs = [h_ for h_ in hubs() if keys is None or h_["key"] in keys]
    kx = math.cos(math.radians(23.72))
    unit = min(w, h)
    ls = label_size or max(unit * 0.034, 2.0)
    ns = node_size or unit * 0.022
    m = unit * 0.035 if margin is None else margin
    b = hub_extent(keys, pad)
    s0 = min(w / ((b[2] - b[0]) * kx), h / (b[3] - b[1]))
    lon0, lat1 = min(h_["lon"] for h_ in hs), max(h_["lat"] for h_ in hs)
    grid = sorted(((fx, fy) for fx in (0, 0.25, 0.5, 0.75, 1) for fy in (0, 0.25, 0.5, 0.75, 1)),
                  key=lambda t: (t[0] - 0.5) ** 2 + (t[1] - 0.5) ** 2)

    def position(sc):
        bx = _label_boxes(sc, hs, labels, ls, ns, suffix, highlight, lon0, lat1)
        c0, c1 = min(q[1][0] for q in bx), min(q[1][1] for q in bx)
        c2, c3 = max(q[1][2] for q in bx), max(q[1][3] for q in bx)
        if c2 - c0 > w - 2 * m or c3 - c1 > h - 2 * m:
            return None
        lx, hx = x + m - c0, x + w - m - c2
        ly, hy = y + m - c1, y + h - m - c3
        for fx, fy in grid:
            ox, oy = lx + (hx - lx) * fx, ly + (hy - ly) * fy
            if not any(_overlap((q[0] + ox, q[1] + oy, q[2] + ox, q[3] + oy), a) for _, q in bx for a in avoid):
                return ox, oy
        return None

    sc, pos = s0, position(s0)
    if pos is None:
        lo, hi = s0 * 0.05, s0
        for _ in range(48):
            mid = (lo + hi) / 2
            if position(mid) is not None:
                lo = mid
            else:
                hi = mid
        sc, pos = lo, position(lo)
    ox, oy = pos
    bx = _label_boxes(sc, hs, labels, ls, ns, suffix, highlight, lon0, lat1)
    clash = _clashes(bx, hs) if labels else []
    if clash:
        print(f"  map warning: labels collide {clash} in a {w:.0f} x {h:.0f} map")
    clon = lon0 - (ox - (x + w / 2)) / (kx * sc)
    clat = lat1 + (oy - (y + h / 2)) / sc
    hw, hh = w / 2 / (kx * sc), h / 2 / sc
    return (clon - hw, clat - hh, clon + hw, clat + hh)


def halo_text(s, key, size, x, y, fill, halo, anchor="start", weight=None, sw=None, tracking=0.0):
    d, adv = T.path_d(s, key, size, x, y, anchor, weight, tracking=tracking)
    sw = sw if sw is not None else size * 0.32
    return (f'<path d="{d}" fill="none" stroke="{halo}" stroke-width="{fmt(sw)}" stroke-linejoin="round" '
            f'stroke-opacity="0.92"/><path d="{d}" fill="{fill}"/>')


def hub_map(x, y, w, h, style="dark", extent=None, highlight=None, labels="both", label_size=None, network=True,
            inset=True, scalebar=False, attribution=True, rivers=True, fade=True, clip_id="mapclip", node_size=None,
            hub_suffix=" Hub", only=None, avoid=()):
    """The hub network map inside the box (x, y, w, h). Returns an SVG fragment (defs included)."""
    st = STYLES[style]
    unit = min(w, h)
    ls = label_size or max(unit * 0.034, 2.0)
    if extent is None:
        avoid = list(avoid)                       # caller's keep-clear zones (text fades, overlays) plus our own
        if inset:
            isz = unit * 0.24
            avoid.append((x + w - isz - unit * 0.03, y + unit * 0.03, x + w - unit * 0.03, y + unit * 0.03 + isz * 1.18))
        if scalebar:
            avoid.append((x + unit * 0.03, y + h - unit * 0.09, x + unit * 0.32, y + h - unit * 0.02))
        if attribution:
            avoid.append((x + w - unit * 0.36, y + h - unit * 0.045, x + w, y + h))
        extent = fit_extent(x, y, w, h, labels, ls, node_size or unit * 0.022, hub_suffix, highlight, only, avoid)
    p = Proj(x, y, w, h, extent)
    reg = region()
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
            hi_ = highlight == h_["key"]
            obstacles.append(_label_layout(h_, px, py, ns0 * (1.45 if hi_ else 1.0), ls * (1.15 if hi_ else 1.0),
                                           labels, hub_suffix)[5])
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
            size = ls * (1.15 if hi else 1.0)
            anchor, tx, ty, by, bs, _ = _label_layout(h_, px, py, r, size, labels, hub_suffix)
            op_fill = st["label"] if not dim else st["muted"]
            if labels in ("en", "both"):
                out.append(halo_text(h_["name"] + hub_suffix, "montserrat", size, tx, ty, op_fill, st["halo"], anchor, 800))
            if labels in ("bn", "both"):
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
