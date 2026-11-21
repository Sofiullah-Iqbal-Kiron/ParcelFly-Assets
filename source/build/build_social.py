"""Social media library: covers for every platform (safe-zone aware), profile pictures, Instagram highlights,
post and story templates. Output: social/<platform>/...  (SVG masters + PNG/JPG ready to upload)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pfbrand import ROOT, layout as LY, scenes as SC, symbol as S, text as T  # noqa: E402
from pfbrand import pictograms as P  # noqa: E402
from pfbrand import maps as MP  # noqa: E402
from pfbrand.brand import (AQUA, CLOUD, CONTACT, COBALT, CYAN, INK, MINT, MIST, NAVY, SKY, SLATE,  # noqa: E402
                           TAGLINE, TAGLINE_BN, WHITE)
from pfbrand.svg import Doc  # noqa: E402
from pfbrand.text import fmt  # noqa: E402

OUT = ROOT / "social"

# ------------------------------------------------------------------ platform specs (w, h, safe box)
COVERS = {
    "facebook/cover": (1640, 624, (305, 60, 1030, 504)),            # mobile shows the centre 1109 x 624
    "linkedin/company-cover": (1128, 191, (300, 28, 790, 135)),     # logo overlaps bottom-left
    "linkedin/personal-cover": (1584, 396, (560, 56, 960, 284)),    # profile photo overlaps the left
    "x/header": (1500, 500, (430, 80, 1010, 340)),                  # avatar bottom-left, mobile crops top/bottom
    "youtube/banner": (2560, 1440, (507, 508, 1546, 423)),          # 1546 x 423 is visible on every device
    "google-business/cover": (1080, 608, (70, 70, 940, 468)),
    "email/header": (1200, 400, (60, 50, 1080, 300)),
    "web/og-image": (1200, 630, (80, 80, 1040, 470)),
}


def fit_text_size(s, key, max_w, max_h_cap, weight=None, tracking=0.0, cap_ratio=0.70):
    size = T.fit_size(s, key, max_w, max_h_cap / cap_ratio, weight, tracking=tracking)
    return size


# ------------------------------------------------------------------ cover concepts

def cover_signature(w, h, safe):
    sx, sy, sw, sh = safe
    d = Doc(w, h, bg=NAVY, title="Parcel Fly cover: Signature")
    SC.glow(d, w * 0.86, h * 0.15, max(w, h) * 0.55, COBALT, 0.7)
    SC.glow(d, w * 0.05, h * 1.05, max(w, h) * 0.35, SKY, 0.25)
    H = h * 1.25
    k = H / S.HEIGHT
    d.add(SC.watermark(COBALT, w - S.WIDTH * k * 0.78, (h - H) / 2, H, 0.75))
    wide = sw / sh > 4.5
    if wide:
        frag, bb = LY.place_logo("horizontal", "ondark", sx, sy, w=sw * 0.46, h=sh * 0.62, valign="middle")
        d.add(frag)
        ts = fit_text_size(TAGLINE.upper(), "montserrat", sw * 0.40, sh * 0.16, 700, 0.2)
        d.add(T.text(TAGLINE.upper(), "montserrat", ts, sx + sw, sy + sh / 2 + ts * 0.35, CYAN, "end", 700, tracking=0.2))
    else:
        frag, bb = LY.place_logo("horizontal", "ondark", sx, sy, w=sw * 0.68, h=sh * 0.42, tagline="en", valign="middle")
        frag, bb = LY.place_logo("horizontal", "ondark", sx, sy + (sh - (bb[3] - bb[1])) / 2, w=sw * 0.68,
                                 h=sh * 0.42, tagline="en")
        d.add(frag)
        ws = min(sh * 0.07, 34 * w / 1640 * 1.0 + 6)
        d.add(T.text(CONTACT["web"], "montserrat", ws, sx + sw, sy + sh - ws * 0.2, WHITE, "end", 600, opacity=0.8))
    return d


def cover_bangla(w, h, safe):
    sx, sy, sw, sh = safe
    d = Doc(w, h, title="Parcel Fly cover: সবসময়, সবখানে")
    SC.gradient_bg(d, [(0, NAVY), (0.6, COBALT), (1, SKY)], angle=-12)
    d.add(LY.speed_lines(-w * 0.05, h * 0.18, h * 0.64, w * 0.62, (WHITE, WHITE, WHITE), opacity=0.07))
    wide = sw / sh > 4.5
    if wide:
        frag, bb = LY.place_logo("horizontal", "white", sx, sy, w=sw * 0.36, h=sh * 0.5, valign="middle")
        d.add(frag)
        size = T.fit_size(TAGLINE_BN, "mina-bold", sw * 0.50, sh * 0.95)
        x0, y0, x1, y1 = T.ink_bounds(TAGLINE_BN, "mina-bold", size)
        d.add(T.text(TAGLINE_BN, "mina-bold", size, sx + sw, sy + sh / 2 - (y0 + y1) / 2, WHITE, "end"))
        return d
    # symbol on the right (full colour on dark), text block on the left
    H = min(sh * 0.78, sw * 0.36 * S.HEIGHT / S.WIDTH)
    sym_w = S.WIDTH * H / S.HEIGHT
    d.add(SC.watermark("ondark", sx + sw - sym_w, sy + (sh - H) / 2, H))
    text_w = sw - sym_w - sw * 0.07
    size = T.fit_size(TAGLINE_BN, "mina-bold", text_w, sh * 0.40)
    x0, y0, x1, y1 = T.ink_bounds(TAGLINE_BN, "mina-bold", size)
    ls = size * 0.24
    logo_h = sh * 0.13
    block = logo_h + sh * 0.12 + (y1 - y0) + ls * 2.4
    top = sy + (sh - block) / 2
    frag, bb = LY.place_logo("horizontal", "white", sx, top, w=text_w * 0.5, h=logo_h)
    d.add(frag)
    base = top + logo_h + sh * 0.12 - y0
    d.add(T.text(TAGLINE_BN, "mina-bold", size, sx - x0, base, WHITE))
    d.add(LY.label(TAGLINE, sx, base + y1 + ls * 2.2, ls, CYAN, tracking=0.22))
    return d


def cover_merchant(w, h, safe):
    sx, sy, sw, sh = safe
    d = Doc(w, h, bg=CLOUD, title="Parcel Fly cover: Merchants")
    SC.lattice(d, MIST, cell=max(28, h * 0.11))
    wide = sw / sh > 4.5
    head = "Delivery that keeps up with your business."
    if wide:
        frag, bb = LY.place_logo("horizontal", "color", sx, sy, w=sw * 0.30, h=sh * 0.45, valign="middle")
        d.add(frag)
        hs = T.fit_size(head, "montserrat", sw * 0.42, sh * 0.30, 800)
        d.add(T.text(head, "montserrat", hs, sx + sw * 0.34, sy + sh / 2 + hs * 0.35, NAVY, "start", 800))
        c, cb = LY.chip(sx + sw, sy + sh / 2 - hs * 0.62, "Become a merchant", hs * 0.62, CYAN, NAVY, anchor="start")
        cw = cb[2] - cb[0]
        c, cb = LY.chip(sx + sw - cw, sy + sh / 2 - (cb[3] - cb[1]) / 2, "Become a merchant", hs * 0.62, CYAN, NAVY)
        d.add(c)
        return d
    tw = sw * 0.56
    right = w - (w - sx - sw) * 0.35
    left = sx + tw + sw * 0.05
    H = min(h * 0.80, sh * 1.02, (right - left) * S.HEIGHT / S.WIDTH)
    d.add(SC.watermark("color", right - S.WIDTH * H / S.HEIGHT, (h - H) / 2, H))
    hs = sh * 0.135
    ls = hs * 0.36
    ps = hs * 0.40
    lines = T.wrap(head, "montserrat", hs, tw, 800, tracking=-0.01)
    block = ls * 1.2 + hs * 0.55 + len(lines) * hs * 1.1 + ps * 1.4 + ps * 2.6 + ps * 1.9
    y = sy + (sh - block) / 2
    d.add(LY.label("For Dhaka merchants", sx, y + ls, ls, SKY))
    hfrag, last = LY.heading(head, sx, y + ls * 1.2 + hs * 1.05, hs, NAVY, max_width=tw, weight=800)
    d.add(hfrag)
    pfrag, plast = LY.para("Pickup from your store, timestamped tracking and COD you can see.", sx, last + hs * 0.85,
                           ps, SLATE, max_width=tw, weight=500)
    d.add(pfrag)
    c, cb = LY.chip(sx, plast + ps * 1.3, "Become a merchant", ps * 1.0, CYAN, NAVY)
    d.add(c)
    d.add(T.text(f"{CONTACT['phone']}  ·  {CONTACT['web']}", "montserrat", ps * 0.92, cb[2] + ps * 1.0,
                 (cb[1] + cb[3]) / 2 + ps * 0.33, NAVY, "start", 700))
    return d


_NS = [h_["name"] for h_ in sorted(MP.hubs(), key=lambda h_: -h_["lat"])]   # north to south, from source/geo/hubs.json
HUB_LINE = f"{', '.join(_NS[:-1])} and {_NS[-1]} hubs keep us close to your customers."


def cover_coverage(w, h, safe):
    """Real hub map (OpenStreetMap) on the right, message on the left."""
    sx, sy, sw, sh = safe
    d = Doc(w, h, bg=NAVY, title="Parcel Fly cover: Coverage")
    wide = sw / sh > 4.5
    mx = sx + sw * (0.5 if wide else 0.46)
    my, mh = (sy, sh) if sh < h * 0.6 else (0, h)   # YouTube: only the 1546 x 423 band is visible everywhere
    d.add(MP.hub_map(mx, my, w - mx, mh, "dark", labels="en" if wide else "both", inset=False, clip_id="cov",
                     label_size=min(sh * (0.11 if wide else 0.045), 40), node_size=sh * (0.035 if wide else 0.02),
                     extent=MP.hub_extent(pad=0.16 if wide else 0.2), attribution=False))
    # OpenStreetMap credit inside the safe zone so no platform crop can hide it
    asz = max(min(sh * 0.035, 14), 7)
    d.add(T.text("Map: " + MP.ATTRIBUTION, "montserrat", asz, sx, sy + sh - asz * 0.2, "#8FA3E8", "start", 500))
    # soft hand-over from the text area into the map
    gid = SC.uid("cf")
    d.defs_add(f'<linearGradient id="{gid}"><stop offset="0" stop-color="{NAVY}"/><stop offset="1" stop-color="{NAVY}" stop-opacity="0"/></linearGradient>')
    d.rect(mx - 1, 0, (w - mx) * 0.18, h, f"url(#{gid})")
    if wide:
        frag, bb = LY.place_logo("horizontal", "ondark", sx, sy, w=sw * 0.32, h=sh * 0.42, valign="middle")
        d.add(frag)
        return d
    frag, bb = LY.place_logo("horizontal", "ondark", sx, sy, w=sw * 0.28, h=sh * 0.15)
    d.add(frag)
    tw = sw * 0.44
    hs = min(sh * 0.12, T.fit_size("Five hubs across", "montserrat", tw, 300, 800))
    hfrag, last = LY.heading("Five hubs across Dhaka and Narayanganj.", sx, sy + sh * 0.30 + hs, hs, WHITE, max_width=tw)
    d.add(hfrag)
    ps = hs * 0.36
    pfrag, _ = LY.para(HUB_LINE, sx, last + hs * 0.9, ps, CYAN, max_width=tw, weight=600)
    d.add(pfrag)
    return d


def cover_rider(w, h, safe):
    sx, sy, sw, sh = safe
    d = Doc(w, h, bg=SKY, title="Parcel Fly cover: Riders")
    d.add(LY.speed_lines(-w * 0.1, h * 0.12, h * 0.76, w * 0.75, (WHITE, WHITE, WHITE), opacity=0.09))
    wide = sw / sh > 4.5
    if wide:
        frag, bb = LY.place_logo("horizontal", "white", sx, sy, w=sw * 0.3, h=sh * 0.45, valign="middle")
        d.add(frag)
        hs = T.fit_size("Ride with Parcel Fly", "montserrat", sw * 0.36, sh * 0.32, 800)
        d.add(T.text("Ride with Parcel Fly", "montserrat", hs, sx + sw * 0.36, sy + sh / 2 + hs * 0.35, WHITE, "start", 800))
        c, cb = LY.chip(0, 0, f"Call {CONTACT['phone']}", hs * 0.55, NAVY, WHITE)
        c, cb = LY.chip(sx + sw - (cb[2] - cb[0]), sy + sh / 2 - (cb[3] - cb[1]) / 2, f"Call {CONTACT['phone']}",
                        hs * 0.55, NAVY, WHITE)
        d.add(c)
        return d
    H = min(sh * 0.70, sw * 0.38 * S.HEIGHT / S.WIDTH)
    sym_w = S.WIDTH * H / S.HEIGHT
    d.add(SC.watermark("white", sx + sw - sym_w, sy + (sh - H) / 2, H))
    tw = sw - sym_w - sw * 0.06
    hs = min(sh * 0.15, T.fit_size("Ride with Parcel Fly", "montserrat", tw, 300, 800))
    bs = hs * 0.62
    x0, y0, x1, y1 = T.ink_bounds("রাইডার হিসেবে যোগ দিন", "mina-bold", bs)
    badge = hs * 1.25
    block = badge + hs * 0.45 + hs * 0.75 + hs * 0.35 + (y1 - y0) + hs * 0.45 + hs * 0.36 * 2.2
    y = sy + (sh - block) / 2
    d.circle(sx + badge / 2, y + badge / 2, badge / 2, NAVY)
    d.add(P.icon("rider", sx + badge * 0.2, y + badge * 0.2, badge * 0.6, WHITE, 3.4))
    frag, bb = LY.place_logo("horizontal", "white", sx + badge * 1.25, y + badge * 0.28, w=tw * 0.5, h=badge * 0.44)
    d.add(frag)
    hy = y + badge + hs * 0.45 + hs * 0.75
    d.add(T.text("Ride with Parcel Fly", "montserrat", hs, sx, hy, WHITE, "start", 800))
    by = hy + hs * 0.35 - y0
    d.add(T.text("রাইডার হিসেবে যোগ দিন", "mina-bold", bs, sx, by, NAVY))
    c, cb = LY.chip(sx, by + y1 + hs * 0.45, f"Call {CONTACT['phone']}", hs * 0.36, NAVY, WHITE)
    d.add(c)
    return d


def cover_minimal(w, h, safe):
    sx, sy, sw, sh = safe
    d = Doc(w, h, bg=WHITE, title="Parcel Fly cover: Minimal")
    lh = min(h * 0.62, sh * 1.05)
    d.add(LY.speed_lines(-lh * 1.2, (h - lh * 0.62) / 2, lh * 0.62, sx + sw * 0.04 + lh * 1.2 - lh * 0.1,
                         (SKY, COBALT, NAVY), cut="left", stagger=True))
    cw = LY.chevron_width(lh * 0.62)
    d.add(LY.chevron(sx + sw - cw * 0.9 + (w - sx - sw) * 0.5, (h - lh * 0.62) / 2, lh * 0.62))
    wide = sw / sh > 4.5
    if wide:
        frag, bb = LY.place_logo("horizontal", "color", sx, sy, w=sw * 0.62, h=sh * 0.55, align="center", valign="middle")
    else:
        frag, bb = LY.place_logo("stacked", "color", sx, sy, w=sw * 0.6, h=sh * 0.66, align="center", valign="middle",
                                 tagline="en")
    d.add(frag)
    return d


CONCEPTS = {
    "signature": cover_signature, "bangla": cover_bangla, "merchant": cover_merchant,
    "coverage": cover_coverage, "rider": cover_rider, "minimal": cover_minimal,
}


# ------------------------------------------------------------------ profile pictures (circle-safe)

def profile(kind, size=1080):
    d = Doc(size, size, title="Parcel Fly profile picture")
    inner = size * 0.80          # circle crop safe square
    off = (size - inner) / 2
    if kind == "navy":
        d.rect(0, 0, size, size, NAVY)
        SC.glow(d, size * 0.5, size * 0.5, size * 0.62, COBALT, 0.65)
        frag, _ = LY.place_logo("symbol", "ondark", off + inner * 0.06, off, w=inner * 0.88, h=inner, valign="middle")
    elif kind == "white":
        d.rect(0, 0, size, size, WHITE)
        frag, _ = LY.place_logo("symbol", "color", off + inner * 0.06, off, w=inner * 0.88, h=inner, valign="middle")
    elif kind == "gradient":
        SC.gradient_bg(d, [(0, NAVY), (0.55, COBALT), (1, SKY)], angle=45)
        frag, _ = LY.place_logo("symbol", "white", off + inner * 0.06, off, w=inner * 0.88, h=inner, valign="middle")
    elif kind == "bold":
        d.rect(0, 0, size, size, NAVY)
        clip, frag = LY.flight_crop("ondark", size, clip_id="pc")
        d.defs_add(clip)
    elif kind == "stacked":
        d.rect(0, 0, size, size, WHITE)
        frag, _ = LY.place_logo("stacked", "color", off, off, w=inner, h=inner * 0.8, align="center", valign="middle")
    elif kind == "stacked-bn":
        d.rect(0, 0, size, size, WHITE)
        frag, _ = LY.place_logo("stacked", "color", off, off, w=inner, h=inner * 0.8, align="center", valign="middle",
                                lang="bn")
    d.add(frag)
    return d


PROFILE_USE = {
    "facebook": ["navy", "white", "gradient", "bold", "stacked", "stacked-bn"],
    "instagram": ["navy", "white", "gradient", "bold"],
    "linkedin": ["stacked", "navy", "white"],
    "x": ["navy", "white", "bold"],
    "youtube": ["navy", "white", "gradient"],
    "whatsapp": ["navy", "white", "bold", "stacked"],
    "tiktok": ["navy", "bold"],
    "google-business": ["stacked", "white", "navy"],
}


# ------------------------------------------------------------------ Instagram highlights

HIGHLIGHTS = ["track", "pricing", "coverage", "merchant", "rider", "offers", "reviews", "faq", "phone", "info"]


def highlight(icon, style):
    d = Doc(1080, 1920, title=f"Instagram highlight: {P.LABELS[icon]}")
    bg, fg, ring = {"navy": (NAVY, WHITE, CYAN), "white": (WHITE, NAVY, CYAN), "sky": (SKY, WHITE, MINT)}[style]
    d.rect(0, 0, 1080, 1920, bg)
    if style == "navy":
        SC.glow(d, 540, 960, 620, COBALT, 0.7)
    d.circle(540, 960, 330, "none", f' stroke="{ring}" stroke-width="14"')
    d.add(P.icon(icon, 540 - 190, 960 - 190, 380, fg, 3.0))
    return d


# ------------------------------------------------------------------ posts and stories

SERVICES = [
    ("fast", "Dhaka-wide", "Fast city delivery",
     "A Dhaka-focused delivery network designed to move customer orders quickly from pickup to doorstep."),
    ("pickup", "Doorstep service", "Pickup and drop",
     "Schedule a pickup from your store and let Parcel Fly handle the delivery journey end to end."),
    ("frozen", "Careful handling", "Frozen and fragile care",
     "Purpose-built handling for temperature-sensitive and fragile parcels that need extra attention."),
    ("parcel", "Food friendly", "Prepared food delivery",
     "Dependable local delivery for home kitchens, restaurants and food businesses serving Dhaka customers."),
    ("cash", "COD enabled", "Cash on delivery",
     "Offer customers the payment experience they know while keeping COD and receivables visible in your account."),
    ("secure", "Reduce risk", "Fraud check",
     "Check a customer number before confirming a risky order."),
]

STEPS = [
    ("Create your merchant account", "Sign up with your business and contact information."),
    ("Set up your pickup store", "Add the location our team should collect parcels from."),
    ("Book one or many parcels", "Enter customer details, COD amount and delivery preferences."),
    ("Track, deliver and settle", "Follow parcel progress and review your receivable balance."),
]


def post_frame(w, h, dark=True, title=""):
    d = Doc(w, h, bg=NAVY if dark else CLOUD, title=title)
    if dark:
        SC.glow(d, w * 0.9, h * 0.05, w * 0.9, COBALT, 0.75)
    else:
        SC.lattice(d, MIST, cell=w * 0.06)
    return d


def post_footer(d, w, h, dark=True, m=None):
    m = m or w * 0.074
    way = "ondark" if dark else "color"
    frag, bb = LY.place_logo("horizontal", way, m, h - m - w * 0.062, w=w * 0.36, h=w * 0.062)
    d.add(frag)
    d.add(T.text(CONTACT["web"], "montserrat", w * 0.026, w - m, h - m - w * 0.018, WHITE if dark else NAVY, "end", 600,
                 opacity=0.85 if dark else None))


def post_service(w, h, svc, idx):
    icon, tag, title, desc = svc
    d = post_frame(w, h, True, f"Parcel Fly service: {title}")
    m = w * 0.074
    H = h * 0.62
    d.add(SC.watermark(COBALT, w - S.WIDTH * H / S.HEIGHT * 0.55, h * 0.06, H, 0.55))
    isz = w * 0.16
    d.add(LY.parcel(m + isz / 2, m + isz / 2, isz * 0.72, CYAN))
    d.add(P.icon(icon, m + isz * 0.2, m + isz * 0.2, isz * 0.6, NAVY, 3.6))
    ty = m + isz + w * 0.12
    d.add(LY.label(f"{idx:02d} · {tag}", m, ty, w * 0.03, CYAN))
    hfrag, last = LY.heading(title, m, ty + w * 0.105, w * 0.088, WHITE, max_width=w - 2 * m)
    d.add(hfrag)
    pfrag, plast = LY.para(desc, m, last + w * 0.085, w * 0.036, WHITE, max_width=w * 0.78, opacity=0.86)
    d.add(pfrag)
    post_footer(d, w, h)
    return d


def post_brand(w, h, lang="en"):
    d = Doc(w, h, title="Parcel Fly post: tagline")
    SC.gradient_bg(d, [(0, NAVY), (0.55, COBALT), (1, SKY)], angle=60)
    m = w * 0.074
    H = w * 0.36
    d.add(SC.watermark("ondark", (w - S.WIDTH * H / S.HEIGHT) / 2, h * 0.16, H))
    if lang == "bn":
        size = T.fit_size(TAGLINE_BN, "mina-bold", w - 2 * m, w * 0.17)
        x0, y0, x1, y1 = T.ink_bounds(TAGLINE_BN, "mina-bold", size)
        base = h * 0.16 + H + h * 0.1 - y0
        d.add(T.text(TAGLINE_BN, "mina-bold", size, w / 2, base, WHITE, "middle"))
        d.add(LY.label(TAGLINE, w / 2, base + y1 + w * 0.07, w * 0.032, CYAN, "middle", tracking=0.22))
    else:
        hs = T.fit_size(TAGLINE + ".", "montserrat", w - 2 * m, w * 0.11, 800)
        base = h * 0.16 + H + h * 0.12 + hs * 0.7
        d.add(T.text(TAGLINE + ".", "montserrat", hs, w / 2, base, WHITE, "middle", 800, tracking=-0.01))
        bs = hs * 0.62
        x0, y0, x1, y1 = T.ink_bounds(TAGLINE_BN, "mina-bold", bs)
        d.add(T.text(TAGLINE_BN, "mina-bold", bs, w / 2, base + hs * 0.55 - y0, CYAN, "middle"))
    frag, bb = LY.place_logo("wordmark", "white", 0, 0, w=w * 0.34)
    frag, bb = LY.place_logo("wordmark", "white", (w - (bb[2] - bb[0])) / 2, h - m - (bb[3] - bb[1]), w=w * 0.34)
    d.add(frag)
    return d


def post_steps(w, h):
    d = post_frame(w, h, False, "Parcel Fly: how it works")
    m = w * 0.074
    d.add(LY.label("How it works", m, m + w * 0.03, w * 0.03, SKY))
    hfrag, last = LY.heading("Start shipping in four steps.", m, m + w * 0.13, w * 0.072, NAVY, max_width=w - 2 * m)
    d.add(hfrag)
    y = last + w * 0.09
    avail = (h - m - w * 0.12) - y
    row = avail / 4
    for i, (t, desc) in enumerate(STEPS):
        cy = y + row * i + row * 0.42
        d.add(LY.parcel(m + w * 0.045, cy, w * 0.045, [NAVY, COBALT, SKY, CYAN][i]))
        d.add(T.text(str(i + 1), "montserrat", w * 0.04, m + w * 0.045, cy + w * 0.014, WHITE, "middle", 800))
        avail = w - m - (m + w * 0.13)
        ts = min(w * 0.042, T.fit_size(t, "montserrat", avail, 200, 800))
        ds = min(w * 0.029, T.fit_size(desc, "montserrat", avail, 200, 500))
        d.add(T.text(t, "montserrat", ts, m + w * 0.13, cy - w * 0.004, NAVY, "start", 800))
        d.add(T.text(desc, "montserrat", ds, m + w * 0.13, cy + w * 0.045, SLATE, "start", 500))
    post_footer(d, w, h, dark=False)
    return d


def post_hiring(w, h):
    d = Doc(w, h, bg=SKY, title="Parcel Fly: riders wanted")
    d.add(LY.speed_lines(-w * 0.2, h * 0.08, h * 0.42, w * 1.0, (WHITE, WHITE, WHITE), opacity=0.1))
    m = w * 0.074
    footer_top = h - m - w * 0.062
    isz = w * (0.28 if h / w < 1.1 else 0.34)
    d.add(P.icon("rider", w - m - isz, m * 0.8, isz, WHITE, 3.0))
    hs = min(w * 0.092, T.fit_size("Ride with Parcel Fly.", "montserrat", w - 2 * m, 400, 800, tracking=-0.01))
    bs = w * 0.062
    cs = w * 0.036
    x0, y0, x1, y1 = T.ink_bounds("রাইডার হিসেবে যোগ দিন", "mina-bold", bs)
    lines = T.wrap("Ride with Parcel Fly.", "montserrat", hs, w - 2 * m, 800, tracking=-0.01)
    block = w * 0.034 + hs * 0.5 + len(lines) * hs * 1.1 + w * 0.04 + (y1 - y0) + w * 0.05 + cs * 2.0
    top = max(m * 0.8 + isz + w * 0.04, footer_top - w * 0.07 - block)
    d.add(LY.label("We're hiring", m, top + w * 0.034, w * 0.034, NAVY))
    hfrag, last = LY.heading("Ride with Parcel Fly.", m, top + w * 0.034 + hs * 1.25, hs, WHITE, max_width=w - 2 * m)
    d.add(hfrag)
    by = last + w * 0.04 - y0
    d.add(T.text("রাইডার হিসেবে যোগ দিন", "mina-bold", bs, m, by, NAVY))
    c, cb = LY.chip(m, by + y1 + w * 0.05, f"Call {CONTACT['phone']}", cs, NAVY, WHITE)
    d.add(c)
    frag, bb = LY.place_logo("horizontal", "white", m, footer_top, w=w * 0.36, h=w * 0.062)
    d.add(frag)
    return d


def post_track(w, h):
    d = post_frame(w, h, True, "Parcel Fly: track your parcel")
    m = w * 0.074
    d.add(LY.label("Track your parcel", m, m + w * 0.03, w * 0.03, CYAN))
    hfrag, last = LY.heading("Every milestone, timestamped.", m, m + w * 0.13, w * 0.08, WHITE, max_width=w * 0.8)
    d.add(hfrag)
    pfrag, plast = LY.para("Follow your parcel from pickup to doorstep at parcelflybd.com.", m, last + w * 0.08,
                           w * 0.036, WHITE, max_width=w * 0.62, opacity=0.86)
    d.add(pfrag)
    qs = w * 0.3
    qx, qy = w - m - qs, plast + w * 0.08
    d.rect(qx - w * 0.02, qy - w * 0.02, qs + w * 0.04, qs + w * 0.04, WHITE, rx=w * 0.03)
    d.add(LY.qr(f"{CONTACT['url']}/#track-parcel", qx, qy, qs, NAVY))
    d.add(LY.label("Scan to track", qx + qs / 2, qy + qs + w * 0.07, w * 0.026, CYAN, "middle"))
    d.add(P.icon("track", m, qy, w * 0.2, CYAN, 3.0))
    post_footer(d, w, h)
    return d


def post_coverage(w, h):
    d = Doc(w, h, bg=NAVY, title="Parcel Fly: hub network")
    m = w * 0.074
    hs = w * 0.066
    lines = T.wrap("Five hubs across Dhaka and Narayanganj.", "montserrat", hs, w - 2 * m, 800, tracking=-0.01)
    last = m + w * 0.12 + (len(lines) - 1) * hs * 1.1
    top = last + w * 0.05
    d.add(MP.hub_map(0, top, w, h - top - w * 0.15, "dark", inset=False, clip_id="pc", label_size=w * 0.028,
                     node_size=w * 0.016))
    d.rect(0, h - w * 0.15, w, w * 0.15, NAVY)
    d.add(LY.label("Hub network", m, m + w * 0.03, w * 0.03, CYAN))
    hfrag, _ = LY.heading("Five hubs across Dhaka and Narayanganj.", m, m + w * 0.12, hs, WHITE, max_width=w - 2 * m)
    d.add(hfrag)
    post_footer(d, w, h)
    return d


def post_hub(w, h, key):
    """One hub, highlighted on the real map."""
    hb = MP.hub(key)
    d = Doc(w, h, bg=NAVY, title=f"Parcel Fly {hb['name']} Hub")
    m = w * 0.074
    top = m + w * (0.33 if h / w < 1.2 else 0.36)
    d.add(MP.hub_map(0, top, w, h - top - w * 0.15, "dark", highlight=key, inset=False, clip_id="ph",
                     label_size=w * 0.028, node_size=w * 0.016))
    d.rect(0, h - w * 0.15, w, w * 0.15, NAVY)
    d.add(LY.label("Parcel Fly hub", m, m + w * 0.03, w * 0.03, CYAN))
    hs = min(w * 0.11, T.fit_size(f"{hb['name']} Hub", "montserrat", w - 2 * m, 400, 800))
    d.add(T.text(f"{hb['name']} Hub", "montserrat", hs, m, m + w * 0.04 + hs * 0.95, WHITE, "start", 800, tracking=-0.01))
    bs = hs * 0.62
    b0, b1, b2, b3 = T.ink_bounds(f"{hb['name_bn']} হাব", "mina-bold", bs)
    d.add(T.text(f"{hb['name_bn']} হাব", "mina-bold", bs, m - b0, m + w * 0.04 + hs * 0.95 + hs * 0.32 - b1, CYAN))
    post_footer(d, w, h)
    return d


def story_hubs(key=None):
    w, h = 1080, 1920
    top_ui, bottom_ui = 250, 340
    hb = MP.hub(key) if key else None
    d = Doc(w, h, bg=NAVY, title=f"Parcel Fly story: {hb['name'] + ' Hub' if hb else 'hub network'}")
    m = 90
    d.add(MP.hub_map(0, top_ui + 330, w, h - top_ui - 330 - bottom_ui - 40, "dark", highlight=key, inset=not key,
                     clip_id="sh", label_size=34, node_size=20))
    d.add(LY.label("Parcel Fly hub" if hb else "Hub network", m, top_ui + 40, 36, CYAN))
    if hb:
        d.add(T.text(f"{hb['name']} Hub", "montserrat", T.fit_size(f"{hb['name']} Hub", "montserrat", w - 2 * m, 120, 800),
                     m, top_ui + 160, WHITE, "start", 800))
        b0, b1, b2, b3 = T.ink_bounds(f"{hb['name_bn']} হাব", "mina-bold", 70)
        d.add(T.text(f"{hb['name_bn']} হাব", "mina-bold", 70, m - b0, top_ui + 200 - b1, CYAN))
    else:
        hfrag, last = LY.heading("Five hubs. One fast network.", m, top_ui + 150, 86, WHITE, max_width=w - 2 * m)
        d.add(hfrag)
    frag, bb = LY.place_logo("horizontal", "ondark", (w - 520) / 2, h - bottom_ui - 10, w=520)
    d.add(frag)
    return d


def post_wide(kind, w=1200, h=627):
    """Landscape posts (LinkedIn / Facebook link images): two-column layouts."""
    m = w * 0.06
    if kind == "tagline":
        d = Doc(w, h, title="Parcel Fly post: tagline")
        SC.gradient_bg(d, [(0, NAVY), (0.55, COBALT), (1, SKY)], angle=20)
        H = h * 0.30
        d.add(SC.watermark("ondark", m, (h - H) / 2, H))
        tx = m + S.WIDTH * H / S.HEIGHT + w * 0.06
        tw = w - m - tx
        hs = T.fit_size(TAGLINE + ".", "montserrat", tw, h * 0.13, 800, tracking=-0.01)
        bs = hs * 1.0
        x0, y0, x1, y1 = T.ink_bounds(TAGLINE_BN, "mina-bold", bs)
        block = hs * 0.72 + hs * 0.5 + (y1 - y0)
        top = (h - block) / 2
        d.add(T.text(TAGLINE + ".", "montserrat", hs, tx, top + hs * 0.72, WHITE, "start", 800, tracking=-0.01))
        d.add(T.text(TAGLINE_BN, "mina-bold", bs, tx - x0, top + hs * 0.72 + hs * 0.5 - y0, CYAN))
        frag, bb = LY.place_logo("wordmark", "white", tx, h - m - h * 0.06, h=h * 0.06)
        d.add(frag)
        return d
    if kind == "steps":
        d = Doc(w, h, bg=CLOUD, title="Parcel Fly: how it works")
        SC.lattice(d, MIST, cell=w * 0.05)
        d.add(LY.label("How it works", m, m + h * 0.03, h * 0.035, SKY))
        hs = h * 0.085
        d.add(T.text("Start shipping in four steps.", "montserrat", hs, m, m + h * 0.03 + hs * 1.5, NAVY, "start", 800))
        cw = (w - 2 * m - w * 0.04) / 2
        for i, (t, desc) in enumerate(STEPS):
            cx = m + (i % 2) * (cw + w * 0.04)
            cy = h * 0.42 + (i // 2) * h * 0.2
            d.add(LY.parcel(cx + h * 0.045, cy, h * 0.045, [NAVY, COBALT, SKY, CYAN][i]))
            d.add(T.text(str(i + 1), "montserrat", h * 0.04, cx + h * 0.045, cy + h * 0.014, WHITE, "middle", 800))
            avail = cw - h * 0.13
            ts = min(h * 0.042, T.fit_size(t, "montserrat", avail, 200, 800))
            ds = min(h * 0.03, T.fit_size(desc, "montserrat", avail, 200, 500))
            d.add(T.text(t, "montserrat", ts, cx + h * 0.13, cy - h * 0.004, NAVY, "start", 800))
            d.add(T.text(desc, "montserrat", ds, cx + h * 0.13, cy + h * 0.05, SLATE, "start", 500))
        frag, bb = LY.place_logo("horizontal", "color", m, h - m - h * 0.07, h=h * 0.07)
        d.add(frag)
        d.add(T.text(CONTACT["web"], "montserrat", h * 0.032, w - m, h - m - h * 0.02, NAVY, "end", 600))
        return d
    if kind == "hiring":
        d = Doc(w, h, bg=SKY, title="Parcel Fly: riders wanted")
        d.add(LY.speed_lines(-w * 0.1, h * 0.1, h * 0.8, w * 0.8, (WHITE, WHITE, WHITE), opacity=0.1))
        H = h * 0.30
        sym_w = S.WIDTH * H / S.HEIGHT
        d.add(SC.watermark("white", w - m - sym_w, h * 0.22, H))
        text_w = w - 2 * m - sym_w - w * 0.05
        isz = h * 0.2
        d.circle(m + isz / 2, m + isz / 2, isz / 2, NAVY)
        d.add(P.icon("rider", m + isz * 0.2, m + isz * 0.2, isz * 0.6, WHITE, 3.4))
        d.add(LY.label("We're hiring", m + isz * 1.25, m + isz * 0.62, h * 0.035, NAVY))
        hs = min(h * 0.1, T.fit_size("Ride with Parcel Fly.", "montserrat", text_w, 400, 800))
        d.add(T.text("Ride with Parcel Fly.", "montserrat", hs, m, m + isz + h * 0.16, WHITE, "start", 800))
        bs = hs * 0.7
        x0, y0, x1, y1 = T.ink_bounds("রাইডার হিসেবে যোগ দিন", "mina-bold", bs)
        by = m + isz + h * 0.16 + hs * 0.45 - y0
        d.add(T.text("রাইডার হিসেবে যোগ দিন", "mina-bold", bs, m, by, NAVY))
        c, cb = LY.chip(m, by + y1 + h * 0.06, f"Call {CONTACT['phone']}", h * 0.04, NAVY, WHITE)
        d.add(c)
        frag, bb = LY.place_logo("horizontal", "white", w - m - w * 0.22, h - m - h * 0.07, w=w * 0.22, h=h * 0.07,
                                 align="right")
        d.add(frag)
        return d
    if kind == "coverage":
        d = Doc(w, h, bg=NAVY, title="Parcel Fly: hub network")
        mx = w * 0.42
        d.add(MP.hub_map(mx, 0, w - mx, h, "dark", inset=False, clip_id="lc", label_size=h * 0.03, node_size=h * 0.02))
        gid = SC.uid("lf")
        d.defs_add(f'<linearGradient id="{gid}"><stop offset="0" stop-color="{NAVY}"/><stop offset="1" stop-color="{NAVY}" stop-opacity="0"/></linearGradient>')
        d.rect(mx - 1, 0, w * 0.1, h, f"url(#{gid})")
        d.add(LY.label("Hub network", m, m + h * 0.03, h * 0.035, CYAN))
        hfrag, last = LY.heading("Five hubs across Dhaka and Narayanganj.", m, m + h * 0.17, h * 0.075, WHITE,
                                 max_width=mx - m - w * 0.02)
        d.add(hfrag)
        pfrag, _ = LY.para(HUB_LINE, m, last + h * 0.09, h * 0.032, CYAN, max_width=mx - m - w * 0.03, weight=600)
        d.add(pfrag)
        frag, bb = LY.place_logo("horizontal", "ondark", m, h - m - h * 0.07, h=h * 0.07)
        d.add(frag)
        return d
    raise KeyError(kind)


def story(kind):
    w, h = 1080, 1920
    top, bottom = 250, 340  # app UI zones
    if kind == "brand":
        d = Doc(w, h, title="Parcel Fly story: tagline")
        SC.gradient_bg(d, [(0, NAVY), (0.6, COBALT), (1, SKY)], angle=75)
        H = 300
        d.add(SC.watermark("ondark", (w - S.WIDTH * H / S.HEIGHT) / 2, top + 260, H))
        size = T.fit_size(TAGLINE_BN, "mina-bold", w - 160, 200)
        x0, y0, x1, y1 = T.ink_bounds(TAGLINE_BN, "mina-bold", size)
        base = top + 260 + H + 170 - y0
        d.add(T.text(TAGLINE_BN, "mina-bold", size, w / 2, base, WHITE, "middle"))
        d.add(LY.label(TAGLINE, w / 2, base + y1 + 90, 38, CYAN, "middle", tracking=0.22))
        frag, bb = LY.place_logo("wordmark", "white", (w - 400) / 2, h - bottom - 60, w=400)
        d.add(frag)
        return d
    if kind == "merchant":
        d = Doc(w, h, bg=CLOUD, title="Parcel Fly story: become a merchant")
        SC.lattice(d, MIST, cell=72)
        H = 300
        d.add(SC.watermark("color", w - 90 - S.WIDTH * H / S.HEIGHT, top + 60, H))
        m = 90
        d.add(LY.label("For Dhaka merchants", m, top + 520, 34, SKY))
        hfrag, last = LY.heading("Delivery that keeps up with your business.", m, top + 640, 92, NAVY, max_width=w - 2 * m)
        d.add(hfrag)
        y = last + 120
        for item in ["Pickup from your store", "Timestamped tracking updates", "COD and receivable visibility",
                     "Single and bulk parcel booking"]:
            d.add(LY.parcel(m + 16, y - 14, 16, CYAN))
            d.add(T.text(item, "montserrat", 40, m + 56, y, NAVY, "start", 600))
            y += 78
        c, cb = LY.chip(m, y + 20, "Become a merchant", 44, CYAN, NAVY)
        d.add(c)
        d.add(T.text(f"{CONTACT['phone']}  ·  {CONTACT['web']}", "montserrat", 36, m, cb[3] + 80, NAVY, "start", 700))
        return d
    if kind == "rider":
        d = Doc(w, h, bg=SKY, title="Parcel Fly story: riders wanted")
        d.add(LY.speed_lines(-300, top + 80, 520, 1300, (WHITE, WHITE, WHITE), opacity=0.1))
        d.add(P.icon("rider", (w - 560) / 2, top + 60, 560, WHITE, 3.0))
        m = 90
        d.add(LY.label("We're hiring", w / 2, top + 820, 40, NAVY, "middle"))
        d.add(T.text("Ride with", "montserrat", 118, w / 2, top + 960, WHITE, "middle", 800))
        d.add(T.text("Parcel Fly.", "montserrat", 118, w / 2, top + 1090, WHITE, "middle", 800))
        x0, y0, x1, y1 = T.ink_bounds("রাইডার হিসেবে যোগ দিন", "mina-bold", 74)
        d.add(T.text("রাইডার হিসেবে যোগ দিন", "mina-bold", 74, w / 2, top + 1180 - y0, NAVY, "middle"))
        c, cb = LY.chip(w / 2, top + 1280, f"Call {CONTACT['phone']}", 46, NAVY, WHITE, anchor="middle")
        d.add(c)
        return d
    if kind == "track":
        d = Doc(w, h, bg=NAVY, title="Parcel Fly story: track your parcel")
        SC.glow(d, w * 0.8, top + 200, 900, COBALT, 0.8)
        m = 90
        d.add(LY.label("Track your parcel", m, top + 120, 36, CYAN))
        hfrag, last = LY.heading("Every milestone, timestamped.", m, top + 250, 100, WHITE, max_width=w - 2 * m)
        d.add(hfrag)
        qs = 520
        qx, qy = (w - qs) / 2, last + 160
        d.rect(qx - 30, qy - 30, qs + 60, qs + 60, WHITE, rx=44)
        d.add(LY.qr(f"{CONTACT['url']}/#track-parcel", qx, qy, qs, NAVY))
        d.add(LY.label("Scan to track", w / 2, qy + qs + 120, 38, CYAN, "middle"))
        frag, bb = LY.place_logo("horizontal", "ondark", (w - 520) / 2, h - bottom - 40, w=520)
        d.add(frag)
        return d
    raise KeyError(kind)


# ------------------------------------------------------------------ main

def save(d, path, jpg=False):
    d.save(path.with_suffix(".svg"), png=[int(d.w)] if not jpg else None, jpg=[int(d.w)] if jpg else None)


def main():
    n = 0
    for spec, (w, h, safe) in COVERS.items():
        for name, fn in CONCEPTS.items():
            d = fn(w, h, safe)
            p = OUT / spec.split("/")[0] / f"parcelfly-{spec.split('/')[1]}-{name}"
            d.save(p.with_suffix(".svg"), png=[w], jpg=[w])
            n += 3
    for platform, kinds in PROFILE_USE.items():
        for kind in kinds:
            d = profile(kind)
            d.save(OUT / platform / f"parcelfly-profile-{kind}.svg", png=[1080, 400])
            n += 3
    for style in ["navy", "white", "sky"]:
        for ic in HIGHLIGHTS:
            d = highlight(ic, style)
            d.save(OUT / "instagram" / "highlights" / style / f"parcelfly-highlight-{ic}.svg", png=[1080])
            n += 2
    for (w, h), tag in [((1080, 1080), "square"), ((1080, 1350), "portrait")]:
        for i, svc in enumerate(SERVICES, start=1):
            save(post_service(w, h, svc, i), OUT / "posts" / tag / f"parcelfly-post-service-{i:02d}", True)
        save(post_brand(w, h, "en"), OUT / "posts" / tag / "parcelfly-post-tagline-en", True)
        save(post_brand(w, h, "bn"), OUT / "posts" / tag / "parcelfly-post-tagline-bn", True)
        save(post_steps(w, h), OUT / "posts" / tag / "parcelfly-post-how-it-works", True)
        save(post_hiring(w, h), OUT / "posts" / tag / "parcelfly-post-riders-wanted", True)
        save(post_track(w, h), OUT / "posts" / tag / "parcelfly-post-track", True)
        save(post_coverage(w, h), OUT / "posts" / tag / "parcelfly-post-hub-network", True)
        n += 24
    for (w, h), tag in [((1080, 1080), "square"), ((1080, 1350), "portrait")]:
        for hb in MP.hubs():
            save(post_hub(w, h, hb["key"]), OUT / "posts" / tag / f"parcelfly-post-hub-{hb['key']}", True)
            n += 2
    save(story_hubs(), OUT / "stories" / "parcelfly-story-hub-network", True)
    for hb in MP.hubs():
        save(story_hubs(hb["key"]), OUT / "stories" / f"parcelfly-story-hub-{hb['key']}", True)
        n += 2
    for kind, name in [("tagline", "tagline"), ("steps", "how-it-works"), ("hiring", "riders-wanted"), ("coverage", "hub-network")]:
        save(post_wide(kind), OUT / "posts" / "landscape" / f"parcelfly-post-{name}", True)
        n += 2
    for kind in ["brand", "merchant", "rider", "track"]:
        save(story(kind), OUT / "stories" / f"parcelfly-story-{kind}", True)
        n += 2
    # YouTube watermark (transparent, 150 px)
    d = Doc(150, 150, title="Parcel Fly watermark")
    frag, _ = LY.place_logo("symbol", "white", 10, 10, w=130, h=130, valign="middle")
    d.add(frag)
    d.save(OUT / "youtube" / "parcelfly-youtube-watermark.svg", png=[150])
    print(f"social: ~{n} files")


if __name__ == "__main__":
    main()
