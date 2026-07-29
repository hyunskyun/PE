"""프레임을 가속 구간 / 최대 속도 구간으로 나눈다.

원리: 엉덩이 중심의 프레임 간 이동량(속도의 대리 지표)을 구해서
이동량이 처음으로 최고점의 일정 비율 이상으로 "유지"되기 시작하는
지점을 두 구간의 경계로 본다. 신뢰할 수 있는 경계를 찾지 못하면
전체 프레임의 앞 40%를 가속 구간으로 보는 단순 규칙으로 대체한다.
"""
from .config import PHASE_ACCEL, PHASE_MAXV
from .metrics import FrameMetrics


def _moving_average(values: list[float | None], window: int) -> list[float | None]:
    n = len(values)
    result = []
    half = window // 2
    for i in range(n):
        chunk = [v for v in values[max(0, i - half): min(n, i + half + 1)] if v is not None]
        result.append(sum(chunk) / len(chunk) if chunk else None)
    return result


def segment_phases(
    frame_metrics: list[FrameMetrics],
    fps: float,
    smoothing_window: int = 5,
    sustain_sec: float = 0.3,
    plateau_ratio: float = 0.85,
) -> list[str]:
    if len(frame_metrics) < 2:
        return [PHASE_ACCEL for _ in frame_metrics]

    hip_x = [m.hip_x for m in frame_metrics]
    raw_speed: list[float | None] = [None] + [
        abs(hip_x[i] - hip_x[i - 1]) for i in range(1, len(hip_x))
    ]
    speed = _moving_average(raw_speed, smoothing_window)

    valid_speeds = [s for s in speed if s is not None]
    boundary = None
    if valid_speeds:
        threshold = max(valid_speeds) * plateau_ratio
        sustain_frames = max(1, int(sustain_sec * fps))
        streak = 0
        for i, s in enumerate(speed):
            if s is not None and s >= threshold:
                streak += 1
                if streak >= sustain_frames:
                    boundary = i - sustain_frames + 1
                    break
            else:
                streak = 0

    if boundary is None:
        boundary = int(len(frame_metrics) * 0.4)  # 대체 규칙

    return [PHASE_ACCEL if i < boundary else PHASE_MAXV for i in range(len(frame_metrics))]
