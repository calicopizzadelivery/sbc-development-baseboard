# Layout directives

What the board is placed from. Everything here comes from
[hardware-spec.md](hardware-spec.md) §2 and §8a and the block diagram; when
one of them changes, this file changes with it. The origin is the board's
top-left corner, X to the right, Y down, in millimetres, as KiCad draws it.

## Outline and stackup

- **140 × 80 mm**, 1.6 mm, 2 mm corner radius. Components on **both sides**
  by the rule under Sides below (2026-10-06; top side only before that).
- Advanced Circuits standard 4-layer 0.062": L1 signal (1 oz), 0.012"
  prepreg, L2 **ground plane** (1 oz), 0.028" core, L3 power / signal (1 oz),
  0.012" prepreg, L4 signal (1 oz). State it in the fab notes and ask for
  controlled impedance on the `USB` class.

## Mounting holes

Four M3, plated, on GND, centred **7 mm in from each corner**: (7, 7),
(133, 7), (7, 73), (133, 73), moved out from 10 mm on 2026-10-06 for 3 mm
more room inboard. A 6 mm standoff pad on each; the corner square of
10.5 mm around each hole carries nothing else. The edge connectors were
packed from 14 mm after each corner while the holes were at 10 mm and stay
where they are (their positions are locked in `gen/layout.py`).

## Edges and what faces where

The user sits at the **left** edge; the target is at the **right** edge; the
**front** long edge takes the overflow, each end matching its direction; the
**back** edge carries nothing, so the board can sit against a wall or a DIN
rail.

| Edge | Connectors, in order from the back corner to the front | Faces | Bodies (measured) |
|---|---|---|---|
| Left (x = 0), 54 mm usable | J10 RJ45 · J1 USB-C upstream · J2 USB-C PD in | workstation / charger | 22.4 + 10.6 + 10.6 = 43.6 mm |
| Right (x = 140), 54 mm usable | J3 USB-C HID · J13 console · J9 FTDI right-angle | target | 10.6 + 16.5 + 16.3 = 43.4 mm |
| Front (y = 80), left end | J4, J5 USB-A stacks · J18 PSU in · J19 PSU out | bench / PSU | 17.2 + 17.2 + 13.2 + 13.2 = 60.8 mm |
| Front (y = 80), right end | J14 +5V_TGT · J12, J11 relays | target | 13.2 + 13.05 + 13.05 = 39.3 mm |
| Inboard | J16 Cortex debug · J15 GPIO header · **J17 programming, top entry** (BM04B-SRSS-TB) | any | — |

Three things moved from the spec's first table once the footprints were
measured (2026-10-06): the RJ45 is 22 mm wide, not 16, so the left edge
could not also take J17, which is now a top-entry part inboard beside J2;
**J19 sits beside J18** so the PSU passthrough is one compact isolated
region behind the two of them instead of a strip across the board; and J9
takes J19's place on the right edge, where an FTDI header facing the
target belongs anyway. Bodies are packed 1 mm apart from 14 mm after each
corner. Edge connectors sit with their mating face flush with the edge, or
on the footprint's own "PCB Edge" mark where it has one (the USB-C
receptacles overhang by 1.1 mm). The mating face is the end of the body
farthest from the solder pins, which sit at the rear of every horizontal
connector in KiCad's library (the RJ45's long axis runs inboard, so it mates
along it); a pin header mates where its pins point. Checked in the 3D view.

## Keep-outs

- The 10.5 mm square at each corner (standoff pad and screw head): nothing
  but the hole, enforced as rule areas.
- **Isolation**: the PSU passthrough (J18, J19, K803's contact side, the
  opto-coupler's LED side, D807, R810, R811) sits in its own region behind
  J18/J19 at the front, x 48–84, y 42–80, with the barrier running through
  K803 between its coil and contact pins (x = 64) and through U801 between
  its LED and transistor pins (y = 42). It has its own **PSU_GND** copper on
  L2 with **no board ground plane under it**, and a 2 mm creepage gap to
  every board net, enforced by DRC rules (`sbc-baseboard.kicad_dru`: board
  nets' tracks and vias are kept out of the region, a board-net zone may not
  lie inside it, and the creepage clearance applies to every board-net item
  that carries a net; the relay's unused NC contact has no net and sits inside
  the region by placement). The L2 ground plane is drawn as one outline
  notched around the region from the front edge. Only the opto-coupler and
  the relay body cross the gap.
- **Lanes** (below): no part on either side inside a lane's corridor.
- Under the Ethernet magnetics (inside J10): no copper on any layer under
  the magnetics side of the jack.
- The back edge: nothing within 5 mm, so it can lie flat against a rail.
- No part other than an edge connector within 3 mm of any edge (a
  tailoring of ECSS-Q-ST-70-12C 14.3.2 c, whose 5 mm is for the assembler's
  conveyor; the assembler is consulted).
- Parent standard for everything not stated here: ECSS-Q-ST-70-12C Rev.1,
  with the tailorings listed in ecad-standards/layout.md section 0.

## Lanes

A lane is a corridor reserved for one routed path, from pad to pad through
axis-aligned legs, as wide as its class's track plus the class clearance plus
0.25 mm each side, kept free of parts on both sides of the board, and laid as
copper by the generator at the class width. Two lanes carry the PSU
passthrough (`LANES` in `gen/layout.py`):

| Lane | Net, class | Path |
|---|---|---|
| PSU_VP | PSU_VP, `PSU_3A` (2 mm) | J18 pin 1, up to y = 65, right to the x of K803 pin 6 (COM), up into the relay |
| PSU_VOUT | PSU_VOUT, `PSU_3A` (2 mm) | K803 pin 4 (NO), down to y = 73 under J19's body past its GND pin, left to the x of J19 pin 1, up into it |

PSU_GND goes from J18 pin 2 to J19 pin 2 through the PSU_GND island on L2.
The VP leg at y = 65 keeps the 2 mm creepage to the opto-coupler's board-side
pins (y ≤ 62); the VOUT leg at y = 73 clears J19's GND pad by the class
clearance. The lanes' corridors stop at the courtyards of the parts they join
and appear in the board as footprint keep-out rule areas named `lane_*`. The
USB 2.0 pairs get their lanes when the pairs are placed (standard, section
8.3).

## Sides

Connectors, ICs, relays, inductors, crystals and their load capacitors,
switches, jumpers, LEDs, test points, the bulk and large capacitors, the
parts of each buck's switching loop, the ESD arrays and the series parts on
the USB pairs, and every part on a `USB_VBUS_3A`, `PWR_6A` or `PSU_3A` net
stay on the **top**. Resistors and capacitors up to 1206, small diodes
(SOD-123) and SOT-23 transistors may go to the **bottom**, under the pin they
serve, 1 mm inside their host's courtyard edge, never within 1 mm of a
through-hole pad (hand soldering) or 0.6 mm of an exposed pad's via field.
The corner keep-outs, the 3 mm edge zone, the lanes and the isolation rule
apply on both sides. The bottom carries nothing taller than 3 mm (the
standoffs). The area this frees on top is for the blocks' copper zones.

## Placement

The connectors are locked where the edge table puts them (`CONNECTORS` in
`gen/layout.py`). The ICs are anchored by flow, below; the two parts that
straddle the isolation barrier are fixed; **every other part is placed by the
generator at the pin it serves** (ecad-standards/layout.md section 2): its
host is the placed part it shares the most specific nets with, a decoupling
capacitor's host is the IC the schematic draws it beside, it sits on the
host's side nearest that pin, turned so the pad on the host's net faces it,
and the parts along a side pack outward in rings. `placement.txt` beside the
board file records every part's host and ring (or the distance to its pin
where no ring had room). The generator lists the parts it could not keep
within 8 mm of their pin; those, and the indicator LEDs, are the first
things to refine by hand. The anchors are the second: they are the knobs.

| Part | (x, y, rot) | Why there |
|---|---|---|
| K803 | (56, 53, 0) | straddles the isolation barrier |
| U801 | (66, 60.5, 180) | straddles the isolation barrier |
| U301 | (30, 24, 0) | PHY behind J10, TX/RX pins toward the jack |
| U101 | (24, 52, 0) | PD controller at J2 |
| U102 | (31, 46, 0) | PD bus buffer |
| U103 | (56, 11, 0) | buck 1 (+5V_PORTS): SW on its right, the loop flows right |
| U104 | (56, 27, 0) | buck 2 (+5V_TGT) |
| U105 | (70, 33, 0) | +3V3 buck |
| U402 | (44, 40, 90) | hub: downstream pins toward J4/J5, upstream and crystal toward J1 |
| U201 | (96, 22, 270) | K64: RMII toward the PHY, port/FAULT/UART pins toward the hub and FTDI, GPIO toward J15 |
| U601 | (95, 47, 0) | DAPLink K20 |
| J601 | (88.5, 46, 0) | SWD to the K20 |
| U501 | (117, 51, 0) | FT231X behind J9 |
| K801 | (91, 60, 0) | relays behind J11 / J12 |
| K802 | (105, 60, 0) |  |
| U701 | (119, 61, 0) | +5V_TGT eFuse behind J14 |
| U704 | (118, 30, 0) | GPIO level shifter near J15 |
| U702 | (112, 37, 0) | console UART shifter near J13 |
| U703 | (123, 37, 0) | I2C shifter |

The LEDs and their resistors are not anchored: the generator puts them at
the nearest free spot to the pin that drives them, and they are moved by
hand to where they can be seen.

## Flow

Power enters at J2 on the left edge and moves right: the PD controller and
its parts at the connector, then the eFuse, then the bucks, then the rails
as polygons to each block. Signals read the same way, from the user's edge
on the left to the target's edge on the right. Each IC's own layout rules
are in [layout-guidelines.md](layout-guidelines.md).

## Special considerations

- **USB 2.0 pairs** (class `USB`, 0.35 mm / 0.20 mm, 90 Ω): on L1 over the
  L2 ground plane, routed as pairs, no stubs, length-matched within 1 mm,
  90 Ω end to end from the receptacle through the ESD array to the
  transceiver (standard 3.8). The USBLC6-2 arrays are flow-through: the
  receptacle's pair enters pins 1/3, the IC's pair leaves pins 6/4, and the
  two are separate nets, both in the `USB` class (`J1_D_?` and `HUB_UP_?`,
  `PORTn_D_?` and `HUB_DNn_?`, `J3_D_?` and `K64_USB_?`); the build refuses
  a pair outside the class. The arrays are placed first, on top, at the
  receptacle's signal pins, turned so pins 1/3 face the receptacle.
- **ESD on single lines** (PESD5V0S1UL on J9's four signals and J13's
  console, ESDA25W at the PD inlet): on top at the connector pin, first,
  the signal passing the diode's pad, the ground pad to the plane by a via.
- **High current**: `PSU_3A` (PSU_VP, PSU_VOUT, PSU_GND) and `USB_VBUS_3A`
  (VBUS_IN, PORTn_VBUS, FTDI_VBUS) at 2 mm or pours; `PWR_6A` (+5V_PORTS,
  +5V_TGT) at 4 mm or pours; two 0.5 mm vias per layer change on any of them.
- **Crystals** next to their IC, load capacitors between crystal and IC,
  no signals under them.
- **Bucks**: the SW node, catch diode and inductor in a tight loop; input
  capacitors against the VIN pin; a thermal pour under each regulator.
- **Silkscreen**: J9 pin 1 marked `BLK`, pin 6 `GRN`, TXD/RXD arrows; J11/J12
  COM/NO/NC; J18/J19 polarity; every connector's reference readable with the
  plug fitted.
