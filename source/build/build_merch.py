"""Merchandise: print files and mockups.

merch/print/mugs/             11 oz sublimation wraps, 216 x 89 mm (signature, navy, Bangla)
merch/print/cups/             12 oz paper cup wraps, printable fan templates (300 dpi) and the fan die line
merch/print/diary/            A5 hardcover case wraps (navy, white) and the ruled page
merch/print/pens/             pen barrel prints, 50 x 8 mm, for navy, white and sky barrels
merch/print/laptop-stickers/  A5 kiss-cut laptop sticker sheet and its cut line
mockups/merch/                studio scenes and flat lays; cutouts/ holds transparent product renders
"""
import io
import math
import re
import sys
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pfbrand import ROOT, merch as M, mockup as MK, props as PR  # noqa: E402
from pfbrand.brand import CYAN, NAVY, SKY, WHITE  # noqa: E402
from pfbrand.svg import Doc  # noqa: E402
from pfbrand.text import fmt  # noqa: E402
import build_bags  # noqa: E402

OUT = ROOT / "merch"
MOCK = ROOT / "mockups" / "merch"
DPI = 300
CUT = "#FF00FF"


def px(mm, dpi=DPI):
    return int(round(mm / 25.4 * dpi))


def svg_file_img(path, w):
    return Image.open(io.BytesIO(cairosvg.svg2png(url=str(path), output_width=w))).convert("RGBA")


# ------------------------------------------------------------------ print files

def cup_fan_dieline():
    """The fan (annular sector) outline of the 12 oz cup, with a 5 mm glue overlap on one end."""
    D, d_, h = M.CUP["top"], M.CUP["bottom"], M.CUP["height"]
    slant = math.hypot(h, (D - d_) / 2)
    R = slant * D / (D - d_)
    r = R - slant
    ang = math.pi * D / R
    glue = 5.0 / R
    a0, a1 = -ang / 2 - glue, ang / 2
    W = 2 * R * math.sin(ang / 2 + glue) + 10
    Hh = R - r * math.cos(ang / 2 + glue) + 10
    cx, cy = W / 2, 5 + R

    def pt(rad, a):
        return cx + rad * math.sin(a), cy - rad * math.cos(a)

    p = [pt(R, a0), pt(R, a1), pt(r, a1), pt(r, a0)]
    d = (f"M{fmt(p[0][0])} {fmt(p[0][1])}A{fmt(R)} {fmt(R)} 0 0 1 {fmt(p[1][0])} {fmt(p[1][1])}"
         f"L{fmt(p[2][0])} {fmt(p[2][1])}A{fmt(r)} {fmt(r)} 0 0 0 {fmt(p[3][0])} {fmt(p[3][1])}Z")
    g = [pt(R, -ang / 2), pt(r, -ang / 2)]
    doc = Doc(W, Hh, unit="mm", title="Parcel Fly 12 oz paper cup fan: die line (magenta cut, cyan glue edge)")
    doc.add(f'<path d="{d}" fill="none" stroke="{CUT}" stroke-width="0.3"/>'
            f'<path d="M{fmt(g[0][0])} {fmt(g[0][1])}L{fmt(g[1][0])} {fmt(g[1][1])}" stroke="#00AEEF" '
            f'stroke-width="0.3" stroke-dasharray="2 1.2"/>')
    return doc, (R, r, ang)


LAPTOP_STICKERS = ["round/parcelfly-sticker-round-logo", "round/parcelfly-sticker-round-logo-bn",
                   "die-cut/parcelfly-sticker-symbol-diecut", "die-cut/parcelfly-sticker-symbol-diecut-navy",
                   "brand/parcelfly-sticker-laptop"]


def laptop_sheet():
    """A5 portrait kiss-cut sheet: the laptop-friendly stickers, shelf-packed, with the matching cut layer."""
    W, H, Mg, G = 148.0, 210.0, 8.0, 5.0
    items = []
    for key in LAPTOP_STICKERS:
        f = ROOT / "stickers" / f"{key}.svg"
        vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', f.read_text()).group(1).split()]
        items.append((vb[3], vb[2], f))
    items.sort(key=lambda t: (-t[0], -t[1]))
    placed, x, y, shelf = [], Mg, Mg, 0.0
    for h, w, f in items:
        if x + w > W - Mg:
            x, y, shelf = Mg, y + shelf + G, 0.0
        placed.append((f, x, y))
        x += w + G
        shelf = max(shelf, h)
    d = Doc(W, H, unit="mm", title="Parcel Fly laptop sticker sheet A5 (kiss cut)")
    d.rect(0, 0, W, H, "#FFFFFF")
    cut = Doc(W, H, unit="mm", title="Parcel Fly laptop sticker sheet A5: cut line")
    for f, x, y in placed:
        name = f.stem
        inner = re.search(r"<svg[^>]*>(.*)</svg>", f.read_text(), re.S).group(1)
        inner = re.sub(r"<title>.*?</title>", "", inner)
        inner = inner.replace('id="', f'id="{name}-').replace("url(#", f"url(#{name}-")
        d.add(f'<g transform="translate({fmt(x)} {fmt(y)})">{inner}</g>')
        c = f.with_name(f.stem + "-cutline.svg").read_text()
        cin = re.sub(r"<title>.*?</title>", "", re.search(r"<svg[^>]*>(.*)</svg>", c, re.S).group(1))
        cut.add(f'<g transform="translate({fmt(x)} {fmt(y)})">{cin.replace(chr(105) + "d=" + chr(34) + "CutContour" + chr(34), "")}</g>')
    return d, cut


def print_files():
    n = 0
    for design in ["signature", "navy", "bangla"]:
        d = M.mug_wrap(design)
        d.save(OUT / "print" / "mugs" / f"parcelfly-mug-wrap-{design}-216x89.svg", pdf=True, png=[px(216)])
        n += 3
    die, (R, r, ang) = cup_fan_dieline()
    die.save(OUT / "print" / "cups" / "parcelfly-cup-12oz-fan-dieline.svg", pdf=True)
    n += 2
    for design in ["white", "navy"]:
        d = M.cup_wrap(design)
        d.save(OUT / "print" / "cups" / f"parcelfly-cup-12oz-wrap-{design}.svg", png=[px(d.w)])
        fan = M.cup_fan(MK.doc_img(d, px(d.w)), px_per_mm=DPI / 25.4)
        fan.save(OUT / "print" / "cups" / f"parcelfly-cup-12oz-fan-{design}-300dpi.png", dpi=(DPI, DPI))
        n += 3
    for design in ["navy", "white"]:
        d = M.diary_cover(design)
        d.save(OUT / "print" / "diary" / f"parcelfly-diary-a5-cover-{design}.svg", pdf=True, png=[px(d.w) // 2])
        n += 3
    d = M.diary_page()
    d.save(OUT / "print" / "diary" / "parcelfly-diary-a5-page.svg", pdf=True, png=[px(148) // 2])
    n += 3
    for barrel in ["navy", "white", "sky"]:
        d = M.pen_print(barrel)
        d.save(OUT / "print" / "pens" / f"parcelfly-pen-print-{barrel}-barrel-50x8.svg", pdf=True, png=[px(50)])
        n += 3
    sheet, cut = laptop_sheet()
    sheet.save(OUT / "print" / "laptop-stickers" / "parcelfly-laptop-sticker-sheet-a5.svg", pdf=True, png=[px(148) // 2])
    cut.save(OUT / "print" / "laptop-stickers" / "parcelfly-laptop-sticker-sheet-a5-cutline.svg", pdf=True)
    n += 5
    return n


# ------------------------------------------------------------------ product renders

PEN_BARREL = {"navy": NAVY, "white": "#F4F6F8", "sky": SKY}


def mug(design, handle="left", px_w=900):
    inner = {"signature": None, "navy": CYAN, "bangla": NAVY}[design]
    img, g = PR.mug(MK.doc_img(M.mug_wrap(design), 2200), handle, inner=inner, px_w=px_w)
    return img, g, 95 + 82 * math.sin(math.radians(13))


def cup(design, coffee=False, px_w=700):
    wrap = MK.doc_img(M.cup_wrap(design), 1800)
    if coffee:
        img, g = PR.paper_cup(wrap, lid=None, coffee=True, px_w=px_w, turn=0.75)
        return img, g, 110 + 93 * math.sin(math.radians(14))
    img, g = PR.paper_cup(wrap, lid="#FFFFFF" if design == "white" else "#1C1F26", px_w=px_w)
    return img, g, 119.5 + 95 * math.sin(math.radians(14))


def diary_faces(design, px_w=1500):
    W, H, SP = M.DIARY
    full = MK.doc_img(M.diary_cover(design), int(px_w * (2 * W + SP + 30) / W))
    k = full.width / (2 * W + SP + 30)
    front = full.crop((int((15 + W + SP) * k), int(15 * k), int((15 + 2 * W + SP) * k), int((15 + H) * k)))
    spine = full.crop((int((15 + W) * k), int(15 * k), int((15 + W + SP) * k), int((15 + H) * k)))
    return front, spine


DIARY_BAND = {"navy": CYAN, "white": NAVY}


def diary(design, yaw=-26, px_w=900):
    front, spine = diary_faces(design)
    img, g = PR.book(front, spine, M.DIARY, yaw=yaw, cover=NAVY if design == "navy" else WHITE,
                     band=DIARY_BAND[design], px_w=px_w)
    return img, g, M.DIARY[1] + 12


def diary_top(design, k):
    """Closed diary from above (flat lays): cover with the band and a sliver of fore-edge."""
    front, _ = diary_faces(design)
    W, H, _ = M.DIARY
    f = front.resize((int(W * k), int(H * k)), Image.LANCZOS)
    d = ImageDraw.Draw(f)
    d.rectangle((int(f.width - 17.5 * k), 0, int(f.width - 10.5 * k), f.height), fill=DIARY_BAND[design])
    d.rectangle((int(f.width - 17.5 * k), 0, int(f.width - 17.0 * k), f.height), fill=MK.darker(DIARY_BAND[design], 0.6))
    return PR.paper(f, 3, 0.02, 0.015)


def pen(barrel, k, angle):
    return PR.pen(MK.doc_img(M.pen_print(barrel), 1200), PEN_BARREL[barrel], px_len=int(140 * k), angle=angle)


def laptop_stickers(px_w):
    S = ROOT / "stickers"
    st = [(svg_file_img(S / "brand/parcelfly-sticker-laptop.svg", 1400), 152, 66, 96, -5),
          (svg_file_img(S / "die-cut/parcelfly-sticker-symbol-diecut.svg", 1200), 64, 146, 70, 10),
          (svg_file_img(S / "round/parcelfly-sticker-round-logo-bn.svg", 1000), 244, 148, 52, -9),
          (svg_file_img(S / "round/parcelfly-sticker-round-logo.svg", 1000), 158, 158, 46, 6),
          (svg_file_img(S / "die-cut/parcelfly-sticker-symbol-diecut-navy.svg", 1200), 252, 52, 56, 16)]
    return PR.laptop(st, px_w=px_w)


def row(scene, items, base_y, px_per_mm, gap_px, fill=0.9):
    """build_bags.row, scaled down when the row would not fit inside `fill` of the scene width."""
    total = 0.0
    for img, ground, h_mm in items:
        bb = img.getchannel("A").getbbox()
        total += (bb[2] - bb[0]) * h_mm * px_per_mm / (bb[3] - bb[1])
    total += gap_px * (len(items) - 1)
    k = min(1.0, scene.width * fill / total)
    build_bags.row(scene, items, base_y, px_per_mm * k, gap_px * k)


# ------------------------------------------------------------------ output helpers

def save_scene(scene, name, folder=MOCK):
    p = folder / f"parcelfly-{name}"
    p.parent.mkdir(parents=True, exist_ok=True)
    rgb = scene.convert("RGB")
    rgb.save(p.with_suffix(".jpg"), quality=92, optimize=True, progressive=True)
    rgb.resize((rgb.width // 2, rgb.height // 2), Image.LANCZOS).save(p.with_name(p.name + "-preview.jpg"), quality=86)
    return 2


def cutout(img, name, folder=MOCK):
    p = folder / "cutouts" / f"parcelfly-{name}.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    img.crop(img.getchannel("A").getbbox()).save(p)
    return 1


# ------------------------------------------------------------------ scenes

def studio_scenes():
    n = 0
    sig_l, sig_r = mug("signature", "left"), mug("signature", "right")
    navy, bangla = mug("navy", "left"), mug("bangla", "right")
    cw, cn, cc = cup("white"), cup("navy"), cup("white", coffee=True)
    dn, dw = diary("navy", -26), diary("white", -22)
    for (img, g, h), name in [(sig_l, "mug-signature"), (sig_r, "mug-signature-tagline-side"), (navy, "mug-navy"),
                              (bangla, "mug-bangla"), (cw, "paper-cup-white"), (cn, "paper-cup-navy"),
                              (cc, "paper-cup-open"), (dn, "diary-navy"), (dw, "diary-white")]:
        n += cutout(img, name)
        s = MK.studio(1600, 1800)
        MK.place(s, img, g, 800, 1600, 1150 if "diary" not in name else 1350)
        n += save_scene(s, f"{name}-studio")
    s = MK.studio(2400, 1500)
    row(s, [sig_l, navy, bangla], 1320, 9.2, 110)
    n += save_scene(s, "mugs")
    s = MK.studio(2400, 1500)
    row(s, [sig_l, sig_r], 1300, 8.6, 150)
    n += save_scene(s, "mug-signature-both-sides")
    s = MK.studio(2400, 1500)
    row(s, [cw, cn, cc], 1300, 7.0, 130)
    n += save_scene(s, "paper-cups")
    s = MK.studio(2400, 1500, top="#0C1C9C", bottom="#00004E")
    row(s, [cn, navy], 1300, 7.4, 120)
    n += save_scene(s, "mug-and-cup-night")
    s = MK.studio(2400, 1500)
    row(s, [dn, dw], 1320, 4.6, 140)
    n += save_scene(s, "diaries")
    s = MK.studio(3600, 1400, floor=0.78)
    row(s, [dn, sig_l, cw, navy, cn, bangla, dw], 1240, 3.9, 70)
    n += save_scene(s, "merch-family")
    return n


def flatlays():
    n = 0
    # desk: open diary, closed diary, pens, laptop with stickers and a coffee cup's edge out of frame
    k = 5.0
    s = PR.surface(3000, 2000, "wood", 11)
    lap = laptop_stickers(int(304 * k))
    PR.lay(s, lap, 2350, 520, -8, lift=3.0)
    pg = MK.doc_img(M.diary_page(), 1400)
    ob = PR.open_book(pg, pg, px_w=int(304 * k))
    PR.lay(s, ob, 1080, 1180, 4, lift=1.6)
    PR.lay(s, diary_top("navy", k), 2440, 1640, -14, lift=2.6)
    PR.lay(s, pen("navy", k, -58), 1820, 1240, lift=1.2)
    PR.lay(s, pen("white", k, 32), 520, 300, lift=1.2)
    s = PR.finish(s)
    n += save_scene(s, "desk-flatlay")
    # diaries from above on concrete
    k = 5.2
    s = PR.surface(3000, 2000, "concrete", 12)
    PR.lay(s, diary_top("navy", k), 760, 1000, -6, lift=2.6)
    PR.lay(s, diary_top("white", k), 1560, 980, 5, lift=2.6)
    PR.lay(s, pen("navy", k, -78), 2180, 1020, lift=1.2)
    PR.lay(s, pen("sky", k, -84), 2400, 1060, lift=1.2)
    PR.lay(s, pen("white", k, -72), 2620, 980, lift=1.2)
    s = PR.finish(s)
    n += save_scene(s, "diaries-flatlay")
    # pens on navy
    k = 11.0
    s = PR.surface(3000, 2000, "navy", 13)
    ux, uy = -math.sin(math.radians(32)), math.cos(math.radians(32))      # across the pens' direction
    for i, b in enumerate(["navy", "white", "sky"]):
        PR.lay(s, pen(b, k, -32), 1500 + (i - 1) * 250 * ux, 1000 + (i - 1) * 250 * uy, lift=1.4, strength=0.5)
    s = PR.finish(s, 0.05, 0.16)
    n += save_scene(s, "pens-flatlay")
    # laptop stickers: lid + the printed sheet
    k = 5.4
    s = PR.surface(3000, 2000, "desk", 14)
    PR.lay(s, laptop_stickers(int(304 * k)), 1180, 1000, -3, lift=3.0)
    sheet = svg_file_img(OUT / "print" / "laptop-stickers" / "parcelfly-laptop-sticker-sheet-a5.svg", int(148 * k))
    PR.lay(s, PR.paper(sheet, 5), 2470, 1040, 7, lift=1.0)
    s = PR.finish(s)
    n += save_scene(s, "laptop-stickers-flatlay")
    n += cutout(laptop_stickers(1800), "laptop-with-stickers")
    for b in PEN_BARREL:
        n += cutout(pen(b, 9, 0), f"pen-{b}")
    return n


def main():
    n = print_files()
    n += studio_scenes()
    n += flatlays()
    print(f"merch: {n} files")


if __name__ == "__main__":
    main()
