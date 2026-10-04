#!/usr/bin/env python3
"""Generate the KiCad project, run ERC, export the PDF.

    ./build.py            # writes ../sbc-baseboard/*, runs ERC + PDF export

The generated files are a first pass. Once they are edited by hand in KiCad,
the KiCad files are the source of truth and this generator is retired.
"""
import os, sys, json, subprocess, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sch import Schematic, uid
from kit import Sheet, FP
import parts, sheets_a, sheets_b, sheets_c

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "sbc-baseboard"))
PROJECT = "sbc-baseboard"


def main():
    os.makedirs(OUT, exist_ok=True)
    plib = parts.project_lib()
    root = Schematic(PROJECT, "SBC development baseboard", "A3", 1, "/")
    root.comments = ["140 x 80 mm, four M3. Spec: docs/hardware-spec.md"]
    defs = [("Power", "power.kicad_sch", sheets_a.power, 1), ("MCU", "mcu.kicad_sch", sheets_a.mcu, 2),
            ("Ethernet", "ethernet.kicad_sch", sheets_b.ethernet, 3), ("USB hub", "hub.kicad_sch", sheets_b.hub, 4),
            ("FTDI", "ftdi.kicad_sch", sheets_b.ftdi, 5), ("DAPLink", "daplink.kicad_sch", sheets_b.daplink, 6),
            ("Target I/O", "target.kicad_sch", sheets_c.target, 7), ("Relays", "relays.kicad_sch", sheets_c.relays, 8)]
    x, y = 30, 40
    for i, (name, file, fn, num) in enumerate(defs):
        suuid = uid()
        sh = fn(PROJECT, num, i + 2, "/" + suuid, plib)
        sh.emit(os.path.join(OUT, file), root.uuid)
        root.sheet(name, file, (x + (i % 4) * 60, y + (i // 4) * 40), (50, 25), suuid, i + 2)
    # root: mounting holes and the design summary
    for n in range(4):
        h = root.add("Mechanical", "MountingHole_Pad", f"H{n+1}", "M3", (40 + n * 15, 150), footprint=FP["HOLE"])
        root.pin_power(h, "1", "GND")
    notes = ["SBC DEVELOPMENT BASEBOARD - schematic first pass, generated 2026-10-04",
             "One board for remote development on an attached SBC: K64 as USB HID to the target and Ethernet to the workstation,",
             "four switched USB-A ports, FT231X FTDI header, two isolated SPDT signal relays, level-shifted console and GPIO/I2C,",
             "switched +5V_TGT eFuse, and an isolated PSU passthrough on a 5 A relay. 140 x 80 mm, four M3 at 10 mm from each corner.",
             "",
             "VERIFY BEFORE FAB (also in docs/hardware-spec.md section 8):",
             "  - K803 JW1FSN contact pad mapping (COM 6 / NO 4 / NC 2) against the Panasonic drawing",
             "  - DAPLink k20dx HIC pin assignments (SWCLK PTC5, SWDIO PTC6, nRESET PTB1, LED PTD4, UART1 PTC3/4)",
             "  - TPS54560B compensation values; TPS2553 ILIM at bring-up; TPS26630 UVLO/ILIM",
             "  - STUSB4500 operation from VSYS alone (J17 programmer, no VBUS); PCA9517A isolation with VCC(B) = 0",
             "  - USB2517 VBUS_DET divider (10k/22k) vs the EVB; LED_A/B strap pull-downs",
             "  - KSZ8081 crystal load (22 pF) and 50 MHz REF_CLK series resistor",
             "Reference designators: 1xx power, 2xx MCU, 3xx Ethernet, 4xx hub, 5xx FTDI, 6xx DAPLink, 7xx target I/O, 8xx relays and passthrough."]
    for i, ln in enumerate(notes):
        root.text(ln, (30, 175 + i * 3.2), size=1.6, bold=(i == 0))
    root.emit(os.path.join(OUT, f"{PROJECT}.kicad_sch"), root.uuid)
    # project file, project symbol library, lib table
    pro = {"board": {"design_settings": {"defaults": {}, "rules": {}}, "layer_presets": [], "viewports": []},
           "boards": [], "cvpcb": {"equivalence_files": []}, "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
           "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 1}, "net_settings": {"classes": [], "meta": {"version": 3}},
           "pcbnew": {"page_layout_descr_file": ""}, "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
           "sheets": [[root.uuid, "Root"]], "text_variables": {}}
    json.dump(pro, open(os.path.join(OUT, f"{PROJECT}.kicad_pro"), "w"), indent=2)
    parts.write_lib(os.path.join(OUT, f"{PROJECT}.kicad_sym"))
    open(os.path.join(OUT, "sym-lib-table"), "w").write(
        '(sym_lib_table\n\t(version 7)\n\t(lib (name "sbcbb")(type "KiCad")(uri "${KIPRJMOD}/' + PROJECT + '.kicad_sym")(options "")(descr "project symbols"))\n)\n')
    open(os.path.join(OUT, "fp-lib-table"), "w").write('(fp_lib_table\n\t(version 7)\n)\n')
    print(f"wrote {OUT}")
    # ERC + PDF
    sch = os.path.join(OUT, f"{PROJECT}.kicad_sch")
    r = subprocess.run(["kicad-cli", "sch", "erc", "--severity-all", "--format", "report", "-o", os.path.join(OUT, "erc.txt"), sch],
                       capture_output=True, text=True)
    print((r.stdout + r.stderr).strip()[-300:])
    r = subprocess.run(["kicad-cli", "sch", "export", "pdf", "-o", os.path.join(OUT, f"{PROJECT}.pdf"), sch], capture_output=True, text=True)
    print((r.stdout + r.stderr).strip()[-200:])


if __name__ == "__main__":
    main()
