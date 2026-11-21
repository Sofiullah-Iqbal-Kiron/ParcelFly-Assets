"""Website artwork for the client panel landing page: promo banners, hero backgrounds and cards.

web/banners/<name>-{desktop-1920x640,mobile-1080x1080}.{svg,png,webp,jpg}
web/hero-backgrounds/  text-free backgrounds for live HTML text (left side kept calm)
web/cards/             service and feature cards (light and dark)
Copy comes from the live client-frontend home page (page.tsx); see README.md, Website artwork.
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pfbrand import ROOT, layout as LY, scenes as SC, symbol as S, text as T  # noqa: E402
from pfbrand import maps as MP, pictograms as P  # noqa: E402
from pfbrand.brand import (CLOUD, CONTACT, COBALT, CYAN, MINT, MIST, NAVY, SKY, SLATE, TAGLINE, TAGLINE_BN,  # noqa: E402
                           WHITE, INK)
from pfbrand.svg import Doc, png_image  # noqa: E402
from pfbrand.text import fmt  # noqa: E402

OUT = ROOT / "web"

BANNERS = {
    "become-a-merchant": dict(label="For Dhaka merchants", head="Delivery that keeps up with your business.",
                              sub="Fast, careful and trackable parcel delivery across Dhaka for online sellers, food "
                                  "businesses and growing local brands.", cta="Become a merchant", art="symbol"),
    "hub-network": dict(label="Hub network", head=MP.headline(), sub=MP.hub_line(),
                        cta="See coverage areas", art="map"),
    "cash-on-delivery": dict(label="Cash on delivery", head="Cash on delivery, visible in your account.",
                             sub="Offer customers the payment experience they know while keeping COD and receivables "
                                 "visible in your account.", cta="Become a merchant", art="cash"),
    "fraud-check": dict(label="Fraud check", head="Check a customer before you confirm.",
                        sub="Check a customer number before confirming a risky order.", cta="Sign in to check", art="secure"),
    "track-parcel": dict(label="Track your parcel", head="Every milestone, timestamped.",
                         sub="Follow every milestone from request and review through transit, delivery or return.",
                         cta="Track a parcel", art="track"),
    "frozen-fragile": dict(label="Careful handling", head="Frozen and fragile care.",
                           sub="Purpose-built handling for temperature-sensitive and fragile parcels that need extra "
                               "attention.", cta="Become a merchant", art="frozen"),
    "riders-wanted": dict(label="We're hiring", head="Ride with Parcel Fly.", sub_bn="রাইডার হিসেবে যোগ দিন",
                          sub="Join the rider team that keeps Dhaka moving.", cta=f"Call {CONTACT['phone']}", art="rider",
                          bg=SKY),
    "bangla": dict(label="Parcel Fly", head_bn=TAGLINE_BN, sub_bn="দ্রুত, যত্নশীল ও ট্র্যাকযোগ্য পার্সেল ডেলিভারি, পুরো ঢাকা জুড়ে।",
                   cta_bn="মার্চেন্ট হিসেবে যোগ দিন", art="symbol"),
}


def art_block(d, kind, x, y, w, h, bg):
    """Right-hand visual for a banner inside (x, y, w, h)."""
    if kind == "map":
        d.add(MP.hub_map(x, y, w, h, "dark" if bg != SKY else "dark", inset=False, clip_id=SC.uid("bm"),
                         label_size=min(w, h) * 0.04, node_size=min(w, h) * 0.022, labels="en"))
        return
    if kind == "symbol":
        hh = min(h * 0.62, w * 0.62 * S.HEIGHT / S.WIDTH)
        d.add(SC.watermark("ondark", x + (w - S.WIDTH * hh / S.HEIGHT) / 2, y + (h - hh) / 2, hh))
        return
    if kind == "rider":
        hh = min(h * 0.5, w * 0.62 * S.HEIGHT / S.WIDTH)
        d.add(SC.watermark("white", x + (w - S.WIDTH * hh / S.HEIGHT) / 2, y + (h - hh) / 2, hh))
        return
    # pictogram inside a parcel frame
    s = min(w, h) * 0.62
    cx, cy = x + w / 2, y + h / 2
    d.add(LY.parcel(cx, cy, s * 0.62, CYAN))
    d.add(LY.parcel(cx, cy, s * 0.62 - min(w, h) * 0.022, NAVY if bg != SKY else SKY))
    d.add(P.icon(kind, cx - s * 0.3, cy - s * 0.3, s * 0.6, WHITE, 3.0))


def banner(name, w, h):
    b = BANNERS[name]
    bg = b.get("bg", NAVY)
    d = Doc(w, h, bg=bg, title=f"Parcel Fly banner: {name}")
    if bg == NAVY:
        SC.glow(d, w * 0.85, h * 0.1, max(w, h) * 0.6, COBALT, 0.75)
    d.add(LY.speed_lines(-w * 0.1, h * 0.62, h * 0.3, w * 0.5, (WHITE, WHITE, WHITE), opacity=0.05))
    wide = w / h > 1.6
    m = h * (0.12 if wide else 0.08)
    if wide:
        tx, tw = m * 1.2, w * 0.5
        if b["art"] == "map":
            art_block(d, "map", w * 0.5, 0, w * 0.5, h, bg)
            gid = SC.uid("wf")
            d.defs_add(f'<linearGradient id="{gid}"><stop offset="0" stop-color="{bg}"/><stop offset="1" stop-color="{bg}" stop-opacity="0"/></linearGradient>')
            d.rect(w * 0.5 - 1, 0, w * 0.12, h, f"url(#{gid})")
        else:
            art_block(d, b["art"], w * 0.56, h * 0.08, w * 0.4, h * 0.84, bg)
        top = h * 0.2
    else:
        tx, tw = m, w - 2 * m
        if b["art"] == "map":
            art_block(d, "map", 0, 0, w, h * 0.5, bg)
            gid = SC.uid("wf")
            d.defs_add(f'<linearGradient id="{gid}" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{bg}"/><stop offset="1" stop-color="{bg}" stop-opacity="0"/></linearGradient>')
            d.rect(0, h * 0.5 - h * 0.12, w, h * 0.12 + 1, f"url(#{gid})")
        else:
            art_block(d, b["art"], m, h * 0.06, w - 2 * m, h * 0.42, bg)
        top = h * 0.52
    fg = WHITE
    acc = CYAN if bg == NAVY else NAVY
    ls = h * (0.032 if wide else 0.026)
    y = top
    d.add(LY.label(b["label"], tx, y + ls, ls, acc))
    y += ls * 2.4
    if "head_bn" in b:
        hs = min(h * (0.16 if wide else 0.1), T.fit_size(b["head_bn"], "mina-bold", tw, 400))
        x0, y0, x1, y1 = T.ink_bounds(b["head_bn"], "mina-bold", hs)
        d.add(T.text(b["head_bn"], "mina-bold", hs, tx - x0, y - y0, fg))
        y = y - y0 + y1 + hs * 0.25
    else:
        hs = h * (0.085 if wide else 0.062)
        hfrag, last = LY.heading(b["head"], tx, y + hs * 0.9, hs, fg, max_width=tw)
        d.add(hfrag)
        y = last + hs * 0.55
    if "sub_bn" in b:
        bs = h * (0.045 if wide else 0.034)
        x0, y0, x1, y1 = T.ink_bounds(b["sub_bn"], "noto-bengali", bs, 600)
        sub_lines = T.wrap(b["sub_bn"], "noto-bengali", bs, tw, 600)
        for i, ln in enumerate(sub_lines):
            d.add(T.text(ln, "noto-bengali", bs, tx, y + bs * 1.1 + i * bs * 1.5, acc if "head_bn" not in b else WHITE,
                         "start", 600))
        y += bs * 1.5 * len(sub_lines) + bs * 0.4
    if "sub" in b and ("sub_bn" not in b or not wide):
        ps = h * (0.032 if wide else 0.026)
        pfrag, last = LY.para(b["sub"], tx, y + ps * 1.2, ps, fg, max_width=tw * 0.92, opacity=0.86)
        d.add(pfrag)
        y = last + ps * 0.9
    cta = b.get("cta_bn") or b.get("cta")
    cs = h * (0.032 if wide else 0.026)
    if cta:
        key = "noto-bengali" if "cta_bn" in b else "montserrat"
        c, cb = LY.chip(tx, y + cs * 0.9, cta, cs, CYAN if bg == NAVY else NAVY, NAVY if bg == NAVY else WHITE, key=key)
        d.add(c)
    return d   # no logo: the site navbar already carries it


def hero_background(kind, w, h):
    d = Doc(w, h, bg=NAVY, title=f"Parcel Fly hero background: {kind}")
    wide = w > h
    if kind == "map":
        mx = w * 0.42 if wide else 0
        my = 0 if wide else h * 0.42
        d.add(MP.hub_map(mx, my, w - mx, h - my, "dark", inset=False, clip_id="hm", label_size=min(w, h) * 0.024,
                         node_size=min(w, h) * 0.014, labels="en"))
        gid = SC.uid("hf")
        if wide:
            d.defs_add(f'<linearGradient id="{gid}"><stop offset="0" stop-color="{NAVY}"/><stop offset="1" stop-color="{NAVY}" stop-opacity="0"/></linearGradient>')
            d.rect(mx - 2, 0, w * 0.2, h, f"url(#{gid})")
        else:
            d.defs_add(f'<linearGradient id="{gid}" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{NAVY}"/><stop offset="1" stop-color="{NAVY}" stop-opacity="0"/></linearGradient>')
            d.rect(0, my - 2, w, h * 0.12, f"url(#{gid})")
    elif kind == "flight":
        SC.glow(d, w * 0.85, h * 0.2, max(w, h) * 0.6, COBALT, 0.85)
        hh = h * 1.15
        d.add(SC.watermark(COBALT, w - S.WIDTH * hh / S.HEIGHT * 0.75, (h - hh) / 2, hh, 0.7))
        d.add(LY.speed_lines(-w * 0.05, h * 0.66, h * 0.22, w * 0.55, (SKY, COBALT, CYAN), opacity=0.35))
    elif kind == "lattice":
        SC.gradient_bg(d, [(0, NAVY), (0.6, NAVY), (1, COBALT)], angle=20)
        SC.lattice(d, COBALT, cell=min(w, h) * 0.06, opacity=0.8)
        hh = h * 0.5 if wide else w * 0.35
        d.add(SC.watermark("ondark", w - S.WIDTH * hh / S.HEIGHT - w * 0.06 if wide else (w - S.WIDTH * hh / S.HEIGHT) / 2,
                           (h - hh) / 2 if wide else h * 0.66, hh))
    return d


SERVICE_CARDS = [
    ("fast", "Dhaka-wide", "Fast city delivery", "A Dhaka-focused delivery network designed to move customer orders quickly from pickup to doorstep."),
    ("pickup", "Doorstep service", "Pickup and drop", "Schedule a pickup from your store and let Parcel Fly handle the delivery journey end to end."),
    ("frozen", "Careful handling", "Frozen and fragile care", "Purpose-built handling for temperature-sensitive and fragile parcels that need extra attention."),
    ("parcel", "Food friendly", "Prepared food delivery", "Dependable local delivery for home kitchens, restaurants and food businesses serving Dhaka customers."),
    ("cash", "COD enabled", "Cash on delivery", "Offer customers the payment experience they know while keeping COD and receivables visible in your account."),
    ("pickup", "Flexible fulfilment", "Exchange-ready delivery", "Create exchange parcels and manage returns through the same clear parcel lifecycle."),
]
FEATURE_CARDS = [
    ("parcel", "Save time", "Bulk parcel booking", "Create multiple deliveries together when order volume grows."),
    ("merchant", "Stay organised", "Multi-store control", "Keep pickup details organised across your active stores."),
    ("cash", "Know your numbers", "Receivable visibility", "See COD, charges and clearable parcel breakdowns in one place."),
    ("secure", "Reduce risk", "Fraud check", "Check a customer number before confirming a risky order."),
    ("phone", "One tap away", "Install the merchant app", "Add Parcel Fly to your home screen from the browser for one-tap access."),
]


def card(icon, tag, title, desc, w, h, dark):
    bg, fg, sub, acc = (NAVY, WHITE, "#C9D6F5", CYAN) if dark else (WHITE, NAVY, SLATE, SKY)
    d = Doc(w, h, title=f"Parcel Fly card: {title}")
    r = w * 0.05
    d.rect(0, 0, w, h, bg, rx=r)
    if dark:
        SC.glow(d, w * 0.95, 0, w * 0.7, COBALT, 0.8)
    else:
        d.add(f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="{r}" fill="none" stroke="{MIST}" stroke-width="2"/>')
    square = h / w > 0.95
    m = w * (0.1 if square else 0.08)
    s = w * (0.24 if square else 0.16)
    ts, ds = (w * 0.09, w * 0.046) if square else (w * 0.072, w * 0.036)
    lines = T.wrap(desc, "montserrat", ds, w - 2 * m, 500)
    hs = min(ts, T.fit_size(title, "montserrat", w - 2 * m, 200, 800))
    block = s + w * 0.08 + w * 0.035 + hs * 2.0 + ds * 1.45 * len(lines)
    top = (h - block) / 2 if square else m
    d.add(LY.parcel(m + s / 2, top + s / 2, s * 0.62, CYAN if dark else CLOUD))
    d.add(P.icon(icon, m + s * 0.18, top + s * 0.18, s * 0.64, NAVY, 3.4))
    y = top + s + w * 0.08
    d.add(LY.label(tag, m, y, w * (0.034 if square else 0.03), acc))
    d.add(T.text(title, "montserrat", hs, m, y + w * 0.035 + hs, fg, "start", 800))
    pfrag, last = LY.para(desc, m, y + w * 0.035 + hs * 2.0, ds, sub, max_width=w - 2 * m, weight=500)
    d.add(pfrag)
    return d


def save(d, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    d.save(path.with_suffix(".svg"), png=[int(d.w)])
    im = Image.open(path.with_suffix(".png")).convert("RGBA")
    im.save(path.with_suffix(".webp"), quality=88, method=5)
    if im.getchannel("A").getextrema()[0] == 255:
        im.convert("RGB").save(path.with_suffix(".jpg"), quality=90, optimize=True, progressive=True)
    return 4


def main():
    n = 0
    for name in BANNERS:
        n += save(banner(name, 1920, 640), OUT / "banners" / f"parcelfly-banner-{name}-desktop-1920x640")
        n += save(banner(name, 1080, 1080), OUT / "banners" / f"parcelfly-banner-{name}-mobile-1080x1080")
    for kind in ["map", "flight", "lattice"]:
        n += save(hero_background(kind, 2400, 1000), OUT / "hero-backgrounds" / f"parcelfly-hero-{kind}-desktop-2400x1000")
        n += save(hero_background(kind, 1080, 1600), OUT / "hero-backgrounds" / f"parcelfly-hero-{kind}-mobile-1080x1600")
    for i, (ic, tag, title, desc) in enumerate(SERVICE_CARDS, start=1):
        for dark in (False, True):
            n += save(card(ic, tag, title, desc, 1200, 900, dark),
                      OUT / "cards" / "services" / f"parcelfly-card-service-{i:02d}-{'dark' if dark else 'light'}")
    for i, (ic, tag, title, desc) in enumerate(FEATURE_CARDS, start=1):
        for dark in (False, True):
            n += save(card(ic, tag, title, desc, 1080, 1080, dark),
                      OUT / "cards" / "features" / f"parcelfly-card-feature-{i:02d}-{'dark' if dark else 'light'}")
    print(f"web: {n} files")


if __name__ == "__main__":
    main()
