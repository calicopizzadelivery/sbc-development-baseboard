"""Power and MCU sheets."""
from kit import Sheet, Row, FP

AMBER, GREEN, RED = "LED AMBER", "LED GREEN", "LED RED"


def power(project, num, page, sheet_path, plib):
    s = Sheet(project, "Power: PD inlet, programming header, bus buffer, three bucks", num, page, sheet_path)
    s.project_lib = plib
    s.note(["POWER", "J2 is a PD sink only (no data). STUSB4500 negotiates from NVM; VBUS_EN_SNK gates the 5 V bucks,",
            "so the rails only come up once a sink contract (or plain Type-C 5 V) is valid. No series VBUS FET.",
            "J17 (Qwiic) programs the STUSB4500 NVM and powers it through VSYS when the board is dead.",
            "PCA9517A: A side = PD segment (+3V3_PD, diode-OR of +3V3 and the programmer), B side = K64 I2C0.",
            "A programmer on J17 pulls PCA_EN low: the K64 is disconnected from the PD bus in hardware."], (15, 15), 1.5)

    # ---- J2 PD inlet
    j2 = s.ic("Connector", "USB_C_Receptacle_USB2.0_16P", "J2", "USB-C PD in", (40, 60), fp=FP["USBC"],
              nets={"A5": "PD_CC1", "B5": "PD_CC2"}, power={"A4": "VBUS_IN", "A1": "GND", "SH": "GND"},
              nc=["A6", "B6", "A7", "B7", "A8", "B8"])
    r = Row(25, 110)
    s.two(s.D("Diode", "SMAJ24A", "SMAJ24A", r(), rot=270, fp=FP["SMA"]), "VBUS_IN", "GND")
    s.decap("VBUS_IN", "10u/50V", r(), fp=FP["C1210"]); s.decap("VBUS_IN", "10u/50V", r(), fp=FP["C1210"]); s.decap("VBUS_IN", "100n/50V", r())
    s.led_chain("VBUS_IN", "GND", "10k", AMBER, r())
    s.flag_rail("VBUS_IN", (25, 135)); s.flag_rail("GND", (45, 135))
    s.two(s.D("Device", "D_TVS", "ESDA25W", (25, 150), rot=270, fp=FP["SOD523"]), "PD_CC1", "GND")
    s.two(s.D("Device", "D_TVS", "ESDA25W", (35, 150), rot=270, fp=FP["SOD523"]), "PD_CC2", "GND")

    # ---- STUSB4500
    u1 = s.ic("Interface_USB", "STUSB4500QTR", "U101", "STUSB4500QTR", (125, 70),
              fp="Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm",
              nets={1: "PD_CC1", 2: "PD_CC1", 4: "PD_CC2", 5: "PD_CC2", 6: "PD_RESET", 7: "PD_SCL", 8: "PD_SDA",
                    9: "PD_DISCH", 11: "PD_ATTACH_N", 16: "PD_VBUS_EN_N", 18: "PD_VBUS_VS", 19: "PD_ALERT_N",
                    21: "PD_VREG_1V2", 23: "PD_VREG_2V7"},
              power={24: "VBUS_IN", 22: "+3V3_PRG", 10: "GND", 12: "GND", 13: "GND", 25: "GND"},
              nc=[3, 14, 15, 17, 20])
    r = Row(85, 115, 20.32)
    s.pulldown("PD_RESET", "10k", r())
    s.series("VBUS_IN", "PD_DISCH", "470", r(), fp=FP["R1206"])
    s.series("VBUS_IN", "PD_VBUS_VS", "1k", r())
    s.decap("VBUS_IN", "1u/50V", r(), fp=FP["C0805"]); s.decap("VBUS_IN", "100n/50V", r())
    s.cap_to_gnd("PD_VREG_1V2", "1u", r()); s.cap_to_gnd("PD_VREG_2V7", "1u", r())
    r = Row(85, 140)
    s.decap("+3V3_PRG", "1u", r()); s.pulldown("+3V3_PRG", "100k", r())
    s.pullup("PD_ATTACH_N", "10k", r(), rail="+3V3_PD"); s.pullup("PD_ALERT_N", "10k", r(), rail="+3V3_PD")
    s.pullup("PD_SCL", "4.7k", r(), rail="+3V3_PD"); s.pullup("PD_SDA", "4.7k", r(), rail="+3V3_PD")
    # buck enable: VBUS_EN_SNK (open drain, low = contract valid) -> inverter -> BUCK_EN
    s.series("VBUS_IN", "PD_VBUS_EN_N", "100k", (85, 165))
    s.two(s.D("Device", "D_Zener", "BZT52C5V1", (100, 165), rot=270, fp=FP["SOD123"]), "PD_VBUS_EN_N", "GND")
    q = s.Q("Transistor_FET", "2N7002", "2N7002", (118, 170))
    s.pin_label(q, "1", "PD_VBUS_EN_N"); s.pin_power(q, "2", "GND"); s.pin_label(q, "3", "BUCK_EN")
    s.note(["BUCK_EN: VBUS_EN_SNK released (no contract) -> Q101 on -> EN low -> bucks off.",
            "Contract valid -> VBUS_EN_SNK low -> Q101 off -> EN floats high (internal pull-up) -> bucks on.",
            "Zener keeps the gate below 5.1 V at 20 V VBUS."], (85, 185), 1.3)

    # ---- J17 programming header + bus buffer
    s.ic("Connector_Generic", "Conn_01x04", "J17", "Qwiic PD programming", (40, 200), fp=FP["QWIIC"],
         nets={3: "PD_SDA", 4: "PD_SCL"}, power={1: "GND", 2: "+3V3_PRG"})
    s.two(s.D("Device", "D_TVS", "PESD5V0S1UL", (25, 225), rot=270, fp=FP["SOD523"]), "PD_SDA", "GND")
    s.two(s.D("Device", "D_TVS", "PESD5V0S1UL", (35, 225), rot=270, fp=FP["SOD523"]), "PD_SCL", "GND")
    d = s.D("Diode", "BAT54C", "BAT54C", (70, 205), fp=FP["SOT23"])
    s.pin_power(d, "1", "+3V3"); s.pin_power(d, "2", "+3V3_PRG"); s.pin_power(d, "3", "+3V3_PD")
    r = Row(85, 225, 20.32)
    s.decap("+3V3_PD", "100n", r()); s.led_chain("+3V3_PD", "GND", "470", AMBER, r())
    s.series("+3V3_PRG", "PD_PROG_DET", "100k", r())
    s.series("+3V3_PRG", "PCA_EN_GATE", "100k", r()); s.pulldown("PCA_EN_GATE", "100k", r())
    s.pullup("PCA_EN", "10k", r())
    q = s.Q("Transistor_FET", "2N7002", "2N7002", (150, 248))
    s.pin_label(q, "1", "PCA_EN_GATE"); s.pin_power(q, "2", "GND"); s.pin_label(q, "3", "PCA_EN")
    s.ic("sbcbb", "PCA9517A", "U102", "PCA9517A", (190, 200), fp="Package_SO:TSSOP-8_4.4x3mm_P0.65mm",
         nets={2: "PD_SCL", 3: "PD_SDA", 5: "PCA_EN", 7: "I2C0_SCL", 6: "I2C0_SDA"},
         power={1: "+3V3_PD", 8: "+3V3", 4: "GND"})
    s.decap("+3V3_PD", "100n", (175, 230)); s.decap("+3V3", "100n", (185, 230))
    s.flag_rail("+3V3_PD", (210, 230)); s.flag_rail("+3V3_PRG", (230, 230))

    # ---- bucks 1 and 2: TPS54560B, 5 V / 5 A from VBUS_IN
    def buck(ref, y, rail, led_r):
        u = s.ic("Regulator_Switching", "TPS54560BDDA", ref, "TPS54560BDDA", (300, y),
                 fp="Package_SO:HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.1mm",
                 nets={1: f"{ref}_BOOT", 3: "BUCK_EN", 4: f"{ref}_RT", 5: f"{ref}_FB", 6: f"{ref}_COMP", 8: f"{ref}_SW"},
                 power={2: "VBUS_IN", 7: "GND", 9: "GND"})
        r = Row(225, y + 22, 12.7)
        s.decap("VBUS_IN", "10u/50V", r(), fp=FP["C1210"]); s.decap("VBUS_IN", "10u/50V", r(), fp=FP["C1210"]); s.decap("VBUS_IN", "100n/50V", r())
        s.pulldown(f"{ref}_RT", "243k", r())
        s.two(s.R("19.1k", r()), f"{ref}_COMP", f"{ref}_CZ"); s.cap_to_gnd(f"{ref}_CZ", "3n3", r()); s.cap_to_gnd(f"{ref}_COMP", "47p", r())
        s.two(s.CP("100u/10V", r()), rail, "GND")
        s.two(s.R("51.1k", r()), rail, f"{ref}_FB"); s.pulldown(f"{ref}_FB", "9.76k", r())
        s.led_chain(rail, "GND", led_r, AMBER, r())
        r = Row(340, y - 8, 12.7)
        s.two(s.C("100n/50V", r()), f"{ref}_BOOT", f"{ref}_SW")
        s.two(s.L("10u/6A", r(), fp=FP["L_PWR"]), f"{ref}_SW", rail)
        s.two(s.D("Device", "D_Schottky", "B560C", r(), rot=270, fp=FP["SMA"]), f"{ref}_SW", "GND")
        s.decap(rail, "47u/10V", r(), fp=FP["C1210"]); s.decap(rail, "47u/10V", r(), fp=FP["C1210"])
        s.flag_rail(rail, (395, y + 22))
        return u
    buck("U103", 70, "+5V_PORTS", "1k")
    buck("U104", 140, "+5V_TGT", "1k")
    s.note(["TPS54560B: non-synchronous, 4.5-60 V in, 5 A. fsw 400 kHz (RT 243k). FB 51.1k/9.76k -> 5.0 V.",
            "COMP values are placeholders (19.1k / 3.3n / 47p): run TI WEBENCH or the datasheet procedure before fab.",
            "Buck 1 feeds the USB ports, the FT231X, the relay coils and buck 3 (~4.6 A at 1.0 A/port); buck 2 is the 5 A target rail."],
           (240, 200), 1.3)

    # ---- buck 3: +3V3 from +5V_PORTS
    s.ic("Regulator_Switching", "TPS62823DLC", "U105", "TPS62823DLC", (240, 240),
         fp="Package_SON:Texas_VSON-HR-8_1.5x2mm_P0.5mm",
         nets={6: "U105_SW", 2: "U105_FB"}, power={7: "+5V_PORTS", 1: "+5V_PORTS", 3: "GND", 5: "GND"}, nc=[4, 8])
    r = Row(290, 232)
    s.two(s.L("470n/4A", r()), "U105_SW", "+3V3")
    s.decap("+5V_PORTS", "10u", r(), fp=FP["C0805"]); s.decap("+3V3", "22u", r(), fp=FP["C0805"]); s.decap("+3V3", "22u", r(), fp=FP["C0805"])
    s.two(s.R("100k", r()), "+3V3", "U105_FB"); s.pulldown("U105_FB", "22.1k", r())
    s.led_chain("+3V3", "GND", "470", AMBER, r())
    s.flag_rail("+3V3", (395, 262))
    return s


def mcu(project, num, page, sheet_path, plib):
    s = Sheet(project, "MCU: MK64FN1M0VLL12, USB device port, SWD, heartbeat", num, page, sheet_path)
    s.project_lib = plib
    s.note(["MCU", "MK64FN1M0VLL12 (LQFP-100). Clock: 50 MHz RMII REF_CLK from the KSZ8081 into EXTAL0, as on the FRDM-K64F.",
            "USB regulator: VREGIN fed only from J3 VBUS through D201, so the K64 cannot back-feed the target and the D+ pull-up",
            "disappears when the target is off. VOUT33 powers the transceiver. Pin allocation in docs/hardware-spec.md.",
            "Spare pins (PTA1, PTA2, PTB23, PTD7, PTE0-6, PTE26, ADC, DAC) are left no-connect."], (15, 15), 1.5)
    nets = {34: "SWCLK", 37: "SWDIO", 39: "RMII_RXER", 42: "RMII_RXD1", 43: "RMII_RXD0", 44: "RMII_CRS_DV", 45: "RMII_TXEN",
            46: "RMII_TXD0", 47: "RMII_TXD1", 53: "MDIO", 54: "MDC", 55: "TGT_IMON", 56: "PSU_PRESENT_N", 57: "PD_ATTACH_N",
            58: "PD_ALERT_N", 59: "PD_PROG_DET", 62: "K64_UART0_RX", 63: "K64_UART0_TX", 64: "HUB_RESET_N", 65: "HB_R",
            66: "HB_G", 67: "HB_B", 68: "PHY_INT_N", 70: "PORT1_EN", 71: "PORT2_EN", 72: "PORT3_EN", 73: "TGT_UART_RX",
            76: "TGT_UART_TX", 77: "PORT4_EN", 78: "PORT1_FAULT_N", 79: "PORT2_FAULT_N", 80: "PORT3_FAULT_N", 81: "PORT4_FAULT_N",
            82: "I2C1_SCL", 83: "I2C1_SDA", 84: "FTDI_EN", 85: "FTDI_FAULT_N", 86: "TGT_EN", 87: "TGT_FAULT_N", 90: "RLY1_DRV",
            91: "RLY2_DRV", 92: "RLY_PSU_DRV", 93: "GPIO1", 94: "GPIO2", 95: "GPIO3", 96: "GPIO4", 97: "GPIO5", 98: "GPIO6",
            99: "VBUS_SENSE", 31: "I2C0_SCL", 32: "I2C0_SDA",
            13: "K64_VREGIN", 12: "K64_VOUT33", 10: "K64_USB_DP", 11: "K64_USB_DM", 50: "RMII_CLK_50M",
            29: "K64_EXTAL32", 28: "K64_XTAL32", 52: "K64_RESET_N", 38: "K64_NMI_N"}
    power = {8: "+3V3", 40: "+3V3", 48: "+3V3", 61: "+3V3", 75: "+3V3", 89: "+3V3", 22: "+3V3A", 23: "+3V3A", 30: "+3V3",
             9: "GND", 41: "GND", 49: "GND", 60: "GND", 74: "GND", 88: "GND", 24: "GND", 25: "GND"}
    nc = [51, 14, 15, 16, 17, 18, 19, 20, 21, 26, 27, 35, 36, 69, 100, 1, 2, 3, 4, 5, 6, 7, 33]
    s.ic("sbcbb", "MK64FN1M0VLL12", "U201", "MK64FN1M0VLL12", (175, 150), fp="Package_QFP:LQFP-100_14x14mm_P0.5mm",
         nets=nets, power=power, nc=nc)
    # decoupling + analogue supply
    r = Row(25, 60)
    for _ in range(6): s.decap("+3V3", "100n", r())
    s.decap("+3V3", "10u", r(), fp=FP["C0805"])
    r = Row(25, 85)
    s.two(s.FB("600R@100MHz", r()), "+3V3", "+3V3A"); s.decap("+3V3A", "10u", r(), fp=FP["C0805"]); s.decap("+3V3A", "100n", r())
    s.flag_rail("+3V3A", (65, 100))
    # USB regulator
    r = Row(25, 120)
    s.two(s.D("Device", "D_Schottky", "BAT54", r(), rot=270, fp=FP["SOD123"]), "K64_VREGIN", "J3_VBUS")
    s.cap_to_gnd("K64_VREGIN", "2u2", r()); s.cap_to_gnd("K64_VOUT33", "2u2", r())
    s.flag_net("K64_VREGIN", (25, 138)); s.flag_net("J3_VBUS", (45, 138))
    # 32 kHz crystal (RTC), reset, NMI
    y = s.add("Device", "Crystal", "Y201", "32.768kHz", (35, 160), footprint=FP["XTAL2"])
    s.pin_label(y, "1", "K64_EXTAL32"); s.pin_label(y, "2", "K64_XTAL32")
    s.cap_to_gnd("K64_EXTAL32", "12p", (25, 175)); s.cap_to_gnd("K64_XTAL32", "12p", (45, 175))
    r = Row(25, 200)
    s.pullup("K64_RESET_N", "10k", r()); s.cap_to_gnd("K64_RESET_N", "1u", r()); s.pullup("K64_NMI_N", "10k", r())
    sw = s.add("Switch", "SW_Push", "SW201", "RESET", (40, 225), footprint=FP["SW"])
    s.pin_label(sw, "1", "K64_RESET_N"); s.pin_power(sw, "2", "GND")
    # SWD header
    s.ic("Connector", "Conn_ARM_JTAG_SWD_10", "J16", "SWD", (300, 60), fp=FP["SWD10"],
         nets={2: "SWDIO", 4: "SWCLK", 10: "K64_RESET_N"}, power={1: "+3V3", 3: "GND", 9: "GND"}, nc=[6, 7, 8])
    # J3: USB-C device port to the target (HID)
    s.ic("Connector", "USB_C_Receptacle_USB2.0_16P", "J3", "USB-C HID to target", (295, 125), fp=FP["USBC"],
         nets={"A5": "J3_CC1", "B5": "J3_CC2", "A6": "J3_DP", "B6": "J3_DP", "A7": "J3_DM", "B7": "J3_DM", "A4": "J3_VBUS"},
         power={"A1": "GND", "SH": "GND"}, nc=["A8", "B8"])
    r = Row(335, 110)
    s.pulldown("J3_CC1", "5.1k", r()); s.pulldown("J3_CC2", "5.1k", r())
    s.series("J3_VBUS", "VBUS_SENSE", "100k", r()); s.pulldown("VBUS_SENSE", "47k", r())
    s.ic("Power_Protection", "USBLC6-2SC6", "U202", "USBLC6-2SC6", (340, 155), fp=FP["SOT236"],
         nets={1: "J3_DP", 6: "K64_USB_DP", 3: "J3_DM", 4: "K64_USB_DM", 5: "J3_VBUS"}, power={2: "GND"})
    s.note(["J3: UFP, Rd 5.1k on both CC. VBUS is sense-only: D201 to VREGIN plus the 100k/47k divider. No board rail reaches J3."],
           (285, 185), 1.3)
    # heartbeat RGB (common anode)
    d = s.add("Device", "LED_RGBA", "D202", "RGB heartbeat", (300, 215), footprint=FP["RGB"])
    s.pin_power(d, "4", "+3V3")
    for pin, net in (("1", "HB_R"), ("2", "HB_G"), ("3", "HB_B")):
        s.pin_label(d, pin, net + "_K")
    r = Row(335, 205, 20.32)
    for net in ("HB_R", "HB_G", "HB_B"):
        s.series(net + "_K", net, "330", r())
    # I2C pull-ups (K64 side of both buses)
    r = Row(335, 245)
    for net in ("I2C0_SCL", "I2C0_SDA", "I2C1_SCL", "I2C1_SDA"):
        s.pullup(net, "4.7k", r())
    return s
