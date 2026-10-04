#!/usr/bin/env python3
"""Pin-name overlap check: for every symbol embedded in a sheet, estimate the box of
each visible pin name (KiCad stroke font, per-glyph advance) inside the body and report
pairs of names in the same unit that intersect. Independent of the symbol's source
(KiCad library or project), rotation or mirroring: the overlap is intrinsic to the symbol.
Usage: check_pins.py sheet.kicad_sch [...]  (exit 1 when anything overlaps)"""
import sys, re

# approximate advance of the KiCad stroke font, in units of the text size
ADV = {**{c: 0.95 for c in "ABCDEFGHKNOPQRSUVXYZ"}, "I": 0.45, "J": 0.75, "L": 0.8, "M": 1.15, "T": 0.85, "W": 1.2,
       **{c: 0.85 for c in "0123456789"}, "1": 0.7, **{c: 0.8 for c in "abcdefghknopqrsuvxyz"},
       "i": 0.4, "j": 0.45, "l": 0.4, "m": 1.2, "t": 0.55, "w": 1.1, "_": 0.95, "/": 0.75, "-": 0.65, "+": 0.95,
       "(": 0.5, ")": 0.5, ".": 0.4, ",": 0.4, " ": 0.6, "~": 0.95, "#": 0.95, "{": 0.5, "}": 0.5, "*": 0.8, "%": 1.0}
def text_w(s, size):
    s = re.sub(r"~\{([^}]*)\}", r"\1", s)          # overline markup takes no room
    return sum(ADV.get(c, 0.9) for c in s) * size

def parse(src):
    tok = re.findall(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()"]+', src)
    def walk(i):
        out = []
        while i < len(tok):
            t = tok[i]
            if t == "(":
                sub, i = walk(i + 1); out.append(sub)
            elif t == ")":
                return out, i + 1
            else:
                out.append(t[1:-1] if t.startswith('"') else t); i += 1
        return out, i
    return walk(0)[0]

def find(node, key):
    return [n for n in node if isinstance(n, list) and n and n[0] == key]

def pin_boxes(sym_node, unit):
    """Boxes (x0, y0, x1, y1, name, number) of visible pin names for one unit, library coords (Y up)."""
    offset, hide_all = 1.016, False
    for pn in find(sym_node, "pin_names"):
        for o in find(pn, "offset"): offset = float(o[1])
        if "hide" in pn or any(isinstance(x, list) and x[0] == "hide" and x[1] == "yes" for x in pn): hide_all = True
    if hide_all: return []
    boxes = []
    for sub in find(sym_node, "symbol"):
        m = re.match(r".*_(\d+)_(\d+)$", sub[1])
        if not m or int(m.group(1)) not in (0, unit) or int(m.group(2)) != 1: continue
        for p in find(sub, "pin"):
            at = find(p, "at")[0]; x, y, ang = float(at[1]), float(at[2]), float(at[3]) % 360
            L = float(find(p, "length")[0][1])
            nm = find(p, "name")[0]; name = nm[1]
            size = 1.27
            for e in find(nm, "effects"):
                for f in find(e, "font"):
                    for s in find(f, "size"): size = float(s[1])
                if any(isinstance(x, list) and x[0] == "hide" and x[1] == "yes" for x in e) or "hide" in e: name = ""
            if "hide" in p or any(isinstance(x, list) and x[0] == "hide" and x[1] == "yes" for x in p): continue   # hidden pin
            if name in ("", "~"): continue
            w, h = text_w(name, size), size
            if ang == 0:      boxes.append((x + L + offset, y - h / 2, x + L + offset + w, y + h / 2, name, find(p, "number")[0][1]))
            elif ang == 180:  boxes.append((x - L - offset - w, y - h / 2, x - L - offset, y + h / 2, name, find(p, "number")[0][1]))
            elif ang == 90:   boxes.append((x - h / 2, y + L + offset, x + h / 2, y + L + offset + w, name, find(p, "number")[0][1]))
            else:             boxes.append((x - h / 2, y - L - offset - w, x + h / 2, y - L - offset, name, find(p, "number")[0][1]))
    return boxes

def gaps(path, within=1.0):
    """Closest non-overlapping name pairs (gap <= within mm), to review marginal clearances."""
    root = parse(open(path).read())[0]
    libs = {s[1]: s for ls in find(root, "lib_symbols") for s in find(ls, "symbol")}
    used = {(find(i, "lib_id")[0][1], int(find(i, "unit")[0][1]) if find(i, "unit") else 1) for i in find(root, "symbol")}
    out = []
    for lid, unit in sorted(used):
        if lid not in libs: continue
        bx = pin_boxes(libs[lid], unit)
        for i in range(len(bx)):
            for j in range(i + 1, len(bx)):
                a, b = bx[i], bx[j]
                if a[:5] == b[:5]: continue
                ox, oy = min(a[2], b[2]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[1], b[1])
                if ox > 0 and oy > 0: continue
                gap = max(-ox, -oy) if (ox > 0 or oy > 0) else min(-ox, -oy)
                if (ox > 0 or oy > 0) and gap <= within:
                    out.append((round(gap, 2), f"{lid} unit {unit}: '{a[4]}' .. '{b[4]}' gap {gap:.2f} mm"))
    return [line for _, line in sorted(out)]

def check(path, tol=0.1):
    root = parse(open(path).read())[0]
    libs = {s[1]: s for ls in find(root, "lib_symbols") for s in find(ls, "symbol")}
    used = {}
    for inst in find(root, "symbol"):
        lid = find(inst, "lib_id")[0][1]
        unit = int(find(inst, "unit")[0][1]) if find(inst, "unit") else 1
        ref = [pr[2] for pr in find(inst, "property") if pr[1] == "Reference"][0]
        used.setdefault((lid, unit), []).append(ref)
    reports = []
    for (lid, unit), refs in sorted(used.items()):
        if lid not in libs: continue
        bx = pin_boxes(libs[lid], unit)
        for i in range(len(bx)):
            for j in range(i + 1, len(bx)):
                a, b = bx[i], bx[j]
                if a[:5] == b[:5]: continue                      # stacked pins (VBUS x4): the same name printed in the same place
                ox, oy = min(a[2], b[2]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[1], b[1])
                if ox > tol and oy > tol:
                    reports.append(f"   {lid} unit {unit} ({', '.join(refs[:4])}{'...' if len(refs) > 4 else ''}): pin {a[5]} '{a[4]}' overlaps pin {b[5]} '{b[4]}' by {ox:.2f} x {oy:.2f} mm")
    return reports

if __name__ == "__main__":
    bad = 0
    if sys.argv[1:2] == ["--gaps"]:
        for path in sys.argv[2:]:
            for line in gaps(path): print(f"   {line}")
        sys.exit(0)
    for path in sys.argv[1:]:
        r = check(path)
        print(f"{path}: {len(r)} pin-name overlap(s)")
        for line in r: print(line)
        bad += len(r)
    sys.exit(1 if bad else 0)
