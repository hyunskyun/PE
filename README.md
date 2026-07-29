# 50m 달리기 자세 분석 프로그램

측면에서 촬영한 50m 단거리 달리기 영상을 입력받아, MediaPipe Pose로
관절 좌표를 추출하고 조건문(if-else) 기반 임계값 비교로 자세 오류를
자동 판정하는 핵심 분석 엔진입니다. 탐구 보고서의 "3.4 조건문 기반
평가 로직 설계 / 4.5 MediaPipe 기반 자세 분석 시스템 구조" 항목을 그대로
코드로 옮긴 구조입니다.

## 처리 순서

```
영상 입력 -> 프레임 단위 분할 -> MediaPipe Pose 랜드마크 추출
   -> 좌표 기반 각도·거리 계산 -> 구간 분류(가속/최대 속도)
   -> 조건문 비교 -> 오류 판정 -> 교정 피드백 출력
```

## 폴더 구조

```
posture_analysis/
  constants.py      랜드마크 번호 (어깨11·12, 팔꿈치13·14, 손목15·16, 엉덩이23·24, 무릎25·26, 발목27·28)
  geometry.py        각도/거리 계산 (좌표 기반 순수 함수)
  metrics.py          상체 기울기, 무릎각, 팔치기각, 보폭비율, 착지오프셋 계산
  phase.py             가속 구간 / 최대 속도 구간 분류
  thresholds.py        구간별 권장 범위 + 오류별 교정 문장 (여기 숫자만 바꾸면 판정 기준 조정 가능)
  judge.py              조건문 기반 판정 로직 (이 파일이 "3.4" 항목의 실제 구현)
  landing.py            착지 프레임(발목 y좌표 국소 최댓값) 탐지
  pose_extractor.py      OpenCV + MediaPipe로 프레임별 랜드마크 추출
  analyzer.py             전체 파이프라인 오케스트레이션
  report.py                구간별 평균/오류횟수/점수 집계 및 텍스트 출력
main.py                     CLI 실행 진입점
tests/test_core.py          mediapipe 없이도 도는 순수 로직 단위 테스트
```

## 실행 방법

```bash
pip install -r requirements.txt
python main.py --video sprint.mp4 --height 172
```

옵션:

- `--acceleration-end` : 가속 구간이 끝나는 시각(초). 생략하면 영상 길이의 40% 지점을 기본 경계로 사용합니다.
- `--output result.json` : 프레임별 상세 결과 + 요약을 JSON으로 저장합니다.

출력 예시:

```
[가속 구간]
  상체 기울기 평균: 11.20 (권장 범위 15~45) -> 판정: 권장 범위 이탈
  보폭 비율 평균: 1.21 (권장 범위 0.8~1.15) -> 판정: 권장 범위 이탈
  오류 발생 횟수:
    - 초기 전방 기울기 부족: 18회
    - 오버스트라이딩 의심(가속 구간): 9회
  우선 교정 필요 요소: 초기 전방 기울기 부족 (18회)
  구간 자세 점수: 62.5 / 100

[최대 속도 구간]
  상체 기울기 평균: 8.40 (권장 범위 5~12) -> 판정: 적정
  ...
```

## 테스트

```bash
python -m unittest tests.test_core -v
```

각도 계산, 구간 분류, 조건문 판정, 리포트 집계처럼 mediapipe/opencv 없이
검증 가능한 순수 로직만 다룹니다. 실제 영상 처리(`pose_extractor.py`,
`analyzer.py`)는 `pip install -r requirements.txt` 후 실제 영상으로
직접 확인하세요.

## 임계값(판정 기준) 조정하기

`posture_analysis/thresholds.py`의 `THRESHOLDS` dict 숫자만 바꾸면
판정 기준이 즉시 바뀝니다. 현재 값은 일반적인 스프린트 생체역학 자료를
참고한 예시이므로, 탐구를 진행하며 코치 자문이나 참고 문헌의 수치로
교체하는 것을 권장합니다.

## 다른 형태로 확장하기

핵심 로직(`posture_analysis/`)은 UI와 완전히 분리되어 있어서, 아래처럼
여러 형태로 감쌀 수 있습니다.

1. **정적 웹사이트 (Cloudflare Pages)**
   - `analyzer.py` + `report.py`의 결과를 `--output result.json`으로 저장
   - JSON을 읽어 그래프/표로 보여주는 정적 HTML+JS 페이지를 만들어
     Cloudflare Pages에 업로드 (분석 자체는 로컬/서버에서 미리 실행)
   - 실시간 업로드-분석까지 원하면 별도 서버(예: Cloudflare Workers +
     외부 Python 백엔드 API)가 필요합니다. Workers 자체는 Python
     비디오 처리를 직접 실행하지 못합니다.

2. **안드로이드 앱 (Google AI Studio 등)**
   - MediaPipe는 Android용 Tasks API(`Pose Landmarker`)를 제공하므로,
     `metrics.py` / `thresholds.py` / `judge.py`의 로직(각도 공식과
     임계값 비교 규칙)을 Kotlin/Java로 그대로 옮기면 기기 내에서
     실시간 분석이 가능합니다. 이 Python 코드는 로직 설계를 검증하는
     참고 구현으로 사용하세요.

3. **데스크톱 프로그램**
   - `main.py`를 그대로 `pyinstaller`로 패키징하면 별도 설치 없이
     실행 파일 형태로 배포할 수 있습니다.
   - GUI가 필요하면 `analyze_video()` / `summarize()` 함수를 그대로
     불러와 Tkinter 등으로 파일 선택 창만 얹으면 됩니다.

어떤 형태로 감싸든 핵심 판정 로직(`judge.py`, `thresholds.py`)은
그대로 재사용할 수 있도록 UI 의존성 없이 순수 함수로 작성했습니다.

## 한계

- 2D 측면 영상이라 깊이 정보가 없어 좌우 비대칭이나 실제 3D 각도를
  정확히 구하지 못합니다.
- 지면반발력을 직접 측정하지 않고, 착지 프레임을 발목 y좌표 국소
  최댓값으로 근사합니다.
- 신장(px) 추정은 코-발목 거리 근사치이므로 카메라 각도·거리 변화에
  따라 오차가 생길 수 있습니다.
- `thresholds.py`의 권장 범위는 예시 값이며, 실제 탐구에서는 근거
  문헌이나 코치 자문으로 검증해 교체하는 것을 권장합니다.
