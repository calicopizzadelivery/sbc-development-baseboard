"""Target-facing I/O: console, GPIO/I2C breakout, signal relays, +5V_TGT eFuse, isolated PSU passthrough."""
from kit import Sheet, Row, FP

AMBER, GREEN, RED = "LED AMBER", "LED GREEN", "LED RED"


def target(project, num, page, sheet_path, plib):
    s = Sheet(project, "Target I/O: console, GPIO+I2C, relays, +5V_TGT eFuse, PSU passthrough", num, page, sheet_path)
    s.project_lib = plib
    s.note(["TARGET-FACING I/O",
            "VREF_TGT comes from the target on J13.1 / J15.1 and sets the level of every translator (TXB0104/TXB0108/TXS0102).",
            "OE pins follow VREF_TGT: with the target off the translators are high-impedance. J15 GPIO are push-pull (TXB).",
            "Relays boot de-energized (gate pull-downs). K701/K702 G6K-2F-Y: pole 1 used (COM 3, NC 2, NO 4); pole 2 unused.",
            "Passthrough J18 -> K703 (NO) -> J19 on nets PSU_VP / PSU_VOUT / PSU_GND that touch no board net. Opto only.",
            "K703 JW1FSN pad map COM=6 NO=4 NC=2: VERIFY against the Panasonic terminal drawing before fab."], (15, 15), 1.5)

    # ---- console J13 + TXB0104
    s.ic("Connector_Generic", "Conn_01x04", "J13", "Console VREF/TXD/RXD/GND", (40, 70), fp=FP["PH4"],
         nets={1: "VREF_TGT", 2: "J13_TXD", 3: "J13_RXD"}, power={4: "GND"})
    s.ic("Logic_LevelTranslator", "TXB0104PW", "U701", "TXB0104PW", (110, 75), fp="Package_SO:TSSOP-14_4.4x5mm_P0.65mm",
         nets={1: "VREF_TGT", 8: "VREF_TGT", 2: "J13_TXD", 13: "TGT_UART_TX", 3: "J13_RXD", 12: "TGT_UART_RX"},
         power={14: "+3V3", 7: "GND"}, nc=[4, 5, 6, 9, 10, 11])
    r = Row(25, 110)
    s.pulldown("VREF_TGT", "100k", r()); s.cap_to_gnd("VREF_TGT", "100n", r()); s.decap("+3V3", "100n", r())
    s.two(s.D("Device", "D_TVS", "PESD5V0S1UL", r(), rot=270, fp=FP["SOD523"]), "J13_TXD", "GND")
    s.two(s.D("Device", "D_TVS", "PESD5V0S1UL", r(), rot=270, fp=FP["SOD523"]), "J13_RXD", "GND")
    s.flag_net("VREF_TGT", (25, 130))

    # ---- GPIO / I2C breakout J15 + TXB0108 + TXS0102
    s.ic("Connector_Generic", "Conn_02x06_Odd_Even", "J15", "GPIO + I2C breakout", (40, 170), fp=FP["HDR2x6"],
         nets={1: "VREF_TGT", 3: "TGT_GPIO1", 4: "TGT_GPIO2", 5: "TGT_GPIO3", 6: "TGT_GPIO4", 7: "TGT_GPIO5", 8: "TGT_GPIO6",
               9: "J15_SDA", 10: "J15_SCL"}, power={2: "GND", 11: "GND", 12: "GND"})
    s.ic("Logic_LevelTranslator", "TXB0108PW", "U702", "TXB0108PW", (120, 170), fp="Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm",
         nets={2: "VREF_TGT", 10: "VREF_TGT", 1: "TGT_GPIO1", 3: "TGT_GPIO2", 4: "TGT_GPIO3", 5: "TGT_GPIO4", 6: "TGT_GPIO5", 7: "TGT_GPIO6",
               20: "GPIO1", 18: "GPIO2", 17: "GPIO3", 16: "GPIO4", 15: "GPIO5", 14: "GPIO6"},
         power={19: "+3V3", 11: "GND"}, nc=[8, 9, 12, 13])
    s.ic("Logic_LevelTranslator", "TXS0102DCU", "U703", "TXS0102DCU", (120, 235), fp="Package_SO:VSSOP-8_2.3x2mm_P0.5mm",
         nets={3: "VREF_TGT", 6: "VREF_TGT", 5: "J15_SCL", 4: "J15_SDA", 8: "I2C1_SCL", 1: "I2C1_SDA"}, power={7: "+3V3", 2: "GND"})
    r = Row(25, 215)
    s.cap_to_gnd("VREF_TGT", "100n", r()); s.decap("+3V3", "100n", r()); s.cap_to_gnd("VREF_TGT", "100n", r()); s.decap("+3V3", "100n", r())
    s.note(["TXS0102 instead of PCA9306: works with VREF_TGT equal to 3.3 V (PCA9306 needs VREF2 > VREF1). Range 1.65-3.6 V.",
            "Internal 10k pull-ups on both sides; K64-side 4.7k pull-ups are on the MCU sheet."], (20, 262), 1.3)

    # ---- signal relays K701 / K702 -> J11 / J12
    def relay(n, y):
        k = s.ic("Relay", "G6K-2", f"K70{n}", "G6K-2F-Y DC5", (230, y), fp="Relay_SMD:Relay_DPDT_Omron_G6K-2F-Y",
                 nets={8: f"RLY{n}_COIL", 3: f"J1{n}_COM", 2: f"J1{n}_NC", 4: f"J1{n}_NO"}, power={1: "+5V_PORTS"}, nc=[5, 6, 7])
        s.two(s.D("Diode", "1N4148W", "1N4148W", (200, y - 2), rot=270, fp=FP["SOD123"]), "+5V_PORTS", f"RLY{n}_COIL")
        s.led_chain("+5V_PORTS", f"RLY{n}_COIL", "2.2k", RED, (185, y - 10))
        q = s.Q("Transistor_FET", "2N7002", "2N7002", (215, y + 22))
        s.pin_label(q, "1", f"RLY{n}_GATE"); s.pin_power(q, "2", "GND"); s.pin_label(q, "3", f"RLY{n}_COIL")
        s.series(f"RLY{n}_DRV", f"RLY{n}_GATE", "1k", (185, y + 22)); s.pulldown(f"RLY{n}_GATE", "100k", (170, y + 10))
        s.ic("Connector_Generic", "Conn_01x03", f"J1{n}", "Relay COM/NO/NC", (290, y), fp=FP["PH3"],
             nets={1: f"J1{n}_COM", 2: f"J1{n}_NO", 3: f"J1{n}_NC"})
    relay(1, 60); relay(2, 110)

    # ---- +5V_TGT eFuse -> J14
    s.ic("Power_Management", "TPS26630RGE", "U704", "TPS26630RGE", (230, 185),
         fp="Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm_ThermalVias",
         nets={6: "TGT_UVLO", 9: "TGT_DVDT", 10: "TGT_ILIM", 12: "TGT_EN", 13: "TGT_IMON", 14: "TGT_FAULT_N"},
         power={1: "+5V_TGT", 2: "+5V_TGT", 5: "+5V_TGT", 7: "GND", 8: "GND", 11: "GND", 15: "GND", 25: "GND", 17: "+5V_TGT_OUT", 18: "+5V_TGT_OUT"},
         nc=[3, 4, 16, 19, 20, 21, 22, 23, 24])
    r = Row(170, 225)
    s.two(s.R("196k", r()), "+5V_TGT", "TGT_UVLO"); s.pulldown("TGT_UVLO", "75k", r())
    s.cap_to_gnd("TGT_DVDT", "10n", r()); s.pulldown("TGT_ILIM", "3.65k 1%", r())
    s.pullup("TGT_EN", "10k", r()); s.pullup("TGT_FAULT_N", "10k", r())
    s.pulldown("TGT_IMON", "20k", r()); s.cap_to_gnd("TGT_IMON", "1n", r())
    r = Row(170, 250)
    s.decap("+5V_TGT", "10u", r(), fp=FP["C0805"]); s.decap("+5V_TGT", "100n", r())
    s.decap("+5V_TGT_OUT", "22u", r(), fp=FP["C1206"]); s.led_chain("+5V_TGT_OUT", "GND", "1k", GREEN, r())
    s.ic("Connector_Generic", "Conn_01x02", "J14", "+5V_TGT out", (290, 185), fp=FP["PH2"], power={1: "+5V_TGT_OUT", 2: "GND"})
    s.note(["TPS26630: ILIM 3.65k -> ~5 A (3k = 6 A, 4.02k = 4.5 A). UVLO 196k/75k -> 4.3 V. OVP/MODE/PGTH to GND (defaults, latch-off).",
            "IMON 20k -> 2.8 V at 5 A into K64 ADC (PTB2). SHDN = TGT_EN, pulled up: boots ON."], (165, 272), 1.3)

    # ---- isolated PSU passthrough J18 -> K703 -> J19, with opto presence
    s.ic("Connector_Generic", "Conn_01x02", "J18", "PSU in (isolated)", (330, 60), fp=FP["PH2"], nets={1: "PSU_VP", 2: "PSU_GND"})
    s.ic("Connector_Generic", "Conn_01x02", "J19", "PSU out (isolated)", (400, 60), fp=FP["PH2"], nets={1: "PSU_VOUT", 2: "PSU_GND"})
    s.ic("sbcbb", "JW1FSN", "K703", "JW1FSN-DC5V", (365, 95), fp="Relay_THT:Relay_SPDT_Panasonic_JW1_FormC",
         nets={8: "RLY3_COIL", 6: "PSU_VP", 4: "PSU_VOUT"}, power={1: "+5V_PORTS"}, nc=[2])
    s.two(s.D("Diode", "1N4148W", "1N4148W", (335, 100), rot=270, fp=FP["SOD123"]), "+5V_PORTS", "RLY3_COIL")
    s.led_chain("+5V_PORTS", "RLY3_COIL", "2.2k", RED, (320, 92))
    q = s.Q("Transistor_FET", "AO3400A", "AO3400A", (350, 125))
    s.pin_label(q, "1", "RLY3_GATE"); s.pin_power(q, "2", "GND"); s.pin_label(q, "3", "RLY3_COIL")
    s.series("RLY_PSU_DRV", "RLY3_GATE", "1k", (320, 125)); s.pulldown("RLY3_GATE", "100k", (305, 110))
    u = s.ic("Isolator", "LTV-817", "U705", "LTV-817", (365, 160), fp=FP["DIP4"],
             nets={1: "PSU_OPTO_A", 2: "PSU_GND", 4: "PSU_PRESENT_N"}, power={3: "GND"})
    s.series("PSU_VP", "PSU_OPTO_R", "1.8k", (320, 150), fp=FP["R1206"]); s.series("PSU_OPTO_R", "PSU_OPTO_A", "1.8k", (335, 150), fp=FP["R1206"])
    s.two(s.D("Diode", "1N4148W", "1N4148W", (320, 170), rot=270, fp=FP["SOD123"]), "PSU_OPTO_A", "PSU_GND")
    s.pullup("PSU_PRESENT_N", "10k", (395, 150))
    s.note(["Opto LED: 2x1.8k 1206 in series, 1 mA at 5 V, 8 mA / 0.12 W each at 30 V. D708 protects a reversed PSU.",
            "PSU_PRESENT_N is active low at the K64. No LED on the passthrough itself."], (300, 195), 1.3)
    return s
