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
    assert arm.raw_to_deg(1, 4090, 10) == pytest.approx(-16 * 360 / 4096)
    assert arm.raw_to_deg(1, 10, 4090) == pytest.approx(16 * 360 / 4096)


def test_joint_pos_is_nan_without_calibration_or_reading():
    arm = make_arm([-1, 1215, -1, -1, -1], {1: {'zero_raw': 1556}})
    pos = arm.joint_pos()
    assert pos[1] == pytest.approx((1215 - 1556) * 360 / 4096)  # about -30 deg
    assert all(math.isnan(p) for i, p in enumerate(pos) if i != 1)


def test_home_action_drives_toward_home_then_stops():
    cal = {1: {'zero_raw': 1556, 'home': -30.0}}
    behind = make_arm([-1, 1556 - 500, -1, -1, -1], cal)  # ~-44 deg, behind home
    assert behind.home_action()[1] == pytest.approx(robot.HOME_MAX_SPEED)  # forward, full speed

    ahead = make_arm([-1, 1556 - 300, -1, -1, -1], cal)  # ~-26 deg, ahead of home
    assert -robot.HOME_MAX_SPEED < ahead.home_action()[1] < -robot.HOME_MIN_SPEED

    at_home = make_arm([-1, 1556 - 341, -1, -1, -1], cal)  # -29.97 deg
    assert at_home.home_action() is None


def test_home_action_stops_on_lost_encoder():
    arm = make_arm([-1, -1, -1, -1, -1], {1: {'zero_raw': 1556, 'home': -30.0}})
    assert arm.home_action() is None


def test_save_calibration_merges(tmp_path, monkeypatch):
    monkeypatch.setattr(robot, 'CALIBRATION_FILE', str(tmp_path / 'cal.json'))
    arm = make_arm([-1] * 5, {0: {'zero_raw': 7}})
    arm.save_calibration({1: {'zero_raw': 1556, 'home': -30.0}})
    assert arm.load_calibration() == {0: {'zero_raw': 7}, 1: {'zero_raw': 1556, 'home': -30.0}}
