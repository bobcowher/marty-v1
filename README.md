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
- `main.py` — 50Hz control loop; Start/Back buttons for calibration and go-home
- `robot_server.py` / `robot_env.py` — ZMQ backend and gym env for RL
- `calibration.py` — per-joint calibration sequence and its spoken prompts
- `voice/`, `voice_link.py` — robot voice, and the ZMQ bridge that speaks it on another machine
- `encoder_check.py` — moves the shoulder ~9° and back, compares encoder change to step count
- `firmware/i2c_scan/` — bring-up sketch: scans the mux and prints raw AS5600 readings
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
- `STATE x y z e0 e1 gripper enc0 enc1 enc2 enc3 enc4\n` — broadcast every 100ms. Step counts, servo angle, then raw AS5600 angle per joint (0–4095; `-1` = no sensor, no magnet, or read error)
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

## Calibrating Marty (quick start)

You'll need marty powered up with the gamepad connected, and this desktop (the one with speakers) on the same network.

1. **Check the robot is listening.** Run `ssh marty 'systemctl --user is-active marty'`. It should say `active`. If it doesn't, run `./deploy.sh`.
2. **Start the voice on the desktop.** Run this and leave it running:
   ```bash
   conda activate marty-v1
   python voice_link.py          # prints "Listening to tcp://marty.local:5556"
   ```
3. **Press Start.** Marty says "Calibration started", then "Shoulder joint, vertical".
4. **For each prompt, jog the joint there with the sticks, then press Start.** Each joint gets four positions:
   - **vertical**: straight up. Every angle is measured from here.
   - **home**: where Back sends it. Keep it a few degrees *inside* the limits, not on one. Homing stops 1° short of a limit, so a home sitting on a limit may never be reached.
   - **min limit**: as far back as it can safely go.
   - **max limit**: as far forward as it can safely go.

   Marty does the shoulder, then the elbow, then any other joint that has a working encoder.
5. **"Calibration saved"** means you're done. Press Back to check it goes home.

Things to know:
- **Soft limits are off while calibrating.** That's so you can reach the old limits and beyond. Watch the arm.
- **Back cancels**, and nothing is saved. Every joint with an encoder gets redone each time; there's no way to do just one yet.
- **Silence?** Check that `voice_link.py` is still running. Then watch `ssh marty 'journalctl --user-unit marty -f'`. Every prompt is logged there as `SAY: …`, so you can follow along by reading even without the voice. If nothing at all happens on Start, the journal will say there are no encoder readings.
- **Checking the result:** `ssh marty cat marty-v1/calibration.json`. If something is slightly off, you can edit that file directly; angles are in degrees.

## Encoders

AS5600 magnetic encoders on each joint's output, behind a PCA9548A I2C mux (address 0x70) on the RAMPS I2C header (D20 SDA / D21 SCL / GND / 5V, right of Z-MAX). Mux channel = joint index: 0 base, 1 shoulder, 2 elbow, 3 wrist tilt, 4 wrist rotate. Shoulder (channel 1) and elbow (channel 2) are wired so far.

The firmware reads one encoder every 20ms in rotation at 400kHz, so a read never blocks stepping for long and every encoder is fresh on each STATE line.

**Mounting:** diametric magnet centred over the chip, on the chip side of the board. The shoulder bracket needed a 0.8mm card shim to clear the chip's "magnet too weak" flag; the reprinted mount plate should sit 1.2mm higher than the original. Run `./deploy.sh firmware/i2c_scan` to check AGC and status flags after any mounting change (`./deploy.sh firmware` to go back).

**Shoulder, measured:** 50:1 at 800 pulses/rev is 40,000 steps per joint revolution vs 4,096 encoder counts, about 9.8 steps per count. `encoder_check.py` agreed with the step count to within 2%. A positive shoulder action moves the arm *back*.

### Joint angles

`Arm.joint_pos()` returns degrees from vertical per joint, forward positive, `NaN` for joints without a calibrated encoder. The env exposes it as `info['joint_pos']` from `reset()` and `step()`; the shoulder is index 1.

Two per-joint signs in `robot.py` connect the pieces. `ANGLE_SIGN` makes forward positive and `ACTION_SIGN` says which way a positive action turns the angle. Both are −1 for the shoulder and the elbow; set them for each new joint before calibrating it.

### Calibration (Start button)

Calibration is saved to `calibration.json` on the robot (not in git). Press Start ("Calibration started"), then each joint that has an encoder reading is walked through in turn. For each prompt, jog with the sticks and press Start again:

1. "Shoulder joint, vertical": sets zero
2. "Shoulder joint, home"
3. "Shoulder joint, min limit": the back end (negative angles)
4. "Shoulder joint, max limit": the forward end (positive angles)

…then the same for the elbow, and so on. After the last joint: "Calibration saved". Back cancels ("Calibration cancelled") and nothing is saved; joints not walked through keep their saved values.

Prompts are printed to the journal (`journalctl --user-unit marty -f`) and spoken through the voice client (below). The sequence lives in `calibration.py`.

As of 2026-10-27: shoulder home −21.4°, limits −52.5° / +96.8°; elbow home +149.8°, limits −62.9° / +149.8° (home on the limit, see step 4 above). Files that still use the old `forward_limit`/`back_limit` keys are renamed on load.

### Voice

`voice/` speaks text in a small-robot voice: Piper TTS, then a filter in `voice/effects.py` (pitch up, warble, ring-mod buzz, bit-crush grit, small-speaker band-pass). Phrases are cached as WAVs in `~/.cache/marty-voice` and played with `aplay`. It knows nothing about the arm, so it can move onto the robot once it has a speaker.

Until then, `main.py` publishes each prompt over ZMQ (PUB, port 5556) and a client on another machine speaks it:

```bash
pip install piper-tts pyzmq
python -m piper.download_voices en_US-lessac-medium --data-dir ~/.local/share/piper-voices
python voice_link.py              # connects to marty.local:5556
python voice_samples.py           # render every prompt to voice_samples/ to judge the voice
```

Publishing never blocks; prompts are dropped if no client is listening. `voice_link.py` goes away once the robot has its own speaker.

### Go home (Back button)

Drives every joint with a saved home toward it using the encoder, at ~8°/s, slowing within 10° and stopping within 1°. Any stick input cancels. It stops if an encoder reading drops out.

### Soft limits

Enforced in `Arm.step()`, which both the joystick loop and `robot_server.py` go through, so an agent can't bypass them. They're off only while calibrating.

- Within 10° of a limit, motion toward it is capped at ~5°/s
- 1° short of a limit, motion toward it is blocked; motion away is always allowed
- A joint with limits but no encoder reading can't move at all

The margins cover encoder latency: the reading reaches Python up to ~200ms late. Measured stops on the shoulder land 0.4–0.6° inside the limit.

These are software limits. If Python dies mid-move, the firmware's 150ms command watchdog is what stops the motors.
