#!/usr/bin/env python3
"""Layout review of a generated sheet: text that overlaps something, wires that
run through a symbol body, and power symbols pointing the wrong way.

Usage: check_layout.py <sheet.kicad_sch> [-v]

Text boxes are estimated (1.0 mm per character at 1.27 mm, 1.5 mm tall; global
labels get a 2.5 mm box). A field's angle is the symbol's rotation plus its
own, which is how KiCad draws it."""
import sys, math
from kisym import parse, Sym, pins_of, transform

SIZE = 1.27


def child(node, name):
    for c in node[1:]:
        if isinstance(c, list) and c and c[0] == Sym(name):
            return c


def props(node):
    out = {}
    for c in node[1:]:
        if isinstance(c, list) and c and c[0] == Sym("property"):
            at = child(c, "at")
            eff = child(c, "effects")
            hide = any(isinstance(x, list) and x and x[0] == Sym("hide") and x[1] == Sym("yes") for x in c[3:])
            just = None
            if eff:
                j = child(eff, "justify")
                if j:
                    just = " ".join(str(x) for x in j[1:])
            size = SIZE
            if eff:
                f = child(eff, "font")
                if f:
                    sz = child(f, "size")
                    if sz: size = float(sz[1])
            out[c[1]] = (c[2], float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0, just, hide, size)
    return out


def text_box(text, x, y, angle, just, size=SIZE, pad=0.0):
    w = max(1.0, len(text) * size * 0.8) + pad
    h = size * 1.2 + pad
    angle = angle % 180
    if angle == 0:
        if just and "left" in just:
            x0 = x
        elif just and "right" in just:
            x0 = x - w
        else:
            x0 = x - w / 2
        return (x0, y - h / 2, x0 + w, y + h / 2)
    # vertical text: extends along y
    if just and "left" in just:
        y1 = y
        y0 = y - w
    elif just and "right" in just:
        y0 = y
        y1 = y + w
    else:
        y0, y1 = y - w / 2, y + w / 2
    return (x - h / 2, y0, x + h / 2, y1)


def overlap(a, b, tol=0.05):
    return a[0] < b[2] - tol and b[0] < a[2] - tol and a[1] < b[3] - tol and b[1] < a[3] - tol


def seg_box(a, b, tol=0.0):
    return (min(a[0], b[0]) - tol, min(a[1], b[1]) - tol, max(a[0], b[0]) + tol, max(a[1], b[1]) + tol)


def main(path, verbose=False):
    root = parse(open(path, encoding="utf-8").read())
    libs = {}
    ls = child(root, "lib_symbols")
    for sym in ls[1:]:
        if isinstance(sym, list) and sym[0] == Sym("symbol"):
            libs[sym[1]] = sym
    texts, bodies, stubs, wires, powers = [], [], [], [], []
    for node in root[1:]:
        if not isinstance(node, list) or not node:
            continue
        tag = node[0]
        if tag == Sym("wire"):
            pts = child(node, "pts")
            a, b = [(float(c[1]), float(c[2])) for c in pts[1:]]
            wires.append((a, b))
        elif tag in (Sym("label"), Sym("global_label")):
            at = child(node, "at")
            x, y, rot = float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0
            glob = tag == Sym("global_label")
            w = len(node[1]) * SIZE * 0.8 + (3.0 if glob else 0.5)
            h = 2.0 if glob else 1.5
            if rot % 180 == 0:
                box = (x, y - h / 2, x + w, y + h / 2) if rot == 0 else (x - w, y - h / 2, x, y + h / 2)
            else:
                box = (x - h / 2, y - w, x + h / 2, y) if rot == 90 else (x - h / 2, y, x + h / 2, y + w)
            texts.append((f"label {node[1]}", box, None, (x, y)))
        elif tag == Sym("text"):
            pass
        elif tag == Sym("symbol"):
            lib_id = child(node, "lib_id")[1]
            at = child(node, "at")
            X, Y, rot = float(at[1]), float(at[2]), int(float(at[3])) if len(at) > 3 else 0
            m = child(node, "mirror"); mirror = str(m[1]) if m else None
            pr = props(node)
            ref, val = pr["Reference"][0], pr["Value"][0]
            lib = libs[lib_id]
            is_power = lib_id.startswith("power:")
            # body: rectangles from the lib, else the pin extent shrunk by the stubs
            rects = []
            for sub in lib[1:]:
                if isinstance(sub, list) and sub and sub[0] == Sym("symbol"):
                    for g in sub[1:]:
                        if isinstance(g, list) and g and g[0] == Sym("rectangle"):
                            s0, e0 = child(g, "start"), child(g, "end")
                            p = transform(float(s0[1]), float(s0[2]), X, Y, rot, mirror)
                            q = transform(float(e0[1]), float(e0[2]), X, Y, rot, mirror)
                            rects.append(seg_box(p, q))
            pins = pins_of(lib)
            pin_pts = []
            for p in pins:
                px, py = transform(p.x, p.y, X, Y, rot, mirror)
                # stub toward the body
                ang = ((180 - p.angle) if mirror == "y" else p.angle)
                ang = (ang + rot) % 360
                dx, dy = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}[ang]
                qx, qy = px + dx * p.length, py + dy * p.length
                pin_pts.append((px, py))
                if not is_power:
                    stubs.append((ref, (px, py), (qx, qy)))
            if rects:
                body = rects[0]
                for r in rects[1:]:
                    body = (min(body[0], r[0]), min(body[1], r[1]), max(body[2], r[2]), max(body[3], r[3]))
            elif pin_pts and not is_power:
                xs = [p[0] for p in pin_pts]; ys = [p[1] for p in pin_pts]
                body = (min(xs) + 1.5, min(ys) + 1.5, max(xs) - 1.5, max(ys) - 1.5)
                if body[0] > body[2]: body = (X - 1.0, body[1], X + 1.0, body[3])
                if body[1] > body[3]: body = (body[0], Y - 1.0, body[2], Y + 1.0)
            else:
                body = (X - 1.3, Y - 2.5, X + 1.3, Y + 2.5) if is_power else None
            if body is not None:
                bodies.append((ref, body, is_power))
            if is_power:
                gnd = val == "GND" or val.endswith("GND")
                powers.append((val, rot, X, Y, gnd))
                # the value text of a power symbol
                v = pr["Value"]
                if not v[5]:
                    texts.append((f"{ref}:{val}", text_box(val, v[1], v[2], v[3], v[4], v[6]), ref, (X, Y)))
                continue
            for name in ("Reference", "Value"):
                t, x, y, ang, just, hide, size = pr[name]
                if hide:
                    continue
                eff_ang = (ang + rot) % 360
                if eff_ang == 180 and just:
                    just = {"left": "right", "right": "left"}.get(just, just)
                texts.append((f"{ref}:{t}", text_box(t, x, y, eff_ang, just, size), ref, (X, Y)))
    # the sheet: A3 landscape, inner frame line 12 mm in, title block in the lower right
    # (measured from KiCad's default drawing sheet); keep 3 mm inside the frame and off the block
    FRAME = (15.0, 15.0, 405.0, 282.0)
    TITLE = (297.0, 250.0, 420.0, 297.0)
    for node in root[1:]:
        if isinstance(node, list) and node and node[0] == Sym("text"):
            at = child(node, "at"); eff = child(node, "effects")
            size = SIZE
            if eff:
                f = child(eff, "font")
                if f and child(f, "size"): size = float(child(f, "size")[1])
            lines = str(node[1]).split("\n")
            wdt = max(len(l) for l in lines) * size * 0.8
            x, y = float(at[1]), float(at[2])
            texts.append((f"note '{lines[0][:24]}'", (x, y - size * 0.6, x + wdt, y + size * 0.7), None, None))
    issues = {"text-body": [], "text-wire": [], "text-text": [], "text-stub": [], "wire-body": [], "power-dir": [], "frame": [], "pin-name": []}
    def outside(box):
        if box[0] < FRAME[0] or box[1] < FRAME[1] or box[2] > FRAME[2] or box[3] > FRAME[3]:
            return "past the frame"
        if overlap(box, TITLE):
            return "on the title block"
        return None
    for ref, body, is_power in bodies:
        why = outside(body)
        if why: issues["frame"].append((ref, why))
    for name, box, owner, anchor in texts:
        why = outside(box)
        if why: issues["frame"].append((name, why))
    for a, b in wires:
        why = outside(seg_box(a, b))
        if why: issues["frame"].append((f"wire {a}->{b}", why))
    for name, box, owner, anchor in texts:
        for ref, body, is_power in bodies:
            if ref == owner or is_power:
                continue
            if overlap(box, body):
                issues["text-body"].append((name, ref))
        for a, b in wires:
            sb = seg_box(a, b)
            if overlap(box, sb, tol=0.3):
                # a label's own wire ends at its anchor: ignore wires ending at the anchor
                if anchor and (abs(a[0] - anchor[0]) < 0.05 and abs(a[1] - anchor[1]) < 0.05 or abs(b[0] - anchor[0]) < 0.05 and abs(b[1] - anchor[1]) < 0.05):
                    continue
                issues["text-wire"].append((name, f"wire {a}->{b}"))
                break
        for ref, p, q in stubs:
            if ref != owner and overlap(box, seg_box(p, q), tol=0.2):
                issues["text-stub"].append((name, f"{ref} pin at {p}"))
                break
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            if texts[i][0].startswith("note") and texts[j][0].startswith("note"):
                continue                                     # note lines are stacked on purpose
            if overlap(texts[i][1], texts[j][1], tol=0.2):
                issues["text-text"].append((texts[i][0], texts[j][0]))
    for a, b in wires:
        sb = seg_box(a, b)
        for ref, body, is_power in bodies:
            if is_power:
                continue
            # a wire through a body: overlaps the interior, not just touching the edge at a pin
            inner = (body[0] + 0.3, body[1] + 0.3, body[2] - 0.3, body[3] - 0.3)
            if overlap(sb, inner, tol=0.0):
                issues["wire-body"].append((f"wire {a}->{b}", ref))
    for val, rot, X, Y, gnd in powers:
        if val == "PWR_FLAG":
            continue
        if (gnd and rot != 0) or (not gnd and rot != 0):
            issues["power-dir"].append((f"{val} rot {rot}", f"@({X:.2f}, {Y:.2f})"))
    import check_pins
    issues["pin-name"] = [(line.strip(), "") for line in check_pins.check(path)]   # names inside a symbol that print over each other
    total = sum(len(v) for v in issues.values())
    print(f"{path}: {total} layout issue(s)  " + "  ".join(f"{k}={len(v)}" for k, v in issues.items()))
    if verbose:
        for k, v in issues.items():
            for a, b in v[:40]:
                print(f"   {k:10s} {a}  ~  {b}")
    return total


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    sys.exit(1 if main(args[0], "-v" in sys.argv) else 0)
