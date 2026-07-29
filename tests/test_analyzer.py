"""analyzer 전체 파이프라인 테스트.

MediaPipe를 실행하지 않고 합성 랜드마크 시퀀스로
  구간 분류 -> 지표 계산 -> 착지 검출 -> 조건 판정 -> 검출 통계
전체 흐름을 검증한다. analyze_video()는 extractor 인자를 가짜 추출기로
바꿔 테스트한다.
"""

import unittest

from posture_analysis import constants as lm
from posture_analysis.analyzer import (
    DIRECTION_SOURCE_ESTIMATED,
    analyze_frames,
    analyze_video,
    estimate_run_direction,
    select_primary_side,
)
from posture_analysis.phase import ACCELERATION, MAX_VELOCITY

FPS = 30.0
NUM_FRAMES = 60  # 2초 분량


def make_runner_frame(frame_idx, base_x_step=4.0, left_ankle_bump=0.0,
                      right_ankle_bump=0.0):
    """오른쪽으로 달리는 사람의 합성 랜드마크 한 프레임을 만든다.

    어깨를 엉덩이보다 30px 앞(+x)에 둬서 전방 기울기 약 16.7도가 되게 한다.
    ankle_bump는 착지 파형을 만들기 위해 발목 y좌표에 더하는 값이다.
    """
    x = 100.0 + base_x_step * frame_idx
    v = 0.9
    return {
        lm.NOSE: (x, 40.0, v),
        lm.LEFT_SHOULDER: (x + 30, 100.0, v),
        lm.RIGHT_SHOULDER: (x + 30, 100.0, v),
        lm.LEFT_ELBOW: (x + 10, 130.0, v),
        lm.RIGHT_ELBOW: (x - 10, 130.0, v),
        lm.LEFT_WRIST: (x + 20, 160.0, v),
        lm.RIGHT_WRIST: (x - 20, 160.0, v),
        lm.LEFT_HIP: (x, 200.0, v),
        lm.RIGHT_HIP: (x, 200.0, v),
        lm.LEFT_KNEE: (x + 5, 260.0, v),
        lm.RIGHT_KNEE: (x - 5, 260.0, v),
        lm.LEFT_ANKLE: (x + 10, 320.0 + left_ankle_bump, v),
        lm.RIGHT_ANKLE: (x - 10, 320.0 + right_ankle_bump, v),
    }


def make_runner_frames(left_landings=(10, 30, 50), right_landings=(20, 40)):
    """착지 파형(±2프레임 삼각형 봉우리)이 있는 프레임 시퀀스를 만든다."""
    def bump_at(frame_idx, centers, amplitude=15.0):
        total = 0.0
        for center in centers:
            offset = abs(frame_idx - center)
            if offset <= 2:
                total += amplitude * (1 - offset / 3)
        return total

    return [
        make_runner_frame(
            i,
            left_ankle_bump=bump_at(i, left_landings),
            right_ankle_bump=bump_at(i, right_landings),
        )
        for i in range(NUM_FRAMES)
    ]


class EstimateRunDirectionTest(unittest.TestCase):
    def test_right_movement_detected(self):
        frames = [make_runner_frame(i) for i in range(30)]
        self.assertEqual(estimate_run_direction(frames), lm.RUN_RIGHT)

    def test_left_movement_detected(self):
        frames = [make_runner_frame(i, base_x_step=-4.0) for i in range(30)]
        self.assertEqual(estimate_run_direction(frames), lm.RUN_LEFT)

    def test_no_movement_returns_none(self):
        frames = [make_runner_frame(0) for _ in range(30)]
        self.assertIsNone(estimate_run_direction(frames))

    def test_insufficient_frames_returns_none(self):
        self.assertIsNone(estimate_run_direction([None, None]))


class SelectPrimarySideTest(unittest.TestCase):
    def test_side_with_higher_visibility_selected(self):
        frames = [make_runner_frame(i) for i in range(10)]
        for landmarks in frames:
            for idx in lm.RIGHT_LEG:
                x, y, _v = landmarks[idx]
                landmarks[idx] = (x, y, 0.6)  # 오른쪽 다리 visibility를 낮춤
        self.assertEqual(select_primary_side(frames), "left")

    def test_no_visible_legs_returns_none(self):
        self.assertIsNone(select_primary_side([None, {}]))


class AnalyzeFramesPipelineTest(unittest.TestCase):
    """합성 랜드마크 -> 전체 파이프라인 통합 검증."""

    @classmethod
    def setUpClass(cls):
        cls.result = analyze_frames(
            fps=FPS,
            frame_landmarks_list=make_runner_frames(),
            run_direction=lm.RUN_RIGHT,
        )

    def test_all_frames_analyzed(self):
        self.assertEqual(len(self.result["frame_results"]), NUM_FRAMES)
        detection = self.result["detection"]
        self.assertEqual(detection["total_frames_analyzed"], NUM_FRAMES)
        self.assertEqual(detection["pose_detected_frames"], NUM_FRAMES)
        self.assertAlmostEqual(detection["detection_rate"], 1.0)

    def test_phase_boundary_is_estimated_by_default(self):
        phase_info = self.result["phase_info"]
        self.assertEqual(phase_info["phase_boundary_source"], "estimated_fraction")
        self.assertAlmostEqual(phase_info["acceleration_end_sec"], 0.8)  # 2초의 40%

        phases = {f["phase"] for f in self.result["frame_results"]}
        self.assertEqual(phases, {ACCELERATION, MAX_VELOCITY})

    def test_landings_detected(self):
        landing_frames = [
            f["frame_idx"] for f in self.result["frame_results"] if f["is_landing_frame"]
        ]
        # 왼발 3회 + 오른발 2회 착지 파형을 심어 두었다
        self.assertEqual(len(landing_frames), 5)

    def test_knee_judged_only_on_landing_frames(self):
        for frame in self.result["frame_results"]:
            if "knee_angle_deg" in frame["judged_metrics"]:
                self.assertTrue(frame["is_landing_frame"])
            else:
                # 판정에서 빠져도 원자료로는 기록된다
                self.assertIn("knee_angle_deg", frame["metrics"])

    def test_landing_offset_only_on_landing_frames(self):
        for frame in self.result["frame_results"]:
            if "landing_offset_ratio" in frame["judged_metrics"]:
                self.assertTrue(frame["is_landing_frame"])

    def test_trunk_lean_is_signed_and_positive_for_forward_lean(self):
        first = self.result["frame_results"][0]
        self.assertGreater(first["judged_metrics"]["trunk_lean_deg"], 0)

    def test_max_velocity_trunk_lean_error_detected(self):
        # 전방 기울기 약 16.7도는 최대 속도 구간 권장 범위(5~12) 초과
        max_vel_errors = [
            error_name
            for f in self.result["frame_results"]
            if f["phase"] == MAX_VELOCITY
            for _metric, error_name, _msg in f["errors"]
        ]
        self.assertIn("과도한 전방 기울기", max_vel_errors)


class AnalyzeFramesWindowTest(unittest.TestCase):
    def test_frames_outside_analysis_window_excluded(self):
        result = analyze_frames(
            fps=FPS,
            frame_landmarks_list=make_runner_frames(),
            run_direction=lm.RUN_RIGHT,
            analysis_start_sec=0.5,
            analysis_end_sec=1.5,
        )
        indices = [f["frame_idx"] for f in result["frame_results"]]
        self.assertGreaterEqual(min(indices), 15)
        self.assertLessEqual(max(indices), 45)


class AnalyzeFramesValidationTest(unittest.TestCase):
    def test_invalid_direction_raises(self):
        with self.assertRaises(ValueError):
            analyze_frames(FPS, make_runner_frames(), run_direction=0)

    def test_invalid_fps_raises(self):
        with self.assertRaises(ValueError):
            analyze_frames(0, make_runner_frames(), run_direction=lm.RUN_RIGHT)

    def test_empty_frames_raises(self):
        with self.assertRaises(ValueError):
            analyze_frames(FPS, [], run_direction=lm.RUN_RIGHT)

    def test_no_landmarks_at_all_raises(self):
        with self.assertRaises(ValueError):
            analyze_frames(FPS, [None] * 30, run_direction=lm.RUN_RIGHT)


class AnalyzeVideoWithMockExtractorTest(unittest.TestCase):
    """MediaPipe 대신 가짜 추출기를 주입해 analyze_video 흐름을 검증한다."""

    def test_direction_auto_estimated(self):
        def fake_extractor(_path):
            return FPS, make_runner_frames()

        result = analyze_video("fake.mp4", extractor=fake_extractor)
        self.assertEqual(result["run_direction"], lm.RUN_RIGHT)
        self.assertEqual(result["run_direction_source"], DIRECTION_SOURCE_ESTIMATED)
        self.assertEqual(result["video_path"], "fake.mp4")

    def test_user_direction_overrides_estimation(self):
        def fake_extractor(_path):
            return FPS, make_runner_frames()

        result = analyze_video(
            "fake.mp4", run_direction=lm.RUN_LEFT, extractor=fake_extractor
        )
        self.assertEqual(result["run_direction"], lm.RUN_LEFT)
        self.assertEqual(result["run_direction_source"], "user_input")

    def test_estimation_failure_raises(self):
        def fake_extractor(_path):
            return FPS, [make_runner_frame(0) for _ in range(30)]  # 제자리

        with self.assertRaises(ValueError):
            analyze_video("fake.mp4", extractor=fake_extractor)


if __name__ == "__main__":
    unittest.main()
