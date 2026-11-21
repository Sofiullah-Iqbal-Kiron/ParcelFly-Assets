"""Geometry of the Parcel Fly symbol, rebuilt from the production artwork.

Measured from the 1164 px production PNG by fitting this model to every pixel (< 1 % error per shape)
and then snapping to clean values. Units are "logo units" (1 unit = 1 px of the production PNG).

Construction
  * The parcel is a square of side 256 turned 45 deg (half-diagonal D = 128 * sqrt 2).
  * Every white channel is 26 units wide (g), measured at right angles to the edges it separates.
  * The symbol is 2 * (D + 6) tall; the three feathers share that height with two 26-unit gaps.
  * Feathers end on lines parallel to the parcel's left edges (channel g); the middle feather wraps the
    parcel's left corner. Their left tips step down a 45 deg line; their tails are quarter-ellipses
    118 units wide (the same 118 as the facet width).
  * Two facets (parallelograms, 118 wide) form the arrow head, mirrored about the horizontal axis.
"""
import math

SQRT2 = math.sqrt(2)
SIDE = 256.0
D = SIDE / SQRT2                 # 181.019 half-diagonal of the parcel
GAP = 26.0                       # channel width (perpendicular)
GX = GAP * SQRT2                 # horizontal offset between parallel 45 deg edges
HALF_H = D + 6.0                 # 187.019
HEIGHT = 2 * HALF_H              # 374.039
FEATHER_H = (HEIGHT - 2 * GAP) / 3   # 107.346
STEP = FEATHER_H + GAP           # 133.346 (45 deg stair of the feather tips)
FACET_W = 118.0
TAIL_W = 118.0
CX = 513.0                       # parcel centre x
CY = HALF_H                      # horizontal mirror axis
C1 = CX - CY + D + GX            # facet inner edge:      x - y = C1
C2 = CX + CY - D - GX            # feather upper edges:   x + y = C2
C3 = CX - CY - D - GX            # feather lower edges:   x - y = C3
FACET_BOTTOM = CY - GAP / 2
WIDTH = FACET_BOTTOM + C1 + FACET_W  # 835.789 (nose of the arrow)

# colour keys per part, resolved through a colourway
PARTS = ("feather_top", "feather_mid", "feather_bot", "parcel", "facet_top", "facet_bot")

COLOURWAYS = {
    # full colour, as in production
    "color":  {"feather_top": "#0077C9", "feather_mid": "#00318D", "feather_bot": "#000080",
               "parcel": "#00B5D8", "facet_top": "#00EAD3", "facet_bot": "#00D8DB"},
    # full colour for dark backgrounds: white wings, the parcel keeps its colours
    "ondark": {"feather_top": "#FFFFFF", "feather_mid": "#FFFFFF", "feather_bot": "#FFFFFF",
               "parcel": "#00B5D8", "facet_top": "#00EAD3", "facet_bot": "#00D8DB"},
    # greyscale with the same value steps as the colour version
    "grey":   {"feather_top": "#6E6E6E", "feather_mid": "#3A3A3A", "feather_bot": "#1A1A1A",
               "parcel": "#9C9C9C", "facet_top": "#C8C8C8", "facet_bot": "#B4B4B4"},
    # sub-brand icon colourways (only on their own tiles, see brand.ICON_SCHEMES)
    "hub":    {"feather_top": "#000080", "feather_mid": "#000080", "feather_bot": "#000080",
               "parcel": "#FFFFFF", "facet_top": "#000080", "facet_bot": "#000080"},
    "admin":  {"feather_top": "#FFFFFF", "feather_mid": "#FFFFFF", "feather_bot": "#FFFFFF",
               "parcel": "#F5A100", "facet_top": "#FFFFFF", "facet_bot": "#FFFFFF"},
}


def colourway(name: str) -> dict:
    """'color', 'ondark', 'grey' or a single colour such as '#000080' / 'navy' / 'white' / 'black'."""
    if name in COLOURWAYS:
        return COLOURWAYS[name]
    from .brand import hex_of
    named = {"black": "#000000", "white": "#FFFFFF"}
    c = named.get(name) or hex_of(name)
    return {p: c for p in PARTS}


def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _pt(x, y):
    return f"{f(x)} {f(y)}"


def part_paths() -> dict:
    """SVG path data for each part, in logo units, symbol bbox = (0, 0, WIDTH, HEIGHT)."""
    h, rx = FEATHER_H, TAIL_W
    out = {}
    out["parcel"] = f"M{_pt(CX, CY - D)}L{_pt(CX + D, CY)}L{_pt(CX, CY + D)}L{_pt(CX - D, CY)}Z"
    yb = FACET_BOTTOM
    top = [(C1, 0.0), (C1 + FACET_W, 0.0), (yb + C1 + FACET_W, yb), (yb + C1, yb)]
    out["facet_top"] = "M" + "L".join(_pt(*p) for p in top) + "Z"
    out["facet_bot"] = "M" + "L".join(_pt(x, HEIGHT - y) for x, y in top) + "Z"

    def tail(x_end, y_end, x_tip, y_tip):
        return f"L{_pt(x_end, y_end)}A{f(rx)} {f(h)} 0 0 1 {_pt(x_tip, y_tip)}Z"

    t1, b1 = 0.0, h
    out["feather_top"] = (f"M{_pt(0, t1)}L{_pt(C2 - t1, t1)}L{_pt(C2 - b1, b1)}" + tail(rx, b1, 0, t1))
    t2, b2 = h + GAP, 2 * h + GAP
    vx, vy = (C2 + C3) / 2, (C2 - C3) / 2
    out["feather_mid"] = (f"M{_pt(STEP, t2)}L{_pt(C2 - t2, t2)}L{_pt(vx, vy)}L{_pt(C3 + b2, b2)}"
                          + tail(STEP + rx, b2, STEP, t2))
    t3, b3 = 2 * h + 2 * GAP, HEIGHT
    out["feather_bot"] = (f"M{_pt(2 * STEP, t3)}L{_pt(C3 + t3, t3)}L{_pt(C3 + b3, b3)}"
                          + tail(2 * STEP + rx, b3, 2 * STEP, t3))
    return out


def polygons(n_arc: int = 48) -> dict:
    """Polygon approximations of each part (for shapely: offsets, cut lines, area checks)."""
    h, rx = FEATHER_H, TAIL_W

    def arc(cx, cy, a0, a1):
        return [(cx + rx * math.cos(a), cy + h * math.sin(a))
                for a in [a0 + (a1 - a0) * i / n_arc for i in range(n_arc + 1)]]

    yb = FACET_BOTTOM
    top = [(C1, 0.0), (C1 + FACET_W, 0.0), (yb + C1 + FACET_W, yb), (yb + C1, yb)]
    t1, b1 = 0.0, h
    t2, b2 = h + GAP, 2 * h + GAP
    t3, b3 = 2 * h + 2 * GAP, HEIGHT
    vx, vy = (C2 + C3) / 2, (C2 - C3) / 2
    return {
        "parcel": [(CX, CY - D), (CX + D, CY), (CX, CY + D), (CX - D, CY)],
        "facet_top": top,
        "facet_bot": [(x, HEIGHT - y) for x, y in top],
        # tails: ellipse centred on (tip.x + rx, tip.y), from 90 deg (bottom) to 180 deg (tip)
        "feather_top": [(0, t1), (C2 - t1, t1), (C2 - b1, b1)] + arc(rx, t1, math.pi / 2, math.pi)[:-1],
        "feather_mid": [(STEP, t2), (C2 - t2, t2), (vx, vy), (C3 + b2, b2)]
        + arc(STEP + rx, t2, math.pi / 2, math.pi)[:-1],
        "feather_bot": [(2 * STEP, t3), (C3 + t3, t3), (C3 + b3, b3)]
        + arc(2 * STEP + rx, t3, math.pi / 2, math.pi)[:-1],
    }


def svg_group(way: str = "color", transform: str = "") -> str:
    cw = colourway(way)
    paths = part_paths()
    attr = f' transform="{transform}"' if transform else ""
    body = "".join(f'<path id="{p.replace("_", "-")}" fill="{cw[p]}" d="{paths[p]}"/>' for p in PARTS)
    return f'<g id="symbol"{attr}>{body}</g>'
