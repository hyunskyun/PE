"""좌표만 가지고 각도/거리를 계산하는 순수 함수 모음.

mediapipe나 cv2를 전혀 쓰지 않으므로, 영상 없이도 좌표 딕셔너리만 만들면
이 파일의 모든 함수를 그대로 테스트할 수 있다.
"""

import math

from sprint_core import config
from sprint_core.landmarks import (
    LEFT_ANKLE, RIGHT_ANKLE,
    LEFT_ELBOW, RIGHT_ELBOW,
    LEFT_HIP, RIGHT_HIP,
    LEFT_KNEE, RIGHT_KNEE,
    LEFT_SHOULDER, RIGHT_SHOULDER,
    LEFT_WRIST, RIGHT_WRIST,
    NOSE,
)

_SIDE_LANDMARKS = {
    "left": dict(shoulder=LEFT_SHOULDER, elbow=LEFT_ELBOW, wrist=LEFT_WRIST,
                 hip=LEFT_HIP, knee=LEFT_KNEE, ankle=LEFT_ANKLE),
    "right": dict(shoulder=RIGHT_SHOULDER, elbow=RIGHT_ELBOW, wrist=RIGHT_WRIST,
                  hip=RIGHT_HIP, knee=RIGHT_KNEE, ankle=RIGHT_ANKLE),
}


def midpoint(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def angle_from_vertical(top_pt, bottom_pt) -> float:
    """top_pt -> bottom_pt 벡터가 수직선(위에서 아래)과 이루는 각도, 도 단위."""
    dx = bottom_pt[0] - top_pt[0]
    dy = bottom_pt[1] - top_pt[1]
    return math.degrees(math.atan2(abs(dx), abs(dy)))


def joint_angle(a, b, c) -> float:
    """b를 꼭짓점으로 하는 a-b-c 각도, 도 단위 (무릎, 팔꿈치 각도에 사용)."""
    v1 = (a[0] - b[0], a[1] - b[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.hypot(*v1)
    mag2 = math.hypot(*v2)
    if mag1 == 0 or mag2 == 0:
        return 0.0
    cos_angle = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_angle))


def frame_is_valid(frame: dict, side: str = config.RUNNING_SIDE) -> bool:
    if not frame:
        return False
    needed = _SIDE_LANDMARKS[side].values()
    return all(
        idx in frame and frame[idx][2] >= config.MIN_VISIBILITY
        for idx in list(needed) + [LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP]
    )


def trunk_lean_angle(frame: dict) -> float:
    shoulder_mid = midpoint(frame[LEFT_SHOULDER], frame[RIGHT_SHOULDER])
    hip_mid = midpoint(frame[LEFT_HIP], frame[RIGHT_HIP])
    return angle_from_vertical(shoulder_mid, hip_mid)


def knee_flexion_angle(frame: dict, side: str = config.RUNNING_SIDE) -> float:
    pts = _SIDE_LANDMARKS[side]
    return joint_angle(frame[pts["hip"]], frame[pts["knee"]], frame[pts["ankle"]])


def arm_swing_angle(frame: dict, side: str = config.RUNNING_SIDE) -> float:
    pts = _SIDE_LANDMARKS[side]
    return joint_angle(frame[pts["shoulder"]], frame[pts["elbow"]], frame[pts["wrist"]])


def estimate_height_px(frame: dict) -> float:
    """코~발목 중점 사이의 픽셀 거리로 신장(px)을 대략 추정한다."""
    ankle_mid = midpoint(frame[LEFT_ANKLE], frame[RIGHT_ANKLE])
    nose = frame[NOSE]
    return math.hypot(nose[0] - ankle_mid[0], nose[1] - ankle_mid[1])


def stride_length_ratio(frame: dict, height_px: float) -> float:
    """양 발목 사이 수평 거리 / 신장(px).

    분자 분모 모두 같은 프레임의 픽셀 단위라서 신장(cm) 값과 무관하게
    계산되는 비율이다. height_cm는 표시/향후 확장용으로 남겨둔다.
    """
    ankle_dx = abs(frame[LEFT_ANKLE][0] - frame[RIGHT_ANKLE][0])
    if height_px == 0:
        return 0.0
    return ankle_dx / height_px


def footstrike_offset_ratio(frame: dict, height_px: float, side: str = config.RUNNING_SIDE) -> float:
    """착지 발목과 엉덩이 중심의 수평 거리 / 신장(px). 오버스트라이딩 판별용."""
    pts = _SIDE_LANDMARKS[side]
    hip_mid = midpoint(frame[LEFT_HIP], frame[RIGHT_HIP])
    ankle = frame[pts["ankle"]]
    if height_px == 0:
        return 0.0
    return (ankle[0] - hip_mid[0]) / height_px


def ankle_y(frame: dict, side: str = config.RUNNING_SIDE) -> float:
    return frame[_SIDE_LANDMARKS[side]["ankle"]][1]


def detect_footstrike_frames(ankle_y_series: list[float], min_gap: int = 5) -> list[int]:
    """발목 y좌표(아래로 갈수록 값이 커짐)가 극댓값을 찍는 프레임을 착지 순간으로 본다."""
    footstrikes = []
    for i in range(1, len(ankle_y_series) - 1):
        is_local_max = ankle_y_series[i] > ankle_y_series[i - 1] and ankle_y_series[i] >= ankle_y_series[i + 1]
        if is_local_max and (not footstrikes or i - footstrikes[-1] >= min_gap):
            footstrikes.append(i)
    return footstrikes
