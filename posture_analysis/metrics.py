"""프레임 하나에서 자세 지표를 계산하는 함수 모음 + 달리기 기록 지표.

`landmarks` 인자는 {랜드마크 번호: (x_px, y_px, visibility)} 형태의 딕셔너리.
각 함수는 계산이 불가능하면(관절이 안 보이면) None을 반환한다.

주의: ankle_separation_ratio는 '한 프레임에서 양 발목 사이의 수평 거리'를
화면상 신장으로 나눈 값이며, 실제 보폭(stride length)이 아니다. 실제 보폭은
연속 착지 사건의 위치 차이와 픽셀-미터 보정이 필요하다 (아래 TODO 참고).
"""

from typing import Dict, Optional, Sequence, Tuple

from posture_analysis import constants as lm
from posture_analysis.geometry import (
    distance,
    forward_lean_angle,
    joint_angle,
    midpoint,
)

# {랜드마크 번호: (x_px, y_px, visibility)}
Landmarks = Dict[int, Tuple[float, float, float]]


def _visible(landmarks: Landmarks, index: int) -> Optional[Tuple[float, float]]:
    """visibility가 기준 이상인 랜드마크의 (x, y)를 반환한다. 아니면 None."""
    point = landmarks.get(index)
    if point is None:
        return None
    x, y, visibility = point
    if visibility < lm.MIN_VISIBILITY:
        return None
    return (x, y)


def _side_fully_visible(landmarks: Landmarks, indices: Sequence[int]) -> bool:
    """해당 측면의 모든 관절이 MIN_VISIBILITY를 넘는지 확인한다."""
    return all(_visible(landmarks, i) is not None for i in indices)


def _avg_visibility(landmarks: Landmarks, indices: Sequence[int]) -> float:
    points = [landmarks.get(i) for i in indices]
    if any(p is None for p in points):
        return -1.0
    return sum(p[2] for p in points) / len(points)


def _pick_side(
    landmarks: Landmarks,
    left_indices: Sequence[int],
    right_indices: Sequence[int],
    preferred_side: Optional[str] = None,
) -> Optional[Sequence[int]]:
    """좌/우 측면 중 사용할 쪽의 관절 묶음을 고른다.

    - 세 관절 모두 MIN_VISIBILITY를 넘는 측면만 후보가 된다.
    - preferred_side("left"/"right")가 후보에 있으면 우선 사용한다.
      (프레임마다 좌우가 계속 바뀌는 것을 막기 위한 장치)
    - 양쪽 모두 기준 미달이면 None을 반환한다.
    """
    left_ok = _side_fully_visible(landmarks, left_indices)
    right_ok = _side_fully_visible(landmarks, right_indices)

    if not left_ok and not right_ok:
        return None
    if left_ok and not right_ok:
        return left_indices
    if right_ok and not left_ok:
        return right_indices

    # 양쪽 모두 사용 가능: 선호 측면 -> 평균 visibility 순으로 결정
    if preferred_side == "left":
        return left_indices
    if preferred_side == "right":
        return right_indices
    left_score = _avg_visibility(landmarks, left_indices)
    right_score = _avg_visibility(landmarks, right_indices)
    return left_indices if left_score >= right_score else right_indices


def trunk_lean_deg(landmarks: Landmarks, run_direction: int) -> Optional[float]:
    """부호 있는 상체 기울기(도). 진행 방향 기준 전방이 양수, 후방이 음수."""
    l_sh, r_sh = _visible(landmarks, lm.LEFT_SHOULDER), _visible(landmarks, lm.RIGHT_SHOULDER)
    l_hip, r_hip = _visible(landmarks, lm.LEFT_HIP), _visible(landmarks, lm.RIGHT_HIP)
    if not (l_sh and r_sh and l_hip and r_hip):
        return None

    shoulder_center = midpoint(l_sh, r_sh)
    hip_center = midpoint(l_hip, r_hip)
    return forward_lean_angle(hip_center, shoulder_center, run_direction)


def knee_angle_deg(
    landmarks: Landmarks, preferred_side: Optional[str] = None
) -> Optional[float]:
    """무릎 굴곡각 (엉덩이-무릎-발목). 세 관절이 모두 보이는 쪽 다리를 쓴다."""
    leg = _pick_side(landmarks, lm.LEFT_LEG, lm.RIGHT_LEG, preferred_side)
    if leg is None:
        return None
    hip, knee, ankle = (_visible(landmarks, i) for i in leg)
    return joint_angle(hip, knee, ankle)


def knee_angle_for_ankle(
    landmarks: Landmarks, ankle_index: int
) -> Optional[float]:
    """특정 발목(착지 다리)과 같은 쪽 다리의 무릎 굴곡각.

    착지 프레임에서 '착지한 다리'의 무릎 각도를 판정할 때 사용한다.
    """
    leg = lm.ANKLE_TO_LEG.get(ankle_index)
    if leg is None or not _side_fully_visible(landmarks, leg):
        return None
    hip, knee, ankle = (_visible(landmarks, i) for i in leg)
    return joint_angle(hip, knee, ankle)


def arm_swing_angle_deg(
    landmarks: Landmarks, preferred_side: Optional[str] = None
) -> Optional[float]:
    """팔치기 각도 (어깨-팔꿈치-손목). 세 관절이 모두 보이는 쪽 팔을 쓴다."""
    arm = _pick_side(landmarks, lm.LEFT_ARM, lm.RIGHT_ARM, preferred_side)
    if arm is None:
        return None
    shoulder, elbow, wrist = (_visible(landmarks, i) for i in arm)
    return joint_angle(shoulder, elbow, wrist)


def body_height_px(landmarks: Landmarks) -> Optional[float]:
    """코(머리)~발목 중점 사이 거리로 화면상 신체 길이(px)를 근사한다.

    픽셀-미터 변환이 아니라, '신체 크기 대비 비율'을 만들 때의 스케일
    기준으로만 사용한다. 카메라-피사체 거리가 프레임 내내 크게 변하지
    않는다고 가정한 근사치다.
    """
    nose = _visible(landmarks, lm.NOSE)
    l_ankle, r_ankle = _visible(landmarks, lm.LEFT_ANKLE), _visible(landmarks, lm.RIGHT_ANKLE)
    if not (nose and (l_ankle or r_ankle)):
        return None

    ankles = [p for p in (l_ankle, r_ankle) if p]
    ankle_center = midpoint(ankles[0], ankles[-1]) if len(ankles) == 2 else ankles[0]
    return distance(nose, ankle_center)


def ankle_separation_ratio(
    landmarks: Landmarks, reference_length_px: Optional[float]
) -> Optional[float]:
    """한 프레임에서 양 발목 사이 수평 거리 / 화면상 신체 길이(px).

    실제 보폭(stride length)이 아니라 순간적인 발목 벌어짐 정도를 나타내는
    간접 지표다.

    TODO(실제 보폭): 같은 발의 연속 착지 x좌표 차이와 픽셀-미터 보정을
    이용해 stride_length_m(landing_events, meters_per_px)를 구현할 수 있다.
    """
    l_ankle, r_ankle = _visible(landmarks, lm.LEFT_ANKLE), _visible(landmarks, lm.RIGHT_ANKLE)
    if not (l_ankle and r_ankle) or not reference_length_px:
        return None
    return abs(l_ankle[0] - r_ankle[0]) / reference_length_px


def landing_offset_ratio(
    landmarks: Landmarks,
    landing_ankle_index: int,
    reference_length_px: Optional[float],
    run_direction: int,
) -> Optional[float]:
    """착지 순간 (발목 - 엉덩이중심) 수평거리 / 화면상 신체 길이(px).

    진행 방향 기준으로 발목이 엉덩이보다 앞이면 양수(오버스트라이딩 방향),
    뒤면 음수가 된다.
    """
    if run_direction not in lm.VALID_RUN_DIRECTIONS:
        raise ValueError(
            f"run_direction은 +1(오른쪽) 또는 -1(왼쪽)이어야 합니다: {run_direction}"
        )
    ankle = _visible(landmarks, landing_ankle_index)
    l_hip, r_hip = _visible(landmarks, lm.LEFT_HIP), _visible(landmarks, lm.RIGHT_HIP)
    if not (ankle and l_hip and r_hip) or not reference_length_px:
        return None
    hip_center = midpoint(l_hip, r_hip)
    return (ankle[0] - hip_center[0]) * run_direction / reference_length_px


# ---------------------------------------------------------------------------
# 달리기 기록 지표 (영상과 무관하게 기록/신체 정보만으로 계산)
# ---------------------------------------------------------------------------

def average_speed_mps(distance_m: float, record_time_sec: float) -> float:
    """구간 거리와 기록으로 평균 속도(m/s)를 계산한다."""
    if distance_m <= 0:
        raise ValueError(f"거리는 0보다 커야 합니다: {distance_m}")
    if record_time_sec <= 0:
        raise ValueError(f"기록 시간은 0보다 커야 합니다: {record_time_sec}")
    return distance_m / record_time_sec


def froude_number(
    speed_mps: float,
    leg_length_m: float,
    gravity_mps2: float = 9.81,
) -> float:
    """프루드 수 Fr = v^2 / (g * L).

    달리기 속도(v)와 특성 길이(L, 기본적으로 다리 길이)의 영향을 무차원화한
    지표로, 신장이 다른 사람 간의 속도를 신체 크기를 고려해 비교할 때 쓴다.
    이 값 하나로 자세의 좋고 나쁨을 판정하는 지표가 아니다.
    """
    if speed_mps < 0:
        raise ValueError(f"속도는 0 이상이어야 합니다: {speed_mps}")
    if leg_length_m <= 0:
        raise ValueError(f"다리 길이는 0보다 커야 합니다: {leg_length_m}")
    if gravity_mps2 <= 0:
        raise ValueError(f"중력가속도는 0보다 커야 합니다: {gravity_mps2}")
    return speed_mps**2 / (gravity_mps2 * leg_length_m)


def build_running_metrics(
    record_time_sec: Optional[float],
    leg_length_m: Optional[float] = None,
    height_cm: Optional[float] = None,
    distance_m: float = lm.SPRINT_DISTANCE_M,
) -> Optional[dict]:
    """50m 기록과 다리 길이 정보로 평균 속도·프루드 수 요약을 만든다.

    - 프루드 수는 '50m 전체 평균속도' 기준이다. 구간별(가속/최대 속도)
      프루드 수는 구간별 거리와 통과 시간이 있어야 계산할 수 있으므로
      여기서는 만들지 않는다.
    - 다리 길이를 직접 입력하지 않으면 신장 x LEG_LENGTH_HEIGHT_RATIO로
      근사하며, leg_length_source에 근사값임을 표시한다.

    record_time_sec이 없으면 None을 반환한다.
    """
    if record_time_sec is None:
        return None

    speed = average_speed_mps(distance_m, record_time_sec)

    if leg_length_m is not None:
        if leg_length_m <= 0:
            raise ValueError(f"다리 길이는 0보다 커야 합니다: {leg_length_m}")
        leg_length_source = "user_input"
    elif height_cm is not None:
        if height_cm <= 0:
            raise ValueError(f"신장은 0보다 커야 합니다: {height_cm}")
        leg_length_m = height_cm / 100 * lm.LEG_LENGTH_HEIGHT_RATIO
        leg_length_source = "estimated_from_height"
    else:
        leg_length_source = None

    froude = froude_number(speed, leg_length_m) if leg_length_m else None

    return {
        "distance_m": distance_m,
        "record_time_sec": record_time_sec,
        "average_speed_mps": speed,
        "leg_length_m": leg_length_m,
        "leg_length_source": leg_length_source,
        "froude_number": froude,
        "note": "프루드 수는 50m 전체 평균속도 기준이며, 단독으로 자세 우열을 판정하지 않는다.",
    }
