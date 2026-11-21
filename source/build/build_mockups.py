"""Mockups for every physical item in the kit, rendered from the real print files.

mockups/stationery/   business cards, letterhead set, ID cards with lanyards, flyers
mockups/packaging/    shipping cartons (tape, label, stickers), mailer box, rider delivery box, poly mailers, tape
mockups/stamps/       stamp impressions on a delivery note and a shipping label
mockups/stickers/     sticker sheets and loose stickers, seals on packaging
mockups/apparel/      T-shirts (front, back, rider), caps
mockups/signage/      hub shop fronts (day, night), roll-up banner
(bags: mockups/bags from build_bags.py; merchandise: mockups/merch from build_merch.py)
"""
import argparse
import io
import math
import re
import sys
from pathlib import Path

import cairosvg
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pfbrand import ROOT, layout as LY, mockup as MK, props as PR, scenes as SC, text as T  # noqa: E402
from pfbrand import maps as MP  # noqa: E402
from pfbrand.brand import CLOUD, CYAN, MIST, NAVY, SKY, SLATE, WHITE, CONTACT  # noqa: E402
from pfbrand.svg import Doc  # noqa: E402
from pfbrand.text import fmt  # noqa: E402
import build_merch as BM  # noqa: E402

MOCK = ROOT / "mockups"


def art(rel, w):
    """Render a print file (SVG or PNG) from the kit at w px wide."""
    p = ROOT / rel
    if p.suffix == ".png":
        im = Image.open(p).convert("RGBA")
        return im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    return Image.open(io.BytesIO(cairosvg.svg2png(url=str(p), output_width=w))).convert("RGBA")


def mm(rel):
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', (ROOT / rel).read_text()).group(1).split()]
    return vb[2], vb[3]


def sheet(rel, k, seed=1):
    """A printed sheet at k px/mm with paper grain."""
    w, h = mm(rel)
    return PR.paper(art(rel, int(w * k)), seed)


def single(img, g, w=1800, h=1600, max_w=0.76, max_h=0.64, base=0.89):
    """Studio shot sized to fit both the width and the height of the frame."""
    s = MK.studio(w, h)
    bb = img.getchannel("A").getbbox()
    hp = min(h * max_h, w * max_w * (bb[3] - bb[1]) / (bb[2] - bb[0]))
    MK.place(s, img, g, w / 2, h * base, hp)
    return s


def save(scene, folder, name):
    return BM.save_scene(scene, name, MOCK / folder)


def cut(img, folder, name):
    return BM.cutout(img, name, MOCK / folder)


# ------------------------------------------------------------------ stationery

BC = "stationery/business-card/parcelfly-business-card-"


def card_stack(rel, k, n=6, seed=1, step=(0.35, 0.5)):
    """A small stack of cards: copies offset by a fraction of a mm, the lower ones a touch darker."""
    c = sheet(rel, k, seed)
    w, h = c.size
    out = Image.new("RGBA", (w + int(n * step[0] * k) + 4, h + int(n * step[1] * k) + 4), (0, 0, 0, 0))
    edge = Image.new("RGBA", c.size, (236, 238, 242, 255))
    edge.putalpha(c.getchannel("A"))
    for i in range(n - 1, -1, -1):
        out.alpha_composite(c if i == 0 else edge, (int(i * step[0] * k), int(i * step[1] * k)))
    return out


def stationery():
    n = 0
    # hero flat lay: letterhead, envelope, compliment slip, both card designs, ID card, pen
    k = 4.2
    s = PR.surface(3200, 2200, "concrete", 31)
    PR.lay(s, sheet("stationery/letterhead/parcelfly-letterhead-a4.svg", k, 2), 760, 1100, -3, lift=0.8)
    PR.lay(s, sheet("stationery/envelope/parcelfly-envelope-dl.svg", k, 3), 1720, 520, 4, lift=1.2)
    PR.lay(s, sheet("stationery/compliment-slip/parcelfly-compliment-slip.svg", k, 4), 1760, 1090, -2, lift=0.8)
    PR.lay(s, card_stack(BC + "a-front-navy.svg", k, 5, 5), 1500, 1660, 8, lift=1.4)
    PR.lay(s, sheet(BC + "a-back-white.svg", k, 6), 1980, 1720, -6, lift=0.9)
    PR.lay(s, sheet(BC + "b-front-white.svg", k, 7), 2450, 1580, 12, lift=0.9)
    PR.lay(s, PR.punch_slot(sheet("stationery/id-card/parcelfly-id-card-manager-front.svg", k, 8), k), 2620, 880, -8,
           lift=1.2)
    PR.lay(s, BM.pen("navy", k, -62), 1270, 1240, lift=1.2)
    n += save(PR.finish(s), "stationery", "stationery-flatlay")
    # business cards on navy felt: both designs, fronts and backs
    k = 9.0
    s = PR.surface(3000, 2000, "navy", 32)
    PR.lay(s, card_stack(BC + "a-front-navy.svg", k, 8, 9), 820, 640, -12, lift=1.5, strength=0.5)
    PR.lay(s, sheet(BC + "a-back-white.svg", k, 10), 1640, 760, 6, lift=1.1, strength=0.5)
    PR.lay(s, card_stack(BC + "b-front-white.svg", k, 8, 11), 1380, 1430, 9, lift=1.5, strength=0.5)
    PR.lay(s, sheet(BC + "b-back-navy.svg", k, 12), 2250, 1300, -5, lift=1.1, strength=0.5)
    n += save(PR.finish(s, 0.05, 0.18), "stationery", "business-cards")
    # letterhead set on wood
    k = 3.6
    s = PR.surface(3000, 2000, "wood", 33)
    PR.lay(s, sheet("stationery/letterhead/parcelfly-letterhead-a4.svg", k, 13), 1050, 1000, 3, lift=0.8)
    PR.lay(s, sheet("stationery/envelope/parcelfly-envelope-dl.svg", k, 14), 2120, 700, -5, lift=1.2)
    PR.lay(s, sheet("stationery/compliment-slip/parcelfly-compliment-slip.svg", k, 15), 2150, 1360, 4, lift=0.8)
    PR.lay(s, BM.pen("white", k, 72), 1620, 1100, lift=1.2)
    n += save(PR.finish(s), "stationery", "letterhead-set")
    # ID cards with lanyards
    k = 7.5
    s = PR.surface(3000, 2000, "desk", 34)
    strap_svg = lanyard_print(k)
    cards = [("manager", 600, -4), ("hub-staff", 1220, 3), ("rider", 1840, -2)]
    clip = PR.lanyard_clip(k)
    for i, (who, cx, ang) in enumerate(cards):
        card = PR.punch_slot(sheet(f"stationery/id-card/parcelfly-id-card-{who}-front.svg", k, 20 + i), k)
        cy = 1250
        top = cy - card.height / 2
        crimp = top - 18 * k - clip.height / 2           # top of the clip's crimp
        for side, a in ((-1, 9), (1, -9)):
            strap = PR.lanyard(260, k, NAVY, strap_svg, seed=30 + i)
            ra = math.radians(a)
            bx, by = cx + side * 5.5 * k, crimp + 3 * k   # strap ends run into the crimp
            PR.lay(s, strap, bx - strap.height / 2 * math.sin(ra), by - strap.height / 2 * math.cos(ra), a, lift=0.6)
        PR.lay(s, card, cx, cy, ang, lift=1.0)
        PR.lay(s, clip, cx, top - 18 * k, 0, lift=0.8)
    PR.lay(s, sheet("stationery/id-card/parcelfly-id-card-back.svg", k, 40), 2520, 1300, 8, lift=1.0)
    n += save(PR.finish(s), "stationery", "id-cards-lanyards")
    # flyers: front and back, fanned
    k = 5.2
    s = PR.surface(3000, 2000, "concrete", 35)
    fr = sheet("signage/flyer/parcelfly-flyer-a5-front.svg", k, 41)
    bk = sheet("signage/flyer/parcelfly-flyer-a5-back.svg", k, 42)
    for i in range(3):
        PR.lay(s, fr, 1060 - i * 22, 1010 + i * 10, -8 + i * 3.5, lift=0.7)
    PR.lay(s, bk, 1960, 990, 7, lift=0.9)
    n += save(PR.finish(s), "stationery", "flyers-a5")
    return n


def lanyard_print(k):
    """Repeat on a 20 mm strap: white symbol and PARCEL FLY, reading along the strap."""
    from pfbrand.bags import vertical_text
    w, h = 20 * k, 260 * k
    out = []
    for i in range(4):
        y = (20 + i * 65) * k
        out.append(LY.symbol_at("ondark", w / 2, y, 14 * k))
        out.append(vertical_text("PARCEL FLY", "montserrat", 5.2 * k, w / 2, y + 30 * k, WHITE, 800, rot=-90))
    return "".join(out)


# ------------------------------------------------------------------ packaging

def kraft_faces(k):
    """Shipping carton 400 x 300 x 250 mm: navy one-colour print, branded tape over the flap seam, shipping label,
    handling stickers and a tamper seal over the tape end."""
    W, D, H = 400, 300, 250
    tape = art("packaging/tape/parcelfly-tape-48mm-repeat-navy.svg", 1800)
    top = PR.kraft(int(W * k), int(D * k), 1)
    seam = Image.new("RGBA", (int(W * k), max(2, int(1.2 * k))), (90, 62, 36, 200))
    top.alpha_composite(seam, (0, int(D * k / 2)))
    PR.stick(top, PR.tape_strip(tape, int(W * k), int(48 * k)), W * k / 2, D * k / 2, k=k)
    label = PR.paper(art("stationery/shipping-label/parcelfly-shipping-label-4x6.svg", int(101.6 * k)), 3)
    PR.stick(top, label, W * k * 0.42, D * k * 0.765, angle=90, k=k)
    PR.stick(top, art("stickers/handling/parcelfly-sticker-fragile.svg", int(92 * k)), W * k * 0.82, D * k * 0.78,
             angle=-4, k=k)
    front = PR.kraft(int(W * k), int(H * k), 2)
    logo = Doc(W, H, unit="mm", title="print")
    frag, _ = LY.place_logo("horizontal", NAVY, W * 0.08, H * 0.12, w=W * 0.5)
    logo.add(frag)
    logo.add(T.text(CONTACT["web"], "montserrat", 9, W * 0.08, H * 0.88, NAVY, "start", 700))
    pr = MK.doc_img(logo, int(W * k))
    a = pr.getchannel("A").point(lambda v: int(v * 0.88))
    pr.putalpha(a)
    front.alpha_composite(pr)
    PR.stick(front, art("stickers/handling/parcelfly-sticker-this-side-up.svg", int(92 * k)), W * k * 0.8, H * k * 0.7,
             k=k)
    side = PR.kraft(int(D * k), int(H * k), 3)
    PR.stick(side, PR.tape_strip(tape, int(70 * k), int(48 * k), angle=90), D * k / 2, 35 * k, k=k)
    PR.stick(side, art("stickers/brand/parcelfly-sticker-tamper-seal.svg", int(102 * k)), D * k / 2, 70 * k, k=k)
    PR.stick(side, art("stickers/brand/parcelfly-sticker-scan-to-track.svg", int(52 * k)), D * k / 2, H * k * 0.66, k=k)
    return top, front, side, (W, D, H)


def mailer_faces(k):
    """Printed mailer box 300 x 200 x 100 mm: the top panel art; front and sides in the same white, dots and bar."""
    W, D, H = 300, 200, 100
    top = art("packaging/box/parcelfly-box-top-panel.svg", int(W * k))

    def face(w, h, logo):
        d = Doc(w, h, unit="mm", title="face")
        d.rect(0, 0, w, h, WHITE)
        SC.lattice(d, CLOUD, cell=20)
        gid = SC.uid("fb")
        d.defs_add(LY.flight_gradient(gid))
        d.rect(0, h - 6, w, 6, f"url(#{gid})")
        if logo:
            frag, _ = LY.place_logo("horizontal", "color", w * 0.3, h * 0.28, w=w * 0.4, align="center")
            d.add(frag)
            d.add(T.text(CONTACT["web"], "montserrat", 4.2, w / 2, h * 0.74, SLATE, "middle", 700))
        else:
            d.add(T.text("ALWAYS, EVERYWHERE", "montserrat", 4.2, w / 2, h * 0.52, SKY, "middle", 700, tracking=0.2))
        return PR.paper(MK.doc_img(d, int(w * k)), 4, 0.015, 0.01)

    return top, face(W, H, True), face(D, H, False), (W, D, H)


def delivery_box_faces(k):
    """Rider top box 460 x 460 x 440 mm, navy shell: square decal on the back (facing traffic), side decal."""
    W, D, H = 460, 460, 440

    def shell(w, h, decal=None, dw=None):
        base = Image.new("RGBA", (int(w * k), int(h * k)), NAVY)
        base = MK.textured(base, MK.noise(base.width, base.height, 7, 1.0), 0.03)
        if decal:
            im = art(decal, int(dw * k))
            PR.stick(base, im, w * k / 2, h * k * 0.53, lift=0.1, k=k, shadow=0.2)
        lid = Image.new("RGBA", (base.width, max(2, int(2 * k))), (0, 0, 40, 255))
        base.alpha_composite(lid, (0, int(62 * k)))
        hl = Image.new("RGBA", (base.width, max(1, int(1 * k))), (90, 110, 220, 180))
        base.alpha_composite(hl, (0, int(64 * k)))
        return base

    top = Image.new("RGBA", (int(W * k), int(D * k)), "#0A0A8C")
    top = MK.textured(top, MK.noise(top.width, top.height, 8, 1.0), 0.03)
    frag, _ = LY.place_logo("horizontal", "ondark", 0, 0, w=W * 0.5)
    lg = Doc(W, D, unit="mm", title="lid")
    lg.add(f'<g transform="translate({W * 0.25} {D * 0.42})">{frag}</g>')
    top.alpha_composite(MK.doc_img(lg, top.width))
    front = shell(W, H, "packaging/delivery-box/parcelfly-delivery-box-decal-square-400x400.svg", 400)
    side = shell(D, H, "packaging/delivery-box/parcelfly-delivery-box-decal-side-400x300.svg", 400)
    return top, front, side, (W, D, H)


def packaging():
    n = 0
    k = 3.0
    kt, kf, ks, kd = kraft_faces(k)
    kraft_img, kraft_g, kraft_s = PR.carton(kt, kf, ks, kd, yaw=30, px_w=1300, pitch=21)
    mt, mf, ms, md = mailer_faces(4.0)
    mail_img, mail_g, mail_s = PR.carton(mt, mf, ms, md, yaw=-26, px_w=1100, pitch=27)
    dt, df, dsd, dd = delivery_box_faces(2.6)
    dbox_img, dbox_g, dbox_s = PR.carton(dt, df, dsd, dd, yaw=32, px_w=1200, pitch=12)
    tape_n, _ = PR.tape_roll(art("packaging/tape/parcelfly-tape-48mm-repeat-navy.svg", 2400), edge="#0B1460", px_w=600)
    tape_w, _ = PR.tape_roll(art("packaging/tape/parcelfly-tape-48mm-repeat-white.svg", 2400), px_w=600)
    tape_g = PR.Lathe(55, 48, 0, 600, 30.0, 1).ground(55)

    def mm_h(img, scale):
        bb = img.getchannel("A").getbbox()
        return (bb[3] - bb[1]) / scale

    items = {"shipping-carton": (kraft_img, kraft_g, mm_h(kraft_img, kraft_s)),
             "mailer-box": (mail_img, mail_g, mm_h(mail_img, mail_s)),
             "rider-delivery-box": (dbox_img, dbox_g, mm_h(dbox_img, dbox_s)),
             "tape-navy": (tape_n, tape_g, 48 * 0.87 + 110 * 0.5), "tape-white": (tape_w, tape_g, 48 * 0.87 + 110 * 0.5)}
    for name, (img, g, h) in items.items():
        n += cut(img, "packaging", name)
        n += save(single(img, g, max_h=0.64 if "tape" not in name else 0.42), "packaging", f"{name}-studio")
    s = MK.studio(2600, 1500)
    BM.row(s, [items["mailer-box"], items["shipping-carton"], items["tape-navy"], items["tape-white"]], 1320, 2.4, 110)
    n += save(s, "packaging", "packaging-family")
    s = MK.studio(2400, 1500, top="#0C1C9C", bottom="#00004E")
    BM.row(s, [items["rider-delivery-box"], items["shipping-carton"]], 1330, 2.0, 140)
    n += save(s, "packaging", "rider-delivery-box-night")
    # poly mailers, front and back, on concrete
    k = 3.8
    s = PR.surface(3000, 2000, "concrete", 51)
    PR.lay(s, PR.poly_mailer(art("packaging/mailer/parcelfly-poly-mailer-front.svg", 1400), k, 5), 1040, 1000, -6,
           lift=0.9)
    PR.lay(s, PR.poly_mailer(art("packaging/mailer/parcelfly-poly-mailer-back.svg", 1400), k, 6), 2000, 1010, 5,
           lift=0.9)
    n += save(PR.finish(s), "packaging", "poly-mailers")
    return n


# ------------------------------------------------------------------ stamps, stickers, seals

def delivery_note(k):
    """The A4 letterhead filled in as a delivery note (sample data) to carry stamp impressions."""
    src = (ROOT / "stationery/letterhead/parcelfly-letterhead-a4.svg").read_text()
    inner = re.sub(r"<title>.*?</title>", "", re.search(r"<svg[^>]*>(.*)</svg>", src, re.S).group(1))
    d = Doc(210, 297, unit="mm", title="Delivery note (sample)")
    d.add(inner)
    x0 = 20
    d.add(T.text("DELIVERY NOTE", "montserrat", 6.2, x0, 74, NAVY, "start", 800, tracking=0.06))
    d.add(T.text("Merchant: Sample Fashion House   Hub: Mirpur   Date: 21 Nov 2026", "montserrat", 3.1, x0, 84, SLATE,
                 "start", 600))
    rows = [("PF 2511 2100 01", "Dhanmondi", "Delivered", "1,250"), ("PF 2511 2100 02", "Uttara", "Delivered", "860"),
            ("PF 2511 2100 03", "Mohammadpur", "Delivered", "2,400"), ("PF 2511 2100 04", "Badda", "Returned", "0"),
            ("PF 2511 2100 05", "Mirpur 10", "Delivered", "1,780")]
    y = 100
    cols = [x0, 70, 118, 160]
    for c, hd in zip(cols, ["PARCEL ID", "AREA", "STATUS", "COD (BDT)"]):
        d.add(T.text(hd, "montserrat", 2.8, c, y, NAVY, "start", 800, tracking=0.1))
    d.rect(x0, y + 3, 170, 0.35, NAVY)
    for i, r in enumerate(rows):
        yy = y + 11 + i * 9
        for c, v in zip(cols, r):
            d.add(T.text(v, "geist-mono" if c == x0 else "montserrat", 3.2, c, yy, "#1E2433", "start", 500))
        d.rect(x0, yy + 3.2, 170, 0.2, MIST)
    d.add(T.text("Received in good condition.", "montserrat", 3.2, x0, 168, SLATE, "start", 600))
    d.add(T.text("Signature", "montserrat", 2.8, x0, 214, SLATE, "start", 700, tracking=0.1))
    d.rect(x0, 206, 60, 0.3, SLATE)
    sig = ('<path d="M24 202c4-6 7-9 9-6s-3 9 1 8 6-11 9-10-2 8 1 8 7-7 9-6 1 5 4 4 8-5 10-4" fill="none" '
           'stroke="#1F3FA0" stroke-width="0.6" stroke-linecap="round"/>')
    d.add(sig)
    return PR.paper(MK.doc_img(d, int(210 * k)), 61)


def stamps():
    n = 0
    k = 4.0
    note = delivery_note(k)
    inked = ROOT / "stamps/digital-inked"
    for f, x, y, w, op in [("parcelfly-stamp-delivered.png", 120, 150, 70, 0.92),
                           ("parcelfly-hub-stamp-mirpur.png", 150, 192, 44, 0.88),
                           ("parcelfly-company-seal.png", 92, 230, 40, 0.85),
                           ("parcelfly-stamp-paid.png", 26, 236, 62, 0.9)]:
        im = Image.open(inked / f).convert("RGBA")
        im = im.resize((int(w * k), int(w * k * im.height / im.width)), Image.LANCZOS)
        note = PR.ink_on(note, im, int(x * k - im.width / 2), int(y * k - im.height / 2), op)
    s = PR.surface(3000, 2000, "wood", 62)
    PR.lay(s, note, 1250, 1000, -5, lift=0.8)
    label = PR.paper(art("stationery/shipping-label/parcelfly-shipping-label-4x6.svg", int(101.6 * k)), 63)
    im = Image.open(inked / "parcelfly-stamp-delivered.png").convert("RGBA")
    im = im.resize((int(62 * k), int(62 * k * im.height / im.width)), Image.LANCZOS)
    label = PR.ink_on(label, im, int(20 * k), int(70 * k), 0.9)
    kr = PR.kraft(int(240 * k), int(200 * k), 64)
    PR.stick(kr, label, kr.width * 0.5, kr.height * 0.5, angle=4, k=k)
    PR.lay(s, kr, 2400, 1150, 8, lift=1.6)
    PR.lay(s, BM.pen("navy", k, 50), 2150, 380, lift=1.2)
    n += save(PR.finish(s), "stamps", "stamps-on-documents")
    return n


def stickers():
    n = 0
    k = 3.6
    s = PR.surface(3000, 2000, "desk", 71)
    for rel, x, y, a, seed in [("stickers/sheet/parcelfly-sticker-sheet-a4-p1.svg", 820, 1000, -5, 72),
                               ("stickers/sheet/parcelfly-sticker-sheet-a4-p2.svg", 1660, 1040, 4, 73)]:
        st = sheet(rel, k, seed)
        liner = PR.paper(Image.new("RGBA", st.size, (248, 248, 246, 255)), seed)
        liner.alpha_composite(st)
        PR.lay(s, liner, x, y, a, lift=0.8)
    loose = [("stickers/die-cut/parcelfly-sticker-symbol-diecut.svg", 78, 2420, 520, 14),
             ("stickers/round/parcelfly-sticker-round-logo.svg", 62, 2560, 960, -8),
             ("stickers/round/parcelfly-sticker-thank-you.svg", 66, 2330, 1330, 6),
             ("stickers/handling/parcelfly-sticker-fragile.svg", 92, 2580, 1700, -12),
             ("stickers/brand/parcelfly-sticker-delivered-by.svg", 82, 2280, 1800, 9)]
    for rel, wmm, x, y, a in loose:
        PR.lay(s, art(rel, int(wmm * k)), x, y, a, lift=0.5)
    n += save(PR.finish(s), "stickers", "stickers-flatlay")
    # seals on packaging: a kraft envelope sealed with a round seal, a box flap, loose seals
    k = 4.2
    s = PR.surface(3000, 2000, "concrete", 74)
    env = PR.kraft(int(229 * k), int(162 * k), 75, "#C8A27A", flutes=False)
    from PIL import ImageDraw
    dr = ImageDraw.Draw(env)
    w, h = env.size
    dr.line([(0, 0), (w / 2, h * 0.58), (w, 0)], fill=(140, 104, 68, 255), width=max(2, int(0.6 * k)))
    PR.stick(env, art("seals/color/parcelfly-seal-official-partner-color.svg", int(46 * k)), w / 2, h * 0.58, k=k)
    PR.lay(s, env, 1000, 820, -6, lift=1.0)
    box = PR.kraft(int(200 * k), int(150 * k), 76)
    PR.stick(box, PR.tape_strip(art("packaging/tape/parcelfly-tape-48mm-repeat-white.svg", 1600), box.width,
                                int(48 * k)), box.width / 2, box.height / 2, k=k)
    PR.stick(box, art("seals/navy/parcelfly-seal-secure-packaging-navy.svg", int(44 * k)), box.width * 0.78,
             box.height * 0.5, k=k)
    PR.lay(s, box, 1050, 1580, 4, lift=1.6)
    for i, (rel, x, y, a) in enumerate([("seals/color/parcelfly-seal-verified-merchant-color.svg", 2050, 520, 8),
                                        ("seals/navy/parcelfly-seal-fast-delivery-navy.svg", 2450, 760, -12),
                                        ("seals/light/parcelfly-seal-bn-tagline-light.svg", 2080, 1030, 5),
                                        ("seals/color/parcelfly-seal-quality-checked-color.svg", 2480, 1300, -4),
                                        ("seals/color/parcelfly-seal-cash-on-delivery-color.svg", 2100, 1560, 10),
                                        ("seals/navy/parcelfly-seal-heritage-navy.svg", 2500, 1780, -9)]):
        PR.lay(s, art(rel, int(48 * k)), x, y, a, lift=0.4)
    n += save(PR.finish(s), "stickers", "seals-on-packaging")
    return n


# ------------------------------------------------------------------ apparel

def apparel():
    n = 0
    k = 2.3
    label = Doc(46, 20, unit="mm", title="neck label")
    label.add('<rect width="46" height="20" rx="1.5" fill="#FFFFFF"/>')
    frag, _ = LY.place_logo("horizontal", "color", 4, 5, w=38, h=10, align="center", valign="middle")
    label.add(frag)
    lab = MK.doc_img(label, 400)
    chest = art("apparel/tshirt/parcelfly-tshirt-chest-ondark.svg", 1200)
    back = art("apparel/tshirt/parcelfly-tshirt-back-ondark.svg", 2000)
    rider_back = art("apparel/tshirt/parcelfly-tshirt-back-rider-ondark.svg", 2000)
    tf = PR.tshirt(chest, (95, 165, 100), "front", k=k, label_img=lab)
    tb = PR.tshirt(back, (0, 120, 280), "back", k=k, seed=8)
    tr = PR.tshirt(rider_back, (0, 120, 280), "back", k=k, seed=9)
    for img, name in [(tf, "tshirt-front"), (tb, "tshirt-back"), (tr, "tshirt-rider-back")]:
        n += cut(img, "apparel", name)
    s = PR.surface(4200, 2400, "concrete", 81)
    PR.lay(s, tf, 1080, 1200, -2, lift=1.0)
    PR.lay(s, tb, 3120, 1200, 2, lift=1.0)
    n += save(PR.finish(s), "apparel", "tshirt-front-back")
    s = PR.surface(2600, 2400, "wood", 82)
    PR.lay(s, tr, 1300, 1200, 0, lift=1.0)
    n += save(PR.finish(s), "apparel", "tshirt-rider-back")
    sym = Doc(70, 32, unit="mm", title="cap front, full colour")
    sym.add(LY.symbol_at("color", 35, 16, 62))
    caps = [("cap-navy-colour-embroidery", art("apparel/cap/parcelfly-cap-front-colour.svg", 1600), "#141C5C", 11),
            ("cap-charcoal-white-embroidery", art("apparel/cap/parcelfly-cap-front-embroidery-white.svg", 1600),
             "#2C3039", 12),
            ("cap-white-colour-embroidery", MK.doc_img(sym, 1600), "#F2F4F7", 13)]
    row_items = []
    for name, a_img, colour, seed in caps:
        img, g = PR.cap(a_img, colour, px_w=1000, seed=seed)
        n += cut(img, "apparel", name)
        row_items.append((img, g, 170))
    s = MK.studio(3000, 1400)
    BM.row(s, row_items, 1180, 4.4, 150)
    n += save(s, "apparel", "caps")
    return n


# ------------------------------------------------------------------ signage

def signage():
    n = 0
    for hub in [h["key"] for h in MP.hubs()]:
        sign = art(f"signage/signboard/parcelfly-signboard-{hub}-hub.svg", 2400)
        n += save(PR.storefront(sign, seed=len(hub) * 7), "signage", f"storefront-{hub}-hub")
    sign = art("signage/signboard/parcelfly-signboard.svg", 2400)
    n += save(PR.storefront(sign, night=True, seed=5), "signage", "storefront-night")
    ban = art("signage/roll-up/parcelfly-rollup-850x2000.svg", 900)
    img, g = PR.rollup(ban, px_w=800)
    n += cut(img, "signage", "rollup-banner")
    s = MK.studio(1800, 2400, floor=0.8)
    MK.place(s, img, g, 900, 2250, 2050, cast=0.12)
    n += save(s, "signage", "rollup-banner-studio")
    return n


AREAS = {"stationery": stationery, "packaging": packaging, "stamps": stamps, "stickers": stickers,
         "apparel": apparel, "signage": signage}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=list(AREAS))
    args = ap.parse_args()
    n = 0
    for name, fn in AREAS.items():
        if args.only and name != args.only:
            continue
        n += fn()
    print(f"mockups: {n} files")


if __name__ == "__main__":
    main()
