# Map data

Pre-processed by `source/build/fetch_geo.py` on 2026-11-21 (OpenStreetMap snapshot 2026-11-21T03:08:01Z).

| File | Contents | Source and licence |
|---|---|---|
| `dhaka-region.json` | Rivers and water bodies, major roads, railways for Dhaka to Narayanganj | OpenStreetMap contributors, ODbL 1.0 |
| `hubs.json` | The five Parcel Fly hub areas (area centroids, not street addresses) | Geocoded with OpenStreetMap Nominatim |
| `bangladesh.json` | Bangladesh outline and major rivers | Natural Earth 1:10m, public domain |

Every map built from OpenStreetMap data must show the credit "© OpenStreetMap contributors" (the build adds it).
Hub pins mark the neighbourhood, not the hub's street address: update `hubs.json` with exact coordinates if needed.
