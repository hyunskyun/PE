"""조건문 기반 판정 로직 테스트 (음수 상체 기울기의 후경 판정 포함)."""

import unittest

from posture_analysis.judge import HIGH, LOW, NEGATIVE, OK, judge_frame, judge_metric
from posture_analysis.phase import ACCELERATION, MAX_VELOCITY


class JudgeMetricTest(unittest.TestCase):
    def test_value_within_range_is_ok(self):
        status, error_name, _msg = judge_metric("trunk_lean_deg", 20, ACCELERATION)
        self.assertEqual(status, OK)
        self.assertIsNone(error_name)

    def test_value_below_range_is_low(self):
        status, error_name, message = judge_metric("trunk_lean_deg", 5, ACCELERATION)
        self.assertEqual(status, LOW)
        self.assertEqual(error_name, "초기 전방 기울기 부족")
        self.assertIsNotNone(message)

    def test_value_above_range_is_high(self):
        status, error_name, _msg = judge_metric(
            "ankle_separation_ratio", 1.5, ACCELERATION
        )
        self.assertEqual(status, HIGH)
        self.assertEqual(error_name, "발목 간격 과다(가속 구간)")

    def test_negative_trunk_lean_is_backward_lean(self):
        # 음수 = 후방 기울기이므로 '전방 기울기 부족'이 아니라 후경으로 판정
        status, error_name, _msg = judge_metric("trunk_lean_deg", -3.0, MAX_VELOCITY)
        self.assertEqual(status, NEGATIVE)
        self.assertEqual(error_name, "상체 후경 의심")

        status, error_name, _msg = judge_metric("trunk_lean_deg", -3.0, ACCELERATION)
        self.assertEqual(status, NEGATIVE)
        self.assertEqual(error_name, "상체 후경 의심(가속 구간)")

    def test_small_positive_lean_in_max_velocity_is_low_not_backward(self):
        status, error_name, _msg = judge_metric("trunk_lean_deg", 2.0, MAX_VELOCITY)
        self.assertEqual(status, LOW)
        self.assertEqual(error_name, "전방 기울기 부족(최대 속도 구간)")

    def test_none_value_is_ok(self):
        status, _name, _msg = judge_metric("trunk_lean_deg", None, ACCELERATION)
        self.assertEqual(status, OK)


class JudgeFrameTest(unittest.TestCase):
    def test_collects_only_deviating_metrics(self):
        result = judge_frame(
            {"trunk_lean_deg": 5, "ankle_separation_ratio": 1.0}, ACCELERATION
        )
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0][0], "trunk_lean_deg")

    def test_empty_metrics_no_errors(self):
        result = judge_frame({}, ACCELERATION)
        self.assertEqual(result["errors"], [])


if __name__ == "__main__":
    unittest.main()
