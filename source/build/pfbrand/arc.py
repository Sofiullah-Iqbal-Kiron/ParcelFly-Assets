"""Text on a circle (outlined glyphs), for seals, stamps and round stickers.

Glyphs are grouped by shaping cluster so Bangla vowel signs, reph and conjunct parts rotate together with
their base consonant (Latin text is one glyph per cluster)."""
import math

from . import text as T
from .text import fmt


def _glyph_d(key, var, gid, scale, ox=0.0, oy=0.0):
    parts = []
    for op, pts in T._glyph_ops(key, var, gid):
        if op == "Z":
            parts.append("Z")
        elif op in ("M", "L"):
            parts.append(f"{op}{fmt(ox + pts[0] * scale)} {fmt(oy - pts[1] * scale)}")
        elif op == "C":
            parts.append("C" + " ".join(f"{fmt(ox + px * scale)} {fmt(oy - py * scale)}" for px, py in pts))
        elif op == "Q":
            pts = list(pts)
            *offs, end = pts
            for j, c in enumerate(offs):
                e = end if j == len(offs) - 1 else ((offs[j][0] + offs[j + 1][0]) / 2, (offs[j][1] + offs[j + 1][1]) / 2)
                parts.append(f"Q{fmt(ox + c[0] * scale)} {fmt(oy - c[1] * scale)} "
                             f"{fmt(ox + e[0] * scale)} {fmt(oy - e[1] * scale)}")
    return "".join(parts)


def _clusters(s, key, size, weight, tracking):
    """[(path_d in cluster-local coords, advance)]"""
    import uharfbuzz as hb
    var = T._var(weight, None)
    font = T._font(key, var)
    buf = hb.Buffer()
    buf.add_str(s)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True})
    scale = size / T.upem(key)
    infos, poss = buf.glyph_infos, buf.glyph_positions
    missing = [s[i.cluster] for i in infos if i.codepoint == 0 and not s[i.cluster].isspace()]
    if missing:
        raise ValueError(f"font '{key}' has no glyph for {''.join(sorted(set(missing)))!r} in {s!r}")
    groups, cur, cur_cl = [], [], None
    for info, pos in zip(infos, poss):
        if cur and info.cluster != cur_cl:
            groups.append(cur)
            cur = []
        cur.append((info.codepoint, pos))
        cur_cl = info.cluster
    if cur:
        groups.append(cur)
    out = []
    track = tracking * size
    for gi, g in enumerate(groups):
        x, parts = 0.0, []
        for gid, pos in g:
            parts.append(_glyph_d(key, var, gid, scale, x + pos.x_offset * scale, -pos.y_offset * scale))
            x += pos.x_advance * scale
        out.append(("".join(parts), x + (track if gi < len(groups) - 1 else 0)))
    return out


def arc_text(s, key, size, cx, cy, r, position="top", fill="#000", weight=None, tracking=0.0, centre_deg=None):
    """Outlined text along a circle of radius r (the baseline).
    top: reads clockwise over the top, letters point outward. bottom: reads left to right along the bottom,
    letters point toward the centre (both stay upright to the reader)."""
    cl = _clusters(s, key, size, weight, tracking)
    total = sum(a for _, a in cl) / r
    out = []
    if position == "top":
        theta = math.radians(centre_deg if centre_deg is not None else -90) - total / 2
        for d, a in cl:
            mid = theta + (a / 2) / r
            px, py = cx + r * math.cos(mid), cy + r * math.sin(mid)
            if d:
                out.append(f'<path fill="{fill}" transform="translate({fmt(px)} {fmt(py)}) '
                           f'rotate({math.degrees(mid) + 90:.3f}) translate({fmt(-a / 2)} 0)" d="{d}"/>')
            theta += a / r
    else:
        theta = math.radians(centre_deg if centre_deg is not None else 90) + total / 2
        for d, a in cl:
            mid = theta - (a / 2) / r
            px, py = cx + r * math.cos(mid), cy + r * math.sin(mid)
            if d:
                out.append(f'<path fill="{fill}" transform="translate({fmt(px)} {fmt(py)}) '
                           f'rotate({math.degrees(mid) - 90:.3f}) translate({fmt(-a / 2)} 0)" d="{d}"/>')
            theta -= a / r
    return "".join(out)


def arc_span_deg(s, key, size, r, weight=None, tracking=0.0):
    return math.degrees(sum(a for _, a in _clusters(s, key, size, weight, tracking)) / r)


def fit_arc_size(s, key, r, max_deg, max_size, weight=None, tracking=0.0):
    """Largest size <= max_size whose arc spans at most max_deg."""
    span = arc_span_deg(s, key, max_size, r, weight, tracking)
    return max_size if span <= max_deg else max_size * max_deg / span
