"""Product mockups rendered from the real artwork: a pinhole camera, perspective-warped faces, lighting, textures,
handles and soft shadows (PIL + cairosvg). Used for bags and packaging scenes."""
import io
import math

import cairosvg
import numpy as np
from PIL import Image, ImageChops, ImageFilter

from .svg import png_image
from .text import fmt


# ------------------------------------------------------------------ raster helpers

def svg_img(body, w, h):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{body}</svg>')
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=w, output_height=h))).convert("RGBA")


def doc_img(doc, px_w):
    return png_image(doc.svg(), px_w, doc.w, doc.h)


def poly_mask(pts, w, h):
    d = "M" + "L".join(f"{fmt(x)} {fmt(y)}" for x, y in pts) + "Z"
    return svg_img(f'<path d="{d}" fill="#fff"/>', w, h).getchannel("A")


def coeffs(dst, src):
    """Perspective coefficients mapping output (dst) points to input (src) points for Image.transform."""
    A, B = [], []
    for (x, y), (X, Y) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -X * x, -X * y])
        A.append([0, 0, 0, x, y, 1, -Y * x, -Y * y])
        B.extend([X, Y])
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def warp(img, quad, size):
    w, h = img.size
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    return img.transform(size, Image.PERSPECTIVE, coeffs(quad, src), Image.BICUBIC)


def noise(w, h, seed=1, scale=1.0, fibres=False, weave=False):
    """Grayscale texture 0..1 (mean ~0.5)."""
    rng = np.random.default_rng(seed)
    n = rng.random((h, w))
    img = Image.fromarray((n * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6 * scale))
    a = np.asarray(img, float) / 255
    if fibres:
        low = Image.fromarray((rng.random((max(2, h // 45), max(2, w // 45))) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        a = a * 0.8 + np.asarray(low, float) / 255 * 0.2
        streak = Image.fromarray((rng.random((h, max(2, w // 3))) * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)
        a = a * 0.75 + np.asarray(streak, float) / 255 * 0.25
        specks = rng.random((h, w)) > 0.9985
        a = np.where(specks, a - 0.35, a)
    if weave:
        yy, xx = np.mgrid[0:h, 0:w]
        period = max(3, int(4 * scale))
        a = a * 0.45 + 0.55 * (0.5 + 0.25 * np.sin(xx * 2 * math.pi / period) * np.sin(yy * 2 * math.pi / period))
    a = (a - a.mean()) / (a.std() + 1e-6) * 0.18 + 0.5
    return np.clip(a, 0, 1)


def textured(img, tex, strength=0.12):
    """Modulate brightness of an RGBA art image by a texture (mean 0.5)."""
    a = np.asarray(img, float)
    t = (tex[: a.shape[0], : a.shape[1]] - 0.5) * 2 * strength
    a[..., :3] = np.clip(a[..., :3] * (1 + t[..., None]), 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def shade_img(w, h, left=0.0, right=0.0, top=0.0, bottom=0.0, ao=0.0, highlight=0.0, pillow=0.0, wrinkles=0.0, seed=3):
    """Black/white shading overlay in art space (alpha encodes darkness/brightness)."""
    xx = np.linspace(0, 1, w)[None, :]
    yy = np.linspace(0, 1, h)[:, None]
    dark = left + (right - left) * xx + top + (bottom - top) * yy
    dark = dark + ao * np.clip((yy - 0.92) / 0.08, 0, 1) ** 2
    if pillow:
        r = np.sqrt(((xx - 0.45) / 0.75) ** 2 + ((yy - 0.45) / 0.8) ** 2)
        dark = dark + pillow * np.clip(r - 0.25, 0, 1)
    if wrinkles:
        rng = np.random.default_rng(seed)
        for _ in range(5):
            cx, cy, ang = rng.random(), rng.random(), rng.uniform(-0.6, 0.6)
            d_ = ((xx - cx) * math.sin(ang) + (yy - cy) * math.cos(ang))
            dark = dark + wrinkles * np.exp(-(d_ / 0.025) ** 2) * (0.5 + 0.5 * np.cos((xx - cx) * 6))
    dark = np.clip(dark, -0.6, 0.85)
    out = np.zeros((h, w, 4), np.uint8)
    neg = dark < 0
    out[..., :3] = np.where(neg[..., None], 255, 0)
    out[..., 3] = (np.abs(dark) * 255).astype(np.uint8)
    if highlight:
        hl = highlight * np.exp(-((xx - 0.08) / 0.05) ** 2) * np.ones_like(yy)
        a = out[..., 3].astype(float)
        out[..., :3] = np.where((hl > np.abs(dark))[..., None], 255, out[..., :3])
        out[..., 3] = np.maximum(a, hl * 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


# ------------------------------------------------------------------ camera


class Cam:
    """Pinhole camera on the bag's front axis, rotated by yaw; verticals stay vertical (product-shot look)."""

    def __init__(self, yaw=26.0, dist=1500.0, eye=520.0):
        self.t = math.radians(yaw)
        self.dist, self.eye = dist, eye

    def __call__(self, x, y, z):
        c, s = math.cos(self.t), math.sin(self.t)
        xr = x * c - z * s
        zr = x * s + z * c
        dz = self.dist - zr
        return xr / dz, (y - self.eye) / dz


class Canvas:
    """Fits projected points into an image and composites layers."""

    def __init__(self, cam, pts3d, px_w, margin=0.06):
        self.cam = cam
        uv = [cam(*p) for p in pts3d]
        us, vs = [p[0] for p in uv], [p[1] for p in uv]
        self.u0, self.u1, self.v0, self.v1 = min(us), max(us), min(vs), max(vs)
        span_u, span_v = self.u1 - self.u0, self.v1 - self.v0
        self.s = px_w * (1 - 2 * margin) / span_u
        self.w = int(px_w)
        self.h = int(span_v * self.s + 2 * margin * px_w)
        self.m = margin * px_w
        self.img = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))

    def p(self, x, y, z):
        u, v = self.cam(x, y, z)
        return (self.m + (u - self.u0) * self.s, self.m + (self.v1 - v) * self.s)

    def scale_at(self, x, y, z):
        u0, _ = self.cam(x, y, z)
        u1, _ = self.cam(x + 1, y, z)
        return abs(u1 - u0) * self.s

    def face(self, corners3d, art, shade=None):
        """corners: TL, TR, BR, BL in 3D; art: RGBA image mapped onto them."""
        quad = [self.p(*c) for c in corners3d]
        layer = warp(art, quad, (self.w, self.h))
        mask = poly_mask(quad, self.w, self.h)
        layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))
        self.img.alpha_composite(layer)
        if shade is not None:
            sl = warp(shade, quad, (self.w, self.h))
            sl.putalpha(ImageChops.multiply(sl.getchannel("A"), mask))
            self.img.alpha_composite(sl)
        return quad

    def svg(self, body):
        self.img.alpha_composite(svg_img(body, self.w, self.h))

    def path(self, pts3d, close=False):
        pts = [self.p(*q) for q in pts3d]
        return "M" + "L".join(f"{fmt(x)} {fmt(y)}" for x, y in pts) + ("Z" if close else "")


def shadows(obj, ground_pts, w, h, soft=0.06, contact=0.012, strength=0.55, skew=0.18):
    """Contact shadow under the base + soft cast shadow from the silhouette (returns RGBA shadow layer)."""
    a = obj.getchannel("A")
    # cast shadow: squash the silhouette onto the ground, lean it right/back, blur it
    bbox = a.getbbox() or (0, 0, w, h)
    base_y = max(p[1] for p in ground_pts)
    sil = a.crop(bbox)
    sh_h = max(2, int(sil.height * 0.22))
    sil = sil.resize((sil.width, sh_h), Image.BILINEAR)
    cast = Image.new("L", (w, h), 0)
    cast.paste(sil, (bbox[0] + int(sil.width * skew * 0.5), int(base_y - sh_h * 0.85)))
    cast = cast.filter(ImageFilter.GaussianBlur(w * soft))
    con = Image.new("L", (w, h), 0)
    con.paste(poly_mask(ground_pts, w, h), (0, 0))
    con = con.filter(ImageFilter.GaussianBlur(w * contact))
    alpha = ImageChops.add(cast.point(lambda v: v * 0.55 * strength), con.point(lambda v: v * 0.9 * strength))
    out = Image.new("RGBA", (w, h), (8, 14, 45, 0))
    out.putalpha(alpha)
    return out


# ------------------------------------------------------------------ products


def darker(hex_, k):
    h = hex_.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02X%02X%02X" % (int(r * k), int(g * k), int(b * k))


def paper_bag(front, side, dims, substrate, handle_col, yaw=26.0, px_w=1400, kraft=False, seed=1):
    """Open paper shopping bag with twisted rope handles. front/side: RGBA art (front W x H, side D x H)."""
    W, D, H = dims
    cam = Cam(yaw, dist=H * 4.2, eye=H * 1.45)
    hh = H * 0.30
    pts = [(x, y, z) for x in (-W / 2, W / 2) for y in (0, H + hh) for z in (-D / 2, D / 2)]
    cv = Canvas(cam, pts, px_w)
    right = yaw >= 0
    sx = W / 2 if right else -W / 2
    tex = noise(front.width, front.height, seed, 1.2, fibres=kraft)
    stex = noise(side.width, side.height, seed + 1, 1.2, fibres=kraft)
    front_t = textured(front, tex, 0.07 if kraft else 0.04)
    side_t = textured(side, stex, 0.07 if kraft else 0.04)

    def handle(z, lean):
        out = []
        for i in range(41):
            t = i / 40
            x = -W * 0.17 + W * 0.34 * t
            y = H - 28 + (hh + 28) * math.sin(math.pi * t) ** 0.8
            out.append((x, y, z + lean * math.sin(math.pi * t)))
        return out

    def rope(pts3d, col):
        light = sum(int(col.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) > 450
        mid = pts3d[len(pts3d) // 2]
        wpx = 9 * cv.scale_at(*mid)
        d = cv.path(pts3d)
        return (f'<path d="{d}" fill="none" stroke="{darker(col, 0.55)}" stroke-opacity="0.35" stroke-width="{fmt(wpx * 1.25)}" '
                f'stroke-linecap="round" transform="translate({fmt(wpx * 0.25)} {fmt(wpx * 0.35)})"/>'
                f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{fmt(wpx)}" stroke-linecap="round"/>'
                f'<path d="{d}" fill="none" stroke="{darker(col, 0.55)}" stroke-opacity="{0.22 if light else 0.4}" '
                f'stroke-width="{fmt(wpx * 0.8)}" stroke-dasharray="{fmt(wpx * 0.28)} {fmt(wpx * 0.42)}" stroke-linecap="butt"/>'
                f'<path d="{d}" fill="none" stroke="#FFFFFF" stroke-opacity="0.28" stroke-width="{fmt(wpx * 0.22)}" '
                f'stroke-linecap="round" transform="translate({fmt(-wpx * 0.18)} {fmt(-wpx * 0.2)})"/>')

    # back handle, interior, inner back band
    cv.svg(rope(handle(-D / 2 + 3, -18), handle_col))
    TL, TR = (-W / 2, H, D / 2), (W / 2, H, D / 2)
    BTL, BTR = (-W / 2, H, -D / 2), (W / 2, H, -D / 2)
    inside = darker(substrate, 0.35)
    gid = "ins"
    q = [cv.p(*TL), cv.p(*TR), cv.p(*BTR), cv.p(*BTL)]
    body = (f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{darker(substrate, 0.55)}"/>'
            f'<stop offset="1" stop-color="{inside}"/></linearGradient>'
            f'<path d="M' + "L".join(f"{fmt(x)} {fmt(y)}" for x, y in q) + f'Z" fill="url(#{gid})"/>')
    band = [cv.p(*BTL), cv.p(*BTR), cv.p(W / 2, H - 40, -D / 2), cv.p(-W / 2, H - 40, -D / 2)]
    body += ('<path d="M' + "L".join(f"{fmt(x)} {fmt(y)}" for x, y in band) + f'Z" fill="{darker(substrate, 0.72)}"/>')
    cv.svg(body)
    cv.svg(rope(handle(D / 2 - 3, 22), handle_col))
    # faces
    fsh = shade_img(front.width, front.height, left=-0.04, right=0.06, top=-0.02, bottom=0.06, ao=0.22, wrinkles=0.03,
                    seed=seed)
    cv.face([TL, TR, (W / 2, 0, D / 2), (-W / 2, 0, D / 2)], front_t, fsh)
    if right:
        corners = [(W / 2, H, D / 2), (W / 2, H, -D / 2), (W / 2, 0, -D / 2), (W / 2, 0, D / 2)]
        ssh = shade_img(side.width, side.height, left=0.18, right=0.30, bottom=0.05, ao=0.25)
    else:
        corners = [(-W / 2, H, -D / 2), (-W / 2, H, D / 2), (-W / 2, 0, D / 2), (-W / 2, 0, -D / 2)]
        ssh = shade_img(side.width, side.height, left=0.02, right=0.10, bottom=0.05, ao=0.25)
    cv.face(corners, side_t, ssh)
    # gusset crease, top-edge highlight, corner highlight
    cz = [(sx, H - 6, 0), (sx, 0, 0)]
    cv.svg(f'<path d="{cv.path(cz)}" stroke="#000" stroke-opacity="0.16" stroke-width="{fmt(cv.s * 0.0009)}" fill="none"/>'
           f'<path d="{cv.path([TL, TR])}" stroke="#FFFFFF" stroke-opacity="0.35" stroke-width="{fmt(cv.s * 0.0006)}" fill="none"/>'
           f'<path d="{cv.path([(sx, H, D / 2), (sx, 0, D / 2)])}" stroke="#FFFFFF" stroke-opacity="0.22" '
           f'stroke-width="{fmt(cv.s * 0.0007)}" fill="none"/>')
    ground = [cv.p(-W / 2, 0, D / 2), cv.p(W / 2, 0, D / 2), cv.p(W / 2, 0, -D / 2), cv.p(-W / 2, 0, -D / 2)]
    return cv.img, ground


def flat_bag(front, dims, fabric_tex="canvas", yaw=-10.0, px_w=1200, handles=None, hole=None, seed=2, depth=6):
    """Tote / non-woven bag standing upright: front panel art, optional die-cut hole (path in art px),
    handles: ('strap', colour, width_mm, height_mm) or ('loop', ...)."""
    W, H = dims
    cam = Cam(yaw, dist=H * 4.5, eye=H * 1.15)
    top = H + (handles[3] if handles else 0)
    pts = [(x, y, z) for x in (-W / 2, W / 2) for y in (0, top) for z in (-depth, depth)]
    cv = Canvas(cam, pts, px_w)
    tex = noise(front.width, front.height, seed, 1.5, fibres=fabric_tex == "nonwoven", weave=fabric_tex == "canvas")
    art = textured(front, tex, 0.13 if fabric_tex == "canvas" else 0.09)
    if hole:
        m = svg_img(f'<path d="{hole}" fill="#fff"/>', front.width, front.height).getchannel("A")
        art.putalpha(ImageChops.subtract(art.getchannel("A"), m))
    TL, TR = (-W / 2, H, depth), (W / 2, H, depth)

    span = handles[4] if handles and len(handles) > 4 else 0.22

    def strap(xc, z, col, wmm, hmm, back=False):
        pts3d = []
        for i in range(41):
            t = i / 40
            x = xc - W * span + W * 2 * span * t
            y = H - 30 + (hmm + 30) * math.sin(math.pi * t) ** 0.75
            pts3d.append((x, y, z + (-60 if back else 18) * math.sin(math.pi * t)))
        mid = pts3d[20]
        wpx = wmm * cv.scale_at(*mid)
        d = cv.path(pts3d)
        return (f'<path d="{d}" fill="none" stroke="{darker(col, 0.8)}" stroke-width="{fmt(wpx)}" stroke-linecap="butt"/>'
                f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{fmt(wpx * 0.82)}" stroke-linecap="butt"/>'
                f'<path d="{d}" fill="none" stroke="{darker(col, 0.55)}" stroke-opacity="0.6" stroke-width="{fmt(wpx * 0.06)}" '
                f'stroke-dasharray="{fmt(wpx * 0.18)} {fmt(wpx * 0.12)}" transform="translate(0 {fmt(-wpx * 0.28)})"/>'
                f'<path d="{d}" fill="none" stroke="{darker(col, 0.55)}" stroke-opacity="0.6" stroke-width="{fmt(wpx * 0.06)}" '
                f'stroke-dasharray="{fmt(wpx * 0.18)} {fmt(wpx * 0.12)}" transform="translate(0 {fmt(wpx * 0.28)})"/>')

    if handles:
        kind, col, wmm, hmm = handles[:4]
        cv.svg(strap(0, -depth, darker(col, 0.85), wmm, hmm * 0.92, back=True))
    sh = shade_img(front.width, front.height, left=-0.05, right=0.09, top=-0.03, bottom=0.05, ao=0.22, pillow=0.3,
                   wrinkles=0.09 if fabric_tex == "canvas" else 0.06, seed=seed)
    if hole:
        sh.putalpha(ImageChops.subtract(sh.getchannel("A"), svg_img(f'<path d="{hole}" fill="#fff"/>', front.width,
                                                                    front.height).getchannel("A")))
    cv.face([TL, TR, (W / 2, 0, depth), (-W / 2, 0, depth)], art, sh)
    if handles:
        cv.svg(strap(0, depth, col, wmm, hmm))
        for xs in (-W * span, W * span):
            q = [cv.p(xs - wmm / 2, H - 4, depth), cv.p(xs + wmm / 2, H - 4, depth), cv.p(xs + wmm / 2, H - 4 - wmm * 1.2, depth),
                 cv.p(xs - wmm / 2, H - 4 - wmm * 1.2, depth)]
            d = "M" + "L".join(f"{fmt(x)} {fmt(y)}" for x, y in q) + "Z"
            cv.svg(f'<path d="{d}" fill="{col}"/><path d="{d}" fill="none" stroke="{darker(col, 0.5)}" stroke-opacity="0.6" '
                   f'stroke-width="{fmt(cv.s * 0.0005)}" stroke-dasharray="{fmt(cv.s * 0.002)} {fmt(cv.s * 0.0015)}"/>')
    ground = [cv.p(-W / 2, 0, depth), cv.p(W / 2, 0, depth), cv.p(W / 2, 0, -depth * 3), cv.p(-W / 2, 0, -depth * 3)]
    return cv.img, ground


def box(front, side, topart, dims, yaw=30.0, px_w=1400, piping="#000050", seed=4, strap=True):
    """Closed box (rider delivery backpack or carton) seen from above: front, side and top faces."""
    W, D, H = dims
    cam = Cam(yaw, dist=H * 5.5, eye=H * 1.55)
    pts = [(x, y, z) for x in (-W / 2, W / 2) for y in (0, H + 40) for z in (-D / 2, D / 2)]
    cv = Canvas(cam, pts, px_w)
    tex = noise(front.width, front.height, seed, 1.4, weave=True)
    stex = noise(side.width, side.height, seed + 1, 1.4, weave=True)
    ttex = noise(topart.width, topart.height, seed + 2, 1.4, weave=True)
    cv.face([(-W / 2, H, -D / 2), (W / 2, H, -D / 2), (W / 2, H, D / 2), (-W / 2, H, D / 2)], textured(topart, ttex, 0.06),
            shade_img(topart.width, topart.height, left=-0.06, right=0.04, top=0.02, bottom=-0.03))
    cv.face([(-W / 2, H, D / 2), (W / 2, H, D / 2), (W / 2, 0, D / 2), (-W / 2, 0, D / 2)], textured(front, tex, 0.06),
            shade_img(front.width, front.height, left=-0.03, right=0.07, bottom=0.05, ao=0.2, pillow=0.08))
    cv.face([(W / 2, H, D / 2), (W / 2, H, -D / 2), (W / 2, 0, -D / 2), (W / 2, 0, D / 2)], textured(side, stex, 0.06),
            shade_img(side.width, side.height, left=0.16, right=0.28, bottom=0.05, ao=0.22))
    pw = cv.s * 0.0011
    edges = [[(-W / 2, H, D / 2), (W / 2, H, D / 2)], [(W / 2, H, D / 2), (W / 2, H, -D / 2)],
             [(W / 2, H, -D / 2), (-W / 2, H, -D / 2)], [(-W / 2, H, -D / 2), (-W / 2, H, D / 2)],
             [(W / 2, H, D / 2), (W / 2, 0, D / 2)], [(-W / 2, H, D / 2), (-W / 2, 0, D / 2)],
             [(W / 2, H, -D / 2), (W / 2, 0, -D / 2)]]
    body = "".join(f'<path d="{cv.path(e)}" stroke="{piping}" stroke-width="{fmt(pw * 3.2)}" stroke-linecap="round" fill="none"/>'
                   f'<path d="{cv.path(e)}" stroke="#FFFFFF" stroke-opacity="0.12" stroke-width="{fmt(pw)}" fill="none"/>'
                   for e in edges)
    zi = 22
    zip_ = [(-W / 2 + zi, H, D / 2 - zi), (W / 2 - zi, H, D / 2 - zi), (W / 2 - zi, H, -D / 2 + zi), (-W / 2 + zi, H, -D / 2 + zi)]
    body += (f'<path d="{cv.path(zip_, True)}" stroke="#000030" stroke-opacity="0.55" stroke-width="{fmt(pw * 1.6)}" '
             f'stroke-dasharray="{fmt(pw * 2)} {fmt(pw * 1.2)}" fill="none"/>')
    if strap:
        hs = [(-W * 0.16, H, 0), (-W * 0.12, H + 34, 0), (W * 0.12, H + 34, 0), (W * 0.16, H, 0)]
        body += (f'<path d="{cv.path(hs)}" stroke="{piping}" stroke-width="{fmt(pw * 9)}" stroke-linejoin="round" '
                 f'stroke-linecap="round" fill="none"/>')
    cv.svg(body)
    ground = [cv.p(-W / 2, 0, D / 2), cv.p(W / 2, 0, D / 2), cv.p(W / 2, 0, -D / 2), cv.p(-W / 2, 0, -D / 2)]
    return cv.img, ground


# ------------------------------------------------------------------ scene


def studio(w, h, top="#F6F9FC", bottom="#DCE5EF", floor=0.72):
    """Soft studio backdrop with a gentle floor transition."""
    a = np.zeros((h, w, 3), float)
    t = np.linspace(0, 1, h)[:, None]
    c0 = np.array([int(top[i:i + 2], 16) for i in (1, 3, 5)], float)
    c1 = np.array([int(bottom[i:i + 2], 16) for i in (1, 3, 5)], float)
    k = np.clip((t - floor + 0.08) / 0.16, 0, 1)
    k = k * k * (3 - 2 * k)
    col = c0 * (1 - k * 0.5) + c1 * (k * 0.5)          # (h, 3)
    a[:] = col[:, None, :]
    xx = np.linspace(-1, 1, w)[None, :]
    vign = 1 - 0.06 * (xx ** 2) - 0.05 * (np.linspace(-1, 1, h)[:, None] ** 2)
    a = a * vign[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def place(scene, item, ground, cx, base_y, height, cast=0.22, dark=(10, 16, 52)):
    """Place an item so its ground-line centre sits at (cx, base_y) with the given pixel height; shadows are built
    in scene space: contact (base outline), ambient occlusion (wider) and a soft shadow cast back-right."""
    a = item.getchannel("A")
    bb = a.getbbox()
    k = height / (bb[3] - bb[1])
    size = (max(1, int(item.width * k)), max(1, int(item.height * k)))
    it = item.resize(size, Image.LANCZOS)
    g = [(x * k, y * k) for x, y in ground]
    gx0, gx1 = min(p[0] for p in g), max(p[0] for p in g)
    gy1 = max(p[1] for p in g)
    x = int(cx - (gx0 + gx1) / 2)
    y = int(base_y - gy1)
    W, H = scene.size
    sg = [(px + x, py + y) for px, py in g]
    contact = poly_mask(sg, W, H).filter(ImageFilter.GaussianBlur(max(2, height * 0.012)))
    xs, ys = [p[0] for p in sg], [p[1] for p in sg]
    cxg, cyg = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    rx, ry = (max(xs) - min(xs)) * 0.62, (max(ys) - min(ys)) * 0.9 + height * 0.02
    amb = svg_img(f'<ellipse cx="{fmt(cxg)}" cy="{fmt(cyg)}" rx="{fmt(rx)}" ry="{fmt(ry)}" fill="#fff"/>', W, H).getchannel("A")
    amb = amb.filter(ImageFilter.GaussianBlur(max(3, height * 0.045)))
    sil = it.getchannel("A")
    cast_l = Image.new("L", (W, H), 0)
    if cast:
        sb = sil.getbbox()
        piece = sil.crop(sb)
        ph = max(2, int(piece.height * 0.2))
        piece = piece.resize((piece.width, ph), Image.BILINEAR)
        piece = piece.transform(piece.size, Image.AFFINE, (1, 0.9, -0.9 * ph, 0, 1, 0), Image.BILINEAR)
        cast_l.paste(piece, (x + sb[0] + int(height * 0.03), int(base_y - ph * 0.95)))
        cast_l = cast_l.filter(ImageFilter.GaussianBlur(max(4, height * 0.05)))
    alpha = ImageChops.add(ImageChops.add(contact.point(lambda v: v * 0.55), amb.point(lambda v: v * 0.22)),
                           cast_l.point(lambda v: v * cast))
    sh = Image.new("RGBA", (W, H), dark + (0,))
    sh.putalpha(alpha)
    scene.alpha_composite(sh)
    _paste(scene, it, x, y)


def _paste(scene, im, x, y):
    layer = Image.new("RGBA", scene.size, (0, 0, 0, 0))
    layer.paste(im, (x, y))
    scene.alpha_composite(layer)
