"""Ethernet, USB hub, FTDI and DAPLink sheets."""
from kit import Sheet, Row, FP

AMBER, GREEN, RED = "LED AMBER", "LED GREEN", "LED RED"


def ethernet(project, num, page, sheet_path, plib):
    s = Sheet(project, "Ethernet: KSZ8081RNA RMII PHY and magjack", num, page, sheet_path)
    s.project_lib = plib
    s.note(["ETHERNET", "KSZ8081RNA in RMII 25 MHz mode (its power-up default): 25 MHz crystal on XI/XO, REF_CLK outputs 50 MHz",
            "to the K64 EXTAL0 through R301. This is the FRDM-K64F arrangement (Zephyr: microchip,interface-type = rmii-25MHz).",
            "PHY address 0 (pins 15/16 internal pull-downs; the MAC does not drive them). RXER needs the external pull-down.",
            "Transformer centre taps go to 0.1 uF each, not to a supply (datasheet 11.x). Bob Smith: 4x75R to 1 nF/2 kV."], (15, 15), 1.5)
    s.ic("Interface_Ethernet", "KSZ8081RNA", "U301", "KSZ8081RNA", (150, 110), fp="Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm",
         nets={1: "PHY_1V2", 3: "ETH_RXM", 4: "ETH_RXP", 5: "ETH_TXM", 6: "ETH_TXP", 7: "PHY_XO", 8: "PHY_XI", 9: "PHY_REXT",
               10: "MDIO", 11: "MDC", 12: "RMII_RXD1", 13: "RMII_RXD0", 15: "RMII_CRS_DV", 16: "PHY_REFCLK", 17: "RMII_RXER",
               18: "PHY_INT_N", 19: "RMII_TXEN", 20: "RMII_TXD0", 21: "RMII_TXD1", 23: "ETH_LED_LINK_N", 24: "K64_RESET_N"},
         power={2: "+3V3A_PHY", 14: "+3V3", 22: "GND", 25: "GND"})
    r = Row(45, 60, 17.78)
    s.series("PHY_REFCLK", "RMII_CLK_50M", "33", r()); s.pulldown("PHY_REXT", "6.49k 1%", r()); s.pullup("MDIO", "4.7k", r())
    s.pulldown("RMII_RXER", "10k", r()); s.pullup("PHY_INT_N", "1k", r())
    r = Row(25, 90)
    s.cap_to_gnd("PHY_1V2", "2u2", r()); s.cap_to_gnd("PHY_1V2", "100n", r())
    s.two(s.FB("600R@100MHz", r()), "+3V3", "+3V3A_PHY"); s.decap("+3V3A_PHY", "22u", r(), fp=FP["C0805"]); s.decap("+3V3A_PHY", "100n", r())
    s.decap("+3V3", "100n", r())
    s.flag_rail("+3V3A_PHY", (25, 110))
    y = s.add("Device", "Crystal_GND24", "Y301", "25MHz", (45, 140), footprint=FP["XTAL4"])
    s.pin_label(y, "1", "PHY_XI"); s.pin_label(y, "3", "PHY_XO"); s.pin_power(y, "2", "GND")
    s.cap_to_gnd("PHY_XI", "22p", (25, 160)); s.cap_to_gnd("PHY_XO", "22p", (60, 160))
    s.note(["Crystal: 25 MHz +/-50 ppm, CL 16 pF typ (datasheet) -> 22 pF each, trim at bring-up."], (20, 180), 1.3)
    # magjack
    s.ic("Connector", "RJ45_Kycon_G7LX-A88S7-BP-GY", "J10", "RJ45 magjack 10/100", (300, 100), fp=FP["RJ45"],
         nets={1: "ETH_TXP", 2: "ETH_TXM", 3: "ETH_RXP", 6: "ETH_RXM", 4: "ETH_TCT", 7: "ETH_RCT", 5: "ETH_BS1", 8: "ETH_BS2",
               9: "ETH_BS4", 10: "ETH_BS3", 12: "ETH_LEDY_A", 13: "ETH_LED_LINK_N", 14: "ETH_LEDG_A"},
         power={11: "GND", "SH": "GND"})
    r = Row(230, 150, 20.32)
    s.cap_to_gnd("ETH_TCT", "100n", r()); s.cap_to_gnd("ETH_RCT", "100n", r())
    for n in ("ETH_BS1", "ETH_BS2", "ETH_BS3", "ETH_BS4"):
        s.series(n, "ETH_BS", "75", r())
    s.cap_to_gnd("ETH_BS", "1n/2kV", r(), fp=FP["C1206"])
    r = Row(230, 180, 20.32)
    s.series("+3V3", "ETH_LEDG_A", "330", r()); s.series("+3V3", "ETH_LEDY_A", "330", r())
    s.note(["Green LED = link/activity (PHY LED0, active low). Yellow LED = PHY powered (cathode to GND)."], (240, 200), 1.3)
    return s


def hub(project, num, page, sheet_path, plib):
    s = Sheet(project, "USB hub: USB2517, upstream J1, four switched USB-A ports, FT231X switch", num, page, sheet_path)
    s.project_lib = plib
    s.note(["USB HUB", "USB2517 strap-configured (CFG_SEL=000), no firmware needed for the USB tree to come up.",
            "Port map: 1 = DAPLink, 2 = FT231X, 3 = disabled (DN3 pulled up), 4..7 = USB-A PORT1..PORT4 (J4: ports 4,5; J5: ports 6,7).",
            "NON_REM=11 (pin 40 up, pin 45 up) marks ports 1-3 non-removable and LOCAL_PWR high reports self-powered.",
            "LED_A/B pins pulled down: PRT_SWP normal polarity, BOOST=00, GANG_EN=0 (individual over-current).",
            "Port power is switched by TPS2553 under K64 GPIO (boot ON via pull-ups); PRTPWR outputs unused; /FAULT feeds OCSx_N."], (15, 15), 1.5)
    s.ic("Connector", "USB_C_Receptacle_USB2.0_16P", "J1", "USB-C upstream", (40, 70), fp=FP["USBC"],
         nets={"A5": "J1_CC1", "B5": "J1_CC2", "A6": "J1_DP", "B6": "J1_DP", "A7": "J1_DM", "B7": "J1_DM", "A4": "J1_VBUS"},
         power={"A1": "GND", "SH": "GND"}, nc=["A8", "B8"])
    r = Row(25, 115)
    s.pulldown("J1_CC1", "5.1k", r()); s.pulldown("J1_CC2", "5.1k", r())
    s.series("J1_VBUS", "HUB_VBUS_DET", "10k", r()); s.pulldown("HUB_VBUS_DET", "22k", r())
    s.ic("Power_Protection", "USBLC6-2SC6", "U401", "USBLC6-2SC6", (40, 150), fp=FP["SOT236"],
         nets={1: "J1_DP", 6: "USBUP_DP", 3: "J1_DM", 4: "USBUP_DM", 5: "J1_VBUS"}, power={2: "GND"})
    s.flag_net("J1_VBUS", (25, 175))
    nets = {59: "USBUP_DP", 58: "USBUP_DM", 44: "HUB_VBUS_DET", 61: "HUB_XTAL1", 60: "HUB_XTAL2", 43: "HUB_RESET_N", 63: "HUB_RBIAS",
            13: "HUB_CFG_SEL2", 42: "HUB_CFG_SEL1", 41: "HUB_CFG_SEL0", 40: "HUB_NON_REM1", 45: "HUB_LOCAL_PWR",
            25: "HUB_VDD18", 62: "HUB_VDD18PLL",
            2: "HUB_DN1_DP", 1: "HUB_DN1_DM", 4: "HUB_DN2_DP", 3: "HUB_DN2_DM", 7: "HUB_DN3_DP", 6: "HUB_DN3_DM",
            9: "HUB_DN4_DP", 8: "HUB_DN4_DM", 12: "HUB_DN5_DP", 11: "HUB_DN5_DM", 54: "HUB_DN6_DP", 53: "HUB_DN6_DM",
            56: "HUB_DN7_DP", 55: "HUB_DN7_DM",
            27: "FTDI_FAULT_N", 21: "PORT1_FAULT_N", 35: "PORT2_FAULT_N", 38: "PORT3_FAULT_N", 37: "PORT4_FAULT_N",
            51: "HUB_LEDA1", 49: "HUB_LEDA2", 47: "HUB_LEDA3", 33: "HUB_LEDA4", 31: "HUB_LEDA5", 17: "HUB_LEDA6", 15: "HUB_LEDA7",
            50: "HUB_LEDB1", 48: "HUB_LEDB2", 34: "HUB_LEDB3"}
    power = {19: "GND", 46: "+3V3", 24: "+3V3", 64: "+3V3", 5: "+3V3", 10: "+3V3", 52: "+3V3", 57: "+3V3", 65: "GND"}
    nc = [29, 26, 23, 20, 30, 39, 36, 28, 22, 32, 18, 16, 14]
    s.ic("sbcbb", "USB2517", "U402", "USB2517", (170, 130), fp="Package_DFN_QFN:QFN-64-1EP_9x9mm_P0.5mm_EP7.15x7.15mm",
         nets=nets, power=power, nc=nc)
    r = Row(25, 200)
    for n in ("HUB_CFG_SEL2", "HUB_CFG_SEL1", "HUB_CFG_SEL0"): s.pulldown(n, "10k", r())
    for n in ("HUB_NON_REM1", "HUB_LOCAL_PWR"): s.pullup(n, "10k", r())
    s.pulldown("HUB_RBIAS", "12.0k 1%", r()); s.pullup("HUB_RESET_N", "10k", r()); s.cap_to_gnd("HUB_RESET_N", "1u", r())
    s.pullup("HUB_DN3_DP", "10k", r()); s.pullup("HUB_DN3_DM", "10k", r())
    r = Row(25, 225)
    for n in ("HUB_LEDA1", "HUB_LEDA2", "HUB_LEDA3", "HUB_LEDA4", "HUB_LEDA5", "HUB_LEDA6", "HUB_LEDA7", "HUB_LEDB1", "HUB_LEDB2", "HUB_LEDB3"):
        s.pulldown(n, "10k", r())
    r = Row(25, 250)
    for _ in range(7): s.decap("+3V3", "100n", r())
    s.decap("+3V3", "4u7", r(), fp=FP["C0805"])
    s.cap_to_gnd("HUB_VDD18", "1u", r()); s.cap_to_gnd("HUB_VDD18", "100n", r()); s.cap_to_gnd("HUB_VDD18PLL", "1u", r()); s.cap_to_gnd("HUB_VDD18PLL", "100n", r())
    y = s.add("Device", "Crystal_GND24", "Y401", "24MHz", (165, 255), footprint=FP["XTAL4"])
    s.pin_label(y, "1", "HUB_XTAL1"); s.pin_label(y, "3", "HUB_XTAL2"); s.pin_power(y, "2", "GND")
    s.cap_to_gnd("HUB_XTAL1", "33p", (180, 270)); s.cap_to_gnd("HUB_XTAL2", "33p", (190, 270))
    # port switches + ESD + connectors
    def port(n, hubport, x, y):
        s.ic("sbcbb", "TPS2553DBV", f"U40{2+n}", "TPS2553DBV", (x, y), fp=FP["SOT236"],
             nets={3: f"PORT{n}_EN", 5: f"PORT{n}_ILIM", 6: f"PORT{n}_VBUS", 4: f"PORT{n}_FAULT_N"}, power={1: "+5V_PORTS", 2: "GND"})
        r = Row(x - 20, y + 18)
        s.pulldown(f"PORT{n}_ILIM", "23.7k", r()); s.pullup(f"PORT{n}_EN", "10k", r()); s.pullup(f"PORT{n}_FAULT_N", "10k", r())
        s.decap("+5V_PORTS", "100n", r()); s.cap_to_gnd(f"PORT{n}_VBUS", "22u", r(), fp=FP["C1206"])
        s.led_chain(f"PORT{n}_VBUS", "GND", "1k", GREEN, r())
        s.ic("Power_Protection", "USBLC6-2SC6", f"U4{7+n:02d}", "USBLC6-2SC6", (x + 90, y), fp=FP["SOT236"],
             nets={1: f"HUB_DN{hubport}_DP", 6: f"PORT{n}_DP", 3: f"HUB_DN{hubport}_DM", 4: f"PORT{n}_DM", 5: f"PORT{n}_VBUS"}, power={2: "GND"})
    port(1, 4, 240, 50); port(2, 5, 240, 100); port(3, 6, 240, 150); port(4, 7, 240, 200)
    s.ic("Connector", "USB_A_Stacked", "J4", "2x USB-A (PORT1, PORT2)", (385, 75), fp=FP["USBA2"],
         nets={1: "PORT1_VBUS", 3: "PORT1_DP", 2: "PORT1_DM", 5: "PORT2_VBUS", 7: "PORT2_DP", 6: "PORT2_DM"}, power={4: "GND", 8: "GND", "SH": "GND"})
    s.ic("Connector", "USB_A_Stacked", "J5", "2x USB-A (PORT3, PORT4)", (385, 175), fp=FP["USBA2"],
         nets={1: "PORT3_VBUS", 3: "PORT3_DP", 2: "PORT3_DM", 5: "PORT4_VBUS", 7: "PORT4_DP", 6: "PORT4_DM"}, power={4: "GND", 8: "GND", "SH": "GND"})
    # FT231X switch (hub port 2 power), under its own verb, outside PORT ALL
    s.ic("sbcbb", "TPS2553DBV", "U407", "TPS2553DBV", (240, 250), fp=FP["SOT236"],
         nets={3: "FTDI_EN", 5: "FTDI_ILIM", 6: "FTDI_VBUS", 4: "FTDI_FAULT_N"}, power={1: "+5V_PORTS", 2: "GND"})
    r = Row(220, 268)
    s.pulldown("FTDI_ILIM", "23.7k", r()); s.pullup("FTDI_EN", "10k", r()); s.pullup("FTDI_FAULT_N", "10k", r())
    s.decap("+5V_PORTS", "100n", r()); s.cap_to_gnd("FTDI_VBUS", "10u", r(), fp=FP["C0805"]); s.led_chain("FTDI_VBUS", "GND", "1k", GREEN, r())
    s.note(["TPS2553 ILIM 23.7k -> ~1.1 A (datasheet: 20k -> 1.3 A typ, 15k -> 1.7 A). EN/FAULT pull-ups set the boot-ON state."], (240, 290), 1.3)
    return s


def ftdi(project, num, page, sheet_path, plib):
    s = Sheet(project, "FTDI: FT231X on hub port 2, standard 6-pin FTDI header", num, page, sheet_path)
    s.project_lib = plib
    s.note(["FTDI HEADER J9", "Pinout = TTL-232R / SparkFun: 1 GND (blk)  2 CTS (brn)  3 VCC (red)  4 TXD (org)  5 RXD (yel)  6 RTS/DTR (grn).",
            "TXD/RXD named from the FT231X side: TXD drives the target's RX. 3.3 V levels only; 1.8 V consoles use J13.",
            "JP501: pin 6 = DTR# (bridge C-B, default) or RTS# (bridge C-A). JP502: pin 3 VCC from 3V3OUT (50 mA), open by default.",
            "VCC comes from the TPS2553 on the hub sheet (FTDI_VBUS): FTDI CYCLE power-cycles the bridge without a replug.",
            "CBUS defaults: CBUS1 = RXLED#, CBUS2 = TXLED# (factory MTP); change with FT_PROG if ever needed."], (15, 15), 1.5)
    s.ic("Interface_USB", "FT231XS", "U501", "FT231XS", (150, 90), fp="Package_SO:SSOP-20_3.9x8.7mm_P0.635mm",
         nets={20: "FTDI_TXD", 4: "J9_RXD", 9: "J9_CTS", 2: "FTDI_RTS_N", 1: "FTDI_DTR_N", 17: "FTDI_RXLED_N", 10: "FTDI_TXLED_N",
               11: "HUB_DN2_DP", 12: "HUB_DN2_DM", 13: "FTDI_3V3", 14: "FTDI_RESET_N", 3: "FTDI_3V3"},
         power={15: "FTDI_VBUS", 6: "GND", 16: "GND"}, nc=[5, 7, 8, 18, 19])
    r = Row(25, 60)
    s.decap("FTDI_VBUS", "10u", r(), fp=FP["C0805"]); s.decap("FTDI_VBUS", "100n", r()); s.cap_to_gnd("FTDI_3V3", "100n", r())
    s.pullup("FTDI_RESET_N", "10k", r(), rail="FTDI_3V3")
    r = Row(240, 60)
    s.series("FTDI_TXD", "J9_TXD", "470", r())
    jp = s.add("Jumper", "SolderJumper_3_Open", "JP501", "RTS/DTR", (260, 85), footprint=FP["JP3"])
    s.pin_label(jp, "1", "FTDI_RTS_N"); s.pin_label(jp, "3", "FTDI_DTR_N"); s.pin_label(jp, "2", "FTDI_PIN6")
    s.series("FTDI_PIN6", "J9_PIN6", "470", (240, 105))
    jp2 = s.add("Jumper", "SolderJumper_2_Open", "JP502", "VCC to J9", (260, 125), footprint=FP["JP2"])
    s.pin_label(jp2, "1", "FTDI_3V3"); s.pin_label(jp2, "2", "J9_VCC")
    s.ic("Connector_Generic", "Conn_01x06", "J9", "FTDI header", (330, 90), fp=FP["HDR6"],
         nets={2: "J9_CTS", 3: "J9_VCC", 4: "J9_TXD", 5: "J9_RXD", 6: "J9_PIN6"}, power={1: "GND"})
    r = Row(240, 160)
    s.led_chain("FTDI_3V3", "FTDI_TXLED_N", "470", GREEN, r()); s.led_chain("FTDI_3V3", "FTDI_RXLED_N", "470", GREEN, r())
    for n in ("J9_TXD", "J9_RXD", "J9_CTS", "J9_PIN6"):
        s.two(s.D("Device", "D_TVS", "PESD5V0S1UL", r(), rot=270, fp=FP["SOD523"]), n, "GND")
    return s


def daplink(project, num, page, sheet_path, plib):
    s = Sheet(project, "DAPLink: MK20DX128VFM5 on hub port 1, SWD + CDC + MSD to the K64", num, page, sheet_path)
    s.project_lib = plib
    s.note(["DAPLINK", "MK20DX128VFM5 running DAPLink (k20dx HIC), powered from +5V_PORTS through its own USB regulator (VOUT33 -> VDD).",
            "Pin use follows the DAPLink k20dx HIC: PTC5 = SWCLK, PTC6 = SWDIO, PTB1 = nRESET to the K64, PTD4 = LED,",
            "UART1 PTC3/PTC4 bridges to the K64 UART0 (CDC console). Verify against DAPLink source/hic_hal/freescale/k20dx/IO_Config.h.",
            "J601 programs the K20 itself (bootloader + DAPLink). SW601 held at power-up enters DAPLink maintenance mode."], (15, 15), 1.5)
    s.ic("MCU_NXP_Kinetis", "MK20DX128VFM5", "U601", "MK20DX128VFM5", (150, 110), fp="Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm",
         nets={3: "HUB_DN1_DP", 4: "HUB_DN1_DM", 5: "K20_3V3", 1: "K20_3V3", 7: "K20_3V3", 11: "K20_3V3", 12: "DAP_SWCLK", 15: "DAP_SWDIO",
               16: "DAP_NMI_N", 17: "K20_EXTAL", 18: "K20_XTAL", 19: "DAP_RESET_N", 21: "K64_RESET_N", 24: "K64_UART0_TX",
               25: "K64_UART0_RX", 26: "SWCLK", 27: "SWDIO", 29: "DAP_LED_N"},
         power={6: "+5V_PORTS", 2: "GND", 8: "GND", 33: "GND"}, nc=[9, 10, 13, 14, 20, 22, 23, 28, 30, 31, 32])
    r = Row(25, 60)
    s.decap("+5V_PORTS", "2u2", r()); s.cap_to_gnd("K20_3V3", "2u2", r()); s.cap_to_gnd("K20_3V3", "100n", r()); s.cap_to_gnd("K20_3V3", "100n", r())
    s.pullup("DAP_RESET_N", "10k", r(), rail="K20_3V3"); s.cap_to_gnd("DAP_RESET_N", "100n", r()); s.pullup("DAP_NMI_N", "10k", r(), rail="K20_3V3")
    sw = s.add("Switch", "SW_Push", "SW601", "DAP RESET", (40, 95), footprint=FP["SW"])
    s.pin_label(sw, "1", "DAP_RESET_N"); s.pin_power(sw, "2", "GND")
    y = s.add("Device", "Crystal_GND24", "Y601", "8MHz", (45, 130), footprint=FP["XTAL4"])
    s.pin_label(y, "1", "K20_EXTAL"); s.pin_label(y, "3", "K20_XTAL"); s.pin_power(y, "2", "GND")
    s.cap_to_gnd("K20_EXTAL", "18p", (25, 150)); s.cap_to_gnd("K20_XTAL", "18p", (60, 150))
    s.led_chain("K20_3V3", "DAP_LED_N", "470", GREEN, (90, 150))
    s.ic("Connector", "Conn_ARM_JTAG_SWD_10", "J601", "SWD (K20)", (280, 80), fp=FP["SWD10"],
         nets={2: "DAP_SWDIO", 4: "DAP_SWCLK", 10: "DAP_RESET_N", 1: "K20_3V3"}, power={3: "GND", 9: "GND"}, nc=[6, 7, 8])
    return s
