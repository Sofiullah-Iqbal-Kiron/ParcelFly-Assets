"""Bag artwork (flat, in mm): paper shopping bags, canvas totes, non-woven carry bags, the rider delivery backpack.

Each design returns panel fragments; `paper_dieline` assembles a printer's layout with cut/fold lines."""
from . import layout as LY
from . import scenes as SC
from . import symbol as S
from . import text as T
from .brand import AQUA, CLOUD, CONTACT, COBALT, CYAN, MINT, MIST, NAVY, SKY, SLATE, TAGLINE, TAGLINE_BN, WHITE
from .svg import Doc
from .text import fmt

KRAFT = "#C49A6C"
CANVAS = "#EFE6D4"
TWO_TONE = {"feather_top": WHITE, "feather_mid": WHITE, "feather_bot": WHITE, "parcel": CYAN, "facet_top": CYAN,
            "facet_bot": CYAN}
S.COLOURWAYS["two-tone"] = TWO_TONE

# paper bag sizes (width, gusset, height) in mm
PAPER = {"medium": (320, 120, 410), "small": (200, 80, 250)}
TOP_FOLD, GLUE = 40.0, 20.0


def panel(w, h, bg):
    d = Doc(w, h, unit="mm")
    d.rect(0, 0, w, h, bg)
    return d


def _inner(d: Doc):
    return d.svg().split(">", 1)[1].rsplit("</svg>", 1)[0].split("</title>", 1)[-1]


def vertical_text(s, key, size, cx, cy, fill, weight=None, rot=-90):
    d, adv = T.path_d(s, key, size, 0, 0, "middle", weight)
    x0, y0, x1, y1 = T.ink_bounds(s, key, size, weight)
    return (f'<g transform="translate({fmt(cx)} {fmt(cy)}) rotate({rot})"><path transform="translate(0 {fmt(-(y0 + y1) / 2)})" '
            f'd="{d}" fill="{fill}"/></g>')


# ------------------------------------------------------------------ paper shopping bags

def paper_panels(design, size="medium"):
    """Return {'front','back','gusset'} Docs (mm) and the substrate colour."""
    W, D, H = PAPER[size]
    if design == "navy":
        sub = NAVY
        f = panel(W, H, NAVY)
        SC.glow(f, W * 0.85, 0, W * 0.9, COBALT, 0.8)
        f.add(LY.speed_lines(-W * 0.35, H * 0.80, H * 0.11, W * 0.62, (SKY, COBALT, CYAN), opacity=0.45))
        frag, bb = LY.place_logo("stacked", "ondark", W * 0.18, H * 0.2, w=W * 0.64, align="center", tagline="en")
        f.add(frag)
        f.add(T.text(CONTACT["web"], "montserrat", W * 0.034, W / 2, H * 0.93, WHITE, "middle", 700))
        g = panel(D, H, NAVY)
        g.add(vertical_text(TAGLINE_BN, "mina-bold", D * 0.2, D / 2, H * 0.45, CYAN))
        g.add(LY.symbol_at("ondark", D / 2, H * 0.86, D * 0.62))
        b = panel(W, H, NAVY)
        SC.lattice(b, COBALT, cell=W * 0.08)
        frag, bb = LY.place_logo("horizontal", "ondark", W * 0.15, H * 0.36, w=W * 0.7, align="center")
        b.add(frag)
        b.add(T.text(f"{CONTACT['phone']}  ·  {CONTACT['web']}", "montserrat", W * 0.032, W / 2, H * 0.62, WHITE, "middle", 700))
        return {"front": f, "gusset": g, "back": b}, sub
    if design == "kraft":            # one ink (navy) on natural kraft
        sub = KRAFT
        f = panel(W, H, KRAFT)
        frag, bb = LY.place_logo("stacked", NAVY, W * 0.2, H * 0.24, w=W * 0.6, align="center", tagline="en")
        f.add(frag)
        b0, b1, b2, b3 = T.ink_bounds(TAGLINE_BN, "mina-bold", W * 0.055)
        f.add(T.text(TAGLINE_BN, "mina-bold", W * 0.055, W / 2, bb[3] + H * 0.05 - b1, NAVY, "middle"))
        f.add(T.text(CONTACT["web"], "montserrat", W * 0.034, W / 2, H * 0.93, NAVY, "middle", 700))
        g = panel(D, H, KRAFT)
        g.add(LY.symbol_at(NAVY, D / 2, H * 0.2, D * 0.6))
        g.add(vertical_text("PARCEL FLY", "montserrat", D * 0.16, D / 2, H * 0.6, NAVY, 800))
        b = panel(W, H, KRAFT)
        frag, bb = LY.place_logo("horizontal", NAVY, W * 0.2, H * 0.4, w=W * 0.6, align="center")
        b.add(frag)
        b.add(T.text(f"{CONTACT['phone']}  ·  {CONTACT['web']}", "montserrat", W * 0.032, W / 2, H * 0.62, NAVY, "middle", 700))
        return {"front": f, "gusset": g, "back": b}, sub
    if design == "white":
        sub = WHITE
        f = panel(W, H, WHITE)
        gid = SC.uid("bf")
        f.defs_add(LY.flight_gradient(gid))
        f.rect(0, H * 0.78, W, H * 0.22, f"url(#{gid})")
        f.add(LY.speed_lines(-W * 0.2, H * 0.805, H * 0.17, W * 0.95, (WHITE, WHITE, WHITE), opacity=0.13))
        frag, bb = LY.place_logo("stacked", "color", W * 0.2, H * 0.17, w=W * 0.6, align="center", tagline="en")
        f.add(frag)
        f.add(T.text(CONTACT["web"], "montserrat", W * 0.034, W / 2, H * 0.94, WHITE, "middle", 700))
        g = panel(D, H, SKY)
        g.add(LY.symbol_at("white", D / 2, H * 0.18, D * 0.6))
        g.add(vertical_text(TAGLINE.upper(), "montserrat", D * 0.11, D / 2, H * 0.6, WHITE, 800))
        b = panel(W, H, WHITE)
        SC.lattice(b, MIST, cell=W * 0.08)
        q = W * 0.3
        b.rect(W / 2 - q / 2 - 4, H * 0.3 - 4, q + 8, q + 8, WHITE)
        b.add(LY.qr(f"{CONTACT['url']}/#track-parcel", W / 2 - q / 2, H * 0.3, q, NAVY, quiet=1))
        b.add(T.text("SCAN TO TRACK YOUR PARCEL", "montserrat", W * 0.03, W / 2, H * 0.3 + q + W * 0.08, NAVY, "middle",
                     800, tracking=0.1))
        frag, bb = LY.place_logo("horizontal", "color", W * 0.25, H * 0.8, w=W * 0.5, align="center")
        b.add(frag)
        return {"front": f, "gusset": g, "back": b}, sub
    if design == "sky":               # small gift bag
        sub = SKY
        f = panel(W, H, SKY)
        f.add(LY.speed_lines(-W * 0.3, H * 0.06, H * 0.15, W * 0.9, (WHITE, WHITE, WHITE), opacity=0.12))
        f.add(LY.symbol_at("white", W / 2, H * 0.4, W * 0.66))
        b0, b1, b2, b3 = T.ink_bounds(TAGLINE_BN, "mina-bold", W * 0.11)
        f.add(T.text(TAGLINE_BN, "mina-bold", W * 0.11, W / 2, H * 0.6 - b1, WHITE, "middle"))
        frag, bb = LY.place_logo("wordmark", WHITE, W * 0.3, H * 0.84, w=W * 0.4, align="center")
        f.add(frag)
        g = panel(D, H, NAVY)
        g.add(LY.symbol_at("ondark", D / 2, H * 0.85, D * 0.62))
        b = panel(W, H, SKY)
        frag, bb = LY.place_logo("stacked", "white", W * 0.25, H * 0.3, w=W * 0.5, align="center")
        b.add(frag)
        b.add(T.text("Delivered with care", "montserrat", W * 0.05, W / 2, H * 0.72, WHITE, "middle", 700))
        return {"front": f, "gusset": g, "back": b}, sub
    raise KeyError(design)


def paper_dieline(design, size="medium", bleed=3.0):
    """Printer's flat: back | gusset | front | gusset | glue flap, with top fold-over and bottom section.
    Cut lines magenta, fold lines cyan dashed (on their own layer groups)."""
    W, D, H = PAPER[size]
    bottom = D * 0.6 + 20
    panels, sub = paper_panels(design, size)
    order = [("back", W), ("gusset", D), ("front", W), ("gusset", D)]
    total_w = 2 * W + 2 * D + GLUE
    total_h = TOP_FOLD + H + bottom
    doc = Doc(total_w + 2 * bleed, total_h + 2 * bleed, unit="mm",
              title=f"Parcel Fly paper bag {design} {size} ({W}x{D}x{H} mm) dieline")
    ox, oy = bleed, bleed
    doc.rect(0, 0, doc.w, doc.h, sub)
    x = ox
    for i, (name, pw) in enumerate(order):
        cid = f"panel{i}"
        doc.defs_add(f'<clipPath id="{cid}"><rect x="0" y="0" width="{fmt(pw)}" height="{fmt(H)}"/></clipPath>')
        inner = _inner(panels[name]).replace('id="', f'id="{cid}-').replace("url(#", f"url(#{cid}-")
        doc.add(f'<g transform="translate({fmt(x)} {fmt(oy + TOP_FOLD)})"><g clip-path="url(#{cid})">{inner}</g></g>')
        x += pw
    # top fold-over (inside band) and glue flap carry the substrate/brand colour
    cut, fold = "#FF00FF", "#00AEEF"
    lines = [f'<g id="CutContour" fill="none" stroke="{cut}" stroke-width="0.35">'
             f'<rect x="{fmt(ox)}" y="{fmt(oy)}" width="{fmt(total_w)}" height="{fmt(total_h)}"/></g>',
             f'<g id="Folds" fill="none" stroke="{fold}" stroke-width="0.3" stroke-dasharray="3 2">']
    x = ox
    for name, pw in order:
        x += pw
        lines.append(f'<path d="M{fmt(x)} {fmt(oy)}V{fmt(oy + total_h)}"/>')
    for gx in (ox + W + D / 2, ox + 2 * W + 1.5 * D):
        lines.append(f'<path d="M{fmt(gx)} {fmt(oy + TOP_FOLD)}V{fmt(oy + total_h)}"/>')
        by = oy + TOP_FOLD + H
        lines.append(f'<path d="M{fmt(gx - D / 2)} {fmt(by)}L{fmt(gx)} {fmt(by + D / 2)}L{fmt(gx + D / 2)} {fmt(by)}"/>')
    lines.append(f'<path d="M{fmt(ox)} {fmt(oy + TOP_FOLD)}H{fmt(ox + total_w)}M{fmt(ox)} {fmt(oy + TOP_FOLD + H)}'
                 f'H{fmt(ox + total_w)}"/></g>')
    doc.add("".join(lines))
    labels = [("BACK", ox + W / 2), ("GUSSET", ox + W + D / 2), ("FRONT", ox + W + D + W / 2),
              ("GUSSET", ox + 2 * W + 1.5 * D)]
    for lab, lx in labels:
        doc.add(T.text(lab, "montserrat", 4, lx, oy + TOP_FOLD - 8, "#FF00FF", "middle", 800, tracking=0.2))
    doc.add(T.text("TOP FOLD-OVER", "montserrat", 3.4, ox + total_w / 2, oy + 12, "#FF00FF", "middle", 800, tracking=0.2))
    doc.add(T.text("BOTTOM", "montserrat", 3.4, ox + W + D + W / 2, oy + TOP_FOLD + H + bottom / 2, "#FF00FF", "middle",
                   800, tracking=0.2))
    doc.add(T.text("GLUE", "montserrat", 3.0, ox + total_w - GLUE / 2, oy + total_h / 2, "#FF00FF", "middle", 800))
    return doc, panels, sub


# ------------------------------------------------------------------ totes (canvas, screen print)

TOTE = (380, 420)


def tote_print(design):
    """Front of a canvas tote, 380 x 420 mm, print area about 280 x 300. Returns (Doc, fabric colour, ink note)."""
    W, H = TOTE
    if design == "natural":
        d = panel(W, H, CANVAS)
        d.add(LY.symbol_at(NAVY, W / 2, H * 0.36, W * 0.62))
        frag, bb = LY.place_logo("wordmark", NAVY, W * 0.2, H * 0.53, w=W * 0.6, align="center")
        d.add(frag)
        b0, b1, b2, b3 = T.ink_bounds(TAGLINE_BN, "mina-bold", W * 0.06)
        d.add(T.text(TAGLINE_BN, "mina-bold", W * 0.06, W / 2, bb[3] + H * 0.05 - b1, NAVY, "middle"))
        return d, CANVAS, "1 colour screen print, navy (Pantone 2738 C)"
    if design == "navy":
        d = panel(W, H, NAVY)
        x = W * 0.14
        d.add(LY.symbol_at("two-tone", x + W * 0.17, H * 0.3, W * 0.34))
        d.add(T.text("Always,", "montserrat", W * 0.115, x, H * 0.52, WHITE, "start", 800, tracking=-0.01))
        d.add(T.text("Everywhere.", "montserrat", W * 0.115, x, H * 0.52 + W * 0.13, WHITE, "start", 800, tracking=-0.01))
        b0, b1, b2, b3 = T.ink_bounds(TAGLINE_BN, "mina-bold", W * 0.07)
        d.add(T.text(TAGLINE_BN, "mina-bold", W * 0.07, x - b0, H * 0.52 + W * 0.2 - b1, CYAN))
        frag, bb = LY.place_logo("wordmark", CYAN, x, H * 0.84, w=W * 0.3)
        d.add(frag)
        return d, NAVY, "2 colour screen print, white + cyan (Pantone 306 C)"
    raise KeyError(design)


# ------------------------------------------------------------------ non-woven carry bags

NONWOVEN = {"dcut": (300, 400), "loop": (350, 420)}


def dcut_hole(W):
    """D-cut handle opening path (mm), centred near the top."""
    w, h, top = W * 0.3, W * 0.12, W * 0.09
    x0, x1 = W / 2 - w / 2, W / 2 + w / 2
    r = h / 2
    return (f"M{fmt(x0 + r)} {fmt(top)}H{fmt(x1 - r)}A{fmt(r)} {fmt(r)} 0 0 1 {fmt(x1 - r)} {fmt(top + h)}"
            f"H{fmt(x0 + r)}A{fmt(r)} {fmt(r)} 0 0 1 {fmt(x0 + r)} {fmt(top)}Z")


def nonwoven_print(design):
    if design == "dcut":
        W, H = NONWOVEN["dcut"]
        fab = SKY
        d = panel(W, H, fab)
        d.add(LY.speed_lines(-W * 0.4, H * 0.66, H * 0.14, W * 0.75, (WHITE, WHITE, WHITE), opacity=0.14))
        frag, bb = LY.place_logo("stacked", "white", W * 0.22, H * 0.2, w=W * 0.56, align="center", tagline="en")
        d.add(frag)
        b0, b1, b2, b3 = T.ink_bounds(TAGLINE_BN, "mina-bold", W * 0.065)
        d.add(T.text(TAGLINE_BN, "mina-bold", W * 0.065, W / 2, bb[3] + H * 0.045 - b1, WHITE, "middle"))
        d.add(T.text(f"{CONTACT['phone']}  ·  {CONTACT['web']}", "montserrat", W * 0.036, W / 2, H * 0.92, WHITE, "middle", 700))
        return d, fab, "1 colour print, white; D-cut handle", dcut_hole(W)
    if design == "loop":
        W, H = NONWOVEN["loop"]
        fab = NAVY
        d = panel(W, H, fab)
        d.add(LY.symbol_at("two-tone", W / 2, H * 0.32, W * 0.6))
        frag, bb = LY.place_logo("wordmark", WHITE, W * 0.22, H * 0.48, w=W * 0.56, align="center")
        d.add(frag)
        d.add(LY.label(TAGLINE, W / 2, bb[3] + H * 0.07, W * 0.032, CYAN, "middle", tracking=0.22))
        d.add(T.text(f"{CONTACT['phone']}  ·  {CONTACT['web']}", "montserrat", W * 0.034, W / 2, H * 0.9, WHITE, "middle", 700))
        return d, fab, "2 colour print, white + cyan; sewn loop handles", None
    raise KeyError(design)


# ------------------------------------------------------------------ rider delivery backpack (thermal box bag)

BACKPACK = (420, 330, 420)   # width, depth, height (mm)


def backpack_panels():
    W, D, H = BACKPACK
    silver = "#C9D2DE"

    def base(w, h):
        d = panel(w, h, NAVY)
        d.rect(0, h * 0.86, w, h * 0.055, silver)            # reflective strip
        return d

    f = base(W, H)
    frag, bb = LY.place_logo("stacked", "ondark", W * 0.2, H * 0.12, w=W * 0.6, align="center")
    f.add(frag)
    f.add(T.text(CONTACT["phone"], "montserrat", W * 0.055, W / 2, H * 0.78, WHITE, "middle", 800))
    s = base(D, H)
    s.add(LY.symbol_at("ondark", D / 2, H * 0.3, D * 0.7))
    b0, b1, b2, b3 = T.ink_bounds(TAGLINE_BN, "mina-bold", D * 0.1)
    s.add(T.text(TAGLINE_BN, "mina-bold", D * 0.1, D / 2, H * 0.55 - b1, CYAN, "middle"))
    s.add(T.text(CONTACT["web"], "montserrat", D * 0.06, D / 2, H * 0.74, WHITE, "middle", 700))
    t = panel(W, D, NAVY)
    t.add(LY.symbol_at("ondark", W / 2, D / 2, W * 0.5))
    return {"front": f, "side": s, "top": t}
