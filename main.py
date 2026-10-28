import numpy as np

import controller
from calibration import Calibration
from robot import Arm
from voice_link import VoicePublisher

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
START_BUTTON = 9  # calibrate: per joint, vertical, home, min limit, max limit
BACK_BUTTON = 8   # go home; cancels calibration in progress

calibration = Calibration(robot, say=VoicePublisher().say)

homing = False

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
                calibration.press()
            elif event.button == BACK_BUTTON:
                if calibration.active:
                    calibration.cancel()
                else:
                    homing = True
                    print("HOME: going home")

    robot.enforce_limits = not calibration.active

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




