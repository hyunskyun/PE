"""전체 처리 과정을 순서대로 실행하는 진입점.

영상 입력 -> 프레임 분할 -> 랜드마크 추출 -> 지표 계산
-> 구간 분류 -> 조건문 비교 -> 오류 판정 -> 리포트 생성
"""
import cv2

from .landing import detect_landing_events
from .landmarks import PoseExtractor
from .metrics import compute_frame_metrics
from .phases import segment_phases
from .report import build_report

DEFAULT_FPS = 30.0


def analyze_video(video_path: str, user_height_cm: float | None = None, sample_every: int = 1) -> dict:
    """측면 달리기 영상을 분석해서 리포트(dict)를 반환한다.

    user_height_cm: 사용자 신장(cm). 주어지면 보폭 비율을 실제 길이(cm)로도 환산해서 보여준다.
    sample_every: 1이면 모든 프레임을, 2면 한 프레임씩 건너뛰며 분석한다.
    (영상이 길거나 컴퓨터 성능이 낮을 때 처리 속도를 높이는 용도)
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"영상을 열 수 없습니다: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or DEFAULT_FPS
    effective_fps = fps / sample_every

    frame_metrics = []
    with PoseExtractor() as extractor:
        frame_idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_idx % sample_every == 0:
                points = extractor.extract(frame)
                if points is not None:
                    time_sec = frame_idx / fps
                    frame_metrics.append(compute_frame_metrics(points, len(frame_metrics), time_sec))
            frame_idx += 1
    cap.release()

    if len(frame_metrics) < 2:
        raise ValueError(
            "사람을 충분히 인식하지 못했습니다. 촬영 각도, 조명, 프레임 안에 "
            "전신이 들어오는지를 확인해주세요."
        )

    phases = segment_phases(frame_metrics, effective_fps)
    landing_events = detect_landing_events(frame_metrics, effective_fps)

    return build_report(frame_metrics, phases, landing_events, user_height_cm=user_height_cm)
