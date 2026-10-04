"""Component-centric layout: nets fan out of a hub part as wires, and whatever
a net connects to is drawn at the end of its lane.

The model (from the OpenPilot Revolution reference): the hub IC sits in the
middle, its pins fan outward in diverging, non-crossing lanes; each lane ends
in an attachment -- a wire to a connector pin, an in-line series part, a
pull-up hanging from a rail with a junction, a power symbol, or (sparingly)
a net label for a net that leaves the page. Power pins of one rail share a
bus with the rail symbol at its end; decoupling sits in a row beside the IC.
"""
import os
from sch import snap, sp, G
from kisym import transform

PITCH = 2.54


# ----------------------------------------------------------------------------- attachments
def text_w(txt, glob=False):
    """Rendered width of 1.27 mm text (plus the global-label box)."""
    return 1.05 * len(txt) + (2.5 if glob else 1.0)


class Att:
    """Base attachment. render(s, E, sx, lane) draws from lane end E in direction sx.

    Layout metadata (all in mm, relative to the point the element is rendered at):
      h_up / h_down  how far a hanging element reaches above / below the lane
      lext           how far it spreads back toward the pin (text, symbol body)
      step           where the next element starts when the chain continues
      end_w          how far the content extends when this is the last element
      route          True for attachments that occupy the whole row (wires to elsewhere)
    """
    h_up = 0.0
    h_down = 0.0
    lext = 1.27       # how far a hanging element spreads back toward the pin
    ew = None         # how far it spreads onward (default: end_w)
    step = 5.08
    end_w = 1.27
    route = False

    def __init__(self, next=None):
        self.next = next

    def render(self, s, E, sx, lane):
        raise NotImplementedError

    def total_h(self):
        n = self
        up = dn = 0
        while n is not None:
            up, dn = max(up, n.h_up), max(dn, n.h_down)
            n = n.next
        return up, dn


def analyse(att):
    """Walk a chain: hanging elements [(offset, up, down, lext, ew)], whether the
    row is finite, and the offset of the end of its content (text included)."""
    elems, off, n = [], 0.0, att
    finite, end = True, 0.0
    while n is not None:
        if n.h_up > 0 or n.h_down > 0:
            elems.append((off, n.h_up, n.h_down, n.lext, n.ew if n.ew is not None else n.end_w))
        if n.route:
            finite = False
        if n.next is None:
            end = off + n.end_w
        else:
            off += n.step
        n = n.next
    return elems, finite, end


class L(Att):
    """Net label at the lane end (global/local chosen by the sheet's CROSS rule)."""
    def __init__(self, net, glob=None):
        super().__init__(None); self.net, self.glob = net, glob
        self.end_w = text_w(net, True)

    def render(self, s, E, sx, lane):
        s.label(self.net, E, 0 if sx > 0 else 180, self.glob)
        return E


class P(Att):
    """Power symbol at the lane end."""
    def __init__(self, rail):
        super().__init__(None); self.rail = rail
        if rail == "GND" or rail.endswith("GND"):
            self.h_down = 3.81
            self.lext = 2.0
        else:
            self.h_up = 5.08
            self.lext = max(1.5, 0.55 * len(rail) + 0.5)
        self.end_w = self.lext

    def render(self, s, E, sx, lane):
        s.power(self.rail, E, 0)
        return E


class Ser(Att):
    """Two-pin part in line with the wire; `near` says which pin touches the lane end.
    kind: 'R','C','L','FB','D' (Device:D_* via name), with lib/name overridable."""
    width = 7.62
    step = 7.62

    def __init__(self, kind, value, next, fp=None, lib=None, name=None, near="1", flip=False):
        super().__init__(next)
        self.kind, self.value, self.fp, self.lib, self.name, self.near, self.flip = kind, value, fp, lib, name, near, flip

    def render(self, s, E, sx, lane):
        far = (snap(E[0] + sx * 7.62), E[1])
        # vertical-library parts (R, C, L, FB) at rot 90 put pin 1 on the left; horizontal ones
        # (diodes, LED) at rot 0 put pin 1 (K) on the left.
        if self.kind in ("R", "C", "L", "FB"):
            make = {"R": s.R, "C": s.C, "L": s.L, "FB": s.FB}[self.kind]
            inst = make(self.value, (snap(E[0] + sx * 3.81), E[1]), rot=90, **({"fp": self.fp} if self.fp and self.kind != "FB" else {}))
            left, right = ("1", "2")
        else:
            inst = s.add(self.lib, self.name, s.ref("D"), self.value, (snap(E[0] + sx * 3.81), E[1]), 0, footprint=self.fp or "")
            left, right = ("1", "2")
        # pin at E must be `near`: if the pin naturally on E's side is not it, swap by rotating 180
        e_side_pin = left if sx > 0 else right
        if e_side_pin != self.near:
            inst.rot = (inst.rot + 180) % 360
        # make sure the near pin lands exactly on E (rotation about the centre keeps it)
        s.wire(E, inst.pin(self.near))
        other = "2" if self.near == "1" else "1"
        s.wire(inst.pin(other), far)
        # both texts above the part, inside the row pitch: ref ends left of centre, value starts right of it
        inst.ref_at = (inst.X - 0.4, E[1] - 1.4); inst.ref_just = "right"
        inst.val_at = (inst.X + 0.4, E[1] - 1.4); inst.val_just = "left"
        return self.next.render(s, far, sx, lane) if self.next else far


class Pull(Att):
    """A part hanging off the lane with a junction: up to a rail or down to a
    ground-like rail. kind: 'R', 'C', 'D' (Device:D_TVS), or a tuple
    (lib, name, top_pin) for anything else -- a zener, a switch, an LED."""
    def __init__(self, rail, kind, value, next, fp=None, ref_letter=None):
        super().__init__(next)
        self.rail, self.kind, self.value, self.fp, self.ref_letter = rail, kind, value, fp, ref_letter
        self.down = rail == "GND" or rail.endswith("GND")
        if self.down:
            self.h_down = 16.51
        else:
            self.h_up = 17.78
        self.end_w = 2.54 + text_w(value)

    def render(self, s, E, sx, lane):
        y = snap(E[1] + (6.35 if self.down else -6.35))
        if self.kind in ("R", "C"):
            make = {"R": s.R, "C": s.C}[self.kind]
            top, bot = "1", "2"
            inst = make(self.value, (E[0], y), rot=0, **({"fp": self.fp} if self.fp else {}))
        else:
            spec = self.kind if isinstance(self.kind, tuple) else ("Device", "D_TVS", "2")
            lib, name, top = spec[:3]
            letter = self.ref_letter or ("SW" if lib == "Switch" else "C" if name.startswith("C") else "D")
            if len(spec) > 3 and spec[3] == "v":     # vertical-library part: pin 1 on top at rot 0
                rot = 0 if top == "1" else 180
            else:
                rot = 90 if top == "2" else 270      # horizontal-library parts: pin 1 left at rot 0
            inst = s.add(lib, name, s.ref(letter), self.value, (E[0], y), rot, footprint=self.fp or "")
            bot = "1" if top == "2" else "2"
        if self.down:
            s.wire(E, inst.pin(top)); s.pin_power(inst, bot, self.rail)
        else:
            s.wire(E, inst.pin(bot)); s.pin_power(inst, top, self.rail)
        inst.ref_at = (E[0] + 2.54, y - 1.27); inst.val_at = (E[0] + 2.54, y + 1.27)
        if self.next is not None:
            s.junction(E)
            # continue the lane past the junction
            far = (snap(E[0] + sx * 5.08), E[1])
            s.wire(E, far)
            return self.next.render(s, far, sx, lane)
        return E


class PullLED(Att):
    """Resistor + LED hanging from the lane: down to GND (current flows lane ->
    R -> LED -> GND), or up to a rail (rail -> R -> LED -> lane)."""
    def __init__(self, color, r_value, next, fp_led=None, rail="GND"):
        super().__init__(next); self.color, self.r_value, self.fp_led, self.rail = color, r_value, fp_led, rail
        self.down = rail == "GND" or rail.endswith("GND")
        if self.down:
            self.h_down = 22.86
        else:
            self.h_up = 22.86
        self.end_w = 2.54 + text_w(r_value)

    def render(self, s, E, sx, lane):
        if self.down:
            r = s.R(self.r_value, (E[0], snap(E[1] + 5.08)), rot=0)
            d = s.LED(self.color, (E[0], snap(E[1] + 13.97)), rot=90, fp=self.fp_led)     # anode up
            s.wire(E, r.pin("1")); s.wire(r.pin("2"), d.pin("2")); s.pin_power(d, "1", self.rail)
        else:
            d = s.LED(self.color, (E[0], snap(E[1] - 5.08)), rot=90, fp=self.fp_led)      # cathode down, on the lane
            r = s.R(self.r_value, (E[0], snap(E[1] - 13.97)), rot=0)
            s.wire(E, d.pin("1")); s.wire(d.pin("2"), r.pin("2")); s.pin_power(r, "1", self.rail)
        r.ref_at = (E[0] + 2.54, r.Y - 1.27); r.val_at = (E[0] + 2.54, r.Y + 1.27)
        if self.next is not None:
            s.junction(E)
            far = (snap(E[0] + sx * 5.08), E[1]); s.wire(E, far)
            return self.next.render(s, far, sx, lane)
        return E


class Flag(Att):
    """A PWR_FLAG on the lane (for rails that arrive through passive parts)."""
    h_up = 7.62
    lext = 4.5
    end_w = 4.5

    def __init__(self, next):
        super().__init__(next)

    def render(self, s, E, sx, lane):
        s.flag(E, 0)
        if self.next is not None:
            far = (snap(E[0] + sx * 5.08), E[1]); s.wire(E, far)
            return self.next.render(s, far, sx, lane)
        return E


class Tag(Att):
    """A net label dropped on the lane; the lane carries on."""
    def __init__(self, net, next, glob=None):
        super().__init__(next); self.net, self.glob = net, glob
        self.step = max(5.08, snap(text_w(net, True) + 1.27))
        self.end_w = text_w(net, True)

    def render(self, s, E, sx, lane):
        s.label(self.net, E, 0 if sx > 0 else 180, self.glob)
        if self.next is not None:
            far = (snap(E[0] + sx * self.step), E[1]); s.wire(E, far)
            return self.next.render(s, far, sx, lane)
        return E


class BusEnd(Att):
    """Record the lane end under a key; bus_join() wires all such ends together."""
    registry = {}
    route = True

    def __init__(self, key):
        super().__init__(None); self.key = key

    def render(self, s, E, sx, lane):
        BusEnd.registry.setdefault((id(s), self.key), []).append(E)
        return E


def bus_join(s, key, then=None, sx=1):
    """Vertical wire through every BusEnd(key) point; `then` renders from the bottom end."""
    pts = sorted(BusEnd.registry.pop((id(s), key)), key=lambda p: p[1])
    x = pts[0][0]
    s.wire((x, pts[0][1]), (x, pts[-1][1]))
    for p in pts[1:-1]:
        s.junction(p)
    if then is not None:
        s.junction(pts[-1])
        far = (snap(x + sx * 5.08), pts[-1][1]); s.wire(pts[-1], far)
        then.render(s, far, sx, 0)


class Conn(Att):
    """Wire from the lane end to a placed instance's pin (Z-route, channel staggered by lane)."""
    route = True

    def __init__(self, inst, pin, stub=2.54):
        super().__init__(None); self.inst, self.pin, self.stub = inst, str(pin), stub
        self.channel_x = None          # set by fan(): beyond every lane's attachments

    def render(self, s, E, sx, lane, vertical=None):
        px, py = self.inst.pin(self.pin)
        d = self.inst.pin_dir(self.pin)
        dx, dy = {"L": (-self.stub, 0), "R": (self.stub, 0), "U": (0, -self.stub), "D": (0, self.stub)}[d]
        T = (snap(px + dx), snap(py + dy))
        if vertical is not None:                      # lane leaves a top/bottom pin: go vertical first
            chy = snap(E[1] + vertical * (2.54 + lane * 1.27))
            s.wire(E, (E[0], chy), (T[0], chy), T)
        elif abs(T[1] - E[1]) < 1e-6:
            s.wire(E, T)
        else:
            ch = self.channel_x if self.channel_x is not None else snap(E[0] + sx * (2.54 + lane * 1.27))
            s.wire(E, (ch, E[1]), (ch, T[1]), T)
        s.wire(T, (px, py))
        return T


class NC(Att):
    def render(self, s, E, sx, lane):
        s.nc(E); return E


class Skip(Att):
    """A pin whose wiring is drawn by other code (join_pins, a cluster): the fan
    reserves its row as a route so hanging neighbours keep clear, draws nothing."""
    route = True

    def render(self, s, E, sx, lane):
        return E


def chain_width(att):
    """Horizontal room a chain of attachments consumes before its last element."""
    w, n = 0.0, att
    while n is not None and n.next is not None:
        w += n.step
        n = n.next
    return w


def chain(*atts):
    """Link attachments: chain(Ser(...), Pull(...), L('X')) -> Ser.next = Pull, Pull.next = L."""
    for a, b in zip(atts, atts[1:]):
        n = a
        while n.next is not None:
            n = n.next
        n.next = b
    return atts[0]


# ----------------------------------------------------------------------------- fans
class End(Att):
    """Lane end exposed as a routing target under a key (for lane-to-lane routes)."""
    registry = {}
    route = True

    def __init__(self, key):
        super().__init__(None); self.key = key

    def render(self, s, E, sx, lane):
        End.registry[(id(s), self.key)] = (E, sx)
        return E


class To(Att):
    """Route from this lane end to an End(key) recorded by another fan on the sheet."""
    route = True

    def __init__(self, key):
        super().__init__(None); self.key = key; self.channel_x = None

    def render(self, s, E, sx, lane, vertical=None):
        T, tsx = End.registry[(id(s), self.key)]
        if abs(T[1] - E[1]) < 1e-6:
            s.wire(E, T)
        elif vertical is not None:
            chy = snap(E[1] + vertical * (2.54 + lane * 1.27))
            s.wire(E, (E[0], chy), (T[0], chy), T)
        else:
            ch = self.channel_x if self.channel_x is not None else snap(E[0] + sx * (2.54 + lane * 1.27))
            s.wire(E, (ch, E[1]), (ch, T[1]), T)
        return T


def fan(s, hub, atts, reach=None, min_pitch=PITCH, group_gap=0, align="center", channels=None):
    """Fan every pin in `atts` {pin: Att} out of the hub.

    Lanes on a side keep pin pitch wherever they can. A hanging element (pull,
    cap, flag, power symbol) reaches across the neighbouring rows, so it is slid
    along its lane until those rows have ended -- the staircase of pull-ups in
    the reference schematic. Only when a covered row cannot end (it is a route
    to another part) or two elements face each other is the pair spread apart
    vertically. Lanes that had to move turn in staggered columns so nothing
    crosses. `align` places a spread stack: "center" on the pin group, "top" or
    "bottom" flush with its first or last pin. `channels` fixes the x where routes
    turn (a value, or {side: value}) when the default would land on something
    else. Returns {pin: lane-end point}."""
    ends = {}
    by_side = {}
    seen_pos = set()
    for pin, att in atts.items():
        pos = hub.pin(str(pin))
        if pos in seen_pos:                      # co-located pins (VBUS x4, GND+EP): one lane serves all
            continue
        seen_pos.add(pos)
        d = hub.pin_dir(str(pin))
        by_side.setdefault(d, []).append((str(pin), att))
    reach_arg = reach
    for d, items in by_side.items():
        reach = reach_arg
        al = align.get(d, "center") if isinstance(align, dict) else align
        ch_base = channels.get(d) if isinstance(channels, dict) else channels
        if d in ("U", "D"):
            # vertical pins: short stubs only (power symbols / labels), no spreading
            items.sort(key=lambda it: hub.pin(it[0])[0])
            for j, (pin, att) in enumerate(items):
                end, _ = s.stub(hub, pin, 2.54 if j % 2 == 0 else 6.35)   # stagger so adjacent symbols do not overprint
                if isinstance(att, P):
                    gnd = att.rail == "GND" or att.rail.endswith("GND")
                    s.power(att.rail, end, 0 if (d == "U") != gnd else 180)
                elif isinstance(att, (Conn, To)):
                    att.render(s, end, 1, j, vertical=(-1 if d == "U" else 1))
                elif isinstance(att, L):
                    s.label(att.net, end, 90 if d == "U" else 270, att.glob)
                else:
                    att.render(s, end, 1, j)
                ends[pin] = end
            continue
        sx = 1 if d == "R" else -1
        items.sort(key=lambda it: hub.pin(it[0])[1])            # top to bottom
        n = len(items)
        ys = [hub.pin(p)[1] for p, _ in items]
        info = [analyse(a) for _, a in items]                   # (elems, finite, end_w)
        up_reach = [max((e[1] for e in el), default=0.0) for el, _, _ in info]
        dn_reach = [max((e[2] for e in el), default=0.0) for el, _, _ in info]
        finite = [f for _, f, _ in info]
        # 1) vertical placement: track the pins, spread only where an element would
        #    cross a row that cannot get out of its way
        rel = [0.0] * n
        facing = set()
        for i in range(1, n):
            r = max(rel[i - 1] + min_pitch, ys[i] - ys[0])
            for j in range(i):
                dj, ui = dn_reach[j], up_reach[i]
                dist = r - rel[j]
                if dj > 0 and ui > 0 and dj + ui + 1.27 > dist:
                    # elements facing each other across the band between the rows
                    if min(dj, ui) <= 7.62:
                        r = max(r, rel[j] + dj + ui + 1.27)          # a small one (power symbol, flag): stack them
                    else:
                        r = max(r, rel[j] + max(dj, ui) + 1.27)      # two tall ones: side by side, each clear of the other's row
                        facing.add((j, i))
                dist = r - rel[j]
                if dj + 1.27 > dist and not finite[i]:              # a route cannot get out of the way: spread
                    r = max(r, rel[j] + dj + 1.27)
                if ui + 1.27 > dist and not finite[j]:
                    r = max(r, rel[j] + ui + 1.27)
            rel[i] = snap(r)
        # 2) slide: an element that reaches a finite row starts beyond that row's content
        shift = [0.0] * n
        for _ in range(n + 2):
            changed = False
            for i in range(n):
                for (off, up, dn, lext, ew) in info[i][0]:
                    for j in range(n):
                        if j == i or not finite[j]:
                            continue
                        dist = rel[j] - rel[i]
                        covers = (dist < 0 and up + 1.27 > -dist) or (dist > 0 and dn + 1.27 > dist)
                        if not covers:
                            continue
                        req = shift[j] + info[j][2] + 1.27 + lext - off
                        if req > shift[i] + 1e-6:
                            shift[i] = snap(req + 1.26)
                            changed = True
            # facing elements share the band between the rows: the lower lane's element
            # starts past the upper lane's element
            for (j, i) in facing:
                for (offj, upj, dnj, lextj, ewj) in info[j][0]:
                    if dnj <= 0:
                        continue
                    for (offi, upi, dni, lexti, ewi) in info[i][0]:
                        if upi <= 0:
                            continue
                        req = shift[j] + offj + ewj + 1.27 + lexti - offi
                        if req > shift[i] + 1e-6:
                            shift[i] = snap(req + 1.26)
                            changed = True
            if not changed:
                break
        if os.environ.get("FAN_DEBUG") and hub.ref in os.environ["FAN_DEBUG"].split(","):
            print(f"[fan] {hub.ref} side {d}")
            for i, (pin, att) in enumerate(items):
                el, fin, endw = info[i]
                print(f"   {pin:>4} y={ys[i]:7.2f} rel={rel[i]:6.2f} shift={shift[i]:6.2f} end={endw:5.1f} finite={fin} elems={[(round(e[0],1), e[1], e[2]) for e in el]}")
        # 3) place the stack
        if al == "top":
            off = ys[0]
        elif al == "bottom":
            off = ys[-1] - rel[-1]
        else:
            off = (ys[0] + ys[-1]) / 2 - (rel[0] + rel[-1]) / 2
        lane_y = [snap(y + off) for y in rel]
        for i in range(1, n):
            if lane_y[i] < lane_y[i - 1] + min_pitch:
                lane_y[i] = snap(lane_y[i - 1] + min_pitch)
        # 4) turn stagger. Lanes going down: the topmost turns outermost (its vertical reaches past the
        #    pins below it). Lanes going up: the bottommost turns outermost. Up-lanes are always above
        #    down-lanes (travel is monotonic), so the two sets can share turn columns.
        travel = [lane_y[i] - ys[i] for i in range(n)]
        ks = [0] * n
        down = [i for i in range(n) if travel[i] > 1e-6]
        up = [i for i in range(n) if travel[i] < -1e-6]
        for j, i in enumerate(down):
            ks[i] = len(down) - 1 - j
        for j, i in enumerate(up):
            ks[i] = j
        maxk = max(ks) if ks else 0
        need = snap(2.54 + maxk * 1.27 + 5.08) if (down or up) else 5.08
        reach = need if reach is None else max(reach, need)
        # route channels start beyond the widest attachment chain of this fan
        px0 = hub.pin(items[0][0])[0]
        base = snap(px0 + sx * (reach + max(shift[i] + chain_width(a) for i, (_, a) in enumerate(items)) + 2.54))
        if ch_base is not None:
            base = snap(ch_base)
        for i, (pin, att) in enumerate(items):
            m = att
            while m is not None:
                if isinstance(m, (Conn, To)):
                    m.channel_x = snap(base + sx * i * 1.27)
                m = m.next
        for i, (pin, att) in enumerate(items):
            px, py = hub.pin(pin)
            Y = lane_y[i]
            xt = snap(px + sx * (2.54 + ks[i] * 1.27))
            E = (snap(px + sx * (reach + shift[i])), Y)
            if isinstance(att, Skip):
                ends[pin] = (px, py)
                continue
            if abs(Y - py) < 1e-6:
                s.wire((px, py), E)
            else:
                s.wire((px, py), (xt, py), (xt, Y), E)
            ends[pin] = att.render(s, E, sx, i)
    return ends


def rail_bus(s, hub, pins, rail, caps=None, cap_fp=None, reach=3.81):
    """Join same-rail pins on one side with a vertical bus; rail symbol at the
    outer end (top for a rail, bottom for GND). Optional decoupling caps hang
    from a horizontal extension of the bus."""
    pins = [str(p) for p in pins]
    pts = sorted((hub.pin(p) for p in pins), key=lambda q: q[1])
    d = hub.pin_dir(pins[0])
    sx = -1 if d == "L" else 1
    bx = snap(pts[0][0] + sx * reach)
    for (px, py) in pts:
        s.wire((px, py), (bx, py))
    top, bot = pts[0][1], pts[-1][1]
    gnd = rail == "GND" or rail.endswith("GND")
    if gnd:
        end = (bx, snap(bot + 2.54)); s.wire((bx, top), end); s.power(rail, end, 0)
    else:
        end = (bx, snap(top - 2.54)); s.wire(end, (bx, bot)); s.power(rail, end, 0)
    for (px, py) in pts[1:-1] if len(pts) > 2 else []:
        s.junction((bx, py))
    if len(pts) >= 2:
        s.junction((bx, pts[0][1]) if not gnd else (bx, pts[-1][1]))
    if caps:
        # cap row: horizontal wire from the bus end outward, caps hanging down to GND
        y = end[1]
        x = snap(bx + sx * 5.08)
        s.wire(end, (snap(bx + sx * (5.08 + 7.62 * (len(caps) - 1))), y))
        s.junction(end)
        for i, (val, fp) in enumerate(caps):
            cx = snap(x + sx * 7.62 * i)
            c = s.C(val, (cx, snap(y + 3.81 + 2.54)), rot=0, fp=fp or cap_fp)
            s.wire((cx, y), c.pin("1")); s.pin_power(c, "2", "GND")
            if i < len(caps) - 1 or True:
                s.junction((cx, y))
    return bx


def decap_row(s, rail, caps, at, gnd="GND"):
    """A row of decoupling caps under a shared rail wire; rail symbol at the left end."""
    x0, y = sp(at)
    xs = [snap(x0 + 10.16 * i) for i in range(len(caps))]
    s.wire((xs[0], y), (xs[-1], y))
    s.power(rail, (xs[0], y), 0)
    for i, entry in enumerate(caps):
        if len(entry) == 3 and entry[0] == "D":
            _, val, fp = entry
            c = s.add("Device", "D_TVS", s.ref("D"), val, (xs[i], snap(y + 6.35)), 90, footprint=fp or "")
            s.wire((xs[i], y), c.pin("2")); s.pin_power(c, "1", gnd)
        elif len(entry) == 3 and entry[0] == "R":
            _, val, fp = entry
            c = s.R(val, (xs[i], snap(y + 6.35)), rot=0, fp=fp)
            s.wire((xs[i], y), c.pin("1")); s.pin_power(c, "2", gnd)
        else:
            val, fp = entry[-2], entry[-1]
            c = s.C(val, (xs[i], snap(y + 6.35)), rot=0, fp=fp)
            s.wire((xs[i], y), c.pin("1")); s.pin_power(c, "2", gnd)
        if i < len(caps) - 1 or i == 0:
            s.junction((xs[i], y))
    return xs


def move_pin_to(inst, pin, point):
    """Shift a placed instance so that `pin`'s connection point is at `point`."""
    px, py = inst.pin(str(pin))
    tx, ty = sp(point)
    inst.X = snap(inst.X + (tx - px)); inst.Y = snap(inst.Y + (ty - py))
    return inst


def join_pins(s, hub, pins, length=2.54):
    """Short stubs from adjacent same-net pins joined by one wire along the
    fan column; the lane for the first pin continues from its stub end (a
    junction is placed there). Returns the stub end of the first pin."""
    pins = [str(p) for p in pins]
    ends = []
    for p in pins:
        e, _ = s.stub(hub, p, length)
        ends.append(e)
    ys = sorted(ends, key=lambda q: q[1])
    s.wire(ys[0], ys[-1])
    for e in ys[1:-1]:
        s.junction(e)
    s.junction(ends[0])
    return ends[0]


def xtal_cluster(s, hub, pin_a, pin_b, value, cap, fp_xtal, fp_cap=None, gnd24=False, reach=15.24):
    """Crystal between two adjacent hub pins, drawn vertically at the fan column,
    a load capacitor hanging from each lane to GND."""
    pa, pb = str(pin_a), str(pin_b)
    d = hub.pin_dir(pa); sx = -1 if d == "L" else 1
    (xa, ya), (xb, yb) = hub.pin(pa), hub.pin(pb)
    yc = snap((ya + yb) / 2)
    xq = snap(xa + sx * reach)
    name = "Crystal_GND24" if gnd24 else "Crystal"
    y = s.add("Device", name, s.ref("Y"), value, (xq, yc), 90, footprint=fp_xtal)   # rot 90: pin 1 down, pin 3/2 up
    top, bot = ("3", "1") if gnd24 else ("2", "1")
    # lanes: straight out to the cap column, cap hangs, then up/down into the crystal pin
    for p, (px, py), cpin in ((pa, (xa, ya), top if ya < yb else bot), (pb, (xb, yb), bot if ya < yb else top)):
        E = (snap(xa + sx * (reach - 7.62)), py)
        s.wire((px, py), E)
        c = s.C(cap, (E[0], snap(py + (-8.89 if py < yc else 8.89))), rot=0, fp=fp_cap)
        if py < yc:
            s.wire(E, c.pin("2")); s.pin_power(c, "1", "GND")
        else:
            s.wire(E, c.pin("1")); s.pin_power(c, "2", "GND")
        s.junction(E)
        T = y.pin(cpin)
        s.wire(E, (T[0], py), T)
    if gnd24:
        s.pin_power(y, "2", "GND")
    return y


def top_caps(s, hub, pin, caps, height=7.62, sx=1, up=False, rail=None):
    """A vertical supply pin with capacitors to GND on a short rail above (or
    below) it. Caps hang toward the symbol by default, away from it with `up`.
    `rail` names a power symbol to put at the far end of the rail."""
    p = str(pin)
    px, py = hub.pin(p)
    d = hub.pin_dir(p)
    T = (px, snap(py + (-height if d == "U" else height)))
    s.wire((px, py), T)
    xs = [snap(px + sx * 7.62 * (i + 1)) for i in range(len(caps))]
    end = (snap(xs[-1] + sx * 5.08), T[1]) if rail else (xs[-1], T[1])
    s.wire(T, end)
    s.junction(T) if len(caps) > 0 else None
    away = (d == "U") == (not up)        # +1: caps extend toward larger y
    for i, (val, fp) in enumerate(caps):
        cy = snap(T[1] + (6.35 if away else -6.35))
        c = s.C(val, (xs[i], cy), rot=0, fp=fp)
        if away:
            s.wire((xs[i], T[1]), c.pin("1")); s.pin_power(c, "2", "GND")
        else:
            s.wire((xs[i], T[1]), c.pin("2")); s.pin_power(c, "1", "GND")
        if i < len(caps) - 1 or rail:
            s.junction((xs[i], T[1]))
    if rail:
        gnd = rail == "GND" or rail.endswith("GND")
        s.power(rail, end, 0 if (d == "U") != gnd else 180)
    return T


def top_bus(s, hub, pins, rail, caps=None, rail_at="left", height=7.62, extra=None, caps_at=None, margin=5.08):
    """Join vertical power pins with a horizontal bus above (or below, for GND)
    the symbol: rail symbol at one end, decoupling capacitors hanging away from
    the symbol at `caps_at` ("left"/"right", default: the end opposite the rail).
    `extra` is an attachment rendered from the end opposite the rail (e.g. a
    ferrite bead to another rail). Returns the bus y."""
    pins = [str(p) for p in pins]
    pts = sorted((hub.pin(p) for p in pins), key=lambda q: q[0])
    d = hub.pin_dir(pins[0])
    sy = -1 if d == "U" else 1
    by = snap(pts[0][1] + sy * height)
    for (px, py) in pts:
        s.wire((px, py), (px, by))
    x0, x1 = pts[0][0], pts[-1][0]
    gnd = rail == "GND" or rail.endswith("GND")
    caps = caps or []
    ncap = len(caps)
    caps_at = caps_at or ("right" if rail_at == "left" else "left")
    cap_room = 7.62 * ncap
    ext_room = 7.62 if extra else 0.0
    left_room = (cap_room if caps_at == "left" else 0.0) + (margin if rail_at == "left" else 0.0) + (ext_room if rail_at == "right" else 0.0)
    right_room = (cap_room if caps_at == "right" else 0.0) + (margin if rail_at == "right" else 0.0) + (ext_room if rail_at == "left" else 0.0)
    bus_l, bus_r = snap(x0 - left_room), snap(x1 + right_room)
    rail_pt = (bus_l, by) if rail_at == "left" else (bus_r, by)
    s.wire((bus_l, by), (bus_r, by))
    s.power(rail, rail_pt, 0 if (d == "U") != gnd else 180)
    for (px, py) in pts:
        if abs(px - bus_l) > 1e-6 and abs(px - bus_r) > 1e-6:
            s.junction((px, by))
    cx = snap(x1 + 7.62) if caps_at == "right" else snap(x0 - 7.62)
    step = 7.62 if caps_at == "right" else -7.62
    far = (bus_r, by) if rail_at == "left" else (bus_l, by)
    for i, (val, fp) in enumerate(caps):
        x = snap(cx + step * i)
        c = s.C(val, (x, snap(by + sy * 6.35)), rot=0, fp=fp)
        if sy < 0:
            s.wire((x, by), c.pin("2")); s.pin_power(c, "1", "GND")
        else:
            s.wire((x, by), c.pin("1")); s.pin_power(c, "2", "GND")
        if abs(x - bus_l) > 1e-6 and abs(x - bus_r) > 1e-6:
            s.junction((x, by))
    if extra is not None:
        extra.render(s, far, 1 if rail_at == "left" else -1, 0)
    return by
