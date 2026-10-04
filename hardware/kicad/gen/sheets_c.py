"""Target-facing I/O (console, GPIO/I2C, +5V_TGT eFuse) and the relays & isolated passthrough."""
from kit import Sheet, FP
from fanout import fan, chain, L, P, Ser, Pull, PullLED, Tag, Flag, Conn, End, To, BusEnd, bus_join, rail_bus, decap_row, join_pins, top_caps, top_bus
from sheets_a import flags, TVS

AMBER, GREEN, RED = "LED AMBER", "LED GREEN", "LED RED"


def target(project, num, page, sheet_path, plib):
    s = Sheet(project, "Target I/O: console, GPIO + I2C breakout, +5V_TGT eFuse", num, page, sheet_path)
    s.project_lib = plib
    s.note(["TARGET-FACING I/O",
            "VREF_TGT comes from the target on J13.1 / J15.1 and sets the level of every translator (TXB0104/TXB0108/TXS0102).",
            "OE pins follow VREF_TGT: with the target off the translators are high-impedance. J15 GPIO are push-pull (TXB).",
            "TXS0102 instead of PCA9306: works with VREF_TGT equal to 3.3 V (PCA9306 needs VREF2 > VREF1). Range 1.65-3.6 V.",
            "TPS26630: ILIM 3.65k -> ~5 A, UVLO 196k/75k -> 4.3 V, OVP/MODE/PGTH to GND (latch-off). IMON 20k -> 2.8 V at 5 A into PTB2."], (15, 15), 1.5)
    j13 = s.add("Connector_Generic", "Conn_01x04", "J13", "Console VREF/TXD/RXD/GND", (40, 68), 180, footprint=FP["PH4"])
    u1 = s.add("Logic_LevelTranslator", "TXB0104PW", "U701", "TXB0104PW", (150, 72), footprint="Package_SO:TSSOP-14_4.4x5mm_P0.65mm")
    j15 = s.add("Connector_Generic", "Conn_02x06_Odd_Even", "J15", "GPIO + I2C breakout", (40, 170), footprint=FP["HDR2x6"])
    u2 = s.add("Logic_LevelTranslator", "TXB0108PW", "U702", "TXB0108PW", (160, 165), footprint="Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm")
    u3 = s.add("Logic_LevelTranslator", "TXS0102DCU", "U703", "TXS0102DCU", (160, 235), footprint="Package_SO:VSSOP-8_2.3x2mm_P0.5mm")
    u4 = s.add("Power_Management", "TPS26630RGE", "U704", "TPS26630RGE", (290, 200), footprint="Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm_ThermalVias")
    j14 = s.add("Connector_Generic", "Conn_01x02", "J14", "+5V_TGT out", (375, 190), footprint=FP["PH2"])
    for pin in (4, 5, 6, 9, 10, 11): s.pin_nc(u1, str(pin))
    for pin in (8, 9, 12, 13): s.pin_nc(u2, str(pin))
    for pin in (3, 4, 16, 19, 20, 21, 22, 23, 24): s.pin_nc(u4, str(pin))
    # console
    fan(s, j13, {1: chain(Flag(None), Pull("GND", "R", "100k", None), Pull("GND", "C", "100n", None), P("VREF_TGT")), 4: P("GND"),
                 2: End("j13_txd"), 3: End("j13_rxd")})
    fan(s, u1, {2: chain(TVS(), To("j13_txd")), 3: chain(TVS(), To("j13_rxd")), 8: P("VREF_TGT"),
                13: L("TGT_UART_TX"), 12: L("TGT_UART_RX"), 7: P("GND")})
    top_caps(s, u1, 1, [("100n", None)], height=7.62, sx=-1, up=True, rail="VREF_TGT")
    top_caps(s, u1, 14, [("100n", None)], height=7.62, sx=1, up=True, rail="+3V3")
    # GPIO + I2C breakout (labelled, as a breakout header is)
    fan(s, j15, {1: P("VREF_TGT"), 2: P("GND"), 3: L("TGT_GPIO1"), 4: L("TGT_GPIO2"), 5: L("TGT_GPIO3"), 6: L("TGT_GPIO4"),
                 7: L("TGT_GPIO5"), 8: L("TGT_GPIO6"), 9: L("J15_SDA"), 10: L("J15_SCL"), 11: P("GND"), 12: P("GND")})
    fan(s, u2, {1: L("TGT_GPIO1"), 3: L("TGT_GPIO2"), 4: L("TGT_GPIO3"), 5: L("TGT_GPIO4"), 6: L("TGT_GPIO5"), 7: L("TGT_GPIO6"), 10: P("VREF_TGT"),
                20: L("GPIO1"), 18: L("GPIO2"), 17: L("GPIO3"), 16: L("GPIO4"), 15: L("GPIO5"), 14: L("GPIO6"),
                11: P("GND")})
    top_caps(s, u2, 2, [("100n", None)], height=7.62, sx=-1, up=True, rail="VREF_TGT")
    top_caps(s, u2, 19, [("100n", None)], height=7.62, sx=1, up=True, rail="+3V3")
    fan(s, u3, {5: L("J15_SCL"), 4: L("J15_SDA"), 6: P("VREF_TGT"), 8: L("I2C1_SCL"), 1: L("I2C1_SDA"), 2: P("GND")})
    top_caps(s, u3, 3, [("100n", None)], height=7.62, sx=-1, up=True, rail="VREF_TGT")
    top_caps(s, u3, 7, [("100n", None)], height=7.62, sx=1, up=True, rail="+3V3")
    # +5V_TGT eFuse
    fan(s, u4, {1: chain(Pull("GND", "C", "100n", None), Pull("GND", "C", "10u", None, fp=FP["C0805"]), P("+5V_TGT")),
                6: chain(Pull("GND", "R", "75k", None), Ser("R", "196k", None), P("+5V_TGT")),
                7: P("GND"), 11: P("GND"), 12: chain(Pull("+3V3", "R", "10k", None), L("TGT_EN")),
                5: P("+5V_TGT"), 8: P("GND"), 25: P("GND"),
                17: chain(Pull("GND", "C", "22u", None, fp=FP["C1206"]), PullLED(GREEN, "1k", None), Conn(j14, 1)),
                15: P("GND"), 13: chain(Pull("GND", "C", "1n", None), Pull("GND", "R", "20k", None), L("TGT_IMON")),
                14: chain(Pull("+3V3", "R", "10k", None), L("TGT_FAULT_N")),
                9: chain(Ser("C", "10n", None), P("GND")), 10: chain(Ser("R", "3.65k 1%", None), P("GND"))})
    fan(s, j14, {2: P("GND")})
    return s


def relays(project, num, page, sheet_path, plib):
    s = Sheet(project, "Relays: two SPDT signal relays, isolated PSU passthrough", num, page, sheet_path)
    s.project_lib = plib
    s.note(["RELAYS AND PASSTHROUGH",
            "K801/K802 G6K-2F-Y: pole 1 used (COM 3, NC 2, NO 4), pole 2 unused. Coils boot de-energized (gate pull-downs).",
            "Red LEDs sit across each coil and show the energized state. Flyback 1N4148W on every coil.",
            "Passthrough J18 -> K803 (NO contact) -> J19 on nets PSU_VP / PSU_VOUT / PSU_GND that touch no board net: PSU_GND is its own ground.",
            "Only the optocoupler's emitter sits across the passthrough, sized for 5-30 V. No indicator LED there.",
            "K803 JW1FSN pad map COM=6 NO=4 NC=2: VERIFY against the Panasonic terminal drawing before fab."], (15, 15), 1.5)
    for n, y in ((1, 75), (2, 150)):
        k = s.add("Relay", "G6K-2", f"K80{n}", "G6K-2F-Y DC5", (150, y), footprint="Relay_SMD:Relay_DPDT_Omron_G6K-2F-Y")
        jx = s.add("Connector_Generic", "Conn_01x03", f"J1{n}", "Relay COM/NO/NC", (230, y), footprint=FP["PH3"])
        q = s.Q("Transistor_FET", "2N7002", "2N7002", (95, y + 42))
        for pin in (5, 6, 7): s.pin_nc(k, str(pin))
        # coil: pin 1 (top-left) to +5V_PORTS; the switched end (pin 8, bottom-left) runs left with
        # the flyback diode and the coil LED hanging up to the rail, then down to the FET drain
        fan(s, k, {1: P("+5V_PORTS"),
                   8: chain(Pull("+5V_PORTS", ("Diode", "1N4148W", "1"), "1N4148W", None, fp=FP["SOD123"]), PullLED(RED, "2.2k", None, rail="+5V_PORTS"), Conn(q, 3)),
                   2: Conn(jx, 3), 4: Conn(jx, 2), 3: Conn(jx, 1)}, side_dir={8: -1})
        fan(s, q, {1: chain(Pull("GND", "R", "100k", None), Ser("R", "1k", None), L(f"RLY{n}_DRV")), 2: P("GND")})
    # passthrough
    k3 = s.add("sbcbb", "JW1FSN", "K803", "JW1FSN-DC5V", (150, 235), footprint="Relay_THT:Relay_SPDT_Panasonic_JW1_FormC")
    q3 = s.Q("Transistor_FET", "AO3400A", "AO3400A", (70, 262))
    j18 = s.add("Connector_Generic", "Conn_01x02", "J18", "PSU in (isolated)", (300, 225), footprint=FP["PH2"])
    j19 = s.add("Connector_Generic", "Conn_01x02", "J19", "PSU out (isolated)", (300, 250), footprint=FP["PH2"])
    opto = s.add("Isolator", "LTV-817", "U801", "LTV-817", (230, 270), 180, footprint=FP["DIP4"])
    s.pin_nc(k3, "2")
    fan(s, k3, {1: P("+5V_PORTS"),
                8: chain(Pull("+5V_PORTS", ("Diode", "1N4148W", "1"), "1N4148W", None, fp=FP["SOD123"]), PullLED(RED, "2.2k", None, rail="+5V_PORTS"), Conn(q3, 3)),
                6: Conn(j18, 1), 4: Conn(j19, 1)})
    fan(s, q3, {1: chain(Pull("GND", "R", "100k", None), Ser("R", "1k", None), L("RLY_PSU_DRV")), 2: P("GND")})
    fan(s, j18, {2: P("PSU_GND")}); fan(s, j19, {2: P("PSU_GND")})
    fan(s, opto, {1: chain(Pull("PSU_GND", ("Diode", "1N4148W", "1"), "1N4148W", None, fp=FP["SOD123"]), Ser("R", "1.8k", None, fp=FP["R1206"]), Ser("R", "1.8k", None, fp=FP["R1206"]), Conn(j18, 1)),
                  2: P("PSU_GND"), 4: chain(Pull("+3V3", "R", "10k", None), L("PSU_PRESENT_N")), 3: P("GND")})
    flags(s, ["PSU_GND"], (25, 276))
    s.note(["Opto LED: 2x1.8k 1206 in series, 1 mA at 5 V, 8 mA / 0.12 W each at 30 V. The antiparallel 1N4148W protects a reversed PSU.",
            "PSU_PRESENT_N is active low at the K64."], (150, 280), 1.3)
    return s
