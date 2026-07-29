import pytest

from sprint_core import config, metrics
from sprint_core.synth import synthetic_frame


def test_trunk_lean_angle_matches_target():
    frame = synthetic_frame(config.PHASE_ACCEL, trunk_lean_deg=11.2, knee_flex_deg=110,
                             arm_swing_deg=95, stride_ratio=1.21)
    assert metrics.trunk_lean_angle(frame) == pytest.approx(11.2, abs=0.5)


def test_trunk_lean_angle_upright_is_near_zero():
    frame = synthetic_frame(config.PHASE_MAXV, trunk_lean_deg=0.0, knee_flex_deg=120,
                             arm_swing_deg=100, stride_ratio=1.0)
    assert metrics.trunk_lean_angle(frame) < 1.0


def test_stride_length_ratio_matches_target():
    frame = synthetic_frame(config.PHASE_ACCEL, trunk_lean_deg=11.2, knee_flex_deg=110,
                             arm_swing_deg=95, stride_ratio=1.21, height_px=1000.0)
    height_px = metrics.estimate_height_px(frame)
    ratio = metrics.stride_length_ratio(frame, height_px)
    assert ratio > 0


def test_frame_is_valid_rejects_empty_frame():
    assert metrics.frame_is_valid({}) is False


def test_joint_angle_straight_line_is_180():
    a, b, c = (0, 0), (1, 0), (2, 0)
    assert metrics.joint_angle(a, b, c) == pytest.approx(180.0)


def test_joint_angle_right_angle_is_90():
    a, b, c = (0, -1), (0, 0), (1, 0)
    assert metrics.joint_angle(a, b, c) == pytest.approx(90.0)
