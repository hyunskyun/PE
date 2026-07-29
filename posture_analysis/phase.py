"""분석 구간 경계 결정과 가속/최대 속도 구간 분류.

가장 정확한 방법은 사용자가 실제 구간 통과 시각을 직접 입력하는 것이다.
입력이 없을 때만 '영상 길이 대비 비율'로 가속 구간 경계를 추정하는
fallback을 쓰며, 이 추정값은 과학적 근거가 약한 자동 추정치임을 결과에
표시한다(phase_boundary_source).
"""

from typing import Optional, Tuple

ACCELERATION = "acceleration"
MAX_VELOCITY = "max_velocity"

BOUNDARY_SOURCE_USER = "user_input"
BOUNDARY_SOURCE_ESTIMATED = "estimated_fraction"

# 가속 구간 종료 시각을 사용자가 입력하지 않았을 때 쓰는 fallback 비율.
# (분석 구간 길이의 40% 지점) 실측 근거가 있는 값이 아니므로 참고용이다.
DEFAULT_ACCELERATION_FRACTION = 0.4


def resolve_phase_boundaries(
    total_duration_sec: float,
    analysis_start_sec: Optional[float] = None,
    acceleration_end_sec: Optional[float] = None,
    analysis_end_sec: Optional[float] = None,
) -> Tuple[float, float, float, str]:
    """분석 시작/가속 종료/분석 종료 시각을 확정하고 유효성을 검증한다.

    반환: (analysis_start, acceleration_end, analysis_end, boundary_source)
    boundary_source는 가속 종료 시각이 사용자 입력인지 비율 추정인지 나타낸다.
    """
    if total_duration_sec <= 0:
        raise ValueError(f"영상 길이는 0보다 커야 합니다: {total_duration_sec}")

    start = 0.0 if analysis_start_sec is None else analysis_start_sec
    end = total_duration_sec if analysis_end_sec is None else analysis_end_sec

    if start < 0:
        raise ValueError(f"분석 시작 시각은 0 이상이어야 합니다: {start}")
    if start >= end:
        raise ValueError(
            f"분석 시작 시각({start}s)은 분석 종료 시각({end}s)보다 작아야 합니다"
        )

    if acceleration_end_sec is None:
        accel_end = start + (end - start) * DEFAULT_ACCELERATION_FRACTION
        boundary_source = BOUNDARY_SOURCE_ESTIMATED
    else:
        accel_end = acceleration_end_sec
        boundary_source = BOUNDARY_SOURCE_USER
        if not (start <= accel_end <= end):
            raise ValueError(
                f"가속 구간 종료 시각({accel_end}s)은 분석 범위 "
                f"[{start}s, {end}s] 안에 있어야 합니다"
            )

    return start, accel_end, end, boundary_source


def classify_phase(
    timestamp_sec: float,
    analysis_start_sec: float,
    acceleration_end_sec: float,
    analysis_end_sec: float,
) -> Optional[str]:
    """주어진 시각의 구간을 반환한다. 분석 범위 밖이면 None."""
    if timestamp_sec < analysis_start_sec or timestamp_sec > analysis_end_sec:
        return None
    if timestamp_sec <= acceleration_end_sec:
        return ACCELERATION
    return MAX_VELOCITY
