"""The layout directives as data: docs/layout-directives.md, in millimetres.

Board origin top-left, X right, Y down (as KiCad draws it). Everything here
is placement intent; pcb.py turns it into the first board file.
"""
BOARD = (140.0, 80.0)
RADIUS = 2.0
HOLES = {"H1": (7.0, 7.0), "H2": (133.0, 7.0), "H3": (7.0, 73.0), "H4": (133.0, 73.0)}   # 7 mm in from each corner
HOLE_KEEPOUT = 10.5        # the square at each corner no connector or tall part may enter (a 6 mm standoff on a 7 mm hole)
HOLE_CLEAR_R = 4.0         # ...except the hole's own pad
EDGE_GAP = 1.0             # between neighbouring edge connectors' bodies

# edge connectors are locked at the positions the first board settled (x, y, rotation); the mating
# rule that placed them: a horizontal connector's solder pins sit at the rear, so it mates toward the
# end of its body farthest from the pad rows; a pin header mates where its pins point
CONNECTORS = {"J1": (3.1, 39.345, -90), "J2": (3.1, 51.035, -90), "J3": (136.9, 19.345, 90), "J4": (19.095, 63.865, 0),
              "J5": (37.285, 63.865, 0), "J9": (129.435, 45.045, 0), "J10": (20.215, 27.945, 180), "J11": (87.745, 71.475, 0),
              "J12": (101.805, 71.475, 0), "J13": (131.475, 39.165, 90), "J14": (116.845, 69.475, 0), "J18": (54.445, 69.475, 0),
              "J19": (68.665, 69.475, 0)}
EDGE_ZONE = 3.0            # no part other than an edge connector nearer the edge than this (ECSS 14.3.2 c, tailored)

# the ICs and inboard headers, placed by the flow in the directives (x, y, rotation of the footprint origin):
# power enters at J2 and moves right through the bucks; each block sits behind the connector it serves
ANCHORS = {
    "U301": (30.0, 24.0, 0),       # PHY behind J10, TX/RX pins toward the jack
    "U101": (24.0, 52.0, 0),       # PD controller at J2
    "U102": (31.0, 46.0, 0),       # PD bus buffer
    "J17":  (26.0, 37.5, 0),       # Qwiic programming, top entry, beside the PD controller
    "U103": (56.0, 11.0, 0),       # buck 1 (+5V_PORTS): SW on its right, the loop flows right
    "U104": (56.0, 27.0, 0),       # buck 2 (+5V_TGT)
    "U105": (70.0, 33.0, 0),       # +3V3 buck
    "U402": (44.0, 40.0, 90),      # hub: downstream pins toward J4/J5, upstream and crystal toward J1
    "U201": (96.0, 22.0, 270),     # K64: RMII toward the PHY, port/FAULT/UART pins toward the hub and FTDI, GPIO toward J15
    "J16":  (83.0, 10.0, 0),       # SWD to the K64
    "U601": (95.0, 47.0, 0),       # DAPLink K20
    "J601": (88.5, 46.0, 0),      # SWD to the K20
    "U501": (117.0, 51.0, 0),      # FT231X behind J9
    "K801": (91.0, 60.0, 0),       # relays behind J11 / J12
    "K802": (105.0, 60.0, 0),
    "U701": (119.0, 61.0, 0),      # +5V_TGT eFuse behind J14
    "U704": (118.0, 30.0, 0),      # GPIO level shifter near J15
    "U702": (112.0, 37.0, 0),      # console UART shifter near J13
    "U703": (123.0, 37.0, 0),      # I2C shifter
    "J15":  (117.0, 10.0, 0),      # GPIO header, inboard
}
SPARE = (72.0, 6.0)     # parts the engine cannot attach anywhere are parked here and reported
RING_GAP = 0.3
RINGS = 8
BIG_AREA = 20.0              # courtyard mm2 from which a part on an IC's pins goes down before the bulk capacitors (inductors, diodes)
SMALL_AREA = 5.0             # courtyard mm2 below which a decoupling capacitor is placed before anything else (0402, 0603)                    # rings tried along a host's side before the nearest free spot is taken
RING_REACH = 8.0             # how far past a host's side a ring may extend, mm
RING_SLIDES = (2.0, 5.0, 12.0, 40.0)   # how far along the side from its pin a part slides before it tries the next ring out
SEARCH_RADIUS = 40.0         # the nearest-free-spot search gives up beyond this, mm (the part is parked)             # courtyard to courtyard between a part and the pin it serves (courtyards carry 0.25 each)
# parts placed by hand across the isolation barrier: (x, y, rotation) of the footprint origin
FIXED = {"K803": (56.0, 53.0, 0),          # coil pads (1, 8) at x = 56 outside the region, contacts (2, 4, 6) inside
         "U801": (66.0, 60.5, 180)}        # below the relay: LED pins (1, 2) at x = 66 inside the region, transistor pins (3, 4) at 58.4 outside
PACK_MARGIN = 0.25          # courtyard to courtyard: with KiCad's 0.25 mm courtyards that is ECSS Table 14-2's 0.6 mm between bodies

# the isolated PSU region: the passthrough block behind J18, a strip along the front and a riser to J19
ISOLATION = [(64, 42), (84, 42), (84, 80), (48, 80), (48, 62), (64, 62)]   # behind J18/J19; x = 64 runs through K803 between coil and contacts
ISOLATION_PLANE_HOLE = [(62, 40), (86, 40), (86, 80), (46, 80), (46, 60), (62, 60)]   # the same, grown by ISO_GAP: the ground plane stops here
ISO_GAP = 2.0
CURRENT_CLASSES = {"USB_VBUS_3A", "PWR_6A", "PSU_3A", "PSU_ISO"}   # a part on these nets belongs at the connector or IC that carries them
PAIR_CLASSES = {"USB"}
ISOLATION_RECTS = [(64, 42, 84, 80), (48, 62, 64, 80)]           # ISOLATION as rectangles, for the placer
ISOLATION_GROWN_RECTS = [(62, 40, 86, 80), (46, 60, 62, 80)]     # ISOLATION_PLANE_HOLE likewise: board-net parts stay out              # creepage between PSU_3A nets and board nets

STACKUP = [  # Advanced Circuits standard 4-layer 0.062"
    ("F.Cu", "copper", 0.035), ("dielectric 1", "prepreg", 0.3048, 4.6), ("In1.Cu", "copper", 0.035),
    ("dielectric 2", "core", 0.7112, 4.7), ("In2.Cu", "copper", 0.035), ("dielectric 3", "prepreg", 0.3048, 4.6), ("B.Cu", "copper", 0.035)]
