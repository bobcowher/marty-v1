import math

import pytest

import robot
from robot import Arm


def make_arm(encoders, calibration):
    arm = Arm.__new__(Arm)  # skip the serial port
    arm.encoders = encoders
    arm.calibration = calibration
    arm._read_state = lambda: None
    return arm


def test_raw_to_deg_wraps_across_zero():
    arm = make_arm([-1] * 5, {})
    assert arm.raw_to_deg(0, 4090, 10) == pytest.approx(-16 * 360 / 4096)
    assert arm.raw_to_deg(0, 10, 4090) == pytest.approx(16 * 360 / 4096)


def test_shoulder_behind_vertical_is_negative():
    # Real readings: vertical 919, home 1215 (raw rises going back)
    arm = make_arm([-1, 1215, -1, -1, -1], {1: {'zero_raw': 919}})
    pos = arm.joint_pos()
    assert pos[1] == pytest.approx(-296 * 360 / 4096)  # about -26 deg
    assert all(math.isnan(p) for i, p in enumerate(pos) if i != 1)


def test_home_action_drives_toward_home_then_stops():
    # Shoulder: positive action moves back, so forward is a negative action
    cal = {1: {'zero_raw': 919, 'home': -25.1}}
    behind = make_arm([-1, 919 + 500, -1, -1, -1], cal)  # ~-44 deg, behind home
    assert behind.home_action()[1] == pytest.approx(-robot.HOME_MAX_SPEED)  # forward, full speed

    ahead = make_arm([-1, 919 + 250, -1, -1, -1], cal)  # ~-22 deg, ahead of home
    assert robot.HOME_MIN_SPEED < ahead.home_action()[1] < robot.HOME_MAX_SPEED  # back, slowing

    at_home = make_arm([-1, 919 + 286, -1, -1, -1], cal)  # -25.1 deg
    assert at_home.home_action() is None


def test_home_action_stops_on_lost_encoder():
    arm = make_arm([-1, -1, -1, -1, -1], {1: {'zero_raw': 919, 'home': -25.1}})
    assert arm.home_action() is None


def test_save_calibration_merges(tmp_path, monkeypatch):
    monkeypatch.setattr(robot, 'CALIBRATION_FILE', str(tmp_path / 'cal.json'))
    arm = make_arm([-1] * 5, {0: {'zero_raw': 7}})
    arm.save_calibration({1: {'zero_raw': 1556, 'home': -30.0}})
    assert arm.load_calibration() == {0: {'zero_raw': 7}, 1: {'zero_raw': 1556, 'home': -30.0}}
