"""프레임을 가속 구간 / 최대 속도 구간으로 나누는 함수 모음."""

from sprint_core import config


def classify_phases_by_fraction(n_frames: int, accel_fraction: float = config.ACCEL_PHASE_FRACTION) -> list[str]:
    """앞쪽 일정 비율(기본 40%)을 가속 구간으로, 나머지를 최대 속도 구간으로 본다."""
    split = int(n_frames * accel_fraction)
    return [config.PHASE_ACCEL] * split + [config.PHASE_MAXV] * (n_frames - split)


def classify_phases_by_velocity(hip_x: list[float], fps: float, plateau_ratio: float = 0.85) -> list[str]:
    """엉덩이 수평 속도가 최고 속도의 plateau_ratio 이상이 되는 시점부터를
    최대 속도 구간으로 본다. 속도가 계속 증가 중이면 가속 구간이다.
    """
    n = len(hip_x)
    if n < 3:
        return [config.PHASE_ACCEL] * n

    velocities = [abs(hip_x[i + 1] - hip_x[i]) * fps for i in range(n - 1)]
    velocities.append(velocities[-1] if velocities else 0.0)
    peak = max(velocities) or 1.0

    phases = []
    for v in velocities:
        phases.append(config.PHASE_MAXV if v >= plateau_ratio * peak else config.PHASE_ACCEL)
    return phases


def classify_phases(n_frames: int, hip_x: list[float] | None = None, fps: float | None = None,
                     method: str = "fraction") -> list[str]:
    if method == "velocity" and hip_x is not None and fps:
        return classify_phases_by_velocity(hip_x, fps)
    return classify_phases_by_fraction(n_frames)
