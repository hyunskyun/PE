"""착지(발이 지면에 닿는) 순간 탐지.

깊이 정보가 없는 2D 옆모습 영상에서는 실제 지면 접촉을 직접 알 수 없다.
대신 "발목의 화면상 y좌표가 국소적으로 가장 커지는(=가장 낮아지는) 시점"을
착지 순간의 근사치로 사용한다. 카메라가 크게 흔들리거나 기울어 촬영되면
오차가 커질 수 있다는 점을 보고서의 한계로 함께 언급하면 된다.
"""


def _local_maxima(series, min_gap_frames):
    """series: [(frame_idx, y_value), ...]. 값이 커지는 국소 최댓값 인덱스만 뽑는다."""
    peaks = []
    for i in range(1, len(series) - 1):
        _, y_prev = series[i - 1]
        _, y_curr = series[i]
        _, y_next = series[i + 1]
        if y_curr >= y_prev and y_curr >= y_next:
            peaks.append(i)

    # min_gap_frames 이내에 몰린 peak는 그 중 y가 가장 큰 것 하나만 남긴다.
    filtered = []
    for i in peaks:
        if filtered and series[i][0] - series[filtered[-1]][0] < min_gap_frames:
            if series[i][1] > series[filtered[-1]][1]:
                filtered[-1] = i
        else:
            filtered.append(i)
    return filtered


def detect_landing_frames(frame_metrics_list, fps, min_interval_sec=0.15):
    """양발 각각 착지 후보를 찾아 시간순으로 합친 프레임 인덱스 목록을 반환한다."""
    min_gap_frames = max(1, int(fps * min_interval_sec))

    left_series = [(f.frame_idx, f.left_ankle_y) for f in frame_metrics_list]
    right_series = [(f.frame_idx, f.right_ankle_y) for f in frame_metrics_list]

    left_peaks = {left_series[i][0] for i in _local_maxima(left_series, min_gap_frames)}
    right_peaks = {right_series[i][0] for i in _local_maxima(right_series, min_gap_frames)}

    return sorted(left_peaks | right_peaks)
