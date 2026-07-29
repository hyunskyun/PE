"""mediapipe/opencv 없이도 돌아가는 순수 로직(각도 계산, 판정 로직) 테스트.

`python -m unittest tests.test_core -v` 로 실행한다.
"""

import unittest

from posture_analysis.geometry import distance, forward_lean_angle, joint_angle, midpoint
from posture_analysis.judge import HIGH, LOW, OK, judge_frame, judge_metric
from posture_analysis.phase import ACCELERATION, MAX_VELOCITY, classify_phase
from posture_analysis.report import summarize


class GeometryTest(unittest.TestCase):
    def test_midpoint(self):
        self.assertEqual(midpoint((0, 0), (2, 4)), (1, 2))

    def test_distance(self):
        self.assertEqual(distance((0, 0), (3, 4)), 5.0)

    def test_joint_angle_straight_line_is_180(self):
        # 엉덩이-무릎-발목이 일직선이면 무릎 각도는 180도
        angle = joint_angle((0, 0), (0, 1), (0, 2))
        self.assertAlmostEqual(angle, 180.0, places=3)

    def test_joint_angle_right_angle(self):
        angle = joint_angle((1, 0), (0, 0), (0, 1))
        self.assertAlmostEqual(angle, 90.0, places=3)

    def test_forward_lean_zero_when_upright(self):
        # 어깨가 엉덩이 바로 위(수직)면 기울기 0도
        angle = forward_lean_angle(hip_center=(0, 10), shoulder_center=(0, 0))
        self.assertAlmostEqual(angle, 0.0, places=3)

    def test_forward_lean_positive_when_leaning_forward(self):
        angle = forward_lean_angle(hip_center=(0, 10), shoulder_center=(5, 0))
        self.assertGreater(angle, 0)


class PhaseTest(unittest.TestCase):
    def test_default_fraction_boundary(self):
        # 총 10초 영상, 기본 경계는 40% 지점(4초)
        self.assertEqual(classify_phase(3.9, 10), ACCELERATION)
        self.assertEqual(classify_phase(4.1, 10), MAX_VELOCITY)

    def test_explicit_boundary_overrides_default(self):
        self.assertEqual(classify_phase(2.0, 10, acceleration_end_sec=1.0), MAX_VELOCITY)


class JudgeTest(unittest.TestCase):
    def test_value_within_range_is_ok(self):
        status, error_name, message = judge_metric("trunk_lean_deg", 20, ACCELERATION)
        self.assertEqual(status, OK)
        self.assertIsNone(error_name)

    def test_value_below_range_is_low(self):
        status, error_name, message = judge_metric("trunk_lean_deg", 5, ACCELERATION)
        self.assertEqual(status, LOW)
        self.assertEqual(error_name, "초기 전방 기울기 부족")
        self.assertIsNotNone(message)

    def test_value_above_range_is_high(self):
        status, error_name, message = judge_metric("stride_ratio", 1.5, ACCELERATION)
        self.assertEqual(status, HIGH)
        self.assertEqual(error_name, "오버스트라이딩 의심(가속 구간)")

    def test_none_value_is_ok(self):
        status, error_name, message = judge_metric("trunk_lean_deg", None, ACCELERATION)
        self.assertEqual(status, OK)

    def test_judge_frame_collects_errors(self):
        result = judge_frame({"trunk_lean_deg": 5, "stride_ratio": 1.0}, ACCELERATION)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0][0], "trunk_lean_deg")


class ReportTest(unittest.TestCase):
    def test_summarize_computes_average_and_score(self):
        analysis_result = {
            "frame_results": [
                {
                    "phase": ACCELERATION,
                    "metrics": {"trunk_lean_deg": 20},
                    "errors": [],
                },
                {
                    "phase": ACCELERATION,
                    "metrics": {"trunk_lean_deg": 5},
                    "errors": [("trunk_lean_deg", "초기 전방 기울기 부족", "메시지")],
                },
            ]
        }
        summary = summarize(analysis_result)
        accel = summary[ACCELERATION]

        self.assertAlmostEqual(accel["averages"]["trunk_lean_deg"], 12.5)
        self.assertEqual(accel["error_counts"]["초기 전방 기울기 부족"], 1)
        self.assertEqual(accel["priority_issue"], ("초기 전방 기울기 부족", 1))
        self.assertAlmostEqual(accel["score"], 50.0)


if __name__ == "__main__":
    unittest.main()
