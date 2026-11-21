"""Fetch and pre-process the map data used by the hub maps (run rarely; results are committed in source/geo/).

    .venv/bin/python source/build/fetch_geo.py [--cache /tmp/pf-geo-dl] [--refresh]

Sources and licences
  * OpenStreetMap (Overpass API, Nominatim): rivers, water bodies, roads, railways and hub area locations for the
    Dhaka to Narayanganj region. ODbL 1.0: every map made from it must credit "© OpenStreetMap contributors".
  * Natural Earth 1:10m (public domain): the Bangladesh outline and major rivers for the national map.
"""
import argparse
import datetime
import json
import subprocess
import sys
import time
from pathlib import Path

from shapely.geometry import LineString, MultiPolygon, Polygon, box, mapping, shape
from shapely.ops import linemerge, polygonize, unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pfbrand import SOURCE  # noqa: E402

OUT = SOURCE / "geo"
UA = "parcelfly-brand-kit-map/1.0"
BBOX = (23.48, 90.15, 23.98, 90.72)          # south, west, north, east (Dhaka to Narayanganj and around)
INNER = (23.58, 90.28, 23.92, 90.58)         # secondary roads only here

HUBS = [  # key, English, Bangla, geocoder query, label side (left, right or below the pin), optional label_dy
    ("bakshibazar", "Bakshibazar", "বকশীবাজার", "Bakshibazar, Dhaka, Bangladesh", "left", -0.75),
    ("jatrabari", "Jatrabari", "যাত্রাবাড়ী", "Jatrabari, Dhaka, Bangladesh", "right"),
    ("mirpur", "Mirpur", "মিরপুর", "Mirpur, Dhaka, Bangladesh", "right"),
    ("rampura", "Rampura", "রামপুরা", "Rampura, Dhaka, Bangladesh", "right"),
    ("narayanganj", "Narayanganj", "নারায়ণগঞ্জ", "Narayanganj, Bangladesh", "left"),
    ("keraniganj", "Keraniganj", "কেরানীগঞ্জ", "Keraniganj, Dhaka, Bangladesh", "below"),
]
PREFER = {"suburb", "city", "town", "neighbourhood", "quarter", "bus_stop"}


def curl(args, out):
    subprocess.run(["curl", "-s", "-A", UA, "--max-time", "320", *args, "-o", str(out)], check=True)


def fetch(cache: Path, refresh: bool):
    cache.mkdir(parents=True, exist_ok=True)
    s, w, n, e = BBOX
    bb = f"{s},{w},{n},{e}"
    si, wi, ni, ei = INNER
    queries = {
        "water": f"""[out:json][timeout:300];(
  way["natural"="water"]["water"~"^(river|canal|lake|reservoir|oxbow|lagoon|stream_pool)$"]({bb});
  relation["natural"="water"]["water"~"^(river|canal|lake|reservoir|oxbow|lagoon)$"]({bb});
  way["waterway"="riverbank"]({bb}); relation["waterway"="riverbank"]({bb}););out geom;""",
        "lines": f"""[out:json][timeout:300];(
  way["waterway"~"^(river|canal)$"]({bb});
  way["highway"~"^(motorway|trunk|primary|motorway_link|trunk_link)$"]({bb});
  way["highway"="secondary"]({si},{wi},{ni},{ei});
  way["railway"="rail"]({bb}););out geom;""",
    }
    for name, q in queries.items():
        f = cache / f"osm-{name}.json"
        if refresh or not f.exists():
            (cache / f"q-{name}.txt").write_text(q)
            curl(["-X", "POST", "https://overpass-api.de/api/interpreter", "--data-urlencode", f"data@{cache / f'q-{name}.txt'}"], f)
            time.sleep(2)
    for key, en, bn, q, side, *_ in HUBS:
        f = cache / f"geo-{key}.json"
        if refresh or not f.exists():
            curl(["-G", "https://nominatim.openstreetmap.org/search", "--data-urlencode", f"q={q}",
                  "--data-urlencode", "format=jsonv2", "--data-urlencode", "limit=3"], f)
            time.sleep(1.2)
    ne = cache / "ne"
    ne.mkdir(exist_ok=True)
    base = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
    for fn in ["ne_10m_admin_0_countries.geojson", "ne_10m_rivers_lake_centerlines.geojson"]:
        if refresh or not (ne / fn).exists():
            subprocess.run(["curl", "-sL", "-A", UA, "-o", str(ne / fn), base + fn], check=True)


def r5(coords):
    return [[round(x, 5), round(y, 5)] for x, y in coords]


def poly_json(g):
    polys = [g] if isinstance(g, Polygon) else list(getattr(g, "geoms", []))
    out = []
    for p in polys:
        if p.is_empty or not isinstance(p, Polygon):
            continue
        out.append([r5(p.exterior.coords)] + [r5(i.coords) for i in p.interiors])
    return out


def line_json(g):
    lines = [g] if isinstance(g, LineString) else list(getattr(g, "geoms", []))
    return [r5(l.coords) for l in lines if isinstance(l, LineString) and len(l.coords) > 1]


def merge(lines):
    u = unary_union(lines)
    return u if u.geom_type == "LineString" else linemerge(u)


def way_line(el):
    return LineString([(p["lon"], p["lat"]) for p in el["geometry"]])


def process(cache: Path):
    s, w, n, e = BBOX
    clip = box(w, s, e, n)
    # ---------------- water polygons
    water = json.loads((cache / "osm-water.json").read_text())
    polys = []
    for el in water["elements"]:
        if el["type"] == "way" and "geometry" in el:
            pts = [(p["lon"], p["lat"]) for p in el["geometry"]]
            if len(pts) >= 4 and pts[0] == pts[-1]:
                polys.append(Polygon(pts).buffer(0))
        elif el["type"] == "relation":
            outer = [way_line({"geometry": m["geometry"]}) for m in el.get("members", [])
                     if m.get("type") == "way" and m.get("role") in ("outer", "") and "geometry" in m]
            inner = [way_line({"geometry": m["geometry"]}) for m in el.get("members", [])
                     if m.get("type") == "way" and m.get("role") == "inner" and "geometry" in m]
            if not outer:
                continue
            o = unary_union(list(polygonize(linemerge(outer))))
            if inner:
                o = o.difference(unary_union(list(polygonize(linemerge(inner)))))
            polys.append(o.buffer(0))
    wat = unary_union([p for p in polys if not p.is_empty]).intersection(clip)
    wat = wat.simplify(0.00012, preserve_topology=True)
    keep = [p for p in getattr(wat, "geoms", [wat]) if isinstance(p, Polygon) and p.area > 2.5e-7]
    wat = MultiPolygon(keep)
    # ---------------- lines
    lines = json.loads((cache / "osm-lines.json").read_text())
    groups = {"river": [], "canal": [], "motorway": [], "primary": [], "secondary": [], "rail": []}
    names = {}
    for el in lines["elements"]:
        if el["type"] != "way" or "geometry" not in el:
            continue
        t = el.get("tags", {})
        ln = way_line(el)
        if t.get("waterway") in ("river", "canal"):
            k = t["waterway"]
            nm = t.get("name:en") or t.get("name")
            if k == "river" and nm:
                names.setdefault(nm, []).append(ln)
        elif t.get("railway") == "rail":
            k = "rail"
        else:
            hw = t.get("highway", "")
            k = "motorway" if hw.startswith(("motorway", "trunk")) else ("primary" if hw == "primary" else "secondary")
        groups[k].append(ln)
    tol = {"river": 0.0001, "canal": 0.0001, "motorway": 0.00008, "primary": 0.00008, "secondary": 0.0001, "rail": 0.0001}
    out_lines = {}
    for k, ls in groups.items():
        merged = merge(ls) if ls else None
        if merged is None:
            out_lines[k] = []
            continue
        merged = merged.intersection(clip).simplify(tol[k], preserve_topology=False)
        out_lines[k] = line_json(merged)
    river_names = {}
    for nm, ls in names.items():
        m = merge(ls).intersection(clip).simplify(0.0002)
        river_names[nm] = line_json(m)
    stamp = json.loads((cache / "osm-lines.json").read_text())["osm3s"]["timestamp_osm_base"]
    region = {"bbox": [w, s, e, n], "source": "OpenStreetMap contributors (ODbL 1.0), Overpass API",
              "osm_timestamp": stamp, "water": poly_json(wat), "lines": out_lines, "rivers_named": river_names}
    # ---------------- hubs
    hubs = []
    for key, en, bn, q, side, *dy in HUBS:
        res = json.loads((cache / f"geo-{key}.json").read_text())
        pick = next((r for r in res if r.get("type") in PREFER or r.get("addresstype") in PREFER), res[0])
        hub_ = {"key": key, "name": en, "name_bn": bn, "lat": round(float(pick["lat"]), 5),
                "lon": round(float(pick["lon"]), 5), "label": side}
        if dy:
            hub_["label_dy"] = dy[0]
        hub_["geocoded"] = f"Nominatim: {pick['display_name']}"
        hubs.append(hub_)
    # ---------------- Bangladesh (Natural Earth)
    ne = cache / "ne"
    countries = json.loads((ne / "ne_10m_admin_0_countries.geojson").read_text())
    bgd = next(f for f in countries["features"] if f["properties"].get("ADM0_A3") == "BGD")
    bd = shape(bgd["geometry"]).simplify(0.004, preserve_topology=True)
    bd_polys = [p for p in getattr(bd, "geoms", [bd]) if p.area > 0.0004]
    bd = MultiPolygon(bd_polys)
    minx, miny, maxx, maxy = bd.bounds
    rv = json.loads((ne / "ne_10m_rivers_lake_centerlines.geojson").read_text())
    bd_rivers = []
    zone = bd.buffer(0.02)
    for f in rv["features"]:
        g = shape(f["geometry"])
        if not g.intersects(box(minx, miny, maxx, maxy)):
            continue
        g = g.intersection(zone).simplify(0.01)
        if g.is_empty:
            continue
        bd_rivers.append({"name": f["properties"].get("name") or "", "rank": f["properties"].get("scalerank"),
                          "lines": line_json(linemerge(g) if g.geom_type == "MultiLineString" else g)})
    country = {"source": "Natural Earth 1:10m (public domain)", "outline": poly_json(bd), "rivers": bd_rivers,
               "bounds": [minx, miny, maxx, maxy]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "dhaka-region.json").write_text(json.dumps(region, separators=(",", ":"), ensure_ascii=False))
    (OUT / "hubs.json").write_text(json.dumps({"hubs": hubs}, indent=2, ensure_ascii=False))
    (OUT / "bangladesh.json").write_text(json.dumps(country, separators=(",", ":"), ensure_ascii=False))
    (OUT / "README.md").write_text(f"""# Map data

Pre-processed by `source/build/fetch_geo.py` on {datetime.date.today().isoformat()} (OpenStreetMap snapshot {stamp}).

| File | Contents | Source and licence |
|---|---|---|
| `dhaka-region.json` | Rivers and water bodies, major roads, railways for Dhaka to Narayanganj | OpenStreetMap contributors, ODbL 1.0 |
| `hubs.json` | The Parcel Fly hub areas (area centroids, not street addresses) | Geocoded with OpenStreetMap Nominatim |
| `bangladesh.json` | Bangladesh outline and major rivers | Natural Earth 1:10m, public domain |

Every map built from OpenStreetMap data must show the credit "© OpenStreetMap contributors" (the build adds it).
Hub pins mark the neighbourhood, not the hub's street address: update `hubs.json` with exact coordinates if needed.
""", encoding="utf-8")
    print(f"water polygons {len(region['water'])}, " + ", ".join(f"{k} {len(v)}" for k, v in out_lines.items())
          + f", named rivers {len(river_names)}, hubs {len(hubs)}, BD polygons {len(country['outline'])}, BD rivers {len(bd_rivers)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="/tmp/pf-geo-dl")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    fetch(Path(a.cache), a.refresh)
    process(Path(a.cache))
