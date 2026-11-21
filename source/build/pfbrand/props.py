"""Product renderers for merchandise and print mockups, built from the real artwork with numpy shading:
mugs, paper cups and tape rolls (surfaces of revolution under a raised orthographic camera), pens, a laptop lid,
standing and open books, plus flat-lay surfaces, paper texture and soft shadows."""
import math

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from scipy import ndimage

from . import mockup as MK


def _norm(*v):
    a = np.array(v, float)
    return a / np.linalg.norm(a)


L_KEY = _norm(-0.55, 0.62, 0.56)       # studio key light: upper left, in front (x right, y up, z to camera)
FLAT_LIGHT = _norm(-0.42, -0.55, 0.72)  # flat lays: x right, y down (screen), z up to the camera
EXPO = 1.08


# ------------------------------------------------------------------ raster helpers

def rgbf(hex_):
    h = hex_.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def premul(img):
    a = np.asarray(img.convert("RGBA"), np.float32) / 255
    a[..., :3] *= a[..., 3:4]
    return a


def sample(arr, x, y):
    """Bilinear sample of an H x W x C array at float pixel coordinates (clamped)."""
    h, w = arr.shape[:2]
    x = np.clip(x, 0, w - 1.001)
    y = np.clip(y, 0, h - 1.001)
    x0, y0 = np.floor(x).astype(np.int32), np.floor(y).astype(np.int32)
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    a, b = arr[y0, x0], arr[y0, x0 + 1]
    c, d = arr[y0 + 1, x0], arr[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def to_image(rgb, alpha, ss=1):
    out = np.dstack([np.clip(rgb, 0, 1) * 255, np.clip(alpha, 0, 1)[..., None] * 255]).astype(np.uint8)
    im = Image.fromarray(out, "RGBA")
    if ss > 1:
        im = im.convert("RGBa").resize((im.width // ss, im.height // ss), Image.LANCZOS).convert("RGBA")
    return im


def fbm(w, h, seed=1, octaves=((1.0, 2), (0.6, 8), (0.5, 40))):
    """Smooth value noise (mean 0, std 1): sum of upscaled random grids, (amplitude, cell px)."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    for amp, cell in octaves:
        gw, gh = max(2, int(w / cell)), max(2, int(h / cell))
        n = (rng.random((gh, gw)) * 255).astype(np.uint8)
        out += amp * (np.asarray(Image.fromarray(n).resize((w, h), Image.BICUBIC), np.float32) / 255 - 0.5)
    return (out - out.mean()) / (out.std() + 1e-6)


# ------------------------------------------------------------------ lighting

def shade(n, amb=0.5, kd=0.56, wrap=0.35, fill=0.16, edge=0.28, light=L_KEY):
    nx, ny, nz = n
    d = nx * light[0] + ny * light[1] + nz * light[2]
    s = amb + kd * np.clip((d + wrap) / (1 + wrap), 0, 1)
    s = s + fill * np.clip(nx, 0, 1) ** 2
    return s * (1 - edge * (1 - np.clip(nz, 0, 1)) ** 3)


def strips(th, spec):
    """Vertical softbox reflections on a surface of revolution: [(centre deg, width deg, strength)]."""
    out = np.zeros_like(th)
    for c, w, k in spec:
        out = out + k * np.exp(-((th - math.radians(c)) / math.radians(w)) ** 2)
    return out


def blinn(n, view, power, k, light=L_KEY):
    hv = _norm(*(np.array(light) + np.array(view)))
    c = n[0] * hv[0] + n[1] * hv[1] + n[2] * hv[2]
    return k * np.clip(c, 0, 1) ** power


# ------------------------------------------------------------------ surfaces of revolution

class Lathe:
    """Raised orthographic camera on an upright object of revolution (axis = y, millimetres).
    Screen y grows downwards and y = 0 is the centre of the ellipse at height `top`."""

    def __init__(self, r_max, top, bottom, px_w, elev=14.0, ss=2, pad=4.0, left=0.0, right=0.0):
        e = math.radians(elev)
        self.se, self.ce = math.sin(e), math.cos(e)
        self.top, self.ss = top, ss
        self.x0 = -r_max - pad - left
        x1 = r_max + pad + right
        self.y0 = -r_max * self.se - pad
        y1 = (top - bottom) * self.ce + r_max * self.se + pad
        self.k = px_w * ss / (x1 - self.x0)
        self.W = int(round((x1 - self.x0) * self.k))
        self.H = int(round((y1 - self.y0) * self.k))
        xs = (self.x0 + (np.arange(self.W) + 0.5) / self.k).astype(np.float32)
        ys = (self.y0 + (np.arange(self.H) + 0.5) / self.k).astype(np.float32)
        self.X, self.Y = np.meshgrid(xs, ys)
        self.rgb = np.zeros((self.H, self.W, 3), np.float32)
        self.a = np.zeros((self.H, self.W), np.float32)
        self.view = (0.0, self.se, self.ce)

    def sy(self, h, z=0.0):
        return (self.top - h) * self.ce + z * self.se

    def band(self, r0, r1, h0, h1):
        """Front surface of a conical band (radius r0 at height h0, r1 at h1): mask, theta, height, normal."""
        slope = (r1 - r0) / (h1 - h0)
        X, Y = self.X, self.Y
        h = self.top - Y / self.ce
        for _ in range(5):
            r = r0 + slope * (np.clip(h, h0, h1) - h0)
            s = np.clip(X / r, -1, 1)
            h = self.top - (Y - r * np.sqrt(1 - s * s) * self.se) / self.ce
        r = r0 + slope * (np.clip(h, h0, h1) - h0)
        m = (np.abs(X) < r) & (h >= h0) & (h <= h1)
        th = np.arcsin(np.clip(X / r, -1, 1))
        a = math.atan(slope)
        n = (np.sin(th) * math.cos(a), np.full_like(th, -math.sin(a)), np.cos(th) * math.cos(a))
        return m, th, h, n

    def disc(self, r, h, r_in=0.0):
        yc = self.sy(h)
        m = (self.X / r) ** 2 + ((self.Y - yc) / (r * self.se)) ** 2 <= 1
        if r_in > 0:
            m &= (self.X / r_in) ** 2 + ((self.Y - yc) / (r_in * self.se)) ** 2 > 1
        return m

    def radius(self, h):
        """Radial distance (mm) of each pixel on the horizontal plane at height h."""
        return np.sqrt(self.X ** 2 + ((self.Y - self.sy(h)) / self.se) ** 2)

    def inner(self, ri, h0, h1):
        """Back inner wall of a hollow cylinder, seen through its opening."""
        zb = -np.sqrt(np.clip(ri * ri - self.X ** 2, 0, None))
        h = self.top - (self.Y - zb * self.se) / self.ce
        m = (np.abs(self.X) < ri) & (h >= h0) & (h <= h1)
        return m, h, (-self.X / ri, np.zeros_like(zb), -zb / ri)

    def paint(self, m, rgb, a=1.0):
        if isinstance(rgb, np.ndarray) and rgb.ndim == 3:
            self.rgb[m] = rgb[m]
        else:
            self.rgb[m] = rgb
        self.a[m] = a

    def px(self, x, y):
        return (x - self.x0) * self.k, (y - self.y0) * self.k

    def image(self):
        return to_image(self.rgb, self.a, self.ss)

    def ground(self, r, h=0.0, n=36):
        out = []
        for i in range(n):
            t = 2 * math.pi * i / n
            x, y = self.px(r * math.sin(t), self.sy(h, r * math.cos(t)))
            out.append((x / self.ss, y / self.ss))
        return out


def _bezier(p, n=240):
    t = np.linspace(0, 1, n)[:, None]
    p = np.array(p, float)
    return ((1 - t) ** 3 * p[0] + 3 * (1 - t) ** 2 * t * p[1] + 3 * (1 - t) * t ** 2 * p[2] + t ** 3 * p[3])


def _tube(lt, centre_mm, radius_mm):
    """Shaded tube along a polyline (mm): mask and 3D normals from a distance transform."""
    cl = np.zeros((lt.H, lt.W), bool)
    for x, y in centre_mm:
        px, py = lt.px(x, y)
        ix, iy = int(px), int(py)
        if 0 <= ix < lt.W and 0 <= iy < lt.H:
            cl[iy, ix] = True
    dist, (iy, ix) = ndimage.distance_transform_edt(~cl, return_indices=True)
    rpx = radius_mm * lt.k
    m = dist <= rpx
    gy, gx = np.mgrid[0:lt.H, 0:lt.W]
    dx = ndimage.gaussian_filter(((gx - ix) / rpx).astype(np.float32), 2.5)
    dy = ndimage.gaussian_filter(((gy - iy) / rpx).astype(np.float32), 2.5)
    nz = np.sqrt(np.clip(1 - dx * dx - dy * dy, 0, 1))
    return m, (dx.astype(np.float32), (-dy).astype(np.float32), nz.astype(np.float32))


MUG = {"d": 82.0, "h": 95.0, "print": (216.0, 89.0), "wall": 3.4}


def mug(wrap_img, handle="right", body="#FFFFFF", inner=None, px_w=1000, elev=13.0, ss=2, face=None):
    """11 oz ceramic mug. The wrap (216 x 89 mm) shows its right half with the handle on the right and its left
    half with the handle on the left; the mug turns so that half's centre (face, mm; default the quarter point)
    faces the camera, which puts the handle slightly behind the body as in product photos.
    inner: colour of the inside, rim and handle (two-tone mugs)."""
    D, Hm = MUG["d"], MUG["h"]
    R = D / 2
    PW, PH = MUG["print"]
    sgn = 1 if handle == "right" else -1
    gap = (math.pi * D - PW) / 2
    face = face if face is not None else (0.75 * PW if sgn > 0 else 0.25 * PW)
    th_h = (PW + gap - face) / R if sgn > 0 else -(face + gap) / R       # handle angle from the camera axis
    reach = 31.0
    lt = Lathe(R, Hm, 0, px_w, elev, ss, left=reach if sgn < 0 else 0, right=reach if sgn > 0 else 0)
    body_c, in_c = rgbf(body), rgbf(inner or body)
    # handle (painted first: the body hides its roots); drawn in its own plane, turned to th_h
    yA, yB = lt.sy(Hm - 13), lt.sy(19)
    ym = (yA + yB) / 2
    c1 = _bezier([(R - 3, yA), (R + 16, yA - 3.5), (R + reach + 1, yA + 2), (R + reach - 1.5, ym)], 3000)
    c2 = _bezier([(R + reach - 1.5, ym), (R + reach - 3, yB - 5), (R + 14, yB + 4), (R - 3, yB)], 3000)
    pts = [(xr * math.sin(th_h), y + xr * math.cos(th_h) * lt.se) for xr, y in np.vstack([c1, c2])]
    hm, hn = _tube(lt, pts, 5.4)
    col = in_c * (shade(hn) * EXPO)[..., None] + blinn(hn, lt.view, 40, 0.55)[..., None]
    lt.paint(hm, col)
    # body with the print
    m, th, h, n = lt.band(R, R, 0, Hm)
    u = (PW + gap + (th - th_h) * R) if sgn > 0 else (-gap + (th - th_h) * R)
    v = (Hm - h) - (Hm - PH) / 2
    art = premul(wrap_img)
    ah, aw = art.shape[:2]
    smp = sample(art, u / PW * aw, v / PH * ah)
    smp[~((u >= 0) & (u <= PW) & (v >= 0) & (v <= PH))] = 0
    alb = smp[..., :3] + body_c * (1 - smp[..., 3:4])
    ao = 1 - 0.30 * smoothstep(5.0, 0.0, h)
    lip = 0.10 * smoothstep(Hm - 3, Hm, h)
    gl = strips(th, [(-24, 5.5, 0.5), (-24, 22, 0.08), (63, 3.5, 0.28)])
    lt.paint(m, alb * (shade(n) * ao * EXPO)[..., None] + (gl + lip)[..., None])
    # inside: the back wall seen through the opening, then the rim
    Ri = R - MUG["wall"]
    mi, hi, ni = lt.inner(Ri, Hm - 80, Hm)
    mi &= lt.disc(Ri, Hm)
    depth = Hm - hi
    lt.paint(mi, in_c * (shade(ni, amb=0.42, kd=0.5) * (1 - 0.45 * np.clip(depth / 24, 0, 1)) * EXPO)[..., None])
    mr = lt.disc(R, Hm, Ri)
    rr = lt.radius(Hm)
    rim = (rr - Ri) / (R - Ri)                       # 0 inner edge .. 1 outer edge
    rim_shade = 0.86 + 0.16 * np.sin(np.clip(rim, 0, 1) * math.pi)
    lt.paint(mr, (in_c if inner else body_c) * (rim_shade * EXPO)[..., None])
    return lt.image(), lt.ground(R)


CUP = {"top": 90.0, "bottom": 60.0, "h": 110.0}


def paper_cup(wrap_img, lid="#FFFFFF", coffee=False, px_w=800, elev=14.0, ss=2, turn=0.25):
    """12 oz paper cup (truncated cone). The rectangular wrap is mapped by angle, like the printed fan.
    turn: which part of the wrap faces the camera (0..1 of its width)."""
    Rt, Rb, Hc = CUP["top"] / 2, CUP["bottom"] / 2, CUP["h"]
    lid_h = 9.5 if lid else 0
    lt = Lathe(Rt + 3, Hc + lid_h, 0, px_w, elev, ss)
    white = rgbf("#FFFFFF")
    m, th, h, n = lt.band(Rb, Rt, 0, Hc)
    art = premul(wrap_img)
    ah, aw = art.shape[:2]
    u = ((th / (2 * math.pi)) + turn) % 1.0 * (aw - 1)
    v = (Hc - h) / Hc * (ah - 1)
    smp = sample(art, u, v)
    alb = smp[..., :3] + white * (1 - smp[..., 3:4])
    ao = 1 - 0.25 * smoothstep(4.0, 0.0, h)
    gl = strips(th, [(-24, 10, 0.12), (60, 5, 0.06)])
    lt.paint(m, alb * (shade(n) * ao * EXPO)[..., None] + gl[..., None])
    # rolled rim (a small torus, drawn as a band whose normal turns with height)
    mr, thr, hr, _ = lt.band(Rt + 1.3, Rt + 1.3, Hc - 1.7, Hc + 1.7)
    ny = np.clip((hr - Hc) / 1.7, -1, 1)
    nr = (np.sin(thr) * np.sqrt(1 - ny * ny), ny, np.cos(thr) * np.sqrt(1 - ny * ny))
    lt.paint(mr, (white * (shade(nr) * EXPO)[..., None]) + blinn(nr, lt.view, 20, 0.15)[..., None])
    if lid:
        lc = rgbf(lid)
        Rl = Rt + 2.6
        ms, ths, hs, ns = lt.band(Rl, Rl, Hc - 3.5, Hc + 4.0)
        lt.paint(ms, lc * (shade(ns) * EXPO)[..., None] + strips(ths, [(-24, 4, 0.4), (62, 3, 0.2)])[..., None])
        lip_r = lt.radius(Hc + 4.0)
        md = lt.disc(Rl, Hc + 4.0)
        deck = 0.9 + 0.05 * smoothstep(Rl - 1.5, Rl, lip_r)
        lt.paint(md, lc * (deck * EXPO)[..., None])
        mdo, thd, hd, nd = lt.band(Rt - 3.5, Rt - 7.0, Hc + 4.0, Hc + 9.5)
        lt.paint(mdo, lc * (shade(nd) * EXPO)[..., None] + strips(thd, [(-24, 5, 0.3)])[..., None])
        mt = lt.disc(Rt - 7.0, Hc + 9.5)
        lt.paint(mt, lc * (0.95 * EXPO))
        # sip opening on the raised rim, facing the camera
        yc = lt.sy(Hc + 9.5, Rt - 9.5)
        hole = ((lt.X / 6.5) ** 2 + ((lt.Y - yc) / (2.2 * lt.se + 0.9)) ** 2) <= 1
        lt.paint(hole & mt, lc * 0.28)
    else:
        Ri = Rt - 0.3
        mi, hi, ni = lt.inner(Ri, Hc - 40, Hc)
        mi &= lt.disc(Ri, Hc)
        depth = Hc - hi
        lt.paint(mi, white * (shade(ni, amb=0.45, kd=0.5) * (1 - 0.35 * np.clip(depth / 14, 0, 1)) * EXPO)[..., None])
        if coffee:
            lvl = Hc - 11
            rc = Rb + (Rt - Rb) * lvl / Hc
            mc = lt.disc(rc, lvl) & lt.disc(Ri, Hc)
            rr = lt.radius(lvl) / rc
            foam = rgbf("#C9A27A") * (1 + 0.12 * (1 - rr ** 2))[..., None]
            foam = foam * (1 - 0.35 * smoothstep(0.86, 1.0, rr))[..., None]
            tex = fbm(lt.W, lt.H, 4, ((1.0, 3), (0.5, 12)))
            foam = foam * (1 + 0.03 * tex)[..., None]
            hl = 0.10 * np.exp(-(((lt.X + rc * 0.35) / (rc * 0.25)) ** 2 + ((lt.Y - lt.sy(lvl, -rc * 0.2)) / (rc * lt.se * 0.4)) ** 2))
            lt.paint(mc, foam + hl[..., None])
        mrt = lt.disc(Rt + 1.6, Hc + 1.7, Ri)
        lt.paint(mrt, white * 1.0)
    return lt.image(), lt.ground(Rb)


def tape_roll(repeat_img, repeat_mm=300.0, edge="#E9EEF5", px_w=700, elev=30.0, ss=2):
    """Roll of 48 mm branded tape standing on its side: printed outer face, layered edge, card core."""
    Ro, Rc, Ri, Ht = 55.0, 39.0, 36.5, 48.0
    lt = Lathe(Ro, Ht, 0, px_w, elev, ss)
    kraft = rgbf("#B98B5E")
    m, th, h, n = lt.band(Ro, Ro, 0, Ht)
    art = premul(repeat_img)
    ah, aw = art.shape[:2]
    u = ((th * Ro + 10 * repeat_mm) % repeat_mm) / repeat_mm * (aw - 1)
    v = (Ht - h) / Ht * (ah - 1)
    smp = sample(art, u, v)
    ec = rgbf(edge)
    alb = smp[..., :3] + ec * (1 - smp[..., 3:4])
    gl = strips(th, [(-24, 4, 0.45), (-24, 16, 0.10), (62, 3, 0.25)])
    lt.paint(m, alb * (shade(n) * EXPO)[..., None] + gl[..., None])
    # layered edge on top
    mt = lt.disc(Ro, Ht, Rc)
    rr = lt.radius(Ht)
    rings = 1 + 0.05 * np.sin(rr / 0.33 * 2 * math.pi) + 0.03 * fbm(lt.W, lt.H, 8, ((1.0, 2), (0.5, 9)))
    sheen = 0.10 * np.exp(-(((lt.X + Ro * 0.3) / (Ro * 0.45)) ** 2))
    lt.paint(mt, ec * (0.86 * rings * EXPO)[..., None] + sheen[..., None])
    lt.paint(lt.disc(Rc, Ht, Ri), kraft * 0.95)
    mi, hi, ni = lt.inner(Ri, 0, Ht)
    mi &= lt.disc(Ri, Ht)
    depth = Ht - hi
    lt.paint(mi, kraft * (shade(ni, amb=0.4, kd=0.45) * (1 - 0.4 * np.clip(depth / Ht, 0, 1)))[..., None])
    return lt.image(), lt.ground(Ro)


# ------------------------------------------------------------------ pen (top-down, for flat lays)

PEN_PARTS = [  # x0, x1, r0, r1, material (x from the button end to the tip, mm)
    (0.0, 6.5, 2.5, 2.8, "chrome"),
    (6.5, 9.0, 5.35, 5.35, "chrome"),
    (9.0, 100.0, 5.2, 5.2, "barrel"),
    (100.0, 124.0, 5.2, 4.7, "grip"),
    (124.0, 135.0, 4.7, 1.7, "chrome"),
    (135.0, 140.0, 1.5, 0.45, "tip"),
]
PEN_LEN = 140.0


def pen(print_img, barrel="#000080", px_len=1300, angle=-30.0, ss=2, print_at=50.0, print_size=(50.0, 8.0)):
    """Click pen lying on a table, seen from above; the light stays fixed in the scene for any angle."""
    k = px_len * ss / (PEN_LEN + 8)
    W, H = int((PEN_LEN + 8) * k), int(16 * k)
    xs = (-4 + (np.arange(W) + 0.5) / k).astype(np.float32)
    ys = (-8 + (np.arange(H) + 0.5) / k).astype(np.float32)
    X, Y = np.meshgrid(xs, ys)
    r = np.zeros_like(X)
    dr = np.zeros_like(X)
    mat = np.full(X.shape, -1, np.int8)
    for i, (x0, x1, r0, r1, _) in enumerate(PEN_PARTS):
        sel = (X >= x0) & (X < x1)
        r = np.where(sel, r0 + (r1 - r0) * (X - x0) / (x1 - x0), r)
        dr = np.where(sel, (r1 - r0) / (x1 - x0), dr)
        mat = np.where(sel, i, mat)
    r = np.where(X < 1.2, r * np.sqrt(np.clip(X / 1.2, 0, 1)), r)       # rounded button end
    inside = (np.abs(Y) <= r) & (mat >= 0)
    q = np.clip(Y / np.maximum(r, 1e-3), -1, 1)
    nz = np.sqrt(1 - q * q)
    nx = -dr * nz
    ln = np.sqrt(nx * nx + q * q + nz * nz)
    n = (nx / ln, q / ln, nz / ln)
    a = math.radians(angle)
    Lx, Ly, Lz = FLAT_LIGHT
    L = np.array([Lx * math.cos(a) - Ly * math.sin(a), Lx * math.sin(a) + Ly * math.cos(a), Lz])
    V = (0.0, 0.0, 1.0)
    dif = 0.42 + 0.62 * np.clip(n[0] * L[0] + n[1] * L[1] + n[2] * L[2], 0, 1)
    spec = blinn(n, V, 70, 0.55, L) + blinn(n, V, 8, 0.08, L)
    bc = rgbf(barrel)
    rgb = np.zeros(X.shape + (3,), np.float32)
    # barrel and grip, with the print wrapped round the barrel
    s_arc = r * np.arcsin(q)
    pw, ph = print_size
    art = premul(print_img)
    ah, aw = art.shape[:2]
    pu = (X - print_at) / pw * (aw - 1)
    pv = (s_arc + ph / 2) / ph * (ah - 1)
    smp = sample(art, pu, pv)
    smp[~((X >= print_at) & (X <= print_at + pw) & (np.abs(s_arc) <= ph / 2))] = 0
    alb = smp[..., :3] + bc * (1 - smp[..., 3:4])
    names = [p[4] for p in PEN_PARTS]
    is_barrel = np.isin(mat, [i for i, nm in enumerate(names) if nm == "barrel"])
    is_grip = np.isin(mat, [i for i, nm in enumerate(names) if nm == "grip"])
    is_chrome = np.isin(mat, [i for i, nm in enumerate(names) if nm == "chrome"])
    is_tip = np.isin(mat, [i for i, nm in enumerate(names) if nm == "tip"])
    rgb[is_barrel] = (alb * dif[..., None] + spec[..., None])[is_barrel]
    rib = 0.86 + 0.14 * np.cos(X / 1.1 * 2 * math.pi)
    rgb[is_grip] = (bc * 0.72 * (dif * rib)[..., None] + 0.4 * spec[..., None])[is_grip]
    # chrome: environment reflection (bright where the mirror direction meets the light, dark horizon band)
    rx, ry, rz = 2 * n[2] * n[0], 2 * n[2] * n[1], 2 * n[2] * n[2] - 1
    rl = rx * L[0] + ry * L[1] + rz * L[2]
    env = 0.22 + 0.95 * np.clip(rl, 0, 1) ** 14 + 0.28 * np.clip(-ry * np.sign(L[1] + 1e-6), 0, 1) ** 3 \
        - 0.12 * np.exp(-((ry + 0.15) / 0.18) ** 2)
    chrome = np.dstack([env * 0.93, env * 0.95, env * 1.0])
    rgb[is_chrome] = chrome[is_chrome]
    rgb[is_tip] = (rgbf("#2B2E35") * dif[..., None] + spec[..., None] * 0.8)[is_tip]
    # clip: chrome strip on top of the cap end, with its shadow on the barrel
    cw = 1.8
    clip = (X >= 6.0) & (X <= 52.0) & (np.abs(Y) <= cw)
    clip |= ((X - 52.0) ** 2 + Y ** 2 <= cw ** 2)
    sh_dx, sh_dy = -L[0] / L[2] * 1.4, -L[1] / L[2] * 1.4
    clip_sh = ndimage.shift(clip.astype(np.float32), (sh_dy * k, sh_dx * k), order=1)
    clip_sh = ndimage.gaussian_filter(clip_sh, 0.6 * k)
    rgb = rgb * (1 - 0.45 * clip_sh * inside)[..., None]
    cq = np.clip(Y / cw, -1, 1)
    cn = (np.zeros_like(cq), cq * 0.55, np.sqrt(1 - (cq * 0.55) ** 2))
    crl = 2 * cn[2] * (cn[1] * L[1] + cn[2] * L[2]) - L[2]
    cenv = 0.3 + 0.85 * np.clip(crl, 0, 1) ** 10 + 0.15 * (1 - np.abs(cq))
    rgb[clip] = np.dstack([cenv * 0.93, cenv * 0.95, cenv])[clip]
    alpha = (inside | clip).astype(np.float32)
    im = to_image(rgb, alpha, ss)
    return im.rotate(angle, resample=Image.BICUBIC, expand=True)


# ------------------------------------------------------------------ flat lays

def surface(w, h, kind="concrete", seed=1):
    """Table tops for flat lays: concrete, paper, navy (felt), wood (light oak), desk (white laminate)."""
    if kind == "wood":
        rng = np.random.default_rng(seed)
        plank = max(60, h // 5)
        yy = np.arange(h)[:, None].astype(np.float32)
        grain = fbm(w, h, seed, ((1.0, 2), (0.8, 6)))
        streak = (rng.random((max(2, h // 2), max(2, w // 160))) * 255).astype(np.uint8)
        streak = np.asarray(Image.fromarray(streak).resize((w, h), Image.BICUBIC), np.float32) / 255 - 0.5
        low = fbm(w, h, seed + 2, ((1.0, max(w, h) / 6),))
        rings = np.sin((yy / (plank * 0.33) + 0.9 * low + 0.6 * streak) * 2 * math.pi)
        t = 0.5 + 0.11 * rings + 0.26 * streak + 0.07 * grain
        idx = (yy // plank).astype(int)
        offs = rng.uniform(-0.08, 0.08, idx.max() + 2)[idx]
        t = np.clip(t + offs, 0, 1)
        c0, c1 = rgbf("#E6CDAA"), rgbf("#C49C72")
        rgb = c0 * (1 - t[..., None]) + c1 * t[..., None]
        seam = (yy % plank) < 2
        rgb = np.where(seam[..., None], rgb * 0.72, rgb)
        return to_image(rgb, np.ones((h, w), np.float32))
    base = {"concrete": "#E3E7EB", "paper": "#F1EEE8", "navy": "#0F1B5E", "desk": "#F3F5F7", "slate": "#2B3140"}[kind]
    amp = {"concrete": (0.010, 0.016, 0.05), "paper": (0.02, 0.012, 0.02), "navy": (0.05, 0.03, 0.04),
           "desk": (0.008, 0.006, 0.015), "slate": (0.05, 0.03, 0.05)}[kind]
    t = (amp[0] * fbm(w, h, seed, ((1.0, 1.5),)) + amp[1] * fbm(w, h, seed + 1, ((1.0, 6), (0.6, 22)))
         + amp[2] * fbm(w, h, seed + 2, ((1.0, max(w, h) / 5), (0.6, max(w, h) / 14))))
    rgb = rgbf(base) * (1 + t[..., None])
    return to_image(rgb, np.ones((h, w), np.float32))


def paper(img, seed=1, grain=0.025, wave=0.02):
    """Paper grain and a slight unevenness on a flat print."""
    a = np.asarray(img.convert("RGBA"), np.float32)
    h, w = a.shape[:2]
    t = grain * fbm(w, h, seed, ((1.0, 1.4), (0.4, 5))) + wave * fbm(w, h, seed + 1, ((1.0, max(w, h) / 2.5),))
    a[..., :3] = np.clip(a[..., :3] * (1 + t[..., None]), 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def lay(scene, item, cx, cy, angle=0.0, lift=1.0, strength=0.34, ink=(14, 20, 40)):
    """Lay a flat item on the scene (top-down) with a contact shadow and a soft shadow towards the lower right."""
    it = item.rotate(angle, resample=Image.BICUBIC, expand=True) if angle else item
    W = scene.width
    off = lift * W * 0.0032
    blur = lift * W * 0.0045 + 1.0
    pad = int(blur * 3 + off + 6)
    a = it.getchannel("A")
    big = Image.new("L", (it.width + 2 * pad, it.height + 2 * pad), 0)
    big.paste(a, (pad, pad))
    soft = big.filter(ImageFilter.GaussianBlur(blur))
    contact = big.filter(ImageFilter.GaussianBlur(max(1.0, W * 0.0007 * (1 + lift * 0.4))))
    x, y = int(round(cx - it.width / 2)), int(round(cy - it.height / 2))
    sh = Image.new("L", scene.size, 0)
    sh.paste(soft, (x - pad + int(off * 0.75), y - pad + int(off)))
    con = Image.new("L", scene.size, 0)
    con.paste(contact, (x - pad + int(off * 0.15), y - pad + int(off * 0.25)))
    alpha = ImageChops.add(sh.point(lambda v: v * strength), con.point(lambda v: v * 0.42))
    layer = Image.new("RGBA", scene.size, ink + (0,))
    layer.putalpha(alpha)
    scene.alpha_composite(layer)
    MK._paste(scene, it, x, y)
    return (x, y, x + it.width, y + it.height)


def finish(scene, light=0.07, vignette=0.12):
    """One light for the whole flat lay: brighter top left, gentle vignette."""
    w, h = scene.size
    xx = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    yy = np.linspace(-1, 1, h, dtype=np.float32)[:, None]
    f = 1 + light * (-(xx + yy) / 2) - vignette * (xx ** 2 + yy ** 2) / 2
    a = np.asarray(scene.convert("RGB"), np.float32) * f[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def _round_rect_mask(w, h, r, ss=3):
    m = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), r * ss, fill=255)
    return m.resize((w, h), Image.LANCZOS)


def laptop(stickers=(), w_mm=304.0, h_mm=212.0, px_w=1800, finish_="space-grey", seed=3):
    """Closed laptop lid from above with vinyl stickers: [(RGBA art, centre x mm, centre y mm, width mm, angle)]."""
    k = px_w / w_mm
    W, H = px_w, int(round(h_mm * k))
    base = rgbf({"space-grey": "#70757C", "silver": "#CED2D7", "midnight": "#2F3542"}[finish_])
    mask = np.asarray(_round_rect_mask(W, H, int(10 * k)), np.float32) / 255
    xx = np.linspace(0, 1, W, dtype=np.float32)[None, :]
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    tex = 0.012 * fbm(W, H, seed, ((1.0, 1.2), (0.3, 5)))
    light = 0.06 * (1 - (xx + yy)) + 0.05 * np.exp(-(((xx * 0.6 + yy * 0.8) - 0.55) / 0.18) ** 2)
    rgb = base * (1 + tex + light)[..., None]
    m8 = mask > 0.5
    inner = ndimage.binary_erosion(m8, iterations=max(1, int(1.1 * k)))
    edge = m8 & ~inner
    tl = edge & (np.roll(~m8, (int(k), int(k)), (0, 1)) | (np.arange(H)[:, None] < k * 2) | (np.arange(W)[None, :] < k * 2))
    rgb = np.where(edge[..., None], rgb * 0.82, rgb)
    rgb = np.where(tl[..., None], np.minimum(rgb * 1.25 + 0.05, 1), rgb)
    lid = to_image(rgb, mask)
    for art, sx, sy, sw, ang in stickers:
        st = art.resize((int(sw * k), int(sw * k * art.height / art.width)), Image.LANCZOS)
        st = st.rotate(ang, resample=Image.BICUBIC, expand=True)
        a = st.getchannel("A")
        pad = int(2 * k)
        sh = Image.new("L", (st.width + 2 * pad, st.height + 2 * pad), 0)
        sh.paste(a, (pad, pad))
        sh = sh.filter(ImageFilter.GaussianBlur(0.45 * k)).point(lambda v: v * 0.45)
        x, y = int(sx * k - st.width / 2), int(sy * k - st.height / 2)
        layer = Image.new("RGBA", lid.size, (10, 14, 30, 0))
        full = Image.new("L", lid.size, 0)
        full.paste(sh, (x - pad + int(0.25 * k), y - pad + int(0.35 * k)))
        layer.putalpha(full)
        lid.alpha_composite(layer)
        # vinyl sheen: the same diagonal reflection as the lid, a little stronger
        sa = np.asarray(st, np.float32)
        hh, ww = sa.shape[:2]
        gx = (np.arange(ww)[None, :] + x) / W
        gy = (np.arange(hh)[:, None] + y) / H
        gloss = 0.10 * np.exp(-(((gx * 0.6 + gy * 0.8) - 0.55) / 0.12) ** 2) + 0.03
        sa[..., :3] = np.clip(sa[..., :3] + gloss[..., None] * 255, 0, 255)
        MK._paste(lid, Image.fromarray(sa.astype(np.uint8), "RGBA"), x, y)
    out = np.asarray(lid, np.float32)
    out[..., 3] = np.minimum(out[..., 3], mask * 255)
    return Image.fromarray(out.astype(np.uint8), "RGBA")


# ------------------------------------------------------------------ books

def book(front, spine, dims=(148.0, 210.0, 18.0), yaw=-28.0, px_w=1000, cover="#000080", page="#F3F0E8",
         band=None, seed=5):
    """Hardcover notebook standing upright: front cover, spine (left) and the top with the page block.
    band: colour of an elastic closure band (drawn on the front and over the top)."""
    W, H, T = dims
    cam = MK.Cam(yaw, dist=H * 4.6, eye=H * 1.5)
    pts = [(x, y, z) for x in (-W / 2, W / 2) for y in (0, H) for z in (-T / 2, T / 2)]
    cv = MK.Canvas(cam, pts, px_w)
    tw = 1200
    th = max(12, int(tw * T / W))
    top = Image.new("RGBA", (tw, th), cover)
    px_mm = tw / W
    pb = (int(2.0 * px_mm), int(th * 2.4 / T), int(tw - 2.6 * px_mm), int(th - th * 2.4 / T))   # page block inside the boards
    rng = np.random.default_rng(seed)
    lines = (0.93 + 0.07 * rng.random(pb[3] - pb[1]))[:, None] * np.ones((1, pb[2] - pb[0]))
    pg = (rgbf(page) * lines[..., None] * 255).astype(np.uint8)
    top.paste(Image.fromarray(pg, "RGB"), (pb[0], pb[1]))
    fr = front.copy()
    if band:
        bx0, bx1 = int(tw - 17.5 * px_mm), int(tw - 10.5 * px_mm)
        ImageDraw.Draw(top).rectangle((bx0, 0, bx1, th), fill=band)
        fpx = fr.width / W
        d = ImageDraw.Draw(fr)
        d.rectangle((int(fr.width - 17.5 * fpx), 0, int(fr.width - 10.5 * fpx), fr.height), fill=band)
        d.rectangle((int(fr.width - 17.5 * fpx), 0, int(fr.width - 17.0 * fpx), fr.height), fill=MK.darker(band, 0.6))
    cv.face([(-W / 2, H, -T / 2), (W / 2, H, -T / 2), (W / 2, H, T / 2), (-W / 2, H, T / 2)],
            MK.textured(top, MK.noise(tw, th, seed, 1.0), 0.03), MK.shade_img(tw, th, left=-0.06, right=0.02))
    cv.face([(-W / 2, H, T / 2), (W / 2, H, T / 2), (W / 2, 0, T / 2), (-W / 2, 0, T / 2)],
            MK.textured(fr, MK.noise(fr.width, fr.height, seed + 1, 1.2), 0.035),
            MK.shade_img(fr.width, fr.height, left=-0.02, right=0.08, top=-0.02, bottom=0.05, ao=0.18))
    cv.face([(-W / 2, H, -T / 2), (-W / 2, H, T / 2), (-W / 2, 0, T / 2), (-W / 2, 0, -T / 2)],
            MK.textured(spine, MK.noise(spine.width, spine.height, seed + 2, 1.2), 0.035),
            MK.shade_img(spine.width, spine.height, left=-0.12, right=-0.04, bottom=0.05, ao=0.18))
    hw = cv.s * 0.0008
    cv.svg(f'<path d="{cv.path([(-W / 2, H, T / 2), (W / 2, H, T / 2)])}" stroke="#FFFFFF" stroke-opacity="0.25" '
           f'stroke-width="{hw:.2f}" fill="none"/>'
           f'<path d="{cv.path([(-W / 2, H, T / 2), (-W / 2, 0, T / 2)])}" stroke="#FFFFFF" stroke-opacity="0.18" '
           f'stroke-width="{hw:.2f}" fill="none"/>')
    ground = [cv.p(-W / 2, 0, T / 2), cv.p(W / 2, 0, T / 2), cv.p(W / 2, 0, -T / 2), cv.p(-W / 2, 0, -T / 2)]
    return cv.img, ground


def open_book(left, right, cover="#000080", px_w=1800, ribbon="#00B5D8", page_mm=(148.0, 210.0), seed=7):
    """Open notebook from above: two pages with gutter shading, page edges and a ribbon marker."""
    pw, ph = page_mm
    m = 4.0
    k = px_w / (2 * pw + 2 * m)
    W, H = px_w, int(round((ph + 2 * m) * k))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cmask = _round_rect_mask(W, H, int(3 * k))
    cov = Image.new("RGBA", (W, H), cover)
    cov.putalpha(cmask)
    out.alpha_composite(cov)
    d = ImageDraw.Draw(out)
    for i in range(5, 0, -1):                       # page edges of the block under the open pages
        o = i * 0.45 * k
        shade_ = int(200 + i * 8)
        d.rectangle((m * k - o, m * k - o * 0.3, W - m * k + o, H - m * k + o * 0.3), fill=(shade_, shade_, shade_ - 6, 255))
    lp = left.resize((int(pw * k), int(ph * k)), Image.LANCZOS)
    rp = right.resize((int(pw * k), int(ph * k)), Image.LANCZOS)
    out.alpha_composite(paper(lp, seed), (int(m * k), int(m * k)))
    out.alpha_composite(paper(rp, seed + 1), (int(m * k + pw * k), int(m * k)))
    a = np.asarray(out, np.float32)
    xx = (np.arange(W, dtype=np.float32) - W / 2) / k
    g = 0.34 * np.exp(-(np.abs(xx) / 9.0) ** 1.3) - 0.035 * np.exp(-((np.abs(xx) - 28) / 14) ** 2)
    yy = np.arange(H, dtype=np.float32)[:, None]
    inside = (yy > m * k) & (yy < H - m * k)
    f = 1 - np.where(inside, g[None, :], 0)
    a[..., :3] *= f[..., None]
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    if ribbon:
        rw = 6 * k
        x0 = W / 2 + 10 * k
        poly = [(W / 2 - rw * 0.2, m * k), (W / 2 + rw * 0.8, m * k), (x0 + rw + 30 * k, H - m * k + 18 * k),
                (x0 + 30 * k, H - m * k + 18 * k)]
        sh = Image.new("L", (W, H + int(30 * k)), 0)
        ImageDraw.Draw(sh).polygon([(px + 0.8 * k, py + 1.2 * k) for px, py in poly], fill=120)
        sh = sh.filter(ImageFilter.GaussianBlur(1.2 * k))
        canvas = Image.new("RGBA", (W, H + int(30 * k)), (0, 0, 0, 0))
        canvas.alpha_composite(out)
        layer = Image.new("RGBA", canvas.size, (10, 14, 30, 0))
        layer.putalpha(sh)
        canvas.alpha_composite(layer)
        rib = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(rib).polygon(poly, fill=ribbon)
        ImageDraw.Draw(rib).polygon([poly[-1], (poly[-1][0] + rw / 2, poly[-1][1] - 4 * k), poly[-2]], fill=(0, 0, 0, 0))
        canvas.alpha_composite(rib)
        out = canvas
    return out


# ------------------------------------------------------------------ boxes, tape, mailers

def kraft(w, h, seed=1, colour="#C29A6B", flutes=True):
    """Corrugated kraft board: fibres, specks and faint flute ridges."""
    out = MK.textured(Image.new("RGBA", (w, h), colour), MK.noise(w, h, seed, 1.3, fibres=True), 0.10)
    if flutes:
        a = np.asarray(out, np.float32)
        yy = np.arange(h, dtype=np.float32)[:, None]
        a[..., :3] *= (1 + 0.018 * np.sin(yy / max(h, w) * 2 * math.pi * 90))[..., None]
        out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    return out


def tape_strip(repeat_img, length_px, width_px, angle=0.0):
    """Branded tape laid flat: the repeat tiled to length, polypropylene gloss and slightly see-through edges."""
    r = repeat_img.resize((max(1, int(repeat_img.width * width_px / repeat_img.height)), width_px), Image.LANCZOS)
    strip = Image.new("RGBA", (length_px, width_px), (0, 0, 0, 0))
    for x in range(0, length_px, r.width):
        strip.paste(r, (x, 0))
    a = np.asarray(strip, np.float32)
    yy = np.linspace(0, 1, width_px, dtype=np.float32)[:, None]
    gloss = 0.16 * np.exp(-((yy - 0.3) / 0.12) ** 2) + 0.05
    a[..., :3] = np.clip(a[..., :3] + gloss[..., None] * 255, 0, 255)
    edge = np.minimum(yy, 1 - yy)
    a[..., 3] *= np.clip(0.82 + edge * 4, 0, 1)
    out = Image.fromarray(a.astype(np.uint8), "RGBA")
    return out.rotate(angle, resample=Image.BICUBIC, expand=True) if angle else out


def stick(base, item, x, y, angle=0.0, lift=0.25, k=4.0, shadow=0.35):
    """Stick a flat item (label, sticker, tape) onto a face texture with a hairline shadow."""
    it = item.rotate(angle, resample=Image.BICUBIC, expand=True) if angle else item
    a = it.getchannel("A")
    pad = int(3 * k)
    sh = Image.new("L", (it.width + 2 * pad, it.height + 2 * pad), 0)
    sh.paste(a, (pad, pad))
    sh = sh.filter(ImageFilter.GaussianBlur(max(0.6, lift * k))).point(lambda v: v * shadow)
    layer = Image.new("RGBA", base.size, (20, 16, 10, 0))
    full = Image.new("L", base.size, 0)
    full.paste(sh, (int(x - it.width / 2) - pad + int(lift * k * 0.6), int(y - it.height / 2) - pad + int(lift * k)))
    layer.putalpha(full)
    base.alpha_composite(layer)
    MK._paste(base, it, int(x - it.width / 2), int(y - it.height / 2))
    return base


def carton(top, front, side, dims, yaw=28.0, px_w=1200, pitch=18.0):
    """Closed box from a raised camera (pitch: degrees looking down at the top): top, front and the side facing
    the camera (right for yaw >= 0, left otherwise). Returns (image, ground polygon, px per mm at the front)."""
    W, D, H = dims
    dist = max(W, D, H) * 5.0
    cam = MK.Cam(yaw, dist=dist, eye=H + dist * math.tan(math.radians(pitch)))
    pts = [(x, y, z) for x in (-W / 2, W / 2) for y in (0, H) for z in (-D / 2, D / 2)]
    cv = MK.Canvas(cam, pts, px_w)
    cv.face([(-W / 2, H, -D / 2), (W / 2, H, -D / 2), (W / 2, H, D / 2), (-W / 2, H, D / 2)], top,
            MK.shade_img(top.width, top.height, left=-0.07, right=0.02, top=0.02, bottom=-0.02))
    cv.face([(-W / 2, H, D / 2), (W / 2, H, D / 2), (W / 2, 0, D / 2), (-W / 2, 0, D / 2)], front,
            MK.shade_img(front.width, front.height, left=-0.02, right=0.06, bottom=0.04, ao=0.12))
    sx = W / 2 if yaw >= 0 else -W / 2                 # the side that faces the camera
    if yaw >= 0:
        cv.face([(sx, H, D / 2), (sx, H, -D / 2), (sx, 0, -D / 2), (sx, 0, D / 2)], side,
                MK.shade_img(side.width, side.height, left=0.15, right=0.25, bottom=0.04, ao=0.14))
    else:
        cv.face([(sx, H, -D / 2), (sx, H, D / 2), (sx, 0, D / 2), (sx, 0, -D / 2)], side,
                MK.shade_img(side.width, side.height, left=-0.04, right=0.03, bottom=0.04, ao=0.14))
    hw = max(1.0, cv.s * 0.0006)
    cv.svg(f'<path d="{cv.path([(-sx, H, D / 2), (sx, H, D / 2), (sx, H, -D / 2)])}" fill="none" '
           f'stroke="#FFFFFF" stroke-opacity="0.4" stroke-width="{hw:.2f}" stroke-linejoin="round"/>'
           f'<path d="{cv.path([(sx, H, D / 2), (sx, 0, D / 2)])}" fill="none" stroke="#FFFFFF" '
           f'stroke-opacity="0.22" stroke-width="{hw:.2f}"/>')
    ground = [cv.p(-W / 2, 0, D / 2), cv.p(W / 2, 0, D / 2), cv.p(W / 2, 0, -D / 2), cv.p(-W / 2, 0, -D / 2)]
    return cv.img, ground, cv.scale_at(0, 0, D / 2)


def poly_mailer(art, k, seed=5, flap_mm=42.0):
    """Glossy poly mailer from above: soft wrinkles, specular glints, crinkled heat seals and the flap fold."""
    w, h = int(254 * k), int(330 * k)
    img = art.resize((w, h), Image.LANCZOS).convert("RGBA")
    hgt = 2.2 * fbm(w, h, seed, ((1.0, w / 2.5), (0.6, w / 6))) + 0.5 * fbm(w, h, seed + 1, ((1.0, w / 14),))
    xx = np.arange(w, dtype=np.float32)[None, :] / k
    yy = np.arange(h, dtype=np.float32)[:, None] / k
    edge = np.minimum(np.minimum(xx, 254 - xx), 330 - yy)
    hgt = hgt + (edge < 7) * 0.35 * fbm(w, h, seed + 2, ((1.0, 2.5),))
    hgt = hgt - 0.8 * np.exp(-((yy - flap_mm) / 1.2) ** 2)
    gy, gx = np.gradient(hgt * k)
    gx, gy = gx / k * k, gy / k * k
    n = (-gx * 0.9, -gy * 0.9, np.ones_like(gx))
    ln = np.sqrt(n[0] ** 2 + n[1] ** 2 + 1)
    n = (n[0] / ln, n[1] / ln, n[2] / ln)
    L = FLAT_LIGHT
    d = n[0] * L[0] + n[1] * L[1] + n[2] * L[2]
    dif = 0.9 + 0.55 * (d - L[2])
    spec = blinn(n, (0, 0, 1), 60, 0.35, L) + 0.05
    a = np.asarray(img, np.float32) / 255
    rgb = a[..., :3] * dif[..., None] + spec[..., None]
    rgb = np.where((edge < 6)[..., None], rgb * 0.96 + 0.03, rgb)
    out = to_image(rgb, a[..., 3] * np.ones_like(dif))
    return out


def ink_on(paper_img, ink, x, y, opacity=0.9):
    """Multiply an inked stamp impression (RGBA) onto paper at (x, y) = top-left."""
    base = np.asarray(paper_img.convert("RGBA"), np.float32)
    st = np.asarray(ink.convert("RGBA"), np.float32)
    h, w = st.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(base.shape[1], x + w), min(base.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return paper_img
    s = st[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[..., 3:4] / 255 * opacity
    reg = base[y0:y1, x0:x1, :3]
    base[y0:y1, x0:x1, :3] = reg * (1 - a + a * s[..., :3] / 255)
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGBA")


# ------------------------------------------------------------------ lanyard

def lanyard_clip(k):
    """Metal crimp, split ring and lobster hook (vector, chrome gradient), hook end at the bottom centre."""
    w, h = int(26 * k), int(46 * k)
    body = (f'<defs><linearGradient id="cr" x1="0" x2="1"><stop offset="0" stop-color="#8A929C"/>'
            f'<stop offset="0.35" stop-color="#F4F6F8"/><stop offset="0.6" stop-color="#A9B1BA"/>'
            f'<stop offset="1" stop-color="#6C747E"/></linearGradient></defs>'
            f'<g transform="scale({k:.4f})">'
            f'<rect x="3" y="0" width="20" height="9" rx="2" fill="url(#cr)"/>'
            f'<rect x="3" y="0" width="20" height="9" rx="2" fill="none" stroke="#5B636C" stroke-width="0.4"/>'
            f'<circle cx="13" cy="14" r="4.2" fill="none" stroke="url(#cr)" stroke-width="1.6"/>'
            f'<rect x="8.5" y="18" width="9" height="22" rx="4.5" fill="none" stroke="url(#cr)" stroke-width="2.2"/>'
            f'<rect x="11.4" y="24" width="3.2" height="7" rx="1" fill="url(#cr)"/></g>')
    return MK.svg_img(body, w, h)


def lanyard(length_mm, k, colour="#000080", print_svg=None, width_mm=20.0, seed=2):
    """Woven lanyard strap (vertical): brand print repeated along it, weave texture, rolled edges."""
    w, h = int(width_mm * k), int(length_mm * k)
    strap = Image.new("RGBA", (w, h), colour)
    if print_svg:
        art = MK.svg_img(print_svg, w, h)
        strap.alpha_composite(art)
    strap = MK.textured(strap, MK.noise(w, h, seed, 1.2, weave=True), 0.10)
    a = np.asarray(strap, np.float32)
    xx = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    a[..., :3] *= (1 - 0.22 * np.abs(xx) ** 6)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def punch_slot(card, k, w_mm=13.0, h_mm=3.2, top_mm=5.0):
    c = card.copy()
    m = Image.new("L", c.size, 0)
    cx = c.width / 2
    ImageDraw.Draw(m).rounded_rectangle((cx - w_mm * k / 2, top_mm * k, cx + w_mm * k / 2, (top_mm + h_mm) * k),
                                        h_mm * k / 2, fill=255)
    c.putalpha(ImageChops.subtract(c.getchannel("A"), m))
    return c


# ------------------------------------------------------------------ apparel

TEE_FRONT = ("M-100 0C-60 6 -40 8 0 8C40 8 60 6 100 0"            # back neckline (seen through the opening)
             "L240 45L420 170L318 322L284 292C286 420 287 560 292 742C200 750 -200 750 -292 742"
             "C-287 560 -286 420 -284 292L-318 322L-420 170L-240 45Z")
TEE_NECK_FRONT = "M-100 0C-90 70 -50 98 0 100C50 98 90 70 100 0"
TEE_NECK_BACK = "M-100 0C-60 16 -40 22 0 22C40 22 60 16 100 0"


def tshirt(print_img=None, print_box=None, side="front", colour="#141C5C", k=2.4, seed=7, label_img=None):
    """Flat-lay T-shirt (size L, mm). print_box: (x, y, w) of the print in shirt mm (x from the centre line, y from
    the high point of the shoulder); the print follows the folds and takes the fabric shading."""
    W, H = 860.0, 760.0
    w, h = int(W * k), int(H * k)
    tx = f'translate({W / 2 * k:.2f} {6 * k:.2f}) scale({k:.4f})'
    outline = TEE_FRONT if side == "front" else TEE_FRONT.replace("C-60 6 -40 8 0 8C40 8 60 6 100 0",
                                                                  "C-60 16 -40 22 0 22C40 22 60 16 100 0")
    sil = MK.svg_img(f'<path transform="{tx}" d="{outline}" fill="#fff"/>', w, h).getchannel("A")
    m = np.asarray(sil, np.float32) / 255
    base = rgbf(colour)
    xx = (np.arange(w, dtype=np.float32)[None, :] / k - W / 2)
    yy = (np.arange(h, dtype=np.float32)[:, None] / k - 6)
    # folds: soft height field (mm) plus a few long creases
    hgt = 5.0 * fbm(w, h, seed, ((1.0, 90 * k), (0.5, 35 * k)))
    rng = np.random.default_rng(seed)
    for _ in range(7):
        cx, cy = rng.uniform(-260, 260), rng.uniform(150, 700)
        ang = rng.uniform(-0.9, 0.9)
        dd = (xx - cx) * math.cos(ang) + (yy - cy) * math.sin(ang)
        along = -(xx - cx) * math.sin(ang) + (yy - cy) * math.cos(ang)
        hgt = hgt + rng.uniform(1.5, 3.5) * np.exp(-(dd / rng.uniform(6, 14)) ** 2) * np.exp(-(along / rng.uniform(80, 180)) ** 2)
    gy, gx = np.gradient(hgt, 1 / k)
    n = (-gx, -gy, np.ones_like(gx))
    ln = np.sqrt(n[0] ** 2 + n[1] ** 2 + 1)
    L = FLAT_LIGHT
    d = (n[0] * L[0] + n[1] * L[1] + L[2]) / ln
    dif = 1 + 0.9 * (d - L[2])
    dist = ndimage.distance_transform_edt(m > 0.5) / k
    dif = dif * (1 - 0.30 * np.clip(1 - dist / 9, 0, 1) ** 2)
    knit = 1 + 0.025 * fbm(w, h, seed + 3, ((1.0, 1.2),)) + 0.012 * np.sin(xx * 2 * math.pi / 1.1)
    rgb = np.ones((h, w, 3), np.float32) * base
    # neck: the inside of the back panel shows through the front opening, then the rib bands
    if side == "front":
        inside = MK.svg_img(f'<path transform="{tx}" d="{TEE_NECK_FRONT}C60 6 40 8 0 8C-40 8 -60 6 -100 0Z" fill="#fff"/>',
                            w, h).getchannel("A")
        ins = np.asarray(inside, np.float32) / 255
        rgb = rgb * (1 - 0.38 * ins)[..., None]
        if label_img is not None:
            lb = label_img.resize((int(46 * k), int(46 * k * label_img.height / label_img.width)), Image.LANCZOS)
            lab = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            lab.paste(lb, (int(w / 2 - lb.width / 2), int(14 * k)))
            la = np.asarray(lab, np.float32) / 255
            rgb = rgb * (1 - la[..., 3:4]) + la[..., :3] * la[..., 3:4]
        neck = TEE_NECK_FRONT
    else:
        neck = TEE_NECK_BACK
    rib = MK.svg_img(f'<path transform="{tx}" d="{neck}" fill="none" stroke="#fff" stroke-width="40" '
                     f'stroke-linecap="butt"/>', w, h).getchannel("A")
    rib = np.asarray(rib, np.float32) / 255
    rib_outer = MK.svg_img(f'<path transform="{tx}" d="{neck}" fill="none" stroke="#fff" stroke-width="40"/>'
                           f'<path transform="{tx}" d="{neck}" fill="none" stroke="#000" stroke-width="0.1"/>', w, h)
    ribs = 0.93 + 0.07 * np.sin(np.arctan2(yy - 40, xx) * 160)
    band = rib * (np.asarray(sil, np.float32) / 255)
    rgb = rgb * (1 - band * (1 - 0.9 * ribs))[..., None]
    if print_img is not None and print_box:
        px0, py0, pw = print_box
        pi = print_img.resize((int(pw * k), int(pw * k * print_img.height / print_img.width)), Image.LANCZOS)
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        layer.paste(pi, (int((W / 2 + px0 - pw / 2) * k), int((py0 + 6) * k)))
        la = np.asarray(layer, np.float32) / 255
        shift_x, shift_y = gx * 0.25 * k, gy * 0.25 * k
        gyy, gxx = np.mgrid[0:h, 0:w].astype(np.float32)
        la = sample(la, gxx + shift_x, gyy + shift_y)
        rgb = rgb * (1 - la[..., 3:4] * 0.97) + la[..., :3] * la[..., 3:4] * 0.97
    rgb = rgb * (dif * knit)[..., None]
    # stitching: sleeve hems, bottom hem, shoulder seams
    st = (f'<g transform="{tx}" fill="none" stroke="#fff" stroke-width="1.1" stroke-dasharray="3 2.4">'
          f'<path d="M402 176L306 322"/><path d="M394 170L298 316"/><path d="M-402 176L-306 322"/><path d="M-394 170L-298 316"/>'
          f'<path d="M-290 722C-200 730 200 730 290 722"/><path d="M-290 714C-200 722 200 722 290 714"/></g>')
    sti = np.asarray(MK.svg_img(st, w, h).getchannel("A"), np.float32) / 255
    rgb = rgb * (1 - 0.25 * sti)[..., None] + 0.06 * sti[..., None]
    return to_image(rgb, m)


def cap(art=None, colour="#141C5C", px_w=1000, ss=2, elev=14.0, art_w_mm=60.0, embroidery=True, seed=9):
    """Six-panel cap, front view from slightly above: ellipsoid crown with panel seams, eyelets and the top button,
    a pre-curved bill; the front art is embroidered (raised, thread texture) or printed."""
    A, B, C = 98.0, 112.0, 96.0              # crown half-width, height, half-depth (mm)
    bill_w, bill_d, droop = 92.0, 70.0, 24.0
    e = math.radians(elev)
    se, ce = math.sin(e), math.cos(e)
    W_mm = 2 * A + 24
    top_pad = 10.0
    H_mm = top_pad + B * ce + C * se + bill_d * se + droop * ce + 14
    k = px_w * ss / W_mm
    w, h = int(W_mm * k), int(H_mm * k)
    X = (np.arange(w, dtype=np.float32)[None, :] + 0.5) / k - W_mm / 2
    Y = (np.arange(h, dtype=np.float32)[:, None] + 0.5) / k - top_pad
    X2 = np.broadcast_to(X, (h, w))
    col = rgbf(colour)
    rgb = np.zeros((h, w, 3), np.float32)
    alpha = np.zeros((h, w), np.float32)
    # crown: front surface of the ellipsoid (x/A)^2 + (y/B)^2 + (z/C)^2 = 1 above the base (y >= 0)
    hh = B - Y / ce
    for _ in range(6):
        q = np.clip(1 - (X / A) ** 2 - (np.clip(hh, 0, B) / B) ** 2, 0, 1)
        hh = B - (Y - C * np.sqrt(q) * se) / ce
    q = 1 - (X / A) ** 2 - (hh / B) ** 2
    crown = (q >= 0) & (hh >= 0) & (hh <= B)
    z = C * np.sqrt(np.clip(q, 0, 1))
    n = (X / A ** 2, hh / B ** 2, z / C ** 2)
    ln = np.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2) + 1e-9
    n = (n[0] / ln, n[1] / ln, n[2] / ln)
    sh = shade(n, amb=0.46, kd=0.62, fill=0.1, edge=0.3) * (1 - 0.22 * smoothstep(0.16 * B, 0.0, hh))
    tex = 1 + 0.03 * fbm(w, h, seed, ((1.0, 1.3 * ss),)) + 0.012 * np.sin((X + Y) * 2 * math.pi / 0.9)
    c_rgb = col * (sh * tex)[..., None]
    phi = np.degrees(np.arctan2(X / A, z / C + 1e-6))
    for ang in (0.0, 60.0, -60.0):
        dist = np.abs(phi - ang) * (1 - (hh / B) ** 2 + 0.05)
        c_rgb = np.where((dist < 0.55)[..., None], c_rgb * 0.6, c_rgb)
        st = (np.abs(dist - 1.7) < 0.28) & (np.sin(hh * 2 * math.pi / 2.6) > 0)
        c_rgb = np.where(st[..., None], c_rgb * 0.8 + 0.03, c_rgb)
    for ang in (-78.0, 78.0):
        ex = A * math.sin(math.radians(ang)) * math.sqrt(1 - 0.72 ** 2)
        ey = (B - 0.72 * B) * ce + C * math.cos(math.radians(ang)) * math.sqrt(1 - 0.72 ** 2) * se
        r_ = np.sqrt(((X - ex) * 1.8) ** 2 + (Y - ey) ** 2)
        c_rgb = np.where((r_ < 2.8)[..., None], c_rgb * 0.75, c_rgb)
        c_rgb = np.where((r_ < 1.5)[..., None], c_rgb * 0.3, c_rgb)
    rgb[crown] = c_rgb[crown]
    alpha[crown] = 1
    if art is not None:
        aw = art_w_mm
        ah = aw * art.height / art.width
        h_top = B * 0.62
        a_arr = premul(art)
        su = (A * np.arcsin(np.clip(X / A, -1, 1)) + aw / 2) / aw * (a_arr.shape[1] - 1)
        sv = (h_top - hh) / ah * (a_arr.shape[0] - 1)
        smp = sample(a_arr, su, sv)
        inside = (su >= 0) & (su <= a_arr.shape[1] - 1) & (sv >= 0) & (sv <= a_arr.shape[0] - 1) & crown
        smp[~inside] = 0
        al = smp[..., 3]
        base_rgb = smp[..., :3] / np.maximum(al, 1e-3)[..., None]
        if embroidery:
            thread = 0.84 + 0.16 * np.sin((X * 0.7 + Y) * 2 * math.pi / 0.55)
            gy_, gx_ = np.gradient(ndimage.gaussian_filter(al, 1.0 * ss))
            emb = np.clip(1 + 2.2 * (-gx_ * 0.6 - gy_ * 0.9) * ss, 0.6, 1.4)
            a_rgb = base_rgb * (sh * thread * emb)[..., None]
            drop = ndimage.shift(ndimage.gaussian_filter(al, 0.8 * ss), (0.5 * k, 0.4 * k), order=1)
            rgb = rgb * (1 - 0.4 * drop * (1 - al))[..., None]
        else:
            a_rgb = base_rgb * sh[..., None]
        rgb = rgb * (1 - al[..., None]) + a_rgb * al[..., None]
    bt = np.sqrt(X ** 2 + ((Y - 0.4) * 1.6) ** 2)
    bm = bt < 6.0
    rgb[bm] = (col * (0.5 + 0.65 * np.clip(1 - (bt / 6.0) ** 2, 0, 1))[..., None])[bm]
    alpha[bm] = 1
    # bill: from the front of the base, forward and curving down at the sides
    sgrid = np.clip(X2 / bill_w, -1, 1)
    xa = np.clip(X2, -A * 0.999, A * 0.999)
    y_attach = B * ce + C * np.sqrt(1 - (xa / A) ** 2) * se
    reach = bill_d * (1 - 0.32 * sgrid ** 2)
    y_front = y_attach + reach * se + (droop * sgrid ** 2 + 2.0) * ce
    bill = (np.abs(X2) <= bill_w) & (Y >= y_attach - 0.8) & (Y <= y_front)
    dd = np.clip((Y - y_attach) / np.maximum(y_front - y_attach, 1e-3), 0, 1)
    b_sh = (0.95 - 0.3 * sgrid ** 2 - 0.08 * dd) * (1 + 0.025 * fbm(w, h, seed + 1, ((1.0, 1.3 * ss),)))
    b_rgb = col * b_sh[..., None]
    rows = np.zeros((h, w), bool)
    for i in range(1, 8):
        rows |= (np.abs(dd - i / 8.6) < 0.01) & (np.sin(X2 * 2 * math.pi / 2.4) > 0)
    b_rgb = np.where(rows[..., None], b_rgb * 0.8 + 0.03, b_rgb)
    rgb[bill] = b_rgb[bill]
    alpha[bill] = 1
    edge = (np.abs(X2) <= bill_w) & (Y > y_front) & (Y <= y_front + 3.2 * ce)
    rgb[edge] = (col * 0.55)
    alpha[edge] = 1
    img = to_image(rgb, alpha, ss)
    bot = img.getchannel("A").getbbox()[3]               # the cap rests on its bill tips and the back of the crown
    back = bot - 2 * C * se * 0.8 / H_mm * img.height
    xg = A * 0.85 / W_mm * img.width
    ground = [(img.width / 2 - xg, back), (img.width / 2 + xg, back), (img.width / 2 + xg, bot),
              (img.width / 2 - xg, bot)]
    return img, ground


# ------------------------------------------------------------------ signage

def storefront(sign_img, w=3000, h=2000, night=False, seed=21):
    """A hub shop front, straight on: painted wall, the lightbox signboard, a half-raised shutter over a lit
    interior with parcel shelves, tiled pillars and the pavement. sign_img: the 2400 x 800 mm signboard art."""
    k = w / 4300.0                                  # px per mm
    rng = np.random.default_rng(seed)
    wall = rgbf("#E6E0D3") if not night else rgbf("#363C5C")
    tex = 1 + 0.016 * fbm(w, h, seed, ((1.0, 1.5),)) + 0.022 * fbm(w, h, seed + 1, ((1.0, 18), (0.6, 60))) \
        + 0.03 * fbm(w, h, seed + 2, ((1.0, 400),))
    rgb = wall * tex[..., None]
    yy = np.arange(h, dtype=np.float32)[:, None] / k
    xx = np.arange(w, dtype=np.float32)[None, :] / k
    rgb = rgb * (1 - 0.14 * smoothstep(2150, 2650, yy))[..., None]          # grime above the pavement
    # pillars with tiles
    for x0 in (0, 3700):
        sel = (xx >= x0) & (xx < x0 + 600) & (yy < 2650)
        tile = ((np.abs(((xx - x0) % 200) - 100) > 98) | (np.abs((yy % 100) - 50) > 48.5))
        sheen = 1 + 0.05 * (1 - ((xx - x0) % 200) / 200) - 0.03 * ((yy % 100) / 100)
        col = (rgbf("#C9CDD3") if not night else rgbf("#2E3450")) * (sheen * (1 + 0.02 * fbm(w, h, seed + 5, ((1.0, 30),))))[..., None]
        col = np.where(tile[..., None], col * 0.78, col)
        rgb = np.where(sel[..., None], col, rgb)
    # shop opening: interior, shelves with parcels, then the shutter
    ox0, ox1, oy0, oy1 = 700, 3600, 1250, 2650
    op = (xx >= ox0) & (xx < ox1) & (yy >= oy0) & (yy < oy1)
    glow = np.exp(-(((xx - 2150) / 1500) ** 2 + ((yy - 2100) / 900) ** 2))
    inter = rgbf("#5A4632") * (0.55 + 0.6 * glow)[..., None] if not night else rgbf("#7A5A36") * (0.7 + 0.8 * glow)[..., None]
    rgb = np.where(op[..., None], inter, rgb)
    shelf_cols = ["#B98B5E", "#C9A06E", "#A57A4F", "#D6B38A", "#FFFFFF", "#B98B5E"]
    for sy in (1750, 2100, 2450):
        rgb = np.where((op & (yy >= sy) & (yy < sy + 25))[..., None], rgbf("#3B2E22"), rgb)
        x = ox0 + 40
        while x < ox1 - 200:
            bw_, bh_ = rng.uniform(160, 330), rng.uniform(120, 300)
            if x + bw_ > ox1 - 40:
                break
            c = rgbf(shelf_cols[rng.integers(len(shelf_cols))]) * (0.75 + 0.35 * glow.max())
            sel = op & (xx >= x) & (xx < x + bw_) & (yy >= sy - bh_) & (yy < sy)
            shade_ = 0.72 + 0.28 * ((xx - x) / bw_)
            lit = (0.6 + 0.5 * glow)[..., None]
            rgb = np.where(sel[..., None], c * shade_[..., None] * lit, rgb)
            topf = op & (xx >= x + 8) & (xx < x + bw_ + 8) & (yy >= sy - bh_ - 22) & (yy < sy - bh_)
            rgb = np.where(topf[..., None], c * 1.12 * lit, rgb)
            tape = (sel | topf) & (np.abs(xx - (x + bw_ / 2)) < 12)
            rgb = np.where(tape[..., None], rgbf("#1B2A8A") * 0.9, rgb)
            gap = op & (xx >= x + bw_) & (xx < x + bw_ + 14) & (yy >= sy - bh_) & (yy < sy)
            rgb = np.where(gap[..., None], rgb * 0.55, rgb)
            x += bw_ + rng.uniform(15, 60)
    for px_ in (ox0, (ox0 + ox1) / 2, ox1 - 40):                            # shelf uprights
        rgb = np.where((op & (xx >= px_) & (xx < px_ + 40) & (yy > 1700))[..., None], rgbf("#2E241B"), rgb)
    tube = op & (yy >= 1716) & (yy < 1734) & (xx > ox0 + 300) & (xx < ox1 - 300)
    rgb = np.where(tube[..., None], rgbf("#FFF6E0"), rgb)
    reveal = op & ((xx - ox0 < 70) | (ox1 - xx < 70))
    rgb = np.where(reveal[..., None], rgb * 0.7, rgb)
    shut = op & (yy < 1700)
    ribs = 0.86 + 0.14 * np.sin((yy - oy0) * 2 * math.pi / 75) ** 2
    s_col = (rgbf("#B8BEC6") if not night else rgbf("#5A6280")) * (ribs * (1 + 0.02 * fbm(w, h, seed + 7, ((1.0, 4),))))[..., None]
    rgb = np.where(shut[..., None], s_col, rgb)
    lip = op & (yy >= 1690) & (yy < 1715)
    rgb = np.where(lip[..., None], rgbf("#6B717A"), rgb)
    shadow_under = op & (yy >= 1715) & (yy < 1830)
    rgb = np.where(shadow_under[..., None], rgb * (0.6 + 0.4 * ((yy - 1715) / 115))[..., None], rgb)
    # pavement
    pv = yy >= 2650
    pav = rgbf("#B9B4AA") if not night else rgbf("#3A3E52")
    pt = ((np.abs((xx % 400) - 200) > 197) | (np.abs(((yy - 2650) % 300) - 150) > 147))
    pcol = pav * (1 + 0.04 * fbm(w, h, seed + 9, ((1.0, 3), (0.6, 60))))[..., None]
    pcol = np.where(pt[..., None], pcol * 0.82, pcol)
    rgb = np.where(pv[..., None], pcol * (0.85 + 0.15 * ((yy - 2650) / 350))[..., None], rgb)
    rgb = np.where(((yy >= 2650) & (yy < 2670))[..., None], rgb * 0.7, rgb)
    rgb = rgb * (1.04 - 0.08 * (yy / (h / k)) - 0.05 * ((xx / (w / k)) - 0.5) ** 2)[..., None]
    scene = to_image(rgb, np.ones((h, w), np.float32))
    # signboard: lightbox with an aluminium frame and a soft shadow on the wall
    sw_, sh_ = int(2480 * k), int(880 * k)
    sx, sy = int((w - sw_) / 2), int(240 * k)
    frame = Image.new("RGBA", (sw_, sh_), "#C3C9D1" if not night else "#8D95A8")
    fd = ImageDraw.Draw(frame)
    fd.rectangle((0, 0, sw_ - 1, int(6 * k)), fill="#E9EDF1")
    fd.rectangle((0, sh_ - int(10 * k), sw_ - 1, sh_ - 1), fill="#8C939C")
    art = sign_img.resize((int(2400 * k), int(800 * k)), Image.LANCZOS)
    if night:
        a = np.asarray(art, np.float32)
        a[..., :3] = np.clip(a[..., :3] * 1.12 + 18, 0, 255)
        art = Image.fromarray(a.astype(np.uint8), "RGBA")
    a = np.asarray(art, np.float32)
    ah_, aw_ = a.shape[:2]
    gx_ = np.linspace(0, 1, aw_, dtype=np.float32)[None, :]
    gy_ = np.linspace(0, 1, ah_, dtype=np.float32)[:, None]
    gloss = 0.07 * np.exp(-((gx_ * 0.8 + gy_ * 0.5 - 0.45) / 0.12) ** 2) + 0.03 * (1 - gy_)
    a[..., :3] = np.clip(a[..., :3] + gloss[..., None] * 255, 0, 255)
    art = Image.fromarray(a.astype(np.uint8), "RGBA")
    frame.alpha_composite(art, (int(40 * k), int(40 * k)))
    sh = Image.new("L", (w, h), 0)
    ImageDraw.Draw(sh).rectangle((sx + int(30 * k), sy + int(60 * k), sx + sw_ + int(30 * k), sy + sh_ + int(70 * k)), fill=150)
    sh = sh.filter(ImageFilter.GaussianBlur(30 * k))
    layer = Image.new("RGBA", (w, h), (20, 16, 10, 0))
    layer.putalpha(sh)
    scene.alpha_composite(layer)
    if night:
        gl = Image.new("L", (w, h), 0)
        ImageDraw.Draw(gl).rectangle((sx, sy, sx + sw_, sy + sh_), fill=255)
        gl = gl.filter(ImageFilter.GaussianBlur(90 * k)).point(lambda v: v * 0.55)
        glow_l = Image.new("RGBA", (w, h), (90, 150, 255, 0))
        glow_l.putalpha(gl)
        scene.alpha_composite(glow_l)
    scene.alpha_composite(frame, (sx, sy))
    # a few degrees off-axis, like a photo taken from the pavement
    quad = [(0, 0), (w, h * 0.045), (w, h * 0.955), (0, h)]
    warped = MK.warp(scene, quad, (w, h))
    return warped.crop((0, int(h * 0.045), w, int(h * 0.955))).resize((w, h), Image.LANCZOS)


def rollup(banner, px_w=900):
    """Roll-up banner stand (850 x 2000 mm) at three quarters: aluminium cassette base, feet, top rail."""
    W, H, Db, Hb = 850.0, 2000.0, 220.0, 75.0
    cam = MK.Cam(-18, dist=H * 3.2, eye=H * 0.62)
    pts = [(x, y, z) for x in (-W / 2 - 25, W / 2 + 25) for y in (0, Hb + H + 20) for z in (-Db / 2, Db / 2)]
    cv = MK.Canvas(cam, pts, px_w)
    ban = MK.textured(banner, MK.noise(banner.width, banner.height, 4, 1.0), 0.02)
    cv.face([(-W / 2, Hb + H, 0), (W / 2, Hb + H, 0), (W / 2, Hb, 0), (-W / 2, Hb, 0)], ban,
            MK.shade_img(banner.width, banner.height, left=-0.04, right=0.06, highlight=0.18))
    rail = Image.new("RGBA", (400, 8), "#D7DCE2")
    cv.face([(-W / 2 - 5, Hb + H + 18, 0), (W / 2 + 5, Hb + H + 18, 0), (W / 2 + 5, Hb + H, 0), (-W / 2 - 5, Hb + H, 0)], rail)
    metal = Image.new("RGBA", (600, 60), "#C7CDD4")
    md = ImageDraw.Draw(metal)
    for i in range(60):
        v = int(180 + 50 * math.sin(i / 60 * math.pi))
        md.line((0, i, 600, i), fill=(v, v + 4, v + 10, 255))
    side = Image.new("RGBA", (200, 60), "#9AA3AD")
    top = Image.new("RGBA", (600, 160), "#B7BEC7")
    bx0, bx1 = -W / 2 - 25, W / 2 + 25
    cv.face([(bx0, Hb, -Db / 2), (bx1, Hb, -Db / 2), (bx1, Hb, Db / 2), (bx0, Hb, Db / 2)], top)
    cv.face([(bx0, Hb, Db / 2), (bx1, Hb, Db / 2), (bx1, 0, Db / 2), (bx0, 0, Db / 2)], metal,
            MK.shade_img(600, 60, left=-0.05, right=0.08))
    cv.face([(bx0, Hb, -Db / 2), (bx0, Hb, Db / 2), (bx0, 0, Db / 2), (bx0, 0, -Db / 2)], side)
    ground = [cv.p(bx0, 0, Db / 2), cv.p(bx1, 0, Db / 2), cv.p(bx1, 0, -Db / 2), cv.p(bx0, 0, -Db / 2)]
    return cv.img, ground
