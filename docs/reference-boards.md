# Reference boards: measured placement practice

Why this exists: the layout engine (`hardware/kicad/gen/pcb.py`) and the
layout standard ([ecad-standards/layout.md](https://github.com/calicopizzadelivery/ecad-standards/blob/main/layout.md))
carry numbers (ring gaps, tuck depths, text sizes, side rules). Rather than
guess them, we measure them on boards that other people laid out well and
published in KiCad, and we set the standard from the measurement, so every
project after this one starts from the same calibrated rules.

## The mirror

`scripts/reference-boards.txt` lists the sources; `scripts/fetch-reference-boards.sh`
mirrors them into `reference-boards/` (git-ignored, about 4 GB, shallow
clones and unpacked archives). The mirror stays until the exercise is
finished. Vendors and the boards they contributed: mnt 14, olimex 48, rpi 3, sparkfun 16
(81 board files; SparkFun and MNT entries include panels and revisions
of the same design, which weigh their practice a little more). Licences as
published (CERN-OHL-S, CC-BY-SA): the boards are read, measured and cited,
never copied into ours.

## The measurement

`scripts/harvest-placement.py` opens each `.kicad_pcb` with `pcbnew` and
reports, per board, what the table below lists; `docs/reference-boards.csv`
holds every board's row. Boards without courtyards (most Olimex designs,
imported from Eagle) are compared on pad-to-pad gaps, which every board has.
A decoupling capacitor is a two-pad capacitor between a ground net and a
rail (named like one, or a plane-sized net); its distance is pad centre to
the nearest pad of an IC on that rail. ESD parts are recognised by value.

## What the boards say, and what we set (2026-10-06)

| Measure | Reference boards, median | Two-sided boards | This board |
|---|---|---|---|
| Decoupling capacitor to its supply pin, median (mm) | 2.41 | 2.20 | 2.19 |
| Decoupling capacitor to its supply pin, 90th percentile (mm) | 8.41 | 8.42 | 9.75 |
| Decoupling on the same side as its IC (share) | 1.00 | 0.89 | 0.93 |
| ESD part to its connector pad (mm; 15 boards) | 4.65 | 6.79 | 3.31 |
| Crystal to its IC pad (mm) | 5.90 | 9.36 | 4.42 |
| Nearest pad-to-pad gap, 10th percentile (mm) | 0.34 | 0.30 | 0.74 |
| Nearest pad-to-pad gap, median (mm) | 0.62 | 0.49 | 0.90 |
| Closest non-connector part to the edge (mm) | 0.73 | 0.64 | 3.79 |
| Parts to the edge, 10th percentile (mm) | 3.67 | 1.91 | 10.07 |
| Parts on the bottom (share) | 0.15 | 0.55 | 0.31 |
| Passives on the bottom (share) | 0.00 | 0.63 | 0.38 |
| ICs on the bottom (share) | 0.00 | 0.33 | 0.00 |
| Bottom part tucked inside a top IC's courtyard (mm) | 2.03 | 1.77 | 0.85 |
| Bottom part to through-hole pad, 10th percentile (mm) | 0.51 | 0.50 | 0.92 |
| Courtyard area over board area (%) | 53.80 | 76.12 | 61.02 |
| Designators visible on silk (%; SparkFun hides all, excluded) | 92.91 | 93.38 | 74.63 |
| Designator height, median (mm) | 0.76 | 0.76 | 0.80 |
| Smallest designator height (mm) | 0.64 | 0.64 | 0.70 |
| Narrowest track (mm) | 0.15 | 0.13 | 2.00 |
| Track width, median (mm) | 0.20 | 0.25 | 2.00 |
| Via drill, median (mm) | 0.40 | 0.40 |  |

Decisions taken from this, in the engine's directives (`gen/layout.py`) and
in the standard:

- **Decoupling stays on its IC's side.** Practice: on the same side as the
  IC in nine cases of ten even on two-sided boards. The engine had sent
  small decoupling to the bottom first; it now tries the IC's first two
  rings on top before the bottom. Ours went from 77 % to 93 % same side.
- **Spacing.** Practice packs parts 0.3 to 0.6 mm pad to pad. We keep the
  parent standard's 0.6 mm between bodies as a floor (courtyards plus a
  0.15 mm margin, ring gap 0.15 mm), which gives 0.65 mm; ours measures
  0.74 mm at the 10th percentile because the rings and lanes add their own
  room.
- **Bottom parts** tuck 1.8 to 2.0 mm inside the IC's courtyard edge and sit
  0.5 mm from through-hole pads: both set so (from 1.0 and 1.0 mm).
- **Designators** are 0.8 mm tall in practice, the smallest 0.65 to 0.72 mm,
  and nearly all are visible. Default 0.8 mm, minimum 0.7 mm (from 1.0 and
  0.8 mm); the project's board constraints allow 0.7 mm text and a 0.1 mm
  stroke. Ours went from 61 % to 75 % visible, with the rest omitted by the
  density rule.
- **The edge zone stays at 3 mm.** Practice goes to 0.7 mm (SparkFun 2.9 mm),
  but the parent standard's conveyor allowance is a process decision, kept
  until the assembler says otherwise.
- **ESD and crystals**: ours sit closer than practice (3.3 vs 3.5 to 6.8 mm;
  4.4 vs 5.9 mm). No change.
- **Density**: two-sided boards run at about 76 % courtyard area; ours is at
  61 %, so there is room before the board is full.

## Routing practice

The same harvest reads the routed boards' copper (the engine does not route
yet; these numbers set the net classes the schematic build writes and the
routing rules in the standard's sections 4 and 5). Medians over the 81
boards, with the 51 multilayer boards and the 49 boards with routed pairs
where it matters:

| Measure | Reference boards | This board's rules |
|---|---|---|
| Signal track width | 0.20 mm (multilayer 0.18) | 0.2 mm default (was 0.25) |
| Clearance in the boards' rules | 0.15 mm (multilayer 0.13) | 0.15 mm, fab minimum 0.127 |
| Via diameter / drill | 0.6 / 0.4 mm (multilayer 0.56 / 0.3) | 0.6 / 0.3 mm |
| Blind or micro vias | none on any board | none |
| Power track width, median / 90th percentile | 0.5 / 1.0 mm | 2 mm and 4 mm classes or pours, by current |
| Track length on the bottom layer | 45 % (multilayer 39 %) | both outer layers route |
| Track length on inner layers | 3 % (multilayer 12 %) | planes, a few crossings |
| Inner ground plane | every multilayer board; most on the layer under the top | GND_L2 on In1.Cu |
| Ground vias per cm² | 3.3 (multilayer 4.2) | about 4, at routing |
| Pads to zones | thermal reliefs on every zone, 0.5 mm gap and spoke | thermal, 0.5 / 0.5 |
| Zone minimum width / clearance | 0.2 / 0.24 mm | 0.25 / 0.3 mm |
| Ground pour share of the outer layers | 44 % | flood around the routing |
| Pair gap / width in the copper | 0.15 / 0.13 mm | 0.20 / 0.35 mm from the stackup (90 Ω) |
| Pair length mismatch, median / 90th percentile | 0.8 / 1.4 mm | within 1 mm |
| Pairs on a single layer | one in three, 3 vias per pair | one layer, no vias (the parent's rule, kept) |

After the autorouter's pass and the copper pass on the 140 × 100 mm board
(2026-10-07) the board measures: 3 148 tracks, signal width 0.2 mm, 47 % of
the track length on the bottom and none on the inner layers, pairs matched
to 0.00 mm with no vias on the pairs beyond the lanes' own layer changes,
ground floods over 52 % of the top and 60 % of the bottom, and 2.8 ground
vias per cm² from the 5 mm stitching grid (the practice's 3.3; the rest of
the grid points fall on routing, and the hand pass adds vias where it thins
the tracks).

What changed: the default track width went from 0.25 to 0.2 mm; the
standard gained layer roles, ground stitching at about four vias per
square centimetre, thermal reliefs at 0.5 mm, ground floods on the outer
layers, and the note that a pair class at KiCad's default width and gap is
not a pair class. Kept with reason: pairs on one layer with no vias (the
parent's 13.11), and the current-based power widths.

## Keeping it current

Rerun `scripts/harvest-placement.py` after the mirror grows or a rule
changes, update this table and section 9 of the standard with the numbers,
and record a rule that practice contradicts either as changed, with the
number, or as kept, with the reason. A new project runs the same script on
its own board and compares against this table.
