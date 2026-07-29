"""가속 구간과 최대 속도 구간을 나누는 로직."""
from __future__ import annotations

# 구간별 시간 정보를 모를 때 사용하는 기본값(초). 일반 고등학생 50m 기록 기준
# 대략 첫 2초 안팎을 가속 구간으로 본다. --split-sec 옵션으로 덮어쓸 수 있다.
DEFAULT_ACCELERATION_END_SEC = 2.0

ACCELERATION = "acceleration"
MAX_VELOCITY = "max_velocity"


def classify_phase(time_sec: float, acceleration_end_sec: float = DEFAULT_ACCELERATION_END_SEC) -> str:
    """acceleration_end_sec 이전이면 가속 구간, 이후면 최대 속도 구간으로 분류."""
    return ACCELERATION if time_sec < acceleration_end_sec else MAX_VELOCITY
