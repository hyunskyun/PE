"""전체 파이프라인을 연결해서 최종 리포트를 만드는 부분."""

from dataclasses import dataclass, field

from sprint_core import config, feedback, judge, metrics, phases
from sprint_core.landmarks import LEFT_HIP, RIGHT_HIP


@dataclass
class Report:
    per_frame: list[dict] = field(default_factory=list)
    footstrike_events: list[dict] = field(default_factory=list)
    phase_averages: dict = field(default_factory=dict)
    verdicts: dict = field(default_factory=dict)
    error_counts: dict = field(default_factory=dict)
    priority: list = field(default_factory=list)
    score: float = 0.0
    text: str = ""


def _hip_mid_x(frame: dict) -> float:
    return (frame[LEFT_HIP][0] + frame[RIGHT_HIP][0]) / 2


def _estimate_height_px(valid_frames: list[dict]) -> float:
    """초반 프레임 중 가장 곧게 선(추정 신장이 가장 큰) 프레임 값을 신장(px)으로 쓴다.

    앞으로 숙인 자세에서는 코~발목 거리가 실제보다 짧게 나오기 때문이다.
    """
    early_count = max(1, int(len(valid_frames) * 0.2))
    early_frames = valid_frames[:early_count]
    return max(metrics.estimate_height_px(frame) for frame in early_frames)


def analyze_landmark_sequence(frames: list[dict], height_cm: float, fps: float,
                               phase_method: str = "fraction") -> Report:
    valid_frames = [f for f in frames if metrics.frame_is_valid(f)]
    if not valid_frames:
        return Report(text="분석 가능한 프레임이 없습니다. 영상을 다시 확인해주세요.")

    height_px = _estimate_height_px(valid_frames)

    hip_x_series = [_hip_mid_x(f) for f in valid_frames]
    ankle_y_series = [metrics.ankle_y(f) for f in valid_frames]

    frame_phases = phases.classify_phases(
        len(valid_frames), hip_x=hip_x_series, fps=fps, method=phase_method,
    )
    footstrike_indices = set(metrics.detect_footstrike_frames(ankle_y_series))

    per_frame = []
    for i, frame in enumerate(valid_frames):
        row = {
            "frame_index": i,
            "phase": frame_phases[i],
            "trunk_lean_deg": metrics.trunk_lean_angle(frame),
            "knee_flex_deg": metrics.knee_flexion_angle(frame),
            "arm_swing_deg": metrics.arm_swing_angle(frame),
            "stride_ratio": metrics.stride_length_ratio(frame, height_px),
            "footstrike_offset_ratio": metrics.footstrike_offset_ratio(frame, height_px),
        }
        per_frame.append(row)

    footstrike_events = [
        {"frame_index": row["frame_index"], "phase": row["phase"],
         "footstrike_offset_ratio": row["footstrike_offset_ratio"]}
        for row in per_frame if row["frame_index"] in footstrike_indices
    ]

    phase_averages = _average_by_phase(per_frame, footstrike_events)
    verdicts = judge.judge_phase_averages(phase_averages)
    error_counts = feedback.count_errors(verdicts)
    priority = feedback.priority_list(error_counts)
    score = feedback.overall_score(verdicts)
    text = feedback.build_text_report(phase_averages, verdicts)

    return Report(
        per_frame=per_frame,
        footstrike_events=footstrike_events,
        phase_averages=phase_averages,
        verdicts=verdicts,
        error_counts=error_counts,
        priority=priority,
        score=score,
        text=text,
    )


def _average_by_phase(per_frame: list[dict], footstrike_events: list[dict]) -> dict:
    continuous_keys = ["trunk_lean_deg", "knee_flex_deg", "arm_swing_deg", "stride_ratio"]
    result = {}

    for phase in (config.PHASE_ACCEL, config.PHASE_MAXV):
        rows = [row for row in per_frame if row["phase"] == phase]
        if not rows:
            continue

        phase_metrics = {
            key: sum(row[key] for row in rows) / len(rows) for key in continuous_keys
        }

        strikes = [e["footstrike_offset_ratio"] for e in footstrike_events if e["phase"] == phase]
        # 착지 순간이 감지되지 않은 구간은 전체 프레임 평균으로 대신한다.
        values = strikes if strikes else [row["footstrike_offset_ratio"] for row in rows]
        phase_metrics["footstrike_offset_ratio"] = sum(values) / len(values)

        result[phase] = phase_metrics

    return result


def analyze_video(video_path: str, height_cm: float, phase_method: str = "fraction",
                   sample_stride: int = 1) -> Report:
    from sprint_core.landmarks import extract_video_landmarks

    frames, fps = extract_video_landmarks(video_path, sample_stride=sample_stride)
    return analyze_landmark_sequence(frames, height_cm, fps, phase_method=phase_method)
