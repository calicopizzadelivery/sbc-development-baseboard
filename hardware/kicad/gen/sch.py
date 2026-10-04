"""KiCad 10 schematic writer.

A Schematic collects symbol instances, wires, labels and sheets, and emits a
.kicad_sch with every used library symbol embedded. Pin positions are computed
from the library geometry so wires and labels can be attached exactly.
"""
import uuid as _uuid
from kisym import (get_symbol, pins_of, transform, pin_direction, dump, find,
                   find_all, prop, Sym)

FONT = lambda size=1.27: [Sym("font"), [Sym("size"), size, size]]


def uid():
    return str(_uuid.uuid4())


G = 1.27                                     # KiCad connection grid, mm


def snap(v):
    return round(round(v / G) * G, 4)


def sp(pt):
    return (snap(pt[0]), snap(pt[1]))


def effects(size=1.27, justify=None, hide=False):
    e = [Sym("effects"), FONT(size)]
    if justify:
        e.append([Sym("justify")] + [Sym(j) for j in justify.split()])
    return e


class Instance:
    def __init__(self, sch, libname, name, ref, value, X, Y, rot, node, unit, mirror=None):
        self.sch, self.libname, self.name = sch, libname, name
        self.ref, self.value, self.X, self.Y, self.rot, self.unit = ref, value, X, Y, rot, unit
        self.mirror = mirror
        self.field_size = 1.27
        self.node = node
        self.pins = {p.number: p for p in pins_of(node) if p.unit in (0, unit)}
        self.fields = {}
        self.footprint = ""
        self.datasheet = "~"
        self.dnp = False
        self.uuid = uid()
        self.ref_at = None
        self.val_at = None
        self.ref_just = None
        self.val_just = None
        self.hide_value = False

    def pin(self, number):
        p = self.pins[str(number)]
        return transform(p.x, p.y, self.X, self.Y, self.rot, self.mirror)

    def pin_dir(self, number):
        p = self.pins[str(number)]
        return pin_direction(p.angle, self.rot, self.mirror)

    def pin_by_name(self, name):
        for p in self.pins.values():
            if p.name == name:
                return p.number
        raise KeyError(name)

    def bbox(self):
        xs = [self.pin(n)[0] for n in self.pins]
        ys = [self.pin(n)[1] for n in self.pins]
        return min(xs), min(ys), max(xs), max(ys)

    def body(self):
        """The symbol outline on the sheet (library rectangles, else the pin extent)."""
        pts = []
        for sub in self.node[1:]:
            if isinstance(sub, list) and sub and sub[0] == Sym("symbol"):
                for g in sub[1:]:
                    if isinstance(g, list) and g and g[0] == Sym("rectangle"):
                        for key in ("start", "end"):
                            c = [x for x in g[1:] if isinstance(x, list) and x and x[0] == Sym(key)][0]
                            pts.append(transform(float(c[1]), float(c[2]), self.X, self.Y, self.rot, self.mirror))
        if not pts:
            return self.bbox()
        return min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)


class Schematic:
    def __init__(self, project, title, paper="A3", page=1, sheet_path="/"):
        self.project = project
        self.title = title
        self.paper = paper
        self.uuid = uid()
        self.page = page
        self.sheet_path = sheet_path       # instance path prefix for symbols on this sheet
        self.lib_symbols = {}
        self.items = []                    # emitted in order
        self.instances = []
        self.project_lib = {}
        self.refs = set()
        self.comments = []
        self.wire_log = []

    # --- symbols ----------------------------------------------------------
    def add(self, libname, name, ref, value, at, rot=0, footprint="", fields=None,
            unit=1, dnp=False, datasheet="~", hide_value=False, project_lib=None, mirror=None):
        key = f"{libname}:{name}"
        plib = project_lib if project_lib is not None else self.project_lib
        if key not in self.lib_symbols:
            self.lib_symbols[key] = get_symbol(libname, name, plib)
        node = self.lib_symbols[key]
        if (ref, unit) in self.refs and not ref.startswith("#"):
            raise ValueError(f"duplicate reference {ref} unit {unit}")
        self.refs.add((ref, unit))
        at = sp(at)
        inst = Instance(self, libname, name, ref, value, at[0], at[1], rot, node, unit, mirror)
        inst.footprint = footprint
        inst.fields = fields or {}
        inst.dnp = dnp
        inst.datasheet = datasheet
        inst.hide_value = hide_value
        self.instances.append(inst)
        self.items.append(("symbol", inst))
        return inst

    def power(self, net, at, rot=0, kind=None):
        """Power symbol. kind: 'GND', '+3V3', '+5V' (any rail name as value),
        'PWR_FLAG'. The Value field is the net name."""
        kind = kind or ("GND" if net == "GND" else "PWR_FLAG" if net == "PWR_FLAG" else "+5V" if net.startswith("+5") or net.startswith("VBUS") else "+3V3")
        if kind == "GND" and net != "GND":
            kind = "GNDPWR" if net.endswith("GND") else "GND"
        n = len([i for i in self.instances if i.ref.startswith("#PWR")]) + 1
        inst = self.add("power", kind, f"#PWR{self.page:02d}{n:03d}", net, at, rot)
        return inst

    def flag(self, at, rot=0):
        return self.power("PWR_FLAG", at, rot, kind="PWR_FLAG")

    # --- connectivity -----------------------------------------------------
    def wire(self, *pts):
        import inspect
        pts = [sp(p) for p in pts]
        who = "/".join(f.function for f in inspect.stack()[1:5] if f.function not in ("<module>", "main"))
        for a, b in zip(pts, pts[1:]):
            if a != b:
                self.items.append(("wire", (a, b)))
                self.wire_log.append((a, b, who))

    def junction(self, at):
        self.items.append(("junction", sp(at)))

    def label(self, net, at, rot=0, glob=False, shape="passive"):
        self.items.append(("label", (net, sp(at), rot, glob, shape)))

    def nc(self, at):
        self.items.append(("nc", sp(at)))

    def text(self, s, at, size=1.5, bold=False):
        self.items.append(("text", (s, at, size, bold)))

    def sheet(self, name, file, at, size, sheet_uuid, page):
        self.items.append(("sheet", (name, file, at, size, sheet_uuid, page)))

    # --- helpers that attach to a pin ------------------------------------
    def stub(self, inst, pin, length=2.54):
        """Short wire from a pin outward; returns the far end and direction."""
        x, y = inst.pin(pin)
        d = inst.pin_dir(pin)
        dx, dy = {"L": (-length, 0), "R": (length, 0), "U": (0, -length), "D": (0, length)}[d]
        end = (round(x + dx, 4), round(y + dy, 4))
        self.wire((x, y), end)
        return end, d

    def pin_label(self, inst, pin, net, glob=True, length=2.54, shape="passive"):
        end, d = self.stub(inst, pin, length)
        rot = {"L": 180, "R": 0, "U": 90, "D": 270}[d]
        self.label(net, end, rot, glob, shape)
        return end

    def pin_power(self, inst, pin, net, length=2.54, kind=None):
        end, d = self.stub(inst, pin, length)
        rot = {"U": 0, "D": 0, "L": 90, "R": 270}[d]
        if net == "GND" or net.endswith("GND"):
            rot = {"D": 0, "U": 180, "L": 90, "R": 270}[d]
        elif d == "D":
            rot = 180
        self.power(net, end, rot, kind)
        return end

    def pin_nc(self, inst, pin):
        self.nc(inst.pin(pin))

    # --- emit --------------------------------------------------------------
    def emit(self, path, root_uuid, title_block=True):
        out = [Sym("kicad_sch"), [Sym("version"), 20260306], [Sym("generator"), "eeschema"],
               [Sym("generator_version"), "10.0"], [Sym("uuid"), self.uuid], [Sym("paper"), self.paper]]
        if title_block:
            tb = [Sym("title_block"), [Sym("title"), self.title], [Sym("date"), "2026-10-03"],
                  [Sym("rev"), "0.1"], [Sym("company"), "sbc-development-baseboard"]]
            for i, c in enumerate(self.comments[:4]):
                tb.append([Sym("comment"), i + 1, c])
            out.append(tb)
        libs = [Sym("lib_symbols")] + [self.lib_symbols[k] for k in sorted(self.lib_symbols)]
        out.append(libs)
        for kind, it in self.items:
            if kind == "symbol":
                out.append(self._symbol(it, root_uuid))
            elif kind == "wire":
                (a, b) = it
                out.append([Sym("wire"), [Sym("pts"), [Sym("xy"), a[0], a[1]], [Sym("xy"), b[0], b[1]]],
                            [Sym("stroke"), [Sym("width"), 0], [Sym("type"), Sym("default")]], [Sym("uuid"), uid()]])
            elif kind == "junction":
                out.append([Sym("junction"), [Sym("at"), it[0], it[1]], [Sym("diameter"), 0],
                            [Sym("color"), 0, 0, 0, 0], [Sym("uuid"), uid()]])
            elif kind == "nc":
                out.append([Sym("no_connect"), [Sym("at"), it[0], it[1]], [Sym("uuid"), uid()]])
            elif kind == "label":
                net, at, rot, glob, shape = it
                just = "left" if rot in (0, 90) else "right"
                if glob:
                    out.append([Sym("global_label"), net, [Sym("shape"), Sym(shape)], [Sym("at"), at[0], at[1], rot],
                                [Sym("fields_autoplaced"), Sym("yes")], effects(1.27, just), [Sym("uuid"), uid()],
                                [Sym("property"), "Intersheetrefs", "${INTERSHEET_REFS}", [Sym("at"), at[0], at[1], 0],
                                 [Sym("hide"), Sym("yes")], [Sym("show_name"), Sym("no")], [Sym("do_not_autoplace"), Sym("no")],
                                 effects(1.27, just)]])
                else:
                    out.append([Sym("label"), net, [Sym("at"), at[0], at[1], rot], [Sym("fields_autoplaced"), Sym("yes")],
                                effects(1.27, just + " bottom"), [Sym("uuid"), uid()]])
            elif kind == "text":
                s, at, size, bold = it
                e = [Sym("effects"), [Sym("font"), [Sym("size"), size, size]] + ([[Sym("bold"), Sym("yes")]] if bold else []),
                     [Sym("justify"), Sym("left"), Sym("bottom")]]
                out.append([Sym("text"), s, [Sym("exclude_from_sim"), Sym("no")], [Sym("at"), at[0], at[1], 0], e, [Sym("uuid"), uid()]])
            elif kind == "sheet":
                name, file, at, size, suuid, page = it
                out.append([Sym("sheet"), [Sym("at"), at[0], at[1]], [Sym("size"), size[0], size[1]],
                            [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")],
                            [Sym("dnp"), Sym("no")], [Sym("fields_autoplaced"), Sym("yes")],
                            [Sym("stroke"), [Sym("width"), 0.1524], [Sym("type"), Sym("solid")]],
                            [Sym("fill"), [Sym("color"), 0, 0, 0, 0]], [Sym("uuid"), suuid],
                            [Sym("property"), "Sheetname", name, [Sym("at"), at[0], round(at[1] - 0.7116, 4), 0],
                             [Sym("show_name"), Sym("no")], [Sym("do_not_autoplace"), Sym("no")], effects(1.27, "left bottom")],
                            [Sym("property"), "Sheetfile", file, [Sym("at"), at[0], round(at[1] + size[1] + 0.5846, 4), 0],
                             [Sym("show_name"), Sym("no")], [Sym("do_not_autoplace"), Sym("no")], effects(1.27, "left top")],
                            [Sym("instances"), [Sym("project"), self.project, [Sym("path"), "/" + root_uuid, [Sym("page"), str(page)]]]]])
        if self.sheet_path == "/":
            out.append([Sym("sheet_instances"), [Sym("path"), "/", [Sym("page"), "1"]]])
        out.append([Sym("embedded_fonts"), Sym("no")])
        open(path, "w", encoding="utf-8").write(dump(out) + "\n")
        import json
        json.dump(self.wire_log, open(path + ".wires.json", "w"))

    def _symbol(self, inst, root_uuid):
        X, Y, rot = inst.X, inst.Y, inst.rot
        x0, y0, x1, y1 = inst.bbox()
        two_pin = len(inst.pins) <= 2 and not inst.ref.startswith("#")
        vertical = False
        # a field's drawn angle is the symbol's rotation plus its own: give fields on a
        # rotated symbol an angle of 90 so they still read horizontally
        fangle = 90 if rot in (90, 270) else 0
        lib_just = {}
        if inst.ref.startswith("#PWR"):
            ref_at, val_at = (X, Y), (X, Y + (2.54 if inst.value == "GND" or inst.value.endswith("GND") else -3.81) if rot in (0, 180) else Y)
            ref_hide = True
        elif two_pin:
            pp = [inst.pin(n) for n in inst.pins]
            vertical = len(pp) == 2 and abs(pp[0][0] - pp[1][0]) < 1e-6    # pins stacked: text beside the part
            if not vertical:
                ref_at, val_at = (X, Y - 2.0), (X, Y + 2.0)
            else:
                ref_at, val_at = (X + 2.2, Y - 1.4), (X + 2.2, Y + 1.4)
            ref_hide = False
        else:
            # multi-pin parts: where the library put the fields, rotated with the symbol
            ref_at, val_at = (X, y0 - 2.54), (X, y1 + 2.54)
            for name in ("Reference", "Value"):
                pr = prop(inst.node, name)
                if pr is None:
                    continue
                at = [c for c in pr[3:] if isinstance(c, list) and c and c[0] == Sym("at")]
                eff = [c for c in pr[3:] if isinstance(c, list) and c and c[0] == Sym("effects")]
                if at and rot == 0:
                    pt = transform(float(at[0][1]), float(at[0][2]), X, Y, rot, inst.mirror)
                    if name == "Reference": ref_at = pt
                    else: val_at = pt
                else:
                    # a part turned round or on its side: both texts beside it, on the left, stacked
                    bx0 = inst.body()[0]
                    if name == "Reference": ref_at = (bx0 - 1.27, Y - 1.27)
                    else: val_at = (bx0 - 1.27, Y + 1.27)
                j = None
                if eff:
                    jj = [c for c in eff[0][1:] if isinstance(c, list) and c and c[0] == Sym("justify")]
                    if jj:
                        j = " ".join(str(x) for x in jj[0][1:] if str(x) in ("left", "right"))
                        if (rot == 180) != (inst.mirror == "y") and j:
                            j = {"left": "right", "right": "left"}.get(j, j)
                lib_just[name] = j or None
                if rot != 0:
                    lib_just[name] = "right"    # ending at the anchor (J() mirrors it when drawn at 180)
            ref_hide = False
        if inst.ref_at: ref_at = inst.ref_at
        if inst.val_at: val_at = inst.val_at
        just = "left" if two_pin and vertical else None
        # text drawn at 180 degrees is shown upright by KiCad with its justification mirrored
        flip = (fangle + rot) % 360 == 180
        def J(j):
            return {"left": "right", "right": "left"}.get(j, j) if (flip and j) else j

        def P(name, val, at, hide=False, j=just):
            p = [Sym("property"), name, val, [Sym("at"), at[0], at[1], fangle if name in ("Reference", "Value") else 0]]
            if hide: p.append([Sym("hide"), Sym("yes")])
            p += [[Sym("show_name"), Sym("no")], [Sym("do_not_autoplace"), Sym("no")],
                  effects(inst.field_size if name in ("Reference", "Value") else 1.27, j)]
            return p
        node = [Sym("symbol"), [Sym("lib_id"), f"{inst.libname}:{inst.name}"], [Sym("at"), X, Y, rot]]
        if inst.mirror:
            node.append([Sym("mirror"), Sym(inst.mirror)])
        node += [
                [Sym("unit"), inst.unit], [Sym("body_style"), 1], [Sym("exclude_from_sim"), Sym("no")],
                [Sym("in_bom"), Sym("no" if inst.ref.startswith("#") else "yes")], [Sym("on_board"), Sym("no" if inst.ref.startswith("#") else "yes")],
                [Sym("in_pos_files"), Sym("yes")], [Sym("dnp"), Sym("yes" if inst.dnp else "no")],
                [Sym("fields_autoplaced"), Sym("no")], [Sym("uuid"), inst.uuid],
                P("Reference", inst.ref, ref_at, hide=ref_hide, j=J(inst.ref_just or lib_just.get("Reference") or just)),
                P("Value", inst.value, val_at, hide=inst.hide_value, j=J(inst.val_just or lib_just.get("Value") or just)),
                P("Footprint", inst.footprint, (X, Y), hide=True),
                P("Datasheet", inst.datasheet, (X, Y), hide=True)]
        desc = prop(inst.node, "Description")
        node.append(P("Description", desc[2] if desc else "", (X, Y), hide=True))
        for k, v in inst.fields.items():
            node.append(P(k, v, (X, Y), hide=True))
        for pn in inst.pins:
            node.append([Sym("pin"), pn, [Sym("uuid"), uid()]])
        path = "/" + root_uuid + ("" if self.sheet_path == "/" else self.sheet_path)
        node.append([Sym("instances"), [Sym("project"), self.project, [Sym("path"), path, [Sym("reference"), inst.ref], [Sym("unit"), inst.unit]]]])
        return node
