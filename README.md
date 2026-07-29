# PE — 50m 단거리 달리기 자세 분석기

50m 단거리 달리기 측면 영상을 MediaPipe Pose로 분석해서, 가속 구간 / 최대 속도
구간별로 상체 기울기·무릎 굴곡각·팔치기 각도·보폭 비율·착지 위치를 계산하고
기준 범위를 벗어나면 교정 피드백을 텍스트로 출력하는 핵심 분석 엔진.

웹(Cloudflare 정적 배포), 안드로이드 앱(Google AI Studio), 데스크톱 프로그램 등
어떤 형태로 감싸든 재사용할 수 있도록, 영상 처리(`sprint_core/landmarks.py`)와
순수 분석 로직(각도 계산 → 구간 분류 → 판정 → 피드백)을 분리해두었다.

## 설치

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

`sprint_core/landmarks.py`가 처음 실행될 때 포즈 인식 모델 파일을 자동으로
내려받는다 (인터넷 연결 필요, `models/` 폴더에 저장됨).

## 실행

실제 영상으로 분석:

```bash
python analyze.py --video 내영상.mp4 --height 175
```

영상 없이, 보고서용 예시 출력 확인:

```bash
python demo.py
```

## 테스트

```bash
pytest tests/
```

`sprint_core/landmarks.py`를 제외한 모든 코드는 mediapipe/OpenCV 없이도
합성 좌표 데이터(`sprint_core/synth.py`)만으로 테스트된다.

## 구조

```
sprint_core/
  config.py      # 구간별 지표 권장 범위 + 한글 판정 문구 (여기만 고치면 기준 조정 가능)
  landmarks.py    # 영상 -> MediaPipe Pose 랜드마크 추출 (cv2/mediapipe를 쓰는 유일한 파일)
  metrics.py      # 좌표 -> 각도/거리 계산 (순수 함수)
  phases.py       # 가속 구간 / 최대 속도 구간 분류
  judge.py        # 계산값 -> 기준 비교 -> 판정 문구
  feedback.py     # 판정 결과 -> 오류 집계, 우선순위, 점수, 텍스트 리포트
  report.py       # 전체 파이프라인 연결
  synth.py        # 테스트/데모용 합성 랜드마크 생성기
  cli.py          # 명령줄 진입점
```
