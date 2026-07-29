"""구간 분류: 가속 구간 vs 최대 속도 유지 구간.

가장 단순한 기준으로 "출발 후 경과 시간"을 사용한다. 스타트 라인을 지나는 시각을
따로 감지하지 않으므로, 영상은 출발 순간부터 촬영되었다고 가정한다.
더 정교한 분석이 필요하면 accel_duration_sec을 사용자가 실측한 10m 통과 시간 등으로
바꿔주면 된다.
"""

ACCELERATION = "acceleration"
MAX_VELOCITY = "max_velocity"


def classify_phase(time_sec, accel_duration_sec):
    return ACCELERATION if time_sec < accel_duration_sec else MAX_VELOCITY
