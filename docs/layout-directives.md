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
**back** edge carries the RJ45 alone (2026-10-06: moved there from the left
edge so the two USB-C inlets could spread out around the middle of the left
edge and the lower-left corner stopped crowding; the board no longer lies
flat against a wall or a DIN rail, which the spec accepted).

| Edge | Connectors, in order from the back corner to the front | Faces | Bodies (measured) |
|---|---|---|---|
| Left (x = 0), 54 mm usable | J2 USB-C PD in (centred y = 30) · J1 USB-C upstream (centred y = 54), split around the middle | charger / workstation | 10.6 + 10.6 = 21.2 mm |
| Back (y = 0), 114 mm usable | J10 RJ45, from x = 14 | workstation | 19.0 mm wide, 22.4 mm deep |
| Right (x = 140), 54 mm usable | J3 USB-C HID · J13 console · J9 FTDI right-angle | target | 10.6 + 16.5 + 16.3 = 43.4 mm |
| Front (y = 80), left end | J5, J4 USB-A stacks (J5 at x = 19, J4 at x = 37: swapped on 2026-10-06 so each stack's pairs reach the hub row they are wired to without crossing) · J18 PSU in · J19 PSU out | bench / PSU | 17.2 + 17.2 + 13.2 + 13.2 = 60.8 mm |
| Front (y = 80), right end | J14 +5V_TGT · J12, J11 relays | target | 13.2 + 13.05 + 13.05 = 39.3 mm |
| Inboard | J16 Cortex debug · J15 GPIO header · **J17 programming, top entry** (BM04B-SRSS-TB) | any | — |

Four things moved from the spec's first table once the footprints were
measured (2026-10-06): the RJ45 is 22 mm wide, not 16, so the left edge
could not also take J17, which is now a top-entry part inboard beside the
PD controller; the RJ45 then went to the back edge so J1 and J2 could spread;
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

The pairs are lanes too (standard, section 2 step 5 and section 3.8): the
generator lays both members at the class geometry, matched in length, with
the escapes, the receptacles' bridges and the layer changes it needs, and
refuses a lane whose members would cross. The ESD arrays and the series
parts are anchored so the lanes can be declared before placement.

| Pair lane | From | To | Path | Layer changes |
|---|---|---|---|---|
| J1_D | J1 (B7/A6 members; A7/B6 bridged behind the row) | U401 | direct | — |
| HUB_UP | U401 | U402 pins 59/58 | right to x = 15, up to the pins' row under the port pairs, right into the hub | 2 (under HUB_DN6/DN7) |
| PORT1_D, PORT3_D | J4 / J5 front rows | U408 / U410 | direct, straight above their pads | — |
| PORT2_D, PORT4_D | J4 / J5 back rows | U409 / U411 | single-net lanes on the bottom through the front row's pin gaps, up to the array's pads | 1 each |
| HUB_DN4, HUB_DN5 | U408, U409 | U402 bottom row | up, right, up (DN4); straight up (DN5) | — |
| HUB_DN6, HUB_DN7 | U410, U411 | U402 left row | up the left of the hub, right into the row, nested, 1.2 mm apart | — |
| HUB_DN1 | U402 pins 2/1 | R602/R603 (hub side) | down, under the port pairs on the bottom, up along x = 50.5, right above the relay at y = 38.75 | 2 |
| K20_USB | R602/R603 | U601 pins 3/4 | right, down into the K20's left row | — |
| HUB_DN2 | U402 pins 4/3 | R505/R504 (hub side) | down, under the port pairs, up along x = 52.1, right above the relay at y = 41.5, down past the DAPLink at x = 86.5, right under it at y = 51.5, down at x = 112, right under the FTDI at y = 57, up at x = 126.5, left into the resistors | 2 |
| FTDI_USB | R505/R504 | U501 pins 11/12 | direct | — |
| J3_D | J3 (A7/A6 middle members; B7/B6 bridged at both ends of the row) | U202 | direct | — |
| K64_USB | U202 | U201 pins 10/11 | left, up to y = 6 along the back edge, left, down into the K64's top row | — |
| ETH_TD, ETH_RD | J10 pins 1/2, 3/6 | U301 pins 6/5, 4/3 | 100 Ω class ETH; TD jogs right to its pins, RD straight down | — |

Four arrays (U408 to U411) and U202 are drawn with the house symbol
USBLC6-2SC6-IO2up (D- on I/O2), because with their connector-side pins toward
the receptacle the pair would otherwise cross itself (standard 3.8); U401
keeps the stock symbol. The hub's two downstream pairs for the K20 and the
FTDI leave adjacent 0.5 mm pins: their centre lines are shifted 0.1 mm
apart and the FTDI pair turns first.
The VP leg at y = 65 keeps the 2 mm creepage to the opto-coupler's board-side
pins (y ≤ 62); the VOUT leg at y = 73 clears J19's GND pad by the class
clearance. The lanes' corridors stop at the courtyards of the parts they join
and appear in the board as footprint keep-out rule areas named `lane_*`. The
USB 2.0 pairs get their lanes when the pairs are placed (standard, section
8.3).

## Planes

L2 (In1.Cu) is the ground plane, one outline notched around the isolation
region. L3 (In2.Cu) carries the rails as regions, the +3V3 plane underneath
at the lowest priority and the others carving it: VBUS_IN top-left to the
bucks' VIN pins; +5V_PORTS from L101 along the back, down the middle beside
the relay and along the band above the USB-A stacks, plus a strip under the
relays and the FTDI switch; +5V_TGT from L102 along the back and right
edges to the eFuse and J14, with a tab to the level shifter. The autorouter
drops vias into them; the regions are adjusted by hand where it could not.

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
| U301 | (23.5, 29, 270) | PHY below J10 on the back edge, TX/RX pins up toward the jack |
| U101 | (15, 36, 0) | PD controller at J2 |
| U102 | (26, 35, 0) | PD bus buffer |
| J17 | (31, 49, 0) | Qwiic programming, top entry, beside the PD controller |
| U103 | (56, 11, 0) | buck 1 (+5V_PORTS): SW on its right, the loop flows right |
| U104 | (56, 27, 0) | buck 2 (+5V_TGT) |
| U105 | (70, 33, 0) | +3V3 buck |
| U402 | (44, 40, 90) | hub: downstream pins toward J4/J5, upstream and crystal toward J1 |
| U201 | (96, 22, 270) | K64: RMII toward the PHY, port/FAULT/UART pins toward the hub and FTDI, GPIO toward J15 |
| J16 | (83, 10, 0) | SWD to the K64 |
| U601 | (97, 47, 0) | DAPLink K20 |
| J601 | (104, 44, 0) | SWD to the K20 |
| U501 | (117, 51, 0) | FT231X behind J9 |
| K801 | (91, 60, 0) | relays behind J11 / J12 |
| K802 | (105, 60, 0) |  |
| U701 | (119, 61, 0) | +5V_TGT eFuse behind J14 |
| U704 | (118, 30, 0) | GPIO level shifter near J15 |
| U702 | (112, 37, 0) | console UART shifter near J13 |
| U703 | (123, 37, 0) | ESD arrays at their receptacles, in line with the pair, and the series parts of the K20 and FTDI pairs |
| U401 | (10.3, 54, 0) | J1 upstream array, pins 1/3 toward J1 |
| U202 | (129.7, 19.34, 180) | J3 array |
| U408 | (40.78, 59, -90) | J4 front row (port 1) -> hub DN4, straight above its pads |
| U409 | (45.5, 57.4, -90) | J4 back row (port 2) -> hub DN5, reached on the bottom around the pin rows |
| U410 | (20, 59, -90) | J5 front row (port 3) -> hub DN6 |
| U411 | (25.2, 59, -90) | J5 back row (port 4) -> hub DN7 |
| R602 | (88.6, 37.75, 180) | K20 pair series resistors, P above N as the lane arrives from the left |
| R603 | (88.6, 39.75, 180) |  |
| R504 | (123.5, 52.6, 0) | FTDI pair series resistors, N above P as the lane arrives from the right |
| R505 | (123.5, 54.5, 0) | I2C shifter |
| J15 | (117, 10, 0) | GPIO header, inboard |

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
