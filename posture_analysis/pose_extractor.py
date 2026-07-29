"""MediaPipe Pose Landmarker(Tasks API)로 한 프레임에서 관절 좌표를 뽑아내는 래퍼.

mediapipe 1.0 부터는 예전의 `mp.solutions.pose` API가 제거되고
Tasks API(PoseLandmarker)만 남았기 때문에, 이 API에 맞춰 작성했다.
"""

import os
import urllib.request

import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision
from mediapipe.tasks.python.vision.core.vision_task_running_mode import (
    VisionTaskRunningMode,
)

from .config import LANDMARK

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
)
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "pose_landmarker_lite.task")


def _ensure_model_downloaded():
    if os.path.exists(MODEL_PATH):
        return
    os.makedirs(MODEL_DIR, exist_ok=True)
    print("포즈 인식 모델을 처음 실행하기 위해 내려받는 중입니다 (약 6MB)...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)


class PoseExtractor:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        _ensure_model_downloaded()
        options = vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=VisionTaskRunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = vision.PoseLandmarker.create_from_options(options)

    def extract(self, frame_bgr, timestamp_ms):
        """frame_bgr(OpenCV 프레임) -> {landmark 이름: (x_px, y_px, visibility)} 또는 None."""
        height, width = frame_bgr.shape[:2]
        rgb = frame_bgr[:, :, ::-1].copy()
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

        if not result.pose_landmarks:
            return None

        points = result.pose_landmarks[0]
        landmarks = {}
        for name, idx in LANDMARK.items():
            p = points[idx]
            landmarks[name] = (p.x * width, p.y * height, p.visibility)
        return landmarks

    def close(self):
        self._landmarker.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
