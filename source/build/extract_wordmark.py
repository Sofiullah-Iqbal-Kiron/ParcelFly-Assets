"""One-time: outline the 'Parcel Fly' wordmark from Nasalization Rg into fixed master artwork.

The wordmark in production is Nasalization Rg (Typodermic), set at 248.889 px with -50/1000 em tracking
(measured from the production PNG: per-glyph fit error < 1 px). The Typodermic desktop EULA allows logos as
fixed artwork but not redistribution of the font, so the kit stores only the outlined word, never the font.

    .venv/bin/python source/build/extract_wordmark.py "/path/to/Nasalization Rg.otf"
"""
import json
import sys
from pathlib import Path

import uharfbuzz as hb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pfbrand import MASTER  # noqa: E402
from pfbrand.text import fmt  # noqa: E402

TEXT = "Parcel Fly"
SIZE = 248.888889      # logo units per em
TRACKING = -50         # font units, applied after every glyph (space included)


class Rec:
    def __init__(self, ox, s):
        self.ox, self.s, self.d = ox, s, []

    def _p(self, p):
        return f"{fmt(self.ox + p[0] * self.s)} {fmt(-p[1] * self.s)}"

    def moveTo(self, p):
        self.d.append("M" + self._p(p))

    def lineTo(self, p):
        self.d.append("L" + self._p(p))

    def curveTo(self, *pts):
        self.d.append("C" + " ".join(self._p(p) for p in pts))

    def qCurveTo(self, *pts):
        self.d.append("Q" + " ".join(self._p(p) for p in pts))

    def closePath(self):
        self.d.append("Z")

    endPath = closePath


def main(font_path):
    face = hb.Face(hb.Blob.from_file_path(font_path))
    font = hb.Font(face)
    upem = face.upem
    s = SIZE / upem
    buf = hb.Buffer()
    buf.add_str(TEXT)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True})
    pen_x, parts = 0, []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        rec = Rec(pen_x * s, s)
        font.draw_glyph_with_pen(info.codepoint, rec)
        parts.extend(rec.d)
        pen_x += pos.x_advance + TRACKING
    d = "".join(parts)
    import re
    nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", d)]
    xs, ys = nums[0::2], nums[1::2]
    ext = font.get_font_extents("ltr")
    metrics = {
        "source": "Nasalization Rg (Typodermic), outlined; tracking -0.05 em",
        "units": "logo units (1 = 1 px of the 1164 px production logo)",
        "font_size": SIZE,
        "baseline": 0,
        "cap_height": 675 * s, "x_height": 528 * s, "ascender_l": 757 * s, "descender_y": 212 * s,
        "ink_bbox": [min(xs), min(ys), max(xs), max(ys)],
        "advance": (pen_x - TRACKING) * s,
        "font_extents": [ext.ascender * s, ext.descender * s],
    }
    MASTER.mkdir(parents=True, exist_ok=True)
    x0, y0, x1, y1 = metrics["ink_bbox"]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{fmt(x0)} {fmt(y0)} {fmt(x1 - x0)} {fmt(y1 - y0)}">'
           f'<title>Parcel Fly wordmark (outlined master)</title>'
           f'<path id="wordmark" fill="#000080" d="{d}"/></svg>\n')
    (MASTER / "wordmark-en.svg").write_text(svg, encoding="utf-8")
    (MASTER / "wordmark-en.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print("wrote", MASTER / "wordmark-en.svg", metrics["ink_bbox"])


if __name__ == "__main__":
    main(sys.argv[1])
