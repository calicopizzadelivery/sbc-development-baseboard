# KiCad project

`sbc-baseboard/` is the KiCad 10 project: a root sheet and seven sub-sheets,
a project symbol library for the five parts the standard libraries lack, an
ERC report, a PDF of every sheet and a BOM.

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
  target.kicad_sch          console, GPIO/I2C, relays, +5V_TGT eFuse, PSU passthrough
  sbc-baseboard.kicad_sym   project symbols: K64, USB2517, TPS2553, PCA9517A, JW1FSN
  sym-lib-table             maps the "sbcbb" nickname to that library
  sbc-baseboard.pdf         all eight sheets
  erc.txt, bom.csv
```

Reference designators are numbered by sheet: R1xx/C1xx power, 2xx MCU,
3xx Ethernet, 4xx hub, 5xx FTDI, 6xx DAPLink, 7xx target I/O.

## How it was made, and the handoff

The first pass was **generated**, by `gen/build.py`. That generator pulls
symbols from KiCad's own libraries (so the embedded copies match what KiCad
ships), builds the five missing symbols from datasheet pin tables, lays each
sheet out as an IC with a net label on every pin plus rows of passives, and
writes the `.kicad_sch` files directly. It then runs `kicad-cli sch erc` and
exports the PDF. Pin-position maths and power-symbol net naming were calibrated
against `kicad-cli`'s netlist export before any real sheet was built.

**The generator is bring-up tooling, not the source of truth.** The moment
anyone edits the schematic in KiCad, the KiCad files are the design and
`gen/` is history: re-running `build.py` would overwrite the edits. The honest
next steps are in KiCad, not here — tidy wiring where labels-on-every-pin
reads badly, then layout.

```bash
cd gen && ./build.py        # regenerate everything (only while nothing has been hand-edited)
```

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

Listed on the root sheet and in the spec's open questions: JW1FSN pad
mapping, DAPLink k20dx pin assignments, TPS54560B compensation (placeholders),
TPS2553/TPS26630 limits at bring-up, STUSB4500 from VSYS alone, PCA9517A
isolation with VCC(B) = 0, USB2517 VBUS_DET divider, KSZ8081 crystal load.
