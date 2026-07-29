"""metrics 모듈 테스트: visibility 처리, 발목 간격, 착지 오프셋 부호."""

import unittest

from posture_analysis import constants as lm
from posture_analysis import metrics as m
from posture_analysis.constants import RUN_LEFT, RUN_RIGHT


def make_landmarks(visibility=0.9, ankle_dx=30, shoulder_dx=0):
    """테스트용 합성 랜드마크. 신체 각 부위를 그럴듯한 위치에 배치한다."""
    return {
        lm.NOSE: (100, 40, visibility),
        lm.LEFT_SHOULDER: (100 + shoulder_dx, 100, visibility),
        lm.RIGHT_SHOULDER: (100 + shoulder_dx, 100, visibility),
        lm.LEFT_ELBOW: (110, 130, visibility),
        lm.RIGHT_ELBOW: (90, 130, visibility),
        lm.LEFT_WRIST: (120, 160, visibility),
        lm.RIGHT_WRIST: (80, 160, visibility),
        lm.LEFT_HIP: (100, 200, visibility),
        lm.RIGHT_HIP: (100, 200, visibility),
        lm.LEFT_KNEE: (110, 260, visibility),
        lm.RIGHT_KNEE: (90, 260, visibility),
        lm.LEFT_ANKLE: (100 + ankle_dx, 320, visibility),
        lm.RIGHT_ANKLE: (100 - ankle_dx, 320, visibility),
    }


class VisibilityTest(unittest.TestCase):
    def test_low_visibility_trunk_returns_none(self):
        landmarks = make_landmarks()
        x, y, _v = landmarks[lm.LEFT_SHOULDER]
        landmarks[lm.LEFT_SHOULDER] = (x, y, lm.MIN_VISIBILITY - 0.1)
        self.assertIsNone(m.trunk_lean_deg(landmarks, RUN_RIGHT))

    def test_side_with_low_visibility_joint_is_not_used(self):
        # 왼쪽 무릎이 기준 미달이면 왼쪽 다리는 후보에서 빠지고 오른쪽 사용
        landmarks = make_landmarks()
        x, y, _v = landmarks[lm.LEFT_KNEE]
        landmarks[lm.LEFT_KNEE] = (x, y, 0.1)
        self.assertIsNotNone(m.knee_angle_deg(landmarks, preferred_side="left"))

    def test_both_sides_below_threshold_returns_none(self):
        landmarks = make_landmarks(visibility=0.2)
        self.assertIsNone(m.knee_angle_deg(landmarks))
        self.assertIsNone(m.arm_swing_angle_deg(landmarks))

    def test_preferred_side_is_respected_when_both_visible(self):
        # 좌우가 대칭이 아니게 만들어 선호 측면이 실제로 반영되는지 확인
        landmarks = make_landmarks()
        landmarks[lm.LEFT_KNEE] = (140, 260, 0.9)  # 왼쪽 무릎만 크게 이동
        left_angle = m.knee_angle_deg(landmarks, preferred_side="left")
        right_angle = m.knee_angle_deg(landmarks, preferred_side="right")
        self.assertNotAlmostEqual(left_angle, right_angle, places=1)


class AnkleSeparationTest(unittest.TestCase):
    def test_ratio_calculation(self):
        landmarks = make_landmarks(ankle_dx=30)
        # 양 발목 수평 거리 60px
        ratio = m.ankle_separation_ratio(landmarks, reference_length_px=280.0)
        self.assertAlmostEqual(ratio, 60 / 280.0)

    def test_none_reference_returns_none(self):
        landmarks = make_landmarks()
        self.assertIsNone(m.ankle_separation_ratio(landmarks, None))

    def test_zero_reference_returns_none(self):
        landmarks = make_landmarks()
        self.assertIsNone(m.ankle_separation_ratio(landmarks, 0))


class LandingOffsetTest(unittest.TestCase):
    def test_sign_follows_run_direction(self):
        # 왼쪽 발목이 엉덩이(x=100)보다 오른쪽(+30px)에 있는 상황
        landmarks = make_landmarks(ankle_dx=30)
        forward = m.landing_offset_ratio(landmarks, lm.LEFT_ANKLE, 280.0, RUN_RIGHT)
        backward = m.landing_offset_ratio(landmarks, lm.LEFT_ANKLE, 280.0, RUN_LEFT)
        self.assertGreater(forward, 0)   # 오른쪽 진행이면 발목이 전방 = 양수
        self.assertLess(backward, 0)     # 왼쪽 진행이면 같은 위치가 후방 = 음수
        self.assertAlmostEqual(forward, -backward)

    def test_invalid_direction_raises(self):
        landmarks = make_landmarks()
        with self.assertRaises(ValueError):
            m.landing_offset_ratio(landmarks, lm.LEFT_ANKLE, 280.0, 0)

    def test_none_reference_returns_none(self):
        landmarks = make_landmarks()
        self.assertIsNone(
            m.landing_offset_ratio(landmarks, lm.LEFT_ANKLE, None, RUN_RIGHT)
        )


class KneeAngleForAnkleTest(unittest.TestCase):
    def test_uses_leg_matching_the_landing_ankle(self):
        landmarks = make_landmarks()
        landmarks[lm.LEFT_KNEE] = (140, 260, 0.9)  # 좌우 무릎 각도가 다르게
        left = m.knee_angle_for_ankle(landmarks, lm.LEFT_ANKLE)
        right = m.knee_angle_for_ankle(landmarks, lm.RIGHT_ANKLE)
        self.assertNotAlmostEqual(left, right, places=1)

    def test_invisible_leg_returns_none(self):
        landmarks = make_landmarks()
        x, y, _v = landmarks[lm.LEFT_KNEE]
        landmarks[lm.LEFT_KNEE] = (x, y, 0.1)
        self.assertIsNone(m.knee_angle_for_ankle(landmarks, lm.LEFT_ANKLE))


if __name__ == "__main__":
    unittest.main()
