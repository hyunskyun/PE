"""프레임 좌표로부터 탐구에서 정의한 지표(상체 기울기, 무릎각, 팔치기각, 보폭 비율,
착지 시 발목-엉덩이 수평 거리)를 계산하는 모듈.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .geometry import angle_deg, distance, midpoint, tilt_from_vertical_deg
from .landmark_types import FrameLandmarks


@dataclass
class FrameMetrics:
    frame_index: int
    time_sec: float
    trunk_lean_deg: Optional[float] = None
    knee_angle_deg: Optional[float] = None
    arm_swing_deg: Optional[float] = None
    stride_ratio: Optional[float] = None
    ankle_hip_gap_ratio: Optional[float] = None  # 착지 순간에만 값이 채워짐


def compute_trunk_lean(lm: FrameLandmarks) -> Optional[float]:
    """어깨 중심 -> 엉덩이 중심 선분이 수직선과 이루는 각도(상체 전방 기울기)."""
    if not lm.all_visible("left_shoulder", "right_shoulder", "left_hip", "right_hip"):
        return None
    shoulder_mid = midpoint(lm.get("left_shoulder"), lm.get("right_shoulder"))
    hip_mid = midpoint(lm.get("left_hip"), lm.get("right_hip"))
    return tilt_from_vertical_deg(shoulder_mid, hip_mid)


def compute_knee_angle(lm: FrameLandmarks, side: str) -> Optional[float]:
    """엉덩이-무릎-발목 각도(무릎 굴곡각). side는 'left' 또는 'right'."""
    names = (f"{side}_hip", f"{side}_knee", f"{side}_ankle")
    if not lm.all_visible(*names):
        return None
    hip, knee, ankle = (lm.get(n) for n in names)
    return angle_deg(hip, knee, ankle)


def compute_arm_swing_angle(lm: FrameLandmarks, side: str) -> Optional[float]:
    """어깨-팔꿈치-손목 각도(팔치기 각도). side는 'left' 또는 'right'."""
    names = (f"{side}_shoulder", f"{side}_elbow", f"{side}_wrist")
    if not lm.all_visible(*names):
        return None
    shoulder, elbow, wrist = (lm.get(n) for n in names)
    return angle_deg(shoulder, elbow, wrist)


def compute_stride_ratio(lm: FrameLandmarks, height_px: Optional[float]) -> Optional[float]:
    """양 발목 사이 거리 / 신장(픽셀). height_px를 모르면 계산하지 않는다."""
    if not height_px or not lm.all_visible("left_ankle", "right_ankle"):
        return None
    stride_px = distance(lm.get("left_ankle"), lm.get("right_ankle"))
    return stride_px / height_px


def compute_ankle_hip_gap_ratio(lm: FrameLandmarks, height_px: Optional[float], side: str) -> Optional[float]:
    """착지 다리 발목과 엉덩이 중심 사이 수평 거리 / 신장(픽셀). 오버스트라이딩 판별용."""
    ankle = lm.get(f"{side}_ankle")
    hip_l, hip_r = lm.get("left_hip"), lm.get("right_hip")
    if ankle is None or hip_l is None or hip_r is None or not height_px:
        return None
    hip_mid = midpoint(hip_l, hip_r)
    horizontal_gap_px = abs(ankle[0] - hip_mid[0])
    return horizontal_gap_px / height_px


def estimate_height_px(lm: FrameLandmarks) -> Optional[float]:
    """어깨-엉덩이-무릎-발목 구간 길이 합으로 신장의 픽셀 길이를 근사한다.

    측면 촬영 영상에는 머리 끝 랜드마크가 없으므로, 몸통+다리 길이 합에
    보정 계수(1.18)를 곱해 전체 신장에 가깝게 추정한다. 이 값은 절대 길이가
    아니라 프레임마다 같은 방식으로 계산되는 '기준 길이'로서 보폭 비율 등
    무차원 지표를 만드는 데만 쓰인다.
    """
    segment_lengths = []
    for side in ("left", "right"):
        names = (f"{side}_shoulder", f"{side}_hip", f"{side}_knee", f"{side}_ankle")
        if lm.all_visible(*names):
            shoulder, hip, knee, ankle = (lm.get(n) for n in names)
            segment_lengths.append(distance(shoulder, hip) + distance(hip, knee) + distance(knee, ankle))

    if not segment_lengths:
        return None
    return (sum(segment_lengths) / len(segment_lengths)) * 1.18
