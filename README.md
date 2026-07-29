# 50m 단거리 달리기 자세 분석 프로그램

측면에서 촬영한 50m 달리기 영상을 MediaPipe Pose로 분석해, 가속 구간과 최대 속도
유지 구간의 자세 오류를 자동으로 판정하고 교정 문장을 출력하는 프로그램입니다.

## 구조

계산 로직(`sprint_posture/`)과 실행 방식(`main.py`)을 분리했습니다. 계산 로직은
OpenCV/MediaPipe에 의존하지 않는 순수 Python이라, 다른 실행 환경으로 옮길 때도
그대로 재사용할 수 있습니다.

```
sprint_posture/
  landmarks.py   - 사용하는 MediaPipe 랜드마크 번호 상수
  geometry.py    - 각도/거리 계산 (순수 수학 함수)
  metrics.py     - 프레임 한 장의 좌표 -> 자세 지표 (상체 기울기, 무릎 각도 등)
  events.py      - 발목 y좌표로 착지 순간 탐지
  phase.py       - 경과 시간 기준 가속/최대속도 구간 분류
  thresholds.py  - 구간별 권장 범위 (숫자만 있는 설정 파일, 여기만 고치면 기준 조정 가능)
  feedback.py    - (구간, 지표, 방향) -> 오류 이름 / 교정 문장 매핑
  pipeline.py    - OpenCV로 영상을 읽고 MediaPipe Pose를 돌리는 실행 레이어 (여기만 플랫폼 종속)
  report.py      - 프레임/이벤트를 구간별로 집계해 최종 리포트 생성
main.py          - 커맨드라인 진입점
```

## 실행 방법 (데스크톱 프로그램)

```bash
pip install -r requirements.txt
python main.py --video run.mp4 --height 170
```

옵션:
- `--accel-seconds` : 출발 후 가속 구간으로 볼 시간(초). 기본 2.0초
- `--sample-every`  : N프레임마다 하나씩 분석해 속도 향상 (기본 1 = 전체 프레임)
- `--json result.json` : 결과를 JSON으로도 저장

출력 예시:

```
[가속 구간] 프레임 60개, 착지 이벤트 8회, 점수 95.9점
  - 상체 기울기 평균: 11.2 (권장 범위 15~45) -> 판정: 초기 전방 기울기 부족
      교정 제안: 출발 직후 상체를 더 앞으로 기울여 지면을 강하게 밀어내는 느낌으로 뛰어보세요.
  - 보폭 비율 평균: 1.21 (권장 범위 0.8~1.15) -> 판정: 오버스트라이딩 의심
...
우선 교정이 필요한 요소: 오버스트라이딩 의심
```

## 판정 기준값 조정

`sprint_posture/thresholds.py`의 `FRAME_THRESHOLDS`, `EVENT_THRESHOLDS` dict 숫자만
바꾸면 됩니다. 상체 기울기·보폭 비율은 탐구 설계 단계에서 정한 값을 그대로 넣었고,
무릎 각도·팔치기 각도는 조정 가능한 추정치이므로 실측 데이터가 쌓이면 교체하는 것을
권장합니다.

## 다른 형식으로 확장하기

핵심 판정 로직(`landmarks.py` ~ `report.py`)은 영상 입출력과 분리되어 있으므로,
`pipeline.py`에 해당하는 부분만 아래처럼 바꿔주면 같은 로직을 다른 형태로 쓸 수 있습니다.

- **웹(정적 사이트, Cloudflare Pages 등)**: 서버 없이 브라우저에서 끝내려면
  MediaPipe Pose의 JS 버전(`@mediapipe/tasks-vision`)으로 좌표 추출 부분만
  다시 구현하고, `metrics.py`/`thresholds.py`/`feedback.py`의 판정 로직을
  동일한 구조의 JS/TS로 옮겨 정적 파일로 빌드해 업로드하면 됩니다. (이 저장소의
  Python 코드는 그 로직 명세 역할을 합니다.) 서버가 필요하다면 `main.py` 대신
  FastAPI 등으로 `analyze_video()`를 감싸 API로 노출할 수도 있습니다.
- **안드로이드 앱**: MediaPipe Pose Android 솔루션으로 관절 좌표를 얻은 뒤,
  `metrics.py`/`thresholds.py`/`feedback.py`의 계산식을 Kotlin으로 옮기면 됩니다.
  Google AI Studio는 이 판정 결과를 자연어 피드백 문장으로 다듬거나 사용자 질의응답
  기능을 붙이는 데 활용할 수 있습니다.
- **데스크톱 프로그램**: 지금 이 `main.py`가 그 형태입니다. PyInstaller 등으로
  실행 파일로 묶거나, Tkinter로 얇은 GUI를 씌워도 `sprint_posture` 패키지는
  그대로 재사용합니다.

## 한계

- 2D 측면 영상만 사용하므로 깊이 정보가 없고, 좌우 비대칭은 분석하지 못합니다.
- 착지 순간은 발목의 화면상 y좌표 국소최댓값으로 근사한 것이라, 실제 지면반발력을
  측정하지는 못합니다.
- 촬영 각도가 달리기 방향과 어긋나거나 조명이 나쁘면 랜드마크 인식 오차가 커집니다.
