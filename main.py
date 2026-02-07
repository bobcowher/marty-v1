import numpy as np

from robot import Arm

robot = Arm(serial_interface='/dev/ttyACM1')
action = np.array([1000, 1000])

for i in range(10):
    robot.step(action)

    action = action * -1
    print(action)
    # robot.step([1000, -1000])





