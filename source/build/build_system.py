"""Brand system resources: patterns, colour tokens/swatches, email signature, logo animation."""
import json
import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pfbrand import ROOT, layout as LY, scenes as SC, symbol as S, text as T  # noqa: E402
from pfbrand import logo as L  # noqa: E402
from pfbrand.brand import (CLOUD, CONTACT, COBALT, CYAN, MINT, MIST, NAVY, NEUTRALS, PALETTE, SKY, STATUS,  # noqa: E402
                           TAGLINE, TAGLINE_BN, WHITE, INK, SLATE, AQUA)
from pfbrand.svg import Doc, png_image, render_png  # noqa: E402
from pfbrand.text import fmt  # noqa: E402
from pfbrand.export import fragment_doc  # noqa: E402


# ================================================================== patterns

def pattern_tile(kind, fg, bg, op=1.0):
    """Seamless tile (SVG user units). Returns (Doc, tile_w, tile_h)."""
    if kind == "lattice":
        c = 64.0
        d = Doc(c, c, bg=bg)
        hd = c * 0.16
        g = (LY.parcel(c / 2, c / 2, hd, fg, op) + "".join(LY.parcel(x, y, hd, fg, op) for x in (0, c) for y in (0, c)))
        d.add(g)
        return d
    if kind == "chevrons":
        w, h = 120.0, 80.0
        d = Doc(w, h, bg=bg)
        ch = 26.0
        cw = LY.chevron_width(ch)
        for (x, y) in [(10, 8), (70, 48), (70 - w, 48), (10 + w, 8)]:
            d.add(LY.chevron(x, y, ch, (fg, fg), op))
        _ = cw
        return d
    if kind == "monogram":
        sw = 200.0
        sh = S.HEIGHT * sw / S.WIDTH
        w, h = sw * 1.5, sh * 2.6
        d = Doc(w, h, bg=bg)
        for (x, y) in [(sw * 0.25, sh * 0.3), (sw * 0.25 + w / 2, sh * 1.6), (sw * 0.25 - w / 2, sh * 1.6)]:
            d.add(f'<g opacity="{op}">{LY.symbol_at(fg, x + sw / 2, y + sh / 2, sw)}</g>')
        return d
    if kind == "wings":
        w, h = 240.0, 120.0
        d = Doc(w, h, bg=bg)
        sh = 100.0
        for x, y in [(-20, 10), (-20 + w, 10)]:
            d.add(LY.speed_lines(x, y, sh, 200, (fg, fg, fg), opacity=op))
        return d
    raise KeyError(kind)


PATTERNS = {
    "lattice": [("mist-on-cloud", MIST, CLOUD, 1.0), ("cobalt-on-navy", COBALT, NAVY, 1.0),
                ("white-on-sky", WHITE, SKY, 0.22), ("cyan-on-white", CYAN, WHITE, 0.35)],
    "chevrons": [("mist-on-white", MIST, WHITE, 1.0), ("cobalt-on-navy", COBALT, NAVY, 1.0), ("white-on-cyan", WHITE, CYAN, 0.3)],
    "monogram": [("cobalt-on-navy", COBALT, NAVY, 1.0), ("mist-on-white", MIST, WHITE, 1.0), ("white-on-sky", "white", SKY, 0.18)],
    "wings": [("cobalt-on-navy", COBALT, NAVY, 1.0), ("mist-on-white", MIST, WHITE, 1.0)],
}


def build_patterns():
    out = ROOT / "patterns"
    n = 0
    for kind, ways in PATTERNS.items():
        for name, fg, bg, op in ways:
            tile = pattern_tile(kind, fg, bg, op)
            base = out / kind / f"parcelfly-pattern-{kind}-{name}"
            tile.title = f"Parcel Fly pattern {kind} ({name}), seamless tile"
            tile.save(base.with_name(base.name + "-tile.svg"), png=[int(tile.w * 4)])
            # full swatch 1920 x 1080 built from the tile
            inner = tile.svg().split(">", 1)[1].rsplit("</svg>", 1)[0]
            inner = inner.split("</title>", 1)[-1]
            pid = f"p{kind}{name}".replace("-", "")
            sw = Doc(1920, 1080, title=f"Parcel Fly pattern {kind} ({name})")
            sw.defs_add(f'<pattern id="{pid}" width="{fmt(tile.w)}" height="{fmt(tile.h)}" patternUnits="userSpaceOnUse">'
                        f'{inner}</pattern>')
            sw.rect(0, 0, 1920, 1080, f"url(#{pid})")
            sw.save(base.with_name(base.name + "-1920x1080.svg"), png=[1920])
            n += 4
    return n


# ================================================================== colour tokens

def srgb_to_oklch(hx):
    r, g, b = (int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    l = 0.4122214708 * lin[0] + 0.5363325363 * lin[1] + 0.0514459929 * lin[2]
    m = 0.2119034982 * lin[0] + 0.6806995451 * lin[1] + 0.1073969566 * lin[2]
    s = 0.0883024619 * lin[0] + 0.2817188376 * lin[1] + 0.6299787005 * lin[2]
    l_, m_, s_ = (v ** (1 / 3) for v in (l, m, s))
    L_ = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b2 = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    C = math.hypot(a, b2)
    h = math.degrees(math.atan2(b2, a)) % 360
    return L_, C, h


def rel_lum(hx):
    vals = []
    for i in (1, 3, 5):
        c = int(hx[i:i + 2], 16) / 255
        vals.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]


def contrast(a, b):
    la, lb = sorted((rel_lum(a), rel_lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def all_colours():
    out = []
    for group, table in [("brand", PALETTE), ("neutral", NEUTRALS), ("status", STATUS)]:
        for key, v in table.items():
            out.append((group, key, v))
    return out


def write_ase(path, colours):
    blocks = b""
    count = 0
    for group, key, v in colours:
        name = (v["name"] + "\0").encode("utf-16-be")
        hx = v["hex"]
        rgb = [int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        body = struct.pack(">H", len(name) // 2) + name + b"RGB " + struct.pack(">fff", *rgb) + struct.pack(">H", 2)
        blocks += struct.pack(">HI", 0x0001, len(body)) + body
        count += 1
    path.write_bytes(b"ASEF" + struct.pack(">HHI", 1, 0, count) + blocks)


def build_tokens():
    out = ROOT / "colors"
    out.mkdir(parents=True, exist_ok=True)
    cols = all_colours()
    # W3C design tokens
    tok = {"color": {}}
    for group, key, v in cols:
        tok["color"].setdefault(group, {})[key] = {"$type": "color", "$value": v["hex"],
                                                  "$description": f"{v['name']}. {v['role']}"}
    tok["color"]["gradient"] = {"flight": {"$type": "gradient", "$value": [
        {"color": c, "position": p} for p, c in zip([0, 0.3, 0.58, 0.82, 1.0], [NAVY, COBALT, SKY, CYAN, MINT])]}}
    (out / "parcelfly-tokens.json").write_text(json.dumps(tok, indent=2), encoding="utf-8")
    # CSS variables (+ semantic aliases)
    lines = [":root {", "  /* Parcel Fly brand colours (source: brand-assets/colors) */"]
    for group, key, v in cols:
        lines.append(f"  --pf-{key}: {v['hex']};  /* {v['name']} */")
    lines += ["", "  /* semantic */", "  --pf-primary: var(--pf-navy);", "  --pf-primary-foreground: var(--pf-white);",
              "  --pf-accent: var(--pf-cyan);", "  --pf-link: var(--pf-sky);", "  --pf-text: var(--pf-ink);",
              "  --pf-text-muted: var(--pf-slate);", "  --pf-border: var(--pf-mist);", "  --pf-surface: var(--pf-cloud);",
              f"  --pf-gradient-flight: linear-gradient(90deg, {NAVY} 0%, {COBALT} 30%, {SKY} 58%, {CYAN} 82%, {MINT} 100%);",
              "}", ""]
    (out / "parcelfly.css").write_text("\n".join(lines), encoding="utf-8")
    # Tailwind v4 theme
    tw = ["/* Tailwind CSS v4: paste into your global CSS after @import \"tailwindcss\"; */", "@theme {"]
    for group, key, v in cols:
        tw.append(f"  --color-pf-{key}: {v['hex']};")
    tw += ['  --font-display: "Montserrat", ui-sans-serif, system-ui, sans-serif;',
           '  --font-bangla: "Noto Sans Bengali", "Mina", ui-sans-serif, sans-serif;', "}", ""]
    (out / "tailwind-theme.css").write_text("\n".join(tw), encoding="utf-8")
    # OKLCH snippet matching client-frontend/manager-frontend globals.css token names
    ok = ["/* Drop-in replacement for the brand tokens in client-frontend / manager-frontend src/app/globals.css.",
          "   Values are the exact logo colours expressed in OKLCH. */", ":root {"]
    for name, hx in [("brand-navy", NAVY), ("brand-blue", SKY), ("brand-cyan", CYAN), ("brand-cobalt", COBALT),
                     ("brand-mint", MINT), ("brand-aqua", AQUA)]:
        L_, C, h = srgb_to_oklch(hx)
        ok.append(f"  --{name}: oklch({L_:.3f} {C:.3f} {h:.1f});  /* {hx} */")
    ok.append("  --brand-navy-foreground: oklch(0.985 0.004 228.8);")
    ok += ["}", ""]
    (out / "globals-oklch-snippet.css").write_text("\n".join(ok), encoding="utf-8")
    # SCSS
    (out / "parcelfly.scss").write_text("\n".join(f"${'pf-' + key}: {v['hex']};" for g, key, v in cols) + "\n", encoding="utf-8")
    # GIMP / Inkscape palette
    gpl = ["GIMP Palette", "Name: Parcel Fly", "Columns: 6", "#"]
    for g, key, v in cols:
        hx = v["hex"]
        r, gg, b = (int(hx[i:i + 2], 16) for i in (1, 3, 5))
        gpl.append(f"{r:3d} {gg:3d} {b:3d}\t{v['name']}")
    (out / "parcelfly.gpl").write_text("\n".join(gpl) + "\n", encoding="utf-8")
    write_ase(out / "parcelfly.ase", cols)
    # palette table (markdown) with contrast
    md = ["# Parcel Fly colour palette", "",
          "CMYK: FOGRA39 coated (ISO Coated v2) / FOGRA29 uncoated, relative colorimetric with black point compensation.",
          "Pantone values are the nearest visual matches: check them against a physical Pantone guide before printing.", "",
          "| Group | Name | HEX | RGB | OKLCH | CMYK coated | CMYK uncoated | Pantone | On white | On navy | Use |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for g, key, v in cols:
        hx = v["hex"]
        r, gg, b = (int(hx[i:i + 2], 16) for i in (1, 3, 5))
        L_, C, h = srgb_to_oklch(hx)
        cm = v.get("cmyk", (0, 0, 0, 0))
        cu = v.get("cmyk_uncoated", (0, 0, 0, 0))
        md.append(f"| {g} | {v['name']} | `{hx}` | {r} {gg} {b} | {L_:.3f} {C:.3f} {h:.1f} | "
                  f"{cm[0]} {cm[1]} {cm[2]} {cm[3]} | {cu[0]} {cu[1]} {cu[2]} {cu[3]} | {v.get('pantone', '')} | "
                  f"{contrast(hx, '#FFFFFF'):.1f}:1 | {contrast(hx, NAVY):.1f}:1 | {v['role']} |")
    md += ["", "Contrast is the WCAG 2 ratio: 4.5:1 or more for body text, 3:1 or more for large text, icons and the logo.", ""]
    (out / "README.md").write_text("\n".join(md), encoding="utf-8")
    # swatch card
    d = Doc(1800, 1000, bg=WHITE, title="Parcel Fly colour palette")
    d.add(T.text("Parcel Fly colours", "montserrat", 46, 70, 100, NAVY, "start", 800))
    x, y = 70, 150
    for i, (g, key, v) in enumerate([c for c in cols if c[0] == "brand"]):
        cx = x + i * 280
        d.rect(cx, y, 250, 330, v["hex"], rx=18)
        light = rel_lum(v["hex"]) > 0.35
        tc = NAVY if light else WHITE
        d.add(T.text(v["name"], "montserrat", 26, cx + 22, y + 250, tc, "start", 800))
        d.add(T.text(v["hex"], "geist-mono", 22, cx + 22, y + 290, tc, "start", 600))
        cm = v["cmyk"]
        d.add(T.text(f"C{cm[0]} M{cm[1]} Y{cm[2]} K{cm[3]}", "geist-mono", 18, cx + 22, y + 318, tc, "start", 500))
    y2 = 540
    for i, (g, key, v) in enumerate([c for c in cols if c[0] != "brand"]):
        cx = x + i * 205
        d.rect(cx, y2, 185, 185, v["hex"], rx=14, extra=f' stroke="{MIST}" stroke-width="2"')
        light = rel_lum(v["hex"]) > 0.35
        tc = NAVY if light else WHITE
        d.add(T.text(v["name"], "montserrat", 19, cx + 16, y2 + 140, tc, "start", 800))
        d.add(T.text(v["hex"], "geist-mono", 17, cx + 16, y2 + 166, tc, "start", 600))
    gid = "fl"
    d.defs_add(LY.flight_gradient(gid))
    d.rect(70, 790, 1660, 80, f"url(#{gid})", rx=14)
    d.add(T.text("Flight gradient: Fly Navy > Cobalt > Sky Blue > Parcel Cyan > Mint (backgrounds only, never the logo)",
                 "montserrat", 22, 70, 920, SLATE, "start", 600))
    d.save(out / "parcelfly-palette.svg", png=[1800], pdf=True)
    return 12


# ================================================================== email signature

def build_email():
    out = ROOT / "email"
    out.mkdir(parents=True, exist_ok=True)
    frag, bb = L.horizontal("color")
    d = fragment_doc(frag, bb, "Parcel Fly")
    render_png(d.svg(), out / "signature-logo.png", 400, d.w, d.h)
    sig = f"""<!-- Parcel Fly email signature. Host signature-logo.png at a public URL (for example
     https://{CONTACT['web']}/email/signature-logo.png) and replace the src below. Name and title are placeholders. -->
<table cellpadding="0" cellspacing="0" border="0" style="font-family:Montserrat,Arial,Helvetica,sans-serif;color:#0B1133;">
  <tr>
    <td style="padding:0 18px 0 0;border-right:3px solid #00B5D8;vertical-align:middle;">
      <img src="signature-logo.png" width="200" alt="Parcel Fly" style="display:block;border:0;">
    </td>
    <td style="padding:0 0 0 18px;vertical-align:middle;font-size:13px;line-height:20px;">
      <div style="font-size:16px;font-weight:800;color:#000080;">Full Name</div>
      <div style="font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#0077C9;">Designation</div>
      <div style="margin-top:6px;">{CONTACT['phone_intl']} &nbsp;&middot;&nbsp;
        <a href="mailto:{CONTACT['email']}" style="color:#0B1133;text-decoration:none;">{CONTACT['email']}</a></div>
      <div><a href="{CONTACT['url']}" style="color:#0077C9;text-decoration:none;font-weight:700;">{CONTACT['web']}</a>
        &nbsp;&middot;&nbsp; {TAGLINE}</div>
    </td>
  </tr>
</table>
"""
    (out / "email-signature.html").write_text(sig, encoding="utf-8")
    return 2


def main():
    n = build_patterns() + build_tokens() + build_email()   # logo motion: build_motion.py
    print(f"system: ~{n} files")


if __name__ == "__main__":
    main()
