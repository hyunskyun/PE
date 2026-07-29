"""MediaPipe Pose Landmarker 모델(.task) 파일을 준비하는 모듈.

최신 MediaPipe(Tasks API)는 모델 가중치를 패키지에 내장하지 않고 별도의 .task
파일을 요구한다. 이 모듈은 최초 실행 시 한 번만 공식 모델을 내려받아 사용자
홈 디렉터리 캐시에 저장하고, 이후 실행에서는 캐시된 파일을 그대로 재사용한다.
"""
from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Optional

# Google이 제공하는 경량(lite) Pose Landmarker 모델. 정확도가 더 필요하면
# 'pose_landmarker_full' 또는 'pose_landmarker_heavy'로 바꿔도 된다.
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
)
CACHE_DIR = Path.home() / ".cache" / "pose_analyzer"
CACHE_PATH = CACHE_DIR / "pose_landmarker_lite.task"


def ensure_pose_model(model_path: Optional[str] = None) -> str:
    """모델 파일 경로를 반환한다.

    model_path를 직접 지정하면 그 경로를 그대로 쓴다. 지정하지 않으면 캐시를
    확인하고, 캐시가 없으면 공식 저장소에서 내려받아 캐시에 저장한 뒤 그 경로를
    반환한다.
    """
    if model_path:
        return model_path

    if not CACHE_PATH.exists():
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(MODEL_URL, CACHE_PATH)

    return str(CACHE_PATH)
