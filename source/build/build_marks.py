"""Stamps, seals and stickers.

stamps/   rubber-stamp vectors (one colour, mm) + inked digital PNGs
seals/    badges (colour, light, one-colour navy/white), English and Bangla
stickers/ artwork with 1 mm bleed + separate magenta cut line + preview, and an A4 sticker sheet
"""
import io
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from shapely.geometry import Polygon
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pfbrand import ROOT, layout as LY, logo as L, symbol as S, text as T  # noqa: E402
from pfbrand import pictograms as P  # noqa: E402
from pfbrand.arc import arc_text, fit_arc_size  # noqa: E402
from pfbrand import maps as MP  # noqa: E402
from pfbrand.brand import (AMBER, CONTACT, COBALT, CYAN, GREEN, MINT, NAVY, RED, SKY, WHITE)  # noqa: E402
from pfbrand.svg import Doc, png_image  # noqa: E402
from pfbrand.text import fmt  # noqa: E402

OUT_STAMPS, OUT_SEALS, OUT_STICKERS = ROOT / "stamps", ROOT / "seals", ROOT / "stickers"
CUT = "#FF00FF"
DPI = 300


def px(mm):
    return int(round(mm / 25.4 * DPI))


def sym(way, cx, cy, width):
    return LY.symbol_at(way, cx, cy, width)


# ================================================================== stamps

STAMPS = [
    # key, English, Bangla, status colour, date line
    ("delivered", "DELIVERED", "ডেলিভারি সম্পন্ন", GREEN, True),
    ("picked-up", "PICKED UP", "পিকআপ সম্পন্ন", GREEN, True),
    ("received", "RECEIVED", "গৃহীত", GREEN, True),
    ("paid", "PAID", "পরিশোধিত", GREEN, True),
    ("verified", "VERIFIED", "যাচাইকৃত", GREEN, True),
    ("cash-on-delivery", "CASH ON DELIVERY", "ক্যাশ অন ডেলিভারি", AMBER, False),
    ("on-hold", "ON HOLD", "স্থগিত", AMBER, True),
    ("urgent", "URGENT", "জরুরি", AMBER, False),
    ("returned", "RETURNED", "ফেরত", RED, True),
    ("cancelled", "CANCELLED", "বাতিল", RED, True),
    ("fragile", "FRAGILE", "ভঙ্গুর", RED, False),
    ("approved", "APPROVED", "অনুমোদিত", NAVY, True),
]


def stamp_rect(en, bn, colour, date):
    W, H = 66.0, 28.0
    d = Doc(W, H, unit="mm", title=f"Parcel Fly stamp: {en}")
    sw = f' fill="none" stroke="{colour}"'
    d.add(f'<rect x="0.6" y="0.6" width="{W - 1.2}" height="{H - 1.2}" rx="2.6"{sw} stroke-width="1.1"/>')
    d.add(f'<rect x="2.1" y="2.1" width="{W - 4.2}" height="{H - 4.2}" rx="1.4"{sw} stroke-width="0.35"/>')
    d.add(sym(colour, 11.2, 11.0, 13.0))
    d.add(T.text("PARCEL FLY", "montserrat", 1.85, 11.2, 18.6, colour, "middle", 800, tracking=0.12))
    d.add(T.text("DHAKA", "montserrat", 1.5, 11.2, 21.2, colour, "middle", 700, tracking=0.3))
    d.add(f'<rect x="19.7" y="4" width="0.35" height="{H - 8}" fill="{colour}"/>')
    x0, x1 = 22.8, W - 4.0
    ws = min(6.4 / 0.72, T.fit_size(en, "montserrat", x1 - x0, 20, 900, tracking=0.04))
    d.add(T.text(en, "montserrat", ws, (x0 + x1) / 2, 4.4 + 6.4, colour, "middle", 900, tracking=0.04))
    bs = min(5.2, T.fit_size(bn, "mina-bold", x1 - x0, 20))
    bx0, by0, bx1, by1 = T.ink_bounds(bn, "mina-bold", bs)
    d.add(T.text(bn, "mina-bold", bs, (x0 + x1) / 2, 13.3 - by0, colour, "middle"))
    if date:
        d.add(T.text("DATE", "montserrat", 1.7, x0, H - 4.3, colour, "start", 700, tracking=0.16))
        d.add(f'<rect x="{x0 + 6.2}" y="{H - 4.4}" width="{x1 - x0 - 6.2}" height="0.3" fill="{colour}"/>')
    return d


def stamp_round(colour):
    D = 40.0
    c = D / 2
    d = Doc(D, D, unit="mm", title="Parcel Fly company seal stamp")
    d.circle(c, c, 19.3, "none", f' stroke="{colour}" stroke-width="1.0"')
    d.circle(c, c, 13.4, "none", f' stroke="{colour}" stroke-width="0.45"')
    d.add(arc_text("PARCEL FLY", "montserrat", 3.7, c, c, 14.5, "top", colour, 800, 0.2))
    d.add(arc_text("DHAKA · BANGLADESH", "montserrat", 2.55, c, c, 18.0, "bottom", colour, 700, 0.12))
    for a in (180, 0):
        x, y = c + 16.3 * math.cos(math.radians(a)), c + 16.3 * math.sin(math.radians(a))
        d.add(LY.parcel(x, y, 0.95, colour))
    d.add(sym(colour, c, c - 1.4, 15.5))
    d.add(T.text("EST. 2025", "montserrat", 2.1, c, c + 6.6, colour, "middle", 800, tracking=0.2))
    return d


def stamp_hub(hb, colour):
    """Round hub stamp: PARCEL FLY + hub name in English (top) and Bangla (bottom), date line in the centre."""
    D = 42.0
    c = D / 2
    d = Doc(D, D, unit="mm", title=f"Parcel Fly {hb['name']} Hub stamp")
    d.circle(c, c, 20.3, "none", f' stroke="{colour}" stroke-width="1.0"')
    d.circle(c, c, 13.9, "none", f' stroke="{colour}" stroke-width="0.45"')
    top = f"PARCEL FLY · {hb['name'].upper()} HUB"
    ts = fit_arc_size(top, "montserrat", 15.2, 200, 3.0, 800, 0.1)
    d.add(arc_text(top, "montserrat", ts, c, c, 15.2, "top", colour, 800, 0.1))
    bn = f"{hb['name_bn']} হাব"
    bs = fit_arc_size(bn, "mina-bold", 18.9, 110, 3.4)
    d.add(arc_text(bn, "mina-bold", bs, c, c, 18.9, "bottom", colour))
    for a in (152, 28):
        x, y = c + 17.1 * math.cos(math.radians(a)), c + 17.1 * math.sin(math.radians(a))
        d.add(LY.parcel(x, y, 0.85, colour))
    d.add(sym(colour, c, c - 3.6, 13.5))
    d.add(T.text("DATE", "montserrat", 1.6, c - 8.5, c + 6.6, colour, "start", 800, tracking=0.16))
    d.add(f'<rect x="{fmt(c - 2.6)}" y="{fmt(c + 6.7)}" width="11.1" height="0.3" fill="{colour}"/>')
    return d


def stamp_signature(colour):
    W, H = 70.0, 34.0
    d = Doc(W, H, unit="mm", title="Parcel Fly approval stamp")
    d.add(f'<rect x="0.6" y="0.6" width="{W - 1.2}" height="{H - 1.2}" rx="2.6" fill="none" stroke="{colour}" stroke-width="1.0"/>')
    d.add(sym(colour, 12, 9.5, 14))
    d.add(T.text("PARCEL FLY", "montserrat", 3.4, 22, 11.2, colour, "start", 900, tracking=0.1))
    d.add(T.text("61/2 Nazimuddin Road, Bongshal, Dhaka", "montserrat", 1.75, 22, 14.4, colour, "start", 600))
    for i, lab in enumerate(["Signature", "Name", "Date"]):
        y = 21.0 + i * 5.0
        d.add(T.text(lab.upper(), "montserrat", 1.7, 5, y, colour, "start", 700, tracking=0.14))
        d.add(f'<rect x="20" y="{y - 0.15}" width="{W - 25}" height="0.3" fill="{colour}"/>')
    return d


def ink(svg_data, w_mm, h_mm, colour_hex, width_px=1200, seed=0, angle=None):
    """Digital 'inked' version: speckle texture + uneven pressure + slight rotation."""
    rng = np.random.default_rng(seed)
    im = png_image(svg_data, width_px, w_mm, h_mm)
    a = np.array(im).astype(np.float32)
    h, w = a.shape[:2]
    low = Image.fromarray((rng.random((max(2, h // 60), max(2, w // 60))) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    low = np.array(low).astype(np.float32) / 255
    speck = rng.random((h, w))
    keep = (speck > 0.10 + 0.35 * (low < 0.22)) & ~((low < 0.08) & (speck < 0.6))
    alpha = a[:, :, 3] * keep * (0.78 + 0.22 * low)
    a[:, :, 3] = alpha
    out = Image.fromarray(a.astype(np.uint8), "RGBA")
    ang = angle if angle is not None else float(rng.uniform(-5, 5))
    return out.rotate(ang, resample=Image.BICUBIC, expand=True)


def build_stamps():
    n = 0
    for key, en, bn, colour, date in STAMPS:
        for name, col in [("black", "#000000"), ("navy", NAVY)]:
            d = stamp_rect(en, bn, col, date)
            d.save(OUT_STAMPS / "rubber-stamp-vector" / f"parcelfly-stamp-{key}-{name}.svg", pdf=True, eps=name == "black",
                   png=[px(66)])
            n += 3
        d = stamp_rect(en, bn, colour, date)
        (OUT_STAMPS / "digital-inked").mkdir(parents=True, exist_ok=True)
        ink(d.svg(), d.w, d.h, colour, seed=sum(map(ord, key))).save(OUT_STAMPS / "digital-inked" / f"parcelfly-stamp-{key}.png")
        n += 1
    for name, col in [("black", "#000000"), ("navy", NAVY)]:
        d = stamp_round(col)
        d.save(OUT_STAMPS / "rubber-stamp-vector" / f"parcelfly-company-seal-{name}.svg", pdf=True, eps=name == "black",
               png=[px(40)])
        d = stamp_signature(col)
        d.save(OUT_STAMPS / "rubber-stamp-vector" / f"parcelfly-approval-stamp-{name}.svg", pdf=True, eps=name == "black",
               png=[px(70)])
        n += 6
    for hb in MP.hubs():
        for name, col in [("black", "#000000"), ("navy", NAVY)]:
            d = stamp_hub(hb, col)
            d.save(OUT_STAMPS / "hub-stamps" / f"parcelfly-hub-stamp-{hb['key']}-{name}.svg", pdf=True,
                   eps=name == "black", png=[px(42)])
            n += 4
        ink(stamp_hub(hb, NAVY).svg(), 42, 42, NAVY, 1000, seed=sum(map(ord, hb["key"]))).save(
            OUT_STAMPS / "digital-inked" / f"parcelfly-hub-stamp-{hb['key']}.png")
        n += 1
    ink(stamp_round(NAVY).svg(), 40, 40, NAVY, 1000, seed=7).save(OUT_STAMPS / "digital-inked" / "parcelfly-company-seal.png")
    ink(stamp_signature(NAVY).svg(), 70, 34, NAVY, 1200, seed=9, angle=-2).save(
        OUT_STAMPS / "digital-inked" / "parcelfly-approval-stamp.png")
    return n + 2


# ================================================================== seals

SEALS = [
    ("official-partner", "OFFICIAL DELIVERY PARTNER", "PARCEL FLY · DHAKA", "en"),
    ("verified-merchant", "VERIFIED MERCHANT", "PARCEL FLY · DHAKA", "en"),
    ("cash-on-delivery", "CASH ON DELIVERY", "AVAILABLE · PARCEL FLY", "en"),
    ("secure-packaging", "SECURE PACKAGING", "SEALED BY PARCEL FLY", "en"),
    ("quality-checked", "QUALITY CHECKED", "PARCEL FLY · DHAKA", "en"),
    ("fast-delivery", "FAST DELIVERY", "ACROSS DHAKA", "en"),
    ("heritage", "ALWAYS, EVERYWHERE", "EST. 2025 · DHAKA", "en"),
    ("bn-official-partner", "অফিসিয়াল ডেলিভারি পার্টনার", "পার্সেল ফ্লাই · ঢাকা", "bn"),
    ("bn-tagline", "সবসময়, সবখানে", "পার্সেল ফ্লাই · ঢাকা", "bn"),
]


def seal(top, bottom, lang, style):
    d = Doc(100, 100, title=f"Parcel Fly seal: {top}")
    c = 50.0
    if style == "color":
        base, ring, txt, txt2, way, dots = NAVY, WHITE, WHITE, CYAN, "ondark", CYAN
    elif style == "light":
        base, ring, txt, txt2, way, dots = WHITE, NAVY, NAVY, SKY, "color", CYAN
    elif style == "navy":
        base, ring, txt, txt2, way, dots = None, NAVY, NAVY, NAVY, NAVY, NAVY
    else:  # white
        base, ring, txt, txt2, way, dots = None, WHITE, WHITE, WHITE, "white", WHITE
    if base:
        d.circle(c, c, 49.2, base)
        if style == "light":
            d.circle(c, c, 48.4, "none", f' stroke="{NAVY}" stroke-width="1.2"')
    else:
        d.circle(c, c, 48.6, "none", f' stroke="{ring}" stroke-width="1.6"')
    for i in range(40):
        a = math.radians(i * 9)
        d.add(LY.parcel(c + 45.6 * math.cos(a), c + 45.6 * math.sin(a), 1.25, dots))
    d.circle(c, c, 42.6, "none", f' stroke="{ring}" stroke-width="0.7"')
    d.circle(c, c, 30.2, "none", f' stroke="{ring}" stroke-width="0.5"')
    if lang == "en":
        ts = fit_arc_size(top, "montserrat", 33.6, 150, 6.0, 800, 0.12)
        d.add(arc_text(top, "montserrat", ts, c, c, 33.6, "top", txt, 800, 0.12))
        bs = fit_arc_size(bottom, "montserrat", 40.2, 115, 4.4, 700, 0.14)
        d.add(arc_text(bottom, "montserrat", bs, c, c, 40.2, "bottom", txt2, 700, 0.14))
    else:
        ts = fit_arc_size(top, "mina-bold", 33.4, 150, 6.6)
        d.add(arc_text(top, "mina-bold", ts, c, c, 33.4, "top", txt))
        bs = fit_arc_size(bottom, "mina-bold", 40.4, 115, 5.0)
        d.add(arc_text(bottom, "mina-bold", bs, c, c, 40.4, "bottom", txt2))
    for a in (180, 0):
        d.add(LY.parcel(c + 36.6 * math.cos(math.radians(a)), c + 36.6 * math.sin(math.radians(a)), 1.3, txt2))
    d.add(sym(way, c, c, 42))
    return d


def build_seals():
    n = 0
    for key, top, bottom, lang in SEALS:
        for style in ["color", "light", "navy", "white"]:
            d = seal(top, bottom, lang, style)
            d.save(OUT_SEALS / style / f"parcelfly-seal-{key}-{style}.svg", png=[1000, 300], pdf=style in ("color", "light"))
            n += 4
    return n


# ================================================================== stickers

def path_from_polygon(poly):
    def ring(coords):
        pts = list(coords)
        return "M" + "L".join(f"{fmt(x)} {fmt(y)}" for x, y in pts[:-1]) + "Z"
    geoms = getattr(poly, "geoms", [poly])
    out = []
    for g in geoms:
        out.append(ring(g.exterior.coords))
        for i in g.interiors:
            out.append(ring(i.coords))
    return "".join(out)


def symbol_union(width, ox, oy):
    k = width / S.WIDTH
    polys = [Polygon([(ox + x * k, oy + y * k) for x, y in pts]) for pts in S.polygons().values()]
    return unary_union(polys)


class Sticker:
    def __init__(self, name, w, h, title):
        self.name, self.w, self.h, self.title = name, w, h, title
        self.art: list[str] = []
        self.defs: list[str] = []
        self.cut = ""

    def doc(self, with_cut=False, cut_only=False):
        d = Doc(self.w, self.h, unit="mm", title=self.title)
        if not cut_only:
            d.defs_add(*self.defs)
            d.add(*self.art)
        if with_cut or cut_only:
            dash = ' stroke-dasharray="1.2 0.8"' if with_cut else ""
            d.add(f'<g id="CutContour"><path d="{self.cut}" fill="none" stroke="{CUT}" stroke-width="0.25"{dash}/></g>')
        return d

    def save(self, folder):
        base = OUT_STICKERS / folder / f"parcelfly-sticker-{self.name}"
        self.doc().save(base.with_suffix(".svg"), pdf=True)
        cut = self.doc(cut_only=True)
        cut.save(base.with_name(base.name + "-cutline.svg"), pdf=True)
        prev = self.doc(with_cut=True)
        from pfbrand.svg import render_png
        render_png(prev.svg(), base.with_name(base.name + "-preview.png"), px(self.w), self.w, self.h)
        return 5


def rounded_rect_path(x, y, w, h, r):
    return (f"M{fmt(x + r)} {fmt(y)}H{fmt(x + w - r)}A{fmt(r)} {fmt(r)} 0 0 1 {fmt(x + w)} {fmt(y + r)}V{fmt(y + h - r)}"
            f"A{fmt(r)} {fmt(r)} 0 0 1 {fmt(x + w - r)} {fmt(y + h)}H{fmt(x + r)}A{fmt(r)} {fmt(r)} 0 0 1 {fmt(x)} {fmt(y + h - r)}"
            f"V{fmt(y + r)}A{fmt(r)} {fmt(r)} 0 0 1 {fmt(x + r)} {fmt(y)}Z")


def circle_path(cx, cy, r):
    return f"M{fmt(cx - r)} {fmt(cy)}A{fmt(r)} {fmt(r)} 0 1 0 {fmt(cx + r)} {fmt(cy)}A{fmt(r)} {fmt(r)} 0 1 0 {fmt(cx - r)} {fmt(cy)}Z"


BLEED = 1.0


def rect_sticker(name, w, h, r, bg, title):
    s = Sticker(name, w + 2 * BLEED, h + 2 * BLEED, title)
    s.art.append(f'<path d="{rounded_rect_path(0, 0, w + 2 * BLEED, h + 2 * BLEED, r + BLEED)}" fill="{bg}"/>')
    s.cut = rounded_rect_path(BLEED, BLEED, w, h, r)
    return s, BLEED, BLEED


def round_sticker(name, dia, bg, title):
    s = Sticker(name, dia + 2 * BLEED, dia + 2 * BLEED, title)
    c = dia / 2 + BLEED
    s.art.append(f'<circle cx="{fmt(c)}" cy="{fmt(c)}" r="{fmt(dia / 2 + BLEED)}" fill="{bg}"/>')
    s.cut = circle_path(c, c, dia / 2)
    return s, c


def two_lang(s, x0, x1, y_en, en, bn, colour, en_size, bn_size, en_weight=900, anchor="middle"):
    cx = (x0 + x1) / 2 if anchor == "middle" else x0
    es = min(en_size, T.fit_size(en, "montserrat", x1 - x0, 50, en_weight, tracking=0.04))
    s.art.append(T.text(en, "montserrat", es, cx, y_en, colour, anchor, en_weight, tracking=0.04))
    bs = min(bn_size, T.fit_size(bn, "mina-bold", x1 - x0, 50))
    b0, b1, b2, b3 = T.ink_bounds(bn, "mina-bold", bs)
    s.art.append(T.text(bn, "mina-bold", bs, cx if anchor == "middle" else x0 - b0, y_en + es * 0.42 - b1, colour, anchor))
    return y_en + es * 0.42 - b1 + b3


def build_stickers():
    n = 0
    # -- die-cut symbol, white border and navy border
    for variant, way, border in [("symbol-diecut", "color", WHITE), ("symbol-diecut-navy", "ondark", NAVY)]:
        W = 70.0
        m = 4.0
        sym_h = S.HEIGHT * W / S.WIDTH
        st = Sticker(variant, W + 2 * m, sym_h + 2 * m, "Parcel Fly die-cut sticker")
        u = symbol_union(W, m, m)
        cut = u.buffer(2.6, join_style="round", quad_segs=24).buffer(0)
        bleed = u.buffer(2.6 + BLEED, join_style="round", quad_segs=24)
        st.art.append(f'<path d="{path_from_polygon(bleed)}" fill="{border}"/>')
        st.art.append(f'<g transform="translate({m} {m}) scale({W / S.WIDTH:.6f})">{S.svg_group(way)}</g>')
        st.cut = path_from_polygon(cut)
        n += st.save("die-cut")
    # -- round logo stickers
    for name, lang in [("round-logo", "en"), ("round-logo-bn", "bn")]:
        st, c = round_sticker(name, 60, NAVY, "Parcel Fly round sticker")
        st.art.append(f'<circle cx="{fmt(c)}" cy="{fmt(c)}" r="27" fill="none" stroke="{CYAN}" stroke-width="0.5"/>')
        frag, _ = LY.place_logo("stacked", "ondark", c - 19, c - 13, w=38, h=26, align="center", valign="middle", lang=lang)
        st.art.append(frag)
        n += st.save("round")
    # -- thank you (for merchants' parcels)
    st, c = round_sticker("thank-you", 64, WHITE, "Thank you sticker")
    st.art.append(f'<circle cx="{fmt(c)}" cy="{fmt(c)}" r="{fmt(31)}" fill="none" stroke="{NAVY}" stroke-width="1.2"/>')
    st.art.append(arc_text("THANK YOU FOR YOUR ORDER", "montserrat", 3.4, c, c, 24.6, "top", NAVY, 800, 0.1))
    st.art.append(arc_text("আপনার অর্ডারের জন্য ধন্যবাদ", "mina-bold", 3.6, c, c, 28.4, "bottom", SKY))
    st.art.append(P.icon("thanks", c - 8.5, c - 12.5, 17, CYAN, 3.6))
    frag, _ = LY.place_logo("horizontal", "color", c - 13, c + 6.2, w=26, h=6.4, align="center")
    st.art.append(T.text("DELIVERED BY", "montserrat", 1.7, c, c + 5.4, "#55607A", "middle", 700, tracking=0.2))
    st.art.append(frag)
    n += st.save("round")
    # -- fragile
    st, ox, oy = rect_sticker("fragile", 90, 55, 4, RED, "Fragile sticker")
    st.art.append(P.icon("fragile", ox + 5, oy + 9, 30, WHITE, 3.4))
    colw = 90 - 37 - 4
    fs = T.fit_size("FRAGILE", "montserrat", colw, 13.5, 900, tracking=0.02)
    st.art.append(T.text("FRAGILE", "montserrat", fs, ox + 37, oy + 22, WHITE, "start", 900, tracking=0.02))
    hs = T.fit_size("HANDLE WITH CARE", "montserrat", colw, 3.6, 700, tracking=0.16)
    st.art.append(T.text("HANDLE WITH CARE", "montserrat", hs, ox + 37.4, oy + 28.6, WHITE, "start", 700, tracking=0.16))
    bs = T.fit_size("ভঙ্গুর · সাবধানে বহন করুন", "mina-bold", colw, 4.6)
    b0, b1, b2, b3 = T.ink_bounds("ভঙ্গুর · সাবধানে বহন করুন", "mina-bold", bs)
    st.art.append(T.text("ভঙ্গুর · সাবধানে বহন করুন", "mina-bold", bs, ox + 37.4 - b0, oy + 32.6 - b1, WHITE))
    frag, _ = LY.place_logo("horizontal", "white", ox + 37.4, oy + 45, h=5.5)
    st.art.append(frag)
    n += st.save("handling")
    # -- handling squares
    for name, icon, en, bn, bg, fg in [
        ("this-side-up", "this-side-up", "THIS SIDE UP", "এই দিক উপরে", WHITE, NAVY),
        ("keep-frozen", "frozen", "KEEP FROZEN", "হিমায়িত রাখুন", CYAN, NAVY),
        ("keep-dry", "keep-dry", "KEEP DRY", "শুকনো রাখুন", SKY, WHITE),
    ]:
        st, ox, oy = rect_sticker(name, 70, 70, 5, bg, f"{en.title()} sticker")
        if bg == WHITE:
            st.art.append(f'<path d="{rounded_rect_path(ox + 2, oy + 2, 66, 66, 3.5)}" fill="none" stroke="{NAVY}" stroke-width="1.4"/>')
        st.art.append(P.icon(icon, ox + 19, oy + 7, 32, fg, 3.2))
        two_lang(st, ox + 6, ox + 64, oy + 49, en, bn, fg, 8.6, 6.0)
        frag, _ = LY.place_logo("wordmark", "white" if fg == WHITE else NAVY, ox + 35 - 11, oy + 62.5, w=22, h=3.6,
                                align="center")
        st.art.append(frag)
        n += st.save("handling")
    # -- cash on delivery
    st, ox, oy = rect_sticker("cash-on-delivery", 76, 38, 4, AMBER, "Cash on delivery sticker")
    st.art.append(P.icon("cash", ox + 4, oy + 6, 22, NAVY, 3.4))
    colw = 76 - 29 - 4
    cs = T.fit_size("DELIVERY", "montserrat", colw, 7.6, 900)
    st.art.append(T.text("CASH ON", "montserrat", cs, ox + 29, oy + 12.5, NAVY, "start", 900))
    st.art.append(T.text("DELIVERY", "montserrat", cs, ox + 29, oy + 12.5 + cs * 0.95, NAVY, "start", 900))
    bs = T.fit_size("ক্যাশ অন ডেলিভারি", "mina-bold", colw, 4.4)
    b0, b1, b2, b3 = T.ink_bounds("ক্যাশ অন ডেলিভারি", "mina-bold", bs)
    st.art.append(T.text("ক্যাশ অন ডেলিভারি", "mina-bold", bs, ox + 29 - b0, oy + 12.5 + cs * 0.95 + 2.8 - b1, NAVY))
    frag, _ = LY.place_logo("wordmark", NAVY, ox + 4, oy + 31, w=20, h=3.4)
    st.art.append(frag)
    n += st.save("handling")
    # -- delivered by
    st, ox, oy = rect_sticker("delivered-by", 80, 28, 4, NAVY, "Delivered by Parcel Fly sticker")
    st.art.append(T.text("DELIVERED BY", "montserrat", 2.6, ox + 40, oy + 7.2, CYAN, "middle", 700, tracking=0.24))
    frag, _ = LY.place_logo("horizontal", "ondark", ox + 8, oy + 10, w=64, h=13, align="center", valign="middle")
    st.art.append(frag)
    n += st.save("brand")
    # -- scan to track
    st, ox, oy = rect_sticker("scan-to-track", 50, 66, 4, WHITE, "Scan to track sticker")
    st.art.append(f'<path d="{rounded_rect_path(ox + 1.5, oy + 1.5, 47, 63, 3)}" fill="none" stroke="{NAVY}" stroke-width="1.1"/>')
    st.art.append(LY.qr(f"{CONTACT['url']}/#track-parcel", ox + 6, oy + 6, 38, NAVY, quiet=1))
    st.art.append(T.text("SCAN TO TRACK", "montserrat", 3.4, ox + 25, oy + 50.5, NAVY, "middle", 900, tracking=0.1))
    b0, b1, b2, b3 = T.ink_bounds("ট্র্যাক করতে স্ক্যান করুন", "mina-bold", 3.2)
    st.art.append(T.text("ট্র্যাক করতে স্ক্যান করুন", "mina-bold", 3.2, ox + 25, oy + 52.6 - b1, SKY, "middle"))
    frag, _ = LY.place_logo("horizontal", "color", ox + 10, oy + 58.5, w=30, h=4.2, align="center")
    st.art.append(frag)
    n += st.save("brand")
    # -- tamper-evident seal strip
    st, ox, oy = rect_sticker("tamper-seal", 100, 20, 2, NAVY, "Tamper-evident seal")
    st.art.append(f'<rect x="{ox + 2}" y="{oy + 2}" width="96" height="16" rx="1" fill="none" stroke="{CYAN}" stroke-width="0.35"/>')
    st.art.append(LY.symbol_at("ondark", ox + 13, oy + 10, 16))
    st.art.append(T.text("SEALED FOR YOUR SAFETY", "montserrat", 3.9, ox + 24, oy + 9.6, WHITE, "start", 900, tracking=0.06))
    st.art.append(T.text("Do not accept if this seal is broken  ·  সিল ভাঙা থাকলে গ্রহণ করবেন না", "noto-bengali", 2.15,
                         ox + 24, oy + 14.2, CYAN, "start", 600))
    n += st.save("brand")
    # -- express
    st, ox, oy = rect_sticker("express", 64, 30, 4, SKY, "Express sticker")
    st.art.append(LY.chevron(ox + 4, oy + 7, 16, (MINT, CYAN)))
    st.art.append(LY.chevron(ox + 10, oy + 7, 16, (WHITE, WHITE)))
    es = T.fit_size("EXPRESS", "montserrat", 64 - 25 - 4, 8.4, 900, tracking=0.02)
    st.art.append(T.text("EXPRESS", "montserrat", es, ox + 25, oy + 16.8, WHITE, "start", 900, tracking=0.02))
    ps = T.fit_size("PRIORITY DELIVERY", "montserrat", 64 - 25 - 4, 2.5, 800, tracking=0.16)
    st.art.append(T.text("PRIORITY DELIVERY", "montserrat", ps, ox + 25.3, oy + 21.6, NAVY, "start", 800, tracking=0.16))
    n += st.save("handling")
    # -- laptop / brand strip
    st, ox, oy = rect_sticker("laptop", 100, 30, 6, WHITE, "Parcel Fly laptop sticker")
    frag, _ = LY.place_logo("horizontal", "color", ox + 7, oy + 6, w=86, h=18, align="center", valign="middle")
    st.art.append(frag)
    n += st.save("brand")
    # -- helmet decal
    st, ox, oy = rect_sticker("helmet-decal", 120, 22, 11, NAVY, "Rider helmet decal")
    st.defs.append(f'<clipPath id="decal"><path d="{rounded_rect_path(0, 0, 122, 24, 12)}"/></clipPath>')
    st.art.append(f'<g clip-path="url(#decal)">{LY.speed_lines(ox - 30, oy + 4, 14, 54, (SKY, COBALT, CYAN))}</g>')
    frag, _ = LY.place_logo("horizontal", "ondark", ox + 30, oy + 4, w=84, h=14, align="right", valign="middle")
    st.art.append(frag)
    n += st.save("brand")
    return n


def build_sticker_sheet():
    """A4 sheets (210 x 297 mm): every sticker shelf-packed with a 5 mm gutter, plus the matching cut layer."""
    import re
    W, H, M, G = 210.0, 297.0, 8.0, 5.0
    items = []
    for f in sorted(OUT_STICKERS.glob("*/parcelfly-sticker-*.svg")):
        if f.name.endswith("-cutline.svg") or f.parent.name == "sheet":
            continue
        svg = f.read_text()
        vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
        items.append((vb[3], vb[2], f))
    items.sort(key=lambda t: (-t[0], -t[1]))
    pages, cur, x, y, shelf_h = [], [], M, M, 0.0
    for h, w, f in items:
        if x + w > W - M:
            x, y, shelf_h = M, y + shelf_h + G, 0.0
        if y + h > H - M:
            pages.append(cur)
            cur, x, y, shelf_h = [], M, M, 0.0
        cur.append((f, x, y))
        x += w + G
        shelf_h = max(shelf_h, h)
    if cur:
        pages.append(cur)
    n = 0
    for pi, page in enumerate(pages, start=1):
        d = Doc(W, H, unit="mm", title=f"Parcel Fly sticker sheet A4, page {pi}")
        cutd = Doc(W, H, unit="mm", title=f"Parcel Fly sticker sheet A4 cut line, page {pi}")
        for f, x, y in page:
            name = f.stem
            inner = re.search(r"<svg[^>]*>(.*)</svg>", f.read_text(), re.S).group(1)
            inner = re.sub(r"<title>.*?</title>", "", inner)
            inner = inner.replace('id="', f'id="{name}-').replace("url(#", f"url(#{name}-")
            d.add(f'<g transform="translate({fmt(x)} {fmt(y)})">{inner}</g>')
            c = f.with_name(f.stem + "-cutline.svg").read_text()
            cinner = re.sub(r"<title>.*?</title>", "", re.search(r"<svg[^>]*>(.*)</svg>", c, re.S).group(1))
            cutd.add(f'<g transform="translate({fmt(x)} {fmt(y)})">{cinner.replace(chr(105) + "d=" + chr(34) + "CutContour" + chr(34), "")}</g>')
        d.save(OUT_STICKERS / "sheet" / f"parcelfly-sticker-sheet-a4-p{pi}.svg", pdf=True, png=[px(210) // 2])
        cutd.save(OUT_STICKERS / "sheet" / f"parcelfly-sticker-sheet-a4-p{pi}-cutline.svg", pdf=True)
        n += 5
    return n


def main():
    n = build_stamps() + build_seals() + build_stickers()
    n += build_sticker_sheet()
    print(f"marks: ~{n} files")


if __name__ == "__main__":
    main()
