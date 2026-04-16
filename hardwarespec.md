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

## Motor 2: Shoulder (Y-axis) — NEW MOTOR (2026-04-08)
**Model:** 17HS24-2104S-PG5 (NEMA 17, 60mm body)
**Current:** 2.1A rated
**Resistance:** 1.6Ω per phase
**Inductance:** 3.0mH ± 20% (1KHz)
**Holding Torque:** 65Ncm (without gearbox)
**Gearbox:** 5.18:1 planetary
**Total Torque:** 65 × 5.18 = 337 N⋅cm (25% more than old motor)
**Output Shaft:** 8mm diameter with D-flat (15mm D-cut length)

**DRV8825 VREF:** 1.68V (start), can go up to 2.1V if needed
**Expected Current:** 2.1A RMS

**Pins:** STEP=60, DIR=61, ENABLE=56
**Wiring (per manufacturer specs):**
- A+ (Black) → 2A
- A- (Green) → 2B
- B+ (Red) → 1A
- B- (Blue) → 1B

**Notes:**
- Replaced defective 17HS19-1684S-PG5 which had internal coil defect (Red-Blue coil measured weak voltage)
- Using DRV8825 driver (2.5A max) instead of TMC2209 (2.0A max) — DRV8825 runs hot at this current
- 8mm D-shaft requires D-bore or keyed pulley for no-slip operation
- Temporarily using existing round-bore pulley with set screw + Loctite for testing
- Plan to upgrade to proper 16T D-bore pulley before RL work

**Recommended future driver: BTT TMC5160**
- Handles up to 4.4A RMS — comfortably within rating for this motor
- StealthChop quiet operation (same as TMC2209)
- Pololu-style board fits RAMPS slot
- Requires SPI wiring + firmware changes (not standalone like DRV8825/TMC2209)
- More expensive — defer until ready to invest in proper driver setup for RL work

---

## Motor 3: Elbow (Z-axis)
**Model:** 17HS13-0404S-PG5
**Current:** 0.4A rated
**Gearbox:** 5:1 planetary

**VREF:** 0.28V (start at 70%), tune up to 0.4V rated max
**Calculation:** 0.4A × 1.0 = 0.4V rated max; 0.4A × 0.70 = 0.28V for 70% start
**Expected Peak Current:** ~0.28-0.4A

**Pins:** STEP=46, DIR=48, ENABLE=62
**Wiring:**
- Black → 2B (A+)
- Green → 2A (A-)
- Red → 1A (B+)
- Blue → 1B (B-)

**Notes:** Previously used as shoulder motor. Confirmed working at 0.4V Vref — consistent with the corrected formula above.

---

## Motor 4: Wrist Tilt (E0)
**Model:** 14HS13-0804S-PG19
**Current:** 0.8A rated
**Gearbox:** 19:1 planetary (high reduction)

**VREF:** 0.56V (start at 70%), tune up to 0.8V rated max
**Calculation:** 0.8A × 1.0 = 0.8V rated max; 0.8A × 0.70 = 0.56V for 70% start
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
**Current:** 0.67A rated (if Nema11) OR 1.68A (if actually 17HS19-1684S-PG5)

**VREF:** 0.47V (if 0.67A) OR 1.18V (if 1.68A) — confirm motor model first
**Calculation:** 0.67A × 1.0 = 0.67V rated max; 0.67A × 0.70 = 0.47V for 70% start

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
Motor 2 (shoulder) uses a DRV8825. Formula depends on the board's sense resistors:
```
Vref = I_RMS × 0.5   (0.1Ω Rsense — Pololu and most name-brand boards)
Vref = I_RMS × 0.4   (0.08Ω Rsense — some Chinese clones)
```
Example for 2.1A motor:  0.1Ω board → 1.05V,  0.08Ω board → 0.84V

**If unsure which board you have**, start at 0.84V and work up — it's within safe range for either variant.
DRV8825 uses SpreadCycle (no StealthChop torque issues) but is louder than TMC2209.


