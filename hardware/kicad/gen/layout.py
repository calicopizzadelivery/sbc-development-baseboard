"""The layout directives as data: docs/layout-directives.md, in millimetres.

Board origin top-left, X right, Y down (as KiCad draws it). Everything here
is placement intent; pcb.py turns it into the first board file.
"""
BOARD = (140.0, 100.0)      # 140 x 80 until 2026-10-07: 20 mm added below y = 52, the front-edge blocks moved with the edge
RADIUS = 2.0
HOLES = {"H1": (7.0, 7.0), "H2": (133.0, 7.0), "H3": (7.0, 93.0), "H4": (133.0, 93.0)}   # 7 mm in from each corner
HOLE_KEEPOUT = 10.5        # the square at each corner no connector or tall part may enter (a 6 mm standoff on a 7 mm hole)
HOLE_CLEAR_R = 4.0         # ...except the hole's own pad
EDGE_GAP = 1.0             # between neighbouring edge connectors' bodies

# edge connectors are locked at the positions the first board settled (x, y, rotation); the mating
# rule that placed them: a horizontal connector's solder pins sit at the rear, so it mates toward the
# end of its body farthest from the pad rows; a pin header mates where its pins point
CONNECTORS = {"J1": (3.1, 74.0, -90), "J2": (3.1, 30.0, -90), "J3": (136.9, 19.345, 90), "J4": (37.285, 83.865, 0),
              "J5": (19.095, 83.865, 0), "J9": (129.435, 45.045, 0), "J10": (76.08, 20.23, 90), "J11": (87.745, 91.475, 0),
              "J12": (101.805, 91.475, 0), "J13": (131.475, 39.165, 90), "J14": (116.845, 89.475, 0), "J18": (54.445, 89.475, 0),
              "J19": (68.665, 89.475, 0)}
EDGE_ZONE = 3.0            # no part other than an edge connector nearer the edge than this (ECSS 14.3.2 c, tailored)

# the ICs and inboard headers, placed by the flow in the directives (x, y, rotation of the footprint origin):
# power enters at J2 and moves right through the bucks; each block sits behind the connector it serves.
# 2026-10-07: the regulators are cities at the inlet (standard 3.1): the two 5 V bucks stacked in the corner
# beside J2, the 3V3 buck below them at buck 1's output, the RJ45 and PHY moved right along the back edge to
# make the room, the hub down into the band the taller board gained
ANCHORS = {
    "U301": (80.5, 29.0, 270),     # PHY below J10 on the back edge, TX/RX pins up toward the jack (J10 + (4.42, 8.77), the ETH lanes' geometry)
    "U101": (16.0, 41.0, 0),      # PD controller behind J2, CC pins toward it, laid out as the STEVAL-ISC005V1 (UM2398 Figure 24; LAYOUTS)
    "U102": (28.0, 44.0, 0),      # PD bus buffer, right of the PD controller
    "J17": (38.0, 50.0, 0),      # Qwiic programming, top entry, beside the PD controller
    "U103": (24.0, 24.0, 0),       # buck 1 (+5V_PORTS) in the corner at J2, laid out as SLVSF00 Figure 57 (LAYOUTS): input left, diode and inductor right, output capacitors above the inductor
    "U104": (52.0, 24.0, 0),       # buck 2 (+5V_TGT) beside it along the back edge, the same figure
    "U105": (41.0, 41.0, 0),      # +3V3 buck below buck 1's output, above the hub, laid out as SLVSDV6C Figure 52 (LAYOUTS)
    "U402": (39.0, 59.0, 90),     # hub, 5 mm down and left toward the USB ports (2026-10-07) to open the centre: downstream pins toward J4/J5, upstream and crystal toward J1
    "U201": (100.5, 23.0, 270),    # K64: RMII toward the PHY, port/FAULT/UART pins toward the hub and FTDI, GPIO toward J15
    "J16":  (93.5, 5.0, 0),        # SWD to the K64, between the jack and the K64 at the back edge
    "U601": (97.0, 47.0, 0),       # DAPLink K20
    "J601": (104.0, 44.0, 0),      # SWD to the K20
    "U501": (117.0, 56.0, 0),     # FT231X behind J9, 5 mm down (2026-10-07) with its island
    "K801": (91.0, 80.0, 0),       # relays behind J11 / J12
    "K802": (105.0, 80.0, 0),
    "U701": (119.0, 81.0, 0),      # +5V_TGT eFuse behind J14
    "U704": (118.0, 29.0, 0),      # GPIO level shifter near J15
    "U702": (112.0, 38.5, 0),      # console UART shifter near J13 (the three shifters 2 mm apart: the void between cities)
    "U703": (123.0, 38.5, 0),
    # ESD arrays at their receptacles, in line with the pair, and the series parts of the K20 and FTDI pairs
    "U401": (10.3, 74.0, 0),       # J1 upstream array, pins 1/3 toward J1
    "U202": (129.7, 19.34, 180),   # J3 array
    "U408": (40.78, 79.0, -90),    # J4 front row (port 1) -> hub DN4, straight above its pads
    "U409": (45.5, 77.4, -90),     # J4 back row (port 2) -> hub DN5, reached on the bottom around the pin rows
    "U410": (20.0, 79.0, -90),     # J5 front row (port 3) -> hub DN6
    "U411": (25.2, 79.0, -90),     # J5 back row (port 4) -> hub DN7
    "R602": (88.6, 37.75, 180),    # K20 pair series resistors, P above N as the lane arrives from the left
    "R603": (88.6, 39.75, 180),
    "R504": (123.5, 57.6, 0),     # FTDI pair series resistors, N above P as the lane arrives from the right
    "R505": (123.5, 59.5, 0),     # I2C shifter
    "J15":  (117.0, 10.0, 0),      # GPIO header, inboard
    # the two reset buttons in the open centre band (2026-10-07), their debounce parts with them
    "SW201": (66.0, 50.0, 0),      # K64 reset
    "SW601": (80.0, 50.0, 0),      # DAPLink reset (the buttons' courtyards are 10.2 mm wide: 2 mm of void between the two cities)
}
SPARE = (8.0, 60.0)     # parts the engine cannot attach anywhere are parked here and reported
# the regulators' cities (standard 3.1 and 3.2): each with its application circuit around it, the inductor and
# catch diode on the side its SW pin faces, placed before every other satellite; the void between cities below
REGULATORS = {"U103": {"layout": "TPS54560B"}, "U104": {"layout": "TPS54560B"}, "U105": {"layout": "TPS62823"}}
TEMPLATED = {"U101": "STUSB4500"}   # other ICs placed from a figure (standard 3.2): the PD controller from its evaluation board
# the datasheets' layout examples as templates (standard 3.2): for each pin of the IC, the side of the IC (in the
# footprint's own frame, as the library draws it) on which the figure puts the parts hanging from that pin, and
# those parts' kinds in order outward (ring 0 first; "^" lays the part along the side); where the output capacitors
# sit relative to the inductor; whether the figure keeps everything on the top side. Pins are listed in the order
# they are placed: the switching loop first.
LAYOUTS = {
    "TPS54560B": {"source": "TI SLVSF00 section 10.2, Figure 57 PCB Layout Example", "top_only": True,
                  "pins": {"SW": ("R", ["D^", "L"]),           # catch diode along the right side at SW, the inductor beyond it
                           "VIN": ("L", ["C"]),                # input bypass at VIN
                           "BOOT": ("L", ["C"]),               # bootstrap capacitor above the input capacitor
                           "EN": ("L", ["R"]),                 # UVLO divider (none on this board)
                           "RT/CLK": ("B", ["R"]),             # frequency-set resistor below the IC
                           "COMP": ("R", ["R", "C"]),          # compensation network right of COMP
                           "FB": ("R", ["R"], 1)},             # the divider beyond the compensation network
                  "inductor_out": ("T", ["C"])},               # output capacitors above the inductor, toward Vout
    "TPS62823": {"source": "TI SLVSDV6C section 11.2, Figure 52 TPS6282x Board Layout", "top_only": True,
                 "pins": {"SW": ("R", ["L"]),                  # inductor on the power-pin side at SW
                          "VIN": ("R", ["C"]),                 # input capacitor beside it at VIN/PGND
                          "FB": ("L", ["R", "C"])},            # divider and feed-forward on the FB/AGND side
                 "inductor_out": ("T", ["C"])},                # output capacitors at the inductor's output, toward the IC's PG end
    "STUSB4500": {"source": "ST UM2398 section 4, Figure 24 STEVAL-ISC005V1 top composite (the datasheet has no layout figure)", "top_only": True,
                  # U1 sits behind the receptacle with its CC pins toward it; the decoupling in a column above and to the left of the
                  # IC; the VBUS sense and discharge resistors to the right; the I2C pull-ups and address straps in a row below
                  "pins": {"CC1": ("L", ["D"]), "CC2": ("L", ["D"]),
                           "VDD": ("T", ["C"]), "VREG_2V7": ("T", ["C"]), "VREG_1V2": ("T", ["C"]), "VSYS": ("T", ["C"]),
                           "ALERT": ("T", ["R"]),
                           "VBUS_VS_DISCH": ("R", ["R"]), "VBUS_EN_SNK": ("R", ["R", "D"]), "DISCH": ("R", ["R"]),
                           "RESET": ("L", ["R"]), "SCL": ("B", ["R"]), "SDA": ("B", ["R"])}},
}
CITY_GAP = 2.0          # the component void between any two islands' parts, both sides of the board (standard 3.1)
# no plane or pour under the RJ45 on any layer (standard 3.4 and 4: its pins span the body, so the void is the body;
# the pins' tracks pass)
COPPER_VOIDS = {"J10_magnetics": (71.0, 1.0, 90.1, 22.5)}   # the jack's courtyard: origin -5.07..+13.97 in x
RING_GAP = 0.15             # a ring's gap to its host and to the ring inside it (courtyards + this: 0.65 mm pad to pad, the standard's spacing)
RINGS = 8
BIG_AREA = 20.0              # courtyard mm2 from which a part on an IC's pins goes down before the bulk capacitors (inductors, diodes)
SMALL_AREA = 5.0             # courtyard mm2 below which a decoupling capacitor is placed before anything else (0402, 0603)                    # rings tried along a host's side before the nearest free spot is taken
RING_REACH = 8.0             # how far past a host's side a ring may extend, mm
RING_SLIDES = (2.0, 5.0, 12.0, 40.0)   # how far along the side from its pin a part slides before it tries the next ring out
SEARCH_RADIUS = 40.0         # the nearest-free-spot search gives up beyond this, mm (the part is parked)             # courtyard to courtyard between a part and the pin it serves (courtyards carry 0.25 each)
# parts placed by hand across the isolation barrier: (x, y, rotation) of the footprint origin
FIXED = {"K803": (56.0, 73.0, 0),          # coil pads (1, 8) at x = 56 outside the region, contacts (2, 4, 6) inside
         "U801": (66.0, 80.5, 180)}        # below the relay: LED pins (1, 2) at x = 66 inside the region, transistor pins (3, 4) at 58.4 outside
PACK_MARGIN = 0.15          # courtyard to courtyard: with KiCad's 0.25 mm courtyards 0.65 mm pad to pad (reference boards: 0.3-0.6; ECSS Table 14-2: 0.6 between bodies)

# the isolated PSU region: the passthrough block behind J18, a strip along the front and a riser to J19
ISOLATION = [(64, 62), (84, 62), (84, 100), (48, 100), (48, 82), (64, 82)]   # behind J18/J19; x = 64 runs through K803 between coil and contacts
ISOLATION_PLANE_HOLE = [(62, 60), (86, 60), (86, 100), (46, 100), (46, 80), (62, 80)]
# the ground plane on L2 as one outline: the board less a 1 mm edge margin, notched by ISOLATION_PLANE_HOLE from the
# front edge (a zone outline with a hole does not fill in KiCad; the notch is open to the edge, so none is needed)
GND_PLANE = [(1, 1), (139, 1), (139, 99), (86, 99), (86, 60), (62, 60), (62, 80), (46, 80), (46, 99), (1, 99)]
PLANES = [("GND_L2", "GND", "In1.Cu", GND_PLANE),
          # L3 rails as rectangles (FreeRouting cannot take a concave plane): every piece at its own priority (KiCad wants
          # touching zones distinct), the 3V3 base lowest, the rails above it, the L102 tab above VBUS_IN; same-net pieces merge
          ("3V3_L3_a", "+3V3", "In2.Cu", [(3, 3), (137, 3), (137, 40), (3, 40)], 0),
          ("3V3_L3_b", "+3V3", "In2.Cu", [(3, 40), (137, 40), (137, 60), (3, 60)], 1),                          # the band above the region
          ("3V3_L3_c", "+3V3", "In2.Cu", [(3, 60), (62, 60), (62, 80), (3, 80)], 2),                             # left of the region...
          ("3V3_L3_e", "+3V3", "In2.Cu", [(3, 80), (46, 80), (46, 97), (3, 97)], 15),                            # ...and of its riser
          ("3V3_L3_d", "+3V3", "In2.Cu", [(86, 60), (137, 60), (137, 97), (86, 97)], 3),
          ("VBUS_IN_L3", "VBUS_IN", "In2.Cu", [(3, 3), (50, 3), (50, 36), (3, 36)], 4),                        # inlet to the bucks' VIN pins
          ("5V_TGT_L3_band", "+5V_TGT", "In2.Cu", [(44, 36), (129, 36), (129, 40), (44, 40)], 5),              # L102 across the board below the PHY...
          ("5V_TGT_L3_right", "+5V_TGT", "In2.Cu", [(129, 8), (137, 8), (137, 97), (129, 97)], 6),             # ...and the right edge...
          ("5V_TGT_L3_tab", "+5V_TGT", "In2.Cu", [(110, 26), (129, 26), (129, 33), (110, 33)], 7),             # ...a tab to the level shifter...
          ("5V_TGT_L3_efuse", "+5V_TGT", "In2.Cu", [(108, 77), (137, 77), (137, 97), (108, 97)], 8),           # ...to the eFuse and J14
          ("5V_TGT_L3_l102", "+5V_TGT", "In2.Cu", [(56, 10), (70, 10), (70, 36), (56, 36)], 9),                # L102's output down to the band
          ("5V_PORTS_L3_l101", "+5V_PORTS", "In2.Cu", [(28, 10), (42, 10), (42, 36), (28, 36)], 10),            # L101's output down to the 3V3 buck...
          ("5V_PORTS_L3_u105", "+5V_PORTS", "In2.Cu", [(36, 40), (62, 40), (62, 48), (36, 48)], 11),            # ...to the 3V3 buck's input...
          ("5V_PORTS_L3_mid", "+5V_PORTS", "In2.Cu", [(50, 48), (62, 48), (62, 80), (50, 80)], 12),             # ...down beside the relay...
          ("5V_PORTS_L3_band", "+5V_PORTS", "In2.Cu", [(10, 70), (50, 70), (50, 82), (10, 82)], 13),            # ...along the port switches
          ("5V_PORTS_L3_right", "+5V_PORTS", "In2.Cu", [(86, 52), (126, 52), (126, 57), (86, 57)], 14),        # ...to the FTDI switch...
          ("5V_PORTS_L3_relays", "+5V_PORTS", "In2.Cu", [(86, 57), (108, 57), (108, 82), (86, 82)], 16)]       # ...and down to the relays
ISO_GAP = 2.0
# ---- lanes (ecad-standards/layout.md sections 1 and 5): a corridor reserved for one routed path, from pad to pad
# through axis-aligned legs ("x"/"y" items move along one axis to a coordinate or to another pad's coordinate),
# as wide as the net class's track plus its clearance plus LANE_MARGIN each side, kept free of parts on both
# sides of the board, and laid as tracks by the generator
LANES = {
    "PSU_VP":   {"net": "PSU_VP",   "layer": "F.Cu", "path": [("J18", "1"), ("y", 85.0), ("x", ("K803", "6")), ("K803", "6")]},
    "PSU_VOUT": {"net": "PSU_VOUT", "layer": "F.Cu", "path": [("K803", "4"), ("y", 93.0), ("x", ("J19", "1")), ("J19", "1")]},   # under J19's body, past its GND pin
    # USB 2.0 pairs: receptacle -> ESD array (direct), array -> hub / transceiver along legs; one layer change where a
    # pair must cross another (the upstream pair under the left stack's pairs)
    "J1_D":    {"pair": "J1_D",    "path": [("J1", {"P": ["A6", "B6"], "N": ["A7", "B7"]}), ("U401", {"P": "3", "N": "1"})]},
    "HUB_UP":  {"pair": "HUB_UP",  "path": [("U401", {"P": "4", "N": "6"}), ("x", 15.0), ("layer", "B.Cu"), ("y", ("U402", {"P": "59", "N": "58"}, (0.0, 0.1))),
                                            ("x", 31.5), ("layer", "F.Cu"), ("U402", {"P": "59", "N": "58"}, (0.0, 0.1))]},
    "PORT1_D": {"pair": "PORT1_D", "path": [("J4", {"P": "3", "N": "2"}), ("U408", {"P": "6", "N": "4"})]},
    "HUB_DN4": {"pair": "HUB_DN4", "path": [("U408", {"P": "1", "N": "3"}), ("y", 69.0), ("x", ("U402", {"P": "9", "N": "8"})), ("U402", {"P": "9", "N": "8"})]},
    "HUB_DN5": {"pair": "HUB_DN5", "path": [("U409", {"P": "1", "N": "3"}), ("y", 67.5), ("x", ("U402", {"P": "12", "N": "11"})), ("U402", {"P": "12", "N": "11"})]},
    "PORT3_D": {"pair": "PORT3_D", "path": [("J5", {"P": "3", "N": "2"}), ("U410", {"P": "6", "N": "4"})]},
    # the left row's two port pairs are a pin pitch apart: their centre lines spread 0.2 mm so the members keep clearance
    "HUB_DN6": {"pair": "HUB_DN6", "path": [("U410", {"P": "1", "N": "3"}), ("y", ("U402", {"P": "54", "N": "53"}, (0.0, -0.05))), ("U402", {"P": "54", "N": "53"}, (0.0, -0.05))]},
    "HUB_DN7": {"pair": "HUB_DN7", "path": [("U411", {"P": "1", "N": "3"}), ("y", ("U402", {"P": "56", "N": "55"}, (0.0, 0.15))), ("U402", {"P": "56", "N": "55"}, (0.0, 0.15))]},
    # the two downstream pairs for the K20 and the FTDI leave the hub's bottom row side by side (0.5 mm pins): their centre
    # lines are shifted 0.1 mm apart, the FTDI pair turns first, and each goes under the port pairs on the bottom
    "HUB_DN1": {"pair": "HUB_DN1", "path": [("U402", {"P": "2", "N": "1"}, (-0.1, 0.0)), ("y", 66.6), ("layer", "B.Cu"), ("y", 68.2), ("x", 50.5), ("y", 66.6), ("layer", "F.Cu"),
                                            ("y", ("pads", {"P": ("R602", "2"), "N": ("R603", "2")})), ("pads", {"P": ("R602", "2"), "N": ("R603", "2")})]},
    "K20_USB": {"pair": "K20_USB", "path": [("pads", {"P": ("R602", "1"), "N": ("R603", "1")}), ("x", 92.0), ("y", ("U601", {"P": "3", "N": "4"})), ("U601", {"P": "3", "N": "4"})]},
    "HUB_DN2": {"pair": "HUB_DN2", "path": [("U402", {"P": "4", "N": "3"}, (0.1, 0.0)), ("y", 65.6), ("x", 37.8), ("layer", "B.Cu"), ("x", 52.1), ("layer", "F.Cu"), ("y", 41.5),
                                            ("x", 86.5), ("y", 51.5), ("x", 112.0), ("y", 62.0), ("x", 126.5),   # over the relay, under the DAPLink and SWD, round the FTDI
                                            ("y", ("pads", {"P": ("R505", "2"), "N": ("R504", "2")})), ("pads", {"P": ("R505", "2"), "N": ("R504", "2")})]},
    "FTDI_USB": {"pair": "FTDI_USB", "path": [("pads", {"P": ("R505", "1"), "N": ("R504", "1")}), ("x", 121.2), ("y", ("U501", {"P": "11", "N": "12"})), ("U501", {"P": "11", "N": "12"})]},
    "J3_D":    {"pair": "J3_D",    "path": [("J3", {"P": ["A6", "B6"], "N": ["A7", "B7"]}), ("U202", {"P": "1", "N": "3"})]},
    "K64_USB": {"pair": "K64_USB", "path": [("U202", {"P": "6", "N": "4"}), ("x", 124.0), ("y", 6.0), ("x", ("U201", {"P": "10", "N": "11"})), ("U201", {"P": "10", "N": "11"})]},
    # Ethernet MDI pairs, jack to PHY (class ETH, 100 ohm)
    "ETH_TD":  {"pair": "ETH_TD",  "path": [("J10", {"P": "1", "N": "2"}), ("y", 24.0), ("x", ("U301", {"P": "6", "N": "5"}, (-0.05, 0.0))), ("U301", {"P": "6", "N": "5"}, (-0.05, 0.0))]},
    "ETH_RD":  {"pair": "ETH_RD",  "path": [("J10", {"P": "3", "N": "6"}), ("U301", {"P": "4", "N": "3"}, (0.05, 0.0))]},
    # the stacks' back rows on the bottom, through the front row's pin gaps, up to the array's connector-side pads
    "PORT2_D_N": {"net": "PORT2_D_N", "layer": "B.Cu", "width": 0.2, "path": [("J4", "6"), ("y", 84.92), ("x", 43.03), ("y", 81.7), ("layer", "F.Cu"), ("U409", "4")]},
    "PORT2_D_P": {"net": "PORT2_D_P", "layer": "B.Cu", "width": 0.2, "path": [("J4", "7"), ("y", 85.43), ("x", 45.44), ("y", 81.7), ("layer", "F.Cu"), ("U409", "6")]},
    "PORT4_D_N": {"net": "PORT4_D_N", "layer": "B.Cu", "width": 0.2, "path": [("J5", "6"), ("y", 84.92), ("x", 24.84), ("y", 81.7), ("layer", "F.Cu"), ("U411", "4")]},
    "PORT4_D_P": {"net": "PORT4_D_P", "layer": "B.Cu", "width": 0.2, "path": [("J5", "7"), ("y", 85.43), ("x", 27.25), ("y", 81.7), ("layer", "F.Cu"), ("U411", "6")]},
}
LANE_MARGIN = 0.25
# ---- sides (ecad-standards/layout.md section 3.7): connectors, ICs, relays, inductors, crystals, switches, jumpers,
# LEDs, large parts and the parts on current-carrying, pair and switching-loop nets stay on top; a small part of
# these kinds, up to the courtyard area given, may go to the bottom, under the pin it serves
BOTTOM_MAX_AREA = {"R": 7.0, "C": 7.0, "D": 8.0, "Q": 12.0}   # mm2: up to 1206, SOD-123, SOT-23
BOTTOM_NEVER_CLASSES = {"USB_VBUS_3A", "PWR_6A", "PSU_3A", "USB"}   # parts on these nets stay on top (current paths, pairs); PSU_ISO parts may go under
# ---- ESD protection (ecad-standards/layout.md section 3.8): recognised by value; placed first of all, on top, at the
# connector's signal pins, a flow-through array turned so its connector-side pins face the connector
ESD_VALUES = ("USBLC", "PESD", "ESDA", "TPD", "SRV05", "IP42", "TVS", "SMAJ", "SMBJ")
# one channel of each stacked USB-A receptacle on each side (standard 3.7): the back rows' load switches and their
# capacitors go to the bottom under the front rows' switches; the indicator LEDs stay on top
SIDES = {"U404": "B", "U406": "B"}
BOTTOM_TUCK = 1.75    # a bottom part's inner edge sits this far inside its host's courtyard edge, under the pin row (reference boards: 1.8)
THT_MARGIN = 0.5      # bottom parts keep this far from through-hole pads (reference boards: 0.5; wave or selective soldering needs the assembler's figure)
EP_MARGIN = 0.6       # and from an exposed pad's via field
REFDES_SIZES = (0.8, 0.7)   # designator text heights tried, mm (reference boards: 0.8 typical, 0.65-0.72 smallest); stroke 15 %, never under 0.1
CURRENT_CLASSES = {"USB_VBUS_3A", "PWR_6A", "PSU_3A", "PSU_ISO"}   # a part on these nets belongs at the connector or IC that carries them
PAIR_CLASSES = {"USB"}
ISOLATION_RECTS = [(64, 62, 84, 100), (48, 82, 64, 100)]           # ISOLATION as rectangles, for the placer
ISOLATION_GROWN_RECTS = [(62, 60, 86, 100), (46, 80, 62, 100)]     # ISOLATION_PLANE_HOLE likewise: board-net parts stay out              # creepage between PSU_3A nets and board nets

STACKUP = [  # Advanced Circuits standard 4-layer 0.062"
    ("F.Cu", "copper", 0.035), ("dielectric 1", "prepreg", 0.3048, 4.6), ("In1.Cu", "copper", 0.035),
    ("dielectric 2", "core", 0.7112, 4.7), ("In2.Cu", "copper", 0.035), ("dielectric 3", "prepreg", 0.3048, 4.6), ("B.Cu", "copper", 0.035)]
# the isolated regions the engine enforces (placement, rule areas, .kicad_dru rules, the region's own island)
ISOLATION_REGIONS = [{"name": "psu_iso", "note": "PSU passthrough isolation", "outline": ISOLATION, "rects": ISOLATION_RECTS,
                      "grown": ISOLATION_GROWN_RECTS, "nets": r"(^|/)PSU_(VP|VOUT|GND|SENSE)", "classes": ("PSU_3A", "PSU_ISO"),
                      "gap": ISO_GAP, "island": ("PSU_GND_L2", "PSU_GND", "In1.Cu", ISOLATION)}]
# the bulk router for gen/pcb.py --route (ecad-standards/tools/autoroute.py): FreeRouting 2.4.1, one thread
FREEROUTING = "/home/flippy/Documents/claude/mythtv-porg/tools/freerouting/bin/freerouting"
FREEROUTING_PASSES = 30
# ---- the copper after routing (ecad-standards/tools/copper.py, layout.md 4 and 5): ground floods on both outer layers,
# notched around the isolation region like the plane, the region's own ground inside it, and ground stitching at
# about four vias per square centimetre, clear of the region by the creepage
FLOODS = [("GND_F", "GND", "F.Cu", GND_PLANE), ("GND_B", "GND", "B.Cu", GND_PLANE),
          ("PSU_GND_F", "PSU_GND", "F.Cu", ISOLATION), ("PSU_GND_B", "PSU_GND", "B.Cu", ISOLATION)]
STITCH = [{"net": "GND", "pitch": 5.0, "margin": 1.5, "keep_out": ISOLATION_GROWN_RECTS},      # clear of the region by the creepage
          {"net": "PSU_GND", "pitch": 5.0, "inside": [(66.3, 64.3, 81.7, 98.5), (50.3, 84.3, 66.3, 98.5)]}]  # the region's own ground, inset by the creepage
STITCH_VIA = (0.6, 0.3)
