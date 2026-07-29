"""영상 입력부터 교정 피드백 출력까지 전체 파이프라인을 orchestrate 한다.

영상 입력 -> 프레임 분할 -> 랜드마크 추출 -> 각도/거리 계산
-> 구간 분류 -> 조건문 비교 -> 오류 판정 -> 교정 피드백 출력
"""

import statistics

import cv2

from .config import (
    PHASE_ACCELERATION,
    PHASE_LABEL_KR,
    PHASE_MAX_VELOCITY,
    THRESHOLDS,
)
from .geometry import midpoint
from .judge import classify, feedback_message
from .landing import find_landing_frames
from .metrics import (
    compute_arm_swing_deg,
    compute_knee_flexion_deg,
    compute_overstride_offset_ratio,
    compute_stride_ratio,
    compute_trunk_lean_deg,
    estimate_height_px,
)
from .phase import phase_for_frame, resolve_split_frame_idx
from .pose_extractor import PoseExtractor

PHASES = (PHASE_ACCELERATION, PHASE_MAX_VELOCITY)


def analyze_video(video_path, height_cm=None, split_time_sec=None):
    frames = _extract_frame_landmarks(video_path)
    total_frames = frames[-1]["frame_idx"] + 1 if frames else 0
    if not frames:
        raise RuntimeError("영상에서 사람의 자세를 인식하지 못했습니다. 촬영 각도/조명을 확인해 주세요.")

    fps = frames[0]["fps"]
    travel_direction = _estimate_travel_direction(frames)
    height_px = statistics.median(estimate_height_px(f["landmarks"]) for f in frames)
    split_frame_idx = resolve_split_frame_idx(total_frames, fps, split_time_sec)
    landing_frames = set(
        find_landing_frames({f["frame_idx"]: midpoint(
            f["landmarks"]["LEFT_ANKLE"], f["landmarks"]["RIGHT_ANKLE"])[1] for f in frames})
    )

    for f in frames:
        _compute_frame_metrics(f, travel_direction, height_px, split_frame_idx, landing_frames)

    phase_reports = {phase: _summarize_phase(frames, phase) for phase in PHASES}
    return {
        "fps": fps,
        "total_frames": total_frames,
        "detected_frames": len(frames),
        "height_px": height_px,
        "height_cm": height_cm,
        "phases": phase_reports,
        "priority_feedback": _pick_priority_feedback(phase_reports),
    }


def _extract_frame_landmarks(video_path):
    frames = []
    with PoseExtractor() as extractor:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            timestamp_ms = int(frame_idx * 1000 / fps)
            landmarks = extractor.extract(frame, timestamp_ms)
            if landmarks is not None:
                frames.append({"frame_idx": frame_idx, "landmarks": landmarks, "fps": fps})
            frame_idx += 1
        cap.release()
    return frames


def _estimate_travel_direction(frames):
    """엉덩이 중심 x좌표의 시작-끝 변화로 달리는 방향(+1/-1)을 추정한다."""
    first_hip_x = midpoint(frames[0]["landmarks"]["LEFT_HIP"], frames[0]["landmarks"]["RIGHT_HIP"])[0]
    last_hip_x = midpoint(frames[-1]["landmarks"]["LEFT_HIP"], frames[-1]["landmarks"]["RIGHT_HIP"])[0]
    return 1 if last_hip_x >= first_hip_x else -1


def _compute_frame_metrics(f, travel_direction, height_px, split_frame_idx, landing_frames):
    landmarks = f["landmarks"]
    f["phase"] = phase_for_frame(f["frame_idx"], split_frame_idx)
    f["time_sec"] = f["frame_idx"] / f["fps"]
    f["trunk_lean_deg"] = compute_trunk_lean_deg(landmarks, travel_direction)
    f["knee_flexion_deg"] = compute_knee_flexion_deg(landmarks)
    f["stride_ratio"] = compute_stride_ratio(landmarks, height_px)
    f["arm_swing_deg"] = compute_arm_swing_deg(landmarks)

    if f["frame_idx"] in landing_frames:
        left_y = landmarks["LEFT_ANKLE"][1]
        right_y = landmarks["RIGHT_ANKLE"][1]
        landing_ankle = "LEFT_ANKLE" if left_y > right_y else "RIGHT_ANKLE"
        f["overstride_offset_ratio"] = compute_overstride_offset_ratio(landmarks, landing_ankle, height_px)


def _summarize_phase(frames, phase):
    phase_frames = [f for f in frames if f["phase"] == phase]
    if not phase_frames:
        return None

    metric_names = ["trunk_lean_deg", "stride_ratio", "knee_flexion_deg", "overstride_offset_ratio", "arm_swing_deg"]
    metrics = {}
    error_ratios = []
    for name in metric_names:
        values = [f[name] for f in phase_frames if name in f]
        if not values:
            continue
        metrics[name] = _summarize_metric(name, values, phase)
        if metrics[name]["error_frame_ratio"] is not None:
            error_ratios.append(metrics[name]["error_frame_ratio"])

    score = round(100 - 100 * (statistics.mean(error_ratios) if error_ratios else 0))
    return {
        "label": PHASE_LABEL_KR[phase],
        "frame_count": len(phase_frames),
        "metrics": metrics,
        "score": max(0, min(100, score)),
    }


def _summarize_metric(name, values, phase):
    mean_value = statistics.mean(values)
    has_threshold = name in THRESHOLDS[phase]

    result = {
        "mean": mean_value,
        "sample_count": len(values),
        "range": THRESHOLDS[phase][name] if has_threshold else None,
        "verdict": None,
        "feedback": None,
        "error_frame_ratio": None,
    }
    if not has_threshold:
        return result

    status = classify(name, mean_value, phase)
    result["verdict"] = "적정" if status == "ok" else "오류 의심"
    result["feedback"] = feedback_message(name, phase, mean_value)
    result["error_frame_ratio"] = sum(1 for v in values if classify(name, v, phase) != "ok") / len(values)
    return result


def _pick_priority_feedback(phase_reports, top_n=3):
    candidates = []
    for phase, report in phase_reports.items():
        if report is None:
            continue
        for metric_name, metric in report["metrics"].items():
            if metric["feedback"] is not None:
                candidates.append((metric["error_frame_ratio"] or 0, metric["feedback"]))

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [text for _, text in candidates[:top_n]]
