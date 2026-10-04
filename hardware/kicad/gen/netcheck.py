#!/usr/bin/env python3
"""Trace wire-level connectivity of a generated sheet and report nets that
carry more than one power rail, or a rail plus labels of another name.

Usage: netcheck.py <sheet.kicad_sch> [--all]

Connectivity follows KiCad's rules: wire ends connect to anything they touch
(another wire's end or body, a pin end, a label point, a power symbol pin);
wires crossing mid-segment do not connect. Part pins are reported as members
but do not join nets through the part."""
import sys
from kisym import parse, Sym, pins_of, transform

TOL = 0.02


def key(p):
    return (round(p[0] / 0.635) , round(p[1] / 0.635))


class UF:
    def __init__(self):
        self.p = {}

    def find(self, a):
        self.p.setdefault(a, a)
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def on_segment(p, a, b):
    (x, y), (x1, y1), (x2, y2) = p, a, b
    if abs(x1 - x2) < TOL:          # vertical
        return abs(x - x1) < TOL and min(y1, y2) - TOL <= y <= max(y1, y2) + TOL
    if abs(y1 - y2) < TOL:          # horizontal
        return abs(y - y1) < TOL and min(x1, x2) - TOL <= x <= max(x1, x2) + TOL
    return False


def prop(node, name):
    for c in node[1:]:
        if isinstance(c, list) and c and c[0] == Sym("property") and c[1] == name:
            return c[2]
    return None


def child(node, name):
    for c in node[1:]:
        if isinstance(c, list) and c and c[0] == Sym(name):
            return c
    return None


def main(path, show_all=False, trace=False):
    root = parse(open(path, encoding="utf-8").read())
    wires, points = [], []            # points: (pt, kind, text)
    libs = {}
    ls = child(root, "lib_symbols")
    if ls:
        for sym in ls[1:]:
            if isinstance(sym, list) and sym[0] == Sym("symbol"):
                libs[sym[1]] = sym
    for node in root[1:]:
        if not isinstance(node, list) or not node:
            continue
        tag = node[0]
        if tag == Sym("wire"):
            pts = child(node, "pts")
            a, b = [(float(c[1]), float(c[2])) for c in pts[1:]]
            wires.append((a, b))
        elif tag in (Sym("label"), Sym("global_label"), Sym("hierarchical_label")):
            at = child(node, "at")
            points.append(((float(at[1]), float(at[2])), "label", node[1]))
        elif tag == Sym("no_connect"):
            at = child(node, "at")
            points.append(((float(at[1]), float(at[2])), "nc", "NC"))
        elif tag == Sym("symbol"):
            lib_id = child(node, "lib_id")[1]
            at = child(node, "at")
            X, Y, rot = float(at[1]), float(at[2]), int(float(at[3])) if len(at) > 3 else 0
            ref, val = prop(node, "Reference"), prop(node, "Value")
            if lib_id.startswith("power:"):
                kind = "flag" if val == "PWR_FLAG" else "rail"
                points.append(((X, Y), kind, val))
                continue
            lib = libs.get(lib_id)
            if lib is None:
                continue
            for p in pins_of(lib):
                px, py = transform(p.x, p.y, X, Y, rot)
                points.append(((px, py), "pin", f"{ref}.{p.number}"))
    uf = UF()
    ends = []
    for i, (a, b) in enumerate(wires):
        uf.union(("w", i), ("p", key(a)))
        uf.union(("w", i), ("p", key(b)))
        ends.append((a, i)); ends.append((b, i))
    # wire ends touching another wire's body
    for (e, i) in ends:
        for j, (a, b) in enumerate(wires):
            if j != i and on_segment(e, a, b):
                uf.union(("w", i), ("w", j))
    # points: attach to any wire they touch
    for pt, kind, text in points:
        pid = ("p", key(pt))
        uf.find(pid)
        for j, (a, b) in enumerate(wires):
            if on_segment(pt, a, b):
                uf.union(pid, ("w", j))
    groups = {}
    for pt, kind, text in points:
        groups.setdefault(uf.find(("p", key(pt))), []).append((kind, text, pt))
    bad = 0
    for g, members in groups.items():
        rails = sorted({t for k, t, _ in members if k == "rail"})
        labels = sorted({t for k, t, _ in members if k == "label"})
        names = rails + [l for l in labels if l not in rails]
        suspicious = len(rails) > 1 or (rails and labels and any(l != rails[0] for l in labels)) or len(labels) > 1 and not rails and len({l for l in labels}) > 1
        if suspicious or show_all:
            bad += suspicious
            print(("!! " if suspicious else "   ") + "net " + " + ".join(names) if names else "   (unnamed)")
            for k, t, pt in sorted(members, key=lambda m: (m[0], m[1])):
                print(f"      {k:5s} {t:28s} @({pt[0]:.2f}, {pt[1]:.2f})")
            if trace and suspicious:
                for j, (a, b) in enumerate(wires):
                    if uf.find(("w", j)) == g:
                        print(f"      wire  ({a[0]:.2f}, {a[1]:.2f}) -> ({b[0]:.2f}, {b[1]:.2f})")
    print(f"{path}: {bad} merged net(s)")
    return bad


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sys.exit(1 if main(args[0], "--all" in sys.argv, "--trace" in sys.argv) else 0)
