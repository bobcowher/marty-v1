import serial
import time

class Arm():

    def __init__(self, serial_interface='/dev/ttyACM1') -> None:
        # Controls -
        # action [base, shoulder]
        # base - positive = right, negative = left
        # shoulder - positive = forward, negative = back

        self.server = serial.Serial(serial_interface, 115200, timeout=10)
        time.sleep(2)  # Wait for Arduino bootloader

        # Position tracking (from step counts)
        self.position = [0, 0]

    def step(self, action):
        """
        Send velocity command and wait for step completion.

        Args:
            action: [x_speed, y_speed] where speed is delay in µs (sign = direction)
                    Smaller values = faster movement

        Returns:
            observation: current position [x, y] as step counts
        """
        # Build and send command
        move_string = f"MOVE {int(action[0])} {int(action[1])}\n"
        self.server.write(move_string.encode())

        # Block until robot signals step complete
        response = self.server.readline().decode().strip()

        # Parse state from response
        if response.startswith("STATE"):
            parts = response.split()
            if len(parts) >= 3:
                self.position = [int(parts[1]), int(parts[2])]
        elif response.startswith("ERROR"):
            print(f"Robot error: {response}")

        return self.position

    def stop(self):
        """Stop all motors."""
        self.server.write(b"STOP 0 0\n")
        response = self.server.readline().decode().strip()
        return response

    def reset_position(self):
        """Reset position tracking to zero."""
        self.position = [0, 0]
