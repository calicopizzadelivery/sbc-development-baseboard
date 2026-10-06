#!/usr/bin/env python3
"""Generate the first board file from the schematic, the project and the layout directives.

    ./pcb.py        # writes ../sbc-baseboard/sbc-baseboard.kicad_pcb (+ .kicad_dru), runs DRC

Outline, holes, keep-outs, edge connectors and the isolation region come from layout.py;
footprints and nets from the schematic's netlist export; net classes from the project file
(KiCad reads them when it opens the board next to the project). Interior parts are packed
by group as a starting point. Run once: after that the board file is the source of truth.
"""
import os, re, sys, subprocess, collections, math, tempfile
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
import layout as L

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "sbc-baseboard"))
PROJECT = "sbc-baseboard"
KICAD_FP = "/usr/share/kicad/footprints"
HOUSE_FP = os.path.normpath(os.path.join(HERE, "..", "libs", "footprints"))
MM = pcbnew.VECTOR2I_MM


def netlist():
    """(components {ref: (value, footprint)}, nets {name: [(ref, pin)]}) from kicad-cli's XML export."""
    tmp = os.path.join(tempfile.gettempdir(), f"{PROJECT}-netlist.xml")
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", tmp,
                    os.path.join(OUT, f"{PROJECT}.kicad_sch")], check=True, capture_output=True)
    root = ET.parse(tmp).getroot()
    comps = {c.get("ref"): (c.findtext("value") or "", c.findtext("footprint") or "") for c in root.iter("comp")}
    nets = {n.get("name"): [(x.get("ref"), x.get("pin")) for x in n.findall("node")] for n in root.iter("net")}
    return comps, nets


def load_footprint(fpid):
    lib, name = fpid.split(":")
    for base in (HOUSE_FP, KICAD_FP):
        path = os.path.join(base, lib + ".pretty")
        if os.path.exists(os.path.join(path, name + ".kicad_mod")):
            fp = pcbnew.FootprintLoad(path, name)
            if fp is not None:
                return fp
    raise FileNotFoundError(fpid)


def bbox_mm(fp, courtyard=True):
    """Courtyard box (or the body+pads box) of a footprint as (x0, y0, x1, y1) in mm."""
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox() if (courtyard and cy.OutlineCount()) else fp.GetBoundingBox(False, False)
    return (bb.GetLeft() / 1e6, bb.GetTop() / 1e6, bb.GetRight() / 1e6, bb.GetBottom() / 1e6)


def rot_for(mate, outward):
    """Rotation (degrees, KiCad's counter-clockwise) that turns the mating direction outward."""
    mx, my = mate
    for deg in (0, 90, 180, 270):
        # screen-CCW rotation with Y down: (x, y) -> (x cos + y sin, -x sin + y cos)
        c, s = round(math.cos(math.radians(deg))), round(math.sin(math.radians(deg)))
        if (mx * c + my * s, -mx * s + my * c) == outward:
            return deg
    raise ValueError(mate)


def edge_text_offset(fp):
    """Distance from the footprint origin to its 'PCB Edge' marker along -Y, if it has one."""
    for t in fp.GraphicalItems():
        if isinstance(t, pcbnew.PCB_TEXT) and "edge" in t.GetText().lower():
            return t.GetPosition().y / 1e6 - fp.GetPosition().y / 1e6
    return None


def main():
    comps, nets = netlist()
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings(); ds.m_MinThroughDrill = pcbnew.FromMM(0.2)     # the fab's minimum is 0.15; thermal vias in footprints are 0.2
    ds.m_CopperEdgeClearance = pcbnew.FromMM(0.25)                                   # the fab's copper-to-edge minimum
    W, H = L.BOARD
    # ---- outline with rounded corners
    r = L.RADIUS
    def seg(a, b):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(MM(*a)); s.SetEnd(MM(*b))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(pcbnew.FromMM(0.1)); board.Add(s)
    def arc(a, m, b):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetArcGeometry(MM(*a), MM(*m), MM(*b))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(pcbnew.FromMM(0.1)); board.Add(s)
    k = r * (1 - math.sqrt(0.5))
    seg((r, 0), (W - r, 0)); seg((W, r), (W, H - r)); seg((W - r, H), (r, H)); seg((0, H - r), (0, r))
    arc((0, r), (k, k), (r, 0)); arc((W - r, 0), (W - k, k), (W, r)); arc((W, H - r), (W - k, H - k), (W - r, H)); arc((r, H), (k, H - k), (0, H - r))
    # ---- nets
    netinfo = {}
    for name in sorted(nets):
        if name.startswith("unconnected-"):
            continue
        n = pcbnew.NETINFO_ITEM(board, name); board.Add(n); netinfo[name] = n
    pad_net = {}
    for name, nodes in nets.items():
        if name.startswith("unconnected-"):
            continue
        for ref, pin in nodes:
            pad_net[(ref, pin)] = name
    # ---- footprints
    fps = {}
    for ref, (value, fpid) in comps.items():
        if not fpid:
            continue
        fp = load_footprint(fpid)
        fp.SetReference(ref); fp.SetValue(value)
        for p in fp.Pads():
            name = pad_net.get((ref, p.GetNumber()))
            if name:
                p.SetNet(netinfo[name])
        board.Add(fp); fps[ref] = fp
    placed = set()
    # ---- mounting holes
    for ref, (x, y) in L.HOLES.items():
        fps[ref].SetPosition(MM(x, y)); placed.add(ref)
    # ---- edge connectors
    def mates(ref):
        name = comps[ref][1].split(":")[1]
        for key, vec in L.MATES:
            if key in name:
                return vec
        raise KeyError(f"no mating direction for {ref} {name}")
    def place_edge(ref, edge, along):
        """Put an edge connector on `edge` with its body starting `along` the edge; returns its length along it."""
        fp = fps[ref]
        outward = {"L": (-1, 0), "R": (1, 0), "F": (0, 1)}[edge]
        fp.SetOrientationDegrees(rot_for(mates(ref), outward))
        fp.SetPosition(MM(0, 0))
        x0, y0, x1, y1 = bbox_mm(fp, courtyard=False)
        marker = None                                   # a "PCB Edge" text says where the edge is
        for it in fp.GraphicalItems():
            if isinstance(it, pcbnew.PCB_TEXT) and "edge" in it.GetText().lower():
                marker = (it.GetPosition().x / 1e6, it.GetPosition().y / 1e6)
        if edge == "L":
            pos = (-(marker[0] if marker else x0), along - y0)
        elif edge == "R":
            pos = (W - (marker[0] if marker else x1), along - y0)
        else:
            pos = (along - x0, H - (marker[1] if marker else y1))
        fp.SetPosition(MM(*pos)); placed.add(ref)
        x0, y0, x1, y1 = bbox_mm(fp, courtyard=False)
        return (y1 - y0) if edge in ("L", "R") else (x1 - x0)
    for edge, refs in L.EDGES.items():
        if edge in ("L", "R"):
            cur = L.EDGE_START
            for ref in refs:
                cur += place_edge(ref, edge, cur) + L.EDGE_GAP
            print(f"   edge {edge}: connectors end at {cur - L.EDGE_GAP:.1f} of {H - L.HOLE_KEEPOUT:.1f}")
            assert cur - L.EDGE_GAP <= H - L.HOLE_KEEPOUT + 1e-6, f"{edge} edge overfull: {cur:.1f}"
        elif edge == "F_left":
            cur = L.EDGE_START
            for ref in refs:
                cur += place_edge(ref, "F", cur) + L.EDGE_GAP
            print(f"   edge F (left end): connectors end at {cur - L.EDGE_GAP:.1f}")
        else:  # F_right: pack leftward from the right corner
            cur = W - L.EDGE_START
            for ref in refs:
                fp = fps[ref]; fp.SetOrientationDegrees(rot_for(mates(ref), (0, 1))); fp.SetPosition(MM(0, 0))
                x0, y0, x1, y1 = bbox_mm(fp, courtyard=False)
                w = x1 - x0; cur -= w
                place_edge(ref, "F", cur); cur -= L.EDGE_GAP
            print(f"   edge F (right end): connectors start at {cur + L.EDGE_GAP:.1f}")
    # ---- parts fixed by hand (the ones that straddle the isolation barrier)
    for ref, (x, y, rot) in L.FIXED.items():
        fps[ref].SetOrientationDegrees(rot); fps[ref].SetPosition(MM(x, y)); placed.add(ref)
    # ---- interior groups: anchors by table, passives by the IC they share the most signal nets with
    group_of = {}
    for g, (rects, anchors) in L.GROUPS.items():
        for ref in anchors:
            if ref in fps and ref not in placed:
                group_of[ref] = g
    signal = {n: nodes for n, nodes in nets.items() if len(nodes) <= 6 and not n.startswith("unconnected-")}
    neigh = collections.defaultdict(collections.Counter)
    for n, nodes in signal.items():
        refs = {r for r, _ in nodes}
        for a in refs:
            for b in refs:
                if a != b: neigh[a][b] += 1
    for ref in sorted(fps):
        if ref in placed or ref in group_of:
            continue
        best = None
        for other, cnt in neigh[ref].most_common():
            if other in group_of:
                best = group_of[other]; break
        if best is None:                                  # fall back to the sheet the reference belongs to
            m = re.match(r"[A-Z]+(\d)", ref)
            best = {"1": "bucks", "2": "mcu", "3": "eth", "4": "hub", "5": "ftdi", "6": "dap", "7": "target", "8": "relays"}.get(m.group(1) if m else "", "mcu")
        group_of[ref] = best
    overflow = []
    for g, (rects, anchors) in L.GROUPS.items():
        members = [r for r in fps if group_of.get(r) == g and r not in placed]
        items = []
        for ref in members:
            fp = fps[ref]; fp.SetOrientationDegrees(0); fp.SetPosition(MM(0, 0))
            items.append((bbox_mm(fp), ref))
        items.sort(key=lambda it: -(it[0][3] - it[0][1]))         # tallest first, shelf packing, rectangle by rectangle
        queue = list(items)
        for (gx0, gy0, gx1, gy1) in rects:
            cx, cy, row_h = gx0, gy0, 0.0
            rest = []
            for (x0, y0, x1, y1), ref in queue:
                w, h = x1 - x0 + L.PACK_MARGIN, y1 - y0 + L.PACK_MARGIN
                if cx + w > gx1 + 1e-6 and cx > gx0:
                    cx, cy, row_h = gx0, cy + row_h, 0.0
                if cy + h > gy1 + 1e-6 or cx + w > gx1 + 1e-6:
                    rest.append(((x0, y0, x1, y1), ref)); continue  # does not fit here: try the next rectangle
                fps[ref].SetPosition(MM(cx - x0 + L.PACK_MARGIN / 2, cy - y0 + L.PACK_MARGIN / 2))
                cx += w; row_h = max(row_h, h)
                placed.add(ref)
            queue = rest
            if not queue:
                break
        if queue:                                          # left over: park them below the last rectangle and say so
            gx0, gy0, gx1, gy1 = rects[-1]
            cx, cy = gx0, gy1
            for (x0, y0, x1, y1), ref in queue:
                fps[ref].SetPosition(MM(cx - x0, cy - y0)); cx += x1 - x0 + L.PACK_MARGIN; placed.add(ref)
            overflow.append((g, len(queue)))
    # ---- keep-outs: the corners (with the hole's pad cut out) and the isolation region's board-net copper
    def rule_area(name, outline, holes=(), layers=("F.Cu", "In1.Cu", "In2.Cu", "B.Cu"), footprints=True):
        z = pcbnew.ZONE(board); z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowZoneFills(True); z.SetDoNotAllowFootprints(footprints)
        z.SetDoNotAllowPads(False)
        ls = pcbnew.LSET()
        for ln in layers: ls.addLayer(board.GetLayerID(ln))
        z.SetLayerSet(ls); z.SetZoneName(name)
        ol = z.Outline(); ol.NewOutline()
        for x, y in outline: ol.Append(MM(x, y))
        for hx, hy, hr in holes:
            ol.NewHole()
            for i in range(24):
                a = 2 * math.pi * i / 24; ol.Append(MM(hx + hr * math.cos(a), hy + hr * math.sin(a)), 0, 0)
        board.Add(z); return z
    s, c = L.HOLE_KEEPOUT, L.HOLE_CLEAR_R
    for ref, (hx, hy) in L.HOLES.items():
        # the corner square less a square around the hole's own pad: four strips
        x0 = 0 if hx < W / 2 else W - s; y0 = 0 if hy < H / 2 else H - s
        strips = [(x0, y0, x0 + s, hy - c), (x0, hy + c, x0 + s, y0 + s), (x0, hy - c, hx - c, hy + c), (hx + c, hy - c, x0 + s, hy + c)]
        for i, (a, b, cc, d) in enumerate(strips):
            if cc - a > 0.1 and d - b > 0.1:
                rule_area(f"corner_{ref}_{i}", [(a, b), (cc, b), (cc, d), (a, d)])
    rule_area("psu_iso", L.ISOLATION, footprints=False)   # tracks, vias and fills of board nets stay out (rule in .kicad_dru)
    # ---- planes: ground on In1.Cu everywhere but the isolation region, which gets its own PSU_GND island
    def copper_zone(name, net, layer, outline, holes=()):
        z = pcbnew.ZONE(board); z.SetLayer(board.GetLayerID(layer)); z.SetNet(netinfo[net]); z.SetZoneName(name)
        z.SetMinThickness(pcbnew.FromMM(0.25)); z.SetLocalClearance(pcbnew.FromMM(0.3))
        ol = z.Outline(); ol.NewOutline()
        for x, y in outline: ol.Append(MM(x, y))
        for hole in holes:
            ol.NewHole()
            for x, y in hole: ol.Append(MM(x, y), 0, 0)
        board.Add(z); return z
    i = 1.0                                           # planes stop a millimetre short of the edge
    copper_zone("GND_L2", "GND", "In1.Cu", [(i, i), (W - i, i), (W - i, H - i), (i, H - i)], holes=[L.ISOLATION_PLANE_HOLE])
    copper_zone("PSU_GND_L2", "PSU_GND", "In1.Cu", L.ISOLATION)
    # ---- save, then the stackup (not reachable through the Python API) and the design rules
    path = os.path.join(OUT, f"{PROJECT}.kicad_pcb")
    pcbnew.SaveBoard(path, board, True)                # skip settings: the project file (net classes) is the schematic build's
    t = open(path, encoding="utf-8").read()
    layers = ['\t\t\t(layer "F.SilkS" (type "Top Silk Screen"))', '\t\t\t(layer "F.Paste" (type "Top Solder Paste"))',
              '\t\t\t(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))']
    for item in L.STACKUP:
        if item[1] == "copper":
            layers.append(f'\t\t\t(layer "{item[0]}" (type "copper") (thickness {item[2]}))')
        else:
            layers.append(f'\t\t\t(layer "{item[0]}" (type "{item[1]}") (thickness {item[2]}) (material "FR4") (epsilon_r {item[3]}) (loss_tangent 0.02))')
    layers += ['\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))', '\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))',
               '\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen"))', '\t\t\t(copper_finish "ENIG")', '\t\t\t(dielectric_constraints no)']
    stack = "\t\t(stackup\n" + "\n".join(layers) + "\n\t\t)\n"
    assert "(stackup" not in t
    t = re.sub(r"(\n\t\(setup\n)", r"\1" + stack.replace("\\", "\\\\"), t, count=1)
    open(path, "w", encoding="utf-8").write(t)
    iso = "(A.NetClass == 'PSU_3A' || A.NetClass == 'PSU_ISO')"
    dru = f'''(version 1)
# PSU passthrough isolation: only the isolated classes' copper inside the region, and {L.ISO_GAP} mm creepage to board nets
(rule "psu_isolation_keepout"
    (condition "A.intersectsArea('psu_iso') && !{iso}")
    (constraint disallow track via zone))
(rule "psu_isolation_gap"
    (condition "{iso} && !{iso.replace('A.', 'B.')}")
    (constraint clearance (min {L.ISO_GAP}mm)))
'''
    open(os.path.join(OUT, f"{PROJECT}.kicad_dru"), "w", encoding="utf-8").write(dru)
    print(f"wrote {path}: {len(fps)} footprints, {len(netinfo)} nets, {len(list(board.Zones()))} zones")
    for g, n in overflow:
        print(f"   group {g}: {n} part(s) did not fit its rectangles (parked below)")
    # ---- DRC gate
    rep = os.path.join(OUT, "drc.txt")
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "--format", "report", "-o", rep, path], capture_output=True, text=True)
    txt = open(rep, encoding="utf-8").read()
    # the report header carries the run time: pin it to the title-block date, as the ERC report is
    txt = re.sub(r"Created on \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "Created on 2026-10-03T00:00:00", txt, count=1)
    open(rep, "w", encoding="utf-8").write(txt)
    kinds = collections.Counter()
    for m in re.finditer(r"^\[(\w+)\][^\n]*\n\s*(?:Rule: [^;]*; )?(\w+)", txt, re.M):
        kinds[(m.group(1), m.group(2))] += 1
    errors = {k: v for (k, sev), v in kinds.items() if sev == "error" and k != "unconnected_items"}
    warnings = {k: v for (k, sev), v in kinds.items() if sev != "error"}
    unconnected = sum(v for (k, sev), v in kinds.items() if k == "unconnected_items")
    print(f"DRC: {sum(errors.values())} error(s) {errors}; {unconnected} unconnected (unrouted); warnings {warnings}")
    return errors


if __name__ == "__main__":
    main()
