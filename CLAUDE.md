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

## KNOWN ISSUE: New Shoulder Motor Has No Torque

**Motor swap:** Replaced old shoulder motor (17HS13-0404S-PG5, 0.4A) with new motor (17HS19-1684S-PG5, 1.68A).

**Symptom:** New motor steps but has almost no torque. Arm falls under gravity. "Thumping" sound when slipping.

**New motor specs (17HS19-1684S-PG5):**
- Rated current: 1.68A
- Phase resistance: 1.8Ω
- Inductance: 3.2mH
- Holding torque: 52Ncm (without gearbox)
- Gearbox: 5.18:1 planetary
- Step angle: 0.35° (with gearbox)

**What we ruled out:**
- ✓ Firmware is correct - confirmed pin 60 is toggling, position counter changes
- ✓ Motor windings good - Black↔Green: 1.9Ω, Red↔Blue: 1.9Ω, cross-pairs open
- ✓ Wiring correct - Black→2B, Green→2A, Red→1A, Blue→1B
- ✓ Coil phase - tried swapping 2A/2B, no change
- ✓ Gearbox smooth - no binding or grit when turned by hand
- ✓ Driver not damaged - tried fresh TMC2209, same behavior
- ✓ Power supply adequate - 24V

**Driver setup:**
- TMC2209 v3 from BigTreeTech
- Sense resistors: R110 (0.11Ω)
- RAMPS 1.4 board from Elegoo
- Microstepping: MS1 and MS2 jumpered (1/16 step)
- NOT using UART mode (standalone only)

**Vref experiments:**
- 0.52V (~1.89A calculated) - terrible torque
- 1.1V - terrible torque, then driver thermal shutdown after a few seconds
- Original setting was 1.6V - way too high, likely caused initial issues

**Vref formula confusion:**
- My formula: Vref = I × 2.5 × Rsense = 1.68 × 0.275 = 0.46V
- Browser Claude formula: Vref ≈ 1.2V for 1.68A
- Neither setting produced adequate torque

**Hypothesis:** TMC2209 in standalone mode may be incompatible with this motor's characteristics (high inductance, different current requirements). StealthChop mode may be limiting torque.

**Next step:** Test with DRV8825 driver (arriving Wednesday). If motor works with DRV8825, the issue is TMC2209 standalone mode. If motor still fails, motor may be defective despite passing resistance tests.

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
- Old shoulder motor: 17HS13-0404S-PG5 (0.4A, 5:1 gearbox) - worked fine at 0.4V Vref
- New shoulder motor: 17HS19-1684S-PG5 (1.68A, 5.18:1 gearbox) - purchased from StepperOnline via Amazon

## CRITICAL: Arduino Mega Issues (2026-03-29)

**Both Arduino Mega boards are non-functional due to polyfuse/short circuit issues:**

1. **"New" replacement Arduino Mega:**
   - Powers on briefly then dies (polyfuse trips)
   - Does not enumerate as USB device
   - USB port solder joints look suspect (poor connection on left shield tab)
   - Likely has internal short circuit drawing >500mA
   - Status: **DEAD**

2. **"Old" original Arduino Mega:**
   - Also not enumerating as USB device after testing
   - May have same polyfuse trip condition
   - Was working previously but now shows same symptoms
   - Status: **UNKNOWN** - needs 15min unplugged cooldown, then retest

**Polyfuse behavior (from Elegoo docs):**
- Resettable fuse trips at >500mA to protect USB port
- Breaks connection automatically when overcurrent detected
- Requires cooldown time (10-15 minutes unplugged) to reset
- If short persists, will trip again immediately

**What we know:**
- `/dev/ttyACM0` is DYGMA DEFY keyboard, NOT Arduino
- `build.sh` updated to use `/dev/ttyACM0` (was ACM1) but this was incorrect
- Arduino should appear as new device (ACM1 or ttyUSB0) when plugged in
- Neither board appears in `lsusb` output (no USB enumeration at all)
- Tested multiple USB cables and ports - problem is on the boards

**Root cause hypothesis:**
- Likely caused by wiring error or ground loop during motor testing
- High VREF settings (1.1V-1.6V) or improper connections may have damaged USB circuit
- Possible reverse voltage or overvoltage from 24V system reached Arduino 5V rail
- Both boards damaged the same way suggests systematic issue in setup

**Next steps (tomorrow):**
1. Let old Arduino sit unplugged for 15+ minutes to reset polyfuse
2. Test old board with nothing connected - if still dead, both boards are toast
3. If old board works, check for shorts with multimeter (5V to GND should be open/high-Z)
4. **Order new Arduino Mega** (genuine or quality clone) if both are dead
5. Before connecting new board: audit all wiring, verify RAMPS connections, check for shorts
6. See `hardwarespec.md` for correct VREF settings (much lower than previously used)

**Files updated tonight:**
- `hardwarespec.md` - Complete VREF calculations and wiring reference for all 5 motors
- `build.sh` - Port updated (though incorrect device was identified)
