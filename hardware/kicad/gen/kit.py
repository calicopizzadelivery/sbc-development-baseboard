"""Design helpers on top of Schematic: auto-numbered passives, the recurring
idioms (pull-up, decoupling, LED chain, series element) and label scoping.

Reference designators are numbered per sheet: R1xx on the power sheet, R2xx
on the MCU sheet, and so on, so a reviewer can tell at a glance which sheet
a part lives on.
"""
from sch import Schematic, snap, sp, G

FP = dict(
    R="Resistor_SMD:R_0603_1608Metric", R0805="Resistor_SMD:R_0805_2012Metric", R1206="Resistor_SMD:R_1206_3216Metric",
    C="Capacitor_SMD:C_0603_1608Metric", C0805="Capacitor_SMD:C_0805_2012Metric", C1206="Capacitor_SMD:C_1206_3216Metric",
    C1210="Capacitor_SMD:C_1210_3225Metric", CP="Capacitor_SMD:CP_Elec_8x10.5",
    LED="LED_SMD:LED_0603_1608Metric", SOD123="Diode_SMD:D_SOD-123", SMA="Diode_SMD:D_SMA", SOD523="Diode_SMD:D_SOD-523",
    SOT23="Package_TO_SOT_SMD:SOT-23", SOT236="Package_TO_SOT_SMD:SOT-23-6",
    FB="Inductor_SMD:L_0603_1608Metric", L_PWR="Inductor_SMD:L_Coilcraft_XAL7020-102", L_SMALL="Inductor_SMD:L_1210_3225Metric",
    XTAL4="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", XTAL2="Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm",
    SW="Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92",
    JP2="Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm", JP3="Jumper:SolderJumper-3_P1.3mm_Open_RoundedPad1.0x1.5mm", JP3B="Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm",
    USBC="calico:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal_PegClear",   # the house copy: outer ground pads clear of the peg holes (libraries 0.3.5)
    USBA2="Connector_USB:USB_A_Wuerth_61400826021_Horizontal_Stacked",
    QWIIC="Connector_JST:JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical",
    PH3="Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3.5_1x03_P3.50mm_Horizontal",
    PH4="Connector_Phoenix_MC:PhoenixContact_MC_1,5_4-G-3.5_1x04_P3.50mm_Horizontal",
    PH2="Connector_Phoenix_MSTB:PhoenixContact_MSTBA_2,5_2-G-5,08_1x02_P5.08mm_Horizontal",
    HDR6="Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Horizontal",
    HDR2x6="Connector_PinHeader_2.54mm:PinHeader_2x06_P2.54mm_Vertical",
    SWD10="Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical",
    RJ45="Connector_RJ:RJ45_Kycon_G7LX-A88S7-BP-xx_Horizontal",
    BARREL="Connector_BarrelJack:BarrelJack_Kycon_KLDX-0202-xC_Horizontal",   # KLDX-0202-BC: 2.5 x 5.5 mm, through-hole, horizontal
    RGB="LED_SMD:LED_RGB_1210", DIP4="Package_DIP:DIP-4_W7.62mm", HOLE="MountingHole:MountingHole_3.2mm_M3_Pad",
)

# nets that cross sheets get global labels; everything else is a local label
CROSS = set("""
I2C0_SCL I2C0_SDA I2C1_SCL I2C1_SDA SWDIO SWCLK K64_RESET_N K64_UART0_RX K64_UART0_TX
TGT_UART_RX TGT_UART_TX RMII_TXD0 RMII_TXD1 RMII_TXEN RMII_RXD0 RMII_RXD1 RMII_RXER RMII_CRS_DV
MDIO MDC RMII_CLK_50M PHY_INT_N HUB_RESET_N HUB_DN1_P HUB_DN1_N HUB_DN2_P HUB_DN2_N
PORT1_EN PORT2_EN PORT3_EN PORT4_EN PORT1_FAULT_N PORT2_FAULT_N PORT3_FAULT_N PORT4_FAULT_N
FTDI_EN FTDI_FAULT_N TGT_EN TGT_FAULT_N TGT_IMON RLY1_DRV RLY2_DRV RLY_PSU_DRV PSU_PRESENT_N
PD_ATTACH_N PD_ALERT_N PD_PROG_DET GPIO1 GPIO2 GPIO3 GPIO4 GPIO5 GPIO6 FTDI_VBUS
""".split())


class Sheet(Schematic):
    def __init__(self, project, title, num, page, sheet_path, paper="A3"):
        super().__init__(project, title, paper, page, sheet_path)
        self.num = num
        self.counters = {}

    def ref(self, letter):
        n = self.counters.get(letter, 0) + 1
        self.counters[letter] = n
        return f"{letter}{self.num}{n:02d}"

    # ---- labels: global if the net crosses sheets
    def pin_label(self, inst, pin, net, glob=None, length=2.54, shape="passive"):
        if glob is None:
            glob = net in CROSS
        return super().pin_label(inst, pin, net, glob, length, shape)

    def label(self, net, at, rot=0, glob=None, shape="passive"):
        if glob is None:
            glob = net in CROSS
        return super().label(net, at, rot, glob, shape)

    # ---- passives
    def R(self, value, at, rot=0, fp=None, dnp=False):
        return self.add("Device", "R", self.ref("R"), value, at, rot, footprint=fp or FP["R"], dnp=dnp)

    def C(self, value, at, rot=0, fp=None, dnp=False):
        return self.add("Device", "C", self.ref("C"), value, at, rot, footprint=fp or FP["C"], dnp=dnp)

    def CP(self, value, at, rot=0, fp=None):
        return self.add("Device", "C_Polarized", self.ref("C"), value, at, rot, footprint=fp or FP["CP"])

    def L(self, value, at, rot=0, fp=None):
        return self.add("Device", "L", self.ref("L"), value, at, rot, footprint=fp or FP["L_SMALL"])

    def FB(self, value, at, rot=0):
        return self.add("Device", "FerriteBead", self.ref("FB"), value, at, rot, footprint=FP["FB"])

    def LED(self, value, at, rot=0, fp=None):
        return self.add("Device", "LED", self.ref("D"), value, at, rot, footprint=fp or FP["LED"])

    def D(self, lib, name, value, at, rot=0, fp=None):
        return self.add(lib, name, self.ref("D"), value, at, rot, footprint=fp or "")

    def Q(self, lib, name, value, at, rot=0, fp=None):
        return self.add(lib, name, self.ref("Q"), value, at, rot, footprint=fp or FP["SOT23"])

    # ---- two-pin idioms (vertical: pin 1 up, pin 2 down)
    def rail_end(self, inst, pin, rail):
        """A power symbol on a pin, always the right way up: rails stand above
        the wire end, GND hangs below it. Horizontal pins get a short jog."""
        gnd = rail == "GND" or rail.endswith("GND")
        end, d = self.stub(inst, pin, 2.54)
        if d in ("L", "R"):
            pt = (end[0], snap(end[1] + (2.54 if gnd else -2.54)))
            self.wire(end, pt)
            self.power(rail, pt, 0)
        elif (d == "U") != gnd:
            self.power(rail, end, 0)
        else:                                   # a rail on a bottom pin or GND on a top pin: jog sideways
            pt = (snap(end[0] + 2.54), end[1]); self.wire(end, pt)
            pt2 = (pt[0], snap(pt[1] + (2.54 if gnd else -2.54))); self.wire(pt, pt2)
            self.power(rail, pt2, 0)
        return end

    def two(self, inst, a, b):
        """Connect a two-pin part: a = pin 1, b = pin 2; each a net name or ('P', rail)."""
        for pin, side in (("1", a), ("2", b)):
            if isinstance(side, tuple):
                self.rail_end(inst, pin, side[1])
            elif side == "GND" or side.startswith("+") or side.startswith("VBUS_IN"):
                self.rail_end(inst, pin, side)
            else:
                self.pin_label(inst, pin, side)
        return inst

    def pullup(self, net, value, at, rail="+3V3"):
        return self.two(self.R(value, at), rail, net)

    def pulldown(self, net, value, at):
        return self.two(self.R(value, at), net, "GND")

    def decap(self, rail, value, at, fp=None):
        return self.two(self.C(value, at, fp=fp), rail, "GND")

    def cap_to_gnd(self, net, value, at, fp=None):
        return self.two(self.C(value, at, fp=fp), net, "GND")

    def series(self, net_a, net_b, value, at, fp=None):
        """Horizontal resistor: pin 1 on the left = net_a, pin 2 right = net_b."""
        r = self.R(value, at, rot=90, fp=fp)
        return self.two(r, net_a, net_b)

    def led_chain(self, top, bottom, value_r, color, at):
        """Resistor over LED, vertical. top/bottom nets (rails allowed).
        Current flows top -> R -> LED anode -> cathode -> bottom."""
        x, y = sp(at)
        r = self.R(value_r, (x, y))
        d = self.LED(color, (x, y + 10.16), rot=90)      # rot 90: anode on top, cathode below
        self.wire(r.pin("2"), d.pin("2"))
        for inst, pin, net in ((r, "1", top), (d, "1", bottom)):
            if net == "GND" or net.startswith("+") or net.startswith("VBUS_IN"):
                self.rail_end(inst, pin, net)
            else:
                self.pin_label(inst, pin, net)
        return r, d

    # ---- an IC with a net map
    def ic(self, lib, name, ref, value, at, rot=0, fp="", nets=None, power=None, nc=(), fields=None, project_lib=None):
        """Place an IC and attach: nets {pin: net} as labels, power {pin: rail}
        as power symbols, nc as no-connect flags."""
        u = self.add(lib, name, ref, value, at, rot, footprint=fp, fields=fields, project_lib=project_lib)
        for pin, net in (nets or {}).items():
            self.pin_label(u, str(pin), net)
        for pin, rail in (power or {}).items():
            self.pin_power(u, str(pin), rail)
        for pin in nc:
            self.pin_nc(u, str(pin))
        return u

    def flag_rail(self, rail, at, cls=None):
        x, y = sp(at)
        self.power(rail, (x, y))
        self.flag((x + 10.16, y))
        if cls:                                        # the net class directive sits on the flag wire, split there
            self.wire((x, y), (x + 5.08, y)); self.wire((x + 5.08, y), (x + 10.16, y))
            self.netclass_flag(cls, (x + 5.08, y), 270)             # pointing down, its text below the strip
        else:
            self.wire((x, y), (x + 10.16, y))

    def flag_class(self, rail, at, cls):
        """A rail symbol with its net class directive beside it, for a net that is already
        driven (no PWR_FLAG: two power outputs on one net is an ERC error)."""
        x, y = sp(at)
        self.power(rail, (x, y))
        self.wire((x, y), (x + 5.08, y))
        self.netclass_flag(cls, (x + 5.08, y), 270)

    def flag_net(self, net, at):
        x, y = sp(at)
        self.flag((x, y))
        self.label(net, (x + 5.08, y))
        self.wire((x, y), (x + 5.08, y))

    def note(self, lines, at, size=1.5):
        x, y = at
        for i, ln in enumerate(lines):
            self.text(ln, (x, y + i * (size * 1.8)), size=size, bold=(i == 0))


class Row:
    """Successive positions along a line, for rows of passives."""
    def __init__(self, x, y, dx=15.24, dy=0):
        self.x, self.y, self.dx, self.dy = x, y, dx, dy
        self.i = 0

    def __call__(self):
        p = (self.x + self.i * self.dx, self.y + self.i * self.dy)
        self.i += 1
        return p
