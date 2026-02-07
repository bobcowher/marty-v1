import numpy as np

from robot import Arm

robot = Arm(serial_interface='/dev/ttyACM1')

# Action is [x_speed, y_speed] in µs delay (smaller = faster, sign = direction)
# 500 µs = ~1000 steps/sec per motor
action = np.array([500, 500])

for i in range(10):
    position = robot.step(action)
    print(f"Step {i}: action={action}, position={position}")

    action = action * -1  # Reverse direction





