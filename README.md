# 50m 달리기 자세 분석 프로그램

50m 단거리 달리기 측면 영상을 입력받아 MediaPipe Pose로 관절 좌표를 추출하고,
가속 구간 / 최대 속도 구간으로 나누어 상체 전방 기울기, 무릎 각도, 팔치기 각도,
보폭 비율, 착지-엉덩이 수평거리를 조건문 기준으로 판정해 교정 피드백을
출력하는 프로그램입니다. 탐구보고서의 핵심 기능만 구현했고, 여러 형태로
쉽게 확장/배포할 수 있도록 로직을 최대한 단순하고 읽기 쉬운 구조로 나눴습니다.

## 폴더 구조

```
posture_analyzer/   핵심 분석 엔진 (Python) — 모든 배포 형태의 기반이 되는 부분
  config.py          임계값·랜드마크 인덱스·피드백 문구 (여기만 고치면 기준 조정 가능)
  geometry.py        각도/거리 계산 (MediaPipe에 의존하지 않는 순수 함수)
  landmarks.py        MediaPipe Pose 래퍼 (프레임 -> 좌표)
  metrics.py          좌표 -> 지표(기울기, 각도 등) 계산
  phases.py            가속 구간 / 최대 속도 구간 분류
  landing.py           착지 순간 감지 + 보폭·착지 위치 계산
  judge.py              임계값 비교 후 오류 유형 판정 (조건문 로직)
  report.py             구간별 집계 + 텍스트 리포트 생성
  pipeline.py            위 단계를 순서대로 실행하는 진입점 (analyze_video)
  cli.py                  명령줄 실행 스크립트
web/
  index.html          브라우저에서 동작하는 정적 버전 (Cloudflare Pages 등에 그대로 업로드 가능)
requirements.txt      Python 의존성 (opencv-python, mediapipe)
```

## 처리 과정

영상 입력 → 프레임 단위 분할 → MediaPipe Pose로 랜드마크 추출 →
좌표 기반 각도·거리 계산 → 구간 분류(가속/최대 속도) → 조건문 비교 →
오류 판정 → 교정 피드백 출력

이 순서가 `pipeline.py`(파이썬)와 `web/index.html`의 `analyzeCurrentVideo` 함수(자바스크립트)에
그대로 대응됩니다.

## 지표 정의 (요약)

| 지표 | 계산 방법 |
|---|---|
| 상체 전방 기울기 | 어깨 중심 → 엉덩이 중심 벡터가 수직선과 이루는 각도 |
| 무릎 각도 | 엉덩이-무릎-발목 세 점이 무릎에서 이루는 각도 |
| 팔치기 각도 | 어깨-팔꿈치-손목 세 점이 팔꿈치에서 이루는 각도 |
| 보폭 비율 | 착지 순간 양 발목 사이 거리 ÷ (코~발목 중점 픽셀 거리로 추정한 신장) |
| 착지-엉덩이 수평거리 비율 | 착지 발목과 엉덩이 중심의 수평거리 ÷ 추정 신장 |

카메라와의 거리·해상도에 관계없이 비교 가능하도록, 모든 거리 지표는 "영상에서 추정한
신장(픽셀)"을 기준으로 나눈 비율로 계산합니다. `--height`(cm)를 입력하면 보폭을
실제 cm 단위로도 함께 보여줍니다.

임계값과 피드백 문구는 `config.py`의 `THRESHOLDS`, `ERROR_MESSAGES`에 모여 있으며,
값을 바꾸면 판정 로직 코드를 건드리지 않고도 기준을 조정할 수 있습니다.

## 실행 방법 (데스크톱 / Python)

```bash
pip install -r requirements.txt
python -m posture_analyzer.cli my_run.mp4 --height 170
python -m posture_analyzer.cli my_run.mp4 --height 170 --json report.json
```

또는 코드에서 직접 호출:

```python
from posture_analyzer import analyze_video, format_report_text

report = analyze_video("my_run.mp4", user_height_cm=170)
print(format_report_text(report))
```

`--sample-every 2` 처럼 옵션을 주면 프레임을 건너뛰며 분석해 처리 속도를 높일 수 있습니다.
PyInstaller 등으로 패키징하면 별도의 "컴퓨터 프로그램(exe)" 형태로도 배포할 수 있습니다.

## 웹 사이트로 배포 (Cloudflare Pages 등 정적 호스팅)

`web/index.html` 하나만으로 동작하는 정적 페이지입니다. 서버나 빌드 과정 없이
파일을 그대로 업로드하면 됩니다.

1. Cloudflare 대시보드 → Workers & Pages → Pages → "Upload assets"
2. `web/index.html`이 들어 있는 폴더(또는 파일)를 업로드
3. 배포된 주소로 접속 → 영상 업로드 → 분석

동작 원리: 브라우저에서 `@mediapipe/tasks-vision`(WASM)을 CDN으로 불러와 포즈를
추정하고, `posture_analyzer`와 동일한 각도 계산·구간 분류·임계값 판정 로직을
자바스크립트로 그대로 옮겨 실행합니다. 영상은 업로드되지 않고 브라우저 안에서만
처리되므로 개인정보 문제도 적습니다. 최초 접속 시 모델(WASM/모델 파일)을
CDN에서 내려받기 때문에 인터넷 연결이 필요합니다.

## 안드로이드 앱으로 만들기 (Google AI Studio 활용)

Google AI Studio의 앱 빌드 기능에 아래 내용을 입력해 Kotlin 기반 안드로이드
앱 초안을 생성할 수 있습니다.

- "MediaPipe Tasks의 PoseLandmarker를 이용해 갤러리에서 고른 달리기 영상을
  프레임 단위로 분석하고, 아래 규칙으로 자세를 판정하는 앱을 만들어줘"
- `config.py`의 `THRESHOLDS`, `ERROR_MESSAGES` 표를 그대로 프롬프트에 붙여넣기
- `metrics.py`의 각도 계산 공식(엉덩이-무릎-발목 각도 등)을 함께 제공

핵심 판정 로직(임계값, 조건문, 피드백 문구)은 이미 `config.py` / `judge.py`에
플랫폼 독립적으로 정리되어 있으므로, 이 파일들을 Kotlin으로 그대로 옮기는 것이
가장 빠른 이식 방법입니다. `web/index.html`의 자바스크립트 포팅본이 참고할
수 있는 두 번째 예시가 됩니다.

## 한계 (보고서 5.3절에 활용)

- 2D 영상이라 깊이(전후) 정보가 없어 좌우 비대칭이나 3차원 동작은 정확히 볼 수 없습니다.
- 지면반발력처럼 힘과 관련된 값은 직접 측정하지 못하고, 자세(각도·비율)로만 간접 추정합니다.
- 신장(픽셀) 추정과 착지 순간 감지는 근사치이므로, 촬영 각도가 달리기 방향과 어긋나거나
  조명이 나쁘면 오차가 커집니다.
- 구간(가속/최대 속도) 경계는 엉덩이 이동량 기반 추정이며, 실제 스플릿 타임 기록이 있다면
  그 값으로 경계를 대체하는 것이 더 정확합니다.
