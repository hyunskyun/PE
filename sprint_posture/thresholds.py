"""구간별(가속/최대속도) 임계 범위와 판정 로직.

숫자는 보고서에 제시된 값(상체 기울기, 보폭 비율)은 그대로 쓰고, 참고 문헌이 마땅치
않은 무릎 각도·팔치기 각도는 일반적인 스프린트 자세 범위를 참고한 추정치다.
전부 이 dict 하나만 고치면 되므로 실측 데이터로 쉽게 교체할 수 있다.
"""

# 프레임마다 계산되는 연속 지표. (최솟값, 최댓값) degree.
FRAME_THRESHOLDS = {
    "acceleration": {
        "trunk_lean_deg": (15, 45),
        "knee_angle_deg": (80, 150),
        "arm_swing_deg": (30, 70),
    },
    "max_velocity": {
        "trunk_lean_deg": (5, 12),
        "knee_angle_deg": (90, 150),
        "arm_swing_deg": (25, 60),
    },
}

# 착지 순간마다 한 번씩 계산되는 지표. 신장 대비 비율(무차원)로 비교한다.
EVENT_THRESHOLDS = {
    "acceleration": {
        "stride_ratio": (0.80, 1.15),
        "landing_offset_ratio": (0.0, 0.12),
    },
    "max_velocity": {
        "stride_ratio": (0.85, 1.25),
        "landing_offset_ratio": (0.0, 0.15),
    },
}


def judge(value, value_range):
    """value가 range 밖이면 'low' 또는 'high', 안이면 None을 반환한다."""
    low, high = value_range
    if value < low:
        return "low"
    if value > high:
        return "high"
    return None
