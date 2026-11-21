"""Parcel Fly pictograms: 48-unit grid, 3.5 stroke, round caps and joins, 45/90 deg geometry.

Each icon is a list of SVG path strings drawn as strokes ('s:' prefix = filled shape instead)."""
import math

from . import text as T
from .text import fmt

GRID = 48.0
STROKE = 3.5


def _snowflake():
    c, out = (24.0, 24.0), []
    for a in (90, 30, -30):
        v = (math.cos(math.radians(a)), -math.sin(math.radians(a)))
        out.append(f"M{fmt(c[0] - v[0] * 18)} {fmt(c[1] - v[1] * 18)}L{fmt(c[0] + v[0] * 18)} {fmt(c[1] + v[1] * 18)}")
    for a in range(0, 360, 60):
        r = math.radians(a + 90)
        v = (math.cos(r), -math.sin(r))
        p = (c[0] + v[0] * 11.5, c[1] + v[1] * 11.5)
        for s in (1, -1):
            rr = r + s * math.radians(45)
            w = (math.cos(rr), -math.sin(rr))
            out.append(f"M{fmt(p[0])} {fmt(p[1])}L{fmt(p[0] + w[0] * 6)} {fmt(p[1] + w[1] * 6)}")
    return out


def _star():
    pts = []
    for i in range(10):
        r = 18 if i % 2 == 0 else 7.6
        a = math.radians(-90 + i * 36)
        pts.append((24 + r * math.cos(a), 25.5 + r * math.sin(a)))
    return ["M" + "L".join(f"{fmt(x)} {fmt(y)}" for x, y in pts) + "Z"]


ICONS = {
    "parcel": ["M8 19h32v19a2.5 2.5 0 0 1-2.5 2.5h-27A2.5 2.5 0 0 1 8 38z", "M6 11.5h36v7.5H6z",
               "M24 11.5V27", "M20 27h8"],
    "track": ["M24 43C24 43 10 30.5 10 20a14 14 0 0 1 28 0c0 10.5-14 23-14 23z", "M24 13.5l6.5 6.5-6.5 6.5-6.5-6.5z"],
    "pricing": ["M6 24l9-12h25a2 2 0 0 1 2 2v20a2 2 0 0 1-2 2H15z", "s:M15 21.5a2.5 2.5 0 1 1 0 5a2.5 2.5 0 1 1 0-5z",
                "t:৳"],
    "coverage": ["M6 12l11-4 14 4 11-4v28l-11 4-14-4-11 4z", "M17 8v28", "M31 12v28"],
    "network": ["M12 34L24 14L36 32Z", "s:M12 29.5a4.5 4.5 0 1 1 0 9a4.5 4.5 0 1 1 0-9z",
                "s:M24 9.5a4.5 4.5 0 1 1 0 9a4.5 4.5 0 1 1 0-9z", "s:M36 27.5a4.5 4.5 0 1 1 0 9a4.5 4.5 0 1 1 0-9z"],
    "merchant": ["M8 18l2.5-10h27L40 18", "M8 18a4 4 0 0 0 8 0a4 4 0 0 0 8 0a4 4 0 0 0 8 0a4 4 0 0 0 8 0",
                 "M10.5 22v18h27V22", "M20 40v-9h8v9"],
    "rider": ["M12 35a5 5 0 1 0 0.01 0z", "M37 35a5 5 0 1 0 0.01 0z", "M17 35h8l6-9h4", "M35 26l2 9",
              "M35 26l-3-11", "M29 15h6", "M6 16h12v10H6z"],
    "cash": ["M6 14h36v20H6z", "M24 19.5a4.5 4.5 0 1 1 0 9a4.5 4.5 0 1 1 0-9z", "M11 19v0", "M37 29v0"],
    "fast": ["M28 11a13 13 0 1 1 0 26a13 13 0 1 1 0-26z", "M28 17v7l5 3", "M4 18h7", "M2 24h9", "M4 30h7"],
    "phone": ["M18 6h12a4 4 0 0 1 4 4v28a4 4 0 0 1-4 4H18a4 4 0 0 1-4-4V10a4 4 0 0 1 4-4z", "M21 36h6"],
    "faq": ["M12 8h24a6 6 0 0 1 6 6v14a6 6 0 0 1-6 6H22l-8 7v-7h-2a6 6 0 0 1-6-6V14a6 6 0 0 1 6-6z", "t:?"],
    "reviews": _star(),
    "offers": ["M8 20h32v19a2 2 0 0 1-2 2H10a2 2 0 0 1-2-2z", "M6 13h36v7H6z", "M24 13v28",
               "M24 13c-3-8-13-6-8 0", "M24 13c3-8 13-6 8 0"],
    "secure": ["M24 6l15 5v11c0 10-7 17-15 20c-8-3-15-10-15-20V11z", "M17 24l5 5l9-10"],
    "frozen": _snowflake(),
    "fragile": ["M15 7h18v9c0 6-4 10-9 10s-9-4-9-10z", "M24 26v12", "M17 41h14", "M21 7l3 5-2.5 3 3.5 4"],
    "this-side-up": ["M16 40V10", "M10 16l6-6 6 6", "M32 40V10", "M26 16l6-6 6 6", "M8 43h32"],
    "keep-dry": ["M6 25a18 16 0 0 1 36 0z", "M24 25v12a4 4 0 0 1-8 0", "M24 6v3"],
    "pickup": ["M10 17h26", "M30 11l6 6-6 6", "M38 31H12", "M18 25l-6 6 6 6"],
    "scan": ["M8 16v-6a2 2 0 0 1 2-2h6", "M32 8h6a2 2 0 0 1 2 2v6", "M40 32v6a2 2 0 0 1-2 2h-6",
             "M16 40h-6a2 2 0 0 1-2-2v-6", "s:M15 15h7v7h-7z", "s:M26 15h7v7h-7z", "s:M15 26h7v7h-7z",
             "s:M27 27h2.5v2.5H27z", "s:M30.5 30.5H33V33h-2.5z"],
    "thanks": ["M24 40C10 30 6 23 6 17a8.5 8.5 0 0 1 18-4a8.5 8.5 0 0 1 18 4c0 6-4 13-18 23z"],
    "info": ["M24 6a18 18 0 1 1 0 36a18 18 0 1 1 0-36z", "M24 22v11", "s:M24 13.2a2.3 2.3 0 1 1 0 4.6a2.3 2.3 0 1 1 0-4.6z"],
    "user": ["M24 9a7 7 0 1 1 0 14a7 7 0 1 1 0-14z", "M10 40c0-9 6-14 14-14s14 5 14 14"],
    "mail": ["M8 12h32a2 2 0 0 1 2 2v20a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V14a2 2 0 0 1 2-2z", "M7 14l17 13 17-13"],
    "web": ["M24 6a18 18 0 1 1 0 36a18 18 0 1 1 0-36z", "M6 24h36",
            "M24 6c-5.5 5-8.5 11-8.5 18s3 13 8.5 18c5.5-5 8.5-11 8.5-18s-3-13-8.5-18z"],
    "calendar": ["M10 10h28a3 3 0 0 1 3 3v25a3 3 0 0 1-3 3H10a3 3 0 0 1-3-3V13a3 3 0 0 1 3-3z", "M7 18h34",
                 "M16 6v8", "M32 6v8", "s:M14 24h5v5h-5z"],
}

LABELS = {
    "parcel": "Parcel", "track": "Track", "pricing": "Pricing", "coverage": "Coverage", "network": "Network",
    "merchant": "Merchant", "rider": "Rider", "cash": "Cash on delivery", "fast": "Fast delivery",
    "phone": "Contact", "faq": "FAQ", "reviews": "Reviews", "offers": "Offers", "secure": "Secure",
    "frozen": "Keep frozen", "fragile": "Fragile", "this-side-up": "This side up", "keep-dry": "Keep dry",
    "pickup": "Pickup & drop", "scan": "Scan", "thanks": "Thank you", "info": "About", "user": "Account",
    "calendar": "Schedule", "mail": "Email", "web": "Website",
}


def icon(name, x, y, size, colour, stroke=STROKE):
    """Place an icon with its 48-unit grid scaled into a size x size box at (x, y)."""
    k = size / GRID
    parts = []
    for p in ICONS[name]:
        if p.startswith("s:"):
            parts.append(f'<path d="{p[2:]}" fill="{colour}" stroke="none"/>')
        elif p.startswith("t:"):
            ch = p[2:]
            key = "noto-bengali" if ch == "৳" else "montserrat"
            cx = 28.5 if ch == "৳" else 24
            base = 30.5 if ch == "৳" else 27
            parts.append(T.text(ch, key, 20 if ch == "৳" else 19, cx, base + 1.5, colour, "middle", 800,
                                extra=' stroke="none"'))
        else:
            parts.append(f'<path d="{p}"/>')
    return (f'<g transform="translate({fmt(x)} {fmt(y)}) scale({k:.6f})" fill="none" stroke="{colour}" '
            f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">{"".join(parts)}</g>')
