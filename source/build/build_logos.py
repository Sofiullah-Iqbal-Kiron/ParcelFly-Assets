"""Build every logo lockup in every colourway: logo/<family>/parcelfly-<lockup>-<colourway>.{svg,pdf,eps,png,jpg}"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pfbrand import ROOT, logo as L  # noqa: E402
from pfbrand.brand import SUBBRANDS  # noqa: E402
from pfbrand.export import export_logo  # noqa: E402

OUT = ROOT / "logo"
WAYS = ["color", "ondark", "navy", "black", "white", "grey"]

LOCKUPS = {
    # family: [(lockup name, builder, title)]
    "primary-stacked": [("stacked", lambda w: L.stacked(w), "Parcel Fly logo, stacked")],
    "horizontal": [("horizontal", lambda w: L.horizontal(w), "Parcel Fly logo, horizontal")],
    "symbol": [("symbol", lambda w: L.symbol_only(w), "Parcel Fly symbol")],
    "wordmark": [("wordmark", lambda w: L.wordmark_only(w), "Parcel Fly wordmark")],
    "tagline": [
        ("stacked-tagline-en", lambda w: L.stacked(w, tagline="en"), "Parcel Fly logo with tagline"),
        ("stacked-tagline-bn", lambda w: L.stacked(w, tagline="bn"), "Parcel Fly logo with Bangla tagline"),
        ("horizontal-tagline-en", lambda w: L.horizontal(w, tagline="en"), "Parcel Fly logo with tagline"),
        ("horizontal-tagline-bn", lambda w: L.horizontal(w, tagline="bn"), "Parcel Fly logo with Bangla tagline"),
    ],
    "bangla": [
        ("bn-stacked", lambda w: L.stacked(w, lang="bn"), "Parcel Fly Bangla logo, stacked"),
        ("bn-horizontal", lambda w: L.horizontal(w, lang="bn"), "Parcel Fly Bangla logo, horizontal"),
        ("bn-stacked-tagline", lambda w: L.stacked(w, lang="bn", tagline="bn"), "Parcel Fly Bangla logo with tagline"),
        ("bn-horizontal-tagline", lambda w: L.horizontal(w, lang="bn", tagline="bn"),
         "Parcel Fly Bangla logo with tagline"),
        ("bn-wordmark", lambda w: L.wordmark_only(w, lang="bn"), "Parcel Fly Bangla wordmark"),
    ],
}


def main():
    count = 0
    for family, items in LOCKUPS.items():
        for name, build, title in items:
            for way in WAYS:
                frag, bb = build(way)
                outs = export_logo(frag, bb, OUT / family / f"parcelfly-{name}-{way}", title, way)
                count += len(outs)
    # sub-brands: descriptor lockups (no grey)
    for key, sb in SUBBRANDS.items():
        label = sb["label"]
        for way in ["color", "ondark", "navy", "black", "white"]:
            for name, build in [
                ("horizontal", lambda w: L.horizontal(w, descriptor_label=label)),
                ("stacked", lambda w: L.stacked(w, descriptor_label=label)),
                ("inline", lambda w: L.subbrand_horizontal(label, w)),
            ]:
                frag, bb = build(way)
                outs = export_logo(frag, bb, OUT / "sub-brands" / key / f"parcelfly-{key}-{name}-{way}",
                                   f"Parcel Fly {label} logo", way, png_widths=(600, 1800))
                count += len(outs)
    print(f"logos: {count} files")


if __name__ == "__main__":
    main()
