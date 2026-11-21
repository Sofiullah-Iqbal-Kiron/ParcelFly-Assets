"""Bags: print-ready artwork and realistic mockups.

bags/print/paper/        paper shopping bag dielines (cut + fold lines, bleed) and panel previews
bags/print/tote/         canvas tote screen-print artwork
bags/print/carry-bag/    non-woven D-cut and loop-handle carry bags (print + die-cut line)
bags/print/rider-backpack/  rider delivery backpack panels
mockups/bags/            studio scenes, single product shots and transparent cut-outs (see build_mockups.py)
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pfbrand import ROOT, text as T  # noqa: E402
from pfbrand import bags as BG, mockup as MK  # noqa: E402
from pfbrand.brand import NAVY, WHITE  # noqa: E402
from pfbrand.svg import Doc  # noqa: E402

OUT = ROOT / "bags"
ART_PX = 1000
HANDLE = {"navy": NAVY, "kraft": "#B08455", "white": "#FFFFFF", "sky": "#FFFFFF"}


# ------------------------------------------------------------------ print files

def print_files():
    n = 0
    for design, size in [("navy", "medium"), ("kraft", "medium"), ("white", "medium"), ("sky", "small")]:
        doc, panels, sub = BG.paper_dieline(design, size)
        W, D, H = BG.PAPER[size]
        base = OUT / "print" / "paper" / f"parcelfly-paper-bag-{design}-{W}x{D}x{H}"
        doc.save(base.with_name(base.name + "-dieline.svg"), pdf=True, png=[2400])
        for name, p in panels.items():
            p.title = f"Parcel Fly paper bag {design}: {name} panel"
            p.save(base.with_name(base.name + f"-{name}.svg"), png=[1200])
        n += 9
    for design in ["natural", "navy"]:
        d, fab, note = BG.tote_print(design)
        d.title = f"Parcel Fly tote ({design}): {note}"
        d.save(OUT / "print" / "tote" / f"parcelfly-tote-{design}-380x420.svg", pdf=True, png=[1200])
        n += 3
    for design in ["dcut", "loop"]:
        d, fab, note, hole = BG.nonwoven_print(design)
        if hole:
            d.add(f'<path d="{hole}" fill="none" stroke="#FF00FF" stroke-width="0.4"/>')
        W, H = BG.NONWOVEN[design]
        d.title = f"Parcel Fly carry bag ({design}): {note}"
        d.save(OUT / "print" / "carry-bag" / f"parcelfly-carry-bag-{design}-{W}x{H}.svg", pdf=True, png=[1200])
        n += 3
    for name, p in BG.backpack_panels().items():
        p.title = f"Parcel Fly rider delivery backpack: {name} panel"
        p.save(OUT / "print" / "rider-backpack" / f"parcelfly-rider-backpack-{name}.svg", pdf=True, png=[1200])
        n += 3
    return n


# ------------------------------------------------------------------ product renders

def paper(design, yaw, size="medium"):
    panels, sub = BG.paper_panels(design, size)
    W, D, H = BG.PAPER[size]
    front = MK.doc_img(panels["front"], ART_PX)
    side = MK.doc_img(panels["gusset"], int(ART_PX * D / W))
    img, ground = MK.paper_bag(front, side, (W, D, H), sub, HANDLE[design], yaw=yaw, px_w=1300, kraft=design == "kraft",
                               seed=len(design))
    return img, ground, H


def tote(design, yaw):
    d, fab, note = BG.tote_print(design)
    img, ground = MK.flat_bag(MK.doc_img(d, ART_PX), BG.TOTE, "canvas", yaw=yaw, px_w=1100,
                              handles=("strap", fab if design == "natural" else NAVY, 28, 340))
    return img, ground, BG.TOTE[1] + 340


def carry(design, yaw):
    d, fab, note, hole = BG.nonwoven_print(design)
    W, H = BG.NONWOVEN[design]
    if hole:
        img, ground = MK.flat_bag(MK.doc_img(d, ART_PX), (W, H), "nonwoven", yaw=yaw, px_w=1000,
                                  hole=BG.dcut_hole(ART_PX))
        return img, ground, H
    img, ground = MK.flat_bag(MK.doc_img(d, ART_PX), (W, H), "nonwoven", yaw=yaw, px_w=1000,
                              handles=("loop", fab, 30, 200, 0.2))
    return img, ground, H + 200


def backpack(yaw=30):
    P = BG.backpack_panels()
    W, D, H = BG.BACKPACK
    img, ground = MK.box(MK.doc_img(P["front"], 900), MK.doc_img(P["side"], int(900 * D / W)), MK.doc_img(P["top"], 900),
                         BG.BACKPACK, yaw=yaw, px_w=1200)
    return img, ground, H + 40


# ------------------------------------------------------------------ scenes

def row(scene, items, base_y, px_per_mm, gap_px):
    """Lay items out left to right, centred, sizes proportional to their real height (mm)."""
    sized = []
    for img, ground, h_mm in items:
        hp = h_mm * px_per_mm
        bb = img.getchannel("A").getbbox()
        k = hp / (bb[3] - bb[1])
        sized.append((img, ground, hp, (bb[2] - bb[0]) * k))
    total = sum(s[3] for s in sized) + gap_px * (len(sized) - 1)
    x = (scene.width - total) / 2
    for img, ground, hp, wpx in sized:
        MK.place(scene, img, ground, x + wpx / 2, base_y, hp)
        x += wpx + gap_px


def save_scene(scene, name):
    p = ROOT / "mockups" / "bags" / f"parcelfly-{name}"
    p.parent.mkdir(parents=True, exist_ok=True)
    rgb = scene.convert("RGB")
    rgb.save(p.with_suffix(".jpg"), quality=92, optimize=True, progressive=True)
    rgb.resize((rgb.width // 2, rgb.height // 2), Image.LANCZOS).save(p.with_name(p.name + "-preview.jpg"), quality=86)


def cutout(img, name):
    p = ROOT / "mockups" / "bags" / "cutouts" / f"parcelfly-{name}.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    img.crop(img.getchannel("A").getbbox()).save(p)


def main():
    n = print_files()
    nav = paper("navy", 20)
    wht = paper("white", -22)
    kra = paper("kraft", 24)
    sky = paper("sky", -18, "small")
    tn = tote("natural", -9)
    tv = tote("navy", 8)
    dc = carry("dcut", -6)
    lp = carry("loop", 7)
    bp = backpack(30)
    for (img, g, h), name in [(nav, "paper-bag-navy"), (wht, "paper-bag-white"), (kra, "paper-bag-kraft"),
                              (sky, "paper-bag-sky-small"), (tn, "tote-natural"), (tv, "tote-navy"),
                              (dc, "carry-bag-dcut"), (lp, "carry-bag-loop"), (bp, "rider-backpack")]:
        cutout(img, name)
        single = MK.studio(1600, 1800)
        MK.place(single, img, g, 800, 1620, 1350)
        save_scene(single, f"{name}-studio")
    # paper shopping bags
    s = MK.studio(2400, 1500)
    row(s, [wht, nav, kra], 1330, 2.45, 120)
    save_scene(s, "paper-bags")
    # dark hero: white bag + small sky bag on navy
    s = MK.studio(2400, 1500, top="#0C1C9C", bottom="#00004E")
    row(s, [wht, sky], 1330, 2.55, 90)
    save_scene(s, "paper-bags-night")
    # totes
    s = MK.studio(2400, 1500)
    row(s, [tn, tv], 1340, 1.6, 180)
    save_scene(s, "tote-bags")
    # non-woven carry bags
    s = MK.studio(2400, 1500)
    row(s, [dc, lp], 1330, 1.95, 200)
    save_scene(s, "carry-bags")
    # rider delivery backpack with a parcel bag
    s = MK.studio(2400, 1500)
    row(s, [bp, kra], 1330, 2.2, 140)
    save_scene(s, "rider-backpack")
    # family: one row, tall pieces at the ends and the centre, nothing overlapping
    s = MK.studio(3600, 1250, floor=0.78)
    row(s, [tn, wht, sky, bp, nav, dc, kra, tv], 1110, 1.12, 46)
    save_scene(s, "bag-family")
    print(f"bags: {n} print files + mockups")


if __name__ == "__main__":
    main()
