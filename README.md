# Parcel Fly brand kit

The complete identity library for Parcel Fly, the Dhaka-focused courier for online sellers, food businesses and
growing local brands. Always, Everywhere. সবসময়, সবখানে।

Start with **`guidelines/parcelfly-brand-guidelines.pdf`** (22 pages) and **`parcelfly-brand-kit-overview.png`**.

## Which file do I use?

| I need... | Use |
|---|---|
| The logo on a website or app | `logo/horizontal/parcelfly-horizontal-color.svg` (on dark: `-ondark.svg`) |
| The logo in Word, PowerPoint, Canva | `logo/primary-stacked/parcelfly-stacked-color-1200.png` (or the `-on-white.jpg`) |
| The logo for a printer or sign maker | the `.pdf` or `.eps` next to it, plus the CMYK values in `colors/README.md` |
| A favicon / PWA icons | `icons/app/<app>/web/` (includes `head-snippet.html` and `site.webmanifest`) |
| App store / Expo icons | `icons/app/<app>/ios/`, `icons/app/<app>/android/`, `icons/app/<app>/expo/` |
| A Facebook / Instagram / LinkedIn / X / YouTube image | `social/<platform>/` (covers in 6 designs, profile pictures) |
| A ready post or story | `social/posts/{square,portrait,landscape}/`, `social/stories/` |
| Instagram highlight covers | `social/instagram/highlights/{navy,white,sky}/` |
| Business cards, letterhead, envelope | `stationery/` (letterhead also as `.docx`) |
| Rubber stamps | `stamps/rubber-stamp-vector/` (send the black PDF/EPS to the stamp maker) |
| A stamp for a digital document | `stamps/digital-inked/` |
| Seals and badges for merchants | `seals/{color,light,navy,white}/` |
| Stickers | `stickers/` (artwork with 1 mm bleed + `-cutline` file; A4 sheets in `stickers/sheet/`) |
| Packaging, rider box, tape | `packaging/` |
| Shopping bags, totes, carry bags (to print) | `bags/print/` (paper bag dielines, tote and carry-bag artwork, rider backpack panels) |
| Mockups of every physical item (bags, merch, stationery, packaging, stamps, stickers, apparel, signage) | `mockups/<area>/` (scenes as JPG + half-size previews; `cutouts/` = transparent PNG products) |
| T-shirts, caps | `apparel/` |
| Hub signboards, roll-up, flyer | `signage/` (a signboard for each hub) |
| A map of the hub network | `maps/hub-network/` (dark and light; square, landscape, portrait; English, Bangla or both) |
| A map that highlights one hub | `maps/hubs/parcelfly-hub-map-<hub>-{dark,light}` |
| A Bangladesh map (website, about pages) | `maps/bangladesh/` (transparent versions replace the website's hand-traced outline) |
| A hub network poster | `maps/poster/parcelfly-hub-network-poster-a3.pdf` |
| A stamp for one hub | `stamps/hub-stamps/` (rubber-stamp vector) and `stamps/digital-inked/parcelfly-hub-stamp-<hub>.png` |
| Social posts for each hub | `social/posts/{square,portrait}/parcelfly-post-hub-<hub>`, `social/stories/parcelfly-story-hub-<hub>` |
| Colour codes for developers | `colors/parcelfly.css`, `colors/tailwind-theme.css`, `colors/parcelfly-tokens.json` |
| Swatches for designers | `colors/parcelfly.ase` (Adobe), `colors/parcelfly.gpl` (GIMP/Inkscape) |
| Backgrounds and textures | `patterns/` (seamless tiles + 1920 x 1080) |
| Logo animations (sign, wordmark, lockups, loaders) | `motion/` (SVG, Lottie, MP4, WebM, WebP, GIF; see Motion below) |
| Email signature | `email/email-signature.html` |
| Website banners, hero backgrounds, cards (client panel home page) | `web/` (banners 1920 x 640 desktop and 1080 x 1080 mobile; SVG, PNG, WebP, JPG) |
| A phone, tablet, laptop or desktop wallpaper | `wallpapers/<audience>/<device>/` (see Wallpapers below) |
| Mugs, paper cups, diary, pens, laptop sticker sheet (to print) | `merch/print/` (see Merchandise below) |

## The logo, in short

- **Final and in production.** The masters here are a faithful vector rebuild of the production artwork (measured to
  under 1 % error), on exact geometry: a 256-unit parcel turned 45 degrees, 26-unit channels, 45 degree edges.
- **Lockups:** stacked (primary), horizontal, symbol, wordmark; with English or Bangla tagline; Bangla lockups
  (পার্সেল ফ্লাই in Mina Bold); sub-brand lockups for Merchant, Rider, Hub and Admin.
- **Colour versions:** `color`, `ondark` (white wings, coloured parcel), `navy`, `black`, `white`, `grey`.
- **Clear space:** one feather height on every side. **Minimum size:** symbol 24 px / 8 mm, horizontal 120 px / 30 mm,
  stacked 72 px / 20 mm. Below 32 px use the app-icon "flight crop" (`icons/app/*/web/favicon.svg`).
- **Never** stretch, rotate, recolour, add shadows or outlines, rearrange the parts, or retype the wordmark.
  The drop shadow on the old production PNG is retired: the logo is flat.

## Hubs and maps

Six hubs across Dhaka and Narayanganj: **Bakshibazar** (বকশীবাজার), **Jatrabari** (যাত্রাবাড়ী), **Keraniganj**
(কেরানীগঞ্জ, in Dhaka District, across the Buriganga), **Mirpur** (মিরপুর), **Rampura** (রামপুরা) and **Narayanganj**
(নারায়ণগঞ্জ). They appear on real maps, hub signboards, hub stamps, the shipping label (tick-box per hub), social posts
and stories, store-front mockups, wallpapers and the A3 poster.

- The maps use real geography: rivers, water and roads from OpenStreetMap, and the Bangladesh outline and rivers from
  Natural Earth. Keep the credit "© OpenStreetMap contributors" (already in every file) wherever a map is used.
- Hub pins mark the neighbourhood (geocoded area centre), not the street address. When the exact addresses are known,
  edit the coordinates in `source/geo/hubs.json` and rebuild.
- To add a hub, add it to `HUBS` in `source/build/fetch_geo.py` and to `source/geo/hubs.json` (key, names, position,
  label side `left`, `right` or `below`, optional `label_dy`), then rebuild: every map, signboard, stamp, post, story,
  label, wallpaper and mockup follows, and headlines count the hubs automatically.
- To refresh the map data from OpenStreetMap: `.venv/bin/python source/build/fetch_geo.py --refresh`.

## Bags

| Bag | Size (mm) | Suggested material and print | Files |
|---|---|---|---|
| Paper shopping bag, navy / white / kraft | 320 x 120 x 410 | 157 gsm art paper, matt lamination, twisted paper handles (kraft: 120 gsm, one colour navy) | `bags/print/paper/*-dieline.pdf` |
| Paper gift bag, sky | 200 x 80 x 250 | as above | `bags/print/paper/parcelfly-paper-bag-sky-200x80x250-dieline.pdf` |
| Canvas tote, natural / navy | 380 x 420, straps 28 mm | 10 oz cotton canvas; 1 colour (natural) or 2 colour (navy) screen print | `bags/print/tote/` |
| Non-woven carry bag, D-cut | 300 x 400 | 80 gsm PP non-woven, 1 colour white; magenta line = die-cut handle | `bags/print/carry-bag/` |
| Non-woven carry bag, loop handle | 350 x 420 | 80 gsm PP non-woven, 2 colour white + cyan, sewn handles | `bags/print/carry-bag/` |
| Rider delivery backpack | 420 x 330 x 420 | 600D polyester, insulated, reflective strip; front, side and top panels | `bags/print/rider-backpack/` |

Dielines: magenta = cut, cyan dashed = fold, 3 mm bleed; panels are back, gusset, front, gusset, glue flap. Materials
are suggestions: confirm stock, inks and handle type with the printer and ask for a physical proof.

## Website artwork

`web/` holds artwork for the client panel landing page; the copy comes from the live client-frontend home page.

- `banners/`: eight promo banners (become a merchant, hub network, cash on delivery, fraud check, track a parcel,
  frozen and fragile care, riders wanted, Bangla), each 1920 x 640 for desktop and 1080 x 1080 for mobile, as SVG,
  PNG, WebP and JPG. The hub network banner uses the real map and keeps the OpenStreetMap credit.
- `hero-backgrounds/`: text-free backgrounds (map, flight, lattice) at 2400 x 1000 and 1080 x 1600 for live HTML
  headlines; the left side (desktop) or top (mobile) stays calm for text.
- `cards/`: six service cards (1200 x 900) and five feature cards (1080 x 1080), light and dark.

## Merchandise

| Item | Size | Files | Notes |
|---|---|---|---|
| 11 oz mug: signature, navy, Bangla | wrap 216 x 89 mm | `merch/print/mugs/` | Sublimation. Each half is designed for the side that shows with the handle left or right. Two-tone mugs (cyan or navy inside and handle) suit the navy and Bangla wraps. |
| 12 oz paper cup: white, navy | 90 / 60 mm x 110 mm | `merch/print/cups/` | The `-fan-*-300dpi.png` is the printable cone shape; `-fan-dieline` is the cut line with the glue edge. |
| A5 hardcover diary: navy, white | 148 x 210 mm, 16 mm spine | `merch/print/diary/` | Case wrap with 15 mm turn-in; ruled inner page with the brand header. Elastic band: cyan (navy cover), navy (white cover). |
| Click pen: navy, white, sky barrel | print 50 x 8 mm | `merch/print/pens/` | Pad print, one or two colours. |
| Laptop sticker sheet | A5 | `merch/print/laptop-stickers/` | Kiss cut; the `-cutline` file is the cut path (magenta). |

## Mockups

`mockups/<area>/` holds realistic renders of every physical item, built from the real print files (change the
artwork, rebuild, and the mockups follow): `bags`, `merch`, `stationery`, `packaging`, `stamps`, `stickers`,
`apparel` and `signage`. Each scene is a full-size JPG plus a half-size `-preview.jpg`; `cutouts/` holds transparent
PNG products (mugs, cups, diaries, pens, laptop, boxes, tape, T-shirts, caps, roll-up) for your own layouts.

## Wallpapers

`wallpapers/<audience>/<device>/parcelfly-wallpaper-<audience>-<design>-<W>x<H>.jpg`; every design on a phone and a
desktop screen in `wallpapers/parcelfly-wallpapers-overview.jpg`.

| Audience | Designs |
|---|---|
| Generic (everyone) | `signature` (navy), `light`, `bangla` (Bangla lockup), `map` (hub network, dark) |
| Merchant | `dark`, `light` (merchant pictograms, MERCHANT pill) |
| Client | `dark`, `light` (delivery route: picked up, at the hub, on the way, delivered) |
| Rider | `dark`, `light` (motion streaks, Bangla tagline, RIDER pill) |
| Hub manager | `map` (light hub map with Bangla names, Hub lockup), `cyan` (hub colourway, HUB MANAGER pill) |
| Staff | `dark`, `light` (TEAM PARCEL FLY, every hub) |
| Admin | `console` (ink, amber admin colourway), `network` (ink hub map, amber network) |

| Device | Sizes (px) |
|---|---|
| Mobile | 1290 x 2796 (iPhone), 1440 x 3200 (Android) |
| Tablet | 2732 x 2732 (iPad: square so it rotates; the art sits in the centre 2048 square), 2560 x 1600 (Android, Windows) |
| Laptop | 2880 x 1800 (16:10), 1920 x 1080 (16:9) |
| Desktop | 3840 x 2160 (4K), 3440 x 1440 (21:9 ultrawide) |

Phone designs keep the lock-screen clock zone (top) and the dock (bottom) calm; desktop lockups sit above the taskbar
and dock. Map wallpapers carry the OpenStreetMap credit under the lockup: keep it when cropping.

## Motion

Nineteen logo animations in `motion/<group>/<name>/`, each in `color` (light backgrounds) and `ondark` (navy)
versions, built from one timeline so every format matches and always ends on the exact master logo.

| Animation | Group | Length | Use it for |
|---|---|---|---|
| `sign-build` | sign | 1.8 s | Intros, app launch |
| `sign-unfold` | sign | 1.8 s | Intros, reveals |
| `sign-fly-in` | sign | 1.4 s | Intros, transitions |
| `sign-draw` | sign | 2.0 s | Slow reveals, presentations |
| `sign-fly-out` | sign | 1.2 s | Outros, 'parcel sent' confirmation |
| `sign-loop` | sign | loop 1.6 s | Idle states, screens |
| `loader-dispatch` | loader | loop 1.1 s | Loading, sending |
| `loader-wings` | loader | loop 1.2 s | Loading |
| `wordmark-wipe` | wordmark | 1.3 s | Titles, lower thirds |
| `wordmark-wipe-bn` | wordmark | 1.3 s | Bangla titles |
| `wordmark-rise` | wordmark | 1.2 s | Titles |
| `horizontal-build` | combined | 2.0 s | Video intros, web headers |
| `horizontal-build-bn` | combined | 2.0 s | Bangla video intros |
| `horizontal-fly-in` | combined | 1.7 s | Video intros |
| `horizontal-tagline-build` | combined | 2.4 s | Ads, end cards |
| `stacked-build` | combined | 2.6 s | Social video, splash screens |
| `stacked-build-bn` | combined | 2.6 s | Bangla social video |
| `stacked-drop` | combined | 2.4 s | Delivery-themed intros |
| `horizontal-outro` | combined | 1.4 s | Video end cards |

| Format | Where |
|---|---|
| `.svg` | Websites: CSS animation, transparent, stops automatically for users who prefer reduced motion |
| `.json` | Lottie for apps and web: `lottie-react-native` in the Expo rider app, `lottie-web` on the website |
| `.mp4` | Social media, presentations, video editing (on white or navy) |
| `.webm` | Video with transparency (web overlays, editors that support VP9 alpha) |
| `.webp` | Animated with transparency (chat apps, stickers, web) |
| `.gif` | Email and chat where nothing else plays |

Expo example (rider app loading state):

```tsx
import LottieView from "lottie-react-native"

<LottieView source={require("./assets/motion/parcelfly-loader-dispatch-color.json")} autoPlay loop style={{ width: 96, height: 96 }} />
```

Web example: `<img src="/motion/parcelfly-horizontal-build-color.svg" alt="Parcel Fly">`.

## Colours

| | Name | HEX | CMYK (FOGRA39) | Pantone (nearest) |
|---|---|---|---|---|
| Primary | Fly Navy | `#000080` | 98 93 0 11 | 2738 C |
| | Cobalt | `#00318D` | 99 84 0 8 | 287 C |
| | Sky Blue | `#0077C9` | 84 47 0 0 | 3005 C |
| Signature | Parcel Cyan | `#00B5D8` | 71 2 12 2 | 306 C |
| | Aqua | `#00D8DB` | 58 0 25 0 | 319 C |
| | Mint | `#00EAD3` | 50 0 29 0 | 3252 C |

Neutrals, status colours, uncoated CMYK, OKLCH and contrast ratios: `colors/README.md`.

## Typography

- **Montserrat** (headlines ExtraBold, body Medium, labels SemiBold caps) for English.
- **Mina Bold** for the Bangla wordmark, Bangla taglines and Bangla display; **Noto Sans Bengali** for Bangla body text.
- **Geist Mono** for tracking numbers and codes.
- **Nasalization** is the logo wordmark only. It is used as outlined, fixed artwork under the Typodermic desktop
  licence; the font itself is not in this kit and must never be committed, uploaded, embedded in apps or websites, or
  used for text. The open-licence fonts are in `source/fonts/` with their licences.

## Putting the icons into the apps

Nothing in the app repositories has been changed. When you are ready:

| App | Copy from | Notes |
|---|---|---|
| `client-frontend` (Merchant PWA) | `icons/app/merchant/web/*` to `public/icons/` | keep `theme_color` `#000080`; maskable icons included |
| `manager-frontend` (Hub) | `icons/app/hub/web/*` | theme colour `#00B5D8` |
| `admin-frontend` (Admin) | `icons/app/admin/web/*` | theme colour `#0B1133` |
| `rider-mobile` (Expo) | `icons/app/rider/expo/*` to `assets/images/` | see `app.json-snippet.json`: white adaptive background, monochrome icon, dark splash |

`colors/globals-oklch-snippet.css` replaces the approximate `--brand-*` tokens in the web apps' `globals.css` with the
exact logo colours.

## Rebuilding

Everything except the outlined wordmark is generated by code from `source/`:

```bash
uv venv .venv && uv pip install --python .venv/bin/python -r source/build/requirements.txt
.venv/bin/python source/build/build_all.py
```

The build also runs the `logo-design` skill's audit, test sheet and presentation board (`presentation/`; open the HTML
files in a browser). `source/build/extract_wordmark.py` re-outlines the wordmark from a locally licensed Nasalization
file if it ever needs to change.

## Before large print runs

- CMYK values were converted with the FOGRA39 coated (and FOGRA29 uncoated) ICC profiles; PDFs are RGB. Ask the
  printer for a proof. Pantone values are nearest matches: check them in a physical Pantone guide.
- A trademark search for the name and logo is recommended before major spending on signage or packaging.

Contact: parcelflybd@gmail.com · +880 1973-582751 · parcelflybd.com
