import numpy as np
import pygame

class Controller:
    def __init__(self):
        self.gripper_closed = None

        pygame.init()
        pygame.joystick.init()

        # Assuming only one joystick is connected
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

    def get_action(self):
        """
        Map PlayStation controller input to the robot's action space.
        """
        action = np.zeros(2)  # Assuming 9 action dimensions as specified

        gripper_button_pressed = False

        # Map left joystick to panda0_joint1 and panda0_joint2 angular velocity
        action[0] = self.joystick.get_axis(0)  # Left stick horizontal
        action[1] = self.joystick.get_axis(1)  # Left stick vertical


        # action[0] = action[0] * -1
        action[1] = action[1] * -1

        dead_zone = 0.15

        # Apply deadzone and remap to full range
        signs = np.sign(action)
        magnitudes = np.abs(action)

        # Zero out values in deadzone, remap rest: deadzone->0, 1.0->1.0
        in_deadzone = magnitudes < dead_zone
        remapped = np.where(
            in_deadzone,
            0.0,
            (magnitudes - dead_zone) / (1 - dead_zone)
        )
        action = signs * remapped

        if np.all(action == 0) and not gripper_button_pressed:
            action = None
        else:
            # Because these are on the same axis, null out one or the other to prevent contamination.
            if np.abs(action[0]) > np.abs(action[1]):
                action[1] = 0
            else:
                action[0] = 0

        return action
