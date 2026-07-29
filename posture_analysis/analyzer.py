"""전체 분석 파이프라인을 하나로 묶는 오케스트레이터.

처리 순서 (보고서 6번 항목과 동일):
  영상 입력 -> 프레임 단위 분할 -> 랜드마크 추출 -> 좌표 기반 각도/거리
  계산 -> 구간 분류 -> 조건문 비교 -> 오류 판정 -> 교정 피드백 출력
"""

from posture_analysis import constants as lm
from posture_analysis import metrics as m
from posture_analysis.judge import judge_frame
from posture_analysis.landing import build_ankle_y_tracks, find_landing_frames
from posture_analysis.phase import classify_phase
from posture_analysis.pose_extractor import extract_video_landmarks


def analyze_video(video_path, user_height_cm, acceleration_end_sec=None):
    """영상 하나를 분석해 프레임별 결과 리스트를 반환한다.

    user_height_cm은 현재 버전에서는 참고 정보로만 저장한다. 실제 거리
    환산은 화면상 신장(px) 대비 비율로 처리하므로, 카메라 왜곡이 적은
    영상일수록 신뢰도가 높아진다.
    """
    fps, frame_landmarks_list = extract_video_landmarks(video_path)
    total_frames = len(frame_landmarks_list)
    total_duration_sec = total_frames / fps if fps else 0

    ankle_tracks = build_ankle_y_tracks(frame_landmarks_list)
    landing_frames_by_ankle = {
        ankle_index: set(find_landing_frames(track, ankle_index))
        for ankle_index, track in ankle_tracks.items()
    }

    frame_results = []

    for frame_idx, landmarks in enumerate(frame_landmarks_list):
        timestamp_sec = frame_idx / fps if fps else 0
        phase = classify_phase(timestamp_sec, total_duration_sec, acceleration_end_sec)

        if landmarks is None:
            frame_results.append(
                {"frame_idx": frame_idx, "timestamp_sec": timestamp_sec, "phase": phase,
                 "metrics": {}, "errors": []}
            )
            continue

        height_px = m.body_height_px(landmarks)

        frame_metrics = {
            "trunk_lean_deg": m.trunk_lean_deg(landmarks),
            "knee_angle_deg": m.knee_angle_deg(landmarks),
            "arm_swing_deg": m.arm_swing_angle_deg(landmarks),
            "stride_ratio": m.stride_ratio(landmarks, height_px),
        }

        for ankle_index, landing_set in landing_frames_by_ankle.items():
            if frame_idx in landing_set:
                frame_metrics["landing_offset_ratio"] = m.landing_offset_ratio(
                    landmarks, ankle_index, height_px
                )
                break  # 한 프레임에 착지 다리는 하나만 반영

        clean_metrics = {k: v for k, v in frame_metrics.items() if v is not None}
        judged = judge_frame(clean_metrics, phase)

        frame_results.append(
            {
                "frame_idx": frame_idx,
                "timestamp_sec": timestamp_sec,
                "phase": phase,
                "metrics": clean_metrics,
                "errors": judged["errors"],
            }
        )

    return {
        "video_path": video_path,
        "user_height_cm": user_height_cm,
        "fps": fps,
        "total_frames": total_frames,
        "total_duration_sec": total_duration_sec,
        "frame_results": frame_results,
    }
