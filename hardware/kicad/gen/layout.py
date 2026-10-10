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
CONNECTORS = {"J1": (3.1, 74.0, -90), "J2": (13.9, 30.0, 0), "J3": (136.9, 19.345, 90), "J4": (37.285, 83.865, 0),
              "J5": (19.095, 83.865, 0), "J9": (129.435, 65.045, 0), "J10": (60.08, 20.23, 90), "J11": (87.745, 91.475, 0),
              "J12": (101.805, 91.475, 0), "J13": (131.475, 49.165, 90), "J14": (116.845, 89.475, 0), "J18": (56.445, 89.475, 0),
              "J19": (70.665, 89.475, 0)}   # J18/J19 2 mm right (2026-10-08): J4's shield pads 2.6 mm from the passthrough region (their copper still enters its 2 mm band by 0.9 mm; the fills keep the creepage)
EDGE_ZONE = 3.0            # no part other than an edge connector nearer the edge than this (ECSS 14.3.2 c, tailored)

# the ICs and inboard headers, placed by the flow in the directives (x, y, rotation of the footprint origin):
# power enters at J2 and moves right through the bucks; each block sits behind the connector it serves.
# 2026-10-07: the regulators are cities at the inlet (standard 3.1): the two 5 V bucks stacked in the corner
# beside J2, the 3V3 buck below them at buck 1's output, the RJ45 and PHY moved right along the back edge to
# make the room, the hub down into the band the taller board gained
ANCHORS = {
    "U301": (64.5, 29.0, 270),     # PHY below J10 on the back edge, TX/RX pins up toward the jack (J10 + (4.42, 8.77), the ETH lanes' geometry); 16 mm left with the jack on 2026-10-10 into the corner the bucks left, opening the K64's side
    "Q101": (20.0, 30.0, 0),       # the inlet's reverse-polarity FET behind the jack (2026-10-10: the PD controller, its I2C buffer and header and the two 5 V bucks went with the PD inlet)
    "U105": (41.0, 41.0, 0),      # +3V3 buck below buck 1's output, above the hub, laid out as SLVSDV6C Figure 52 (LAYOUTS)
    "U402": (39.0, 59.0, 90),     # hub, 5 mm down and left toward the USB ports (2026-10-07) to open the centre: downstream pins toward J4/J5, upstream and crystal toward J1
    "U201": (100.5, 23.0, 270),    # K64: RMII toward the PHY, port/FAULT/UART pins toward the hub and FTDI, GPIO toward J15
    "J16":  (93.5, 5.0, 0),        # SWD to the K64, between the jack and the K64 at the back edge
    "U601": (97.0, 47.0, 0),       # DAPLink K20
    "J601": (104.0, 44.0, 0),      # SWD to the K20
    "U501": (117.0, 70.0, 0),     # FT231X behind J9, which moved 20 mm down the edge (2026-10-07); its island follows
    "K801": (93.0, 80.0, 0),      # relays behind J11 / J12, 2 mm right with the passthrough region (2026-10-08)
    "K802": (106.5, 80.5, 0),   # 2 mm of void to the FTDI island above it
    "U704": (119.0, 81.0, 0),      # +5V_TGT eFuse (TPS26630) behind J14 (anchored under U701's designator until 2026-10-08: the three target-I/O ICs were swapped)
    "U702": (118.0, 29.0, 0),      # GPIO level shifter (TXB0108) near J15
    "U701": (112.0, 46.5, 0),     # console UART shifter (TXB0104) near J13 (J13 10 mm down the edge on 2026-10-07; the shifters follow, clear of the HUB_DN2 leg at x 112)
    "U703": (123.0, 46.5, 0),     # 
    # ESD arrays at their receptacles, in line with the pair, and the series parts of the K20 and FTDI pairs
    "U401": (10.3, 74.0, 0),       # J1 upstream array, pins 1/3 toward J1
    "U202": (129.7, 19.34, 180),   # J3 array
    "U408": (40.78, 79.0, -90),    # J4 front row (port 1) -> hub DN4, straight above its pads
    "U409": (45.5, 77.4, -90),     # J4 back row (port 2) -> hub DN5, reached on the bottom around the pin rows
    "U410": (20.0, 79.0, -90),     # J5 front row (port 3) -> hub DN6
    "U411": (25.2, 79.0, -90),     # J5 back row (port 4) -> hub DN7
    "R602": (88.6, 37.75, 180),    # K20 pair series resistors, P above N as the lane arrives from the left
    "R603": (88.6, 39.75, 180),
    "R504": (123.5, 71.6, 0),     # FTDI pair series resistors, N above P as the lane arrives from the right
    "R505": (123.5, 73.5, 0),     # 
    "J15":  (117.0, 10.0, 0),      # GPIO header, inboard
    # the two reset buttons in the open centre band (2026-10-07), their debounce parts with them
    "SW201": (66.0, 50.0, 0),      # K64 reset
    "SW601": (80.0, 50.0, 0),      # DAPLink reset (the buttons' courtyards are 10.2 mm wide: 2 mm of void between the two cities)
}
SPARE = (8.0, 60.0)     # parts the engine cannot attach anywhere are parked here and reported
# the regulators' cities (standard 3.1 and 3.2): each with its application circuit around it, the inductor and
# catch diode on the side its SW pin faces, placed before every other satellite; the void between cities below
REGULATORS = {"U105": {"layout": "TPS62823"}}
TEMPLATED = {}   # other ICs placed from a figure (standard 3.2); none since the PD controller went
# the datasheets' layout examples as templates (standard 3.2): for each pin of the IC, the side of the IC (in the
# footprint's own frame, as the library draws it) on which the figure puts the parts hanging from that pin, and
# those parts' kinds in order outward (ring 0 first; "^" lays the part along the side); where the output capacitors
# sit relative to the inductor; whether the figure keeps everything on the top side. Pins are listed in the order
# they are placed: the switching loop first.
LAYOUTS = {
    "TPS62823": {"source": "TI SLVSDV6C section 11.2, Figure 52 TPS6282x Board Layout", "top_only": True,
                 "pins": {"SW": ("R", ["L"]),                  # inductor on the power-pin side at SW
                          "VIN": ("R", ["C"]),                 # input capacitor beside it at VIN/PGND
                          "FB": ("L", ["R", "C"])},            # divider and feed-forward on the FB/AGND side
                 "inductor_out": ("T", ["C"])},                # output capacitors at the inductor's output, toward the IC's PG end
}
RAIL_VIAS = {"PWR_4A": 3, "USB_VBUS_3A": 2, "PSU_3A": 2}   # vias beside each SMD pad on a plane net, by class (standard 4); one otherwise
CITY_GAP = 2.0          # the component void between any two islands' parts, both sides of the board (standard 3.1)
# no plane or pour under the RJ45 on any layer (standard 3.4 and 4: its pins span the body, so the void is the body;
# the pins' tracks pass)
COPPER_VOIDS = {"J10_magnetics": (55.0, 1.0, 74.1, 22.5)}   # the jack's courtyard: origin -5.07..+13.97 in x (x 71 to 90 until 2026-10-10)
RING_GAP = 0.15             # a ring's gap to its host and to the ring inside it (courtyards + this: 0.65 mm pad to pad, the standard's spacing)
RINGS = 8
BIG_AREA = 20.0              # courtyard mm2 from which a part on an IC's pins goes down before the bulk capacitors (inductors, diodes)
SMALL_AREA = 5.0             # courtyard mm2 below which a decoupling capacitor is placed before anything else (0402, 0603)                    # rings tried along a host's side before the nearest free spot is taken
RING_REACH = 8.0             # how far past a host's side a ring may extend, mm
RING_SLIDES = (2.0, 5.0, 12.0, 40.0)   # how far along the side from its pin a part slides before it tries the next ring out
SEARCH_RADIUS = 40.0         # the nearest-free-spot search gives up beyond this, mm (the part is parked)             # courtyard to courtyard between a part and the pin it serves (courtyards carry 0.25 each)
# parts placed by hand across the isolation barrier: (x, y, rotation) of the footprint origin
FIXED = {"K803": (58.0, 73.0, 0),          # coil pads (1, 8) at x = 58 outside the region, contacts (2, 4, 6) inside
         "U801": (68.0, 80.5, 180)}        # below the relay: LED pins (1, 2) at x = 68 inside the region, transistor pins (3, 4) at 60.4 outside
PACK_MARGIN = 0.15          # courtyard to courtyard: with KiCad's 0.25 mm courtyards 0.65 mm pad to pad (reference boards: 0.3-0.6; ECSS Table 14-2: 0.6 between bodies)

# the isolated PSU region: the passthrough block behind J18, a strip along the front and a riser to J19
ISOLATION = [(66, 62), (86, 62), (86, 100), (50, 100), (50, 82), (66, 82)]   # behind J18/J19; x = 66 runs through K803 between coil and contacts
ISOLATION_PLANE_HOLE = [(64, 60), (88, 60), (88, 100), (48, 100), (48, 80), (64, 80)]
# the ground plane on L2 as one outline: the board less a 1 mm edge margin, notched by ISOLATION_PLANE_HOLE from the
# front edge (a zone outline with a hole does not fill in KiCad; the notch is open to the edge, so none is needed)
GND_PLANE = [(1, 1), (139, 1), (139, 99), (88, 99), (88, 60), (64, 60), (64, 80), (48, 80), (48, 99), (1, 99)]
# layer roles on the six-layer board (2026-10-09; four layers until then): L1 and L6 route and carry the ground floods, L2 and
# L5 (In1.Cu, In4.Cu) are the unbroken ground planes each outer layer and its pairs reference, L3 (In2.Cu) routes, L4 (In3.Cu)
# carries the heavy rails as rectangles, referenced to L5 across the core. The router routes on L1, L3 and L6; the plane
# layers are typed power for it (gen/pcb.py passes the layers of PLANES)
PLANES = [("GND_L2", "GND", "In1.Cu", GND_PLANE),
          ("GND_L5", "GND", "In4.Cu", GND_PLANE),
          # the L4 rail as rectangles (FreeRouting cannot take a concave plane): every piece at its own priority (KiCad wants
          # touching zones distinct); same-net pieces touch or overlap and merge, and the engine's rails gate holds the rail
          # to one piece. One rail since 2026-10-10: +5V from the barrel jack (4 A, PWR_4A), the two 6 A bucks and the 3 A PD
          # inlet gone with the PD controller. +3V3 stays routed (PWR_1A, 0.6 mm): a +3V3 plane would take a signal layer
          ("5V_L4_in", "+5V", "In3.Cu", [(3, 22), (42, 22), (42, 40), (3, 40)], 4),                            # the jack's centre pin, the FET and the bulk capacitors...
          ("5V_L4_u105", "+5V", "In3.Cu", [(36, 40), (62, 40), (62, 48), (36, 48)], 11),                        # ...to the 3V3 buck's input...
          ("5V_L4_mid", "+5V", "In3.Cu", [(48, 48), (64, 48), (64, 80), (48, 80)], 12),                         # ...down beside the relay...
          ("5V_L4_band", "+5V", "In3.Cu", [(10, 70), (48, 70), (48, 83), (10, 83)], 13),                        # ...along the port switches (their pads at y 78.5 to 80.5)
          ("5V_L4_bridge", "+5V", "In3.Cu", [(62, 45), (100, 45), (100, 57), (62, 57)], 15),                    # ...across above the region to the DAPLink's VBUS...
          ("5V_L4_right", "+5V", "In3.Cu", [(86, 52), (126, 52), (126, 57), (86, 57)], 14),                    # ...to the FTDI switch...
          ("5V_L4_relays", "+5V", "In3.Cu", [(88, 57), (108, 57), (108, 82), (88, 82)], 16),                   # ...down to the relays...
          ("5V_L4_ftdi", "+5V", "In3.Cu", [(108, 57), (126, 57), (126, 77), (108, 77)], 17),                   # ...to the FTDI switch behind J9 (K802's coil pin at y 76.7)...
          ("5V_L4_efuse", "+5V", "In3.Cu", [(108, 77), (137, 77), (137, 97), (108, 97)], 8)]                    # ...and to the eFuse's input behind J14; +5V_TGT leaves it to J14 as a track
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
BOTTOM_NEVER_CLASSES = {"USB_VBUS_3A", "PWR_4A", "PSU_3A", "USB"}   # parts on these nets stay on top (current paths, pairs); PSU_ISO parts may go under
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
CURRENT_CLASSES = {"USB_VBUS_3A", "PWR_4A", "PSU_3A", "PSU_ISO"}   # a part on these nets belongs at the connector or IC that carries them
PAIR_CLASSES = {"USB"}
ISOLATION_RECTS = [(66, 62, 86, 100), (50, 82, 66, 100)]           # ISOLATION as rectangles, for the placer
ISOLATION_GROWN_RECTS = [(64, 60, 88, 100), (48, 80, 64, 100)]     # ISOLATION_PLANE_HOLE likewise: board-net parts stay out              # creepage between PSU_3A nets and board nets

STACKUP = [  # Advanced Circuits standard 6-layer 0.062" (their drawing, 2026-10-09): 1 oz on all six layers, two 2116 sheets
    # between L1-L2, L3-L4 and L5-L6 (pressed 5.1 + 4.7 mil = 0.249 mm by their prepreg guide, er 4.3), a 0.014" core (er 4.6)
    # between L2-L3 and L4-L5; 0.066" with the copper (1.67 mm), inside their +/- 10 %. Their standard stackups are not guaranteed unless
    # the order says so: order it Custom / Controlled Dielectric with controlled impedance on the USB and ETH classes
    ("F.Cu", "copper", 0.035), ("dielectric 1", "prepreg", 0.249, 4.3), ("In1.Cu", "copper", 0.035),
    ("dielectric 2", "core", 0.356, 4.6), ("In2.Cu", "copper", 0.035), ("dielectric 3", "prepreg", 0.249, 4.3),
    ("In3.Cu", "copper", 0.035), ("dielectric 4", "core", 0.356, 4.6), ("In4.Cu", "copper", 0.035),
    ("dielectric 5", "prepreg", 0.249, 4.3), ("B.Cu", "copper", 0.035)]
# the isolated regions the engine enforces (placement, rule areas, .kicad_dru rules, the region's own island)
ISOLATION_REGIONS = [{"name": "psu_iso", "note": "PSU passthrough isolation", "outline": ISOLATION, "rects": ISOLATION_RECTS,
                      "grown": ISOLATION_GROWN_RECTS, "nets": r"(^|/)PSU_(VP|VOUT|GND|SENSE)", "classes": ("PSU_3A", "PSU_ISO"),
                      "gap": ISO_GAP, "islands": [("PSU_GND_L2", "PSU_GND", "In1.Cu", ISOLATION), ("PSU_GND_L4", "PSU_GND", "In3.Cu", ISOLATION),
                                  ("PSU_GND_L5", "PSU_GND", "In4.Cu", ISOLATION)]}]   # the region's own ground on every plane layer
# the bulk router for gen/pcb.py --route (ecad-standards/tools/autoroute.py): FreeRouting 2.4.1, one thread
FREEROUTING = "/home/flippy/Documents/claude/mythtv-porg/tools/freerouting/bin/freerouting"
FREEROUTING_PASSES = 24   # the plateau came before 20 on four layers; the session is written only at the end
FREEROUTING_TIMEOUT = 28800   # seconds: with three signal layers a pass takes twice as long (pass 17 at 3.5 h on 2026-10-09; the 4 h default cut the run)
FREEROUTING_PORTFOLIO = 6     # instances side by side with different costs, the fewest unrouted taken: the router's passes are single-threaded and this machine has 64 cores
# ---- the copper after routing (ecad-standards/tools/copper.py, layout.md 4 and 5): ground floods on both outer layers,
# notched around the isolation region like the plane, the region's own ground inside it, and ground stitching at
# about four vias per square centimetre, clear of the region by the creepage
FLOODS = [("GND_F", "GND", "F.Cu", GND_PLANE), ("GND_B", "GND", "B.Cu", GND_PLANE),
          ("PSU_GND_F", "PSU_GND", "F.Cu", ISOLATION), ("PSU_GND_B", "PSU_GND", "B.Cu", ISOLATION)]
STITCH = [{"net": "GND", "pitch": 5.0, "margin": 1.5, "keep_out": ISOLATION_GROWN_RECTS},      # clear of the region by the creepage
          {"net": "PSU_GND", "pitch": 5.0, "inside": [(68.3, 64.3, 83.7, 98.5), (52.3, 84.3, 68.3, 98.5)]}]  # the region's own ground, inset by the creepage
STITCH_VIA = (0.6, 0.3)
