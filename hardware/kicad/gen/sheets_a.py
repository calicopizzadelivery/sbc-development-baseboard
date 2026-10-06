"""Power and MCU sheets, component-centric: parts are placed first, then every
net fans out of its hub to whatever it connects to."""
from kit import Sheet, FP
from sch import snap
from fanout import fan, chain, L, P, Ser, Pull, PullLED, Tag, Flag, Conn, End, To, BusEnd, bus_join, rail_bus, decap_row, join_pins, top_caps, top_bus, Skip, Ladder, jog, mark_end, Gap, crystal, Reset

AMBER, GREEN, RED = "LED AMBER", "LED GREEN", "LED RED"
def TVS(v="PESD5V0S1UL"):
    """Line-to-GND ESD diode hanging from a lane. PESD5V0S1UL is unidirectional:
    the library symbol puts K (pin 1) on the line and A (pin 2) to GND, SOD-882."""
    if v == "PESD5V0S1UL":
        return Pull("GND", ("Diode", "PESD5V0S1UL", "1"), v, None, fp="Diode_SMD:D_SOD-882")
    return Pull("GND", "D", v, None, fp=FP["SOD523"])


def flags(s, rails, at):
    x, y = at
    for i, r in enumerate(rails):
        s.flag_rail(r, (x + 25.4 * (i % 5), y + 12.7 * (i // 5)))


def power(project, num, page, sheet_path, plib):
    s = Sheet(project, "Power: PD inlet, programming header, bus buffer, three bucks", num, page, sheet_path)
    s.project_lib = plib
    s.note(["POWER", "J2 is a PD sink only (no data). STUSB4500 negotiates from NVM; VBUS_EN_SNK gates the 5 V bucks through Q101,",
            "so the rails only come up once a sink contract (or plain Type-C 5 V) is valid. No series VBUS FET.",
            "J17 (Qwiic) programs the STUSB4500 NVM and powers it through VSYS when the board is dead.",
            "PCA9517A: A side = PD segment (+3V3_PD, diode-OR of +3V3 and the programmer), B side = K64 I2C0.",
            "A programmer on J17 pulls PCA_EN low through Q102: the K64 is disconnected from the PD bus in hardware."], (16, 17), 1.5)
    # ---- parts
    j2 = s.add("Connector", "USB_C_Receptacle_USB2.0_16P", "J2", "USB-C PD in", (28, 85), footprint=FP["USBC"])
    u1 = s.add("Interface_USB", "STUSB4500QTR", "U101", "STUSB4500QTR", (147, 85), footprint="Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm")
    q1 = s.Q("Transistor_FET", "2N7002", "2N7002", (250, 45))       # right of the STUSB4500 routes, above buck 1
    u2 = s.add("calico-ic", "PCA9517A", "U102", "PCA9517A", (150, 185), footprint="Package_SO:TSSOP-8_4.4x3mm_P0.65mm")   # below the STUSB4500's I2C lanes
    j17 = s.add("Connector_Generic", "Conn_01x04", "J17", "Qwiic PD", (40, 165), 0, mirror="y", footprint=FP["QWIIC"])
    q2 = s.Q("Transistor_FET", "2N7002", "2N7002", (150, 215))
    d8 = s.D("Diode", "BAT54C", "BAT54C", (70, 268), rot=180, fp=FP["SOT23"])   # common cathode on top
    for pin in ("A6", "B6", "A7", "B7", "A8", "B8"): s.pin_nc(j2, pin)
    for pin in (3, 14, 15, 17, 20): s.pin_nc(u1, str(pin))
    # ---- inlet
    join_pins(s, u1, [2, 1], length=22.86)        # CC1 + CC1DB: dead-battery mode
    join_pins(s, u1, [4, 5], length=22.86)        # CC2 + CC2DB
    fan(s, j2, {"A4": chain(Pull("GND", ("Device", "D_Zener", "1"), "SMAJ24A", None, fp=FP["SMA"]), P("VBUS_IN")), "A1": P("GND"), "SH": P("GND"),
                "A5": chain(TVS("ESDA25W"), Conn(u1, 2, stub=22.86)), "B5": chain(TVS("ESDA25W"), Conn(u1, 4, stub=22.86))})
    decap_row(s, "VBUS_IN", [("10u/50V", FP["C1210"]), ("10u/50V", FP["C1210"]), ("100n/50V", None), ("1u/50V", FP["C0805"])], (21, 140))
    s.led_chain("VBUS_IN", "GND", "10k", AMBER, (60, 193.04))     # below the PD I2C routes that turn at x = 59.69
    fan(s, u1, {6: chain(Ser("R", "10k", None), P("GND")), 2: Skip(), 1: Skip(), 4: Skip(), 5: Skip(),
                18: chain(Ser("R", "1k", None), P("VBUS_IN")),
                # PD_SCL/PD_SDA reach U102 and J17 by label: a wire would cross half the sheet
                7: chain(Pull("+3V3_PD", "R", "4.7k", None), TVS(), L("PD_SCL")),
                8: chain(Pull("+3V3_PD", "R", "4.7k", None), TVS(), L("PD_SDA")),
                # (left stack anchored on RESET: the CC rows are drawn by join_pins and must stay put)
                19: chain(Pull("+3V3_PD", "R", "10k", None), L("PD_ALERT_N")),
                12: P("GND"), 13: P("GND"),
                16: chain(Pull("VBUS_IN", "R", "100k", None), Pull("GND", ("Device", "D_Zener", "1"), "BZT52C5V1", None, fp=FP["SOD123"]), L("PD_EN_GATE")),   # to Q101 by label: the wire would run up past the buck input ladder
                9: Pull("VBUS_IN", "R", "470", None, fp=FP["R1206"]),
                11: chain(Pull("+3V3_PD", "R", "10k", None), L("PD_ATTACH_N")),
                10: P("GND"), 25: P("GND")}, align={"L": "top"})
    jog(s, u1, 24, "VBUS_IN", up=2.54, over=-7.62)
    jog(s, u1, 22, "+3V3_PRG", up=7.62, over=-20.32)
    top_caps(s, u1, 21, [("1u", None)], height=20.32, sx=-1)
    top_caps(s, u1, 23, [("1u", None)], height=17.78, sx=1)
    fan(s, q1, {1: L("PD_EN_GATE"), 2: P("GND"), 3: L("BUCK_EN")})
    s.note(["BUCK_EN: VBUS_EN_SNK released (no contract) -> Q101 on",
            "-> EN low -> bucks off. Contract valid -> VBUS_EN_SNK low",
            "-> Q101 off -> EN floats high (internal pull-up) -> bucks on.",
            "The zener keeps the gate under 5.1 V at 20 V VBUS."], (168, 109), 1.3)      # between U101 and the U103 compensation parts
    # ---- programming header, bus buffer, +3V3_PD
    fan(s, u2, {2: L("PD_SCL"), 3: L("PD_SDA"), 5: chain(Pull("+3V3", "R", "10k", None), Conn(q2, 3)), 7: L("I2C0_SCL"), 6: L("I2C0_SDA"),
                1: P("+3V3_PD"), 8: P("+3V3"), 4: P("GND")})
    fan(s, j17, {1: chain(Gap(7.62), P("GND")), 2: P("+3V3_PRG"), 3: L("PD_SDA"), 4: L("PD_SCL")})   # GND past the value text under the body
    fan(s, q2, {1: chain(Pull("GND", "R", "100k", None), Ser("R", "100k", None), P("+3V3_PRG")), 2: P("GND")})
    fan(s, d8, {1: P("+3V3"), 2: P("+3V3_PRG"), 3: P("+3V3_PD")})
    decap_row(s, "+3V3_PRG", [("1u", None), ("R", "100k", None)], (100, 262))
    decap_row(s, "+3V3_PD", [("100n", None), ("100n", None)], (135, 262))
    s.led_chain("+3V3_PD", "GND", "470", AMBER, (170, 262))
    decap_row(s, "+3V3", [("100n", None)], (190, 262))
    s.series("+3V3_PRG", "PD_PROG_DET", "100k", (225, 262))
    # ---- bucks 1 and 2
    for ref, y, rail in (("U103", 75, "+5V_PORTS"), ("U104", 150, "+5V_TGT")):
        u = s.add("calico-ic", "TPS54560BDDA", ref, "TPS54560BDDA", (280, y), footprint="Package_SO:HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.1mm")
        lind = s.add("Device", "L", s.ref("L"), "10u/6A", (330, y - 12.7), 90, footprint=FP["L_PWR"])
        fan(s, u, {2: chain(Ladder([("100n/50V", None), ("10u/50V", FP["C1210"]), ("10u/50V", FP["C1210"])]), P("VBUS_IN")),
                   3: L("BUCK_EN"),
                   4: Pull("GND", "R", "243k", None),
                   6: chain(Pull("GND", "C", "47p", None), Ser("R", "16.9k", None), Ser("C", "4n7", None), P("GND")),   # TPS54560B datasheet 5 V / 400 kHz example, same 141 uF output
                   1: chain(Ser("C", "100n/50V", None), Conn(lind, 1)),
                   8: chain(Pull("GND", ("Device", "D_Schottky", "1"), "B560C", None, fp=FP["SMA"]), Conn(lind, 1)),
                   }, align={"L": "top"})                                   # VIN stays on its pin with the input ladder
        fan(s, u, {
                   5: chain(Gap(7.62), Pull("GND", "R", "9.76k", None), Pull(rail, "R", "51.1k", None)),   # past the catch diode's text on the SW lane
                   7: P("GND"), 9: P("GND")})
        fan(s, lind, {2: chain(Ladder([("47u/10V", FP["C1210"]), ("47u/10V", FP["C1210"]), ("CP", "100u/10V", FP["CP"])]), PullLED(AMBER, "1k", None), P(rail, hook=(-7.62, -7.62)))})
    s.note(["TPS54560B: non-synchronous, 4.5-60 V in, 5 A. fsw 400 kHz (RT 243k).",
            "FB 51.1k/9.76k -> 5.0 V. COMP 16.9k / 4.7n / 47p and the B560C are the",
            "datasheet's 5 V / 400 kHz design example (141 uF ceramic out, as here)."], (168, 121), 1.3)
    # ---- buck 3
    u5 = s.add("Regulator_Switching", "TPS62823DLC", "U105", "TPS62823DLC", (300, 215), footprint="Package_SON:Texas_VSON-HR-8_1.5x2mm_P0.5mm")   # above the title block
    s.pin_nc(u5, "4"); s.pin_nc(u5, "8")
    fan(s, u5, {7: chain(Pull("GND", "C", "10u", None, fp=FP["C0805"]), P("+5V_PORTS")), 1: chain(Gap(2.54), P("+5V_PORTS")),
                6: chain(Ser("L", "470n/4A", None), Pull("GND", "C", "22u", None, fp=FP["C0805"]), Pull("GND", "C", "22u", None, fp=FP["C0805"]), PullLED(AMBER, "470", None), P("+3V3")),
                2: chain(Pull("GND", "R", "100k", None), Pull("+3V3", "R", "453k", None), Pull("+3V3", "C", "120p", None)),   # TPS62823 datasheet: R2 100k, R1 for 3.3 V, Cff 120 pF
                3: P("GND"), 5: P("GND")})
    flags(s, ["VBUS_IN", "GND", "+3V3_PRG", "+3V3_PD", "+5V_PORTS", "+5V_TGT", "+3V3"], (25, 246))
    return s


def mcu(project, num, page, sheet_path, plib):
    s = Sheet(project, "MCU: MK64FN1M0VLL12, USB device port, SWD, heartbeat", num, page, sheet_path)
    s.project_lib = plib
    s.note(["MCU", "MK64FN1M0VLL12 (LQFP-100). Clock: 50 MHz RMII REF_CLK from the KSZ8081 into EXTAL0, as on the FRDM-K64F.",
            "USB regulator: VREGIN fed only from J3 VBUS through D201, so the K64 cannot back-feed the target and the D+ pull-up",
            "disappears when the target is off. VOUT33 powers the transceiver. Pin allocation in docs/hardware-spec.md.",
            "Spare pins (PTA1, PTA2, PTB23, PTD7, PTE0-6, PTE26, ADC, DAC) are left no-connect."], (16, 17), 1.5)
    u = s.add("calico-ic", "MK64FN1M0VLL12", "U201", "MK64FN1M0VLL12", (200, 150), footprint="Package_QFP:LQFP-100_14x14mm_P0.5mm")
    j3 = s.add("Connector", "USB_C_Receptacle_USB2.0_16P", "J3", "USB-C HID to target", (35, 73.66), footprint=FP["USBC"])        # D-/D+ rows on U202's, which sit on the K64's USB rows
    j16 = s.add("Connector", "Conn_ARM_JTAG_SWD_10", "J16", "SWD", (360, 60), 0, mirror="y", footprint=FP["SWD10"])   # signals face the K64, VTref up, GND down
    rgb = s.add("Device", "LED_RGBA", "D202", "RGB heartbeat", (355, 225), footprint=FP["RGB"])
    for pin in (51, 14, 15, 16, 17, 18, 19, 20, 21, 26, 27, 35, 36, 69, 100, 1, 2, 3, 4, 5, 6, 7, 33): s.pin_nc(u, str(pin))
    for pin in ("A8", "B8"): s.pin_nc(j3, pin)
    for pin in (6, 7, 8): s.pin_nc(j16, str(pin))
    join_pins(s, j3, ["A6", "B6"], length=7.62); join_pins(s, j3, ["A7", "B7"], length=7.62)
    fan(s, j3, {"A6": Skip(), "B6": Skip(), "A7": Skip(), "B7": Skip(),
                "A4": chain(Flag(None), Gap(22.86), L("J3_VBUS")),
                "A5": chain(Ser("R", "5.1k", None, step=12.7), P("GND")),       # the upper GND lands past the lower row's end
                "B5": chain(Ser("R", "5.1k", None, step=7.62), P("GND")),
                "A1": P("GND"), "SH": P("GND")}, align="top")
    esd = s.add("Power_Protection", "USBLC6-2SC6", "U202", "USBLC6-2SC6", (83.82, 74.93), footprint=FP["SOT236"])  # I/O rows = J3 B7 (D-) and A6 (D+); VBUS pin lands on J3's VBUS lane
    esd.val_at = (83.82, 91.44)                                            # value under the part, clear of the K64's route columns
    jx = snap(j3.pin("A6")[0] + 7.62)                                   # the joined pairs continue straight into the ESD array
    for pin, row in (("1", j3.pin("B7")[1]), ("3", j3.pin("A6")[1])):
        s.wire((jx, row), esd.pin(pin)); s.junction((jx, row))
    fan(s, esd, {2: P("GND")})
    vx, vy = esd.pin("5")                                               # VBUS pin straight up onto J3's VBUS lane
    vb = (vx, j3.pin("A4")[1])
    s.wire((vx, vy), vb); s.junction(vb)
    mark_end(s, "j3vbus", vb, -1)                                       # ...where the K64's VREGIN diode lands too
    led = lambda: Ser("R", "330", None)
    ends = fan(s, u, {
        # left: USB regulator, USB, clock, reset
        13: chain(Flag(None), Pull("GND", "C", "2u2", None), Ser("D", "BAT54", None, lib="Device", name="D_Schottky", near="1", fp=FP["SOD123"]), To("j3vbus", direct=True)),
        12: Pull("GND", "C", "2u2", None),
        10: Conn(esd, 4), 11: Conn(esd, 6),                   # I/O2 carries D+, I/O1 D-
        50: L("RMII_CLK_50M"),
        29: End("extal32"), 28: End("xtal32"),                                # the 32 kHz crystal hangs below, drawn by crystal()
        52: chain(Tag("K64_RESET_N", None), Reset("+3V3", "10k", "1u", "RESET", sw_fp=FP["SW"])),   # pull-up, cap and button in one downward-flowing cluster
        38: Pull("+3V3", "R", "10k", None),
        # right: everything the K64 drives elsewhere
        34: chain(Tag("SWCLK", None), Conn(j16, 4)), 37: chain(Tag("SWDIO", None), Conn(j16, 2)),
        39: L("RMII_RXER"), 42: L("RMII_RXD1"), 43: L("RMII_RXD0"), 44: L("RMII_CRS_DV"), 45: L("RMII_TXEN"), 46: L("RMII_TXD0"), 47: L("RMII_TXD1"),
        53: L("MDIO"), 54: L("MDC"), 55: L("TGT_IMON"), 56: L("PSU_PRESENT_N"), 57: L("PD_ATTACH_N"), 58: L("PD_ALERT_N"), 59: L("PD_PROG_DET"),
        62: L("K64_UART0_RX"), 63: L("K64_UART0_TX"), 64: L("HUB_RESET_N"),
        65: chain(led(), Conn(rgb, 1)), 66: chain(led(), Conn(rgb, 2)), 67: chain(led(), Conn(rgb, 3)),
        68: L("PHY_INT_N"),
        70: L("PORT1_EN"), 71: L("PORT2_EN"), 72: L("PORT3_EN"), 73: L("TGT_UART_RX"), 76: L("TGT_UART_TX"), 77: L("PORT4_EN"),
        78: chain(Tag("PORT1_FAULT_N", None, step=21.59), Ser("R", "10k", None), BusEnd("pu_bus")), 79: chain(Tag("PORT2_FAULT_N", None, step=21.59), Ser("R", "10k", None), BusEnd("pu_bus")), 80: chain(Tag("PORT3_FAULT_N", None, step=21.59), Ser("R", "10k", None), BusEnd("pu_bus")), 81: chain(Tag("PORT4_FAULT_N", None, step=21.59), Ser("R", "10k", None), BusEnd("pu_bus")),
        82: chain(Tag("I2C1_SCL", None, step=21.59), Ser("R", "4.7k", None), BusEnd("pu_bus")), 83: chain(Tag("I2C1_SDA", None, step=21.59), Ser("R", "4.7k", None), BusEnd("pu_bus")),
        84: L("FTDI_EN"), 85: chain(Tag("FTDI_FAULT_N", None, step=21.59), Ser("R", "10k", None), BusEnd("pu_bus")), 86: L("TGT_EN"), 87: L("TGT_FAULT_N"),
        90: L("RLY1_DRV"), 91: L("RLY2_DRV"), 92: L("RLY_PSU_DRV"),
        93: L("GPIO1"), 94: L("GPIO2"), 95: L("GPIO3"), 96: L("GPIO4"), 97: L("GPIO5"), 98: L("GPIO6"),
        99: chain(Pull("GND", "R", "47k", None), Ser("R", "100k", None), L("J3_VBUS")),      # VBUS sense divider at the ADC pin
        31: chain(Pull("+3V3", "R", "4.7k", None), Gap(17.78), L("I2C0_SCL")), 32: chain(Gap(7.62), Pull("+3V3", "R", "4.7k", None), L("I2C0_SDA")),
    }, align={"L": "top"})
    # seven pull-ups to +3V3 on adjacent pins (four port /FAULT, FTDI /FAULT, I2C1 SCL/SDA): one column
    # of resistors to one rail symbol, as the strap buses are drawn. Hung one per lane they would stagger
    # past each other off the sheet.
    bus_join(s, "pu_bus", then=P("+3V3"), sx=1)
    crystal(s, u, "extal32", "xtal32", "Y201", "32.768kHz", FP["XTAL2"], "12p", margin=1.27)   # the K64's left routes are straight, so the columns are free
    top_bus(s, u, [8, 40, 48, 61, 75, 89, 30], "+3V3", caps_left=[("100n", None)] * 6 + [("10u", FP["C0805"])], rail_at="left", height=12.7)
    top_bus(s, u, [22, 23], "+3V3A", caps_right=[("100n", None), ("10u", FP["C0805"])], rail_at="left", height=22.86, margin=2.54,
            extra=chain(Ser("FB", "600R@100MHz", None), P("+3V3")))
    top_bus(s, u, [9, 41, 49, 60, 74, 88, 25, 24], "GND", rail_at="right", height=7.62)
    # J3 and its ESD array
    s.note(["J3: UFP, Rd 5.1k on both CC. VBUS is sense-only: D201 to VREGIN plus the 100k/47k divider. No board rail reaches J3."], (20, 200), 1.3)
    fan(s, j16, {1: P("+3V3"), 3: P("GND"), 9: P("GND"), 10: L("K64_RESET_N")})
    fan(s, rgb, {4: P("+3V3")})
    flags(s, ["+3V3A"], (40, 262))
    return s
