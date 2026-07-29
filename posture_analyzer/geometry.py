"""좌표 기반 각도/거리 계산에 쓰는 순수 함수 모음.

MediaPipe나 OpenCV에 의존하지 않아서 단독으로 테스트하기 쉽다.
"""
from dataclasses import dataclass
from math import acos, atan2, degrees, hypot


@dataclass
class Point:
    x: float
    y: float
    visibility: float = 1.0


def midpoint(a: Point, b: Point) -> Point:
    return Point(
        x=(a.x + b.x) / 2,
        y=(a.y + b.y) / 2,
        visibility=min(a.visibility, b.visibility),
    )


def distance(a: Point, b: Point) -> float:
    return hypot(a.x - b.x, a.y - b.y)


def angle_at_vertex(a: Point, b: Point, c: Point) -> float | None:
    """세 점 a-b-c 중 꼭짓점 b에서의 각도(도)를 반환한다."""
    bax, bay = a.x - b.x, a.y - b.y
    bcx, bcy = c.x - b.x, c.y - b.y
    mag_ba, mag_bc = hypot(bax, bay), hypot(bcx, bcy)
    if mag_ba < 1e-6 or mag_bc < 1e-6:
        return None
    cos_val = (bax * bcx + bay * bcy) / (mag_ba * mag_bc)
    cos_val = max(-1.0, min(1.0, cos_val))  # 부동소수점 오차로 인한 범위 이탈 방지
    return degrees(acos(cos_val))


def lean_angle_from_vertical(top: Point, bottom: Point) -> float:
    """bottom -> top 벡터가 수직선(위쪽)과 이루는 각도(도, 항상 양수)를 반환한다.

    이미지 좌표는 y가 아래로 갈수록 커지므로 "위쪽"은 y가 작아지는 방향이다.
    좌우 방향(전방/후방 기울임)은 구분하지 않고 기울어진 크기만 계산한다.
    """
    dx = top.x - bottom.x
    dy = bottom.y - top.y
    if dx == 0 and dy == 0:
        return 0.0
    return degrees(atan2(abs(dx), max(dy, 1e-6)))
