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

| Edge | Connectors, in order from the back corner to the front | Faces | Bodies |
|---|---|---|---|
| Left (x = 0), 54 mm usable | J10 RJ45 · J1 USB-C upstream · J2 USB-C PD in · J17 Qwiic programming | workstation / charger / user | 41 mm |
| Right (x = 140), 54 mm usable | J3 USB-C HID · J13 console · J19 PSU out | target | 37 mm |
| Front (y = 80), left end | J4, J5 USB-A stacks · J18 PSU in | bench / PSU | 39 mm |
| Front (y = 80), right end | J9 FTDI right-angle · J11, J12 relays · J14 +5V_TGT | target | 52 mm |
| Inboard, vertical | J16 Cortex debug · J15 GPIO header | any (ribbon, jumpers) | — |

Edge connectors sit flush with their edge; the USB-C and RJ45 receptacles
and the USB-A stacks overhang per their footprints. Pluggable terminal
blocks (Phoenix MC 1,5 3.5 mm and 5.08 mm) face outward with their plug
entry at the edge.

## Keep-outs

- The 13 mm from each corner along every edge (standoff pads and screw
  heads): no connectors, no tall parts.
- **Isolation**: the PSU passthrough (J18, J19, K803's contact side, the
  opto-coupler's LED side, D807, R810, R811) sits in its own region at the
  front-left, on its own **PSU_GND** copper with **no L2 ground plane under
  it**; a 2 mm creepage gap separates that region from every board net. Only
  the opto-coupler and the relay body cross the gap.
- Under the Ethernet magnetics (inside J10): no copper on any layer under
  the magnetics side of the jack.
- The back edge: nothing within 5 mm, so it can lie flat against a rail.

## Placement groups

Parts go next to the connector they serve; the groups below are the
starting placement the generator uses, refined by hand afterwards.

| Group | Parts | Where |
|---|---|---|
| Ethernet | U301 KSZ8081, Y301, its passives, D3xx | behind J10, left-back |
| Power in | U101 STUSB4500, Q101, U102 PCA9517A, J17 side | behind J2, left |
| Bucks | U103, U104, L101, L102, their diodes and capacitors, U105 | left-centre, behind the inlet, with a thermal copper area on L1 |
| MCU | U201 K64, Y201, J16, its decoupling | centre |
| Hub | U402 USB2517, Y401, U401 | front-left centre, behind J4/J5 |
| Port switches | U403–U406, U408–U411, C4xx, D40x | between the hub and J4/J5 |
| FTDI | U501, JP501, JP502, D50x | front-right, behind J9 |
| DAPLink | U601 K20, Y601, J601 | centre-front, between the hub and the K64 |
| Target I/O | U701 TPS26630, U702–U704 level shifters, J15 | right, behind J13/J14 |
| Signal relays | K801, K802, Q801, Q802 | front-right, behind J11/J12 |
| Passthrough | K803, Q803, U801, J18, J19 | front-left corner region, isolated (above) |

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
