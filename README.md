# sbc-development-baseboard

One board carrying the hardware you need to develop on and remotely manage an
attached single-board computer: a microcontroller that is a USB device to the
target and a console to you, four individually switched USB-A ports, an FTDI
header straight to the workstation, two isolated
SPDT relays on screw terminals, a level-shifted serial console, and a switched
supply for the target itself.

It replaces a bench that currently takes an FRDM-K64F, a QT Py, an 8-channel
relay board, a two-tier USB hub cascade and a CP2102N dongle, wired together by
hand and documented in a port map that has to be re-surveyed whenever anything
is replugged.

## What it does

| Function | How |
|---|---|
| Type at the target | USB HID keyboard + mouse from the K64's device port |
| Cut power to any USB device | Four USB-A ports on two stacked receptacles, each with its own current-limited switch |
| Hard power-cycle the target | Switched +5V_TGT rail up to 3 A behind an eFuse, or any PSU up to 30 V / 5 A through an isolated relay |
| Toggle target I/O — FORCE_RECOVERY and friends | Two SPDT relays, dry contacts, Phoenix terminals |
| Read the target's serial console | MCU-owned UART, auto level translation 1.2–3.6 V |
| Read it from the workstation directly | FT231X on an internal hub port, standard 6-pin FTDI header, 3.3 V |
| Do all of it from somewhere else | 10/100 Ethernet to the workstation |
| Do all of it with no network | USB CDC console over the onboard DAPLink |

Every one of those is addressable from the same ASCII protocol the relay
controller and the HID injector already speak — one line in, one line out,
starting `OK` or `ERR`. See **[docs/protocol.md](docs/protocol.md)**.

## The shape of it

[![Block diagram](docs/block-diagram.png)](docs/block-diagram.png)

```
workstation ──USB-C──> hub ──> 4x USB-A (switched)     ──> whatever you hang on the bench
                           ──> FT231X, FTDI header     ──> target's console, direct
            ──RJ45───> K64 ──> USB-C device port       ──> target's USB host port
                           ──> UART + VREF             ──> target's console
                           ──> 2x SPDT dry contacts    ──> target's recovery/reset pins
                           ──> switched +5V, 3 A       ──> target's supply
 target PSU ──Phoenix──> isolated relay, NO, 5 A       ──> target's supply, any voltage
 5 V adapter ──barrel──> +5V, one rail, 4 A, 20 W      ──> everything but the passthrough
```

140 × 100 mm, four M3 corner holes. Your connectors leave the left edge, the
target's the right; an LED on every rail, every switched output and every relay
coil, and none on the passthrough, whose voltage is whatever you plugged in.

One USB-C for the workstation and a barrel jack for power (2026-10-10; two
USB-C inlets, a PD charger beside the workstation port, until then). A
workstation port that carries data offers 15 W at best, and four switched ports
plus a target rail need more than that, so power has its own connector: a
5 V 4 A adapter on a 2.5 mm barrel jack, 20 W, which firmware budgets across
the ports and the target rail. A USB-C PD sink feeding two 5 V bucks did that
job first, and went because of what it cost the board rather than the bench:
339 parts became 270, and the one rail layer no longer carries a 3 A inlet
beside two 6 A rails, which is where the router stalled at 98 open connections
on six layers. Keeping power off the workstation link also means the board stays
alive when that link is down, so the MCU can power-cycle the entire USB tree
including its own path back to you.

## Where the design came from

Most of the non-obvious decisions here are bench scars from the Jetson work, not
preferences. They are written up in full in
**[docs/hardware-spec.md](docs/hardware-spec.md)**; the short version:

- **Nothing the MCU depends on sits downstream of a switch it controls.** The
  DAPLink, the Ethernet PHY and the MCU itself are all upstream. `OFF ALL` can
  never take out the console.
- **Rails boot to the state that does no harm.** USB ports and the target rail
  come up powered; relays come up de-energized. Resistors set this while the MCU
  is still in reset, so a reset never drops a load or asserts recovery.
- **The device port cannot back-feed the target.** Its VBUS is sense-only
  through a blocking element. This is the fix for the failure where cutting the
  target's power left it half-alive for 90 seconds because a self-powered
  FRDM-K64F was pushing 5 V up its own device port.
- **The relays are signal relays with gold-clad contacts.** Switching a 1.8 V
  logic pin is a dry circuit; silver power-relay contacts grow an oxide film
  that such a signal cannot break down.
- **The MCU owns the target's console.** No USB-UART bridge to wedge and look
  exactly like a target that is not booting.
- **The target's PSU passes through on its own nets.** A 19 V / 3 A return
  current has no business on the board's ground plane or its USB shields. It
  crosses one relay contact — normally open — so nothing powers until the
  baseboard says so, and a dead baseboard leaves the target off.

## Status

Specification, a generated schematic (KiCad 10, a root sheet and eight sub-sheets, ERC clean) and
a generated, placed six-layer board, both in
[`hardware/kicad/sbc-baseboard/`](hardware/kicad/sbc-baseboard/) with a
[PDF](hardware/kicad/sbc-baseboard/sbc-baseboard.pdf) of the schematic for
review. The board is placed and bulk-routed by the house standard's engine
(see [hardware/kicad/README.md](hardware/kicad/README.md)) and is being
routed again for the barrel-jack inlet (2026-10-10; the board routed before
it, with the PD inlet and the two bucks, stopped at 98 open connections on
six layers and 116 on four); the hand pass that finishes the routing is open.
No firmware.

Next: the routing and the hand pass on the board, then firmware.

## Layout

```
docs/hardware-spec.md   block diagram, part selection, power and pin budgets,
                        safe states, and the open questions
docs/protocol.md        the console protocol, across both transports
docs/block-diagram.*    the diagram above, SVG source and rendered PNG
scripts/block-diagram.py regenerates both; run it with every configuration change
hardware/kicad/         the KiCad project (sbc-baseboard/) and the generator that
                        produced its first pass (gen/) — see hardware/kicad/README.md
hardware/datasheets/    the parts that matter
```

## Related

- [`frdm-k64f-hid`](../frdm-k64f-hid) — the HID injector firmware this board inherits
- [`qtpy-relay-controller`](../qtpy-relay-controller) — the relay protocol and its safe-state rules
- [`nvidia-jetson-tv`](../nvidia-jetson-tv) — the target that motivated all of it

## Licence

Apache-2.0. See [LICENSE](LICENSE).
