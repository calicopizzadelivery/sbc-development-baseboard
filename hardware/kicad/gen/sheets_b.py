"""Ethernet, USB hub, FTDI and DAPLink sheets, component-centric."""
from kit import Sheet, FP
from sch import snap
from fanout import fan, chain, L, P, Ser, Pull, PullLED, Tag, Flag, Conn, End, To, BusEnd, bus_join, rail_bus, decap_row, join_pins, top_caps, top_bus, Skip, jog, mark_end, Gap
from sheets_a import flags, TVS

AMBER, GREEN, RED = "LED AMBER", "LED GREEN", "LED RED"


def ethernet(project, num, page, sheet_path, plib):
    s = Sheet(project, "Ethernet: KSZ8081RNA RMII PHY and magjack", num, page, sheet_path)
    s.project_lib = plib
    s.note(["ETHERNET", "KSZ8081RNA in RMII 25 MHz mode (its power-up default): 25 MHz crystal on XI/XO, REF_CLK outputs 50 MHz",
            "to the K64 EXTAL0 through R301. This is the FRDM-K64F arrangement (Zephyr: microchip,interface-type = rmii-25MHz).",
            "PHY address 0 (pins 15/16 internal pull-downs; the MAC does not drive them). RXER needs the external pull-down.",
            "Transformer centre taps go to 0.1 uF each, not to a supply (datasheet 11.x). Bob Smith: 4x75R to 1 nF/2 kV."], (15, 15), 1.5)
    u = s.add("Interface_Ethernet", "KSZ8081RNA", "U301", "KSZ8081RNA", (160, 125), footprint="Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm")
    yx = s.add("Device", "Crystal_GND24", "Y301", "25MHz", (70, 165), 90, footprint=FP["XTAL4"])
    j10 = s.add("Connector", "RJ45_Kycon_G7LX-A88S7-BP-GY", "J10", "RJ45 magjack 10/100", (335, 125), footprint=FP["RJ45"])
    fan(s, j10, {1: End("td+"), 2: End("td-"), 3: End("rd+"), 6: End("rd-"), 13: End("ledg_k"),
                 14: chain(Ser("R", "330", None), P("+3V3")), 12: chain(Ser("R", "330", None), P("+3V3")), 11: P("GND"),
                 4: Pull("GND", "C", "100n", None), 7: Pull("GND", "C", "100n", None),
                 5: chain(Ser("R", "75", None), BusEnd("bs")), 8: chain(Ser("R", "75", None), BusEnd("bs")),
                 10: chain(Ser("R", "75", None), BusEnd("bs")), 9: chain(Ser("R", "75", None), BusEnd("bs")), "SH": P("GND")})
    bus_join(s, "bs", then=chain(Ser("C", "1n/2kV", None, fp=FP["C1206"]), P("GND")), sx=-1)
    fan(s, u, {10: chain(Pull("+3V3", "R", "4.7k", None), L("MDIO")), 11: L("MDC"), 12: L("RMII_RXD1"), 13: L("RMII_RXD0"), 15: L("RMII_CRS_DV"),
               16: chain(Ser("R", "33", None), L("RMII_CLK_50M")), 17: chain(Pull("GND", "R", "10k", None), L("RMII_RXER")),
               18: chain(Pull("+3V3", "R", "1k", None), L("PHY_INT_N")), 19: L("RMII_TXEN"), 20: L("RMII_TXD0"), 21: L("RMII_TXD1"), 24: L("K64_RESET_N"),
               8: chain(Pull("GND", "C", "22p", None), Conn(yx, 1)), 7: chain(Pull("GND", "C", "22p", None), Conn(yx, 3)),
               3: To("rd-"), 4: To("rd+"), 5: To("td-"), 6: To("td+"), 9: chain(Ser("R", "6.49k 1%", None), P("GND")), 23: To("ledg_k"),
               22: P("GND"), 25: P("GND")}, align={"L": "top"})
    jog(s, u, 2, "+3V3A_PHY", up=5.08, over=10.16)
    jog(s, u, 14, "+3V3", up=2.54, over=12.7)
    top_caps(s, u, 1, [("2u2", None), ("100n", None)], height=15.24, sx=-1)
    fan(s, yx, {2: P("GND")})
    s.two(s.FB("600R@100MHz", (40, 230), rot=90), "+3V3", "+3V3A_PHY")
    decap_row(s, "+3V3A_PHY", [("22u", FP["C0805"]), ("100n", None)], (55, 230))
    decap_row(s, "+3V3", [("100n", None)], (90, 230))
    flags(s, ["+3V3A_PHY"], (120, 230))
    s.note(["Crystal: 25 MHz +/-50 ppm, CL 16 pF typ (datasheet) -> 22 pF each, trim at bring-up.",
            "Green LED = link/activity (PHY LED0, active low). Yellow LED = PHY powered (cathode to GND)."], (20, 255), 1.3)
    return s


def hub(project, num, page, sheet_path, plib):
    s = Sheet(project, "USB hub: USB2517, upstream J1, four switched USB-A ports, FT231X switch", num, page, sheet_path)
    s.project_lib = plib
    s.note(["USB HUB", "USB2517 strap-configured (CFG_SEL=000), no firmware needed for the USB tree to come up.",
            "Port map: 1 = DAPLink, 2 = FT231X, 3 = disabled (DN3 pulled up), 4..7 = USB-A PORT1..PORT4 (J4: ports 4,5; J5: ports 6,7).",
            "NON_REM=11 (pin 40 up, pin 45 up) marks ports 1-3 non-removable and LOCAL_PWR high reports self-powered.",
            "LED_A/B pins pulled down: PRT_SWP normal polarity, BOOST=00, GANG_EN=0 (individual over-current).",
            "Port power is switched by TPS2553 under K64 GPIO (boot ON via pull-ups); PRTPWR outputs unused; /FAULT feeds OCSx_N."], (15, 15), 1.5)
    u = s.add("sbcbb", "USB2517", "U402", "USB2517", (165, 150), footprint="Package_DFN_QFN:QFN-64-1EP_9x9mm_P0.5mm_EP7.15x7.15mm")
    j1 = s.add("Connector", "USB_C_Receptacle_USB2.0_16P", "J1", "USB-C upstream", (35, 80), footprint=FP["USBC"])
    esd0 = s.add("Power_Protection", "USBLC6-2SC6", "U401", "USBLC6-2SC6", (76.2, 80.01), footprint=FP["SOT236"])     # I/O rows = J1 B7 (D-) and A6 (D+); VBUS pin lands on the VBUS stretch before the divider
    yx = s.add("Device", "Crystal_GND24", "Y401", "24MHz", (80, 130), 90, footprint=FP["XTAL4"])
    # Port blocks, one per connector unit: the ESD sits on the D-/D+ rows, the switch
    # output runs along the VBUS row, so every wire into the connector is straight.
    ports = []
    for n in range(1, 5):
        Y = 45.72 + (n - 1) * 58.42                                   # D- row of this port
        ref, unit = [("J4", 1), ("J4", 2), ("J5", 1), ("J5", 2)][n - 1]
        j = s.add("sbcbb", "USB_A_Stacked2", ref, f"USB-A PORT{n}", (394.97, Y + 8.89), unit=unit, footprint=FP["USBA2"])
        esd = s.add("Power_Protection", "USBLC6-2SC6", f"U4{7+n:02d}", "USBLC6-2SC6", (372.11, Y), footprint=FP["SOT236"])
        tps = s.add("sbcbb", "TPS2553DBV", f"U40{2+n}", "TPS2553DBV", (327.66, Y + 20.32), footprint=FP["SOT236"])   # OUT on the VBUS row
        ports.append((esd, tps, j, unit))
    u407 = s.add("sbcbb", "TPS2553DBV", "U407", "TPS2553DBV", (235, 262), footprint=FP["SOT236"])
    for pin in ("A8", "B8"): s.pin_nc(j1, pin)
    for pin in (29, 26, 23, 20, 30, 39, 36, 28, 22, 32, 18, 16, 14): s.pin_nc(u, str(pin))
    pd10 = lambda: chain(Ser("R", "10k", None), P("GND"))
    pu10 = lambda: chain(Ser("R", "10k", None), P("+3V3"))
    join_pins(s, j1, ["A6", "B6"], length=7.62); join_pins(s, j1, ["A7", "B7"], length=7.62)
    atts = {59: End("usbup_dp"), 58: End("usbup_dm"), 44: L("J1_VBUS_DET"),
            61: chain(Pull("GND", "C", "33p", None), Conn(yx, 3)), 60: chain(Pull("GND", "C", "33p", None), Conn(yx, 1)),
            43: chain(Pull("+3V3", "R", "10k", None), Pull("GND", "C", "1u", None), L("HUB_RESET_N")),
            63: chain(Ser("R", "12.0k 1%", None), P("GND")), 19: P("GND"),
            13: pd10(), 42: pd10(), 41: pd10(), 40: pu10(), 45: pu10(),
            65: P("GND"),
            2: L("HUB_DN1_DP"), 1: L("HUB_DN1_DM"), 4: L("HUB_DN2_DP"), 3: L("HUB_DN2_DM"), 7: pu10(), 6: pu10(),
            27: L("FTDI_FAULT_N"), 21: L("PORT1_FAULT_N"), 35: L("PORT2_FAULT_N"), 38: L("PORT3_FAULT_N"), 37: L("PORT4_FAULT_N")}
    for pin in (51, 49, 47, 33, 31, 17, 15, 50, 48, 34):
        atts[pin] = chain(Ser("R", "10k", None), BusEnd("strap_gnd"))      # LED_A/B straps: one shared GND bus
    for n, (esd, tps, j, unit) in enumerate(ports, start=1):
        dp, dm = {1: (9, 8), 2: (12, 11), 3: (54, 53), 4: (56, 55)}[n]
        atts[dp] = Conn(esd, 3); atts[dm] = Conn(esd, 1)                   # I/O2 is the D+ row, I/O1 the D- row
    ends = fan(s, u, atts, align={"L": "top"}, channels={"R": 266.7})    # left rows stay on their pins for U401; routes clear the cap ladder and pull-ups
    bus_join(s, "strap_gnd", then=P("GND"), sx=1)
    top_bus(s, u, [46, 24, 64, 5, 10, 52, 57], "+3V3", caps_left=[("100n", None)] * 4, caps_right=[("100n", None)] * 3 + [("4u7", FP["C0805"])],
            rail_at="left", height=12.7)
    top_caps(s, u, 25, [("1u", None), ("100n", None)], height=7.62, sx=-1)
    top_caps(s, u, 62, [("1u", None), ("100n", None)], height=12.7, sx=1)
    fan(s, yx, {2: P("GND")})
    fan(s, j1, {"A6": Skip(), "B6": Skip(), "A7": Skip(), "B7": Skip(),
                "A4": chain(Flag(None), Gap(20.32), Ser("R", "10k", None), Tag("J1_VBUS_DET", None), Ser("R", "22k", None), P("GND")),
                "A5": chain(Ser("R", "5.1k", None, step=12.7), P("GND")),       # the upper GND lands past the lower row's end
                "B5": chain(Ser("R", "5.1k", None, step=7.62), P("GND")), "A1": P("GND"), "SH": P("GND")}, align="top")
    jx = snap(j1.pin("A6")[0] + 7.62)                                   # the joined pairs continue straight into the ESD array
    for pin, row in (("1", j1.pin("B7")[1]), ("3", j1.pin("A6")[1])):
        s.wire((jx, row), esd0.pin(pin)); s.junction((jx, row))
    fan(s, esd0, {6: To("usbup_dm"), 4: To("usbup_dp"), 2: P("GND")})     # I/O1 sits on the D- row, I/O2 on D+
    vx, vy = esd0.pin("5")                                              # VBUS pin straight up onto J1's VBUS lane
    vb = (vx, j1.pin("A4")[1])
    s.wire((vx, vy), vb); s.junction(vb)
    for n, (esd, tps, j, unit) in enumerate(ports, start=1):
        vb, dmp, dpp, gnd = (1, 2, 3, 4) if unit == 1 else (5, 6, 7, 8)
        fan(s, esd, {6: Conn(j, dmp), 4: Conn(j, dpp), 5: L(f"PORT{n}_VBUS"), 2: P("GND")})
        fan(s, tps, {1: chain(Pull("GND", "C", "100n", None), P("+5V_PORTS")),
                     3: chain(Tag(f"PORT{n}_EN", None), Ser("R", "10k", None), P("+3V3")),
                     5: chain(Ser("R", "23.7k", None), P("GND")),
                     6: chain(Tag(f"PORT{n}_VBUS", None), Pull("GND", "C", "22u", None, fp=FP["C1206"]), PullLED(GREEN, "1k", None), Conn(j, vb)),
                     4: chain(Pull("+3V3", "R", "10k", None), L(f"PORT{n}_FAULT_N")), 2: P("GND")}, align="top")   # OUT stays on the VBUS row
        jatts = {gnd: P("GND")}
        if unit == 1:
            jatts["SH"] = P("GND")
        fan(s, j, jatts)
    fan(s, u407, {1: chain(Pull("GND", "C", "100n", None), P("+5V_PORTS")), 3: chain(Tag("FTDI_EN", None), Ser("R", "10k", None), P("+3V3")),
                  5: chain(Ser("R", "23.7k", None), P("GND")),
                  6: chain(Pull("GND", "C", "10u", None, fp=FP["C0805"]), PullLED(GREEN, "1k", None), P("FTDI_VBUS")),
                  4: chain(Tag("FTDI_FAULT_N", None), Ser("R", "10k", None), P("+3V3")), 2: P("GND")})
    s.note(["TPS2553 ILIM 23.7k -> ~1.1 A (datasheet: 20k -> 1.3 A typ, 15k -> 1.7 A). EN/FAULT pull-ups set the boot-ON state.",
            "U407 switches the FT231X's VBUS (hub port 2) under FTDI CYCLE, outside PORT ALL."], (20, 285), 1.3)
    return s


def ftdi(project, num, page, sheet_path, plib):
    s = Sheet(project, "FTDI: FT231X on hub port 2, standard 6-pin FTDI header", num, page, sheet_path)
    s.project_lib = plib
    s.note(["FTDI HEADER J9", "Pinout = TTL-232R / SparkFun: 1 GND (blk)  2 CTS (brn)  3 VCC (red)  4 TXD (org)  5 RXD (yel)  6 RTS/DTR (grn).",
            "TXD/RXD named from the FT231X side: TXD drives the target's RX. 3.3 V levels only; 1.8 V consoles use J13.",
            "JP501: pin 6 = DTR# (bridge C-A, default) or RTS# (bridge C-B). JP502: pin 3 VCC from 3V3OUT (50 mA), open by default.",
            "VCC comes from the TPS2553 on the hub sheet (FTDI_VBUS): FTDI CYCLE power-cycles the bridge without a replug.",
            "CBUS defaults: CBUS1 = RXLED#, CBUS2 = TXLED# (factory MTP); change with FT_PROG if ever needed."], (15, 15), 1.5)
    u = s.add("Interface_USB", "FT231XS", "U501", "FT231XS", (150, 120), footprint="Package_SO:SSOP-20_3.9x8.7mm_P0.635mm")
    j9 = s.add("Connector_Generic", "Conn_01x06", "J9", "FTDI header", (330, 110), footprint=FP["HDR6"])
    jp = s.add("Jumper", "SolderJumper_3_Open", "JP501", "RTS/DTR", (262, 125), 90, footprint=FP["JP3"])
    jp2 = s.add("Jumper", "SolderJumper_2_Open", "JP502", "VCC to J9", (285, 70), footprint=FP["JP2"])
    for pin in (5, 7, 8, 18, 19): s.pin_nc(u, str(pin))
    led = lambda: chain(Ser("D", "LED GREEN", None, lib="Device", name="LED", near="1", fp=FP["LED"]), Ser("R", "470", None), P("FTDI_3V3"))
    fan(s, u, {20: chain(Ser("R", "470", None), TVS(), Conn(j9, 4)), 4: chain(TVS(), Conn(j9, 5)), 9: chain(TVS(), Conn(j9, 2)),
               2: Conn(jp, 3), 1: Conn(jp, 1), 10: led(), 17: led(),
               11: L("HUB_DN2_DP"), 12: L("HUB_DN2_DM"), 13: chain(Pull("GND", "C", "100n", None), P("FTDI_3V3")),
               14: chain(Ser("R", "10k", None), P("FTDI_3V3")), 3: P("FTDI_3V3"), 6: P("GND"), 16: P("GND")})
    top_caps(s, u, 15, [("10u", FP["C0805"]), ("100n", None)], height=15.24, sx=-1, rail="FTDI_VBUS")
    fan(s, jp, {2: chain(Ser("R", "470", None), TVS(), Conn(j9, 6))})
    fan(s, jp2, {1: P("FTDI_3V3"), 2: Conn(j9, 3)})
    fan(s, j9, {1: P("GND", hook=(-5.08, -7.62))})     # off the row below, which carries the RXD route
    return s


def daplink(project, num, page, sheet_path, plib):
    s = Sheet(project, "DAPLink: MK20DX128VFM5 on hub port 1, SWD + CDC + MSD to the K64", num, page, sheet_path)
    s.project_lib = plib
    s.note(["DAPLINK", "MK20DX128VFM5 running DAPLink (k20dx HIC), powered from +5V_PORTS through its own USB regulator (VOUT33 -> VDD).",
            "Pin use follows the DAPLink k20dx HIC: PTC5 = SWCLK, PTC6 = SWDIO, PTB1 = nRESET to the K64, PTD4 = LED,",
            "UART1 PTC3/PTC4 bridges to the K64 UART0 (CDC console). Verify against DAPLink source/hic_hal/freescale/k20dx/IO_Config.h.",
            "J601 programs the K20 itself (bootloader + DAPLink). SW601 held at power-up enters DAPLink maintenance mode."], (15, 15), 1.5)
    u = s.add("MCU_NXP_Kinetis", "MK20DX128VFM5", "U601", "MK20DX128VFM5", (170, 115), footprint="Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm")
    j = s.add("Connector", "Conn_ARM_JTAG_SWD_10", "J601", "SWD (K20)", (40, 100), footprint=FP["SWD10"])
    yx = s.add("Device", "Crystal_GND24", "Y601", "8MHz", (45, 150), 90, footprint=FP["XTAL4"])   # below J601, clear of the reset network
    for pin in (9, 10, 13, 14, 20, 22, 23, 28, 30, 31, 32): s.pin_nc(u, str(pin))
    for pin in (6, 7, 8): s.pin_nc(j, str(pin))
    fan(s, u, {12: Conn(j, 4), 15: Conn(j, 2), 16: chain(Ser("R", "10k", None), P("K20_3V3")),
               17: chain(Pull("GND", "C", "18p", None), Conn(yx, 3)), 18: chain(Pull("GND", "C", "18p", None), Conn(yx, 1)),
               19: chain(Pull("K20_3V3", "R", "10k", None), Pull("GND", "C", "100n", None), Pull("GND", ("Switch", "SW_Push", "1"), "DAP RESET", None, fp=FP["SW"]), Conn(j, 10)),
               3: L("HUB_DN1_DP"), 4: L("HUB_DN1_DM"), 5: chain(Pull("GND", "C", "2u2", None), P("K20_3V3")),
               21: L("K64_RESET_N"), 24: L("K64_UART0_TX"), 25: L("K64_UART0_RX"), 26: L("SWCLK"), 27: L("SWDIO"),
               29: chain(Ser("D", "LED GREEN", None, lib="Device", name="LED", near="1", fp=FP["LED"]), Ser("R", "470", None), P("K20_3V3")),
               11: P("K20_3V3"), 2: P("GND"), 8: P("GND"), 33: P("GND")})
    top_bus(s, u, [1, 7], "K20_3V3", caps_right=[("100n", None), ("100n", None)], rail_at="right", height=12.7)
    top_caps(s, u, 6, [("2u2", None)], height=20.32, sx=-1, rail="+5V_PORTS")
    fan(s, yx, {2: P("GND")})
    fan(s, j, {1: P("K20_3V3"), 3: P("GND"), 9: P("GND")})
    return s
