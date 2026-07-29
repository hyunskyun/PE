"""OpenCV + MediaPipe로 영상을 읽어 좌표를 뽑아내는 실행 레이어.

계산 로직 자체는 metrics.py / report.py에 있고, 여기서는 "영상 -> 좌표"만 담당한다.
다른 실행 환경(웹, 안드로이드 등)으로 옮길 때는 이 파일만 그 플랫폼의 카메라/영상
입력 방식으로 교체하면 나머지 모듈은 그대로 재사용할 수 있다.
"""
import statistics

import cv2
import mediapipe as mp

from . import landmarks as lm
from .metrics import calibrate_px_per_cm, compute_frame_metrics
from .report import build_report

CALIBRATION_FRAMES = 5  # 초반 몇 프레임의 px/cm 비율을 median으로 합쳐 촬영 흔들림 오차를 줄인다


def _extract_points(pose_landmarks, frame_width, frame_height):
    if pose_landmarks is None:
        return None
    raw = pose_landmarks.landmark
    points = {}
    for idx in lm.REQUIRED:
        p = raw[idx]
        if p.visibility is not None and p.visibility < 0.5:
            return None  # 필요한 관절 중 하나라도 신뢰도가 낮으면 해당 프레임은 버린다
        points[idx] = (p.x * frame_width, p.y * frame_height)
    return points


def analyze_video(video_path, height_cm, accel_duration_sec=2.0, sample_every=1):
    """영상 파일 하나를 분석해 report.Report를 반환한다.

    sample_every=1이면 모든 프레임을, 2면 한 프레임씩 건너뛰며 분석해 속도를 높인다.
    """
    mp_pose = mp.solutions.pose
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"영상을 열 수 없습니다: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    raw_frames = []  # (frame_idx, time_sec, points)
    dropped_frames = 0

    with mp_pose.Pose(model_complexity=1, min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        frame_idx = -1
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_idx += 1
            if frame_idx % sample_every != 0:
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = pose.process(rgb)
            points = _extract_points(result.pose_landmarks, frame_width, frame_height)
            if points is None:
                dropped_frames += 1
                continue

            raw_frames.append((frame_idx, frame_idx / fps, points))

    cap.release()

    if not raw_frames:
        raise RuntimeError("자세를 인식한 프레임이 하나도 없습니다. 촬영 각도/조명을 확인하세요.")

    # px-cm 환산 비율은 전체 프레임에 동일하게 적용해야 하므로, 지표 계산 전에 먼저 확정한다.
    calibration_samples = [
        calibrate_px_per_cm(points, height_cm) for _, _, points in raw_frames[:CALIBRATION_FRAMES]
    ]
    calibration_samples = [v for v in calibration_samples if v]
    px_per_cm = statistics.median(calibration_samples) if calibration_samples else None

    frame_metrics_list = [
        compute_frame_metrics(points, frame_idx, time_sec, px_per_cm)
        for frame_idx, time_sec, points in raw_frames
    ]

    effective_fps = fps / sample_every
    return build_report(frame_metrics_list, height_cm, accel_duration_sec, effective_fps, dropped_frames)
