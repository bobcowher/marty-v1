import numpy as np

import controller
from robot import Arm

from controller import Controller
import pygame
import time

robot = Arm()

controller = Controller()

# Action is [x_speed, y_speed] in µs delay (smaller = faster, sign = direction)
# 500 µs = ~1000 steps/sec per motor
# action = np.array([500, 500])
print("Controller connected. Use left stick to move robot. Ctrl+C to exit.")

COMMAND_RATE_HZ = 50  # Send commands at 50Hz max
command_interval = 1.0 / COMMAND_RATE_HZ

# Logitech Dual Action, confirmed 2026-10-19
START_BUTTON = 9  # calibrate: zero, home, forward limit, back limit
BACK_BUTTON = 8   # go home; cancels calibration in progress

CALIBRATION_STEPS = [
    ('zero',          "CALIBRATE: jog to vertical, then press Start"),
    ('home',          "CALIBRATE: jog to home, then press Start"),
    ('forward_limit', "CALIBRATE: jog to the forward limit, then press Start"),
    ('back_limit',    "CALIBRATE: jog to the back limit, then press Start"),
]


def calibration_press(step, captured):
    """Advance the calibration sequence on a Start press. Returns the new (step, captured)."""
    if step is None:
        print(CALIBRATION_STEPS[0][1])
        return 0, {}

    name = CALIBRATION_STEPS[step][0]
    robot.get_position()
    if name == 'zero':
        captured = {j: {'zero_raw': raw} for j, raw in enumerate(robot.encoders) if raw >= 0}
        if not captured:
            print("CALIBRATE: no encoder readings - cancelled")
            return None, {}
    else:
        for j, cal in captured.items():
            raw = robot.encoders[j]
            if raw < 0:
                print(f"CALIBRATE: lost encoder on joint {j} - cancelled")
                return None, {}
            cal[name] = round(robot.raw_to_deg(j, raw, cal['zero_raw']), 1)
    print(f"CALIBRATE: captured {name}: {captured}")

    step += 1
    if step < len(CALIBRATION_STEPS):
        print(CALIBRATION_STEPS[step][1])
        return step, captured

    for j, cal in captured.items():
        if not cal['back_limit'] < cal['home'] < cal['forward_limit']:
            print(f"CALIBRATE: WARNING joint {j} home is not between its limits")
    robot.save_calibration(captured)
    print("CALIBRATE: saved")
    return None, {}


homing = False
calib_step = None  # index into CALIBRATION_STEPS while calibrating
calib = {}

while True:
    loop_start = time.time()

    # Drain STATE every pass so the serial buffer never fills while sticks are idle
    robot.get_position()

    # Process pygame events (required for joystick to update)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # SDL turns SIGTERM/SIGINT into QUIT
            robot.stop()
            raise SystemExit
        if event.type == pygame.JOYBUTTONDOWN:
            print(f"button {event.button} pressed")
            if event.button == START_BUTTON:
                homing = False
                calib_step, calib = calibration_press(calib_step, calib)
            elif event.button == BACK_BUTTON:
                if calib_step is not None:
                    calib_step, calib = None, {}
                    print("CALIBRATE: cancelled")
                else:
                    homing = True
                    print("HOME: going home")

    action = controller.get_action()

    if action is not None:
        if homing:
            homing = False
            print("HOME: cancelled by stick input")
        print(action)
        robot.step(action)
    elif homing:
        home_action = robot.home_action()
        if home_action is None:
            homing = False
            robot.stop()
            print(f"HOME: done, joint_pos={robot.joint_pos()}")
        else:
            robot.step(home_action)

    # Rate limit to prevent flooding serial
    elapsed = time.time() - loop_start
    if elapsed < command_interval:
        time.sleep(command_interval - elapsed)




