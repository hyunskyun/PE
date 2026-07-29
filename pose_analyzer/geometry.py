"""좌표 기반 각도/거리 계산에 쓰이는 순수 수학 함수 모음.

이 모듈은 OpenCV나 MediaPipe에 의존하지 않는다. (x, y) 좌표 튜플만 다루므로
파이썬 밖(JavaScript, Kotlin 등)으로 그대로 옮겨써도 동작이 같다.
"""
from __future__ import annotations

import math
from typing import Tuple

Point = Tuple[float, float]


def distance(a: Point, b: Point) -> float:
    """두 점 사이의 유클리드 거리."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def midpoint(a: Point, b: Point) -> Point:
    """두 점의 중점."""
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def angle_deg(a: Point, b: Point, c: Point) -> float:
    """b를 꼭짓점으로 하는 a-b-c 각도(0~180도). 무릎각·팔치기각 계산에 사용."""
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    mag = math.hypot(*ba) * math.hypot(*bc)
    if mag == 0:
        return 0.0
    cos_angle = (ba[0] * bc[0] + ba[1] * bc[1]) / mag
    cos_angle = max(-1.0, min(1.0, cos_angle))
    return math.degrees(math.acos(cos_angle))


def tilt_from_vertical_deg(top: Point, bottom: Point) -> float:
    """top->bottom 선분이 수직선과 이루는 각도(0~90도).

    상체 전방 기울기 계산에 사용한다. 값이 클수록 앞으로 많이 기운 것이다.
    """
    dx = bottom[0] - top[0]
    dy = bottom[1] - top[1]
    if dy == 0:
        return 90.0
    return math.degrees(math.atan(abs(dx) / abs(dy)))
