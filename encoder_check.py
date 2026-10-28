"""Move one joint a short way and back, comparing encoder change to step count.

Stop the marty service first (it holds the serial port):
    systemctl --user stop marty && python encoder_check.py [joint]; systemctl --user start marty

joint: 1 shoulder (default), 2 elbow
"""
import sys
import time

from robot import Arm

JOINT = int(sys.argv[1]) if len(sys.argv) > 1 else 1
STEPS_PER_JOINT_REV = {
    1: 800 * 50,             # shoulder: DM542TE at 800 pulses/rev, 50:1 gearbox
    2: 44000,                # elbow: measured 2026-10-27 (~13.7:1 at 1/16; nominal 5.18 x 3 would be 49,700)
}[JOINT]
ENCODER_COUNTS = 4096
SPEED = 0.3       # normalized stick value, ~700 steps/s
MOVE_SECONDS = 1.5


def settle(arm, seconds=0.5):
    """Hold still long enough for every encoder to be re-read, then return state."""
    end = time.time() + seconds
    while time.time() < end:
        arm.get_position()
        time.sleep(0.02)
    return arm.position[JOINT], arm.encoders[JOINT]


def jog(arm, speed, seconds):
    action = [0, 0, 0, 0, 0, 0]
    action[JOINT] = speed
    end = time.time() + seconds
    while time.time() < end:
        arm.step(action)  # resend under the 150ms firmware watchdog
        time.sleep(0.05)
    arm.stop()


def encoder_delta(a, b):
    """Shortest signed difference between two raw readings, handling wrap at 4096."""
    return (b - a + ENCODER_COUNTS // 2) % ENCODER_COUNTS - ENCODER_COUNTS // 2


arm = Arm()
time.sleep(2)  # opening the port can reset the Mega; let it boot
steps0, enc0 = settle(arm, 1.0)
print(f"joint {JOINT} start:  steps={steps0} enc={enc0}")

for label, speed in [("forward", SPEED), ("back", -SPEED)]:
    jog(arm, speed, MOVE_SECONDS)
    steps1, enc1 = settle(arm)
    d_steps = steps1 - steps0
    d_enc = encoder_delta(enc0, enc1)
    expected = d_steps * ENCODER_COUNTS / STEPS_PER_JOINT_REV
    print(f"{label:8s} steps {d_steps:+6d}  enc {d_enc:+5d}  expected ±{abs(expected):6.1f}  "
          f"joint {d_enc * 360 / ENCODER_COUNTS:+6.1f} deg  "
          f"measured {abs(d_steps * ENCODER_COUNTS / d_enc) if d_enc else float('nan'):.0f} steps/rev")
    steps0, enc0 = steps1, enc1
