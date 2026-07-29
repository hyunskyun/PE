"""영상에서 MediaPipe Pose로 관절 좌표를 뽑아내는 부분.

cv2와 mediapipe를 사용하는 곳은 이 파일뿐이다. 나머지 코드는 이 파일이 만들어주는
FrameLandmarks(관절 번호 -> (x, y, visibility)) 딕셔너리만 알면 된다.

mediapipe는 버전에 따라 API가 다른데, 최신 버전(1.x)은 레거시 `mp.solutions.pose`
대신 Tasks API(`mediapipe.tasks.python.vision.PoseLandmarker`)를 쓴다. 이 파일은
Tasks API를 사용하며, 최초 실행 시 포즈 인식 모델 파일(.task)을 자동으로 내려받는다.
"""

import os
import urllib.request

# MediaPipe Pose 랜드마크 번호 (33개 중 이 분석에 쓰는 것만)
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
LEFT_ELBOW, RIGHT_ELBOW = 13, 14
LEFT_WRIST, RIGHT_WRIST = 15, 16
LEFT_HIP, RIGHT_HIP = 23, 24
LEFT_KNEE, RIGHT_KNEE = 25, 26
LEFT_ANKLE, RIGHT_ANKLE = 27, 28
NOSE = 0

USED_LANDMARKS = [
    NOSE,
    LEFT_SHOULDER, RIGHT_SHOULDER,
    LEFT_ELBOW, RIGHT_ELBOW,
    LEFT_WRIST, RIGHT_WRIST,
    LEFT_HIP, RIGHT_HIP,
    LEFT_KNEE, RIGHT_KNEE,
    LEFT_ANKLE, RIGHT_ANKLE,
]

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "pose_landmarker_lite.task")

# FrameLandmarks: {landmark_index: (x_px, y_px, visibility)}
FrameLandmarks = dict


def _ensure_model_downloaded(model_path: str = MODEL_PATH) -> str:
    if not os.path.exists(model_path):
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        print(f"포즈 인식 모델을 내려받는 중... ({MODEL_URL})")
        urllib.request.urlretrieve(MODEL_URL, model_path)
    return model_path


def extract_video_landmarks(video_path: str, sample_stride: int = 1):
    """영상 파일을 읽어 프레임별 랜드마크 좌표 목록과 fps를 반환한다.

    Returns:
        (frames, fps) — frames는 FrameLandmarks의 리스트.
    """
    import cv2
    import mediapipe as mp
    from mediapipe.tasks.python import vision
    from mediapipe.tasks.python.core.base_options import BaseOptions

    model_path = _ensure_model_downloaded()
    options = vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=vision.RunningMode.VIDEO,
    )

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    frames = []
    frame_index = 0
    with vision.PoseLandmarker.create_from_options(options) as landmarker:
        while True:
            ok, image = cap.read()
            if not ok:
                break
            if frame_index % sample_stride == 0:
                height, width = image.shape[:2]
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                timestamp_ms = int(frame_index / fps * 1000)
                result = landmarker.detect_for_video(mp_image, timestamp_ms)
                frames.append(_to_frame_landmarks(result, width, height))
            frame_index += 1

    cap.release()
    return frames, fps


def _to_frame_landmarks(pose_result, width: int, height: int) -> FrameLandmarks:
    """mediapipe 결과(정규화 좌표 0~1)를 실제 픽셀 좌표로 바꾼다.

    x, y는 각각 width, height 기준으로 따로 정규화되어 있으므로 각각 곱해야
    한다. 하나로 퉁쳐서 곱하면 영상이 정사각형이 아닐 때 각도가 틀어진다.
    """
    if not pose_result.pose_landmarks:
        return {}

    landmarks = pose_result.pose_landmarks[0]
    frame = {}
    for idx in USED_LANDMARKS:
        lm = landmarks[idx]
        frame[idx] = (lm.x * width, lm.y * height, lm.visibility)
    return frame
