"""Logo motion library: sign (symbol), wordmark and combined lockup animations, plus app loaders.

motion/<group>/<name>/parcelfly-<name>-<colourway>.{svg,json,mp4,webm,gif,webp}
  .svg   CSS-animated, transparent, honours prefers-reduced-motion (web)
  .json  Lottie (lottie-web, lottie-react-native / Expo, Android, iOS)
  .mp4   H.264 on the brand background (social media, presentations, video)
  .webm  VP9 with transparency (video editors, web overlays)
  .gif   on the brand background (email, chat)
  .webp  animated with transparency (stickers, chat, web)

    .venv/bin/python source/build/build_motion.py [--only name,name] [--preview]
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pfbrand import ROOT, logo as L, symbol as S  # noqa: E402
from pfbrand import motion as M  # noqa: E402
from pfbrand.brand import CYAN, MINT, NAVY, WHITE  # noqa: E402
from pfbrand.svg import png_image  # noqa: E402

OUT = ROOT / "motion"
FPS = 30
BG = {"color": "#FFFFFF", "ondark": NAVY}
WAYS = ["color", "ondark"]


# ================================================================== building blocks

def lockup(kind, way, lang="en", tagline=None):
    if kind == "symbol":
        frag, bb = L.symbol_only(way)
    elif kind == "horizontal":
        frag, bb = L.horizontal(way, lang=lang, tagline=tagline)
    elif kind == "stacked":
        frag, bb = L.stacked(way, lang=lang, tagline=tagline)
    else:
        frag, bb = L.wordmark_only(way, lang)
    return M.parse_lockup(frag), bb


SYM = ["feather-top", "feather-mid", "feather-bot", "parcel", "facet-top", "facet-bot"]


def build_symbol(A, parts, t=0.0, u=None):
    """Feathers fly in (bottom first), the parcel lands, the facets snap into the arrow."""
    u = u or parts["parcel"].base[2]
    for pid, dt in [("feather-bot", 0.0), ("feather-mid", 0.08), ("feather-top", 0.16)]:
        A.seg(pid, "tx", t + dt, t + dt + 0.55, -260 * u, 0, M.out_cubic)
        A.seg(pid, "o", t + dt, t + dt + 0.22, 0, 1, M.linear)
    A.seg("parcel", "s", t + 0.30, t + 0.80, 0.55, 1, M.out_back)
    A.seg("parcel", "o", t + 0.30, t + 0.45, 0, 1, M.linear)
    for pid, dt in [("facet-bot", 0.46), ("facet-top", 0.52)]:
        A.seg(pid, "tx", t + dt, t + dt + 0.45, -90 * u, 0, M.out_cubic)
        A.seg(pid, "o", t + dt, t + dt + 0.18, 0, 1, M.linear)


def fly_in(A, parts, ids, t=0.0, dist=1500.0, dur=0.85, speed="speed"):
    u = parts["parcel"].base[2]
    for pid in ids + ([speed] if speed else []):
        A.seg(pid, "tx", t, t + dur, -dist * u, 0, M.soft_back)
    if speed:
        A.seg(speed, "sx", t, t + 0.55 * dur / 0.85, 0.3, 1.4, M.out_cubic)
        A.seg(speed, "sx", t + 0.6 * dur / 0.85, t + 1.15 * dur / 0.85, 1.4, 0.0, M.in_cubic)
        A.seg(speed, "o", t, t + 0.15, 0, 0.85, M.linear)
        A.seg(speed, "o", t + 0.7 * dur / 0.85, t + 1.15 * dur / 0.85, 0.85, 0, M.linear)


def wipe(A, pid, part, t0, t1, ease=M.out_cubic, x_from=None):
    x0 = x_from if x_from is not None else part.bbox[0] - 20
    x1 = part.bbox[2] + 20
    A.seg(pid, "clip", t0, t1, (x0, x0), (x0, x1), ease)


def bar_part(pid, part, colour, cap=168.0):
    """A speed bar that runs just ahead of a wipe across `part` (its left end sits on the wipe edge)."""
    x0, y0, x1, y1 = part.bbox
    x0 -= 20
    h = cap * 0.09
    w = (x1 - x0) * 0.22
    y = y0 + (y1 - y0) * 0.52 - h / 2
    r = h / 2
    d = (f"M{x0 + r} {y}L{x0 + w - r} {y}A{r} {r} 0 0 1 {x0 + w - r} {y + h}L{x0 + r} {y + h}"
         f"A{r} {r} 0 0 1 {x0 + r} {y}Z")
    return M.Part(pid, [(d, colour)])


def ride_bar(A, pid, part, t0, t1):
    span = part.bbox[2] - part.bbox[0] + 40
    A.seg(pid, "tx", t0, t1, 0, span, M.out_cubic)
    A.seg(pid, "sx", t0, t1, 1.0, 0.35, M.out_cubic)
    A.seg(pid, "o", t0, t0 + 0.1, 0, 1, M.linear)
    A.seg(pid, "o", t1 - 0.3, t1, 1, 0, M.linear)


def emerge(A, pid, part, nose_x, t0, t1, frac=0.45):
    """Wordmark slides out from behind the arrow's nose (static window starts at the nose)."""
    part.window = (nose_x + 4, part.bbox[2] + 400)
    A.seg(pid, "tx", t0, t1, -(part.bbox[2] - part.bbox[0]) * frac, 0, M.out_cubic)
    A.seg(pid, "o", t0, t0 + 0.15, 0, 1, M.linear)


def letters(A, parts_list, wm, t0, rise=60.0, step=0.05, dur=0.5):
    """Per-letter rise: copies of the one wordmark path, each seen through a static window."""
    wins = M.letter_windows(wm)
    out = []
    for i, win in enumerate(wins):
        p = M.Part(f"letter{i}", wm.elems, wm.base, window=win)
        out.append(p)
    return out, [(f"letter{i}", t0 + i * step) for i in range(len(wins))], rise, dur


def apply_letters(A, starts, rise, dur):
    for pid, t in starts:
        A.seg(pid, "ty", t, t + dur, rise, 0, M.out_cubic)
        A.seg(pid, "o", t, t + dur * 0.5, 0, 1, M.linear)


def wm_key(parts):
    return "wordmark" if "wordmark" in parts else "wordmark-bn"


# ================================================================== catalogue
# each factory returns (Anim, video canvas (w, h, fill), tight width)


def sign_build(way):
    parts, bb = lockup("symbol", way)
    A = M.Anim("sign-build", "Parcel Fly sign: build", [parts[i] for i in SYM], 1.75, group="sign",
               note="Feathers fly in, the parcel lands, the facets snap into the arrow.")
    build_symbol(A, parts)
    return A, (1080, 1080, 0.58), 1000


def sign_unfold(way):
    parts, bb = lockup("symbol", way)
    order = ["feather-bot", "feather-mid", "feather-top", "facet-bot", "facet-top", "parcel"]
    A = M.Anim("sign-unfold", "Parcel Fly sign: unfold", [parts[i] for i in order], 1.8, group="sign",
               note="The parcel spins in, the arrow unfolds from it, then the wings grow out.")
    A.seg("parcel", "s", 0.0, 0.55, 0.0, 1.0, M.out_back)
    A.seg("parcel", "r", 0.0, 0.55, -90, 0, M.out_cubic)
    A.seg("parcel", "o", 0.0, 0.12, 0, 1, M.linear)
    for pid in ["facet-top", "facet-bot"]:
        A.seg(pid, "tx", 0.42, 0.92, -170, 0, M.out_cubic)
        A.seg(pid, "o", 0.42, 0.55, 0, 1, M.linear)
    for pid, t in [("feather-mid", 0.72), ("feather-top", 0.82), ("feather-bot", 0.92)]:
        A.seg(pid, "tx", t, t + 0.55, 300, 0, M.out_cubic)
        A.seg(pid, "o", t, t + 0.2, 0, 1, M.linear)
    return A, (1080, 1080, 0.58), 1000


def sign_fly_in(way):
    parts, bb = lockup("symbol", way)
    sp = M.speed_lines_part("speed", parts["parcel"], way)
    A = M.Anim("sign-fly-in", "Parcel Fly sign: fly in", [sp] + [parts[i] for i in SYM], 1.4, group="sign",
               extent=bb, note="The sign flies in on speed lines and settles with a small overshoot.")
    fly_in(A, parts, SYM)
    return A, (1080, 1080, 0.58), 1000


def sign_draw(way):
    parts, bb = lockup("symbol", way)
    for p in parts.values():
        p.stroke_w = 5.0
    A = M.Anim("sign-draw", "Parcel Fly sign: draw", [parts[i] for i in SYM], 2.0, group="sign",
               note="Outlines draw on, then the colour fills in.")
    for i, pid in enumerate(SYM):
        t = 0.08 * i
        A.seg(pid, "draw", t, t + 0.95, 0.0, 1.0, M.in_out_cubic)
        A.seg(pid, "fo", 1.0 + 0.05 * i, 1.55 + 0.05 * i, 0.0, 1.0, M.out_cubic)
    return A, (1080, 1080, 0.58), 1000


def sign_fly_out(way):
    parts, bb = lockup("symbol", way)
    sp = M.speed_lines_part("speed", parts["parcel"], way)
    A = M.Anim("sign-fly-out", "Parcel Fly sign: fly out", [sp] + [parts[i] for i in SYM], 1.2, group="sign",
               extent=bb, note="Outro: the sign is dispatched off to the right (also a 'sent' confirmation).")
    for pid in SYM + ["speed"]:
        A.seg(pid, "tx", 0.25, 1.05, 0, 1700, M.in_cubic)
    A.seg("speed", "sx", 0.25, 0.8, 0.0, 1.6, M.out_cubic)
    A.seg("speed", "o", 0.25, 0.45, 0.0, 0.85, M.linear)
    A.seg("speed", "o", 0.85, 1.05, 0.85, 0.0, M.linear)
    return A, (1080, 1080, 0.58), 1000


def sign_loop(way):
    parts, bb = lockup("symbol", way)
    A = M.Anim("sign-loop", "Parcel Fly sign: idle loop", [parts[i] for i in SYM], 1.6, loop=True, group="sign",
               note="Seamless idle loop: the wings flutter and the arrow nudges forward.")
    for pid, dt in [("feather-bot", 0.0), ("feather-mid", 0.07), ("feather-top", 0.14)]:
        A.seg(pid, "ty", dt, dt + 0.32, 0, -9, M.in_out_sine)
        A.seg(pid, "ty", dt + 0.32, dt + 0.64, -9, 0, M.in_out_sine)
    for pid, dt in [("facet-top", 0.0), ("facet-bot", 0.05)]:
        A.seg(pid, "tx", 0.5 + dt, 0.78 + dt, 0, 18, M.out_cubic)
        A.seg(pid, "tx", 0.78 + dt, 1.2 + dt, 18, 0, M.in_out_cubic)
    A.seg("parcel", "s", 0.45, 0.75, 1.0, 1.035, M.in_out_sine)
    A.seg("parcel", "s", 0.75, 1.1, 1.035, 1.0, M.in_out_sine)
    return A, (1080, 1080, 0.58), 1000


def loader_dispatch(way):
    parts, bb = lockup("symbol", way)
    ghosts = [M.Part(f"ghost-{p}", parts[p].elems, parts[p].base) for p in ["facet-top", "facet-bot"]]
    keep = [parts["parcel"], parts["facet-top"], parts["facet-bot"]]
    x0 = parts["parcel"].bbox[0]
    ext = (x0, 0, S.WIDTH + 140, S.HEIGHT)
    A = M.Anim("loader-dispatch", "Parcel Fly loader: dispatch", ghosts + keep, 1.1, loop=True, group="loader",
               extent=ext, note="Loading loop: arrows leave the parcel one after another.")
    for g in ghosts:
        A.seg(g.id, "tx", 0.0, 0.9, 0, 140, M.out_cubic)
        A.seg(g.id, "o", 0.0, 0.9, 0.75, 0.0, M.linear)
    for pid, dt in [("facet-top", 0.0), ("facet-bot", 0.04)]:
        A.seg(pid, "tx", dt, dt + 0.22, 0, 14, M.out_cubic)
        A.seg(pid, "tx", dt + 0.22, dt + 0.6, 14, 0, M.in_out_cubic)
    A.seg("parcel", "s", 0.0, 0.2, 1.0, 0.95, M.out_cubic)
    A.seg("parcel", "s", 0.2, 0.55, 0.95, 1.0, M.in_out_cubic)
    return A, (512, 512, 0.6), 400


def loader_wings(way):
    parts, bb = lockup("symbol", way)
    A = M.Anim("loader-wings", "Parcel Fly loader: wings", [parts[i] for i in SYM], 1.2, loop=True, group="loader",
               note="Loading loop: a wave runs through the three feathers.")
    for pid, dt in [("feather-bot", 0.0), ("feather-mid", 0.2), ("feather-top", 0.4)]:
        A.seg(pid, "o", dt, dt + 0.3, 1.0, 0.25, M.in_out_sine)
        A.seg(pid, "o", dt + 0.3, dt + 0.6, 0.25, 1.0, M.in_out_sine)
    return A, (512, 512, 0.62), 400


def wordmark_wipe(way, lang="en"):
    parts, bb = lockup("wordmark", way, lang)
    key = wm_key(parts)
    wm = parts[key]
    bar = bar_part("bar", wm, CYAN if way == "color" else MINT, 168.0)
    name = "wordmark-wipe" + ("-bn" if lang == "bn" else "")
    bar.origin = (bar.bbox[0], (bar.bbox[1] + bar.bbox[3]) / 2)
    A = M.Anim(name, f"Parcel Fly {'Bangla ' if lang == 'bn' else ''}wordmark: wipe", [bar, wm], 1.3, group="wordmark",
               extent=bb, note="A speed bar sweeps across and reveals the wordmark.")
    wipe(A, key, wm, 0.1, 0.95)
    ride_bar(A, "bar", wm, 0.1, 0.95)
    return A, (1920, 1080, 0.56), 1200


def wordmark_rise(way):
    parts, bb = lockup("wordmark", way)
    wm = parts["wordmark"]
    lp, starts, rise, dur = letters(None, None, wm, 0.05)
    A = M.Anim("wordmark-rise", "Parcel Fly wordmark: letters rise", lp, 1.2, group="wordmark", extent=bb,
               note="Letters rise into place one after another (the wordmark stays one shape).")
    apply_letters(A, starts, rise * 1.2, dur)
    return A, (1920, 1080, 0.56), 1200


def horizontal_build(way, lang="en"):
    parts, bb = lockup("horizontal", way, lang)
    key = wm_key(parts)
    order = [parts[i] for i in SYM] + [parts[key]]
    name = "horizontal-build" + ("-bn" if lang == "bn" else "")
    A = M.Anim(name, f"Parcel Fly {'Bangla ' if lang == 'bn' else ''}horizontal logo: build", order, 2.0,
               group="combined", extent=bb, note="The sign builds, then the name slides out from behind the arrow.")
    build_symbol(A, parts)
    emerge(A, key, parts[key], parts["facet-top"].bbox[2], 0.95, 1.6)
    return A, (1920, 1080, 0.62), 1200


def horizontal_fly_in(way):
    parts, bb = lockup("horizontal", way)
    sp = M.speed_lines_part("speed", parts["parcel"], way)
    bar = bar_part("bar", parts["wordmark"], CYAN if way == "color" else MINT)
    bar.origin = (bar.bbox[0], (bar.bbox[1] + bar.bbox[3]) / 2)
    A = M.Anim("horizontal-fly-in", "Parcel Fly horizontal logo: fly in", [sp] + [parts[i] for i in SYM]
               + [bar, parts["wordmark"]], 1.7, group="combined", extent=bb,
               note="The sign flies in on speed lines and a speed bar reveals the name.")
    fly_in(A, parts, SYM, 0.0, 2200)
    wipe(A, "wordmark", parts["wordmark"], 0.65, 1.4)
    ride_bar(A, "bar", parts["wordmark"], 0.65, 1.4)
    return A, (1920, 1080, 0.62), 1200


def horizontal_tagline_build(way):
    parts, bb = lockup("horizontal", way, tagline="en")
    order = [parts[i] for i in SYM] + [parts["wordmark"], parts["tagline"]]
    A = M.Anim("horizontal-tagline-build", "Parcel Fly horizontal logo with tagline: build", order, 2.4,
               group="combined", extent=bb, note="Build, name, then the tagline settles in.")
    build_symbol(A, parts)
    emerge(A, "wordmark", parts["wordmark"], parts["facet-top"].bbox[2], 0.95, 1.6)
    A.seg("tagline", "ty", 1.55, 2.1, 30, 0, M.out_cubic)
    A.seg("tagline", "o", 1.55, 1.9, 0, 1, M.linear)
    return A, (1920, 1080, 0.62), 1200


def stacked_build(way, lang="en"):
    parts, bb = lockup("stacked", way, lang, tagline=lang)
    key = wm_key(parts)
    tkey = "tagline" if "tagline" in parts else "tagline-bn"
    name = "stacked-build" + ("-bn" if lang == "bn" else "")
    if lang == "en":
        lp, starts, rise, dur = letters(None, None, parts[key], 1.0)
        order = [parts[i] for i in SYM] + lp + [parts[tkey]]
    else:
        order = [parts[i] for i in SYM] + [parts[key], parts[tkey]]
    A = M.Anim(name, f"Parcel Fly {'Bangla ' if lang == 'bn' else ''}stacked logo: build", order, 2.6,
               group="combined", extent=bb, note="The sign builds, the name rises in, the tagline settles.")
    build_symbol(A, parts)
    if lang == "en":
        apply_letters(A, starts, rise * 1.4, dur)
    else:
        wipe(A, key, parts[key], 0.95, 1.7)
    A.seg(tkey, "ty", 1.75, 2.3, 30, 0, M.out_cubic)
    A.seg(tkey, "o", 1.75, 2.1, 0, 1, M.linear)
    return A, (1080, 1080, 0.6), 900


def stacked_drop(way):
    parts, bb = lockup("stacked", way, tagline="en")
    order = [parts[i] for i in SYM] + [parts["wordmark"], parts["tagline"]]
    A = M.Anim("stacked-drop", "Parcel Fly stacked logo: drop", order, 2.4, group="combined", extent=bb,
               note="The sign is delivered from above and lands with a bounce; the name and tagline follow.")
    for pid in SYM:
        A.seg(pid, "ty", 0.0, 1.0, -(bb[3] - bb[1]) * 1.5, 0, M.out_bounce)
        A.seg(pid, "o", 0.0, 0.1, 0, 1, M.linear)
    wipe(A, "wordmark", parts["wordmark"], 0.95, 1.6)
    A.seg("tagline", "ty", 1.5, 2.05, 30, 0, M.out_cubic)
    A.seg("tagline", "o", 1.5, 1.85, 0, 1, M.linear)
    return A, (1080, 1080, 0.6), 900


def outro_horizontal(way):
    parts, bb = lockup("horizontal", way)
    sp = M.speed_lines_part("speed", parts["parcel"], way)
    order = [sp] + [parts[i] for i in SYM] + [parts["wordmark"]]
    A = M.Anim("horizontal-outro", "Parcel Fly horizontal logo: outro", order, 1.4, group="combined", extent=bb,
               note="End card exit: the name slides back into the arrow and the sign flies away.")
    wm = parts["wordmark"]
    nose = parts["facet-top"].bbox[2]
    wm.window = (nose + 4, wm.bbox[2] + 400)
    A.seg("wordmark", "tx", 0.15, 0.6, 0, -(wm.bbox[2] - wm.bbox[0]) * 0.45, M.in_cubic)
    A.seg("wordmark", "o", 0.45, 0.6, 1, 0, M.linear)
    dist = (bb[2] - bb[0]) * 1.6
    for pid in SYM + ["speed"]:
        A.seg(pid, "tx", 0.55, 1.3, 0, dist, M.in_cubic)
    A.seg("speed", "sx", 0.55, 1.05, 0.0, 1.6, M.out_cubic)
    A.seg("speed", "o", 0.55, 0.75, 0.0, 0.85, M.linear)
    A.seg("speed", "o", 1.1, 1.3, 0.85, 0.0, M.linear)
    return A, (1920, 1080, 0.62), 1200


USE = {
    "sign-build": "Intros, app launch", "sign-unfold": "Intros, reveals", "sign-fly-in": "Intros, transitions",
    "sign-draw": "Slow reveals, presentations", "sign-fly-out": "Outros, 'parcel sent' confirmation",
    "sign-loop": "Idle states, screens", "loader-dispatch": "Loading, sending", "loader-wings": "Loading",
    "wordmark-wipe": "Titles, lower thirds", "wordmark-wipe-bn": "Bangla titles", "wordmark-rise": "Titles",
    "horizontal-build": "Video intros, web headers", "horizontal-build-bn": "Bangla video intros",
    "horizontal-fly-in": "Video intros", "horizontal-tagline-build": "Ads, end cards",
    "stacked-build": "Social video, splash screens", "stacked-build-bn": "Bangla social video",
    "stacked-drop": "Delivery-themed intros", "horizontal-outro": "Video end cards",
}

CATALOGUE = {
    "sign-build": sign_build, "sign-unfold": sign_unfold, "sign-fly-in": sign_fly_in, "sign-draw": sign_draw,
    "sign-fly-out": sign_fly_out, "sign-loop": sign_loop, "loader-dispatch": loader_dispatch,
    "loader-wings": loader_wings,
    "wordmark-wipe": lambda w: wordmark_wipe(w, "en"), "wordmark-wipe-bn": lambda w: wordmark_wipe(w, "bn"),
    "wordmark-rise": wordmark_rise,
    "horizontal-build": lambda w: horizontal_build(w, "en"), "horizontal-build-bn": lambda w: horizontal_build(w, "bn"),
    "horizontal-fly-in": horizontal_fly_in, "horizontal-tagline-build": horizontal_tagline_build,
    "stacked-build": lambda w: stacked_build(w, "en"), "stacked-build-bn": lambda w: stacked_build(w, "bn"),
    "stacked-drop": stacked_drop, "horizontal-outro": outro_horizontal,
}


# ================================================================== export


def video_times(A, lead=0.25, hold=1.4, fps=FPS):
    if A.loop:
        n = int(round(A.duration * 3 * fps))
        return [(i / fps) % A.duration for i in range(n)]
    pre = [0.0] * int(lead * fps)
    body = [i / fps for i in range(int(round(A.duration * fps)) + 1)]
    post = [A.duration] * int(hold * fps)
    return pre + body + post


def ffmpeg(args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


VIDEO_SPEC = {}


def make(name, way):
    A, spec, tight_w = CATALOGUE[name](way)
    A.name = name
    VIDEO_SPEC[name] = spec
    return A, spec, tight_w


def webp_job(job):
    name, way = job
    A, spec, tight_w = make(name, way)
    base = OUT / A.group / name / f"parcelfly-{name}-{way}"
    write_webp(A, base)
    return f"{name}-{way}"


def export(job):
    name, way = job
    A, (vw, vh, fill), tight_w = make(name, way)
    folder = OUT / A.group / name
    folder.mkdir(parents=True, exist_ok=True)
    base = folder / f"parcelfly-{name}-{way}"
    tight = M.Fit(A.extent, tight_w, None, pad=0.22 if A.group != "loader" else 0.12)
    base.with_suffix(".svg").write_text(M.css_svg(A, tight, FPS), encoding="utf-8")
    base.with_suffix(".json").write_text(M.lottie_json(A, tight, FPS), encoding="utf-8")
    fit = M.Fit(A.extent, vw, vh, fill)
    tmp = Path(tempfile.mkdtemp(prefix=f"pfm-{name}-{way}-"))
    try:
        from PIL import Image
        bg = Image.new("RGBA", (vw, vh), BG[way])
        last_key, last_t, last_f = None, None, None
        for i, t in enumerate(video_times(A)):
            key = round(t, 5)
            if key == last_key:              # identical frame (lead-in, hold): copy the files, keep nothing in RAM
                shutil.copyfile(last_t, tmp / f"t{i:04d}.png")
                shutil.copyfile(last_f, tmp / f"f{i:04d}.png")
                continue
            im = png_image(M.frame_svg(A, t, fit), vw, vw, vh)
            im.save(tmp / f"t{i:04d}.png")
            comp = bg.copy()
            comp.alpha_composite(im)
            comp.convert("RGB").save(tmp / f"f{i:04d}.png")
            del im, comp
            last_key, last_t, last_f = key, tmp / f"t{i:04d}.png", tmp / f"f{i:04d}.png"
        ffmpeg(["-framerate", str(FPS), "-i", str(tmp / "f%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                "-preset", "medium", "-movflags", "+faststart", str(base.with_suffix(".mp4"))])
        ffmpeg(["-framerate", str(FPS), "-i", str(tmp / "t%04d.png"), "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0",
                "-crf", "30", "-row-mt", "1", "-deadline", "good", "-cpu-used", "4", str(base.with_suffix(".webm"))])
        gw = 480 if A.group == "loader" else 640
        ffmpeg(["-framerate", str(FPS), "-i", str(tmp / "f%04d.png"), "-vf",
                f"fps=25,scale={gw}:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
                "-loop", "0", str(base.with_suffix(".gif"))])
        write_webp(A, base)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return f"{name}-{way}"


def write_webp(A, base):
    """Animated WebP with transparency (Pillow: reliable frame timing), 25 fps."""
    from PIL import Image
    ww = 512 if A.group in ("sign", "loader") else 800
    vw, vh, fill = VIDEO_SPEC[A.name]
    fit = M.Fit(A.extent, ww, ww * vh / vw, fill)
    fps = 25
    times = video_times(A, fps=fps)
    frames, durs, last_key = [], [], None
    for t in times:
        key = round(t, 5)
        if key == last_key and frames:
            durs[-1] += round(1000 / fps)
            continue
        frames.append(png_image(M.frame_svg(A, t, fit), int(fit.w), fit.w, fit.h))
        durs.append(round(1000 / fps))
        last_key = key
    frames[0].save(base.with_suffix(".webp"), save_all=True, append_images=frames[1:], duration=durs, loop=0,
                   quality=82, method=5, lossless=False, allow_mixed=True)


def preview(names):
    """Contact sheet: frames from the renderer (top) and from rlottie playing the Lottie export (bottom)."""
    from PIL import Image
    import rlottie_python as rl
    rows = []
    for name in names:
        A, (vw, vh, fill), tight_w = CATALOGUE[name]("color")
        fit = M.Fit(A.extent, 600, None, pad=0.22 if A.group != "loader" else 0.12)
        ts = [A.duration * f for f in (0.15, 0.3, 0.5, 0.7, 1.0)]
        top = [png_image(M.frame_svg(A, t, fit, "#FFFFFF"), 300, fit.w, fit.h) for t in ts]
        anim = rl.LottieAnimation.from_data(M.lottie_json(A, fit, FPS))
        bot = []
        for t in ts:
            fr = int(round(t * FPS))
            im = anim.render_pillow_frame(frame_num=fr, width=int(fit.w), height=int(fit.h)).convert("RGBA")
            b = Image.new("RGBA", im.size, "#F3F8FC")
            b.alpha_composite(im)
            bot.append(b.resize((300, int(300 * fit.h / fit.w))))
        rows.append((top, bot))
    h = sum(r[0][0].height + r[1][0].height + 20 for r in rows)
    sheet = Image.new("RGBA", (5 * 310, h), "#888")
    y = 0
    for top, bot in rows:
        for j, im in enumerate(top):
            sheet.alpha_composite(im, (j * 310, y))
        y += top[0].height + 4
        for j, im in enumerate(bot):
            sheet.alpha_composite(im, (j * 310, y))
        y += bot[0].height + 16
    sheet.save("/tmp/pf-motion-preview.png")
    print("preview: /tmp/pf-motion-preview.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--webp-only", action="store_true")
    ap.add_argument("--skip-existing", action="store_true", help="resume: skip jobs whose six files all exist")
    a = ap.parse_args()
    names = [n for n in CATALOGUE if not a.only or n in a.only.split(",")]
    if a.preview:
        preview(names)
        return
    jobs = [(n, w) for n in names for w in WAYS]
    if a.skip_existing:
        def complete(job):
            A = CATALOGUE[job[0]](job[1])[0]
            base = OUT / A.group / job[0] / f"parcelfly-{job[0]}-{job[1]}"
            return all(base.with_suffix(e).exists() for e in (".svg", ".json", ".mp4", ".webm", ".gif", ".webp"))
        jobs = [j for j in jobs if not complete(j)]
        print(f"{len(jobs)} jobs to do", flush=True)
    if a.webp_only:
        with ProcessPoolExecutor(max_workers=min(3, os.cpu_count() or 2)) as ex:
            for r in ex.map(webp_job, jobs):
                print("  webp", r, flush=True)
        return
    # 3 workers: each renders 1080p frames and runs ffmpeg; more than that exhausts a 7 GB machine
    with ProcessPoolExecutor(max_workers=min(3, os.cpu_count() or 2)) as ex:
        for r in ex.map(export, jobs):
            print("  done", r, flush=True)
    n = sum(1 for _ in OUT.rglob("*") if _.is_file())
    print(f"motion: {len(jobs)} animations x formats, {n} files")


if __name__ == "__main__":
    main()
