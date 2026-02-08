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

last_action_was_moving = False

while True:
    # Process pygame events (required for joystick to update)
    pygame.event.pump()

    action = controller.get_action()

    if action is not None:
        robot.step(action)
    #     robot.step(action)
    #     last_action_was_moving = True
    # else:
    #     # Joystick released - stop motors
    #     if last_action_was_moving:
    #         robot.step([0, 0])
    #         print("Stopped")
    #         last_action_was_moving = False
    #     time.sleep(0.01)  # Small sleep when idle
    #




