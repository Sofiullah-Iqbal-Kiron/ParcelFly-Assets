"""Logo lockups composed from the symbol geometry and the outlined wordmark master.

All lockups are built in logo units and returned as (fragment, bbox) where bbox = (x0, y0, x1, y1) of the ink.
The stacked lockup reproduces the production artwork's arrangement exactly; the others are derived from it.
"""
import json
import re
from functools import lru_cache

from . import MASTER
from . import symbol as S
from . import text as T
from .brand import AMBER, NAME_BN, SKY, TAGLINE, TAGLINE_BN, NAVY, CYAN, WHITE
from .text import fmt

# ------------------------------------------------------------------ wordmark (English master)


@lru_cache(maxsize=None)
def _wordmark():
    svg = (MASTER / "wordmark-en.svg").read_text(encoding="utf-8")
    d = re.search(r' d="([^"]+)"', svg).group(1)
    m = json.loads((MASTER / "wordmark-en.json").read_text(encoding="utf-8"))
    return d, m


def wm_metrics():
    return _wordmark()[1]


CAP = 168.0                       # English cap height (logo units)
BN_KEY, BN_WEIGHT = "mina-bold", None
BN_SIZE = 242.0                   # Mina Bold size whose stems match Nasalization (headline ~ cap height)
TAG_KEY, TAG_WEIGHT, TAG_TRACK = "montserrat", 600, 0.2
CLEAR = S.FEATHER_H               # clear-space unit: one feather height


def wordmark_en(fill=NAVY, x=0.0, y=0.0):
    """English wordmark with its pen origin at (x, y) on the baseline. bbox in absolute units."""
    d, m = _wordmark()
    bx0, by0, bx1, by1 = m["ink_bbox"]
    frag = f'<path id="wordmark" fill="{fill}" transform="translate({fmt(x)} {fmt(y)})" d="{d}"/>'
    return frag, (x + bx0, y + by0, x + bx1, y + by1)


@lru_cache(maxsize=None)
def _bn_bounds():
    return T.ink_bounds(NAME_BN, BN_KEY, BN_SIZE, BN_WEIGHT)


def bn_overhang(share=0.6):
    """Mina's aa-kar headline runs ~61 units left of the first letter's body. Optical spacing lets
    `share` of that thin overhang reach into the gap so the letter bodies sit where the English P sits."""
    return share * (T.ink_bounds("প", BN_KEY, BN_SIZE, BN_WEIGHT)[0] - _bn_bounds()[0])


def wordmark_bn(fill=NAVY, x=0.0, y=0.0, size=BN_SIZE):
    k = size / BN_SIZE
    bx0, by0, bx1, by1 = _bn_bounds()
    # place so that the ink starts at x (Bangla side bearings vary)
    d, _ = T.path_d(NAME_BN, BN_KEY, size, x - bx0 * k, y, weight=BN_WEIGHT)
    return f'<path id="wordmark-bn" fill="{fill}" d="{d}"/>', (x, y + by0 * k, x + (bx1 - bx0) * k, y + by1 * k)


def symbol(way="color", x=0.0, y=0.0, scale=1.0):
    t = f"translate({fmt(x)} {fmt(y)})" + (f" scale({scale:.6f})" if scale != 1 else "")
    return S.svg_group(way, t), (x, y, x + S.WIDTH * scale, y + S.HEIGHT * scale)


def union(*bbs):
    return (min(b[0] for b in bbs), min(b[1] for b in bbs), max(b[2] for b in bbs), max(b[3] for b in bbs))


# ------------------------------------------------------------------ colour helpers

def resolve(way):
    """Return (symbol colourway, wordmark colour, tagline colour) for a lockup colourway name."""
    if way == "color":
        return "color", NAVY, SKY
    if way == "ondark":
        return "ondark", WHITE, CYAN
    if way == "grey":
        return "grey", "#1A1A1A", "#6E6E6E"
    # sub-brand colourways, only on their own grounds (hub: cyan, admin: ink), see brand.ICON_SCHEMES
    if way == "hub":
        return "hub", NAVY, WHITE
    if way == "admin":
        return "admin", WHITE, AMBER
    c = {"black": "#000000", "white": "#FFFFFF"}.get(way, way)
    if not c.startswith("#"):
        from .brand import hex_of
        c = hex_of(c)
    return c, c, c


# ------------------------------------------------------------------ taglines / descriptors

def tagline_en(fill, cx, top, width):
    """Tracked caps tagline fitted to `width`, centred on cx, cap top at `top`."""
    s = TAGLINE.upper()
    size = T.fit_size(s, TAG_KEY, width, 400, TAG_WEIGHT, tracking=TAG_TRACK)
    cap = 0.70 * size
    d, adv = T.path_d(s, TAG_KEY, size, cx, top + cap, "middle", TAG_WEIGHT, tracking=TAG_TRACK)
    return f'<path id="tagline" fill="{fill}" d="{d}"/>', (cx - adv / 2, top, cx + adv / 2, top + cap)


def tagline_bn(fill, cx, top, width):
    size = T.fit_size(TAGLINE_BN, BN_KEY, width, 400, BN_WEIGHT)
    x0, y0, x1, y1 = T.ink_bounds(TAGLINE_BN, BN_KEY, size, BN_WEIGHT)
    d, adv = T.path_d(TAGLINE_BN, BN_KEY, size, cx, top - y0, "middle", BN_WEIGHT)
    return f'<path id="tagline-bn" fill="{fill}" d="{d}"/>', (cx - adv / 2, top, cx + adv / 2, top - y0 + y1)


def tagline_left(lang, fill, x, top, width):
    """Left-aligned tagline (for horizontal lockups) fitted to width."""
    if lang == "bn":
        size = T.fit_size(TAGLINE_BN, BN_KEY, width, 400, BN_WEIGHT)
        x0, y0, x1, y1 = T.ink_bounds(TAGLINE_BN, BN_KEY, size, BN_WEIGHT)
        d, adv = T.path_d(TAGLINE_BN, BN_KEY, size, x - x0, top - y0, "start", BN_WEIGHT)
        return f'<path id="tagline-bn" fill="{fill}" d="{d}"/>', (x, top, x + adv, top - y0 + y1)
    s = TAGLINE.upper()
    size = T.fit_size(s, TAG_KEY, width, 400, TAG_WEIGHT, tracking=TAG_TRACK)
    cap = 0.70 * size
    x0, _, _, _ = T.ink_bounds(s, TAG_KEY, size, TAG_WEIGHT, tracking=TAG_TRACK)
    d, adv = T.path_d(s, TAG_KEY, size, x - x0, top + cap, "start", TAG_WEIGHT, tracking=TAG_TRACK)
    return f'<path id="tagline" fill="{fill}" d="{d}"/>', (x, top, x + adv - x0, top + cap)


def descriptor(label, fill, x, top, cap_h, anchor="start"):
    """Sub-brand descriptor in tracked caps (Montserrat Bold), cap height cap_h."""
    size = cap_h / 0.70
    s = label.upper()
    x0, _, _, _ = T.ink_bounds(s, TAG_KEY, size, 700, tracking=0.16)
    if anchor == "start":
        d, adv = T.path_d(s, TAG_KEY, size, x - x0, top + cap_h, "start", 700, tracking=0.16)
        return f'<path id="descriptor" fill="{fill}" d="{d}"/>', (x, top, x + adv - x0, top + cap_h)
    d, adv = T.path_d(s, TAG_KEY, size, x, top + cap_h, "middle", 700, tracking=0.16)
    return f'<path id="descriptor" fill="{fill}" d="{d}"/>', (x - adv / 2, top, x + adv / 2, top + cap_h)


# ------------------------------------------------------------------ lockups

# Stacked (production arrangement): symbol at origin, English wordmark pen origin at (-44.814, 650.959).
STACK_WM_X, STACK_WM_Y = -44.814, 650.959


def stacked(way="color", lang="en", tagline=None, descriptor_label=None):
    sw, wc, tc = resolve(way)
    frags, bbs = [], []
    f, b = symbol(sw)
    frags.append(f); bbs.append(b)
    if lang == "en":
        f, wb = wordmark_en(wc, STACK_WM_X, STACK_WM_Y)
    else:
        # Bangla: same headline height as the English cap height, centred under the same axis
        en_frag, en_b = wordmark_en(wc, STACK_WM_X, STACK_WM_Y)
        bx0, by0, bx1, by1 = _bn_bounds()
        cx = (en_b[0] + en_b[2]) / 2
        width = bx1 - bx0
        # put the Bangla headline (matra) where the English cap top sits
        matra = -T.ink_bounds("প", BN_KEY, BN_SIZE, BN_WEIGHT)[1]
        base = STACK_WM_Y - CAP + matra
        f, wb = wordmark_bn(wc, cx - width / 2, base)
    frags.append(f); bbs.append(wb)
    wcx, wwidth = (wb[0] + wb[2]) / 2, wb[2] - wb[0]
    bottom = wb[3]
    if tagline:
        top = bottom + 0.42 * CLEAR
        if tagline == "en":
            f, tb = tagline_en(tc, wcx, top, wwidth)
        else:
            f, tb = tagline_bn(tc, wcx, top, wwidth * 0.72)
        frags.append(f); bbs.append(tb)
        bottom = tb[3]
    if descriptor_label:
        f, db = descriptor(descriptor_label, tc, wcx, bottom + 0.42 * CLEAR, 0.38 * CAP, "middle")
        frags.append(f); bbs.append(db)
    return "".join(frags), union(*bbs)


# Horizontal: symbol height = H_RATIO x cap height, centred on the cap band; gap = G_RATIO x cap.
H_RATIO = 1.75
G_RATIO = 0.40


def _text_block(lang, wc, tc, x, tagline, descriptor_label):
    """Wordmark (cap top / headline at y=0) plus optional second line, starting at x."""
    frags = []
    if lang == "en":
        d, m = _wordmark()
        f, wb = wordmark_en(wc, x - m["ink_bbox"][0], CAP)
    else:
        matra = -T.ink_bounds("প", BN_KEY, BN_SIZE, BN_WEIGHT)[1]
        f, wb = wordmark_bn(wc, x - bn_overhang(), matra)
    frags.append(f)
    bottom = None
    if tagline or descriptor_label:
        top = max(wb[3], CAP) + 0.30 * CLEAR
        if tagline:
            tx = wb[0] if lang == "en" else x          # Bangla: align to the letter bodies, not the headline tip
            f, tb = tagline_left(tagline, tc, tx, top, (wb[2] - tx) * (1 if tagline == "en" else 0.72))
        else:
            f, tb = descriptor(descriptor_label, tc, wb[0] + 3, top, 0.34 * CAP)
        frags.append(f)
        bottom = tb[3]
        return "".join(frags), union(wb, tb), bottom
    return "".join(frags), wb, bottom


def horizontal(way="color", lang="en", tagline=None, descriptor_label=None, h_ratio=H_RATIO, g_ratio=G_RATIO):
    """Symbol left, wordmark right. Without a second line the symbol is h_ratio x cap height, centred on the
    cap band; with a tagline/descriptor the symbol spans from the cap top to the bottom of the second line."""
    sw, wc, tc = resolve(way)
    gap = g_ratio * CAP
    if tagline or descriptor_label:
        _, _, bottom = _text_block(lang, wc, tc, 0, tagline, descriptor_label)
        k = bottom / S.HEIGHT
        sym_top = 0.0
    else:
        k = h_ratio * CAP / S.HEIGHT
        sym_top = CAP / 2 - S.HEIGHT * k / 2
    f_sym, b_sym = symbol(sw, 0, sym_top, k)
    frag, tb, _ = _text_block(lang, wc, tc, S.WIDTH * k + gap, tagline, descriptor_label)
    return f_sym + frag, union(b_sym, tb)


def wordmark_only(way="color", lang="en"):
    _, wc, _ = resolve(way)
    if lang == "en":
        return wordmark_en(wc, 0, 0)
    return wordmark_bn(wc, 0, 0)


def symbol_only(way="color"):
    return symbol(resolve(way)[0])


def subbrand_horizontal(label, way="color"):
    """Symbol + wordmark | divider | descriptor (one line), for app headers."""
    sw, wc, tc = resolve(way)
    frag, bb = horizontal(way)
    # wordmark cap band is y in [0, CAP]; the divider spans ascender to descender, descriptor caps = 0.72 cap
    x = bb[2] + 0.42 * CAP
    m = wm_metrics()
    rule = (f'<rect x="{fmt(x)}" y="{fmt(CAP - m["ascender_l"])}" width="{fmt(0.06 * CAP)}" '
            f'height="{fmt(m["ascender_l"] + m["descender_y"])}" fill="{tc}"/>')
    f, db = descriptor(label, tc, x + 0.06 * CAP + 0.42 * CAP, CAP * 0.28, CAP * 0.72)
    return frag + rule + f, union(bb, db)
