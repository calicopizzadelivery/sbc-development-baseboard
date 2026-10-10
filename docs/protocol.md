# Console protocol

One ASCII command per line, one reply line starting `OK` or `ERR`. Verbs and
arguments are case-insensitive, `\n` and `\r\n` both work, blank lines are
ignored silently. This is the convention `qtpy-relay-controller` and
`frdm-k64f-hid` already use, so existing host tooling and shell idioms carry
over.

Identical over all three transports:

| Transport | Address | Notes |
|---|---|---|
| USB CDC | DAPLink on hub port 7, via J1 | 115200 baud, nominal — it is a CDC port |
| TCP | J10, port 7373 (configurable) | Several control sessions may be open at once |
| — | J16 SWD | Not a console; debug only |

Commands are atomic single lines, so interleaved control sessions cannot corrupt
each other. `CONSOLE` attach is the exception and is exclusive — see below.

> **There is no authentication.** Anything that can reach port 7373 can cut
> power to the target and assert its recovery pins. Put the management port on a
> trusted segment. Adding auth is [open question 8](hardware-spec.md#8-open-questions).

---

## Switching

| Command | Effect |
|---|---|
| `PORT <1-4\|ALL> ON\|OFF\|TOGGLE` | Power a USB-A port |
| `PORT <n\|ALL> PULSE [ON\|OFF] <ms>` | Invert (or force a state) for *ms*, then revert |
| `PORT <n>` | Report one port |
| `RELAY <1-2\|ALL> ON\|OFF\|TOGGLE` | Energize a relay coil |
| `RELAY <n\|ALL> PULSE [ON\|OFF] <ms>` | As above |
| `RELAY <n>` | Report one relay |
| `TGT 5V ON\|OFF\|TOGGLE` | The board's switched +5V_TGT rail on J14 |
| `TGT PSU ON\|OFF\|TOGGLE` | The external PSU passthrough, J18 → J19 |
| `TGT 5V\|PSU PULSE OFF <ms>` | Hold that supply dark for *ms* |
| `TGT CYCLE [5V\|PSU] [<ms>]` | `PULSE OFF` on one supply, or both if none is named. Default 5000 ms |
| `TGT` | Report both supplies |
| `FTDI ON\|OFF\|TOGGLE` | VBUS to the FT231X behind J9 |
| `FTDI CYCLE [<ms>]` | Power-cycle it, default 2000 ms; it re-enumerates on the workstation |
| `FTDI` | Report it |

Pulses are non-blocking and several can run at once; the console stays
responsive throughout, and the revert happens even if the host wanders off. A
pulse reverts to whatever the channel was set to beforehand, so `PULSE ON 500`
on something that was off returns it to off. Setting a channel outright cancels
any pulse still running on it. Range is 1–3600000 ms.

`ON` always means *the thing the channel exists to do is happening*: a port is
powered, the target is powered, a relay is energized. Which way a relay's
contacts run at that point is a wiring choice — SPDT gives you NO and NC on the
terminal block — so the protocol does not need to know.

`TGT PSU ON` energizes the passthrough relay and the target powers; de-energized
is off, which is also what an unpowered baseboard does. Firmware restores the
last commanded state at boot ([spec, open question 13](hardware-spec.md#8-open-questions)),
so a baseboard reset is a brief power cut to the target rather than a change of
state. A `PULSE` in flight across a reset is lost; the channel comes back to its
pre-pulse state.

`FTDI` is deliberately not `PORT 6`, though that is the hub port it sits on.
`PORT ALL OFF` does not touch it: the bridge you are reading the boot log on
must not be swept away by a script that is clearing the bench. `FTDI CYCLE`
exists for one reason — a USB-UART bridge that stays enumerated and openable
while delivering nothing, which the bench notes record happening and being
misread as a dead target.

`TGT CYCLE` with no supply named cycles both. A target uses one of the two, so
cycling the other is a no-op — and if a target ever uses both, cycling both is
the only thing that is actually a power cycle.

### There is no bare `ON` or `OFF`

`qtpy-relay-controller` accepts `OFF 3`, because on that board there was only
one kind of channel. Here there are three, and they do very different things:

```
> OFF 3
ERR AMBIGUOUS say PORT, RELAY or TGT
```

Guessing would mean a script written for the old board silently cutting the
target's power instead of a USB port. Refusing costs one edit per script and
cannot do that.

Note also that **`RELAY` means the two SPDT contacts, not USB power.** On the
old board `RELAY` addressed what were physically relays switching USB port
power; here those are `PORT`.

---

## Target console

| Command | Effect |
|---|---|
| `CONSOLE` | Attach this session to the target's UART. Escape with `~.` at line start |
| `CONSOLE BAUD <n>` | Set the target UART rate, persisted |
| `CONSOLE TAIL [<n>]` | Last *n* lines from the ring buffer, default 40 |
| `CONSOLE CLEAR` | Empty the ring buffer |

The MCU captures the target's console into a ring buffer continuously, whether
or not anyone is attached. So a boot that failed overnight is still readable in
the morning, and `CONSOLE TAIL` composes in a script — which an attached
interactive session does not.

Only one session may be attached at a time; a second gets
`ERR CONSOLE BUSY <transport>`.

This is J13. The other console, J9, is an FT231X that the workstation talks to
directly as a serial device; it has no commands here beyond `FTDI`.

---

## HID to the target

Unchanged from `frdm-k64f-hid` — the target sees a plain USB keyboard and mouse
on J3 and cannot tell the difference between this and someone at a keyboard.

| Command | Effect |
|---|---|
| `TYPE <text>` | Type the rest of the line literally, case preserved |
| `KEY <combo>` | Press and release, e.g. `KEY ctrl+alt+t` |
| `KEYDOWN <combo>` / `KEYUP <combo>` | Press and hold / release |
| `RELEASE` | Release every held key and button |
| `MOUSE MOVE <dx> <dy>` | Relative move, −127..127 per report |
| `MOUSE SCROLL <n>` | Wheel clicks |
| `MOUSE CLICK\|DOWN\|UP <button>` | `left`, `right` or `middle` |

`ERR USB NOT READY` means the target has not configured the HID interfaces.

---

## Breakout header

| Command | Effect |
|---|---|
| `GPIO <1-6> HIGH\|LOW\|IN` | Drive or release a breakout pin |
| `GPIO <n>` | Read one pin |
| `I2C SCAN` | Addresses present on the target bus |
| `I2C READ <addr> <reg> [<len>]` | Default length 1 |
| `I2C WRITE <addr> <reg> <byte>...` | |

The header's outputs are **push-pull** — a TXB0108 cannot drive an open-drain
net, and an external pull-up below ~50 kΩ will fight it. `HIGH` and `LOW` drive;
`IN` releases to high-impedance, which is the closest thing to open-drain the
translator can do.

Levels follow J13's VREF. With the target unpowered, VREF is 0 V, the translator
is disabled, and `GPIO` returns `ERR NO VREF` rather than pretending.

---

## Status and identity

| Command | Effect |
|---|---|
| `STATE` | Every channel, in one line |
| `POWER` | The +5V rail, the target rail's current from the eFuse's IMON, and the 20 W budget |
| `INFO` | Identity, firmware, USB state, SoC serial |
| `ID` / `SETID <text>` | Read / persist this board's name, 1–8 characters |
| `VERSION`, `HELP` | |
| `EVENTS ON\|OFF` | Unsolicited `EVT` lines, default off |
| `RESET` | Reset the MCU. Does not disturb any rail — see §5 of the spec |

```
> STATE
STATE PORT 1=ON 2=ON 3=OFF 4=ON(pulse 480ms) FTDI=ON RELAY 1=OFF 2=OFF TGT 5V=ON PSU=ON(present)
> POWER
OK POWER rail=present tgt=1.3A budget=20W used=14W headroom=6W
> INFO
OK INFO id=bench-1 fw=sbc-baseboard ver=0.1.0 usb=ready eth=up serial=FFFFFFFF4E45805140040019
```

Several of these boards end up on one workstation, which is why `SETID` exists
and why host tooling should refuse to guess between them. The name persists
across a firmware update.

### Power budget refusals

The board is powered by a 5 V 4 A adapter on the barrel jack J2 and budgeted
at its 20 W ([spec §4](hardware-spec.md#4-power); 2026-10-10, a USB-C PD
inlet until then, whose negotiated contract the MCU read at boot and budgeted
against). The four ports at their 1.1 A limits, the target rail at the
eFuse's 3 A and the board itself add up to more than 4 A, and nothing in
hardware limits the sum but the adapter, so firmware will not enable more
load than the budget allows:

```
> PORT 3 ON
ERR POWER BUDGET need=5W have=2W budget=20W
```

Better than the alternative, which is a rail that sags and drops every attached
device at once — including whichever one you were watching to work out what went
wrong.

The budget is a constant of the hardware, not a reading, so there is nothing
to re-read and no unknown state. `POWER` reports it with what is allocated
from it, and the target rail's actual draw from the eFuse's IMON — the one
current the board measures.

### Events

Faults are asynchronous, and the protocol is otherwise strictly one line in, one
line out. With `EVENTS ON`, unsolicited lines start `EVT`:

```
EVT OC PORT 3 limit=1.1A
EVT TGT FAULT limit=3.0A
EVT TGT UNDERVOLT 4.62V
EVT PSU absent
```

Default off, so a client that reads exactly one line per command — which both
existing host CLIs do — keeps working unchanged.

---

## Exit status, host side

Host tooling should exit non-zero when the firmware answers `ERR`, so commands
compose in shell scripts. Both existing CLIs do this and it is worth keeping.

Note that Zephyr's console echoes what it receives; a client talking to the CDC
port directly should expect its command back before the reply.
