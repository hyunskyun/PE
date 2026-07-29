"""구간 경계 결정(resolve_phase_boundaries)과 구간 분류 테스트."""

import unittest

from posture_analysis.phase import (
    ACCELERATION,
    BOUNDARY_SOURCE_ESTIMATED,
    BOUNDARY_SOURCE_USER,
    MAX_VELOCITY,
    classify_phase,
    resolve_phase_boundaries,
)


class ResolveBoundariesTest(unittest.TestCase):
    def test_defaults_use_estimated_fraction(self):
        start, accel_end, end, source = resolve_phase_boundaries(10.0)
        self.assertEqual(start, 0.0)
        self.assertEqual(end, 10.0)
        self.assertAlmostEqual(accel_end, 4.0)  # 40% 지점
        self.assertEqual(source, BOUNDARY_SOURCE_ESTIMATED)

    def test_user_acceleration_end(self):
        _s, accel_end, _e, source = resolve_phase_boundaries(
            10.0, acceleration_end_sec=2.6
        )
        self.assertEqual(accel_end, 2.6)
        self.assertEqual(source, BOUNDARY_SOURCE_USER)

    def test_estimated_fraction_respects_analysis_window(self):
        start, accel_end, end, _src = resolve_phase_boundaries(
            10.0, analysis_start_sec=2.0, analysis_end_sec=7.0
        )
        self.assertAlmostEqual(accel_end, 2.0 + 5.0 * 0.4)

    def test_start_after_end_raises(self):
        with self.assertRaises(ValueError):
            resolve_phase_boundaries(10.0, analysis_start_sec=8.0, analysis_end_sec=3.0)

    def test_acceleration_end_outside_range_raises(self):
        with self.assertRaises(ValueError):
            resolve_phase_boundaries(10.0, acceleration_end_sec=12.0)
        with self.assertRaises(ValueError):
            resolve_phase_boundaries(
                10.0, analysis_start_sec=3.0, acceleration_end_sec=1.0
            )

    def test_negative_start_raises(self):
        with self.assertRaises(ValueError):
            resolve_phase_boundaries(10.0, analysis_start_sec=-1.0)

    def test_zero_duration_raises(self):
        with self.assertRaises(ValueError):
            resolve_phase_boundaries(0.0)


class ClassifyPhaseTest(unittest.TestCase):
    def test_phases_and_out_of_range(self):
        args = (1.0, 4.0, 9.0)  # start, accel_end, end
        self.assertIsNone(classify_phase(0.5, *args))    # 분석 시작 전
        self.assertEqual(classify_phase(2.0, *args), ACCELERATION)
        self.assertEqual(classify_phase(4.0, *args), ACCELERATION)  # 경계 포함
        self.assertEqual(classify_phase(5.0, *args), MAX_VELOCITY)
        self.assertIsNone(classify_phase(9.5, *args))    # 분석 종료 후


if __name__ == "__main__":
    unittest.main()
