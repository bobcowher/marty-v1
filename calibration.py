"""Guided calibration, one joint at a time: vertical, home, min limit, max limit.

Start begins and then captures each step; Back cancels. Every prompt goes through
`say`, so it can be printed, sent to the voice client, or spoken on the robot.
Only joints with an encoder reading when calibration starts are walked through.
"""

JOINT_NAMES = ['Base', 'Shoulder', 'Elbow', 'Wrist tilt', 'Wrist rotate']

# (calibration key, spoken name). zero_raw is the raw count at vertical; the
# rest are degrees from vertical. min is the back end, max the forward end.
STEPS = [
    ('zero_raw',  'vertical'),
    ('home',      'home'),
    ('min_limit', 'min limit'),
    ('max_limit', 'max limit'),
]

STARTED = "Calibration started"
SAVED = "Calibration saved"
CANCELLED = "Calibration cancelled"


def prompt(joint, step):
    return f"{JOINT_NAMES[joint]} joint, {STEPS[step][1]}"


# Everything calibration can say, so the voice can render it ahead of time
PHRASES = [STARTED] + [prompt(j, s) for j in range(len(JOINT_NAMES)) for s in range(len(STEPS))] + [SAVED, CANCELLED]


class Calibration:

    def __init__(self, arm, say=print):
        self.arm = arm
        self.say = say
        self.joints = None  # joints to calibrate; None when not calibrating
        self.joint = 0      # index into self.joints
        self.step = 0       # index into STEPS
        self.captured = {}

    @property
    def active(self):
        return self.joints is not None

    def press(self):
        """Start pressed: begin calibrating, or capture the current step and prompt the next."""
        self.arm.get_position()
        if not self.active:
            self._start()
            return

        j = self.joints[self.joint]
        key = STEPS[self.step][0]
        raw = self.arm.encoders[j]
        if raw < 0:
            print(f"CALIBRATE: lost encoder on joint {j}")
            self.cancel()
            return
        cal = self.captured.setdefault(j, {})
        cal[key] = raw if key == 'zero_raw' else round(self.arm.raw_to_deg(j, raw, cal['zero_raw']), 1)
        print(f"CALIBRATE: joint {j} {key} = {cal[key]}")

        self.step += 1
        if self.step == len(STEPS):
            if not cal['min_limit'] < cal['home'] < cal['max_limit']:
                print(f"CALIBRATE: WARNING joint {j} home is not between its limits")
            self.step = 0
            self.joint += 1
        if self.joint == len(self.joints):
            self._save()
        else:
            self._prompt()

    def cancel(self):
        """Back pressed: abandon calibration without saving anything."""
        self.joints = None
        self.captured = {}
        self.say(CANCELLED)

    def _start(self):
        joints = [j for j, raw in enumerate(self.arm.encoders) if raw >= 0]
        if not joints:
            print("CALIBRATE: no encoder readings, nothing to calibrate")
            return
        self.joints, self.joint, self.step, self.captured = joints, 0, 0, {}
        self.say(STARTED)
        self._prompt()

    def _prompt(self):
        self.say(prompt(self.joints[self.joint], self.step))

    def _save(self):
        self.arm.save_calibration(self.captured)
        print(f"CALIBRATE: saved {self.captured}")
        self.joints = None
        self.captured = {}
        self.say(SAVED)
