"""MediaPipe Pose를 감싸서 필요한 랜드마크만 꺼내주는 얇은 래퍼.

이 파일만 MediaPipe/OpenCV에 직접 의존한다. 나머지 모듈은
geometry.Point만 알면 되므로, 나중에 다른 포즈 추정 라이브러리로
바꾸더라도 이 파일만 수정하면 된다.
"""
import cv2
import mediapipe as mp

from .config import LANDMARK_INDEX
from .geometry import Point


class PoseExtractor:
    def __init__(self, min_detection_confidence: float = 0.5, min_tracking_confidence: float = 0.5):
        self._pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def extract(self, frame_bgr) -> dict[str, Point] | None:
        """한 프레임에서 관절 좌표를 픽셀 단위로 추출한다.

        사람이 인식되지 않으면 None을 반환한다.
        """
        height, width = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        result = self._pose.process(rgb)
        if not result.pose_landmarks:
            return None

        raw = result.pose_landmarks.landmark
        points = {}
        for name, idx in LANDMARK_INDEX.items():
            lm = raw[idx]
            # MediaPipe는 정규화 좌표(0~1)를 주므로, 각도 계산이 가로세로
            # 비율에 영향을 받지 않도록 실제 픽셀 좌표로 변환한다.
            points[name] = Point(x=lm.x * width, y=lm.y * height, visibility=lm.visibility)
        return points

    def close(self):
        self._pose.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
