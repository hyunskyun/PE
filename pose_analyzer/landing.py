"""착지 순간(발이 지면에 가장 가까워지는 프레임)을 감지하는 모듈."""
from __future__ import annotations

from typing import Dict, List, Optional


def _local_maxima(values: List[Optional[float]], min_distance: int) -> List[int]:
    """리스트에서 지역 최댓값 인덱스를 찾는다. 값이 None인 지점은 건너뛴다."""
    peaks: List[int] = []
    for i in range(1, len(values) - 1):
        if values[i] is None or values[i - 1] is None or values[i + 1] is None:
            continue
        if values[i] >= values[i - 1] and values[i] >= values[i + 1]:
            if not peaks or i - peaks[-1] >= min_distance:
                peaks.append(i)
    return peaks


def find_landing_frames(ankle_y_series: Dict[str, List[Optional[float]]], min_distance: int = 5) -> Dict[int, str]:
    """양쪽 발목의 y좌표(이미지 좌표계, 아래로 갈수록 값이 커짐)에서 지역 최댓값을 찾는다.

    지역 최댓값 = 발이 화면에서 가장 아래(지면에 가장 가까움) = 착지 순간으로 본다.

    Returns:
        {프레임 인덱스: 착지한 다리('left' 또는 'right')}
    """
    landings: Dict[int, str] = {}
    for side, series in ankle_y_series.items():
        for idx in _local_maxima(series, min_distance=min_distance):
            landings[idx] = side
    return landings
