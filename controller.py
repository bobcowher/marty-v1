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

    def debug_inputs(self):
        """Print all button and axis states for mapping."""
        for i in range(self.joystick.get_numbuttons()):
            if self.joystick.get_button(i):
                print(f"  button {i} pressed")
        for i in range(self.joystick.get_numaxes()):
            v = self.joystick.get_axis(i)
            if abs(v) > 0.1:
                print(f"  axis {i} = {v:.2f}")

    def get_action(self):
        """
        Map PlayStation controller input to the robot's action space.
        """
        action = np.zeros(5)  # [x, y, z, e0, servo_step]

        # Map left joystick to panda0_joint1 and panda0_joint2 angular velocity
        action[0] = self.joystick.get_axis(0)  # Left stick horizontal - This is the base rotation
        action[1] = self.joystick.get_axis(1)  # Left stick vertical - This is the shoulder movement

        action[2] = self.joystick.get_axis(3)  # Right stick vertical - This is the arm extension.
        action[3] = self.joystick.get_axis(2)  # Right stick horizontal - This is the arm extension.

        action[1] = action[1] * -1

        dead_zone = 0.15

        # Apply deadzone and remap to full range (axes only, not servo)
        signs = np.sign(action[:4])
        magnitudes = np.abs(action[:4])

        # Zero out values in deadzone, remap rest: deadzone->0, 1.0->1.0
        in_deadzone = magnitudes < dead_zone
        remapped = np.where(
            in_deadzone,
            0.0,
            (magnitudes - dead_zone) / (1 - dead_zone)
        )
        action[:4] = signs * remapped

        # LB (button 4) = -1, RB (button 5) = +1
        lb = self.joystick.get_button(5)
        rb = self.joystick.get_button(6)
        action[4] = rb - lb  # +1, -1, or 0

        if np.all(action == 0):
            action = None
        else:
            # Because these are on the same axis, null out one or the other to prevent contamination.
            if np.abs(action[0]) > np.abs(action[1]):
                action[1] = 0
            else:
                action[0] = 0

            if np.abs(action[2]) > np.abs(action[3]):
                action[3] = 0
            else:
                action[2] = 0

        return action
