"""임계 범위와의 이탈 정도를 0~100점 점수로 변환하는 모듈."""
from __future__ import annotations

from typing import Optional


def score_from_range(value: Optional[float], low: float, high: float, tolerance_ratio: float = 0.5) -> Optional[float]:
    """범위 안이면 100점, 벗어나면 벗어난 정도에 비례해 감점(최저 0점)한다.

    tolerance_ratio: 범위 폭(high-low)의 몇 배만큼 벗어나야 0점이 되는지를 정하는 계수.
    """
    if value is None:
        return None
    if low <= value <= high:
        return 100.0

    span = max(high - low, 1e-6)
    deviation = (low - value) if value < low else (value - high)
    max_deviation = span * tolerance_ratio
    score = 100.0 * (1 - deviation / max_deviation)
    return max(0.0, min(100.0, score))
