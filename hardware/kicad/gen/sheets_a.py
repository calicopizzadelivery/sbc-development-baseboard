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


def flags(s, rails, at, classes=None):
    x, y = at
    for i, r in enumerate(rails):
        s.flag_rail(r, (x + 25.4 * (i % 5), y + 12.7 * (i // 5)), (classes or {}).get(r))


def power(project, num, page, sheet_path, plib):
    s = Sheet(project, "Power: 5 V barrel inlet, input protection, 3V3 buck", num, page, sheet_path)
    s.project_lib = plib
    s.note(["POWER", "J2: 2.5 x 5.5 mm barrel jack, centre positive, for a 5 V 4 A (20 W) adapter (2026-10-10; a USB-C PD inlet with two",
            "5 V bucks until then). SMAJ5.0A clamps the inlet; Q101, a P-channel MOSFET with its body diode toward the rail and its",
            "gate at GND, blocks reverse polarity at 9.5 mOhm. No series fuse: the adapter limits the inlet, the eFuse the target rail,",
            "the TPS2553s the ports. The adapter's 4 A is the only limit on the sum: the ports (4 x 1.1 A), the target rail (3 A) and the",
            "board (0.5 A) can ask for more together; firmware keeps the budget (docs/hardware-spec.md section 4).",
            "+5V is laid out for 4 A (class PWR_4A, 2.5 mm or pours); +5V_TGT leaves the eFuse at up to 3 A in the same class."], (16, 17), 1.5)
    # ---- parts
    j2 = s.add("Connector", "Barrel_Jack_Switch", "J2", "5 V in, 2.5 mm", (28, 85), footprint=FP["BARREL"])
    q1 = s.Q("Transistor_FET", "DMP3013SFV", "DMP3013SFV", (110, 80), fp="Package_SON:Diodes_PowerDI3333-8")   # reverse-polarity pass FET: drain at the jack, source on the rail
    s.pin_nc(j2, "3")                                                 # the jack's switch contact
    # ---- inlet: TVS at the jack, the FET, the bulk capacitors and the rail LED on its source
    fan(s, j2, {1: chain(Pull("GND", ("Device", "D_Zener", "1"), "SMAJ5.0A", None, fp=FP["SMA"]), Conn(q1, 5)), 2: P("GND")})
    fan(s, q1, {1: chain(Ladder([("47u/10V", FP["C1210"]), ("47u/10V", FP["C1210"]), ("100n", None)]), PullLED(AMBER, "1k", None), P("+5V")),
                4: Pull("GND", "R", "100k", None)})
    # ---- the 3V3 buck
    u5 = s.add("Regulator_Switching", "TPS62823DLC", "U105", "TPS62823DLC", (300, 215), footprint="Package_SON:Texas_VSON-HR-8_1.5x2mm_P0.5mm")   # above the title block
    s.pin_nc(u5, "4"); s.pin_nc(u5, "8")
    fan(s, u5, {7: chain(Pull("GND", "C", "10u", None, fp=FP["C0805"]), P("+5V")), 1: chain(Gap(2.54), P("+5V")),
                6: chain(Ser("L", "470n/4A", None), Pull("GND", "C", "22u", None, fp=FP["C0805"]), Pull("GND", "C", "22u", None, fp=FP["C0805"]), PullLED(AMBER, "470", None), P("+3V3")),
                2: chain(Pull("GND", "R", "100k", None), Pull("+3V3", "R", "453k", None), Pull("+3V3", "C", "120p", None)),   # TPS62823 datasheet: R2 100k, R1 for 3.3 V, Cff 120 pF
                3: P("GND"), 5: P("GND")})
    flags(s, ["+5V", "GND", "+3V3"], (25, 246), classes={"+5V": "PWR_4A"})   # the high-current rail carries its class (and current) on the sheet
    return s


def mcu(project, num, page, sheet_path, plib):
    s = Sheet(project, "MCU: MK64FN1M0VLL12, USB device port, SWD, heartbeat", num, page, sheet_path)
    s.project_lib = plib
    s.note(["MCU", "MK64FN1M0VLL12 (LQFP-100). Clock: 50 MHz RMII REF_CLK from the KSZ8081 into EXTAL0, as on the FRDM-K64F.",
            "USB regulator: VREGIN fed only from J3 VBUS through D201, so the K64 cannot back-feed the target and the D+ pull-up",
            "disappears when the target is off. VOUT33 powers the transceiver. Pin allocation in docs/hardware-spec.md.",
            "Spare pins (PTA1, PTA2, PTB23, PTD7, PTE0-6, PTE26, ADC, DAC) are left no-connect.",
            'USB 2.0: K64_USB_P/N (K64 to U202) and J3_D_P/N (U202 to J3) are 90 ohm differential pairs, net class USB: route as pairs, no stubs.'], (16, 17), 1.5)
    u = s.add("calico-ic", "MK64FN1M0VLL12", "U201", "MK64FN1M0VLL12", (200, 150), footprint="Package_QFP:LQFP-100_14x14mm_P0.5mm")
    j3 = s.add("Connector", "USB_C_Receptacle_USB2.0_16P", "J3", "USB-C HID to target", (35, 73.66), footprint=FP["USBC"])        # D-/D+ rows on U202's, which sit on the K64's USB rows
    j16 = s.add("Connector", "Conn_ARM_JTAG_SWD_10", "J16", "SWD", (360, 60), 0, mirror="y", footprint=FP["SWD10"])   # signals face the K64, VTref up, GND down
    rgb = s.add("Device", "LED_RGBA", "D202", "RGB heartbeat", (355, 225), footprint=FP["RGB"])
    for pin in (51, 14, 15, 16, 17, 18, 19, 20, 21, 26, 27, 35, 36, 69, 100, 1, 2, 3, 4, 5, 6, 7, 33): s.pin_nc(u, str(pin))
    for pin in ("A8", "B8"): s.pin_nc(j3, pin)
    for pin in (6, 7, 8): s.pin_nc(j16, str(pin))
    jx = join_pins(s, j3, ["A6", "B6"], length=10.16)[0]; join_pins(s, j3, ["A7", "B7"], length=10.16)   # room for the pair's labels on the lower stubs
    fan(s, j3, {"A6": Skip(), "B6": Skip(), "A7": Skip(), "B7": Skip(),
                "A4": chain(Flag(None), Gap(22.86), L("J3_VBUS")),
                "A5": chain(Ser("R", "5.1k", None, step=12.7), P("GND")),       # the upper GND lands past the lower row's end
                "B5": chain(Ser("R", "5.1k", None, step=7.62), P("GND")),
                "A1": P("GND"), "SH": P("GND")}, align="top")
    # the array drawn with I/O2 on the D- row (house symbol, one row lower than the stock one), so the pair runs through it
    # uncrossed on the board (ecad-standards/layout.md 3.8); I/O rows = J3 B7 (D-) and A6 (D+); VBUS pin lands on J3's VBUS lane
    esd = s.add("calico-ic", "USBLC6-2SC6-IO2up", "U202", "USBLC6-2SC6", (83.82, 74.93 + 2.54), footprint=FP["SOT236"])
    esd.val_at = (83.82, 91.44)                                            # value under the part, clear of the K64's route columns
    # the joined pairs continue straight into the ESD array from their join
    for pin, row in (("3", j3.pin("B7")[1]), ("1", j3.pin("A6")[1])):
        s.wire((jx, row), esd.pin(pin)); s.junction((jx, row))
    fan(s, esd, {2: P("GND")})
    for pin, net in (("B7", "J3_D_N"), ("B6", "J3_D_P")):              # the connector side of the pair, named for the router: on the lower stub of each joined pair
        s.label(net, j3.pin(pin), 0)
    vx, vy = esd.pin("5")                                               # VBUS pin straight up onto J3's VBUS lane
    vb = (vx, j3.pin("A4")[1])
    s.wire((vx, vy), vb); s.junction(vb)
    tap = (snap(vx + 2.54), vb[1]); s.junction(tap)                      # ...and the K64's VREGIN diode lands beside it, not on its stub
    mark_end(s, "j3vbus", tap, -1)
    led = lambda: Ser("R", "330", None)
    ends = fan(s, u, {
        # left: USB regulator, USB, clock, reset
        13: chain(Flag(None), Pull("GND", "C", "2u2", None), Ser("D", "BAT54", None, lib="Device", name="D_Schottky", near="1", fp=FP["SOD123"]), To("j3vbus", direct=True)),
        12: Pull("GND", "C", "2u2", None),
        10: Conn(esd, 6), 11: Conn(esd, 4),                   # I/O1 carries D+ (the lower row of the house symbol), I/O2 D-
        50: L("RMII_CLK_50M"),
        29: End("extal32"), 28: End("xtal32"),                                # the 32 kHz crystal hangs below, drawn by crystal()
        52: chain(Tag("K64_RESET_N", None), Reset("+3V3", "10k", "1u", "RESET", sw_fp=FP["SW"])),   # pull-up, cap and button in one downward-flowing cluster
        38: Pull("+3V3", "R", "10k", None),
        # right: everything the K64 drives elsewhere
        34: chain(Tag("SWCLK", None), Conn(j16, 4)), 37: chain(Tag("SWDIO", None), Conn(j16, 2)),
        39: L("RMII_RXER"), 42: L("RMII_RXD1"), 43: L("RMII_RXD0"), 44: L("RMII_CRS_DV"), 45: L("RMII_TXEN"), 46: L("RMII_TXD0"), 47: L("RMII_TXD1"),
        53: L("MDIO"), 54: L("MDC"), 55: L("TGT_IMON"), 56: L("PSU_PRESENT_N"),
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
    }, align={"L": "top"})
    for pin in ("31", "32", "57", "58", "59"):                        # I2C0 and the PD sink's lines, free since the PD inlet went (2026-10-10)
        s.pin_nc(u, pin)
    for pin, net in (("6", "K64_USB_P"), ("4", "K64_USB_N")):            # the K64 side of the pair, named for the router: at the ESD's pin end, text along the route
        s.label(net, esd.pin(pin), 0)
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
