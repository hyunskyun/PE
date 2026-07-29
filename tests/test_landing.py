"""착지 검출 테스트: 평활화, 돌출량 기준, 근접 후보 병합, 좌우 독립성."""

import unittest

from posture_analysis import constants as lm
from posture_analysis.landing import (
    build_ankle_y_tracks,
    find_landing_frames,
    smooth_series,
)

FPS = 30.0


def make_track(length=60, base_y=320.0, bumps=()):
    """base_y 위에 삼각형 봉우리(bump)를 얹은 발목 y좌표 트랙을 만든다.

    bumps: [(중심 프레임, 최대 높이), ...] — 중심에서 ±2프레임에 걸쳐
    0.33/0.66/1.0/0.66/0.33 비율로 y를 올린다 (착지 파형 근사).
    """
    values = [base_y] * length
    for center, amplitude in bumps:
        for offset, fraction in ((-2, 1 / 3), (-1, 2 / 3), (0, 1.0), (1, 2 / 3), (2, 1 / 3)):
            i = center + offset
            if 0 <= i < length:
                values[i] += amplitude * fraction
    return [(i, y) for i, y in enumerate(values)]


class SmoothSeriesTest(unittest.TestCase):
    def test_constant_series_unchanged(self):
        self.assertEqual(smooth_series([5.0] * 10, window=5), [5.0] * 10)

    def test_none_positions_preserved(self):
        result = smooth_series([1.0, None, 3.0], window=3)
        self.assertIsNone(result[1])

    def test_single_frame_spike_is_flattened(self):
        values = [10.0] * 5 + [100.0] + [10.0] * 5
        smoothed = smooth_series(values, window=5)
        self.assertEqual(smoothed[5], 10.0)  # 중앙값이라 1프레임 스파이크 제거

    def test_invalid_window_raises(self):
        with self.assertRaises(ValueError):
            smooth_series([1.0], window=0)


class FindLandingFramesTest(unittest.TestCase):
    def test_single_clear_landing_detected_once(self):
        track = make_track(bumps=[(30, 15.0)])
        landings = find_landing_frames(track, FPS)
        self.assertEqual(len(landings), 1)
        self.assertAlmostEqual(landings[0], 30, delta=2)

    def test_flat_signal_has_no_landing(self):
        track = make_track(bumps=[])
        self.assertEqual(find_landing_frames(track, FPS), [])

    def test_small_noise_is_not_landing(self):
        # ±0.5px 흔들림은 최소 돌출량(2px) 미달이라 착지가 아니다
        track = [(i, 320.0 + (0.5 if i % 2 == 0 else -0.5)) for i in range(60)]
        self.assertEqual(find_landing_frames(track, FPS), [])

    def test_close_candidates_merged_into_one(self):
        # 4프레임 간격 봉우리 두 개 = 최소 착지 간격(0.25s = 7.5프레임)
        # 이내이므로 하나의 착지로 병합되어야 한다
        track = make_track(bumps=[(20, 15.0), (24, 15.0)])
        landings = find_landing_frames(track, FPS)
        self.assertEqual(len(landings), 1)

    def test_far_candidates_kept_separate(self):
        track = make_track(bumps=[(15, 15.0), (45, 15.0)])
        landings = find_landing_frames(track, FPS)
        self.assertEqual(len(landings), 2)

    def test_invalid_fps_raises(self):
        with self.assertRaises(ValueError):
            find_landing_frames(make_track(), fps=0)


class BuildAnkleTracksTest(unittest.TestCase):
    def test_left_right_tracks_are_independent(self):
        frames = [
            {lm.LEFT_ANKLE: (0, 300.0, 0.9)},                     # 왼쪽만 보임
            {lm.LEFT_ANKLE: (0, 305.0, 0.9), lm.RIGHT_ANKLE: (0, 310.0, 0.9)},
            {lm.RIGHT_ANKLE: (0, 315.0, 0.9)},                    # 오른쪽만 보임
            None,                                                  # 검출 실패 프레임
        ]
        tracks = build_ankle_y_tracks(frames)

        self.assertEqual(
            [y for _i, y in tracks[lm.LEFT_ANKLE]], [300.0, 305.0, None, None]
        )
        self.assertEqual(
            [y for _i, y in tracks[lm.RIGHT_ANKLE]], [None, 310.0, 315.0, None]
        )

    def test_low_visibility_ankle_becomes_none(self):
        frames = [{lm.LEFT_ANKLE: (0, 300.0, 0.2)}]
        tracks = build_ankle_y_tracks(frames)
        self.assertEqual(tracks[lm.LEFT_ANKLE], [(0, None)])


if __name__ == "__main__":
    unittest.main()
