"""Text to outlined SVG paths with HarfBuzz shaping (correct Bangla conjuncts, kerning, variable fonts)."""
from functools import lru_cache

import uharfbuzz as hb

from . import FONTS

FONT_FILES = {
    "montserrat": FONTS / "montserrat" / "Montserrat[wght].ttf",
    "montserrat-italic": FONTS / "montserrat" / "Montserrat-Italic[wght].ttf",
    "noto-bengali": FONTS / "notosansbengali" / "NotoSansBengali[wdth,wght].ttf",
    "geist-mono": FONTS / "geistmono" / "GeistMono[wght].ttf",
    "mina": FONTS / "mina" / "Mina-Regular.ttf",
    "mina-bold": FONTS / "mina" / "Mina-Bold.ttf",
}


def fmt(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


@lru_cache(maxsize=None)
def _face(key: str):
    blob = hb.Blob.from_file_path(str(FONT_FILES[key]))
    return hb.Face(blob)


@lru_cache(maxsize=None)
def _font(key: str, var: tuple):
    font = hb.Font(_face(key))
    if var:
        font.set_variations(dict(var))
    return font


def upem(key: str) -> int:
    return _face(key).upem


class _Recorder:
    """Pen recording glyph outlines in font units."""

    def __init__(self):
        self.ops = []

    def moveTo(self, p):
        self.ops.append(("M", p))

    def lineTo(self, p):
        self.ops.append(("L", p))

    def curveTo(self, *pts):
        self.ops.append(("C", pts))

    def qCurveTo(self, *pts):
        self.ops.append(("Q", pts))

    def closePath(self):
        self.ops.append(("Z", None))

    endPath = closePath


@lru_cache(maxsize=None)
def _glyph_ops(key: str, var: tuple, gid: int):
    rec = _Recorder()
    _font(key, var).draw_glyph_with_pen(gid, rec)
    return tuple(rec.ops)


def _var(weight=None, width=None):
    v = []
    if weight is not None:
        v.append(("wght", float(weight)))
    if width is not None:
        v.append(("wdth", float(width)))
    return tuple(v)


BENGALI_FONTS = {"noto-bengali", "mina", "mina-bold"}
BN_FALLBACK = "noto-bengali"


def _is_bn(ch):
    o = ord(ch)
    return 0x0980 <= o <= 0x09FF or o in (0x200C, 0x200D, 0x0964, 0x0965)


def _runs(text, key):
    """Split text into (substring, font key) runs: Bangla runs fall back to Noto Sans Bengali when the primary
    font is Latin-only. Spaces and punctuation stay with the run they sit in."""
    if key in BENGALI_FONTS or not any(_is_bn(c) for c in text):
        return [(text, key)]
    runs, cur, cur_bn = [], "", None
    for ch in text:
        bn = _is_bn(ch) if not (ch.isspace() or ch in ",.·-:;()!?") else cur_bn
        if cur and bn != cur_bn:
            runs.append((cur, BN_FALLBACK if cur_bn else key))
            cur = ""
        cur += ch
        cur_bn = bn
    if cur:
        runs.append((cur, BN_FALLBACK if cur_bn else key))
    return runs


def _shape_run(text, key, size, var, tracking, features, x0):
    font = _font(key, var)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features or {"kern": True, "liga": True})
    scale = size / upem(key)
    infos, poss = buf.glyph_infos, buf.glyph_positions
    missing = [text[i.cluster] for i in infos if i.codepoint == 0 and not text[i.cluster].isspace()]
    if missing:
        raise ValueError(f"font '{key}' has no glyph for {''.join(sorted(set(missing)))!r} in {text!r}")
    out, x = [], x0
    track = tracking * size
    for i, (info, pos) in enumerate(zip(infos, poss)):
        out.append((key, var, scale, info.codepoint, x + pos.x_offset * scale, pos.y_offset * scale))
        x += pos.x_advance * scale
        if i < len(infos) - 1 and infos[i + 1].cluster != info.cluster:
            x += track
    return out, x


def shape(text: str, key: str, size: float, weight=None, width=None, tracking: float = 0.0, features=None):
    """Return (glyphs, advance): glyphs = [(font key, variations, scale, gid, x, y)] in px, y up, origin at the
    pen start. Mixed English/Bangla strings are shaped run by run with font fallback."""
    if not text:
        return [], 0.0
    out, x = [], 0.0
    runs = _runs(text, key)
    for j, (run, k) in enumerate(runs):
        var = _var(weight, width) if k == key else _var(min(900, max(100, weight or 400)), None)
        g, x = _shape_run(run, k, size, var, tracking, features, x)
        out.extend(g)
        if j < len(runs) - 1:
            x += tracking * size
    return out, x


def _emit(parts, key, var, gid, scale, ox, oy):
    for op, pts in _glyph_ops(key, var, gid):
        if op == "Z":
            parts.append("Z")
        elif op in ("M", "L"):
            parts.append(f"{op}{fmt(ox + pts[0] * scale)} {fmt(oy - pts[1] * scale)}")
        elif op == "C":
            parts.append("C" + " ".join(f"{fmt(ox + px * scale)} {fmt(oy - py * scale)}" for px, py in pts))
        elif op == "Q":
            # TrueType quadratic splines may carry several off-curve points (implied on-curve midpoints)
            *offs, end = list(pts)
            for j in range(len(offs)):
                c = offs[j]
                e = end if j == len(offs) - 1 else ((offs[j][0] + offs[j + 1][0]) / 2, (offs[j][1] + offs[j + 1][1]) / 2)
                parts.append(f"Q{fmt(ox + c[0] * scale)} {fmt(oy - c[1] * scale)} "
                             f"{fmt(ox + e[0] * scale)} {fmt(oy - e[1] * scale)}")


def path_d(text: str, key: str, size: float, x: float = 0.0, y: float = 0.0, anchor: str = "start",
           weight=None, width=None, tracking: float = 0.0, features=None):
    """Outlined text as SVG path data. (x, y) is the baseline point given by anchor (start|middle|end)."""
    glyphs, adv = shape(text, key, size, weight, width, tracking, features)
    if anchor == "middle":
        x -= adv / 2
    elif anchor == "end":
        x -= adv
    parts = []
    for k, var, scale, gid, gx, gy in glyphs:
        _emit(parts, k, var, gid, scale, x + gx, y - gy)
    return "".join(parts), adv


def advance(text: str, key: str, size: float, weight=None, width=None, tracking: float = 0.0) -> float:
    return shape(text, key, size, weight, width, tracking)[1]


def text(text_: str, key: str, size: float, x: float = 0.0, y: float = 0.0, fill: str = "#000",
         anchor: str = "start", weight=None, width=None, tracking: float = 0.0, opacity=None, extra: str = ""):
    """Outlined text as a <path> element."""
    d, _ = path_d(text_, key, size, x, y, anchor, weight, width, tracking)
    op = f' fill-opacity="{opacity}"' if opacity is not None else ""
    return f'<path fill="{fill}"{op}{extra} d="{d}"/>' if d else ""


def fit_size(text_: str, key: str, max_width: float, max_size: float, weight=None, width=None,
             tracking: float = 0.0) -> float:
    """Largest size <= max_size so that the text fits max_width."""
    a = advance(text_, key, max_size, weight, width, tracking)
    return max_size if a <= max_width else max_size * max_width / a


def wrap(text_: str, key: str, size: float, max_width: float, weight=None, width=None, tracking=0.0):
    words, lines, cur = text_.split(), [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if cur and advance(cand, key, size, weight, width, tracking) > max_width:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


@lru_cache(maxsize=4096)
def ink_bounds(text_: str, key: str, size: float, weight=None, width=None, tracking: float = 0.0):
    """Exact (xmin, ymin, xmax, ymax) of the outlined text with baseline at y=0 (SVG y-down)."""
    from fontTools.misc.bezierTools import calcCubicBounds, calcQuadraticBounds
    glyphs, adv = shape(text_, key, size, weight, width, tracking)
    xs0, ys0, xs1, ys1 = [], [], [], []
    for k, var, scale, gid, gx, gy in glyphs:
        cur = None
        for op, pts in _glyph_ops(k, var, gid):
            if op == "M" or op == "L":
                bx = (pts[0], pts[1], pts[0], pts[1])
                if op == "L" and cur:
                    bx = (min(cur[0], pts[0]), min(cur[1], pts[1]), max(cur[0], pts[0]), max(cur[1], pts[1]))
                cur = pts
            elif op == "C":
                bx = calcCubicBounds(cur, *pts)
                cur = pts[-1]
            elif op == "Q":
                offs, end = list(pts[:-1]), pts[-1]
                seg_start, bxs = cur, []
                for j, c in enumerate(offs):
                    e = end if j == len(offs) - 1 else ((offs[j][0] + offs[j + 1][0]) / 2,
                                                         (offs[j][1] + offs[j + 1][1]) / 2)
                    bxs.append(calcQuadraticBounds(seg_start, c, e))
                    seg_start = e
                bx = (min(b[0] for b in bxs), min(b[1] for b in bxs), max(b[2] for b in bxs), max(b[3] for b in bxs))
                cur = end
            else:
                continue
            xs0.append(gx + bx[0] * scale); xs1.append(gx + bx[2] * scale)
            ys0.append(-gy - bx[3] * scale); ys1.append(-gy - bx[1] * scale)
    if not xs0:
        return 0.0, 0.0, 0.0, 0.0
    return min(xs0), min(ys0), max(xs1), max(ys1)
