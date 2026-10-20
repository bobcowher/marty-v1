import json
import math
import os
import serial
from serial.tools import list_ports
import subprocess
import time
import numpy as np

CALIBRATION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'calibration.json')
ENCODER_COUNTS = 4096

# +1 if a positive action raises that joint's raw encoder reading, so positive
# action always means increasing joint angle. Only the shoulder (1) is verified
# (encoder_check.py, 2026-10-19); set the others when their encoders go in.
ENCODER_SIGN = [1, 1, 1, 1, 1]

HOME_TOLERANCE_DEG = 1.0
HOME_SLOW_DEG = 10.0     # start slowing down this far from home
HOME_MIN_SPEED = 0.15    # normalized action, ~5 deg/s on the shoulder
HOME_MAX_SPEED = 0.5     # ~8 deg/s on the shoulder

class Arm():

    def __init__(self, serial_interface=None) -> None:
        # Controls -
        # action [base, shoulder]
        # base - positive = right, negative = left
        # shoulder - positive = forward, negative = back

        if serial_interface is None:
            serial_interface = self.get_arduino_port()

        if serial_interface is None:
            raise RuntimeError("No Arduino port found")

        # Clear HUPCL at OS level so DTR is not dropped on open or close.
        # DTR going LOW is what pulses RESET on the Arduino — this prevents that.
        subprocess.run(['stty', '-F', serial_interface, '-hupcl'], capture_output=True)

        self.server = serial.Serial(serial_interface, 115200, timeout=0.01)
        time.sleep(0.1)

        # Clear any startup messages
        self.server.reset_input_buffer()

        # Position tracking (from step counts + servo angle)
        self.position = [0, 0, 0, 0, 0, 90]

        # Raw AS5600 angle per joint, 0-4095; -1 = no sensor, no magnet, or read error
        self.encoders = [-1, -1, -1, -1, -1]

        # {joint: {'zero_raw', 'home', 'forward_limit', 'back_limit'}}, angles in degrees
        self.calibration = self.load_calibration()

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
                    if len(parts) >= 12:
                        self.encoders = [int(p) for p in parts[7:12]]
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

    def raw_to_deg(self, joint, raw, zero_raw):
        """Degrees from zero, wrapped to [-180, 180)."""
        counts = (raw - zero_raw + ENCODER_COUNTS // 2) % ENCODER_COUNTS - ENCODER_COUNTS // 2
        return ENCODER_SIGN[joint] * counts * 360.0 / ENCODER_COUNTS

    def joint_pos(self):
        """Joint angles in degrees from vertical; NaN where a joint is uncalibrated or has no reading."""
        self._read_state()
        pos = [math.nan] * 5
        for j, cal in self.calibration.items():
            if self.encoders[j] >= 0:
                pos[j] = self.raw_to_deg(j, self.encoders[j], cal['zero_raw'])
        return pos

    def home_action(self):
        """Action that moves calibrated joints toward home, or None once all are within tolerance."""
        homed = {j: cal for j, cal in self.calibration.items() if 'home' in cal}
        if not homed:
            print("No home saved - press Start to calibrate")
            return None

        pos = self.joint_pos()
        action = np.zeros(6)
        for j, cal in homed.items():
            if math.isnan(pos[j]):
                print(f"No encoder reading on joint {j} - homing stopped")
                return None
            err = cal['home'] - pos[j]
            if abs(err) <= HOME_TOLERANCE_DEG:
                continue
            speed = HOME_MIN_SPEED + (HOME_MAX_SPEED - HOME_MIN_SPEED) * min(abs(err) / HOME_SLOW_DEG, 1.0)
            action[j] = np.sign(err) * speed

        return None if np.all(action == 0) else action

    def load_calibration(self):
        if not os.path.exists(CALIBRATION_FILE):
            return {}
        with open(CALIBRATION_FILE) as f:
            return {int(j): cal for j, cal in json.load(f).items()}

    def save_calibration(self, captured):
        """Merge captured joints into the calibration file; other joints keep their values."""
        self.calibration.update(captured)
        with open(CALIBRATION_FILE, 'w') as f:
            json.dump({str(j): cal for j, cal in sorted(self.calibration.items())}, f, indent=2)

    def get_arduino_port(self):
        """Returns first Arduino port or None"""
        arduino_ports = [
            p.device
            for p in list_ports.comports()
            if 'Arduino' in p.description or 
               p.vid in [0x2341, 0x1A86, 0x0403]  # Arduino, CH340, FTDI
        ]
        return arduino_ports[0] if arduino_ports else None
