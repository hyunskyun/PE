"""프레임 하나에서 뽑아내는 자세 지표 계산.

입력은 랜드마크 인덱스 -> (x, y) 픽셀 좌표 dict 하나이며, 다른 모든 계산은 여기서 끝난다.
MediaPipe나 OpenCV를 몰라도 이 모듈만 보면 지표 정의를 이해할 수 있도록 분리했다.
"""
from dataclasses import dataclass

from . import landmarks as lm
from .geometry import angle_at_vertex, angle_from_vertical, distance, midpoint


@dataclass
class FrameMetrics:
    frame_idx: int
    time_sec: float
    trunk_lean_deg: float       # 상체 전방 기울기 (수직 대비)
    knee_angle_deg: float       # 더 굽혀진 쪽(구동 다리) 무릎 각도
    arm_swing_deg: float        # 더 크게 흔들린 쪽 팔의 상완-수직 각도
    stride_cm: float            # 두 발목 사이 수평 거리 (cm)
    front_ankle_offset_cm: float  # 엉덩이 중심 대비 더 앞선 발목의 수평 거리 (cm, 오버스트라이딩 판별용)
    left_ankle_y: float          # 착지 순간(발이 가장 낮아지는 시점) 탐지를 위한 원본 y좌표
    right_ankle_y: float


def calibrate_px_per_cm(points, height_cm):
    """한 프레임의 랜드마크 전체 y범위(대략적인 신장의 픽셀 길이)로 px-cm 환산 비율을 구한다.

    카메라 각도·자세에 따라 오차가 있을 수 있어 여러 프레임의 값을 평균 내어 쓰는 것을 권장한다.
    (pipeline.py에서 초반 프레임 여러 개의 결과를 median으로 합친다.)
    """
    ys = [points[i][1] for i in lm.REQUIRED if i in points]
    pixel_height = max(ys) - min(ys)
    if pixel_height <= 0 or height_cm <= 0:
        return None
    return pixel_height / height_cm


def compute_frame_metrics(points, frame_idx, time_sec, px_per_cm):
    """points: {landmark_index: (x, y)} / px_per_cm: calibrate_px_per_cm() 결과."""
    shoulder_mid = midpoint(points[lm.LEFT_SHOULDER], points[lm.RIGHT_SHOULDER])
    hip_mid = midpoint(points[lm.LEFT_HIP], points[lm.RIGHT_HIP])
    trunk_lean_deg = angle_from_vertical(shoulder_mid, hip_mid)

    knee_left = angle_at_vertex(points[lm.LEFT_HIP], points[lm.LEFT_KNEE], points[lm.LEFT_ANKLE])
    knee_right = angle_at_vertex(points[lm.RIGHT_HIP], points[lm.RIGHT_KNEE], points[lm.RIGHT_ANKLE])
    knee_angle_deg = min(knee_left, knee_right)  # 더 접힌(작은 각) 쪽이 구동 다리

    arm_left = angle_from_vertical(points[lm.LEFT_ELBOW], points[lm.LEFT_SHOULDER])
    arm_right = angle_from_vertical(points[lm.RIGHT_ELBOW], points[lm.RIGHT_SHOULDER])
    arm_swing_deg = max(arm_left, arm_right)

    stride_px = distance(points[lm.LEFT_ANKLE], points[lm.RIGHT_ANKLE])
    hip_x = hip_mid[0]
    front_ankle_offset_px = max(
        abs(points[lm.LEFT_ANKLE][0] - hip_x),
        abs(points[lm.RIGHT_ANKLE][0] - hip_x),
    )

    to_cm = (lambda px: px / px_per_cm) if px_per_cm else (lambda px: float("nan"))

    return FrameMetrics(
        frame_idx=frame_idx,
        time_sec=time_sec,
        trunk_lean_deg=trunk_lean_deg,
        knee_angle_deg=knee_angle_deg,
        arm_swing_deg=arm_swing_deg,
        stride_cm=to_cm(stride_px),
        front_ankle_offset_cm=to_cm(front_ankle_offset_px),
        left_ankle_y=points[lm.LEFT_ANKLE][1],
        right_ankle_y=points[lm.RIGHT_ANKLE][1],
    )
