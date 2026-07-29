"""테스트와 데모용 가짜 랜드마크 생성기.

실제 영상 없이도, 원하는 상체 기울기/무릎각도/팔치기각도/보폭비율 값을 그대로
만들어내는 좌표를 역산해서 만든다. 그래서 예를 들어 trunk_lean_deg=11.2로
프레임을 만들면 metrics.trunk_lean_angle()이 정확히 11.2를 돌려준다.
"""

import math

from sprint_core.config import RUNNING_SIDE
from sprint_core.landmarks import (
    LEFT_ANKLE, RIGHT_ANKLE,
    LEFT_ELBOW, RIGHT_ELBOW,
    LEFT_HIP, RIGHT_HIP,
    LEFT_KNEE, RIGHT_KNEE,
    LEFT_SHOULDER, RIGHT_SHOULDER,
    LEFT_WRIST, RIGHT_WRIST,
    NOSE,
)
from sprint_core.config import PHASE_ACCEL, PHASE_MAXV


def point_at_angle_from_vertical(origin, length, angle_deg):
    """origin에서 수직 위 방향으로 angle_deg만큼 기울어진 지점의 좌표."""
    rad = math.radians(angle_deg)
    return (origin[0] + length * math.sin(rad), origin[1] - length * math.cos(rad))


def point_at_joint_angle(vertex, incoming_dir, length, angle_deg):
    """vertex(관절)를 지나 incoming_dir 반대편에서 들어와 angle_deg로 꺾이는 다음 점의 좌표.

    joint_angle(그 이전 점, vertex, 반환점)을 계산하면 정확히 angle_deg가 나온다.
    """
    base_angle = math.atan2(-incoming_dir[1], -incoming_dir[0])
    rad = base_angle + math.radians(180 - angle_deg)
    return (vertex[0] + length * math.cos(rad), vertex[1] - length * math.sin(rad))


def synthetic_frame(phase: str, trunk_lean_deg: float, knee_flex_deg: float,
                     arm_swing_deg: float, stride_ratio: float, height_px: float = 1000.0) -> dict:
    """지정한 지표값을 그대로 재현하는 한 프레임 분량의 랜드마크를 만든다."""
    segment = height_px / 4  # 대략적인 몸통/팔다리 분절 길이

    hip_mid = (height_px / 2, height_px * 0.55)
    shoulder_mid = point_at_angle_from_vertical(hip_mid, segment * 1.2, trunk_lean_deg)
    nose = (shoulder_mid[0], shoulder_mid[1] - segment * 0.6)

    half_shoulder_w = segment * 0.25
    half_hip_w = segment * 0.2
    left_shoulder = (shoulder_mid[0] - half_shoulder_w, shoulder_mid[1])
    right_shoulder = (shoulder_mid[0] + half_shoulder_w, shoulder_mid[1])
    left_hip = (hip_mid[0] - half_hip_w, hip_mid[1])
    right_hip = (hip_mid[0] + half_hip_w, hip_mid[1])

    is_right = RUNNING_SIDE == "right"
    running_hip = right_hip if is_right else left_hip
    other_hip = left_hip if is_right else right_hip
    running_shoulder = right_shoulder if is_right else left_shoulder
    other_shoulder = left_shoulder if is_right else right_shoulder

    # 다리: 엉덩이 바로 아래에 무릎을 두고, 무릎에서 목표 굴곡각만큼 꺾인 지점을 발목으로 삼는다.
    thigh_len, shank_len = segment * 0.95, segment * 0.95
    knee = (running_hip[0], running_hip[1] + thigh_len)
    hip_to_knee_dir = (0, thigh_len)
    running_ankle = point_at_joint_angle(knee, hip_to_knee_dir, shank_len, knee_flex_deg)

    ankle_dx = stride_ratio * height_px
    trailing_ankle = (running_ankle[0] - ankle_dx, running_ankle[1])
    other_knee = ((other_hip[0] + trailing_ankle[0]) / 2, (other_hip[1] + trailing_ankle[1]) / 2)

    # 팔: 어깨 바로 아래에 팔꿈치를 두고, 팔꿈치에서 목표 팔치기각만큼 꺾인 지점을 손목으로 삼는다.
    upper_arm_len, forearm_len = segment * 0.9, segment * 0.8
    elbow = (running_shoulder[0], running_shoulder[1] + upper_arm_len)
    shoulder_to_elbow_dir = (0, upper_arm_len)
    wrist = point_at_joint_angle(elbow, shoulder_to_elbow_dir, forearm_len, arm_swing_deg)

    other_elbow = (other_shoulder[0], other_shoulder[1] + upper_arm_len)
    other_wrist = (other_elbow[0], other_elbow[1] + forearm_len)

    coords = {
        NOSE: nose,
        LEFT_SHOULDER: left_shoulder, RIGHT_SHOULDER: right_shoulder,
        LEFT_HIP: left_hip, RIGHT_HIP: right_hip,
    }
    if is_right:
        coords.update({
            RIGHT_ANKLE: running_ankle, LEFT_ANKLE: trailing_ankle,
            RIGHT_KNEE: knee, LEFT_KNEE: other_knee,
            RIGHT_ELBOW: elbow, RIGHT_WRIST: wrist,
            LEFT_ELBOW: other_elbow, LEFT_WRIST: other_wrist,
        })
    else:
        coords.update({
            LEFT_ANKLE: running_ankle, RIGHT_ANKLE: trailing_ankle,
            LEFT_KNEE: knee, RIGHT_KNEE: other_knee,
            LEFT_ELBOW: elbow, LEFT_WRIST: wrist,
            RIGHT_ELBOW: other_elbow, RIGHT_WRIST: other_wrist,
        })

    return {idx: (x, y, 1.0) for idx, (x, y) in coords.items()}


def synthetic_sequence(fps: float = 30.0, accel_seconds: float = 2.0, maxv_seconds: float = 3.0):
    """가속 구간 예시 수치와 최대속도 구간 예시 수치로 이루어진 합성 시퀀스."""
    accel_frames = int(fps * accel_seconds)
    maxv_frames = int(fps * maxv_seconds)

    frames = []
    for _ in range(accel_frames):
        frames.append(synthetic_frame(
            PHASE_ACCEL, trunk_lean_deg=11.2, knee_flex_deg=110,
            arm_swing_deg=95, stride_ratio=1.21,
        ))
    for _ in range(maxv_frames):
        frames.append(synthetic_frame(
            PHASE_MAXV, trunk_lean_deg=8.4, knee_flex_deg=120,
            arm_swing_deg=100, stride_ratio=1.10,
        ))
    return frames, fps
