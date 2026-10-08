# KiCad project

`sbc-baseboard/` is the KiCad 10 project: a root sheet and eight sub-sheets,
a project symbol library for the parts the standard libraries lack, an ERC
report, a PDF of every sheet and a BOM.

```
sbc-baseboard/
  sbc-baseboard.kicad_pro   project
  sbc-baseboard.kicad_sch   root: sheet index, mounting holes, the verify-before-fab list
  power.kicad_sch           PD inlet, STUSB4500, J17 programming, PCA9517A, three bucks
  mcu.kicad_sch             K64, USB device port J3, SWD J16, heartbeat
  ethernet.kicad_sch        KSZ8081RNA, magjack
  hub.kicad_sch             USB2517, upstream J1, four switched USB-A, FT231X switch
  ftdi.kicad_sch            FT231X, J9 header, jumpers
  daplink.kicad_sch         MK20DX128 DAPLink
  target.kicad_sch          console, GPIO/I2C breakout, +5V_TGT eFuse
  relays.kicad_sch          two signal relays, PSU passthrough relay and its opto monitor
  libs/                     the house symbol libraries (ecad-libraries), a git submodule pinned to a tag
  sym-lib-table             names them calico-ic and calico-electromechanical, as ${KIPRJMOD}/../libs/...
                            and the stacked USB-A as two units (one per port)
  sbc-baseboard.pdf         all nine sheets
  erc.txt, bom.csv
```

Reference designators are numbered by sheet: R1xx/C1xx power, 2xx MCU,
3xx Ethernet, 4xx hub, 5xx FTDI, 6xx DAPLink, 7xx target I/O, 8xx relays and
passthrough.

## How it was made, and the handoff

The schematic was **generated**, by `gen/build.py`. That generator pulls
symbols from KiCad's own libraries (so the embedded copies match what KiCad
ships), builds the missing symbols from datasheet pin tables, lays each sheet
out around its main component (`gen/fanout.py`: lanes leave the IC's pins at
pin pitch, and connectors, series parts, pull-ups and power symbols are drawn
at the ends of the lanes — the style in
[ecad-standards](https://github.com/calicopizzadelivery/ecad-standards)), and
writes the `.kicad_sch` files directly. It then runs `kicad-cli sch erc` and
exports the PDF and BOM. Pin-position maths and power-symbol net naming were
calibrated against `kicad-cli`'s netlist export before any real sheet was
built.

Five checks guard every build and all pass at zero: `kicad-cli sch erc
--severity-all`; `gen/check_geom.py`, which finds wire ends and pin ends that
land on a foreign wire with no junction (the shorts a netlist shows only as a
merged net) and any two wires drawn over each other;
`gen/netcheck.py`, which traces wire-level connectivity in each sheet and
reports any net carrying two rails; and `gen/check_layout.py`, which reports
text over outlines, wires or other text, wires through a part body, and power
symbols pointing the wrong way (GND always hangs down, rails always stand up),
anything on the sheet frame or the title block, pin numbers treated as text
like any other, and pin names inside a symbol that print over each other
(`gen/check_pins.py`, run on library symbols too; its `--gaps` option lists the
closest name pairs). Text widths come from a per-glyph table fitted to the text
extents KiCad writes into its own PDF export. The fifth is reproducibility:
build, `git add` the outputs, build again, and `git status` must be empty. The netlist was also diffed against the
first label-style pass with passive renumbering factored out, so the re-layout
changed drawing, not connectivity (the JP501 default and the J1 VBUS divider
tap, which became a local label, are the two intended exceptions).

**Nothing is drawn over anything else.** Routes into a stacked connector
from one side take staggered columns and rows (the route bound for the
farthest pin gets the outermost column and the nearest row), a tag before a
route ends where the route's target lies, several routes into one pin share
one stub, and a second tap on a wire lands beside the first, never on it.
The geometry check is at zero on every sheet: no wire end on a foreign wire
without a junction, no two wires sharing a stretch.

**The FTDI header is an Adafruit FTDI Friend.** J9 is GND, CTS, VCC, TX, RX,
RTS in that order; VCC is 5 V by default (JP502, bridged A–C) or 3.3 V from
the FT231X's regulator (B–C); pin 6 is RTS by default (JP501, bridged A–C)
or DTR. Logic is 3.3 V. The first pass left J9's VCC pin on an open jumper
only, so it floated by default; the bridged jumpers fix that.

**The DAPLink K20 follows the FRDM-K64F OpenSDA circuit.** DAPLink's k20dx
port reads SWDIO on PTC7 and drives it on PTC6, so both are on the SWDIO
net; the FRDM's 33 Ω series resistors on the K20's USB pair are fitted. See
[reference-design-review.md](../../docs/reference-design-review.md).

**Differential pairs are named for the router.** Every USB 2.0 pair carries
net names `<base>_P` / `<base>_N`, the suffixes KiCad's PCB editor pairs up:
`J1_D`, `J3_D` and `PORT1_D`..`PORT4_D` on the receptacle side of each ESD
array, `HUB_UP` and `HUB_DN1`..`HUB_DN7` at the hub, `K64_USB` and
`FTDI_USB` at the chips (the ESD arrays' pass-through pins and the FT231X's
series resistors each split a pair into two nets, and both halves are named).
The project file carries a `USB` net class matched by pattern
(`*_USB_?`, `*_D_?`, `HUB_UP_?`, `HUB_DN?_?`); the patterns are globs over
the full hierarchical name, so a sheet-local net such as `/USB hub/PORT1_VBUS`
is matched only by a pattern that starts with `*` (the port VBUS nets sat in
`Default` until 2026-10-08 for want of that star, and the standard's engine
now stops on a class that no net resolves to). Its differential width and
gap are KiCad's defaults until the stackup is chosen, then set them from the
fab's impedance calculator for 90 Ω before routing. Route each pair as a
pair, no stubs, over an unbroken reference plane.

**Builds are reproducible.** Every UUID in the generated files is derived,
not drawn: a UUID5 in a namespace made from the project name, keyed by what
the element is (a symbol by its reference and unit, a pin by its symbol, a
wire by its sheet and ends, a label by its sheet, net and position, a sheet by
its file name; identical keys get a counter in draw order). The ERC report
header and the PDF's creation date are pinned to the title-block date. So two
builds of one design give byte-identical files, a commit touches only the
sheets whose design changed, and once layout starts a regenerated sheet keeps
its footprints linked, since the board links footprints to symbols by UUID
path. The costs are the ones KiCad itself has: renaming a reference is a new
symbol, moving a wire or label is a new UUID (nothing outside the sheet refers
to those), and the power symbols, numbered in draw order per sheet, renumber
when one is inserted before them. Keep it that way: never write a random UUID
into the output, and never let an export's timestamp into a tracked file.

**The generator is bring-up tooling, not the source of truth.** The moment
anyone edits the schematic in KiCad, the KiCad files are the design and
`gen/` is history: re-running `build.py` would overwrite the edits. The honest
next step is layout.

```bash
cd gen && ./build.py        # regenerate everything (only while nothing has been hand-edited)
```

## Layout

The board file `sbc-baseboard.kicad_pcb` was generated once, by the
standard's placement engine (`standards/tools/placer.py`, the ecad-standards
repository as a submodule at `standards/`, on KiCad's `pcbnew` Python module)
called from `gen/pcb.py`, from the schematic's netlist, the project file and
the directives in `gen/layout.py`, which are
[docs/layout-directives.md](../../docs/layout-directives.md) as data. It
carries the 140 × 100 mm outline with 2 mm corners, the four M3 holes on GND
7 mm from the corners with their corner keep-outs, Advanced Circuits' 4-layer
stackup, every footprint with its nets, the L2 ground plane with the isolated
PSU_GND island, and `sbc-baseboard.kicad_dru` with the passthrough's
isolation rules.

The placement follows
[ecad-standards/layout.md](https://github.com/calicopizzadelivery/ecad-standards/blob/main/layout.md)
section 3: the edge connectors are locked at the directives' positions,
facing outward; the ICs are anchored by flow (the table in the directives);
the two parts that straddle the isolation barrier are fixed; every other
part is placed at the pin it serves, by the generator, in five passes (small
decoupling capacitors at their pins, the large parts on an IC's own pins,
bulk capacitors, the small parts on those pins, then parts hosted by other
passives), each on its host's nearest side with the pad on the host's net
facing it, packed outward in rings. Small resistors, capacitors, diodes and
transistors that are not on a current-carrying, pair or switching-loop net go
to the bottom, tucked under their host's pin row, clear of through-hole pads
and exposed-pad via fields (the directives' Sides section); the rest stay on
top. The lanes the directives declare (the PSU passthrough: J18 to the relay
to J19) are laid first as footprint keep-outs on both sides and as 2 mm
tracks, so nothing is placed in the way of the 3 A path. ESD parts go down
before anything else, on top, in the first ring at their connector's signal
pins; the USB arrays are flow-through, turned with their receptacle-side
pins toward the receptacle, and both nets of each pair are in the `USB`
class (the schematic build refuses a `_P`/`_N` pair outside it). `placement.txt`
records every part's host, side and ring; the generator prints the parts it
could not keep within 8 mm of their pin. The silkscreen pass places each reference designator where it
overlaps nothing (1.0 mm, then 0.8 mm text) and omits it otherwise, per the
standard's section 6; ICs and connectors are never omitted, their designator
steps out to the nearest pocket instead, and the generator lists those too.
The fabrication layer keeps every designator.

The pairs are laid by the engine as pair lanes (both members at the class's
differential geometry, escapes, the USB-C bridges, two layer changes where
a pair must pass under the port pairs, lengths matched by a bump), the ESD
arrays and series parts anchored for it; the PSU passthrough is laid as
single-net lanes; the rails are regions on L3. What is left is routed by
FreeRouting through the standard's `tools/autoroute.py` with all of that
locked (`gen/pcb.py --route`; the directives' `FREEROUTING` setting names
the binary), and the hand pass finishes from there. KiCad Routing Tools
was tried on the same board as a second opinion (2026-10-07): two hours in
it had 25 connections left and 1 646 DRC errors, having routed below the
fab's track and via floors and through the keep-outs; FreeRouting honours
the Specctra rules and the fixed lanes, so it stays the bulk router.

`gen/pcb.py` also runs `kicad-cli pcb drc --severity-all --refill-zones`
(the planes are filled for the check and not saved, so a plane that fails to
fill or strays into a keep-out shows; the unconnected count is the ratsnest's
and does not credit the planes); its report is `drc.txt`.

The board as committed (2026-10-07, routed) is the engine's placement on the
140 × 100 mm outline, bulk-routed by FreeRouting over the locked lanes and
planes (`gen/pcb.py --route`, 30 passes, the plateau at 172 open
connections after the router's optimiser) and given the standard's copper
pass (`--copper`): 3 148 track segments, 47 % of the track length on the
bottom and none on the inner layers, 664 vias of which 360 are ground
stitching on the 5 mm grid (2.8 ground vias per cm² outside the isolated
region), ground floods over 52 % of the top and 60 % of the bottom, notched
around the passthrough block, which floods its own `PSU_GND`. The 282 lane
tracks are locked and intact, every pair matched to 0.00 mm. 129 of the 499
connections are left for the hand pass. DRC reports no errors; its warnings
are 39 starved thermals (ground pads the routing crowds so a flood reaches
them with one spoke; the generator writes that check at warning severity),
three rail islands on L3 that still want vias, and one dangling track end
the router left. From here the board file is the source of truth and is
edited in KiCad; `gen/pcb.py` is not run again over it, except `--copper`,
which adds only what is missing. The schematic generator stays usable: its
derived UUIDs keep the footprints linked.

The ICs' own layout rules, with sources, are in
[docs/layout-guidelines.md](../../docs/layout-guidelines.md).

The engine's numbers (ring gap, tuck depth, through-hole margin, designator
sizes, which side decoupling takes) are calibrated against 79 published
KiCad boards from Olimex, MNT, SparkFun and Raspberry Pi, measured by
`scripts/harvest-placement.py` (the standard's `tools/harvest.py`) over a
local mirror; the comparison and the
decisions are in [docs/reference-boards.md](../../docs/reference-boards.md)
and in the standard's section 9.

Layout order, per the standard's section 8: the edge connectors against the
mechanical drawing (done: they are locked), the isolated passthrough block
(done: fixed parts, island, rules), then by hand the far-placed parts and
the indicator LEDs, the USB 2.0 pairs from each receptacle through its ESD
array to the hub, the bucks' switching loops and the PWR_6A pours, and the
rest.

## Design decisions that were made during capture

These are also reflected in `docs/hardware-spec.md`.

- **Hub port map, strap mode.** USB2517 in strap mode (CFG_SEL = 000) so the
  USB tree needs no firmware. In strap mode the self-powered flag shares a pin
  with the non-removable strap, which only covers ports 1-3 — so the DAPLink
  and FT231X went to ports 1 and 2, port 3 is strap-disabled, and the USB-A
  ports are hub ports 4-7. The hub's SMBus is not connected to the K64.
- **Clock tree.** KSZ8081RNA with a 25 MHz crystal in its default 25 MHz mode;
  its 50 MHz REF_CLK output drives the K64's EXTAL0. This is the FRDM-K64F
  arrangement and what Zephyr's `frdm_k64f` board file expects.
- **Bucks.** TPS54560B for both 5 V rails (5 A, in the library); TPS62823 for
  +3V3. The bucks' EN is gated by the STUSB4500's VBUS_EN_SNK, so no series
  VBUS FET.
- **eFuse.** TPS26630 (in the library), with IMON to a K64 ADC pin.
- **I2C translation.** TXS0102 instead of PCA9306, because a 3.3 V target gives
  VREF equal to the K64 rail, which PCA9306 cannot handle.
- **Magjack.** Kycon G7LX-A88S7-BP-GY, because its library symbol names the
  LED pins.
- **K64 USB regulator.** VREGIN is fed only from J3's VBUS through a Schottky,
  so the K64 cannot back-feed the target and its D+ pull-up vanishes when the
  target is off.

## Verify before fab

Listed on the root sheet and in the spec's open questions: K803 JW1FSN pad
mapping, DAPLink k20dx pin assignments, TPS54560B compensation (placeholders),
TPS2553/TPS26630 limits at bring-up, STUSB4500 from VSYS alone, PCA9517A
isolation with VCC(B) = 0, USB2517 VBUS_DET divider, KSZ8081 crystal load.
