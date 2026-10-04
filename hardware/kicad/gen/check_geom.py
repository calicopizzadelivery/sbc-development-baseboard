#!/usr/bin/env python3
"""Find accidental connections in a generated sheet: any wire whose interior
passes through a symbol pin, a label, or another wire's endpoint, where no
junction was placed. KiCad connects on contact, so each of these is a short
the author did not intend.

    ./check_geom.py ../sbc-baseboard/ftdi.kicad_sch
"""
import sys
from kisym import parse, find, find_all, pins_of, transform

def load(path):
    t = parse(open(path, encoding="utf-8").read())
    libs = {s[1]: s for s in find_all(find(t, "lib_symbols"), "symbol")}
    wires, pins, points, juncs = [], [], [], set()
    for el in t:
        if not isinstance(el, list): continue
        k = el[0]
        if k == "wire":
            pts = find(el, "pts"); xy = find_all(pts, "xy")
            wires.append(((float(xy[0][1]), float(xy[0][2])), (float(xy[1][1]), float(xy[1][2]))))
        elif k == "junction":
            at = find(el, "at"); juncs.add((round(float(at[1]), 2), round(float(at[2]), 2)))
        elif k == "symbol":
            lib_id = find(el, "lib_id")[1]; at = find(el, "at"); ref = find(el, "property")  # first property is Reference
            refname = next(p[2] for p in find_all(el, "property") if p[1] == "Reference")
            X, Y, rot = float(at[1]), float(at[2]), int(float(at[3])) if len(at) > 3 else 0
            unit = int(find(el, "unit")[1])
            for p in pins_of(libs[lib_id]):
                if p.unit in (0, unit):
                    pins.append((transform(p.x, p.y, X, Y, rot), f"{refname}.{p.number}"))
        elif k in ("label", "global_label", "hierarchical_label"):
            at = find(el, "at"); points.append(((float(at[1]), float(at[2])), f"label {el[1]}"))
        elif k == "no_connect":
            at = find(el, "at"); points.append(((float(at[1]), float(at[2])), "NC"))
    return wires, pins, points, juncs

def on_interior(pt, a, b, eps=0.01):
    (x, y), (x1, y1), (x2, y2) = pt, a, b
    if abs(x1 - x2) < eps:   # vertical
        return abs(x - x1) < eps and min(y1, y2) + eps < y < max(y1, y2) - eps
    if abs(y1 - y2) < eps:   # horizontal
        return abs(y - y1) < eps and min(x1, x2) + eps < x < max(x1, x2) - eps
    return False

def check(path):
    wires, pins, points, juncs = load(path)
    ends = [(w[0], "wire-end"), (w[1], "wire-end")] if False else []
    for w in wires:
        ends.append((w[0], "wire-end")); ends.append((w[1], "wire-end"))
    hits = []
    for (a, b) in wires:
        for pt, what in pins + points + ends:
            if on_interior(pt, a, b) and (round(pt[0], 2), round(pt[1], 2)) not in juncs:
                hits.append((pt, what, a, b))
    # de-duplicate by point
    seen = {}
    for pt, what, a, b in hits:
        key = (round(pt[0], 2), round(pt[1], 2))
        seen.setdefault(key, set()).add(what)
    return seen

if __name__ == "__main__":
    for path in sys.argv[1:]:
        res = check(path)
        print(f"{path}: {len(res)} unintended contact point(s)")
        for key, whats in sorted(res.items()):
            print(f"   at {key[0]:.2f},{key[1]:.2f}: wire passes through {sorted(whats)}")
