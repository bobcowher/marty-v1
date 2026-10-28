import pytest

import robot
from calibration import Calibration, CANCELLED, SAVED, STARTED
from test_calibration import make_arm


def raw_at(deg, zero_raw=919):
    """Shoulder raw count for an angle (raw falls as the arm goes forward)."""
    return round(zero_raw - deg * 4096 / 360)


@pytest.fixture
def arm(tmp_path, monkeypatch):
    monkeypatch.setattr(robot, 'CALIBRATION_FILE', str(tmp_path / 'cal.json'))
    arm = make_arm([-1, 919, 2000, -1, -1], {})
    arm.get_position = lambda: None
    return arm


def run(cal, arm, readings):
    """Press Start once to begin, then once per {joint: raw} reading."""
    cal.press()
    for reading in readings:
        for j, raw in reading.items():
            arm.encoders[j] = raw
        cal.press()


def test_walks_each_joint_in_turn_then_saves(arm):
    said = []
    cal = Calibration(arm, say=said.append)
    run(cal, arm, [
        {1: 919}, {1: raw_at(-25)}, {1: raw_at(-60)}, {1: raw_at(55)},
        {2: 2000}, {2: 2100}, {2: 1900}, {2: 2200},
    ])
    assert said == [
        STARTED,
        "Shoulder joint, vertical", "Shoulder joint, home",
        "Shoulder joint, min limit", "Shoulder joint, max limit",
        "Elbow joint, vertical", "Elbow joint, home",
        "Elbow joint, min limit", "Elbow joint, max limit",
        SAVED,
    ]
    assert not cal.active
    saved = arm.load_calibration()
    assert saved[1]['zero_raw'] == 919
    assert saved[1]['home'] == pytest.approx(-25, abs=0.1)
    assert saved[1]['min_limit'] == pytest.approx(-60, abs=0.1)
    assert saved[1]['max_limit'] == pytest.approx(55, abs=0.1)
    assert saved[2]['zero_raw'] == 2000


def test_cancel_saves_nothing(arm):
    said = []
    cal = Calibration(arm, say=said.append)
    run(cal, arm, [{1: 919}, {1: raw_at(-25)}])
    cal.cancel()
    assert said[-1] == CANCELLED
    assert not cal.active
    assert arm.load_calibration() == {}


def test_lost_reading_cancels(arm):
    said = []
    cal = Calibration(arm, say=said.append)
    run(cal, arm, [{1: 919}, {1: -1}])
    assert said[-1] == CANCELLED
    assert not cal.active


def test_no_encoders_does_not_start(arm):
    arm.encoders = [-1] * 5
    said = []
    cal = Calibration(arm, say=said.append)
    cal.press()
    assert said == [] and not cal.active
