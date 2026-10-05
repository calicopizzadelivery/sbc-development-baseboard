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


def snap_up(v):
    """Round up to the connection grid."""
    import math
    return round(math.ceil(v / G - 1e-6) * G, 4)


# ----------------------------------------------------------------------------- attachments
from check_pins import text_w as glyph_w          # per-glyph stroke-font widths, calibrated against KiCad's PDF


def text_w(txt, glob=False):
    """Rendered width of 1.27 mm text (plus the label box)."""
    return glyph_w(txt, 1.27) + (2.5 if glob else 1.0)


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
    zones = None      # [(lo, hi)] distances from the lane where a wire may not cross (part body, symbol); None = all
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
    row is finite, the offset of the end of its content (text included), and the
    stretches [(a, b)] of the lane that carry a part or text (plain wire between
    them may be crossed)."""
    elems, off, n = [], 0.0, att
    finite, end, occ = True, 0.0, []
    while n is not None:
        ew = n.ew if n.ew is not None else n.end_w
        if n.h_up > 0 or n.h_down > 0:
            z = n.zones if n.zones is not None else [(0.0, max(n.h_up, n.h_down))]
            elems.append((off, n.h_up, n.h_down, n.lext, ew, z))
        if not isinstance(n, (Gap, Conn, To, End, BusEnd, Skip, NC)):
            occ.append((off - n.lext, off + (n.end_w if n.next is None else max(ew, n.lext + 0.1))))
            end = max(end, off + (n.end_w if n.next is None else ew))
        if n.route:
            finite = False
        if n.next is None:
            end = max(end, off + n.end_w)
        else:
            off += n.step
        n = n.next
    return elems, finite, end, occ


class L(Att):
    """Net label at the lane end (global/local chosen by the sheet's CROSS rule)."""
    def __init__(self, net, glob=None):
        super().__init__(None); self.net, self.glob = net, glob
        self.end_w = text_w(net, True)

    def render(self, s, E, sx, lane):
        s.label(self.net, E, 0 if sx > 0 else 180, self.glob)
        return E


class P(Att):
    """Power symbol at the lane end. `hook` = (dx, dy) moves it off the lane
    end by a stub up/down then sideways, for when the symbol would otherwise
    hang over a neighbouring wire."""
    def __init__(self, rail, hook=None):
        super().__init__(None); self.rail = rail; self.hook = hook
        if rail == "GND" or rail.endswith("GND"):
            self.h_down = 3.81
        else:
            self.h_up = 5.08
        self.lext = max(1.5, text_w(rail) / 2 + 0.5)                 # the symbol's name, centred on the lane end
        self.end_w = self.lext

    def render(self, s, E, sx, lane):
        if self.hook:
            dx, dy = self.hook
            p1 = (E[0], snap(E[1] + dy)); p2 = (snap(E[0] + dx), p1[1])
            s.wire(E, p1, p2)
            s.power(self.rail, p2, 0)
            return p2
        s.power(self.rail, E, 0)
        return E


class Ser(Att):
    """Two-pin part in line with the wire; `near` says which pin touches the lane end.
    kind: 'R','C','L','FB','D' (Device:D_* via name), with lib/name overridable."""
    width = 7.62
    lext = 1.5            # the reference, right-justified, reaches back a little past the lane end
    h_up = 2.2            # the texts sit above the part (outline is +-1.0), so the row above must be clear there
    zones = [(1.0, 2.2)]

    def __init__(self, kind, value, next, fp=None, lib=None, name=None, near="1", flip=False, tight=False, step=None):
        """tight: do not reserve the row above for the text (for columns of identical
        resistors at pin pitch, where the text just touches the neighbour's outline).
        step: override where the next element starts."""
        super().__init__(next)
        self.kind, self.value, self.fp, self.lib, self.name, self.near, self.flip = kind, value, fp, lib, name, near, flip
        self.ew = 4.2 + text_w(value)
        self.lext = 0.4 + text_w("R000")                                   # the reference, left of centre
        self.step = step if step is not None else max(7.62, snap(self.ew + 2.5 + 1.26))
        if tight:
            self.h_up = 0.0

    def render(self, s, E, sx, lane):
        far = (snap(E[0] + sx * self.step), E[1])
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
        # both texts above the part, small, inside the row pitch: the reference on the side the
        # lane came from, the (longer) value on the side it continues to
        inst.field_size = 1.0
        inst.ref_at = (inst.X - 0.4, E[1] - 1.6); inst.ref_just = "right"
        inst.val_at = (inst.X + 0.4, E[1] - 1.6); inst.val_just = "left"
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
            self.h_down = 17.78
        else:
            self.h_up = 19.05
        self.zones = [(3.0, 12.2), (13.5, 19.5)]                     # body with its pins; rail symbol and its name
        half = text_w(rail) / 2 + 0.5                                 # the rail symbol's name, centred on the part
        self.lext = max(1.27, half)
        self.end_w = max(2.54 + max(text_w(value), 5.0), half)
        self.text_step = max(5.08, snap(self.end_w + 1.5 + 1.26))   # used when the next part hangs the same way

    def render(self, s, E, sx, lane):
        y = snap(E[1] + (7.62 if self.down else -7.62))
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
        # text beside the part, on the side away from the pin
        inst.ref_at = (E[0] + sx * 2.54, y - 1.27); inst.val_at = (E[0] + sx * 2.54, y + 1.27)
        inst.ref_just = inst.val_just = "left" if sx > 0 else "right"
        if self.next is not None:
            s.junction(E)
            # continue the lane past the junction
            far = (snap(E[0] + sx * self.step), E[1])
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
        self.zones = [(0.0, 22.86)]
        self.end_w = 2.54 + max(text_w(r_value), text_w(color))
        self.text_step = max(5.08, snap(self.end_w + 1.5 + 1.26))

    def render(self, s, E, sx, lane):
        if self.down:
            r = s.R(self.r_value, (E[0], snap(E[1] + 5.08)), rot=0)
            d = s.LED(self.color, (E[0], snap(E[1] + 13.97)), rot=90, fp=self.fp_led)     # anode up
            s.wire(E, r.pin("1")); s.wire(r.pin("2"), d.pin("2")); s.pin_power(d, "1", self.rail)
        else:
            d = s.LED(self.color, (E[0], snap(E[1] - 5.08)), rot=90, fp=self.fp_led)      # cathode down, on the lane
            r = s.R(self.r_value, (E[0], snap(E[1] - 13.97)), rot=0)
            s.wire(E, d.pin("1")); s.wire(d.pin("2"), r.pin("2")); s.pin_power(r, "1", self.rail)
        for inst in (r, d):
            inst.ref_at = (E[0] + sx * 2.54, inst.Y - 1.27); inst.val_at = (E[0] + sx * 2.54, inst.Y + 1.27)
            inst.ref_just = inst.val_just = "left" if sx > 0 else "right"
        if self.next is not None:
            s.junction(E)
            far = (snap(E[0] + sx * self.step), E[1]); s.wire(E, far)
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
    def __init__(self, net, next, glob=None, step=None):
        super().__init__(next); self.net, self.glob = net, glob
        self.step = step if step else max(5.08, snap(text_w(net, True) + 3.81))   # a fixed step lines up lanes that share a bus
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


def bus_join(s, key, then=None, sx=1, then_down=False, at_top=False):
    """Vertical wire through every BusEnd(key) point; `then` renders from the
    bottom end (the top end with `at_top`, for a bus to a rail), sideways by
    default or straight on with `then_down`."""
    pts = sorted(BusEnd.registry.pop((id(s), key)), key=lambda p: p[1])
    x = pts[0][0]
    s.wire((x, pts[0][1]), (x, pts[-1][1]))
    for p in pts[1:-1]:
        s.junction(p)
    if then is not None:
        end = pts[0] if at_top else pts[-1]
        if then_down:
            far = (x, snap(end[1] + (-2.54 if at_top else 2.54))); s.wire(end, far)
        else:
            s.junction(end)
            far = (snap(x + sx * 5.08), end[1]); s.wire(end, far)
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


class Gap(Att):
    """A plain stretch of wire, to leave room on the lane (for a junction, say)."""
    def __init__(self, width, next=None):
        super().__init__(next); self.step = width; self.end_w = width

    def render(self, s, E, sx, lane):
        far = (snap(E[0] + sx * self.step), E[1]); s.wire(E, far)
        return self.next.render(s, far, sx, lane) if self.next else far


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
    """Link attachments: chain(Ser(...), Pull(...), L('X')) -> Ser.next = Pull, Pull.next = L.
    Two parts hanging the same way in a row are spaced so the first one's text
    clears the second."""
    for a, b in zip(atts, atts[1:]):
        n = a
        while n.next is not None:
            n = n.next
        n.next = b
    n = atts[0]
    while n is not None and n.next is not None:
        m = n.next
        if isinstance(n, (Pull, PullLED)) and isinstance(m, (Pull, PullLED, Ladder)) and (isinstance(m, Ladder) or n.down == m.down):
            n.step = max(n.step, n.text_step)
        n = m
    return atts[0]


def cap_pitch(caps):
    """Capacitor spacing in a ladder: wide enough for the longer of reference and value."""
    return [max(7.62, snap(2.54 + max(text_w(c[1] if c[0] == "CP" else c[0]), 5.0) + 1.5)) for c in caps]


class Ladder(Att):
    """A row of capacitors hanging from the lane into a GND rail below, with one
    GND symbol at the end; the lane carries on past them. caps: (value, fp) or
    ("CP", value, fp) for a polarised one."""
    def __init__(self, caps, next=None):
        super().__init__(next)
        self.caps = caps
        self.pitches = cap_pitch(caps)
        self.h_down = 7.62 + 6.35
        self.lext = 1.3
        last = caps[-1][1] if caps[-1][0] == "CP" else caps[-1][0]
        self.width = sum(self.pitches[:-1]) + max(5.08 + 2.5, 2.54 + text_w(last) + 1.0)   # up to the GND symbol or the last cap's text
        self.step = snap(self.width + 2.54)
        self.end_w = self.width
        self.ew = self.width

    def render(self, s, E, sx, lane):
        x_end, _ = ladder(s, E[0], E[1], sx, self.caps, pitches=self.pitches)
        s.wire(E, (x_end, E[1]))
        if self.next is not None:
            far = (snap(E[0] + sx * self.step), E[1])
            if abs(far[0] - x_end) > 1e-6:
                s.wire((x_end, E[1]), far)
            return self.next.render(s, far, sx, lane)
        return (x_end, E[1])


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
    """Route from this lane end to an End(key) recorded by another fan on the sheet.
    `direct`: turn at the target's own x (an L, arriving into the end from above
    or below) instead of in this fan's channel."""
    route = True

    def __init__(self, key, direct=False):
        super().__init__(None); self.key = key; self.channel_x = None; self.direct = direct

    def render(self, s, E, sx, lane, vertical=None):
        T, tsx = End.registry[(id(s), self.key)]
        if abs(T[1] - E[1]) < 1e-6:
            s.wire(E, T)
        elif self.direct:
            s.wire(E, (T[0], E[1]), T)
        elif vertical is not None:
            chy = snap(E[1] + vertical * (2.54 + lane * 1.27))
            s.wire(E, (E[0], chy), (T[0], chy), T)
        else:
            ch = self.channel_x if self.channel_x is not None else snap(E[0] + sx * (2.54 + lane * 1.27))
            s.wire(E, (ch, E[1]), (ch, T[1]), T)
        return T


def fan(s, hub, atts, reach=None, min_pitch=PITCH, group_gap=0, align="center", channels=None, side_dir=None, turn_at=None):
    """Fan every pin in `atts` {pin: Att} out of the hub.

    Lanes on a side keep pin pitch wherever they can. A hanging element (pull,
    cap, flag, power symbol) reaches across the neighbouring rows, so it is slid
    along its lane until those rows have ended -- the staircase of pull-ups in
    the reference schematic. Only when a covered row cannot end (it is a route
    to another part) or two elements face each other is the pair spread apart
    vertically. Lanes that had to move turn in staggered columns so nothing
    crosses. `align` places a spread stack: "center" on the pin group, "top" or
    "bottom" flush with its first or last pin. `channels` fixes the x where routes
    turn (a value, or {side: value}) when the default would land on something;
    `turn_at` likewise fixes the x of the innermost turn column (default 2.54 mm
    from the pin end) when a column would run through something placed beside the hub
    else. `side_dir` {pin: -1|1} says which way a chain on a top or bottom pin
    runs (default: to the right). Returns {pin: lane-end point}."""
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
        t_base = turn_at.get(d) if isinstance(turn_at, dict) else turn_at      # innermost turn column, when given
        side = d                                                               # d is reused as a distance below
        if d in ("U", "D"):
            # vertical pins: short stubs only (power symbols / labels), no spreading
            items.sort(key=lambda it: hub.pin(it[0])[0])
            for j, (pin, att) in enumerate(items):
                end, _ = s.stub(hub, pin, 2.54 if j % 2 == 0 else 6.35)   # stagger so adjacent symbols do not overprint
                if isinstance(att, P):
                    gnd = att.rail == "GND" or att.rail.endswith("GND")
                    if att.hook:                                            # sideways (and on) before the symbol
                        dx, dy = att.hook
                        far = (snap(end[0] + dx), snap(end[1] + dy))
                        s.wire(end, (far[0], end[1]), far)
                        end = far
                    s.power(att.rail, end, 0 if (d == "U") != gnd else 180)
                elif isinstance(att, (Conn, To)):
                    att.render(s, end, 1, j, vertical=(-1 if d == "U" else 1))
                elif isinstance(att, L):
                    s.label(att.net, end, 90 if d == "U" else 270, att.glob)
                else:
                    # a chain on a top or bottom pin: run sideways first so nothing hangs into the body
                    sxd = (side_dir or {}).get(int(pin) if pin.isdigit() else pin, 1)
                    lead = (snap(end[0] + sxd * 10.16), end[1])
                    s.wire(end, lead)
                    att.render(s, lead, sxd, j)
                ends[pin] = end
            continue
        sx = 1 if d == "R" else -1
        items.sort(key=lambda it: hub.pin(it[0])[1])            # top to bottom
        n = len(items)
        ys = [hub.pin(p)[1] for p, _ in items]
        info = [analyse(a) for _, a in items]                   # (elems, finite, end_w)
        up_reach = [max((e[1] for e in inf[0]), default=0.0) for inf in info]
        dn_reach = [max((e[2] for e in inf[0]), default=0.0) for inf in info]
        finite = [inf[1] for inf in info]
        # 1) vertical placement: track the pins, spread only where an element would
        #    cross a row that cannot get out of its way
        rel = [0.0] * n
        facing = set()
        for i in range(1, n):
            r = max(rel[i - 1] + max(min_pitch, ys[i] - ys[i - 1]), ys[i] - ys[0])
            for j in range(i):
                dist = r - rel[j]
                dj, ui = dn_reach[j], up_reach[i]
                j_reaches_i = dj + 1.27 > dist
                i_reaches_j = ui + 1.27 > dist
                # do any of j's downward elements line up horizontally with i's upward ones?
                xo = any(oj - lj <= oi + ewi and oi - li <= oj + ewj
                         for (oj, _, dj_, lj, ewj, _z) in info[j][0] if dj_ > 0
                         for (oi, ui_, _, li, ewi, _z2) in info[i][0] if ui_ > 0)
                if j_reaches_i and i_reaches_j:
                    # each reaches the other's row: sliding would chase forever, so spread
                    if xo and min(dj, ui) <= 7.62:
                        r = max(r, rel[j] + dj + ui + 1.27)          # a small one under a tall one: stack them
                    else:
                        r = max(r, rel[j] + max(dj, ui) + 2.54)      # side by side, each clear of the other's row and its label
                        if xo:
                            facing.add((j, i))
                elif dj > 0 and ui > 0 and dj + ui + 1.27 > dist and xo:
                    # neither reaches the other's row, but the elements would meet in between
                    if min(dj, ui) <= 7.62:
                        r = max(r, rel[j] + dj + ui + 1.27)
                    else:
                        r = max(r, rel[j] + max(dj, ui) + 2.54)
                        facing.add((j, i))
                dist = r - rel[j]
                if dj + 1.27 > dist and not finite[i]:              # a route cannot get out of the way: spread
                    r = max(r, rel[j] + dj + 1.27)
                if ui + 1.27 > dist and not finite[j]:
                    r = max(r, rel[j] + ui + 1.27)
            rel[i] = snap_up(r)
        # 2) slide: an element that reaches a finite row starts beyond that row's content
        shift = [0.0] * n
        for _ in range(n + 2):
            changed = False
            for i in range(n):
                for (off, up, dn, lext, ew, zones) in info[i][0]:
                    for j in range(n):
                        if j == i or not finite[j]:
                            continue
                        dist = rel[j] - rel[i]
                        covers = (dist < 0 and up + 1.27 > -dist) or (dist > 0 and dn + 1.27 > dist)
                        if not covers:
                            continue
                        xe = shift[i] + off
                        d = abs(dist)
                        if any(lo - 0.6 <= d <= hi + 0.6 for lo, hi in zones):
                            # the row would run into the part or its symbol: it must end before
                            spans = [(0.0, shift[j] + info[j][2])]
                        else:
                            spans = [(a + shift[j], b + shift[j]) for (a, b) in info[j][3]]
                        for (a2, b2) in spans:
                            if xe - lext < b2 + 1.27 and xe + ew > a2 - 1.27:
                                req = b2 + 1.27 + lext - off
                                if req > shift[i] + 1e-6:
                                    shift[i] = snap(req + 1.26)
                                    changed = True
            # facing elements share the band between the rows: one must start past the
            # other, text included. Slide whichever lane that costs less.
            for (j, i) in facing:
                for (offj, upj, dnj, lextj, ewj, _z) in info[j][0]:
                    if dnj <= 0:
                        continue
                    for (offi, upi, dni, lexti, ewi, _z2) in info[i][0]:
                        if upi <= 0:
                            continue
                        xj, xi = shift[j] + offj, shift[i] + offi
                        if xi - lexti >= xj + ewj + 1.27 - 1e-6 or xj - lextj >= xi + ewi + 1.27 - 1e-6:
                            continue
                        req_i = xj + ewj + 1.27 + lexti - offi          # slide i past j's element
                        req_j = xi + ewi + 1.27 + lextj - offj          # or j past i's
                        if req_i - shift[i] <= req_j - shift[j]:
                            shift[i] = snap(req_i + 1.26)
                        else:
                            shift[j] = snap(req_j + 1.26)
                        changed = True
            if not changed:
                break
        if os.environ.get("FAN_DEBUG") and hub.ref in os.environ["FAN_DEBUG"].split(","):
            print(f"[fan] {hub.ref} side {side}")
            for i, (pin, att) in enumerate(items):
                el, fin, endw = info[i][:3]
                print(f"   {pin:>4} y={ys[i]:7.2f} rel={rel[i]:6.2f} shift={shift[i]:6.2f} end={endw:5.1f} finite={fin} elems={[(round(e[0],1), e[1], e[2]) for e in el]}")
        # 3) place the stack
        if al == "top":
            off = ys[0]
        elif al == "bottom":
            off = ys[-1] - rel[-1]
        else:
            off = (ys[0] + ys[-1]) / 2 - (rel[0] + rel[-1]) / 2
        off = snap(off)                 # on the grid, so the spreads between rows survive the snap below
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
        # a lane going down turns outside every lane below it whose pin lies within its
        # vertical run; assign columns from the bottom up so each one clears just those
        for i in reversed(down):
            below = [ks[j] for j in down if j > i and ys[j] <= lane_y[i] + 1e-6]
            ks[i] = (max(below) + 1) if below else 0
        for i in up:
            above = [ks[j] for j in up if j < i and ys[j] >= lane_y[i] - 1e-6]
            ks[i] = (max(above) + 1) if above else 0
        maxk = max(ks) if ks else 0
        px0 = hub.pin(items[0][0])[0]
        t0 = t_base
        d0 = 2.54 if t0 is None else snap(abs(t0 - px0))
        need = snap(d0 + maxk * 1.27 + 5.08) if (down or up) else 5.08
        reach = need if reach is None else max(reach, need)
        # route channels start beyond the widest attachment chain of this fan
        base = snap(px0 + sx * (reach + max(shift[i] + max(chain_width(a), info[i][2]) for i, (_, a) in enumerate(items)) + 2.54))
        if ch_base is not None:
            base = snap(ch_base)
        if os.environ.get("FAN_DEBUG") and hub.ref in os.environ["FAN_DEBUG"].split(","):
            print(f"[fan] {hub.ref} side {side}: reach={reach} turn d0={d0} maxk={maxk} channel base={base}")
        k = 0
        for i, (pin, att) in enumerate(items):
            m, routed = att, False
            while m is not None:
                if isinstance(m, (Conn, To)):
                    m.channel_x = snap(base + sx * k * 1.27)
                    routed = True
                m = m.next
            k += routed
        s.channel_edge[(hub.ref, side)] = snap(base + sx * k * 1.27)      # for clusters drawn beyond the routes (crystal())
        for i, (pin, att) in enumerate(items):
            px, py = hub.pin(pin)
            Y = lane_y[i]
            xt = snap(px + sx * (d0 + ks[i] * 1.27))
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
    xs, x = [], x0
    for entry in caps:
        xs.append(snap(x))
        x += max(10.16, snap(2.54 + text_w(entry[-2]) + 1.5))
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


def ladder(s, x_first, y_top, sx, caps, gnd_sym=True, pitches=None):
    """A row of decoupling capacitors between a supply rail at y_top and a GND
    rail 7.62 below it, extending in direction sx from x_first (the first
    capacitor's x). The GND rail ends in one GND symbol pointing down. Returns
    the x where both rails end and the last capacitor's x."""
    if not caps:
        return x_first, x_first
    pitches = pitches or cap_pitch(caps)
    xs, x = [], x_first
    for i in range(len(caps)):
        xs.append(snap(x))
        x += sx * pitches[i]
    x_end = snap(xs[-1] + sx * 5.08)
    y_bot = snap(y_top + 7.62)
    s.wire((xs[0], y_bot), (x_end, y_bot))
    for i, cap in enumerate(caps):
        if cap[0] == "CP":
            c = s.CP(cap[1], (xs[i], snap(y_top + 3.81)), rot=0, fp=cap[2])
        else:
            val, fp = cap[-2], cap[-1]
            c = s.C(val, (xs[i], snap(y_top + 3.81)), rot=0, fp=fp)
        c.ref_at = (xs[i] + sx * 1.5 if sx > 0 else xs[i] - 1.5, snap(y_top + 3.81) - 1.27)
        c.val_at = (xs[i] + sx * 1.5 if sx > 0 else xs[i] - 1.5, snap(y_top + 3.81) + 1.27)
        c.ref_just = c.val_just = "left" if sx > 0 else "right"
        s.junction((xs[i], y_top))
        if i > 0:
            s.junction((xs[i], y_bot))
    if gnd_sym:
        s.power("GND", (x_end, y_bot), 0)
    return x_end, xs[-1]


def jog(s, hub, pin, rail, up=2.54, over=7.62):
    """A rail symbol on a vertical pin, moved sideways: stub `up`, run `over`
    (signed), then the symbol standing up (or GND hanging down). For supply
    pins so close together that their names would print over each other."""
    p = str(pin)
    px, py = hub.pin(p)
    d = hub.pin_dir(p)
    gnd = rail == "GND" or rail.endswith("GND")
    T = (px, snap(py + (-up if d == "U" else up)))
    J = (snap(px + over), T[1])
    s.wire((px, py), T, J)
    s.power(rail, J, 0 if (d == "U") != gnd else 180)
    return J


def crystal(s, hub, key_a, key_b, ref, value, fp, cap, cap_fp=None, drop=10.16, margin=8.89):
    """A clock source drawn to flow downward. The two XTAL lanes end in End(key_a) and
    End(key_b); from there they run on, beyond the hub's route channels, to two columns
    7.62 mm apart and drop straight down: through the crystal's pins (the crystal lies
    across the two columns), on into one load capacitor each, and into a shared GND rail
    with one GND symbol under the crystal, which also takes the crystal's own ground pins.
    The upper lane takes the outer column, so nothing crosses. Every wire meets its part
    at a right angle; the texts sit on the outer side, away from the hub."""
    (Ea, sx), (Eb, _) = End.registry[(id(s), key_a)], End.registry[(id(s), key_b)]
    E_hi, E_lo = (Ea, Eb) if Ea[1] <= Eb[1] else (Eb, Ea)
    edge = s.channel_edge[(hub.ref, "L" if sx < 0 else "R")]
    x_near = snap(edge + sx * margin)                  # room beside the near capacitor for its text
    x_far = snap(x_near + sx * 7.62)
    xc = snap((x_near + x_far) / 2)
    y_cr = snap(max(E_hi[1], E_lo[1]) + drop)
    for E, x in ((E_hi, x_far), (E_lo, x_near)):
        s.wire(E, (x, E[1]), (x, y_cr)); s.junction((x, y_cr))
    four = fp is None or "4Pin" in fp or "4-Pin" in fp or "GND24" in fp
    y = s.add("Device", "Crystal_GND24" if four else "Crystal", ref, value, (xc, y_cr), 0, footprint=fp or "")
    just_out, just_in = ("right", "left") if sx < 0 else ("left", "right")
    y.ref_at, y.val_at = (snap(x_far + sx * 1.27), snap(y_cr - 1.27)), (snap(x_far + sx * 1.27), snap(y_cr + 1.27))
    y.ref_just = y.val_just = just_out
    y_cap, y_rail = snap(y_cr + 10.16), snap(y_cr + 13.97)
    for x, out in ((x_far, True), (x_near, False)):
        c = s.C(cap, (x, y_cap), rot=0, **({"fp": cap_fp} if cap_fp else {}))
        s.wire((x, y_cr), (x, snap(y_cap - 3.81)))
        tx = snap(x + sx * 2.2) if out else snap(x - sx * 2.2)
        c.ref_at, c.val_at = (tx, snap(y_cap - 1.4)), (tx, snap(y_cap + 1.4))
        c.ref_just = c.val_just = just_out if out else just_in
    # the rail in two pieces meeting under the crystal: a pin only connects at a wire end
    s.wire((x_far, y_rail), (xc, y_rail)); s.wire((xc, y_rail), (x_near, y_rail)); s.junction((xc, y_rail))
    if four:
        s.wire((xc, snap(y_cr + 5.08)), (xc, y_rail))
    s.power("GND", (xc, y_rail), 0)
    return y


def mark_end(s, key, pt, sx=1):
    """Register a point as a route target (as End would) for To() routes."""
    End.registry[(id(s), key)] = (pt, sx)


def top_caps(s, hub, pin, caps, height=12.7, sx=1, up=False, rail=None):
    """A vertical supply pin with its decoupling on a short rail beside it: the
    capacitors hang from the rail into a GND rail below, one GND symbol at the
    end pointing down, and the supply symbol (if `rail`) above it. For a pin on
    the top edge the rail needs height >= 12.7 so the GND rail clears the pins."""
    p = str(pin)
    px, py = hub.pin(p)
    d = hub.pin_dir(p)
    if d == "U" and caps:
        height = max(height, 12.7)
    T = (px, snap(py + (-height if d == "U" else height)))
    s.wire((px, py), T)
    x_end, x_last = ladder(s, snap(px + sx * 7.62), T[1], sx, caps)
    x_rail = snap(x_end + sx * 3.81) if up else x_end     # caps hanging up: one more step so the rail's name clears their GND rail
    s.wire(T, (x_rail if rail else x_last, T[1]))
    if rail:
        gnd = rail == "GND" or rail.endswith("GND")
        s.power(rail, (x_rail, T[1]), 180 if gnd else 0)
    return T


def top_bus(s, hub, pins, rail, caps=None, rail_at="left", height=7.62, extra=None, caps_at=None, margin=5.08,
            caps_left=None, caps_right=None):
    """Join vertical power pins with a horizontal bus above (or below, for GND)
    the symbol. Decoupling capacitors hang from the bus beyond the pins, on
    either side, into a GND rail below them (`ladder`). The rail symbol stands
    at the `rail_at` end, past that side's ladder; `extra` is an attachment
    rendered from the other end (e.g. a ferrite bead to another rail)."""
    pins = [str(p) for p in pins]
    pts = sorted((hub.pin(p) for p in pins), key=lambda q: q[0])
    d = hub.pin_dir(pins[0])
    sy = -1 if d == "U" else 1
    if caps and caps_left is None and caps_right is None:
        if (caps_at or ("right" if rail_at == "left" else "left")) == "left":
            caps_left = caps
        else:
            caps_right = caps
    caps_left, caps_right = caps_left or [], caps_right or []
    if d == "U" and (caps_left or caps_right):
        height = max(height, 12.7)
    by = snap(pts[0][1] + sy * height)
    for (px, py) in pts:
        s.wire((px, py), (px, by))
    x0, x1 = pts[0][0], pts[-1][0]
    gnd = rail == "GND" or rail.endswith("GND")
    if caps_left:
        end_l, last_l = ladder(s, snap(x0 - 7.62), by, -1, caps_left)
        bus_l = end_l if (rail_at == "left" or extra is not None and rail_at == "right") else last_l
    else:
        bus_l = snap(x0 - (margin if rail_at == "left" else 0))
    if caps_right:
        end_r, last_r = ladder(s, snap(x1 + 7.62), by, 1, caps_right)
        bus_r = end_r if (rail_at == "right" or extra is not None and rail_at == "left") else last_r
    else:
        bus_r = snap(x1 + (margin if rail_at == "right" else 0))
    s.wire((bus_l, by), (bus_r, by))
    rail_pt = (bus_l, by) if rail_at == "left" else (bus_r, by)
    s.power(rail, rail_pt, 0 if (d == "U") != gnd else 180)
    for (px, py) in pts:
        if abs(px - bus_l) > 1e-6 and abs(px - bus_r) > 1e-6:
            s.junction((px, by))
    if extra is not None:
        far = (bus_r, by) if rail_at == "left" else (bus_l, by)
        s.junction(far) if (caps_right if rail_at == "left" else caps_left) else None
        extra.render(s, far, 1 if rail_at == "left" else -1, 0)
    return by
