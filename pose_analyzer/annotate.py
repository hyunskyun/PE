"""(선택 기능) 원본 영상에 스켈레톤과 프레임별 교정 문구를 덧그려 저장하는 모듈.

보고서 결과를 시연하거나 스크린샷을 뜰 때 쓰기 좋다. 분석 자체에는 필요 없다.
"""
from __future__ import annotations

from typing import Dict, List

import cv2

from .landmarks import LANDMARK_INDEX, FrameLandmarks, PoseExtractor
from .report import AnalysisReport

SKELETON_EDGES = [
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"), ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"), ("right_elbow", "right_wrist"),
    ("left_shoulder", "left_hip"), ("right_shoulder", "right_hip"),
    ("left_hip", "right_hip"),
    ("left_hip", "left_knee"), ("left_knee", "left_ankle"),
    ("right_hip", "right_knee"), ("right_knee", "right_ankle"),
]


def _to_px(point):
    return int(round(point[0])), int(round(point[1]))


def _draw_skeleton(frame, lm: FrameLandmarks) -> None:
    for a, b in SKELETON_EDGES:
        pa, pb = lm.get(a), lm.get(b)
        if pa and pb:
            cv2.line(frame, _to_px(pa), _to_px(pb), (0, 255, 0), 2)
    for name in LANDMARK_INDEX:
        p = lm.get(name)
        if p:
            cv2.circle(frame, _to_px(p), 4, (0, 0, 255), -1)


def annotate_video(video_path: str, report: AnalysisReport, out_path: str) -> None:
    """원본 영상에 스켈레톤 + 교정 문구를 덧그려 out_path(mp4)로 저장한다."""
    feedback_by_frame: Dict[int, List[str]] = {
        fr.frame_index: [j.message for j in fr.judgements.values() if j.message] for fr in report.frame_results
    }

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"영상을 열 수 없습니다: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

    extractor = PoseExtractor(fps=fps)
    try:
        frame_index = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            lm = extractor.extract(frame)
            if lm:
                _draw_skeleton(frame, lm)

            for i, line in enumerate(feedback_by_frame.get(frame_index, [])[:3]):
                cv2.putText(frame, line, (10, 30 + i * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            writer.write(frame)
            frame_index += 1
    finally:
        cap.release()
        writer.release()
        extractor.close()
