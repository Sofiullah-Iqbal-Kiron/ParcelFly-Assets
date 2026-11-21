"""Tiny SVG document builder plus rendering to PNG / JPG / PDF / EPS (cairosvg)."""
import io
from html import escape
from pathlib import Path

import cairosvg
from PIL import Image

from .text import fmt


class Doc:
    """An SVG document. width/height are the canvas size in user units; `unit` sets physical size
    for print ('mm') or leaves pixels ('px')."""

    def __init__(self, width: float, height: float, unit: str = "px", title: str = "", bg: str | None = None):
        self.w, self.h, self.unit, self.title = width, height, unit, title
        self.defs: list[str] = []
        self.body: list[str] = []
        if bg:
            self.rect(0, 0, width, height, bg)

    # -- primitives
    def add(self, *els: str):
        self.body.extend(e for e in els if e)
        return self

    def defs_add(self, *els: str):
        self.defs.extend(els)
        return self

    def rect(self, x, y, w, h, fill, rx=0, extra=""):
        r = f' rx="{fmt(rx)}"' if rx else ""
        self.body.append(f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}"{r} fill="{fill}"{extra}/>')
        return self

    def circle(self, cx, cy, r, fill, extra=""):
        self.body.append(f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r)}" fill="{fill}"{extra}/>')
        return self

    def path(self, d, fill, extra=""):
        self.body.append(f'<path d="{d}" fill="{fill}"{extra}/>')
        return self

    def place(self, inner: str, x=0.0, y=0.0, scale=1.0, extra=""):
        """Place a fragment (in its own units) at (x, y) scaled uniformly."""
        t = f"translate({fmt(x)} {fmt(y)})" + (f" scale({scale:.6f})" if scale != 1 else "")
        self.body.append(f'<g transform="{t}"{extra}>{inner}</g>')
        return self

    def svg(self) -> str:
        u = "" if self.unit == "px" else self.unit
        title = f"<title>{escape(self.title)}</title>" if self.title else ""
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                f'viewBox="0 0 {fmt(self.w)} {fmt(self.h)}" width="{fmt(self.w)}{u}" height="{fmt(self.h)}{u}" '
                f'role="img">{title}{defs}{"".join(self.body)}</svg>\n')

    def save(self, path, png=None, jpg=None, pdf=False, eps=False, jpg_bg="#FFFFFF"):
        """Write the SVG and any renders. png/jpg: list of output widths in px (or None)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.svg()
        path.write_text(data, encoding="utf-8")
        outs = [path]
        png = list(png or [])
        for wpx in png:
            # one size -> name.png; several sizes -> name-<width>.png
            p = path.with_suffix(".png") if len(png) == 1 else path.with_name(f"{path.stem}-{wpx}.png")
            render_png(data, p, wpx, self.w, self.h)
            outs.append(p)
        for wpx in jpg or []:
            p = path.with_suffix(".jpg") if len(jpg) == 1 else path.with_name(f"{path.stem}-{wpx}.jpg")
            render_jpg(data, p, wpx, self.w, self.h, jpg_bg)
            outs.append(p)
        if pdf:
            p = path.with_suffix(".pdf")
            cairosvg.svg2pdf(bytestring=data.encode(), write_to=str(p))
            outs.append(p)
        if eps:
            p = path.with_suffix(".eps")
            cairosvg.svg2eps(bytestring=data.encode(), write_to=str(p))
            outs.append(p)
        return outs


def render_png(svg_data: str, out, width_px=None, w=None, h=None):
    kw = {}
    if width_px:
        kw["output_width"] = int(round(width_px))
        if w and h:
            kw["output_height"] = int(round(width_px * h / w))
    cairosvg.svg2png(bytestring=svg_data.encode(), write_to=str(out), **kw)


def render_jpg(svg_data: str, out, width_px=None, w=None, h=None, bg="#FFFFFF", quality=92):
    kw = {}
    if width_px:
        kw["output_width"] = int(round(width_px))
        if w and h:
            kw["output_height"] = int(round(width_px * h / w))
    png = cairosvg.svg2png(bytestring=svg_data.encode(), **kw)
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    base = Image.new("RGBA", im.size, bg)
    base.alpha_composite(im)
    base.convert("RGB").save(out, "JPEG", quality=quality, optimize=True, progressive=True)


def png_image(svg_data: str, width_px: int, w=None, h=None) -> Image.Image:
    kw = {"output_width": int(width_px)}
    if w and h:
        kw["output_height"] = int(round(width_px * h / w))
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg_data.encode(), **kw))).convert("RGBA")


def linear_gradient(gid, stops, x1=0, y1=0, x2=1, y2=0, units="objectBoundingBox"):
    s = "".join(f'<stop offset="{fmt(o)}" stop-color="{c}"{"" if a is None else f" stop-opacity={chr(34)}{a}{chr(34)}"}/>'
                for o, c, a in [(st + (None,))[:3] for st in stops])
    return (f'<linearGradient id="{gid}" gradientUnits="{units}" x1="{fmt(x1)}" y1="{fmt(y1)}" '
            f'x2="{fmt(x2)}" y2="{fmt(y2)}">{s}</linearGradient>')


def radial_gradient(gid, stops, cx=0.5, cy=0.5, r=0.5, units="objectBoundingBox"):
    s = "".join(f'<stop offset="{fmt(o)}" stop-color="{c}"{"" if a is None else f" stop-opacity={chr(34)}{a}{chr(34)}"}/>'
                for o, c, a in [(st + (None,))[:3] for st in stops])
    return f'<radialGradient id="{gid}" gradientUnits="{units}" cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r)}">{s}</radialGradient>'
