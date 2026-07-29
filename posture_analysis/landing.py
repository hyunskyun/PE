"""착지(footstrike) 프레임 탐지.

발목의 y좌표(픽셀, 아래로 갈수록 값이 커짐)가 국소 최댓값을 이루는
프레임을 '발이 가장 낮은 지점 = 착지 순간'으로 근사한다. 간단한
3프레임 비교(전-현재-후)만 사용하는 휴리스틱으로, 실제 지면 접촉
센서만큼 정확하지는 않지만 측면 영상만으로 착지 시점을 추정하기에
충분한 수준이다.
"""

from posture_analysis import constants as lm


def find_landing_frames(ankle_y_track, ankle_index):
    """ankle_y_track: [(frame_idx, y_px) ...] (None 허용, 프레임 순서 보장)

    반환: 착지로 판단된 frame_idx 리스트
    """
    landing_frames = []
    for i in range(1, len(ankle_y_track) - 1):
        prev_idx, prev_y = ankle_y_track[i - 1]
        cur_idx, cur_y = ankle_y_track[i]
        next_idx, next_y = ankle_y_track[i + 1]

        if prev_y is None or cur_y is None or next_y is None:
            continue

        if cur_y >= prev_y and cur_y >= next_y:
            landing_frames.append(cur_idx)

    return landing_frames


def build_ankle_y_tracks(frame_landmarks_list):
    """전체 프레임의 랜드마크 리스트에서 좌/우 발목 y좌표 트랙을 만든다.

    frame_landmarks_list: [landmarks_dict_or_None, ...] (프레임 순서)
    반환: {lm.LEFT_ANKLE: [(idx, y), ...], lm.RIGHT_ANKLE: [(idx, y), ...]}
    """
    tracks = {lm.LEFT_ANKLE: [], lm.RIGHT_ANKLE: []}

    for frame_idx, landmarks in enumerate(frame_landmarks_list):
        for ankle_index in tracks:
            if landmarks and ankle_index in landmarks:
                _, y, visibility = landmarks[ankle_index]
                y_value = y if visibility >= lm.MIN_VISIBILITY else None
            else:
                y_value = None
            tracks[ankle_index].append((frame_idx, y_value))

    return tracks
