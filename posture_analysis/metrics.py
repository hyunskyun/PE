"""프레임 하나에서 자세 지표를 계산하는 함수 모음.

`landmarks` 인자는 {랜드마크 번호: (x_px, y_px, visibility)} 형태의 딕셔너리.
각 함수는 계산이 불가능하면(관절이 안 보이면) None을 반환한다.
"""

from posture_analysis import constants as lm
from posture_analysis.geometry import distance, forward_lean_angle, joint_angle, midpoint


def _visible(landmarks, index):
    point = landmarks.get(index)
    if point is None:
        return None
    x, y, visibility = point
    if visibility < lm.MIN_VISIBILITY:
        return None
    return (x, y)


def _pick_visible_side(landmarks, left_indices, right_indices):
    """양쪽 다리(또는 팔) 중 세 관절이 모두 잘 보이는 쪽을 고른다.

    측면 촬영 특성상 카메라와 가까운 쪽 다리/팔이 대체로 더 잘 보인다.
    둘 다 보이면 평균 visibility가 더 높은 쪽을 사용한다.
    """
    def avg_visibility(indices):
        points = [landmarks.get(i) for i in indices]
        if any(p is None for p in points):
            return -1
        return sum(p[2] for p in points) / len(points)

    left_score = avg_visibility(left_indices)
    right_score = avg_visibility(right_indices)

    if left_score < 0 and right_score < 0:
        return None
    return left_indices if left_score >= right_score else right_indices


def trunk_lean_deg(landmarks):
    """상체 전방 기울기 (도). 어깨/엉덩이 중점을 이용한다."""
    l_sh, r_sh = _visible(landmarks, lm.LEFT_SHOULDER), _visible(landmarks, lm.RIGHT_SHOULDER)
    l_hip, r_hip = _visible(landmarks, lm.LEFT_HIP), _visible(landmarks, lm.RIGHT_HIP)
    if not (l_sh and r_sh and l_hip and r_hip):
        return None

    shoulder_center = midpoint(l_sh, r_sh)
    hip_center = midpoint(l_hip, r_hip)
    return forward_lean_angle(hip_center, shoulder_center)


def knee_angle_deg(landmarks):
    """무릎 굴곡각 (엉덩이-무릎-발목). 더 잘 보이는 쪽 다리를 사용한다."""
    leg = _pick_visible_side(landmarks, lm.LEFT_LEG, lm.RIGHT_LEG)
    if leg is None:
        return None
    hip_idx, knee_idx, ankle_idx = leg
    hip, knee, ankle = landmarks[hip_idx], landmarks[knee_idx], landmarks[ankle_idx]
    return joint_angle((hip[0], hip[1]), (knee[0], knee[1]), (ankle[0], ankle[1]))


def arm_swing_angle_deg(landmarks):
    """팔치기 각도 (어깨-팔꿈치-손목). 더 잘 보이는 쪽 팔을 사용한다."""
    arm = _pick_visible_side(landmarks, lm.LEFT_ARM, lm.RIGHT_ARM)
    if arm is None:
        return None
    sh_idx, el_idx, wr_idx = arm
    shoulder, elbow, wrist = landmarks[sh_idx], landmarks[el_idx], landmarks[wr_idx]
    return joint_angle(
        (shoulder[0], shoulder[1]), (elbow[0], elbow[1]), (wrist[0], wrist[1])
    )


def body_height_px(landmarks):
    """코(머리)~발목 중점 사이 거리로 화면상 신장(px)을 근사한다.

    카메라-피사체 거리가 프레임 내내 크게 변하지 않는다고 가정한 근사치이며,
    보폭 비율처럼 '신장 대비' 값을 계산할 때 스케일 기준으로만 쓴다.
    """
    nose = _visible(landmarks, lm.NOSE)
    l_ankle, r_ankle = _visible(landmarks, lm.LEFT_ANKLE), _visible(landmarks, lm.RIGHT_ANKLE)
    if not (nose and (l_ankle or r_ankle)):
        return None

    ankles = [p for p in (l_ankle, r_ankle) if p]
    ankle_center = midpoint(ankles[0], ankles[-1]) if len(ankles) == 2 else ankles[0]
    return distance(nose, ankle_center)


def stride_ratio(landmarks, height_px):
    """양 발목 사이 수평 거리 / 신장(px)."""
    l_ankle, r_ankle = _visible(landmarks, lm.LEFT_ANKLE), _visible(landmarks, lm.RIGHT_ANKLE)
    if not (l_ankle and r_ankle and height_px):
        return None
    stride_px = abs(l_ankle[0] - r_ankle[0])
    return stride_px / height_px


def landing_offset_ratio(landmarks, landing_ankle_index, height_px):
    """착지 순간 발목-엉덩이중심 수평거리 / 신장(px). 오버스트라이딩 판별용."""
    ankle = _visible(landmarks, landing_ankle_index)
    l_hip, r_hip = _visible(landmarks, lm.LEFT_HIP), _visible(landmarks, lm.RIGHT_HIP)
    if not (ankle and l_hip and r_hip and height_px):
        return None
    hip_center = midpoint(l_hip, r_hip)
    return (ankle[0] - hip_center[0]) / height_px
