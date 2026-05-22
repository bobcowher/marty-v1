import numpy as np
import pygame
import time

class Controller:
    def __init__(self, timeout=300, retry_interval=5):
        self.gripper_closed = None

        pygame.init()
        pygame.joystick.init()

        self.joystick = self._wait_for_joystick(timeout, retry_interval)

    def _wait_for_joystick(self, timeout, retry_interval):
        deadline = time.time() + timeout
        while True:
            pygame.joystick.quit()
            pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                joystick = pygame.joystick.Joystick(0)
                joystick.init()
                print(f"Joystick connected: {joystick.get_name()}")
                return joystick
            remaining = deadline - time.time()
            if remaining <= 0:
                raise RuntimeError("Timed out waiting for joystick after 5 minutes")
            print(f"No joystick found. Retrying in {retry_interval}s ({int(remaining)}s remaining)...")
            time.sleep(retry_interval)

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
        action = np.zeros(6)  # [x, y, z, e0, e1, servo_step]

        action[0] = self.joystick.get_axis(0)  # Left stick horizontal - base rotation
        action[1] = self.joystick.get_axis(1)  # Left stick vertical   - shoulder
        action[4] = self.joystick.get_axis(2)  # Right stick horizontal 
        action[2] = self.joystick.get_axis(3)  # Right stick vertical  - elbow

        dead_zone = 0.15

        # Apply deadzone and remap to full range (analog axes only)
        dead_zone_indices = [0,1,2,4]
        signs = np.sign(action[dead_zone_indices])
        magnitudes = np.abs(action[dead_zone_indices])

        in_deadzone = magnitudes < dead_zone
        remapped = np.where(
            in_deadzone,
            0.0,
            (magnitudes - dead_zone) / (1 - dead_zone)
        )
        action[dead_zone_indices] = signs * remapped

        # L1 (button 5) = up, R1 (button 6) = down — wrist tilt
        l1 = self.joystick.get_button(5)
        r1 = self.joystick.get_button(6)
        action[3] = l1 - r1  # +1 (up), -1 (down), 0 (neither)

        # L2 (button 7) / R2 (button 8) — wrist rotation
        # l2 = self.joystick.get_button(7)
        # r2 = self.joystick.get_button(8)
        # action[4] = r2 - l2  # -1, 0, or +1

        # action[5] = servo step — unassigned until servo is connected

        if np.all(action == 0):
            action = None
        else:
            # Null out the weaker axis on left stick to prevent contamination
            if np.abs(action[0]) > np.abs(action[1]):
                action[1] = 0
            else:
                action[0] = 0
            
            if np.abs(action[2]) > np.abs(action[4]):
                action[4] = 0
            else:
                action[2] = 0

        return action
