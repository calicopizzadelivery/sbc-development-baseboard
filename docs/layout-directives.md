# Layout directives

What the board is placed from. Everything here comes from
[hardware-spec.md](hardware-spec.md) §2 and §8a and the block diagram; when
one of them changes, this file changes with it. The origin is the board's
top-left corner, X to the right, Y down, in millimetres, as KiCad draws it.

## Outline and stackup

- **140 × 80 mm**, 1.6 mm, 2 mm corner radius. Components on the **top side
  only**.
- Advanced Circuits standard 4-layer 0.062": L1 signal (1 oz), 0.012"
  prepreg, L2 **ground plane** (1 oz), 0.028" core, L3 power / signal (1 oz),
  0.012" prepreg, L4 signal (1 oz). State it in the fab notes and ask for
  controlled impedance on the `USB` class.

## Mounting holes

Four M3, plated, on GND, centred **10 mm in from each corner**: (10, 10),
(130, 10), (10, 70), (130, 70). A 6 mm standoff pad on each, so the first
13 mm of every edge from each corner carries no connector. Each short edge
has about 54 mm usable, each long edge about 114 mm.

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
target belongs anyway. Bodies are packed 1 mm apart from 13.5 mm after each
corner. Edge connectors sit with their mating face flush with the edge, or
on the footprint's own "PCB Edge" mark where it has one (the USB-C
receptacles overhang by 1.1 mm). Verify the terminal blocks' orientation in
the 3D view before ordering.

## Keep-outs

- The 13 mm from each corner along every edge (standoff pads and screw
  heads): no connectors, no tall parts.
- **Isolation**: the PSU passthrough (J18, J19, K803's contact side, the
  opto-coupler's LED side, D807, R810, R811) sits in its own region behind
  J18/J19 at the front, x 48–84, y 42–80, with the barrier running through
  K803 between its coil and contact pins (x = 64) and through U801 between
  its LED and transistor pins (y = 42). It has its own **PSU_GND** copper on
  L2 with **no board ground plane under it**, and a 2 mm creepage gap to
  every board net, enforced by a DRC rule (`sbc-baseboard.kicad_dru`). Only
  the opto-coupler and the relay body cross the gap.
- Under the Ethernet magnetics (inside J10): no copper on any layer under
  the magnetics side of the jack.
- The back edge: nothing within 5 mm, so it can lie flat against a rail.

## Placement groups

Parts go next to the connector they serve; the groups below are the
starting placement the generator uses, refined by hand afterwards.

| Group | Rectangle (x0, y0, x1, y1) | Anchors |
|---|---|---|
| Ethernet | 22, 1, 52, 11 | U301, Y301 (behind J10) |
| Hub and port switches | 22, 11, 52, 56 | U402, Y401, U403–U406, U408–U411, U407, U105 (behind J4/J5) |
| Power in | 5, 37, 22, 58 | U101, U102, Q101, Q102, U401, J17 (beside J1/J2) |
| Bucks | 52, 1, 85, 36 | U103, U104, L101, L102 |
| Passthrough driver | 48, 36, 70, 42 | Q803 (board side of the barrier) |
| Passthrough, isolated | 64, 56, 84, 66 | D807, R810, R811; K803 and U801 fixed across the barrier |
| MCU | 85, 1, 113, 38 | U201, Y201, J16, SW201, D202 |
| DAPLink | 84, 42, 100, 66 | U601, Y601, J601, SW601 |
| FTDI | 100, 38, 113, 66 | U501, JP501, JP502 (behind J9) |
| Target I/O | 113, 1, 127, 38 | U701–U704, J15, U202 (behind J3/J13) |
| Signal relays | 113, 38, 128.5, 64 | K801, K802, Q801, Q802 (behind J11/J12/J14) |

Every other part joins the group of the IC it shares the most signal nets
with. The rectangles are the generator's starting placement (`gen/layout.py`);
they are sized from the parts' courtyards and are the first thing to adjust
by hand.

## Special considerations

- **USB 2.0 pairs** (class `USB`, 0.35 mm / 0.20 mm, 90 Ω): on L1 over the
  L2 ground plane, routed as pairs, no stubs, length-matched within 1 mm,
  the ESD arrays in line with the pair next to their receptacle.
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
