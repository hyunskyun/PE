"""영상을 프레임 단위로 분할하고 MediaPipe Pose로 랜드마크를 추출한다.

보고서의 처리 순서 중 "영상 입력 -> 프레임 단위 분할 -> MediaPipe Pose로
랜드마크 추출" 단계에 해당한다.
"""

import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose


def extract_video_landmarks(video_path, model_complexity=1):
    """영상 전체를 순회하며 프레임별 랜드마크를 추출한다.

    반환: (fps, frame_landmarks_list)
        frame_landmarks_list[i]는 {랜드마크번호: (x_px, y_px, visibility)}
        딕셔너리이거나, 사람이 감지되지 않은 프레임이면 None.
    """
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise FileNotFoundError(f"영상을 열 수 없습니다: {video_path}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    frame_landmarks_list = []

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
    return fps, frame_landmarks_list
