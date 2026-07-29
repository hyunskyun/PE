"""geometry 모듈 테스트: 각도/거리 계산과 부호 있는 상체 기울기."""

import unittest

from posture_analysis.constants import RUN_LEFT, RUN_RIGHT
from posture_analysis.geometry import (
    distance,
    forward_lean_angle,
    joint_angle,
    midpoint,
)


class BasicGeometryTest(unittest.TestCase):
    def test_midpoint(self):
        self.assertEqual(midpoint((0, 0), (2, 4)), (1, 2))

    def test_distance(self):
        self.assertEqual(distance((0, 0), (3, 4)), 5.0)

    def test_joint_angle_straight_line_is_180(self):
        angle = joint_angle((0, 0), (0, 1), (0, 2))
        self.assertAlmostEqual(angle, 180.0, places=3)

    def test_joint_angle_right_angle(self):
        angle = joint_angle((1, 0), (0, 0), (0, 1))
        self.assertAlmostEqual(angle, 90.0, places=3)

    def test_joint_angle_degenerate_returns_none(self):
        self.assertIsNone(joint_angle((0, 0), (0, 0), (1, 1)))


class ForwardLeanTest(unittest.TestCase):
    """부호 있는 상체 기울기: 진행 방향 기준 전방 양수, 후방 음수."""

    def test_upright_is_zero(self):
        angle = forward_lean_angle((0, 10), (0, 0), RUN_RIGHT)
        self.assertAlmostEqual(angle, 0.0, places=3)

    def test_forward_lean_positive_when_running_right(self):
        # 오른쪽 진행, 어깨가 엉덩이보다 오른쪽(+x) = 전방 기울기
        angle = forward_lean_angle((0, 10), (5, 0), RUN_RIGHT)
        self.assertGreater(angle, 0)

    def test_forward_lean_positive_when_running_left(self):
        # 왼쪽 진행, 어깨가 엉덩이보다 왼쪽(-x) = 전방 기울기
        angle = forward_lean_angle((0, 10), (-5, 0), RUN_LEFT)
        self.assertGreater(angle, 0)

    def test_backward_lean_negative(self):
        # 오른쪽 진행인데 어깨가 왼쪽(-x)에 있으면 후방 기울기 = 음수
        angle = forward_lean_angle((0, 10), (-5, 0), RUN_RIGHT)
        self.assertLess(angle, 0)
        # 왼쪽 진행인데 어깨가 오른쪽(+x)이어도 후방 기울기 = 음수
        angle = forward_lean_angle((0, 10), (5, 0), RUN_LEFT)
        self.assertLess(angle, 0)

    def test_same_lean_magnitude_regardless_of_direction(self):
        right = forward_lean_angle((0, 10), (5, 0), RUN_RIGHT)
        left = forward_lean_angle((0, 10), (-5, 0), RUN_LEFT)
        self.assertAlmostEqual(right, left, places=6)

    def test_invalid_direction_raises(self):
        with self.assertRaises(ValueError):
            forward_lean_angle((0, 10), (5, 0), 0)
        with self.assertRaises(ValueError):
            forward_lean_angle((0, 10), (5, 0), 2)

    def test_shoulder_below_hip_returns_none(self):
        self.assertIsNone(forward_lean_angle((0, 0), (0, 10), RUN_RIGHT))


if __name__ == "__main__":
    unittest.main()
