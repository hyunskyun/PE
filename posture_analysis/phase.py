"""프레임을 가속 구간 / 최대 속도 구간으로 나눈다."""

from .config import DEFAULT_PHASE_SPLIT_RATIO, PHASE_ACCELERATION, PHASE_MAX_VELOCITY


def phase_for_frame(frame_idx, split_frame_idx):
    return PHASE_ACCELERATION if frame_idx < split_frame_idx else PHASE_MAX_VELOCITY


def resolve_split_frame_idx(total_frames, fps, split_time_sec=None):
    """가속 구간이 끝나는 프레임 번호를 계산한다.

    split_time_sec(사용자가 입력한 구간별 시간)이 있으면 그것을 쓰고,
    없으면 전체 프레임의 DEFAULT_PHASE_SPLIT_RATIO 지점을 기준으로 삼는다.
    """
    if split_time_sec is not None and fps > 0:
        return int(split_time_sec * fps)
    return int(total_frames * DEFAULT_PHASE_SPLIT_RATIO)
