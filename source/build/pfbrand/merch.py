"""Merchandise artwork (mm): mug wraps, paper cup wraps, A5 diary covers and pages, pen barrel prints."""
import math

import numpy as np
from PIL import Image

from . import layout as LY
from . import scenes as SC
from . import symbol as S
from . import text as T
from .bags import vertical_text
from .brand import CLOUD, CONTACT, COBALT, CYAN, MINT, MIST, NAVY, SKY, SLATE, TAGLINE, TAGLINE_BN, WHITE
from .svg import Doc, png_image
from .text import fmt

MUG = (216.0, 89.0)            # 11 oz sublimation template
CUP = {"top": 90.0, "bottom": 60.0, "height": 110.0}   # 12 oz paper cup
DIARY = (148.0, 210.0, 16.0)   # A5 hardcover, spine 16 mm
PEN = (50.0, 8.0)              # barrel print area


def _doc(w, h, bg, title):
    d = Doc(w, h, unit="mm", title=title)
    d.rect(0, 0, w, h, bg)
    return d


# ------------------------------------------------------------------ mugs (wrap is seen half at a time: design both halves)

def mug_wrap(design):
    """Each half is designed for the side that shows: centred on the quarter points, inside ~58 mm (the band that
    reads well on an 82 mm mug)."""
    W, H = MUG
    q1, q3 = W * 0.25, W * 0.75
    if design == "signature":
        d = _doc(W, H, WHITE, "Parcel Fly mug wrap: signature")
        frag, _ = LY.place_logo("stacked", "color", q1 - 29, H * 0.15, w=58, h=H * 0.7, align="center", valign="middle")
        d.add(frag)
        size = 7.6
        b0, b1, b2, b3 = T.ink_bounds(TAGLINE_BN, "mina-bold", size)
        d.add(T.text(TAGLINE_BN, "mina-bold", size, q3, H * 0.47 - (b1 + b3) / 2, NAVY, "middle"))
        d.add(LY.label(TAGLINE, q3, H * 0.47 + 10, 3.0, SKY, "middle", tracking=0.2))
        return d
    if design == "navy":
        d = _doc(W, H, NAVY, "Parcel Fly mug wrap: navy")
        SC.glow(d, q1, H * 0.4, H * 1.2, COBALT, 0.8)
        d.add(LY.speed_lines(-W * 0.05, H * 0.62, H * 0.22, W * 0.14, (SKY, COBALT, CYAN), opacity=0.55))
        frag, _ = LY.place_logo("horizontal", "ondark", q1 - 29, H * 0.25, w=58, h=H * 0.5, align="center",
                                valign="middle")
        d.add(frag)
        d.add(LY.symbol_at("ondark", q3, H * 0.42, 50))
        d.add(LY.label(TAGLINE, q3, H * 0.78, 3.0, CYAN, "middle", tracking=0.2))
        return d
    if design == "bangla":
        d = _doc(W, H, CLOUD, "Parcel Fly mug wrap: Bangla")
        SC.lattice(d, MIST, cell=9)
        size = 7.6
        b0, b1, b2, b3 = T.ink_bounds(TAGLINE_BN, "mina-bold", size)
        for cx in (q1, q3):
            d.add(LY.symbol_at("color", cx, H * 0.33, 40))
            d.add(T.text(TAGLINE_BN, "mina-bold", size, cx, H * 0.6 - b1, NAVY, "middle"))
            frag, _ = LY.place_logo("wordmark", SKY, cx - 17, H * 0.8, w=34, align="center")
            d.add(frag)
        return d
    raise KeyError(design)


# ------------------------------------------------------------------ paper cups (rectangular art + conical fan template)

def cup_wrap(design):
    """Rectangular wrap artwork (circumference at mid height x height)."""
    mid = math.pi * (CUP["top"] + CUP["bottom"]) / 2
    W, H = mid, CUP["height"]
    if design == "white":
        d = _doc(W, H, WHITE, "Parcel Fly cup wrap: white")
        gid = SC.uid("cw")
        d.defs_add(LY.flight_gradient(gid))
        d.rect(0, H * 0.86, W, H * 0.14, f"url(#{gid})")
        for cx in (W * 0.25, W * 0.75):
            frag, _ = LY.place_logo("stacked", "color", cx - W * 0.16, H * 0.2, w=W * 0.32, h=H * 0.55, align="center",
                                    valign="middle")
            d.add(frag)
        return d
    if design == "navy":
        d = _doc(W, H, NAVY, "Parcel Fly cup wrap: navy")
        SC.lattice(d, COBALT, cell=10)
        b0, b1, b2, b3 = T.ink_bounds(TAGLINE_BN, "mina-bold", 10)
        for cx in (W * 0.25, W * 0.75):
            d.add(LY.symbol_at("ondark", cx, H * 0.38, W * 0.26))
            d.add(T.text(TAGLINE_BN, "mina-bold", 10, cx, H * 0.62 - b1, WHITE, "middle"))
            d.add(LY.label("Parcel Fly", cx, H * 0.86, 3.6, CYAN, "middle", tracking=0.2))
        return d
    raise KeyError(design)


def cup_fan(art_img, px_per_mm=6):
    """Warp rectangular cup art into the printable fan (annular sector) of a truncated cone."""
    D, d_, h = CUP["top"], CUP["bottom"], CUP["height"]
    slant = math.hypot(h, (D - d_) / 2)
    R = slant * D / (D - d_)
    r = R - slant
    ang = math.pi * D / R
    W = int(2 * R * math.sin(ang / 2) * px_per_mm) + 20
    Hh = int((R - r * math.cos(ang / 2)) * px_per_mm) + 20
    cx, cy = W / 2, 10 + R * px_per_mm
    yy, xx = np.mgrid[0:Hh, 0:W]
    dx, dy = (xx - cx) / px_per_mm, (cy - yy) / px_per_mm
    rad = np.hypot(dx, dy)
    th = np.arctan2(dx, dy)
    a = np.asarray(art_img.convert("RGBA"))
    u = (th + ang / 2) / ang * (a.shape[1] - 1)
    v = (R - rad) / slant * (a.shape[0] - 1)
    inside = (rad >= r) & (rad <= R) & (np.abs(th) <= ang / 2)
    ui = np.clip(u, 0, a.shape[1] - 1).astype(int)
    vi = np.clip(v, 0, a.shape[0] - 1).astype(int)
    out = np.zeros((Hh, W, 4), np.uint8)
    out[inside] = a[vi[inside], ui[inside]]
    return Image.fromarray(out, "RGBA")


# ------------------------------------------------------------------ diary

def diary_cover(design):
    """Full cover flat: back | spine | front, plus 15 mm turn-in around (hardcover case wrap)."""
    W, H, SP = DIARY
    turn = 15.0
    total_w, total_h = 2 * W + SP + 2 * turn, H + 2 * turn
    if design == "navy":
        d = _doc(total_w, total_h, NAVY, "Parcel Fly A5 diary cover: navy")
        x_front = turn + W + SP
        SC.glow(d, x_front + W * 0.8, turn, W, COBALT, 0.7)
        SC.lattice(d, COBALT, cell=12, x=turn, y=turn, w=W, h=H, opacity=0.9)
        d.add(LY.symbol_at("ondark", x_front + W / 2, turn + H * 0.42, W * 0.6))
        frag, _ = LY.place_logo("wordmark", WHITE, x_front + W * 0.3, turn + H * 0.86, w=W * 0.4, align="center")
        d.add(frag)
        d.add(vertical_text("PARCEL FLY", "montserrat", 5.5, turn + W + SP / 2, turn + H / 2, WHITE, 800, rot=90))
        frag, _ = LY.place_logo("horizontal", "ondark", turn + W * 0.25, turn + H * 0.45, w=W * 0.5, align="center")
        d.add(frag)
        d.add(T.text(CONTACT["web"], "montserrat", 4, turn + W / 2, turn + H * 0.58, WHITE, "middle", 700))
        return d
    if design == "white":
        d = _doc(total_w, total_h, WHITE, "Parcel Fly A5 diary cover: white")
        x_front = turn + W + SP
        gid = SC.uid("dg")
        d.defs_add(LY.flight_gradient(gid, 90))
        d.rect(x_front - SP, 0, SP, total_h, f"url(#{gid})")
        d.rect(0, total_h - turn - H * 0.12, total_w, H * 0.12 + turn, f"url(#{gid})")
        frag, _ = LY.place_logo("stacked", "color", x_front + W * 0.2, turn + H * 0.25, w=W * 0.6, align="center", tagline="en")
        d.add(frag)
        d.add(vertical_text("PARCEL FLY", "montserrat", 5.5, turn + W + SP / 2, turn + H * 0.4, WHITE, 800, rot=90))
        b0, b1, b2, b3 = T.ink_bounds(TAGLINE_BN, "mina-bold", 9)
        d.add(T.text(TAGLINE_BN, "mina-bold", 9, turn + W / 2, turn + H * 0.45 - b1, NAVY, "middle"))
        return d
    raise KeyError(design)


def diary_front(design):
    """Just the front board (for mockups)."""
    W, H, SP = DIARY
    full = diary_cover(design)
    turn = 15.0
    d = Doc(W, H, unit="mm", title=full.title)
    inner = full.svg().split(">", 1)[1].rsplit("</svg>", 1)[0].split("</title>", 1)[-1]
    d.add(f'<g transform="translate({-(turn + W + SP)} {-turn})">{inner}</g>')
    return d


def diary_page():
    """Ruled A5 page with the brand header."""
    W, H = DIARY[0], DIARY[1]
    d = _doc(W, H, WHITE, "Parcel Fly diary page")
    frag, _ = LY.place_logo("horizontal", "color", 12, 10, h=6)
    d.add(frag)
    d.add(T.text("DATE", "montserrat", 2.2, W - 40, 15, SLATE, "start", 700, tracking=0.16))
    d.rect(W - 31, 15.3, 19, 0.2, MIST)
    for i in range(24):
        y = 30 + i * 7.2
        d.rect(12, y, W - 24, 0.2, "#C9D8E8")
    d.add(T.text(CONTACT["web"], "montserrat", 2.0, W / 2, H - 8, SLATE, "middle", 600))
    return d


# ------------------------------------------------------------------ pen

def pen_print(barrel):
    W, H = PEN
    col = WHITE if barrel in ("navy", "sky") else NAVY
    d = Doc(W, H, unit="mm", title=f"Parcel Fly pen print ({barrel} barrel)")
    frag, _ = LY.place_logo("horizontal", "ondark" if barrel == "navy" else ("white" if barrel == "sky" else "color"),
                            0, 0, w=W, h=H, align="center", valign="middle")
    d.add(frag)
    return d
