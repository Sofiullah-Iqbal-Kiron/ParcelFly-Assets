"""Background scenes and patterns shared by social, print and guideline layouts."""
import math

from . import layout as LY
from . import symbol as S
from .brand import CLOUD, COBALT, CYAN, MIST, MINT, NAVY, SKY, WHITE
from .svg import Doc
from .text import fmt

_uid = [0]


def uid(prefix="g"):
    _uid[0] += 1
    return f"{prefix}{_uid[0]}"


def gradient_bg(doc: Doc, stops, angle=0, x=0, y=0, w=None, h=None):
    gid = uid("lg")
    doc.defs_add(LY.flight_gradient(gid, angle, stops))
    doc.rect(x, y, w or doc.w, h or doc.h, f"url(#{gid})")


def glow(doc: Doc, cx, cy, r, colour, opacity=0.45):
    gid = uid("gl")
    doc.defs_add(LY.glow(gid, colour, opacity))
    doc.add(f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r)}" fill="url(#{gid})"/>')


def watermark(way, x, y, height, opacity=1.0, crop=None):
    """Symbol of a given height at (x, y) = top-left; one colour or colourway."""
    k = height / S.HEIGHT
    op = f' opacity="{opacity}"' if opacity < 1 else ""
    return f'<g transform="translate({fmt(x)} {fmt(y)}) scale({k:.6f})"{op}>{S.svg_group(way)}</g>'


def lattice(doc: Doc, colour=MIST, opacity=1.0, cell=64, r=0.16, x=0, y=0, w=None, h=None, outline=False):
    """Staggered grid of small parcels (diamonds), as an SVG <pattern>."""
    pid = uid("pt")
    hd = cell * r
    d1 = LY.diamond_path(cell / 2, cell / 2, hd)
    d2 = LY.diamond_path(0, 0, hd) + LY.diamond_path(cell, 0, hd) + LY.diamond_path(0, cell, hd) + LY.diamond_path(cell, cell, hd)
    paint = (f'fill="none" stroke="{colour}" stroke-width="{fmt(cell * 0.03)}"' if outline else f'fill="{colour}"')
    doc.defs_add(f'<pattern id="{pid}" width="{fmt(cell)}" height="{fmt(cell)}" patternUnits="userSpaceOnUse">'
                 f'<path d="{d1}{d2}" {paint}/></pattern>')
    op = f' opacity="{opacity}"' if opacity < 1 else ""
    doc.add(f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w or doc.w)}" height="{fmt(h or doc.h)}" fill="url(#{pid})"{op}/>')


def chevron_trail(x, y, height, n=3, fills=None, step=None, opacity=None):
    """A trail of facet chevrons (>>>) pointing right."""
    fills = fills or [(COBALT, COBALT), (SKY, SKY), (MINT, CYAN)]
    step = step or LY.chevron_width(height) * 0.62
    out = []
    for i in range(n):
        f = fills[i % len(fills)]
        out.append(LY.chevron(x + i * step, y, height, f, opacity))
    return "".join(out)
