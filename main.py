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

while True:
    loop_start = time.time()

    # Process pygame events (required for joystick to update)
    pygame.event.pump()

    action = controller.get_action()

    if action is not None:
        print(action)
        robot.step(action)

    # Rate limit to prevent flooding serial
    elapsed = time.time() - loop_start
    if elapsed < command_interval:
        time.sleep(command_interval - elapsed)




