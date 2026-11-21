"""Brand facts: palette, contacts, taglines and sub-brands. Single source of truth for the whole kit."""

NAME = "Parcel Fly"
NAME_BN = "পার্সেল ফ্লাই"
TAGLINE = "Always, Everywhere"
TAGLINE_BN = "সবসময়, সবখানে"
EST = "EST. 2025"
EST_YEAR = 2025
CITY = "Dhaka"

CONTACT = {
    "phone": "01973-582751",
    "phone_intl": "+880 1973-582751",
    "phone_tel": "+8801973582751",
    "email": "parcelflybd@gmail.com",
    "web": "parcelflybd.com",
    "url": "https://parcelflybd.com",
    "facebook": "facebook.com/parcelflybd",
    "handle": "@parcelflybd",
    "address": "61/2 Nazimuddin Road, Bongshal, Dhaka 1000, Bangladesh",
    "address_lines": ["61/2 Nazimuddin Road, Bongshal", "Dhaka 1000, Bangladesh"],
}

# ---------------------------------------------------------------- palette
# The six logo colours were sampled from the production artwork (flat fills, exact values).
# CMYK: sRGB -> FOGRA39 (ISO Coated v2) and FOGRA29 (uncoated), relative colorimetric + black point
# compensation. Pantone values are nearest visual matches. Proof both before a print run.
PALETTE = {
    "navy":  {"name": "Fly Navy",    "hex": "#000080", "cmyk": (98, 93, 0, 11), "cmyk_uncoated": (95, 100, 0, 10), "pantone": "2738 C",
              "role": "Primary. Wordmark, text, dark backgrounds, one-colour logo."},
    "cobalt": {"name": "Cobalt",     "hex": "#00318D", "cmyk": (99, 84, 0, 8), "cmyk_uncoated": (96, 93, 0, 9), "pantone": "287 C",
               "role": "Middle feather. Secondary dark, headings on light backgrounds."},
    "sky":   {"name": "Sky Blue",    "hex": "#0077C9", "cmyk": (84, 47, 0, 0), "cmyk_uncoated": (87, 47, 0, 1), "pantone": "3005 C",
              "role": "Top feather. Links, highlights, taglines, secondary actions."},
    "cyan":  {"name": "Parcel Cyan", "hex": "#00B5D8", "cmyk": (71, 2, 12, 2), "cmyk_uncoated": (71, 4, 10, 1), "pantone": "306 C",
              "role": "The parcel (diamond). Signature accent, on-dark highlights."},
    "aqua":  {"name": "Aqua",        "hex": "#00D8DB", "cmyk": (58, 0, 25, 0), "cmyk_uncoated": (54, 0, 20, 0), "pantone": "319 C",
              "role": "Lower facet. Accent, illustrations, data."},
    "mint":  {"name": "Mint",        "hex": "#00EAD3", "cmyk": (50, 0, 29, 0), "cmyk_uncoated": (45, 0, 24, 0), "pantone": "3252 C",
              "role": "Upper facet. Accent, the brightest step of the flight gradient."},
}

NEUTRALS = {
    "ink":    {"name": "Ink",    "hex": "#0B1133", "cmyk": (93, 71, 3, 82), "cmyk_uncoated": (91, 56, 20, 78), "role": "Body text, deepest backgrounds."},
    "slate":  {"name": "Slate",  "hex": "#55607A", "cmyk": (65, 50, 26, 31), "cmyk_uncoated": (62, 42, 9, 40), "role": "Secondary text, captions, icons."},
    "mist":   {"name": "Mist",   "hex": "#DCE7F2", "cmyk": (15, 7, 6, 0), "cmyk_uncoated": (14, 7, 5, 0), "role": "Borders, dividers, quiet fills."},
    "cloud":  {"name": "Cloud",  "hex": "#F3F8FC", "cmyk": (5, 3, 3, 0), "cmyk_uncoated": (4, 2, 2, 0), "role": "Page and card backgrounds."},
    "white":  {"name": "White",  "hex": "#FFFFFF", "cmyk": (0, 0, 0, 0), "cmyk_uncoated": (0, 0, 0, 0), "role": "Backgrounds, reversed logo."},
}

# Status colours are functional (stamps, stickers, UI states), never brand decoration.
STATUS = {
    "success": {"name": "Delivered Green", "hex": "#0E9F6E", "cmyk": (78, 3, 68, 8), "cmyk_uncoated": (80, 0, 65, 5), "role": "Delivered, paid, verified."},
    "warning": {"name": "Signal Amber",    "hex": "#F5A100", "cmyk": (2, 41, 94, 4), "cmyk_uncoated": (0, 33, 97, 4), "role": "Handle with care, pending, COD."},
    "danger":  {"name": "Alert Red",       "hex": "#E0303A", "cmyk": (0, 92, 74, 5), "cmyk_uncoated": (0, 95, 81, 3), "role": "Fragile, returned, cancelled."},
}


def hex_of(key: str) -> str:
    for table in (PALETTE, NEUTRALS, STATUS):
        if key in table:
            return table[key]["hex"]
    if key.startswith("#"):
        return key
    raise KeyError(key)


NAVY, COBALT, SKY, CYAN, AQUA, MINT = (PALETTE[k]["hex"] for k in ("navy", "cobalt", "sky", "cyan", "aqua", "mint"))
INK, SLATE, MIST, CLOUD, WHITE = (NEUTRALS[k]["hex"] for k in ("ink", "slate", "mist", "cloud", "white"))
GREEN, AMBER, RED = (STATUS[k]["hex"] for k in ("success", "warning", "danger"))

# The flight gradient: the logo's colours in the order the eye reads the mark (tail -> nose).
FLIGHT = [NAVY, COBALT, SKY, CYAN, MINT]

# ---------------------------------------------------------------- sub-brands
# Icon schemes: tile colour + symbol colourway (registered in symbol.COLOURWAYS by name).
# The brand (main) icon and the Merchant app share the navy scheme: the merchant PWA is the public face.
ICON_SCHEMES = {
    "brand":    {"tile": NAVY, "way": "ondark", "theme": NAVY},
    "merchant": {"tile": NAVY, "way": "ondark", "theme": NAVY},
    "rider":    {"tile": WHITE, "way": "color", "theme": NAVY},
    "hub":      {"tile": CYAN, "way": "hub", "theme": CYAN},
    "admin":    {"tile": INK, "way": "admin", "theme": INK},
}

SUBBRANDS = {
    "merchant": {"label": "Merchant", "label_bn": "মার্চেন্ট", "app": "client-frontend",
                 "desc": "Merchant web app (PWA): create, track and settle deliveries."},
    "rider":    {"label": "Rider", "label_bn": "রাইডার", "app": "rider-mobile",
                 "desc": "Rider mobile app (Android and iOS, Expo)."},
    "hub":      {"label": "Hub", "label_bn": "হাব", "app": "manager-frontend",
                 "desc": "Hub manager web app."},
    "admin":    {"label": "Admin", "label_bn": "অ্যাডমিন", "app": "admin-frontend",
                 "desc": "Administration web app."},
}
