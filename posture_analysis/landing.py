"""착지(footstrike) 후보 프레임 탐지.

발목의 y좌표(픽셀, 아래로 갈수록 값이 커짐)가 뚜렷한 국소 최댓값을 이루는
프레임을 '발이 가장 낮은 지점 = 착지 순간'으로 근사한다.

노이즈 대응:
1. 이동 중앙값으로 y좌표 시계열을 평활화한다.
2. 주변 프레임 대비 최소 돌출량(min_prominence_px)을 넘는 봉우리만
   착지 후보로 인정한다 (평평한 구간·미세 흔들림 제외).
3. 같은 발에서 시간상 너무 가까운 후보(min_interval_sec 이내)는 하나로
   병합하고, 발이 가장 낮은 프레임을 대표로 남긴다.

지면 접촉 센서만큼 정확하지는 않지만, 측면 영상만으로 착지 시점을
추정하는 순수 함수라 합성 좌표로 검증할 수 있다.
"""

from typing import Dict, List, Optional, Sequence, Tuple

from posture_analysis import constants as lm

# 이동 중앙값 평활화 윈도 크기 (홀수 권장)
SMOOTHING_WINDOW = 5
# 같은 발의 연속 착지로 인정하는 최소 시간 간격 (초)
MIN_LANDING_INTERVAL_SEC = 0.25
# 착지 봉우리로 인정하는 최소 돌출량 (px)
MIN_PROMINENCE_PX = 2.0

# (frame_idx, y_px 또는 None) 시퀀스
YTrack = Sequence[Tuple[int, Optional[float]]]


def smooth_series(
    values: Sequence[Optional[float]], window: int = SMOOTHING_WINDOW
) -> List[Optional[float]]:
    """이동 중앙값 평활화. None 위치는 None으로 유지한다.

    각 위치에서 window 범위 안의 유효한(None이 아닌) 값들의 중앙값을
    취한다. 유효 값이 하나도 없으면 None.
    """
    if window < 1:
        raise ValueError(f"윈도 크기는 1 이상이어야 합니다: {window}")

    half = window // 2
    smoothed: List[Optional[float]] = []
    for i, value in enumerate(values):
        if value is None:
            smoothed.append(None)
            continue
        neighborhood = [
            v for v in values[max(0, i - half): i + half + 1] if v is not None
        ]
        neighborhood.sort()
        mid = len(neighborhood) // 2
        if len(neighborhood) % 2 == 1:
            smoothed.append(neighborhood[mid])
        else:
            smoothed.append((neighborhood[mid - 1] + neighborhood[mid]) / 2)
    return smoothed


def find_landing_frames(
    ankle_y_track: YTrack,
    fps: float,
    min_interval_sec: float = MIN_LANDING_INTERVAL_SEC,
    min_prominence_px: float = MIN_PROMINENCE_PX,
    smoothing_window: int = SMOOTHING_WINDOW,
) -> List[int]:
    """한쪽 발목의 y좌표 트랙에서 착지 후보 frame_idx 리스트를 반환한다.

    ankle_y_track: [(frame_idx, y_px 또는 None), ...] (프레임 순서 보장)
    fps: 영상 프레임률. 최소 착지 간격을 프레임 수로 환산할 때 쓴다.
    """
    if fps <= 0:
        raise ValueError(f"fps는 0보다 커야 합니다: {fps}")

    frame_indices = [idx for idx, _y in ankle_y_track]
    raw_values = [y for _idx, y in ankle_y_track]
    values = smooth_series(raw_values, smoothing_window)

    min_interval_frames = max(1, int(round(min_interval_sec * fps)))
    # 돌출량 판단에 쓰는 주변 구간 반경 (최소 착지 간격과 같은 크기)
    prominence_radius = min_interval_frames

    candidates: List[Tuple[int, float]] = []  # (트랙 내 위치 i, y값)
    for i in range(1, len(values) - 1):
        prev_y, cur_y, next_y = values[i - 1], values[i], values[i + 1]
        if prev_y is None or cur_y is None or next_y is None:
            continue
        if not (cur_y >= prev_y and cur_y >= next_y):
            continue

        # 주변 구간의 최저점 대비 충분히 돌출된 봉우리만 인정한다
        neighborhood = [
            v
            for v in values[max(0, i - prominence_radius): i + prominence_radius + 1]
            if v is not None
        ]
        if cur_y - min(neighborhood) < min_prominence_px:
            continue

        candidates.append((i, cur_y))

    return _merge_close_candidates(candidates, frame_indices, min_interval_frames)


def _merge_close_candidates(
    candidates: List[Tuple[int, float]],
    frame_indices: List[int],
    min_interval_frames: int,
) -> List[int]:
    """min_interval_frames 이내로 붙어 있는 후보들을 하나로 병합한다.

    같은 착지로 보이는 그룹에서는 y가 가장 큰(발이 가장 낮은) 프레임을
    대표로 남긴다.
    """
    landing_frames: List[int] = []
    group: List[Tuple[int, float]] = []

    for candidate in candidates:
        if group and candidate[0] - group[-1][0] >= min_interval_frames:
            best_i, _best_y = max(group, key=lambda c: c[1])
            landing_frames.append(frame_indices[best_i])
            group = []
        group.append(candidate)

    if group:
        best_i, _best_y = max(group, key=lambda c: c[1])
        landing_frames.append(frame_indices[best_i])

    return landing_frames


def build_ankle_y_tracks(
    frame_landmarks_list: Sequence[Optional[dict]],
) -> Dict[int, List[Tuple[int, Optional[float]]]]:
    """전체 프레임의 랜드마크 리스트에서 좌/우 발목 y좌표 트랙을 만든다.

    frame_landmarks_list: [landmarks_dict_or_None, ...] (프레임 순서)
    반환: {lm.LEFT_ANKLE: [(idx, y), ...], lm.RIGHT_ANKLE: [(idx, y), ...]}
    좌우 발목 트랙은 서로 독립적으로 만들어지고 독립적으로 착지 검출된다.
    """
    tracks: Dict[int, List[Tuple[int, Optional[float]]]] = {
        lm.LEFT_ANKLE: [],
        lm.RIGHT_ANKLE: [],
    }

    for frame_idx, landmarks in enumerate(frame_landmarks_list):
        for ankle_index in tracks:
            if landmarks and ankle_index in landmarks:
                _, y, visibility = landmarks[ankle_index]
                y_value = y if visibility >= lm.MIN_VISIBILITY else None
            else:
                y_value = None
            tracks[ankle_index].append((frame_idx, y_value))

    return tracks
