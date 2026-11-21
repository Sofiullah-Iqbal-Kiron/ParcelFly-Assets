"""Logo motion engine: one timeline per animation, exported to animated SVG (CSS), Lottie JSON and video frames.

Parts are taken from the static lockups in pfbrand.logo, so every animation resolves exactly to the master logo.
Track properties (lockup units): tx, ty (translation), s (uniform scale), sx/sy (extra scale, only for effects such as
speed lines, never for the logo), r (rotation, degrees), o (opacity), fo (fill opacity), draw (outline drawn 0..1),
clip (x0, x1) animated horizontal window. A part may also have a static window (x0, x1) for per-letter effects.
"""
import json
import math
import re

from . import layout as LY
from . import logo as L
from . import symbol as S
from .text import fmt

# ------------------------------------------------------------------ easing


def linear(t):
    return t


def out_cubic(t):
    return 1 - (1 - t) ** 3


def in_cubic(t):
    return t ** 3


def in_out_cubic(t):
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def out_quint(t):
    return 1 - (1 - t) ** 5


def out_back(t, s=1.45):
    t -= 1
    return 1 + (s + 1) * t ** 3 + s * t ** 2


def soft_back(t):
    return out_back(t, 1.1)


def out_bounce(t):
    n, d = 7.5625, 2.75
    if t < 1 / d:
        return n * t * t
    if t < 2 / d:
        t -= 1.5 / d
        return n * t * t + 0.75
    if t < 2.5 / d:
        t -= 2.25 / d
        return n * t * t + 0.9375
    t -= 2.625 / d
    return n * t * t + 0.984375


def in_out_sine(t):
    return -(math.cos(math.pi * t) - 1) / 2


DEFAULTS = {"tx": 0.0, "ty": 0.0, "s": 1.0, "sx": 1.0, "sy": 1.0, "r": 0.0, "o": 1.0, "fo": 1.0, "draw": None,
            "clip": None}

# ------------------------------------------------------------------ parts


class Part:
    """elems: [(d, fill)] in part units; base maps part units to lockup units: lockup = k * p + (bx, by)."""

    def __init__(self, pid, elems, base=(0.0, 0.0, 1.0), origin=None, window=None, stroke_w=None):
        self.id, self.elems, self.base, self.window = pid, elems, base, window
        bb = path_bbox(" ".join(d for d, _ in elems))
        bx, by, k = base
        self.bbox = (bx + bb[0] * k, by + bb[1] * k, bx + bb[2] * k, by + bb[3] * k)
        self.origin = origin or ((self.bbox[0] + self.bbox[2]) / 2, (self.bbox[1] + self.bbox[3]) / 2)
        self.stroke_w = stroke_w
        self.lengths = [path_length(d) * k for d, _ in elems]


NUM = re.compile(r"-?\d+(?:\.\d+)?(?:e-?\d+)?")


def path_bbox(d):
    nums = [float(v) for v in NUM.findall(d)]
    # A arcs carry radii/flags: treat conservatively by scanning only coordinate pairs of M/L/C/Q segments
    pts = list(iter_points(d))
    if pts:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return min(xs), min(ys), max(xs), max(ys)
    xs, ys = nums[0::2], nums[1::2]
    return min(xs), min(ys), max(xs), max(ys)


def tokenize(d):
    for m in re.finditer(r"([MLHVCQAZmlhvcqaz])|(-?\d+(?:\.\d+)?(?:e-?\d+)?)", d):
        yield m.group(1) or float(m.group(2))


def parse_path(d):
    """Absolute-command SVG path -> list of subpaths [(start, [segments], closed)], segments = ('L'|'C', pts)."""
    toks = list(tokenize(d))
    i, cmd = 0, None
    subs, cur, start, pos = [], None, None, (0.0, 0.0)

    def num():
        nonlocal i
        v = toks[i]
        i += 1
        return v

    while i < len(toks):
        if isinstance(toks[i], str):
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                if cur is not None:
                    subs.append((start, cur, True))
                    cur = None
                pos = start
                continue
        if cmd == "M":
            if cur is not None:
                subs.append((start, cur, False))
            pos = (num(), num())
            start, cur = pos, []
            cmd = "L"
        elif cmd == "L":
            p = (num(), num())
            cur.append(("L", [p]))
            pos = p
        elif cmd == "H":
            p = (num(), pos[1])
            cur.append(("L", [p]))
            pos = p
        elif cmd == "V":
            p = (pos[0], num())
            cur.append(("L", [p]))
            pos = p
        elif cmd == "C":
            c1, c2, p = (num(), num()), (num(), num()), (num(), num())
            cur.append(("C", [c1, c2, p]))
            pos = p
        elif cmd == "Q":
            q, p = (num(), num()), (num(), num())
            c1 = (pos[0] + 2 / 3 * (q[0] - pos[0]), pos[1] + 2 / 3 * (q[1] - pos[1]))
            c2 = (p[0] + 2 / 3 * (q[0] - p[0]), p[1] + 2 / 3 * (q[1] - p[1]))
            cur.append(("C", [c1, c2, p]))
            pos = p
        elif cmd == "A":
            rx, ry, phi, la, sw = num(), num(), num(), num(), num()
            p = (num(), num())
            for seg in arc_to_cubics(pos, rx, ry, phi, int(la), int(sw), p):
                cur.append(("C", seg))
            pos = p
        else:
            raise ValueError(f"unsupported path command {cmd!r} (use absolute commands)")
    if cur is not None:
        subs.append((start, cur, False))
    return subs


def iter_points(d):
    try:
        for start, segs, closed in parse_path(d):
            yield start
            for kind, pts in segs:
                yield from pts
    except (ValueError, IndexError):
        return


def arc_to_cubics(p0, rx, ry, phi, large, sweep, p1):
    if rx == 0 or ry == 0:
        return [[p0, p1, p1]]
    cphi, sphi = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    dx, dy = (p0[0] - p1[0]) / 2, (p0[1] - p1[1]) / 2
    x1p, y1p = cphi * dx + sphi * dy, -sphi * dx + cphi * dy
    rx, ry = abs(rx), abs(ry)
    lam = (x1p / rx) ** 2 + (y1p / ry) ** 2
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num_ = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    coef = math.sqrt(max(0.0, num_ / den)) * (-1 if large == sweep else 1)
    cxp, cyp = coef * rx * y1p / ry, -coef * ry * x1p / rx
    cx = cphi * cxp - sphi * cyp + (p0[0] + p1[0]) / 2
    cy = sphi * cxp + cphi * cyp + (p0[1] + p1[1]) / 2

    def ang(ux, uy, vx, vy):
        a = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        return a

    t1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dt = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dt > 0:
        dt -= 2 * math.pi
    elif sweep and dt < 0:
        dt += 2 * math.pi
    n = max(1, int(math.ceil(abs(dt) / (math.pi / 2) - 1e-9)))
    seg = dt / n
    kk = 4 / 3 * math.tan(seg / 4)
    out = []
    for j in range(n):
        a0, a1 = t1 + j * seg, t1 + (j + 1) * seg

        def pt(a):
            x, y = rx * math.cos(a), ry * math.sin(a)
            return cx + cphi * x - sphi * y, cy + sphi * x + cphi * y

        def der(a):
            x, y = -rx * math.sin(a), ry * math.cos(a)
            return cphi * x - sphi * y, sphi * x + cphi * y

        q0, q3 = pt(a0), pt(a1)
        d0, d3 = der(a0), der(a1)
        out.append([(q0[0] + kk * d0[0], q0[1] + kk * d0[1]), (q3[0] - kk * d3[0], q3[1] - kk * d3[1]), q3])
    return out


def path_length(d, steps=16):
    total = 0.0
    try:
        subs = parse_path(d)
    except (ValueError, IndexError):
        return 0.0
    for start, segs, closed in subs:
        pos = start
        for kind, pts in segs:
            if kind == "L":
                total += math.dist(pos, pts[0])
                pos = pts[0]
            else:
                prev = pos
                for s_ in range(1, steps + 1):
                    t = s_ / steps
                    mt = 1 - t
                    q = (mt ** 3 * pos[0] + 3 * mt * mt * t * pts[0][0] + 3 * mt * t * t * pts[1][0] + t ** 3 * pts[2][0],
                         mt ** 3 * pos[1] + 3 * mt * mt * t * pts[0][1] + 3 * mt * t * t * pts[1][1] + t ** 3 * pts[2][1])
                    total += math.dist(prev, q)
                    prev = q
                pos = pts[2]
        if closed:
            total += math.dist(pos, start)
    return total


# ------------------------------------------------------------------ lockup parsing

SYM_IDS = ["feather-top", "feather-mid", "feather-bot", "parcel", "facet-top", "facet-bot"]


def parse_lockup(frag):
    """Split a lockup fragment from pfbrand.logo into named parts."""
    parts = {}
    m = re.search(r'<g id="symbol"(?: transform="([^"]*)")?>(.*?)</g>', frag, re.S)
    if m:
        tx, ty, k = 0.0, 0.0, 1.0
        if m.group(1):
            t = re.search(r"translate\(([-\d.e]+) ([-\d.e]+)\)", m.group(1))
            sc = re.search(r"scale\(([-\d.e]+)\)", m.group(1))
            tx, ty = float(t.group(1)), float(t.group(2))
            k = float(sc.group(1)) if sc else 1.0
        for pid, fill, d in re.findall(r'<path id="([^"]+)" fill="([^"]+)" d="([^"]+)"/>', m.group(2)):
            parts[pid] = Part(pid, [(d, fill)], (tx, ty, k))
        frag = frag.replace(m.group(0), "")
    for pm in re.finditer(r'<path id="([^"]+)" fill="([^"]+)"(?: transform="translate\(([-\d.e]+) ([-\d.e]+)\)")? d="([^"]+)"/>', frag):
        pid, fill, tx, ty, d = pm.groups()
        parts[pid] = Part(pid, [(d, fill)], (float(tx or 0), float(ty or 0), 1.0))
    for rm in re.finditer(r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)" fill="([^"]+)"/>', frag):
        x, y, w, h, fill = rm.groups()
        x, y, w, h = float(x), float(y), float(w), float(h)
        d = f"M{fmt(x)} {fmt(y)}L{fmt(x + w)} {fmt(y)}L{fmt(x + w)} {fmt(y + h)}L{fmt(x)} {fmt(y + h)}Z"
        parts["rule"] = Part("rule", [(d, fill)])
    return parts


def letter_windows(part, pad=40.0):
    """Static x-windows around each glyph of a wordmark path (the path itself stays one compound shape)."""
    d = part.elems[0][0]
    bx, by, k = part.base
    boxes = []
    for sub in re.findall(r"M[^M]+", d):
        x0, y0, x1, y1 = path_bbox(sub)
        boxes.append([bx + x0 * k, bx + x1 * k])
    boxes.sort()
    letters = []
    for x0, x1 in boxes:
        if letters and x0 < letters[-1][1] - 1:
            letters[-1][1] = max(letters[-1][1], x1)
        else:
            letters.append([x0, x1])
    wins = []
    for i, (x0, x1) in enumerate(letters):
        left = (letters[i - 1][1] + x0) / 2 if i else x0 - pad
        right = (x1 + letters[i + 1][0]) / 2 if i < len(letters) - 1 else x1 + pad
        wins.append((left, right))
    return wins


# ------------------------------------------------------------------ animation


class Anim:
    def __init__(self, name, title, parts, duration, loop=False, extent=None, group="sign", note=""):
        self.name, self.title, self.parts, self.duration, self.loop = name, title, parts, duration, loop
        self.group, self.note = group, note
        self.tracks = {p.id: {} for p in parts}
        if extent is None:
            xs0 = [p.bbox[0] for p in parts]
            ys0 = [p.bbox[1] for p in parts]
            xs1 = [p.bbox[2] for p in parts]
            ys1 = [p.bbox[3] for p in parts]
            extent = (min(xs0), min(ys0), max(xs1), max(ys1))
        self.extent = extent

    def seg(self, pid, prop, t0, t1, v0, v1, ease=out_cubic):
        self.tracks[pid].setdefault(prop, []).append((t0, t1, v0, v1, ease))
        return self

    def value(self, pid, prop, t):
        segs = self.tracks[pid].get(prop)
        if not segs:
            return DEFAULTS[prop]
        segs = sorted(segs, key=lambda s: s[0])
        if t <= segs[0][0]:
            return segs[0][2]
        for t0, t1, v0, v1, ease in segs:
            if t0 <= t <= t1:
                u = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
                if isinstance(v0, tuple):
                    return tuple(a + (b - a) * u for a, b in zip(v0, v1))
                return v0 + (v1 - v0) * u
        last = segs[-1]
        for t0, t1, v0, v1, ease in segs:
            if t1 <= t:
                last = (t0, t1, v0, v1, ease)
        return last[3]

    def state(self, pid, t):
        return {k: self.value(pid, k, t) for k in DEFAULTS}


class Fit:
    """Lockup units -> canvas units."""

    def __init__(self, extent, w, h, fill=0.62, pad=None):
        x0, y0, x1, y1 = extent
        if pad is not None:
            ew, eh = x1 - x0, y1 - y0
            p = pad * eh
            x0, y0, x1, y1 = x0 - p, y0 - p, x1 + p, y1 + p
            self.w, self.h = w, w * (y1 - y0) / (x1 - x0)
            self.k = w / (x1 - x0)
            self.dx, self.dy = -x0 * self.k, -y0 * self.k
            return
        self.w, self.h = w, h
        self.k = min(w * fill / (x1 - x0), h * fill / (y1 - y0))
        self.dx = w / 2 - (x0 + x1) / 2 * self.k
        self.dy = h / 2 - (y0 + y1) / 2 * self.k

    def pt(self, x, y):
        return self.dx + x * self.k, self.dy + y * self.k


# ------------------------------------------------------------------ static frame


def frame_svg(anim: Anim, t, fit: Fit, bg=None):
    w, h = fit.w, fit.h
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fmt(w)} {fmt(h)}" width="{fmt(w)}" height="{fmt(h)}">']
    if bg:
        out.append(f'<rect width="{fmt(w)}" height="{fmt(h)}" fill="{bg}"/>')
    out.append(f'<g transform="translate({fit.dx:.4f} {fit.dy:.4f}) scale({fit.k:.6f})">')
    for i, p in enumerate(anim.parts):
        st = anim.state(p.id, t)
        if st["o"] <= 0.001:
            continue
        clips = []
        if p.window:
            clips.append(p.window)
        if st["clip"] is not None:
            clips.append(st["clip"])
        wrap_open, wrap_close = "", ""
        for j, (x0, x1) in enumerate(clips):
            if x1 - x0 <= 0.01:
                break
            cid = f"c{i}_{j}"
            out.append(f'<clipPath id="{cid}"><rect x="{fmt(x0)}" y="-100000" width="{fmt(x1 - x0)}" height="200000"/></clipPath>')
            wrap_open += f'<g clip-path="url(#{cid})">'
            wrap_close += "</g>"
        else:
            out.append(wrap_open + _part_body(p, st) + wrap_close)
    out.append("</g></svg>")
    return "".join(out)


def _transform(p: Part, st):
    ox, oy = p.origin
    sx, sy = st["s"] * st["sx"], st["s"] * st["sy"]
    return (f"translate({st['tx'] + ox:.4f} {st['ty'] + oy:.4f}) rotate({st['r']:.4f}) scale({sx:.6f} {sy:.6f}) "
            f"translate({-ox:.4f} {-oy:.4f})")


def _part_body(p: Part, st):
    bx, by, k = p.base
    inner = []
    for (d, fill), L_ in zip(p.elems, p.lengths):
        if st["draw"] is not None:
            sw = (p.stroke_w or 6.0) / k
            Lp = L_ / k
            off = Lp * (1 - st["draw"])
            inner.append(f'<path d="{d}" fill="{fill}" fill-opacity="{st["fo"]:.4f}" stroke="{fill}" stroke-width="{fmt(sw)}" '
                         f'stroke-linejoin="round" stroke-dasharray="{fmt(Lp)} {fmt(Lp)}" stroke-dashoffset="{fmt(off)}"/>')
        else:
            fo = f' fill-opacity="{st["fo"]:.4f}"' if st["fo"] < 0.999 else ""
            inner.append(f'<path d="{d}" fill="{fill}"{fo}/>')
    return (f'<g opacity="{st["o"]:.4f}" transform="{_transform(p, st)}"><g transform="translate({fmt(bx)} {fmt(by)}) '
            f'scale({k:.6f})">{"".join(inner)}</g></g>')


# ------------------------------------------------------------------ CSS-animated SVG


def _times(anim, fps):
    n = max(2, int(round(anim.duration * fps)))
    return [anim.duration * i / n for i in range(n + 1)]


def css_svg(anim: Anim, fit: Fit, fps=30, title=None):
    w, h = fit.w, fit.h
    times = _times(anim, fps)
    css, body, defs = [], [], []
    BIG = (-2 * w, -2 * h, 5 * w, 5 * h)   # fixed reference box for clip-path inset
    iters = "infinite" if anim.loop else "1"
    for i, p in enumerate(anim.parts):
        states = [anim.state(p.id, t) for t in times]
        ox, oy = fit.pt(*p.origin)

        def tr(st):
            sx, sy = st["s"] * st["sx"], st["s"] * st["sy"]
            return (f"translate({st['tx'] * fit.k:.3f}px,{st['ty'] * fit.k:.3f}px) rotate({st['r']:.3f}deg) "
                    f"scale({sx:.5f},{sy:.5f})")

        frames = []
        for t, st in zip(times, states):
            pct = 100 * t / anim.duration
            frames.append((pct, f"transform:{tr(st)};opacity:{st['o']:.4f}"))
        final = states[0] if anim.loop else states[-1]
        css.append(_keyframes(f"a{i}", frames))
        css.append(f".a{i}{{transform-box:view-box;transform-origin:{ox:.3f}px {oy:.3f}px;"
                   f"transform:{tr(final)};opacity:{final['o']:.4f};animation:a{i} {anim.duration}s linear {iters} both}}")
        has_clip = any(st["clip"] is not None for st in states)
        if has_clip:
            bw, bh = BIG[2], BIG[3]

            def inset(st):
                if st["clip"] is None:
                    return "inset(0 0 0 0)"
                x0, x1 = fit.pt(st["clip"][0], 0)[0], fit.pt(st["clip"][1], 0)[0]
                left = (x0 - BIG[0]) / bw * 100
                right = (BIG[0] + bw - x1) / bw * 100
                return f"inset(0 {max(0.0, right):.4f}% 0 {max(0.0, left):.4f}%)"

            cframes = [(100 * t / anim.duration, f"clip-path:{inset(st)}") for t, st in zip(times, states)]
            css.append(_keyframes(f"c{i}", cframes))
            css.append(f".c{i}{{clip-path:{inset(final)};animation:c{i} {anim.duration}s linear {iters} both}}")
        bx, by, k = p.base
        inner = []
        drawn = any(st["draw"] is not None for st in states)
        for j, ((d, fill), L_) in enumerate(zip(p.elems, p.lengths)):
            if drawn:
                sw = (p.stroke_w or 6.0) / k
                Lp = L_ / k
                dfr = [(100 * t / anim.duration,
                        f"stroke-dashoffset:{Lp * (1 - (st['draw'] if st['draw'] is not None else 1)):.3f};"
                        f"fill-opacity:{st['fo']:.4f}") for t, st in zip(times, states)]
                css.append(_keyframes(f"d{i}_{j}", dfr))
                css.append(f".d{i}_{j}{{stroke-dasharray:{Lp:.3f} {Lp:.3f};stroke-dashoffset:0;fill-opacity:1;"
                           f"animation:d{i}_{j} {anim.duration}s linear {iters} both}}")
                inner.append(f'<path class="d{i}_{j}" d="{d}" fill="{fill}" stroke="{fill}" stroke-width="{fmt(sw)}" '
                             f'stroke-linejoin="round"/>')
            else:
                inner.append(f'<path d="{d}" fill="{fill}"/>')
        g = (f'<g class="a{i}"><g transform="translate({fit.dx:.4f} {fit.dy:.4f}) scale({fit.k:.6f})">'
             f'<g transform="translate({fmt(bx)} {fmt(by)}) scale({k:.6f})">{"".join(inner)}</g></g></g>')
        if has_clip:
            g = (f'<g class="c{i}"><rect x="{fmt(BIG[0])}" y="{fmt(BIG[1])}" width="{fmt(BIG[2])}" height="{fmt(BIG[3])}" '
                 f'fill="none"/>{g}</g>')
        if p.window:
            x0, x1 = fit.pt(p.window[0], 0)[0], fit.pt(p.window[1], 0)[0]
            defs.append(f'<clipPath id="w{i}"><rect x="{fmt(x0)}" y="{fmt(-h)}" width="{fmt(x1 - x0)}" height="{fmt(3 * h)}"/></clipPath>')
            g = f'<g clip-path="url(#w{i})">{g}</g>'
        body.append(g)
    css.append("@media (prefers-reduced-motion:reduce){.pf *{animation:none!important}}")
    t = title or anim.title
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="pf" viewBox="0 0 {fmt(w)} {fmt(h)}" width="{fmt(w)}" '
            f'height="{fmt(h)}" role="img"><title>{t}</title><style>{"".join(css)}</style>'
            f'<defs>{"".join(defs)}</defs>{"".join(body)}</svg>\n')


def _keyframes(name, frames):
    out, last = [], None
    for k, (pct, decl) in enumerate(frames):
        if decl == last and k < len(frames) - 1 and frames[k + 1][1] == decl:
            continue
        out.append(f"{pct:.3f}%{{{decl}}}")
        last = decl
    return f"@keyframes {name}{{{''.join(out)}}}"


# ------------------------------------------------------------------ Lottie


def _hex_rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def _shape_from_path(d, base, fit):
    bx, by, k = base

    def tp(p):
        x, y = bx + p[0] * k, by + p[1] * k
        return [round(fit.dx + x * fit.k, 3), round(fit.dy + y * fit.k, 3)]

    shapes = []
    for start, segs, closed in parse_path(d):
        v, ins, outs = [tp(start)], [[0, 0]], [[0, 0]]
        for kind, pts in segs:
            if kind == "L":
                v.append(tp(pts[0]))
                ins.append([0, 0])
                outs.append([0, 0])
            else:
                c1, c2, p = tp(pts[0]), tp(pts[1]), tp(pts[2])
                prev = v[-1]
                outs[-1] = [round(c1[0] - prev[0], 3), round(c1[1] - prev[1], 3)]
                v.append(p)
                ins.append([round(c2[0] - p[0], 3), round(c2[1] - p[1], 3)])
                outs.append([0, 0])
        if len(v) > 1 and abs(v[-1][0] - v[0][0]) < 1e-3 and abs(v[-1][1] - v[0][1]) < 1e-3:
            ins[0] = ins[-1]
            v, ins, outs = v[:-1], ins[:-1], outs[:-1]
        shapes.append({"ty": "sh", "ks": {"a": 0, "k": {"i": ins, "o": outs, "v": v, "c": True}}})
    return shapes


def _prop(samples, frames, eps=1e-3):
    """Static or linear-keyframed Lottie property from per-frame samples (lists)."""
    if all(max(abs(a - b) for a, b in zip(s, samples[0])) < eps for s in samples):
        v = samples[0]
        return {"a": 0, "k": v if len(v) > 1 else v[0]}
    keys = []
    n = len(samples)
    for i in range(n):
        if 0 < i < n - 1:
            prev, cur, nxt = samples[i - 1], samples[i], samples[i + 1]
            if all(abs((p + q) / 2 - c) < eps for p, c, q in zip(prev, cur, nxt)):
                continue
        keys.append(i)
    out = []
    for j, i in enumerate(keys):
        kf = {"t": frames[i], "s": [round(x, 4) for x in samples[i]]}
        if j < len(keys) - 1:
            kf["i"] = {"x": [1], "y": [1]}
            kf["o"] = {"x": [0], "y": [0]}
        out.append(kf)
    return {"a": 1, "k": out}


def lottie(anim: Anim, fit: Fit, fps=30, hold=0.6):
    total = anim.duration + (0 if anim.loop else hold)
    n = int(round(total * fps))
    frames = list(range(n + 1))
    times = [min(f / fps, anim.duration) for f in frames]
    layers = []
    ind = 1
    for p in reversed(anim.parts):   # Lottie draws the first layer on top
        states = [anim.state(p.id, t) for t in times]
        ox, oy = fit.pt(*p.origin)
        ks = {
            "o": _prop([[st["o"] * 100] for st in states], frames),
            "r": _prop([[st["r"]] for st in states], frames),
            "p": _prop([[ox + st["tx"] * fit.k, oy + st["ty"] * fit.k] for st in states], frames),
            "a": {"a": 0, "k": [round(ox, 3), round(oy, 3)]},
            "s": _prop([[st["s"] * st["sx"] * 100, st["s"] * st["sy"] * 100] for st in states], frames),
        }
        groups = []
        drawn = any(st["draw"] is not None for st in states)
        for (d, fill), L_ in zip(p.elems, p.lengths):
            items = _shape_from_path(d, p.base, fit)
            col = _hex_rgb(fill) + [1]
            if drawn:
                items.append({"ty": "tm", "s": {"a": 0, "k": 0},
                              "e": _prop([[(st["draw"] if st["draw"] is not None else 1) * 100] for st in states], frames),
                              "o": {"a": 0, "k": 0}, "m": 1})
                items.append({"ty": "st", "c": {"a": 0, "k": col}, "o": {"a": 0, "k": 100},
                              "w": {"a": 0, "k": round((p.stroke_w or 6.0) * fit.k, 3)}, "lc": 2, "lj": 2})
            items.append({"ty": "fl", "c": {"a": 0, "k": col},
                          "o": _prop([[st["fo"] * 100] for st in states], frames), "r": 1})
            items.append({"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]},
                          "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}})
            groups.append({"ty": "gr", "it": items, "nm": p.id})
        layer = {"ddd": 0, "ind": ind, "ty": 4, "nm": p.id, "sr": 1, "ks": ks, "ao": 0, "shapes": groups,
                 "ip": 0, "op": n + 1, "st": 0, "bm": 0}
        # mattes: animated clip window and/or static letter window, in canvas space
        windows = []
        if any(st["clip"] is not None for st in states):
            windows.append([((fit.pt(st["clip"][0], 0)[0], fit.pt(st["clip"][1], 0)[0]) if st["clip"] else (-4 * fit.w, 5 * fit.w))
                            for st in states])
        if p.window:
            x0, x1 = fit.pt(p.window[0], 0)[0], fit.pt(p.window[1], 0)[0]
            windows.append([(x0, x1)] * len(states))
        if windows:
            if len(windows) == 2:
                windows = [[(max(a[0], b[0]), min(a[1], b[1])) for a, b in zip(*windows)]]
            win = windows[0]
            ind_m = ind + 1
            matte = {"ddd": 0, "ind": ind, "ty": 4, "nm": f"{p.id} window", "sr": 1, "td": 1, "ao": 0, "ip": 0,
                     "op": n + 1, "st": 0, "bm": 0,
                     "ks": {"o": {"a": 0, "k": 100}, "r": {"a": 0, "k": 0}, "a": {"a": 0, "k": [0, 0]},
                            "p": _prop([[x0, -fit.h] for x0, x1 in win], frames),
                            "s": _prop([[max(x1 - x0, 0.0) * 100, 3 * fit.h * 100] for x0, x1 in win], frames)},
                     "shapes": [{"ty": "gr", "nm": "window", "it": [
                         {"ty": "sh", "ks": {"a": 0, "k": {"i": [[0, 0]] * 4, "o": [[0, 0]] * 4,
                                                          "v": [[0, 0], [1, 0], [1, 1], [0, 1]], "c": True}}},
                         {"ty": "fl", "c": {"a": 0, "k": [1, 1, 1, 1]}, "o": {"a": 0, "k": 100}, "r": 1},
                         {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]},
                          "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}}]}]}
            layer["ind"] = ind_m
            layer["tt"] = 1
            layers.append(matte)
            ind = ind_m
        layers.append(layer)
        ind += 1
    return {"v": "5.7.4", "fr": fps, "ip": 0, "op": n + 1, "w": round(fit.w), "h": round(fit.h), "nm": anim.title,
            "ddd": 0, "assets": [], "layers": layers, "meta": {"g": "Parcel Fly brand kit"}}


def lottie_json(anim, fit, fps=30, hold=0.6):
    return json.dumps(lottie(anim, fit, fps, hold), separators=(",", ":"))


# ------------------------------------------------------------------ helpers for building animations


def speed_lines_part(pid, symbol_part, way):
    """Three streaks trailing to the left of the symbol's feathers (effect only)."""
    tx, ty, k = symbol_part.base
    cols = {"color": ("#0077C9", "#00318D", "#000080"), "ondark": ("#FFFFFF", "#FFFFFF", "#FFFFFF")}.get(
        way, ("#0077C9", "#00318D", "#000080"))
    h = S.FEATHER_H * 0.42
    elems = []
    for i in range(3):
        y = i * (S.FEATHER_H + S.GAP) + (S.FEATHER_H - h) / 2
        x_end = i * S.STEP - 40
        frag = LY.feather_bar(x_end - 720, y, h, 720, "square", cols[i])
        d = re.search(r' d="([^"]+)"', frag).group(1)
        elems.append((d, cols[i]))
    p = Part(pid, elems, (tx, ty, k))
    p.origin = (tx + (S.STEP - 40) * k, ty + S.CY * k)
    return p
