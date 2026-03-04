# Robot Arm Project - Context for Claude

## Project Goal
5-DOF robotic arm controlled via Arduino Mega, intended for reinforcement learning integration. Current phase: getting smooth continuous control working before adding encoders and RL.

## Architecture

**Firmware** (`firmware/firmware.ino`): Arduino Mega 2560 running stepper control
**Host** (`robot.py`, `main.py`): Python interface over serial (115200 baud, `/dev/ttyACM1`)
**Build**: `build.sh` uses arduino-cli with TMCStepper library
**Controller**: 8BitDo Ultimate Wireless (must be in X-input mode: hold X+Start on power-on)

## Hardware

5 stepper motors on RAMPS 1.4-style pinout (only X and Y currently active):

| Motor | STEP | DIR | ENABLE | Purpose |
|-------|------|-----|--------|---------|
| X (1) | 54   | 55  | 38     | Base rotation |
| Y (2) | 60   | 61  | 56     | Shoulder |
| Z (3) | 46   | 48  | 62     | Elbow (not yet used) |
| E0 (4)| 26   | 28  | 24     | Wrist (not yet used) |
| E1 (5)| 36   | 34  | 30     | Gripper (not yet used) |

Encoders planned but not yet wired.

## Current Firmware: Continuous Velocity Mode

The firmware now uses **non-blocking motor control** with `micros()` timing:

- Motors run continuously at their set velocity until changed
- Commands are processed immediately (no blocking)
- STATE updates sent every 100ms regardless of commands
- Each motor has a struct tracking: step_pin, dir_pin, step_period, next_step_time, position, direction

**Commands:**
- `MOVE <x_speed> <y_speed>\n` - Set motor velocities
- `STOP 0 0\n` - Stop motors

**Velocity interpretation:**
- Positive value = forward direction
- Negative value = reverse direction
- Magnitude = delay in microseconds between step pulses (smaller = faster)
- 0 = stopped

## Controller Integration

`controller.py` maps 8BitDo joystick to motor commands:
- Left stick horizontal → X motor (base rotation)
- Left stick vertical → Y motor (shoulder)
- Deadzone: 0.1
- Scaling: joystick magnitude mapped to delay (full stick = 200µs fast, threshold = 800µs slow)

`main.py` runs the control loop:
- Sends velocity commands while joystick is active
- Sends stop command when joystick released

## KNOWN ISSUE: Y Motor Not Working

**Symptom:** Y motor gets very hot but does not move when commanded.

**What works:**
- X motor responds to joystick, runs smoothly in continuous velocity mode
- Commands are being received (X motor responds)

**What's broken:**
- Y motor does not step
- Motor is enabled (hot) but not moving
- Direct serial command `MOVE 0 400` does not move Y motor

**Possible causes to investigate:**
1. Wiring issue - Y step pin (60) may not be connected correctly
2. Code issue - something wrong with motor_y struct or updateMotor() for Y
3. Driver issue - Y axis stepper driver may be faulty
4. Pin issue - verify pin 60 is actually toggling

**Next debugging steps:**
1. Add debug output to confirm motor_y.step_period is being set
2. Test pin 60 directly with a simple blink test
3. Check wiring between Arduino pin 60 and Y driver STEP input
4. Swap X and Y drivers to rule out driver failure

**SAFETY:** Y motor overheats when enabled but not stepping. Disable Y motor (set Y_ENABLE_PIN HIGH) when not actively debugging.

## Files

- `firmware/firmware.ino` - Arduino code (continuous velocity mode)
- `robot.py` - `Arm` class with non-blocking `step(action)` method
- `main.py` - Joystick control loop
- `controller.py` - 8BitDo joystick mapping with deadzone and scaling
- `build.sh` - Compile and upload script

## Build Commands

```bash
./build.sh              # Compile and upload
arduino-cli monitor -p /dev/ttyACM1 -c baudrate=115200  # Serial monitor
```

## Session Notes

- Speed control: delay value in µs (smaller = faster). Originally was step count, now is velocity.
- Blocking vs non-blocking: Old firmware blocked during stepping. New firmware uses micros() for non-blocking step timing.
- Gym integration: Robot controls timing via STATE responses. Python waits for response to synchronize.
