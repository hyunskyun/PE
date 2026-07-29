"""좌표 기반 각도·거리 계산 유틸리티.

모든 좌표는 (x, y) 픽셀 튜플로 다룬다. MediaPipe는 정규화 좌표(0~1)를
주므로, 상위 코드에서 프레임 가로/세로 픽셀 크기를 곱해 변환한 뒤 이
모듈로 넘긴다. 이미지 좌표계는 아래로 갈수록 y가 커진다.
"""

import math
from typing import Optional, Tuple

from posture_analysis.constants import VALID_RUN_DIRECTIONS

Point = Tuple[float, float]


def midpoint(point_a: Point, point_b: Point) -> Point:
    """두 점의 중점을 반환한다."""
    return ((point_a[0] + point_b[0]) / 2, (point_a[1] + point_b[1]) / 2)


def distance(point_a: Point, point_b: Point) -> float:
    """두 점 사이의 유클리드 거리."""
    return math.hypot(point_a[0] - point_b[0], point_a[1] - point_b[1])


def joint_angle(point_a: Point, vertex: Point, point_b: Point) -> Optional[float]:
    """vertex를 꼭짓점으로 하는 A-vertex-B 사이의 내각(도 단위).

    무릎 각도(엉덩이-무릎-발목), 팔꿈치 각도(어깨-팔꿈치-손목) 계산에 쓴다.
    두 점 중 하나가 vertex와 겹치면 각도를 정의할 수 없어 None을 반환한다.
    """
    vec1 = (point_a[0] - vertex[0], point_a[1] - vertex[1])
    vec2 = (point_b[0] - vertex[0], point_b[1] - vertex[1])

    len1 = math.hypot(*vec1)
    len2 = math.hypot(*vec2)
    if len1 == 0 or len2 == 0:
        return None

    cos_angle = (vec1[0] * vec2[0] + vec1[1] * vec2[1]) / (len1 * len2)
    cos_angle = max(-1.0, min(1.0, cos_angle))  # 부동소수점 오차 보정
    return math.degrees(math.acos(cos_angle))


def forward_lean_angle(
    hip_center: Point, shoulder_center: Point, run_direction: int
) -> Optional[float]:
    """수직선 대비 상체(엉덩이->어깨)의 부호 있는 기울기 각도(도 단위).

    진행 방향(run_direction) 기준으로 어깨가 엉덩이보다 앞이면 양수
    (전방 기울기), 뒤면 음수(후방 기울기)가 된다.

    run_direction: 화면 기준 오른쪽 진행이면 +1, 왼쪽 진행이면 -1.
    어깨가 엉덩이보다 아래에 있으면(자세 인식 오류로 추정) None을 반환한다.
    """
    if run_direction not in VALID_RUN_DIRECTIONS:
        raise ValueError(
            f"run_direction은 +1(오른쪽) 또는 -1(왼쪽)이어야 합니다: {run_direction}"
        )

    signed_dx = (shoulder_center[0] - hip_center[0]) * run_direction
    dy = hip_center[1] - shoulder_center[1]  # 위로 갈수록 양수
    if dy <= 0:
        return None
    return math.degrees(math.atan2(signed_dx, dy))
