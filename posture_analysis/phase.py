"""가속 구간 / 최대 속도 구간 분류.

가장 정확한 방법은 실제 구간별 통과 시간(스플릿 타임)을 쓰는 것이지만,
고등학생이 스마트워치나 스타트 신호 없이 촬영한 영상에서는 구하기 어렵다.
그래서 기본값은 '영상 전체 길이 대비 비율'로 단순화하고, 사용자가 가속
종료 시각을 알고 있으면 그 값을 우선 사용하도록 했다.
"""

ACCELERATION = "acceleration"
MAX_VELOCITY = "max_velocity"

# 50m 기록 기준 일반적인 고등학생 스프린터는 대략 25~30m 지점에서
# 최고 속도에 도달한다. 전체 촬영 시간 중 이 지점까지 걸리는 비율의
# 근사값을 기본 경계로 사용한다. (조정 가능)
DEFAULT_ACCELERATION_FRACTION = 0.4


def classify_phase(timestamp_sec, total_duration_sec, acceleration_end_sec=None):
    """주어진 시각이 가속 구간인지 최대 속도 구간인지 반환한다.

    acceleration_end_sec: 가속 구간이 끝나는 시각(초)을 사용자가 직접
        입력했다면 그 값을 경계로 쓴다. 없으면 전체 길이의
        DEFAULT_ACCELERATION_FRACTION 지점을 경계로 쓴다.
    """
    if acceleration_end_sec is None:
        acceleration_end_sec = total_duration_sec * DEFAULT_ACCELERATION_FRACTION

    if timestamp_sec <= acceleration_end_sec:
        return ACCELERATION
    return MAX_VELOCITY
