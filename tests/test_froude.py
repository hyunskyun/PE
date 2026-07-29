"""프루드 수·평균 속도·달리기 기록 지표 테스트."""

import unittest

from posture_analysis.constants import LEG_LENGTH_HEIGHT_RATIO
from posture_analysis.metrics import (
    average_speed_mps,
    build_running_metrics,
    froude_number,
)


class FroudeNumberTest(unittest.TestCase):
    def test_normal_calculation(self):
        # Fr = v^2 / (g * L)
        self.assertAlmostEqual(froude_number(5.0, 1.0), 5.0**2 / (9.81 * 1.0))

    def test_custom_gravity(self):
        self.assertAlmostEqual(froude_number(3.0, 0.9, gravity_mps2=10.0), 9.0 / 9.0)

    def test_zero_speed_is_zero(self):
        self.assertEqual(froude_number(0.0, 0.9), 0.0)

    def test_negative_speed_raises(self):
        with self.assertRaises(ValueError):
            froude_number(-1.0, 0.9)

    def test_zero_leg_length_raises(self):
        with self.assertRaises(ValueError):
            froude_number(5.0, 0.0)

    def test_negative_leg_length_raises(self):
        with self.assertRaises(ValueError):
            froude_number(5.0, -0.9)

    def test_zero_gravity_raises(self):
        with self.assertRaises(ValueError):
            froude_number(5.0, 0.9, gravity_mps2=0.0)


class AverageSpeedTest(unittest.TestCase):
    def test_speed_from_50m_record(self):
        speed = average_speed_mps(50.0, 10.0)
        self.assertAlmostEqual(speed, 5.0)
        # 50m 기록 기반 프루드 수 계산 예시
        self.assertAlmostEqual(froude_number(speed, 1.0), 5.0**2 / (9.81 * 1.0))

    def test_zero_record_time_raises(self):
        with self.assertRaises(ValueError):
            average_speed_mps(50.0, 0.0)

    def test_negative_record_time_raises(self):
        with self.assertRaises(ValueError):
            average_speed_mps(50.0, -7.4)

    def test_zero_distance_raises(self):
        with self.assertRaises(ValueError):
            average_speed_mps(0.0, 7.4)


class BuildRunningMetricsTest(unittest.TestCase):
    def test_no_record_time_returns_none(self):
        self.assertIsNone(build_running_metrics(None))

    def test_user_leg_length(self):
        result = build_running_metrics(7.4, leg_length_m=0.92)
        self.assertAlmostEqual(result["average_speed_mps"], 50.0 / 7.4)
        self.assertEqual(result["leg_length_source"], "user_input")
        expected_fr = (50.0 / 7.4) ** 2 / (9.81 * 0.92)
        self.assertAlmostEqual(result["froude_number"], expected_fr)

    def test_leg_length_estimated_from_height(self):
        result = build_running_metrics(8.0, height_cm=170.0)
        self.assertEqual(result["leg_length_source"], "estimated_from_height")
        self.assertAlmostEqual(
            result["leg_length_m"], 1.70 * LEG_LENGTH_HEIGHT_RATIO
        )
        self.assertIsNotNone(result["froude_number"])

    def test_user_leg_length_takes_priority_over_height(self):
        result = build_running_metrics(8.0, leg_length_m=0.9, height_cm=170.0)
        self.assertEqual(result["leg_length_source"], "user_input")
        self.assertEqual(result["leg_length_m"], 0.9)

    def test_no_leg_info_gives_speed_but_no_froude(self):
        result = build_running_metrics(8.0)
        self.assertAlmostEqual(result["average_speed_mps"], 6.25)
        self.assertIsNone(result["froude_number"])
        self.assertIsNone(result["leg_length_source"])

    def test_invalid_inputs_raise(self):
        with self.assertRaises(ValueError):
            build_running_metrics(0.0, leg_length_m=0.9)
        with self.assertRaises(ValueError):
            build_running_metrics(7.4, leg_length_m=-0.9)
        with self.assertRaises(ValueError):
            build_running_metrics(7.4, height_cm=-170)


if __name__ == "__main__":
    unittest.main()
