"""랜드마크 좌표로부터 자세 지표(각도/비율/거리)를 계산한다."""

from .geometry import angle_at_point, distance, forward_lean_angle, midpoint


def estimate_height_px(landmarks):
    """코~발목 중점 사이 세로 픽셀 거리로 신장을 근사한다.

    실제 신장(cm)이 없어도 보폭/착지거리와 같은 픽셀 단위이므로
    비율 계산에는 그대로 사용할 수 있다. (2D 영상의 한계로 완벽한
    값은 아니며, 프레임마다 값이 흔들릴 수 있어 analyzer 에서
    여러 프레임의 중앙값을 사용한다.)
    """
    nose = landmarks["NOSE"]
    ankle_mid = midpoint(landmarks["LEFT_ANKLE"], landmarks["RIGHT_ANKLE"])
    return abs(ankle_mid[1] - nose[1])


def compute_trunk_lean_deg(landmarks, travel_direction):
    shoulder_mid = midpoint(landmarks["LEFT_SHOULDER"], landmarks["RIGHT_SHOULDER"])
    hip_mid = midpoint(landmarks["LEFT_HIP"], landmarks["RIGHT_HIP"])
    return forward_lean_angle(hip_mid, shoulder_mid, travel_direction)


def compute_knee_flexion_deg(landmarks):
    """좌우 무릎 각도의 평균. 스탠스/스윙 다리를 구분하지 않는 단순화된 값이다."""
    left = angle_at_point(landmarks["LEFT_HIP"], landmarks["LEFT_KNEE"], landmarks["LEFT_ANKLE"])
    right = angle_at_point(landmarks["RIGHT_HIP"], landmarks["RIGHT_KNEE"], landmarks["RIGHT_ANKLE"])
    return (left + right) / 2


def compute_stride_ratio(landmarks, height_px):
    stride_px = distance(landmarks["LEFT_ANKLE"], landmarks["RIGHT_ANKLE"])
    return stride_px / height_px


def compute_arm_swing_deg(landmarks):
    """어깨-팔꿈치-손목 각도의 평균으로 팔치기 각도를 근사한다."""
    left = angle_at_point(landmarks["LEFT_SHOULDER"], landmarks["LEFT_ELBOW"], landmarks["LEFT_WRIST"])
    right = angle_at_point(landmarks["RIGHT_SHOULDER"], landmarks["RIGHT_ELBOW"], landmarks["RIGHT_WRIST"])
    return (left + right) / 2


def compute_overstride_offset_ratio(landmarks, landing_ankle_name, height_px):
    """착지 순간 발목과 엉덩이 중심의 수평 거리를 신장 대비 비율로 반환한다."""
    ankle = landmarks[landing_ankle_name]
    hip_mid = midpoint(landmarks["LEFT_HIP"], landmarks["RIGHT_HIP"])
    return abs(ankle[0] - hip_mid[0]) / height_px
