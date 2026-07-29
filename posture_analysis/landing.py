"""착지(발이 지면에 닿는 순간) 프레임을 근사적으로 찾아내는 로직.

깊이 카메라나 지면반발력 센서 없이 2D 영상만으로 착지를 정확히
판정할 수는 없다. 여기서는 발목의 세로 좌표(y, 아래로 갈수록 값이 큼)가
주변 프레임 대비 극댓값(=발이 가장 아래에 있는 지점)을 이루는 프레임을
착지 후보로 본다.
"""


def find_landing_frames(ankle_y_by_frame, window=3, min_gap=5):
    """ankle_y_by_frame: {frame_idx: y좌표}. 착지로 추정되는 frame_idx 리스트 반환."""
    indices = sorted(ankle_y_by_frame)
    if not indices:
        return []

    candidates = []
    for pos, idx in enumerate(indices):
        lo = max(0, pos - window)
        hi = min(len(indices), pos + window + 1)
        neighborhood = [ankle_y_by_frame[indices[p]] for p in range(lo, hi)]
        if ankle_y_by_frame[idx] == max(neighborhood):
            candidates.append(idx)

    landing_frames = []
    last_idx = -min_gap
    for idx in candidates:
        if idx - last_idx >= min_gap:
            landing_frames.append(idx)
            last_idx = idx
    return landing_frames
