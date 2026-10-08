# Reference-design review

Every IC's surrounding parts were checked against the implementation its
maker publishes: the datasheet's typical application or design example, and
the evaluation board where its schematic was available. The point is to ship
proven values and to know exactly where and why this board departs from them.
Checked 2026-10-04 against the documents named per part; "changed" means the
schematic was brought in line in commit `reference-design review`.

| IC | Source | Reference implementation | This board | Verdict |
|---|---|---|---|---|
| STUSB4500 (U101) | Datasheet §6.3, fig. 10 "typical schematic with MCU" | VBUS_VS_DISCH 1 kΩ; DISCH 470 Ω; VREG_2V7, VREG_1V2 1 µF; VDD 1 µF; VSYS 1 µF; ESDA25W on CC1/CC2; ESDA25P35 on VBUS; external I2C pull-ups; ADDR to GND | R103 1 kΩ, R108 470 Ω, C105/C106 1 µF, C104 1 µF/50 V on VBUS_IN beside VDD, C107 1 µF on VSYS, D103/D104 ESDA25W, D102 SMAJ24A (same role, 24 V standoff), 4.7 kΩ pull-ups, ADDR0/1 to GND | Matches. VBUS_EN_SNK drives Q101 (gates the buck EN) through a 100 kΩ pull-up to VBUS_IN and a 5.1 V zener instead of a PMOS load switch: by design, the bucks are the switch. |
| TPS54560B (U103, U104) | Datasheet §8.2 "5 V output design example", TPS54560EVM BOM | f_sw 400 kHz, RT 243 kΩ; FB 53.6 kΩ/10.2 kΩ; L 7.2 µH (7–60 V in); B560C catch diode; 0.1 µF boot; C_out 3×47 µF ceramic (141 µF); C_in 4×2.2 µF; COMP 16.9 kΩ, 4.7 nF, 47 pF; EN with a UVLO divider | RT 243 kΩ; FB 51.1 kΩ/9.76 kΩ (same ratio, 4.99 V); L 10 µH/6 A (input is 20 V max, so 6.3 µH minimum: fine); B560C; 100 nF boot; 2×47 µF ceramic + 100 µF electrolytic; 2×10 µF + 100 nF + 1 µF in; COMP 16.9 kΩ / 4.7 nF / 47 pF; EN pulled low by Q101, else floats high on the internal pull-up | **Changed**: compensation was a placeholder (19.1 kΩ / 3.3 nF / 47 pF), now the datasheet example's values, which were derived for the same 141 µF ceramic output. No UVLO divider by design (the PD contract gates EN). |
| TPS62823 (U105) | Datasheet §9.2 typical application, §9.2.2.2–3 | L 470 nH (XFL4015-471, 6.6 A sat); C_in 10 µF; C_out 2×10 µF or 22 µF (up to 150 µF allowed); R2 100 kΩ recommended, R1 = R2·(VOUT/0.6 − 1); C_ff = 12 µs / R2 = 120 pF | L103 470 nH/4 A; C129 10 µF; 2×22 µF; R127 100 kΩ, R128 453 kΩ (3.32 V), C132 120 pF; EN tied to VIN; PG open | **Changed**: the divider was 100 kΩ/22.1 kΩ with no feed-forward capacitor; now the recommended set. Check the chosen inductor's saturation rating is at least 4.5 A. |
| TPS2553 (U403–U407) | Datasheet §10.2.3 "typical application as USB power switch" | 0.1 µF at IN; R_FAULT 100 kΩ; R_ILIM 20 kΩ (1.2 A example), 15–232 kΩ allowed; ≥ 120 µF bulk per hub on the downstream side | 100 nF at each IN plus the rail's bulk; FAULT pull-ups 10 kΩ (faster edge, within limits); R_ILIM 23.7 kΩ ≈ 1.1 A; 22 µF per port plus 194 µF on +5V_PORTS | Matches. The FAULT pull-ups sit at the K64 as one column of resistors to +3V3 (the datasheet allows them anywhere on the net). |
| TPS26630 (U704) | Datasheet §9.2.2.1 (R_ILIM = 18/I_OL kΩ), electrical characteristics (UVLO 1.2 V, dVdT 2 µA / 25 V/V, IMON 27.9 µA/A) | R_ILIM 9.09 kΩ for 2 A; dVdT capacitor per ramp time; IMON resistor sized for the ADC | R708 3.65 kΩ → 4.9 A (spec: 5 A); UVLO 196 kΩ/75 kΩ → 4.34 V rising; dVdT 10 nF → 5 V/ms; IMON 20 kΩ → 0.56 V/A, 2.8 V at 5 A; MODE, OVP, PGTH to GND; PGOOD open | Matches the spec's intent. Confirm at bring-up that MODE = GND selects the wanted fault response (latch or retry) and that OVP tied low is acceptable. |
| USB2517 (U402) | Datasheet pin table; EVB-USB2517 schematic | RBIAS 12.0 kΩ 1 %; 24 MHz crystal with 33 pF; VDD18 and VDD18PLL 1 µF + 0.1 µF; VDD33 0.1 µF per pin + 4.7 µF; VBUS_DET from upstream VBUS through 100 kΩ/100 kΩ with 1 µF; RESET_N 100 kΩ pull-up + 0.1 µF; straps 10 kΩ; TEST to GND | R404 12.0 kΩ 1 %; 24 MHz + 2×33 pF; 1 µF + 100 nF on each 1.8 V pin; 7×100 nF + 4.7 µF; VBUS_DET 100 kΩ/100 kΩ + 1 µF; RESET_N 10 kΩ + 1 µF, driven by the K64; 10 kΩ straps; TEST to GND | **Changed**: VBUS_DET was 10 kΩ/22 kΩ (3.4 V at the pin, above VDD33); now the evaluation board's divider. |
| KSZ8081RNA (U301) | Datasheet pin table, §11 magnetics | REXT 6.49 kΩ 1 %; VDD_1.2 2.2 µF + 0.1 µF; MDIO and INTRP each need an external 1.0 kΩ pull-up; 25 MHz crystal; REF_CLK 50 MHz to the MAC; on-chip termination; transformer centre taps to 0.1 µF each, not to a supply; PHYAD straps have internal pull-downs (address 0) | R311 6.49 kΩ 1 %; C306/C307 2.2 µF + 100 nF; MDIO 1 kΩ, INTRP 1 kΩ; 25 MHz + 2×22 pF; 33 Ω series on REF_CLK; TCT/RCT 100 nF to GND; no straps (the K64's RMII pins are inputs at reset); 75 Ω ×4 + 1 nF/2 kV Bob Smith | **Changed**: the MDIO pull-up was 4.7 kΩ; the datasheet requires 1.0 kΩ. Crystal load capacitors depend on the crystal's CL: confirm 22 pF against the part ordered. |
| MK64FN1M0VLL12 (U201) | Datasheet; FRDM-K64F arrangement (RMII clock from the PHY, USB regulator) | VREGIN 2.2 µF, VOUT33 2.2 µF; VDDA filtered; VBAT; RESET_b and NMI_b pulled up; 32.768 kHz crystal with load capacitors per its CL | C201/C202 2.2 µF; FB201 + 100 nF + 10 µF on VDDA/VREFH; VBAT to +3V3; 10 kΩ pull-ups, 1 µF on reset; Y201 with 2×12 pF; EXTAL0 fed by the PHY's 50 MHz through R307 33 Ω; D201 BAT54 feeds VREGIN only from J3 VBUS | Matches. Confirm 12 pF against the 32.768 kHz crystal's CL (FRDM-K64F uses a 12.5 pF part). |
| MK20DX128VFM5 (U601) | mbed HDK "DAPlink-K20DX v1.0.0" interface schematic; DAPLink k20dx HIC | USB 5 V into VREGIN, VOUT33 feeds VDD/VDDA; crystal on XTALIN/XTALOUT (8 MHz per the k20dx firmware); SWD and UART pin use per the HIC; reset button | VREGIN from +5V_PORTS with 2.2 µF; VOUT33 → K20_3V3 with 2.2 µF + 2×100 nF; 8 MHz + 2×18 pF; SWCLK PTC5, SWDIO PTC6, UART1 PTC3/PTC4, nRESET PTB1, LED PTD4; 10 kΩ + 100 nF + button on RESET | Matches. Confirm 18 pF against the 8 MHz crystal's CL. |
| FT231XS (U501) | Datasheet fig. 6.1 "bus powered configuration" | 27 Ω in series with USBDM/USBDP and 47 pF to GND on the bus side; VCC through a ferrite bead with 10 nF + 4.7 µF + 100 nF; 3V3OUT 100 nF; VCCIO from 3V3OUT; RESET# may be tied to 3V3OUT; CBUS LEDs | R504/R505 27 Ω, C502/C503 47 pF; VCC is the TPS2553-switched FTDI_VBUS with 10 µF + 100 nF at the pin and 10 µF at the switch (no ferrite); C501 100 nF; VCCIO from 3V3OUT; RESET# 10 kΩ to 3V3OUT; 470 Ω LEDs | **Changed**: the USB series resistors and capacitors were missing. The ferrite bead is replaced by the power switch and its bulk capacitor: a deliberate deviation. |
| PCA9517A (U102) | Datasheet §6 | EN has an internal pull-up to VCC(B); external pull-ups on both sides; VCC(A) ≥ 0.9 V, VCC(B) ≥ 2.5 V | 4.7 kΩ both sides; 100 nF per supply; EN driven through Q102 with a 10 kΩ pull-up | Matches. |
| TXB0104, TXB0108, TXS0102 (U701–U703) | Datasheets | 0.1 µF per supply; OE pulled low through a resistor until the supplies are up; VCCA ≤ VCCB | 100 nF per supply; OE tied to VCCA = VREF_TGT, which is the target's own rail; VCCB = +3V3 is always up | Deviation by design: OE follows the target rail, so the translators are off whenever the target is off, and VCCA never exceeds VCCB. |
| USBLC6-2SC6, PESD5V0S1UL, ESDA25W | Datasheets | Line-side placement next to the connector | As drawn | Matches. |
| LTV-817, G6K-2F-Y, JW1FSN | Datasheets | 1–10 mA LED current; 5 V coils with flyback diodes; drivers rated for the coil current | 2×1.8 kΩ (1–8 mA over 5–30 V); 1N4148W on every coil; 2N7002 for the 20 mA signal relays, AO3400A for the 106 mA power relay | Matches. |
| GCT USB4105 (J1, J2, J3) | Drawing rev B4, "Recommended PCB Layout": 12 × 1.15 contact pads, 2 × Ø0.65 board-lock peg holes 5.78 mm apart, 4 × Ø0.60 shell slots | KiCad's footprint reproduces the drawing; its outer ground pads sit 0.19 mm from the peg holes | House footprint (ecad-libraries 0.3.6): the same pad for pad, with the four outer ground pads A1, A12, B1, B12 shortened 1.15 → 1.05 mm at the peg end, hole to copper 0.29 mm at those pads; the next pads in (A4, A9, B4, B9) stay at KiCad's 0.26 mm, the footprint's new minimum | Deviates from the drawing by 0.1 mm on four ground pads (9 % less solder area each) so the fab's 0.25 mm hole-to-copper minimum holds without an exception; the shell slots carry the mechanical load. |

## FRDM-K64F OpenSDA, revisited for the DAPLink K20 (2026-10-06)

The FRDM-K64F schematic (rev E4, sheet 4 "OpenSDA interface") agrees with
DAPLink's `k20dx` IO_Config.h: SWCLK PTC5, SWDIO PTC6 driving and PTC7
reading the same line, nRESET PTB1, LED PTD4, UART1 PTC3/PTC4. Two things
the first pass missed, both now fitted: PTC7 was unconnected (DAPLink reads
SWDIO through it, so SWD would never have worked), and the FRDM's 33 Ω
series resistors on the K20's USB D+/D− (R20/R22). The FRDM's level shifters
between the K20 and its target are not needed here: the K64 target runs at
the K20's 3.3 V. PTD6 (POWER_EN) and PTD7 (VTRG_FAULT_B) are left open; the
firmware drives one and ignores the other.

## Open items for bring-up

- Crystal load capacitors (24 MHz 33 pF, 25 MHz 22 pF, 8 MHz 18 pF, 32.768 kHz
  12 pF) are right only for crystals with the matching CL: confirm when the
  crystals are chosen.
- TPS26630: MODE and OVP strapping, and the 4.9 A limit against the buck's
  6 A switch limit.
- TPS62823: inductor saturation rating (≥ 4.5 A).
- TPS54560B: the datasheet example's compensation is now fitted, but TI still
  recommends a load-step check; the output also carries a 100 µF electrolytic
  the example does not have.
