# Layout directives

What the board is placed from. Everything here comes from
[hardware-spec.md](hardware-spec.md) §2 and §8a and the block diagram; when
one of them changes, this file changes with it. The origin is the board's
top-left corner, X to the right, Y down, in millimetres, as KiCad draws it.

## Outline and stackup

- **140 × 100 mm**, 1.6 mm, 2 mm corner radius (140 × 80 until 2026-10-07,
  when 20 mm of board was added below y = 52: everything behind the front
  edge, from the USB-A stacks and the passthrough region to the relays and
  the eFuse, moved 20 mm with the edge, and the band between the hub, the
  3V3 buck and the K20 and the front-edge blocks is the room gained. The
  routed 140 × 80 board was discarded with the change and stays in history).
  Components on **both sides** by the rule under Sides below (2026-10-06; top
  side only before that).
- Advanced Circuits standard 4-layer 0.062": L1 signal (1 oz), 0.012"
  prepreg, L2 **ground plane** (1 oz), 0.028" core, L3 power / signal (1 oz),
  0.012" prepreg, L4 signal (1 oz). State it in the fab notes and ask for
  controlled impedance on the `USB` class.

## Mounting holes

Four M3, plated, on GND, centred **7 mm in from each corner**: (7, 7),
(133, 7), (7, 93), (133, 93), moved out from 10 mm on 2026-10-06 for 3 mm
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

| Edge | Connectors, in order from the back corner to the front | Faces | Courtyards (measured) |
|---|---|---|---|
| Left (x = 0), 74 mm usable | J2 USB-C PD in (centred y = 30) · J1 USB-C upstream (centred y = 74), split around the middle | charger / workstation | 10.6 + 10.6 = 21.2 mm |
| Back (y = 0), 114 mm usable | J10 RJ45, from x = 71 (from x = 14 until 2026-10-07, when the two bucks took the back-edge corner beside J2) | workstation | 19.0 mm wide, 22.4 mm deep |
| Right (x = 140), 74 mm usable | J3 USB-C HID (centred y = 19.3) · J13 console (origin y = 49.2) · J9 FTDI right-angle (origin y = 65.0), J13 moved 10 mm and J9 20 mm down the edge on 2026-10-07, leaving 11 mm between courtyards (they were packed 1.5 mm apart in the back half) | target | 10.6 + 16.5 + 16.3 = 43.4 mm |
| Front (y = 100), left end | J5, J4 USB-A stacks (J5 at x = 19, J4 at x = 37: swapped on 2026-10-06 so each stack's pairs reach the hub row they are wired to without crossing) · J18 PSU in (x = 56.4) · J19 PSU out (x = 70.7), both 2 mm right since 2026-10-08 so J4's shield pads stand 2.6 mm from the passthrough region (their copper still enters its 2 mm creepage band by 0.9 mm; the fills keep the creepage, DRC agrees) | bench / PSU | 17.2 + 17.2 + 13.2 + 13.2 = 60.8 mm |
| Front (y = 100), right end | J14 +5V_TGT · J12, J11 relays | target | 13.2 + 13.05 + 13.05 = 39.3 mm |
| Inboard | J16 Cortex debug · J15 GPIO header · **J17 programming, top entry** (BM04B-SRSS-TB) | any | — |

Four things moved from the spec's first table once the footprints were
measured (2026-10-06): the RJ45's courtyard runs 22 mm along the edge, not 16, so the left edge
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
  J18/J19 at the front, x 50–86, y 62–100 (x 48–84 until 2026-10-08, y
  42–80 on the 80 mm board), with the barrier running through K803 between
  its coil and contact pins and through U801 between its LED and transistor
  pins, both at x = 66. A part of the region keeps the 2 mm creepage from
  every part and connector outside it by placement, and a board-net plane
  that enters the region's grown outline is refused at generation. It has its own **PSU_GND** copper on
  L2 with **no board ground plane under it**, and a 2 mm creepage gap to
  every board net, enforced by DRC rules (`sbc-baseboard.kicad_dru`: board
  nets' tracks and vias are kept out of the region, a board-net zone may not
  lie inside it, and the creepage clearance applies to every board-net item
  that carries a net; the relay's unused NC contact has no net and sits inside
  the region by placement). The L2 ground plane is drawn as one outline
  notched around the region from the front edge. Only the opto-coupler and
  the relay body cross the gap.
- **Lanes** (below): no part on either side inside a lane's corridor.
- Under J10: no plane or pour on any layer under the jack's body (its pins
  span the body, so the whole body is the void; the pins' tracks pass),
  drawn by the generator as the rule area `void_J10_magnetics` from
  `COPPER_VOIDS`.
- **Voids between cities** (standard 3.1): every two parts of different
  schematic islands on one side of the board keep 2 mm apart; the routing
  between blocks runs in those voids. The void holds per side, so a split
  channel's switch may sit under the other channel's. Connectors, holes, ESD parts and lone
  symbols at a connector stand outside the cities.
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
| PSU_VP | PSU_VP, `PSU_3A` (2 mm) | J18 pin 1, up to y = 85, right to the x of K803 pin 6 (COM), up into the relay |
| PSU_VOUT | PSU_VOUT, `PSU_3A` (2 mm) | K803 pin 4 (NO), down to y = 93 under J19's body past its GND pin, left to the x of J19 pin 1, up into it |

PSU_GND goes from J18 pin 2 to J19 pin 2 through the PSU_GND island on L2.

The pairs are lanes too (standard, section 2 step 5 and section 3.8): the
generator lays both members at the class geometry, matched in length, with
the escapes, the receptacles' bridges and the layer changes it needs, and
refuses a lane whose members would cross. The ESD arrays and the series
parts are anchored so the lanes can be declared before placement.

| Pair lane | From | To | Path | Layer changes |
|---|---|---|---|---|
| J1_D | J1 (B7/A6 members; A7/B6 bridged behind the row) | U401 | direct | — |
| HUB_UP | U401 | U402 pins 59/58 | right to x = 15, up to the pins' row under the port pairs, right to x = 31.5 and into the hub | 2 (under HUB_DN6/DN7) |
| PORT1_D, PORT3_D | J4 / J5 front rows | U408 / U410 | direct, straight above their pads | — |
| PORT2_D, PORT4_D | J4 / J5 back rows | U409 / U411 | single-net lanes on the bottom through the front row's pin gaps, up to the array's pads | 1 each |
| HUB_DN4, HUB_DN5 | U408, U409 | U402 bottom row | up to y = 69, left, up (DN4); up to y = 67.5, left, up (DN5) | — |
| HUB_DN6, HUB_DN7 | U410, U411 | U402 left row | up the left of the hub, right into the row, nested, 1.2 mm apart | — |
| HUB_DN1 | U402 pins 2/1 | R602/R603 (hub side) | down to y = 66.6, under the port pairs on the bottom, up along x = 50.5, right across the band at y = 38.75 | 2 |
| K20_USB | R602/R603 | U601 pins 3/4 | right, down into the K20's left row | — |
| HUB_DN2 | U402 pins 4/3 | R505/R504 (hub side) | down to y = 65.6, under the port pairs, up along x = 52.1, right across the band at y = 41.5, down past the DAPLink at x = 86.5, right under it at y = 51.5, down at x = 112, right under the FTDI at y = 62, up at x = 126.5, left into the resistors | 2 |
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
The VP leg at y = 85 keeps the 2 mm creepage to the opto-coupler's board-side
pins (y ≤ 82); the VOUT leg at y = 93 clears J19's GND pad by the class
clearance. The lanes' corridors stop at the courtyards of the parts they join
and appear in the board as footprint keep-out rule areas named `lane_*`. The
USB 2.0 pairs get their lanes when the pairs are placed (standard, section
8.3).

## Planes

L2 (In1.Cu) is the ground plane, one outline notched around the isolation
region. L3 (In2.Cu) carries the three heavy rails as rectangles (the
autorouter's DSN reader takes no concave plane), each at its own priority,
every rail one piece (the standard's rails gate rasterises each rail with
the others carving it and stops on a rail in pieces): VBUS_IN in the inlet
corner under the bucks' VIN pins and down to the PD controller's VBUS
parts; +5V_PORTS from L101's output down to the 3V3 buck's input, down the
middle beside the relay, along the band over the port switches (their pads
at y 78.5 to 80.5), across above the region to the DAPLink's VBUS, to the FTDI
switch, down to the relays and to the switch behind J9; +5V_TGT from L102's
output (and R125 at the back edge) down to the band at y 36–40, across it
below the PHY to the right edge, down it to the eFuse and J14. +3V3 is
routed, in its 0.5 mm `PWR_1A` class (2026-10-08): until then an +3V3 base
lay under the rails in five pieces, and the other three rails cut it into
three islands that no rail via or router track joined, with 16 of its 45
rail vias standing in copper another rail had carved away; on one rail
layer the two 6 A trees and the 3 A inlet leave no planar room for a fourth
net. The generator drops the rail vias into the rails; the autorouter adds
its own; the hand pass joins the pads the report lists with no room.

## Floods and stitching

Ground floods both outer layers (`GND_F`, `GND_B`) on the plane's outline,
notched around the isolation region by the 2 mm creepage, and the region
floods its own `PSU_GND` on both outer layers inside its outline
(`PSU_GND_F`, `PSU_GND_B`), all at the lowest priority with thermal
reliefs. Ground stitching sits on a 5 mm grid, 1.5 mm in from the edge,
kept out of the isolation region grown by its creepage; the region's own
ground is stitched on the same grid inside its outline inset by the
creepage. Vias are 0.6 mm on a 0.3 mm drill. The standard's `copper.py`
draws all of it over the routed board (`gen/pcb.py --copper`), moving a
via to the nearest clear spot where the routing is in the way, dropping one
that would cut a sliver off a rail or that the filled floods reach on fewer
than two layers, and adding one inside any pour island that holds a ground
pad but no via. Before the router, the generator drops **rail vias** beside
every SMD pad on a plane net (`RAIL_VIAS`: three for `PWR_6A`, two for the
3 A classes, one otherwise), joined by a stub at the class width or the pad's narrower side, and
reports the pads the packed rings leave no room beside.

## Sides

Connectors, ICs, relays, inductors, crystals and their load capacitors,
switches, jumpers, LEDs, test points, the bulk and large capacitors, the
parts of each buck's switching loop, the ESD arrays and the series parts on
the USB pairs, and every part on a `USB_VBUS_3A`, `PWR_6A` or `PSU_3A` net
stay on the **top**. Resistors and capacitors up to 1206, small diodes
(SOD-123) and SOT-23 transistors may go to the **bottom**, under the pin they
serve, 1 mm inside their host's courtyard edge, never within 1 mm of a
through-hole pad (hand soldering) or 0.6 mm of an exposed pad's via field.
The two stacked USB-A receptacles each carry two ports: the back rows'
load switches (U404, U406) and their capacitors go to the **bottom**
(`SIDES`, standard 3.7, 2026-10-07), the front rows' (U403, U405) stay on
top with the ESD arrays, so the area in front of each stack holds one
port's switch per side; the ports' indicator LEDs and their series
resistors stay on top. The corner keep-outs, the 3 mm edge zone, the lanes
and the isolation rule apply on both sides. The bottom carries nothing
taller than 3 mm (the standoffs). The area this frees on top is for the
blocks' copper zones.

## Placement

The connectors are locked where the edge table puts them (`CONNECTORS` in
`gen/layout.py`). The ICs are anchored by flow, below; the two parts that
straddle the isolation barrier are fixed; **every other part is placed by the
generator at the pin it serves** (ecad-standards/layout.md section 2): its
host is the placed part it shares the most specific nets with, a decoupling
capacitor's host is the IC the schematic draws it beside, it sits on the
host's side nearest that pin, turned so the pad on the host's net faces it,
and the parts along a side pack outward in rings. Since 2026-10-07 the
board mimics the schematic's islands as cities (standard 3.1): what a sheet
joins by wires is one city on the board, packed together, with a 2 mm void
to every other city on both sides, where the routing between blocks runs;
each city's hub goes first and its members come to it; a connector's city
comes to the connector (ESD stays at its receptacle); the regulators' cities
go before everything else. Since the same day a crystal lies along its IC's edge with its load
capacitors flanking it, each turned across the edge with its signal pad on
the trace to the pin (standard 5), and a decoupling capacitor lies across
the power trace it decouples, its axis along the IC's edge and its power pad
nearest the pin (standard 3.3). `placement.txt` beside the board file
records every part's host and ring (or the distance to its pin where no
ring had room), then each city's extent and the members placed more than
10 mm from every other member, then any gap between cities narrower than
the void. The
generator lists the parts it could not keep within 8 mm of their pin;
those, the members placed apart from their island, and the indicator LEDs
are the first things to refine by hand. The anchors are the second: they
are the knobs.

| Part | (x, y, rot) | Why there |
|---|---|---|
| K803 | (58, 73, 0) | straddles the isolation barrier |
| U801 | (68, 80.5, 180) | straddles the isolation barrier |
| U301 | (80.5, 29, 270) | PHY below J10 on the back edge, TX/RX pins up toward the jack (J10 + (4.42, 8.77), the ETH lanes' geometry) |
| U101 | (16, 41, 0) | PD controller behind J2 with its CC pins toward it, laid out as ST's STEVAL-ISC005V1 (UM2398 Figure 24, the `STUSB4500` template): decoupling in a column above, VBUS sense and enable parts right, I2C pull-ups below, reset pull-down left, all top side |
| U102 | (28, 44, 0) | PD bus buffer, right of the PD controller |
| J17 | (38, 50, 0) | Qwiic programming, top entry, beside the PD buffer |
| U103 | (24, 24, 0) | buck 1 (+5V_PORTS) in the corner at J2, laid out to TI SLVSF00 Figure 57 (the `TPS54560B` template): input column left at VIN and BOOT, catch diode along the right side at SW, inductor beyond it, output capacitors above the inductor, RT resistor below, compensation and divider right |
| U104 | (52, 24, 0) | buck 2 (+5V_TGT) beside it along the back edge, the same figure |
| U105 | (41, 41, 0) | +3V3 buck below buck 1's output, above the hub, laid out to TI SLVSDV6C Figure 52 (the `TPS62823` template): inductor and input capacitor on the power-pin side, output capacitors at the inductor's output, divider and feed-forward on the FB side |
| U402 | (39, 59, 90) | hub, moved 5 mm down and left toward the USB ports on 2026-10-07 to open the centre: downstream pins toward J4/J5, upstream and crystal toward J1 |
| U201 | (100.5, 23, 270) | K64: RMII toward the PHY, port/FAULT/UART pins toward the hub and FTDI, GPIO toward J15 |
| J16 | (93.5, 5, 0) | SWD to the K64, between the jack and the K64 at the back edge |
| U601 | (97, 47, 0) | DAPLink K20 |
| J601 | (104, 44, 0) | SWD to the K20 |
| U501 | (117, 70, 0) | FT231X behind J9, which moved 20 mm down the edge; its island follows (2026-10-07) |
| K801 | (93, 80, 0) | relays behind J11 / J12, 2 mm right with the passthrough region (2026-10-08) |
| K802 | (106.5, 80.5, 0) | 2 mm of void to the FTDI island above it |
| U704 | (119, 81, 0) | +5V_TGT eFuse (TPS26630) behind J14; its output net `+5V_TGT_OUT` is in the 6 A class (until 2026-10-08 the three target-I/O ICs were anchored under each other's designators: the eFuse sat 60 mm from J14 with its output in the default class) |
| U702 | (118, 29, 0) | GPIO level shifter (TXB0108) near J15 |
| U701 | (112, 46.5, 0) | console UART shifter (TXB0104) behind J13, which moved 10 mm down the edge; clear of the HUB_DN2 leg at x = 112 |
| U703 | (123, 46.5, 0) |  |
| U401 | (10.3, 74, 0) | J1 upstream array at its receptacle, in line with the pair, pins 1/3 toward J1 |
| U202 | (129.7, 19.34, 180) | J3 array |
| U408 | (40.78, 79, -90) | J4 front row (port 1) -> hub DN4, straight above its pads |
| U409 | (45.5, 77.4, -90) | J4 back row (port 2) -> hub DN5, reached on the bottom around the pin rows |
| U410 | (20, 79, -90) | J5 front row (port 3) -> hub DN6 |
| U411 | (25.2, 79, -90) | J5 back row (port 4) -> hub DN7 |
| R602 | (88.6, 37.75, 180) | K20 pair series resistors, P above N as the lane arrives from the left |
| R603 | (88.6, 39.75, 180) |  |
| R504 | (123.5, 71.6, 0) | FTDI pair series resistors, N above P as the lane arrives from the right |
| R505 | (123.5, 73.5, 0) |  |
| J15 | (117, 10, 0) | GPIO header, inboard |
| SW201 | (66, 50, 0) | K64 reset button in the open centre band (2026-10-07), its debounce parts with it |
| SW601 | (80, 50, 0) | DAPLink reset button beside it, 2 mm of void between the two cities |

The LEDs and their resistors are not anchored: the generator puts them at
the nearest free spot to the pin that drives them, and they are moved by
hand to where they can be seen.

## Flow

Power enters at J2 on the left edge and moves right: the PD controller
behind the connector with its CC pins toward it, laid out as ST's
evaluation board (standard 3.2, the `STUSB4500` template from UM2398
Figure 24), the two 5 V bucks side by side along the back edge above it, each a city of its own placed to its datasheet's layout
example (standard 3.2: `REGULATORS` and the `LAYOUTS` templates transcribe
TI's Figure 57) with 2 mm of void about it, the 3V3 buck below them at buck
1's output placed to its own figure, then the rails as polygons to each
block. Signals read the same way, from the user's edge
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
  (VBUS_IN, PORTn_VBUS, FTDI_VBUS; the project's patterns for the sheet-local
  ones start with `*`) at 2 mm or pours; `PWR_6A` (+5V_PORTS,
  +5V_TGT) at 4 mm or pours; two 0.5 mm vias per layer change on any of them.
- **Crystals** next to their IC, load capacitors between crystal and IC,
  no signals under them.
- **Bucks**: the SW node, catch diode and inductor in a tight loop; input
  capacitors against the VIN pin; a thermal pour under each regulator.
- **Silkscreen**: J9 pin 1 marked `BLK`, pin 6 `GRN`, TXD/RXD arrows; J11/J12
  COM/NO/NC; J18/J19 polarity; every connector's reference readable with the
  plug fitted.
