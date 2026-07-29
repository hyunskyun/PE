"""영상을 프레임 단위로 분할하고 MediaPipe Pose로 랜드마크를 추출한다.

이 모듈만 cv2/mediapipe에 의존한다. 순수 계산 로직(metrics, judge 등)은
이 모듈 없이도 임포트·테스트할 수 있도록 분리되어 있다.
"""

import os
from typing import Dict, List, Optional, Tuple

import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose

Landmarks = Dict[int, Tuple[float, float, float]]


def extract_video_landmarks(
    video_path: str, model_complexity: int = 1
) -> Tuple[float, List[Optional[Landmarks]]]:
    """영상 전체를 순회하며 프레임별 랜드마크를 추출한다.

    반환: (fps, frame_landmarks_list)
        frame_landmarks_list[i]는 {랜드마크번호: (x_px, y_px, visibility)}
        딕셔너리이거나, 사람이 감지되지 않은 프레임이면 None.

    예외:
        FileNotFoundError: 영상 파일이 존재하지 않음
        ValueError: 영상을 열 수 없음 / FPS 비정상 / 프레임 없음
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"영상 파일이 존재하지 않습니다: {video_path}")

    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise ValueError(f"영상을 열 수 없습니다 (지원하지 않는 형식일 수 있음): {video_path}")

    fps = capture.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        capture.release()
        raise ValueError(f"영상의 FPS 정보가 비정상입니다 (fps={fps}): {video_path}")

    frame_landmarks_list: List[Optional[Landmarks]] = []

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=model_complexity,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as pose:
        while True:
            success, frame = capture.read()
            if not success:
                break

            height, width = frame.shape[:2]
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = pose.process(rgb_frame)

            if result.pose_landmarks is None:
                frame_landmarks_list.append(None)
                continue

            landmarks = {
                idx: (point.x * width, point.y * height, point.visibility)
                for idx, point in enumerate(result.pose_landmarks.landmark)
            }
            frame_landmarks_list.append(landmarks)

    capture.release()

    if not frame_landmarks_list:
        raise ValueError(f"영상에서 프레임을 하나도 읽지 못했습니다: {video_path}")

    return fps, frame_landmarks_list
