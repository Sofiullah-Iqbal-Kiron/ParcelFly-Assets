"""Print and environment applications (mm documents, RGB PDFs + previews; CMYK values are in the guidelines).

stationery/  business cards, letterhead (PDF + Word), envelope DL, compliment slip, ID cards, shipping label
packaging/   tape, poly mailer, box panel, rider delivery-box decals
apparel/     T-shirt chest/back prints, cap
signage/     hub signboards, roll-up banner, A5 flyer
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pfbrand import ROOT, layout as LY, scenes as SC, symbol as S, text as T  # noqa: E402
from pfbrand import pictograms as P  # noqa: E402
from pfbrand import maps as MP  # noqa: E402
from pfbrand.brand import (AQUA, CLOUD, CONTACT, COBALT, CYAN, INK, MINT, MIST, NAVY, SKY, SLATE,  # noqa: E402
                           TAGLINE, TAGLINE_BN, WHITE, NAME_BN)
from pfbrand.svg import Doc, render_png  # noqa: E402
from pfbrand.text import fmt  # noqa: E402

OUT = ROOT
DPI = 300


def px(mm, dpi=DPI):
    return int(round(mm / 25.4 * dpi))


def save(d: Doc, path: Path, dpi=DPI, max_px=4000):
    path.parent.mkdir(parents=True, exist_ok=True)
    d.save(path.with_suffix(".svg"), pdf=True)
    render_png(d.svg(), path.with_suffix(".png"), min(px(d.w, dpi), max_px), d.w, d.h)
    return 3


def flight_bar(d, x, y, w, h):
    gid = SC.uid("fb")
    d.defs_add(LY.flight_gradient(gid, 0))
    d.rect(x, y, w, h, f"url(#{gid})")


def contact_rows(d, x, y, size, colour, icon_colour, gap=1.65, items=None):
    items = items or [("phone", CONTACT["phone_intl"]), ("mail", CONTACT["email"]), ("web", CONTACT["web"]),
                      ("track", CONTACT["address"])]
    for i, (ic, txt) in enumerate(items):
        yy = y + i * size * gap
        d.add(P.icon(ic, x, yy - size * 0.95, size * 1.15, icon_colour, 3.6))
        d.add(T.text(txt, "montserrat", size, x + size * 1.75, yy, colour, "start", 600))
    return y + (len(items) - 1) * size * gap


# ================================================================== stationery

def business_cards():
    out = OUT / "stationery" / "business-card"
    W, H, B = 89.0, 51.0, 3.0  # trim, bleed
    n = 0

    def front_navy():
        d = Doc(W + 2 * B, H + 2 * B, unit="mm", title="Business card front (navy)")
        d.rect(0, 0, d.w, d.h, NAVY)
        SC.glow(d, d.w * 0.95, 0, 60, COBALT, 0.8)
        hh = d.h * 1.25
        d.add(SC.watermark(COBALT, d.w - S.WIDTH * hh / S.HEIGHT * 0.62, (d.h - hh) / 2, hh, 0.7))
        frag, _ = LY.place_logo("horizontal", "ondark", B + 7, B, w=52, h=H, valign="middle", tagline="en")
        d.add(frag)
        return d

    def front_white():
        d = Doc(W + 2 * B, H + 2 * B, unit="mm", title="Business card front (white)")
        d.rect(0, 0, d.w, d.h, WHITE)
        frag, _ = LY.place_logo("stacked", "color", B + 20, B + 8, w=W - 40, h=H - 19, align="center", valign="middle",
                                tagline="en")
        d.add(frag)
        flight_bar(d, 0, d.h - B - 2.2, d.w, 2.2 + B)
        return d

    def back(dark):
        d = Doc(W + 2 * B, H + 2 * B, unit="mm", title="Business card back")
        bg, fg, sub, ic = (NAVY, WHITE, CYAN, CYAN) if dark else (WHITE, NAVY, SKY, SKY)
        d.rect(0, 0, d.w, d.h, bg)
        x0, y0 = B + 6, B + 6
        d.add(T.text("Full Name", "montserrat", 4.3, x0, y0 + 3.6, fg, "start", 800))
        d.add(LY.label("Designation", x0, y0 + 8.3, 2.1, sub, tracking=0.16))
        contact_rows(d, x0, y0 + 17.2, 2.15, fg, ic, gap=2.05,
                     items=[("phone", CONTACT["phone_intl"]), ("mail", CONTACT["email"]), ("web", CONTACT["web"]),
                            ("track", "61/2 Nazimuddin Road, Bongshal, Dhaka 1000")])
        q = 16.5
        qx, qy = B + W - 6 - q, B + 6
        d.rect(qx - 1, qy - 1, q + 2, q + 2, WHITE, rx=1.2)
        d.add(LY.qr(CONTACT["url"], qx, qy, q, NAVY, quiet=1))
        frag, _ = LY.place_logo("symbol", "ondark" if dark else "color", qx, qy + q + 3.5, w=q, h=8, align="center")
        d.add(frag)
        if not dark:
            flight_bar(d, 0, d.h - B - 1.6, d.w, 1.6 + B)
        return d

    n += save(front_navy(), out / "parcelfly-business-card-a-front-navy")
    n += save(back(False), out / "parcelfly-business-card-a-back-white")
    n += save(front_white(), out / "parcelfly-business-card-b-front-white")
    n += save(back(True), out / "parcelfly-business-card-b-back-navy")
    return n


def letterhead():
    out = OUT / "stationery" / "letterhead"
    W, H = 210.0, 297.0

    def header(d, y0=0.0):
        flight_bar(d, 0, y0, W, 3.2)
        frag, _ = LY.place_logo("horizontal", "color", 18, y0 + 14, w=58, h=14)
        d.add(frag)
        ys = y0 + 16.5
        for i, line in enumerate([CONTACT["phone_intl"], CONTACT["email"], CONTACT["web"]]):
            d.add(T.text(line, "montserrat", 2.75, W - 18, ys + i * 4.3, SLATE, "end", 600))

    def footer(d, y0=H):
        d.rect(18, y0 - 17, W - 36, 0.25, MIST)
        d.add(T.text(CONTACT["address"], "montserrat", 2.5, 18, y0 - 11, SLATE, "start", 500))
        bn_w = T.advance(TAGLINE_BN, "mina-bold", 2.7)
        d.add(T.text(TAGLINE_BN, "mina-bold", 2.7, W - 18, y0 - 11, SKY, "end"))
        d.add(T.text(f"{TAGLINE}  ·", "montserrat", 2.5, W - 18 - bn_w - 1.4, y0 - 11, SKY, "end", 700))

    d = Doc(W, H, unit="mm", title="Parcel Fly letterhead A4")
    d.rect(0, 0, W, H, WHITE)
    hh = 150
    d.add(SC.watermark(CLOUD, W - S.WIDTH * hh / S.HEIGHT * 0.55, H - hh * 0.72, hh))
    header(d)
    footer(d)
    n = save(d, out / "parcelfly-letterhead-a4", dpi=200)
    # Word template: header and footer as images, body editable
    hd = Doc(W, 34, unit="mm", title="Letterhead header")
    hd.rect(0, 0, W, 34, WHITE)
    header(hd)
    fd = Doc(W, 20, unit="mm", title="Letterhead footer")
    fd.rect(0, 0, W, 20, WHITE)
    footer(fd, 20)
    render_png(hd.svg(), out / "letterhead-header.png", px(W), W, 34)
    render_png(fd.svg(), out / "letterhead-footer.png", px(W), W, 20)
    from docx import Document
    from docx.shared import Mm, Pt, RGBColor
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(W), Mm(H)
    sec.left_margin = sec.right_margin = Mm(18)
    sec.top_margin, sec.bottom_margin = Mm(42), Mm(28)
    sec.header_distance, sec.footer_distance = Mm(0), Mm(0)
    for part, img, hmm in [(sec.header, out / "letterhead-header.png", 34), (sec.footer, out / "letterhead-footer.png", 20)]:
        p = part.paragraphs[0]
        p.paragraph_format.left_indent = Mm(-18)
        p.paragraph_format.right_indent = Mm(-18)
        p.add_run().add_picture(str(img), width=Mm(W), height=Mm(hmm))
    style = doc.styles["Normal"]
    style.font.name = "Montserrat"
    style.font.size = Pt(10.5)
    style.font.color.rgb = RGBColor(0x0B, 0x11, 0x33)
    doc.add_paragraph("Date: ")
    doc.add_paragraph("")
    doc.add_paragraph("Dear ,")
    doc.add_paragraph("Start typing your letter here.")
    doc.save(str(out / "parcelfly-letterhead-a4.docx"))
    return n + 3


def envelope_and_slip():
    out = OUT / "stationery"
    n = 0
    W, H = 220.0, 110.0
    d = Doc(W, H, unit="mm", title="Parcel Fly envelope DL")
    d.rect(0, 0, W, H, WHITE)
    frag, _ = LY.place_logo("horizontal", "color", 14, 12, w=52, h=12)
    d.add(frag)
    for i, line in enumerate(CONTACT["address_lines"] + [f"{CONTACT['phone_intl']}  ·  {CONTACT['web']}"]):
        d.add(T.text(line, "montserrat", 2.6, 14, 31 + i * 4.0, SLATE, "start", 500))
    flight_bar(d, 0, H - 4, W, 4)
    n += save(d, out / "envelope" / "parcelfly-envelope-dl", dpi=200)
    W, H = 210.0, 99.0
    d = Doc(W, H, unit="mm", title="Parcel Fly compliment slip")
    d.rect(0, 0, W, H, WHITE)
    frag, _ = LY.place_logo("horizontal", "color", 16, 14, w=58, h=14)
    d.add(frag)
    d.add(T.text("With compliments", "montserrat", 6.2, 16, 46, NAVY, "start", 800))
    d.add(T.text("শুভেচ্ছাসহ", "mina-bold", 5.2, 16, 55, SKY, "start"))
    contact_rows(d, 120, 18, 2.7, NAVY, SKY, gap=2.2)
    flight_bar(d, 0, H - 3, W, 3)
    n += save(d, out / "compliment-slip" / "parcelfly-compliment-slip", dpi=200)
    return n


def id_cards():
    out = OUT / "stationery" / "id-card"
    W, H, B = 54.0, 85.6, 2.0
    n = 0
    for role, chip_bg in [("Rider", SKY), ("Hub staff", COBALT), ("Manager", NAVY)]:
        d = Doc(W + 2 * B, H + 2 * B, unit="mm", title=f"Parcel Fly ID card front ({role})")
        d.rect(0, 0, d.w, d.h, WHITE)
        d.rect(0, 0, d.w, B + 26, NAVY)
        SC.glow(d, d.w, 0, 40, COBALT, 0.8)
        frag, _ = LY.place_logo("horizontal", "ondark", B + 6, B + 6, w=W - 12, h=11, align="center", valign="middle")
        d.add(frag)
        cx, cy, hd = d.w / 2, B + 37, 15.5
        d.add(f'<path d="{LY.diamond_path(cx, cy, hd + 1.4, 1.2)}" fill="{WHITE}"/>')
        d.add(f'<path d="{LY.diamond_path(cx, cy, hd, 1.0)}" fill="{MIST}"/>')
        d.add(P.icon("user", cx - 7, cy - 7.5, 14, SLATE, 3.2))
        d.add(T.text("PHOTO", "montserrat", 1.6, cx, cy + 9.5, SLATE, "middle", 700, tracking=0.2))
        d.add(T.text("Full Name", "montserrat", 4.4, cx, B + 61.5, NAVY, "middle", 800))
        c, cb = LY.chip(cx, B + 64.2, role.upper(), 2.1, chip_bg, WHITE, tracking=0.14, anchor="middle")
        d.add(c)
        d.add(T.text("ID  PF-0000", "geist-mono", 2.4, cx, B + 74.2, SLATE, "middle", 600))
        d.add(T.text("HUB", "montserrat", 1.7, B + 9, B + 79.2, SLATE, "start", 800, tracking=0.16))
        d.rect(B + 16, B + 79.4, W - 25, 0.22, MIST)
        flight_bar(d, 0, d.h - B - 3, d.w, 3 + B)
        n += save(d, out / f"parcelfly-id-card-{role.lower().replace(' ', '-')}-front")
    d = Doc(W + 2 * B, H + 2 * B, unit="mm", title="Parcel Fly ID card back")
    d.rect(0, 0, d.w, d.h, NAVY)
    SC.lattice(d, COBALT, cell=6, opacity=0.6)
    cx = d.w / 2
    frag, _ = LY.place_logo("symbol", "ondark", cx - 12, B + 7, w=24, align="center")
    d.add(frag)
    lines = ["This card is the property of Parcel Fly.", "If found, please return it to:"]
    for i, ln in enumerate(lines):
        d.add(T.text(ln, "montserrat", 2.05, cx, B + 25 + i * 3.4, WHITE, "middle", 600))
    for i, ln in enumerate(CONTACT["address_lines"] + [CONTACT["phone_intl"]]):
        d.add(T.text(ln, "montserrat", 2.05, cx, B + 33.5 + i * 3.4, CYAN, "middle", 700))
    q = 20
    d.rect(cx - q / 2 - 1.2, B + 45, q + 2.4, q + 2.4, WHITE, rx=1.2)
    d.add(LY.qr(CONTACT["url"], cx - q / 2, B + 46.2, q, NAVY, quiet=1))
    d.add(T.text("VALID UNTIL", "montserrat", 1.7, B + 6, B + 75, CYAN, "start", 700, tracking=0.16))
    d.rect(B + 6, B + 79.5, 18, 0.25, WHITE)
    d.add(T.text("AUTHORISED SIGNATURE", "montserrat", 1.7, d.w - B - 6, B + 75, CYAN, "end", 700, tracking=0.12))
    d.rect(d.w - B - 26, B + 79.5, 20, 0.25, WHITE)
    n += save(d, out / "parcelfly-id-card-back")
    return n


def shipping_label():
    """4 x 6 in thermal label template (black only)."""
    out = OUT / "stationery" / "shipping-label"
    W, H = 101.6, 152.4
    K = "#000000"
    d = Doc(W, H, unit="mm", title="Parcel Fly shipping label 4x6")
    d.rect(0, 0, W, H, WHITE)
    m = 4.0
    frag, _ = LY.place_logo("horizontal", "black", m, m, w=38, h=9)
    d.add(frag)
    d.add(T.text(CONTACT["web"], "montserrat", 2.4, W - m, m + 3.4, K, "end", 700))
    d.add(T.text(CONTACT["phone"], "montserrat", 2.4, W - m, m + 7.2, K, "end", 700))
    d.rect(m, 16, W - 2 * m, 0.8, K)
    tracking = "PF2511210001"
    d.add(LY.code128(tracking, m, 19, W - 2 * m, 20, K))
    d.add(T.text("PF 2511 2100 01", "geist-mono", 4.2, W / 2, 44.6, K, "middle", 700))

    def box(x, y, w, h, label, big=None):
        d.add(f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" fill="none" stroke="{K}" stroke-width="0.4"/>')
        d.add(T.text(label, "montserrat", 2.0, x + 1.8, y + 3.6, K, "start", 800, tracking=0.12))
        if big:
            d.add(T.text(big, "noto-bengali", 6.5, x + 1.8, y + h - 2.6, K, "start", 800))

    bw = (W - 2 * m) / 3
    box(m, 48, bw, 13, "COD", "৳")
    box(m + bw, 48, bw, 13, "WEIGHT (KG)")
    box(m + 2 * bw, 48, bw, 13, "DATE")
    # destination hub: tick one (the five Parcel Fly hubs)
    d.add(T.text("HUB", "montserrat", 2.1, m, 66.2, K, "start", 900, tracking=0.12))
    hx = m + 9.5
    for hb in MP.hubs():
        d.add(f'<rect x="{fmt(hx)}" y="63.9" width="2.6" height="2.6" fill="none" stroke="{K}" stroke-width="0.3"/>')
        d.add(T.text(hb["name"], "montserrat", 1.95, hx + 3.4, 66.1, K, "start", 700))
        hx += 3.4 + T.advance(hb["name"], "montserrat", 1.95, 700) + 2.4

    def block(y, title, rows, step=5.9):
        d.add(T.text(title, "montserrat", 3.0, m, y, K, "start", 900, tracking=0.12))
        for i, r in enumerate(rows):
            yy = y + 5.6 + i * step
            d.add(T.text(r, "montserrat", 2.1, m, yy, K, "start", 600))
            d.rect(m + 17, yy + 0.4, W - 2 * m - 17, 0.25, K)
        return y + 5.6 + len(rows) * step

    y = block(73, "TO", ["Name", "Phone", "Address", "", "Area"])
    d.rect(m, y - 1.5, W - 2 * m, 0.5, K)
    y = block(y + 4.2, "FROM", ["Merchant", "Phone"])
    d.rect(m, H - 22, W - 2 * m, 0.8, K)
    for i, ic in enumerate(["fragile", "this-side-up", "keep-dry"]):
        d.add(P.icon(ic, m + i * 13, H - 18.5, 11, K, 3.4))
    q = 15
    d.add(LY.qr(f"{CONTACT['url']}/#track-parcel", W - m - q, H - m - q, q, K, quiet=0))
    d.add(T.text("SCAN TO TRACK", "montserrat", 1.8, W - m - q - 2, H - m - 2, K, "end", 800, tracking=0.12))
    return save(d, out / "parcelfly-shipping-label-4x6")


# ================================================================== packaging

def packaging():
    out = OUT / "packaging"
    n = 0
    # tape: one repeat unit 48 x 300 mm, plus a 1 m strip
    for name, bg, way, fg, acc in [("navy", NAVY, "ondark", WHITE, CYAN), ("white", WHITE, "color", NAVY, SKY)]:
        unit_w, H = 300.0, 48.0
        def unit(dd, x0):
            dd.add(LY.symbol_at(way, x0 + 32, H / 2, 46))
            frag, _ = LY.place_logo("wordmark", fg, x0 + 62, 0, h=12.5, valign="middle")
            fr, bb = LY.place_logo("wordmark", fg, x0 + 62, (H - 12.5) / 2 - 1.5, h=12.5)
            dd.add(fr)
            dd.add(LY.label(TAGLINE, x0 + 62, H / 2 + 12.5, 3.4, acc, tracking=0.2))
            dd.add(SC.chevron_trail(x0 + 150, (H - 22) / 2, 22, 3, [(acc, acc), (fg, fg), (acc, acc)]))
            bs = 9.0
            b0, b1, b2, b3 = T.ink_bounds(TAGLINE_BN, "mina-bold", bs)
            dd.add(T.text(TAGLINE_BN, "mina-bold", bs, x0 + 196 - b0, H / 2 - (b1 + b3) / 2, fg))
        d = Doc(unit_w, H, unit="mm", title=f"Parcel Fly packaging tape repeat ({name})")
        d.rect(0, 0, unit_w, H, bg)
        unit(d, 0)
        n += save(d, out / "tape" / f"parcelfly-tape-48mm-repeat-{name}", dpi=200)
        d = Doc(1000, H, unit="mm", title=f"Parcel Fly packaging tape 1 m ({name})")
        d.rect(0, 0, 1000, H, bg)
        for i in range(4):
            unit(d, i * unit_w)
        n += save(d, out / "tape" / f"parcelfly-tape-48mm-1m-{name}", dpi=100)
    # poly mailer front/back 254 x 330 mm
    W, H = 254.0, 330.0
    d = Doc(W, H, unit="mm", title="Parcel Fly poly mailer front")
    d.rect(0, 0, W, H, NAVY)
    SC.glow(d, W * 0.8, 0, 200, COBALT, 0.8)
    d.add(LY.symbol_at("ondark", W / 2, 70, 150))
    frag, _ = LY.place_logo("wordmark", WHITE, (W - 120) / 2, 118, w=120)
    d.add(frag)
    d.add(LY.label(TAGLINE, W / 2, 152, 6, CYAN, "middle", tracking=0.22))
    d.add(f'<rect x="{(W - 104) / 2}" y="176" width="104" height="128" rx="4" fill="{WHITE}"/>')
    d.add(T.text("PLACE SHIPPING LABEL HERE", "montserrat", 3.4, W / 2, 242, MIST, "middle", 800, tracking=0.12))
    d.add(T.text(CONTACT["web"], "montserrat", 5, W / 2, 320, WHITE, "middle", 700))
    n += save(d, out / "mailer" / "parcelfly-poly-mailer-front", dpi=150)
    d = Doc(W, H, unit="mm", title="Parcel Fly poly mailer back")
    d.rect(0, 0, W, H, WHITE)
    SC.lattice(d, MIST, cell=18)
    frag, _ = LY.place_logo("stacked", "color", (W - 120) / 2, 70, w=120, align="center", tagline="en")
    d.add(frag)
    d.add(T.text("If undelivered, please return to:", "montserrat", 4.4, W / 2, 210, SLATE, "middle", 600))
    for i, ln in enumerate(CONTACT["address_lines"] + [CONTACT["phone_intl"]]):
        d.add(T.text(ln, "montserrat", 4.8, W / 2, 222 + i * 7.5, NAVY, "middle", 700))
    flight_bar(d, 0, H - 10, W, 10)
    n += save(d, out / "mailer" / "parcelfly-poly-mailer-back", dpi=150)
    # box top panel 300 x 200
    W, H = 300.0, 200.0
    d = Doc(W, H, unit="mm", title="Parcel Fly box top panel")
    d.rect(0, 0, W, H, WHITE)
    SC.lattice(d, CLOUD, cell=20)
    frag, _ = LY.place_logo("stacked", "color", 75, 30, w=150, h=120, align="center", valign="middle", tagline="en")
    d.add(frag)
    for i, ic in enumerate(["this-side-up", "fragile", "keep-dry"]):
        d.add(P.icon(ic, W - 18 - (3 - i) * 20, H - 28, 16, NAVY, 3.4))
    flight_bar(d, 0, H - 6, W, 6)
    n += save(d, out / "box" / "parcelfly-box-top-panel", dpi=150)
    # rider delivery box decals
    for name, (W, H) in [("square-400x400", (400.0, 400.0)), ("side-400x300", (400.0, 300.0))]:
        d = Doc(W, H, unit="mm", title=f"Parcel Fly delivery box decal {name}")
        d.rect(0, 0, W, H, NAVY)
        SC.glow(d, W, 0, W * 0.9, COBALT, 0.8)
        d.add(LY.speed_lines(-W * 0.2, H * 0.08, H * 0.22, W * 0.75, (SKY, COBALT, CYAN), opacity=0.55))
        if H == W:
            frag, bb = LY.place_logo("stacked", "ondark", 50, 95, w=300, h=200, align="center", valign="middle")
        else:
            frag, bb = LY.place_logo("horizontal", "ondark", 40, 95, w=320, h=90, align="center", valign="middle")
        d.add(frag)
        bs = 26 if H == W else 22
        b0, b1, b2, b3 = T.ink_bounds(TAGLINE_BN, "mina-bold", bs)
        d.add(T.text(TAGLINE_BN, "mina-bold", bs, W / 2, bb[3] + 16 - b1, CYAN, "middle"))
        d.add(T.text(f"{CONTACT['phone']}  ·  {CONTACT['web']}", "montserrat", 13, W / 2, H - 26, WHITE, "middle", 700))
        n += save(d, out / "delivery-box" / f"parcelfly-delivery-box-decal-{name}", dpi=100)
    return n


# ================================================================== apparel

def apparel():
    out = OUT / "apparel"
    n = 0
    d = Doc(100, 50, unit="mm", title="T-shirt chest print")
    frag, _ = LY.place_logo("horizontal", "ondark", 0, 0, w=100, h=50, valign="middle")
    d.add(frag)
    n += save(d, out / "tshirt" / "parcelfly-tshirt-chest-ondark")
    for name, extra in [("back", None), ("back-rider", "RIDER")]:
        W, H = 280.0, 330.0
        d = Doc(W, H, unit="mm", title=f"T-shirt {name} print")
        d.add(LY.symbol_at("ondark", W / 2, 70, 230))
        frag, bb = LY.place_logo("wordmark", WHITE, (W - 230) / 2, 150, w=230)
        d.add(frag)
        bs = 34
        b0, b1, b2, b3 = T.ink_bounds(TAGLINE_BN, "mina-bold", bs)
        d.add(T.text(TAGLINE_BN, "mina-bold", bs, W / 2, bb[3] + 22 - b1, CYAN, "middle"))
        if extra:
            c, cb = LY.chip(W / 2, 268, extra, 16, CYAN, NAVY, tracking=0.2, anchor="middle")
            d.add(c)
        n += save(d, out / "tshirt" / f"parcelfly-tshirt-{name}-ondark", dpi=150)
        # preview on a navy garment swatch
        pv = Doc(W, H, unit="mm", bg=NAVY)
        pv.add(d.svg().split(">", 1)[1].rsplit("</svg>", 1)[0])
        render_png(pv.svg(), out / "tshirt" / f"parcelfly-tshirt-{name}-preview.png", 1400, W, H)
        n += 1
    for name, way in [("cap-front-colour", "ondark"), ("cap-front-embroidery-white", "white")]:
        d = Doc(70, 32, unit="mm", title=f"Cap {name}")
        frag, _ = LY.place_logo("symbol", way, 0, 0, w=70, h=32, align="center", valign="middle")
        d.add(frag)
        n += save(d, out / "cap" / f"parcelfly-{name}")
    return n


# ================================================================== signage & collateral

def signage():
    out = OUT / "signage"
    n = 0
    for hb in [None] + MP.hubs():
        hub = hb["name"] if hb else None
        W, H = 2400.0, 800.0
        d = Doc(W, H, unit="mm", title=f"Parcel Fly signboard{' ' + hub + ' Hub' if hub else ''}")
        d.rect(0, 0, W, H, NAVY)
        SC.glow(d, W * 0.9, 0, 1200, COBALT, 0.8)
        d.add(LY.speed_lines(-300, 120, 560, 900, (SKY, COBALT, CYAN), opacity=0.35))
        frag, bb = LY.place_logo("horizontal", "ondark", 200, 0, w=1040, h=310, valign="middle")
        frag, bb = LY.place_logo("horizontal", "ondark", 200, (H - (bb[3] - bb[1])) / 2 - 40, w=1040, h=310)
        d.add(frag)
        d.add(LY.label(TAGLINE, 222, bb[3] + 90, 52, CYAN, tracking=0.24))
        right = W - 160
        bs = 120
        b0, b1, b2, b3 = T.ink_bounds(NAME_BN, "mina-bold", bs)
        if hub:
            d.add(T.text(NAME_BN, "mina-bold", 104, right, 230, WHITE, "end"))
            c, cb = LY.chip(0, 0, f"{hub.upper()} HUB", 58, CYAN, NAVY, tracking=0.14)
            c, cb = LY.chip(right - (cb[2] - cb[0]), 290, f"{hub.upper()} HUB", 58, CYAN, NAVY, tracking=0.14)
            d.add(c)
            hb_bn = f"{hb['name_bn']} হাব"
            x0b, y0b, x1b, y1b = T.ink_bounds(hb_bn, "mina-bold", 74)
            d.add(T.text(hb_bn, "mina-bold", 74, right, cb[3] + 40 - y0b, CYAN, "end"))
            d.add(T.text(f"{CONTACT['phone']}  ·  {CONTACT['web']}", "montserrat", 50, right, 690, WHITE, "end", 700))
        else:
            d.add(T.text(NAME_BN, "mina-bold", bs, right, 300, WHITE, "end"))
            d.add(T.text(f"{CONTACT['phone']}  ·  {CONTACT['web']}", "montserrat", 54, right, 640, WHITE, "end", 700))
        name = f"parcelfly-signboard-{hub.lower()}-hub" if hub else "parcelfly-signboard"
        n += save(d, out / "signboard" / name, dpi=25)
    # roll-up banner 850 x 2000
    W, H = 850.0, 2000.0
    d = Doc(W, H, unit="mm", title="Parcel Fly roll-up banner")
    d.rect(0, 0, W, H, WHITE)
    d.rect(0, 0, W, 760, NAVY)
    SC.glow(d, W, 0, 900, COBALT, 0.85)
    frag, _ = LY.place_logo("stacked", "ondark", 125, 90, w=600, h=330, align="center", valign="middle", tagline="en")
    d.add(frag)
    hfrag, last = LY.heading("Delivery that keeps up with your business.", 70, 540, 62, WHITE, max_width=W - 140)
    d.add(hfrag)
    y = 860
    for i, (ic, title) in enumerate([("fast", "Fast city delivery"), ("pickup", "Pickup and drop"),
                                     ("frozen", "Frozen and fragile care"), ("cash", "Cash on delivery"),
                                     ("track", "Timestamped tracking"), ("secure", "Fraud check")]):
        cy = y + i * 120
        d.add(LY.parcel(115, cy, 44, CYAN))
        d.add(P.icon(ic, 115 - 26, cy - 26, 52, NAVY, 3.6))
        d.add(T.text(title, "montserrat", 44, 190, cy + 15, NAVY, "start", 800))
    q = 230
    d.add(LY.qr(CONTACT["url"], 70, 1600, q, NAVY, quiet=1))
    d.add(T.text("Become a merchant", "montserrat", 46, 340, 1660, NAVY, "start", 800))
    d.add(T.text(CONTACT["phone_intl"], "montserrat", 40, 340, 1730, SKY, "start", 700))
    d.add(T.text(CONTACT["web"], "montserrat", 40, 340, 1790, SKY, "start", 700))
    flight_bar(d, 0, H - 60, W, 60)
    n += save(d, out / "roll-up" / "parcelfly-rollup-850x2000", dpi=30)
    # A5 flyer
    W, H = 148.0, 210.0
    d = Doc(W, H, unit="mm", title="Parcel Fly A5 flyer front")
    d.rect(0, 0, W, H, NAVY)
    SC.glow(d, W, 0, 160, COBALT, 0.85)
    d.add(LY.symbol_at("ondark", W / 2, 52, 104))
    d.add(LY.label("For Dhaka merchants", 12, 100, 3.6, CYAN))
    hfrag, last = LY.heading("Delivery that keeps up with your business.", 12, 114, 10.5, WHITE, max_width=W - 24)
    d.add(hfrag)
    pfrag, plast = LY.para("Fast, careful and trackable parcel delivery across Dhaka for online sellers, food businesses "
                           "and growing local brands.", 12, last + 10, 3.8, WHITE, max_width=W - 24, opacity=0.86)
    d.add(pfrag)
    c, cb = LY.chip(12, plast + 7, "Become a merchant", 4.2, CYAN, NAVY)
    d.add(c)
    frag, _ = LY.place_logo("horizontal", "ondark", 12, H - 22, h=11)
    d.add(frag)
    d.add(T.text(CONTACT["phone"], "montserrat", 3.6, W - 12, H - 17.5, WHITE, "end", 700))
    d.add(T.text(CONTACT["web"], "montserrat", 3.6, W - 12, H - 12.5, CYAN, "end", 700))
    n += save(d, out / "flyer" / "parcelfly-flyer-a5-front", dpi=200)
    d = Doc(W, H, unit="mm", title="Parcel Fly A5 flyer back")
    d.rect(0, 0, W, H, CLOUD)
    SC.lattice(d, MIST, cell=10)
    d.add(LY.label("Services", 12, 18, 3.6, SKY))
    d.add(T.text("Everything your deliveries need.", "montserrat", 6.4, 12, 28, NAVY, "start", 800))
    services = [("fast", "Fast city delivery"), ("pickup", "Pickup and drop"), ("frozen", "Frozen and fragile care"),
                ("parcel", "Prepared food delivery"), ("cash", "Cash on delivery"), ("secure", "Fraud check")]
    for i, (ic, t) in enumerate(services):
        x = 12 + (i % 2) * 64
        y = 40 + (i // 2) * 24
        d.add(f'<rect x="{x}" y="{y}" width="60" height="20" rx="3" fill="{WHITE}"/>')
        d.add(LY.parcel(x + 10, y + 10, 6.5, CYAN))
        d.add(P.icon(ic, x + 6, y + 6, 8, NAVY, 3.6))
        d.add(T.text(t, "montserrat", 3.1, x + 19, y + 11.2, NAVY, "start", 800))
    d.add(LY.label("How it works", 12, 124, 3.6, SKY))
    from build_social import STEPS
    for i, (t, desc) in enumerate(STEPS):
        y = 134 + i * 11
        d.add(LY.parcel(16, y - 1.2, 3.8, [NAVY, COBALT, SKY, CYAN][i]))
        d.add(T.text(str(i + 1), "montserrat", 3.0, 16, y, WHITE, "middle", 800))
        d.add(T.text(t, "montserrat", 3.3, 23, y - 1.2, NAVY, "start", 800))
        d.add(T.text(desc, "montserrat", 2.5, 23, y + 3.0, SLATE, "start", 500))
    q = 26
    d.rect(W - 12 - q - 2, 172, q + 4, q + 4, WHITE, rx=2)
    d.add(LY.qr(CONTACT["url"], W - 12 - q, 174, q, NAVY, quiet=1))
    frag, _ = LY.place_logo("horizontal", "color", 12, 182, h=9)
    d.add(frag)
    d.add(T.text(f"{CONTACT['phone']}  ·  {CONTACT['web']}", "montserrat", 3.0, 12, 198, NAVY, "start", 700))
    n += save(d, out / "flyer" / "parcelfly-flyer-a5-back", dpi=200)
    return n


def main():
    n = business_cards() + letterhead() + envelope_and_slip() + id_cards() + shipping_label()
    n += packaging() + apparel() + signage()
    print(f"print: ~{n} files")


if __name__ == "__main__":
    main()
