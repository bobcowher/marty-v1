# Robot Arm 1 — Arduino

5-DOF robotic arm controlled via Arduino Mega 2560, intended for reinforcement learning integration. Current phase: getting smooth continuous control working before adding encoders and RL.

## Hardware

- **Controller board:** Arduino Mega 2560 + RAMPS 1.4 shield (Elegoo)
- **Stepper drivers:** TMC2209 v3 (BigTreeTech) for X/Z/E0, DRV8825 for Y (shoulder)
- **Stepper motors:** NEMA 17 with planetary gearboxes (see Motor Models below)
- **Gripper:** SG90 servo (prototype — underpowered, pending replacement)
- **Gamepad:** 8BitDo Ultimate Wireless in X-input mode (hold X+Start on power-on)
- **Power supply:** 24V

### Motor Models

| Position | Model | Current | Gearbox | Status |
|----------|-------|---------|---------|--------|
| Base (X) | 17HS13-0404S-PG5 | 0.4A | 5:1 | Working |
| Shoulder (Y) | 17HS19-1684S-PG5 | 1.68A | 5.18:1 | Debugging (see Known Issues) |
| Elbow (Z) | TBD | — | — | Not yet installed |
| Wrist (E0) | TBD | — | — | Not yet installed |

**Shoulder motor specs (17HS19-1684S-PG5):**
- Phase resistance: 1.8Ω, Inductance: 3.2mH
- Holding torque: 52Ncm (motor only), gearbox max: 3Nm
- Purchased from StepperOnline via Amazon

### Motor Pinout

| Motor | STEP | DIR | ENABLE | Purpose         | Status      |
|-------|------|-----|--------|-----------------|-------------|
| X     | 54   | 55  | 38     | Base rotation   | Working     |
| Y     | 60   | 61  | 56     | Shoulder        | DRV8825 driver |
| Z     | 46   | 48  | 62     | Elbow           | Not yet used |
| E0    | 26   | 28  | 24     | Wrist           | Not yet used |
| E1    | 36   | 34  | 30     | (unused)        | Not yet used |

### Servo

- **Pin:** D11 (RAMPS S0 servo header — first slot, next to reset button)
- **Power:** RAMPS servo power jumper must bridge the blank pin to 5V (left-to-middle)
- **Range:** 0–180°, starts at 90°, 2° per step

### DRV8825 Driver (Y/Shoulder)

The shoulder motor (17HS19-1684S-PG5, 1.68A) uses a DRV8825 instead of TMC2209 due to torque issues with TMC2209 standalone mode.

**Vref setting:**
```
Vref = I_limit × 0.5 = 1.68 × 0.5 = 0.84V
```
Start at 0.7V and increase if needed. Measure between potentiometer and GND.

**Microstepping (via MS1/MS2/MS3 jumpers):**

| MS1 | MS2 | MS3 | Microsteps |
|-----|-----|-----|------------|
| Low | Low | Low | Full step |
| High | Low | Low | 1/2 |
| Low | High | Low | 1/4 |
| High | High | Low | 1/8 |
| Low | Low | High | 1/16 |
| High | High | High | 1/32 |

With MS1+MS2 jumpered (matching other slots), DRV8825 runs at 1/8 microstepping.

## Architecture

- `firmware/firmware.ino` — Arduino: non-blocking velocity control via `micros()` timing, servo via `Servo.h`
- `robot.py` — `Arm` class: serial interface, sends `MOVE` commands, tracks position
- `controller.py` — 8BitDo joystick mapping with deadzone and scaling
- `main.py` — 50Hz control loop
- `build.sh` — compile and upload via arduino-cli

## Controls (8BitDo Ultimate)

| Input               | Action            |
|---------------------|-------------------|
| Left stick X        | Base rotation     |
| Left stick Y        | Shoulder          |
| Right stick Y       | Elbow (Z)         |
| Right stick X       | Wrist (E0)        |
| Left trigger (B5)   | Close gripper     |
| Right trigger (B6)  | Open gripper      |

Axes on the same stick are mutually exclusive (dominant axis wins) to prevent diagonal contamination.

## Serial Protocol

**Baud rate:** 115200, port `/dev/ttyACM1`

| Command                        | Description                              |
|-------------------------------|------------------------------------------|
| `MOVE x y z e0 servo\n`       | Set motor velocities + servo step        |
| `STOP 0 0 0 0 0\n`            | Stop all motors                          |

Motor speed values: signed µs delay between steps (smaller magnitude = faster, 0 = stopped).
Servo step: `-1` (close), `0` (hold), `+1` (open).

**Responses:**
- `READY` — on boot
- `MOVE OK x_period=N v5=N` — command acknowledged
- `SERVO step=N pos=N` — servo moved
- `STATE x y z e0 gripper\n` — position broadcast every 100ms
- `ERROR ...` — parse failure

## Build & Monitor

```bash
./build.sh                                              # Compile and upload
arduino-cli monitor -p /dev/ttyACM1 -c baudrate=115200  # Serial monitor
```

## Known Issues

### Y Motor (Shoulder) — Torque Issues with TMC2209
New shoulder motor (17HS19-1684S-PG5) had no torque with TMC2209 in standalone mode.
- **Ruled out:** firmware (pin 60 confirmed toggling), wiring, motor windings (1.9Ω per coil), gearbox (smooth), driver (tried fresh TMC2209)
- **Solution:** Switched to DRV8825 driver (see DRV8825 section above)

### Gripper (Prototype)
SG90 servo is too weak for the current gripper design and the sliders stick under load. Planned replacement: MG996R or a rack-and-pinion parallel jaw design.

### `stop()` Command Format
`robot.py`'s `stop()` method sends `STOP 0 0\n` (2 args) but the firmware parser requires 5 args. Currently unused — motors stop via the 150ms firmware watchdog.

## Encoders
Not yet wired. Planned for closed-loop control before RL integration.
