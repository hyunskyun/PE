"""좌표 기반 각도/거리 계산에 쓰이는 순수 함수 모음."""

import math


def midpoint(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def angle_at_point(a, b, c):
    """점 b를 꼭짓점으로 하는 a-b-c 사잇각(0~180도).

    무릎 각도(엉덩이-무릎-발목)처럼 관절 굴곡각을 구할 때 사용한다.
    """
    v1 = (a[0] - b[0], a[1] - b[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag = math.hypot(*v1) * math.hypot(*v2)
    if mag == 0:
        return 0.0
    cos_angle = max(-1.0, min(1.0, dot / mag))
    return math.degrees(math.acos(cos_angle))


def forward_lean_angle(hip, shoulder, travel_direction):
    """수직선 대비 상체가 진행 방향으로 얼마나 기울었는지(도).

    이미지 좌표는 아래로 갈수록 y가 커지므로, 엉덩이 y - 어깨 y 를
    "몸통 세로 길이"로 사용한다. travel_direction 은 +1(오른쪽으로 달림)
    또는 -1(왼쪽으로 달림)이며, 어깨가 진행 방향 쪽으로 나와 있으면
    양수(전방 기울기)가 되도록 부호를 맞춘다.
    """
    vertical_extent = hip[1] - shoulder[1]
    horizontal_offset = (shoulder[0] - hip[0]) * travel_direction
    return math.degrees(math.atan2(horizontal_offset, max(vertical_extent, 1e-6)))
