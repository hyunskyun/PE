"""영상 입력부터 최종 리포트까지 전체 파이프라인을 연결하는 메인 클래스.

처리 순서(탐구 보고서 "6. 프로그램 처리 과정"과 동일):
영상 입력 -> 프레임 분할 -> 랜드마크 추출 -> 각도/거리 계산
-> 구간 분류 -> 조건문 비교 -> 오류 판정 -> (report 모듈에서) 교정 피드백 집계
"""
from __future__ import annotations

from typing import Dict, List, Optional

import cv2

from .landing import find_landing_frames
from .landmarks import FrameLandmarks, PoseExtractor
from .metrics import (
    FrameMetrics,
    compute_ankle_hip_gap_ratio,
    compute_arm_swing_angle,
    compute_knee_angle,
    compute_stride_ratio,
    compute_trunk_lean,
    estimate_height_px,
)
from .phase import DEFAULT_ACCELERATION_END_SEC, classify_phase
from .report import AnalysisReport, FrameResult, MetricJudgement, build_report
from .thresholds import judge


class VideoPostureAnalyzer:
    """50m 달리기 측면 영상 한 개를 분석해 AnalysisReport를 만드는 클래스."""

    def __init__(self, acceleration_end_sec: float = DEFAULT_ACCELERATION_END_SEC, frame_stride: int = 1):
        self.acceleration_end_sec = acceleration_end_sec
        self.frame_stride = frame_stride  # N프레임마다 한 번씩만 분석(성능 조절용)

    def analyze(self, video_path: str) -> AnalysisReport:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"영상을 열 수 없습니다: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        extractor = PoseExtractor(fps=fps)

        landmarks_by_frame: List[Optional[FrameLandmarks]] = []
        ankle_y_series: Dict[str, List[Optional[float]]] = {"left": [], "right": []}

        try:
            frame_index = 0
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                lm = None
                if frame_index % self.frame_stride == 0:
                    lm = extractor.extract(frame)

                landmarks_by_frame.append(lm)
                for side in ("left", "right"):
                    ankle = lm.get(f"{side}_ankle") if lm else None
                    ankle_y_series[side].append(ankle[1] if ankle else None)
                frame_index += 1
        finally:
            cap.release()
            extractor.close()

        landing_frames = find_landing_frames(ankle_y_series)
        frame_results = self._build_frame_results(landmarks_by_frame, landing_frames, fps)
        return build_report(frame_results)

    def _build_frame_results(
        self,
        landmarks_by_frame: List[Optional[FrameLandmarks]],
        landing_frames: Dict[int, str],
        fps: float,
    ) -> List[FrameResult]:
        frame_results: List[FrameResult] = []

        for idx, lm in enumerate(landmarks_by_frame):
            if lm is None:
                continue

            time_sec = idx / fps
            phase = classify_phase(time_sec, self.acceleration_end_sec)
            height_px = estimate_height_px(lm)

            metrics = FrameMetrics(
                frame_index=idx,
                time_sec=time_sec,
                trunk_lean_deg=compute_trunk_lean(lm),
                knee_angle_deg=self._trailing_knee_angle(lm),
                arm_swing_deg=self._leading_arm_angle(lm),
                stride_ratio=compute_stride_ratio(lm, height_px),
            )

            judgements: Dict[str, MetricJudgement] = {}
            for metric_name in ("trunk_lean_deg", "knee_angle_deg", "arm_swing_deg", "stride_ratio"):
                value = getattr(metrics, metric_name)
                if value is None:
                    continue
                status, message = judge(metric_name, value, phase)
                judgements[metric_name] = MetricJudgement(value=value, status=status, message=message)

            if idx in landing_frames:
                side = landing_frames[idx]
                gap_ratio = compute_ankle_hip_gap_ratio(lm, height_px, side)
                if gap_ratio is not None:
                    metrics.ankle_hip_gap_ratio = gap_ratio
                    status, message = judge("ankle_hip_gap_ratio", gap_ratio, phase)
                    judgements["ankle_hip_gap_ratio"] = MetricJudgement(value=gap_ratio, status=status, message=message)

            frame_results.append(
                FrameResult(frame_index=idx, time_sec=time_sec, phase=phase, metrics=metrics, judgements=judgements)
            )

        return frame_results

    @staticmethod
    def _trailing_knee_angle(lm: FrameLandmarks) -> Optional[float]:
        """양쪽 무릎 각도 중 더 많이 굽혀진(작은) 쪽을 프레임 대표값으로 사용."""
        candidates = [v for v in (compute_knee_angle(lm, "left"), compute_knee_angle(lm, "right")) if v is not None]
        return min(candidates) if candidates else None

    @staticmethod
    def _leading_arm_angle(lm: FrameLandmarks) -> Optional[float]:
        """양쪽 팔치기 각도 중 더 크게 벌어진 쪽을 프레임 대표값으로 사용."""
        candidates = [v for v in (compute_arm_swing_angle(lm, "left"), compute_arm_swing_angle(lm, "right")) if v is not None]
        return max(candidates) if candidates else None
