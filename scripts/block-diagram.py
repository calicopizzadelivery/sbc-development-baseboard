#!/usr/bin/env python3
"""Regenerate docs/block-diagram.svg and .png from the layout below.

    ./scripts/block-diagram.py            # both files
    ./scripts/block-diagram.py --svg-only # no Chrome needed

The layout is by hand, on purpose: one lane per interface off a tall MCU box
gives orthogonal routing with no crossings, which an auto-layout never managed
for this topology. When the configuration changes, change the boxes and paths
here, run it, and commit all three files together.

The PNG is the SVG rendered by headless Chrome at 2x and dated in the corner.
"""
import os, pathlib, shutil, subprocess, sys, tempfile, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
SVG = ROOT / "docs" / "block-diagram.svg"
PNG = ROOT / "docs" / "block-diagram.png"

STAMP = f"spec rev 0.1 · {datetime.date.today().isoformat()}"

W, H = 1760, 1700
out = []
def e(s): out.append(s)

# ---------- palette (light, printable)
C = dict(
    ink="#1f2430", mute="#5b6372", line="#2b3340", power="#b45309", iso="#15803d",
    panel="#f5f6f8", panel_edge="#d6d9de", conn="#dbeafe", conn_edge="#2563eb",
    dev="#ffffff", dev_edge="#374151", mcu="#fef3c7", mcu_edge="#b45309",
    pwr="#ffedd5", pwr_edge="#c2410c", isofill="#ecfdf5", iso_edge="#15803d",
    tag="#fff7ed", tag_edge="#c2410c",
)

def box(x, y, w, h, title, sub=None, kind="dev", r=6):
    fill, edge = {"dev": (C["dev"], C["dev_edge"]), "conn": (C["conn"], C["conn_edge"]),
                  "mcu": (C["mcu"], C["mcu_edge"]), "pwr": (C["pwr"], C["pwr_edge"])}[kind]
    e(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{edge}" stroke-width="1.6"/>')
    lines = [title] + (sub if isinstance(sub, list) else ([sub] if sub else []))
    n = len(lines); lh = 17
    y0 = y + h/2 - (n-1)*lh/2 + 5
    for i, t in enumerate(lines):
        wt = "600" if i == 0 else "400"
        col = C["ink"] if i == 0 else C["mute"]
        fs = 14 if i == 0 else 12.5
        e(f'<text x="{x+w/2}" y="{y0+i*lh}" text-anchor="middle" font-size="{fs}" font-weight="{wt}" fill="{col}">{t}</text>')

def path(pts, label=None, lpos=None, arrow="end", width=1.6, color=None, dash=None, anchor="middle"):
    color = color or C["line"]
    d = "M " + " L ".join(f"{x},{y}" for x, y in pts)
    ms = ' marker-start="url(#arrowR)"' if arrow in ("both",) else ""
    me = ' marker-end="url(#arrow)"' if arrow in ("end", "both") else ""
    da = f' stroke-dasharray="{dash}"' if dash else ""
    e(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{ms}{me}{da}/>')
    if label:
        lx, ly = lpos
        e(f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" font-size="12" fill="{C["mute"]}" '
          f'paint-order="stroke" stroke="#ffffff" stroke-width="4" stroke-linejoin="round">{label}</text>')

def tag(x, y, text, anchor="start"):
    tw = len(text) * 7.2 + 14
    tx = x if anchor == "start" else x - tw
    e(f'<rect x="{tx}" y="{y-10}" width="{tw}" height="20" rx="10" fill="{C["tag"]}" stroke="{C["tag_edge"]}" stroke-width="1"/>')
    e(f'<text x="{tx+tw/2}" y="{y+4}" text-anchor="middle" font-size="11.5" font-weight="600" fill="{C["power"]}">{text}</text>')

def header(x, y, text):
    e(f'<text x="{x}" y="{y}" font-size="13" font-weight="700" letter-spacing="1.5" fill="{C["mute"]}">{text}</text>')

LED = dict(out="#16a34a", rail="#d97706", coil="#dc2626")
def led(x, y, kind):
    e(f'<circle cx="{x}" cy="{y}" r="5.5" fill="{LED[kind]}" stroke="#1f2430" stroke-width="1"/>')
def rgb(x, y):
    for i, c in enumerate(("#dc2626", "#16a34a", "#2563eb")):
        e(f'<circle cx="{x+i*12}" cy="{y}" r="4" fill="{c}" stroke="#1f2430" stroke-width="0.8"/>')

e(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
  f'font-family="Inter, Helvetica, Arial, DejaVu Sans, sans-serif">')
e('<defs>'
  f'<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
  f'<path d="M0,1 L9,5 L0,9 z" fill="{C["line"]}"/></marker>'
  f'<marker id="arrowR" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
  f'<path d="M10,1 L1,5 L10,9 z" fill="{C["line"]}"/></marker>'
  '</defs>')
e(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

# ---------- title
e(f'<text x="30" y="34" font-size="20" font-weight="700" fill="{C["ink"]}">SBC development baseboard — block diagram</text>')
e(f'<text x="{W-30}" y="34" text-anchor="end" font-size="12.5" fill="{C["mute"]}">{STAMP}</text>')

# ---------- panels
for (x, w, t) in [(30, 240, "FACING YOU"), (300, 1120, "BASEBOARD"), (1450, 280, "FACING THE TARGET")]:
    e(f'<rect x="{x}" y="52" width="{w}" height="1030" rx="10" fill="{C["panel"]}" stroke="{C["panel_edge"]}"/>')
    header(x + 14, 74, t)

# ---------- isolation region (drawn before boxes so boxes sit on top)
e(f'<rect x="312" y="935" width="1096" height="130" rx="8" fill="{C["isofill"]}" stroke="{C["iso_edge"]}" stroke-width="1.4" stroke-dasharray="7 5"/>')
e(f'<text x="326" y="1052" font-size="12" font-weight="600" fill="{C["iso"]}">ISOLATED — the passthrough nets connect to no board net. Not the ground plane, not a rail. No indicator LED: the voltage is unknown.</text>')

# ---------- left column: connectors facing you
box(50, 90, 200, 60, "J1  USB-C", "upstream data · USB 2.0", "conn")
box(50, 290, 200, 60, "J10  RJ45", "10/100 Ethernet", "conn")
box(50, 400, 200, 60, "J16  Cortex debug", "SWD, bypasses DAPLink", "conn")
box(50, 520, 200, 60, "J2  USB-C", "PD power in · no data", "conn")
box(50, 610, 200, 60, "J17  JST SH 1.0 mm", "PD programming · Qwiic", "conn")
box(50, 950, 200, 70, "J18  Phoenix 5.08", ["PSU in", "0–30 VDC · 5 A"], "conn")

# ---------- center-left devices
box(330, 85, 200, 75, "USB2517", "7-port USB 2.0 HS · strap mode · port 3 n/c")
box(330, 195, 200, 60, "MK20DX128  DAPLink", "SWD · CDC · MSD")
box(330, 290, 200, 60, "KSZ8081RNA", "RMII PHY")
box(330, 520, 200, 150, "STUSB4500", ["USB-PD sink", "autonomous, NVM PDOs", "I2C readback"], "pwr")
box(580, 565, 130, 60, "PCA9517A", "I2C buffer")
e(f'<text x="645" y="645" text-anchor="middle" font-size="11" fill="{C["mute"]}">EN low while J17 powered</text>')
e(f'<text x="645" y="659" text-anchor="middle" font-size="11" fill="{C["mute"]}">→ K64 disconnected in hardware</text>')

# power tree
box(330, 735, 200, 45, "buck 1 · TPS54560B", "+5V_PORTS · 5 A", "pwr")
box(330, 800, 200, 45, "buck 3 · TPS62823", "+3V3 · 3 A", "pwr")
box(330, 865, 200, 45, "buck 2 · TPS54560B", "+5V_TGT · 5 A", "pwr")
path([(430, 670), (430, 735)], width=2.4, color=C["power"])
path([(430, 705), (310, 705), (310, 887), (330, 887)], width=2.4, color=C["power"])
e(f'<text x="446" y="700" font-size="11.5" font-weight="600" fill="{C["power"]}">VBUS_IN 5–20 V</text>')
path([(430, 780), (430, 800)], width=2.4, color=C["power"])
tag(540, 757, "+5V_PORTS → switches, coils")
tag(540, 822, "+3V3 → logic")
tag(540, 887, "+5V_TGT → eFuse")

# opto, straddling the barrier
e(f'<rect x="690" y="900" width="150" height="70" rx="6" fill="{C["dev"]}" stroke="{C["dev_edge"]}" stroke-width="1.6"/>')
e(f'<text x="765" y="924" text-anchor="middle" font-size="14" font-weight="600" fill="{C["ink"]}">optocoupler</text>')
e(f'<line x1="692" y1="935" x2="838" y2="935" stroke="{C["iso_edge"]}" stroke-width="1.4" stroke-dasharray="7 5"/>')
e(f'<text x="765" y="958" text-anchor="middle" font-size="12.5" fill="{C["mute"]}">PSU presence</text>')

# ---------- MCU
box(780, 180, 200, 580, "MK64FN1M0VLL12", ["Cortex-M4F · 120 MHz", "1 MB flash · 256 KB SRAM", "", "USB FS device", "10/100 ENET MAC", "", "Zephyr", "frdm-k64f-hid lineage"], "mcu", r=10)

# ---------- center-right devices
box(1090, 85, 220, 50, "FT231X", "USB-UART · 3.3 V I/O · TX/RX LEDs")
box(1090, 155, 220, 50, "5× TPS2553", "4× USB-A at 1.1 A · 1× FT231X")
tag(1215, 221, "+5V_PORTS")
path([(1200, 155), (1200, 135)], width=2.4, color=C["power"])
box(1090, 345, 220, 55, "TXB0104", "UART level shift · VREF from target")
box(1090, 415, 220, 55, "TXB0108 + TXS0102", "GPIO push-pull · I2C open-drain")
box(1090, 490, 220, 55, "2× Omron G6K-1F-Y", "SPDT signal relay · gold contacts · 1 A")
box(1090, 565, 220, 55, "TPS26630 eFuse", "+5V_TGT · 5 A · /FAULT · IMON")
tag(1095, 635, "+5V_TGT")
# power relay straddling the barrier
e(f'<rect x="1090" y="880" width="220" height="120" rx="6" fill="{C["dev"]}" stroke="{C["dev_edge"]}" stroke-width="1.6"/>')
e(f'<text x="1200" y="903" text-anchor="middle" font-size="14" font-weight="600" fill="{C["ink"]}">JW1FSN power relay</text>')
e(f'<text x="1200" y="922" text-anchor="middle" font-size="12.5" fill="{C["mute"]}">coil: +5V_PORTS · FET + flyback</text>')
e(f'<line x1="1092" y1="935" x2="1308" y2="935" stroke="{C["iso_edge"]}" stroke-width="1.4" stroke-dasharray="7 5"/>')
e(f'<text x="1200" y="962" text-anchor="middle" font-size="12.5" fill="{C["mute"]}">NO · 10 A at 30 VDC · AgSnO2</text>')
e(f'<text x="1200" y="980" text-anchor="middle" font-size="12.5" fill="{C["mute"]}">COM → NO when energized</text>')

# ---------- right column
box(1470, 85, 240, 50, "J9  FTDI header · 6-pin 0.1″", "GND CTS VCC TXD RXD DTR · 3.3 V", "conn")
box(1470, 155, 240, 50, "J4, J5  2× stacked USB-A", "4 ports · bench · each switched", "conn")
box(1470, 270, 240, 55, "J3  USB-C", "HID kbd + mouse · VBUS sense-only", "conn")
box(1470, 345, 240, 55, "J13  Phoenix 3.5", "console: VREF · TXD · RXD · GND", "conn")
box(1470, 415, 240, 55, "J15  2×6 header", "6× GPIO · I2C · VREF · GND", "conn")
box(1470, 490, 240, 55, "J11, J12  Phoenix 3.5", "COM · NO · NC, per relay", "conn")
box(1470, 565, 240, 55, "J14  Phoenix 5.08", "+5V_TGT out · 5 A", "conn")
box(1470, 950, 240, 70, "J19  Phoenix 5.08", ["PSU out", "V+ via NO · GND via bus"], "conn")

# ---------- indicator LEDs (on the net, not on a pin)
led(1298, 95, "out"); led(1298, 165, "out"); led(1298, 575, "out")          # FT231X VBUS, port switches, eFuse out
led(518, 745, "rail"); led(518, 810, "rail"); led(518, 875, "rail")          # +5V_PORTS, +3V3, +5V_TGT
led(560, 696, "rail"); led(698, 575, "rail")                                 # VBUS_IN, +3V3_PD
led(1298, 500, "coil"); led(1298, 890, "coil")                               # signal relays, passthrough coil
rgb(944, 192)                                                                # heartbeat

# ---------- edges: USB / debug / ethernet
path([(250, 120), (330, 120)])
path([(530, 110), (1090, 110)], "port 2", (700, 104))
path([(530, 130), (1050, 130), (1050, 180), (1090, 180)], "ports 4–7", (950, 124))
path([(380, 160), (380, 195)], "port 1 · unswitched", (392, 183), anchor="start")
path([(1310, 110), (1470, 110)], "UART · 3.3 V", (1390, 104))
path([(1310, 180), (1470, 180)])
path([(530, 225), (780, 225)], "SWD + UART", (655, 219))
path([(250, 320), (330, 320)])
path([(530, 320), (780, 320)], "RMII", (655, 314))
path([(250, 430), (780, 430)], "SWD, direct", (515, 424))

# PD + programming
path([(250, 550), (330, 550)], "VBUS", (290, 544), width=2.4, color=C["power"])
path([(250, 640), (330, 640)], "I2C + VSYS", (290, 634))
path([(530, 595), (580, 595)], arrow="both")
path([(710, 595), (780, 595)], "I2C", (745, 589), arrow="both")

# MCU outputs
path([(980, 230), (1200, 230), (1200, 205)], "5× EN · 5× /FAULT", (1090, 224))
path([(980, 297), (1470, 297)], "USB FS device", (1225, 291))
path([(980, 372), (1090, 372)], "UART", (1035, 366)); path([(1310, 372), (1470, 372)])
path([(980, 442), (1090, 442)], "GPIO · I2C", (1035, 436)); path([(1310, 442), (1470, 442)])
path([(980, 517), (1090, 517)], "2× FET + flyback", (1035, 511)); path([(1310, 517), (1470, 517)], "dry contacts", (1390, 511))
path([(980, 592), (1090, 592)], "EN · /FAULT", (1035, 586)); path([(1310, 592), (1470, 592)], "5 A", (1390, 586), width=2.4, color=C["power"])
path([(980, 700), (1200, 700), (1200, 880)], "coil drive · FET + flyback", (1212, 800), anchor="start")

# passthrough
path([(250, 975), (1090, 975)], "V+  →  COM", (960, 991), width=2.6, color=C["iso"])
path([(1310, 975), (1470, 975)], "NO", (1390, 969), width=2.6, color=C["iso"])
path([(250, 1010), (1470, 1010)], "GND · copper bus ≥ 5 mm, both outer layers", (900, 1028), width=5, color=C["iso"], arrow="none")
# opto stubs + sense line
e(f'<line x1="740" y1="970" x2="740" y2="975" stroke="{C["iso"]}" stroke-width="1.6"/>')
e(f'<line x1="790" y1="970" x2="790" y2="1010" stroke="{C["iso"]}" stroke-width="1.6"/>')
e(f'<circle cx="740" cy="975" r="3.2" fill="{C["iso"]}"/><circle cx="790" cy="1010" r="3.2" fill="{C["iso"]}"/>')
path([(765, 900), (765, 850), (820, 850), (820, 760)], "PSU present", (700, 854), anchor="end")

# ---------- mechanical inset, to scale
MX, MY, S = 40, 1165, 5            # origin in px, px per mm
def mm(x, y): return (MX + x*S, MY + y*S)
e(f'<text x="{MX}" y="{MY-22}" font-size="14" font-weight="700" fill="{C["ink"]}">Mechanical — 140 × 100 mm · 4× M3, 7 mm from each corner · to scale · component side</text>')
e(f'<rect x="{MX}" y="{MY}" width="{140*S}" height="{100*S}" rx="6" fill="#ffffff" stroke="{C["ink"]}" stroke-width="2"/>')
for hx, hy in [(7,7),(133,7),(7,93),(133,93)]:
    cx, cy = mm(hx, hy)
    e(f'<circle cx="{cx}" cy="{cy}" r="{3*S}" fill="none" stroke="{C["mute"]}" stroke-dasharray="3 3"/>')
    e(f'<circle cx="{cx}" cy="{cy}" r="{1.6*S}" fill="#ffffff" stroke="{C["ink"]}" stroke-width="1.5"/>')
e(f'<text x="{mm(7,7)[0]+18}" y="{mm(7,7)[1]-14}" font-size="10" fill="{C["mute"]}">M3 · 6 mm pad</text>')
DEPTH = 8
def conn(edge, a, L, label, depth=DEPTH):
    if edge == "T":                                               # the back edge: the RJ45, its long axis inboard
        x, y = mm(a, 0)
        e(f'<rect x="{x}" y="{y}" width="{L*S}" height="{depth*S}" fill="{C["conn"]}" stroke="{C["conn_edge"]}"/>')
        e(f'<text x="{x+L*S/2}" y="{y+depth*S+14}" text-anchor="middle" font-size="11" fill="{C["ink"]}">{label}</text>')
    elif edge == "L":
        x, y = mm(0, a)
        e(f'<rect x="{x}" y="{y}" width="{DEPTH*S}" height="{L*S}" fill="{C["conn"]}" stroke="{C["conn_edge"]}"/>')
        e(f'<text x="{x+DEPTH*S+6}" y="{y+L*S/2+4}" font-size="11" fill="{C["ink"]}">{label}</text>')
    elif edge == "R":
        x, y = mm(140-DEPTH, a)
        e(f'<rect x="{x}" y="{y}" width="{DEPTH*S}" height="{L*S}" fill="{C["conn"]}" stroke="{C["conn_edge"]}"/>')
        e(f'<text x="{x-6}" y="{y+L*S/2+4}" text-anchor="end" font-size="11" fill="{C["ink"]}">{label}</text>')
    elif edge == "B":
        x, y = mm(a, 100-DEPTH)
        e(f'<rect x="{x}" y="{y}" width="{L*S}" height="{DEPTH*S}" fill="{C["conn"]}" stroke="{C["conn_edge"]}"/>')
        e(f'<text x="{x+L*S/2}" y="{y-6}" text-anchor="middle" font-size="11" fill="{C["ink"]}">{label}</text>')
# the edge table of docs/layout-directives.md (gen/layout.py CONNECTORS; the courtyards of the placed board, 2026-10-08)
conn("T", 71, 19, "J10 RJ45", depth=22.4)
conn("L", 24.7, 10.6, "J2 PD in"); conn("L", 68.7, 10.6, "J1 upstream")
conn("R", 14, 10.7, "J3 HID"); conn("R", 35.7, 16.6, "J13 console"); conn("R", 63.2, 16.3, "J9 FTDI")
conn("B", 14, 17.2, "J5"); conn("B", 32.2, 17.2, "J4"); conn("B", 52.4, 13.2, "J18"); conn("B", 66.6, 13.2, "J19")
conn("B", 84.6, 13.1, "J11"); conn("B", 98.7, 13.1, "J12"); conn("B", 112.8, 13.2, "J14")
for (hx, hy, hw, hh, lab) in [(91.9, 3.8, 4.5, 7.5, "J16 SWD"), (115.2, 8.2, 6.2, 16.3, "J15 GPIO"), (34.1, 47.4, 7.9, 5.3, "J17 prog")]:
    x, y = mm(hx, hy)
    e(f'<rect x="{x}" y="{y}" width="{hw*S}" height="{hh*S}" fill="{C["dev"]}" stroke="{C["dev_edge"]}"/>')
    if hx + hw > 110:                                                 # near the right edge: the label on the left, clear of J3
        e(f'<text x="{x-6}" y="{y+hh*S/2+4}" text-anchor="end" font-size="11" fill="{C["ink"]}">{lab}</text>')
    else:
        e(f'<text x="{x+hw*S+6}" y="{y+hh*S/2+4}" font-size="11" fill="{C["ink"]}">{lab}</text>')
e(f'<text transform="rotate(-90 {MX-16} {MY+50*S})" x="{MX-16}" y="{MY+50*S}" text-anchor="middle" font-size="12" font-weight="700" letter-spacing="1.5" fill="{C["mute"]}">FACING YOU</text>')
e(f'<text transform="rotate(90 {MX+140*S+18} {MY+50*S})" x="{MX+140*S+18}" y="{MY+50*S}" text-anchor="middle" font-size="12" font-weight="700" letter-spacing="1.5" fill="{C["mute"]}">FACING THE TARGET</text>')
e(f'<text x="{MX+70*S}" y="{MY+100*S+20}" text-anchor="middle" font-size="11.5" fill="{C["mute"]}">front edge — overflow from the short edges; your end on the left, the target\'s on the right · back edge: the RJ45</text>')

# ---------- indicator key
KX, KY = 800, 1150
e(f'<text x="{KX}" y="{KY}" font-size="14" font-weight="700" fill="{C["ink"]}">Indicators — on the net, not on a pin</text>')
rows = [("out", "Switched outputs, green — PORT 1–4, FT231X, +5V_TGT at the eFuse (6)"),
        ("rail", "Rails, amber — VBUS_IN, +5V_PORTS, +5V_TGT, +3V3, +3V3_PD (5)"),
        ("coil", "Coils, red — relay 1, relay 2, passthrough (3)"),
        ("rgb", "Heartbeat — K64 RGB, firmware alive (1)"),
        ("out", "TX / RX — FT231X CBUS, beside J9 (2)"),
        (None, "Link / activity — in the RJ45"),
        (None, "None on J18 / J19 — the voltage is whatever was plugged in"),
        (None, "An LED shows the actual state: a switch tripped on overcurrent goes dark even if firmware thinks it is on.")]
for i, (k, t) in enumerate(rows):
    y = KY + 30 + i*27
    if k == "rgb": rgb(KX+6, y-4)
    elif k: led(KX+8, y-4, k)
    e(f'<text x="{KX+40}" y="{y}" font-size="12.5" fill="{C["ink"] if k else C["mute"]}">{t}</text>')

# ---------- legend
lx, ly = 1455, 1095
e(f'<line x1="{lx}" y1="{ly}" x2="{lx+28}" y2="{ly}" stroke="{C["line"]}" stroke-width="1.6" marker-end="url(#arrow)"/>')
e(f'<text x="{lx+34}" y="{ly+4}" font-size="11.5" fill="{C["mute"]}">signal</text>')
e(f'<line x1="{lx+90}" y1="{ly}" x2="{lx+118}" y2="{ly}" stroke="{C["power"]}" stroke-width="2.6"/>')
e(f'<text x="{lx+124}" y="{ly+4}" font-size="11.5" fill="{C["mute"]}">board power</text>')
e(f'<line x1="{lx+206}" y1="{ly}" x2="{lx+234}" y2="{ly}" stroke="{C["iso"]}" stroke-width="2.6"/>')
e(f'<text x="{lx+240}" y="{ly+4}" font-size="11.5" fill="{C["mute"]}">isolated</text>')
e('</svg>')



SVG.write_text("\n".join(out))
print(f"wrote {SVG.relative_to(ROOT)}")

if "--svg-only" in sys.argv:
    sys.exit(0)

chrome = next((c for c in ("google-chrome", "chromium", "chromium-browser", "google-chrome-stable") if shutil.which(c)), None)
if not chrome:
    sys.exit("no Chrome/Chromium on PATH; use --svg-only or install one")
with tempfile.TemporaryDirectory() as td:
    wrap = pathlib.Path(td) / "wrap.html"
    wrap.write_text('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0;overflow:hidden;background:#fff}</style></head>'
                    f'<body><img src="file://{SVG}" width="{W}" height="{H}"></body></html>')
    r = subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=2", f"--window-size={W},{H}",
                        f"--screenshot={PNG}", f"file://{wrap}"], capture_output=True, text=True, timeout=90)
if not PNG.exists():
    sys.exit(f"render failed:\n{r.stderr[-800:]}")
print(f"wrote {PNG.relative_to(ROOT)} ({PNG.stat().st_size // 1024} KiB)")
