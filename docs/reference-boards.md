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
finished. Vendors and the boards they contributed: mnt 14, olimex 48, rpi 3, sparkfun 14
(79 board files; SparkFun and MNT entries include panels and revisions
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
| Decoupling capacitor to its supply pin, median (mm) | 2.41 | 1.99 | 2.19 |
| Decoupling capacitor to its supply pin, 90th percentile (mm) | 8.41 | 8.41 | 9.75 |
| Decoupling on the same side as its IC (share) | 1.00 | 0.89 | 0.93 |
| ESD part to its connector pad (mm; 15 boards) | 4.65 | 6.79 | 3.31 |
| Crystal to its IC pad (mm) | 5.90 | 9.36 | 4.42 |
| Nearest pad-to-pad gap, 10th percentile (mm) | 0.34 | 0.30 | 0.74 |
| Nearest pad-to-pad gap, median (mm) | 0.62 | 0.49 | 0.90 |
| Closest non-connector part to the edge (mm) | 0.73 | 0.65 | 3.79 |
| Parts to the edge, 10th percentile (mm) | 3.67 | 2.13 | 10.07 |
| Parts on the bottom (share) | 0.15 | 0.55 | 0.31 |
| Passives on the bottom (share) | 0.00 | 0.63 | 0.38 |
| ICs on the bottom (share) | 0.00 | 0.33 | 0.00 |
| Bottom part tucked inside a top IC's courtyard (mm) | 1.77 | 1.77 | 0.85 |
| Bottom part to through-hole pad, 10th percentile (mm) | 0.50 | 0.49 | 0.92 |
| Courtyard area over board area (%) | 53.80 | 75.74 | 61.02 |
| Designators visible on silk (%; SparkFun hides all, excluded) | 92.91 | 93.38 | 74.63 |
| Designator height, median (mm) | 0.76 | 0.76 | 0.80 |
| Smallest designator height (mm) | 0.64 | 0.64 | 0.70 |
| Narrowest track (mm) | 0.15 | 0.13 | 2.00 |
| Track width, median (mm) | 0.23 | 0.28 | 2.00 |
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
- **Bottom parts** tuck about 1.8 mm inside the IC's courtyard edge and sit
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

## Keeping it current

Rerun `scripts/harvest-placement.py` after the mirror grows or a rule
changes, update this table and section 9 of the standard with the numbers,
and record a rule that practice contradicts either as changed, with the
number, or as kept, with the reason. A new project runs the same script on
its own board and compares against this table.
