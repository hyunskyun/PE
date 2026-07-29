"""랜드마크 좌표 -> 분석 지표(각도, 거리, 비율) 계산."""
from dataclasses import dataclass

from .geometry import Point, angle_at_vertex, distance, lean_angle_from_vertical


@dataclass
class FrameMetrics:
    frame_idx: int
    time_sec: float
    side: str  # 카메라에 더 잘 보이는 쪽("l" 또는 "r")
    torso_lean_deg: float
    knee_angle_deg: float | None
    arm_swing_angle_deg: float | None
    hip_x: float
    ankle_l_x: float
    ankle_l_y: float
    ankle_r_x: float
    ankle_r_y: float
    body_height_px: float | None


def pick_visible_side(points: dict[str, Point]) -> str:
    """측면 촬영에서는 카메라 반대쪽 관절이 가려지기 쉬우므로,
    MediaPipe가 보고하는 visibility 점수가 더 높은 쪽을 기준 측으로 사용한다."""
    left_keys = ["shoulder_l", "elbow_l", "wrist_l", "hip_l", "knee_l", "ankle_l"]
    right_keys = ["shoulder_r", "elbow_r", "wrist_r", "hip_r", "knee_r", "ankle_r"]
    left_score = sum(points[k].visibility for k in left_keys) / len(left_keys)
    right_score = sum(points[k].visibility for k in right_keys) / len(right_keys)
    return "l" if left_score >= right_score else "r"


def compute_frame_metrics(points: dict[str, Point], frame_idx: int, time_sec: float) -> FrameMetrics:
    side = pick_visible_side(points)
    other = "r" if side == "l" else "l"

    shoulder = points[f"shoulder_{side}"]
    hip = points[f"hip_{side}"]
    elbow = points[f"elbow_{side}"]
    wrist = points[f"wrist_{side}"]
    knee = points[f"knee_{side}"]
    ankle = points[f"ankle_{side}"]

    shoulder_center = Point(
        (shoulder.x + points[f"shoulder_{other}"].x) / 2,
        (shoulder.y + points[f"shoulder_{other}"].y) / 2,
    )
    hip_center = Point(
        (hip.x + points[f"hip_{other}"].x) / 2,
        (hip.y + points[f"hip_{other}"].y) / 2,
    )

    ankle_l, ankle_r = points["ankle_l"], points["ankle_r"]
    ankle_mid = Point((ankle_l.x + ankle_r.x) / 2, (ankle_l.y + ankle_r.y) / 2)
    body_height_px = distance(points["nose"], ankle_mid)

    return FrameMetrics(
        frame_idx=frame_idx,
        time_sec=time_sec,
        side=side,
        torso_lean_deg=lean_angle_from_vertical(shoulder_center, hip_center),
        knee_angle_deg=angle_at_vertex(hip, knee, ankle),
        arm_swing_angle_deg=angle_at_vertex(shoulder, elbow, wrist),
        hip_x=hip_center.x,
        ankle_l_x=ankle_l.x,
        ankle_l_y=ankle_l.y,
        ankle_r_x=ankle_r.x,
        ankle_r_y=ankle_r.y,
        body_height_px=body_height_px if body_height_px > 1e-3 else None,
    )
