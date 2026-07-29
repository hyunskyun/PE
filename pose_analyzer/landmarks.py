"""MediaPipe Pose(Tasks API)를 감싸서, 탐구 보고서에서 정의한 12개 핵심 랜드마크만 뽑아주는 모듈.

이 파일은 OpenCV/MediaPipe(PoseExtractor)에 의존하는 I/O 계층이다. 랜드마크
자료형(FrameLandmarks)과 인덱스 표는 순수 로직 쪽에서도 쓸 수 있도록
landmark_types.py에 따로 정의되어 있다.
"""
from __future__ import annotations

from typing import Dict, Optional

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

from .landmark_types import LANDMARK_INDEX, FrameLandmarks, Point
from .model import ensure_pose_model

VISIBILITY_THRESHOLD = 0.5


class PoseExtractor:
    """OpenCV BGR 프레임을 순서대로 넣으면 FrameLandmarks를 돌려주는 얇은 래퍼.

    MediaPipe Tasks API의 VIDEO 모드는 프레임마다 증가하는 타임스탬프(ms)가
    필요하므로, fps를 받아 내부에서 자동으로 타임스탬프를 계산해 관리한다.
    프레임은 반드시 영상 순서대로 extract()에 넣어야 한다.
    """

    def __init__(
        self,
        fps: float = 30.0,
        model_path: Optional[str] = None,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        self._fps = fps
        self._frame_index = 0
        self._last_timestamp_ms = -1

        options = vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=ensure_pose_model(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = vision.PoseLandmarker.create_from_options(options)

    def extract(self, frame_bgr) -> Optional[FrameLandmarks]:
        """사람이 감지되지 않으면 None을 반환한다."""
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        timestamp_ms = int(self._frame_index * 1000 / self._fps)
        if timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1
        self._last_timestamp_ms = timestamp_ms
        self._frame_index += 1

        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)
        if not result.pose_landmarks:
            return None

        height, width = frame_bgr.shape[:2]
        pose = result.pose_landmarks[0]  # num_poses=1이므로 가장 뚜렷한 인물 하나만 사용

        points: Dict[str, Point] = {}
        visible: Dict[str, bool] = {}
        for name, idx in LANDMARK_INDEX.items():
            lm = pose[idx]
            points[name] = (lm.x * width, lm.y * height)
            visible[name] = (lm.visibility or 0.0) >= VISIBILITY_THRESHOLD
        return FrameLandmarks(points=points, visible=visible)

    def close(self) -> None:
        self._landmarker.close()
