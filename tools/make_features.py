"""Pull the exam's rivers and lakes out of Natural Earth and write them as JS.

  python -I make_features.py <natural earth dir> <out.js>

The rivers come from ne_10m_rivers_lake_centerlines (every record whose name
matches, inside a box that keeps the Scottish Don and the Siberian Oka out),
the lakes from ne_10m_lakes. Shapes are Douglas-Peucker simplified so the
page stays small.
"""

import json
import math
import sys
from pathlib import Path

import shapefile

# name, Lithuanian name (as on the exam list), matching names, lon/lat box
RIVERS = [
    ("Glomma", "Gloma", ["Glomma", "Glåma", "Glama"], (7, 58, 13, 63.5)),
    ("Pechora", "Pečiora", ["Pechora"], (48, 59, 70, 70)),
    ("Northern Dvina", "Šiaurės Dvina", ["Severnaya Dvina", "Northern Dvina"], (38, 58, 50, 66)),
    ("Volga", "Volga", ["Volga"], (30, 44, 60, 60)),
    ("Oka", "Oka", ["Oka"], (33, 50, 45, 58)),
    ("Daugava", "Dauguva", ["Daugava", "Western Dvina", "Zapadnaya Dvina", "Dvina"], (20, 54, 35, 58)),
    ("Nemunas", "Nemunas", ["Neman", "Nemunas", "Nioman", "Niemen"], (19, 52, 28, 57)),
    ("Don", "Donas", ["Don"], (35, 45, 45, 56)),
    ("Dnieper", "Dnepras", ["Dnipro", "Dnieper", "Dnepr"], (25, 45, 38, 58)),
    ("Dniester", "Dnestras", ["Dniester", "Dnister", "Nistru"], (22, 45, 32, 50)),
    ("Danube", "Dunojus", ["Danube", "Donau", "Dunav", "Duna", "Dunărea", "Dunarea", "Dunaj"], (7, 42, 31, 50)),
    ("Tisza", "Tisa", ["Tisza", "Tisa"], (18, 44, 26, 49)),
    ("Vistula", "Vysla", ["Vistula", "Wisła", "Wisla"], (17, 48, 23, 55)),
    ("Oder", "Oderis (Odra)", ["Oder", "Odra"], (13, 48, 20, 55)),
    ("Elbe", "Elbė", ["Elbe", "Labe"], (7, 48, 17, 55)),
    ("Rhine", "Reinas", ["Rhine", "Rhein", "Rijn", "Rhin"], (3, 45, 12, 53)),
    ("Thames", "Temzė", ["Thames"], (-3, 50, 2, 53)),
    ("Seine", "Sena", ["Seine"], (-1, 46, 6, 51)),
    ("Loire", "Luara", ["Loire"], (-3, 43, 6, 49)),
    ("Garonne", "Garona", ["Garonne"], (-2, 41, 4, 46)),
    ("Rhône", "Rona", ["Rhône", "Rhone"], (3, 42, 10, 48)),
    ("Po", "Po", ["Po"], (6, 43, 13, 46)),
    ("Tiber", "Tiberis", ["Tiber", "Tevere"], (10, 40, 14, 44)),
    ("Douro", "Dueras", ["Douro", "Duero"], (-9, 40, -1, 43)),
]

LAKES = [
    ("Onega", "Onega", ["Lake Onega", "Onega"]),
    ("Ladoga", "Ladoga", ["Lake Ladoga", "Ladoga"]),
    ("Peipus", "Peipus", ["Lake Peipus", "Peipus"]),
    ("Saimaa", "Saima", ["Lake Saimaa", "Saimaa"]),
    ("Vänern", "Venernas", ["Vänern", "Vanern"]),
    ("Vättern", "Veternas", ["Vättern", "Vattern"]),
    ("Lake Geneva", "Ženevos ež.", ["Lake Geneva", "Lac Léman", "Geneva"]),
    ("Lake Constance", "Bodeno ež.", ["Bodensee", "Lake Constance", "Constance"]),
    ("Balaton", "Balatonas", ["Lake Balaton", "Balaton"]),
    ("Lake Van", "Vano ež.", ["Lake Van", "Van Gölü", "Van"]),
]


def simplify(points, tol):
    """Douglas-Peucker on (lon, lat) points."""
    if len(points) < 3:
        return list(points)
    ax, ay = points[0]
    bx, by = points[-1]
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy)
    best, best_i = -1.0, 0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        if length == 0:
            d = math.hypot(px - ax, py - ay)
        else:
            d = abs(dx * (ay - py) - (ax - px) * dy) / length
        if d > best:
            best, best_i = d, i
    if best > tol:
        left = simplify(points[: best_i + 1], tol)
        right = simplify(points[best_i:], tol)
        return left[:-1] + right
    return [points[0], points[-1]]


def inside(box, points):
    minlon, minlat, maxlon, maxlat = box
    lon = sum(p[0] for p in points) / len(points)
    lat = sum(p[1] for p in points) / len(points)
    return minlon <= lon <= maxlon and minlat <= lat <= maxlat


def parts_of(shape):
    pts = shape.points
    starts = list(shape.parts) + [len(pts)]
    return [pts[a:b] for a, b in zip(starts, starts[1:]) if b - a >= 2]


# Pieces Natural Earth files elsewhere or not at all, as (lat, lon) lines.
# The Rhine's Dutch branches and the upper Nemunas (filed as "Nyoman" in the
# Europe supplement) come from the data; the lower Glomma from Kongsvinger
# through lake Oyeren to Fredrikstad, and the Elbe estuary below Hamburg, are
# drawn by hand because the data stops short of the sea.
EXTRA_RECORDS = {
    "Rhine": ("ne_10m_rivers_lake_centerlines", ["Waal", "Lek", "Nederrijn"], (3.5, 51.5, 6.5, 52.2)),
    "Nemunas": ("ne_10m_rivers_europe", ["Nyoman"], (21, 53, 28, 56)),
}
EXTRA_LINES = {
    "Glomma": [[[60.52, 12.03], [60.35, 12.03], [60.19, 11.99], [60.25, 11.68], [60.12, 11.47],
                [59.95, 11.3], [59.78, 11.15], [59.62, 11.1], [59.42, 11.1], [59.28, 11.11], [59.21, 10.93]]],
    "Elbe": [[[53.55, 9.82], [53.63, 9.65], [53.79, 9.42], [53.89, 9.13], [53.87, 8.70]]],
}


def load(ne, name):
    sf = shapefile.Reader(str(ne / name / name))
    fields = [f[0] for f in sf.fields[1:]]
    return [(dict(zip(fields, sr.record)), sr.shape) for sr in sf.iterShapeRecords()]


def matching(records, aliases, box, tol):
    shapes = []
    for d, shape in records:
        names = {str(d.get(k) or "") for k in ("name", "name_en", "name_alt")}
        if not any(a in names for a in aliases):
            continue
        if "Canal" in str(d.get("name") or ""):
            continue
        for part in parts_of(shape):
            if not inside(box, part):
                continue
            simp = simplify(part, tol)
            shapes.append([[round(lat, 3), round(lon, 3)] for lon, lat in simp])
    return shapes


def rivers(ne):
    files = {n: load(ne, n) for n in ("ne_10m_rivers_lake_centerlines", "ne_10m_rivers_europe")}
    out = []
    for name, name_lt, aliases, box in RIVERS:
        shapes = matching(files["ne_10m_rivers_lake_centerlines"], aliases, box, 0.02)
        if name in EXTRA_RECORDS:
            src, more, more_box = EXTRA_RECORDS[name]
            shapes += matching(files[src], more, more_box, 0.02)
        shapes += EXTRA_LINES.get(name, [])
        hits = len(shapes)
        if not shapes:
            print(f"  !! {name}: nothing found")
            continue
        n = sum(len(s) for s in shapes)
        lons = [p[1] for s in shapes for p in s]
        lats = [p[0] for s in shapes for p in s]
        print(f"  {name:16s} {hits:3d} parts {n:4d} pts  lon {min(lons):6.1f}..{max(lons):6.1f}  lat {min(lats):5.1f}..{max(lats):5.1f}")
        out.append({"name": name, "nameLt": name_lt, "shapes": shapes})
    return out


def lakes(ne):
    sf = shapefile.Reader(str(ne / "ne_10m_lakes" / "ne_10m_lakes"))
    fields = [f[0] for f in sf.fields[1:]]
    records = []
    for sr in sf.iterShapeRecords():
        d = dict(zip(fields, sr.record))
        records.append((d, sr.shape))
    out = []
    for name, name_lt, aliases in LAKES:
        rings = []
        for d, shape in records:
            names = {str(d.get(k) or "") for k in ("name", "name_en", "name_alt")}
            if not any(a in names for a in aliases):
                continue
            for part in parts_of(shape):
                simp = simplify(part, 0.01)
                if len(simp) >= 4:
                    rings.append([[round(lat, 3), round(lon, 3)] for lon, lat in simp])
        if not rings:
            print(f"  !! {name}: nothing found")
            continue
        rings.sort(key=len, reverse=True)
        n = sum(len(r) for r in rings)
        lons = [p[1] for r in rings for p in r]
        lats = [p[0] for r in rings for p in r]
        print(f"  {name:16s} {len(rings):3d} rings {n:4d} pts  lon {min(lons):6.1f}..{max(lons):6.1f}  lat {min(lats):5.1f}..{max(lats):5.1f}")
        out.append({"name": name, "nameLt": name_lt, "rings": rings})
    return out


def main():
    ne = Path(sys.argv[1])
    out = Path(sys.argv[2])
    print("rivers")
    r = rivers(ne)
    print("lakes")
    l = lakes(ne)
    js = "// Generated by tools/make_features.py from Natural Earth 10m (public domain).\n"
    js += "const RIVERS = " + json.dumps(r, ensure_ascii=False, separators=(",", ":")) + ";\n"
    js += "const LAKES = " + json.dumps(l, ensure_ascii=False, separators=(",", ":")) + ";\n"
    out.write_text(js, encoding="utf-8")
    print(f"wrote {out}: {len(r)} rivers, {len(l)} lakes, {out.stat().st_size} bytes")


if __name__ == "__main__":
    main()
