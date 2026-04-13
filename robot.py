import serial
from serial.tools import list_ports
import time
import numpy as np

class Arm():

    def __init__(self, serial_interface=None) -> None:
        # Controls -
        # action [base, shoulder]
        # base - positive = right, negative = left
        # shoulder - positive = forward, negative = back

        if serial_interface is None:
            serial_interface = self.get_arduino_port()

        self.server = serial.Serial(serial_interface, 115200, timeout=0.01)
        time.sleep(2)  # Wait for Arduino bootloader

        # Clear any startup messages
        self.server.reset_input_buffer()

        # Position tracking (from step counts + servo angle)
        self.position = [0, 0, 0, 0, 0, 90]

    def step(self, action):
        """
        Send velocity command. Motors continue at this velocity until next command.

        Args:
            action: [x_speed, y_speed, z_speed, e0_speed, e1_speed, servo_step]
                    Motor speeds are delay in µs (sign = direction, smaller = faster, 0 = stopped)
                    servo_step is discrete: -1, 0, or +1

        Returns:
            observation: current position [x, y, z, e0, e1, gripper_angle]
        """

        MIN_DELAY = 200
        MAX_DELAY = 1800

        motor_action = action[:5]
        servo_step = int(action[5])

        signs = np.sign(motor_action)
        magnitudes = np.abs(motor_action)

        # Map magnitude 0.1->1.0 to delay MAX->MIN
        # t=0 at mag=0.1, t=1 at mag=1.0
        t = (magnitudes - 0.1) / 0.9
        t = np.clip(t, 0, 1)
        delays = MAX_DELAY - t * (MAX_DELAY - MIN_DELAY)

        delays[3] = int(delays[3] * 0.5)

        # Where magnitude is 0 (deadzone), set delay to 0 (no movement)
        delays = np.where(magnitudes == 0, 0, delays)

        action_scaled = signs * delays

        # Build and send command
        move_string = "MOVE"
        for val in action_scaled:
            move_string += " " + str(int(val))
        move_string += " " + str(servo_step)
        move_string += "\n"

        print(move_string)

        self.server.write(move_string.encode())
        self._read_state()

        return self.position

    def _read_state(self):
        """Read and parse any available state updates from the robot."""
        while self.server.in_waiting > 0:
            try:
                response = self.server.readline().decode().strip()
                if response.startswith("STATE"):
                    parts = response.split()
                    if len(parts) >= 7:
                        self.position = [int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5]), int(parts[6])]
            except:
                pass  # Ignore decode errors

    def stop(self):
        """Stop all motors."""
        self.server.write(b"STOP 0 0 0 0 0 0\n")
        return self.position

    def get_position(self):
        """Get latest position without sending a command."""
        self._read_state()
        return self.position

    def reset_position(self):
        """Reset position tracking to zero."""
        self.position = [0, 0, 0, 0, 0, 90]

    def get_arduino_port(self):
        """Returns first Arduino port or None"""
        arduino_ports = [
            p.device
            for p in list_ports.comports()
            if 'Arduino' in p.description or 
               p.vid in [0x2341, 0x1A86, 0x0403]  # Arduino, CH340, FTDI
        ]
        return arduino_ports[0] if arduino_ports else None
