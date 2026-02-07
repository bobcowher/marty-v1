import serial
import time

class Arm():

    def __init__(self, serial_interface) -> None:
        # Controls - 
        # action [base, shoulder]
        # base - positive = right, negative = left
        # shoulder - positive = forward, negative = back

        self.server = serial.Serial(serial_interface, 115200, timeout=10)
        time.sleep(2)

    def step(self, action):
        move_string = "MOVE"

        for move in action:
            move_string = move_string + " "
            move_string = move_string + str(move)

        move_string = move_string + '\n'

        move_string = move_string.encode()

        print(move_string)

        self.server.write(move_string) 

        time.sleep(0.1)
