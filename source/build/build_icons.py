"""App, web and platform icons for the brand and each sub-brand app, plus the pictogram library.

icons/app/<app>/{ios,android,expo,web}/...   icons/pictograms/...
The icon artwork is the "flight crop": the symbol enlarged so the parcel and facets fill 62 % of the tile with the
nose at 89 %, the wings running off the left edge. It keeps the exact logo geometry and stays legible at 16 px.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pfbrand import ROOT, symbol as S  # noqa: E402
from pfbrand import pictograms as P  # noqa: E402
from pfbrand.brand import ICON_SCHEMES, NAVY, SKY, WHITE, NAME  # noqa: E402
from pfbrand.svg import Doc, png_image, render_png  # noqa: E402
from pfbrand.text import fmt  # noqa: E402
from pfbrand import logo as L  # noqa: E402
from pfbrand.export import fragment_doc  # noqa: E402

OUT = ROOT / "icons"
SKILL = ROOT / ".claude" / "skills" / "logo-design" / "scripts"
NOSE, SPAN = 0.89, 0.62
RX = 0.2237  # iOS-like corner radius for previews and favicons

APPS = {
    "parcelfly": ("brand", NAME, "Parcel Fly", "Fast, careful and trackable parcel delivery across Dhaka."),
    "merchant": ("merchant", "Parcel Fly Merchant", "Parcel Fly", "Create, track and settle your Parcel Fly deliveries."),
    "rider": ("rider", "Parcel Fly Rider", "PF Rider", "Pickups, deliveries and earnings for Parcel Fly riders."),
    "hub": ("hub", "Parcel Fly Hub", "PF Hub", "Hub operations for Parcel Fly managers."),
    "admin": ("admin", "Parcel Fly Admin", "PF Admin", "Parcel Fly administration."),
}


def crop_group(way, vx, vy, vs):
    """Symbol composed inside the visible box (vx, vy, vs x vs)."""
    k = vs * SPAN / (S.WIDTH - (S.CX - S.D))
    x = vx + vs * NOSE - S.WIDTH * k
    y = vy + (vs - S.HEIGHT * k) / 2
    return f'<g transform="translate({fmt(x)} {fmt(y)}) scale({k:.6f})">{S.svg_group(way)}</g>'


def tile_doc(scheme, size=1024, rx=0.0, safe=1.0, bg=True, way=None, title=""):
    sc = ICON_SCHEMES[scheme]
    way = way or sc["way"]
    d = Doc(size, size, title=title)
    vs = size * safe
    v0 = (size - vs) / 2
    d.defs_add(f'<clipPath id="tile"><rect width="{fmt(size)}" height="{fmt(size)}" rx="{fmt(rx * size)}"/></clipPath>')
    if bg:
        d.rect(0, 0, size, size, sc["tile"], rx=rx * size)
    d.add(f'<g clip-path="url(#tile)">{crop_group(way, v0, v0, vs)}</g>')
    return d


def png(doc, path, px):
    path.parent.mkdir(parents=True, exist_ok=True)
    render_png(doc.svg(), path, px, doc.w, doc.h)


def build_app(app):
    scheme, name, short, desc = APPS[app]
    sc = ICON_SCHEMES[scheme]
    base = OUT / "app" / app
    title = f"{name} app icon"
    # ---------------- master + iOS (square, opaque: iOS applies its own mask)
    master = tile_doc(scheme, 1024, 0, title=title)
    master.save(base / f"{app}-icon-master.svg")
    rounded = tile_doc(scheme, 1024, RX, title=title)
    rounded.save(base / f"{app}-icon-rounded.svg", png=[1024])
    for s in [1024, 180, 167, 152, 120, 87, 80, 76, 60, 58, 40, 29, 20]:
        png(master, base / "ios" / f"AppIcon-{s}.png", s)
    # ---------------- Android
    png(master, base / "android" / "play-store-512.png", 512)
    fg = tile_doc(scheme, 432, 0, safe=72 / 108, bg=False)                 # adaptive foreground (108dp, 72dp visible)
    mono = tile_doc(scheme, 432, 0, safe=72 / 108, bg=False, way="white")  # themed icon (Android 13+)
    bgd = Doc(432, 432, bg=sc["tile"])
    fg.save(base / "android" / "adaptive" / "ic_launcher_foreground.svg")
    for d_, n in [(fg, "ic_launcher_foreground"), (mono, "ic_launcher_monochrome"), (bgd, "ic_launcher_background")]:
        png(d_, base / "android" / "adaptive" / f"{n}.png", 432)
    (base / "android" / "adaptive" / "ic_launcher.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '    <background android:drawable="@color/ic_launcher_background"/>\n'
        '    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n'
        '    <monochrome android:drawable="@mipmap/ic_launcher_monochrome"/>\n</adaptive-icon>\n'
        f'<!-- values/colors.xml: <color name="ic_launcher_background">{sc["tile"]}</color> -->\n', encoding="utf-8")
    legacy = tile_doc(scheme, 512, 0.18)
    rnd = Doc(512, 512)
    rnd.defs_add('<clipPath id="tile"><circle cx="256" cy="256" r="256"/></clipPath>')
    rnd.circle(256, 256, 256, sc["tile"])
    rnd.add(f'<g clip-path="url(#tile)">{crop_group(sc["way"], 512 * 0.12, 512 * 0.12, 512 * 0.76)}</g>')
    for dpi, s in [("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)]:
        png(legacy, base / "android" / f"mipmap-{dpi}" / "ic_launcher.png", s)
        png(rnd, base / "android" / f"mipmap-{dpi}" / "ic_launcher_round.png", s)
    note = tile_doc(scheme, 96, 0, safe=0.9, bg=False, way="white")
    for dpi, s in [("mdpi", 24), ("hdpi", 36), ("xhdpi", 48), ("xxhdpi", 72), ("xxxhdpi", 96)]:
        png(note, base / "android" / f"drawable-{dpi}" / "ic_stat_parcelfly.png", s)
    # ---------------- Expo (rider-mobile uses these names)
    png(master, base / "expo" / "icon.png", 1024)
    efg = tile_doc(scheme, 1024, 0, safe=72 / 108, bg=False)
    png(efg, base / "expo" / "adaptive-icon.png", 1024)
    emono = tile_doc(scheme, 1024, 0, safe=72 / 108, bg=False, way="white")
    png(emono, base / "expo" / "adaptive-icon-monochrome.png", 1024)
    frag, bb = L.stacked("color", descriptor_label=None if app == "parcelfly" else name.replace("Parcel Fly ", ""))
    sp = fragment_doc(frag, bb, f"{name} splash")
    png(sp, base / "expo" / "splash-icon.png", 1024)
    frag, bb = L.stacked("ondark", descriptor_label=None if app == "parcelfly" else name.replace("Parcel Fly ", ""))
    png(fragment_doc(frag, bb, f"{name} splash (dark)"), base / "expo" / "splash-icon-dark.png", 1024)
    png(rounded, base / "expo" / "favicon.png", 48)
    (base / "expo" / "app.json-snippet.json").write_text(json.dumps({
        "icon": "./assets/images/icon.png",
        "android": {"adaptiveIcon": {"foregroundImage": "./assets/images/adaptive-icon.png",
                                     "monochromeImage": "./assets/images/adaptive-icon-monochrome.png",
                                     "backgroundColor": sc["tile"]}},
        "plugins": [["expo-splash-screen", {"image": "./assets/images/splash-icon.png", "imageWidth": 200,
                                            "resizeMode": "contain", "backgroundColor": "#ffffff",
                                            "dark": {"image": "./assets/images/splash-icon-dark.png",
                                                     "backgroundColor": NAVY}}]],
        "web": {"favicon": "./assets/images/favicon.png"},
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    # ---------------- Web / PWA
    web = base / "web"
    fav = tile_doc(scheme, 256, RX, title=f"{name} favicon")
    fav.save(web / "favicon.svg")
    for s in [16, 32, 48, 96]:
        png(fav, web / f"favicon-{s}.png", s)
    subprocess.run([sys.executable, str(SKILL / "render_png.py"), str(web / "favicon.svg"), "--ico",
                    str(web / "favicon.ico"), "--ico-sizes", "16", "32", "48"], check=True, capture_output=True)
    png(master, web / "apple-touch-icon.png", 180)
    png(rounded, web / "icon-192.png", 192)
    png(rounded, web / "icon-512.png", 512)
    mask = tile_doc(scheme, 512, 0, safe=0.8)
    png(mask, web / "icon-192-maskable.png", 192)
    png(mask, web / "icon-512-maskable.png", 512)
    png(master, web / "mstile-150.png", 150)
    pin = tile_doc(scheme, 256, 0, safe=1.0, bg=False, way="black")
    pin.save(web / "safari-pinned-tab.svg")
    (web / "site.webmanifest").write_text(json.dumps({
        "name": name, "short_name": short, "description": desc,
        "start_url": "/", "scope": "/", "display": "standalone",
        "background_color": "#ffffff", "theme_color": sc["theme"],
        "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
                  {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
                  {"src": "/icon-192-maskable.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable"},
                  {"src": "/icon-512-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}],
    }, indent=2), encoding="utf-8")
    (web / "head-snippet.html").write_text(
        '<link rel="icon" href="/favicon.ico" sizes="48x48">\n'
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png">\n'
        f'<link rel="mask-icon" href="/safari-pinned-tab.svg" color="{sc["theme"]}">\n'
        '<link rel="manifest" href="/site.webmanifest">\n'
        f'<meta name="theme-color" content="{sc["theme"]}">\n', encoding="utf-8")


def build_pictograms():
    out = OUT / "pictograms"
    for name in P.ICONS:
        for cname, col in [("navy", NAVY), ("sky", SKY), ("white", WHITE), ("black", "#000000")]:
            d = Doc(48, 48, title=P.LABELS[name])
            d.add(P.icon(name, 0, 0, 48, col))
            d.save(out / cname / f"pf-icon-{name}.svg", png=[192] if cname in ("navy", "white") else None)
    # one sprite sheet for quick reference
    names = list(P.ICONS)
    cols = 6
    sheet = Doc(cols * 180, ((len(names) + cols - 1) // cols) * 200, bg="#FFFFFF", title="Parcel Fly pictograms")
    from pfbrand import text as T
    for i, n in enumerate(names):
        x, y = (i % cols) * 180 + 42, (i // cols) * 200 + 24
        sheet.add(P.icon(n, x, y, 96, NAVY))
        sheet.add(T.text(P.LABELS[n], "montserrat", 16, x + 48, y + 136, "#55607A", "middle", 600))
    sheet.save(out / "pf-pictograms-sheet.svg", png=[1080])


def main():
    for app in APPS:
        build_app(app)
    build_pictograms()
    n = sum(1 for _ in OUT.rglob("*") if _.is_file())
    print(f"icons: {n} files")


if __name__ == "__main__":
    main()
