"""Shared export helpers: wrap a fragment into a standalone SVG and write all formats."""
from pathlib import Path

from .svg import Doc
from .text import fmt

DARK_BG = "#000080"


def fragment_doc(frag, bb, title, pad=0.0, bg=None, unit="px", scale=1.0):
    """Standalone doc with the fragment's ink box (plus pad on each side) as the canvas, origin at 0,0."""
    x0, y0, x1, y1 = bb
    w, h = (x1 - x0 + 2 * pad) * scale, (y1 - y0 + 2 * pad) * scale
    doc = Doc(w, h, unit=unit, title=title, bg=bg)
    t = f"translate({fmt((pad - x0) * scale)} {fmt((pad - y0) * scale)})" + (f" scale({scale:.6f})" if scale != 1 else "")
    doc.add(f'<g transform="{t}">{frag}</g>')
    return doc


def export_logo(frag, bb, out_base: Path, title, way, png_widths=(600, 1200, 2400), vector=True, jpg=True):
    """SVG (+PDF/EPS) at logo-unit size, PNGs at several widths, JPG on the intended background."""
    doc = fragment_doc(frag, bb, title)
    outs = doc.save(out_base.with_suffix(".svg"), png=png_widths, pdf=vector, eps=vector)
    if jpg:
        pad = 0.12 * max(bb[2] - bb[0], bb[3] - bb[1])
        bg = DARK_BG if way in ("ondark", "white") else "#FFFFFF"
        jdoc = fragment_doc(frag, bb, title, pad=pad, bg=bg)
        from .svg import render_jpg
        p = out_base.with_name(out_base.name + "-on-" + ("navy" if bg == DARK_BG else "white") + ".jpg")
        render_jpg(jdoc.svg(), p, 2000, jdoc.w, jdoc.h, bg)
        outs.append(p)
    return outs
