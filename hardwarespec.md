# Robot Arm Motor Configuration Reference

## Driver Settings: TMC2209 v3 (BigTreeTech)
- Sense resistors: R110 = 0.11Ω
- Board: RAMPS 1.4 (Elegoo)
- Microstepping: MS1 + MS2 jumpered = 1/16 step
- Mode: Standalone (no UART)
- Power: 24V supply

## VREF Calculation Formula
For TMC2209 v3 with R110 (0.11Ω) sense resistors:
```
Vref = (I_rated × (Rs + 0.02) × 2.5) / 0.325
     = I_rated × (0.13 × 2.5) / 0.325
     = I_rated × 1.0
```
With R110 sense resistors the scaling factor is exactly 1.0 — Vref equals the motor's rated peak current in volts.

**CRITICAL:** Start at 70-80% of rated current, measure torque, adjust up if needed.
TMC2209 in StealthChop may limit torque on high-inductance motors.

---

## Motor 1: Base Rotation (X-axis)
**Model:** 17HS19-2004S1
**Current:** 2.0A rated
**VREF:** 1.40V (start at 70%), tune up to 2.0V rated max
**Calculation:** 2.0A × 1.0 = 2.0V rated max; 2.0A × 0.70 = 1.4V for 70% start
**Expected Peak Current:** ~1.4-2.0A

**Pins:** STEP=54, DIR=55, ENABLE=38
**Wiring (typical NEMA17):**
- Black → 2B
- Green → 2A
- Red → 1A
- Blue → 1B

---

## Motor 2: Shoulder (Y-axis) — NEMA 23 + DM542TE (2026-10-04)
**Model:** 23HS22-2904S (NEMA 23)
**Current:** 2.9A rated
**Holding Torque:** 1.2 Nm
**Mounting:** Full shoulder redesign for the NEMA 23 frame
**Reduction:** 50:1

**Driver:** StepperOnline DM542TE (external, opto-isolated inputs)
- Supply range: **24–50V** (per label). 24V is the floor; trim the PSU to ~26V so the rail doesn't sag into undervoltage alarm under load.
- Signal inputs: 5–24V, so Arduino 5V logic drives them directly.
- **Label table is inverted vs generic DM542 tables online — always use the label on the driver.**

**DIP switches:**
| SW1 | SW2 | SW3 | SW4 | SW5 | SW6 | SW7 | SW8 |
|-----|-----|-----|-----|-----|-----|-----|-----|
| off | off | on  | on  | on  | off | on  | on  |

- SW1–3: 2.8A peak / 2.0A RMS (start). Step up: 3.3A peak / 2.4A RMS = SW1 on, SW2 off, SW3 on.
- SW4 on: full current at standstill (half current risks the arm dropping under gravity).
- SW5–8: 800 pulses/rev (2026-10-11; was 3200). 50:1 gearbox made 3200 too slow (~11°/s at the 200µs firmware floor); 800 gives ~45°/s. Feels slightly aggressive — fine-tune later. Fallback: 1600 = SW5 off, SW6 off, SW7 on, SW8 on.
- Shoulder position counts are 4× coarser than the 1/16 joints — account for this in RL/encoder work.

**Signal wiring (common-cathode):**
- PUL+ → pin 60 (Y STEP)
- DIR+ → pin 61 (Y DIR)
- PUL−, DIR−, ENA− → Arduino GND
- ENA+ → unconnected (driver always enabled). If wired to pin 56: LOW = enabled, matches firmware.
- DRV8825 removed from the RAMPS Y socket.

**Motor wiring (coil pairs confirmed by meter):**
- A+ (Black), A− (Green) — coil 1
- B+ (Red), B− (Blue) — coil 2
- If direction is backwards, swap A+ and A−.
- 4 red blinks on the driver = phase error (open/mis-paired coil). Measure at the screw terminals: each pair ~1Ω, across pairs open (0.L).

**Previous shoulder:** 17HS24-2104S-PG5 (2.1A, 5.18:1 gearbox) on DRV8825 — DRV8825 ran hot at its limit. Replaced by this setup.

---

## Motor 3: Elbow (Z-axis) — moved from shoulder (2026-10-11)
**Model:** 17HS24-2104S-PG5 (NEMA 17, 60mm body)
**Current:** 2.1A rated
**Resistance:** 1.6Ω per phase
**Inductance:** 3.0mH ± 20% (1KHz)
**Holding Torque:** 65Ncm (without gearbox)
**Gearbox:** 5.18:1 planetary, plus 3:1 pulley = ~15.5:1 total
**Output Shaft:** 8mm diameter with D-flat (15mm D-cut length)

**Driver:** DRV8825, moved over from the shoulder along with the motor, same VREF as it ran there.
**VREF:** Measure and record. Old notes said 1.68V, but by the DRV8825 formula below that's ~3.4A, beyond the DRV8825's 2.5A max — the right setting for 2.1A is ~1.05V (0.1Ω board) or ~0.84V (0.08Ω board).

**Pins:** STEP=46, DIR=48, ENABLE=62
**Wiring:** Black/Green = one coil, Red/Blue = other coil.

**Notes:**
- Replaced 17HS13-0404S-PG5 (0.4A, 5:1), which was under-torqued for the redesigned arm. Torque now good.
- Had intermittent clicking with the old motor that cleared itself; watch for it returning (would point at cable/driver).
- DRV8825 ran hot driving this motor on the shoulder — keep a heatsink on it.

---

## Motor 4: Wrist Tilt (E0)
**Model:** 14HS13-0804S-PG19
**Current:** 0.8A rated
**Gearbox:** 19:1 planetary (high reduction)

**VREF:** 0.64V (start at 80%), tune up to 0.8V rated max
**Expected Peak Current:** ~0.56-0.8A

**Pins:** STEP=26, DIR=28, ENABLE=24
**Wiring (color mapping):**
- Motor Red → Black terminal (2B)
- Motor Green → Green terminal (2A)
- Motor Yellow → Red terminal (1A)
- Motor Blue → Blue terminal (1B)

---

## Motor 5: Wrist Rotation (E1)
**Model:** (Verify - listed as 17HS19-1684S-PG5 but described as Nema11 0.67A)
**Current:** 0.67A rated (if Nema11)

**VREF:** 0.53V 

**Pins:** STEP=36, DIR=34, ENABLE=30
**Wiring:** TBD - verify motor model and color code

**ACTION NEEDED:** Confirm actual motor model before wiring.

---

## Motor 6: Gripper
**Model:** B0FJLBK8X7 (Amazon ASIN - need model specs)
**VREF:** TBD - measure motor resistance, get rated current from listing

**ACTION NEEDED:** Look up specs or measure motor parameters.

---

## Wiring Standard
All drivers use RAMPS 1.4 pinout (above). Standard NEMA stepper colors:
- **Black/Green pair:** Coil A (measure ~1.8-2Ω between them)
- **Red/Blue pair:** Coil B (measure ~1.8-2Ω between them)
- Cross-pairs should be open circuit

**If torque is weak:**
1. Swap one coil's polarity (e.g., swap 2A↔2B)
2. Increase Vref by 0.05V increments
3. Watch for driver heating (>50°C means reduce Vref)

---

## Troubleshooting VREF
- **No torque, motor buzzes:** Vref too low OR wrong wiring
- **Driver shuts down (goes silent):** Thermal protection, Vref too high
- **Motor skips steps under load:** Increase Vref 10-20%
- **Driver heatsink hot (>60°C):** Decrease Vref or add cooling

## DRV8825 Driver Formula
Motor 3 (elbow) uses a DRV8825. Formula depends on the board's sense resistors:
```
Vref = I_RMS × 0.5   (0.1Ω Rsense — Pololu and most name-brand boards)
Vref = I_RMS × 0.4   (0.08Ω Rsense — some Chinese clones)
```
Example for 2.1A motor:  0.1Ω board → 1.05V,  0.08Ω board → 0.84V

**If unsure which board you have**, start at 0.84V and work up — it's within safe range for either variant.
DRV8825 uses SpreadCycle (no StealthChop torque issues) but is louder than TMC2209.


