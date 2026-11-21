# Parcel Fly brand assets

Home of the Parcel Fly brand kit. Sibling repos (admin-frontend, client-frontend, manager-frontend,
api-backend, rider-mobile, ...) live in `/home/kiron/Documents/Parcel Fly/`. `README.md` is the user-facing index.

## The logo is final

The Parcel Fly logo is finalized and in production. Do not propose new concepts or a redesign. Work in the
logo-design skill's **Assets** and **System** modes only.

- The masters are a measured vector rebuild of the production PNG (`client-frontend/public/Transparent Logo.png`):
  geometry lives in `source/build/pfbrand/symbol.py` (256-unit parcel, 26-unit channels, 45 deg edges).
- The wordmark is Nasalization Rg, tracking -0.05 em, stored only as outlined artwork in `source/master/`.
  Typodermic desktop EULA: never commit, bundle or upload the font; never use it for live or editable text.
  `extract_wordmark.py` takes a local font path when the outline must be regenerated.
- The old production PNG's drop shadow is retired; masters are flat.

## Decisions already made (do not re-ask)

- Bangla lockup: পার্সেল ফ্লাই in **Mina Bold**, sized so stems match Nasalization (`logo.py`, `BN_SIZE`).
- Taglines: "Always, Everywhere" (Montserrat SemiBold caps, +0.2 em) and "সবসময়, সবখানে" (Mina Bold).
- Brand type: Montserrat (English), Noto Sans Bengali (Bangla body), Geist Mono (codes). Only OFL fonts in `source/fonts/`.
- Small sizes and app icons use the "flight crop" (parcel + facets fill 62 % of the tile, nose at 89 %, wings bleed
  off the left). Never crop the parcel or the arrow of a hero symbol; only the wings may bleed.
- Icon schemes (`brand.ICON_SCHEMES`): brand/merchant navy tile, rider white tile, hub cyan tile, admin ink tile with
  amber parcel.
- CMYK from FOGRA39 coated / FOGRA29 uncoated ICC profiles; Pantone values are nearest matches.
- Five hubs (confirmed by the user on 2026-11-21): Bakshibazar, Jatrabari, Mirpur, Rampura, Narayanganj.
  `source/geo/hubs.json` is the single source for hub names (English and Bangla) and positions; every hub asset reads it.
- Maps are real geography (`pfbrand/maps.py`): OpenStreetMap layers in `source/geo/dhaka-region.json` (ODbL, the
  "© OpenStreetMap contributors" credit must stay visible on every map), Natural Earth for Bangladesh.
  `fetch_geo.py` refreshes the data; hub pins are area centres, not street addresses.

## Building

```bash
.venv/bin/python source/build/build_all.py      # everything; motion renders only missing files (--motion-force to redo)
.venv/bin/python source/build/build_social.py   # or one area at a time
```

- `.venv` (uv) holds the packages in `source/build/requirements.txt`; system Python has no SVG renderer.
- All text is outlined with HarfBuzz (`pfbrand/text.py`), with Bangla font fallback. A missing glyph raises an error:
  keep that guard, it is how tofu boxes are caught.
- Output folders (`logo/`, `icons/`, `maps/`, `bags/`, `merch/`, `mockups/`, `web/`, `wallpapers/`, `social/`, `stamps/`,
  `seals/`, `stickers/`, `stationery/`, `packaging/`, `apparel/`, `signage/`, `patterns/`, `colors/`, `email/`, `motion/`,
  `guidelines/`, `presentation/`) are generated:
  edit the code in `source/build/`, not the outputs.
- After visual changes, render and look at the PNGs before reporting (the skill rule "look at your work").
- The build post-processes the skill's HTML to remove em dashes (house rule: no em dash in any file).
- Motion (`pfbrand/motion.py`, `build_motion.py`): one timeline per animation exported to CSS SVG, Lottie, MP4, WebM,
  WebP and GIF. Parts come from the static lockups, so animations always end on the master. The logo is only
  translated, rotated, uniformly scaled or faded; `sx`/`sy` are for speed lines only. `--preview` renders frames from
  both the engine and rlottie (Lottie check) to /tmp/pf-motion-preview.png. Keep motion export at 3 workers: more
  workers run a 7 GB machine out of memory.
- Bags and mockups (`pfbrand/bags.py`, `pfbrand/mockup.py`, `build_bags.py`): flat print artwork in mm, then a small
  3D renderer (pinhole camera, perspective-warped faces, generated textures, rope/strap handles, scene-space shadows).
  Dieline panels are clipped to their own area. Lay scenes out with `row()` so nothing overlaps.

- Merch and mockups (`pfbrand/merch.py`, `pfbrand/props.py`, `build_merch.py`, `build_mockups.py`): print files in
  `merch/print/`, every mockup in `mockups/<area>/` (bags included). `props.py` renders products with numpy shading:
  `Lathe` (raised orthographic camera) for mugs, paper cups and tape rolls, `carton()` for boxes (pick `pitch` so the
  top shows), top-down flat lays with `surface()`, `lay()` and `finish()`, pens, laptop lid, books, T-shirts, caps,
  storefront and roll-up. Mug wraps put each half's centre on the quarter points; the mug turns so it faces the camera.
- Web and wallpapers (`build_web.py`, `build_wallpapers.py`): `web/` banners, hero backgrounds and cards for the client
  panel; `wallpapers/<audience>/<device>/` for generic, merchant, client, rider, hub manager, staff and admin. Map
  wallpapers fit hubs and labels with `fit_extent()` and must keep the OSM credit (drawn under the lockup).
- Shared colourways: `logo.resolve()` knows `hub` (navy text, white tagline) and `admin` (white text, amber tagline);
  `maps.STYLES["ink"]` is the admin map. Only use them on their own grounds.

## logo-design skill

Installed project-scoped at `.claude/skills/logo-design` from https://github.com/kaankiziltug/logo-design-skill (MIT),
commit `e9eaddc07895575253d6663320354a708f53e955`. Run its scripts with `.venv/bin/python`. The library has no
logistics tag; use `--industry travel-transport`. No Chrome is installed, so its HTML sheets cannot be screenshotted
here (`render_png.py` HTML mode needs Chrome).
