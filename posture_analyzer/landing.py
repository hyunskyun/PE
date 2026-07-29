"""착지 순간(발이 지면에 닿는 프레임)을 찾고, 착지 관련 지표를 계산한다."""
from dataclasses import dataclass

from .metrics import FrameMetrics


@dataclass
class LandingEvent:
    frame_idx: int
    foot: str  # "l" 또는 "r"
    stride_ratio: float
    landing_hip_offset_ratio: float


def _find_local_maxima(values: list[float], min_gap: int) -> list[int]:
    """이미지 좌표는 y가 클수록 아래쪽이므로, 발목 y좌표의 극댓값이
    발이 가장 낮은 지점 즉 착지 순간에 해당한다."""
    peaks: list[int] = []
    for i in range(1, len(values) - 1):
        if values[i] > values[i - 1] and values[i] >= values[i + 1]:
            if peaks and i - peaks[-1] < min_gap:
                if values[i] > values[peaks[-1]]:
                    peaks[-1] = i
            else:
                peaks.append(i)
    return peaks


def detect_landing_events(
    frame_metrics: list[FrameMetrics], fps: float, min_interval_sec: float = 0.15
) -> list[LandingEvent]:
    min_gap = max(1, int(min_interval_sec * fps))
    left_peaks = _find_local_maxima([m.ankle_l_y for m in frame_metrics], min_gap)
    right_peaks = _find_local_maxima([m.ankle_r_y for m in frame_metrics], min_gap)

    candidates = [(i, "l") for i in left_peaks] + [(i, "r") for i in right_peaks]
    candidates.sort(key=lambda item: item[0])

    events = []
    for idx, foot in candidates:
        m = frame_metrics[idx]
        if not m.body_height_px:
            continue
        stride_px = abs(m.ankle_l_x - m.ankle_r_x)
        landing_ankle_x = m.ankle_l_x if foot == "l" else m.ankle_r_x
        offset_px = abs(landing_ankle_x - m.hip_x)
        events.append(
            LandingEvent(
                frame_idx=idx,
                foot=foot,
                stride_ratio=stride_px / m.body_height_px,
                landing_hip_offset_ratio=offset_px / m.body_height_px,
            )
        )
    return events
