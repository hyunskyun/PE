"""50m 달리기 자세 분석 프로그램의 핵심 로직 패키지.

- geometry.py, thresholds.py, scoring.py, phase.py: 외부 라이브러리에 의존하지
  않는 순수 로직. 웹(JS)/안드로이드(Kotlin) 등 다른 플랫폼으로 이식할 때는
  이 파일들의 로직만 그대로 옮기면 된다.
- landmarks.py, analyzer.py, annotate.py: OpenCV/MediaPipe로 영상을 처리하는
  파이썬 전용 I/O 계층.

VideoPostureAnalyzer는 여기서 미리 import하지 않는다. opencv/mediapipe가 설치되지
않은 환경에서도 geometry/thresholds/scoring/phase 같은 순수 로직 모듈은 바로 쓸 수
있어야 하기 때문이다. 영상 분석이 필요하면 아래처럼 직접 import한다.

    from pose_analyzer.analyzer import VideoPostureAnalyzer
"""
