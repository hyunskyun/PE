"""좌표 기반 각도·거리 계산 함수 모음.

모든 좌표는 (x, y) 픽셀 튜플이며, 이미지 좌표계(y는 아래로 갈수록 증가)를 따른다.
"""
import math


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def midpoint(a, b):
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def angle_at_vertex(a, b, c):
    """점 b를 꼭짓점으로 하는 각 ABC를 度로 반환한다. (예: 엉덩이-무릎-발목 -> 무릎 각도)"""
    v1 = (a[0] - b[0], a[1] - b[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    len1 = math.hypot(*v1)
    len2 = math.hypot(*v2)
    if len1 < 1e-6 or len2 < 1e-6:
        return 0.0
    cos_angle = (v1[0] * v2[0] + v1[1] * v2[1]) / (len1 * len2)
    cos_angle = max(-1.0, min(1.0, cos_angle))
    return math.degrees(math.acos(cos_angle))


def angle_from_vertical(p_top, p_bottom):
    """p_bottom -> p_top 벡터와 수직(위쪽) 축 사이의 각도를 度로 반환한다.

    예) 상체 기울기 = angle_from_vertical(어깨중점, 엉덩이중점)
        완전히 곧게 서 있으면 0도, 옆으로 많이 기울수록 90도에 가까워진다.
    """
    dx = p_top[0] - p_bottom[0]
    dy = p_bottom[1] - p_top[1]  # 이미지 y는 아래로 증가하므로 부호를 뒤집어 "위쪽"을 양수로 만든다
    return math.degrees(math.atan2(abs(dx), abs(dy) + 1e-9))
