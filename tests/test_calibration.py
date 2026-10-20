import math

import numpy as np
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


# Shoulder from the real calibration: forward is a negative action, back is positive
LIMITS = {1: {'zero_raw': 919, 'home': -25.1, 'forward_limit': 59.9, 'back_limit': -63.8}}
FORWARD, BACK = -1.0, 1.0


def raw_at(deg):
    return round(919 - deg * 4096 / 360)


def shoulder_action(arm, speed):
    arm._limited = set()
    action = [0, speed, 0, 0, 0, 0]
    return arm._apply_limits(np.array(action, dtype=float))[1]


def test_limits_pass_through_away_from_limits():
    arm = make_arm([-1, raw_at(0), -1, -1, -1], LIMITS)
    assert shoulder_action(arm, FORWARD) == FORWARD
    assert shoulder_action(arm, BACK) == BACK


def test_limits_slow_near_and_block_at_forward_limit():
    near = make_arm([-1, raw_at(50), -1, -1, -1], LIMITS)
    assert shoulder_action(near, FORWARD) == -robot.LIMIT_SLOW_SPEED
    assert shoulder_action(near, BACK) == BACK  # moving away is never limited

    at = make_arm([-1, raw_at(59.5), -1, -1, -1], LIMITS)
    assert shoulder_action(at, FORWARD) == 0
    assert shoulder_action(at, BACK) == BACK


def test_limits_block_past_back_limit():
    past = make_arm([-1, raw_at(-66), -1, -1, -1], LIMITS)
    assert shoulder_action(past, BACK) == 0
    assert shoulder_action(past, FORWARD) == FORWARD


def test_limits_block_joint_without_reading():
    arm = make_arm([-1, -1, -1, -1, -1], LIMITS)
    assert shoulder_action(arm, FORWARD) == 0
    assert shoulder_action(arm, BACK) == 0
