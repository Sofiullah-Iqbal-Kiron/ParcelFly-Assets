"""One-image overview of the kit (parcelfly-brand-kit-overview.png) assembled from the built files."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pfbrand import ROOT, text as T  # noqa: E402
from pfbrand.svg import Doc, png_image  # noqa: E402

W = 2400
BG = (243, 248, 252)


def load(rel, w=None, h=None, bg=(255, 255, 255)):
    im = Image.open(ROOT / rel).convert("RGBA")
    if bg is not None:
        b = Image.new("RGBA", im.size, bg + (255,))
        b.alpha_composite(im)
        im = b
    r = (w / im.width) if w else (h / im.height)
    return im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)


def heading(sheet, s, y):
    d = Doc(W, 90)
    d.add(T.text(s.upper(), "montserrat", 30, 80, 60, "#0077C9", "start", 800, tracking=0.16))
    sheet.alpha_composite(png_image(d.svg(), W, W, 90), (0, y))
    return y + 90


def row(sheet, ims, y, gap=30, x=80):
    h = 0
    for im in ims:
        sheet.alpha_composite(im, (x, y))
        x += im.width + gap
        h = max(h, im.height)
    return y + h + 50


def main():
    sheet = Image.new("RGBA", (W, 14000), BG + (255,))
    top = Image.new("RGBA", (W, 520), (0, 0, 128, 255))
    sheet.alpha_composite(top, (0, 0))
    lg = load("logo/primary-stacked/parcelfly-stacked-ondark-2400.png", h=330, bg=None)
    sheet.alpha_composite(lg, (80, 95))
    d = Doc(1300, 400)
    d.add(T.text("Brand kit", "montserrat", 110, 0, 170, "#FFFFFF", "start", 800))
    d.add(T.text("Logos · icons · social · print · packaging · merch · mockups · web · wallpapers", "montserrat", 34, 4, 250,
                 "#00B5D8", "start", 600))
    d.add(T.text("সবসময়, সবখানে", "mina-bold", 56, 4, 340, "#FFFFFF"))
    sheet.alpha_composite(png_image(d.svg(), 1300, 1300, 400), (700, 70))
    y = 580
    y = heading(sheet, "Logo family", y)
    y = row(sheet, [load("logo/primary-stacked/parcelfly-stacked-color-1200.png", h=260),
                    load("logo/horizontal/parcelfly-horizontal-color-1200.png", w=700),
                    load("logo/bangla/parcelfly-bn-stacked-color-1200.png", h=260),
                    load("logo/horizontal/parcelfly-horizontal-ondark-on-navy.jpg", w=560)], y)
    y = heading(sheet, "App icons", y)
    y = row(sheet, [load(f"icons/app/{a}/{a}-icon-rounded.png", h=220, bg=BG) for a in ("parcelfly", "rider", "hub", "admin")]
            + [load("icons/pictograms/pf-pictograms-sheet.png", h=300)], y)
    y = heading(sheet, "Social media", y)
    y = row(sheet, [load("social/facebook/parcelfly-cover-signature.jpg", w=740), load("social/facebook/parcelfly-cover-bangla.jpg", w=740),
                    load("social/facebook/parcelfly-cover-merchant.jpg", w=740)], y)
    y = row(sheet, [load("social/posts/square/parcelfly-post-service-03.jpg", h=360), load("social/posts/square/parcelfly-post-tagline-bn.jpg", h=360),
                    load("social/posts/square/parcelfly-post-how-it-works.jpg", h=360), load("social/stories/parcelfly-story-rider.jpg", h=360),
                    load("social/stories/parcelfly-story-track.jpg", h=360), load("social/facebook/parcelfly-profile-navy-400.png", h=200)], y)
    y = heading(sheet, "Hub network", y)
    y = row(sheet, [load("maps/hub-network/parcelfly-hub-map-landscape-dark.png", h=560),
                    load("social/posts/square/parcelfly-post-hub-rampura.jpg", h=560),
                    load("stamps/digital-inked/parcelfly-hub-stamp-mirpur.png", h=300)], y)
    y = heading(sheet, "Motion", y)
    import build_motion as BM
    from pfbrand import motion as MO
    A = BM.CATALOGUE["horizontal-build"]("color")[0]
    fit = MO.Fit(A.extent, 1000, None, pad=0.25)
    strip = [png_image(MO.frame_svg(A, A.duration * f, fit, "#FFFFFF"), 430, fit.w, fit.h) for f in (0.15, 0.35, 0.55, 0.8, 1.0)]
    y = row(sheet, strip, y, gap=14)
    y = heading(sheet, "Bags", y)
    y = row(sheet, [load("mockups/bags/parcelfly-bag-family.jpg", w=2240)], y)
    y = heading(sheet, "Stationery, stamps and seals", y)
    y = row(sheet, [load("stationery/business-card/parcelfly-business-card-a-front-navy.png", w=520),
                    load("stationery/business-card/parcelfly-business-card-a-back-white.png", w=520),
                    load("stamps/digital-inked/parcelfly-stamp-delivered.png", w=420, bg=BG),
                    load("stamps/digital-inked/parcelfly-company-seal.png", h=300, bg=BG),
                    load("seals/color/parcelfly-seal-official-partner-color-1000.png", h=300, bg=BG)], y)
    y = heading(sheet, "Stickers and packaging", y)
    y = row(sheet, [load("stickers/sheet/parcelfly-sticker-sheet-a4-p2.png", h=640), load("stickers/sheet/parcelfly-sticker-sheet-a4-p1.png", h=640),
                    load("packaging/mailer/parcelfly-poly-mailer-front.png", h=640),
                    load("packaging/delivery-box/parcelfly-delivery-box-decal-square-400x400.png", h=420)], y)
    y = row(sheet, [load("packaging/tape/parcelfly-tape-48mm-repeat-navy.png", w=1100), load("signage/signboard/parcelfly-signboard-mirpur-hub.png", w=1100)], y)
    y = heading(sheet, "Merchandise", y)
    y = row(sheet, [load("mockups/merch/parcelfly-merch-family.jpg", w=2240)], y)
    y = row(sheet, [load("mockups/merch/parcelfly-mugs.jpg", w=740), load("mockups/merch/parcelfly-paper-cups.jpg", w=740),
                    load("mockups/merch/parcelfly-desk-flatlay.jpg", w=740)], y)
    y = heading(sheet, "Mockups", y)
    y = row(sheet, [load("mockups/stationery/parcelfly-stationery-flatlay.jpg", w=740),
                    load("mockups/packaging/parcelfly-packaging-family.jpg", w=740),
                    load("mockups/signage/parcelfly-storefront-mirpur-hub.jpg", w=740)], y)
    y = row(sheet, [load("mockups/apparel/parcelfly-tshirt-front-back.jpg", w=740),
                    load("mockups/stationery/parcelfly-id-cards-lanyards.jpg", w=740),
                    load("mockups/packaging/parcelfly-poly-mailers.jpg", w=740)], y)
    y = heading(sheet, "Website and wallpapers", y)
    y = row(sheet, [load("web/banners/parcelfly-banner-hub-network-desktop-1920x640.jpg", w=1110),
                    load("web/banners/parcelfly-banner-become-a-merchant-desktop-1920x640.jpg", w=1110)], y)
    y = row(sheet, [load("wallpapers/parcelfly-wallpapers-overview.jpg", w=2240)], y)
    y = heading(sheet, "Colour", y)
    y = row(sheet, [load("colors/parcelfly-palette.png", w=1300)], y)
    sheet = sheet.crop((0, 0, W, y + 40)).convert("RGB")
    sheet.save(ROOT / "parcelfly-brand-kit-overview.png", optimize=True)
    small = sheet.resize((1200, int(sheet.height * 1200 / W)), Image.LANCZOS)
    small.save(ROOT / "guidelines" / "parcelfly-brand-kit-overview-1200.jpg", quality=88)
    print("overview: 2 files")


if __name__ == "__main__":
    main()
