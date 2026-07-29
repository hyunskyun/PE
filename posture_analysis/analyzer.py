"""전체 분석 파이프라인을 하나로 묶는 오케스트레이터.

처리 순서:
  영상 입력 -> 프레임 단위 분할 -> 랜드마크 추출 -> 좌표 기반 각도/거리
  계산 -> 구간 분류 -> 착지 검출 -> 조건문 비교 -> 오류 판정

MediaPipe 의존부(pose_extractor)는 analyze_video() 안에서만 지연 임포트
하므로, analyze_frames()는 합성 랜드마크만으로 테스트할 수 있다.

무릎 각도는 매 프레임 원자료(raw)로 기록하되, 오류 판정은 착지 후보
프레임에서만 수행한다. 회복기(swing)에는 무릎이 크게 굽는 것이 정상이라
전 프레임 판정은 오탐을 만들기 때문이다.
"""

from typing import Callable, List, Optional, Sequence, Tuple

from posture_analysis import constants as lm
from posture_analysis import metrics as m
from posture_analysis.judge import judge_frame
from posture_analysis.landing import build_ankle_y_tracks, find_landing_frames
from posture_analysis.phase import classify_phase, resolve_phase_boundaries

DIRECTION_SOURCE_USER = "user_input"
DIRECTION_SOURCE_ESTIMATED = "estimated"

FrameLandmarksList = Sequence[Optional[dict]]


def estimate_run_direction(frame_landmarks_list: FrameLandmarksList) -> Optional[int]:
    """엉덩이 중심 x좌표의 전체 이동 방향으로 진행 방향을 추정한다.

    오른쪽 이동이면 +1, 왼쪽 이동이면 -1. 이동량이 너무 작거나 유효한
    프레임이 부족해 판단할 수 없으면 None을 반환한다 (이 경우 사용자가
    직접 방향을 입력해야 한다).
    """
    hip_x_values = []
    for landmarks in frame_landmarks_list:
        if not landmarks:
            continue
        l_hip = landmarks.get(lm.LEFT_HIP)
        r_hip = landmarks.get(lm.RIGHT_HIP)
        if not (l_hip and r_hip):
            continue
        if l_hip[2] < lm.MIN_VISIBILITY or r_hip[2] < lm.MIN_VISIBILITY:
            continue
        hip_x_values.append((l_hip[0] + r_hip[0]) / 2)

    if len(hip_x_values) < 2:
        return None

    travel = hip_x_values[-1] - hip_x_values[0]
    if abs(travel) < lm.MIN_DIRECTION_TRAVEL_PX:
        return None
    return lm.RUN_RIGHT if travel > 0 else lm.RUN_LEFT


def select_primary_side(frame_landmarks_list: FrameLandmarksList) -> Optional[str]:
    """영상 전체의 다리 관절 평균 visibility로 주 분석 측면을 정한다.

    프레임마다 좌우 선택이 계속 바뀌는 것을 줄이기 위해, 분석 시작 전에
    한 번 결정해 모든 프레임에 선호 측면으로 넘긴다. (해당 프레임에서
    선호 측면이 기준 미달이면 metrics 쪽에서 반대편으로 대체된다.)
    """
    sums = {"left": 0.0, "right": 0.0}
    counts = {"left": 0, "right": 0}

    for landmarks in frame_landmarks_list:
        if not landmarks:
            continue
        for side, leg in (("left", lm.LEFT_LEG), ("right", lm.RIGHT_LEG)):
            points = [landmarks.get(i) for i in leg]
            if any(p is None for p in points):
                continue
            sums[side] += sum(p[2] for p in points) / len(points)
            counts[side] += 1

    averages = {
        side: (sums[side] / counts[side]) if counts[side] else -1.0
        for side in sums
    }
    if averages["left"] < 0 and averages["right"] < 0:
        return None
    return "left" if averages["left"] >= averages["right"] else "right"


def analyze_frames(
    fps: float,
    frame_landmarks_list: FrameLandmarksList,
    run_direction: int,
    analysis_start_sec: Optional[float] = None,
    acceleration_end_sec: Optional[float] = None,
    analysis_end_sec: Optional[float] = None,
    run_direction_source: str = DIRECTION_SOURCE_USER,
) -> dict:
    """추출된 랜드마크 시퀀스를 분석해 프레임별 결과와 검출 통계를 만든다.

    MediaPipe 없이 합성 랜드마크로 직접 호출할 수 있는 순수 함수다.
    """
    if run_direction not in lm.VALID_RUN_DIRECTIONS:
        raise ValueError(
            f"run_direction은 +1(오른쪽) 또는 -1(왼쪽)이어야 합니다: {run_direction}"
        )
    if fps <= 0:
        raise ValueError(f"fps는 0보다 커야 합니다: {fps}")
    if not frame_landmarks_list:
        raise ValueError("분석할 프레임이 없습니다")
    if all(landmarks is None for landmarks in frame_landmarks_list):
        raise ValueError(
            "영상에서 랜드마크가 전혀 추출되지 않았습니다. "
            "촬영 각도/조명/전신 프레이밍을 확인하세요."
        )

    total_frames = len(frame_landmarks_list)
    total_duration_sec = total_frames / fps

    start, accel_end, end, boundary_source = resolve_phase_boundaries(
        total_duration_sec, analysis_start_sec, acceleration_end_sec, analysis_end_sec
    )

    primary_side = select_primary_side(frame_landmarks_list)

    ankle_tracks = build_ankle_y_tracks(frame_landmarks_list)
    landing_frames_by_ankle = {
        ankle_index: set(find_landing_frames(track, fps))
        for ankle_index, track in ankle_tracks.items()
    }

    frame_results = []
    frames_in_range = 0
    pose_detected_frames = 0
    valid_measurement_frames = 0

    for frame_idx, landmarks in enumerate(frame_landmarks_list):
        timestamp_sec = frame_idx / fps
        phase = classify_phase(timestamp_sec, start, accel_end, end)
        if phase is None:
            continue  # 분석 범위 밖 프레임은 집계에서 제외

        frames_in_range += 1
        landing_ankle = _landing_ankle_for_frame(frame_idx, landing_frames_by_ankle)
        is_landing_frame = landing_ankle is not None

        base_result = {
            "frame_idx": frame_idx,
            "timestamp_sec": timestamp_sec,
            "phase": phase,
            "is_landing_frame": is_landing_frame,
        }

        if landmarks is None:
            frame_results.append(
                {**base_result, "metrics": {}, "judged_metrics": {}, "errors": []}
            )
            continue

        pose_detected_frames += 1
        raw_metrics, judged_metrics = _compute_frame_metrics(
            landmarks, run_direction, primary_side, landing_ankle
        )

        if judged_metrics:
            valid_measurement_frames += 1

        judged = judge_frame(judged_metrics, phase)
        frame_results.append(
            {
                **base_result,
                "metrics": raw_metrics,
                "judged_metrics": judged_metrics,
                "errors": judged["errors"],
            }
        )

    detection_rate = (
        valid_measurement_frames / frames_in_range if frames_in_range else 0.0
    )

    return {
        "fps": fps,
        "total_frames": total_frames,
        "total_duration_sec": total_duration_sec,
        "run_direction": run_direction,
        "run_direction_source": run_direction_source,
        "primary_side": primary_side,
        "phase_info": {
            "analysis_start_sec": start,
            "acceleration_end_sec": accel_end,
            "analysis_end_sec": end,
            "phase_boundary_source": boundary_source,
        },
        "detection": {
            "total_frames_analyzed": frames_in_range,
            "pose_detected_frames": pose_detected_frames,
            "valid_measurement_frames": valid_measurement_frames,
            "detection_rate": detection_rate,
        },
        "frame_results": frame_results,
    }


def _landing_ankle_for_frame(
    frame_idx: int, landing_frames_by_ankle: dict
) -> Optional[int]:
    """이 프레임이 착지 후보이면 착지한 발목 번호를, 아니면 None을 반환한다."""
    for ankle_index, landing_set in landing_frames_by_ankle.items():
        if frame_idx in landing_set:
            return ankle_index
    return None


def _compute_frame_metrics(
    landmarks: dict,
    run_direction: int,
    primary_side: Optional[str],
    landing_ankle: Optional[int],
) -> Tuple[dict, dict]:
    """프레임 지표를 계산해 (원자료 전체, 판정 대상)으로 나눈다.

    - 원자료(raw): 계산된 모든 지표. 무릎 각도는 착지가 아니어도 기록한다.
    - 판정 대상(judged): 상체 기울기/팔치기/발목 간격은 항상, 무릎 각도와
      착지 오프셋은 착지 후보 프레임에서만 포함한다.
    """
    reference_length_px = m.body_height_px(landmarks)

    raw_metrics = {}
    judged_metrics = {}

    always_judged = {
        "trunk_lean_deg": m.trunk_lean_deg(landmarks, run_direction),
        "arm_swing_deg": m.arm_swing_angle_deg(landmarks, primary_side),
        "ankle_separation_ratio": m.ankle_separation_ratio(
            landmarks, reference_length_px
        ),
    }
    for name, value in always_judged.items():
        if value is not None:
            raw_metrics[name] = value
            judged_metrics[name] = value

    # 무릎 각도: 원자료로는 항상 기록, 판정은 착지 프레임의 착지 다리만
    raw_knee = m.knee_angle_deg(landmarks, primary_side)
    if raw_knee is not None:
        raw_metrics["knee_angle_deg"] = raw_knee

    if landing_ankle is not None:
        landing_knee = m.knee_angle_for_ankle(landmarks, landing_ankle)
        if landing_knee is not None:
            raw_metrics["knee_angle_deg"] = landing_knee
            judged_metrics["knee_angle_deg"] = landing_knee

        landing_offset = m.landing_offset_ratio(
            landmarks, landing_ankle, reference_length_px, run_direction
        )
        if landing_offset is not None:
            raw_metrics["landing_offset_ratio"] = landing_offset
            judged_metrics["landing_offset_ratio"] = landing_offset

    return raw_metrics, judged_metrics


def analyze_video(
    video_path: str,
    run_direction: Optional[int] = None,
    analysis_start_sec: Optional[float] = None,
    acceleration_end_sec: Optional[float] = None,
    analysis_end_sec: Optional[float] = None,
    extractor: Optional[Callable] = None,
) -> dict:
    """영상 하나를 분석한다.

    run_direction이 None이면 엉덩이 이동 방향으로 자동 추정하고, 추정에
    실패하면 사용자가 --direction을 입력하도록 ValueError를 낸다.
    extractor는 테스트에서 MediaPipe 추출기를 대체하기 위한 주입 지점이다.
    """
    if extractor is None:
        from posture_analysis.pose_extractor import extract_video_landmarks
        extractor = extract_video_landmarks

    fps, frame_landmarks_list = extractor(video_path)

    if run_direction is None:
        run_direction = estimate_run_direction(frame_landmarks_list)
        direction_source = DIRECTION_SOURCE_ESTIMATED
        if run_direction is None:
            raise ValueError(
                "진행 방향을 자동 추정하지 못했습니다. "
                "--direction right 또는 --direction left를 직접 입력하세요."
            )
    else:
        direction_source = DIRECTION_SOURCE_USER

    result = analyze_frames(
        fps=fps,
        frame_landmarks_list=frame_landmarks_list,
        run_direction=run_direction,
        analysis_start_sec=analysis_start_sec,
        acceleration_end_sec=acceleration_end_sec,
        analysis_end_sec=analysis_end_sec,
        run_direction_source=direction_source,
    )
    result["video_path"] = video_path
    return result
