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
- Advanced Circuits standard 6-layer 0.062" (their drawing, 2026-10-09;
  four layers until then: the router left 116 connections open on two
  routing layers, 99 with its costs tuned, and the wall was the layer
  count): 1 oz on all six layers; L1 signal and ground flood, two 2116
  sheets (9.8 mil pressed), L2 **ground plane**, 0.014" core, L3 signal,
  two 2116 sheets, L4 the **+5V rail**, 0.014" core, L5 **ground plane**, two 2116
  sheets, L6 signal and ground flood. Order it Custom / Controlled
  Dielectric (their standard stackups are not guaranteed otherwise) with
  controlled impedance on the `USB` and `ETH` classes, and confirm both
  cores are 0.014".

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
edge so the two left-edge connectors, both USB-C then, could spread out
around the middle of the left edge and the lower-left corner stopped
crowding; the board no longer lies flat against a wall or a DIN rail, which
the spec accepted).

| Edge | Connectors, in order from the back corner to the front | Faces | Courtyards (measured) |
|---|---|---|---|
| Left (x = 0), 74 mm usable | J2 barrel power in (Kycon KLDX-0202-BC, 2.5 × 5.5 mm, through-hole, horizontal, centre positive: origin y = 30, its front face at the edge and its body 14.5 mm inboard, pins at y 30 and 34.7; a USB-C PD receptacle until 2026-10-10) · J1 USB-C upstream (centred y = 64; y = 74 until 2026-10-10, when it moved 10 mm up the edge toward the middle), split around the middle | adapter / workstation | 11.2 + 10.6 = 21.8 mm |
| Back (y = 0), 114 mm usable | J10 RJ45, from x = 45 (from x = 14 until 2026-10-07, when the PD inlet's two 5 V bucks took the back-edge corner beside J2; from x = 71 until 2026-10-10, when the bucks had gone and the jack and its PHY moved 26 mm back toward the corner to open the K64's side, the two reset buttons in a column beside the jack) | workstation | 19.0 mm wide, 22.4 mm deep |
| Right (x = 140), 74 mm usable | J3 USB-C HID (centred y = 19.3) · J13 console (origin y = 49.2) · J9 FTDI right-angle (origin y = 65.0), J13 moved 10 mm and J9 20 mm down the edge on 2026-10-07, leaving 11 mm between courtyards (they were packed 1.5 mm apart in the back half) | target | 10.6 + 16.5 + 16.3 = 43.4 mm |
| Front (y = 100), left end | J5, J4 USB-A stacks (J5 at x = 19, J4 at x = 37: swapped on 2026-10-06 so each stack's pairs reach the hub row they are wired to without crossing) · J18 PSU in (x = 56.4) · J19 PSU out (x = 70.7), both 2 mm right since 2026-10-08 so J4's shield pads stand 2.6 mm from the passthrough region (their copper still enters its 2 mm creepage band by 0.9 mm; the fills keep the creepage, DRC agrees) | bench / PSU | 17.2 + 17.2 + 13.2 + 13.2 = 60.8 mm |
| Front (y = 100), right end | J14 +5V_TGT · J12, J11 relays | target | 13.2 + 13.05 + 13.05 = 39.3 mm |
| Inboard | J16 Cortex debug · J15 GPIO header · J601 K20 SWD (J17, the PD programming header, top entry, until 2026-10-10) | any | — |

Four things moved from the spec's first table once the footprints were
measured (2026-10-06): the RJ45's courtyard runs 22 mm along the edge, not 16, so the left edge
could not also take J17, the PD programming header, which went inboard as a
top-entry part (and went altogether with the PD inlet on 2026-10-10); the
RJ45 then went to the back edge so J1 and J2 could spread;
**J19 sits beside J18** so the PSU passthrough is one compact isolated
region behind the two of them instead of a strip across the board; and J9
takes J19's place on the right edge, where an FTDI header facing the
target belongs anyway. Bodies are packed 1 mm apart from 14 mm after each
corner. Edge connectors sit with their mating face flush with the edge, or
on the footprint's own "PCB Edge" mark where it has one (the USB-C
receptacles overhang by 1.1 mm; the barrel jack's front face sits at the
edge). The mating face is the end of the body
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

L2 (In1.Cu) and L5 (In4.Cu) are the ground planes, one outline each
notched around the isolation region, which holds its own PSU_GND island on
both and on the rail layer; L3 (In2.Cu) routes with the outer layers. L4 (In3.Cu) carries the
one heavy rail, +5V (class `PWR_4A`), as rectangles, referenced to L5
across the core (the autorouter's DSN reader takes no concave plane), each
at its own priority, the rail one piece (the standard's rails gate
rasterises each rail with the others carving it and stops on a rail in
pieces): from the jack's centre pin, the FET and the bulk capacitors in the
inlet corner (x 3–42, y 22–40) to the 3V3 buck's input (x 36–62, y 40–48),
down the middle beside the relay (x 48–64, y 48–80), along the band over the
port switches (x 10–48, y 70–83; their pads at y 78.5 to 80.5), across
above the region to the DAPLink's VBUS (x 62–100, y 45–57) and on to the
FTDI switch (x 86–126, y 52–57), down to the relays (x 88–108, y 57–82)
and the switch behind J9 (x 108–126, y 57–77), and to the eFuse's input
behind J14 (x 108–137, y 77–97), which +5V_TGT leaves as a track to J14.
One rail since 2026-10-10; until then three: VBUS_IN at 3 A in the inlet
corner under the two bucks' VIN pins and down to the PD controller's VBUS
parts, +5V_PORTS at 6 A from buck 1's inductor along the path the +5V rail
now takes, and +5V_TGT at 6 A from buck 2's inductor down to a band at
y 36–40, across it below the PHY to the right edge and down it to the eFuse
and J14. +3V3 is
routed, in its 0.6 mm `PWR_1A` class (0.5 mm on four layers; an inner 1 oz
track carries about half of an outer one; on six layers a plane for
it would cost the third routing layer, so it stays routed): before that an
+3V3 base lay under the rails in five pieces, and the three rails of the
time cut it into
three islands that no rail via or router track joined, with 16 of its 45
rail vias standing in copper another rail had carved away; on one rail
layer the two 6 A trees and the 3 A inlet left no planar room for a fourth
net. The generator drops the rail vias into the rail; the autorouter adds
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
every SMD pad on a plane net (`RAIL_VIAS`: three for `PWR_4A`, two for the
3 A classes `USB_VBUS_3A` and `PSU_3A`, one otherwise; three for `PWR_6A`
until 2026-10-10), joined by a stub at the class width or the pad's narrower side, and
reports the pads the packed rings leave no room beside.

## Sides

Connectors, ICs, relays, inductors, crystals and their load capacitors,
switches, jumpers, LEDs, test points, the bulk and large capacitors, the
parts of the 3V3 buck's switching loop, the ESD arrays and the series parts on
the USB pairs, and every part on a `USB_VBUS_3A`, `PWR_4A` or `PSU_3A` net
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

Since 2026-10-10 the placement is the owner's: the first hand pass in
KiCad moved 133 of the 271 parts (commit c1628c5), and the standard's
`tools/handplace.py` harvests every part's pose (x, y, rotation, side) off
the saved board into `gen/hand_placement.py` (`HAND`, 254 parts, 84 on the
bottom; standard section 2, item 4). `layout.py` merges `HAND` over
`FIXED`, a hand-fixed part outranks its anchor and the engine's own rule,
and the generator reproduces the saved board exactly (`handplace.py
--check` against the generated board finds nothing placed elsewhere). The
edge connectors stay in `CONNECTORS`, rewritten by the harvest when one
moves (J1, J2, J3 and J10 in the first pass). A hand-fixed part is reported
rather than refused: `placement.txt` carries a "hand placement" section
(after the rail vias) listing the pairs of hand-fixed parts closer than
the packing margin (the DRC gate judges their courtyards), the lanes that
run through a hand-fixed part, the lanes the engine could not lay, and the
pair lanes laid with their members crossing because a moved part now
faces the path the wrong way; that section is
the next hand pass's work, and the board is not routed until the lanes lay
and the DRC gate is clean. The hand loop is: move parts in KiCad and save,
harvest, regenerate, read the section, repeat. The harvest takes the
parts' poses only: the designators follow the silkscreen rule on every
regeneration, so they are not moved by hand. The anchors below are the
positions the generator used before the hand pass; where `HAND` has an
entry, it wins, and the table's "why there" still says what the part is
for and which way it faces.

| Part | (x, y, rot) | Why there |
|---|---|---|
| K803 | (58, 73, 0) | straddles the isolation barrier |
| U801 | (68, 80.5, 180) | straddles the isolation barrier |
| U301 | (54.5, 29, 270) | PHY below J10 on the back edge, TX/RX pins up toward the jack (J10 + (6.81, 8.96), the ETH lanes' geometry; at (80.5, 29) until the jack moved left on 2026-10-10; the hand pass put it at (52.11, 28.81)) |
| Q101 | (20, 30, 0) | the inlet's reverse-polarity FET (DMP3013SFV) behind J2, drain at the jack's centre pin, source on the +5V rail, gate to GND through R102; the inlet island comes to it and to the jack: D101 the SMAJ5.0A at the jack's centre pin (19.3, 34), C101/C102 47 µF at (12, 22.7) and (7.3, 22.8) with C103 100 nF beside the source, the amber LED D102 and R101 at (13, 20). 2026-10-10: until then the corner held U101 the STUSB4500 at (16, 41) placed from ST's STEVAL-ISC005V1 figure (UM2398 Figure 24), U102 the PD bus buffer at (28, 44), J17 the Qwiic programming header at (38, 50) and the two TPS54560B bucks U103 (+5V_PORTS) at (24, 24) and U104 (+5V_TGT) at (52, 24) placed from TI SLVSF00 Figure 57; all five anchors and both templates went with the PD inlet |
| U105 | (41, 41, 0) | +3V3 buck above the hub, where the +5V rail's inlet rectangle hands to the next (below buck 1's output until 2026-10-10), laid out to TI SLVSDV6C Figure 52 (the `TPS62823` template): inductor and input capacitor on the power-pin side, output capacitors at the inductor's output, divider and feed-forward on the FB side |
| U402 | (39, 59, 90) | hub, moved 5 mm down and left toward the USB ports on 2026-10-07 to open the centre: downstream pins toward J4/J5, upstream and crystal toward J1 |
| U201 | (100.5, 23, 270) | K64: RMII toward the PHY, port/FAULT/UART pins toward the hub and FTDI, GPIO toward J15 |
| J16 | (93.5, 5, 0) | SWD to the K64, between the jack and the K64 at the back edge |
| U601 | (97, 47, 0) | DAPLink K20 |
| J601 | (104, 44, 0) | SWD to the K20 |
| U501 | (117, 70, 0) | FT231X behind J9, which moved 20 mm down the edge; its island follows (2026-10-07) |
| K801 | (93, 80, 0) | relays behind J11 / J12, 2 mm right with the passthrough region (2026-10-08) |
| K802 | (106.5, 80.5, 0) | 2 mm of void to the FTDI island above it |
| U704 | (119, 81, 0) | +5V_TGT eFuse (TPS26630, 3 A since 2026-10-10; 5 A before) behind J14, its input from the +5V rail's last rectangle; its output `+5V_TGT`, a sheet-local label on the target sheet, is in the `PWR_4A` class (until 2026-10-08 the three target-I/O ICs were anchored under each other's designators: the eFuse sat 60 mm from J14 with its output in the default class) |
| U702 | (118, 29, 0) | GPIO level shifter (TXB0108) near J15 |
| U701 | (112, 46.5, 0) | console UART shifter (TXB0104) behind J13, which moved 10 mm down the edge; clear of the HUB_DN2 leg at x = 112 |
| U703 | (123, 46.5, 0) |  |
| U401 | (10.3, 64, 0) | J1 upstream array at its receptacle (10 mm up the edge with J1 on 2026-10-10), in line with the pair, pins 1/3 toward J1 |
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
| SW201 | (71.5, 8, 0) | K64 reset button, in a column beside the RJ45 on the back edge (in the open centre band from 2026-10-07 to 2026-10-10), its debounce parts with it |
| SW601 | (71.5, 17, 0) | DAPLink reset button below it, 2 mm of void between the two cities and from the jack |

The LEDs and their resistors are not anchored: the generator puts them at
the nearest free spot to the pin that drives them, and they are moved by
hand to where they can be seen.

## Flow

Power enters at J2 on the left edge and moves right: the TVS at the jack's
centre pin, the reverse-polarity FET behind the jack with the bulk
capacitors at its source, one inlet island (standard 3.1) with 2 mm of void
about it; the 3V3 buck above the hub, a city of its own placed to its
datasheet's layout example (standard 3.2: `REGULATORS` and the `LAYOUTS`
template transcribe TI's SLVSDV6C Figure 52) with 2 mm of void about it;
then the +5V rail as rectangles on L4 to each block (2026-10-10; until then
the STUSB4500 PD controller sat behind a USB-C receptacle with its CC pins
toward it, placed from ST's evaluation board, UM2398 Figure 24, the two
TPS54560B 5 V bucks stood side by side along the back edge above it, each a
city placed from TI SLVSF00 Figure 57, and the 3V3 buck hung from buck 1's
output; `TEMPLATED` has been empty and `REGULATORS` has held U105 alone
since). Signals read the same way, from the user's edge
on the left to the target's edge on the right. Each IC's own layout rules
are in [layout-guidelines.md](layout-guidelines.md).

## Special considerations

- **USB 2.0 pairs** (class `USB`, 0.33 mm / 0.20 mm, 90 Ω on the six-layer stackup): on L1 over the
  L2 ground plane, routed as pairs, no stubs, length-matched within 1 mm,
  90 Ω end to end from the receptacle through the ESD array to the
  transceiver (standard 3.8). The USBLC6-2 arrays are flow-through: the
  receptacle's pair enters pins 1/3, the IC's pair leaves pins 6/4, and the
  two are separate nets, both in the `USB` class (`J1_D_?` and `HUB_UP_?`,
  `PORTn_D_?` and `HUB_DNn_?`, `J3_D_?` and `K64_USB_?`); the build refuses
  a pair outside the class. The arrays are placed first, on top, at the
  receptacle's signal pins, turned so pins 1/3 face the receptacle.
- **ESD on single lines** (PESD5V0S1UL on J9's four signals and J13's
  console; the SMAJ5.0A at the jack's centre pin is placed the same way;
  ESDA25W at the PD inlet's CC pins until 2026-10-10): on top at the
  connector pin, first, the signal passing the diode's pad, the ground pad
  to the plane by a via.
- **High current**: `PSU_3A` (PSU_VP, PSU_VOUT, PSU_GND) and `USB_VBUS_3A`
  (PORTn_VBUS, FTDI_VBUS; the project's patterns for the sheet-local
  ones start with `*`) at 2 mm or pours; `PWR_4A` (+5V, +5V_TGT) at 2.5 mm
  or pours (2026-10-10; until then `PWR_6A` at 4 mm for +5V_PORTS and
  +5V_TGT, and VBUS_IN in the 3 A VBUS class); 1.0 mm / 0.5 mm vias, two
  per layer change on any of them.
- **Inlet**: the TVS at the jack's centre pin, the FET behind the jack with
  its gate pull-down at the gate pin, the bulk capacitors beside its
  source; no series fuse (the adapter limits the inlet, the eFuse the target
  rail, the TPS2553s the ports).
- **Crystals** next to their IC, load capacitors between crystal and IC,
  no signals under them.
- **The 3V3 buck** (the only switching regulator since 2026-10-10): the SW
  node and inductor in a tight loop; the input capacitor against the VIN
  pin; a thermal pour under it.
- **Silkscreen**: J9 pin 1 marked `BLK`, pin 6 `GRN`, TXD/RXD arrows; J11/J12
  COM/NO/NC; J18/J19 polarity; every connector's reference readable with the
  plug fitted.
