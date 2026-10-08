#!/usr/bin/env python3
"""Generate the KiCad project, run ERC, export the PDF.

    ./build.py            # writes ../sbc-baseboard/*, runs ERC + PDF export

The generated files are a first pass. Once they are edited by hand in KiCad,
the KiCad files are the source of truth and this generator is retired.
"""
import os, re, sys, json, subprocess, shutil, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kisym
from sch import Schematic, uid, set_project, DATE
from kit import Sheet, FP
import sheets_a, sheets_b, sheets_c

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "sbc-baseboard"))
LIBS = os.path.normpath(os.path.join(HERE, "..", "libs"))          # the ecad-libraries submodule
PROJECT = "sbc-baseboard"
PAIR_CLASSES = {"USB", "ETH"}                        # the controlled-impedance classes; every _P/_N net is in one (checked at build)
# the house symbol libraries, by their nickname (file stem), as the project's sym-lib-table names them
kisym.EXTRA_LIBS = {os.path.splitext(os.path.basename(f))[0]: f for f in glob.glob(os.path.join(LIBS, "symbols", "*.kicad_sym"))}


def netclass(name, **kw):
    """A net class as KiCad 10 writes it (net_settings version 4). Geometry is KiCad's default;
    the USB class's differential width and gap are set from the stackup before routing."""
    c = {"bus_width": 12, "clearance": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2,   # Default clearance 0.15: 0.5 mm pitch parts (fab minimum 0.127)
         "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1, "name": name, "pcb_color": "rgba(0, 0, 0, 0.000)",
         "priority": 2147483647, "schematic_color": "rgba(0, 0, 0, 0.000)", "track_width": 0.2, "via_diameter": 0.6,     # 0.2 mm signal tracks, 0.6/0.3 vias: layout.md 5 and 9
         "via_drill": 0.3, "wire_width": 6}
    c.update(kw)
    return c


def net_settings():
    # USB 2.0 pairs: every net named <base>_P / <base>_N (J1_D, J3_D, PORTn_D on the connector side; K64_USB, FTDI_USB at the chips; HUB_UP, HUB_DNn at the hub)
    # 90 ohm differential microstrip on Advanced Circuits' standard 4-layer 62 mil stackup: 1 oz outer
    # copper over a 12 mil prepreg (er 4.6) to the L2 ground plane -> 0.35 mm traces, 0.20 mm gap
    # (edge-coupled microstrip estimate, ~91 ohm); the fab's impedance calculator has the last word
    # current-carrying classes, the current in the name (1 oz outer copper, 10 C rise: 3 A ~ 1.5 mm, 6 A ~ 3.6 mm)
    return {"classes": [netclass("Default", clearance=0.15), netclass("USB", priority=0, diff_pair_width=0.35, diff_pair_gap=0.2, track_width=0.35),
                        netclass("PSU_3A", priority=1, track_width=2.0, clearance=0.3, via_diameter=1.0, via_drill=0.5),
                        netclass("USB_VBUS_3A", priority=2, track_width=2.0, via_diameter=1.0, via_drill=0.5),
                        netclass("PWR_6A", priority=3, track_width=4.0, via_diameter=1.2, via_drill=0.6),
                        netclass("PSU_ISO", priority=4, track_width=0.25),
                        netclass("ETH", priority=5, diff_pair_width=0.28, diff_pair_gap=0.25, track_width=0.28),
                        netclass("PWR_1A", priority=6, track_width=0.5, clearance=0.15)],   # +3V3, routed: no room for a plane of it on L3 among the 6 A rails; the default clearance, since it reaches 0.5 mm pitch pins   # 100 ohm MDI pairs on the same stackup (estimate; the fab's calculator rules)               # the opto's sense nets: isolated like PSU_3A, thin "meta": {"version": 4}, "net_colors": None,
            "netclass_assignments": None,
            "netclass_patterns": [{"netclass": "USB", "pattern": p} for p in ("*_USB_?", "*_D_?", "*HUB_UP_?", "*HUB_DN?_?")]   # sheet-local nets carry their sheet path: the leading * matches it
                               + [{"netclass": "PSU_3A", "pattern": p} for p in ("*PSU_VP", "*PSU_VOUT", "PSU_GND")]   # local nets carry their sheet path
                               + [{"netclass": "PSU_ISO", "pattern": "*PSU_SENSE*"}]
                               + [{"netclass": "ETH", "pattern": "*ETH_?D_?"}]
                               + [{"netclass": "USB_VBUS_3A", "pattern": p} for p in ("VBUS_IN", "*PORT?_VBUS", "*FTDI_VBUS")]
                               + [{"netclass": "PWR_6A", "pattern": p} for p in ("+5V_PORTS", "+5V_TGT", "*+5V_TGT_OUT")]
                               + [{"netclass": "PWR_1A", "pattern": "+3V3"}]}


def main():
    os.makedirs(OUT, exist_ok=True)
    set_project(PROJECT)                          # UUIDs are derived in this project's namespace (see sch.py)
    plib = None                                   # every symbol comes from KiCad's libraries or the house submodule
    root = Schematic(PROJECT, "SBC development baseboard", "A3", 1, "/", file=f"{PROJECT}.kicad_sch")
    root.comments = ["140 x 80 mm, four M3. Spec: docs/hardware-spec.md"]
    defs = [("Power", "power.kicad_sch", sheets_a.power, 1), ("MCU", "mcu.kicad_sch", sheets_a.mcu, 2),
            ("Ethernet", "ethernet.kicad_sch", sheets_b.ethernet, 3), ("USB hub", "hub.kicad_sch", sheets_b.hub, 4),
            ("FTDI", "ftdi.kicad_sch", sheets_b.ftdi, 5), ("DAPLink", "daplink.kicad_sch", sheets_b.daplink, 6),
            ("Target I/O", "target.kicad_sch", sheets_c.target, 7), ("Relays", "relays.kicad_sch", sheets_c.relays, 8)]
    x, y = 30, 40
    for i, (name, file, fn, num) in enumerate(defs):
        suuid = uid("sheet", file)                # the (sheet ...) element in the root; the file has its own
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
             "switched +5V_TGT eFuse, and an isolated PSU passthrough on a 5 A relay. 140 x 80 mm, four M3 at 7 mm from each corner.",
             "",
             "VERIFY BEFORE FAB (also in docs/hardware-spec.md section 8):",
             "  - K803 JW1FSN contact pad mapping (COM 6 / NO 4 / NC 2) against the Panasonic drawing",
             "  - DAPLink K20: pins verified against DAPLink k20dx and the FRDM-K64F OpenSDA circuit; confirm SWD at bring-up",
             "  - TPS54560B compensation values; TPS2553 ILIM at bring-up; TPS26630 UVLO/ILIM",
             "  - STUSB4500 operation from VSYS alone (J17 programmer, no VBUS); PCA9517A isolation with VCC(B) = 0",
             "  - USB2517 VBUS_DET divider (10k/22k) vs the EVB; LED_A/B strap pull-downs",
             "  - KSZ8081 crystal load (22 pF) and 50 MHz REF_CLK series resistor",
             "Reference designators: 1xx power, 2xx MCU, 3xx Ethernet, 4xx hub, 5xx FTDI, 6xx DAPLink, 7xx target I/O, 8xx relays and passthrough."]
    for i, ln in enumerate(notes):
        root.text(ln, (30, 175 + i * 3.2), size=1.6, bold=(i == 0))
    root.emit(os.path.join(OUT, f"{PROJECT}.kicad_sch"), root.uuid)
    # project file, project symbol library, lib table
    # board constraints: Advanced Circuits' standard-process minimums (0.005" trace/space, 0.010" copper to edge,
    # 0.006" drill); thermal vias in the library footprints are 0.2 mm, which the fab allows
    rules = {"min_clearance": 0.127, "min_track_width": 0.127, "min_through_hole_diameter": 0.2, "min_hole_clearance": 0.25,
             "min_hole_to_hole": 0.25, "min_copper_edge_clearance": 0.25, "min_via_diameter": 0.5, "min_via_annular_width": 0.125,
             "min_connection": 0.127, "solder_mask_to_copper_clearance": 0.0,
             "min_text_height": 0.7, "min_text_thickness": 0.1}       # silk: the standard's smallest designator (section 6), the fab's 0.1 mm line
    # a pad the routing crowds so a zone reaches it with one spoke is connected: a warning for the hand pass, not an
    # error (ecad-standards/layout.md section 4); KiCad's default severity for it is error
    severities = {"starved_thermal": "warning"}
    pro = {"board": {"design_settings": {"defaults": {}, "rules": rules, "rule_severities": severities}, "layer_presets": [], "viewports": []},
           "boards": [], "cvpcb": {"equivalence_files": []}, "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
           "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 1}, "net_settings": net_settings(),
           "pcbnew": {"page_layout_descr_file": ""}, "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
           "sheets": [[root.uuid, "Root"]], "text_variables": {}}
    json.dump(pro, open(os.path.join(OUT, f"{PROJECT}.kicad_pro"), "w"), indent=2)
    # library tables: the fragments the submodule ships, which refer to it as ${KIPRJMOD}/../libs
    for table in ("sym-lib-table", "fp-lib-table"):
        shutil.copyfile(os.path.join(LIBS, "tables", table), os.path.join(OUT, table))
    print(f"wrote {OUT}")
    # ERC + PDF
    sch = os.path.join(OUT, f"{PROJECT}.kicad_sch")
    r = subprocess.run(["kicad-cli", "sch", "erc", "--severity-all", "--format", "report", "-o", os.path.join(OUT, "erc.txt"), sch],
                       capture_output=True, text=True)
    print((r.stdout + r.stderr).strip()[-300:])
    # the report header carries the export time: pin it to the title-block date so two builds of one design match
    erc = os.path.join(OUT, "erc.txt")
    lines = open(erc, encoding="utf-8").read().split("\n")
    lines[0] = re.sub(r"\(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", f"({DATE}T00:00:00", lines[0])
    open(erc, "w", encoding="utf-8").write("\n".join(lines))
    # every pair net (named _P/_N, on either side of a flow-through ESD array) must be in a pair class, or it is
    # routed at the default geometry instead of its impedance (ecad-standards/layout.md 3.8)
    xml = os.path.join(OUT, "netlist-check.xml")
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", xml, sch], capture_output=True, text=True)
    import xml.etree.ElementTree as ET
    classes = {n.get("name"): (n.get("class") or "Default") for n in ET.parse(xml).getroot().iter("net")}
    pairs = {n: c for n, c in classes.items() if re.search(r"_[PN]$", n) and (n[:-1] + ("N" if n.endswith("P") else "P")) in classes}   # a _P with its _N
    os.remove(xml)
    unclassed = sorted(n for n, c in pairs.items() if c not in PAIR_CLASSES)
    print(f"pair nets: {len(pairs)}, in a pair class: {len(pairs) - len(unclassed)}" + (f"; NOT classed: {' '.join(unclassed)}" if unclassed else ""))
    if unclassed:
        raise SystemExit("pair nets outside a pair class")
    # BOM: grouped by value and footprint, full reference lists (no ranges), as the README documents
    r = subprocess.run(["kicad-cli", "sch", "export", "bom", "--fields", "Reference,Value,Footprint,${QUANTITY}",
                        "--labels", "Reference,Value,Footprint,QUANTITY", "--group-by", "Value,Footprint",
                        "--ref-range-delimiter", "", "-o", os.path.join(OUT, "bom.csv"), sch], capture_output=True, text=True)
    print((r.stdout + r.stderr).strip()[-200:])
    pdf = os.path.join(OUT, f"{PROJECT}.pdf")
    r = subprocess.run(["kicad-cli", "sch", "export", "pdf", "-o", pdf, sch], capture_output=True, text=True)
    print((r.stdout + r.stderr).strip()[-200:])
    # the PDF's creation date is the only thing that differs between two exports of one design: pin it too
    # (same length as what KiCad wrote, so the file's offsets stay valid)
    raw = open(pdf, "rb").read()
    stamp = DATE.replace("-", ":").encode() + b":00:00:00"
    raw2 = re.sub(rb"/CreationDate \(D:\d{4}:\d{2}:\d{2}:\d{2}:\d{2}:\d{2}\)", b"/CreationDate (D:" + stamp + b")", raw)
    if raw2 != raw:
        open(pdf, "wb").write(raw2)


if __name__ == "__main__":
    main()
