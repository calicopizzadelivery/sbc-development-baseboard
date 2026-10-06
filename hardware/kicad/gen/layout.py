"""The layout directives as data: docs/layout-directives.md, in millimetres.

Board origin top-left, X right, Y down (as KiCad draws it). Everything here
is placement intent; pcb.py turns it into the first board file.
"""
BOARD = (140.0, 80.0)
RADIUS = 2.0
HOLES = {"H1": (10.0, 10.0), "H2": (130.0, 10.0), "H3": (10.0, 70.0), "H4": (130.0, 70.0)}
HOLE_KEEPOUT = 13.0        # the square at each corner no connector or tall part may enter
HOLE_CLEAR_R = 4.0         # ...except the hole's own pad
EDGE_GAP = 1.0             # between neighbouring edge connectors' bodies

# which way a connector footprint mates at rotation 0, in board coordinates, by footprint name.
# USB-C: the GCT footprint marks the board edge with a "PCB Edge" text on the mating side. USB-A:
# the pins are at the rear of the shell, the opening at the far end. RJ45: the Kycon's contacts sit
# near the front, the magnetics behind. Phoenix headers: pins behind the plug face. Verify the
# terminal blocks in the 3D view before ordering.
MATES = [("USB_C_Receptacle", (0, 1)), ("USB_A_", (0, 1)), ("RJ45", (0, -1)), ("PhoenixContact", (0, -1)), ("PinHeader", (1, 0))]
EDGE_START = HOLE_KEEPOUT + 1.0     # first connector body after the corner square (courtyards reach a little further)

# edge connectors in order from the back corner (left/right edges: top to bottom; front edge: left end
# rightward and right end leftward). "L" x=0, "R" x=140, "F" y=80.
EDGES = {
    "L": ["J10", "J1", "J2"],                   # J17 is top-entry and inboard: the edge is full at the measured widths
    "R": ["J3", "J13", "J9"],                   # J9 (right-angle FTDI header) faces the target from the right edge
    "F_left": ["J4", "J5", "J18", "J19"],       # PSU in and out side by side: one compact isolated region, no strip across the board
    "F_right": ["J14", "J12", "J11"],           # from the right corner leftward
}

# interior placement groups: rectangle (x0, y0, x1, y1) and the parts that anchor them;
# passives join the group of the IC they share the most signal nets with
GROUPS = {
    "eth":      ([(22, 1, 52, 11)],                   ["U301", "Y301", "J10"]),
    "pwr_in":   ([(22, 11, 52, 24)],                  ["U101", "U102", "Q101", "Q102", "U401", "J17"]),
    "hub":      ([(22, 24, 52, 56), (10, 37, 22, 58)], ["U402", "Y401", "U403", "U404", "U405", "U406", "U408", "U409", "U410", "U411", "U407", "U105", "L103"]),
    "bucks":    ([(52, 1, 85, 36)],                   ["U103", "U104", "L101", "L102"]),
    "pass_drv": ([(52, 36, 70, 42)],                  ["Q803"]),                      # the coil driver, board side of the barrier
    "pass":     ([(68, 56, 84, 66)],                  ["D807", "R810", "R811"]),       # the opto's LED network, PSU side
    "mcu":      ([(85, 1, 111, 38)],                  ["U201", "Y201", "J16", "SW201", "D202"]),
    "dap":      ([(86, 39, 100, 66)],                 ["U601", "Y601", "J601", "SW601"]),    # 2 mm creepage from the isolated region (x = 84)
    "ftdi":     ([(100, 38, 110, 66)],                ["U501", "JP501", "JP502"]),
    "target":   ([(111, 1, 127, 38)],                 ["U701", "U702", "U703", "U704", "J15", "U202"]),
    "relays":   ([(110, 38, 128.5, 64)],              ["K801", "K802", "Q801", "Q802"]),
}
# parts placed by hand across the isolation barrier: (x, y, rotation) of the footprint origin
FIXED = {"K803": (56.0, 53.0, 0),          # coil pads (1, 8) at x = 56 outside the region, contacts (2, 4, 6) inside
         "U801": (66.0, 60.5, 180)}        # below the relay: LED pins (1, 2) at x = 66 inside the region, transistor pins (3, 4) at 58.4 outside
PACK_MARGIN = 0.0          # courtyard to courtyard (courtyards already carry 0.25 mm each)

# the isolated PSU region: the passthrough block behind J18, a strip along the front and a riser to J19
ISOLATION = [(64, 42), (84, 42), (84, 80), (48, 80), (48, 62), (64, 62)]   # behind J18/J19; x = 64 runs through K803 between coil and contacts
ISOLATION_PLANE_HOLE = [(62, 40), (86, 40), (86, 80), (46, 80), (46, 60), (62, 60)]   # the same, grown by ISO_GAP: the ground plane stops here
ISO_GAP = 2.0              # creepage between PSU_3A nets and board nets

STACKUP = [  # Advanced Circuits standard 4-layer 0.062"
    ("F.Cu", "copper", 0.035), ("dielectric 1", "prepreg", 0.3048, 4.6), ("In1.Cu", "copper", 0.035),
    ("dielectric 2", "core", 0.7112, 4.7), ("In2.Cu", "copper", 0.035), ("dielectric 3", "prepreg", 0.3048, 4.6), ("B.Cu", "copper", 0.035)]
