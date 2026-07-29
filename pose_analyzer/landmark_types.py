"""랜드마크 데이터 구조 정의. OpenCV/MediaPipe에 의존하지 않는 순수 자료형이다.

metrics.py 같은 순수 로직 모듈이 이 파일만 참조하도록 해서, cv2/mediapipe가 없는
환경(예: 로직만 다른 언어로 이식해서 검증할 때)에서도 계산 로직을 그대로 쓸 수 있게 한다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

Point = Tuple[float, float]

# 랜드마크 이름 -> MediaPipe Pose 인덱스 (탐구 보고서 "4. 추출할 핵심 랜드마크"와 동일)
LANDMARK_INDEX: Dict[str, int] = {
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28,
}


@dataclass
class FrameLandmarks:
    """한 프레임에서 추출한 관절 좌표(이미지 픽셀 좌표계)."""

    points: Dict[str, Point] = field(default_factory=dict)
    visible: Dict[str, bool] = field(default_factory=dict)

    def get(self, name: str) -> Optional[Point]:
        if not self.visible.get(name, False):
            return None
        return self.points.get(name)

    def all_visible(self, *names: str) -> bool:
        return all(self.visible.get(n, False) for n in names)
