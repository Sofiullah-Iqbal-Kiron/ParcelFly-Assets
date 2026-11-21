"""Hub network maps (real geography) and the Bangladesh map.

maps/hub-network/   every hub, dark and light, square / landscape / portrait, English+Bangla / English / Bangla labels
maps/hubs/          one map per hub with that hub highlighted
maps/bangladesh/    Bangladesh with major rivers, Dhaka and Narayanganj marked (Natural Earth)
maps/poster/        A3 hub network poster (print)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pfbrand import ROOT, layout as LY, maps as MP, text as T  # noqa: E402
from pfbrand.brand import CLOUD, CONTACT, CYAN, NAVY, SKY, SLATE, WHITE, TAGLINE, TAGLINE_BN  # noqa: E402
from pfbrand.svg import Doc  # noqa: E402

OUT = ROOT / "maps"


def save(d, path, png_w=None, jpg=False):
    return d.save(path.with_suffix(".svg"), png=[png_w or int(d.w)], jpg=[int(d.w)] if jpg else None)


def network_maps():
    n = 0
    for style in ["dark", "light"]:
        for fmt_name, (w, h) in {"square": (2000, 2000), "landscape": (1920, 1080), "portrait": (1080, 1350)}.items():
            for lab in (["both", "en", "bn"] if fmt_name == "square" else ["both"]):
                d = Doc(w, h, title="Parcel Fly hub network map")
                d.add(MP.hub_map(0, 0, w, h, style, labels=lab, scalebar=True, clip_id="m",
                                 hub_suffix=" Hub"))
                suffix = "" if lab == "both" else f"-{lab}"
                n += len(save(d, OUT / "hub-network" / f"parcelfly-hub-map-{fmt_name}{suffix}-{style}"))
    for h_ in MP.hubs():
        for style in ["dark", "light"]:
            d = Doc(1080, 1080, title=f"Parcel Fly {h_['name']} Hub map")
            d.add(MP.hub_map(0, 0, 1080, 1080, style, highlight=h_["key"], scalebar=True, clip_id="m"))
            n += len(save(d, OUT / "hubs" / f"parcelfly-hub-map-{h_['key']}-{style}"))
    return n


def bangladesh_maps():
    n = 0
    for style, bg in [("dark", NAVY), ("light", CLOUD)]:
        d = Doc(1200, 1500, bg=bg, title="Bangladesh map: Parcel Fly")
        d.add(MP.bangladesh_map(0, 0, 1200, 1500, style, clip_id="bd"))
        n += len(save(d, OUT / "bangladesh" / f"parcelfly-bangladesh-map-{style}"))
        # transparent version for the website (replaces the hand-traced outline)
        d = Doc(480, 640, title="Bangladesh map")
        d.add(MP.bangladesh_map(0, 0, 480, 640, style, labels=False, clip_id="bdt"))
        n += len(save(d, OUT / "bangladesh" / f"parcelfly-bangladesh-outline-{style}-transparent", png_w=960))
    return n


def poster():
    """A3 landscape (420 x 297 mm) hub network poster for hubs, offices and merchants' counters."""
    W, H = 420.0, 297.0
    d = Doc(W, H, unit="mm", title="Parcel Fly hub network poster A3")
    d.rect(0, 0, W, H, WHITE)
    mx = 150.0
    d.add(MP.hub_map(mx, 0, W - mx, H, "light", scalebar=True, clip_id="pm", label_size=7.2, node_size=4.2))
    frag, _ = LY.place_logo("horizontal", "color", 18, 18, w=96)
    d.add(frag)
    d.add(LY.label("Hub network", 18, 62, 4.2, SKY))
    hfrag, last = LY.heading(MP.headline(), 18, 78, 11, NAVY, max_width=118)
    d.add(hfrag)
    y = last + 16
    hs_ = MP.hubs()
    step = min(17.0, (H - 74 - 10 - y) / len(hs_))        # the list always ends above the QR block
    for i, h_ in enumerate(hs_):
        yy = y + i * step
        d.add(LY.parcel(23, yy - 2.2, 3.6, NAVY))
        d.add(LY.parcel(23, yy - 2.2, 1.6, CYAN))
        d.add(T.text(f"{h_['name']} Hub", "montserrat", 6.0, 31, yy, NAVY, "start", 800))
        d.add(T.text(f"{h_['name_bn']} হাব", "mina-bold", 5.0, 31, yy + 6.2, SKY, "start"))
    q = 34
    d.rect(18, H - 74, q, q, WHITE)
    d.add(LY.qr(CONTACT["url"], 18, H - 74, q, NAVY, quiet=1))
    d.add(T.text("Scan to become a merchant", "montserrat", 3.6, 18 + q + 5, H - 74 + 14, NAVY, "start", 800))
    d.add(T.text("or track a parcel", "montserrat", 3.4, 18 + q + 5, H - 74 + 19.5, SLATE, "start", 600))
    d.add(T.text(f"{CONTACT['phone_intl']}  ·  {CONTACT['web']}", "montserrat", 4.6, 18, H - 22, NAVY, "start", 700))
    b0, b1, b2, b3 = T.ink_bounds(TAGLINE_BN, "mina-bold", 5.4)
    d.add(T.text(f"{TAGLINE}  ·", "montserrat", 4.4, 18, H - 13, SLATE, "start", 600))
    d.add(T.text(TAGLINE_BN, "mina-bold", 5.0, 18 + T.advance(f"{TAGLINE}  · ", "montserrat", 4.4, 600), H - 13, SLATE))
    gid = "pfl"
    d.defs_add(LY.flight_gradient(gid))
    d.rect(0, H - 4, W, 4, f"url(#{gid})")
    d.save(OUT / "poster" / "parcelfly-hub-network-poster-a3.svg", pdf=True, png=[3508])
    return 3


def main():
    n = network_maps() + bangladesh_maps() + poster()
    print(f"maps: {n} files")


if __name__ == "__main__":
    main()
